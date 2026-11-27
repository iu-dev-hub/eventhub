"""EventHub Mobile Client Views (TG-160)."""

from mobile_client.views.events_view import build_events_view
from mobile_client.views.profile_view import build_profile_view
from mobile_client.views.tickets_view import build_tickets_view
from mobile_client.views.auth_view import build_login_view, build_register_view

__all__ = ["build_events_view", "build_tickets_view", "build_profile_view", "build_login_view", "build_register_view"]
