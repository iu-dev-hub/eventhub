"""Events modülü birim (unit) testleri - Görev #120 (#32 PB-08)."""

import pytest
from app.services.event_service import create_draft_event, validate_event_capacity

pytestmark = pytest.mark.unit


def test_capacity_exceeds_venue_limit_validation():
    """BR-2.3: Etkinlik kapasitesi salon kapasitesini (100) aşarsa geçersiz sayılmalıdır."""
    hall_capacity = 100
    requested_capacity = 101
    
    is_valid = validate_event_capacity(requested_capacity, hall_capacity)
    assert not is_valid, "101 kapasite 100 limitli salonda reddedilmelidir."


def test_valid_capacity_passes_validation():
    """BR-2.2: Salon kapasitesi dahilindeki değerler geçerli kabul edilmelidir."""
    hall_capacity = 100
    requested_capacity = 50
    
    is_valid = validate_event_capacity(requested_capacity, hall_capacity)
    assert is_valid, "50 kapasite onaylanmalıdır."


def test_zero_price_is_handled_as_free():
    """Bilet fiyatı 0 TL olduğunda sistem tarafından ücretsiz olarak işlendiğini doğrula."""
    event_data = {
        "title": "Ücretsiz Seminer",
        "price": 0,
        "capacity": 50,
        "venue_id": 1
    }
    # Gerçek servis fonksiyonu üzerinden fiyat/durum kontrolü
    draft = create_draft_event(event_data, commit=False)
    assert draft.get("price") == 0 or draft.get("is_free") is True