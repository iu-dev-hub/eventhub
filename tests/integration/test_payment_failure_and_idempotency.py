"""Entegrasyon testleri: Ödeme hataları, zaman aşımı ve idempotency senaryoları (TG-139)."""
from datetime import datetime, timedelta

import pytest

from app import create_app
from app.core.db import get_db, init_db
from app.payments import services

VALID_CARD = "4242424242424242"
NO_BALANCE_CARD = "1111111111110000"
INVALID_CARD = "1234abcd5678"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "LOG_FILE", tmp_path / "payment_logs.json")
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        init_db()
    return app.test_client()


def test_payment_failure_does_not_create_reservation_and_preserves_lock(client):
    """Yetersiz bakiye durumunda rezervasyon ve bilet oluşmaz; koltuk kilitli kalır."""
    client.post("/api/seats/lock", json={"seats": ["H1"]})

    pay_resp = client.post(
        "/api/payment/pay",
        json={"cardNumber": NO_BALANCE_CARD, "amount": 100, "seats": ["H1"]},
    )
    assert pay_resp.status_code == 200
    data = pay_resp.get_json()
    assert data["success"] is False
    assert data["message"] == "Yetersiz bakiye"

    with client.application.app_context():
        db = get_db()
        # Rezervasyon oluşmamalı
        res_count = db.execute(
            "SELECT COUNT(*) AS c FROM reservations"
        ).fetchone()["c"]
        assert res_count == 0

        # Koltuk hâlâ kilitli kalmalı (kullanıcı geçerli kartla tekrar deneyebilsin)
        seat = db.execute(
            "SELECT status FROM seats WHERE seat_code = 'H1'"
        ).fetchone()
        assert seat["status"] == "locked"


def test_payment_timeout_lock_released_and_payment_rejected(client):
    """Zaman aşımına uğramış kilitte ödeme isteği geldiğinde ödeme reddedilir."""
    start = datetime(2026, 6, 1, 14, 0, 0)
    with client.application.app_context():
        # Koltuk saat 14:00'te kilitlendi
        services.lock_seats(["J1"], event_id=1, now=start)

        # Saat 14:11'de (11 dk sonra) ödeme yapılmak istendiğinde kilit süresi dolmuştur
        result = services.process_payment(
            VALID_CARD,
            100,
            ["J1"],
            event_id=1,
            now=start + timedelta(minutes=11),
        )
        assert result["success"] is False
        assert result["message"] == "Koltuk kilitli değil"

        db = get_db()
        # Rezervasyon oluşmamalı
        count = db.execute("SELECT COUNT(*) AS c FROM reservations").fetchone()["c"]
        assert count == 0

        # Koltuk serbest kalmalı
        seat = db.execute(
            "SELECT status FROM seats WHERE seat_code = 'J1'"
        ).fetchone()
        assert seat["status"] == "available"


def test_repeated_payment_requests_with_idempotency_key(client):
    """Aynı idempotencyKey ile tekrarlanan ödeme isteklerinde mükerrer kayıt oluşmaz."""
    client.post("/api/seats/lock", json={"seats": ["K1", "K2"]})

    payload = {
        "cardNumber": VALID_CARD,
        "amount": 250,
        "seats": ["K1", "K2"],
        "eventId": 1,
        "userId": 7,
        "idempotencyKey": "idem-merve-task-139",
    }

    # İlk ödeme isteği
    resp1 = client.post("/api/payment/pay", json=payload)
    assert resp1.status_code == 200
    data1 = resp1.get_json()
    assert data1["success"] is True
    res_id = data1["reservationId"]
    ticket_code = data1["ticketCode"]

    # Tekrarlanan istek
    resp2 = client.post("/api/payment/pay", json=payload)
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2["success"] is True
    assert data2.get("idempotent") is True
    assert data2["reservationId"] == res_id
    assert data2["ticketCode"] == ticket_code

    with client.application.app_context():
        db = get_db()
        res_count = db.execute(
            "SELECT COUNT(*) AS c FROM reservations WHERE idempotency_key = ?",
            ("idem-merve-task-139",),
        ).fetchone()["c"]
        assert res_count == 1

        seat_count = db.execute(
            "SELECT COUNT(*) AS c FROM reservation_seats WHERE reservation_id = ?",
            (res_id,),
        ).fetchone()["c"]
        assert seat_count == 2


def test_data_integrity_between_payments_and_reservations(client):
    """Ödemeler tablosu ile rezervasyonlar tablosu arasındaki veri bütünlüğü kontrol edilir."""
    # Başarısız deneme
    client.post("/api/seats/lock", json={"seats": ["L1"]})
    client.post(
        "/api/payment/pay",
        json={"cardNumber": INVALID_CARD, "amount": 100, "seats": ["L1"]},
    )

    # Başarılı deneme
    client.post(
        "/api/payment/pay",
        json={"cardNumber": VALID_CARD, "amount": 100, "seats": ["L1"]},
    )

    with client.application.app_context():
        db = get_db()
        # Toplam 2 ödeme denemesi kaydedilmiş olmalı (1 başarısız, 1 başarılı)
        all_payments = db.execute(
            "SELECT id, success FROM payments ORDER BY id"
        ).fetchall()
        assert len(all_payments) == 2
        assert all_payments[0]["success"] == 0
        assert all_payments[1]["success"] == 1

        # Sadece başarılı olan ödeme için tek bir rezervasyon kaydı olmalı
        reservations = db.execute("SELECT * FROM reservations").fetchall()
        assert len(reservations) == 1
        assert reservations[0]["payment_id"] == all_payments[1]["id"]
