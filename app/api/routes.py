"""Mobil istemci için JSON API uç noktaları."""

from flask import jsonify

from app.api import bp


# TODO: events servisi hazır olunca kaldır (TG-67)
def _get_temporary_published_events() -> list[dict]:
    """team-events servisi hazır olana kadar geçici test verisi döndürür."""
    return [
        {
            "id": 12,
            "title": "Yapay Zekâ Semineri",
            "category": "Seminer",
            "venue": "Konferans Salonu A",
            "starts_at": "2026-11-05T14:00:00",
            "price": "0.00",
            "status": "published",
        }
    ]


def get_events_from_service() -> list[dict]:
    """team-events servisinden yayındaki etkinlikleri alır.

    Mimari kuralı: API iş kuralı yazmaz. Etkinlikleri app/events/services.py'deki
    fonksiyondan alır, yalnızca JSON'a çevirir. team-events servisi hazır olana kadar
    geçici fonksiyon kullanılır.
    """
    try:
        from app.events import services as events_services

        if hasattr(events_services, "get_published_events"):
            return events_services.get_published_events()
    except (ImportError, AttributeError):
        pass

    return _get_temporary_published_events()


@bp.get("/health")
def health():
    """API sağlık kontrolü."""
    return jsonify({"status": "ok"}), 200


@bp.get("/events")
def get_events():
    """Yalnızca yayındaki (published) etkinlikleri döndürür.

    Etkinlik yoksa boş liste döner (404 değil).
    Fiyatlar yuvarlama hatalarını önlemek için string olarak döndürülür.
    Tarihler ISO 8601 biçimindedir.
    """
    raw_events = get_events_from_service()

    formatted_events = []
    for item in raw_events:
        price_val = item.get("price", "0.00")
        if isinstance(price_val, (int, float)):
            price_str = f"{price_val:.2f}"
        else:
            price_str = str(price_val)

        formatted_events.append(
            {
                "id": int(item["id"]),
                "title": str(item["title"]),
                "category": str(item["category"]),
                "venue": str(item["venue"]),
                "starts_at": str(item["starts_at"]),
                "price": price_str,
                "status": str(item["status"]),
            }
        )

    return jsonify({"events": formatted_events}), 200
