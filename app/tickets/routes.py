import json

from flask import flash, redirect, render_template, request, session, url_for

from app.core.db import get_db
from app.tickets import bp, services


@bp.route("/")
def index():
    return render_template("tickets/index.html")


@bp.route("/my-tickets")
def my_tickets():
    """Kullanıcının biletlerini listeler."""
    user_id = session.get("user_id") or request.args.get("user_id", type=int) or 1
    tickets = []
    if hasattr(services, "get_user_tickets"):
        tickets = services.get_user_tickets(user_id)
    else:
        db = get_db()
        rows = db.execute(
            "SELECT r.id, r.ticket_code, r.status, r.created_at, p.amount, p.seats "
            "FROM reservations r "
            "LEFT JOIN payments p ON r.payment_id = p.id "
            "WHERE r.user_id = ? "
            "ORDER BY r.id DESC",
            (user_id,),
        ).fetchall()
        for row in rows:
            seats_data = json.loads(row["seats"]) if row["seats"] else []
            tickets.append({
                "ticket_code": row["ticket_code"],
                "status": row["status"],
                "created_at": row["created_at"],
                "amount": row["amount"],
                "seats": seats_data,
                "event_title": "EventHub Etkinliği",
                "venue_name": "Ana Salon",
            })
    return render_template("tickets/my_tickets.html", tickets=tickets)


@bp.post("/purchase")
def purchase():
    """Bilet satın alma isteğini işler."""
    event_id = request.form.get("event_id", type=int)
    user_id = request.form.get("user_id", type=int)

    try:
        services.purchase_ticket(event_id, user_id)
    except ValueError as error:
        flash(str(error), "error")
    else:
        flash("Biletiniz başarıyla alındı , kontenjan güncellendi", "success")
    return redirect(url_for("tickets.index"))


@bp.post("/<int:ticket_id>/cancel")
def cancel_ticket(ticket_id: int):
    """Bilet iptal isteğini işler."""
    try:
        services.cancel_ticket(ticket_id)
    except ValueError as error:
        flash(str(error), "error")
    else:
        flash("Biletiniz başarıyla iptal edildi.", "success")
    return redirect(url_for("tickets.index"))
