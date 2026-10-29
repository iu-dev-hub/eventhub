"""
AURA Ödeme ve Rezervasyon Ekranı
BR-3.5: 15 dakikalık rezervasyon süresi sayacı
BR-4.3: Kart simülasyonu (0000 ile biten kartlarda yetersiz bakiye testi)
BR-4.6: Ücretsiz etkinliklerde ödeme adımı atlanır
"""
import flet as ft
from typing import List
from src.core.theme import AppColors, AppRadius
from src.core.constants import EARLY_BIRD_DISCOUNT, STUDENT_DISCOUNT
from src.services.api_service import api_service
from src.services.auth_service import auth_service
from src.models.event import Event
from src.models.seat import Seat

class CheckoutView(ft.Container):
    def __init__(self, event: Event, selected_seats: List[Seat], on_back_click, on_order_success):
        self.event = event
        self.selected_seats = selected_seats
        self.on_back_click = on_back_click
        self.on_order_success = on_order_success

        is_student = auth_service.current_user.is_student
        self.total = 0.0
        for s in selected_seats:
            p = s.price
            if event.is_early_bird:
                p *= (1.0 - EARLY_BIRD_DISCOUNT)
            if is_student:
                p *= (1.0 - STUDENT_DISCOUNT)
            self.total += p
        self.total = round(self.total, 2)

        # Girdi Alanları
        self.card_name_field = ft.TextField(
            label="Kart Üzerindeki İsim",
            value=auth_service.current_user.name,
            border_radius=AppRadius.NORMAL,
            bgcolor="#0E1320",
            border_color="#222B3F",
            color=AppColors.TEXT_PRIMARY,
            text_size=12
        )
        
        self.card_num_field = ft.TextField(
            label="Kart Numarası (16 Haneli)",
            value="4543 1234 5678 9012",
            helper_text="BR-4.3 Testi: 0000 ile biten kart 'Bakiye Yetersiz' yanıtı verir",
            helper_style=ft.TextStyle(color=AppColors.SECONDARY, size=10),
            border_radius=AppRadius.NORMAL,
            bgcolor="#0E1320",
            border_color="#222B3F",
            color=AppColors.TEXT_PRIMARY,
            text_size=12,
            max_length=19
        )

        self.exp_field = ft.TextField(
            label="Son Kullanma (AA/YY)",
            value="12/28",
            border_radius=AppRadius.NORMAL,
            bgcolor="#0E1320",
            border_color="#222B3F",
            color=AppColors.TEXT_PRIMARY,
            text_size=12,
            expand=True
        )

        self.cvv_field = ft.TextField(
            label="CVV",
            value="345",
            password=True,
            can_reveal_password=True,
            border_radius=AppRadius.NORMAL,
            bgcolor="#0E1320",
            border_color="#222B3F",
            color=AppColors.TEXT_PRIMARY,
            text_size=12,
            max_length=3,
            expand=True
        )

        self.status_text = ft.Text("", size=11, weight=ft.FontWeight.BOLD)

        super().__init__(
            content=ft.Column(
                controls=[
                    # Üst Bar
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Icon(ft.Icons.ARROW_BACK, color=ft.Colors.WHITE, size=18),
                                    bgcolor="#161E2E",
                                    padding=8,
                                    border_radius=AppRadius.FULL,
                                    ink=True,
                                    on_click=lambda e: self.on_back_click()
                                ),
                                ft.Text("Rezervasyonu Onayla", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                ft.Container(width=34)
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        margin=ft.Margin(16, 6, 16, 6)
                    ),
                    # BR-3.5: Canlı Rezervasyon Sayacı
                    self._build_timer_badge(),
                    # Bilet Özeti Kartı
                    self._build_summary_card(),
                    # Ödeme Formu
                    self._build_payment_form(),
                    # Hata / Durum Bildirimi
                    ft.Container(content=self.status_text, margin=ft.Margin(16, 0, 16, 0)),
                    # Onay Butonu
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.LOCK, size=15, color=ft.Colors.WHITE),
                                ft.Text(
                                    f"Ödemeyi Tamamla ({self.total} ₺)" if event.base_price > 0 else "Ücretsiz Davetiyeyi Al",
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=6
                        ),
                        bgcolor=AppColors.PRIMARY if event.base_price > 0 else AppColors.SUCCESS,
                        padding=ft.Padding(0, 14, 0, 14),
                        border_radius=AppRadius.FULL,
                        ink=True,
                        on_click=self._handle_payment,
                        margin=ft.Margin(16, 10, 16, 80)
                    )
                ],
                spacing=6,
                scroll=ft.ScrollMode.ADAPTIVE
            ),
            expand=True
        )

    def _build_timer_badge(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.TIMER_OUTLINED, size=15, color=AppColors.SECONDARY),
                    ft.Text("Koltuk Ayrıldı: 14:59 (BR-3.5)", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Yeriniz güvence altında", size=10, color=AppColors.TEXT_MUTED)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6
            ),
            padding=ft.Padding(12, 6, 12, 6),
            bgcolor="#10222E",
            border_radius=AppRadius.FULL,
            border=ft.Border.all(1, "#06B6D444"),
            margin=ft.Margin(16, 0, 16, 4)
        )

    def _build_summary_card(self):
        seat_chips = [
            ft.Container(
                content=ft.Text(s.label, size=10, color=ft.Colors.WHITE),
                bgcolor="#1E273A",
                padding=ft.Padding(10, 4, 10, 4),
                border_radius=AppRadius.FULL
            )
            for s in self.selected_seats
        ]

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(self.event.title, size=14, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                    ft.Text(f"🏛️ {self.event.venue_name} • {self.event.date_str}", size=11, color=AppColors.TEXT_MUTED),
                    ft.Divider(color="#202A40", height=1),
                    ft.Text("Seçilen Salon Koltukları:", size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED),
                    ft.Row(controls=seat_chips, wrap=True, spacing=6),
                    ft.Divider(color="#202A40", height=1),
                    ft.Row(
                        controls=[
                            ft.Text("Toplam Koltuk:", size=11, color=AppColors.TEXT_MUTED),
                            ft.Text(f"{len(self.selected_seats)} Adet", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("Toplam Tutar:", size=13, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                            ft.Text(f"{self.total} ₺", size=15, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY_LIGHT)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    )
                ],
                spacing=6
            ),
            padding=14,
            bgcolor=AppColors.BG_CARD,
            border_radius=AppRadius.CARD,
            border=ft.Border.all(1, "#202A40"),
            margin=ft.Margin(16, 0, 16, 4)
        )

    def _build_payment_form(self):
        if self.event.base_price == 0:
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=AppColors.SUCCESS, size=18),
                        ft.Text("Ücretsiz Kültür Etkinliği: Ödeme adımı yoktur (BR-4.6).", size=11, color=AppColors.SUCCESS)
                    ],
                    spacing=8
                ),
                padding=12,
                bgcolor="#0F241C",
                border_radius=AppRadius.NORMAL,
                margin=ft.Margin(16, 0, 16, 4)
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CREDIT_CARD, size=15, color=AppColors.PRIMARY_LIGHT),
                            ft.Text("Güvenli Ödeme Bilgileri", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ],
                        spacing=6
                    ),
                    self.card_name_field,
                    self.card_num_field,
                    ft.Row(controls=[self.exp_field, self.cvv_field], spacing=8)
                ],
                spacing=8
            ),
            padding=14,
            bgcolor=AppColors.BG_CARD,
            border_radius=AppRadius.CARD,
            border=ft.Border.all(1, "#202A40"),
            margin=ft.Margin(16, 0, 16, 4)
        )

    def _handle_payment(self, e):
        card_num = self.card_num_field.value or ""
        
        result = api_service.create_order(
            event=self.event,
            selected_seats=self.selected_seats,
            user_name=self.card_name_field.value or auth_service.current_user.name,
            user_email=auth_service.current_user.email,
            card_number=card_num,
            is_student=auth_service.current_user.is_student
        )

        if not result["success"]:
            self.status_text.value = f"❌ {result['message']}"
            self.status_text.color = AppColors.DANGER
            try:
                self.status_text.update()
            except Exception:
                pass
        else:
            self.status_text.value = f"✅ {result['message']}"
            self.status_text.color = AppColors.SUCCESS
            try:
                self.status_text.update()
            except Exception:
                pass
            self.on_order_success(result["tickets"])
