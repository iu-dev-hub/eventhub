from app.core.db import get_db
from app.tickets import services

def test_cancelled_tickets_do_not_use_capacity(app, monkeypatch):
    """İptal edilen biletlerin aktif kontenjandan sayılmadığını doğrular."""
    with app.app_context():
        db = get_db()
        
        # Diğer ekibin tablosuna bağımlı kalmamak için events.capacity sorgusunu mock'luyoruz (Rehber Md. 6)
        monkeypatch.setattr(services, "get_remaining_capacity", lambda event_id: 48)

        # Sadece kendi tablomuz olan tickets'a test verisi ekliyoruz
        db.execute("INSERT INTO tickets (event_id, user_id, status, created_at) VALUES (?, ?, ?, ?)", (1, 1, "paid", "2026-03-02"))
        db.execute("INSERT INTO tickets (event_id, user_id, status, created_at) VALUES (?, ?, ?, ?)", (1, 2, "paid", "2026-03-02"))
        db.execute("INSERT INTO tickets (event_id, user_id, status, created_at) VALUES (?, ?, ?, ?)", (1, 3, "cancelled", "2026-03-02"))
        db.commit()

        # Sadece paid olanlar sayılmalı (Beklenen: 2)
        assert services.count_active_tickets(event_id=1) == 2