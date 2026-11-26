"""GET /events/<int:event_id> rota-servis entegrasyon testleri (TG-192, PB-07 / #31)."""

import pytest

from app.core.db import get_db
from app.events import services

ORGANIZER = 10
OTHER_ORGANIZER = 11
PARTICIPANT = 12
ADMIN = 13


@pytest.fixture
def detail_route_db(app):
    """Yayınlanmış ve taslak etkinlikler ile farklı rollerde kullanıcılar hazırlar."""
    with app.app_context():
        db = get_db()
        for uid, role in [
            (ORGANIZER, "organizer"),
            (OTHER_ORGANIZER, "organizer"),
            (PARTICIPANT, "participant"),
            (ADMIN, "admin"),
        ]:
            db.execute(
                "INSERT INTO users (id, email, password_hash, role) VALUES (?, ?, 'x', ?)",
                (uid, f"tg192_{uid}@example.com", role),
            )

        db.execute(
            "INSERT INTO venues (id, name, address, capacity) VALUES (1, ?, ?, 250)",
            ("Merkez Salon", "Beyazıt Kampüsü, İstanbul"),
        )

        cols = (
            "id, title, category, venue_id, start_time, end_time, "
            "capacity, price, status, organizer_id"
        )
        db.execute(
            f"INSERT INTO events ({cols}) VALUES "
            "(101, 'Açık Konser', 'Konser', 1, '2026-12-20T20:00', "
            "'2026-12-20T23:00', 180, 150.0, 'published', ?)",
            (ORGANIZER,),
        )
        db.execute(
            f"INSERT INTO events ({cols}) VALUES "
            "(102, 'Gizli Taslak Konser', 'Eğitim', 1, '2026-12-21T10:00', "
            "'2026-12-21T12:00', 50, 0.0, 'draft', ?)",
            (ORGANIZER,),
        )
        db.commit()
    return app


def login(client, user_id, role):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_email"] = f"tg192_{user_id}@example.com"
        sess["user_role"] = role


@pytest.mark.parametrize(
    ("user_id", "role"),
    [
        (None, None),
        (PARTICIPANT, "participant"),
        (ORGANIZER, "organizer"),
        (OTHER_ORGANIZER, "organizer"),
        (ADMIN, "admin"),
    ],
)
def test_published_event_returns_200_json_for_all_roles(detail_route_db, client, user_id, role):
    """Yayınlanmış etkinlik anonim dahil tüm roller için salon alanlarıyla 200 JSON döner."""
    if user_id is not None:
        login(client, user_id, role)

    response = client.get("/events/101")
    assert response.status_code == 200

    data = response.get_json()
    assert data["id"] == 101
    assert data["title"] == "Açık Konser"
    assert data["status"] == "published"
    assert data["venue_name"] == "Merkez Salon"
    assert data["venue_address"] == "Beyazıt Kampüsü, İstanbul"
    assert data["venue_capacity"] == 250


@pytest.mark.parametrize(
    ("user_id", "role"),
    [
        (None, None),
        (PARTICIPANT, "participant"),
        (OTHER_ORGANIZER, "organizer"),
        (ORGANIZER, "participant"),
    ],
)
def test_draft_event_returns_404_without_leaking_for_unauthorized(
    detail_route_db, client, user_id, role
):
    """Taslak etkinlik anonim, katılımcı ve yetkisiz organizatöre veri sızdırmadan 404 döner."""
    if user_id is not None or role is not None:
        login(client, user_id, role)

    response = client.get("/events/102")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Etkinlik bulunamadı."}

    raw = response.get_data(as_text=True)
    assert "Gizli Taslak Konser" not in raw
    assert "Merkez Salon" not in raw


@pytest.mark.parametrize(
    ("user_id", "role"),
    [
        (ORGANIZER, "organizer"),
        (ADMIN, "admin"),
    ],
)
def test_draft_event_returns_200_json_for_owner_and_admin(detail_route_db, client, user_id, role):
    """Taslak etkinlik yalnızca sahibi olan organizatöre ve admine 200 JSON döner."""
    login(client, user_id, role)

    response = client.get("/events/102")
    assert response.status_code == 200

    data = response.get_json()
    assert data["id"] == 102
    assert data["title"] == "Gizli Taslak Konser"
    assert data["status"] == "draft"
    assert data["organizer_id"] == ORGANIZER
    assert data["venue_name"] == "Merkez Salon"


def test_nonexistent_event_returns_404_for_anonymous_and_authenticated(detail_route_db, client):
    """Var olmayan etkinlik ID'si anonim ve giriş yapmış kullanıcılar için 404 JSON döner."""
    anon_resp = client.get("/events/9999")
    assert anon_resp.status_code == 404
    assert anon_resp.get_json() == {"error": "Etkinlik bulunamadı."}

    login(client, ORGANIZER, "organizer")
    auth_resp = client.get("/events/9999")
    assert auth_resp.status_code == 404
    assert auth_resp.get_json() == {"error": "Etkinlik bulunamadı."}


def test_event_detail_route_delegates_to_service(detail_route_db, client, monkeypatch):
    """Rota doğrudan SQL yerine services.get_event_detail fonksiyonunu oturumla çağırır."""
    calls = []
    real_get_event_detail = services.get_event_detail

    def spy_get_event_detail(db, event_id, user_id=None, user_role=None):
        calls.append((event_id, user_id, user_role))
        return real_get_event_detail(db, event_id, user_id=user_id, user_role=user_role)

    monkeypatch.setattr(services, "get_event_detail", spy_get_event_detail)

    # 1. Anonim istek
    res_anon = client.get("/events/101")
    assert res_anon.status_code == 200
    assert calls[-1] == (101, None, None)

    # 2. Oturum açmış kullanıcı isteği
    login(client, ORGANIZER, "organizer")
    res_auth = client.get("/events/102")
    assert res_auth.status_code == 200
    assert calls[-1] == (102, ORGANIZER, "organizer")

    # 3. Servis None döndüğünde route 404 döner (ham SQL fallback yapılmaz)
    monkeypatch.setattr(services, "get_event_detail", lambda *args, **kwargs: None)
    res_hidden = client.get("/events/101")
    assert res_hidden.status_code == 404
    assert res_hidden.get_json() == {"error": "Etkinlik bulunamadı."}
