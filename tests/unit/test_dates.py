"""EXAMPLE unit tests for app/core/dates.py

Bu dosya, derste öğrenilen tekniklerin pytest'e nasıl aktarıldığını gösterir:
- pytest.mark.parametrize ile birden çok test durumu tek fonksiyonda
- Sınır değer analizi: sınırın hemen altı, kendisi ve hemen üstü
- Hata durumlarının pytest.raises ile test edilmesi
"""

from datetime import date, datetime

import pytest

from app.core.dates import add_days, minutes_until

EVENT_START = datetime(2026, 11, 20, 19, 0)


@pytest.mark.parametrize(
    ("days", "expected"),
    [
        (0, date(2026, 10, 1)),  # aynı gün
        (14, date(2026, 10, 15)),  # iki hafta sonrası
        (30, date(2026, 10, 31)),  # ay sonu
        (31, date(2026, 11, 1)),  # ay geçişi
    ],
)
def test_add_days(days, expected):
    assert add_days(date(2026, 10, 1), days) == expected


def test_add_days_across_year_boundary():
    assert add_days(date(2026, 12, 25), 14) == date(2027, 1, 8)


def test_add_days_rejects_negative_days():
    with pytest.raises(ValueError):
        add_days(date(2026, 10, 1), -1)


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (datetime(2026, 11, 20, 17, 59), 61),  # sınırın hemen üstü (BR-3.3: 60 dk)
        (datetime(2026, 11, 20, 18, 0), 60),  # tam sınır
        (datetime(2026, 11, 20, 18, 1), 59),  # sınırın hemen altı
        (datetime(2026, 11, 20, 19, 0), 0),  # etkinlik başladı
        (datetime(2026, 11, 20, 19, 30), -30),  # etkinlik başlayalı 30 dk oldu
    ],
)
def test_minutes_until_boundary_values(now, expected):
    assert minutes_until(EVENT_START, now) == expected
