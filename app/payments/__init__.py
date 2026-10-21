"""Ödeme modülü: koltuk kilitleme ve ödeme API'si."""
from flask import Blueprint

# Blueprint adı kurallara göre "payments" olmalı
bp = Blueprint("payments", __name__)

# routes en altta içe aktarılır, böylece döngüsel import oluşmaz
from app.payments import routes  # noqa: E402, F401
