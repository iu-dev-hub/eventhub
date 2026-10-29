from app.core.db import get_db
from app.events.services import get_all_venues


def test_unauthenticated_user_cannot_create_venue(client, app):
    """Oturumsuz kullanıcının salon oluşturma isteğinde doğrudan

    401 Unauthorized döndüğünü ve DB'ye kayıt atılmadığını test eder.
    """
    with app.app_context():
        initial_count = len(get_all_venues())

    response = client.post(
        "/events/venues",
        json={
            "name": "Anonim Salon",
            "address": "Cadde",
            "capacity": 100,
        },
    )

    assert response.status_code == 401

    with app.app_context():
        assert len(get_all_venues()) == initial_count


def test_organizer_and_participant_cannot_create_venue(client, app):
    """Organizatör ve katılımcı rollerinin oturum açarak salon oluşturmaya

    çalıştığında 403 aldığını ve DB'ye kayıt atılmadığını test eder.
    """
    for idx, role in enumerate(["organizer", "participant"], start=20):
        with app.app_context():
            initial_count = len(get_all_venues())
            db = get_db()
            db.execute(
                "INSERT OR REPLACE INTO users (id, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (idx, f"{role}@test.com", "dummy_hash", role),
            )
            db.commit()

        with client.session_transaction() as sess:
            sess["user_id"] = idx
            sess["user_role"] = role
            sess["user_email"] = f"{role}@test.com"

        response = client.post(
            "/events/venues",
            json={
                "name": f"Rol Engeli Salonu {role}",
                "address": "Adres",
                "capacity": 150,
            },
        )

        assert response.status_code == 403

        with app.app_context():
            assert len(get_all_venues()) == initial_count


def test_admin_role_can_create_venue_via_api(client, app):
    """Admin rolüyle oturum açılarak POST /events/venues isteği atıldığında

    201 Created döndüğünü ve salonun DB'ye kaydedildiğini test eder.
    """
    with app.app_context():
        initial_count = len(get_all_venues())
        db = get_db()
        db.execute(
            "INSERT OR REPLACE INTO users (id, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (1, "admin_api@test.com", "dummy_hash", "admin"),
        )
        db.commit()

    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_role"] = "admin"
        sess["user_email"] = "admin_api@test.com"

    response = client.post(
        "/events/venues",
        json={
            "name": "Admin API Salonu PB02",
            "address": "Merkez Mah. No:1",
            "capacity": 500,
        },
    )

    assert response.status_code == 201

    with app.app_context():
        venues = get_all_venues()
        assert len(venues) == initial_count + 1
        created = next((v for v in venues if v["name"] == "Admin API Salonu PB02"), None)
        assert created is not None
        assert created["address"] == "Merkez Mah. No:1"
        assert created["capacity"] == 500
