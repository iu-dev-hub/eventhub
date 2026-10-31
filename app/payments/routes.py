"""Koltuk kilitleme ve ödeme uç noktaları."""

import sqlite3

from flask import current_app, jsonify, render_template, request, session

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
        return jsonify(
            {
                "success": False,
                "message": "Koltuk(lar) zaten kilitli veya dolu",
                "seats": taken,
            }
        ), 409

    return jsonify(
        {
            "success": True,
            "seats": seats,
            "expiresAt": expires.isoformat(timespec="seconds"),
        }
    ), 200


@bp.post("/api/payment/pay")
def pay():
    data = request.get_json(silent=True) or {}
    card_number = str(data.get("cardNumber") or "")
    amount = data.get("amount")
    seats = _get_seats(data) or []
    event_id = data.get("eventId") or data.get("event_id") or services.DEFAULT_EVENT_ID
    user_id = data.get("userId") or data.get("user_id")
    idempotency_key = data.get("idempotencyKey") or data.get("idempotency_key")

    # Görev gereği başarısız ödeme de 200 döner, sonuç success alanındadır
    result = services.process_payment(
        card_number,
        amount,
        seats,
        event_id=event_id,
        user_id=user_id,
        idempotency_key=idempotency_key,
    )
    return jsonify(result), 200


@bp.get("/api/seats/status")
def seats_status():
    """Koltukların güncel kilit ve satış durumunu döner."""
    event_id = request.args.get("event_id", default=services.DEFAULT_EVENT_ID, type=int)
    seats_param = request.args.get("seats")
    seats = None
    if seats_param:
        seats = [s.strip() for s in seats_param.split(",") if s.strip()]
    elif request.args.getlist("seats"):
        seats = request.args.getlist("seats")

    if not seats and request.is_json:
        data = request.get_json(silent=True) or {}
        seats = data.get("seats")
        if "event_id" in data:
            event_id = data.get("event_id")

    status_list = services.get_seats_status(seats=seats, event_id=event_id)
    return jsonify({
        "success": True,
        "event_id": event_id,
        "seats": status_list,
    }), 200


@bp.post("/api/seats/unlock")
def unlock_seats():
    """Kilitli koltukları manuel olarak serbest bırakır."""
    data = request.get_json(silent=True) or {}
    seats = _get_seats(data)
    if seats is None:
        return jsonify({"success": False, "message": "seats listesi gerekli"}), 400

    ok, released = services.unlock_seats(seats)
    if not ok:
        return jsonify({
            "success": False,
            "message": "Serbest bırakılacak kilitli koltuk bulunamadı",
            "released": [],
        }), 409

    return jsonify({
        "success": True,
        "message": "Koltuk kilidi kaldırıldı",
        "released": released,
    }), 200


@bp.get("/api/tickets/my-tickets")
def my_tickets_api():
    """Kullanıcının biletlerini JSON olarak döner."""
    user_id = session.get("user_id") or request.args.get("user_id", type=int) or 1
    tickets = services.get_user_tickets(user_id)
    return jsonify({"success": True, "tickets": tickets}), 200


@bp.errorhandler(sqlite3.Error)
def handle_database_error(error):
    # Ayrıntı kullanıcıya gösterilmez (güvenlik), sunucu loguna yazılır
    current_app.logger.error("Veritabanı hatası: %s", error)
    return jsonify({
        "success": False,
        "message": "Veritabanı hatası, lütfen tekrar deneyin.",
    }), 500


@bp.get("/payments/")
def payment_page():
    """Ödeme sayfası (arayüz)."""
    return render_template("payments/index.html")
