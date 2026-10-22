"""Account security utilities and brute-force protection (TG-53, TG-54, PB-02).

This module provides rate limiting, brute-force lockout tracking,
and access control decorators for authentication and authorization.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


class AccountLockoutTracker:
    """In-memory thread-safe tracker for failed login attempts and temporary lockouts (TG-53)."""

    def __init__(
        self,
        max_attempts: int = MAX_FAILED_ATTEMPTS,
        lockout_minutes: int = LOCKOUT_DURATION_MINUTES,
    ):
        self.max_attempts = max_attempts
        self.lockout_minutes = lockout_minutes
        # Stores email -> {"count": int, "locked_until": Optional[datetime]}
        self._records: Dict[str, Dict] = {}

    def _normalize_email(self, email: str) -> str:
        if not email or not isinstance(email, str):
            return ""
        return email.strip().lower()

    def is_locked(self, email: str) -> Tuple[bool, Optional[int]]:
        """Checks if the account corresponding to email is currently locked.

        Args:
            email: User's email address.

        Returns:
            Tuple of (is_locked: bool, remaining_seconds: Optional[int]).
        """
        normalized = self._normalize_email(email)
        if not normalized or normalized not in self._records:
            return False, None

        record = self._records[normalized]
        locked_until = record.get("locked_until")
        if not locked_until:
            return False, None

        now = datetime.now(timezone.utc)
        if now < locked_until:
            remaining = int((locked_until - now).total_seconds())
            return True, max(1, remaining)

        # Lockout period expired: reset counter
        self.reset(normalized)
        return False, None

    def record_failed_attempt(self, email: str) -> Tuple[int, bool]:
        """Records a failed login attempt for an email.

        If failed attempts reach max_attempts, locks the account.

        Args:
            email: User's email address.

        Returns:
            Tuple of (failed_count: int, is_now_locked: bool).
        """
        normalized = self._normalize_email(email)
        if not normalized:
            return 0, False

        now = datetime.now(timezone.utc)
        record = self._records.setdefault(normalized, {"count": 0, "locked_until": None})

        # If already locked and expired, reset first
        if record["locked_until"] and now >= record["locked_until"]:
            record["count"] = 0
            record["locked_until"] = None

        record["count"] += 1

        if record["count"] >= self.max_attempts:
            record["locked_until"] = now + timedelta(minutes=self.lockout_minutes)
            return record["count"], True

        return record["count"], False

    def reset(self, email: str) -> None:
        """Resets failed login attempts for an email upon successful login."""
        normalized = self._normalize_email(email)
        if normalized in self._records:
            del self._records[normalized]

    def clear_all(self) -> None:
        """Clears all tracking records (primarily for testing)."""
        self._records.clear()


# Global tracker singleton
lockout_tracker = AccountLockoutTracker()
