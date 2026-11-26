"""TG-190: Etkinlik detayi rol ve taslak gorunurlugu servis testleri."""

import pytest

from app.core.db import get_db
from app.events.services import get_event, get_event_detail


@pytest.fixture
def visibility_db(app):
    """Izole veritabaninda yayinda ve taslak etkinlikleri hazirlar."""
    with app.app_context():
        db = get_db()
        for user_id, role in [
            (190, "organizer"),
            (191, "organizer"),
            (192, "participant"),
            (193, "admin"),
        ]:
            db.execute(
                "INSERT INTO users (id, email, password_hash, role) VALUES (?, ?, 'testhash', ?)",
                (user_id, f"tg190_{user_id}@example.com", role),
            )

        db.execute(
            "INSERT INTO venues (id, name, address, capacity) VALUES (?, ?, ?, ?)",
            (190, "Bilim Salonu", "Iğdır Merkez", 100),
        )

        for event_id, status, organizer_id in [
            (190, "draft", 190),
            (191, "published", 190),
        ]:
            db.execute(
                """INSERT INTO events
                   (id, title, category, venue_id, start_time, end_time,
                    capacity, price, status, organizer_id)
                   VALUES (?, ?, 'Egitim', 190, ?, ?, 50, 0, ?, ?)""",
                (
                    event_id,
                    f"TG-190 Etkinlik {event_id}",
                    "2026-12-10T10:00",
                    "2026-12-10T12:00",
                    status,
                    organizer_id,
                ),
            )
        db.commit()
        yield db


@pytest.mark.parametrize(
    "user_id,user_role",
    [
        (None, None),  # Anonim
        (192, "participant"),
        (190, "organizer"),
        (191, "organizer"),
        (193, "admin"),
    ],
)
def test_published_event_is_visible_to_everyone(visibility_db, user_id, user_role):
    event = get_event_detail(visibility_db, 191, user_id=user_id, user_role=user_role)
    assert event is not None
    assert event["status"] == "published"
    assert event["venue_name"] == "Bilim Salonu"
    assert event["venue_address"] == "Iğdır Merkez"
    assert event["venue_capacity"] == 100
    assert event["price"] == 0.0


@pytest.mark.parametrize(
    "user_id,user_role",
    [(190, "organizer"), (193, "admin")],
)
def test_draft_is_visible_to_owner_or_admin(visibility_db, user_id, user_role):
    event = get_event_detail(visibility_db, 190, user_id=user_id, user_role=user_role)
    assert event is not None
    assert event["status"] == "draft"
    assert event["organizer_id"] == 190


@pytest.mark.parametrize(
    "user_id,user_role",
    [
        (None, None),
        (190, None),
        (None, "admin"),
        (0, "admin"),
        (True, "admin"),
        (192, "participant"),
        (190, "participant"),  # ID sahibi olsa bile rolu organizer olmali.
        (191, "organizer"),  # Baska organizator kendi olmayan taslagi goremez.
    ],
)
def test_draft_is_hidden_from_unauthorized_users(visibility_db, user_id, user_role):
    assert get_event_detail(visibility_db, 190, user_id=user_id, user_role=user_role) is None


@pytest.mark.parametrize("event_id", [None, True, "190", 0, -1, 99999, 2.5])
def test_unknown_or_invalid_event_id_returns_none(visibility_db, event_id):
    assert get_event_detail(visibility_db, event_id, user_id=193, user_role="admin") is None


def test_legacy_get_event_still_reads_drafts_for_internal_operations(visibility_db):
    """TG-171/172/173 yayinlama ve taslak akislarinin okuma davranisi korunur."""
    assert get_event(visibility_db, 190)["status"] == "draft"


def test_visibility_query_does_not_change_event_data(visibility_db):
    """Gorunurluk kontrolu kayit yazmaz, status degistirmez."""
    before = get_event(visibility_db, 190)
    assert get_event_detail(visibility_db, 190, user_id=192, user_role="participant") is None
    after = get_event(visibility_db, 190)
    assert before == after
