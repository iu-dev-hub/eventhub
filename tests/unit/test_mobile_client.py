"""Unit tests for Mobile Client logic (flet-independent).

Test edilebilirlik kuralı: İstemcinin modelleri ve iş mantığı flet içe
aktarmayan modüllerde yer alır ve CI'da sorunsuz çalışır.
"""

from mobile_client.src.models.event import Event


def test_event_model_remaining_capacity():
    """Kalan kapasite hesabı doğru yapılmalı ve negatif olmamalıdır."""
    event = Event(
        id="evt-101",
        title="Senfoni Konseri",
        category="Konser",
        venue_name="Atatürk Kültür Merkezi",
        city="İstanbul",
        date_str="25 Kasım 2026",
        days_until_event=20,
        time_str="20:00",
        base_price=120.0,
        capacity=100,
        sold_count=40,
    )
    assert event.remaining == 60


def test_event_model_remaining_never_negative():
    """Satılan bilet kapasiteyi aşsa bile remaining 0'ın altına düşmemelidir."""
    event = Event(
        id="evt-102",
        title="Oda Tiyatrosu",
        category="Tiyatro",
        venue_name="Şehir Tiyatrosu",
        city="Ankara",
        date_str="10 Aralık 2026",
        days_until_event=30,
        time_str="19:30",
        base_price=80.0,
        capacity=50,
        sold_count=55,
    )
    assert event.remaining == 0


def test_event_model_early_bird_discount_eligibility():
    """Etkinliğe 14 gün veya daha fazla varsa erken kayıt indirimi aktif olmalıdır (BR-4.1)."""
    event_early = Event(
        id="evt-103",
        title="Piyano Resitali",
        category="Klasik",
        venue_name="Süreyya Operası",
        city="İstanbul",
        date_str="15 Aralık 2026",
        days_until_event=14,
        time_str="20:00",
        base_price=150.0,
        capacity=200,
    )
    assert event_early.is_early_bird is True

    event_late = Event(
        id="evt-104",
        title="Caz Gecesi",
        category="Konser",
        venue_name="Babylon",
        city="İstanbul",
        date_str="2 Kasım 2026",
        days_until_event=13,
        time_str="21:30",
        base_price=150.0,
        capacity=150,
    )
    assert event_late.is_early_bird is False
