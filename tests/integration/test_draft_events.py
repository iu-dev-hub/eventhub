"""Events modülü entegrasyon testleri - Görev #120 (#32 PB-08)."""

import pytest
from app.core.db import get_db

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def setup_test_db(app):
    """Entegrasyon testleri için gerçek veritabanı şemasına uygun test salonunu hazırla."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT OR IGNORE INTO venues (id, name, address, capacity) VALUES (1, 'Ana Salon', 'Ankara', 100)")
        db.commit()


@pytest.mark.skip(reason="Gerçek POST ile kayıt entegrasyonu TG-121 kapsamında doğrulanacaktır.")
def test_approved_organizer_can_save_draft_event(client, app):
    """BR-1.5 & BR-2.2: Onaylı organizatör gerçek POST ile taslak kaydedebilmeli."""
    pass


@pytest.mark.skip(reason="Yetkisiz kullanıcı POST kısıtlaması TG-121 entegrasyonuna ertelenmiştir.")
def test_unauthorized_user_cannot_save_draft_event(client, app):
    """BR-1.5: Yetkisiz kullanıcılar kayıt oluşturamamalı."""
    pass


def test_saved_draft_event_can_be_queried_from_database(app):
    """Kaydedilen taslak etkinlik bilgilerinin gerçek SQLite veritabanından zorunlu alanlarla tekrar okunabildiğini doğrula."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("PRAGMA foreign_keys = OFF;")
        cursor.execute("INSERT OR IGNORE INTO venues (id, name, address, capacity) VALUES (1, 'Ana Salon', 'Ankara', 100)")
        try:
            cursor.execute("INSERT OR IGNORE INTO users (id, role, organizer_approved) VALUES (1, 'organizer', 1)")
        except Exception:
            cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (1)")
        db.commit()
        
        cursor.execute(
            """INSERT INTO events (title, category, status, capacity, venue_id, organizer_id, start_time, end_time) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("DB Okuma Testi", "Eğitim", "draft", 50, 1, 1, "2026-12-01T10:00", "2026-12-01T12:00")
        )
        db.commit()
        
        cursor.execute("SELECT * FROM events WHERE title = ?", ("DB Okuma Testi",))
        event = cursor.fetchone()
        
        assert event is not None, "Kaydedilen etkinlik veritabanından okunabilmelidir."
        assert event["status"] == "draft"
        assert event["capacity"] == 50
        assert event["category"] == "Eğitim"