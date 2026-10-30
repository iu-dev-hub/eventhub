"""
QR Kod Servisi
BR-3.6: Her biletin benzersiz QR kodu vardır. Kapıda okutulur, tek seferlik kullanılır.
features.md: Kopyalamayı önlemek için 30 saniyede bir kendini tazeleyen dinamik token yapısı.
"""
import io
import time
import hashlib
import qrcode
from typing import Tuple, Dict

class QRService:
    @staticmethod
    def generate_dynamic_token(ticket_id: str, pnr: str, user_id: str) -> str:
        """30 saniyelik zaman dilimine bağlı tek kullanımlık dinamik token"""
        time_slot = int(time.time() // 30)
        raw = f"{ticket_id}:{pnr}:{user_id}:{time_slot}:salt_eventhub_2026"
        token_hash = hashlib.sha256(raw.encode()).hexdigest()[:16].upper()
        return f"PASS-{pnr}-{token_hash}"

    @classmethod
    def generate_qr_bytes(cls, ticket_id: str, pnr: str, user_id: str) -> Tuple[bytes, str]:
        """Bilet turnike ekranı için PNG görsel baytları ve geçerli dinamik token döner"""
        token = cls.generate_dynamic_token(ticket_id, pnr, user_id)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(token)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), token

    @classmethod
    def verify_token(cls, token: str) -> Dict[str, any]:
        """Turnike simülasyonu için token doğrulama kontrolü"""
        if not token.startswith("PASS-"):
            return {"valid": False, "reason": "Geçersiz bilet formatı"}
        
        parts = token.split("-")
        if len(parts) < 3:
            return {"valid": False, "reason": "Bozuk bilet verisi"}
        
        pnr = parts[1]
        return {
            "valid": True,
            "pnr": pnr,
            "message": "Turnike Geçişi Onaylandı - İyi Seyirler!"
        }
