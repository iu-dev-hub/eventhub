def test_events_index_page_loads(client):
    """Events ana sayfasının HTTP 200 yanıtı verdiğini doğrular."""
    response = client.get("/events/")
    assert response.status_code == 200
    assert b"Etkinlikler" in response.data