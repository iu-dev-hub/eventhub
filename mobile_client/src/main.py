import sys
import os
from pathlib import Path

# Proje ana dizinini sys.path'e ekle
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import flet as ft
from src.core.theme import AppColors, AppRadius
from src.services.api_service import api_service
from src.components.navbar import TopBar, FloatingBottomBar
from src.views.home.home_view import HomeView
from src.views.event_detail.detail_view import EventDetailView
from src.views.seat_selection.seat_view import SeatSelectionView
from src.views.checkout.checkout_view import CheckoutView
from src.views.profile.profile_view import ProfileWalletView, UserProfileView
from src.views.admin.admin_view import AdminView

def main(page: ft.Page):
    # Sayfa Temel Ayarları
    page.title = "AURA — Kültür, Sahne & Etkinlik Keşfi"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = AppColors.BG_DARK
    page.padding = 0
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Ekran Durum Değişkenleri
    # Komut satırından '--admin' ile doğrudan admin panelinde başlatılabilir
    is_direct_admin = "--admin" in sys.argv
    current_tab = 2 if is_direct_admin else 0
    current_screen = "admin" if is_direct_admin else "home"
    current_event = None
    current_seats = []

    # Canlı Bildirim / Toast Barı
    toast_text = ft.Text("", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    toast_container = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE, size=15, color=AppColors.SECONDARY),
                toast_text
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8
        ),
        bgcolor="#182332",
        padding=ft.Padding(16, 7, 16, 7),
        border_radius=AppRadius.FULL,
        border=ft.Border.all(1, AppColors.SECONDARY),
        visible=False,
        animate=300,
        margin=ft.Margin(20, 4, 20, 4)
    )

    def show_toast(msg: str, is_success: bool = True):
        toast_text.value = msg
        toast_container.border = ft.Border.all(1, AppColors.SUCCESS if is_success else AppColors.DANGER)
        toast_container.content.controls[0].color = AppColors.SUCCESS if is_success else AppColors.DANGER
        toast_container.visible = True
        try:
            page.update()
        except Exception:
            pass

    # Dinamik İçerik Alanı
    content_area = ft.Container(expand=True)

    # Görünüm Değiştirme Fonksiyonları
    def render_screen():
        nonlocal current_screen, current_tab
        
        # Admin modunda kullanıcı üst ve alt barları gizlenir (Ayrı Admin Paneli)
        if current_screen == "admin":
            top_bar.visible = False
            bottom_bar.visible = False
        else:
            top_bar.visible = True
            # Koltuk seçimi ve ödeme ekranında alt bar gizlenerek tam odaklanma sağlanır
            bottom_bar.visible = (current_screen in ["home", "wallet", "profile"])
            
            if current_screen == "home":
                current_tab = 0
            elif current_screen == "wallet":
                current_tab = 1
            elif current_screen == "profile":
                current_tab = 2

            bottom_bar.current_tab = current_tab
            bottom_bar.content = ft.Row(
                controls=[bottom_bar._build_item(item) for item in bottom_bar.items],
                alignment=ft.MainAxisAlignment.SPACE_AROUND
            )

        if current_screen == "home":
            view = HomeView(
                on_event_select=go_to_detail,
                on_api_sync=None
            )
        elif current_screen == "detail":
            view = EventDetailView(
                event=current_event,
                on_back_click=lambda: go_to_home(),
                on_proceed_seats=go_to_seats
            )
        elif current_screen == "seat":
            view = SeatSelectionView(
                event=current_event,
                on_back_click=lambda: go_to_detail(current_event),
                on_proceed_checkout=go_to_checkout
            )
        elif current_screen == "checkout":
            view = CheckoutView(
                event=current_event,
                selected_seats=current_seats,
                on_back_click=lambda: go_to_seats(current_event),
                on_order_success=handle_order_success
            )
        elif current_screen == "wallet":
            view = ProfileWalletView(
                on_browse_events=lambda: go_to_home()
            )
        elif current_screen == "profile":
            view = UserProfileView(
                on_open_admin_panel=go_to_admin
            )
        elif current_screen == "admin":
            view = AdminView(
                on_back_to_app_callback=go_to_profile,
                on_api_synced_callback=handle_admin_sync
            )
        else:
            view = ft.Container()

        content_area.content = view
        try:
            page.update()
        except Exception:
            pass

    # Navigasyon Eylemleri
    def go_to_home():
        nonlocal current_screen
        current_screen = "home"
        render_screen()

    def go_to_detail(event):
        nonlocal current_screen, current_event
        current_event = event
        current_screen = "detail"
        render_screen()

    def go_to_seats(event):
        nonlocal current_screen, current_event
        current_event = event
        current_screen = "seat"
        render_screen()

    def go_to_checkout(event, seats):
        nonlocal current_screen, current_event, current_seats
        current_event = event
        current_seats = seats
        current_screen = "checkout"
        render_screen()

    def go_to_profile():
        nonlocal current_screen
        current_screen = "profile"
        render_screen()

    def go_to_admin():
        nonlocal current_screen
        current_screen = "admin"
        render_screen()

    def handle_order_success(tickets):
        nonlocal current_screen
        show_toast("🎉 Tebrikler! Biletiniz cüzdana eklendi. Turnike QR kodunuz hazır.")
        current_screen = "wallet"
        render_screen()

    def handle_admin_sync():
        show_toast("⚙️ Yönetici Paneli: Veriler ve API durumu senkronize edildi.")
        render_screen()

    def on_tab_change(tab_idx: int):
        nonlocal current_screen, current_tab
        current_tab = tab_idx
        if tab_idx == 0:
            current_screen = "home"
        elif tab_idx == 1:
            current_screen = "wallet"
        elif tab_idx == 2:
            current_screen = "profile"
        render_screen()

    # Üst ve Alt Barlar (Kullanıcı için saf ve temiz)
    top_bar = TopBar(
        on_profile_click=go_to_profile
    )
    
    bottom_bar = FloatingBottomBar(
        current_tab=0,
        on_tab_change=on_tab_change
    )

    # Android Durum Çubuğu (Status Bar)
    def build_android_status_bar():
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("18:50", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    # Ön Kamera Delik Çentiği (Punch Hole)
                    ft.Container(
                        width=10,
                        height=10,
                        bgcolor="#000000",
                        border_radius=AppRadius.FULL,
                        border=ft.Border.all(1, "#30363D")
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("5G", size=10, weight=ft.FontWeight.BOLD, color=AppColors.SECONDARY),
                            ft.Icon(ft.Icons.WIFI, size=14, color=ft.Colors.WHITE),
                            ft.Row(
                                controls=[
                                    ft.Text("98%", size=10, color=AppColors.TEXT_MUTED),
                                    ft.Icon(ft.Icons.BATTERY_FULL, size=14, color=AppColors.SUCCESS)
                                ],
                                spacing=2
                            )
                        ],
                        spacing=6
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=ft.Padding(18, 6, 18, 4),
            bgcolor="#0F131A"
        )

    # Android Alt Hareket Çubuğu (Gesture Pill Bar)
    def build_android_gesture_bar():
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=130,
                        height=4,
                        bgcolor="#FFFFFF55",
                        border_radius=AppRadius.FULL
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER
            ),
            padding=ft.Padding(0, 4, 0, 8),
            bgcolor="#0F131A"
        )

    # Mobil Cihaz Şablon Çerçevesi (Android Pixel / Galaxy Form Faktörü)
    app_shell = ft.Container(
        content=ft.Column(
            controls=[
                build_android_status_bar(),
                top_bar,
                toast_container,
                content_area,
                bottom_bar,
                build_android_gesture_bar()
            ],
            spacing=0,
            expand=True
        ),
        width=420,
        bgcolor=AppColors.BG_SURFACE,
        border_radius=AppRadius.CARD,
        border=ft.Border.all(2, "#262C36"),
        shadow=ft.BoxShadow(
            spread_radius=3,
            blur_radius=30,
            color="#000000CC",
            offset=ft.Offset(0, 10)
        ),
        margin=ft.Margin(0, 8, 0, 8),
        expand=True
    )

    page.add(app_shell)
    render_screen()

if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    else:
        ft.app(target=main)
