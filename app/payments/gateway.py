"""Ödeme sağlayıcısı (Payment Gateway) adaptörü ve simülatörü (TG-148).

Gerçek ödeme altyapısı (Iyzico, Stripe vb.) entegrasyonu için Provider / Adapter
tasarım deseni sunar.
"""
import uuid
from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    """Harici ödeme sağlayıcıları için temel soyut sınıf."""

    @abstractmethod
    def charge(
        self, card_number: str, amount: float, currency: str = "TRY"
    ) -> dict:
        """Ödeme işlemini gerçekleştirir ve sağlayıcı sonucunu döner."""
        pass


class SimulatedPaymentGateway(PaymentGateway):
    """EventHub için test ve simülasyon ödeme sağlayıcısı adaptörü."""

    def charge(
        self, card_number: str, amount: float, currency: str = "TRY"
    ) -> dict:
        sanitized = card_number.replace(" ", "").replace("-", "").strip()

        if len(sanitized) != 16 or not sanitized.isdigit():
            return {
                "success": False,
                "error_code": "INVALID_CARD",
                "message": "Geçersiz kart",
                "transaction_id": None,
            }

        if sanitized.endswith("4242"):
            txn_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
            return {
                "success": True,
                "error_code": None,
                "message": "Ödeme başarılı",
                "transaction_id": txn_id,
                "amount": amount,
                "currency": currency,
            }

        if sanitized.endswith("0000"):
            return {
                "success": False,
                "error_code": "INSUFFICIENT_FUNDS",
                "message": "Yetersiz bakiye",
                "transaction_id": None,
            }

        return {
            "success": False,
            "error_code": "DECLINED",
            "message": "Geçersiz kart",
            "transaction_id": None,
        }


def get_payment_gateway() -> PaymentGateway:
    """Aktif yapılandırılmış ödeme sağlayıcı adaptörünü döner."""
    return SimulatedPaymentGateway()
