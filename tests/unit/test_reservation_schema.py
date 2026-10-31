"""reservations ve reservation_seats şema testleri (TG-123).

Test tasarımı: Tablo oluşturma, UNIQUE kısıtları ve CHECK kısıtları.
Bitti ölçütü: Şema hatasız yükleniyor ve kısıtlar doğrulanıyor.
"""
import sqlite3

import pytest

from app import create_app
from app.core.db import get_db, init_db


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        init_db()
    return app


def test_schema_loads_reservations_and_reservation_seats_tables(app):
    """Şema yüklendiğinde reservations ve reservation_seats tabloları var olmalıdır."""
    with app.app_context():
        db = get_db()
        tables = [
            row["name"]
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        assert "reservations" in tables
        assert "reservation_seats" in tables


def test_reservation_idempotency_key_must_be_unique(app):
    """Aynı idempotency_key ile iki rezervasyon oluşturulamaz (UNIQUE kısıtı)."""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO payments (amount, card_last4, success, message, seats, created_at) "
            "VALUES (100, '4242', 1, 'OK', '[\"A1\"]', '2026-01-01T10:00:00')"
        )
        payment_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        sql = (
            "INSERT INTO reservations "
            "(payment_id, event_id, idempotency_key, ticket_code, status, created_at) "
            "VALUES (?, 1, 'key-123', 'TCK-001', 'confirmed', '2026-01-01T10:00:00')"
        )
        db.execute(sql, (payment_id,))

        with pytest.raises(sqlite3.IntegrityError):
            sql_duplicate = (
                "INSERT INTO reservations "
                "(payment_id, event_id, idempotency_key, ticket_code, status, created_at) "
                "VALUES (?, 1, 'key-123', 'TCK-002', 'confirmed', '2026-01-01T10:00:00')"
            )
            db.execute(sql_duplicate, (payment_id,))


def test_same_seat_cannot_be_reserved_twice_for_same_event(app):
    """Aynı etkinlik için aynı koltuk kodu iki kez rezerve edilemez (UNIQUE kısıtı)."""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO payments (amount, card_last4, success, message, seats, created_at) "
            "VALUES (100, '4242', 1, 'OK', '[\"A1\"]', '2026-01-01T10:00:00')"
        )
        payment_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        sql_res1 = (
            "INSERT INTO reservations (payment_id, event_id, ticket_code, status, created_at) "
            "VALUES (?, 1, 'TCK-001', 'confirmed', '2026-01-01T10:00:00')"
        )
        db.execute(sql_res1, (payment_id,))
        res_id_1 = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        db.execute(
            "INSERT INTO reservation_seats (reservation_id, event_id, seat_code, created_at) "
            "VALUES (?, 1, 'A1', '2026-01-01T10:00:00')",
            (res_id_1,),
        )

        sql_res2 = (
            "INSERT INTO reservations (payment_id, event_id, ticket_code, status, created_at) "
            "VALUES (?, 1, 'TCK-002', 'confirmed', '2026-01-01T10:01:00')"
        )
        db.execute(sql_res2, (payment_id,))
        res_id_2 = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO reservation_seats (reservation_id, event_id, seat_code, created_at) "
                "VALUES (?, 1, 'A1', '2026-01-01T10:01:00')",
                (res_id_2,),
            )


def test_invalid_reservation_status_is_rejected_by_check_constraint(app):
    """Geçersiz rezervasyon durumu CHECK kısıtı ile reddedilir."""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO payments (amount, card_last4, success, message, seats, created_at) "
            "VALUES (100, '4242', 1, 'OK', '[\"A1\"]', '2026-01-01T10:00:00')"
        )
        payment_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO reservations (payment_id, event_id, status, created_at) "
                "VALUES (?, 1, 'invalid_status', '2026-01-01T10:00:00')",
                (payment_id,),
            )
