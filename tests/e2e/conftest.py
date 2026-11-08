"""Live server for E2E tests.

Testler başlamadan uygulama boş bir test veritabanıyla rastgele bir portta
arka planda başlatılır. Playwright'ın `page.goto("/")` gibi göreli adresleri
bu sunucuya gider. Sunucuyu elle başlatmanız gerekmez.
"""

import threading

import pytest
from werkzeug.serving import make_server

from app import create_app
from app.accounts.services import register_user
from app.core.db import get_db, init_db

ORGANIZER_EMAIL = "e2e-organizer@example.com"
ORGANIZER_PASSWORD = "Parola12345"


@pytest.fixture(scope="session")
def base_url(tmp_path_factory):
    database = tmp_path_factory.mktemp("e2e") / "e2e.sqlite"
    app = create_app({"TESTING": True, "DATABASE": str(database)})
    with app.app_context():
        init_db()
        db = get_db()
        # TG-121: etkinlik oluşturmak için yönetici onaylı organizatör gerekir (BR-1.5).
        # Accounts'ta kalıcı onay mekanizması henüz yok; onay sütunu test veritabanına eklenir.
        db.execute("ALTER TABLE users ADD COLUMN organizer_approved BOOLEAN NOT NULL DEFAULT 0")
        user = register_user(ORGANIZER_EMAIL, ORGANIZER_PASSWORD, role="organizer")
        db.execute("UPDATE users SET organizer_approved = 1 WHERE id = ?", (user["id"],))
        # E2E testleri için test salonu (id=1, kapasite 100)
        db.execute(
            "INSERT OR IGNORE INTO venues (id, name, address, capacity) "
            "VALUES (1, 'Ana Salon', 'Ankara', 100)"
        )
        db.commit()

    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture
def organizer_page(page):
    """Onaylı organizatör olarak oturum açmış tarayıcı sayfası."""
    response = page.context.request.post(
        "/accounts/login", data={"email": ORGANIZER_EMAIL, "password": ORGANIZER_PASSWORD}
    )
    assert response.ok
    return page
