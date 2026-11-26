from flask import flash, g, jsonify, redirect, render_template, request, session, url_for

from app.accounts.security import role_required
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
            f"{query} WHERE e.organizer_id = ? OR e.status = 'published' ORDER BY e.id DESC",
            (user_id,),
        ).fetchall()
    elif user_role == "admin":
        rows = db.execute(f"{query} ORDER BY e.id DESC").fetchall()
    else:
        rows = db.execute(f"{query} WHERE e.status = 'published' ORDER BY e.id DESC").fetchall()

    events = [dict(r) for r in rows]
    return render_template(
        "events/index.html",
        events=events,
        current_user_id=user_id,
        user_role=user_role,
    )


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
def event_detail(event_id):
    """Etkinlik detayını rol bazlı görünürlük ve içerik pazarlığıyla HTML/JSON döner (TG-193)."""
    user_id = session.get("user_id")
    user_role = session.get("user_role")
    event = services.get_event_detail(
        get_db(),
        event_id,
        user_id=user_id,
        user_role=user_role,
    )
    is_html = _wants_html()
    if event is None:
        if is_html:
            return render_template("events/not_found.html"), 404
        return jsonify({"error": "Etkinlik bulunamadı."}), 404
    if is_html:
        return (
            render_template(
                "events/detail.html",
                event=event,
                user_role=user_role,
                current_user_id=user_id,
            ),
            200,
        )
    return jsonify(event), 200


def _wants_html():
    """İsteğin HTML yanıtı mı yoksa JSON yanıtı mı tercih ettiğini belirler."""
    if not request.headers.get("Accept", "").strip():
        return False
    accept = request.accept_mimetypes
    html_q = max(accept.quality("text/html"), accept.quality("application/xhtml+xml"))
    json_q = accept.quality("application/json")
    if html_q <= 0:
        return False
    if html_q != json_q:
        return html_q > json_q
    # Eşit q değerinde (örn. "text/html,*/*") medya türü özgüllüğünü Werkzeug belirler;
    # aynı özgüllükte JSON ilk sırada olduğu için varsayılan JSON kalır.
    best = accept.best_match(["application/json", "text/html", "application/xhtml+xml"])
    return best in ("text/html", "application/xhtml+xml")


@bp.route("/<int:event_id>/publish", methods=["POST"])
@role_required("organizer")
def publish(event_id):
    """Taslak etkinliği yayınlar (TG-174, PB-04; BR-1.5, BR-2.2, BR-2.3, BR-2.4)."""
    is_html = _wants_html()
    db = get_db()
    try:
        ok, event, errors = services.publish_event(db, event_id, g.user_id)
    except services.EventPermissionError as exc:
        if is_html:
            flash(str(exc), "error")
            return redirect(url_for("events.index"))
        return jsonify({"error": str(exc)}), 403

    if not ok:
        if errors and errors[0] == "Etkinlik bulunamadı.":
            if is_html:
                flash(errors[0], "error")
                return redirect(url_for("events.index"))
            return jsonify({"error": errors[0], "errors": errors}), 404
        status_code = (
            409
            if any(
                "başka bir etkinlik var" in e.lower()
                or "çakış" in e.lower()
                or "zaten yayınlanmış" in e.lower()
                or "yalnızca taslak" in e.lower()
                for e in errors
            )
            else 400
        )
        if is_html:
            for err in errors:
                flash(err, "error")
            return redirect(
                url_for("events.event_detail", event_id=event_id)
                if services.get_event(db, event_id)
                else url_for("events.index")
            )
        return jsonify({"error": errors[0], "errors": errors}), status_code

    msg = f"Etkinlik başarıyla yayınlandı. (Etkinlik No: {event['id']})"
    flash(msg, "success")
    if is_html:
        return redirect(url_for("events.index"))
    return jsonify({"message": msg, "event": event}), 200


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
