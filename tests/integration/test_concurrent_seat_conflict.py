"""Entegrasyon testleri: Eş zamanlı koltuk kilitleme ve çakışma senaryoları (TG-138)."""
from datetime import datetime, timedelta

import pytest

from app import create_app
from app.core.db import init_db
from app.payments import services

VALID_CARD = "4242424242424242"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "LOG_FILE", tmp_path / "payment_logs.json")
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        init_db()
    return app.test_client()


def test_concurrent_seat_lock_conflict_returns_409(client):
    """Aynı koltuğu kilitlemek isteyen iki kullanıcıdan ilki başarılı olur, ikincisi 409 alır."""
    # Kullanıcı 1 koltuğu kilitler
    r1 = client.post("/api/seats/lock", json={"seats": ["A1", "A2"]})
    assert r1.status_code == 200
    assert r1.get_json()["success"] is True

    # Kullanıcı 2 aynı koltuğu kilitlemeyi dener
    r2 = client.post("/api/seats/lock", json={"seats": ["A2", "A3"]})
    assert r2.status_code == 409
    data2 = r2.get_json()
    assert data2["success"] is False
    assert "A2" in data2["seats"]

    # All-or-nothing kuralı gereği Kullanıcı 2 talebindeki boş A3 koltuğu kilitlenmemelidir
    r3 = client.post("/api/seats/lock", json={"seats": ["A3"]})
    assert r3.status_code == 200
    assert r3.get_json()["success"] is True


def test_expired_lock_allows_new_user_to_lock(client):
    """Kilit süresi (10 dk) dolduğunda koltuk başka bir kullanıcı tarafından kilitlenebilir."""
    start = datetime(2026, 5, 1, 10, 0, 0)

    with client.application.app_context():
        # Kullanıcı 1 kilitleme yapar
        ok, _, _ = services.lock_seats(["B1"], event_id=1, now=start)
        assert ok is True

        # 5. dakikada Kullanıcı 2 kilitleyemez (hâlâ kilitli)
        ok2, taken, _ = services.lock_seats(
            ["B1"], event_id=1, now=start + timedelta(minutes=5)
        )
        assert ok2 is False
        assert taken == ["B1"]

        # 10. dakikada kilit süresi dolar; Kullanıcı 2 kilitleyebilir
        ok3, _, expires = services.lock_seats(
            ["B1"], event_id=1, now=start + timedelta(minutes=10)
        )
        assert ok3 is True
        assert expires == start + timedelta(minutes=20)


def test_concurrent_payment_on_sold_seat_prevented(client):
    """Bir koltuk satıldıktan sonra başka kullanıcı tarafından tekrar kilitlenemez ve ödenemez."""
    # Koltuk kilitlenir ve ödeme tamamlanır
    client.post("/api/seats/lock", json={"seats": ["C1"]})
    pay_resp = client.post(
        "/api/payment/pay",
        json={"cardNumber": VALID_CARD, "amount": 100, "seats": ["C1"]},
    )
    assert pay_resp.status_code == 200
    assert pay_resp.get_json()["success"] is True

    # Başka bir kullanıcı aynı koltuğu kilitlemeyi dener: 409 Conflict
    lock_again = client.post("/api/seats/lock", json={"seats": ["C1"]})
    assert lock_again.status_code == 409

    # Başka bir kullanıcı doğrudan ödeme yapmayı dener: Satılmış uyarısı
    pay_again = client.post(
        "/api/payment/pay",
        json={"cardNumber": VALID_CARD, "amount": 100, "seats": ["C1"]},
    )
    assert pay_again.status_code == 200
    data = pay_again.get_json()
    assert data["success"] is False
    assert "zaten satılmış" in data["message"]


def test_payment_without_locking_is_rejected(client):
    """Kilitlenmemiş koltuk için ödeme yapılamaz."""
    res = client.post(
        "/api/payment/pay",
        json={"cardNumber": VALID_CARD, "amount": 100, "seats": ["D1"]},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is False
    assert "Koltuk kilitli değil" in data["message"]


def test_multi_seat_partial_lock_conflict_behavior(client):
    """Birden fazla koltuk seçildiğinde en az birinde çakışma varsa hiçbiri kilitlenmez."""
    # Koltuk X1 kilitlenir
    r1 = client.post("/api/seats/lock", json={"seats": ["X1"]})
    assert r1.status_code == 200

    # Başka bir kullanıcı X1 ve X2'yi aynı anda kilitlemek ister
    r2 = client.post("/api/seats/lock", json={"seats": ["X1", "X2"]})
    assert r2.status_code == 409
    assert r2.get_json()["seats"] == ["X1"]

    # X2 kilitlenmemiş olmalı ve tek başına kilitlenebilmelidir
    r3 = client.post("/api/seats/lock", json={"seats": ["X2"]})
    assert r3.status_code == 200
    assert r3.get_json()["success"] is True
