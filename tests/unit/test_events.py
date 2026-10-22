"""Events modülü birim testleri (BR-2.2, BR-2.3) - Görev #23.

Sınır değer analizi: salon kapasitesi 100 kabul edilir
(`services.validate_event_data` içinde prototip için sabit 100'dür).
"""

import pytest

from app.events.services import validate_event_data

HALL_CAPACITY = 100

CAPACITY_EXCEEDED_MSG = "Etkinlik kapasitesi salonun kapasitesini aşamaz."
REQUIRED_FIELDS_MSG = "Lütfen tüm zorunlu alanları doldurun."

VALID = {
    "title": "Yazılım Semineri",
    "category": "Eğitim",
    "venue": "Salon A",
    "start_time": "2026-12-01T10:00",
    "end_time": "2026-12-01T12:00",
    "capacity": 50,
    "price": 100,
}


def make(**overrides):
    return {**VALID, **overrides}


# --- BR-2.3: kapasite sınır değer analizi (TC-01 ... TC-04) -------------------


@pytest.mark.parametrize(
    "capacity",
    [
        pytest.param(50, id="TC-01-salon-sinirinin-altinda"),
        pytest.param(HALL_CAPACITY - 1, id="TC-02-sinirin-bir-altinda"),
        pytest.param(HALL_CAPACITY, id="TC-03-tam-sinirda"),
    ],
)
def test_capacity_within_hall_limit_is_accepted(capacity):
    assert validate_event_data(**make(capacity=capacity)) is True


@pytest.mark.parametrize(
    "capacity",
    [
        pytest.param(HALL_CAPACITY + 1, id="TC-04-sinirin-bir-ustunde"),
        pytest.param(500, id="sinirin-cok-ustunde"),
    ],
)
def test_capacity_above_hall_limit_is_rejected_with_message(capacity):
    with pytest.raises(ValueError) as exc:
        validate_event_data(**make(capacity=capacity))
    assert str(exc.value) == CAPACITY_EXCEEDED_MSG


# --- BR-2.2: zorunlu alanlar ----------------------------------------------------


@pytest.mark.parametrize(
    "field, empty_value",
    [
        ("title", ""),
        ("category", ""),
        ("venue", ""),
        ("start_time", ""),
        ("end_time", ""),
        ("capacity", None),
        ("price", None),
    ],
)
def test_missing_required_field_is_rejected(field, empty_value):
    with pytest.raises(ValueError) as exc:
        validate_event_data(**make(**{field: empty_value}))
    assert str(exc.value) == REQUIRED_FIELDS_MSG


def test_all_required_fields_present_is_accepted():
    assert validate_event_data(**VALID) is True


# --- BR-2.2: fiyatı 0 TL olan etkinlik ücretsizdir ------------------------------
# Serviste ayrı bir "ücretsiz mi" fonksiyonu yok; 0 TL fiyat geçerli kabul edilir.
# "Ücretsiz" etiketinin gösterimi arayüz davranışıdır (bkz. tests/e2e/test_events.py).


def test_zero_price_is_valid_free_event():
    assert validate_event_data(**make(price=0)) is True


# TODO: Kapasite 1, 0 ve negatif değerlerin beklenen davranışı BR belgesinde
# kesinleşmemiştir; öğretmenle netleştirilecek. Netleşmeden bu değerler için
# test YAZILMAMIŞTIR (mevcut kod capacity < 1 için hata verse de bu bir kural
# olarak kabul edilmemelidir).
