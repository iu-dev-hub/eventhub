"""HTML/JSON sözleşme tutarlılığı ve Sprint 5 regresyon doğrulama testleri (TG-197, PB-07 / #31).

Kapsam:
- Aynı yayınlanmış etkinlik için `Accept: text/html` isteğinin HTML sayfa,
  `Accept: application/json` isteğinin ise sözleşmeye uygun geçerli JSON nesnesi döndürdüğünün
  parametrik testlerle doğrulanması.
- `detail.html` sayfasındaki `Etkinlikler Listesine Dön` bağlantısının ve organizatör görünümündeki
  aksiyonların (`Yayınla` formu/butonu görünürlük kuralları) doğru render edildiğinin kontrolü.
- Sprint 1-5 (PB-02 salon oluşturma -> PB-08 taslak etkinlik oluşturma -> PB-04 etkinlik yayınlama
  -> PB-07 HTML ve JSON detay görüntüleme) uçtan uca regresyon akışının doğrulanması.
"""

import pytest

from app.core.db import get_db

OWNER_ORGANIZER = 10
OTHER_ORGANIZER = 11
PARTICIPANT = 12
ADMIN = 13

PUBLISHED_EVENT_ID = 701
DRAFT_EVENT_ID = 702

BROWSER_HTML_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"


@pytest.fixture
def contract_db(app):
    """Sözleşme ve regresyon testleri için kullanıcı, salon ve etkinlik verilerini hazırlar."""
    with app.app_context():
        db = get_db()
        users = [
            (OWNER_ORGANIZER, "owner197@example.com", "organizer", 1),
            (OTHER_ORGANIZER, "other197@example.com", "organizer", 1),
            (PARTICIPANT, "part197@example.com", "participant", 0),
            (ADMIN, "admin197@example.com", "admin", 1),
        ]
        for uid, email, role, approved in users:
            db.execute(
                "INSERT INTO users (id, email, password_hash, role, organizer_approved) "
                "VALUES (?, ?, 'hash', ?, ?)",
                (uid, email, role, approved),
            )

        db.execute(
            "INSERT INTO venues (id, name, address, capacity) VALUES (1, ?, ?, ?)",
            ("Atatürk Kültür Merkezi", "Taksim, Beyoğlu / İstanbul", 500),
        )

        cols = (
            "id, title, category, venue_id, start_time, end_time, "
            "capacity, price, status, organizer_id"
        )
        db.execute(
            f"INSERT INTO events ({cols}) VALUES (?, ?, ?, 1, ?, ?, ?, ?, 'published', ?)",
            (
                PUBLISHED_EVENT_ID,
                "Ulusal Yazılım Mimarisi Konferansı",
                "Konferans",
                "2026-12-22T09:30",
                "2026-12-22T17:30",
                450,
                175.0,
                OWNER_ORGANIZER,
            ),
        )
        db.execute(
            f"INSERT INTO events ({cols}) VALUES (?, ?, ?, 1, ?, ?, ?, ?, 'draft', ?)",
            (
                DRAFT_EVENT_ID,
                "Yayın Bekleyen Taslak Seminer",
                "Eğitim",
                "2026-12-24T10:00",
                "2026-12-24T12:00",
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


@pytest.mark.parametrize(
    ("accept_header", "expected_mode"),
    [
        ("text/html", "html"),
        (BROWSER_HTML_ACCEPT, "html"),
        ("text/html;q=0.9, application/json;q=0.4", "html"),
        ("application/json", "json"),
        ("application/json, text/plain, */*", "json"),
        ("text/html;q=0.3, application/json;q=0.9", "json"),
    ],
)
def test_same_published_event_serves_consistent_html_and_json_by_accept_header(
    contract_db, client, accept_header, expected_mode
):
    """TC-197-01 · PB-07: Aynı yayınlanmış etkinlik Accept başlığına göre HTML veya JSON döner."""
    resp = client.get(
        f"/events/{PUBLISHED_EVENT_ID}",
        headers={"Accept": accept_header},
    )
    assert resp.status_code == 200

    if expected_mode == "html":
        assert resp.mimetype == "text/html"
        assert not resp.is_json
        html = resp.get_data(as_text=True)
        assert "Ulusal Yazılım Mimarisi Konferansı" in html
        assert "Konferans" in html
        assert "Atatürk Kültür Merkezi" in html
        assert "Taksim, Beyoğlu / İstanbul" in html
        assert "2026-12-22T09:30" in html
        assert "2026-12-22T17:30" in html
        assert "450 Kişi" in html
        assert "500 Kişi" in html
        assert "175 TL" in html
        assert "Yayında" in html
    else:
        assert resp.mimetype == "application/json"
        assert resp.is_json
        payload = resp.get_json()
        assert payload == {
            "id": PUBLISHED_EVENT_ID,
            "title": "Ulusal Yazılım Mimarisi Konferansı",
            "category": "Konferans",
            "venue_id": 1,
            "start_time": "2026-12-22T09:30",
            "end_time": "2026-12-22T17:30",
            "capacity": 450,
            "price": 175.0,
            "status": "published",
            "organizer_id": OWNER_ORGANIZER,
            "venue_name": "Atatürk Kültür Merkezi",
            "venue_address": "Taksim, Beyoğlu / İstanbul",
            "venue_capacity": 500,
        }


def test_detail_html_back_to_events_list_link_renders_and_navigates(contract_db, client):
    """TC-197-02 · PB-07: detail.html içindeki 'Etkinlikler Listesine Dön' bağlantısı çalışır."""
    detail_resp = client.get(
        f"/events/{PUBLISHED_EVENT_ID}",
        headers={"Accept": "text/html"},
    )
    assert detail_resp.status_code == 200
    detail_html = detail_resp.get_data(as_text=True)

    assert "Etkinlikler Listesine Dön" in detail_html
    assert 'class="back-link"' in detail_html
    assert 'href="/events/"' in detail_html

    list_resp = client.get("/events/", headers={"Accept": "text/html"})
    assert list_resp.status_code == 200
    assert "Ulusal Yazılım Mimarisi Konferansı" in list_resp.get_data(as_text=True)


def test_detail_html_organizer_actions_render_only_for_draft_owner(contract_db, client):
    """TC-197-03 · PB-07 & PB-04: detail.html'de Yayınla aksiyonu yalnızca taslak sahibine çıkar."""
    # 1. Taslak sahibi organizatör taslak detayında "Yayınla" formunu ve butonunu görür
    _login(client, OWNER_ORGANIZER, "organizer")
    owner_draft_html = client.get(
        f"/events/{DRAFT_EVENT_ID}",
        headers={"Accept": "text/html"},
    ).get_data(as_text=True)
    assert "Yayın Bekleyen Taslak Seminer" in owner_draft_html
    assert "Taslak" in owner_draft_html
    assert f'action="/events/{DRAFT_EVENT_ID}/publish"' in owner_draft_html
    assert "btn-publish" in owner_draft_html
    assert "Yayınla" in owner_draft_html

    # 2. Taslak sahibi organizatör zaten yayınlanmış etkinlik detayında "Yayınla" butonu görmez
    owner_pub_html = client.get(
        f"/events/{PUBLISHED_EVENT_ID}",
        headers={"Accept": "text/html"},
    ).get_data(as_text=True)
    assert f'action="/events/{PUBLISHED_EVENT_ID}/publish"' not in owner_pub_html
    assert "btn-publish" not in owner_pub_html

    # 3. Admin taslak detayını görebilir ama "Yayınla" butonunu görmez
    _login(client, ADMIN, "admin")
    admin_draft_html = client.get(
        f"/events/{DRAFT_EVENT_ID}",
        headers={"Accept": "text/html"},
    ).get_data(as_text=True)
    assert "Yayın Bekleyen Taslak Seminer" in admin_draft_html
    assert f'action="/events/{DRAFT_EVENT_ID}/publish"' not in admin_draft_html
    assert "btn-publish" not in admin_draft_html

    # 4. Başka bir organizatör yayınlanmış etkinlik detayında "Yayınla" butonu görmez
    _login(client, OTHER_ORGANIZER, "organizer")
    other_pub_html = client.get(
        f"/events/{PUBLISHED_EVENT_ID}",
        headers={"Accept": "text/html"},
    ).get_data(as_text=True)
    assert "btn-publish" not in other_pub_html


def test_cross_sprint_regression_venue_to_draft_to_publish_to_html_and_json_detail(
    contract_db, client
):
    """TC-197-04: Sprint 2-5 uçtan uca regresyon (PB-02 -> PB-08 -> PB-04 -> PB-07 HTML & JSON)."""
    # 1. PB-02: Admin yeni bir salon oluşturur
    _login(client, ADMIN, "admin")
    venue_resp = client.post(
        "/events/venues",
        json={
            "name": "Sprint 5 Regresyon Salonu",
            "address": "Mühendislik Fakültesi Kampüsü",
            "capacity": 90,
        },
    )
    assert venue_resp.status_code == 201
    venue_id = venue_resp.get_json()["id"]

    # 2. PB-08: Onaylı organizatör bu salonda yeni bir taslak etkinlik oluşturur
    _login(client, OWNER_ORGANIZER, "organizer")
    create_resp = client.post(
        "/events/create",
        data={
            "title": "Sprint 5 Regresyon Zirvesi",
            "category": "Eğitim",
            "venue_id": str(venue_id),
            "start_time": "2026-12-30T10:00",
            "end_time": "2026-12-30T13:00",
            "capacity": "75",
            "price": "0",
        },
        follow_redirects=True,
    )
    assert create_resp.status_code == 200
    assert "Taslak etkinlik kaydedildi" in create_resp.get_data(as_text=True)

    with contract_db.app_context():
        row = (
            get_db()
            .execute("SELECT id FROM events WHERE title = ?", ("Sprint 5 Regresyon Zirvesi",))
            .fetchone()
        )
        assert row is not None
        new_event_id = row["id"]

    # 3. PB-04: Organizatör taslak detay sayfasındaki Yayınla aksiyonunu çalıştırır
    pub_resp = client.post(
        f"/events/{new_event_id}/publish",
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert pub_resp.status_code == 200
    assert "Etkinlik başarıyla yayınlandı" in pub_resp.get_data(as_text=True)

    # 4. PB-07: Katılımcı aynı etkinliği hem HTML hem JSON sözleşmesiyle tutarlı olarak okur
    _login(client, PARTICIPANT, "participant")
    html_detail = client.get(f"/events/{new_event_id}", headers={"Accept": "text/html"})
    assert html_detail.status_code == 200
    assert html_detail.mimetype == "text/html"
    html_text = html_detail.get_data(as_text=True)
    assert "Sprint 5 Regresyon Zirvesi" in html_text
    assert "Sprint 5 Regresyon Salonu" in html_text
    assert "Mühendislik Fakültesi Kampüsü" in html_text
    assert "75 Kişi" in html_text
    assert "90 Kişi" in html_text
    assert "Ücretsiz" in html_text
    assert "btn-publish" not in html_text

    json_detail = client.get(f"/events/{new_event_id}", headers={"Accept": "application/json"})
    assert json_detail.status_code == 200
    assert json_detail.mimetype == "application/json"
    json_data = json_detail.get_json()
    assert json_data["id"] == new_event_id
    assert json_data["title"] == "Sprint 5 Regresyon Zirvesi"
    assert json_data["status"] == "published"
    assert json_data["venue_name"] == "Sprint 5 Regresyon Salonu"
    assert json_data["venue_address"] == "Mühendislik Fakültesi Kampüsü"
    assert json_data["venue_capacity"] == 90
    assert json_data["capacity"] == 75
    assert json_data["price"] == 0.0
