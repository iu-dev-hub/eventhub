def test_events_index_page_loads(client):
    """Events ana sayfasının HTTP 200 yanıtı verdiğini doğrular."""
    response = client.get("/events/")
    assert response.status_code == 200
    assert b"Etkinlikler" in response.data

def test_create_event_page_loads(client):
    """Sayfanın 200 HTTP koduyla açıldığını ve form elemanlarını içerdiğini test eder."""
    response = client.get("/events/create")
    assert response.status_code == 200
    
    html = response.get_data(as_text=True)
    assert "Etkinlik Oluştur" in html
    assert 'for="capacity"' in html  # Label var mı?
    assert 'name="title"' in html    # Input var mı?
    assert "Kontrol Et" in html      # Buton var mı?