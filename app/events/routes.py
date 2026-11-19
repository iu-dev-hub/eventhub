from flask import flash, g, jsonify, redirect, render_template, request, session, url_for

from app.accounts.security import login_required, role_required
from app.core.db import get_db
from app.events import bp, services


@bp.route("/")
def index():
    user_id = session.get("user_id")
    user_role = session.get("user_role")
    db = get_db()

    query = (
        "SELECT e.id, e.title, e.category, e.venue_id, e.start_time, e.end_time, "
        "e.capacity, e.price, e.status, e.organizer_id, v.name AS venue_name "
        "FROM events e "
        "LEFT JOIN venues v ON e.venue_id = v.id "
    )

    if user_role == "organizer" and user_id:
        rows = db.execute(
            f"{query} WHERE e.organizer_id = ? ORDER BY e.id DESC", (user_id,)
        ).fetchall()
    elif user_role == "admin":
        rows = db.execute(f"{query} ORDER BY e.id DESC").fetchall()
    else:
        rows = db.execute(f"{query} WHERE e.status = 'published' ORDER BY e.id DESC").fetchall()

    events = [dict(r) for r in rows]
    return render_template("events/index.html", events=events)


def _forbidden_unless_approved_organizer(action="oluşturmak"):
    """BR-1.5: yalnızca rol yetmez, yönetici onayı da gerekir. Yetkisizse 403 döner."""
    if not services.is_approved_organizer(g.user_id, get_db()):
        return jsonify(
            {"error": f"Etkinlik {action} için yönetici onaylı organizatör olmalısınız."}
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


@bp.route("/<int:event_id>/publish", methods=["POST"])
@role_required("organizer")
def publish(event_id):
    """Taslak etkinliği yayınlar (TG-174, TG-175, PB-04; BR-1.5, BR-2.2, BR-2.3, BR-2.4)."""
    is_ui_request = (
        request.headers.get("Accept", "").find("text/html") != -1
        or bool(request.form)
        or not request.is_json
    )

    denied = _forbidden_unless_approved_organizer(action="yayınlamak")
    if denied:
        if is_ui_request:
            flash("Etkinlik yayınlamak için yönetici onaylı organizatör olmalısınız.", "error")
            return redirect(url_for("events.index"))
        return denied

    db = get_db()
    event = services.get_event(db, event_id)
    if event is None:
        if is_ui_request:
            flash("Etkinlik bulunamadı.", "error")
            return redirect(url_for("events.index"))
        return jsonify({"error": "Etkinlik bulunamadı."}), 404

    if event["organizer_id"] != g.user_id:
        msg = "Etkinliği yayınlamak için yönetici onaylı etkinlik sahibi organizatör olmalısınız."
        if is_ui_request:
            flash(msg, "error")
            return redirect(url_for("events.index"))
        return jsonify({"error": msg}), 403

    # İş kuralları kontrolleri (BR-2.2, BR-2.3, BR-2.4)
    validation_errors = []
    if not str(event.get("title") or "").strip():
        validation_errors.append("Etkinlik başlığı zorunludur.")
    if not str(event.get("category") or "").strip():
        validation_errors.append("Etkinlik kategorisi zorunludur.")

    venue = db.execute(
        "SELECT id, name, capacity FROM venues WHERE id = ?", (event["venue_id"],)
    ).fetchone()
    if venue and event["capacity"] > venue["capacity"]:
        v_cap = venue["capacity"]
        validation_errors.append(
            f"Etkinlik kapasitesi ({event['capacity']}), salon kapasitesini ({v_cap}) aşamaz."
        )

    start_dt = services._parse_form_datetime(event["start_time"])
    end_dt = services._parse_form_datetime(event["end_time"])
    if start_dt and end_dt:
        conflicts = db.execute(
            "SELECT id, title, start_time, end_time FROM events "
            "WHERE venue_id = ? AND status = 'published' AND id != ?",
            (event["venue_id"], event_id),
        ).fetchall()
        for other in conflicts:
            o_start = services._parse_form_datetime(other["start_time"])
            o_end = services._parse_form_datetime(other["end_time"])
            if o_start and o_end and start_dt < o_end and end_dt > o_start:
                validation_errors.append(
                    "Aynı salonda zamanı çakışan başka bir etkinlik bulunmaktadır "
                    f"({other['title']})."
                )
                break

    if validation_errors:
        if is_ui_request:
            for err in validation_errors:
                flash(err, "error")
            return redirect(url_for("events.index"))
        status = 409 if any("çakışan" in e.lower() for e in validation_errors) else 400
        return jsonify({"error": validation_errors[0], "errors": validation_errors}), status

    try:
        ok, published_event, errors = services.publish_event(db, event_id, organizer_id=g.user_id)
    except services.EventPermissionError as exc:
        if is_ui_request:
            flash(str(exc), "error")
            return redirect(url_for("events.index"))
        return jsonify({"error": str(exc)}), 403

    if not ok:
        if is_ui_request:
            for err in errors:
                flash(err, "error")
            return redirect(url_for("events.index"))
        status_code = 409 if any("taslak" in e.lower() for e in errors) else 400
        return jsonify({"error": errors[0], "errors": errors}), status_code

    msg = f"Etkinlik başarıyla yayınlandı. (Etkinlik No: {published_event['id']})"
    flash(msg, "success")
    if is_ui_request:
        return redirect(url_for("events.index"))
    return jsonify({"message": msg, "event": published_event}), 200


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
