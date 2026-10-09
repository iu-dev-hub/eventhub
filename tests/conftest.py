"""Shared fixtures for all tests.

- app:    Her test için geçici, boş bir veritabanıyla uygulama
- client: Flask test istemcisi (tarayıcı olmadan HTTP isteği gönderir)
"""

import pytest

from app import create_app
from app.core.db import init_db


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})
    with app.app_context():
        init_db()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()
