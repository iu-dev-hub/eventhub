"""Mobile client page views package (TG-160, TG-182, TG-183, TG-184)."""

from mobile_client.views.auth_view import build_login_view, build_register_view
from mobile_client.views.base import PLACEHOLDER_TEXT, build_page_view
from mobile_client.views.event_detail_view import (
    build_event_detail_view,
    build_payment_view,
)
from mobile_client.views.events_view import build_events_view
from mobile_client.views.profile_view import build_profile_view
from mobile_client.views.tickets_view import build_tickets_view

__all__ = [
    "PLACEHOLDER_TEXT",
    "build_event_detail_view",
    "build_events_view",
    "build_login_view",
    "build_page_view",
    "build_payment_view",
    "build_profile_view",
    "build_register_view",
    "build_tickets_view",
]
