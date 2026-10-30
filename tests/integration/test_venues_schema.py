"""venues tablosu şema testleri (TG-40, BR-2.1)."""

import sqlite3

import pytest

from app.core.db import get_db, init_db


def _insert(db, name="Salon A", address="Beyazıt, İstanbul", capacity=100):
    return db.execute(
        "INSERT INTO venues (name, address, capacity) VALUES (?, ?, ?)",
        (name, address, capacity),
    )


def test_venues_table_exists_with_expected_columns(app):
    with app.app_context():
        columns = [r["name"] for r in get_db().execute("PRAGMA table_info(venues)")]
    assert columns == ["id", "name", "address", "capacity"]


def test_venue_can_be_saved_and_read_back(app):
    with app.app_context():
        db = get_db()
        _insert(db)
        db.commit()
        row = db.execute("SELECT * FROM venues WHERE name = 'Salon A'").fetchone()
    assert row["id"] == 1
    assert row["address"] == "Beyazıt, İstanbul"
    assert row["capacity"] == 100


def test_venue_ids_are_unique_and_incrementing(app):
    with app.app_context():
        db = get_db()
        first = _insert(db, name="Salon A").lastrowid
        second = _insert(db, name="Salon B").lastrowid
    assert first != second


def test_venue_persists_across_connections(app):
    with app.app_context():
        db = get_db()
        _insert(db)
        db.commit()
    with app.app_context():
        count = get_db().execute("SELECT COUNT(*) FROM venues").fetchone()[0]
    assert count == 1


def test_duplicate_venue_name_rejected(app):
    with app.app_context():
        db = get_db()
        _insert(db)
        with pytest.raises(sqlite3.IntegrityError):
            _insert(db)


@pytest.mark.parametrize("capacity", [0, -5])
def test_non_positive_capacity_rejected(app, capacity):
    with app.app_context():
        with pytest.raises(sqlite3.IntegrityError):
            _insert(get_db(), capacity=capacity)


@pytest.mark.parametrize("field", ["name", "address", "capacity"])
def test_required_fields_cannot_be_null(app, field):
    values = {"name": "Salon A", "address": "Adres", "capacity": 10}
    values[field] = None
    with app.app_context():
        with pytest.raises(sqlite3.IntegrityError):
            _insert(get_db(), **values)


def test_other_tables_still_created(app):
    with app.app_context():
        tables = {
            r["name"]
            for r in get_db().execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    assert {"users", "tickets", "venues"} <= tables


def test_reinitializing_db_keeps_existing_venues(app):
    """init-db tekrar çalıştırıldığında admin'in tanımladığı salonlar silinmemeli."""
    with app.app_context():
        db = get_db()
        _insert(db)
        db.commit()
        init_db()
        count = get_db().execute("SELECT COUNT(*) FROM venues").fetchone()[0]
    assert count == 1
