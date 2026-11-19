
"""TG-171: Etkinlik yayınlama ve veritabanı kalıcılık testleri."""

import sqlite3

import pytest

from app.core.db import get_db
from app.events.services import get_event, publish_event


@pytest.fixture
def event_db(app):
    """Her test için gerçek SQLite veritabanı ve örnek kayıt hazırlar."""

    with app.app_context():
        db = get_db()

        # Örnek organizatör oluştur.
        organizer_id = db.execute(
            """
            INSERT INTO users (email, password_hash, role)
            VALUES (?, ?, ?)
            """,
            ("test171@example.com", "testhash", "organizer"),
        ).lastrowid

        # Örnek salon oluştur.
        venue_id = db.execute(
            """
            INSERT INTO venues (name, address, capacity)
            VALUES (?, ?, ?)
            """,
            ("TG171 Salonu", "Iğdır", 100),
        ).lastrowid

        db.commit()

        def add_event(title="Yazılım Semineri"):
            """Veritabanına taslak etkinlik ekler."""

            cursor = db.execute(
                """
                INSERT INTO events (
                    title, category, venue_id,
                    start_time, end_time,
                    capacity, price, status, organizer_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title, "Eğitim", venue_id,
                    "2026-12-01T10:00",
                    "2026-12-01T12:00",
                    50, 0, "draft", organizer_id,
                ),
            )

            db.commit()
            return cursor.lastrowid

        yield db, add_event, app.config["DATABASE"]


def test_draft_event_is_published_and_persisted(event_db):
    """Taslak yayınlanır ve yeni DB bağlantısında da published görünür."""

    db, add_event, db_path = event_db
    event_id = add_event()

    ok, event, errors = publish_event(db, event_id)

    assert ok is True
    assert errors == []
    assert event["status"] == "published"

    # Başka bağlantıyla tekrar oku: COMMIT gerçekten yapılmış mı?
    check_db = sqlite3.connect(db_path)
    try:
        row = check_db.execute(
            "SELECT status FROM events WHERE id = ?",
            (event_id,),
        ).fetchone()

        assert row is not None
        assert row[0] == "published"
    finally:
        check_db.close()


def test_published_event_cannot_be_published_again(event_db):
    """Zaten yayınlanan etkinlik tekrar yayınlanamaz."""

    db, add_event, _ = event_db
    event_id = add_event()

    publish_event(db, event_id)
    ok, event, errors = publish_event(db, event_id)

    assert ok is False
    assert event is None
    assert errors == ["Yalnızca taslak etkinlikler yayınlanabilir."]


def test_unknown_event_cannot_be_published(event_db):
    """Veritabanında olmayan etkinlik yayınlanamaz."""

    db, _, _ = event_db

    ok, event, errors = publish_event(db, 99999)

    assert ok is False
    assert event is None
    assert errors == ["Etkinlik bulunamadı."]


def test_other_events_remain_unchanged(event_db):
    """Bir etkinlik yayınlanınca diğer etkinliğin durumu bozulmaz."""

    db, add_event, _ = event_db
    first_id = add_event("Birinci Etkinlik")
    second_id = add_event("İkinci Etkinlik")

    ok, _, _ = publish_event(db, first_id)

    assert ok is True
    assert get_event(db, first_id)["status"] == "published"
    assert get_event(db, second_id)["status"] == "draft"


@pytest.mark.parametrize("bad_id", [None, 0, -1, "1", True])
def test_invalid_event_id_is_rejected(event_db, bad_id):
    """Geçersiz etkinlik kimliği kabul edilmez."""

    db, _, _ = event_db

    ok, event, errors = publish_event(db, bad_id)

    assert ok is False
    assert event is None
    assert errors == ["Geçersiz etkinlik kimliği."]
