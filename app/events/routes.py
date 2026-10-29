from flask import flash, jsonify, redirect, render_template, request, url_for

from app.accounts.security import role_required
from app.core.db import get_db
from app.events import bp, services


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


@bp.route("/venues", methods=["GET"])
def venues_list_ui():
    """Kayıtlı salonların listelendiği UI sayfası."""
    venues_list = services.get_all_venues()
    return render_template("events/venues.html", venues=venues_list)


@bp.route("/venues", methods=["POST"])
@role_required("admin")
def create_venue_api():
    """Emircan'ın geliştirdiği salon oluşturma API'si (BR-2.1). Yalnızca admin."""
    data = request.get_json(silent=True) or request.form
    ok, venue, errors = services.create_venue(
        get_db(), data.get("name"), data.get("address"), data.get("capacity")
    )
    if ok:
        return jsonify(venue), 201
    status = 409 if errors == ["Bu isimde bir salon zaten mevcut."] else 400
    return jsonify({"error": errors[0], "errors": errors}), status


@bp.route("/venues/create", methods=["GET", "POST"])
@role_required("admin")
def create_venue_ui():
    """Yeni salon oluşturma UI sayfası ve formu."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        address = request.form.get("address", "").strip()
        capacity = request.form.get("capacity", "")

        if not name or not address or not capacity:
            flash("Lütfen salon adı, adresi ve kapasitesi alanlarını eksiksiz doldurun.", "error")
            return redirect(url_for("events.create_venue_ui"))

        try:
            capacity_val = int(capacity)
            if capacity_val < 1:
                raise ValueError
        except ValueError:
            flash("Kapasite geçerli ve 1'den büyük bir sayı olmalıdır.", "error")
            return redirect(url_for("events.create_venue_ui"))

        ok, venue_or_error, errors = services.create_venue(get_db(), name, address, capacity_val)

        if ok:
            flash("Salon başarıyla kaydedildi.", "success")
            return redirect(url_for("events.venues_list_ui"))
        else:
            # Hata mesajını göster
            error_msg = errors[0] if errors else "Bir hata oluştu."
            flash(error_msg, "error")
            return redirect(url_for("events.create_venue_ui"))

    return render_template("events/create_venue.html")
