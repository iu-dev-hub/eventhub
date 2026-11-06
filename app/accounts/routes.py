"""Account routes and HTTP request handlers (TG-8).

Provides user registration endpoints supporting both JSON API and form payloads.
"""

from flask import Blueprint, jsonify, render_template, request, session

from app.accounts.security import (
    lockout_tracker,
    login_required,
    role_required,
)
from app.accounts.services import (
    DuplicateEmailError,
    authenticate_user,
    change_password,
    create_password_reset_token,
    get_user_by_id,
    register_user,
    reset_password_with_token,
    update_notification_preferences,
    update_user_profile,
)

bp = Blueprint("accounts", __name__, url_prefix="/accounts")


@bp.route("/", methods=["GET"])
def index():
    """Accounts module index endpoint."""
    if (
        request.accept_mimetypes.best_match(
            ["text/html", "application/json"], default="application/json"
        )
        == "text/html"
    ):
        return render_template("accounts/index.html")
    return jsonify(
        {
            "module": "accounts",
            "description": "EventHub Hesap Yönetimi Modülü",
            "endpoints": {
                "register": "/accounts/register",
                "login": "/accounts/login",
                "logout": "/accounts/logout",
                "me": "/accounts/me",
            },
        }
    ), 200


@bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration endpoint (TG-8, TG-10, TG-68, TG-70, TG-78).

    Accepts JSON or form data with 'first_name', 'last_name', 'email', 'password',
    and 'terms_accepted' fields.

    Responses:
        201 Created: Registration successful.
        400 Bad Request: Missing or invalid input fields or terms not accepted.
        409 Conflict: Email already registered (BR-1.2).
    """
    if request.method == "GET":
        return render_template("accounts/register.html")

    data = request.get_json(silent=True) or request.form

    email = data.get("email") if data else None
    password = data.get("password") if data else None
    role = data.get("role", "participant") if data else "participant"
    first_name = data.get("first_name") if data else None
    last_name = data.get("last_name") if data else None
    terms_val = data.get("terms_accepted") if data else None
    is_student_val = data.get("is_student") if data else False
    student_number = data.get("student_number") if data else None

    if not email or not str(email).strip() or not password:
        return jsonify({"error": "E-posta ve şifre zorunludur."}), 400

    if first_name is not None and not str(first_name).strip():
        return jsonify({"error": "Ad alanı zorunludur."}), 400

    if last_name is not None and not str(last_name).strip():
        return jsonify({"error": "Soyad alanı zorunludur."}), 400

    terms_accepted = False
    if terms_val in (True, "true", "on", "1", 1):
        terms_accepted = True

    if terms_val is not None and not terms_accepted:
        return jsonify({"error": "Kullanım Koşulları kabul edilmelidir."}), 400

    is_student = is_student_val in (True, "true", "on", "1", 1)

    try:
        user = register_user(
            email=str(email),
            password=str(password),
            role=str(role),
            first_name=str(first_name).strip() if first_name else "",
            last_name=str(last_name).strip() if last_name else "",
            terms_accepted=terms_accepted if terms_val is not None else True,
            is_student=is_student,
            student_number=str(student_number).strip() if student_number else None,
        )
        return jsonify(
            {
                "message": "Kullanıcı kaydı başarıyla tamamlandı.",
                "user": user,
            }
        ), 201

    except DuplicateEmailError as e:
        return jsonify({"error": str(e)}), 409

    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/login", methods=["GET", "POST"])
def login():
    """User authentication and login endpoint (TG-50, TG-51, TG-70, PB-02).

    Accepts JSON or form data with 'email' and 'password' fields.
    On successful authentication, stores user_id and email in Flask session.

    Responses:
        200 OK: Authentication successful, user session created.
        400 Bad Request: Missing email or password fields.
        401 Unauthorized: Invalid email or password.
    """
    if request.method == "GET":
        return render_template("accounts/login.html")

    data = request.get_json(silent=True) or request.form

    email = data.get("email") if data else None
    password = data.get("password") if data else None

    if not email or not str(email).strip() or not password or not str(password).strip():
        return jsonify({"error": "E-posta ve şifre zorunludur."}), 400

    email_str = str(email).strip().lower()

    # TG-53: Brute-force hesap kilitleme kontrolü
    is_locked, remaining_seconds = lockout_tracker.is_locked(email_str)
    if is_locked:
        return jsonify(
            {
                "error": "Çok sayıda başarısız giriş denemesi. Hesabınız geçici olarak kilitlendi.",
                "remaining_seconds": remaining_seconds,
            }
        ), 429

    try:
        user = authenticate_user(email=email_str, password=str(password))
        # Başarılı girişte hatalı deneme sayacı sıfırlanır (TG-53)
        lockout_tracker.reset(email_str)

        # TG-51: Flask session altyapısı ile oturum başlatma
        session.clear()
        session["user_id"] = user["id"]
        session["user_email"] = user["email"]
        session["user_role"] = user["role"]
        session["user_name"] = (
            f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user["email"]
        )

        remember_me = data.get("remember_me") if data else False
        if remember_me in (True, "true", "on", "1", 1):
            session.permanent = True

        return jsonify(
            {
                "message": "Giriş başarılı.",
                "user": user,
            }
        ), 200

    except ValueError as e:
        count, is_now_locked = lockout_tracker.record_failed_attempt(email_str)
        if is_now_locked:
            return jsonify(
                {
                    "error": (
                        "Çok sayıda başarısız giriş denemesi. "
                        "Hesabınız 15 dakika süreyle geçici olarak kilitlendi."
                    ),
                    "remaining_seconds": 900,
                }
            ), 429

        return jsonify(
            {
                "error": str(e),
                "remaining_attempts": max(0, 5 - count),
            }
        ), 401


@bp.route("/logout", methods=["GET", "POST"])
def logout():
    """User logout endpoint (TG-51, TG-69, PB-02).

    Clears the current user session.

    Responses:
        200 OK: Session successfully terminated.
    """
    if request.method == "GET":
        return render_template("accounts/logout_confirm.html")
    session.clear()
    return jsonify({"message": "Oturum başarıyla kapatıldı."}), 200


@bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    """Returns the currently logged in user from session (TG-51, TG-54, TG-72).

    Responses:
        200 OK: User is authenticated.
        401 Unauthorized: No active session.
    """
    user_id = session.get("user_id")
    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return jsonify({"error": "Kullanıcı bulunamadı."}), 401

    return jsonify(
        {
            "user": {
                "id": user["id"],
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "email": user["email"],
                "role": user["role"],
                "is_student": bool(user.get("is_student", False)),
                "student_number": user.get("student_number"),
                "notify_email": bool(user.get("notify_email", True)),
                "avatar_url": user.get("avatar_url"),
                "created_at": str(user.get("created_at", "")),
            }
        }
    ), 200


@bp.route("/admin/status", methods=["GET"])
@role_required("admin")
def admin_status():
    """Admin-only protected endpoint to verify role-based authorization (TG-54).

    Responses:
        200 OK: Admin authenticated.
        401 Unauthorized: Not logged in.
        403 Forbidden: Logged in but not an admin.
    """
    return jsonify(
        {
            "status": "ok",
            "message": "Yönetici paneli erişimi onaylandı.",
        }
    ), 200


@bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    """Temporary accounts welcome dashboard (TG-71, PB-04)."""
    user_id = session.get("user_id")
    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return jsonify({"error": "Kullanıcı bulunamadı."}), 401
    if (
        request.accept_mimetypes.best_match(["text/html", "application/json"], default="text/html")
        == "text/html"
    ):
        return render_template("accounts/dashboard.html", user=user)
    return jsonify({"user": user, "message": "Hoş geldiniz."}), 200


@bp.route("/guest", methods=["GET"])
def guest():
    """Guest / unregistered user exploration screen (TG-77, PB-10)."""
    if (
        request.accept_mimetypes.best_match(["text/html", "application/json"], default="text/html")
        == "text/html"
    ):
        return render_template("accounts/guest.html")
    return jsonify(
        {
            "status": "guest",
            "message": "Misafir kullanıcı modu. Etkinlikleri keşfedebilirsiniz.",
            "explore_url": "/events",
        }
    ), 200


@bp.route("/profile", methods=["GET"])
@login_required
def profile():
    """User profile screen (TG-72, PB-05)."""
    user_id = session.get("user_id")
    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return jsonify({"error": "Kullanıcı bulunamadı."}), 401
    if (
        request.accept_mimetypes.best_match(["text/html", "application/json"], default="text/html")
        == "text/html"
    ):
        return render_template("accounts/profile.html", user=user)
    return jsonify({"user": user}), 200


@bp.route("/profile/edit", methods=["POST"])
@login_required
def profile_edit():
    """User profile update endpoint (TG-73, PB-06). Only allows first_name and last_name updates."""
    user_id = session.get("user_id")
    data = request.get_json(silent=True) or request.form

    first_name = data.get("first_name") if data else None
    last_name = data.get("last_name") if data else None

    if not first_name or not str(first_name).strip():
        return jsonify({"error": "Ad alanı zorunludur."}), 400
    if not last_name or not str(last_name).strip():
        return jsonify({"error": "Soyad alanı zorunludur."}), 400

    try:
        updated = update_user_profile(user_id, str(first_name), str(last_name))
        session["user_name"] = (
            f"{updated.get('first_name', '')} {updated.get('last_name', '')}".strip()
        )
        return jsonify(
            {
                "message": "Profil başarıyla güncellendi.",
                "user": updated,
            }
        ), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/settings", methods=["GET"])
@login_required
def settings():
    """User account settings screen (TG-74, PB-07)."""
    user_id = session.get("user_id")
    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return jsonify({"error": "Kullanıcı bulunamadı."}), 401
    if (
        request.accept_mimetypes.best_match(["text/html", "application/json"], default="text/html")
        == "text/html"
    ):
        return render_template("accounts/settings.html", user=user)
    return jsonify({"user": user, "settings": ["profile", "security", "notifications"]}), 200


@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password_route():
    """User password change endpoint (TG-75, PB-08)."""
    if request.method == "GET":
        return render_template("accounts/change_password.html")

    user_id = session.get("user_id")
    data = request.get_json(silent=True) or request.form

    current_password = data.get("current_password") if data else None
    new_password = data.get("new_password") if data else None

    if not current_password or not new_password:
        return jsonify({"error": "Mevcut şifre ve yeni şifre zorunludur."}), 400

    try:
        change_password(user_id, str(current_password), str(new_password))
        return jsonify({"message": "Şifreniz başarıyla değiştirildi."}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Password reset request endpoint (TG-76, PB-09, PO decision 1)."""
    if request.method == "GET":
        return render_template("accounts/forgot_password.html")

    data = request.get_json(silent=True) or request.form
    email = data.get("email") if data else None

    if not email or not str(email).strip():
        return jsonify({"error": "E-posta adresi zorunludur."}), 400

    token = create_password_reset_token(str(email))
    resp = {
        "message": (
            "Şifre sıfırlama bağlantısı e-posta adresinize gönderildi. "
            "Lütfen gelen kutunuzu kontrol edin."
        ),
        "simulated_notice": (
            "E-posta servisi bulunmadığından demo ortamı için sıfırlama tokenı üretildi."
        ),
    }
    if token:
        resp["reset_token"] = token
        resp["reset_url"] = f"/accounts/reset-password/{token}"

    return jsonify(resp), 200


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Password reset submission endpoint (TG-76, PB-09)."""
    if request.method == "GET":
        return render_template("accounts/reset_password.html", token=token)

    data = request.get_json(silent=True) or request.form
    new_password = data.get("new_password") if data else None

    if not new_password:
        return jsonify({"error": "Yeni şifre zorunludur."}), 400

    try:
        reset_password_with_token(token, str(new_password))
        return jsonify(
            {"message": "Şifreniz başarıyla sıfırlandı. Yeni şifrenizle giriş yapabilirsiniz."}
        ), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/terms", methods=["GET"])
def terms():
    """Terms of Service legal demo draft page (TG-79, PB-12)."""
    return render_template("accounts/terms.html")


@bp.route("/privacy", methods=["GET"])
def privacy():
    """Privacy Policy legal demo draft page (TG-79, PB-12)."""
    return render_template("accounts/privacy.html")


@bp.route("/kvkk", methods=["GET"])
def kvkk():
    """KVKK Disclosure legal demo draft page (TG-79, PB-12)."""
    return render_template("accounts/kvkk.html")


@bp.route("/preferences", methods=["POST"])
@login_required
def preferences():
    """Notification preferences update endpoint (TG-81, PB-14)."""
    user_id = session.get("user_id")
    data = request.get_json(silent=True) or request.form
    notify_email = data.get("notify_email", True) if data else True
    is_notify = notify_email in (True, "true", "on", "1", 1)

    try:
        update_notification_preferences(user_id, is_notify)
        return jsonify({"message": "Bildirim tercihleriniz güncellendi."}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
