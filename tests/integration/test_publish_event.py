"""POST /events/<int:event_id>/publish entegrasyon testleri (TG-174, PB-04).

İş Kuralları ve Güvenlik:
- BR-1.5: Yalnızca yönetici onaylı organizatörler işlem yapabilir (yetkisiz: 401/403).
- IDOR: Yalnızca etkinliğin sahibi organizatör yayınlayabilir (başka organizatör: 403).
- Zaten yayınlanmış veya taslak olmayan etkinlik yayınlanamaz (409 Conflict).
- Var olmayan etkinlik yayınlanamaz (404 Not Found).
- Geçersiz etkinlik ID'si reddedilir (400 Bad Request).
- Başarılı durumda etkinlik 'published' durumuna geçer, flash mesajı eklenir ve HTTP 200 döner.
"""

import pytest

from app.core.db import get_db

ORGANIZER = 10
OTHER_ORGANIZER = 11
UNAPPROVED = 12
PARTICIPANT = 13
ADMIN = 14


def _insert_users(db):
    users = [
        (ORGANIZER, "organizer", 1),
        (OTHER_ORGANIZER, "organizer", 1),
        (UNAPPROVED, "organizer", 0),
        (PARTICIPANT, "participant", 0),
        (ADMIN, "admin", 1),
    ]
    for uid, role, approved in users:
        db.execute(
            "INSERT INTO users (id, email, password_hash, role, organizer_approved) "
            "VALUES (?, ?, 'x', ?, ?)",
            (uid, f"u{uid}@example.com", role, approved),
        )


@pytest.fixture
def seeded_db(app):
    with app.app_context():
        db = get_db()
        db.execute("ALTER TABLE users ADD COLUMN organizer_approved BOOLEAN NOT NULL DEFAULT 0")
        db.execute(
            "INSERT INTO venues (id, name, address, capacity) VALUES (1, 'Ana Salon', 'Adres', 100)"
        )
        db.execute(
            "INSERT INTO venues (id, name, address, capacity) "
            "VALUES (2, 'Küçük Salon', 'Adres', 20)"
        )
        _insert_users(db)

        # 1 nolu taslak: ORGANIZER tarafından oluşturulmuş
        db.execute(
            "INSERT INTO events ("
            "id, title, category, venue_id, start_time, "
            "end_time, capacity, price, status, organizer_id"
            ") VALUES (1, 'Rock Festivali', 'Konser', 1, '2026-12-01T18:00', "
            "'2026-12-01T22:00', 80, 100.0, 'draft', ?)",
            (ORGANIZER,),
        )

        # 2 nolu yayınlanmış etkinlik: OTHER_ORGANIZER (Salon 1, 10:00 - 14:00)
        db.execute(
            "INSERT INTO events ("
            "id, title, category, venue_id, start_time, "
            "end_time, capacity, price, status, organizer_id"
            ") VALUES (2, 'Sabah Caz', 'Konser', 1, '2026-12-01T10:00', "
            "'2026-12-01T14:00', 50, 50.0, 'published', ?)",
            (OTHER_ORGANIZER,),
        )

        # 3 nolu taslak: ORGANIZER (Salon 1, 12:00 - 16:00 -> 2 nolu etkinlik ile çakışır)
        db.execute(
            "INSERT INTO events ("
            "id, title, category, venue_id, start_time, "
            "end_time, capacity, price, status, organizer_id"
            ") VALUES (3, 'Öğle Caz', 'Konser', 1, '2026-12-01T12:00', "
            "'2026-12-01T16:00', 40, 50.0, 'draft', ?)",
            (ORGANIZER,),
        )

        db.commit()
    return app


def login(client, user_id, role):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_email"] = f"u{user_id}@example.com"
        sess["user_role"] = role


def test_unauthenticated_user_cannot_publish(seeded_db, client):
    """Giriş yapmamış kullanıcı 401 Unauthorized alır."""
    response = client.post("/events/1/publish")
    assert response.status_code == 401
    assert response.get_json()["error"] == "Oturum açılmamış."


def test_participant_cannot_publish(seeded_db, client):
    """Participant rolündeki kullanıcı 403 Forbidden alır."""
    login(client, PARTICIPANT, "participant")
    response = client.post("/events/1/publish")
    assert response.status_code == 403
    assert "yetkiniz" in response.get_json()["error"].lower()


def test_unapproved_organizer_cannot_publish(seeded_db, client):
    """BR-1.5: Onaysız organizatör 403 Forbidden alır."""
    login(client, UNAPPROVED, "organizer")
    response = client.post("/events/1/publish")
    assert response.status_code == 403
    assert "onay" in response.get_json()["error"].lower()


def test_approved_organizer_can_publish_own_draft_json(seeded_db, client):
    """Onaylı organizatör kendi taslağını başarıyla yayınlar ve 200 JSON yanıtı alır."""
    login(client, ORGANIZER, "organizer")
    response = client.post("/events/1/publish", json={})

    assert response.status_code == 200
    data = response.get_json()
    assert "yayınlandı" in data["message"].lower()
    assert data["event"]["status"] == "published"
    assert data["event"]["id"] == 1

    with seeded_db.app_context():
        event = get_db().execute("SELECT status FROM events WHERE id = 1").fetchone()
        assert event["status"] == "published"


def test_approved_organizer_publish_html_redirect_and_flash(seeded_db, client):
    """Tarayıcı isteği (Accept: text/html) ile yayınlama yönlendirme ve flash mesajı üretir."""
    login(client, ORGANIZER, "organizer")
    response = client.post(
        "/events/1/publish",
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with client.session_transaction() as sess:
        flashes = sess.get("_flashes", [])
        assert any("başarıyla yayınlandı" in f[1] for f in flashes)


def test_idor_protection_cannot_publish_other_organizers_draft(seeded_db, client):
    """IDOR koruması: Organizatör başka bir organizatörün taslağını yayınlayamaz (403)."""
    # 1 nolu etkinlik ORGANIZER'a ait; OTHER_ORGANIZER yayınlamaya çalışıyor
    login(client, OTHER_ORGANIZER, "organizer")
    response = client.post("/events/1/publish")

    assert response.status_code == 403
    err = response.get_json()["error"].lower()
    assert "etkinlik sahibi" in err or "onay" in err or "yetki" in err

    with seeded_db.app_context():
        event = get_db().execute("SELECT status FROM events WHERE id = 1").fetchone()
        assert event["status"] == "draft"


def test_publish_nonexistent_event_returns_404(seeded_db, client):
    """Var olmayan etkinlik ID'si 404 döner."""
    login(client, ORGANIZER, "organizer")
    response = client.post("/events/999/publish")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Etkinlik bulunamadı."


def test_publish_already_published_event_returns_conflict(seeded_db, client):
    """Zaten yayınlanmış etkinlik tekrar yayınlanamaz (409 Conflict)."""
    login(client, OTHER_ORGANIZER, "organizer")
    response = client.post("/events/2/publish")

    assert response.status_code == 409
    assert any("taslak" in e.lower() for e in response.get_json().get("errors", []))


def test_publish_invalid_event_id_returns_bad_request(seeded_db, client):
    """Geçersiz etkinlik ID'si 400 Bad Request döner."""
    login(client, ORGANIZER, "organizer")
    response = client.post("/events/0/publish")

    assert response.status_code == 400
    assert any("geçersiz" in e.lower() for e in response.get_json().get("errors", []))


def test_publish_time_conflict_returns_conflict_409(seeded_db, client):
    """Zaman çakışması olan taslak yayınlanamaz, HTTP 409 ve hata mesajı döner (BR-2.4)."""
    login(client, ORGANIZER, "organizer")
    response = client.post("/events/3/publish")

    assert response.status_code == 409
    data = response.get_json()
    conflict_msg = "Aynı salonda bu saatlerde yayınlanmış başka bir etkinlik var."
    assert conflict_msg in data.get("errors", [])


def test_publish_time_conflict_html_redirect_and_flash(seeded_db, client):
    """Tarayıcı isteğinde zaman çakışması durumunda flash mesajı üretilir ve yönlendirilir."""
    login(client, ORGANIZER, "organizer")
    response = client.post(
        "/events/3/publish",
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with client.session_transaction() as sess:
        flashes = sess.get("_flashes", [])
        conflict_msg = "Aynı salonda bu saatlerde yayınlanmış başka bir etkinlik var."
        assert any(conflict_msg in f[1] for f in flashes)
