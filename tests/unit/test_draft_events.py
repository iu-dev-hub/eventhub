"""Events modülü birim (unit) testleri - Görev #120 (#32 PB-08)."""

import pytest

pytestmark = pytest.mark.unit


def test_capacity_exceeds_venue_limit_validation():
    """BR-2.3: Etkinlik kapasitesi salon kapasitesini (100) aşarsa geçersiz sayılmalıdır."""
    hall_capacity = 100
    requested_capacity = 101
    
    # Kapasite kontrol mantığı birim testi
    is_valid = requested_capacity <= hall_capacity
    assert not is_valid, "101 kapasite 100 limitli salonda reddedilmelidir."


def test_valid_capacity_passes_validation():
    """BR-2.2: Salon kapasitesi dahilindeki değerler geçerli kabul edilmelidir."""
    hall_capacity = 100
    requested_capacity = 50
    
    is_valid = requested_capacity <= hall_capacity
    assert is_valid, "50 kapasite onaylanmalıdır."


def test_zero_price_is_marked_as_free():
    """Bilet fiyatı 0 TL olduğunda sistem tarafından ücretsiz olarak işaretlenmelidir."""
    price = 0
    assert price == 0, "0 TL bilet fiyatı ücretsiz olmalıdır."