"""Shared page skeleton used by all mobile client views (TG-160)."""

from typing import Callable, Optional

import flet as ft

from mobile_client.components.navbar import BottomNavBar
from mobile_client.core.routes import index_for_route
from mobile_client.core.theme import DEFAULT_THEME

PLACEHOLDER_TEXT = "Bu sayfanın içeriği sonraki görevlerde eklenecektir."


def build_page_view(
    route: str,
    title: str,
    on_nav_change: Optional[Callable[[int], None]] = None,
    theme=DEFAULT_THEME,
) -> ft.View:
    """Başlık, boş içerik alanı ve alt gezinme çubuğundan oluşan sayfa iskeleti."""
    return ft.View(
        route=route,
        appbar=ft.AppBar(
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            bgcolor=theme.colors.background,
            automatically_imply_leading=False,
        ),
        controls=[
            ft.Container(
                content=ft.Text(
                    PLACEHOLDER_TEXT,
                    size=14,
                    color=theme.colors.text_secondary,
                ),
                padding=16,
            ),
        ],
        navigation_bar=BottomNavBar(
            selected_index=index_for_route(route),
            on_change=on_nav_change,
            theme=theme,
        ),
        bgcolor=theme.colors.surface,
    )
