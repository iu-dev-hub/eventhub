"""Unit tests for Account services and security hashing (TG-10, TG-11).

Tests core business rules and scrypt hashing functions in isolation.
"""

import pytest

from app.accounts.services import (
    hash_password,
    is_email_registered,
    register_user,
    verify_password,
)


def test_hash_password_uses_scrypt():
    """TG-10: Parola Werkzeug'un scrypt algoritmasıyla hash'lenmelidir."""
    password = "SecretPassword123"
    hashed = hash_password(password)

    # Scrypt formatı: scrypt:<N>:<r>:<p>$<salt>$<hash>
    assert hashed.startswith("scrypt:")
    assert hashed != password


def test_hash_password_empty_raises():
    """Boş parola hash'lenmeye çalışıldığında ValueError fırlatılmalıdır."""
    with pytest.raises(ValueError, match="Şifre boş bırakılamaz"):
        hash_password("")


def test_unique_salt_per_hash():
    """TG-10: Aynı parola için üretilen her hash farklı bir tuz (salt) içermelidir."""
    password = "SamePassword123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    assert hash1 != hash2
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


def test_verify_password_correct_and_incorrect():
    """Doğru parola doğrulanmalı, yanlış parola reddedilmelidir."""
    password = "MyCorrectPassword"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(password, "") is False


def test_is_email_registered_empty():
    """Boş e-posta adresi kontrol edildiğinde False dönmelidir."""
    assert is_email_registered("") is False
    assert is_email_registered("   ") is False


def test_register_user_service_validations():
    """Servis seviyesindeki zorunlu alan ve rol doğrulamaları."""
    with pytest.raises(ValueError, match="E-posta adresi boş bırakılamaz"):
        register_user("", "pass123")

    with pytest.raises(ValueError, match="E-posta adresi boş bırakılamaz"):
        register_user("   ", "pass123")

    with pytest.raises(ValueError, match="Şifre boş bırakılamaz"):
        register_user("user@example.com", "")

    with pytest.raises(ValueError, match="Geçersiz hesap türü"):
        register_user("user@example.com", "pass123", role="invalid_role")
