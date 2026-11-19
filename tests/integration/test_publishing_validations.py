"""TG-173: Yayınlama öncesi zorunlu alan, kapasite ve zaman çakışması testleri."""

import sqlite3
from contextlib import closing

import pytest

from app.core.db import get_db
from app.events.services import get_event, publish_event


@pytest.fixture
def publishing_db(app):
    """Her testte bağımsız SQLite veritabanı ve onaylı organizatör hazırla."""
    with app.app_context():
        db = get_db()

        # Accounts onay alanı varsa yeniden ekleme; gerçek şemayı değiştirme.
        columns = {row["name"] for row in db.execute("PRAGMA table_info(users)")}
        if "organizer_approved" not in columns:
            db.execute("ALTER TABLE users ADD COLUMN organizer_approved INTEGER NOT NULL DEFAULT 0")

        organizer_id = db.execute(
            """INSERT INTO users (email, password_hash, role, organizer_approved)
            VALUES (?, ?, ?, ?)""",
            ("tg173@example.com", "testhash", "organizer", 1),
        ).lastrowid
        first_venue = db.execute(
            "INSERT INTO venues (name, address, capacity) VALUES (?, ?, ?)",
            ("TG-173 Ana Salon", "Iğdır", 100),
        ).lastrowid
        second_venue = db.execute(
            "INSERT INTO venues (name, address, capacity) VALUES (?, ?, ?)",
            ("TG-173 Küçük Salon", "Iğdır", 50),
        ).lastrowid
        db.commit()

        def add_event(
            *,
            title="Yapay Zekâ Semineri",
            category="Eğitim",
            venue_id=None,
            start_time="2026-12-01T10:00",
            end_time="2026-12-01T12:00",
            capacity=40,
            price=0,
            status="draft",
        ):
            if venue_id is None:
                venue_id = first_venue
            cursor = db.execute(
                """
                INSERT INTO events (
                    title, category, venue_id, start_time, end_time,
                    capacity, price, status, organizer_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    category,
                    venue_id,
                    start_time,
                    end_time,
                    capacity,
                    price,
                    status,
                    organizer_id,
                ),
            )
            db.commit()
            return cursor.lastrowid

        yield {
            "db": db,
            "db_path": app.config["DATABASE"],
            "organizer_id": organizer_id,
            "first_venue": first_venue,
            "second_venue": second_venue,
            "add_event": add_event,
        }


def _publish(context, event_id):
    return publish_event(context["db"], event_id, context["organizer_id"])


def _assert_still_draft(context, event_id):
    """Hem mevcut bağlantıda hem yeni SQLite bağlantısında draft kaldığını kontrol et."""
    assert get_event(context["db"], event_id)["status"] == "draft"
    with closing(sqlite3.connect(context["db_path"])) as separate_db:
        row = separate_db.execute("SELECT status FROM events WHERE id = ?", (event_id,)).fetchone()
        assert row is not None
        assert row[0] == "draft"


def test_valid_event_can_be_published(publishing_db):
    """BR-2.2: Geçerli ücretsiz etkinlik yayınlanır ve kayıt kalıcıdır."""
    event_id = publishing_db["add_event"]()

    ok, event, errors = _publish(publishing_db, event_id)

    assert ok is True
    assert errors == []
    assert event["status"] == "published"
    with closing(sqlite3.connect(publishing_db["db_path"])) as separate_db:
        row = separate_db.execute("SELECT status FROM events WHERE id = ?", (event_id,)).fetchone()
        assert row[0] == "published"


@pytest.mark.parametrize(
    "field,value",
    [
        ("title", ""),
        ("title", "   "),
        ("category", ""),
        ("category", "  "),
    ],
)
def test_missing_required_text_prevents_publishing(publishing_db, field, value):
    """BR-2.2: Boş başlık veya kategori ile yayınlamaya izin verilmez."""
    event_id = publishing_db["add_event"]()
    publishing_db["db"].execute(f"UPDATE events SET {field} = ? WHERE id = ?", (value, event_id))
    publishing_db["db"].commit()

    ok, event, errors = _publish(publishing_db, event_id)

    assert ok is False
    assert event is None
    assert errors
    _assert_still_draft(publishing_db, event_id)


@pytest.mark.parametrize(
    "field,value",
    [
        ("start_time", ""),
        ("end_time", ""),
        ("start_time", "gecersiz-tarih"),
        ("end_time", "gecersiz-tarih"),
    ],
)
def test_missing_or_invalid_datetime_prevents_publishing(publishing_db, field, value):
    """BR-2.2: Eksik veya yanlış tarih verisi yayınlamayı engeller."""
    event_id = publishing_db["add_event"]()
    publishing_db["db"].execute(f"UPDATE events SET {field} = ? WHERE id = ?", (value, event_id))
    publishing_db["db"].commit()

    ok, event, errors = _publish(publishing_db, event_id)

    assert ok is False
    assert event is None
    assert any("zaman" in msg.lower() for msg in errors)
    _assert_still_draft(publishing_db, event_id)


@pytest.mark.parametrize(
    "start_time,end_time",
    [
        ("2026-12-01T12:00", "2026-12-01T10:00"),
        ("2026-12-01T10:00", "2026-12-01T10:00"),
    ],
)
def test_end_time_must_be_after_start_time(publishing_db, start_time, end_time):
    """Bitiş başlangıçtan önce veya ona eşit olamaz."""
    event_id = publishing_db["add_event"](start_time=start_time, end_time=end_time)

    ok, event, errors = _publish(publishing_db, event_id)

    assert ok is False
    assert event is None
    assert errors
    _assert_still_draft(publishing_db, event_id)


def test_incompatible_datetime_timezones_are_rejected(publishing_db):
    """Saat dilimli ve saat dilimsiz tarihler kontrolsüz karşılaştırılmamalı."""
    event_id = publishing_db["add_event"](
        start_time="2026-12-01T10:00+03:00",
        end_time="2026-12-01T12:00",
    )

    ok, event, errors = _publish(publishing_db, event_id)

    assert ok is False
    assert event is None
    assert errors
    _assert_still_draft(publishing_db, event_id)


def test_capacity_over_venue_limit_prevents_publishing(publishing_db):
    """BR-2.3: Taslak oluşturulduktan sonra kapasite yükseltilse bile reddedilir."""
    event_id = publishing_db["add_event"](capacity=40)
    publishing_db["db"].execute("UPDATE events SET capacity = 101 WHERE id = ?", (event_id,))
    publishing_db["db"].commit()

    ok, event, errors = _publish(publishing_db, event_id)

    assert ok is False
    assert event is None
    assert any("kapasite" in msg.lower() for msg in errors)
    _assert_still_draft(publishing_db, event_id)


def test_capacity_equal_to_venue_limit_is_valid(publishing_db):
    """BR-2.3: Salon kapasitesine eşit etkinlik kapasitesi kabul edilir."""
    event_id = publishing_db["add_event"](capacity=100, price=25)

    ok, event, errors = _publish(publishing_db, event_id)

    assert ok is True
    assert errors == []
    assert event["status"] == "published"


def test_deleted_or_unknown_venue_prevents_publishing(publishing_db):
    """BR-2.2: Eski ve tutarsız bir salon referansı güvenli şekilde reddedilir."""
    event_id = publishing_db["add_event"]()
    db = publishing_db["db"]
    # Sadece izole test DB'sinde bozuk/eskimiş referans durumu oluştur.
    db.execute("PRAGMA foreign_keys = OFF")
    try:
        db.execute("UPDATE events SET venue_id = 99999 WHERE id = ?", (event_id,))
        db.commit()
    finally:
        db.execute("PRAGMA foreign_keys = ON")

    ok, event, errors = _publish(publishing_db, event_id)

    assert ok is False
    assert event is None
    assert errors
    _assert_still_draft(publishing_db, event_id)


@pytest.mark.parametrize(
    "candidate_start,candidate_end",
    [
        ("2026-12-01T11:00", "2026-12-01T13:00"),  # Kısmi çakışma: sağ
        ("2026-12-01T09:00", "2026-12-01T11:00"),  # Kısmi çakışma: sol
        ("2026-12-01T09:00", "2026-12-01T13:00"),  # Tam kapsama
        ("2026-12-01T10:30", "2026-12-01T11:30"),  # İçeride kalma
        ("2026-12-01T10:00", "2026-12-01T12:00"),  # Tam aynı saat
    ],
)
def test_overlapping_published_event_blocks_publishing(
    publishing_db, candidate_start, candidate_end
):
    """BR-2.4: Aynı salonda herhangi bir saat çakışması varsa engelle."""
    publishing_db["add_event"](status="published")
    event_id = publishing_db["add_event"](start_time=candidate_start, end_time=candidate_end)

    ok, event, errors = _publish(publishing_db, event_id)

    assert ok is False
    assert event is None
    assert any("salon" in msg.lower() for msg in errors)
    _assert_still_draft(publishing_db, event_id)


@pytest.mark.parametrize(
    "candidate_start,candidate_end",
    [
        ("2026-12-01T08:00", "2026-12-01T10:00"),
        ("2026-12-01T12:00", "2026-12-01T13:00"),
    ],
)
def test_adjacent_time_slots_can_be_published(publishing_db, candidate_start, candidate_end):
    """BR-2.4 sınır testi: Bir etkinlik bittiği anda diğeri başlayabilir."""
    publishing_db["add_event"](status="published")
    event_id = publishing_db["add_event"](start_time=candidate_start, end_time=candidate_end)

    ok, event, errors = _publish(publishing_db, event_id)

    assert ok is True
    assert errors == []
    assert event["status"] == "published"


def test_same_time_in_different_venue_is_allowed(publishing_db):
    """BR-2.4: Farklı salonların aynı saati kullanması engellenmez."""
    publishing_db["add_event"](status="published")
    event_id = publishing_db["add_event"](venue_id=publishing_db["second_venue"], capacity=50)

    ok, event, errors = _publish(publishing_db, event_id)

    assert ok is True
    assert errors == []
    assert event["status"] == "published"


def test_another_draft_does_not_reserve_the_venue(publishing_db):
    """İki taslak çakışabilir; birisi yayınlanınca ikincisi engellenir."""
    first_id = publishing_db["add_event"]()
    second_id = publishing_db["add_event"]()

    ok_first, first, errors_first = _publish(publishing_db, first_id)
    ok_second, second, errors_second = _publish(publishing_db, second_id)

    assert ok_first is True
    assert errors_first == []
    assert first["status"] == "published"
    assert ok_second is False
    assert second is None
    assert errors_second
    _assert_still_draft(publishing_db, second_id)
