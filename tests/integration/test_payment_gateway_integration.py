"""Entegrasyon testleri: Ödeme sağlayıcı adaptörünün API ile entegrasyonu (TG-149)."""
import pytest

from app import create_app
from app.core.db import init_db
from app.payments import services

VALID_CARD = "4242424242424242"
FAIL_CARD = "1111111111110000"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "LOG_FILE", tmp_path / "payment_logs.json")
    services._FAILED_ATTEMPTS.clear()
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        init_db()
    return app.test_client()


def test_api_payment_integration_with_gateway_success(client):
    """Sağlayıcı üzerinden onaylanan ödeme koltuğu satıldı yapar ve bilet döner."""
    client.post("/api/seats/lock", json={"seats": ["GW1"]})
    resp = client.post(
        "/api/payment/pay",
        json={"cardNumber": VALID_CARD, "amount": 250, "seats": ["GW1"]},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "ticketId" in data
    assert "reservationId" in data


def test_api_payment_integration_with_gateway_insufficient_funds(client):
    """Sağlayıcı bakiye yetersiz yanıtı verdiğinde API kullanıcıya uygun hata döner."""
    client.post("/api/seats/lock", json={"seats": ["GW2"]})
    resp = client.post(
        "/api/payment/pay",
        json={"cardNumber": FAIL_CARD, "amount": 250, "seats": ["GW2"]},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is False
    assert data["message"] == "Yetersiz bakiye"
