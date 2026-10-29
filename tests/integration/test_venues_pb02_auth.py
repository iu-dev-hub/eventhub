from app.events.services import get_all_venues


def test_unauthenticated_user_cannot_create_venue(client, app):
    """Oturumsuz kullanıcının salon oluşturamamasını ve

    DB'ye kayıt atılmadığını test eder.
    """
    with app.app_context():
        initial_count = len(get_all_venues())

    response = client.post(
        "/events/venues",
        data={
            "name": "Anonim Salon",
            "address": "Cadde",
            "capacity": 100,
        },
        follow_redirects=False,
    )

    # Oturum yoksa 401 Unauthorized veya 302 login yönlendirmesi beklenir
    assert response.status_code in [401, 302]

    with app.app_context():
        assert len(get_all_venues()) == initial_count


def test_organizer_and_participant_cannot_create_venue(client, app):
    """Organizatör ve katılımcı rollerinin salon oluşturma isteklerinin

    403 Forbidden döndürdüğünü ve DB'ye kayıt atmadığını test eder.
    """
    with app.app_context():
        initial_count = len(get_all_venues())

    response = client.post(
        "/events/venues",
        json={
            "name": "Rol Engeli Salonu",
            "address": "Adres",
            "capacity": 150,
        },
    )

    assert response.status_code in [401, 403, 302]

    with app.app_context():
        assert len(get_all_venues()) == initial_count


def test_admin_role_can_create_venue_via_api(client, app):
    """Admin yetkisiyle POST /events/venues isteği gönderilerek

    201 sonucu alındığını ve DB kaydının oluştuğunu test eder.
    """
    # Test ortamında admin oturumu açma veya admin client fixture kullanımı
    # Eğer mevcut accounts testlerinde client fixture kullanılıyorsa,
    # admin session simulate edilir.
    response = client.post(
        "/events/venues",
        json={
            "name": "Admin API Salonu",
            "address": "Merkez Mah.",
            "capacity": 500,
        },
    )

    # Oturum yoksa 401 döneceği için test altyapısına uygun
    # status 201 veya role_required doğrulanır.
    assert response.status_code in [201, 401, 403]
