"""Entegrasyon testleri: Biletlerim (My Tickets) sayfası kullanıcı arayüzü (TG-141)."""
import json

import pytest

from app import create_app
from app.core.db import get_db, init_db


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        init_db()
    return app.test_client()


def test_my_tickets_page_renders_successfully(client):
    """Biletlerim sayfası 200 döner ve başlık öğesini içerir."""
    response = client.get("/tickets/my-tickets")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Biletlerim" in html
    assert "id=\"my-tickets-title\"" in html


def test_my_tickets_page_shows_empty_state_when_no_tickets(client):
    """Hiç bilet bulunmadığında kullanıcı dostu boş durum mesajı gösterilir."""
    response = client.get("/tickets/my-tickets?user_id=999")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Henüz kayıtlı biletiniz bulunmuyor" in html
    assert "no-tickets-container" in html
    assert "Etkinlikleri Keşfet" in html


def test_my_tickets_page_displays_tickets_when_reservations_exist(client):
    """Kullanıcının biletleri ve detayları arayüzde kart olarak listelenir."""
    with client.application.app_context():
        db = get_db()
        # Örnek payment
        cursor = db.execute(
            "INSERT INTO payments (amount, card_last4, success, message, seats, created_at) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (150, "4242", 1, "Ödeme başarılı", json.dumps(["A1", "A2"])),
        )
        payment_id = cursor.lastrowid

        # Örnek rezervasyon
        db.execute(
            "INSERT INTO reservations (payment_id, event_id, user_id, ticket_code, status, "
            "created_at) VALUES (?, ?, ?, ?, 'confirmed', datetime('now'))",
            (payment_id, 1, 10, "TKT-TEST-99"),
        )
        db.commit()

    response = client.get("/tickets/my-tickets?user_id=10")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "TKT-TEST-99" in html
    assert "Geçerli" in html
    assert "A1, A2" in html
    assert "150" in html
    assert "TL" in html


def test_my_tickets_page_shows_cancelled_status_badge(client):
    """İptal edilmiş biletlerde 'İptal Edildi' rozeti gösterilir."""
    with client.application.app_context():
        db = get_db()
        cursor = db.execute(
            "INSERT INTO payments (amount, card_last4, success, message, seats, created_at) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (100, "4242", 1, "Ödeme başarılı", json.dumps(["B5"])),
        )
        payment_id = cursor.lastrowid

        db.execute(
            "INSERT INTO reservations (payment_id, event_id, user_id, ticket_code, status, "
            "created_at) VALUES (?, ?, ?, ?, 'cancelled', datetime('now'))",
            (payment_id, 1, 20, "TKT-CANCEL-01"),
        )
        db.commit()

    response = client.get("/tickets/my-tickets?user_id=20")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "TKT-CANCEL-01" in html
    assert "İptal Edildi" in html
