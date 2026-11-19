"""TG-172: Etkinlik yayınlamada organizatör onayı ve sahiplik testleri."""

import sqlite3

import pytest

from app.core.db import get_db
from app.events.services import EventPermissionError, get_event, publish_event


@pytest.fixture
def auth_db(app):
    """Gerçek SQLite ile onaylı, onaysız ve farklı rollerde kullanıcılar oluşturur."""
    with app.app_context():
        db = get_db()

        # Accounts onay sütunu henüz gerçek şemada yok; yalnızca test DB'ye eklenir.
        db.execute("ALTER TABLE users ADD COLUMN organizer_approved INTEGER NOT NULL DEFAULT 0")

        def add_user(email, role, approved):
            return db.execute(
                """
                INSERT INTO users (email, password_hash, role, organizer_approved)
                VALUES (?, ?, ?, ?)
                """,
                (email, "testhash", role, approved),
            ).lastrowid

        owner = add_user("owner172@example.com", "organizer", 1)
        other_organizer = add_user("other172@example.com", "organizer", 1)
        unapproved = add_user("pending172@example.com", "organizer", 0)
        participant = add_user("participant172@example.com", "participant", 1)

        venue_id = db.execute(
            "INSERT INTO venues (name, address, capacity) VALUES (?, ?, ?)",
            ("TG172 Salonu", "Iğdır", 120),
        ).lastrowid
        db.commit()

        def add_event(*, event_owner=None):
            if event_owner is None:
                event_owner = owner
            cursor = db.execute(
                """
                INSERT INTO events (
                    title, category, venue_id, start_time, end_time,
                    capacity, price, status, organizer_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "TG172 Etkinliği",
                    "Eğitim",
                    venue_id,
                    "2026-12-01T10:00",
                    "2026-12-01T12:00",
                    50,
                    0,
                    "draft",
                    event_owner,
                ),
            )
            db.commit()
            return cursor.lastrowid

        yield {
            "db": db,
            "db_path": app.config["DATABASE"],
            "add_event": add_event,
            "owner": owner,
            "other": other_organizer,
            "unapproved": unapproved,
            "participant": participant,
        }


def _assert_still_draft(auth_db, event_id):
    """Ret sonrası veritabanında hiç değişiklik olmadığını yeni bağlantıyla doğrular."""
    db = auth_db["db"]
    assert get_event(db, event_id)["status"] == "draft"

    separate = sqlite3.connect(auth_db["db_path"])
    try:
        row = separate.execute("SELECT status FROM events WHERE id = ?", (event_id,)).fetchone()
        assert row is not None
        assert row[0] == "draft"
    finally:
        separate.close()


def test_approved_owner_can_publish(auth_db):
    """BR-1.5: yönetici onaylı organizatör kendi etkinliğini yayınlar."""
    event_id = auth_db["add_event"]()
    ok, event, errors = publish_event(auth_db["db"], event_id, auth_db["owner"])

    assert ok is True
    assert errors == []
    assert event["organizer_id"] == auth_db["owner"]
    assert event["status"] == "published"


def test_unapproved_organizer_is_rejected(auth_db):
    """Yönetici onayı yoksa kendi etkinliğini dahi yayınlayamaz."""
    event_id = auth_db["add_event"](event_owner=auth_db["unapproved"])

    with pytest.raises(EventPermissionError, match="yönetici onaylı"):
        publish_event(auth_db["db"], event_id, auth_db["unapproved"])

    _assert_still_draft(auth_db, event_id)


def test_other_approved_organizer_is_rejected(auth_db):
    """Başka onaylı organizatör etkinliğin sahibi olmadığı için yayınlayamaz."""
    event_id = auth_db["add_event"]()

    with pytest.raises(EventPermissionError, match="etkinlik sahibi"):
        publish_event(auth_db["db"], event_id, auth_db["other"])

    _assert_still_draft(auth_db, event_id)


def test_participant_cannot_publish_even_if_approved_flag_is_set(auth_db):
    """Onay alanı 1 olsa da kullanıcı rolü participant ise yayınlama yasaktır."""
    event_id = auth_db["add_event"](event_owner=auth_db["participant"])

    with pytest.raises(EventPermissionError):
        publish_event(auth_db["db"], event_id, auth_db["participant"])

    _assert_still_draft(auth_db, event_id)


def test_unknown_user_is_rejected(auth_db):
    """Veritabanında bulunmayan kullanıcı yetki alamaz."""
    event_id = auth_db["add_event"]()

    with pytest.raises(EventPermissionError):
        publish_event(auth_db["db"], event_id, 99999)

    _assert_still_draft(auth_db, event_id)


@pytest.mark.parametrize("bad_user_id", [None, 0, -1, True, "1"])
def test_invalid_user_id_is_rejected(auth_db, bad_user_id):
    """Geçersiz kullanıcı kimliği yetki doğrulamasından geçemez."""
    event_id = auth_db["add_event"]()

    with pytest.raises(EventPermissionError):
        publish_event(auth_db["db"], event_id, bad_user_id)

    _assert_still_draft(auth_db, event_id)


def test_owner_can_publish_after_unauthorized_attempt(auth_db):
    """Yetkisiz deneme etkinliği değiştirmez; sahibi daha sonra yayınlayabilir."""
    event_id = auth_db["add_event"]()

    with pytest.raises(EventPermissionError):
        publish_event(auth_db["db"], event_id, auth_db["other"])

    _assert_still_draft(auth_db, event_id)
    ok, event, errors = publish_event(auth_db["db"], event_id, auth_db["owner"])
    assert ok is True
    assert errors == []
    assert event["status"] == "published"
