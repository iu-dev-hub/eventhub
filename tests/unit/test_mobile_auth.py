"""Unit tests for mobile authentication, validation, and JSON persistence (TG-182).

İş mantığı testleri Flet içe aktarmaz; CI'da Flet olmadan da çalışır.
UI testleri Flet kuruluysa çalışır.
"""

import json
import pytest

from mobile_client.core.constants import DEMO_INVALID_PASSWORD, MAX_FAILED_LOGIN_ATTEMPTS
from mobile_client.services.auth_service import (
    AuthService,
    LoginAttemptTracker,
    validate_email,
    validate_name,
    validate_password,
    validate_password_confirm,
    validate_role,
    validate_student_number,
    validate_terms,
)


@pytest.fixture
def temp_users_file(tmp_path):
    """Testler için geçici users.json dosyası oluşturur."""
    users = [
        {
            "id": 1,
            "first_name": "Ahmet",
            "last_name": "Yılmaz",
            "email": "ahmet.yilmaz@itu.edu.tr",
            "role": "organizer",
            "is_student": False,
            "student_number": None,
            "notify_email": True,
            "avatar_url": None,
            "created_at": "2024-01-15T09:30:00Z",
        },
        {
            "id": 2,
            "first_name": "Ayşe",
            "last_name": "Kaya",
            "email": "ayse.kaya@itu.edu.tr",
            "role": "participant",
            "is_student": True,
            "student_number": "2019123456",
            "notify_email": True,
            "avatar_url": None,
            "created_at": "2024-01-16T10:45:00Z",
        },
    ]
    path = tmp_path / "users.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    return path


# ==============================================================================
# Validasyon Birim Testleri (BR-1.1 .. BR-1.6)
# ==============================================================================


@pytest.mark.parametrize(
    "email",
    [
        "user@itu.edu.tr",
        "first.last@example.com",
        "student+1@ogr.iu.edu.tr",
    ],
)
def test_validate_email_valid(email):
    ok, err = validate_email(email)
    assert ok is True
    assert err == ""


@pytest.mark.parametrize(
    "email",
    [
        "",
        "   ",
        "plainaddress",
        "@missing.com",
        "user@domain",
        "user@domain..com",
        "user@domain.",
        "user@-domain.com",
        "user@domain.c",
    ],
)
def test_validate_email_invalid(email):
    ok, err = validate_email(email)
    assert ok is False
    assert err != ""


@pytest.mark.parametrize(
    "password",
    [
        "Passwor1",  # 8 karakter alt sınır (BR-1.3)
        "MySecurePass123",
        "A123456789012345678b",  # 20 karakter üst sınır (BR-1.3)
    ],
)
def test_validate_password_valid_boundaries(password):
    ok, err = validate_password(password)
    assert ok is True
    assert err == ""


@pytest.mark.parametrize(
    "password",
    [
        "",
        "Pass1!",  # < 8 karakter
        "A1234567890123456789b",  # > 20 karakter (21)
        "OnlyLettersHere",  # rakam yok
        "12345678",  # harf yok
    ],
)
def test_validate_password_invalid(password):
    ok, err = validate_password(password)
    assert ok is False
    assert err != ""


def test_validate_other_registration_fields():
    assert validate_name("", "Ad")[0] is False
    assert validate_name("Ali", "Ad")[0] is True
    assert validate_password_confirm("Pass1234", "Pass1234")[0] is True
    assert validate_password_confirm("Pass1234", "Diff1234")[0] is False
    assert validate_role("participant")[0] is True
    assert validate_role("organizer")[0] is True
    assert validate_role("admin")[0] is False
    assert validate_student_number(False, None)[0] is True
    assert validate_student_number(True, "")[0] is False
    assert validate_student_number(True, "abc12")[0] is False
    assert validate_student_number(True, "2019123456")[0] is True
    assert validate_terms(False)[0] is False
    assert validate_terms(True)[0] is True


# ==============================================================================
# Login ve Token Oturum Testleri
# ==============================================================================


def test_login_success_generates_token_and_sets_session(temp_users_file):
    service = AuthService(users_file=temp_users_file)
    result = service.login("Ayse.Kaya@itu.edu.tr", "HerhangiSifre1")

    assert result.success is True
    assert result.token is not None and result.token.startswith("evh_")
    assert result.user is not None
    assert result.user.email == "ayse.kaya@itu.edu.tr"
    assert service.is_authenticated is True


def test_login_rejects_demo_password_1234(temp_users_file):
    service = AuthService(users_file=temp_users_file)
    result = service.login("ayse.kaya@itu.edu.tr", DEMO_INVALID_PASSWORD)

    assert result.success is False
    assert result.error_code == "invalid_credentials"
    assert service.is_authenticated is False


def test_login_rejects_unknown_email(temp_users_file):
    service = AuthService(users_file=temp_users_file)
    result = service.login("yok@itu.edu.tr", "ValidPass1")

    assert result.success is False
    assert result.error_code == "invalid_credentials"


def test_login_locks_account_after_max_failed_attempts(temp_users_file):
    tracker = LoginAttemptTracker(max_attempts=MAX_FAILED_LOGIN_ATTEMPTS, lockout_minutes=15)
    service = AuthService(users_file=temp_users_file, attempt_tracker=tracker)

    for _ in range(MAX_FAILED_LOGIN_ATTEMPTS - 1):
        res = service.login("ayse.kaya@itu.edu.tr", DEMO_INVALID_PASSWORD)
        assert res.error_code == "invalid_credentials"

    locked_res = service.login("ayse.kaya@itu.edu.tr", DEMO_INVALID_PASSWORD)
    assert locked_res.success is False
    assert locked_res.error_code == "account_locked"

    # Kilitliyken doğru şifreyle bile giriş engellenmelidir (BR-1.4)
    blocked_res = service.login("ayse.kaya@itu.edu.tr", "ValidPass1")
    assert blocked_res.success is False
    assert blocked_res.error_code == "account_locked"


def test_login_network_error_returns_network_error(temp_users_file):
    service = AuthService(users_file=temp_users_file, simulate_network_error=True)
    result = service.login("ayse.kaya@itu.edu.tr", "ValidPass1")

    assert result.success is False
    assert result.error_code == "network_error"
    assert "Ağ hatası" in result.message


def test_login_missing_json_file_returns_network_error(tmp_path):
    service = AuthService(users_file=tmp_path / "missing_users.json")
    result = service.login("ayse.kaya@itu.edu.tr", "ValidPass1")

    assert result.success is False
    assert result.error_code == "network_error"


def test_restore_session_and_logout(temp_users_file):
    service = AuthService(users_file=temp_users_file)
    assert service.restore_session("evh_saved_token", "ayse.kaya@itu.edu.tr") is True
    assert service.is_authenticated is True
    assert service.current_user.email == "ayse.kaya@itu.edu.tr"

    service.logout()
    assert service.is_authenticated is False
    assert service.current_token is None
    assert service.current_user is None


# ==============================================================================
# Register ve JSON Yazma Testleri (BR-1.2, BR-1.5, BR-1.6)
# ==============================================================================


def test_register_participant_writes_valid_json_without_password(temp_users_file):
    service = AuthService(users_file=temp_users_file)
    result = service.register(
        first_name="Zeynep",
        last_name="Arslan",
        email="Zeynep.Arslan@itu.edu.tr",
        password="Password1",
        password_confirm="Password1",
        role="participant",
        is_student=True,
        student_number="2022123456",
        notify_email=True,
        terms_accepted=True,
    )

    assert result.success is True
    assert result.user is not None
    assert result.user.id == 3
    assert result.user.email == "zeynep.arslan@itu.edu.tr"
    assert result.user.approved is True

    with open(temp_users_file, "r", encoding="utf-8") as f:
        saved = json.load(f)

    assert len(saved) == 3
    new_record = saved[-1]
    assert new_record["email"] == "zeynep.arslan@itu.edu.tr"
    assert new_record["is_student"] is True
    assert new_record["student_number"] == "2022123456"
    assert "password" not in new_record


def test_register_organizer_sets_approved_false_per_br_1_5(temp_users_file):
    service = AuthService(users_file=temp_users_file)
    result = service.register(
        first_name="Kemal",
        last_name="Öz",
        email="kemal.oz@itu.edu.tr",
        password="Organizer1",
        password_confirm="Organizer1",
        role="organizer",
        is_student=False,
        terms_accepted=True,
    )

    assert result.success is True
    assert result.user.role == "organizer"
    assert result.user.approved is False
    assert "yönetici onayı" in result.message.lower()

    with open(temp_users_file, "r", encoding="utf-8") as f:
        saved = json.load(f)
    assert saved[-1]["approved"] is False


def test_register_rejects_duplicate_email_case_insensitive(temp_users_file):
    service = AuthService(users_file=temp_users_file)
    result = service.register(
        first_name="Ayşe",
        last_name="Kaya",
        email="AYSE.KAYA@itu.edu.tr",
        password="Password1",
        password_confirm="Password1",
        role="participant",
        terms_accepted=True,
    )

    assert result.success is False
    assert result.error_code == "duplicate_email"


# ==============================================================================
# Flet UI Etkileşim Testleri (Flet kuruluysa)
# ==============================================================================


def test_login_view_shows_toast_on_invalid_password(temp_users_file):
    ft = pytest.importorskip("flet")
    from mobile_client.views.auth_view import build_login_view

    class DummyPage:
        def __init__(self):
            self.dialogs = []
            self.updated = 0

        def show_dialog(self, dialog):
            self.dialogs.append(dialog)

        def update(self):
            self.updated += 1

    page = DummyPage()
    service = AuthService(users_file=temp_users_file)
    view = build_login_view(auth_service=service, page=page)

    # Form kartındaki kontrolleri bul
    card = view.controls[0].content
    col = card.content
    email_field = next(c for c in col.controls if isinstance(c, ft.TextField) and not c.password)
    password_field = next(c for c in col.controls if isinstance(c, ft.TextField) and c.password)
    login_btn = next(c for c in col.controls if isinstance(c, ft.FilledButton))

    email_field.value = "ayse.kaya@itu.edu.tr"
    password_field.value = "1234"
    login_btn.on_click(None)

    assert len(page.dialogs) == 1
    assert isinstance(page.dialogs[0], ft.SnackBar)
    assert service.is_authenticated is False
