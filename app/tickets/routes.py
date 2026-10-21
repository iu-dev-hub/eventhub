from flask import Blueprint, flash, redirect, render_template, url_for
from app.tickets import services

# Bilet modülü için Blueprint tanımı
bp = Blueprint("tickets", __name__, url_prefix="/tickets")

@bp.route("/")
def index():
    return render_template("tickets/index.html")

@bp.post("/<int:ticket_id>/cancel")
def cancel_ticket(ticket_id: int):
    """Bilet iptal isteğini işler."""
    try:
        services.cancel_ticket(ticket_id)
    except ValueError as error:
        # Hata durumunda mesaj gösterimi
        flash(str(error), "error")
    else:
        flash("Biletiniz başarıyla iptal edildi.", "success")
    return redirect(url_for("tickets.index"))