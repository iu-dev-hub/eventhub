"""
AURA Bilet Cüzdanı ve Profil Görünümleri
Kullanıcı için Biletlerim ve Profil & Ayarlar ekranları
features.md: Satın alınan biletler, dinamik 30 saniyelik turnike QR kod yapısı
"""
import flet as ft
from src.core.theme import AppColors, AppRadius
from src.services.api_service import api_service
from src.services.auth_service import auth_service
from src.services.qr_service import QRService
from src.models.ticket import Ticket

class ProfileWalletView(ft.Container):
    """Biletlerim / Cüzdan Görünümü"""
    def __init__(self, on_browse_events):
        self.on_browse_events = on_browse_events
        self.active_ticket: Ticket = None
        self.tickets_list_column = ft.Column(spacing=12)
        self.qr_card_container = ft.Container(visible=False)

        super().__init__(
            content=ft.Column(
                controls=[
                    # Başlık
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text("Bilet Cüzdanım", size=18, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                                        ft.Text("Konser, Tiyatro & Sergi Giriş Kodları", size=11, color=AppColors.TEXT_MUTED)
                                    ],
                                    spacing=2
                                ),
                                ft.Container(
                                    content=ft.Icon(ft.Icons.QR_CODE_2, color=AppColors.PRIMARY_LIGHT, size=22),
                                    bgcolor="#1B2236",
                                    padding=8,
                                    border_radius=AppRadius.NORMAL
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        margin=ft.Margin(16, 6, 16, 6)
                    ),
                    # Açık Turnike QR Kartı
                    self.qr_card_container,
                    # Biletler Listesi
                    ft.Container(
                        content=self.tickets_list_column,
                        margin=ft.Margin(16, 0, 16, 80)
                    )
                ],
                spacing=6,
                scroll=ft.ScrollMode.ADAPTIVE
            ),
            expand=True
        )
        self.refresh_tickets()

    def refresh_tickets(self):
        user_id = auth_service.current_user.id
        tickets = api_service.get_user_tickets(user_id)
        self.tickets_list_column.controls.clear()

        if not tickets:
            self.tickets_list_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.CONFIRMATION_NUMBER_OUTLINED, size=48, color=AppColors.TEXT_MUTED),
                            ft.Text("Henüz bir biletiniz bulunmuyor.", size=13, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                            ft.Text("Seçkin konser ve tiyatroları keşfedip hemen yerinizi ayırtın.", size=11, color=AppColors.TEXT_MUTED),
                            ft.Container(
                                content=ft.Text("Etkinlikleri Keşfet", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                bgcolor=AppColors.PRIMARY,
                                padding=ft.Padding(16, 8, 16, 8),
                                border_radius=AppRadius.FULL,
                                ink=True,
                                on_click=lambda e: self.on_browse_events()
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8
                    ),
                    padding=32,
                    alignment=ft.Alignment(0, 0)
                )
            )
        else:
            for tkt in tickets:
                self.tickets_list_column.controls.append(self._build_ticket_card(tkt))

        try:
            self.update()
        except Exception:
            pass

    def _build_ticket_card(self, ticket: Ticket):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(f"PNR: {ticket.pnr}", size=10, weight=ft.FontWeight.BOLD, color=AppColors.SECONDARY),
                                bgcolor="#0C1D26",
                                padding=ft.Padding(8, 3, 8, 3),
                                border_radius=AppRadius.FULL,
                                border=ft.Border.all(1, "#06B6D433")
                            ),
                            ft.Container(
                                content=ft.Text(
                                    "KULLANILDI" if ticket.status == "used" else "GEÇERLİ BİLET",
                                    size=9,
                                    weight=ft.FontWeight.BOLD,
                                    color=AppColors.TEXT_MUTED if ticket.status == "used" else AppColors.SUCCESS
                                ),
                                bgcolor="#0D2218" if ticket.status != "used" else "#1A202C",
                                padding=ft.Padding(8, 3, 8, 3),
                                border_radius=AppRadius.FULL
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Text(ticket.event_title, size=14, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.LOCATION_ON, size=13, color=AppColors.TEXT_MUTED),
                            ft.Text(f"{ticket.venue_name} • {ticket.event_date}", size=11, color=AppColors.TEXT_MUTED)
                        ],
                        spacing=4
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.EVENT_SEAT, size=13, color=AppColors.PRIMARY_LIGHT),
                                ft.Text(ticket.seat_label, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                            ],
                            spacing=5
                        ),
                        padding=ft.Padding(10, 5, 10, 5),
                        bgcolor="#0D121E",
                        border_radius=AppRadius.NORMAL
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(f"{ticket.price} ₺", size=13, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY_LIGHT),
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.QR_CODE, size=15, color=ft.Colors.WHITE),
                                        ft.Text("Turnike QR Kodunu Aç", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                                    ],
                                    spacing=4
                                ),
                                bgcolor=AppColors.PRIMARY if ticket.status != "used" else "#252F44",
                                padding=ft.Padding(12, 6, 12, 6),
                                border_radius=AppRadius.FULL,
                                ink=ticket.status != "used",
                                on_click=lambda e, t=ticket: self._open_turnstile_mode(t)
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    )
                ],
                spacing=7
            ),
            padding=14,
            bgcolor=AppColors.BG_CARD,
            border_radius=AppRadius.CARD,
            border=ft.Border.all(1, "#202A40")
        )

    def _open_turnstile_mode(self, ticket: Ticket):
        self.active_ticket = ticket
        qr_bytes, token = QRService.generate_qr_bytes(ticket.id, ticket.pnr, ticket.user_id)

        self.qr_card_container.visible = True
        self.qr_card_container.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("SALON GİRİŞ TURNİKE KODU", size=12, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY_LIGHT),
                            ft.Container(
                                content=ft.Icon(ft.Icons.CLOSE, size=15, color=AppColors.TEXT_MUTED),
                                ink=True,
                                on_click=lambda e: self._close_turnstile_mode(),
                                padding=4,
                                border_radius=AppRadius.FULL
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Text("Girişteki optik okuyucuya yaklaştırınız", size=10, color=AppColors.TEXT_MUTED),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Image(
                                    src=qr_bytes,
                                    width=175,
                                    height=175,
                                    fit=ft.BoxFit.CONTAIN
                                ),
                                ft.Text(f"KOD: {token}", size=9, weight=ft.FontWeight.BOLD, color="#0F172A")
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=3
                        ),
                        bgcolor=ft.Colors.WHITE,
                        padding=12,
                        border_radius=AppRadius.LARGE,
                        alignment=ft.Alignment(0, 0)
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.SYNC, size=13, color=AppColors.SUCCESS),
                                ft.Text("Dinamik Token: 30s Otomatik Tazeleme (Kopya Önleme)", size=9, color=AppColors.SUCCESS)
                            ],
                            spacing=4,
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        bgcolor="#0D241A",
                        padding=ft.Padding(10, 4, 10, 4),
                        border_radius=AppRadius.FULL
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.CHECK, size=15, color=ft.Colors.WHITE),
                                ft.Text("Turnikeden Geçişi Simüle Et (BR-3.6)", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=6
                        ),
                        bgcolor=AppColors.SUCCESS,
                        padding=ft.Padding(12, 7, 12, 7),
                        border_radius=AppRadius.FULL,
                        ink=True,
                        on_click=lambda e: self._simulate_gate_pass(ticket)
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            ),
            padding=16,
            bgcolor="#131B2D",
            border_radius=AppRadius.CARD,
            border=ft.Border.all(2, AppColors.PRIMARY),
            margin=ft.Margin(16, 0, 16, 12)
        )
        try:
            self.update()
        except Exception:
            pass

    def _simulate_gate_pass(self, ticket: Ticket):
        ticket.status = "used"
        self._close_turnstile_mode()
        self.refresh_tickets()

    def _close_turnstile_mode(self):
        self.qr_card_container.visible = False
        try:
            self.update()
        except Exception:
            pass

class UserProfileView(ft.Container):
    """Kullanıcı Profil ve Ayarlar Görünümü (Ayrı Yönetici Paneli Girişi Buradadır)"""
    def __init__(self, on_open_admin_panel):
        self.on_open_admin_panel = on_open_admin_panel
        user = auth_service.current_user

        super().__init__(
            content=ft.Column(
                controls=[
                    # Başlık
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Hesabım", size=20, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                                ft.Text("Kişisel Bilgiler & Tercihler", size=11, color=AppColors.TEXT_MUTED)
                            ],
                            spacing=2
                        ),
                        margin=ft.Margin(16, 8, 16, 8)
                    ),
                    # Kullanıcı Kartı
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Text(user.name[0], size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                    width=50,
                                    height=50,
                                    bgcolor=AppColors.PRIMARY,
                                    border_radius=AppRadius.FULL,
                                    alignment=ft.Alignment(0, 0)
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(user.name, size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                        ft.Text(user.email, size=11, color=AppColors.TEXT_MUTED),
                                        ft.Container(
                                            content=ft.Text("Doğrulanmış Katılımcı", size=9, weight=ft.FontWeight.BOLD, color=AppColors.SUCCESS),
                                            bgcolor="#0E231B",
                                            padding=ft.Padding(6, 2, 6, 2),
                                            border_radius=AppRadius.FULL
                                        )
                                    ],
                                    spacing=2
                                )
                            ],
                            spacing=12
                        ),
                        padding=16,
                        bgcolor=AppColors.BG_CARD,
                        border_radius=AppRadius.CARD,
                        border=ft.Border.all(1, "#202A40"),
                        margin=ft.Margin(16, 0, 16, 8)
                    ),
                    # Öğrenci İndirimi Ayarı
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.SCHOOL, size=18, color=AppColors.SECONDARY),
                                        ft.Column(
                                            controls=[
                                                ft.Text("Öğrenci / Genç İndirimi (%25)", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                                ft.Text("Kültür sanat etkinliklerinde geçerli", size=10, color=AppColors.TEXT_MUTED)
                                            ],
                                            spacing=1
                                        )
                                    ],
                                    spacing=8
                                ),
                                ft.Switch(
                                    value=user.is_student,
                                    active_color=AppColors.SECONDARY,
                                    on_change=lambda e: auth_service.toggle_student()
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=14,
                        bgcolor="#111B2A",
                        border_radius=AppRadius.NORMAL,
                        border=ft.Border.all(1, "#1E2B3E"),
                        margin=ft.Margin(16, 0, 16, 12)
                    ),
                    # BİLDİRİM & GÜVENLİK BİLGİSİ
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Uygulama Bilgileri", size=12, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED),
                                ft.Text("• AURA Events v1.0.0 (Android Sanat Sürümü)", size=11, color=AppColors.TEXT_SECONDARY),
                                ft.Text("• 256-bit Güvenli Biletleme & Dinamik Turnike Altyapısı", size=11, color=AppColors.TEXT_SECONDARY),
                            ],
                            spacing=4
                        ),
                        padding=14,
                        bgcolor=AppColors.BG_CARD,
                        border_radius=AppRadius.NORMAL,
                        border=ft.Border.all(1, "#1A2234"),
                        margin=ft.Margin(16, 0, 16, 16)
                    ),
                    # ÖZEL: AYRI YÖNETİCİ & ORGANİZATÖR PANELİNE GEÇİŞ BUTONU
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, size=18, color=AppColors.ACCENT_GOLD),
                                        ft.Text("Yönetici & Organizatör Girişi", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                                    ],
                                    spacing=6
                                ),
                                ft.Text(
                                    "Canlı API senkronizasyonu, hasılat raporları, etkinlik yönetimi ve turnike doğrulama istasyonuna erişin.",
                                    size=10,
                                    color=AppColors.TEXT_MUTED
                                ),
                                ft.Container(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(ft.Icons.LOCK_OPEN, size=15, color=ft.Colors.BLACK),
                                            ft.Text("Ayrı Yönetici Paneline Git", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=6
                                    ),
                                    bgcolor=AppColors.ACCENT_GOLD,
                                    padding=ft.Padding(0, 12, 0, 12),
                                    border_radius=AppRadius.FULL,
                                    ink=True,
                                    on_click=lambda e: self.on_open_admin_panel()
                                )
                            ],
                            spacing=10
                        ),
                        padding=16,
                        bgcolor="#1C180E",
                        border_radius=AppRadius.CARD,
                        border=ft.Border.all(1, "#FCD34D55"),
                        margin=ft.Margin(16, 0, 16, 80)
                    )
                ],
                spacing=6,
                scroll=ft.ScrollMode.ADAPTIVE
            ),
            expand=True
        )
