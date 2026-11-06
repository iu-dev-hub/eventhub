"""Account services - core business logic for user management (BR-1).

This module contains server-side business rules and database queries
for user accounts, registration, and secure password hashing.
"""

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from werkzeug.security import check_password_hash, generate_password_hash

from app.core.db import get_db

VALID_ROLES = ("participant", "organizer", "admin")
DEFAULT_ROLE = "participant"

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 20


class DuplicateEmailError(ValueError):
    """Raised when attempting to register an already existing email (BR-1.2)."""

    pass


def validate_email_format(email: str) -> None:
    """Validates email address format (BR-1.2, TG-9).

    Checks standard email structure (RFC 5322 pattern), ensuring local-part,
    '@' symbol, domain with valid extension, and no consecutive dots.

    Args:
        email: Email address string to validate.

    Raises:
        ValueError: If email is empty or has an invalid format.
    """
    if not email or not isinstance(email, str) or not email.strip():
        raise ValueError("E-posta adresi boş bırakılamaz.")
    cleaned = email.strip()
    if not EMAIL_REGEX.match(cleaned) or ".." in cleaned or cleaned.endswith("."):
        raise ValueError("Geçersiz e-posta formatı.")
    domain = cleaned.split("@")[1]
    labels = domain.split(".")
    if "." not in domain or any(label.startswith("-") or label.endswith("-") for label in labels):
        raise ValueError("Geçersiz e-posta formatı.")
    tld = labels[-1]
    if len(tld) < 2:
        raise ValueError("Geçersiz e-posta formatı.")


def validate_password_strength(password: str) -> None:
    """Validates password strength according to business rules (BR-1.3, TG-9).

    Requirements:
        - Must be between 8 and 20 characters in length.
        - Must contain at least one letter (a-z, A-Z).
        - Must contain at least one digit (0-9).

    Args:
        password: The plaintext password string to validate.

    Raises:
        ValueError: If password is empty or does not satisfy complexity requirements.
    """
    if not password or not isinstance(password, str):
        raise ValueError("Şifre boş bırakılamaz.")
    if len(password) < MIN_PASSWORD_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(
            f"Şifre {MIN_PASSWORD_LENGTH} ile {MAX_PASSWORD_LENGTH} karakter arasında olmalıdır."
        )
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise ValueError("Şifre en az bir harf ve en az bir rakam içermelidir.")


def hash_password(password: str) -> str:
    """Hashes a plaintext password using Werkzeug's scrypt key derivation (TG-10).

    Produces a memory-hard scrypt hash containing a cryptographically secure,
    random per-password salt. Plaintext passwords are never stored.

    Args:
        password: The plaintext password to hash.

    Returns:
        The scrypt hash string (format: 'scrypt:32768:8:1$<salt>$<hash>').

    Raises:
        ValueError: If password is empty.
    """
    if not password:
        raise ValueError("Şifre boş bırakılamaz.")
    return generate_password_hash(password, method="scrypt")


def verify_password(password: str, password_hash: str) -> bool:
    """Verifies a plaintext password against a stored scrypt password hash.

    Args:
        password: The plaintext password to verify.
        password_hash: The stored scrypt hash string.

    Returns:
        True if the password matches, False otherwise.
    """
    if not password or not password_hash:
        return False
    return check_password_hash(password_hash, password)


def ensure_user_columns(db) -> None:
    """Ensures backwards compatibility if table was created in Sprint 1/2."""
    try:
        rows = db.execute("PRAGMA table_info(users)").fetchall()
        cols = {row["name"] for row in rows}
        if cols and "first_name" not in cols:
            db.execute("ALTER TABLE users ADD COLUMN first_name TEXT NOT NULL DEFAULT ''")
            db.execute("ALTER TABLE users ADD COLUMN last_name TEXT NOT NULL DEFAULT ''")
            db.execute("ALTER TABLE users ADD COLUMN is_student BOOLEAN NOT NULL DEFAULT 0")
            db.execute("ALTER TABLE users ADD COLUMN student_number TEXT DEFAULT NULL")
            db.execute("ALTER TABLE users ADD COLUMN notify_email BOOLEAN NOT NULL DEFAULT 1")
            db.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT DEFAULT NULL")
            db.commit()

        db.execute(
            "CREATE TABLE IF NOT EXISTS password_resets ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, "
            "token_hash TEXT NOT NULL UNIQUE, expires_at TIMESTAMP NOT NULL, "
            "used BOOLEAN NOT NULL DEFAULT 0, "
            "created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, "
            "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)"
        )
        db.commit()
    except Exception:
        pass


def is_email_registered(email: str) -> bool:
    """Checks whether an email address is already registered in the system (BR-1.2).

    Email comparison is case-insensitive.

    Args:
        email: Email address to check.

    Returns:
        True if the email already exists in users table, False otherwise.
    """
    if not email or not email.strip():
        return False
    cleaned_email = email.strip().lower()
    db = get_db()
    ensure_user_columns(db)
    row = db.execute(
        "SELECT id FROM users WHERE LOWER(email) = LOWER(?) LIMIT 1",
        (cleaned_email,),
    ).fetchone()
    return row is not None


def register_user(
    email: str,
    password: str,
    role: str = DEFAULT_ROLE,
    first_name: str = "",
    last_name: str = "",
    terms_accepted: bool = True,
    is_student: bool = False,
    student_number: Optional[str] = None,
) -> Dict[str, Any]:
    """Registers a new user with scrypt password hashing (TG-8, TG-10, TG-68, TG-78).

    Args:
        email: The user's unique email address.
        password: The user's plaintext password.
        role: User role ('participant', 'organizer', 'admin'). Default is 'participant'.
        first_name: User first name.
        last_name: User last name.
        terms_accepted: Boolean acceptance of Terms of Service (BR-1.1, TG-68).
        is_student: Student status flag (TG-78, PO decision 3).
        student_number: Optional student identification number.

    Returns:
        Dictionary containing user information (id, first_name, last_name, email, role, is_student).

    Raises:
        ValueError: If inputs are invalid or terms not accepted.
        DuplicateEmailError: If the email address is already registered (409 Conflict).
    """
    if terms_accepted is False or terms_accepted == 0:
        raise ValueError("Kullanım Koşulları kabul edilmelidir.")

    if not email or not isinstance(email, str) or not email.strip():
        raise ValueError("E-posta adresi boş bırakılamaz.")
    if not password or not isinstance(password, str):
        raise ValueError("Şifre boş bırakılamaz.")
    if role not in VALID_ROLES:
        raise ValueError(f"Geçersiz hesap türü: {role}")

    cleaned_email = email.strip().lower()
    cleaned_first_name = (first_name or "").strip()
    cleaned_last_name = (last_name or "").strip()
    cleaned_student_num = (student_number or "").strip() if student_number else None

    # TG-9, BR-1.2: E-posta format kontrolü
    validate_email_format(cleaned_email)

    # TG-9, BR-1.3: Şifre karmaşıklık kuralları
    validate_password_strength(password)

    # BR-1.2: Bir e-posta adresiyle yalnızca bir hesap açılabilir.
    if is_email_registered(cleaned_email):
        raise DuplicateEmailError("Bu e-posta adresi zaten kayıtlı.")

    # TG-10: Parolaların scrypt ile güvenli saklanması
    hashed = hash_password(password)

    db = get_db()
    cursor = db.execute(
        "INSERT INTO users ("
        "first_name, last_name, email, password_hash, role, is_student, student_number"
        ") VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            cleaned_first_name,
            cleaned_last_name,
            cleaned_email,
            hashed,
            role,
            int(bool(is_student)),
            cleaned_student_num,
        ),
    )
    db.commit()

    return {
        "id": cursor.lastrowid,
        "first_name": cleaned_first_name,
        "last_name": cleaned_last_name,
        "email": cleaned_email,
        "role": role,
        "is_student": bool(is_student),
        "student_number": cleaned_student_num,
    }


DUMMY_SCRYPT_HASH = (
    "scrypt:32768:8:1$6FpUTZybXZ3HcojC$fcc81f26de099d38104f6aae5a985cd85d09fb5ec"
    "16119e27a6b9ba0fa7ffe20009ab1019b6600abae18058587be0af708f41cf8d2e46acac90"
    "649f5ddcae0f0"
)


def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    """Authenticates a user with email and plaintext password (TG-50, TG-52, PB-02).

    Validates that credentials match an existing user record and checks
    the provided password against the stored scrypt hash. Implements
    timing-attack countermeasure to prevent user enumeration (TG-52).

    Args:
        email: User email address.
        password: User plaintext password.

    Returns:
        Dictionary containing user info (id, first_name, last_name, email, role, is_student).

    Raises:
        ValueError: If email/password is missing or invalid, or if authentication fails.
    """
    if not email or not isinstance(email, str) or not email.strip():
        raise ValueError("E-posta adresi boş bırakılamaz.")
    if not password or not isinstance(password, str) or not password.strip():
        raise ValueError("Şifre boş bırakılamaz.")

    cleaned_email = email.strip().lower()
    db = get_db()
    ensure_user_columns(db)
    row = db.execute(
        "SELECT id, first_name, last_name, email, password_hash, role, is_student, student_number "
        "FROM users WHERE LOWER(email) = LOWER(?) LIMIT 1",
        (cleaned_email,),
    ).fetchone()

    # TG-52 (OWASP): Timing attack ve user enumeration koruması
    target_hash = row["password_hash"] if row is not None else DUMMY_SCRYPT_HASH
    is_valid = verify_password(password, target_hash)

    if row is None or not is_valid:
        raise ValueError("Geçersiz e-posta veya şifre.")

    return {
        "id": row["id"],
        "first_name": row["first_name"] if "first_name" in row.keys() else "",
        "last_name": row["last_name"] if "last_name" in row.keys() else "",
        "email": row["email"],
        "role": row["role"],
        "is_student": bool(row["is_student"]) if "is_student" in row.keys() else False,
        "student_number": row["student_number"] if "student_number" in row.keys() else None,
    }


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetches user information by user ID.

    Args:
        user_id: The integer ID of the user.

    Returns:
        Dictionary containing user information or None if not found.
    """
    if not user_id or not isinstance(user_id, int):
        return None
    db = get_db()
    ensure_user_columns(db)
    query = (
        "SELECT id, first_name, last_name, email, role, is_student, "
        "student_number, notify_email, avatar_url, created_at "
        "FROM users WHERE id = ? LIMIT 1"
    )
    row = db.execute(query, (user_id,)).fetchone()
    if row is None:
        return None
    res = dict(row)
    res["is_student"] = bool(res.get("is_student", False))
    res["notify_email"] = bool(res.get("notify_email", True))
    return res


def update_user_profile(user_id: int, first_name: str, last_name: str) -> Dict[str, Any]:
    """Updates user's first and last name (AC-06, TG-73).

    Strictly protects role and email from modification (PO Decision 4).
    """
    if not user_id or not isinstance(user_id, int):
        raise ValueError("Geçersiz kullanıcı kimliği.")
    if not first_name or not isinstance(first_name, str) or not first_name.strip():
        raise ValueError("Ad alanı boş bırakılamaz.")
    if not last_name or not isinstance(last_name, str) or not last_name.strip():
        raise ValueError("Soyad alanı boş bırakılamaz.")

    cleaned_first = first_name.strip()
    cleaned_last = last_name.strip()

    db = get_db()
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError("Kullanıcı bulunamadı.")

    db.execute(
        "UPDATE users SET first_name = ?, last_name = ? WHERE id = ?",
        (cleaned_first, cleaned_last, user_id),
    )
    db.commit()

    updated = get_user_by_id(user_id)
    return updated or {}


def change_password(user_id: int, current_password: str, new_password: str) -> bool:
    """Changes user's password after verifying existing password (AC-08, TG-75)."""
    if not user_id or not isinstance(user_id, int):
        raise ValueError("Geçersiz kullanıcı kimliği.")
    if not current_password or not isinstance(current_password, str):
        raise ValueError("Mevcut şifre boş bırakılamaz.")
    if not new_password or not isinstance(new_password, str):
        raise ValueError("Yeni şifre boş bırakılamaz.")

    db = get_db()
    row = db.execute("SELECT password_hash FROM users WHERE id = ? LIMIT 1", (user_id,)).fetchone()
    if not row:
        raise ValueError("Kullanıcı bulunamadı.")

    if not verify_password(current_password, row["password_hash"]):
        raise ValueError("Mevcut şifreniz hatalı.")

    validate_password_strength(new_password)
    new_hash = hash_password(new_password)

    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
    db.commit()
    return True


def create_password_reset_token(email: str) -> Optional[str]:
    """Generates a secure 15-minute single-use password reset token (AC-09, TG-76)."""
    if not email or not isinstance(email, str) or not email.strip():
        return None

    cleaned_email = email.strip().lower()
    db = get_db()
    row = db.execute(
        "SELECT id FROM users WHERE LOWER(email) = LOWER(?) LIMIT 1", (cleaned_email,)
    ).fetchone()
    if not row:
        return None

    user_id = row["id"]
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    db.execute(
        "INSERT INTO password_resets (user_id, token_hash, expires_at, used) VALUES (?, ?, ?, 0)",
        (user_id, token_hash, expires_at.strftime("%Y-%m-%d %H:%M:%S")),
    )
    db.commit()
    return raw_token


def reset_password_with_token(raw_token: str, new_password: str) -> bool:
    """Validates reset token and sets new password (AC-09, TG-76)."""
    if not raw_token or not isinstance(raw_token, str):
        raise ValueError("Geçersiz veya süresi dolmuş sıfırlama bağlantısı.")

    token_hash = hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()
    db = get_db()
    row = db.execute(
        "SELECT id, user_id, expires_at, used FROM password_resets WHERE token_hash = ? LIMIT 1",
        (token_hash,),
    ).fetchone()

    if not row or row["used"]:
        raise ValueError("Geçersiz veya süresi dolmuş sıfırlama bağlantısı.")

    exp_str = row["expires_at"]
    try:
        exp_dt = datetime.strptime(exp_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        exp_dt = datetime.fromisoformat(exp_str).replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > exp_dt:
        raise ValueError("Geçersiz veya süresi dolmuş sıfırlama bağlantısı.")

    validate_password_strength(new_password)
    new_hash = hash_password(new_password)

    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, row["user_id"]))
    db.execute("UPDATE password_resets SET used = 1 WHERE id = ?", (row["id"],))
    db.commit()
    return True


def update_notification_preferences(user_id: int, notify_email: bool) -> bool:
    """Updates user email notification preferences (AC-14, TG-81)."""
    if not user_id or not isinstance(user_id, int):
        raise ValueError("Geçersiz kullanıcı kimliği.")
    db = get_db()
    db.execute(
        "UPDATE users SET notify_email = ? WHERE id = ?",
        (int(bool(notify_email)), user_id),
    )
    db.commit()
    return True


def update_avatar_url(user_id: int, avatar_url: str) -> bool:
    """Updates user avatar URL (AC-14, TG-81)."""
    if not user_id or not isinstance(user_id, int):
        raise ValueError("Geçersiz kullanıcı kimliği.")
    db = get_db()
    db.execute(
        "UPDATE users SET avatar_url = ? WHERE id = ?",
        (avatar_url.strip() if avatar_url else None, user_id),
    )
    db.commit()
    return True
