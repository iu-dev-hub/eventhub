"""Ödeme sayfası ve arayüz API entegrasyon testleri (TG-55, Task #134, #135).

Test tasarımı: Arayüz yükleme, form alanları ve backend API entegrasyonu.
"""
import pytest

from app import create_app
from app.core.db import init_db
from app.payments import services


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "LOG_FILE", tmp_path / "payment_logs.json")
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        init_db()
    return app.test_client()


def test_payment_page_renders_successfully(client):
    """GET /payments/ sayfası 200 döner ve temel başlıkları içerir."""
    resp = client.get("/payments/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Ödeme" in html
    assert "Sipariş Özeti" in html
    assert "Kart Bilgileri" in html
    assert "Ödemeyi Tamamla" in html


def test_payment_page_contains_required_form_elements(client):
    """Ödeme formunda kart sahibi, numara, son kullanma ve CVV alanları bulunur."""
    resp = client.get("/payments/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'id="card-name"' in html
    assert 'id="card-number"' in html
    assert 'id="card-expiry"' in html
    assert 'id="card-cvv"' in html
    assert 'id="payment-form"' in html
    assert 'id="submit-btn"' in html


def test_payment_page_contains_feedback_and_alert_containers(client):
    """Ödeme sayfasında başarı, hata ve bildirim alanları bulunur."""
    resp = client.get("/payments/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'id="alert-container"' in html
    assert 'id="payment-success-card"' in html
    assert 'id="no-seats-warning"' in html


def test_payment_page_api_integration_flow(client):
    """Frontend tarafından kullanılan API akışı (lock -> pay -> status) doğrulanır."""
    seats = ["B1", "B2"]

    # 1. Kilitleme isteği
    lock_resp = client.post("/api/seats/lock", json={"seats": seats})
    assert lock_resp.status_code == 200
    assert lock_resp.get_json()["success"] is True

    # 2. Ödeme tamamlama isteği
    pay_resp = client.post("/api/payment/pay", json={
        "cardNumber": "4242424242424242",
        "amount": 300,
        "seats": seats
    })
    assert pay_resp.status_code == 200
    pay_data = pay_resp.get_json()
    assert pay_data["success"] is True
    assert "ticketId" in pay_data

    # 3. Durum kontrolü: koltuklar 'sold' olmalı
    status_resp = client.get("/api/seats/status?seats=B1,B2")
    assert status_resp.status_code == 200
    seats_data = status_resp.get_json()["seats"]
    assert all(s["status"] == "sold" for s in seats_data)


def test_payment_page_handles_failed_payment_flow(client):
    """Yetersiz bakiye durumunda API başarısız yanıt döner ve koltuk kilitli kalır."""
    seats = ["C1"]
    client.post("/api/seats/lock", json={"seats": seats})

    pay_resp = client.post("/api/payment/pay", json={
        "cardNumber": "0000000000000000",
        "amount": 150,
        "seats": seats
    })
    assert pay_resp.status_code == 200
    data = pay_resp.get_json()
    assert data["success"] is False
    assert data["message"] == "Yetersiz bakiye"
