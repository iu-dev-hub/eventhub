from flask import render_template, request, flash, redirect, url_for
from app.events import bp
from app.events.services import validate_event_creation

@bp.route("/")
def index():
    return render_template("events/index.html")

@bp.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        title = request.form.get("title")
        capacity = request.form.get("capacity")
        price = request.form.get("price")

        is_valid, messages = validate_event_creation(title, capacity, price)

        for message in messages:
            category = "success" if is_valid else "error"
            flash(message, category)

        if is_valid:
            return redirect(url_for("events.index"))

    return render_template("events/create.html")