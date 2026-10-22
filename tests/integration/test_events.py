def test_events_index_page_loads(client):
    """Events ana sayfasının HTTP 200 yanıtı verdiğini doğrular."""
    response = client.get("/events/")
    assert response.status_code == 200
    assert "Etkinlikler" in response.get_data(as_text=True)

def test_create_event_page_loads(client):
    """Sayfanın 200 HTTP koduyla açıldığını ve form elemanlarını içerdiğini test eder."""
    response = client.get("/events/create")
    assert response.status_code == 200
    
    html = response.get_data(as_text=True)
    assert "Etkinlik Oluştur" in html
    assert 'for="capacity"' in html  # Label var mı?
    assert 'name="title"' in html    # Input var mı?
    assert "Kontrol Et" in html      # Buton var mı?

def test_event_creation_success(client):
    """Kapasite sınırları içinde (50 ve 100) geçerli kayıt testleri."""
    # Formun yeni zorunlu alanları için geçerli örnek veri seti
    valid_data = {
        "title": "Konser", "category": "Konser", "venue": "Salon A", 
        "start_time": "2026-12-01T20:00", "end_time": "2026-12-01T23:00"
    }
    
    # 50 Kapasite ve Ücretli
    data1 = valid_data.copy()
    data1.update({"capacity": "50", "price": "100.0"})
    response1 = client.post("/events/create", data=data1, follow_redirects=True)
    assert "Etkinlik bilgileri doğrulandı" in response1.get_data(as_text=True)

    # 100 Kapasite (Sınır değer) ve Ücretsiz
    data2 = valid_data.copy()
    data2.update({"capacity": "100", "price": "0"})
    response2 = client.post("/events/create", data=data2, follow_redirects=True)
    assert "Ücretsiz etkinlik doğrulaması başarılı" in response2.get_data(as_text=True)

def test_event_creation_capacity_exceeded(client):
    """Kapasite 100'ü aştığında (101) hata dönmelidir."""
    data = {
        "title": "Büyük Konser", "category": "Konser", "venue": "Salon A", 
        "start_time": "2026-12-01T20:00", "end_time": "2026-12-01T23:00",
        "capacity": "101", "price": "50.0"
    }
    response = client.post("/events/create", data=data, follow_redirects=True)
    assert "salon kapasitesini (100) aşamaz" in response.get_data(as_text=True)

def test_event_creation_missing_fields(client):
    """Zorunlu alanlar eksik olduğunda hata dönmelidir."""
    # Sadece 2 alan gönderip diğerlerini bilerek boş bırakıyoruz
    response = client.post("/events/create", data={"capacity": "50", "price": ""}, follow_redirects=True)
    assert "Lütfen tüm zorunlu alanları doldurun" in response.get_data(as_text=True)