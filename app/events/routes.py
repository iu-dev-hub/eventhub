from flask import flash, g, jsonify, redirect, render_template, request, url_for

from app.accounts.security import login_required, role_required
from app.core.db import get_db
from app.events import bp, services


@bp.route("/")
def index():
    return render_template("events/index.html")


def _forbidden_unless_approved_organizer():
    """BR-1.5: yalnızca rol yetmez, yönetici onayı da gerekir. Yetkisizse 403 döner."""
    if not services.is_approved_organizer(g.user_id, get_db()):
        return jsonify(
            {"error": "Etkinlik oluşturmak için yönetici onaylı organizatör olmalısınız."}
        ), 403
    return None


@bp.route("/create", methods=["GET", "POST"])
@role_required("organizer")
def create():
    """Taslak etkinlik formu (TG-119) ve kaydı (TG-118, TG-121). BR-1.5, BR-2.2, BR-2.3."""
    denied = _forbidden_unless_approved_organizer()
    if denied:
        return denied

    if request.method == "POST":
        try:
            # organizer_id istekten değil oturumdan alınır (g.user_id).
            is_valid, event, messages = services.create_draft_event(
                get_db(),
                g.user_id,
                request.form.get("title", ""),
                request.form.get("category", ""),
                "",
                request.form.get("start_time", ""),
                request.form.get("end_time", ""),
                request.form.get("capacity", ""),
                request.form.get("price", ""),
                venue_id=request.form.get("venue_id", ""),
            )
        except services.EventPermissionError as exc:
            return jsonify({"error": str(exc)}), 403

        if is_valid:
            flash(f"Taslak etkinlik kaydedildi. (Etkinlik No: {event['id']})", "success")
            return redirect(url_for("events.index"))

        for message in messages:
            flash(message, "error")
        return redirect(url_for("events.create"))

    return render_template("events/create.html", venues=services.get_all_venues())


@bp.route("/<int:event_id>", methods=["GET"])
@login_required
def event_detail(event_id):
    """Kaydedilmiş etkinliği JSON döndürür; taslaklar yalnızca sahibine ve admine açıktır."""
    event = services.get_event(get_db(), event_id)
    if event is None:
        return jsonify({"error": "Etkinlik bulunamadı."}), 404
    if event["status"] != "published" and not (
        g.user_role == "admin" or event["organizer_id"] == g.user_id
    ):
        # Taslağın varlığını sızdırmamak için 404 döndürülür.
        return jsonify({"error": "Etkinlik bulunamadı."}), 404
    return jsonify(event)


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
            # Emircan'ın isteğine göre hata mesajı güncellendi
            flash("Kapasite en az 1 olan geçerli bir tam sayı olmalıdır.", "error")
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
