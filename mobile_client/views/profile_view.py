"""Profile page for EventHub mobile application."""

from typing import Callable, Optional

import flet as ft

from mobile_client.core.constants import USER_ROLES
from mobile_client.core.routes import ROUTE_PROFILE
from mobile_client.core.theme import DEFAULT_THEME, USER_ROLE_COLORS
from mobile_client.models.user import User
from mobile_client.views.base import build_page_view


def build_profile_view(
    on_nav_change: Optional[Callable[[int], None]] = None,
    user: Optional[User] = None,
    on_logout: Optional[Callable[[], None]] = None,
) -> ft.View:
    """Profil sayfası."""
    base_view = build_page_view(ROUTE_PROFILE, "Profil", on_nav_change)

    if user is None:
        return base_view

    role_label = USER_ROLES.get(user.role, user.role.capitalize())
    role_color = USER_ROLE_COLORS.get(user.role, DEFAULT_THEME.colors.text_secondary)

    badges = [
        ft.Container(
            bgcolor=DEFAULT_THEME.colors.surface,
            border=ft.Border.all(1, role_color),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            content=ft.Text(role_label, size=12, weight=ft.FontWeight.BOLD, color=role_color),
        )
    ]

    if user.is_student:
        student_text = (
            f"Öğrenci ({user.student_number})" if user.student_number else "Öğrenci"
        )
        badges.append(
            ft.Container(
                bgcolor=DEFAULT_THEME.colors.surface,
                border=ft.Border.all(1, DEFAULT_THEME.colors.success),
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                content=ft.Text(
                    student_text,
                    size=12,
                    weight=ft.FontWeight.W_500,
                    color=DEFAULT_THEME.colors.success,
                ),
            )
        )

    if user.role == "organizer" and not user.approved:
        badges.append(
            ft.Container(
                bgcolor="#FFFBEB",
                border=ft.Border.all(1, DEFAULT_THEME.colors.warning),
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                content=ft.Text(
                    "Yönetici Onayı Bekliyor (BR-1.5)",
                    size=12,
                    weight=ft.FontWeight.W_500,
                    color=DEFAULT_THEME.colors.warning,
                ),
            )
        )

    profile_card = ft.Container(
        padding=20,
        border_radius=8,
        bgcolor=DEFAULT_THEME.colors.background,
        border=ft.Border.all(1, DEFAULT_THEME.colors.border),
        content=ft.Column(
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.CircleAvatar(
                    radius=34,
                    bgcolor=DEFAULT_THEME.colors.primary,
                    content=ft.Text(
                        f"{user.first_name[:1]}{user.last_name[:1]}".upper() or "EH",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=DEFAULT_THEME.colors.background,
                    ),
                ),
                ft.Text(
                    f"{user.first_name} {user.last_name}".strip(),
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=DEFAULT_THEME.colors.text_primary,
                ),
                ft.Text(user.email, size=14, color=DEFAULT_THEME.colors.text_secondary),
                ft.Row(
                    wrap=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                    controls=badges,
                ),
                ft.Divider(),
                ft.FilledButton(
                    "Çıkış Yap",
                    icon=ft.Icons.LOGOUT,
                    width=240,
                    on_click=lambda _: on_logout() if on_logout else None,
                    style=ft.ButtonStyle(
                        color=DEFAULT_THEME.colors.background,
                        bgcolor=DEFAULT_THEME.colors.error,
                    ),
                ),
            ],
        ),
    )

    base_view.controls = [
        ft.Container(
            padding=16,
            content=profile_card,
        )
    ]
    return base_view
