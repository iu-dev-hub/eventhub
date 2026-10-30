"""Koltuk kilitleme ve ödeme uç noktaları."""
from flask import jsonify, request

from app.payments import bp, services


def _get_seats(data):
    """Gövdeden koltuk listesini alır, geçersizse None döner."""
    seats = data.get("seats")
    if not isinstance(seats, list) or not seats:
        return None
    if not all(isinstance(s, str) for s in seats):
        return None
    return seats


@bp.post("/api/seats/lock")
def lock_seats():
    # silent=True: bozuk JSON gelirse hata fırlatmak yerine None döner
    data = request.get_json(silent=True) or {}
    seats = _get_seats(data)
    if seats is None:
        return jsonify({"success": False, "message": "seats listesi gerekli"}), 400

    ok, taken, expires = services.lock_seats(seats)
    if not ok:
        # Koltuk zaten kilitli veya dolu: 409 Conflict
        return jsonify({
            "success": False,
            "message": "Koltuk(lar) zaten kilitli veya dolu",
            "seats": taken,
        }), 409

    return jsonify({
        "success": True,
        "seats": seats,
        "expiresAt": expires.isoformat(timespec="seconds"),
    }), 200


@bp.post("/api/payment/pay")
def pay():
    data = request.get_json(silent=True) or {}
    card_number = str(data.get("cardNumber") or "")
    amount = data.get("amount")
    seats = _get_seats(data) or []

    # Görev gereği başarısız ödeme de 200 döner, sonuç success alanındadır
    result = services.process_payment(card_number, amount, seats)
    return jsonify(result), 200
