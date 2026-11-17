"""Integration tests for Mobile Client JSON API endpoints (/api)."""

import pytest


def test_api_events_returns_json(client):
    """GET /api/events endpoint'i 200 döner ve content-type application/json olmalıdır."""
    response = client.get("/api/events")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("Content-Type", "")

    data = response.get_json()
    assert isinstance(data, dict)
    assert "events" in data
    assert isinstance(data["events"], list)


@pytest.mark.skip(reason="events servisi bekleniyor, TG-67")
def test_api_events_lists_only_published(client):
    """Yalnızca published durumundaki etkinlikler listede olmalı, draft/cancelled yer almamalı."""
    response = client.get("/api/events")
    assert response.status_code == 200
    data = response.get_json()
    for item in data["events"]:
        assert item["status"] == "published"


def test_api_events_empty_returns_empty_list(client, monkeypatch):
    """Etkinlik yoksa 404 değil, 200 ile boş liste {"events": []} dönmelidir."""
    from app.api import routes

    monkeypatch.setattr(routes, "get_events_from_service", lambda: [])

    response = client.get("/api/events")
    assert response.status_code == 200
    assert response.get_json() == {"events": []}


def test_api_events_item_has_required_fields(client):
    """Her etkinlik öğesinde arayüz sözleşmesinde belirlenen 7 zorunlu alan bulunmalıdır."""
    response = client.get("/api/events")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["events"]) > 0

    required_fields = {
        "id",
        "title",
        "category",
        "venue",
        "starts_at",
        "price",
        "status",
    }

    for item in data["events"]:
        assert required_fields.issubset(item.keys())
        assert isinstance(item["id"], int)
        assert isinstance(item["title"], str)
        assert isinstance(item["category"], str)
        assert isinstance(item["venue"], str)
        assert isinstance(item["starts_at"], str)
        assert item["status"] == "published"


def test_api_events_price_is_string(client):
    """Para float olursa yuvarlama hataları oluşur; fiyat kesinlikle metin (str) dönmelidir."""
    response = client.get("/api/events")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["events"]) > 0

    for item in data["events"]:
        assert isinstance(item["price"], str)
        # Ondalık nokta formatı kontrolü ("0.00", "150.00" gibi)
        parts = item["price"].split(".")
        assert len(parts) == 2
        assert parts[0].isdigit()
        assert parts[1].isdigit()
