def test_event_creation_success(client):
    """Kapasite sınırları içinde (50 ve 100) geçerli kayıt testleri."""
    # 50 Kapasite ve Ücretli
    response = client.post("/events/create", data={"title": "Konser", "capacity": "50", "price": "100.0"}, follow_redirects=True)
    assert b"Do\xc4\x9frulama ba\xc5\x9far\xc4\xb1l\xc4\xb1." in response.data

    # 100 Kapasite (Sınır değer) ve Ücretsiz
    response2 = client.post("/events/create", data={"title": "Seminer", "capacity": "100", "price": "0"}, follow_redirects=True)
    assert b"\xc3\x9ccretsiz etkinlik do\xc4\x9frulamas\xc4\xb1 ba\xc5\x9far\xc4\xb1l\xc4\xb1" in response2.data

def test_event_creation_capacity_exceeded(client):
    """Kapasite 100'ü aştığında (101) hata dönmelidir."""
    response = client.post("/events/create", data={"title": "Büyük Konser", "capacity": "101", "price": "50.0"})
    assert b"salon kapasitesini (100) a\xc5\x9famaz." in response.data

def test_event_creation_missing_fields(client):
    """Zorunlu alanlar eksik olduğunda hata dönmelidir."""
    response = client.post("/events/create", data={"title": "", "capacity": "50", "price": ""})
    assert b"T\xc3\xbcm zorunlu alanlar\xc4\xb1n doldurulmas\xc4\xb1 gerekmektedir" in response.data