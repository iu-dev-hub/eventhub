"""
AURA Ana Sayfa ve Etkinlik Keşif Görünümü (Özgün Sanat Portalı)
Küratör Seçimi Hero Banner, Sakin Kategori Çipleri, Dinlendirici Arama & Etkinlik Kartları
"""
import flet as ft
from src.core.theme import AppColors, AppRadius
from src.core.constants import CATEGORIES
from src.services.api_service import api_service
from src.services.auth_service import auth_service
from src.components.event_card import EventCard

class HomeView(ft.Container):
    def __init__(self, on_event_select, on_api_sync):
        self.on_event_select = on_event_select
        self.on_api_sync = on_api_sync
        self.selected_category = "all"
        self.search_term = ""

        self.events_column = ft.Column(spacing=14, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        # Gözü yormayan sakin arama kutusu
        self.search_field = ft.TextField(
            hint_text="Konser, tiyatro, sergi veya sanatçı ara...",
            hint_style=ft.TextStyle(color=AppColors.TEXT_MUTED, size=12),
            prefix_icon=ft.Icons.SEARCH,
            border_radius=AppRadius.FULL,
            bgcolor="#111625",
            border_color="#232C42",
            color=AppColors.TEXT_PRIMARY,
            text_size=12,
            content_padding=ft.Padding(16, 10, 16, 10),
            on_change=self._on_search_change,
            expand=True
        )

        # Öğrenci durumu
        self.student_switch = ft.Switch(
            value=auth_service.current_user.is_student,
            active_color=AppColors.SECONDARY,
            on_change=self._toggle_student
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    # Arama Barı
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                self.search_field,
                            ]
                        ),
                        margin=ft.Margin(16, 0, 16, 8)
                    ),
                    # Öğrenci Kültür & Sanat İndirim Kartı (BR-4.2)
                    self._build_student_banner(),
                    # Küratör Seçimi Hero Banner (Sanat & Sahne Odaklı)
                    self._build_hero_banner(),
                    # Kategori Çipleri
                    self._build_category_chips(),
                    # Bölüm Başlığı
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text("Seçkin Sahne & Gösteriler", size=15, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                                ft.Text("Tümü", size=11, color=AppColors.PRIMARY_LIGHT, weight=ft.FontWeight.W_600)
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        margin=ft.Margin(16, 10, 16, 4)
                    ),
                    # Etkinlik Kartları Listesi
                    ft.Container(
                        content=self.events_column,
                        margin=ft.Margin(16, 0, 16, 80)
                    )
                ],
                spacing=6,
                scroll=ft.ScrollMode.ADAPTIVE
            ),
            expand=True
        )
        self.refresh_events()

    def _build_student_banner(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.AUTO_AWESOME, size=16, color=AppColors.SECONDARY),
                            ft.Column(
                                controls=[
                                    ft.Text("Genç & Öğrenci Sanat Desteği (%25 İndirim)", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                    ft.Text("BR-4.2: Tüm tiyatro ve konser biletlerinde geçerli", size=9, color=AppColors.TEXT_MUTED)
                                ],
                                spacing=1
                            )
                        ],
                        spacing=8
                    ),
                    self.student_switch
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=ft.Padding(14, 8, 14, 8),
            bgcolor="#112231",
            border_radius=AppRadius.NORMAL,
            border=ft.Border.all(1, "#06B6D433"),
            margin=ft.Margin(16, 0, 16, 4)
        )

    def _build_hero_banner(self):
        """Sanat & Sahne Odaklı Küratör Seçimi Büyük Görsel"""
        featured_evt = api_service.events.get("evt-201")
        if not featured_evt:
            return ft.Container()

        return ft.Container(
            content=ft.Stack(
                controls=[
                    ft.Image(
                        src=featured_evt.image_url,
                        width=350,
                        height=180,
                        fit=ft.BoxFit.COVER,
                        border_radius=AppRadius.CARD
                    ),
                    ft.Container(
                        width=350,
                        height=180,
                        border_radius=AppRadius.CARD,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment(-1, -1),
                            end=ft.Alignment(1, 1),
                            colors=["#00000011", "#090C15F5"]
                        )
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(
                                    content=ft.Text("✨ KÜRATÖR SEÇİMİ", size=9, weight=ft.FontWeight.BOLD, color=AppColors.SECONDARY),
                                    bgcolor="#0B202DCC",
                                    padding=ft.Padding(10, 4, 10, 4),
                                    border_radius=AppRadius.FULL,
                                    border=ft.Border.all(1, "#06B6D455")
                                ),
                                ft.Text(
                                    featured_evt.title,
                                    size=17,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                    max_lines=2
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Text(f"🏛️ {featured_evt.venue_name.split('—')[0]}", size=11, color=AppColors.TEXT_MUTED),
                                        ft.Container(
                                            content=ft.Text("Bilet Seç", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                            bgcolor=AppColors.PRIMARY,
                                            padding=ft.Padding(14, 6, 14, 6),
                                            border_radius=AppRadius.FULL
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                )
                            ],
                            spacing=6
                        ),
                        bottom=14,
                        left=16,
                        right=16
                    )
                ],
                width=350,
                height=180
            ),
            margin=ft.Margin(16, 4, 16, 8),
            ink=True,
            on_click=lambda e: self.on_event_select(featured_evt)
        )

    def _build_category_chips(self):
        chips = []
        for cat in CATEGORIES:
            is_active = (cat["id"] == self.selected_category)
            chips.append(
                ft.Container(
                    content=ft.Text(
                        cat["name"],
                        size=11,
                        weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                        color=ft.Colors.WHITE if is_active else AppColors.TEXT_MUTED
                    ),
                    bgcolor=AppColors.PRIMARY if is_active else "#131929",
                    padding=ft.Padding(14, 7, 14, 7),
                    border_radius=AppRadius.FULL,
                    border=ft.Border.all(1, AppColors.PRIMARY if is_active else "#222C42"),
                    ink=True,
                    on_click=lambda e, cid=cat["id"]: self._select_category(cid),
                    animate=200
                )
            )

        return ft.Container(
            content=ft.Row(
                controls=chips,
                scroll=ft.ScrollMode.ALWAYS,
                spacing=8
            ),
            padding=ft.Padding(16, 4, 16, 6)
        )

    def _on_search_change(self, e):
        self.search_term = e.control.value
        self.refresh_events()

    def _select_category(self, cat_id: str):
        self.selected_category = cat_id
        self.content.controls[3] = self._build_category_chips()
        self.refresh_events()
        try:
            self.update()
        except Exception:
            pass

    def _toggle_student(self, e):
        auth_service.toggle_student()
        self.refresh_events()

    def refresh_events(self):
        events = api_service.get_events(self.selected_category, self.search_term)
        self.events_column.controls.clear()
        
        if not events:
            self.events_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.SEARCH_OFF, size=44, color=AppColors.TEXT_MUTED),
                            ft.Text("Aramanızla eşleşen sanat etkinliği bulunamadı.", size=12, color=AppColors.TEXT_MUTED)
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8
                    ),
                    padding=32
                )
            )
        else:
            for ev in events:
                card = EventCard(ev, self.on_event_select)
                self.events_column.controls.append(card)
        
        try:
            self.events_column.update()
        except Exception:
            pass
