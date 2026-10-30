"""tickets.event_id -> events.id FK'sinin temiz ve eski veritabanlarında oluştuğunu doğrular (TG-117)."""

import sqlite3

import pytest

from app.core.db import get_db, init_db

# FK eklenmeden önceki (main'deki) tickets şeması.
OLD_TICKETS_DDL = """
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'reserved',
    qr_code TEXT UNIQUE,
    created_at TEXT NOT NULL
);
"""


def _fk_targets(db):
    return {(r["from"], r["table"], r["to"]) for r in db.execute("PRAGMA foreign_key_list(tickets)")}


def _make_legacy_db(db):
    """Eski şemayı (events yok, FK'siz tickets) birebir kurar."""
    db.executescript(
        "DROP TABLE IF EXISTS tickets; DROP TABLE IF EXISTS events;" + OLD_TICKETS_DDL
    )


def test_fresh_db_has_tickets_event_fk(app):
    with app.app_context():
        assert ("event_id", "events", "id") in _fk_targets(get_db())


def test_legacy_db_gets_tickets_event_fk_and_keeps_tickets(app):
    with app.app_context():
        db = get_db()
        _make_legacy_db(db)
        db.execute("INSERT INTO venues (id, name, address, capacity) VALUES (1, 'Salon A', 'A', 100)")
        db.execute("INSERT INTO users (id, email, password_hash, role) VALUES (1, 'o@e.com', 'x', 'organizer')")
        db.commit()
        # Eski DB'de events yok; bilet kaydı henüz yok -> migrasyon sorunsuz olmalı.
        init_db()
        db = get_db()
        assert ("event_id", "events", "id") in _fk_targets(db)
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO tickets (event_id, user_id, created_at) VALUES (999, 1, 'now')")


def test_legacy_tickets_with_valid_events_are_preserved(app):
    with app.app_context():
        db = get_db()
        _make_legacy_db(db)
        db.executescript(
            "INSERT OR IGNORE INTO venues (id, name, address, capacity) VALUES (1, 'Salon A', 'A', 100);"
            "INSERT OR IGNORE INTO users (id, email, password_hash, role) VALUES (1, 'o@e.com', 'x', 'organizer');"
        )
        init_db()  # events tablosu oluşur, FK eklenir
        db = get_db()
        db.execute(
            "INSERT INTO events (id, title, category, venue_id, start_time, end_time, capacity, price, organizer_id)"
            " VALUES (1, 'T', 'C', 1, 's', 'e', 10, 0, 1)"
        )
        db.execute("INSERT INTO tickets (event_id, user_id, status, created_at) VALUES (1, 1, 'paid', 'now')")
        db.commit()
        init_db()  # tekrar çalışınca bilet silinmemeli
        assert get_db().execute("SELECT COUNT(*) FROM tickets").fetchone()[0] == 1


def test_legacy_orphan_tickets_fail_with_clear_error_and_are_not_lost(app):
    with app.app_context():
        db = get_db()
        _make_legacy_db(db)
        db.execute("INSERT INTO tickets (event_id, user_id, created_at) VALUES (42, 1, 'now')")
        db.commit()
        with pytest.raises(RuntimeError, match="tickets"):
            init_db()
        count = get_db().execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        assert count == 1
