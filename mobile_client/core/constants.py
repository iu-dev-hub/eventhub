"""
EventHub Mobil Uygulama Sabitleri
Bu dosya projede kullanılan sabitleri tanımlar.
"""

# User roles
USER_ROLES = {"participant": "Katılımcı", "organizer": "Organizatör", "admin": "Yönetici"}

# Event statuses
EVENT_STATUSES = {
    "draft": "Taslak",
    "published": "Yayında",
    "sales_closed": "Satışa kapalı",
    "completed": "Tamamlandı",
    "cancelled": "İptal edildi",
}

# Ticket statuses
TICKET_STATUSES = {
    "reserved": "Ayrıldı (ödeme bekleniyor)",
    "paid": "Geçerli",
    "used": "Kullanıldı",
    "refunded": "İade edildi",
    "cancelled": "İptal edildi",
}

# Business rule constants
MAX_TICKETS_PER_EVENT = 4  # BR-3.1
EARLY_BIRD_DAYS_THRESHOLD = 14  # BR-4.1
REFUND_7DAYS_THRESHOLD = 7  # BR-4.4
REFUND_2_6DAYS_THRESHOLD = 2  # BR-4.4
MINUTES_BEFORE_EVENT_START_SALES_CLOSE = 60  # BR-3.3
MINUTES_BEFORE_EVENT_START_ENTRY_OPEN = 60  # BR-3.7
TIMEOUT_FOR_PAYMENT_RESERVATION = 15  # BR-3.5 (minutes)


# Payment simulation constants
VALID_CARD_LENGTH = 16


# Account & authentication constants (BR-1)
MIN_PASSWORD_LENGTH = 8  # BR-1.3
MAX_PASSWORD_LENGTH = 20  # BR-1.3
MAX_FAILED_LOGIN_ATTEMPTS = 5  # BR-1.4
LOCKOUT_DURATION_MINUTES = 15  # BR-1.4
DEMO_INVALID_PASSWORD = "1234"  # Demo için hatalı kabul edilen şifre
MIN_STUDENT_NUMBER_LENGTH = 5
MAX_STUDENT_NUMBER_LENGTH = 15

# Kayıt ekranında seçilebilen roller (BR-1.1, BR-1.5)
REGISTER_ROLES = {
    "participant": USER_ROLES["participant"],
    "organizer": USER_ROLES["organizer"],
}

# Lokal token depolama anahtarları
TOKEN_STORAGE_KEY = "user_token"
USER_EMAIL_STORAGE_KEY = "current_user_email"
USER_ID_STORAGE_KEY = "current_user_id"


# Event categories (could be extended based on business needs)
EVENT_CATEGORIES = ["Konferans", "Seminer", "Workshop", "Performans", "Söyleşi", "Fuar", "Kültür"]
