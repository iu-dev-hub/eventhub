"""Taslak etkinlik servisi birim testleri (TG-118; BR-1.5, BR-2.2, BR-2.3)."""

import sqlite3

import pytest

from app.accounts import services as accounts_services
from app.core.db import get_db
from app.events.services import (
    EventPermissionError,
    create_draft_event,
    get_event,
    is_approved_organizer,
    list_events_by_organizer,
)

ARGS = ("Seminer", "Eğitim", "Salon A", "2026-12-01T10:00", "2026-12-01T12:00", "50", "100")

# TG-117 main'e birleştirildiğinde init_db() gerçek events tablosunu oluşturur ve
# aşağıdaki IF NOT EXISTS ifadeleri devreye girmeden doğrudan gerçek şema kullanılır.
# TG-117 öncesi CI çalışmasında ise TG-117 ile birebir aynı şema kullanılır.
_EVENTS_DDL = """
CREATE TABLE IF NOT EXISTS events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT    NOT NULL,
    category     TEXT    NOT NULL,
    venue_id     INTEGER NOT NULL,
    start_time   TEXT    NOT NULL,
    end_time     TEXT    NOT NULL,
    capacity     INTEGER NOT NULL CHECK (capacity > 0),
    price        REAL    NOT NULL DEFAULT 0 CHECK (price >= 0),
    status       TEXT    NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published')),
    organizer_id INTEGER NOT NULL,
    FOREIGN KEY (venue_id) REFERENCES venues(id),
    FOREIGN KEY (organizer_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_events_organizer_id ON events(organizer_id);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
"""


@pytest.fixture
def db(app):
    with app.app_context():
        db = get_db()
        db.executescript(_EVENTS_DDL)
        db.execute("INSERT INTO venues (id, name, address, capacity) VALUES (1,'Salon A','A',100)")
        db.execute(
            "INSERT INTO users (id, email, password_hash, role) "
            "VALUES (1, 'o@e.com', 'x', 'organizer')"
        )
        db.commit()
        yield db


def approve(db, user_id=1):
    db.execute("ALTER TABLE users ADD COLUMN organizer_approved BOOLEAN NOT NULL DEFAULT 0")
    db.execute("UPDATE users SET organizer_approved = 1 WHERE id = ?", (user_id,))
    db.commit()


def test_events_table_matches_tg117_schema(db):
    """Testteki events tablosunun TG-117 şemasıyla birebir uyumlu olduğunu doğrular."""
    cols = [r["name"] for r in db.execute("PRAGMA table_info(events)").fetchall()]
    assert cols == [
        "id",
        "title",
        "category",
        "venue_id",
        "start_time",
        "end_time",
        "capacity",
        "price",
        "status",
        "organizer_id",
    ]
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO events (title, category, venue_id, start_time, end_time, "
            "capacity, price, status, organizer_id) "
            "VALUES ('T', 'K', 1, '2026-12-01T10:00', '2026-12-01T12:00', 10, 0, 'cancelled', 1)"
        )


def test_without_approval_mechanism_access_is_closed(db):
    """Accounts'ta onay sütunu yokken organizer rolü bile yetki vermez (güvenli varsayılan)."""
    assert is_approved_organizer(1, db) is False
    with pytest.raises(EventPermissionError):
        create_draft_event(db, 1, *ARGS)
    assert db.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0


def test_delegates_to_accounts_approval_service_when_available(db, monkeypatch):
    """Accounts kalıcı onay servisi eklendiğinde yetki kontrolü doğrudan ona delege edilir."""
    calls = []

    def fake_accounts_approval(user_id, passed_db=None):
        calls.append(user_id)
        return user_id == 1

    monkeypatch.setattr(
        accounts_services, "is_approved_organizer", fake_accounts_approval, raising=False
    )
    assert is_approved_organizer(1, db) is True
    assert is_approved_organizer(2, db) is False
    assert calls == [1, 2]


def test_unapproved_organizer_is_denied(db):
    db.execute("ALTER TABLE users ADD COLUMN organizer_approved BOOLEAN NOT NULL DEFAULT 0")
    db.commit()
    with pytest.raises(EventPermissionError):
        create_draft_event(db, 1, *ARGS)


@pytest.mark.parametrize("bad_id", [None, 0, "1", True, 999])
def test_invalid_user_ids_are_denied(db, bad_id):
    approve(db)
    assert is_approved_organizer(bad_id, db) is False


def test_approved_organizer_saves_draft_and_reads_it_back(db):
    approve(db)
    ok, event, errors = create_draft_event(db, 1, *ARGS)
    assert ok and errors == []
    assert event["status"] == "draft"
    assert event == get_event(db, event["id"])
    assert [e["id"] for e in list_events_by_organizer(db, 1)] == [event["id"]]


def test_missing_required_fields_are_rejected(db):
    approve(db)
    ok, event, errors = create_draft_event(db, 1, "", *ARGS[1:])
    assert not ok and event is None
    assert errors == ["Lütfen tüm zorunlu alanları doldurun."]


def test_venue_capacity_limit_and_unknown_venue(db):
    approve(db)
    ok, event, errors = create_draft_event(db, 1, *ARGS[:5], "101", "100")
    assert not ok and event is None
    assert errors == ["Etkinlik kapasitesi (101), salon kapasitesini (100) aşamaz."]

    ok2, event2, errors2 = create_draft_event(db, 1, "Seminer", "Eğitim", "Yok", *ARGS[3:])
    assert not ok2 and event2 is None
    assert errors2 == ["Seçilen salon bulunamadı."]


@pytest.mark.parametrize(
    "capacity, price",
    [("abc", "10"), ("5.5", "10"), ("10", "abc"), ("10", "nan"), ("10", "inf")],
)
def test_non_numeric_values_are_rejected(db, capacity, price):
    approve(db)
    ok, event, errors = create_draft_event(db, 1, *ARGS[:5], capacity, price)
    assert not ok and event is None and errors


@pytest.mark.parametrize("capacity, price", [("0", "10"), ("-3", "10"), ("10", "-1")])
def test_out_of_range_values_are_rejected(db, capacity, price):
    approve(db)
    ok, _, errors = create_draft_event(db, 1, *ARGS[:5], capacity, price)
    assert not ok and errors


def test_invalid_or_reversed_dates_are_rejected(db):
    approve(db)
    ok, _, errors = create_draft_event(db, 1, "T", "K", "Salon A", "yarın", "sonra", "5", "0")
    assert not ok and errors == ["Başlangıç ve bitiş zamanı geçerli bir tarih olmalıdır."]

    ok2, _, errors2 = create_draft_event(
        db, 1, "T", "K", "Salon A", "2026-12-01T12:00", "2026-12-01T10:00", "5", "0"
    )
    assert not ok2 and errors2 == ["Bitiş zamanı başlangıç zamanından sonra olmalıdır."]


def test_database_error_is_handled_and_rolled_back(db):
    approve(db)

    class FailingDb:
        """INSERT sırasında sqlite hatası veren sahte bağlantı."""

        def __init__(self, real):
            self.real = real
            self.rolled_back = False

        def execute(self, sql, *params):
            if sql.lstrip().upper().startswith("INSERT"):
                raise sqlite3.OperationalError("disk I/O error")
            return self.real.execute(sql, *params)

        def commit(self):
            self.real.commit()

        def rollback(self):
            self.rolled_back = True
            self.real.rollback()

    failing = FailingDb(db)
    ok, event, errors = create_draft_event(failing, 1, *ARGS)
    assert not ok and event is None
    assert errors == ["Etkinlik kaydedilirken bir veritabanı hatası oluştu. Lütfen tekrar deneyin."]
    assert failing.rolled_back
    assert db.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0


def test_get_event_missing_or_invalid_id_returns_none(db):
    assert get_event(db, 12345) is None
    assert get_event(db, "1") is None
    assert get_event(db, True) is None
