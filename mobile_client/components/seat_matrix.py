"""Seat matrix component for interactive seat selection in mobile client (TG-161)."""

from typing import Callable, List, Optional, Set

import flet as ft

from mobile_client.core.constants import MAX_TICKETS_PER_EVENT
from mobile_client.core.theme import DEFAULT_THEME
from mobile_client.models.seat import Seat


class SeatMatrix(ft.Container):
    """Grid matrix representing available and occupied seats for an event."""

    def __init__(
        self,
        seats: List[Seat],
        selected_codes: Optional[Set[str]] = None,
        max_selection: int = MAX_TICKETS_PER_EVENT,
        on_selection_change: Optional[Callable[[List[str]], None]] = None,
        theme=DEFAULT_THEME,
    ):
        self.seats = seats
        self.selected_codes: Set[str] = set(selected_codes or [])
        self.max_selection = max_selection
        self.on_selection_change = on_selection_change
        self.app_theme = theme

        super().__init__(
            content=ft.Column(
                controls=[
                    self._build_screen_indicator(),
                    self._build_grid(),
                    self._build_legend(),
                ],
                spacing=16,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=12,
        )

    def _build_screen_indicator(self) -> ft.Control:
        return ft.Column(
            controls=[
                ft.Container(
                    height=4,
                    width=220,
                    bgcolor=self.app_theme.colors.border,
                    border_radius=2,
                ),
                ft.Text(
                    "SAHNE / EKRAN",
                    size=10,
                    weight=ft.FontWeight.BOLD,
                    color=self.app_theme.colors.text_secondary,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        )

    def _build_grid(self) -> ft.Control:
        # Group seats by their row prefix (e.g., 'A', 'B', 'C')
        rows_dict = {}
        for s in self.seats:
            row_key = s.seat_code[0] if s.seat_code else "A"
            if row_key not in rows_dict:
                rows_dict[row_key] = []
            rows_dict[row_key].append(s)

        row_controls = []
        for row_key in sorted(rows_dict.keys()):
            row_seats = sorted(rows_dict[row_key], key=lambda x: x.seat_code)
            seat_buttons = [self._build_seat_button(s) for s in row_seats]
            row_controls.append(
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                row_key,
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=self.app_theme.colors.text_secondary,
                            ),
                            width=20,
                            alignment=ft.alignment.center,
                        ),
                        ft.Row(controls=seat_buttons, spacing=6),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                )
            )

        return ft.Column(controls=row_controls, spacing=8)

    def _build_seat_button(self, seat: Seat) -> ft.Control:
        is_selected = seat.seat_code in self.selected_codes
        is_occupied = seat.status in ("sold", "occupied", "locked")

        if is_selected:
            bg_color = self.app_theme.colors.primary
            border_color = self.app_theme.colors.primary
            text_color = "#FFFFFF"
        elif is_occupied:
            bg_color = self.app_theme.colors.surface
            border_color = self.app_theme.colors.border
            text_color = self.app_theme.colors.text_secondary
        else:
            bg_color = self.app_theme.colors.background
            border_color = self.app_theme.colors.primary
            text_color = self.app_theme.colors.text_primary

        return ft.Container(
            content=ft.Text(
                seat.seat_code,
                size=10,
                weight=ft.FontWeight.BOLD,
                color=text_color,
            ),
            width=34,
            height=34,
            border_radius=6,
            bgcolor=bg_color,
            border=ft.border.all(1, border_color),
            alignment=ft.alignment.center,
            disabled=is_occupied,
            opacity=0.45 if is_occupied else 1.0,
            on_click=lambda _, sc=seat.seat_code: self._toggle_seat(sc),
            ink=not is_occupied,
        )

    def _toggle_seat(self, seat_code: str):
        if seat_code in self.selected_codes:
            self.selected_codes.remove(seat_code)
        else:
            if len(self.selected_codes) >= self.max_selection:
                return  # Maximum limit reached
            self.selected_codes.add(seat_code)

        if self.on_selection_change:
            self.on_selection_change(sorted(list(self.selected_codes)))

    def _build_legend(self) -> ft.Control:
        items = [
            ("Müsait", self.app_theme.colors.background, self.app_theme.colors.primary),
            ("Seçili", self.app_theme.colors.primary, self.app_theme.colors.primary),
            ("Dolu", self.app_theme.colors.surface, self.app_theme.colors.border),
        ]
        legend_controls = []
        for label, bg, border_col in items:
            legend_controls.append(
                ft.Row(
                    controls=[
                        ft.Container(
                            width=14,
                            height=14,
                            border_radius=3,
                            bgcolor=bg,
                            border=ft.border.all(1, border_col),
                        ),
                        ft.Text(
                            label,
                            size=11,
                            color=self.app_theme.colors.text_secondary,
                        ),
                    ],
                    spacing=4,
                )
            )
        return ft.Row(
            controls=legend_controls,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=16,
        )
