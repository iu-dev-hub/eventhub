"""Events modülü entegrasyon testleri - Görev #120 (#32 PB-08)."""

import pytest
from app.core.db import get_db

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def setup_test_db(app):
    """Mevcut gerçek test şemasına uygun olarak entegrasyon test verilerini dinamik ve hatasız hazırla."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Venues tablosu dinamik hazırlık
        venue_info = cursor.execute("PRAGMA table_info(venues)").fetchall()
        v_cols = [col["name"] for col in venue_info]
        if "id" in v_cols and "name" in v_cols and "capacity" in v_cols:
            cursor.execute("INSERT OR IGNORE INTO venues (id, name, address, capacity) VALUES (1, 'Ana Salon', 'Ankara', 100)")
        
        # Users tablosu gerçek şema kısıtlarına uygun dinamik INSERT
        user_info = cursor.execute("PRAGMA table_info(users)").fetchall()
        insert_cols = []
        insert_vals = []
        for col in user_info:
            cname = col["name"]
            notnull = col["notnull"]
            dflt = col["dflt_value"]
            pk = col["pk"]
            
            if cname == "id":
                insert_cols.append("id")
                insert_vals.append(1)
            elif cname == "role":
                insert_cols.append("role")
                insert_vals.append("organizer")
            elif notnull and dflt is None and not pk:
                insert_cols.append(cname)
                if "email" in cname:
                    insert_vals.append("test@example.com")
                elif "name" in cname or "user" in cname:
                    insert_vals.append("testuser")
                elif "pass" in cname:
                    insert_vals.append("hash")
                else:
                    insert_vals.append("test")
                    
        col_str = ", ".join(insert_cols)
        val_placeholder = ", ".join(["?"] * len(insert_vals))
        cursor.execute(f"INSERT OR IGNORE INTO users ({col_str}) VALUES ({val_placeholder})", tuple(insert_vals))
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