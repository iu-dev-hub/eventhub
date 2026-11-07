"""
Uygulama Yapılandırması ve Canlı API Mod Ayarları
AURA Events — Özgün Kültür, Sanat ve Sahne Biletleme Platformu
"""
from dataclasses import dataclass

@dataclass
class AppConfig:
    app_name: str = "AURA Events"
    version: str = "1.0.0-PRO"
    
    # Canlı API Modu Yapılandırması
    # Kullanıcı arayüzdeki 'Canlı API Senkronizasyonu' butonuyla dilediği an açıp kapatabilir
    api_live_enabled: bool = False
    api_base_url: str = "https://api.auraevents.art/v1"
    api_timeout_seconds: float = 3.0
    
    # Kullanıcı Oturum Bilgisi
    current_user_id: str = "usr-aura-77"
    current_user_name: str = "Berk Yılmaz"
    current_user_email: str = "berk@auraevents.art"
    current_user_role: str = "participant"  # participant | organizer | admin
    is_student: bool = True                 # Öğrenci indirimi testi için

config = AppConfig()
