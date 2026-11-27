from app.core.db import get_db
from app.tickets import services


def _seed_event(db, event_id):
    """tickets.event_id -> events.id FK'si için gerçek bir (yayımlanmış) etkinlik ekler."""
    db.execute(
        "INSERT OR IGNORE INTO venues (id, name, address, capacity) "
        "VALUES (1, 'Salon A', 'Adres', 100)"
    )
    db.execute(
        "INSERT OR IGNORE INTO users (id, email, password_hash, role) "
        "VALUES (1, 'org@example.com', 'x', 'organizer')"
    )
    db.execute(
        "INSERT INTO events (id, title, category, venue_id, start_time, end_time, "
        "capacity, price, status, organizer_id) "
        "VALUES (?, 'Test', 'Eğitim', 1, '2026-12-01T10:00', '2026-12-01T12:00', 50, 0, "
        "'published', 1)",
        (event_id,),
    )
    db.commit()


def test_cancelled_tickets_do_not_use_capacity(app, monkeypatch):
    """İptal edilen biletlerin aktif kontenjandan sayılmadığını doğrular."""
    with app.app_context():
        db = get_db()
        _seed_event(db, 1)

        monkeypatch.setattr(services, "get_remaining_capacity", lambda event_id: 48)

        db.execute("INSERT INTO tickets (event_id, user_id, status, created_at) VALUES (?, ?, ?, ?)", (1, 1, "paid", "2026-03-02"))
        db.execute("INSERT INTO tickets (event_id, user_id, status, created_at) VALUES (?, ?, ?, ?)", (1, 2, "paid", "2026-03-02"))
        db.execute("INSERT INTO tickets (event_id, user_id, status, created_at) VALUES (?, ?, ?, ?)", (1, 3, "cancelled", "2026-03-02"))
        db.commit()

        
        # Sadece paid olanlar sayılmalı (Beklenen: 2)
        assert services.count_active_tickets(event_id=1) == 2

def test_ticket_purchase_and_cancellation_capacity_flow(app, monkeypatch):
    """Bilet alındığında kontenjanın azaldığını, iptal edildiğinde arttığını doğrular."""
    with app.app_context():
        _seed_event(get_db(), 10)
        # Etkinlik kapasitesini 5 kabul edelim ve dinamik hesaplayalım
        fake_capacity = 5
        monkeypatch.setattr(
            services, 
            "get_remaining_capacity", 
            lambda eid: max(0, fake_capacity - services.count_active_tickets(eid))
        )
        
        # 1. Bilet alımı öncesi kontrol
        initial_active = services.count_active_tickets(event_id=10)
        
        # 2. Bilet satın alma (Aktif bilet sayısı 1 artmalı)
        ticket_id = services.purchase_ticket(event_id=10, user_id=1)
        assert services.count_active_tickets(event_id=10) == initial_active + 1
        
        # 3. Bilet iptali (Aktif bilet sayısı 1 azalmalı, kontenjan eski haline dönmeli)
        services.cancel_ticket(ticket_id)
        assert services.count_active_tickets(event_id=10) == initial_active
