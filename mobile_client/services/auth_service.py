"""Authentication, validation, and JSON persistence services for EventHub mobile client.

Bu modül Flet içe aktarmaz; böylece tüm iş kuralları ve validasyonlar CI'da
Flet kurulu olmadan da test edilebilir (mobile_client/README.md).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import secrets
from typing import Dict, List, Optional, Tuple

from mobile_client.core.constants import (
    DEMO_INVALID_PASSWORD,
    LOCKOUT_DURATION_MINUTES,
    MAX_FAILED_LOGIN_ATTEMPTS,
    MAX_PASSWORD_LENGTH,
    MAX_STUDENT_NUMBER_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_STUDENT_NUMBER_LENGTH,
    REGISTER_ROLES,
)
from mobile_client.models.user import User

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
DEFAULT_USERS_JSON_PATH = Path(__file__).resolve().parents[2] / "app" / "api" / "users.json"


@dataclass
class AuthResult:
    """Kimlik doğrulama ve kayıt işlemlerinin standart dönüş modeli."""

    success: bool
    message: str = ""
    error_code: str = ""
    user: Optional[User] = None
    token: Optional[str] = None
    field_errors: Optional[Dict[str, str]] = None


def validate_name(value: str, field_label: str = "Ad") -> Tuple[bool, str]:
    """Ad ve soyad alanlarının boş olmamasını ve uzunluk sınırını doğrular."""
    if not isinstance(value, str) or not value.strip():
        return False, f"{field_label} alanı boş bırakılamaz."
    cleaned = value.strip()
    if len(cleaned) > 50:
        return False, f"{field_label} en fazla 50 karakter olabilir."
    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """E-posta adresinin formatını doğrular (BR-1.2)."""
    if not isinstance(email, str) or not email.strip():
        return False, "E-posta adresi boş bırakılamaz."
    cleaned = email.strip()
    if not EMAIL_REGEX.match(cleaned) or ".." in cleaned or cleaned.endswith("."):
        return False, "Geçersiz e-posta formatı."
    domain = cleaned.split("@")[1]
    labels = domain.split(".")
    if any(label.startswith("-") or label.endswith("-") for label in labels):
        return False, "Geçersiz e-posta formatı."
    if len(labels[-1]) < 2:
        return False, "Geçersiz e-posta formatı."
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """Şifre kurallarını doğrular (BR-1.3: 8–20 karakter, en az 1 harf ve 1 rakam)."""
    if not isinstance(password, str) or not password:
        return False, "Şifre boş bırakılamaz."
    if len(password) < MIN_PASSWORD_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
        return (
            False,
            f"Şifre {MIN_PASSWORD_LENGTH} ile {MAX_PASSWORD_LENGTH} karakter arasında olmalıdır.",
        )
    if not any(c.isalpha() for c in password):
        return False, "Şifre en az bir harf içermelidir."
    if not any(c.isdigit() for c in password):
        return False, "Şifre en az bir rakam içermelidir."
    return True, ""


def validate_password_confirm(password: str, password_confirm: str) -> Tuple[bool, str]:
    """Kayıt sırasında şifre tekrarının eşleştiğini doğrular."""
    if not isinstance(password_confirm, str) or not password_confirm:
        return False, "Şifre tekrarı boş bırakılamaz."
    if password != password_confirm:
        return False, "Girilen şifreler birbiriyle eşleşmiyor."
    return True, ""


def validate_role(role: str) -> Tuple[bool, str]:
    """Kayıt için seçilen hesap türünü doğrular (BR-1.1, BR-1.5)."""
    if role not in REGISTER_ROLES:
        return False, "Geçersiz hesap türü seçildi."
    return True, ""


def validate_student_number(is_student: bool, student_number: Optional[str]) -> Tuple[bool, str]:
    """Öğrenci statüsü seçiliyse öğrenci numarasını doğrular (BR-1.6)."""
    if not is_student:
        return True, ""
    if not isinstance(student_number, str) or not student_number.strip():
        return False, "Öğrenci seçimi için öğrenci numarası zorunludur."
    cleaned = student_number.strip()
    if not cleaned.isdigit() or not (
        MIN_STUDENT_NUMBER_LENGTH <= len(cleaned) <= MAX_STUDENT_NUMBER_LENGTH
    ):
        return (
            False,
            f"Öğrenci numarası {MIN_STUDENT_NUMBER_LENGTH}–{MAX_STUDENT_NUMBER_LENGTH} "
            "haneli rakamlardan oluşmalıdır.",
        )
    return True, ""


def validate_terms(terms_accepted: bool) -> Tuple[bool, str]:
    """Kullanım Koşulları onayını doğrular."""
    if not terms_accepted:
        return False, "Devam etmek için Kullanım Koşulları'nı kabul etmelisiniz."
    return True, ""


def dict_to_user(data: dict) -> User:
    """JSON sözlüğünü User model nesnesine dönüştürür."""
    role = str(data.get("role", "participant"))
    # Mevcut sahte veride approved alanı yoksa organizatörler dahil varsayılan True kabul edilir;
    # yeni kayıt olan organizatörlerde BR-1.5 gereği açıkça False yazılır.
    default_approved = True if "approved" not in data else False
    return User(
        id=int(data["id"]),
        first_name=str(data.get("first_name", "")),
        last_name=str(data.get("last_name", "")),
        email=str(data.get("email", "")),
        role=role,
        is_student=bool(data.get("is_student", False)),
        student_number=data.get("student_number"),
        notify_email=bool(data.get("notify_email", True)),
        avatar_url=data.get("avatar_url"),
        created_at=str(data.get("created_at", "")),
        approved=bool(data.get("approved", default_approved)),
    )


class LoginAttemptTracker:
    """Art arda hatalı giriş denemelerinde hesabı geçici olarak kilitler (BR-1.4)."""

    def __init__(
        self,
        max_attempts: int = MAX_FAILED_LOGIN_ATTEMPTS,
        lockout_minutes: int = LOCKOUT_DURATION_MINUTES,
    ):
        self.max_attempts = max_attempts
        self.lockout_minutes = lockout_minutes
        self._records: Dict[str, Dict] = {}

    def _normalize(self, email: str) -> str:
        return email.strip().lower() if isinstance(email, str) else ""

    def is_locked(self, email: str) -> Tuple[bool, int]:
        """Hesap kilitliyse (True, kalan_saniye) döndürür."""
        key = self._normalize(email)
        record = self._records.get(key)
        if not record or not record.get("locked_until"):
            return False, 0

        now = datetime.now(timezone.utc)
        if now < record["locked_until"]:
            remaining = max(1, int((record["locked_until"] - now).total_seconds()))
            return True, remaining

        self.reset(key)
        return False, 0

    def record_failure(self, email: str) -> Tuple[int, bool]:
        """Hatalı giriş denemesini kaydeder; limite ulaşılırsa hesabı kilitler."""
        key = self._normalize(email)
        if not key:
            return 0, False

        now = datetime.now(timezone.utc)
        record = self._records.setdefault(key, {"count": 0, "locked_until": None})
        if record["locked_until"] and now >= record["locked_until"]:
            record["count"] = 0
            record["locked_until"] = None

        record["count"] += 1
        if record["count"] >= self.max_attempts:
            record["locked_until"] = now + timedelta(minutes=self.lockout_minutes)
            return record["count"], True

        return record["count"], False

    def reset(self, email: str) -> None:
        """Başarılı girişte hatalı deneme sayacını sıfırlar."""
        self._records.pop(self._normalize(email), None)


class AuthService:
    """Mobil istemci için JSON tabanlı kimlik doğrulama ve kayıt servisi."""

    def __init__(
        self,
        users_file: Optional[Path] = None,
        attempt_tracker: Optional[LoginAttemptTracker] = None,
        simulate_network_error: bool = False,
    ):
        self.users_file = Path(users_file) if users_file else DEFAULT_USERS_JSON_PATH
        self.attempt_tracker = attempt_tracker or LoginAttemptTracker()
        self.simulate_network_error = simulate_network_error
        self.current_token: Optional[str] = None
        self.current_user: Optional[User] = None

    @property
    def is_authenticated(self) -> bool:
        """Aktif bir lokal oturum tokenı ve kullanıcı varsa True döndürür."""
        return bool(self.current_token and self.current_user)

    def load_users(self) -> List[dict]:
        """Kullanıcı listesini json.load ile okur."""
        if self.simulate_network_error:
            raise ConnectionError("Simüle edilmiş ağ bağlantı hatası.")
        with open(self.users_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Kullanıcı veri dosyası geçerli bir liste formatında değil.")
        return data

    def _save_users(self, users: List[dict]) -> None:
        """Kullanıcı listesini bellekte güncelleyip json.dump ile yeniden yazar."""
        if self.simulate_network_error:
            raise ConnectionError("Simüle edilmiş ağ bağlantı hatası.")
        with open(self.users_file, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

    def find_user_by_email(self, email: str) -> Optional[User]:
        """E-posta adresine göre users.json içinden kullanıcıyı bulur."""
        cleaned = email.strip().lower()
        for record in self.load_users():
            if str(record.get("email", "")).strip().lower() == cleaned:
                return dict_to_user(record)
        return None

    def restore_session(self, token: Optional[str], email: Optional[str]) -> bool:
        """Lokal depolamadan okunan token ve e-posta ile oturumu geri yükler."""
        if not token or not email:
            return False
        try:
            user = self.find_user_by_email(email)
        except (OSError, ConnectionError, ValueError, json.JSONDecodeError):
            return False
        if not user:
            return False
        self.current_token = token
        self.current_user = user
        return True

    def logout(self) -> None:
        """Aktif lokal oturumu ve token bilgisini temizler."""
        self.current_token = None
        self.current_user = None

    def login(self, email: str, password: str) -> AuthResult:
        """Kullanıcı girişini doğrular, token üretir ve hataları raporlar."""
        field_errors: Dict[str, str] = {}

        email_ok, email_err = validate_email(email)
        if not email_ok:
            field_errors["email"] = email_err

        if not isinstance(password, str) or not password.strip():
            field_errors["password"] = "Şifre boş bırakılamaz."

        if field_errors:
            first_msg = next(iter(field_errors.values()))
            return AuthResult(
                success=False,
                message=first_msg,
                error_code="validation_error",
                field_errors=field_errors,
            )

        cleaned_email = email.strip().lower()
        is_locked, remaining_seconds = self.attempt_tracker.is_locked(cleaned_email)
        if is_locked:
            remaining_minutes = max(1, (remaining_seconds + 59) // 60)
            return AuthResult(
                success=False,
                error_code="account_locked",
                message=(
                    "Çok sayıda hatalı giriş denemesi. Hesabınız geçici olarak "
                    f"kilitlendi ({remaining_minutes} dakika sonra tekrar deneyin)."
                ),
            )

        try:
            user = self.find_user_by_email(cleaned_email)
        except (OSError, ConnectionError, ValueError, json.JSONDecodeError):
            return AuthResult(
                success=False,
                error_code="network_error",
                message="Ağ hatası: Kullanıcı verilerine ulaşılamadı. Lütfen tekrar deneyin.",
            )

        # Demo kuralı: Şifre "1234" ise veya kullanıcı kayıtlı değilse giriş reddedilir.
        if password == DEMO_INVALID_PASSWORD or user is None:
            count, now_locked = self.attempt_tracker.record_failure(cleaned_email)
            if now_locked:
                return AuthResult(
                    success=False,
                    error_code="account_locked",
                    message=(
                        "Çok sayıda hatalı giriş denemesi. Hesabınız "
                        f"{LOCKOUT_DURATION_MINUTES} dakika süreyle geçici olarak kilitlendi."
                    ),
                )
            remaining = max(0, MAX_FAILED_LOGIN_ATTEMPTS - count)
            return AuthResult(
                success=False,
                error_code="invalid_credentials",
                message=f"Hatalı e-posta veya şifre. (Kalan deneme: {remaining})",
            )

        self.attempt_tracker.reset(cleaned_email)
        token = f"evh_{secrets.token_urlsafe(24)}"
        self.current_token = token
        self.current_user = user
        return AuthResult(
            success=True,
            message=f"Hoş geldiniz, {user.first_name}!",
            user=user,
            token=token,
        )

    def register(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        password_confirm: str,
        role: str = "participant",
        is_student: bool = False,
        student_number: Optional[str] = None,
        notify_email: bool = True,
        terms_accepted: bool = False,
    ) -> AuthResult:
        """Yeni kullanıcıyı Business Rules'a göre doğrular ve users.json'a ekler."""
        field_errors: Dict[str, str] = {}

        checks = [
            ("first_name", validate_name(first_name, "Ad")),
            ("last_name", validate_name(last_name, "Soyad")),
            ("email", validate_email(email)),
            ("password", validate_password(password)),
            ("password_confirm", validate_password_confirm(password, password_confirm)),
            ("role", validate_role(role)),
            ("student_number", validate_student_number(is_student, student_number)),
            ("terms", validate_terms(terms_accepted)),
        ]
        for field_name, (ok, err_msg) in checks:
            if not ok:
                field_errors[field_name] = err_msg

        if field_errors:
            first_msg = next(iter(field_errors.values()))
            return AuthResult(
                success=False,
                message=first_msg,
                error_code="validation_error",
                field_errors=field_errors,
            )

        cleaned_email = email.strip().lower()

        try:
            users = self.load_users()
        except (OSError, ConnectionError, ValueError, json.JSONDecodeError):
            return AuthResult(
                success=False,
                error_code="network_error",
                message="Ağ hatası: Kullanıcı verileri okunamadı. Lütfen tekrar deneyin.",
            )

        # BR-1.2: Bir e-posta adresiyle yalnızca bir hesap açılabilir.
        if any(str(u.get("email", "")).strip().lower() == cleaned_email for u in users):
            return AuthResult(
                success=False,
                error_code="duplicate_email",
                message="Bu e-posta adresi zaten kayıtlı.",
                field_errors={"email": "Bu e-posta adresi zaten kayıtlı."},
            )

        next_id = max((int(u.get("id", 0)) for u in users), default=0) + 1
        new_record = {
            "id": next_id,
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "email": cleaned_email,
            "role": role,
            "is_student": bool(is_student),
            "student_number": student_number.strip() if is_student and student_number else None,
            "notify_email": bool(notify_email),
            "avatar_url": None,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "approved": role != "organizer",  # BR-1.5
        }

        # Doğru JSON ekleme yöntemi: bellekte listeye ekle ve json.dump ile yeniden yaz.
        users.append(new_record)
        try:
            self._save_users(users)
        except (OSError, ConnectionError, ValueError):
            return AuthResult(
                success=False,
                error_code="network_error",
                message="Ağ hatası: Kayıt sunucuya yazılamadı. Lütfen tekrar deneyin.",
            )

        user_obj = dict_to_user(new_record)
        if role == "organizer":
            success_msg = (
                "Kayıt tamamlandı! Organizatör hesabınız yönetici onayından sonra "
                "etkinlik oluşturabilir (BR-1.5)."
            )
        else:
            success_msg = "Kayıt başarıyla tamamlandı. Şimdi giriş yapabilirsiniz."

        return AuthResult(
            success=True,
            message=success_msg,
            user=user_obj,
        )
