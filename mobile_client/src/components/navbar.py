"""
AURA Navigasyon Bileşenleri (Kullanıcı Arayüzü)
Kullanıcı arayüzünde hiçbir API butonu veya geliştirici rozeti yer almaz;
tüm API kontrolleri yalnızca ayrı olan Yönetici Paneli'nde bulunur.
"""
import flet as ft
from src.core.theme import AppColors, AppRadius

class TopBar(ft.Container):
    def __init__(self, on_profile_click=None):
        self.on_profile_click = on_profile_click

        super().__init__(
            content=ft.Row(
                controls=[
                    # Sol: Logo & Marka (AURA)
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(ft.Icons.AUTO_STORIES, color=ft.Colors.WHITE, size=18),
                                bgcolor=AppColors.PRIMARY,
                                padding=7,
                                border_radius=AppRadius.NORMAL
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("AURA", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                    ft.Text("Kültür & Sahne Sanatları", size=10, color=AppColors.TEXT_MUTED)
                                ],
                                spacing=0
                            )
                        ],
                        spacing=8
                    ),
                    # Sağ: Bildirim / Profil İkonu (Kullanıcıya özel sakin görünüm)
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.NOTIFICATIONS_NONE, size=18, color=AppColors.TEXT_SECONDARY),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        bgcolor="#151C2C",
                        padding=8,
                        border_radius=AppRadius.FULL,
                        border=ft.Border.all(1, "#28354D"),
                        ink=True,
                        on_click=lambda e: self.on_profile_click() if self.on_profile_click else None
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=ft.Padding(18, 10, 18, 10),
            bgcolor=AppColors.BG_SURFACE,
            border_radius=AppRadius.NORMAL,
            margin=ft.Margin(12, 6, 12, 6)
        )

class FloatingBottomBar(ft.Container):
    """Kullanıcı için 3 Temel Sekme: Keşfet, Biletlerim, Profil"""
    def __init__(self, current_tab: int, on_tab_change):
        self.current_tab = current_tab
        self.on_tab_change = on_tab_change
        
        self.items = [
            {"index": 0, "icon": ft.Icons.COMPASS_CALIBRATION_OUTLINED, "label": "Keşfet"},
            {"index": 1, "icon": ft.Icons.BOOKMARK_BORDER, "label": "Biletlerim"},
            {"index": 2, "icon": ft.Icons.PERSON_OUTLINE, "label": "Profil"},
        ]
        
        super().__init__(
            content=ft.Row(
                controls=[self._build_item(item) for item in self.items],
                alignment=ft.MainAxisAlignment.SPACE_AROUND
            ),
            padding=ft.Padding(14, 6, 14, 6),
            bgcolor="#131929",
            border_radius=AppRadius.FULL,
            border=ft.Border.all(1, "#26324B"),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=18,
                color="#00000099",
                offset=ft.Offset(0, 4)
            ),
            margin=ft.Margin(20, 0, 20, 14),
            height=60
        )

    def _build_item(self, item):
        is_active = (self.current_tab == item["index"])
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        item["icon"],
                        size=18,
                        color=AppColors.PRIMARY_LIGHT if is_active else AppColors.TEXT_MUTED
                    ),
                    ft.Text(
                        item["label"],
                        size=12,
                        weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                        color=ft.Colors.WHITE if is_active else AppColors.TEXT_MUTED
                    )
                ],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor="#212A42" if is_active else ft.Colors.TRANSPARENT,
            padding=ft.Padding(14, 8, 14, 8),
            border_radius=AppRadius.FULL,
            ink=True,
            on_click=lambda e, idx=item["index"]: self._handle_click(idx),
            animate=200
        )

    def _handle_click(self, idx):
        self.current_tab = idx
        if self.on_tab_change:
            self.on_tab_change(idx)
