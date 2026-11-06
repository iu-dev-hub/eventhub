"""Events rotaları entegrasyon testleri (TG-121, PB-08; BR-1.5, BR-2.2, BR-2.3).

Form (TG-119) `venue_id` gönderir; route, TG-118 taslak servisine bağlıdır.
Accounts'ta kalıcı organizatör onay mekanizması henüz yok: onay sütunu test
veritabanına eklenir. Sütun yokken erişimin kapalı olduğu da test edilir.
"""

import pytest

from app.core.db import get_db

ORGANIZER = 10
OTHER_ORGANIZER = 11
UNAPPROVED = 12
PARTICIPANT = 13
ADMIN = 14

VALID = {
    "title": "Konser",
    "category": "Konser",
    "venue_id": "1",
    "start_time": "2026-12-01T20:00",
    "end_time": "2026-12-01T23:00",
    "capacity": "50",
    "price": "100.0",
}


def _insert_users(db, with_approval):
    users = [
        (ORGANIZER, "organizer", 1),
        (OTHER_ORGANIZER, "organizer", 1),
        (UNAPPROVED, "organizer", 0),
        (PARTICIPANT, "participant", 0),
        (ADMIN, "admin", 1),
    ]
    for uid, role, approved in users:
        if with_approval:
            db.execute(
                "INSERT INTO users (id, email, password_hash, role, organizer_approved) "
                "VALUES (?, ?, 'x', ?, ?)",
                (uid, f"u{uid}@example.com", role, approved),
            )
        else:
            db.execute(
                "INSERT INTO users (id, email, password_hash, role) VALUES (?, ?, 'x', ?)",
                (uid, f"u{uid}@example.com", role),
            )


@pytest.fixture
def seeded(app):
    """Salon A (kapasite 100) ve farklı rol/onay durumlarında kullanıcılar."""
    with app.app_context():
        db = get_db()
        db.execute("ALTER TABLE users ADD COLUMN organizer_approved BOOLEAN NOT NULL DEFAULT 0")
        db.execute(
            "INSERT INTO venues (id, name, address, capacity) VALUES (1,'Salon A','Adres',100)"
        )
        _insert_users(db, with_approval=True)
        db.commit()
    return app


def login(client, user_id, role):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_email"] = f"u{user_id}@example.com"
        sess["user_role"] = role


def event_count(app):
    with app.app_context():
        return get_db().execute("SELECT COUNT(*) FROM events").fetchone()[0]


def test_events_index_page_loads(client):
    response = client.get("/events/")
    assert response.status_code == 200
    assert "Etkinlikler" in response.get_data(as_text=True)


def test_create_event_page_loads_for_approved_organizer(seeded, client):
    login(client, ORGANIZER, "organizer")
    response = client.get("/events/create")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Etkinlik Oluştur" in html
    assert 'for="capacity"' in html
    assert 'name="title"' in html
    assert 'name="venue_id"' in html
    assert 'value="1"' in html  # salonlar veritabanından listelenir
    assert "Taslak Kaydet" in html


def test_draft_event_is_saved_with_venue_id_and_can_be_read_back(seeded, client):
    login(client, ORGANIZER, "organizer")
    response = client.post("/events/create", data=VALID, follow_redirects=True)
    assert "Taslak etkinlik kaydedildi" in response.get_data(as_text=True)

    event = client.get("/events/1").get_json()
    assert event["status"] == "draft"
    assert event["organizer_id"] == ORGANIZER
    assert event["venue_id"] == 1
    assert event["capacity"] == 50
    assert event["price"] == 100.0
    assert event["title"] == "Konser"


def test_free_event_at_venue_capacity_boundary_is_saved(seeded, client):
    login(client, ORGANIZER, "organizer")
    client.post("/events/create", data={**VALID, "capacity": "100", "price": "0"})
    assert event_count(seeded) == 1


def test_capacity_above_venue_capacity_is_rejected(seeded, client):
    login(client, ORGANIZER, "organizer")
    response = client.post(
        "/events/create", data={**VALID, "capacity": "101"}, follow_redirects=True
    )
    assert "salon kapasitesini (100) aşamaz" in response.get_data(as_text=True)
    assert event_count(seeded) == 0


def test_capacity_uses_real_venue_data_by_venue_id(seeded, client):
    with seeded.app_context():
        db = get_db()
        db.execute("INSERT INTO venues (id, name, address, capacity) VALUES (2,'Küçük','A',20)")
        db.commit()
    login(client, ORGANIZER, "organizer")
    response = client.post(
        "/events/create", data={**VALID, "venue_id": "2", "capacity": "30"}, follow_redirects=True
    )
    assert "salon kapasitesini (20) aşamaz" in response.get_data(as_text=True)
    assert event_count(seeded) == 0


@pytest.mark.parametrize("venue_id", ["999", "abc", "-1", "1 OR 1=1"])
def test_unknown_or_malformed_venue_id_is_rejected(seeded, client, venue_id):
    login(client, ORGANIZER, "organizer")
    response = client.post(
        "/events/create", data={**VALID, "venue_id": venue_id}, follow_redirects=True
    )
    assert "Seçilen salon bulunamadı" in response.get_data(as_text=True)
    assert event_count(seeded) == 0


def test_missing_fields_are_rejected(seeded, client):
    login(client, ORGANIZER, "organizer")
    response = client.post(
        "/events/create", data={"capacity": "50", "price": ""}, follow_redirects=True
    )
    assert "Lütfen tüm zorunlu alanları doldurun" in response.get_data(as_text=True)
    assert event_count(seeded) == 0


def test_end_before_start_is_rejected(seeded, client):
    login(client, ORGANIZER, "organizer")
    response = client.post(
        "/events/create", data={**VALID, "end_time": "2026-12-01T19:00"}, follow_redirects=True
    )
    assert "Bitiş zamanı başlangıç zamanından sonra olmalıdır" in response.get_data(as_text=True)
    assert event_count(seeded) == 0


def test_anonymous_cannot_create(seeded, client):
    assert client.get("/events/create").status_code == 401
    assert client.post("/events/create", data=VALID).status_code == 401
    assert event_count(seeded) == 0


@pytest.mark.parametrize(
    "user_id, role",
    [
        (PARTICIPANT, "participant"),
        (UNAPPROVED, "organizer"),  # BR-1.5: yalnızca organizer rolü yetmez
        (ADMIN, "admin"),
    ],
)
def test_unauthorized_users_cannot_create(seeded, client, user_id, role):
    login(client, user_id, role)
    assert client.get("/events/create").status_code == 403
    response = client.post("/events/create", data=VALID)
    assert response.status_code == 403
    assert response.get_json()["error"]
    assert event_count(seeded) == 0


def test_stale_session_role_does_not_grant_access(seeded, client):
    """Oturumda 'organizer' yazsa da veritabanında katılımcı olan kullanıcı engellenir."""
    login(client, PARTICIPANT, "organizer")
    assert client.post("/events/create", data=VALID).status_code == 403
    assert event_count(seeded) == 0


def test_without_approval_mechanism_organizer_is_denied(app, client):
    """Accounts onay sütunu yokken organizer bile kayıt yapamaz (güvenli varsayılan)."""
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO venues (id, name, address, capacity) VALUES (1,'Salon A','A',100)")
        _insert_users(db, with_approval=False)
        db.commit()
    login(client, ORGANIZER, "organizer")
    assert client.post("/events/create", data=VALID).status_code == 403
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0


def test_organizer_id_comes_from_session_not_form(seeded, client):
    login(client, ORGANIZER, "organizer")
    client.post("/events/create", data={**VALID, "organizer_id": str(OTHER_ORGANIZER)})
    assert client.get("/events/1").get_json()["organizer_id"] == ORGANIZER


def test_draft_is_hidden_from_others_but_visible_to_owner_and_admin(seeded, client):
    login(client, ORGANIZER, "organizer")
    client.post("/events/create", data=VALID)
    assert client.get("/events/1").status_code == 200

    login(client, OTHER_ORGANIZER, "organizer")
    assert client.get("/events/1").status_code == 404
    login(client, PARTICIPANT, "participant")
    assert client.get("/events/1").status_code == 404
    login(client, ADMIN, "admin")
    assert client.get("/events/1").status_code == 200


def test_event_detail_requires_login_and_handles_missing(seeded, client):
    assert client.get("/events/1").status_code == 401
    login(client, ORGANIZER, "organizer")
    assert client.get("/events/999").status_code == 404
