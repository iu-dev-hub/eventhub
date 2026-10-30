"""POST /events/venues yetki ve kayıt entegrasyon testleri (TG-41, BR-2.1)."""

import pytest

from app.core.db import get_db

VALID = {"name": "Salon A", "address": "Beyazıt, İstanbul", "capacity": 100}


def _login_as(client, role):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_email"] = "u@example.com"
        sess["user_role"] = role


def _count(app):
    with app.app_context():
        return get_db().execute("SELECT COUNT(*) FROM venues").fetchone()[0]


def test_admin_can_create_venue_json(client, app):
    _login_as(client, "admin")
    res = client.post("/events/venues", json=VALID)
    assert res.status_code == 201
    assert res.get_json() == {"id": 1, **VALID}
    assert _count(app) == 1


def test_admin_can_create_venue_form(client, app):
    _login_as(client, "admin")
    res = client.post("/events/venues", data=VALID)
    assert res.status_code == 201
    assert _count(app) == 1


def test_unauthenticated_gets_401(client, app):
    res = client.post("/events/venues", json=VALID)
    assert res.status_code == 401
    assert _count(app) == 0


@pytest.mark.parametrize("role", ["organizer", "participant", "unknown"])
def test_non_admin_gets_403(client, app, role):
    _login_as(client, role)
    res = client.post("/events/venues", json=VALID)
    assert res.status_code == 403
    assert _count(app) == 0


@pytest.mark.parametrize("missing", ["name", "address", "capacity"])
def test_missing_field_gets_400(client, app, missing):
    _login_as(client, "admin")
    payload = {k: v for k, v in VALID.items() if k != missing}
    res = client.post("/events/venues", json=payload)
    assert res.status_code == 400
    assert "error" in res.get_json()
    assert _count(app) == 0


def test_invalid_capacity_gets_400(client, app):
    _login_as(client, "admin")
    res = client.post("/events/venues", json={**VALID, "capacity": 0})
    assert res.status_code == 400
    assert _count(app) == 0


def test_duplicate_name_gets_409(client, app):
    _login_as(client, "admin")
    client.post("/events/venues", json=VALID)
    res = client.post("/events/venues", json=VALID)
    assert res.status_code == 409
    assert _count(app) == 1


def test_non_admin_cannot_bypass_with_valid_data(client, app):
    """Yetki sunucu tarafında uygulanır; geçerli veri rolü aşmaz."""
    _login_as(client, "organizer")
    assert client.post("/events/venues", data=VALID).status_code == 403
    assert _count(app) == 0
