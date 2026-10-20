from flask import render_template

from app.tickets import bp


@bp.route("/")
def index():
    event = {
        "title": "Yazılım ve Teknoloji Etkinliği",
        "description": "Yazılım dünyasındaki yenilikleri keşfedin.",
        "date": "20 Kasım 2026",
        "location": "Iğdır Üniversitesi",
        "remaining_tickets": 50,
    }

    return render_template("tickets/index.html", event=event)