"""Unit tests for mobile event listing, sorting, category filtering, and search (TG-183)."""

import json
from pathlib import Path

import pytest

from mobile_client.models.event import Event
from mobile_client.services.event_service import (
    ALL_CATEGORIES_LABEL,
    EventService,
    dict_to_event,
    filter_and_sort_events,
    filter_events_by_category,
    normalize_search_text,
    parse_iso_datetime,
    search_events,
    sort_events_by_nearest_date,
)


@pytest.fixture
def sample_events_json(tmp_path: Path) -> Path:
    """Sırasız, farklı kategorilerde ve farklı durumlarda örnek etkinlik JSON dosyası."""
    data = [
        {
            "id": 10,
            "title": "Web Geliştirme Bootcamp",
            "category": "Eğitim",
            "venue_id": 2,
            "start_time": "2026-06-25T14:00:00Z",
            "end_time": "2026-06-26T18:00:00Z",
            "capacity": 150,
            "price": 150.0,
            "status": "published",
            "organizer_id": 1,
        },
        {
            "id": 11,
            "title": "Yazılım Doğrulama ve Sınama Dersi",
            "category": "Eğitim",
            "venue_id": 1,
            "start_time": "2026-05-15T09:00:00Z",
            "end_time": "2026-05-15T17:00:00Z",
            "capacity": 300,
            "price": 0.0,
            "status": "published",
            "organizer_id": 1,
        },
        {
            "id": 12,
            "title": "Yapay Zeka Semineri",
            "category": "Teknoloji",
            "venue_id": 1,
            "start_time": "2026-05-20T10:00:00Z",
            "end_time": "2026-05-20T16:00:00Z",
            "capacity": 250,
            "price": 50.0,
            "status": "published",
            "organizer_id": 4,
        },
        {
            "id": 13,
            "title": "Mobil Uygulama Taslak Etkinliği",
            "category": "Eğitim",
            "venue_id": 3,
            "start_time": "2026-05-10T09:00:00Z",
            "end_time": "2026-05-10T15:00:00Z",
            "capacity": 100,
            "price": 75.0,
            "status": "draft",
            "organizer_id": 4,
        },
        {
            "id": 14,
            "title": "İptal Edilen Konser",
            "category": "Kültür",
            "venue_id": 3,
            "start_time": "2026-05-12T20:00:00Z",
            "end_time": "2026-05-12T23:00:00Z",
            "capacity": 200,
            "price": 100.0,
            "status": "cancelled",
            "organizer_id": 1,
        },
    ]
    json_path = tmp_path / "events.json"
    with json_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    return json_path


def test_default_api_events_json_loads_and_sorts_nearest_first():
    """../app/api/events.json dosyasından yayındaki etkinlikler en yakın tarih başta gelmelidir."""
    service = EventService()
    events = service.get_events()

    assert len(events) >= 3
    # Sadece yayındaki (published) etkinlikler gelmeli (BR-2.5, BR-2.7)
    assert all(ev.status == "published" for ev in events)
    # Tarih sırası küçükten büyüğe (en yakın tarih en başta) olmalı
    timestamps = [parse_iso_datetime(ev.start_time) for ev in events]
    assert timestamps == sorted(timestamps)


def test_sort_events_by_nearest_date_orders_chronologically(sample_events_json: Path):
    """Etkinlik listesi en yakın başlangıç tarihli etkinlik en başta olacak şekilde sıralanmalı."""
    service = EventService(events_json_path=sample_events_json)
    events = service.get_events()

    assert [ev.id for ev in events] == [11, 12, 10]
    assert events[0].title == "Yazılım Doğrulama ve Sınama Dersi"
    assert events[-1].title == "Web Geliştirme Bootcamp"


def test_filter_events_by_category(sample_events_json: Path):
    """Kategori seçimine göre etkinlik listesi doğru filtrelenmelidir (BR-2.6)."""
    service = EventService(events_json_path=sample_events_json)

    all_events = service.get_events(category=ALL_CATEGORIES_LABEL)
    assert [ev.id for ev in all_events] == [11, 12, 10]

    edu_events = service.get_events(category="Eğitim")
    assert [ev.id for ev in edu_events] == [11, 10]

    tech_events = service.get_events(category="Teknoloji")
    assert [ev.id for ev in tech_events] == [12]

    empty_cat_events = service.get_events(category="Performans")
    assert empty_cat_events == []


@pytest.mark.parametrize(
    ("query", "expected_ids"),
    [
        ("Yapay Zeka", [12]),
        ("YAPAY", [12]),
        ("Sınama", [11]),
        ("eğitim", [11, 10]),
        ("2026-05-20", [12]),
        ("Bootcamp", [10]),
        ("   ", [11, 12, 10]),
        ("BulunmayanEtkinlik", []),
    ],
)
def test_dynamic_search_events(sample_events_json: Path, query: str, expected_ids: list[int]):
    """Arama çubuğuna yazılan metne göre başlık, kategori ve tarihte dinamik arama yapılmalıdır."""
    service = EventService(events_json_path=sample_events_json)
    results = service.get_events(search_query=query)
    assert [ev.id for ev in results] == expected_ids


def test_combined_category_and_search_filter(sample_events_json: Path):
    """Kategori seçimi ve arama çubuğu birlikte çalışmalıdır."""
    service = EventService(events_json_path=sample_events_json)

    results = service.get_events(category="Eğitim", search_query="Bootcamp")
    assert [ev.id for ev in results] == [10]

    no_match = service.get_events(category="Teknoloji", search_query="Bootcamp")
    assert no_match == []


def test_get_categories_includes_all_and_event_categories(sample_events_json: Path):
    """Kategori listesi 'Tümü' ile başlamalı ve etkinlik kategorilerini içermelidir."""
    service = EventService(events_json_path=sample_events_json)
    categories = service.get_categories()

    assert categories[0] == ALL_CATEGORIES_LABEL
    assert "Eğitim" in categories
    assert "Teknoloji" in categories


def test_missing_or_corrupt_json_returns_empty_list(tmp_path: Path):
    """JSON dosyası yoksa veya bozuksa servis hata fırlatmadan boş liste döndürmelidir."""
    missing_service = EventService(events_json_path=tmp_path / "nonexistent.json")
    assert missing_service.get_events() == []

    corrupt_path = tmp_path / "corrupt.json"
    corrupt_path.write_text("{ invalid json ", encoding="utf-8")
    corrupt_service = EventService(events_json_path=corrupt_path)
    assert corrupt_service.get_events() == []


def test_pure_helper_functions():
    """Flet'ten bağımsız yardımcı fonksiyonlar sınır değerlerle doğru çalışmalıdır."""
    assert normalize_search_text("  İSTANBUL ve IĞDIR  ") == "istanbul ve ığdır"
    assert normalize_search_text(None) == ""

    raw = {
        "id": "5",
        "title": "Test Etkinliği",
        "category": "Seminer",
        "venue_id": "1",
        "start_time": "2026-07-01T10:00:00Z",
        "end_time": "2026-07-01T12:00:00Z",
        "capacity": "50",
        "price": "25.5",
        "status": "published",
        "organizer_id": "2",
    }
    ev = dict_to_event(raw)
    assert isinstance(ev, Event)
    assert ev.id == 5
    assert ev.price == 25.5

    assert filter_events_by_category([ev], None) == [ev]
    assert search_events([ev], "") == [ev]
    assert sort_events_by_nearest_date([ev]) == [ev]
    assert filter_and_sort_events([ev]) == [ev]


def test_events_view_search_and_category_filter_with_flet(sample_events_json: Path):
    """Flet kuruluysa Ana Sayfa görünümünde arama, kategori filtreleme ve tıklama doğrulanır."""
    pytest.importorskip("flet")
    from mobile_client.views.events_view import EMPTY_EVENTS_MESSAGE, build_events_view

    service = EventService(events_json_path=sample_events_json)
    clicked_events = []

    view = build_events_view(
        event_service=service,
        on_event_click=lambda ev: clicked_events.append(ev.id),
    )

    events_col = view.data["events_list_column"]
    assert len(events_col.controls) == 3
    # İlk kart en yakın tarihli etkinlik (id=11) olmalı
    assert events_col.controls[0].event.id == 11

    # Kategori seçimi: Teknoloji -> yalnızca id=12 kalmalı
    view.data["select_category"]("Teknoloji")
    assert len(events_col.controls) == 1
    assert events_col.controls[0].event.id == 12

    # Kategori: Tümü, Arama: Bootcamp -> yalnızca id=10 kalmalı
    view.data["select_category"](ALL_CATEGORIES_LABEL)
    view.data["set_search"]("Bootcamp")
    assert len(events_col.controls) == 1
    assert events_col.controls[0].event.id == 10

    # Kart tıklaması
    events_col.controls[0]._handle_click(None)
    assert clicked_events == [10]

    # Eşleşmeyen arama -> boş durum mesajı
    view.data["set_search"]("EşleşmeyenAramaMetni")
    assert len(events_col.controls) == 1
    assert events_col.controls[0].content.value == EMPTY_EVENTS_MESSAGE
