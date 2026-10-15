"""Integration tests for User Registration endpoint and services (TG-8, TG-10, TG-11).

Tests full request-response lifecycle with Flask test client and isolated SQLite database.
"""

import pytest

from app.accounts.services import (
    DuplicateEmailError,
    is_email_registered,
    register_user,
    verify_password,
)
from app.core.db import get_db


def test_accounts_index(client):
    """Hesaplar modülü ana sayfası durum 200 dönmelidir."""
    response = client.get("/accounts/")
    assert response.status_code == 200
    data = response.get_json()
    assert data["module"] == "accounts"


def test_accounts_index_html(client):
    """HTML Accept başlığı ile çağrıldığında şablon render edilmelidir."""
    response = client.get("/accounts/", headers={"Accept": "text/html"})
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Hesap Yönetimi" in html
    assert "EventHub" in html


def test_register_user_success(client, app):
    """TG-8: Geçerli e-posta ve parola ile kayıt 201 Created dönmelidir."""
    payload = {
        "email": "yusuf@example.com",
        "password": "SecurePassword123",
        "role": "participant",
    }
    response = client.post("/accounts/register", json=payload)

    assert response.status_code == 201
    json_data = response.get_json()
    assert "user" in json_data
    assert json_data["user"]["email"] == "yusuf@example.com"
    assert json_data["user"]["role"] == "participant"
    assert "id" in json_data["user"]

    # Veritabanında kaydın var olduğunu doğrula
    with app.app_context():
        assert is_email_registered("yusuf@example.com") is True


def test_register_user_form_data(client, app):
    """Form verisi (application/x-www-form-urlencoded) ile kayıt desteklenmelidir."""
    form_data = {
        "email": "formuser@example.com",
        "password": "SecurePassword123",
    }
    response = client.post("/accounts/register", data=form_data)
    assert response.status_code == 201
    assert response.get_json()["user"]["email"] == "formuser@example.com"


def test_register_duplicate_email_returns_409(client):
    """TG-8, BR-1.2: Aynı e-posta ile ikinci kayıt 409 Conflict dönmelidir."""
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123",
    }
    # İlk kayıt başarılı
    first_res = client.post("/accounts/register", json=payload)
    assert first_res.status_code == 201

    # Aynı e-posta ile tekrar kayıt (büyük/küçük harf duyarsız kontrol)
    second_payload = {
        "email": "DUPLICATE@example.com",
        "password": "AnotherPassword456",
    }
    second_res = client.post("/accounts/register", json=second_payload)

    assert second_res.status_code == 409
    error_data = second_res.get_json()
    assert "zaten kayıtlı" in error_data["error"]


def test_register_missing_fields_returns_400(client):
    """E-posta veya parola eksik ya da boş olduğunda 400 Bad Request dönmelidir."""
    # Boş e-posta
    res1 = client.post("/accounts/register", json={"email": "", "password": "123"})
    assert res1.status_code == 400
    assert "zorunludur" in res1.get_json()["error"]

    # Eksik parola
    res2 = client.post("/accounts/register", json={"email": "valid@example.com"})
    assert res2.status_code == 400
    assert "zorunludur" in res2.get_json()["error"]

    # Tamamen boş istek
    res3 = client.post("/accounts/register", json={})
    assert res3.status_code == 400


def test_password_not_stored_as_plaintext(client, app):
    """TG-10: Veritabanında gerçek parola asla düz metin olarak saklanmamalıdır."""
    raw_password = "SuperSecretPlaintextPassword!99"
    email = "security_check@example.com"

    response = client.post(
        "/accounts/register",
        json={"email": email, "password": raw_password},
    )
    assert response.status_code == 201

    with app.app_context():
        db = get_db()
        row = db.execute(
            "SELECT password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()

        assert row is not None
        stored_hash = row["password_hash"]

        # Düz metin parolanın veritabanında bulunmadığını kesinleştir
        assert raw_password not in stored_hash
        assert stored_hash.startswith("scrypt:")

        # scrypt hash doğrulaması başarılı olmalı
        assert verify_password(raw_password, stored_hash) is True
        assert verify_password("WrongPassword", stored_hash) is False


def test_register_user_service_directly_handles_duplicate(app):
    """Servis seviyesinde DuplicateEmailError fırlatılmalıdır."""
    with app.app_context():
        register_user("service_test@example.com", "Password123")

        with pytest.raises(DuplicateEmailError, match="Bu e-posta adresi zaten kayıtlı"):
            register_user("service_test@example.com", "AnotherPassword")


def test_register_invalid_role_returns_400(client):
    """Geçersiz rol gönderildiğinde 400 Bad Request dönmelidir."""
    payload = {
        "email": "invalid_role@example.com",
        "password": "Password123",
        "role": "hacker",
    }
    response = client.post("/accounts/register", json=payload)
    assert response.status_code == 400
    assert "Geçersiz hesap türü" in response.get_json()["error"]

