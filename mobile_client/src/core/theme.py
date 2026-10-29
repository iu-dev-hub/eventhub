"""
Tema ve Renk Paleti - AURA Events Özgün Sanat & Kültür Deneyimi
Passo'dan tamamen farklı, daha önce yapılmamış, gözü yormayan 'Ambient Velvet Dark' paleti.
Köşeli yapılar içermez, tüm çizgiler yumuşak ve ergonomiktir.
"""
import flet as ft

class AppColors:
    # Arka planlar (Gözü yormayan derin kadife obsidyen tonları)
    BG_DARK = "#090C15"
    BG_SURFACE = "#111625"
    BG_CARD = "#171E31"
    BG_CARD_HOVER = "#202A42"
    BG_INPUT = "#0D121F"
    
    # Özgün Aura İmzası: Ethereal Indigo, Elektrik Lavanta & Canlı Neon Turkuaz
    PRIMARY = "#6366F1"          # Aurora Indigo (Asil, modern, göz yormayan ana renk)
    PRIMARY_LIGHT = "#818CF8"    # Yumuşak Lavanta
    PRIMARY_GRADIENT_START = "#6366F1"
    PRIMARY_GRADIENT_END = "#A855F7"
    
    SECONDARY = "#06B6D4"        # Ethereal Cyan (Küratör seçimi ve indirimler)
    ACCENT_ROSE = "#F43F5E"      # Bilet ve Hızlı Eylem Vurgusu
    ACCENT_GOLD = "#FCD34D"      # VIP Sahne & Şampanya Altını
    
    # Durum Renkleri
    SUCCESS = "#10B981"          # Satışta / Onaylandı
    WARNING = "#F59E0B"          # Az Koltuk Kaldı
    DANGER = "#EF4444"           # Tükendi / İptal
    INFO = "#38BDF8"             # Kültür Rehberi
    
    # Gözü Yormayan Dinlendirici Metin Renkleri
    TEXT_PRIMARY = "#F8FAFC"     # Yumuşak kırık beyaz
    TEXT_SECONDARY = "#94A3B8"   # Dingin gümüş gri
    TEXT_MUTED = "#64748B"       # Muted slate
    
    # Tiyatro / Sahne Koltuk Renkleri
    SEAT_AVAILABLE = "#1E293B"   # Boş koltuk (dingin koyu slate)
    SEAT_SELECTED = "#6366F1"    # Seçili koltuk (parlayan aurora)
    SEAT_OCCUPIED = "#0F172A"    # Dolu koltuk
    SEAT_VIP = "#F59E0B"         # VIP Parter koltuğu

class AppRadius:
    # Köşesiz, insanı yormayan yumuşak kavisler
    SMALL = 12
    NORMAL = 18
    LARGE = 24
    CARD = 26
    FULL = 999  # Pill / Tam oval

class AppTheme:
    @staticmethod
    def get_theme():
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=AppColors.PRIMARY,
                surface=AppColors.BG_SURFACE,
                on_primary=ft.Colors.WHITE,
            ),
        )
