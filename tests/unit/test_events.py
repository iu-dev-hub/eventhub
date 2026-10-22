"""Events modülü birim testleri (BR-2.2, BR-2.3) - Görev #23.

`validate_event_creation` 7 parametre alır ve `(is_valid, messages)` döndürür.
Sınır değer analizi: salon kapasitesi 100 kabul edilir (serviste prototip için sabit 100).
Form alanları servise metin (str) olarak geldiği için testler de değerleri metin olarak verir.
"""

import pytest

from app.events.services import validate_event_creation

HALL_CAPACITY = 100

REQUIRED_FIELDS_MSG = "Lütfen tüm zorunlu alanları doldurun."
MIN_CAPACITY_MSG = "Etkinlik kapasitesi en az 1 olmalıdır."
NEGATIVE_PRICE_MSG = "Bilet fiyatı negatif olamaz."

VALID = {
    "title": "Yazılım Semineri",
    "category": "Eğitim",
    "venue": "Salon A",
    "start_time": "2026-12-01T10:00",
    "end_time": "2026-12-01T12:00",
    "capacity": "50",
    "price": "100",
}


def run(**overrides):
    return validate_event_creation(**{**VALID, **overrides})


# --- BR-2.3: kapasite sınır değer analizi (TC-01 ... TC-04) -------------------


@pytest.mark.parametrize(
    "capacity",
    [
        pytest.param("50", id="TC-01-salon-sinirinin-altinda"),
        pytest.param("99", id="TC-02-sinirin-bir-altinda"),
        pytest.param("100", id="TC-03-tam-sinirda"),
    ],
)
def test_capacity_within_hall_limit_is_accepted(capacity):
    is_valid, messages = run(capacity=capacity)
    assert is_valid is True
    assert len(messages) == 1


@pytest.mark.parametrize(
    "capacity",
    [
        pytest.param("101", id="TC-04-sinirin-bir-ustunde"),
        pytest.param("500", id="sinirin-cok-ustunde"),
    ],
)
def test_capacity_above_hall_limit_is_rejected_with_message(capacity):
    is_valid, messages = run(capacity=capacity)
    assert is_valid is False
    assert messages == [
        f"Etkinlik kapasitesi ({capacity}), salon kapasitesini ({HALL_CAPACITY}) aşamaz."
    ]


# --- Kapasite alt sınırı: 1, 0 ve negatif -----------------------------------------
# NOT: Alt sınır ve negatif değer kuralları BR belgesinde henüz kesinleşmemiştir;
# öğretmenle netleştirilecek. Aşağıdaki testler BR kuralı değil, servisin
# GÜNCEL davranışını kaydeder. Kural değişirse bu testler güncellenmelidir.


def test_capacity_one_is_accepted():
    is_valid, _ = run(capacity="1")
    assert is_valid is True


@pytest.mark.parametrize("capacity", ["0", "-1", "-50"])
def test_capacity_zero_or_negative_is_rejected_with_message(capacity):
    is_valid, messages = run(capacity=capacity)
    assert is_valid is False
    assert messages == [MIN_CAPACITY_MSG]


def test_non_numeric_capacity_is_rejected():
    is_valid, messages = run(capacity="abc")
    assert is_valid is False
    assert messages == ["Kapasite ve fiyat geçerli sayısal değerler olmalıdır."]


# --- BR-2.2: zorunlu alanlar ----------------------------------------------------


@pytest.mark.parametrize(
    "field",
    ["title", "category", "venue", "start_time", "end_time", "capacity", "price"],
)
def test_missing_required_field_is_rejected(field):
    is_valid, messages = run(**{field: ""})
    assert is_valid is False
    assert messages == [REQUIRED_FIELDS_MSG]


def test_all_required_fields_present_is_accepted():
    is_valid, _ = run()
    assert is_valid is True


# --- Fiyat -----------------------------------------------------------------------


def test_negative_price_is_rejected_with_message():
    is_valid, messages = run(price="-1")
    assert is_valid is False
    assert messages == [NEGATIVE_PRICE_MSG]


# --- BR-2.2: fiyatı 0 TL olan etkinlik ücretsizdir ------------------------------


def test_zero_price_is_accepted_as_free_event():
    is_valid, messages = run(price="0")
    assert is_valid is True
    assert messages[0].startswith("Ücretsiz etkinlik")


def test_paid_event_is_not_reported_as_free():
    is_valid, messages = run(price="100")
    assert is_valid is True
    assert not messages[0].startswith("Ücretsiz")
