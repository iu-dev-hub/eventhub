"""Entegrasyon testleri: GET /api/tickets/my-tickets uç noktası (TG-143)."""
import json

import pytest

from app import create_app
from app.core.db import get_db, init_db
from app.payments import services


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "LOG_FILE", tmp_path / "payment_logs.json")
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        init_db()
    return app.test_client()


def test_api_my_tickets_returns_empty_list_when_no_tickets(client):
    """Kayıtlı bilet olmadığında API boş bilet listesiyle 200 döner."""
    resp = client.get("/api/tickets/my-tickets?user_id=888")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["tickets"] == []


def test_api_my_tickets_returns_tickets_with_full_details(client):
    """Kullanıcının biletleri API yanıtında doğru JSON şemasıyla döner."""
    with client.application.app_context():
        db = get_db()
        p = db.execute(
            "INSERT INTO payments (amount, card_last4, success, message, seats, created_at) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (300, "4242", 1, "Ödeme başarılı", json.dumps(["M1", "M2", "M3"])),
        ).lastrowid
        db.execute(
            "INSERT INTO reservations (payment_id, event_id, user_id, ticket_code, "
            "status, created_at) VALUES (?, 2, 77, 'TKT-API-77', 'confirmed', datetime('now'))",
            (p,),
        )
        db.commit()

    resp = client.get("/api/tickets/my-tickets?user_id=77")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert len(data["tickets"]) == 1
    ticket = data["tickets"][0]
    assert ticket["ticket_code"] == "TKT-API-77"
    assert ticket["status"] == "confirmed"
    assert ticket["amount"] == 300
    assert ticket["seats"] == ["M1", "M2", "M3"]
    assert ticket["event_id"] == 2
