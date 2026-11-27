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
from mobile_client.services.event_service import (
    ALL_CATEGORIES_LABEL,
    EventService,
    dict_to_event,
    filter_and_sort_events,
    filter_events_by_category,
    normalize_search_text,
    parse_iso_datetime,
    search_events,
    sort_events_by_nearest_date,
)

__all__ = [
    "ALL_CATEGORIES_LABEL",
    "AuthResult",
    "AuthService",
    "EventService",
    "LoginAttemptTracker",
    "dict_to_event",
    "dict_to_user",
    "filter_and_sort_events",
    "filter_events_by_category",
    "normalize_search_text",
    "parse_iso_datetime",
    "search_events",
    "sort_events_by_nearest_date",
    "validate_email",
    "validate_name",
    "validate_password",
    "validate_password_confirm",
    "validate_role",
    "validate_student_number",
    "validate_terms",
]
