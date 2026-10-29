"""Account services - core business logic for user management (BR-1).

This module contains server-side business rules and database queries
for user accounts, registration, and secure password hashing.
"""

import re
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
    row = db.execute(
        "SELECT id FROM users WHERE LOWER(email) = LOWER(?) LIMIT 1",
        (cleaned_email,),
    ).fetchone()
    return row is not None


def register_user(email: str, password: str, role: str = DEFAULT_ROLE) -> Dict[str, Any]:
    """Registers a new user with secure scrypt password hashing (BR-1.1, BR-1.2, TG-8, TG-10).

    Args:
        email: The user's unique email address.
        password: The user's plaintext password.
        role: User role ('participant', 'organizer', 'admin'). Default is 'participant'.

    Returns:
        Dictionary containing created user information (id, email, role).

    Raises:
        ValueError: If email or password is missing/invalid, or role is invalid.
        DuplicateEmailError: If the email address is already registered (409 Conflict).
    """
    if not email or not isinstance(email, str) or not email.strip():
        raise ValueError("E-posta adresi boş bırakılamaz.")
    if not password or not isinstance(password, str):
        raise ValueError("Şifre boş bırakılamaz.")
    if role not in VALID_ROLES:
        raise ValueError(f"Geçersiz hesap türü: {role}")

    cleaned_email = email.strip().lower()

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
        "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
        (cleaned_email, hashed, role),
    )
    db.commit()

    return {
        "id": cursor.lastrowid,
        "email": cleaned_email,
        "role": role,
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
        Dictionary containing authenticated user info (id, email, role).

    Raises:
        ValueError: If email/password is missing or invalid, or if authentication fails.
    """
    if not email or not isinstance(email, str) or not email.strip():
        raise ValueError("E-posta adresi boş bırakılamaz.")
    if not password or not isinstance(password, str) or not password.strip():
        raise ValueError("Şifre boş bırakılamaz.")

    cleaned_email = email.strip().lower()
    db = get_db()
    row = db.execute(
        "SELECT id, email, password_hash, role FROM users WHERE LOWER(email) = LOWER(?) LIMIT 1",
        (cleaned_email,),
    ).fetchone()

    # TG-52 (OWASP): Timing attack ve user enumeration koruması
    target_hash = row["password_hash"] if row is not None else DUMMY_SCRYPT_HASH
    is_valid = verify_password(password, target_hash)

    if row is None or not is_valid:
        raise ValueError("Geçersiz e-posta veya şifre.")

    return {
        "id": row["id"],
        "email": row["email"],
        "role": row["role"],
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
    row = db.execute(
        "SELECT id, email, role, created_at FROM users WHERE id = ? LIMIT 1",
        (user_id,),
    ).fetchone()
    if row is None:
        return None
    return dict(row)
