"""
AURA Etkinlik Kartı Bileşeni (Özgün, Gözü Yormayan Sanat Kartı)
Passo'dan tamamen farklı; zarif, ferah, akıcı ve dinlendirici görsel dil.
"""
import flet as ft
from src.core.theme import AppColors, AppRadius
from src.models.event import Event

class EventCard(ft.Container):
    def __init__(self, event: Event, on_card_click):
        self.event = event
        self.on_card_click = on_card_click

        # Fiyat formatı
        if event.base_price == 0:
            price_text = "ÜCRETSİZ DAVETİYE"
            price_color = AppColors.SUCCESS
        else:
            price_text = f"{int(event.base_price)} ₺'den başlayan"
            price_color = AppColors.PRIMARY_LIGHT

        # Zarif rozetler
        badges = []
        if event.is_early_bird:
            badges.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.AUTO_AWESOME, size=11, color=AppColors.ACCENT_GOLD),
                            ft.Text("%20 Erken Rezervasyon", size=10, weight=ft.FontWeight.BOLD, color=AppColors.ACCENT_GOLD)
                        ],
                        spacing=3
                    ),
                    bgcolor="#242114",
                    padding=ft.Padding(8, 3, 8, 3),
                    border_radius=AppRadius.FULL,
                    border=ft.Border.all(1, "#FCD34D55")
                )
            )

        if event.remaining < 400:
            badges.append(
                ft.Container(
                    content=ft.Text(f"Son {event.remaining} Koltuk", size=10, weight=ft.FontWeight.W_600, color="#FCA5A5"),
                    bgcolor="#2B151A",
                    padding=ft.Padding(8, 3, 8, 3),
                    border_radius=AppRadius.FULL,
                    border=ft.Border.all(1, "#EF444455")
                )
            )

        super().__init__(
            content=ft.Column(
                controls=[
                    # Üst Görsel ve Karartma Katmanı
                    ft.Stack(
                        controls=[
                            ft.Image(
                                src=event.image_url,
                                width=340,
                                height=165,
                                fit=ft.BoxFit.COVER,
                                border_radius=AppRadius.LARGE
                            ),
                            # Sanatsal degrade gölgelendirme (Gözü yormaz)
                            ft.Container(
                                width=340,
                                height=165,
                                border_radius=AppRadius.LARGE,
                                gradient=ft.LinearGradient(
                                    begin=ft.Alignment(0, -1),
                                    end=ft.Alignment(0, 1),
                                    colors=["#00000011", "#0B0F1BEE"]
                                )
                            ),
                            # Sol Üst: Kategori Kapsülü
                            ft.Container(
                                content=ft.Text(
                                    event.category.upper(),
                                    size=9,
                                    weight=ft.FontWeight.BOLD,
                                    color=AppColors.TEXT_PRIMARY
                                ),
                                bgcolor="#0F172ACC",
                                padding=ft.Padding(10, 4, 10, 4),
                                border_radius=AppRadius.FULL,
                                border=ft.Border.all(1, "#334155"),
                                top=12,
                                left=12
                            ),
                            # Sağ Üst: Takvim Rozeti
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text(event.date_str.split()[0], size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                        ft.Text(event.date_str.split()[1][:3].upper(), size=9, weight=ft.FontWeight.W_600, color=AppColors.PRIMARY_LIGHT)
                                    ],
                                    spacing=0,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                ),
                                bgcolor="#171E31DD",
                                padding=ft.Padding(8, 6, 8, 6),
                                border_radius=AppRadius.NORMAL,
                                border=ft.Border.all(1, "#28344E"),
                                top=12,
                                right=12
                            ),
                            # Sol Alt Rozetler
                            ft.Container(
                                content=ft.Row(controls=badges, spacing=6),
                                bottom=10,
                                left=12
                            )
                        ],
                        width=340,
                        height=165
                    ),
                    # Alt Bilgi ve Eylem Alanı
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                # Başlık
                                ft.Text(
                                    event.title,
                                    size=15,
                                    weight=ft.FontWeight.BOLD,
                                    color=AppColors.TEXT_PRIMARY,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS
                                ),
                                # Mekan
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.THEATER_COMEDY, size=13, color=AppColors.SECONDARY),
                                        ft.Text(f"{event.venue_name}", size=11, color=AppColors.TEXT_SECONDARY, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
                                    ],
                                    spacing=4
                                ),
                                # Fiyat ve İncele Butonu
                                ft.Row(
                                    controls=[
                                        ft.Text(price_text, size=12, weight=ft.FontWeight.BOLD, color=price_color),
                                        ft.Container(
                                            content=ft.Row(
                                                controls=[
                                                    ft.Text("Koltuk Seç", size=11, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                                                    ft.Icon(ft.Icons.ARROW_FORWARD, size=11, color=ft.Colors.WHITE)
                                                ],
                                                spacing=4
                                            ),
                                            bgcolor=AppColors.PRIMARY,
                                            padding=ft.Padding(12, 6, 12, 6),
                                            border_radius=AppRadius.FULL
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                )
                            ],
                            spacing=6
                        ),
                        padding=ft.Padding(14, 10, 14, 14)
                    )
                ],
                spacing=0
            ),
            width=340,
            bgcolor=AppColors.BG_CARD,
            border_radius=AppRadius.CARD,
            border=ft.Border.all(1, "#232D42"),
            ink=True,
            on_click=lambda e: self.on_card_click(self.event),
            animate=200,
            margin=ft.Margin(0, 0, 0, 14)
        )
