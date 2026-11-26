"""GET /events/<int:event_id> HTML ve JSON içerik pazarlığı entegrasyon testleri (TG-193)."""

import pytest

from app.core.db import get_db

ORGANIZER = 20
OTHER_ORGANIZER = 21
PARTICIPANT = 22
ADMIN = 23

BROWSER_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"


@pytest.fixture
def negotiation_db(app):
    """Ücretli, ücretsiz ve taslak etkinlikler ile farklı rollerde kullanıcılar hazırlar."""
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
                (uid, f"tg193_{uid}@example.com", role),
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
            "(201, 'Açık Ücretli Konser', 'Konser', 1, '2026-12-20T20:00', "
            "'2026-12-20T23:00', 180, 150.0, 'published', ?)",
            (ORGANIZER,),
        )
        db.execute(
            f"INSERT INTO events ({cols}) VALUES "
            "(202, 'Ücretsiz Bilim Semineri', 'Eğitim', 1, '2026-12-22T14:00', "
            "'2026-12-22T16:00', 100, 0.0, 'published', ?)",
            (ORGANIZER,),
        )
        db.execute(
            f"INSERT INTO events ({cols}) VALUES "
            "(203, 'Gizli Taslak Atölye', 'Atölye', 1, '2026-12-25T10:00', "
            "'2026-12-25T12:00', 50, 75.0, 'draft', ?)",
            (ORGANIZER,),
        )
        db.commit()
    return app


def login(client, user_id, role):
    """Test istemcisinde oturum açar."""
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_email"] = f"tg193_{user_id}@example.com"
        sess["user_role"] = role


@pytest.mark.parametrize("accept_header", ["text/html", BROWSER_ACCEPT])
@pytest.mark.parametrize(
    ("user_id", "role"),
    [
        (None, None),
        (PARTICIPANT, "participant"),
        (OTHER_ORGANIZER, "organizer"),
        (ADMIN, "admin"),
    ],
)
def test_published_paid_event_returns_html_for_html_accept(
    negotiation_db, client, user_id, role, accept_header
):
    """Yayınlanmış ücretli etkinlik HTML isteğinde detail.html ile 200 döner."""
    if user_id is not None:
        login(client, user_id, role)

    response = client.get("/events/201", headers={"Accept": accept_header})
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert not response.is_json

    html = response.get_data(as_text=True)
    assert "Açık Ücretli Konser" in html
    assert "Konser" in html
    assert "Merkez Salon" in html
    assert "Beyazıt Kampüsü, İstanbul" in html
    assert "250 Kişi" in html
    assert "180 Kişi" in html
    assert "150 TL" in html
    assert "Yayında" in html
    assert 'href="/events/"' in html
    assert "/events/201/publish" not in html


@pytest.mark.parametrize("accept_header", ["text/html", BROWSER_ACCEPT])
def test_published_free_event_returns_html_with_ucretsiz(negotiation_db, client, accept_header):
    """Yayınlanmış ücretsiz etkinlik HTML isteğinde 'Ücretsiz' fiyatıyla 200 döner."""
    response = client.get("/events/202", headers={"Accept": accept_header})
    assert response.status_code == 200
    assert response.mimetype == "text/html"

    html = response.get_data(as_text=True)
    assert "Ücretsiz Bilim Semineri" in html
    assert "Ücretsiz" in html
    assert "Yayında" in html


@pytest.mark.parametrize("headers", [{"Accept": "application/json"}, {"Accept": "*/*"}, {}])
def test_published_event_returns_json_for_api_or_default_accept(negotiation_db, client, headers):
    """API Accept, */* veya Accept başlığı olmadan istek yapıldığında 200 JSON döner."""
    response = client.get("/events/201", headers=headers)
    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert response.is_json

    data = response.get_json()
    assert data["id"] == 201
    assert data["title"] == "Açık Ücretli Konser"
    assert data["status"] == "published"
    assert data["venue_name"] == "Merkez Salon"


@pytest.mark.parametrize("accept_header", ["text/html", BROWSER_ACCEPT])
def test_draft_event_html_for_owner_organizer_shows_publish_form(
    negotiation_db, client, accept_header
):
    """Taslak etkinlik sahibi olan organizatöre HTML'de Yayınla formuyla 200 döner."""
    login(client, ORGANIZER, "organizer")

    response = client.get("/events/203", headers={"Accept": accept_header})
    assert response.status_code == 200
    assert response.mimetype == "text/html"

    html = response.get_data(as_text=True)
    assert "Gizli Taslak Atölye" in html
    assert "Taslak" in html
    assert "75 TL" in html
    assert "/events/203/publish" in html
    assert "Yayınla" in html


@pytest.mark.parametrize("accept_header", ["text/html", BROWSER_ACCEPT])
def test_draft_event_html_for_admin_hides_publish_form(negotiation_db, client, accept_header):
    """Taslak etkinlik admine HTML 200 döner ancak Yayınla formu göstermez."""
    login(client, ADMIN, "admin")

    response = client.get("/events/203", headers={"Accept": accept_header})
    assert response.status_code == 200
    assert response.mimetype == "text/html"

    html = response.get_data(as_text=True)
    assert "Gizli Taslak Atölye" in html
    assert "Taslak" in html
    assert "/events/203/publish" not in html
    assert "btn-publish" not in html


@pytest.mark.parametrize("accept_header", ["text/html", BROWSER_ACCEPT])
@pytest.mark.parametrize(
    ("user_id", "role"),
    [
        (None, None),
        (PARTICIPANT, "participant"),
        (OTHER_ORGANIZER, "organizer"),
        (ORGANIZER, "participant"),
    ],
)
def test_draft_event_html_returns_404_page_without_leaking_for_unauthorized(
    negotiation_db, client, user_id, role, accept_header
):
    """Yetkisiz kullanıcı HTML isteğinde 404 not_found sayfası görür, veri sızdırılmaz."""
    if user_id is not None or role is not None:
        login(client, user_id, role)

    response = client.get("/events/203", headers={"Accept": accept_header})
    assert response.status_code == 404
    assert response.mimetype == "text/html"
    assert not response.is_json

    html = response.get_data(as_text=True)
    assert "Etkinlik bulunamadı" in html
    assert 'href="/events/"' in html
    assert "Gizli Taslak Atölye" not in html
    assert "Merkez Salon" not in html
    assert "Beyazıt Kampüsü" not in html
    assert "/events/203/publish" not in html


@pytest.mark.parametrize("accept_header", ["text/html", BROWSER_ACCEPT])
def test_nonexistent_event_html_returns_404_page_without_redirect(
    negotiation_db, client, accept_header
):
    """Var olmayan etkinlik HTML isteğinde yönlendirme yapmadan 404 sayfası döner."""
    response = client.get("/events/99999", headers={"Accept": accept_header})
    assert response.status_code == 404
    assert response.mimetype == "text/html"
    assert not response.is_json

    html = response.get_data(as_text=True)
    assert "Etkinlik bulunamadı" in html
    assert 'href="/events/"' in html


@pytest.mark.parametrize("headers", [{"Accept": "application/json"}, {"Accept": "*/*"}, {}])
@pytest.mark.parametrize(
    ("event_id", "user_id", "role"),
    [
        (99999, None, None),
        (99999, ADMIN, "admin"),
        (203, None, None),
        (203, PARTICIPANT, "participant"),
        (203, OTHER_ORGANIZER, "organizer"),
    ],
)
def test_missing_or_unauthorized_event_returns_404_json_for_api_accept(
    negotiation_db, client, event_id, user_id, role, headers
):
    """Var olmayan veya yetkisiz etkinlik JSON/*/* veya başlık yokken 404 JSON döner."""
    if user_id is not None:
        login(client, user_id, role)

    response = client.get(f"/events/{event_id}", headers=headers)
    assert response.status_code == 404
    assert response.mimetype == "application/json"
    assert response.get_json() == {"error": "Etkinlik bulunamadı."}
    assert "Gizli Taslak Atölye" not in response.get_data(as_text=True)


@pytest.mark.parametrize(
    "accept_header",
    [
        "application/xhtml+xml",
        "text/html;q=0.9, application/json;q=0.5",
        "text/html,application/xhtml+xml,*/*",
    ],
)
def test_accept_header_quality_edge_cases_prefer_html(negotiation_db, client, accept_header):
    """XHTML veya JSON'dan yüksek q değerine sahip HTML Accept başlıkları HTML döner."""
    response = client.get("/events/201", headers={"Accept": accept_header})
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert not response.is_json
    assert "Açık Ücretli Konser" in response.get_data(as_text=True)


@pytest.mark.parametrize(
    "accept_header",
    [
        "",
        "text/html;q=0",
        "text/html;q=0, */*;q=0.8",
        "text/html;q=0.5, application/json;q=0.9",
        "text/html, application/json",
    ],
)
def test_accept_header_quality_edge_cases_prefer_json(negotiation_db, client, accept_header):
    """q=0, JSON'dan düşük q, eşit q veya boş Accept başlıkları güvenli JSON döner."""
    response = client.get("/events/201", headers={"Accept": accept_header})
    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert response.is_json
    assert response.get_json()["id"] == 201
