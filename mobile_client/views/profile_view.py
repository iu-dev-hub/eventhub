"""Profile page skeleton (TG-160)."""

from typing import Callable, Optional

import flet as ft

from mobile_client.core.routes import ROUTE_PROFILE
from mobile_client.views.base import build_page_view


def build_profile_view(on_nav_change: Optional[Callable[[int], None]] = None) -> ft.View:
    """Profil sayfası (boş iskelet)."""
    return build_page_view(ROUTE_PROFILE, "Profil", on_nav_change)
