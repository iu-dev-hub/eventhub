from app.core.db import get_db
from app.tickets import services


def test_cancelled_tickets_do_not_use_capacity(app, monkeypatch):
    """İptal edilen biletlerin aktif kontenjandan sayılmadığını doğrular."""
    with app.app_context():
        db = get_db()

        monkeypatch.setattr(services, "get_remaining_capacity", lambda event_id: 48)

        db.execute(
            "INSERT INTO tickets (event_id, user_id, status, created_at) VALUES (?, ?, ?, ?)",
            (1, 1, "paid", "2026-03-02"),
        )
        db.execute(
            "INSERT INTO tickets (event_id, user_id, status, created_at) VALUES (?, ?, ?, ?)",
            (1, 2, "paid", "2026-03-02"),
        )
        db.execute(
            "INSERT INTO tickets (event_id, user_id, status, created_at) VALUES (?, ?, ?, ?)",
            (1, 3, "cancelled", "2026-03-02"),
        )
        db.commit()

        # Sadece paid olanlar sayılmalı (Beklenen: 2)
        assert services.count_active_tickets(event_id=1) == 2


def test_ticket_purchase_and_cancellation_capacity_flow(app, monkeypatch):
    """Bilet alındığında kontenjanın azaldığını, iptal edildiğinde arttığını doğrular."""
    with app.app_context():
        # Etkinlik kapasitesini 5 kabul edelim ve dinamik hesaplayalım
        fake_capacity = 5
        monkeypatch.setattr(
            services,
            "get_remaining_capacity",
            lambda eid: max(0, fake_capacity - services.count_active_tickets(eid)),
        )

        # 1. Bilet alımı öncesi kontrol
        initial_active = services.count_active_tickets(event_id=10)

        # 2. Bilet satın alma (Aktif bilet sayısı 1 artmalı)
        ticket_id = services.purchase_ticket(event_id=10, user_id=1)
        assert services.count_active_tickets(event_id=10) == initial_active + 1

        # 3. Bilet iptali (Aktif bilet sayısı 1 azalmalı, kontenjan eski haline dönmeli)
        services.cancel_ticket(ticket_id)
        assert services.count_active_tickets(event_id=10) == initial_active
