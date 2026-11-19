"""Etkinlik yayınlama servisi birim testleri (TG-174, PB-04; BR-1.5, BR-2.2, BR-2.3, BR-2.4)."""

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
            "INSERT INTO venues (id, name, address, capacity) "
            "VALUES (2, 'Küçük Salon', 'Adres', 30)"
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

    assert "yetki" in str(exc_info.value).lower() or "kendi" in str(exc_info.value).lower()
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
    assert any("zaten yayınlanmış" in e.lower() for e in errors)


def test_publish_event_cancelled_cannot_be_published(db):
    """İptal edilmiş veya taslak dışı etkinlik yayınlanamaz."""
    event_id = _insert_event(db, organizer_id=1, status="draft")
    db.execute("UPDATE events SET status = 'published' WHERE id = ?", (event_id,))
    db.commit()

    ok, event, errors = publish_event(db, event_id, organizer_id=1)

    assert ok is False
    assert event is None
    assert any("taslak" in e.lower() or "zaten yayınlanmış" in e.lower() for e in errors)


def test_publish_event_capacity_exceeds_venue_capacity(db):
    """BR-2.3: Etkinlik kapasitesi salon kapasitesini aşıyorsa yayınlanamaz."""
    # Salon 2 kapasitesi 30, etkinlik kapasitesi 50
    event_id = _insert_event(db, organizer_id=1, venue_id=2, capacity=50)

    ok, event, errors = publish_event(db, event_id, organizer_id=1)

    assert ok is False
    assert event is None
    assert any("salon kapasitesini (30) aşamaz" in e for e in errors)


def test_publish_event_invalid_capacity_or_price(db, monkeypatch):
    """BR-2.2: Kapasite < 1 veya negatif fiyat kontrolü."""
    event_id = _insert_event(db, organizer_id=1, capacity=10, price=10.0)

    original_get_event = get_event

    def mock_get_invalid_capacity(db_conn, eid):
        ev = original_get_event(db_conn, eid)
        if ev and ev["id"] == event_id:
            ev["capacity"] = 0
        return ev

    monkeypatch.setattr("app.events.services.get_event", mock_get_invalid_capacity)
    ok1, _, err1 = publish_event(db, event_id, organizer_id=1)
    assert ok1 is False
    assert any("en az 1" in e for e in err1)

    def mock_get_invalid_price(db_conn, eid):
        ev = original_get_event(db_conn, eid)
        if ev and ev["id"] == event_id:
            ev["price"] = -5.0
        return ev

    monkeypatch.setattr("app.events.services.get_event", mock_get_invalid_price)
    ok2, _, err2 = publish_event(db, event_id, organizer_id=1)
    assert ok2 is False
    assert any("negatif olamaz" in e for e in err2)


def test_publish_event_invalid_dates_end_before_start(db):
    """BR-2.2: Bitiş zamanı başlangıç zamanından sonra olmalıdır."""
    event_id = _insert_event(
        db,
        organizer_id=1,
        start_time="2026-12-01T20:00",
        end_time="2026-12-01T18:00",
    )

    ok, event, errors = publish_event(db, event_id, organizer_id=1)

    assert ok is False
    assert event is None
    assert any("başlangıç zamanından sonra" in e for e in errors)


def test_publish_event_missing_venue(db):
    """Etkinliğin salonu silinmişse veya bulunamıyorsa yayınlanamaz."""
    db.execute(
        "INSERT INTO venues (id, name, address, capacity) VALUES (3, 'Geçici Salon', 'Adres', 50)"
    )
    event_id = _insert_event(db, organizer_id=1, venue_id=3)
    db.commit()

    # Salonu sil (FK kısıtını geçici olarak kapatıp salonu siliyoruz)
    db.execute("PRAGMA foreign_keys = OFF")
    db.execute("DELETE FROM venues WHERE id = 3")
    db.execute("PRAGMA foreign_keys = ON")
    db.commit()

    ok, event, errors = publish_event(db, event_id, organizer_id=1)

    assert ok is False
    assert event is None
    assert any("salon bulunamadı" in e.lower() for e in errors)


def test_publish_event_time_conflict_in_same_venue(db):
    """BR-2.4: Aynı salonda zamanı çakışan iki etkinlik yayınlanamaz."""
    # Önceden yayınlanmış etkinlik: Salon 1, 14:00 - 17:00
    _insert_event(
        db,
        title="Mevcut Konser",
        venue_id=1,
        start_time="2026-12-01T14:00",
        end_time="2026-12-01T17:00",
        status="published",
        organizer_id=2,
    )

    # Çakışan taslak: Salon 1, 16:00 - 18:00
    draft_id = _insert_event(
        db,
        title="Yeni Tiyatro",
        venue_id=1,
        start_time="2026-12-01T16:00",
        end_time="2026-12-01T18:00",
        status="draft",
        organizer_id=1,
    )

    ok, event, errors = publish_event(db, draft_id, organizer_id=1)

    assert ok is False
    assert event is None
    assert any("çakışan" in e.lower() for e in errors)
    assert get_event(db, draft_id)["status"] == "draft"


def test_publish_event_no_conflict_when_adjacent_times(db):
    """BR-2.4: Biri biter bitmez diğeri başlayan etkinlikler çakışmaz."""
    _insert_event(
        db,
        venue_id=1,
        start_time="2026-12-01T10:00",
        end_time="2026-12-01T12:00",
        status="published",
    )

    draft_id = _insert_event(
        db,
        venue_id=1,
        start_time="2026-12-01T12:00",
        end_time="2026-12-01T14:00",
        status="draft",
        organizer_id=1,
    )

    ok, event, errors = publish_event(db, draft_id, organizer_id=1)

    assert ok is True
    assert errors == []
    assert event["status"] == "published"


def test_publish_event_no_conflict_in_different_venues(db):
    """BR-2.4: Farklı salonlardaki etkinlikler aynı saatte olsa bile çakışmaz."""
    _insert_event(
        db,
        venue_id=1,
        start_time="2026-12-01T14:00",
        end_time="2026-12-01T17:00",
        status="published",
    )

    draft_id = _insert_event(
        db,
        venue_id=2,
        start_time="2026-12-01T14:00",
        end_time="2026-12-01T17:00",
        capacity=20,
        status="draft",
        organizer_id=1,
    )

    ok, event, errors = publish_event(db, draft_id, organizer_id=1)

    assert ok is True
    assert errors == []
    assert event["status"] == "published"


def test_publish_event_no_conflict_with_other_drafts(db):
    """BR-2.4: Henüz yayınlanmamış taslak etkinlikler salonu bloke etmez."""
    _insert_event(
        db,
        venue_id=1,
        start_time="2026-12-01T14:00",
        end_time="2026-12-01T17:00",
        status="draft",
        organizer_id=2,
    )

    draft_id = _insert_event(
        db,
        venue_id=1,
        start_time="2026-12-01T14:00",
        end_time="2026-12-01T17:00",
        status="draft",
        organizer_id=1,
    )

    ok, event, errors = publish_event(db, draft_id, organizer_id=1)

    assert ok is True
    assert errors == []
    assert event["status"] == "published"
