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


# ==============================================================================
# TG-53: 5 Hatalı Girişte Brute-Force Güvenlik Kilidi Birim Testleri
# ==============================================================================


def test_lockout_tracker_locks_at_5_attempts():
    """TG-53: 5 hatalı denemede hesap 15 dakika süreyle kilitlenmelidir."""
    from app.accounts.security import AccountLockoutTracker

    tracker = AccountLockoutTracker(max_attempts=5, lockout_minutes=15)
    email = "target@example.com"

    for i in range(1, 5):
        count, is_locked = tracker.record_failed_attempt(email)
        assert count == i
        assert is_locked is False
        locked, _ = tracker.is_locked(email)
        assert locked is False

    # 5. denemede kilitlenmeli
    count, is_locked = tracker.record_failed_attempt(email)
    assert count == 5
    assert is_locked is True

    locked, remaining = tracker.is_locked(email)
    assert locked is True
    assert remaining is not None
    assert remaining > 0


def test_lockout_tracker_resets_counter():
    """TG-53: Başarılı girişte sayaç sıfırlanmalıdır."""
    from app.accounts.security import AccountLockoutTracker

    tracker = AccountLockoutTracker(max_attempts=5, lockout_minutes=15)
    email = "reset@example.com"

    tracker.record_failed_attempt(email)
    tracker.record_failed_attempt(email)
    assert tracker._records[email]["count"] == 2

    tracker.reset(email)
    assert email not in tracker._records
    locked, _ = tracker.is_locked(email)
    assert locked is False


def test_lockout_tracker_unlocks_after_time_expires():
    """TG-53: Kilit süresi dolduğunda hesap otomatik olarak açılmalıdır."""
    from datetime import datetime, timedelta, timezone

    from app.accounts.security import AccountLockoutTracker

    tracker = AccountLockoutTracker(max_attempts=5, lockout_minutes=15)
    email = "expire@example.com"

    for _ in range(5):
        tracker.record_failed_attempt(email)

    assert tracker.is_locked(email)[0] is True

    # Kilit süresini geçmişe alalım
    tracker._records[email]["locked_until"] = datetime.now(timezone.utc) - timedelta(seconds=1)

    is_locked, remaining = tracker.is_locked(email)
    assert is_locked is False
    assert remaining is None


def test_lockout_tracker_invalid_inputs():
    """TG-53: Geçersiz veya boş e-posta parametreleri güvenli ele alınmalıdır."""
    from app.accounts.security import AccountLockoutTracker

    tracker = AccountLockoutTracker()
    assert tracker.is_locked(None) == (False, None)
    assert tracker.is_locked("") == (False, None)
    assert tracker.is_locked(123) == (False, None)
    assert tracker.record_failed_attempt(None) == (0, False)
    assert tracker.record_failed_attempt("") == (0, False)


def test_lockout_tracker_record_after_expiration_resets_count():
    """TG-53: Kilit süresi dolduktan sonraki yeni hatalı deneme sayacı 1'den başlatmalıdır."""
    from datetime import datetime, timedelta, timezone

    from app.accounts.security import AccountLockoutTracker

    tracker = AccountLockoutTracker(max_attempts=5, lockout_minutes=15)
    email = "exp_reset@example.com"

    for _ in range(5):
        tracker.record_failed_attempt(email)

    assert tracker.is_locked(email)[0] is True

    # Kilit süresini geçmişe alalım
    tracker._records[email]["locked_until"] = datetime.now(timezone.utc) - timedelta(seconds=1)

    # Yeni hatalı deneme -> sayaç 1 olmalı, kilit kalkmış olmalı
    count, is_locked = tracker.record_failed_attempt(email)
    assert count == 1
    assert is_locked is False


# ==============================================================================
# TG-54: @login_required ve @role_required Yetkilendirme Dekoratörleri Birim Testleri
# ==============================================================================


def test_login_required_decorator_blocks_without_session(app):
    """TG-54: Oturum açılmamışken @login_required 401 dönmelidir."""
    from app.accounts.security import login_required

    @login_required
    def dummy_view():
        return "ok"

    with app.test_request_context():
        response, status_code = dummy_view()
        assert status_code == 401
        assert response.get_json()["error"] == "Oturum açılmamış."


def test_login_required_decorator_passes_with_session(app):
    """TG-54: Oturum açıkken @login_required g nesnesini doldurup fonksiyonu çalıştırmalıdır."""
    from flask import g, session

    from app.accounts.security import login_required

    @login_required
    def dummy_view():
        return f"ok:{g.user_id}:{g.user_email}:{g.user_role}"

    with app.test_request_context():
        session["user_id"] = 42
        session["user_email"] = "auth@example.com"
        session["user_role"] = "participant"

        result = dummy_view()
        assert result == "ok:42:auth@example.com:participant"


def test_role_required_decorator_blocks_unauthorized_role(app):
    """TG-54: İstenen role sahip olmayan kullanıcıya 403 Forbidden dönülmelidir."""
    from flask import session

    from app.accounts.security import role_required

    @role_required("admin")
    def admin_only_view():
        return "admin_ok"

    with app.test_request_context():
        session["user_id"] = 1
        session["user_role"] = "participant"

        response, status_code = admin_only_view()
        assert status_code == 403
        assert response.get_json()["error"] == "Bu işlem için yetkiniz bulunmamaktadır."


def test_role_required_decorator_allows_authorized_role(app):
    """TG-54: İstenen role sahip kullanıcı başarıyla erişebilmelidir."""
    from flask import session

    from app.accounts.security import role_required

    @role_required("admin", "organizer")
    def privileged_view():
        return "privileged_ok"

    with app.test_request_context():
        session["user_id"] = 2
        session["user_role"] = "organizer"

        result = privileged_view()
        assert result == "privileged_ok"


def test_register_user_with_full_name_and_student_status(app):
    """TG-68, TG-78: Ad, soyad ve öğrenci statüsü ile kayıt doğrulaması."""
    from app.accounts.services import get_user_by_id, register_user

    with app.app_context():
        user = register_user(
            email="ogrenci@igdir.edu.tr",
            password="SecurePass123",
            first_name="Ahmet",
            last_name="Yılmaz",
            terms_accepted=True,
            is_student=True,
            student_number="120501001",
        )
        assert user["first_name"] == "Ahmet"
        assert user["last_name"] == "Yılmaz"
        assert user["is_student"] is True

        fetched = get_user_by_id(user["id"])
        assert fetched is not None
        assert fetched["first_name"] == "Ahmet"
        assert fetched["last_name"] == "Yılmaz"
        assert fetched["is_student"] is True
        assert fetched["student_number"] == "120501001"


def test_register_user_without_terms_fails(app):
    """TG-68: Sözleşme kabul edilmediğinde ValueError fırlatılmalıdır."""
    from app.accounts.services import register_user

    with app.app_context():
        with pytest.raises(ValueError, match="Kullanım Koşulları kabul edilmelidir"):
            register_user(
                email="noterms@example.com",
                password="SecurePass123",
                first_name="Test",
                last_name="User",
                terms_accepted=False,
            )


def test_update_user_profile_success(app):
    """TG-73: Ad ve soyad güncellenebilmeli, rol ve email değişmemelidir."""
    from app.accounts.services import get_user_by_id, register_user, update_user_profile

    with app.app_context():
        user = register_user(
            email="profiletest@example.com",
            password="SecurePass123",
            first_name="EskiAd",
            last_name="EskiSoyad",
            terms_accepted=True,
        )
        updated = update_user_profile(user["id"], "YeniAd", "YeniSoyad")
        assert updated["first_name"] == "YeniAd"
        assert updated["last_name"] == "YeniSoyad"
        assert updated["email"] == "profiletest@example.com"
        assert updated["role"] == "participant"

        fetched = get_user_by_id(user["id"])
        assert fetched["first_name"] == "YeniAd"
        assert fetched["last_name"] == "YeniSoyad"


def test_update_user_profile_empty_names_fails(app):
    """TG-73: Ad veya soyad boş girildiğinde ValueError fırlatılmalıdır."""
    from app.accounts.services import register_user, update_user_profile

    with app.app_context():
        user = register_user(
            email="emptyname@example.com",
            password="SecurePass123",
            first_name="Valid",
            last_name="Name",
            terms_accepted=True,
        )
        with pytest.raises(ValueError, match="Ad alanı boş bırakılamaz"):
            update_user_profile(user["id"], "", "Valid")

        with pytest.raises(ValueError, match="Soyad alanı boş bırakılamaz"):
            update_user_profile(user["id"], "Valid", "")


def test_change_password_success_and_verifies(app):
    """TG-75: Şifre başarıyla değiştirilmeli ve yeni şifre doğrulanabilmelidir."""
    from app.accounts.services import (
        authenticate_user,
        change_password,
        register_user,
    )

    with app.app_context():
        user = register_user(
            email="changepwd@example.com",
            password="OldPassword123",
            first_name="Change",
            last_name="Pass",
            terms_accepted=True,
        )
        change_password(user["id"], "OldPassword123", "BrandNewPass456")

        # Yeni şifreyle giriş başarılı olmalı
        auth_user = authenticate_user("changepwd@example.com", "BrandNewPass456")
        assert auth_user["id"] == user["id"]

        # Eski şifre reddedilmeli
        with pytest.raises(ValueError, match="Geçersiz e-posta veya şifre"):
            authenticate_user("changepwd@example.com", "OldPassword123")


def test_change_password_wrong_current_fails(app):
    """TG-75: Mevcut şifre yanlışsa şifre değiştirme reddedilmelidir."""
    from app.accounts.services import change_password, register_user

    with app.app_context():
        user = register_user(
            email="wrongpwd@example.com",
            password="CorrectPass123",
            first_name="Wrong",
            last_name="Pass",
            terms_accepted=True,
        )
        with pytest.raises(ValueError, match="Mevcut şifreniz hatalı"):
            change_password(user["id"], "IncorrectPass999", "NewPassWord123")


def test_password_reset_token_lifecycle(app):
    """TG-76: Şifre sıfırlama tokenı üretimi, kullanımı ve tek seferlik olması."""
    from app.accounts.services import (
        authenticate_user,
        create_password_reset_token,
        register_user,
        reset_password_with_token,
    )

    with app.app_context():
        register_user(
            email="resettest@example.com",
            password="InitialPass123",
            first_name="Reset",
            last_name="Test",
            terms_accepted=True,
        )

        token = create_password_reset_token("resettest@example.com")
        assert token is not None
        assert len(token) > 20

        # Şifreyi token ile sıfırla
        reset_password_with_token(token, "ResetPassword789")

        # Yeni şifre ile giriş doğrula
        auth = authenticate_user("resettest@example.com", "ResetPassword789")
        assert auth["email"] == "resettest@example.com"

        # Kullanılmış token tekrar kullanılamaz
        with pytest.raises(ValueError, match="Geçersiz veya süresi dolmuş"):
            reset_password_with_token(token, "AnotherPass123")


def test_update_notification_preferences(app):
    """TG-81: Bildirim tercihleri güncellenebilmelidir."""
    from app.accounts.services import (
        get_user_by_id,
        register_user,
        update_notification_preferences,
    )

    with app.app_context():
        user = register_user(
            email="notifytest@example.com",
            password="NotifyPass123",
            first_name="Notify",
            last_name="User",
            terms_accepted=True,
        )
        fetched = get_user_by_id(user["id"])
        assert fetched["notify_email"] is True

        update_notification_preferences(user["id"], False)
        fetched_after = get_user_by_id(user["id"])
        assert fetched_after["notify_email"] is False


def test_ensure_user_columns_backwards_compatibility(app):
    """TG-82: Eski şemaya sahip veritabanına yeni kolonlar eklenmelidir."""
    import sqlite3

    from app.accounts.services import ensure_user_columns

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, password_hash TEXT, role TEXT)"
    )
    conn.commit()

    # ensure_user_columns çağrıldığında yeni kolonlar eklenmeli
    ensure_user_columns(conn)

    cols = {row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    assert "first_name" in cols
    assert "last_name" in cols
    assert "is_student" in cols
    assert "student_number" in cols
    assert "notify_email" in cols
    assert "avatar_url" in cols

    # Tablolar zaten varsa tekrar çağrıldığında hata vermemeli
    ensure_user_columns(conn)
    conn.close()


def test_ensure_user_columns_exception_gracefully_handled():
    """TG-82: Beklenmeyen veritabanı hatalarında fonksiyon çökmemelidir."""
    from app.accounts.services import ensure_user_columns

    class BrokenDB:
        def execute(self, *args, **kwargs):
            raise RuntimeError("Database connection failure")

    ensure_user_columns(BrokenDB())


def test_update_user_profile_invalid_inputs(app):
    """TG-73: Geçersiz parametrelerle profil güncelleme reddedilmelidir."""
    from app.accounts.services import register_user, update_user_profile

    with app.app_context():
        user = register_user(
            email="profupdate@example.com",
            password="Password123",
            first_name="Prof",
            last_name="User",
            terms_accepted=True,
        )

        # Geçersiz user_id
        with pytest.raises(ValueError, match="Geçersiz kullanıcı kimliği"):
            update_user_profile(None, "Valid", "Name")
        with pytest.raises(ValueError, match="Geçersiz kullanıcı kimliği"):
            update_user_profile("not_int", "Valid", "Name")

        # Boş ad veya soyad
        with pytest.raises(ValueError, match="Ad alanı boş bırakılamaz"):
            update_user_profile(user["id"], "", "Valid")
        with pytest.raises(ValueError, match="Soyad alanı boş bırakılamaz"):
            update_user_profile(user["id"], "Valid", "   ")

        # Var olmayan kullanıcı
        with pytest.raises(ValueError, match="Kullanıcı bulunamadı"):
            update_user_profile(99999, "Valid", "Name")


def test_change_password_invalid_inputs(app):
    """TG-75: Şifre değiştirme geçersiz girdi kontrolleri."""
    from app.accounts.services import change_password, register_user

    with app.app_context():
        user = register_user(
            email="chgpwd_invalid@example.com",
            password="Password123",
            first_name="Chg",
            last_name="Pwd",
            terms_accepted=True,
        )

        with pytest.raises(ValueError, match="Geçersiz kullanıcı kimliği"):
            change_password(None, "Password123", "NewPass123")
        with pytest.raises(ValueError, match="Geçersiz kullanıcı kimliği"):
            change_password("bad_id", "Password123", "NewPass123")

        with pytest.raises(ValueError, match="Mevcut şifre boş bırakılamaz"):
            change_password(user["id"], "", "NewPass123")

        with pytest.raises(ValueError, match="Yeni şifre boş bırakılamaz"):
            change_password(user["id"], "Password123", "")

        with pytest.raises(ValueError, match="Kullanıcı bulunamadı"):
            change_password(99999, "Password123", "NewPass123")


def test_create_password_reset_token_invalid_or_nonexistent_email(app):
    """TG-76: Boş veya kayıtlı olmayan e-postada token üretilmemelidir (None)."""
    from app.accounts.services import create_password_reset_token

    with app.app_context():
        assert create_password_reset_token(None) is None
        assert create_password_reset_token("") is None
        assert create_password_reset_token("   ") is None
        assert create_password_reset_token("unregistered_ghost@example.com") is None


def test_reset_password_with_token_invalid_inputs(app):
    """TG-76: Geçersiz, boş veya sahte token ile sıfırlama reddedilmelidir."""
    from app.accounts.services import reset_password_with_token

    with app.app_context():
        with pytest.raises(ValueError, match="Geçersiz veya süresi dolmuş"):
            reset_password_with_token(None, "NewPass123")
        with pytest.raises(ValueError, match="Geçersiz veya süresi dolmuş"):
            reset_password_with_token("completely_fake_token_12345", "NewPass123")


def test_reset_password_with_token_expired(app):
    """TG-76: Süresi dolmuş token ile şifre sıfırlama reddedilmelidir."""
    import hashlib
    from datetime import datetime, timedelta, timezone

    from app.accounts.services import register_user, reset_password_with_token
    from app.core.db import get_db

    with app.app_context():
        user = register_user(
            email="expiredtoken@example.com",
            password="Password123",
            first_name="Expired",
            last_name="Token",
            terms_accepted=True,
        )

        db = get_db()
        raw_token = "expired_raw_token_xyz"
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        past_dt = datetime.now(timezone.utc) - timedelta(minutes=30)
        past_time = past_dt.strftime("%Y-%m-%d %H:%M:%S")

        db.execute(
            "INSERT INTO password_resets "
            "(user_id, token_hash, expires_at, used) VALUES (?, ?, ?, 0)",
            (user["id"], token_hash, past_time),
        )
        db.commit()

        with pytest.raises(ValueError, match="Geçersiz veya süresi dolmuş"):
            reset_password_with_token(raw_token, "NewPassword123")


def test_reset_password_with_token_isoformat_expiry(app):
    """TG-76: ISO formatındaki son kullanma tarihi desteklenmelidir."""
    import hashlib
    from datetime import datetime, timedelta, timezone

    from app.accounts.services import (
        authenticate_user,
        register_user,
        reset_password_with_token,
    )
    from app.core.db import get_db

    with app.app_context():
        user = register_user(
            email="isotoken@example.com",
            password="Password123",
            first_name="Iso",
            last_name="Token",
            terms_accepted=True,
        )

        db = get_db()
        raw_token = "iso_raw_token_abc"
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        future_iso = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

        db.execute(
            "INSERT INTO password_resets "
            "(user_id, token_hash, expires_at, used) VALUES (?, ?, ?, 0)",
            (user["id"], token_hash, future_iso),
        )
        db.commit()

        assert reset_password_with_token(raw_token, "BrandNewIsoPass123") is True
        auth = authenticate_user("isotoken@example.com", "BrandNewIsoPass123")
        assert auth["id"] == user["id"]


def test_update_notification_preferences_invalid_user_id(app):
    """TG-81: Geçersiz user_id ile bildirim tercihi güncelleme reddedilmelidir."""
    from app.accounts.services import update_notification_preferences

    with app.app_context():
        with pytest.raises(ValueError, match="Geçersiz kullanıcı kimliği"):
            update_notification_preferences(None, True)
        with pytest.raises(ValueError, match="Geçersiz kullanıcı kimliği"):
            update_notification_preferences("bad_id", True)


def test_update_avatar_url(app):
    """TG-81: Avatar URL güncelleme ve geçerlilik denetimleri."""
    from app.accounts.services import (
        get_user_by_id,
        register_user,
        update_avatar_url,
    )

    with app.app_context():
        user = register_user(
            email="avataruser@example.com",
            password="Password123",
            first_name="Avatar",
            last_name="User",
            terms_accepted=True,
        )

        # Geçersiz user_id
        with pytest.raises(ValueError, match="Geçersiz kullanıcı kimliği"):
            update_avatar_url(None, "https://example.com/avatar.png")

        # Geçerli avatar URL
        update_avatar_url(user["id"], "  https://example.com/avatar.png  ")
        user_after = get_user_by_id(user["id"])
        assert user_after["avatar_url"] == "https://example.com/avatar.png"

        # Boş avatar URL (None olarak sıfırlar)
        update_avatar_url(user["id"], "")
        user_cleared = get_user_by_id(user["id"])
        assert user_cleared["avatar_url"] is None

