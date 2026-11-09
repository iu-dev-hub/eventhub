"""Bottom navigation bar component for mobile client navigation (TG-161)."""

from typing import Callable, Optional

import flet as ft

from mobile_client.core.theme import DEFAULT_THEME


class BottomNavBar(ft.NavigationBar):
    """Reusable bottom navigation bar with clean role-compliant tabs."""

    def __init__(
        self,
        selected_index: int = 0,
        on_change: Optional[Callable[[int], None]] = None,
        theme=DEFAULT_THEME,
    ):
        self.nav_callback = on_change
        self.app_theme = theme

        super().__init__(
            selected_index=selected_index,
            bgcolor=theme.colors.background,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.EXPLORE_OUTLINED,
                    selected_icon=ft.Icons.EXPLORE,
                    label="Etkinlikler",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.CONFIRMATION_NUMBER_OUTLINED,
                    selected_icon=ft.Icons.CONFIRMATION_NUMBER,
                    label="Biletlerim",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.PERSON_OUTLINED,
                    selected_icon=ft.Icons.PERSON,
                    label="Profil",
                ),
            ],
            on_change=self._handle_change,
        )

    def _handle_change(self, e: ft.ControlEvent):
        self.selected_index = e.control.selected_index
        if self.nav_callback:
            self.nav_callback(e.control.selected_index)
