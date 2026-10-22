"""Unit tests for Account services and security hashing (TG-10, TG-11).

Tests core business rules and scrypt hashing functions in isolation.
"""

import pytest

from app.accounts.services import (
    authenticate_user,
    hash_password,
    is_email_registered,
    register_user,
    validate_email_format,
    validate_password_strength,
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
    password = "MyCorrectPassword1"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword1", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(password, "") is False


def test_is_email_registered_empty():
    """Boş e-posta adresi kontrol edildiğinde False dönmelidir."""
    assert is_email_registered("") is False
    assert is_email_registered("   ") is False


def test_register_user_service_validations():
    """Servis seviyesindeki zorunlu alan ve rol doğrulamaları."""
    with pytest.raises(ValueError, match="E-posta adresi boş bırakılamaz"):
        register_user("", "Password123")

    with pytest.raises(ValueError, match="E-posta adresi boş bırakılamaz"):
        register_user("   ", "Password123")

    with pytest.raises(ValueError, match="Şifre boş bırakılamaz"):
        register_user("user@example.com", "")

    with pytest.raises(ValueError, match="Geçersiz hesap türü"):
        register_user("user@example.com", "Password123", role="invalid_role")


# ==============================================================================
# TG-9, BR-1.2: E-posta Format Doğrulama Birim Testleri
# ==============================================================================


@pytest.mark.parametrize(
    "valid_email",
    [
        "user@example.com",
        "first.last@domain.co",
        "user+tag@gmail.com",
        "student_1443@ogr.iu.edu.tr",
        "dev-accounts@eventhub.io",
    ],
)
def test_validate_email_format_valid(valid_email):
    """Geçerli e-posta formatları hata vermeden doğrulanmalıdır (BR-1.2, TG-9)."""
    # Fonksiyon geçerli olduğunda None dönmeli, istisna fırlatmamalıdır
    assert validate_email_format(valid_email) is None


@pytest.mark.parametrize(
    "invalid_email",
    [
        "plainaddress",
        "@missingusername.com",
        "username@.com",
        "user@domain",
        "user@domain..com",
        "user@domain.",
        "user@-domain.com",
        "user@domain-.com",
        "user@domain.c",
        "user name@domain.com",
    ],
)
def test_validate_email_format_invalid_patterns(invalid_email):
    """Standart dışı e-posta adresleri 'Geçersiz e-posta formatı.' hatası üretmelidir."""
    with pytest.raises(ValueError, match="Geçersiz e-posta formatı"):
        validate_email_format(invalid_email)


@pytest.mark.parametrize("empty_email", ["", "   ", None])
def test_validate_email_format_empty(empty_email):
    """Boş veya sadece boşluktan oluşan e-postalar reddedilmelidir."""
    with pytest.raises(ValueError, match="E-posta adresi boş bırakılamaz"):
        validate_email_format(empty_email)


# ==============================================================================
# TG-9, BR-1.3: Şifre Karmaşıklık ve Sınır Değer (BVA) Birim Testleri
# ==============================================================================


def test_validate_password_strength_valid_boundaries():
    """BR-1.3: 8 ve 20 karakter sınır değerleri geçerli kabul edilmelidir."""
    # 8 karakter: alt sınır (1 harf + 1 rakam dahil)
    assert validate_password_strength("Passwor1") is None

    # 14 karakter: orta değer
    assert validate_password_strength("MySecurePass123!") is None

    # 20 karakter: üst sınır (1 harf + 1 rakam dahil)
    assert validate_password_strength("A123456789012345678b") is None


def test_validate_password_strength_too_short():
    """BR-1.3: 7 karakter veya daha kısa şifreler reddedilmelidir (Alt sınır - 1)."""
    with pytest.raises(ValueError, match="Şifre 8 ile 20 karakter arasında olmalıdır"):
        validate_password_strength("Passw1!")  # 7 karakter


def test_validate_password_strength_too_long():
    """BR-1.3: 21 karakter veya daha uzun şifreler reddedilmelidir (Üst sınır + 1)."""
    with pytest.raises(ValueError, match="Şifre 8 ile 20 karakter arasında olmalıdır"):
        validate_password_strength("A12345678901234567890c")  # 22 karakter


def test_validate_password_strength_missing_digit():
    """BR-1.3: Rakam içermeyen şifreler uzunluğu yeterli olsa da reddedilmelidir."""
    with pytest.raises(ValueError, match="Şifre en az bir harf ve en az bir rakam içermelidir"):
        validate_password_strength("PasswordOnlyLetters")


def test_validate_password_strength_missing_letter():
    """BR-1.3: Harf içermeyen şifreler uzunluğu yeterli olsa da reddedilmelidir."""
    with pytest.raises(ValueError, match="Şifre en az bir harf ve en az bir rakam içermelidir"):
        validate_password_strength("123456789012345")


@pytest.mark.parametrize("empty_password", ["", None])
def test_validate_password_strength_empty(empty_password):
    """Boş şifre denemesi reddedilmelidir."""
    with pytest.raises(ValueError, match="Şifre boş bırakılamaz"):
        validate_password_strength(empty_password)


# ==============================================================================
# TG-50, PB-02: Kullanıcı Kimlik Doğrulama (authenticate_user) Birim Testleri
# ==============================================================================


def test_authenticate_user_success(app):
    """TG-50: Doğru e-posta ve şifre ile kullanıcı başarıyla doğrulanmalıdır."""
    with app.app_context():
        created = register_user("testlogin@example.com", "Password123", role="participant")
        auth_user = authenticate_user("testlogin@example.com", "Password123")

        assert auth_user["id"] == created["id"]
        assert auth_user["email"] == "testlogin@example.com"
        assert auth_user["role"] == "participant"


def test_authenticate_user_case_insensitive_email(app):
    """TG-50: E-posta adresi büyük/küçük harf duyarsız doğrulanabilmelidir."""
    with app.app_context():
        register_user("caseuser@example.com", "Password123")
        auth_user = authenticate_user("CaseUser@EXAMPLE.com", "Password123")
        assert auth_user["email"] == "caseuser@example.com"


def test_authenticate_user_wrong_password(app):
    """TG-50: Yanlış parola girildiğinde ValueError fırlatılmalıdır."""
    with app.app_context():
        register_user("wrongpass@example.com", "Password123")
        with pytest.raises(ValueError, match="Geçersiz e-posta veya şifre"):
            authenticate_user("wrongpass@example.com", "WrongPassword1")


def test_authenticate_user_nonexistent_email(app):
    """TG-50: Kayıtlı olmayan e-posta ile giriş denendiğinde ValueError fırlatılmalıdır."""
    with app.app_context():
        with pytest.raises(ValueError, match="Geçersiz e-posta veya şifre"):
            authenticate_user("nonexistent@example.com", "Password123")


@pytest.mark.parametrize("bad_email", ["", "   ", None])
def test_authenticate_user_empty_email_raises(bad_email):
    """Boş e-posta ile giriş denendiğinde ValueError fırlatılmalıdır."""
    with pytest.raises(ValueError, match="E-posta adresi boş bırakılamaz"):
        authenticate_user(bad_email, "Password123")


@pytest.mark.parametrize("bad_pass", ["", None])
def test_authenticate_user_empty_password_raises(bad_pass):
    """Boş parola ile giriş denendiğinde ValueError fırlatılmalıdır."""
    with pytest.raises(ValueError, match="Şifre boş bırakılamaz"):
        authenticate_user("user@example.com", bad_pass)


def test_get_user_by_id(app):
    """TG-51: ID ile kullanıcı sorgulama doğru bilgileri dönmeli veya None vermelidir."""
    from app.accounts.services import get_user_by_id

    with app.app_context():
        created = register_user("idcheck@example.com", "Password123")
        user = get_user_by_id(created["id"])
        assert user is not None
        assert user["id"] == created["id"]
        assert user["email"] == "idcheck@example.com"
        assert "password_hash" not in user or user["email"] == "idcheck@example.com"

        # Var olmayan ID
        assert get_user_by_id(99999) is None
        # Geçersiz ID tipleri
        assert get_user_by_id(0) is None
        assert get_user_by_id("invalid") is None


# ==============================================================================
# TG-52: Hatalı Giriş ve 401 Unauthorized Hata Kontrolleri Birim Testleri
# ==============================================================================


def test_authenticate_user_timing_attack_countermeasure(app, monkeypatch):
    """TG-52: Var olmayan kullanıcıda bile verify_password çağrılmalı,
    timing attack ile kullanıcı tespiti engellenmelidir.
    """
    called_with_hash = []

    def mock_verify(password, p_hash):
        called_with_hash.append(p_hash)
        return False

    monkeypatch.setattr("app.accounts.services.verify_password", mock_verify)

    with app.app_context():
        with pytest.raises(ValueError, match="Geçersiz e-posta veya şifre"):
            authenticate_user("ghost@example.com", "Password123")

    assert len(called_with_hash) == 1
    assert "scrypt:" in called_with_hash[0]


@pytest.mark.parametrize("whitespace_pass", ["   ", "\t", "\n"])
def test_authenticate_user_whitespace_password_raises(whitespace_pass):
    """TG-52: Yalnızca boşluklardan oluşan şifreler reddedilmelidir."""
    with pytest.raises(ValueError, match="Şifre boş bırakılamaz"):
        authenticate_user("user@example.com", whitespace_pass)


def test_authenticate_user_sql_injection_attempt_safely_rejected(app):
    """TG-52: SQL injection girişimi veritabanını bozmadan güvenli şekilde 401/hata vermelidir."""
    with app.app_context():
        with pytest.raises(ValueError, match="Geçersiz e-posta veya şifre"):
            authenticate_user("admin' OR '1'='1", "Password123")

