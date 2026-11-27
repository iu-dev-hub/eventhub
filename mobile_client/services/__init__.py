"""EventHub Mobile Client Services Package."""

from mobile_client.services.auth_service import (
    AuthResult,
    AuthService,
    LoginAttemptTracker,
    dict_to_user,
    validate_email,
    validate_name,
    validate_password,
    validate_password_confirm,
    validate_role,
    validate_student_number,
    validate_terms,
)

__all__ = [
    "AuthResult",
    "AuthService",
    "LoginAttemptTracker",
    "dict_to_user",
    "validate_email",
    "validate_name",
    "validate_password",
    "validate_password_confirm",
    "validate_role",
    "validate_student_number",
    "validate_terms",
]
