"""Entegrasyon testleri: Ödeme güvenliği, sanitization ve rate limiting (TG-145)."""
import pytest

from app import create_app
from app.core.db import get_db, init_db
from app.payments import services

VALID_CARD = "4242424242424242"
FAIL_CARD = "1111111111110000"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "LOG_FILE", tmp_path / "payment_logs.json")
    # Reset in-memory rate limiter between tests
    services._FAILED_ATTEMPTS.clear()
    app = create_app({"TESTING": True, "ENABLE_RATE_LIMIT": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        init_db()
    return app.test_client()


def test_card_number_sanitization(client):
    """Boşluklu veya tireli kart numaraları temizlenerek geçerli kabul edilir."""
    client.post("/api/seats/lock", json={"seats": ["S1"]})
    resp1 = client.post(
        "/api/payment/pay",
        json={"cardNumber": "4242 4242 4242 4242", "amount": 100, "seats": ["S1"]},
    )
    assert resp1.status_code == 200
    assert resp1.get_json()["success"] is True

    client.post("/api/seats/lock", json={"seats": ["S2"]})
    resp2 = client.post(
        "/api/payment/pay",
        json={"cardNumber": "4242-4242-4242-4242", "amount": 100, "seats": ["S2"]},
    )
    assert resp2.status_code == 200
    assert resp2.get_json()["success"] is True


def test_rate_limiting_blocks_brute_force_attempts(client):
    """Art arda 5 başarısız denemeden sonraki denemeler rate limiter tarafından engellenir."""
    client.post("/api/seats/lock", json={"seats": ["S3"]})

    # 5 ardışık başarısız deneme yap
    for _ in range(5):
        resp = client.post(
            "/api/payment/pay",
            json={"cardNumber": FAIL_CARD, "amount": 100, "seats": ["S3"]},
        )
        assert resp.status_code == 200
        assert resp.get_json()["success"] is False

    # 6. deneme rate limit engeline takılmalı
    blocked_resp = client.post(
        "/api/payment/pay",
        json={"cardNumber": VALID_CARD, "amount": 100, "seats": ["S3"]},
    )
    assert blocked_resp.status_code == 200
    data = blocked_resp.get_json()
    assert data["success"] is False
    assert "Çok fazla başarısız deneme" in data["message"]


def test_rate_limit_resets_after_success(client):
    """Başarılı bir ödeme yapıldığında rate limit sayacı sıfırlanır."""
    client.post("/api/seats/lock", json={"seats": ["S4", "S5"]})

    # 2 başarısız deneme
    for _ in range(2):
        client.post(
            "/api/payment/pay",
            json={"cardNumber": FAIL_CARD, "amount": 100, "seats": ["S4"]},
        )

    # 1 başarılı deneme
    success_resp = client.post(
        "/api/payment/pay",
        json={"cardNumber": VALID_CARD, "amount": 100, "seats": ["S4"]},
    )
    assert success_resp.get_json()["success"] is True

    # Sayaç sıfırlandığı için yeni hatalı denemeler yapılabilir ve hemen kilitlenmez
    for _ in range(4):
        resp = client.post(
            "/api/payment/pay",
            json={"cardNumber": FAIL_CARD, "amount": 100, "seats": ["S5"]},
        )
        assert "Çok fazla başarısız deneme" not in resp.get_json().get("message", "")


def test_security_full_card_not_logged_or_exposed(client):
    """Kart numarası veritabanında veya yanıtlarda asla tam olarak açıkta saklanmaz."""
    client.post("/api/seats/lock", json={"seats": ["S6"]})
    resp = client.post(
        "/api/payment/pay",
        json={"cardNumber": VALID_CARD, "amount": 100, "seats": ["S6"]},
    )
    data = resp.get_json()
    assert VALID_CARD not in str(data)

    with client.application.app_context():
        db = get_db()
        row = db.execute("SELECT * FROM payments ORDER BY id DESC LIMIT 1").fetchone()
        assert row["card_last4"] == "4242"
        assert VALID_CARD not in str(dict(row))
