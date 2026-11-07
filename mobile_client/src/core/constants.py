"""
Kültür, Sahne Sanatları ve Etkinlik Sabitleri (Sadece Etkinlikler - Maç Yok)
"""
# İş Kuralları Limitleri
MAX_TICKETS_PER_USER = 4       # BR-3.1: Bir kullanıcı en fazla 4 bilet alabilir
CART_EXPIRY_MINUTES = 15       # BR-3.5: Koltuk ayrıldıktan sonra 15 dk süre
QR_REFRESH_SECONDS = 30        # Dinamik turnike QR kod tazeleme süresi
EARLY_BIRD_DAYS = 14           # BR-4.1: 14 gün öncesi erken kayıt %20 indirim
EARLY_BIRD_DISCOUNT = 0.20
STUDENT_DISCOUNT = 0.25        # BR-4.2: Öğrenci indirimi %25
GATE_OPEN_HOURS = 1            # BR-3.7: Kapılar 1 saat önce açılır
SALES_CLOSE_HOURS = 1          # BR-3.3: Satış 1 saat önce kapanır

# Saf Etkinlik ve Sanat Kategorileri (Maçlar kaldırıldı)
CATEGORIES = [
    {"id": "all", "name": "Tüm Etkinlikler", "icon": "CONFIRMATION_NUMBER"},
    {"id": "concert", "name": "Konser & Müzik", "icon": "MUSIC_NOTE"},
    {"id": "theatre", "name": "Tiyatro & Sahne", "icon": "THEATER_COMEDY"},
    {"id": "festival", "name": "Festival & Açık Hava", "icon": "FESTIVAL"},
    {"id": "standup", "name": "Stand-Up & Komedi", "icon": "MIC"},
    {"id": "exhibition", "name": "Sergi & Dijital Sanat", "icon": "PALETTE"},
    {"id": "workshop", "name": "Atölye & Deneyim", "icon": "AUTO_STORIES"},
]

# Prestijli Sahne ve Gösteri Salonları (Stadyumlar kaldırıldı)
DEFAULT_VENUES = [
    {
        "id": "v-1",
        "name": "Zorlu PSM — Turkcell Sahnesi",
        "city": "İstanbul",
        "address": "Levazım Mah. Koru Sok. No:2, Beşiktaş",
        "capacity": 2200
    },
    {
        "id": "v-2",
        "name": "Atatürk Kültür Merkezi (AKM) — Opera Salonu",
        "city": "İstanbul",
        "address": "Gümüşsuyu, Taksim Meydanı, Beyoğlu",
        "capacity": 2040
    },
    {
        "id": "v-3",
        "name": "Harbiye Cemil Topuzlu Açıkhava Tiyatrosu",
        "city": "İstanbul",
        "address": "Taşkışla Cad. No:8, Harbiye, Şişli",
        "capacity": 4500
    },
    {
        "id": "v-4",
        "name": "Maximum Uniq Hall",
        "city": "İstanbul",
        "address": "Huzur Mah. Maslak Ayazağa Cad., Sarıyer",
        "capacity": 1200
    },
    {
        "id": "v-5",
        "name": "Tersane İstanbul — Sanat & Sergi Alanı",
        "city": "İstanbul",
        "address": "Kasımpaşa, Haliç Kıyısı, Beyoğlu",
        "capacity": 3500
    }
]
