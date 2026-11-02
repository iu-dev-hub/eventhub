"""Entegrasyon testleri: API üzerinden rezervasyon ve bilet oluşturma (TG-124)."""

import pytest

from app import create_app
from app.core.db import get_db, init_db
from app.payments import services

VALID_CARD = "4242424242424242"
FAIL_CARD = "1111111111110000"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "LOG_FILE", tmp_path / "payment_logs.json")
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        init_db()
    return app.test_client()


def test_api_pay_creates_reservation_and_ticket_details(client):
    # 1. Koltuk kilitle
    lock_resp = client.post("/api/seats/lock", json={"seats": ["E1", "E2"]})
    assert lock_resp.status_code == 200

    # 2. Ödeme yap
    pay_resp = client.post(
        "/api/payment/pay",
        json={
            "cardNumber": VALID_CARD,
            "amount": 200,
            "seats": ["E1", "E2"],
            "eventId": 1,
            "userId": 10,
            "idempotencyKey": "idem-pay-001",
        },
    )
    assert pay_resp.status_code == 200
    data = pay_resp.get_json()
    assert data["success"] is True
    assert "ticketId" in data
    assert "ticketCode" in data
    assert "reservationId" in data
    assert data["seats"] == ["E1", "E2"]

    # 3. DB doğrula
    with client.application.app_context():
        db = get_db()
        row = db.execute(
            "SELECT * FROM reservations WHERE id = ?", (data["reservationId"],)
        ).fetchone()
        assert row is not None
        assert row["status"] == "confirmed"
        assert row["idempotency_key"] == "idem-pay-001"


def test_api_pay_idempotency_returns_same_reservation(client):
    client.post("/api/seats/lock", json={"seats": ["F1"]})

    payload = {
        "cardNumber": VALID_CARD,
        "amount": 100,
        "seats": ["F1"],
        "eventId": 1,
        "idempotencyKey": "idem-same-key",
    }
    first_resp = client.post("/api/payment/pay", json=payload)
    assert first_resp.status_code == 200
    first_data = first_resp.get_json()

    # İkinci istek
    second_resp = client.post("/api/payment/pay", json=payload)
    assert second_resp.status_code == 200
    second_data = second_resp.get_json()

    assert second_data["success"] is True
    assert second_data.get("idempotent") is True
    assert second_data["reservationId"] == first_data["reservationId"]
    assert second_data["ticketCode"] == first_data["ticketCode"]
