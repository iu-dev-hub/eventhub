"""Etkinlik yayınlama servisi birim testleri (TG-174, TG-172, PB-04; BR-1.5)."""

import pytest

from app.core.db import get_db
from app.events.services import EventPermissionError, get_event, publish_event


@pytest.fixture
def db(app):
    with app.app_context():
        db = get_db()
        db.execute("ALTER TABLE users ADD COLUMN organizer_approved BOOLEAN NOT NULL DEFAULT 0")
        db.execute(
            "INSERT INTO venues (id, name, address, capacity) "
            "VALUES (1, 'Büyük Salon', 'Adres', 100)"
        )
        db.execute(
            "INSERT INTO users (id, email, password_hash, role, organizer_approved) "
            "VALUES (1, 'org1@example.com', 'x', 'organizer', 1)"
        )
        db.execute(
            "INSERT INTO users (id, email, password_hash, role, organizer_approved) "
            "VALUES (2, 'org2@example.com', 'x', 'organizer', 1)"
        )
        db.execute(
            "INSERT INTO users (id, email, password_hash, role, organizer_approved) "
            "VALUES (3, 'unapproved@example.com', 'x', 'organizer', 0)"
        )
        db.commit()
        yield db


def _insert_event(db, **kwargs):
    defaults = {
        "title": "Bahar Konseri",
        "category": "Müzik",
        "venue_id": 1,
        "start_time": "2026-12-01T18:00",
        "end_time": "2026-12-01T21:00",
        "capacity": 80,
        "price": 50.0,
        "status": "draft",
        "organizer_id": 1,
    }
    data = {**defaults, **kwargs}
    cursor = db.execute(
        "INSERT INTO events ("
        "title, category, venue_id, start_time, end_time, capacity, price, status, organizer_id"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            data["title"],
            data["category"],
            data["venue_id"],
            data["start_time"],
            data["end_time"],
            data["capacity"],
            data["price"],
            data["status"],
            data["organizer_id"],
        ),
    )
    db.commit()
    return cursor.lastrowid


def test_publish_event_success_for_approved_organizer(db):
    """Onaylı organizatör kendi geçerli taslak etkinliğini yayınlayabilir."""
    event_id = _insert_event(db, organizer_id=1, status="draft")

    ok, event, errors = publish_event(db, event_id, organizer_id=1)

    assert ok is True
    assert errors == []
    assert event is not None
    assert event["status"] == "published"
    assert event["id"] == event_id

    refetched = get_event(db, event_id)
    assert refetched["status"] == "published"


def test_publish_event_blocked_for_unapproved_organizer(db):
    """BR-1.5: Yönetici onayı olmayan organizatör etkinlik yayınlayamaz."""
    event_id = _insert_event(db, organizer_id=3, status="draft")

    with pytest.raises(EventPermissionError) as exc_info:
        publish_event(db, event_id, organizer_id=3)

    assert "onay" in str(exc_info.value).lower()
    assert get_event(db, event_id)["status"] == "draft"


def test_publish_event_blocked_when_no_approval_column_in_users(app):
    """Kullanıcı tablosunda onay sütunu yoksa güvenli varsayılan olarak yayınlama engellenir."""
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO venues (id, name, address, capacity) VALUES (1, 'V1', 'A', 100)")
        db.execute(
            "INSERT INTO users (id, email, password_hash, role) "
            "VALUES (1, 'org@e.com', 'x', 'organizer')"
        )
        db.execute(
            "INSERT INTO events ("
            "id, title, category, venue_id, start_time, end_time, "
            "capacity, price, status, organizer_id"
            ") VALUES (1, 'T', 'C', 1, '2026-12-01T10:00', '2026-12-01T12:00', 50, 0, 'draft', 1)"
        )
        db.commit()

        with pytest.raises(EventPermissionError):
            publish_event(db, 1, organizer_id=1)

        row = db.execute("SELECT status FROM events WHERE id = 1").fetchone()
        assert row["status"] == "draft"


def test_publish_event_idor_protection_different_organizer(db):
    """IDOR koruması: Organizatör başka bir organizatörün taslağını yayınlayamaz."""
    event_id = _insert_event(db, organizer_id=1, status="draft")

    with pytest.raises(EventPermissionError) as exc_info:
        publish_event(db, event_id, organizer_id=2)

    assert "etkinlik sahibi" in str(exc_info.value).lower()
    assert get_event(db, event_id)["status"] == "draft"


def test_publish_event_not_found(db):
    """Var olmayan etkinlik ID'si verildiğinde hata dönmelidir."""
    ok, event, errors = publish_event(db, 9999, organizer_id=1)

    assert ok is False
    assert event is None
    assert "Etkinlik bulunamadı." in errors


def test_publish_event_already_published(db):
    """Zaten yayınlanmış bir etkinlik tekrar yayınlanamaz."""
    event_id = _insert_event(db, organizer_id=1, status="published")

    ok, event, errors = publish_event(db, event_id, organizer_id=1)

    assert ok is False
    assert event is None
    assert errors == ["Yalnızca taslak etkinlikler yayınlanabilir."]


@pytest.mark.parametrize("invalid_id", [0, -1, None, "abc", True])
def test_publish_event_invalid_id(db, invalid_id):
    """Geçersiz etkinlik ID'si reddedilir."""
    ok, event, errors = publish_event(db, invalid_id, organizer_id=1)

    assert ok is False
    assert event is None
    assert errors == ["Geçersiz etkinlik kimliği."]


def test_publish_event_leaves_other_events_intact(db):
    """Bir etkinliğin yayınlanması diğer etkinliklerin taslak durumunu etkilemez."""
    e1 = _insert_event(db, title="Etkinlik 1", organizer_id=1, status="draft")
    e2 = _insert_event(db, title="Etkinlik 2", organizer_id=1, status="draft")

    ok, event, errors = publish_event(db, e1, organizer_id=1)

    assert ok is True
    assert event["status"] == "published"
    assert get_event(db, e1)["status"] == "published"
    assert get_event(db, e2)["status"] == "draft"
