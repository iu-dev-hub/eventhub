"""
AURA Koltuk Seçim Ekranı Görünümü
Tiyatro & Konser Salonu (Parter/Balkon) İnteraktif Krokisi
"""
import flet as ft
from typing import List
from src.core.theme import AppColors, AppRadius
from src.core.constants import EARLY_BIRD_DISCOUNT, STUDENT_DISCOUNT
from src.services.api_service import api_service
from src.services.auth_service import auth_service
from src.models.event import Event
from src.models.seat import Seat
from src.components.seat_matrix import SeatMatrix

class SeatSelectionView(ft.Container):
    def __init__(self, event: Event, on_back_click, on_proceed_checkout):
        self.event = event
        self.on_back_click = on_back_click
        self.on_proceed_checkout = on_proceed_checkout
        self.selected_seats: List[Seat] = []
        
        seats = api_service.get_seats(event.id)
        self.matrix = SeatMatrix(seats, self._on_seats_changed)

        self.total_price_text = ft.Text("0.00 ₺", size=17, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY_LIGHT)
        self.checkout_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("Biletleri Onayla", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Icon(ft.Icons.ARROW_FORWARD, size=15, color=ft.Colors.WHITE)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=5
            ),
            bgcolor=AppColors.PRIMARY,
            padding=ft.Padding(18, 11, 18, 11),
            border_radius=AppRadius.FULL,
            ink=True,
            opacity=0.4,
            on_click=self._handle_checkout
        )

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
                                ft.Column(
                                    controls=[
                                        ft.Text(event.title, size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, max_lines=1),
                                        ft.Text(f"{event.venue_name} • Salon Planı", size=10, color=AppColors.TEXT_MUTED)
                                    ],
                                    spacing=2
                                ),
                                ft.Container(width=34)
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        margin=ft.Margin(16, 6, 16, 6)
                    ),
                    # Koltuk Matrisi Bileşeni
                    ft.Container(
                        content=self.matrix,
                        margin=ft.Margin(16, 0, 16, 12)
                    ),
                    # Alt Sabit Özet Barı
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text("Toplam Tutar", size=10, color=AppColors.TEXT_MUTED),
                                        self.total_price_text
                                    ],
                                    spacing=2
                                ),
                                self.checkout_btn
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=ft.Padding(18, 12, 18, 12),
                        bgcolor="#111625",
                        border_radius=AppRadius.LARGE,
                        border=ft.Border.all(1, "#232D42"),
                        margin=ft.Margin(16, 0, 16, 80)
                    )
                ],
                spacing=6,
                scroll=ft.ScrollMode.ADAPTIVE
            ),
            expand=True
        )

    def _on_seats_changed(self, selected_seats: List[Seat]):
        self.selected_seats = selected_seats
        
        is_student = auth_service.current_user.is_student
        total = 0.0
        
        for s in selected_seats:
            price = s.price
            if self.event.is_early_bird:
                price *= (1.0 - EARLY_BIRD_DISCOUNT)
            if is_student:
                price *= (1.0 - STUDENT_DISCOUNT)
            total += price
            
        self.total_price_text.value = f"{round(total, 2)} ₺"
        self.checkout_btn.opacity = 1.0 if len(selected_seats) > 0 else 0.4
        try:
            self.update()
        except Exception:
            pass

    def _handle_checkout(self, e):
        if not self.selected_seats:
            return
        self.on_proceed_checkout(self.event, self.selected_seats)
