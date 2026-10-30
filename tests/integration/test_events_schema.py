"""events tablosu şema testleri (TG-117, PB-08)."""

import sqlite3

import pytest

from app.core.db import get_db, init_db


def _seed_refs(db):
    db.execute("INSERT INTO venues (id, name, address, capacity) VALUES (1, 'Salon A', 'Adres', 100)")
    db.execute("INSERT INTO users (id, email, password_hash, role) VALUES (1, 'org@example.com', 'x', 'organizer')")


def _insert_event(db, **overrides):
    values = {
        "title": "Yazılım Semineri",
        "category": "Eğitim",
        "venue_id": 1,
        "start_time": "2026-12-01T10:00",
        "end_time": "2026-12-01T12:00",
        "capacity": 50,
        "price": 100,
        "organizer_id": 1,
    }
    values.update(overrides)
    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    return db.execute(
        f"INSERT INTO events ({columns}) VALUES ({placeholders})", tuple(values.values())
    )


def test_foreign_keys_pragma_is_enabled(app):
    with app.app_context():
        assert get_db().execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_events_table_exists_with_expected_columns(app):
    with app.app_context():
        columns = [r["name"] for r in get_db().execute("PRAGMA table_info(events)")]
    assert columns == [
        "id", "title", "category", "venue_id", "start_time", "end_time",
        "capacity", "price", "status", "organizer_id",
    ]


def test_event_defaults_to_draft_status(app):
    with app.app_context():
        db = get_db()
        _seed_refs(db)
        event_id = _insert_event(db).lastrowid
        status = db.execute("SELECT status FROM events WHERE id = ?", (event_id,)).fetchone()[0]
    assert status == "draft"


def test_published_status_is_accepted(app):
    with app.app_context():
        db = get_db()
        _seed_refs(db)
        _insert_event(db, status="published")


def test_invalid_status_rejected(app):
    with app.app_context():
        db = get_db()
        _seed_refs(db)
        with pytest.raises(sqlite3.IntegrityError):
            _insert_event(db, status="archived")


def test_unknown_organizer_rejected(app):
    with app.app_context():
        db = get_db()
        _seed_refs(db)
        with pytest.raises(sqlite3.IntegrityError):
            _insert_event(db, organizer_id=999)


def test_unknown_venue_rejected(app):
    with app.app_context():
        db = get_db()
        _seed_refs(db)
        with pytest.raises(sqlite3.IntegrityError):
            _insert_event(db, venue_id=999)


@pytest.mark.parametrize("capacity", [0, -1])
def test_non_positive_capacity_rejected(app, capacity):
    with app.app_context():
        db = get_db()
        _seed_refs(db)
        with pytest.raises(sqlite3.IntegrityError):
            _insert_event(db, capacity=capacity)


def test_negative_price_rejected(app):
    with app.app_context():
        db = get_db()
        _seed_refs(db)
        with pytest.raises(sqlite3.IntegrityError):
            _insert_event(db, price=-1)


def test_zero_price_is_accepted_as_free_event(app):
    with app.app_context():
        db = get_db()
        _seed_refs(db)
        _insert_event(db, price=0)


@pytest.mark.parametrize(
    "field", ["title", "category", "venue_id", "start_time", "end_time", "capacity", "organizer_id"]
)
def test_required_fields_cannot_be_null(app, field):
    with app.app_context():
        db = get_db()
        _seed_refs(db)
        with pytest.raises(sqlite3.IntegrityError):
            _insert_event(db, **{field: None})


def test_ticket_for_unknown_event_rejected(app):
    with app.app_context():
        db = get_db()
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO tickets (event_id, user_id, created_at) VALUES (999, 1, '2026-03-02')"
            )


def test_reinitializing_db_with_existing_events_does_not_fail(app):
    """init-db tekrar çalıştırıldığında events -> users FK'si DROP TABLE users'ı bozmamalı."""
    with app.app_context():
        db = get_db()
        _seed_refs(db)
        _insert_event(db)
        db.commit()
        init_db()
        count = get_db().execute("SELECT COUNT(*) FROM events").fetchone()[0]
    assert count == 1
