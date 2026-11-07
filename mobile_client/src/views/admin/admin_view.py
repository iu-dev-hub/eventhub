"""
AURA Ayrı Yönetici & Organizatör Paneli (Dedicated Admin & API Control Station)
Kullanıcının isteği:
'admin paneli ayrı yap ve sadece admin panel için api ile ilgili olan şeyleri aç'
Tüm API kontrolleri, canlı veri çekme düğmeleri, log konsolu ve entegrasyon ayarları
yalnızca bu panelde yer alır.
"""
import flet as ft
from src.core.theme import AppColors, AppRadius
from src.services.api_service import api_service
from src.services.qr_service import QRService

class AdminView(ft.Container):
    def __init__(self, on_back_to_app_callback, on_api_synced_callback=None):
        self.on_back_to_app_callback = on_back_to_app_callback
        self.on_api_synced_callback = on_api_synced_callback
        
        # 1. CANLI API KONTROL BUTONLARI & ANAHTARLARI (YALNIZCA ADMİNDE)
        self.api_toggle_switch = ft.Switch(
            value=api_service.is_live_api_active,
            active_color=AppColors.SUCCESS,
            on_change=self._handle_api_toggle
        )
        
        # Canlı API Butonu
        self.manual_sync_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CLOUD_DOWNLOAD_OUTLINED, size=15, color=ft.Colors.WHITE),
                    ft.Text("Canlı API'den Veri Çek (Senkronize Et)", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor=AppColors.PRIMARY,
            padding=ft.Padding(16, 10, 16, 10),
            border_radius=AppRadius.FULL,
            ink=True,
            on_click=self._handle_manual_sync
        )

        self.api_status_badge = ft.Text(
            "CANLI API: AKTİF" if api_service.is_live_api_active else "CANLI API: PASİF (MOCK MODU)",
            size=11,
            weight=ft.FontWeight.BOLD,
            color=AppColors.SUCCESS if api_service.is_live_api_active else AppColors.TEXT_MUTED
        )

        # API Log Konsolu
        self.log_column = ft.Column(spacing=4)
        
        # Turnike Simülatörü giriş kutusu
        self.token_input = ft.TextField(
            label="Turnike Optik Bilet Kodunu Girin",
            hint_text="Ör: PASS-AURA-94182-TOKEN",
            border_radius=AppRadius.NORMAL,
            bgcolor="#0E1320",
            border_color="#202A40",
            color=AppColors.TEXT_PRIMARY,
            text_size=11,
            expand=True
        )
        self.token_result_text = ft.Text("", size=11, weight=ft.FontWeight.BOLD)

        self.stats_row = ft.Row(spacing=8, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        self.events_list_column = ft.Column(spacing=8)

        super().__init__(
            content=ft.Column(
                controls=[
                    # Üst Yönetici Başlık Barı ve Mobil Uygulamaya Dönüş Butonu
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(ft.Icons.ARROW_BACK, size=16, color=ft.Colors.WHITE),
                                            ft.Text("Mobil Uygulamaya Dön", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                                        ],
                                        spacing=4
                                    ),
                                    bgcolor="#1B2236",
                                    padding=ft.Padding(12, 6, 12, 6),
                                    border_radius=AppRadius.FULL,
                                    border=ft.Border.all(1, "#2C3955"),
                                    ink=True,
                                    on_click=lambda e: self.on_back_to_app_callback()
                                ),
                                ft.Container(
                                    content=ft.Text("ADMİN & OPERASYON", size=9, weight=ft.FontWeight.BOLD, color=AppColors.ACCENT_GOLD),
                                    bgcolor="#242114",
                                    padding=ft.Padding(8, 4, 8, 4),
                                    border_radius=AppRadius.FULL,
                                    border=ft.Border.all(1, "#FCD34D44")
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        margin=ft.Margin(16, 6, 16, 6)
                    ),
                    # Panel Başlığı
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("AURA Yönetici & API İstasyonu", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                ft.Text("Tüm harici API entegrasyonu, ciro ve turnike kontrolleri yalnızca bu paneldedir.", size=10, color=AppColors.TEXT_MUTED)
                            ],
                            spacing=2
                        ),
                        margin=ft.Margin(16, 0, 16, 8)
                    ),
                    # BÖLÜM 1: CANLI API ENTEGRASYON MERKEZİ (SADECE ADMİNE ÖZEL)
                    self._build_api_station(),
                    # BÖLÜM 2: FİNANSAL VE OPERASYON RAPORLARI (BR-4.7)
                    ft.Container(
                        content=self.stats_row,
                        margin=ft.Margin(16, 0, 16, 8)
                    ),
                    # BÖLÜM 3: KAPI & TURNİKE DOĞRULAMA SİMÜLATÖRÜ (BR-3.6)
                    self._build_gate_validator(),
                    # BÖLÜM 4: SAHNE ETKİNLİK YÖNETİMİ & İPTAL KONTROLÜ (BR-2.7)
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Kültür & Sanat Etkinlikleri Operasyonu", size=13, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                                ft.Text("BR-2.7: Bilet satılmış etkinlik silinemez, yalnızca iptal edilebilir.", size=10, color=AppColors.TEXT_MUTED),
                                self.events_list_column
                            ],
                            spacing=6
                        ),
                        margin=ft.Margin(16, 6, 16, 80)
                    )
                ],
                spacing=6,
                scroll=ft.ScrollMode.ADAPTIVE
            ),
            expand=True
        )
        self.refresh_admin_data()

    def _build_api_station(self):
        """Kullanıcının isteği: Sadece admin panel için açık olan API araçları"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Üst Başlık ve Anahtar
                    ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.AUTO_AWESOME, size=16, color=AppColors.SECONDARY),
                                    ft.Text("Canlı API Entegrasyon İstasyonu", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                                ],
                                spacing=6
                            ),
                            self.api_toggle_switch
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    self.api_status_badge,
                    ft.Text(
                        "Dış API servisini dilediğiniz an açıp kapatabilir, aşağıdaki butona basarak canlı veri çekmeyi manuel tetikleyebilirsiniz.",
                        size=10,
                        color=AppColors.TEXT_MUTED
                    ),
                    # API'den Veri Çek Butonu
                    ft.Row(controls=[self.manual_sync_btn]),
                    # API İstek / Yanıt Log Konsolu
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.TERMINAL, size=13, color=AppColors.SECONDARY),
                                        ft.Text("Canlı API İstek & Yanıt Günlüğü", size=10, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED)
                                    ],
                                    spacing=4
                                ),
                                self.log_column
                            ],
                            spacing=4
                        ),
                        padding=10,
                        bgcolor="#0A0E18",
                        border_radius=AppRadius.NORMAL,
                        border=ft.Border.all(1, "#1C263A")
                    )
                ],
                spacing=8
            ),
            padding=14,
            bgcolor="#111625",
            border_radius=AppRadius.CARD,
            border=ft.Border.all(1, AppColors.SECONDARY if api_service.is_live_api_active else "#202A40"),
            margin=ft.Margin(16, 0, 16, 8)
        )

    def _build_gate_validator(self):
        """Kapı Turnike QR Doğrulama Aracı (BR-3.6)"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.QR_CODE_SCANNER, size=16, color=AppColors.PRIMARY_LIGHT),
                            ft.Text("Turnike Optik Kod Doğrulama (BR-3.6)", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ],
                        spacing=6
                    ),
                    ft.Row(
                        controls=[
                            self.token_input,
                            ft.Container(
                                content=ft.Text("Doğrula", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                bgcolor=AppColors.SUCCESS,
                                padding=ft.Padding(14, 11, 14, 11),
                                border_radius=AppRadius.NORMAL,
                                ink=True,
                                on_click=self._handle_verify_token
                            )
                        ],
                        spacing=8
                    ),
                    self.token_result_text
                ],
                spacing=8
            ),
            padding=14,
            bgcolor=AppColors.BG_CARD,
            border_radius=AppRadius.CARD,
            border=ft.Border.all(1, "#202A40"),
            margin=ft.Margin(16, 0, 16, 8)
        )

    def _handle_api_toggle(self, e):
        api_service.toggle_live_api(e.control.value)
        self.api_status_badge.value = "CANLI API: AKTİF" if api_service.is_live_api_active else "CANLI API: PASİF (MOCK MODU)"
        self.api_status_badge.color = AppColors.SUCCESS if api_service.is_live_api_active else AppColors.TEXT_MUTED
        self.refresh_admin_data()
        if self.on_api_synced_callback:
            self.on_api_synced_callback()

    def _handle_manual_sync(self, e):
        res = api_service.sync_with_remote_api()
        self.refresh_admin_data()
        if self.on_api_synced_callback:
            self.on_api_synced_callback()

    def _handle_verify_token(self, e):
        tok = self.token_input.value or ""
        result = QRService.verify_token(tok)
        if result["valid"]:
            self.token_result_text.value = f"✅ {result['message']} (PNR: {result['pnr']})"
            self.token_result_text.color = AppColors.SUCCESS
        else:
            self.token_result_text.value = f"❌ {result['reason']}"
            self.token_result_text.color = AppColors.DANGER
        try:
            self.token_result_text.update()
        except Exception:
            pass

    def refresh_admin_data(self):
        summary = api_service.get_admin_summary()
        
        self.stats_row.controls = [
            self._build_kpi_card(ft.Icons.ATTACH_MONEY, "Sanat Geliri", f"{int(summary['total_revenue'])} ₺", AppColors.SUCCESS),
            self._build_kpi_card(ft.Icons.CONFIRMATION_NUMBER, "Bilet Adedi", f"{summary['total_tickets_sold']}", AppColors.PRIMARY_LIGHT),
            self._build_kpi_card(ft.Icons.AUTO_STORIES, "Etkinlikler", f"{summary['total_events']}", AppColors.SECONDARY),
        ]

        self.log_column.controls.clear()
        if not api_service.sync_logs:
            self.log_column.controls.append(
                ft.Text("Log yok. Canlı senkronizasyon için yukarıdaki butona basabilirsiniz.", size=10, color=AppColors.TEXT_MUTED)
            )
        else:
            for log in api_service.sync_logs[-4:]:
                self.log_column.controls.append(
                    ft.Text(log, size=9, color=AppColors.TEXT_SECONDARY, font_family="monospace")
                )

        self.events_list_column.controls.clear()
        for ev in list(api_service.events.values()):
            is_cancelled = (ev.status == "cancelled")
            self.events_list_column.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(ev.title, size=12, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY, max_lines=1),
                                    ft.Text(f"{ev.venue_name.split('—')[0]} • Doluluk: {ev.sold_count}/{ev.capacity}", size=10, color=AppColors.TEXT_MUTED)
                                ],
                                spacing=2,
                                expand=True
                            ),
                            ft.Container(
                                content=ft.Text(
                                    "İPTAL EDİLDİ" if is_cancelled else "İptal Et",
                                    size=10,
                                    weight=ft.FontWeight.BOLD,
                                    color=AppColors.DANGER if not is_cancelled else AppColors.TEXT_MUTED
                                ),
                                bgcolor="#2B151A" if not is_cancelled else "#171E31",
                                padding=ft.Padding(10, 4, 10, 4),
                                border_radius=AppRadius.FULL,
                                ink=not is_cancelled,
                                on_click=lambda e, eid=ev.id: self._cancel_event(eid) if not is_cancelled else None
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    padding=12,
                    bgcolor="#111625",
                    border_radius=AppRadius.NORMAL,
                    border=ft.Border.all(1, "#202A40")
                )
            )

        try:
            self.update()
        except Exception:
            pass

    def _cancel_event(self, event_id: str):
        api_service.cancel_event(event_id)
        self.refresh_admin_data()

    def _build_kpi_card(self, icon, label, val, color):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(icon, size=16, color=color),
                    ft.Text(label, size=9, color=AppColors.TEXT_MUTED),
                    ft.Text(val, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
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
