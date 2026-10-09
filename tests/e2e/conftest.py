"""Live server for E2E tests.

Testler başlamadan uygulama boş bir test veritabanıyla rastgele bir portta
arka planda başlatılır. Playwright'ın `page.goto("/")` gibi göreli adresleri
bu sunucuya gider. Sunucuyu elle başlatmanız gerekmez.
"""

import threading

import pytest
from werkzeug.serving import make_server

from app import create_app
from app.core.db import init_db


@pytest.fixture(scope="session")
def base_url(tmp_path_factory):
    database = tmp_path_factory.mktemp("e2e") / "e2e.sqlite"
    app = create_app({"TESTING": True, "DATABASE": str(database)})
    with app.app_context():
        init_db()

    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
