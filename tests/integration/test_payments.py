"""Koltuk kilitleme ve ödeme API'si testleri."""

import json
from datetime import datetime, timedelta

import pytest

from app import create_app
from app.payments import services


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Testler gerçek log dosyasını kirletmesin diye geçici klasör kullanılır
    monkeypatch.setattr(services, "LOG_FILE", tmp_path / "payment_logs.json")
    services.reset_state()
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_lock_succeeds_for_free_seats(client):
    response = client.post("/api/seats/lock", json={"seats": ["A1", "A2"]})
    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_lock_fails_when_seat_already_locked(client):
    client.post("/api/seats/lock", json={"seats": ["A1"]})
    response = client.post("/api/seats/lock", json={"seats": ["A1", "A3"]})
    assert response.status_code == 409


def test_lock_rejects_empty_seats(client):
    response = client.post("/api/seats/lock", json={"seats": []})
    assert response.status_code == 400


def test_lock_expires_exactly_after_ten_minutes():
    services.reset_state()
    start = datetime(2026, 1, 1, 12, 0, 0)
    services.lock_seats(["A1"], now=start)

    # 9. dakikada hâlâ kilitli
    ok, _, _ = services.lock_seats(["A1"], now=start + timedelta(minutes=9))
    assert ok is False

    # 10. dakikada kilit düşer
    ok, _, _ = services.lock_seats(["A1"], now=start + timedelta(minutes=10))
    assert ok is True


def test_payment_with_4242_card_succeeds_and_seats_become_sold(client):
    client.post("/api/seats/lock", json={"seats": ["A1"]})
    response = client.post(
        "/api/payment/pay",
        json={
            "cardNumber": "4242424242424242",
            "amount": 100,
            "seats": ["A1"],
        },
    )
    assert response.status_code == 200
    assert response.get_json() == {"success": True, "ticketId": "T12345"}

    # Satılan koltuk tekrar kilitlenemez
    again = client.post("/api/seats/lock", json={"seats": ["A1"]})
    assert again.status_code == 409


def test_payment_with_0000_card_fails_with_insufficient_balance(client):
    response = client.post(
        "/api/payment/pay",
        json={
            "cardNumber": "1111111111110000",
            "amount": 100,
            "seats": ["B1"],
        },
    )
    assert response.status_code == 200
    assert response.get_json() == {"success": False, "message": "Yetersiz bakiye"}


def test_every_payment_attempt_is_logged(client):
    client.post(
        "/api/payment/pay",
        json={
            "cardNumber": "4242424242424242",
            "amount": 100,
            "seats": ["A1"],
        },
    )
    client.post(
        "/api/payment/pay",
        json={
            "cardNumber": "1111111111110000",
            "amount": 100,
            "seats": ["B1"],
        },
    )
    logs = json.loads(services.LOG_FILE.read_text(encoding="utf-8"))
    assert len(logs) == 2
    assert logs[0]["success"] is True
    assert logs[1]["mesaj"] == "Yetersiz bakiye"


def test_payment_fails_when_card_is_shorter_than_16_digits(client):
    response = client.post(
        "/api/payment/pay",
        json={
            "cardNumber": "4242",
            "amount": 100,
            "seats": ["A1"],
        },
    )
    assert response.get_json() == {"success": False, "message": "Geçersiz kart"}


def test_payment_fails_when_card_has_15_digits(client):
    # Sınır değer: 15 hane reddedilir
    response = client.post(
        "/api/payment/pay",
        json={
            "cardNumber": "424242424242424",
            "amount": 100,
            "seats": ["A1"],
        },
    )
    assert response.get_json()["success"] is False


def test_payment_fails_when_card_is_longer_than_16_digits(client):
    # Sınır değer: 17 hane reddedilir
    response = client.post(
        "/api/payment/pay",
        json={
            "cardNumber": "42424242424242424",
            "amount": 100,
            "seats": ["A1"],
        },
    )
    assert response.get_json()["success"] is False


def test_payment_fails_when_card_contains_letters(client):
    response = client.post(
        "/api/payment/pay",
        json={
            "cardNumber": "abc4242",
            "amount": 100,
            "seats": ["A1"],
        },
    )
    assert response.get_json()["success"] is False


def test_payment_succeeds_when_card_has_exactly_16_digits(client):
    # Sınır değer: tam 16 hane kabul edilir
    response = client.post(
        "/api/payment/pay",
        json={
            "cardNumber": "4242424242424242",
            "amount": 100,
            "seats": ["A1"],
        },
    )
    assert response.get_json()["success"] is True


def test_payment_fails_when_seat_is_already_sold(client):
    client.post("/api/seats/lock", json={"seats": ["A1"]})
    body = {"cardNumber": "4242424242424242", "amount": 100, "seats": ["A1"]}
    first = client.post("/api/payment/pay", json=body)
    second = client.post("/api/payment/pay", json=body)

    assert first.get_json()["success"] is True
    assert second.get_json() == {"success": False, "message": "Koltuk zaten satılmış"}
