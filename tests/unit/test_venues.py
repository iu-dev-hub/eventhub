"""Salon oluşturma servisi birim testleri (TG-41, BR-2.1)."""

import pytest

from app.core.db import get_db
from app.events.services import create_venue


def _count(db):
    return db.execute("SELECT COUNT(*) FROM venues").fetchone()[0]


def test_valid_venue_is_saved(app):
    with app.app_context():
        db = get_db()
        ok, venue, errors = create_venue(db, " Salon A ", "Beyazıt", "80")
        assert ok and errors == []
        assert venue == {"id": 1, "name": "Salon A", "address": "Beyazıt", "capacity": 80}
        row = db.execute("SELECT * FROM venues").fetchone()
        assert (row["name"], row["address"], row["capacity"]) == ("Salon A", "Beyazıt", 80)


@pytest.mark.parametrize(
    "name,address,capacity",
    [
        ("", "Adres", "10"),
        ("Salon", "", "10"),
        ("Salon", "Adres", ""),
        (None, "Adres", "10"),
        ("   ", "Adres", "10"),
        ("Salon", "Adres", None),
    ],
)
def test_missing_fields_rejected(app, name, address, capacity):
    with app.app_context():
        db = get_db()
        ok, venue, errors = create_venue(db, name, address, capacity)
        assert not ok and venue is None and errors
        assert _count(db) == 0


@pytest.mark.parametrize("capacity", ["0", "-3", "abc", "1.5"])
def test_invalid_capacity_rejected(app, capacity):
    with app.app_context():
        db = get_db()
        ok, _, errors = create_venue(db, "Salon", "Adres", capacity)
        assert not ok and errors
        assert _count(db) == 0


def test_duplicate_name_rejected(app):
    with app.app_context():
        db = get_db()
        create_venue(db, "Salon", "Adres", "10")
        ok, _, errors = create_venue(db, "Salon", "Başka", "20")
        assert not ok and errors == ["Bu isimde bir salon zaten mevcut."]
        assert _count(db) == 1
