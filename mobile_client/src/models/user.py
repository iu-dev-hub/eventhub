"""
Kullanıcı Veri Modeli
BR-1.1: Katılımcı (participant), Organizatör (organizer), Yönetici (admin)
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: str
    name: str
    email: str
    phone: str
    role: str = "participant"          # participant | organizer | admin
    is_student: bool = False           # BR-1.6: Öğrenci indirimi
    is_approved: bool = True           # BR-1.5: Organizatör yönetici onayı
    is_locked: bool = False            # BR-1.4: Hatalı giriş kilit kontrolü
    failed_attempts: int = 0
    created_at: Optional[str] = None
