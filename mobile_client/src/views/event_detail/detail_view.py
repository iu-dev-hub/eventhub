"""
AURA Etkinlik ve Sahne Detay Ekranı
Sanat eseri posteri, akustik salon bilgisi, kural dökümü ve koltuk seçimi
"""
import flet as ft
from src.core.theme import AppColors, AppRadius
from src.core.constants import EARLY_BIRD_DISCOUNT, STUDENT_DISCOUNT
from src.services.auth_service import auth_service
from src.models.event import Event

class EventDetailView(ft.Container):
    def __init__(self, event: Event, on_back_click, on_proceed_seats):
        self.event = event
        self.on_back_click = on_back_click
        self.on_proceed_seats = on_proceed_seats

        is_student = auth_service.current_user.is_student
        base = event.base_price
        discounted = base
        
        discounts_applied = []
        if event.is_early_bird and base > 0:
            discounted *= (1.0 - EARLY_BIRD_DISCOUNT)
            discounts_applied.append("%20 Erken Rezervasyon İndirimi (BR-4.1)")
        if is_student and base > 0:
            discounted *= (1.0 - STUDENT_DISCOUNT)
            discounts_applied.append("%25 Genç / Öğrenci Kültür İndirimi (BR-4.2)")

        super().__init__(
            content=ft.Column(
                controls=[
                    # Üst Poster Katmanı ve Geri Butonu
                    ft.Stack(
                        controls=[
                            ft.Image(
                                src=event.image_url,
                                width=360,
                                height=220,
                                fit=ft.BoxFit.COVER,
                                border_radius=AppRadius.LARGE
                            ),
                            ft.Container(
                                width=360,
                                height=220,
                                border_radius=AppRadius.LARGE,
                                gradient=ft.LinearGradient(
                                    begin=ft.Alignment(0, -1),
                                    end=ft.Alignment(0, 1),
                                    colors=["#00000033", "#090C15F5"]
                                )
                            ),
                            # Geri Butonu
                            ft.Container(
                                content=ft.Icon(ft.Icons.ARROW_BACK, color=ft.Colors.WHITE, size=18),
                                bgcolor="#00000077",
                                padding=8,
                                border_radius=AppRadius.FULL,
                                ink=True,
                                on_click=lambda e: self.on_back_click(),
                                top=12,
                                left=12
                            ),
                            # Kategori Rozeti
                            ft.Container(
                                content=ft.Text(event.category.upper(), size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                bgcolor=AppColors.PRIMARY,
                                padding=ft.Padding(12, 4, 12, 4),
                                border_radius=AppRadius.FULL,
                                top=12,
                                right=12
                            ),
                            # Başlık ve Mekan
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text(event.title, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                        ft.Row(
                                            controls=[
                                                ft.Icon(ft.Icons.THEATER_COMEDY, size=14, color=AppColors.SECONDARY),
                                                ft.Text(f"{event.venue_name}", size=12, color=AppColors.TEXT_SECONDARY)
                                            ],
                                            spacing=4
                                        )
                                    ],
                                    spacing=4
                                ),
                                bottom=14,
                                left=16,
                                right=16
                            )
                        ],
                        width=360,
                        height=220
                    ),
                    # Tarih & Kontenjan İstatistik Kutucukları (Dingin Slate)
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                self._build_stat_box(ft.Icons.CALENDAR_MONTH, "Tarih", event.date_str),
                                self._build_stat_box(ft.Icons.ACCESS_TIME, "Başlangıç", event.time_str),
                                self._build_stat_box(ft.Icons.EVENT_SEAT, "Kalan", f"{event.remaining} Koltuk"),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        margin=ft.Margin(16, 6, 16, 6)
                    ),
                    # Fiyat ve İndirim Özeti Kartı
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text("Bilet Bedeli", size=13, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                                        ft.Text(
                                            f"Net: {round(discounted, 2)} ₺" if base > 0 else "ÜCRETSİZ DAVETİYE",
                                            size=15,
                                            weight=ft.FontWeight.BOLD,
                                            color=AppColors.PRIMARY_LIGHT if base > 0 else AppColors.SUCCESS
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                ),
                                *(
                                    [ft.Text(f"• {d}", size=11, color=AppColors.SECONDARY) for d in discounts_applied]
                                    if discounts_applied else [ft.Text("Standart tarife uygulanmaktadır.", size=11, color=AppColors.TEXT_MUTED)]
                                )
                            ],
                            spacing=5
                        ),
                        padding=14,
                        bgcolor="#121828",
                        border_radius=AppRadius.NORMAL,
                        border=ft.Border.all(1, "#202A40"),
                        margin=ft.Margin(16, 0, 16, 6)
                    ),
                    # Eser / Etkinlik Hakkında
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Eser & Performans Hakkında", size=13, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                                ft.Text(event.description, size=11, color=AppColors.TEXT_SECONDARY, line_height=1.4)
                            ],
                            spacing=4
                        ),
                        padding=14,
                        bgcolor=AppColors.BG_CARD,
                        border_radius=AppRadius.NORMAL,
                        border=ft.Border.all(1, "#1E273A"),
                        margin=ft.Margin(16, 0, 16, 6)
                    ),
                    # Bilet Satış ve Salon Kuralları (BR-3)
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.VERIFIED, size=15, color=AppColors.PRIMARY_LIGHT),
                                        ft.Text("Salon & Rezervasyon Kuralları", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                                    ],
                                    spacing=6
                                ),
                                ft.Text("• BR-3.1: Bir kullanıcı bu etkinlik için en fazla 4 bilet alabilir.", size=10, color=AppColors.TEXT_MUTED),
                                ft.Text("• BR-3.5: Koltuk ayrıldıktan sonra tamamlamak için 15 dakika süreniz vardır.", size=10, color=AppColors.TEXT_MUTED),
                                ft.Text("• BR-3.6: Dinamik turnike QR kodunuz girişte temassız olarak taranır.", size=10, color=AppColors.TEXT_MUTED),
                            ],
                            spacing=4
                        ),
                        padding=14,
                        bgcolor="#0D121E",
                        border_radius=AppRadius.NORMAL,
                        border=ft.Border.all(1, "#1A2234"),
                        margin=ft.Margin(16, 0, 16, 12)
                    ),
                    # Koltuk Seçimine Devam Et Butonu
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text("Salon Krokisi & Koltuk Seç", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                ft.Icon(ft.Icons.ARROW_FORWARD, size=16, color=ft.Colors.WHITE)
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8
                        ),
                        bgcolor=AppColors.PRIMARY,
                        padding=ft.Padding(0, 14, 0, 14),
                        border_radius=AppRadius.FULL,
                        ink=True,
                        on_click=lambda e: self.on_proceed_seats(self.event),
                        margin=ft.Margin(16, 0, 16, 80)
                    )
                ],
                spacing=6,
                scroll=ft.ScrollMode.ADAPTIVE
            ),
            expand=True
        )

    def _build_stat_box(self, icon, label, val):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(icon, size=16, color=AppColors.PRIMARY_LIGHT),
                    ft.Text(label, size=9, color=AppColors.TEXT_MUTED),
                    ft.Text(val, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2
            ),
            padding=ft.Padding(10, 8, 10, 8),
            bgcolor=AppColors.BG_CARD,
            border_radius=AppRadius.NORMAL,
            border=ft.Border.all(1, "#202A40"),
            width=100
        )
