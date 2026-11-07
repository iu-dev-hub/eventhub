"""Ticket card component for displaying user tickets in wallet/profile (TG-161)."""

from typing import Callable, Optional

import flet as ft

from mobile_client.core.constants import TICKET_STATUSES
from mobile_client.core.theme import DEFAULT_THEME, TICKET_STATUS_COLORS
from mobile_client.models.ticket import Ticket


class TicketCard(ft.Container):
    """Reusable card component for ticket listing in wallet and profile views."""

    def __init__(
        self,
        ticket: Ticket,
        event_title: Optional[str] = None,
        on_click: Optional[Callable[[Ticket], None]] = None,
        theme=DEFAULT_THEME,
    ):
        self.ticket = ticket
        self.on_ticket_click = on_click
        self.app_theme = theme

        status_text = TICKET_STATUSES.get(ticket.status, ticket.status.capitalize())
        status_color = TICKET_STATUS_COLORS.get(ticket.status, theme.colors.text_secondary)

        is_used = ticket.status == "used"
        display_title = event_title or f"Etkinlik #{ticket.event_id}"
        ticket_code_display = ticket.qr_code or f"TKT-{ticket.id:06d}"

        # BUG-14 fix: Disable click for used tickets
        is_clickable = (on_click is not None) and (not is_used)

        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=6,
                                controls=[
                                    ft.Icon(
                                        ft.Icons.CONFIRMATION_NUMBER_OUTLINED,
                                        size=15,
                                        color=theme.colors.primary,
                                    ),
                                    ft.Text(
                                        ticket_code_display,
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color=theme.colors.text_secondary,
                                    ),
                                ],
                            ),
                            ft.Container(
                                content=ft.Text(
                                    status_text.upper() if is_used else status_text,
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                    color=status_color,
                                ),
                                bgcolor=theme.colors.surface,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                border_radius=4,
                            ),
                        ],
                    ),
                    ft.Text(
                        display_title,
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=theme.colors.text_primary,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                f"Bilet No: #{ticket.id}",
                                size=11,
                                color=theme.colors.text_secondary,
                            ),
                            ft.Icon(
                                ft.Icons.QR_CODE_2,
                                size=20,
                                color=theme.colors.text_secondary
                                if is_used
                                else theme.colors.primary,
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
            opacity=0.75 if is_used else 1.0,
            on_click=self._handle_click if is_clickable else None,
            ink=is_clickable,
        )

    def _handle_click(self, _):
        if self.on_ticket_click and self.ticket.status != "used":
            self.on_ticket_click(self.ticket)
