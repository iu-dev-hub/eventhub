"""Birim testleri: get_user_tickets servisi (TG-143)."""
import json

from app import create_app
from app.core.db import get_db, init_db
from app.payments import services


def setup_db(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "LOG_FILE", tmp_path / "payment_logs.json")
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        init_db()
    return app


def test_get_user_tickets_empty(tmp_path, monkeypatch):
    """Bileti olmayan kullanıcı için boş liste döner."""
    app = setup_db(tmp_path, monkeypatch)
    with app.app_context():
        tickets = services.get_user_tickets(user_id=123)
        assert tickets == []


def test_get_user_tickets_returns_all_tickets_for_user(tmp_path, monkeypatch):
    """Kullanıcının tüm bilet ve rezervasyon kayıtlarını doğru detaylarla döner."""
    app = setup_db(tmp_path, monkeypatch)
    with app.app_context():
        db = get_db()
        cursor = db.execute(
            "INSERT INTO payments (amount, card_last4, success, message, seats, created_at) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (200, "4242", 1, "Ödeme başarılı", json.dumps(["F1", "F2"])),
        )
        pid = cursor.lastrowid
        db.execute(
            "INSERT INTO reservations (payment_id, event_id, user_id, ticket_code, "
            "status, created_at) VALUES (?, ?, ?, ?, 'confirmed', datetime('now'))",
            (pid, 1, 55, "TKT-55-AAA"),
        )
        db.commit()

        tickets = services.get_user_tickets(user_id=55)
        assert len(tickets) == 1
        t = tickets[0]
        assert t["ticket_code"] == "TKT-55-AAA"
        assert t["status"] == "confirmed"
        assert t["amount"] == 200
        assert t["seats"] == ["F1", "F2"]
        assert t["event_id"] == 1


def test_get_user_tickets_filters_out_other_users(tmp_path, monkeypatch):
    """Başka kullanıcılara ait biletler sorgu sonucuna dahil edilmez."""
    app = setup_db(tmp_path, monkeypatch)
    with app.app_context():
        db = get_db()
        p1 = db.execute(
            "INSERT INTO payments (amount, card_last4, success, message, seats, created_at) "
            "VALUES (100, '4242', 1, 'OK', '[\"A1\"]', datetime('now'))"
        ).lastrowid
        db.execute(
            "INSERT INTO reservations (payment_id, event_id, user_id, ticket_code, "
            "status, created_at) VALUES (?, 1, 1, 'TKT-USER-1', 'confirmed', datetime('now'))",
            (p1,),
        )

        p2 = db.execute(
            "INSERT INTO payments (amount, card_last4, success, message, seats, created_at) "
            "VALUES (100, '4242', 1, 'OK', '[\"B1\"]', datetime('now'))"
        ).lastrowid
        db.execute(
            "INSERT INTO reservations (payment_id, event_id, user_id, ticket_code, "
            "status, created_at) VALUES (?, 1, 2, 'TKT-USER-2', 'confirmed', datetime('now'))",
            (p2,),
        )
        db.commit()

        t1 = services.get_user_tickets(user_id=1)
        assert len(t1) == 1
        assert t1[0]["ticket_code"] == "TKT-USER-1"

        t2 = services.get_user_tickets(user_id=2)
        assert len(t2) == 1
        assert t2[0]["ticket_code"] == "TKT-USER-2"
