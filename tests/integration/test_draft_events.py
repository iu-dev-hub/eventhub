"""Events modülü entegrasyon testleri - Görev #120 (#32 PB-08)."""

import pytest
from app.models import Event, db

pytestmark = pytest.mark.integration


def test_approved_organizer_can_save_draft_event(client, auth_organizer):
    """BR-1.5 & BR-2.2: Onaylı organizatör gerçek POST ile taslak kaydedebilmeli ve DB'de status='draft' olmalı."""
    response = client.post("/events/create", data={
        "title": "Gerçek Entegrasyon Taslağı",
        "category": "Eğitim",
        "venue_id": "1",
        "start_time": "2026-12-01T10:00",
        "end_time": "2026-12-01T12:00",
        "capacity": "50",
        "price": "100"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # TG-117 events tablosundan gerçek okuma ve status kontrolü
    event = Event.query.filter_by(title="Gerçek Entegrasyon Taslağı").first()
    assert event is not None, "Etkinlik veritabanına kaydedilmelidir."
    assert event.status == "draft", "Etkinliğin durumu 'draft' olmalıdır."


def test_unauthorized_user_cannot_save_draft_event(client, auth_participant):
    """BR-1.5: Yetkisiz kullanıcılar (katılımcılar) kayıt oluşturamamalı ve DB değişmemelidir."""
    initial_count = Event.query.count()
    
    response = client.post("/events/create", data={
        "title": "Yetkisiz Deneme",
        "category": "Eğitim",
        "venue_id": "1",
        "capacity": "50",
        "price": "100"
    })
    
    # Kullanıcının engellendiği (403 veya yönlendirme) doğrulanır
    assert response.status_code in [302, 403], "Yetkisiz kullanıcılar engellenmelidir."
    
    # Veritabanında kayıt sayısının değişmediği doğrulanır
    final_count = Event.query.count()
    assert final_count == initial_count, "Yetkisiz denemede veritabanına yeni kayıt eklenmemelidir."


def test_saved_draft_event_can_be_queried_from_database(app):
    """Kaydedilen taslak etkinlik bilgilerinin gerçek veritabanından tekrar okunabildiğini doğrula."""
    with app.app_context():
        new_event = Event(title="DB Okuma Testi", status="draft", capacity=50, venue_id=1)
        db.session.add(new_event)
        db.session.commit()
        
        queried_event = Event.query.filter_by(title="DB Okuma Testi").first()
        assert queried_event is not None, "Kaydedilen etkinlik veritabanından okunabilmelidir."
        assert queried_event.status == "draft"
        assert queried_event.capacity == 50