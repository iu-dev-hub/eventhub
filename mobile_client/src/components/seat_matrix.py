"""
Koltuk Seçim Matrisi ve Sahne Krokisi Bileşeni (AURA)
Tiyatro, konser ve sahne salonu oturma planı (Maç sahası yok)
Köşeli yapılar kullanılmaz, yumuşak kavisli salon koltukları.
BR-3.1: Bir kullanıcı bir etkinlik için en fazla 4 bilet alabilir.
"""
import flet as ft
from typing import List, Callable
from src.core.theme import AppColors, AppRadius
from src.core.constants import MAX_TICKETS_PER_USER
from src.models.seat import Seat

class SeatMatrix(ft.Container):
    def __init__(self, seats: List[Seat], on_selection_change: Callable[[List[Seat]], None]):
        self.all_seats = seats
        self.on_selection_change = on_selection_change
        self.current_block = "Parter VIP"
        self.selected_seats: List[Seat] = []

        # Tiyatro & Konser Salon Blokları
        self.blocks = ["Parter VIP", "Parter Orta", "Balkon Salon"]
        
        # Koltuk grid konteyneri
        self.matrix_container = ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Seçim durumu ve kota göstergesi
        self.quota_badge = ft.Text(
            f"Seçilen: 0 / {MAX_TICKETS_PER_USER} Koltuk",
            size=12,
            weight=ft.FontWeight.BOLD,
            color=AppColors.SECONDARY
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    # Sahne / Perde Göstergesi (Zarif kavisli tiyatro sahnesi)
                    self._build_stage_header(),
                    # Blok Seçim Çipleri
                    self._build_block_selector(),
                    # Renk Açıklamaları (Legend)
                    self._build_legend(),
                    # Koltuk Matrisi
                    ft.Container(
                        content=self.matrix_container,
                        padding=ft.Padding(12, 16, 12, 16),
                        bgcolor="#0C101A",
                        border_radius=AppRadius.LARGE,
                        border=ft.Border.all(1, "#1E273A")
                    ),
                    # Alt Bilgi Barı
                    ft.Row(
                        controls=[
                            self.quota_badge,
                            ft.Text("Maks 4 Bilet Kotası (BR-3.1)", size=11, color=AppColors.TEXT_MUTED)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    )
                ],
                spacing=12
            ),
            padding=16,
            bgcolor=AppColors.BG_CARD,
            border_radius=AppRadius.CARD
        )
        self._render_matrix()

    def _build_stage_header(self):
        """Zarif kavisli tiyatro sahne ve perde göstergesi"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CURTAINS, size=16, color=AppColors.PRIMARY_LIGHT),
                    ft.Text("🎭 SAHNE & PERDE", size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY_LIGHT)
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor="#1A2035",
            padding=ft.Padding(16, 6, 16, 6),
            border_radius=AppRadius.FULL,
            border=ft.Border.all(1, "#6366F144")
        )

    def _build_block_selector(self):
        chips = []
        for blk in self.blocks:
            is_active = (blk == self.current_block)
            chips.append(
                ft.Container(
                    content=ft.Text(
                        blk,
                        size=11,
                        weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                        color=ft.Colors.WHITE if is_active else AppColors.TEXT_MUTED
                    ),
                    bgcolor=AppColors.PRIMARY if is_active else "#161E2E",
                    padding=ft.Padding(14, 7, 14, 7),
                    border_radius=AppRadius.FULL,
                    ink=True,
                    on_click=lambda e, b=blk: self._change_block(b),
                    animate=200
                )
            )
        return ft.Row(controls=chips, alignment=ft.MainAxisAlignment.CENTER, spacing=6)

    def _build_legend(self):
        def legend_item(color, label):
            return ft.Row(
                controls=[
                    ft.Container(width=10, height=10, bgcolor=color, border_radius=3),
                    ft.Text(label, size=10, color=AppColors.TEXT_MUTED)
                ],
                spacing=4
            )

        return ft.Row(
            controls=[
                legend_item("#1E293B", "Boş"),
                legend_item(AppColors.PRIMARY, "Seçili"),
                legend_item("#0F172A", "Dolu"),
                legend_item(AppColors.ACCENT_GOLD, "VIP")
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12
        )

    def _render_matrix(self):
        self.matrix_container.controls.clear()
        block_seats = [s for s in self.all_seats if s.block == self.current_block]
        
        # 3 sıra
        for r in range(1, 4):
            row_seats = [s for s in block_seats if s.row == r]
            seat_buttons = []
            
            for s in row_seats:
                is_selected = s in self.selected_seats
                
                if is_selected:
                    bg = AppColors.PRIMARY
                    txt_color = ft.Colors.WHITE
                elif s.status == "occupied":
                    bg = "#0F172A"
                    txt_color = "#334155"
                elif s.status == "vip":
                    bg = AppColors.ACCENT_GOLD
                    txt_color = "#000000"
                else:
                    bg = "#1E293B"
                    txt_color = AppColors.TEXT_SECONDARY

                seat_btn = ft.Container(
                    content=ft.Text(f"{s.number}", size=10, weight=ft.FontWeight.BOLD, color=txt_color),
                    width=32,
                    height=32,
                    bgcolor=bg,
                    border_radius=AppRadius.SMALL,
                    alignment=ft.Alignment(0, 0),
                    ink=s.status != "occupied",
                    on_click=lambda e, seat=s: self._toggle_seat(seat),
                    animate=150
                )
                seat_buttons.append(seat_btn)

            row_container = ft.Row(
                controls=[
                    ft.Text(f"Sıra {r}", size=10, color=AppColors.TEXT_MUTED, width=42),
                    ft.Row(controls=seat_buttons, spacing=6)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4
            )
            self.matrix_container.controls.append(row_container)

    def _toggle_seat(self, seat: Seat):
        if seat.status == "occupied":
            return
        
        if seat in self.selected_seats:
            self.selected_seats.remove(seat)
        else:
            if len(self.selected_seats) >= MAX_TICKETS_PER_USER:
                return
            self.selected_seats.append(seat)

        self.quota_badge.value = f"Seçilen: {len(self.selected_seats)} / {MAX_TICKETS_PER_USER} Koltuk"
        self._render_matrix()
        try:
            self.update()
        except Exception:
            pass
        if self.on_selection_change:
            self.on_selection_change(self.selected_seats)

    def _change_block(self, block: str):
        self.current_block = block
        self.content.controls[1] = self._build_block_selector()
        self._render_matrix()
        try:
            self.update()
        except Exception:
            pass
