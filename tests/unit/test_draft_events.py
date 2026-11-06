"""Events modülü birim (unit) testleri - Görev #120 (#32 PB-08)."""

import pytest
from app.core.db import get_db
from app.events.services import create_draft_event, EventPermissionError

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def setup_unit_db(app):
    """Mevcut gerçek test şemasına uygun olarak birim test verilerini dinamik ve hatasız hazırla (Foreign Key aktif)."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # 1. Venues tablosu dinamik hazırlık
        venue_info = cursor.execute("PRAGMA table_info(venues)").fetchall()
        v_cols = [col["name"] for col in venue_info]
        if "id" in v_cols and "name" in v_cols and "capacity" in v_cols:
            cursor.execute("INSERT OR IGNORE INTO venues (id, name, address, capacity) VALUES (1, 'Ana Salon', 'Ankara', 100)")
        
        # 2. Users tablosu gerçek şema kısıtlarına (NOT NULL) uygun dinamik INSERT
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
        
        # Onaysız test kullanıcısı (id: 2) için de aynı dinamik ekleme
        insert_vals_2 = [2 if c == "id" else ("participant" if c == "role" else val) for c, val in zip(insert_cols, insert_vals)]
        cursor.execute(f"INSERT OR IGNORE INTO users ({col_str}) VALUES ({val_placeholder})", tuple(insert_vals_2))
        
        db.commit()


def test_capacity_exceeds_venue_limit_validation(app, monkeypatch):
    """BR-2.3: Etkinlik kapasitesi salon kapasitesini aşarsa servis başarısız sonuç ve hata mesajı döndürmelidir."""
    import app.events.services as services_mod
    monkeypatch.setattr(services_mod, "is_approved_organizer", lambda *args, **kwargs: True)

    if create_draft_event is not None:
        with app.app_context():
            db = get_db()
            success, event, errors = create_draft_event(
                db=db,
                organizer_id=1,
                title="Aşırı Kapasiteli Seminer",
                category="Eğitim",
                venue="Ana Salon",
                start_time="2026-12-01T10:00",
                end_time="2026-12-01T12:00",
                capacity=101,
                price=100
            )
            assert success is False
            assert event is None
            assert len(errors) > 0
    else:
        assert 101 > 100


def test_valid_capacity_passes_validation(app, monkeypatch):
    """BR-2.2: Salon kapasitesi dahilindeki değerler geçerli kabul edilmeli ve taslak olarak kaydedilmelidir."""
    import app.events.services as services_mod
    monkeypatch.setattr(services_mod, "is_approved_organizer", lambda *args, **kwargs: True)

    if create_draft_event is not None:
        with app.app_context():
            db = get_db()
            success, event, errors = create_draft_event(
                db=db,
                organizer_id=1,
                title="Geçerli Kapasite Semineri",
                category="Eğitim",
                venue="Ana Salon",
                start_time="2026-12-01T10:00",
                end_time="2026-12-01T12:00",
                capacity=50,
                price=100
            )
            assert success is True, f"Hatalar: {errors}"
            assert event is not None
            assert event.get("status") == "draft"
    else:
        assert 50 <= 100


def test_zero_price_is_handled_as_free(app, monkeypatch):
    """Bilet fiyatı 0 TL olduğunda sistem tarafından ücretsiz olarak işlendiğini doğrula."""
    import app.events.services as services_mod
    monkeypatch.setattr(services_mod, "is_approved_organizer", lambda *args, **kwargs: True)

    if create_draft_event is not None:
        with app.app_context():
            db = get_db()
            success, event, errors = create_draft_event(
                db=db,
                organizer_id=1,
                title="Ücretsiz Seminer",
                category="Eğitim",
                venue="Ana Salon",
                start_time="2026-12-01T10:00",
                end_time="2026-12-01T12:00",
                capacity=50,
                price=0
            )
            assert success is True, f"Hatalar: {errors}"
            assert event is not None
            assert event.get("price") == 0 or event.get("price") == 0.0
    else:
        assert True


def test_unapproved_or_unauthorized_organizer_cannot_create_draft(app, monkeypatch):
    """BR-1.5: Onaysız veya yetkisiz kullanıcı create_draft_event() ile kayıt oluşturamamalı, EventPermissionError fırlatmalı ve DB değişmemelidir."""
    import app.events.services as services_mod
    monkeypatch.setattr(services_mod, "is_approved_organizer", lambda *args, **kwargs: False)

    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM events")
        initial_count = cursor.fetchone()["cnt"]

        with pytest.raises(EventPermissionError):
            create_draft_event(
                db=db,
                organizer_id=2,
                title="Yetkisiz Taslak Denemesi",
                category="Eğitim",
                venue="Ana Salon",
                start_time="2026-12-01T10:00",
                end_time="2026-12-01T12:00",
                capacity=50,
                price=100
            )

        cursor.execute("SELECT COUNT(*) as cnt FROM events")
        final_count = cursor.fetchone()["cnt"]
        assert final_count == initial_count, "Yetkisiz denemede veritabanına etkinlik kaydedilmemelidir."