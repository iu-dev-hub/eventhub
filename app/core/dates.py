"""Date and time helpers (used by the tickets and payments modules).

Bu dosya aynı zamanda bir ÖRNEKTİR: Küçük, saf (yan etkisiz) fonksiyonlar
ve bunlara ait birim testleri (tests/unit/test_dates.py) nasıl yazılır?
"""

from datetime import date, datetime, timedelta


def add_days(start: date, days: int) -> date:
    """Başlangıç tarihine verilen gün sayısını ekler.

    >>> add_days(date(2026, 10, 1), 14)
    datetime.date(2026, 10, 15)
    """
    if days < 0:
        raise ValueError("days must not be negative")
    return start + timedelta(days=days)


def minutes_until(target: datetime, now: datetime) -> int:
    """Hedef zamana kaç tam dakika kaldığını döndürür.

    Hedef zaman geçmişse negatif değer döner. Örneğin bilet satışının
    kapanıp kapanmadığını (BR-3.3) kontrol etmek için kullanılabilir.
    """
    return int((target - now).total_seconds() // 60)
