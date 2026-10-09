"""EXAMPLE integration tests using the Flask test client.

Tarayıcı açmadan HTTP istekleri gönderir; birim testlerden yavaş,
E2E testlerden çok daha hızlıdır.
"""


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "EventHub" in response.get_data(as_text=True)


def test_unknown_page_returns_404(client):
    assert client.get("/does-not-exist").status_code == 404


def test_init_db_command(app):
    """Komut satırı komutları da test edilebilir."""
    result = app.test_cli_runner().invoke(args=["init-db"])
    assert "Database initialized." in result.output
