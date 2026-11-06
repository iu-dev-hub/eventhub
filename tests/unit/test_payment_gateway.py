"""Birim testleri: PaymentGateway adaptörü ve sağlayıcı simülatörü (TG-149)."""
from app.payments.gateway import (
    PaymentGateway,
    SimulatedPaymentGateway,
    get_payment_gateway,
)

VALID_CARD = "4242424242424242"
FAIL_CARD = "1111111111110000"
DECLINED_CARD = "5555555555555555"


def test_payment_gateway_instance():
    """get_payment_gateway bir PaymentGateway örneği döner."""
    gateway = get_payment_gateway()
    assert isinstance(gateway, PaymentGateway)
    assert isinstance(gateway, SimulatedPaymentGateway)


def test_gateway_charge_success_returns_transaction_id():
    """4242 ile biten kartlar için benzersiz transaction_id üretilir."""
    gateway = get_payment_gateway()
    res = gateway.charge(VALID_CARD, amount=150.0, currency="TRY")
    assert res["success"] is True
    assert res["error_code"] is None
    assert res["message"] == "Ödeme başarılı"
    assert res["transaction_id"].startswith("TXN-")
    assert res["amount"] == 150.0
    assert res["currency"] == "TRY"


def test_gateway_charge_insufficient_funds():
    """0000 ile biten kartlar için INSUFFICIENT_FUNDS hata kodu döner."""
    gateway = get_payment_gateway()
    res = gateway.charge(FAIL_CARD, amount=100.0)
    assert res["success"] is False
    assert res["error_code"] == "INSUFFICIENT_FUNDS"
    assert res["message"] == "Yetersiz bakiye"
    assert res["transaction_id"] is None


def test_gateway_charge_invalid_card_format():
    """Hatalı uzunluk veya harf içeren kartlar INVALID_CARD olarak işaretlenir."""
    gateway = get_payment_gateway()
    res1 = gateway.charge("1234", amount=50.0)
    assert res1["success"] is False
    assert res1["error_code"] == "INVALID_CARD"

    res2 = gateway.charge("424242424242abcd", amount=50.0)
    assert res2["success"] is False
    assert res2["error_code"] == "INVALID_CARD"


def test_gateway_charge_declined():
    """Geçerli formatta ancak tanımsız kartlar DECLINED döner."""
    gateway = get_payment_gateway()
    res = gateway.charge(DECLINED_CARD, amount=200.0)
    assert res["success"] is False
    assert res["error_code"] == "DECLINED"
