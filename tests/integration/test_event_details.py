"""TG-189: Etkinlik detayları ile salon bilgilerinin tek JOIN sorgusunda dönmesi."""

import pytest

from app.core.db import get_db
from app.events.services import get_event


@pytest.fixture
def detail_data(app):
    """Her test için geçici SQLite veritabanında iki farklı salon ve etkinlik hazırlar."""
    with app.app_context():
        db = get_db()

        db.execute(
            "INSERT INTO users (id, email, password_hash, role) "
            "VALUES (189, ?, 'hash', 'organizer')",
            ("organizer189@example.com",),
        )

        db.execute(
            "INSERT INTO users (id, email, password_hash, role) "
            "VALUES (190, ?, 'hash', 'participant')",
            ("participant189@example.com",),
        )

        db.execute(
            "INSERT INTO venues (id, name, address, capacity) VALUES (189, ?, ?, ?)",
            ("Ana Salon", "Iğdır Merkez", 120),
        )

        db.execute(
            "INSERT INTO venues (id, name, address, capacity) VALUES (190, ?, ?, ?)",
            ("Küçük Salon", "Kampüs", 30),
        )

        db.execute(
            """INSERT INTO events
                (id, title, category, venue_id, start_time, end_time,
                 capacity, price, status, organizer_id)
                VALUES (189, ?, ?, 189, ?, ?, 75, 150.0, 'published', 189)""",
            ("Yazılım Semineri", "Eğitim", "2026-12-03T10:00", "2026-12-03T12:00"),
        )

        db.execute(
            """INSERT INTO events
                (id, title, category, venue_id, start_time, end_time,
                 capacity, price, status, organizer_id)
                VALUES (190, ?, ?, 190, ?, ?, 20, 0, 'published', 189)""",
            ("Ücretsiz Atölye", "Atölye", "2026-12-04T13:00", "2026-12-04T15:00"),
        )

        db.execute(
            """INSERT INTO events
                (id, title, category, venue_id, start_time, end_time,
                 capacity, price, status, organizer_id)
                VALUES (191, ?, ?, 189, ?, ?, 25, 0, 'draft', 189)""",
            ("Gizli Taslak", "Eğitim", "2026-12-05T10:00", "2026-12-05T12:00"),
        )

        db.commit()
        yield db


def test_event_details_contain_all_event_and_venue_fields(detail_data):
    """TG-189: İstenen alanlar tek sözlükte, doğru tür ve değerlerle döner."""
    result = get_event(detail_data, 189)

    assert result is not None
    assert {
        "id",
        "title",
        "category",
        "venue_id",
        "start_time",
        "end_time",
        "capacity",
        "price",
        "status",
        "organizer_id",
        "venue_name",
        "venue_address",
        "venue_capacity",
    } <= result.keys()

    assert result["id"] == 189
    assert result["title"] == "Yazılım Semineri"
    assert result["category"] == "Eğitim"
    assert result["venue_id"] == 189
    assert result["start_time"] == "2026-12-03T10:00"
    assert result["end_time"] == "2026-12-03T12:00"
    assert result["capacity"] == 75
    assert result["price"] == 150.0
    assert result["status"] == "published"
    assert result["organizer_id"] == 189
    assert result["venue_name"] == "Ana Salon"
    assert result["venue_address"] == "Iğdır Merkez"
    assert result["venue_capacity"] == 120

    assert isinstance(result["price"], (float, int))
    assert isinstance(result["start_time"], str)
    assert isinstance(result["end_time"], str)


def test_free_event_uses_its_own_venue(detail_data):
    """Fiyat 0 sayısal kalır; JOIN yanlış salon bilgisi döndürmez."""
    result = get_event(detail_data, 190)

    assert result is not None
    assert result["price"] == 0.0
    assert result["venue_name"] == "Küçük Salon"
    assert result["venue_address"] == "Kampüs"
    assert result["venue_capacity"] == 30
    assert result["start_time"] == "2026-12-04T13:00"
    assert result["end_time"] == "2026-12-04T15:00"


@pytest.mark.parametrize("event_id", [None, 0, -1, 99999, "189", True, 1.5])
def test_missing_or_invalid_event_id_returns_none(detail_data, event_id):
    """Geçersiz veya bulunmayan etkinlikte istisna yerine None dönülür."""
    assert get_event(detail_data, event_id) is None


def test_detail_route_exposes_joined_data_to_participant(detail_data, client):
    """Mevcut GET endpoint'i salon bilgilerini JSON döndürür."""
    with client.session_transaction() as session:
        session["user_id"] = 190
        session["user_email"] = "participant189@example.com"
        session["user_role"] = "participant"

    response = client.get("/events/189")

    assert response.status_code == 200

    data = response.get_json()
    assert data["venue_name"] == "Ana Salon"
    assert data["venue_address"] == "Iğdır Merkez"
    assert data["venue_capacity"] == 120
    assert data["price"] == 150.0


def test_draft_visibility_rule_is_preserved(detail_data, client):
    """Yeni JOIN, başkasının taslağını katılımcıya açmamalı."""
    with client.session_transaction() as session:
        session["user_id"] = 190
        session["user_email"] = "participant189@example.com"
        session["user_role"] = "participant"

    assert client.get("/events/191").status_code == 404
