"""Koltuk kilitleme ve ödeme API'si testleri (SQLite üzerinden)."""

import json
import sqlite3
from datetime import datetime, timedelta

import pytest

from app import create_app
from app.core.db import get_db, init_db
from app.payments import services

VALID_CARD = "4242424242424242"
NO_BALANCE_CARD = "1111111111110000"


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Testler gerçek veritabanını ve log dosyasını kirletmesin
    monkeypatch.setattr(services, "LOG_FILE", tmp_path / "payment_logs.json")
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        init_db()
    return app.test_client()


def lock(client, seats):
    return client.post("/api/seats/lock", json={"seats": seats})


def pay(client, card, seats):
    return client.post("/api/payment/pay", json={"cardNumber": card, "amount": 100, "seats": seats})


# --- Kilitleme ---
def test_lock_succeeds_for_free_seats(client):
    response = lock(client, ["A1", "A2"])
    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_lock_fails_when_seat_already_locked(client):
    lock(client, ["A1"])
    assert lock(client, ["A1", "A3"]).status_code == 409


def test_lock_is_all_or_nothing_when_one_seat_is_taken(client):
    lock(client, ["A1"])
    lock(client, ["A1", "A3"])  # 409 döner
    # A3 kilitlenmemiş olmalı, ayrı bir istekle alınabilir
    assert lock(client, ["A3"]).status_code == 200


def test_lock_rejects_empty_seats(client):
    assert lock(client, []).status_code == 400


def test_lock_expires_exactly_after_ten_minutes(client):
    start = datetime(2026, 1, 1, 12, 0, 0)
    with client.application.app_context():
        services.lock_seats(["A1"], now=start)

        # 9. dakikada hâlâ kilitli
        ok, _, _ = services.lock_seats(["A1"], now=start + timedelta(minutes=9))
        assert ok is False

        # 10. dakikada kilit düşer
        ok, _, _ = services.lock_seats(["A1"], now=start + timedelta(minutes=10))
        assert ok is True


# --- Ödeme ---
def test_payment_with_4242_card_succeeds_and_seats_become_sold(client):
    lock(client, ["A1"])
    response = pay(client, VALID_CARD, ["A1"])
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "ticketId" in data
    assert "reservationId" in data
    # Satılan koltuk tekrar kilitlenemez
    assert lock(client, ["A1"]).status_code == 409


def test_payment_with_0000_card_fails_with_insufficient_balance(client):
    lock(client, ["B1"])
    response = pay(client, NO_BALANCE_CARD, ["B1"])
    assert response.status_code == 200
    assert response.get_json() == {"success": False, "message": "Yetersiz bakiye"}


def test_payment_fails_when_card_is_shorter_than_16_digits(client):
    lock(client, ["A1"])
    assert pay(client, "4242", ["A1"]).get_json() == {
        "success": False,
        "message": "Geçersiz kart",
    }


def test_payment_fails_when_card_has_15_digits(client):
    lock(client, ["A1"])
    assert pay(client, "424242424242424", ["A1"]).get_json()["success"] is False


def test_payment_fails_when_card_has_17_digits(client):
    lock(client, ["A1"])
    assert pay(client, "42424242424242424", ["A1"]).get_json()["success"] is False


def test_payment_fails_when_card_contains_letters(client):
    lock(client, ["A1"])
    assert pay(client, "abc4242", ["A1"]).get_json()["success"] is False


def test_payment_succeeds_when_card_has_exactly_16_digits(client):
    lock(client, ["A1"])
    assert pay(client, VALID_CARD, ["A1"]).get_json()["success"] is True


def test_payment_fails_when_seat_is_already_sold(client):
    lock(client, ["A1"])
    first = pay(client, VALID_CARD, ["A1"])
    second = pay(client, VALID_CARD, ["A1"])
    assert first.get_json()["success"] is True
    assert second.get_json() == {"success": False, "message": "Koltuk zaten satılmış"}


def test_payment_fails_when_seat_is_not_locked(client):
    response = pay(client, VALID_CARD, ["C1"])
    assert response.get_json() == {"success": False, "message": "Koltuk kilitli değil"}


# --- Loglama ---
def test_every_payment_attempt_is_logged(client, tmp_path):
    lock(client, ["A1", "B1"])
    pay(client, VALID_CARD, ["A1"])
    pay(client, NO_BALANCE_CARD, ["B1"])
    logs = json.loads((tmp_path / "payment_logs.json").read_text(encoding="utf-8"))
    assert len(logs) == 2
    assert logs[0]["success"] is True
    assert logs[1]["mesaj"] == "Yetersiz bakiye"


# --- Veritabanı: kalıcılık, güvenlik, kısıtlar ---
def test_data_persists_after_app_restart(client, tmp_path):
    lock(client, ["A1"])
    # Yeni app + aynı veritabanı dosyası = uygulamanın yeniden başlatılması
    app2 = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    assert lock_with(app2, ["A1"]).status_code == 409


def lock_with(app, seats):
    return app.test_client().post("/api/seats/lock", json={"seats": seats})


def test_full_card_number_is_never_stored(client):
    lock(client, ["B1"])
    pay(client, NO_BALANCE_CARD, ["B1"])
    with client.application.app_context():
        row = get_db().execute("SELECT * FROM payments").fetchone()
    assert row["card_last4"] == "0000"
    assert NO_BALANCE_CARD not in str(dict(row))


def test_same_seat_cannot_be_inserted_twice_for_one_event(client):
    with client.application.app_context():
        db = get_db()
        db.execute("INSERT INTO seats (event_id, seat_code) VALUES (1, 'A1')")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO seats (event_id, seat_code) VALUES (1, 'A1')")


def test_invalid_seat_status_is_rejected_by_database(client):
    with client.application.app_context():
        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                "INSERT INTO seats (event_id, seat_code, status) VALUES (1, 'A1', 'broken')"
            )


# --- Koltuk Durumu ve Kilit Açma Uç Noktaları (TG-133) ---

def test_seats_status_endpoint_returns_seat_list(client):
    """GET /api/seats/status tüm koltuk listesini döner."""
    lock(client, ["A1", "A2"])
    resp = client.get("/api/seats/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert isinstance(data["seats"], list)
    codes = [s["seat_code"] for s in data["seats"]]
    assert "A1" in codes
    assert "A2" in codes


def test_seats_status_endpoint_filters_by_query_param(client):
    """GET /api/seats/status?seats=A1 belirli koltuk durumunu döner."""
    lock(client, ["A1", "A2"])
    resp = client.get("/api/seats/status?seats=A1")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert len(data["seats"]) == 1
    assert data["seats"][0]["seat_code"] == "A1"
    assert data["seats"][0]["status"] == "locked"


def test_seats_unlock_endpoint_releases_locked_seats(client):
    """POST /api/seats/unlock kilitli koltukları serbest bırakır."""
    lock(client, ["A1", "A2"])
    resp = client.post("/api/seats/unlock", json={"seats": ["A1"]})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["released"] == ["A1"]

    # Koltuk tekrar kilitlenebilir olmalı
    relock_resp = lock(client, ["A1"])
    assert relock_resp.status_code == 200


def test_seats_unlock_endpoint_fails_when_seats_missing(client):
    """POST /api/seats/unlock eksik veya geçersiz gövdede 400 döner."""
    resp = client.post("/api/seats/unlock", json={})
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_seats_unlock_endpoint_fails_when_no_locked_seats(client):
    """POST /api/seats/unlock kilitli olmayan koltuk için 409 döner."""
    resp = client.post("/api/seats/unlock", json={"seats": ["Z9"]})
    assert resp.status_code == 409
    assert resp.get_json()["success"] is False

