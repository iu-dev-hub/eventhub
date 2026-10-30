from app.events.services import create_venue, get_all_venues


def test_admin_can_create_venue(app):
    """Madde 3 & 7: Yönetici rolüyle geçerli bilgilerle salon

    oluşturma ve DB kaydı testi.
    """
    with app.app_context():
        from app.core.db import get_db

        db = get_db()

        success, venue, errors = create_venue(db, "PB02 Test Salonu", "Atatürk Bulvarı No:10", 300)
        assert success is True
        assert errors == []
        assert venue["name"] == "PB02 Test Salonu"
        assert venue["capacity"] == 300


def test_missing_venue_information_rejected(app):
    """Madde 6: Salon adı, adresi veya kapasitesi eksik

    olduğunda reddedildiğini doğrular.
    """
    with app.app_context():
        from app.core.db import get_db

        db = get_db()

        # Eksik Ad
        success, _, errors = create_venue(db, "", "Adres", 100)
        assert success is False

        # Eksik Adres
        success, _, errors = create_venue(db, "Salon Adı", "", 100)
        assert success is False

        # Eksik Kapasite
        success, _, errors = create_venue(db, "Salon Adı", "Adres", None)
        assert success is False


def test_venue_listing_and_retrieval(app):
    """Madde 8: Salon listeleme işleminin kayıtlı salonların ad,

    adres ve kapasitesini doğru gösterdiğini doğrular.
    """
    with app.app_context():
        from app.core.db import get_db

        db = get_db()

        create_venue(db, "Liste Test Salonu", "Çankaya Ankara", 150)

        venues = get_all_venues()
        found = next((v for v in venues if v["name"] == "Liste Test Salonu"), None)

        assert found is not None
        assert found["address"] == "Çankaya Ankara"
        assert found["capacity"] == 150


def test_invalid_capacity_values(app):
    """Geçersiz kapasite (0 veya negatif) durumlarının reddedildiğini doğrular."""
    with app.app_context():
        from app.core.db import get_db

        db = get_db()

        success, _, _ = create_venue(db, "Sıfır Kapasite", "Adres", 0)
        assert success is False

        success, _, _ = create_venue(db, "Negatif Kapasite", "Adres", -10)
        assert success is False
