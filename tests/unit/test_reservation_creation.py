"""Birim testleri: Başarılı ödeme sonrası rezervasyon ve bilet oluşturma (TG-124)."""

from app import create_app
from app.core.db import get_db, init_db
from app.payments import services

VALID_CARD = "4242424242424242"
FAIL_CARD = "1111111111110000"


def setup_db(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "LOG_FILE", tmp_path / "payment_logs.json")
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        init_db()
    return app


def test_process_payment_success_creates_reservation_and_ticket_and_seats(tmp_path, monkeypatch):
    app = setup_db(tmp_path, monkeypatch)
    with app.app_context():
        # Koltukları önce kilitle
        ok, _, _ = services.lock_seats(["A1", "A2"], event_id=1)
        assert ok is True

        res = services.process_payment(
            VALID_CARD,
            250,
            ["A1", "A2"],
            event_id=1,
            user_id=42,
            idempotency_key="idemp-key-101",
        )
        assert res["success"] is True
        assert res["reservationId"] is not None
        assert res["ticketCode"].startswith("T")
        assert res["seats"] == ["A1", "A2"]

        db = get_db()
        r = db.execute(
            "SELECT * FROM reservations WHERE id = ?", (res["reservationId"],)
        ).fetchone()
        assert r is not None
        assert r["event_id"] == 1
        assert r["user_id"] == 42
        assert r["idempotency_key"] == "idemp-key-101"
        assert r["ticket_code"] == res["ticketCode"]
        assert r["status"] == "confirmed"

        seats = db.execute(
            "SELECT seat_code FROM reservation_seats WHERE reservation_id = ? ORDER BY seat_code",
            (res["reservationId"],),
        ).fetchall()
        assert [s["seat_code"] for s in seats] == ["A1", "A2"]


def test_process_payment_failure_does_not_create_reservation_or_seats(tmp_path, monkeypatch):
    app = setup_db(tmp_path, monkeypatch)
    with app.app_context():
        services.lock_seats(["B1"], event_id=1)
        res = services.process_payment(FAIL_CARD, 100, ["B1"], event_id=1)
        assert res["success"] is False

        db = get_db()
        res_count = db.execute("SELECT COUNT(*) AS c FROM reservations").fetchone()["c"]
        seats_count = db.execute("SELECT COUNT(*) AS c FROM reservation_seats").fetchone()["c"]
        assert res_count == 0
        assert seats_count == 0


def test_process_payment_idempotency_prevents_duplicate_reservations(tmp_path, monkeypatch):
    app = setup_db(tmp_path, monkeypatch)
    with app.app_context():
        services.lock_seats(["C1"], event_id=1)
        res1 = services.process_payment(
            VALID_CARD, 100, ["C1"], event_id=1, idempotency_key="key-xyz"
        )
        assert res1["success"] is True

        # İkinci çağrıda aynı idempotency_key ile tekrar gönderildiğinde mükerrer oluşturulmaz
        res2 = services.process_payment(
            VALID_CARD, 100, ["C1"], event_id=1, idempotency_key="key-xyz"
        )
        assert res2["success"] is True
        assert res2["idempotent"] is True
        assert res2["reservationId"] == res1["reservationId"]
        assert res2["ticketCode"] == res1["ticketCode"]

        db = get_db()
        count = db.execute("SELECT COUNT(*) AS c FROM reservations").fetchone()["c"]
        assert count == 1


def test_process_payment_transaction_atomicity_on_duplicate_seat(tmp_path, monkeypatch):
    app = setup_db(tmp_path, monkeypatch)
    with app.app_context():
        services.lock_seats(["D1"], event_id=1)
        res1 = services.process_payment(VALID_CARD, 100, ["D1"], event_id=1)
        assert res1["success"] is True

        # D1 zaten satılmış ve rezerve edilmiş durumda. Tekrar ödeme yapılmaya çalışıldığında
        # işlem başarısız olmalı ve yeni rezervasyon eklenmemelidir.
        res2 = services.process_payment(VALID_CARD, 100, ["D1"], event_id=1)
        assert res2["success"] is False
        assert "zaten satılmış" in res2["message"]

        db = get_db()
        count = db.execute("SELECT COUNT(*) AS c FROM reservations").fetchone()["c"]
        assert count == 1
