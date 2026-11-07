"""Event card component for displaying event information in lists (TG-161)."""

from typing import Callable, Optional

import flet as ft

from mobile_client.core.constants import EVENT_STATUSES
from mobile_client.core.theme import DEFAULT_THEME, EVENT_STATUS_COLORS
from mobile_client.models.event import Event


def _format_event_datetime(dt_str: str) -> str:
    """Format ISO 8601 or string datetime safely without IndexError (BUG-15 fix)."""
    if not dt_str:
        return ""
    clean = dt_str.replace("Z", "").replace("T", " ")
    parts = clean.split()
    if len(parts) >= 2:
        return f"{parts[0]} - {parts[1][:5]}"
    return parts[0]


class EventCard(ft.Container):
    """Reusable card component for events in discover and search lists."""

    def __init__(
        self,
        event: Event,
        on_click: Optional[Callable[[Event], None]] = None,
        theme=DEFAULT_THEME,
    ):
        self.event = event
        self.on_card_click = on_click
        self.app_theme = theme

        status_text = EVENT_STATUSES.get(event.status, event.status.capitalize())
        status_color = EVENT_STATUS_COLORS.get(event.status, theme.colors.text_secondary)

        price_text = "Ücretsiz" if event.price == 0 else f"{int(event.price)} TL"
        formatted_date = _format_event_datetime(event.start_time)

        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    event.category,
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                    color=theme.colors.primary,
                                ),
                                bgcolor=theme.colors.surface,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                border_radius=4,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    status_text,
                                    size=11,
                                    weight=ft.FontWeight.W_500,
                                    color=status_color,
                                ),
                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                            ),
                        ],
                    ),
                    ft.Text(
                        event.title,
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=theme.colors.text_primary,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=4,
                                controls=[
                                    ft.Icon(
                                        ft.Icons.CALENDAR_TODAY,
                                        size=13,
                                        color=theme.colors.text_secondary,
                                    ),
                                    ft.Text(
                                        formatted_date,
                                        size=12,
                                        color=theme.colors.text_secondary,
                                    ),
                                ],
                            ),
                            ft.Text(
                                price_text,
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=theme.colors.primary,
                            ),
                        ],
                    ),
                ],
                spacing=8,
            ),
            padding=14,
            border_radius=8,
            bgcolor=theme.colors.background,
            border=ft.Border.all(1, theme.colors.border),
            on_click=self._handle_click if on_click else None,
            ink=True if on_click else False,
        )

    def _handle_click(self, _):
        if self.on_card_click:
            self.on_card_click(self.event)
