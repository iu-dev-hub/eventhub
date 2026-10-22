from flask import render_template, request, flash, redirect, url_for
from app.events import bp
from app.events import services

@bp.route("/")
def index():
    return render_template("events/index.html")

@bp.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        # TG-21'den gelen tüm form verilerini alıyoruz
        title = request.form.get("title", "")
        category = request.form.get("category", "")
        venue = request.form.get("venue", "")
        start_time = request.form.get("start_time", "")
        end_time = request.form.get("end_time", "")
        capacity = request.form.get("capacity", "")
        price = request.form.get("price", "")

        # TG-22'deki doğrulama servisine tüm verileri gönderiyoruz
        is_valid, messages = services.validate_event_creation(
            title, category, venue, start_time, end_time, capacity, price
        )

        # Doğrulama sonuçlarını (başarılı/hata) flash mesajı olarak basıyoruz
        for message in messages:
            flash_category = "success" if is_valid else "error"
            flash(message, flash_category)

        # Başarılıysa ana sayfaya, hatalıysa tekrar form sayfasına yönlendiriyoruz
        if is_valid:
            return redirect(url_for("events.index"))
        else:
            return redirect(url_for("events.create"))

    return render_template("events/create.html")