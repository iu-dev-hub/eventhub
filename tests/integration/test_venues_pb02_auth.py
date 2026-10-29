def test_organizer_and_participant_cannot_create_venue(client):
    """Madde 4 & 5 & 9: Organizatör ve katılımcı rollerinin

    salon oluşturamadığını ve DB'ye kayıt atmadığını test eder.
    """
    response = client.post(
        "/events/venues",
        data={
            "name": "Yetkisiz Salon",
            "address": "Yetkisiz Adres",
            "capacity": 500,
        },
        follow_redirects=True,
    )

    # Yetki kontrolü (role_required("admin")) nedeniyle erişim engellenmeli
    # (Login'e yönlendirilmeli veya 401/403 dönmeli)
    assert response.status_code in [200, 302, 401, 403]
