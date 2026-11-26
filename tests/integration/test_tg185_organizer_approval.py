"""Independent QA checks for the TG-185 SQLite approval contract."""

import sqlite3
from contextlib import closing

import pytest

from app import create_app
from app.accounts.services import is_approved_organizer, register_user
from app.core.db import get_db, init_db


def assert_approval_column(db):
    columns = [
        row for row in db.execute("PRAGMA table_info(users)") if row["name"] == "organizer_approved"
    ]
    assert len(columns) == 1
    column = columns[0]
    assert (column["type"], column["notnull"], column["dflt_value"]) == ("BOOLEAN", 1, "0")


def test_fresh_schema_enforces_approval_default_and_not_null(app):
    with app.app_context():
        db = get_db()
        assert_approval_column(db)
        user = register_user("new-organizer@example.com", "Password123", role="organizer")
        approval = db.execute(
            "SELECT organizer_approved FROM users WHERE id = ?", (user["id"],)
        ).fetchone()
        assert approval[0] == 0
        with pytest.raises(sqlite3.IntegrityError, match="NOT NULL constraint failed"):
            db.execute("UPDATE users SET organizer_approved = NULL WHERE id = ?", (user["id"],))


def test_migrated_approval_and_event_survive_reopen_and_reinitialization(tmp_path):
    database = tmp_path / "legacy.sqlite"
    legacy_app = create_app({"TESTING": True, "DATABASE": str(database)})
    with legacy_app.app_context():
        init_db()
        db = get_db()
        db.execute("ALTER TABLE users DROP COLUMN organizer_approved")
        db.execute(
            "INSERT INTO users (id, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (42, "legacy@example.com", "original-hash", "organizer"),
        )
        db.execute(
            "INSERT INTO venues (id, name, address, capacity) VALUES (1, 'Salon', 'Adres', 100)"
        )
        db.execute(
            "INSERT INTO events (id, title, category, venue_id, start_time, end_time, "
            "capacity, organizer_id) VALUES (1, 'Etkinlik', 'Eğitim', 1, "
            "'2027-01-01T10:00', '2027-01-01T12:00', 50, 42)"
        )
        db.commit()
        original_user = dict(db.execute("SELECT * FROM users WHERE id = 42").fetchone())
        original_event = dict(db.execute("SELECT * FROM events WHERE id = 1").fetchone())

    with legacy_app.app_context():
        init_db()
        db = get_db()
        assert_approval_column(db)
        assert is_approved_organizer(42, db) is False
        db.execute("UPDATE users SET organizer_approved = 1 WHERE id = 42")
        db.commit()

    restarted_app = create_app({"TESTING": True, "DATABASE": str(database)})
    with restarted_app.app_context():
        init_db()

    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        assert_approval_column(db)
        assert is_approved_organizer(42, db) is True
        assert not db.in_transaction
        assert dict(db.execute("SELECT * FROM users WHERE id = 42").fetchone()) == {
            **original_user,
            "organizer_approved": 1,
        }
        assert dict(db.execute("SELECT * FROM events WHERE id = 1").fetchone()) == original_event
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
