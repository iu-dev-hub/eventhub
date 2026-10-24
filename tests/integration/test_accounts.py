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
    raw_password = "SuperSecretPass1"
    email = "security_check@example.com"

    response = client.post(
        "/accounts/register",
        json={"email": email, "password": raw_password},
    )
    assert response.status_code == 201

    with app.app_context():
        db = get_db()
        row = db.execute("SELECT password_hash FROM users WHERE email = ?", (email,)).fetchone()

        assert row is not None
        stored_hash = row["password_hash"]

        # Düz metin parolanın veritabanında bulunmadığını kesinleştir
        assert raw_password not in stored_hash
        assert stored_hash.startswith("scrypt:")

        # scrypt hash doğrulaması başarılı olmalı
        assert verify_password(raw_password, stored_hash) is True
        assert verify_password("WrongPassword1", stored_hash) is False


def test_register_user_service_directly_handles_duplicate(app):
    """Servis seviyesinde DuplicateEmailError fırlatılmalıdır."""
    with app.app_context():
        register_user("service_test@example.com", "Password123")

        with pytest.raises(DuplicateEmailError, match="Bu e-posta adresi zaten kayıtlı"):
            register_user("service_test@example.com", "AnotherPassword456")


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


# ==============================================================================
# TG-9, BR-1.2 & BR-1.3: HTTP Uç Noktası Validasyon Entegrasyon Testleri
# ==============================================================================


@pytest.mark.parametrize(
    "bad_email",
    [
        "notanemail",
        "@nodomain.com",
        "user@nodomain",
        "user@domain..com",
        "user@.com",
    ],
)
def test_register_invalid_email_format_returns_400(client, bad_email):
    """TG-9, BR-1.2: Geçersiz e-posta formatı 400 Bad Request dönmelidir."""
    payload = {
        "email": bad_email,
        "password": "ValidPassword123",
    }
    response = client.post("/accounts/register", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert "Geçersiz e-posta formatı" in data["error"]


def test_register_password_too_short_returns_400(client):
    """TG-9, BR-1.3: 8 karakterden kısa parola 400 Bad Request dönmelidir."""
    payload = {
        "email": "shortpass@example.com",
        "password": "Pass1",
    }
    response = client.post("/accounts/register", json=payload)
    assert response.status_code == 400
    assert "8 ile 20 karakter arasında" in response.get_json()["error"]


def test_register_password_too_long_returns_400(client):
    """TG-9, BR-1.3: 20 karakterden uzun parola 400 Bad Request dönmelidir."""
    payload = {
        "email": "longpass@example.com",
        "password": "PasswordWithMoreThan20Chars1234",
    }
    response = client.post("/accounts/register", json=payload)
    assert response.status_code == 400
    assert "8 ile 20 karakter arasında" in response.get_json()["error"]


def test_register_password_missing_digit_returns_400(client):
    """TG-9, BR-1.3: Rakam içermeyen parola 400 Bad Request dönmelidir."""
    payload = {
        "email": "nodigit@example.com",
        "password": "PasswordWithoutDigit",
    }
    response = client.post("/accounts/register", json=payload)
    assert response.status_code == 400
    assert "en az bir harf ve en az bir rakam" in response.get_json()["error"]


def test_register_password_missing_letter_returns_400(client):
    """TG-9, BR-1.3: Harf içermeyen parola 400 Bad Request dönmelidir."""
    payload = {
        "email": "noletter@example.com",
        "password": "1234567890123",
    }
    response = client.post("/accounts/register", json=payload)
    assert response.status_code == 400
    assert "en az bir harf ve en az bir rakam" in response.get_json()["error"]


def test_register_boundary_passwords_succeed(client):
    """TG-9, BR-1.3: 8 ve 20 karakter tam sınır parolalar başarıyla 201 dönmelidir."""
    # 8 karakter tam alt sınır
    res8 = client.post(
        "/accounts/register",
        json={"email": "bound8@example.com", "password": "Password1"},
    )
    assert res8.status_code == 201

    # 20 karakter tam üst sınır
    res20 = client.post(
        "/accounts/register",
        json={"email": "bound20@example.com", "password": "A123456789012345678b"},
    )
    assert res20.status_code == 201


# ==============================================================================
# TG-50, TG-51: Giriş (Login), Çıkış (Logout) ve Session Entegrasyon Testleri
# ==============================================================================


def test_login_success_creates_session_and_200(client, app):
    """TG-50, TG-51: Başarılı giriş 200 dönmeli ve oturum (session) oluşturmalıdır."""
    # 1. Kullanıcı kaydı yap
    client.post(
        "/accounts/register",
        json={"email": "loginuser@example.com", "password": "Password123", "role": "participant"},
    )

    # 2. Giriş yap
    response = client.post(
        "/accounts/login",
        json={"email": "loginuser@example.com", "password": "Password123"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Giriş başarılı."
    assert data["user"]["email"] == "loginuser@example.com"
    assert "id" in data["user"]

    # 3. Session /me endpoint'i ile doğrulanmalı
    me_resp = client.get("/accounts/me")
    assert me_resp.status_code == 200
    me_data = me_resp.get_json()
    assert me_data["user"]["email"] == "loginuser@example.com"


def test_login_form_data_support(client, app):
    """TG-50: Form verisi (application/x-www-form-urlencoded) ile giriş desteklenmelidir."""
    client.post(
        "/accounts/register",
        json={"email": "formlogin@example.com", "password": "Password123"},
    )

    response = client.post(
        "/accounts/login",
        data={"email": "formlogin@example.com", "password": "Password123"},
    )

    assert response.status_code == 200
    assert response.get_json()["user"]["email"] == "formlogin@example.com"


def test_login_invalid_password_returns_401(client, app):
    """TG-50: Hatalı şifre girildiğinde 401 Unauthorized dönmelidir."""
    client.post(
        "/accounts/register",
        json={"email": "authfail@example.com", "password": "Password123"},
    )

    response = client.post(
        "/accounts/login",
        json={"email": "authfail@example.com", "password": "WrongPassword1"},
    )

    assert response.status_code == 401
    assert "Geçersiz e-posta veya şifre" in response.get_json()["error"]


def test_login_nonexistent_email_returns_401(client, app):
    """TG-50: Sistemde olmayan e-posta ile giriş denemesi 401 Unauthorized dönmelidir."""
    response = client.post(
        "/accounts/login",
        json={"email": "unknown@example.com", "password": "Password123"},
    )

    assert response.status_code == 401
    assert "Geçersiz e-posta veya şifre" in response.get_json()["error"]


def test_login_missing_fields_returns_400(client):
    """TG-50: E-posta veya şifre eksik olduğunda 400 Bad Request dönmelidir."""
    res1 = client.post("/accounts/login", json={"email": ""})
    assert res1.status_code == 400

    res2 = client.post("/accounts/login", json={"email": "user@example.com", "password": ""})
    assert res2.status_code == 400


def test_logout_clears_session(client, app):
    """TG-51: Logout endpoint'i oturumu sonlandırmalı ve /me 401 dönmelidir."""
    # 1. Kayıt ve giriş
    client.post(
        "/accounts/register",
        json={"email": "logoutuser@example.com", "password": "Password123"},
    )
    client.post(
        "/accounts/login",
        json={"email": "logoutuser@example.com", "password": "Password123"},
    )

    # Oturumun aktif olduğunu teyit et
    assert client.get("/accounts/me").status_code == 200

    # 2. Çıkış yap (logout)
    logout_resp = client.post("/accounts/logout")
    assert logout_resp.status_code == 200
    assert logout_resp.get_json()["message"] == "Oturum başarıyla kapatıldı."

    # 3. Oturum kapandıktan sonra /me çağrısı 401 dönmeli
    assert client.get("/accounts/me").status_code == 401


def test_me_without_session_returns_401(client):
    """TG-51: Giriş yapılmadan /accounts/me çağrıldığında 401 dönmelidir."""
    response = client.get("/accounts/me")
    assert response.status_code == 401
    assert "Oturum açılmamış" in response.get_json()["error"]


def test_me_with_deleted_user_in_session_clears_session_and_returns_401(client, app):
    """TG-51: Session'daki user_id veritabanında yoksa session temizlenmeli ve 401 dönmelidir."""
    with client.session_transaction() as sess:
        sess["user_id"] = 99999

    response = client.get("/accounts/me")
    assert response.status_code == 401
    assert "Kullanıcı bulunamadı" in response.get_json()["error"]


# ==============================================================================
# TG-52: Hatalı Giriş ve 401 Unauthorized Hata Kontrolleri Entegrasyon Testleri
# ==============================================================================


def test_login_user_enumeration_prevention_identical_response(client, app):
    """TG-52: Var olmayan kullanıcı ile yanlış şifre denemesi aynı 401 yanıtını dönmelidir."""
    client.post(
        "/accounts/register",
        json={"email": "existinguser@example.com", "password": "Password123"},
    )

    # 1. Var olan kullanıcıya yanlış şifre
    res1 = client.post(
        "/accounts/login",
        json={"email": "existinguser@example.com", "password": "WrongPassword123"},
    )
    # 2. Var olmayan kullanıcı
    res2 = client.post(
        "/accounts/login",
        json={"email": "nonexistinguser@example.com", "password": "AnyPassword123"},
    )

    assert res1.status_code == 401
    assert res2.status_code == 401
    assert res1.get_json() == res2.get_json()
    assert res1.get_json()["error"] == "Geçersiz e-posta veya şifre."


@pytest.mark.parametrize("whitespace_pass", ["   ", "\t", "  \n  "])
def test_login_whitespace_only_password_returns_400(client, whitespace_pass):
    """TG-52: Sadece boşluklardan oluşan şifreler 400 Bad Request dönmelidir."""
    response = client.post(
        "/accounts/login",
        json={"email": "user@example.com", "password": whitespace_pass},
    )
    assert response.status_code == 400
    assert "E-posta ve şifre zorunludur" in response.get_json()["error"]


def test_login_sql_injection_attempt_returns_401(client, app):
    """TG-52: SQL injection payload'u ile giriş denemesi 401 Unauthorized ile reddedilmelidir."""
    response = client.post(
        "/accounts/login",
        json={"email": "' OR 1=1 --", "password": "' OR '1'='1"},
    )
    assert response.status_code == 401
    assert "Geçersiz e-posta veya şifre" in response.get_json()["error"]


def test_login_trimmed_whitespace_email_success(client, app):
    """TG-52: E-posta başındaki/sonundaki boşluklar temizlenerek giriş başarılı olmalıdır."""
    client.post(
        "/accounts/register",
        json={"email": "trimuser@example.com", "password": "Password123"},
    )

    response = client.post(
        "/accounts/login",
        json={"email": "   trimuser@example.com   ", "password": "Password123"},
    )
    assert response.status_code == 200
    assert response.get_json()["user"]["email"] == "trimuser@example.com"


# ==============================================================================
# TG-53: 5 Hatalı Girişte Brute-Force Güvenlik Kilidi Entegrasyon Testleri
# ==============================================================================


def test_login_brute_force_lockout_after_5_failed_attempts(client, app):
    """TG-53: 5 kez ardışık hatalı şifre girildiğinde hesap
    429 Too Many Requests ile kilitlenmelidir.
    """
    from app.accounts.security import lockout_tracker

    lockout_tracker.clear_all()

    email = "victim@example.com"
    client.post(
        "/accounts/register",
        json={"email": email, "password": "CorrectPassword1"},
    )

    # 1 - 4. denemeler: 401 dönmeli, kalan deneme sayısı bildirilmeli
    for attempt in range(1, 5):
        resp = client.post(
            "/accounts/login",
            json={"email": email, "password": "WrongPassword!"},
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["remaining_attempts"] == (5 - attempt)
        assert "Geçersiz e-posta veya şifre" in data["error"]

    # 5. deneme: 429 Too Many Requests ile kilitlenmeli
    resp5 = client.post(
        "/accounts/login",
        json={"email": email, "password": "WrongPassword!"},
    )
    assert resp5.status_code == 429
    data5 = resp5.get_json()
    assert "geçici olarak kilitlendi" in data5["error"]
    assert data5["remaining_seconds"] > 0

    # 6. deneme (doğru şifre girilse bile kilitli kalmalı)
    resp6 = client.post(
        "/accounts/login",
        json={"email": email, "password": "CorrectPassword1"},
    )
    assert resp6.status_code == 429
    assert "geçici olarak kilitlendi" in resp6.get_json()["error"]


def test_login_successful_login_resets_failed_attempts(client, app):
    """TG-53: Hatalı denemelerin ardından başarılı giriş yapılırsa sayaç sıfırlanmalıdır."""
    from app.accounts.security import lockout_tracker

    lockout_tracker.clear_all()

    email = "resetflow@example.com"
    client.post(
        "/accounts/register",
        json={"email": email, "password": "CorrectPassword1"},
    )

    # 3 kez hatalı deneme
    for _ in range(3):
        res = client.post(
            "/accounts/login",
            json={"email": email, "password": "WrongPassword!"},
        )
        assert res.status_code == 401

    # Başarılı giriş -> sayacı sıfırlar
    success_resp = client.post(
        "/accounts/login",
        json={"email": email, "password": "CorrectPassword1"},
    )
    assert success_resp.status_code == 200

    # Tekrar hatalı girildiğinde kilitlenmemeli, sıfırdan 4 kalan deneme vermeli
    again_fail = client.post(
        "/accounts/login",
        json={"email": email, "password": "WrongPassword!"},
    )
    assert again_fail.status_code == 401
    assert again_fail.get_json()["remaining_attempts"] == 4


# ==============================================================================
# TG-54: @login_required ve @role_required Entegrasyon Testleri
# ==============================================================================


def test_admin_status_without_login_returns_401(client):
    """TG-54: Giriş yapılmadan admin endpoint'ine erişildiğinde 401 dönmelidir."""
    response = client.get("/accounts/admin/status")
    assert response.status_code == 401
    assert "Oturum açılmamış" in response.get_json()["error"]


def test_admin_status_with_participant_role_returns_403(client, app):
    """TG-54: Katılımcı rolündeki kullanıcı admin endpoint'ine
    eriştiğinde 403 Forbidden dönmelidir.
    """
    # Katılımcı olarak kaydol ve giriş yap
    client.post(
        "/accounts/register",
        json={"email": "participant@example.com", "password": "Password123", "role": "participant"},
    )
    client.post(
        "/accounts/login",
        json={"email": "participant@example.com", "password": "Password123"},
    )

    response = client.get("/accounts/admin/status")
    assert response.status_code == 403
    assert "yetkiniz bulunmamaktadır" in response.get_json()["error"]


def test_admin_status_with_admin_role_returns_200(client, app):
    """TG-54: Admin rolündeki kullanıcı admin endpoint'ine eriştiğinde 200 OK dönmelidir."""
    # Admin olarak kaydol ve giriş yap
    client.post(
        "/accounts/register",
        json={"email": "superadmin@example.com", "password": "Password123", "role": "admin"},
    )
    client.post(
        "/accounts/login",
        json={"email": "superadmin@example.com", "password": "Password123"},
    )

    response = client.get("/accounts/admin/status")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
    assert "onaylandı" in response.get_json()["message"]


# ==============================================================================
# Sprint 3 Integration Tests (TG-68 through TG-82)
# ==============================================================================


def test_register_with_first_and_last_name(client):
    """TG-68: Ad, soyad ve sözleşme onayı ile kayıt 201 Created dönmelidir."""
    payload = {
        "first_name": "Deniz",
        "last_name": "Aydın",
        "email": "deniz.aydin@example.com",
        "password": "SecurePassword123",
        "terms_accepted": True,
    }
    response = client.post("/accounts/register", json=payload)
    assert response.status_code == 201
    user = response.get_json()["user"]
    assert user["first_name"] == "Deniz"
    assert user["last_name"] == "Aydın"
    assert user["email"] == "deniz.aydin@example.com"


def test_register_empty_name_returns_400(client):
    """TG-68: Ad veya soyad boş girildiğinde 400 Bad Request dönmelidir."""
    payload = {
        "first_name": "   ",
        "last_name": "Aydın",
        "email": "emptyname@example.com",
        "password": "SecurePassword123",
        "terms_accepted": True,
    }
    res1 = client.post("/accounts/register", json=payload)
    assert res1.status_code == 400
    assert "Ad alanı zorunludur" in res1.get_json()["error"]

    payload["first_name"] = "Deniz"
    payload["last_name"] = "  "
    res2 = client.post("/accounts/register", json=payload)
    assert res2.status_code == 400
    assert "Soyad alanı zorunludur" in res2.get_json()["error"]


def test_register_missing_terms_returns_400(client):
    """TG-68: Kullanım Koşulları reddedildiğinde 400 dönmelidir."""
    payload = {
        "first_name": "Deniz",
        "last_name": "Aydın",
        "email": "termsno@example.com",
        "password": "SecurePassword123",
        "terms_accepted": False,
    }
    res = client.post("/accounts/register", json=payload)
    assert res.status_code == 400
    assert "Kullanım Koşulları" in res.get_json()["error"]


def test_auth_screens_render_templates(client):
    """TG-69, TG-70: Giriş ve Kayıt GET istekleri HTML şablonlarını render etmelidir."""
    res_login = client.get("/accounts/login")
    assert res_login.status_code == 200
    assert "Tekrar Hoş Geldiniz!" in res_login.get_data(as_text=True)

    res_reg = client.get("/accounts/register")
    assert res_reg.status_code == 200
    assert "Hemen kayıt olun!" in res_reg.get_data(as_text=True)


def test_logout_confirm_and_post_flow(client):
    """TG-69, TG-75: Logout GET onay şablonu sunmalı, POST oturumu temizlemelidir."""
    # Giriş yap
    client.post(
        "/accounts/register",
        json={"email": "logoutuser@example.com", "password": "Password123", "terms_accepted": True},
    )
    client.post(
        "/accounts/login",
        json={"email": "logoutuser@example.com", "password": "Password123"},
    )

    # GET isteği onay sayfasını açmalı
    res_get = client.get("/accounts/logout")
    assert res_get.status_code == 200
    assert "Çıkış yapmak istediğinizden emin misiniz?" in res_get.get_data(as_text=True)

    # POST isteği oturumu sonlandırmalı
    res_post = client.post("/accounts/logout")
    assert res_post.status_code == 200

    # Oturum kapalı olduğu için /me 401 dönmeli
    res_me = client.get("/accounts/me")
    assert res_me.status_code == 401


def test_dashboard_flow(client):
    """TG-71: Dashboard oturum gerektirir ve HTML/JSON yanıtlarını destekler."""
    # Oturumsuz istek 401 dönmeli
    res_unauth = client.get("/accounts/dashboard")
    assert res_unauth.status_code == 401

    # Giriş yap
    client.post(
        "/accounts/register",
        json={
            "first_name": "Ceren",
            "last_name": "Yılmaz",
            "email": "ceren@example.com",
            "password": "Password123",
            "terms_accepted": True,
        },
    )
    client.post(
        "/accounts/login",
        json={"email": "ceren@example.com", "password": "Password123"},
    )

    # HTML yanıtı
    res_html = client.get("/accounts/dashboard", headers={"Accept": "text/html"})
    assert res_html.status_code == 200
    html_text = res_html.get_data(as_text=True)
    assert "Tekrar Hoş Geldiniz, Ceren!" in html_text
    assert "Bu ekran geçici bir izleme ekranıdır" in html_text

    # JSON yanıtı
    res_json = client.get("/accounts/dashboard", headers={"Accept": "application/json"})
    assert res_json.status_code == 200
    assert res_json.get_json()["user"]["first_name"] == "Ceren"


def test_guest_screen_renders(client):
    """TG-77: Misafir kullanıcı sayfası 200 OK ve özellik kartlarını sunmalıdır."""
    res = client.get("/accounts/guest")
    assert res.status_code == 200
    content = res.get_data(as_text=True)
    assert "Misafir Kullanıcı" in content
    assert "Giriş Gerekli" in content


def test_profile_and_edit_flow(client):
    """TG-72, TG-73: Profil görüntüleme ve ad/soyad güncelleme akışı."""
    client.post(
        "/accounts/register",
        json={
            "first_name": "Ali",
            "last_name": "Veli",
            "email": "aliveli@example.com",
            "password": "Password123",
            "terms_accepted": True,
        },
    )
    client.post(
        "/accounts/login",
        json={"email": "aliveli@example.com", "password": "Password123"},
    )

    # Profil sayfası
    res_prof = client.get("/accounts/profile")
    assert res_prof.status_code == 200
    assert "Ali Veli" in res_prof.get_data(as_text=True)

    # Profil güncelleme
    res_edit = client.post(
        "/accounts/profile/edit",
        json={"first_name": "Ali Can", "last_name": "Kaya"},
    )
    assert res_edit.status_code == 200
    assert res_edit.get_json()["user"]["first_name"] == "Ali Can"
    assert res_edit.get_json()["user"]["last_name"] == "Kaya"

    # Boş ad veya soyad reddedilmeli
    res_bad = client.post(
        "/accounts/profile/edit",
        json={"first_name": "", "last_name": "Kaya"},
    )
    assert res_bad.status_code == 400


def test_settings_and_change_password_endpoint(client):
    """TG-74, TG-75: Ayarlar sayfası ve şifre değiştirme uç noktası."""
    client.post(
        "/accounts/register",
        json={
            "first_name": "Murat",
            "last_name": "Demir",
            "email": "murat@example.com",
            "password": "OldPassword123",
            "terms_accepted": True,
        },
    )
    client.post(
        "/accounts/login",
        json={"email": "murat@example.com", "password": "OldPassword123"},
    )

    # Ayarlar sayfası GET
    res_settings = client.get("/accounts/settings")
    assert res_settings.status_code == 200
    assert "Hesap Ayarları" in res_settings.get_data(as_text=True)

    # Şifre değiştirme POST
    res_cp = client.post(
        "/accounts/change-password",
        json={"current_password": "OldPassword123", "new_password": "NewSecurePass456"},
    )
    assert res_cp.status_code == 200

    # Hatalı mevcut şifre ile deneme
    res_cp_fail = client.post(
        "/accounts/change-password",
        json={"current_password": "WrongPassword999", "new_password": "NewSecurePass456"},
    )
    assert res_cp_fail.status_code == 400


def test_forgot_password_and_reset_flow(client):
    """TG-76: Şifremi unuttum token üretimi ve şifre sıfırlama akışı."""
    client.post(
        "/accounts/register",
        json={
            "first_name": "Selin",
            "last_name": "Oz",
            "email": "selin@example.com",
            "password": "InitialPass123",
            "terms_accepted": True,
        },
    )

    # GET şablonu
    res_get = client.get("/accounts/forgot-password")
    assert res_get.status_code == 200
    assert "Şifrenizi mi unuttunuz?" in res_get.get_data(as_text=True)

    # POST token isteği
    res_post = client.post("/accounts/forgot-password", json={"email": "selin@example.com"})
    assert res_post.status_code == 200
    data = res_post.get_json()
    assert "reset_token" in data
    token = data["reset_token"]

    # Sıfırlama sayfası GET
    res_reset_get = client.get(f"/accounts/reset-password/{token}")
    assert res_reset_get.status_code == 200
    assert "Yeni Şifre Belirleyin" in res_reset_get.get_data(as_text=True)

    # Yeni şifre belirleme POST
    res_reset_post = client.post(
        f"/accounts/reset-password/{token}",
        json={"new_password": "NewSelinPass123"},
    )
    assert res_reset_post.status_code == 200

    # Yeni şifreyle giriş başarılı olmalı
    res_login = client.post(
        "/accounts/login",
        json={"email": "selin@example.com", "password": "NewSelinPass123"},
    )
    assert res_login.status_code == 200


def test_student_status_in_registration_and_me(client):
    """TG-78: Öğrenci statüsü kayıt ve profil çıktısında yer almalıdır."""
    payload = {
        "first_name": "Bora",
        "last_name": "Can",
        "email": "bora.ogrenci@iu.edu.tr",
        "password": "Password123",
        "is_student": True,
        "student_number": "120501099",
        "terms_accepted": True,
    }
    client.post("/accounts/register", json=payload)
    client.post(
        "/accounts/login",
        json={"email": "bora.ogrenci@iu.edu.tr", "password": "Password123"},
    )

    res_me = client.get("/accounts/me")
    assert res_me.status_code == 200
    user_me = res_me.get_json()["user"]
    assert user_me["is_student"] is True
    assert user_me["student_number"] == "120501099"


def test_legal_pages_render_successfully(client):
    """TG-79: Kullanım Koşulları, Gizlilik ve KVKK sayfaları 200 dönmelidir."""
    res_terms = client.get("/accounts/terms")
    assert res_terms.status_code == 200
    assert "Kullanım Koşulları" in res_terms.get_data(as_text=True)
    assert "DEMO TASLAĞI" in res_terms.get_data(as_text=True)

    res_priv = client.get("/accounts/privacy")
    assert res_priv.status_code == 200
    assert "Gizlilik Politikası" in res_priv.get_data(as_text=True)

    res_kvkk = client.get("/accounts/kvkk")
    assert res_kvkk.status_code == 200
    assert "KVKK Aydınlatma Metni" in res_kvkk.get_data(as_text=True)


def test_preferences_endpoint(client):
    """TG-81: Bildirim tercihleri güncelleme uç noktası."""
    client.post(
        "/accounts/register",
        json={"email": "preftest@example.com", "password": "Password123", "terms_accepted": True},
    )
    client.post(
        "/accounts/login",
        json={"email": "preftest@example.com", "password": "Password123"},
    )

    res = client.post("/accounts/preferences", json={"notify_email": False})
    assert res.status_code == 200

    res_me = client.get("/accounts/me")
    assert res_me.get_json()["user"]["notify_email"] is False


def test_database_schema_idempotency(app):
    """TG-82: Şema birden fazla kez çalıştırıldığında veriler korunmalıdır."""
    from app.accounts.services import is_email_registered, register_user
    from app.core.db import init_db

    with app.app_context():
        # Kullanıcı kaydet
        register_user(
            email="persist@example.com",
            password="Password123",
            first_name="Persist",
            last_name="User",
            terms_accepted=True,
        )
        assert is_email_registered("persist@example.com") is True

        # Şemayı tekrar çalıştır (init_db)
        init_db()

        # Kullanıcı veritabanında hala mevcut olmalı (DROP TABLE yapılmadı)
        assert is_email_registered("persist@example.com") is True
