"""Account services - core business logic for user management (BR-1).

This module contains server-side business rules and database queries
for user accounts, registration, and secure password hashing.
"""

from typing import Any, Dict

from werkzeug.security import check_password_hash, generate_password_hash

from app.core.db import get_db

VALID_ROLES = ("participant", "organizer", "admin")
DEFAULT_ROLE = "participant"


class DuplicateEmailError(ValueError):
    """Raised when attempting to register an already existing email (BR-1.2)."""
    pass


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
    if not email or not email.strip():
        raise ValueError("E-posta adresi boş bırakılamaz.")
    if not password:
        raise ValueError("Şifre boş bırakılamaz.")
    if role not in VALID_ROLES:
        raise ValueError(f"Geçersiz hesap türü: {role}")

    cleaned_email = email.strip().lower()

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
