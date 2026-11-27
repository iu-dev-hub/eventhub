"""Taslak gizliliği, olmayan etkinlik (404) ve rol bazlı erişim testleri (TG-196, PB-07 / #31).

Kapsam:
- Taslak (draft) durumundaki bir etkinliğe anonim kullanıcı, participant ve başka bir organizer
  ile HTML ve JSON istekleri atıldığında 404 döndüğünün ve etkinlik başlığı/bilgilerinin yanıtta
  yer almadığının doğrulanması.
- Aynı taslak etkinliğe kendi sahibi olan organizer ve admin rolüyle erişildiğinde 200 OK ile
  detay sayfasının (hem HTML hem JSON) açıldığının doğrulanması.
- Veritabanında bulunmayan bir ID (GET /events/99999) için hem HTML hem JSON isteklerinde 404
  döndüğünün doğrulanması.
"""

import pytest

from app.core.db import get_db

OWNER_ORGANIZER = 10
OTHER_ORGANIZER = 11
PARTICIPANT = 12
ADMIN = 13

DRAFT_ID = 501
PUBLISHED_ID = 502
MISSING_ID = 99999

HTML_HEADERS = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
JSON_HEADERS = {"Accept": "application/json"}


@pytest.fixture
def access_db(app):
    """Taslak ve yayınlanmış etkinlikler ile farklı rollerde kullanıcıları hazırlar."""
    with app.app_context():
        db = get_db()
        users = [
            (OWNER_ORGANIZER, "owner196@example.com", "organizer", 1),
            (OTHER_ORGANIZER, "other196@example.com", "organizer", 1),
            (PARTICIPANT, "part196@example.com", "participant", 0),
            (ADMIN, "admin196@example.com", "admin", 1),
        ]
        for uid, email, role, approved in users:
            db.execute(
                "INSERT INTO users (id, email, password_hash, role, organizer_approved) "
                "VALUES (?, ?, 'hash', ?, ?)",
                (uid, email, role, approved),
            )

        db.execute(
            "INSERT INTO venues (id, name, address, capacity) VALUES (1, ?, ?, ?)",
            ("Gizli Prova Salonu", "Özel Kampüs Binası Kat:3", 180),
        )

        cols = (
            "id, title, category, venue_id, start_time, end_time, "
            "capacity, price, status, organizer_id"
        )
        db.execute(
            f"INSERT INTO events ({cols}) VALUES (?, ?, ?, 1, ?, ?, ?, ?, 'draft', ?)",
            (
                DRAFT_ID,
                "Çok Gizli Lansman Taslağı",
                "Konferans",
                "2026-12-28T14:00",
                "2026-12-28T17:00",
                95,
                320.0,
                OWNER_ORGANIZER,
            ),
        )
        db.execute(
            f"INSERT INTO events ({cols}) VALUES (?, ?, ?, 1, ?, ?, ?, ?, 'published', ?)",
            (
                PUBLISHED_ID,
                "Herkese Açık Seminer",
                "Eğitim",
                "2026-12-29T10:00",
                "2026-12-29T12:00",
                120,
                0.0,
                OWNER_ORGANIZER,
            ),
        )
        db.commit()
    return app


def _login(client, user_id, role):
    if user_id is None:
        return
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_email"] = f"user{user_id}@example.com"
        sess["user_role"] = role


def _assert_no_draft_leak(raw_text):
    """Yanıt gövdesinde taslak etkinliğe ait hiçbir hassas bilginin sızmadığını doğrular."""
    for secret in (
        "Çok Gizli Lansman Taslağı",
        "Gizli Prova Salonu",
        "Özel Kampüs Binası Kat:3",
        "2026-12-28T14:00",
        "2026-12-28T17:00",
        "320 TL",
        "320.0",
    ):
        assert secret not in raw_text


@pytest.mark.parametrize(
    ("user_id", "role"),
    [
        (None, None),
        (PARTICIPANT, "participant"),
        (OTHER_ORGANIZER, "organizer"),
    ],
    ids=["anonymous", "participant", "other_organizer"],
)
def test_unauthorized_users_receive_404_html_for_draft_without_data_leak(
    access_db, client, user_id, role
):
    """TC-196-01 · PB-07: Anonim, participant ve başka organizer HTML isteğinde 404 alır."""
    _login(client, user_id, role)

    resp = client.get(f"/events/{DRAFT_ID}", headers=HTML_HEADERS)
    assert resp.status_code == 404
    assert "text/html" in resp.content_type

    html = resp.get_data(as_text=True)
    assert "Etkinlik bulunamadı" in html
    assert 'href="/events/"' in html
    _assert_no_draft_leak(html)


@pytest.mark.parametrize(
    ("user_id", "role"),
    [
        (None, None),
        (PARTICIPANT, "participant"),
        (OTHER_ORGANIZER, "organizer"),
    ],
    ids=["anonymous", "participant", "other_organizer"],
)
def test_unauthorized_users_receive_404_json_for_draft_without_data_leak(
    access_db, client, user_id, role
):
    """TC-196-02 · PB-07: Anonim, participant ve başka organizer JSON isteğinde 404 alır."""
    _login(client, user_id, role)

    resp = client.get(f"/events/{DRAFT_ID}", headers=JSON_HEADERS)
    assert resp.status_code == 404
    assert resp.is_json
    assert resp.get_json() == {"error": "Etkinlik bulunamadı."}
    _assert_no_draft_leak(resp.get_data(as_text=True))


@pytest.mark.parametrize(
    ("user_id", "role", "expect_publish_btn"),
    [
        (OWNER_ORGANIZER, "organizer", True),
        (ADMIN, "admin", False),
    ],
    ids=["owner_organizer", "admin"],
)
def test_owner_organizer_and_admin_can_view_draft_detail_html_200(
    access_db, client, user_id, role, expect_publish_btn
):
    """TC-196-03 · PB-07: Taslak sahibi organizer ve admin HTML detay sayfasını 200 OK ile açar."""
    _login(client, user_id, role)

    resp = client.get(f"/events/{DRAFT_ID}", headers=HTML_HEADERS)
    assert resp.status_code == 200
    assert "text/html" in resp.content_type

    html = resp.get_data(as_text=True)
    assert "Çok Gizli Lansman Taslağı" in html
    assert "Konferans" in html
    assert "Gizli Prova Salonu" in html
    assert "Özel Kampüs Binası Kat:3" in html
    assert "2026-12-28T14:00" in html
    assert "2026-12-28T17:00" in html
    assert "95 Kişi" in html
    assert "180 Kişi" in html
    assert "320 TL" in html
    assert "Taslak" in html

    if expect_publish_btn:
        assert f"/events/{DRAFT_ID}/publish" in html
    else:
        assert f"/events/{DRAFT_ID}/publish" not in html


@pytest.mark.parametrize(
    ("user_id", "role"),
    [
        (OWNER_ORGANIZER, "organizer"),
        (ADMIN, "admin"),
    ],
    ids=["owner_organizer", "admin"],
)
def test_owner_organizer_and_admin_can_view_draft_detail_json_200(access_db, client, user_id, role):
    """TC-196-04 · PB-07: Taslak sahibi organizer ve admin JSON detay isteğinde 200 OK alır."""
    _login(client, user_id, role)

    resp = client.get(f"/events/{DRAFT_ID}", headers=JSON_HEADERS)
    assert resp.status_code == 200
    assert resp.is_json

    data = resp.get_json()
    assert data["id"] == DRAFT_ID
    assert data["title"] == "Çok Gizli Lansman Taslağı"
    assert data["status"] == "draft"
    assert data["organizer_id"] == OWNER_ORGANIZER
    assert data["venue_name"] == "Gizli Prova Salonu"
    assert data["venue_address"] == "Özel Kampüs Binası Kat:3"
    assert data["capacity"] == 95
    assert data["price"] == 320.0


@pytest.mark.parametrize(
    ("user_id", "role"),
    [
        (None, None),
        (PARTICIPANT, "participant"),
        (OWNER_ORGANIZER, "organizer"),
        (ADMIN, "admin"),
    ],
    ids=["anonymous", "participant", "organizer", "admin"],
)
def test_nonexistent_event_id_returns_404_for_both_html_and_json(access_db, client, user_id, role):
    """TC-196-05 · PB-07: Olmayan ID (GET /events/99999) HTML ve JSON isteklerinde 404 döner."""
    _login(client, user_id, role)

    html_resp = client.get(f"/events/{MISSING_ID}", headers=HTML_HEADERS)
    assert html_resp.status_code == 404
    assert "text/html" in html_resp.content_type
    html_body = html_resp.get_data(as_text=True)
    assert "Etkinlik bulunamadı" in html_body
    assert 'href="/events/"' in html_body

    json_resp = client.get(f"/events/{MISSING_ID}", headers=JSON_HEADERS)
    assert json_resp.status_code == 404
    assert json_resp.is_json
    assert json_resp.get_json() == {"error": "Etkinlik bulunamadı."}
