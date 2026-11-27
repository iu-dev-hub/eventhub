"""Event listing, sorting, category filtering, and search service (TG-183).

Bu modül Flet içe aktarmaz; böylece etkinlik listeleme, sıralama, kategori filtreleme
ve dinamik arama mantığı CI ortamında Flet kurulmadan doğrudan test edilebilir
(mobile_client/README.md - test edilebilirlik kuralı).
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from mobile_client.core.constants import EVENT_CATEGORIES
from mobile_client.models.event import Event

DEFAULT_API_DIR = Path(__file__).resolve().parents[2] / "app" / "api"
DEFAULT_EVENTS_JSON_PATH = DEFAULT_API_DIR / "events.json"

ALL_CATEGORIES_LABEL = "Tümü"

_TR_LOWER_MAP = str.maketrans(
    {
        "İ": "i",
        "I": "ı",
        "Ğ": "ğ",
        "Ü": "ü",
        "Ş": "ş",
        "Ö": "ö",
        "Ç": "ç",
    }
)


def normalize_search_text(text: Optional[str]) -> str:
    """Türkçe karakter duyarlı küçük harf dönüşümü ve boşluk temizliği yapar."""
    if not isinstance(text, str):
        return ""
    return text.translate(_TR_LOWER_MAP).lower().strip()


def parse_iso_datetime(value: Optional[str]) -> datetime:
    """ISO 8601 tarih/saat dizgesini güvenli şekilde UTC datetime nesnesine çevirir."""
    if not value or not isinstance(value, str):
        return datetime.max.replace(tzinfo=timezone.utc)
    cleaned = value.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(cleaned)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return datetime.max.replace(tzinfo=timezone.utc)


def dict_to_event(raw: Dict[str, Any]) -> Event:
    """JSON sözlüğünü Event model nesnesine dönüştürür."""
    return Event(
        id=int(raw["id"]),
        title=str(raw.get("title", "")).strip(),
        category=str(raw.get("category", "")).strip(),
        venue_id=int(raw.get("venue_id", 0)),
        start_time=str(raw.get("start_time", "")).strip(),
        end_time=str(raw.get("end_time", "")).strip(),
        capacity=int(raw.get("capacity", 0)),
        price=float(raw.get("price", 0.0)),
        status=str(raw.get("status", "draft")).strip(),
        organizer_id=int(raw.get("organizer_id", 0)),
    )


def sort_events_by_nearest_date(events: Iterable[Event]) -> List[Event]:
    """Etkinlikleri başlangıç tarihine göre en yakın tarihteki en başta olacak şekilde sıralar."""
    return sorted(
        events,
        key=lambda ev: (parse_iso_datetime(ev.start_time), ev.id),
    )


def filter_events_by_category(
    events: Iterable[Event],
    category: Optional[str] = None,
) -> List[Event]:
    """Seçilen kategoriye göre etkinlik listesini filtreler (BR-2.6)."""
    normalized_cat = normalize_search_text(category)
    if not normalized_cat or normalized_cat == normalize_search_text(ALL_CATEGORIES_LABEL):
        return list(events)
    return [ev for ev in events if normalize_search_text(ev.category) == normalized_cat]


def search_events(
    events: Iterable[Event],
    search_query: Optional[str] = None,
) -> List[Event]:
    """Arama metnine göre başlık, kategori veya tarihte dinamik arama yapar (BR-2.6)."""
    query = normalize_search_text(search_query)
    if not query:
        return list(events)

    matched: List[Event] = []
    for ev in events:
        haystack = " ".join(
            [
                normalize_search_text(ev.title),
                normalize_search_text(ev.category),
                normalize_search_text(ev.start_time),
            ]
        )
        if query in haystack:
            matched.append(ev)
    return matched


def filter_and_sort_events(
    events: Iterable[Event],
    category: Optional[str] = None,
    search_query: Optional[str] = None,
    only_published: bool = True,
) -> List[Event]:
    """Yayındaki etkinlikleri filtreler, kategori/arama uygular ve en yakın tarihe göre sıralar."""
    items = list(events)
    if only_published:
        items = [ev for ev in items if ev.status == "published"]
    items = filter_events_by_category(items, category=category)
    items = search_events(items, search_query=search_query)
    return sort_events_by_nearest_date(items)


class EventService:
    """../app/api klasöründeki JSON dosyalarından etkinlik verilerini okuyan servis."""

    def __init__(self, events_json_path: Optional[Path] = None) -> None:
        self.events_json_path = (
            Path(events_json_path) if events_json_path else DEFAULT_EVENTS_JSON_PATH
        )

    def load_all_events(self) -> List[Event]:
        """events.json dosyasındaki tüm etkinlik kayıtlarını json.load ile okur."""
        if not self.events_json_path.exists():
            return []
        try:
            with self.events_json_path.open("r", encoding="utf-8") as file:
                raw_list = json.load(file)
        except (OSError, json.JSONDecodeError):
            return []

        if not isinstance(raw_list, list):
            return []

        events: List[Event] = []
        for item in raw_list:
            if isinstance(item, dict) and "id" in item:
                try:
                    events.append(dict_to_event(item))
                except (KeyError, TypeError, ValueError):
                    continue
        return events

    def get_events(
        self,
        category: Optional[str] = None,
        search_query: Optional[str] = None,
        only_published: bool = True,
    ) -> List[Event]:
        """Etkinlikleri kategori ve aramaya göre filtreleyip en yakın tarihe göre sıralar."""
        all_events = self.load_all_events()
        return filter_and_sort_events(
            all_events,
            category=category,
            search_query=search_query,
            only_published=only_published,
        )

    def get_categories(self, only_published: bool = True) -> List[str]:
        """Filtrelemede kullanılacak kategori listesini ('Tümü' + mevcut kategoriler) döndürür."""
        events = self.load_all_events()
        if only_published:
            events = [ev for ev in events if ev.status == "published"]

        categories: List[str] = [ALL_CATEGORIES_LABEL]
        seen = {normalize_search_text(ALL_CATEGORIES_LABEL)}

        for ev in events:
            norm = normalize_search_text(ev.category)
            if norm and norm not in seen:
                categories.append(ev.category)
                seen.add(norm)

        for cat in EVENT_CATEGORIES:
            norm = normalize_search_text(cat)
            if norm and norm not in seen:
                categories.append(cat)
                seen.add(norm)

        return categories
