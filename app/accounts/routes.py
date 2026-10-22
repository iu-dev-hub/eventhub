"""Account routes and HTTP request handlers (TG-8).

Provides user registration endpoints supporting both JSON API and form payloads.
"""

from flask import Blueprint, jsonify, render_template, request, session

from app.accounts.services import (
    DuplicateEmailError,
    authenticate_user,
    get_user_by_id,
    register_user,
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
    return jsonify({
        "module": "accounts",
        "description": "EventHub Hesap Yönetimi Modülü",
        "endpoints": {
            "register": "/accounts/register",
            "login": "/accounts/login",
            "logout": "/accounts/logout",
            "me": "/accounts/me",
        }
    }), 200


@bp.route("/register", methods=["POST"])
def register():
    """User registration endpoint (TG-8, TG-10).

    Accepts JSON or form data with 'email' and 'password' fields.

    Responses:
        201 Created: Registration successful.
        400 Bad Request: Missing or invalid input fields.
        409 Conflict: Email already registered (BR-1.2).
    """
    data = request.get_json(silent=True) or request.form

    email = data.get("email") if data else None
    password = data.get("password") if data else None
    role = data.get("role", "participant") if data else "participant"

    if not email or not str(email).strip() or not password:
        return jsonify({
            "error": "E-posta ve şifre zorunludur."
        }), 400

    try:
        user = register_user(email=str(email), password=str(password), role=str(role))
        return jsonify({
            "message": "Kullanıcı kaydı başarıyla tamamlandı.",
            "user": user,
        }), 201

    except DuplicateEmailError as e:
        return jsonify({
            "error": str(e)
        }), 409

    except ValueError as e:
        return jsonify({
            "error": str(e)
        }), 400


@bp.route("/login", methods=["POST"])
def login():
    """User authentication and login endpoint (TG-50, TG-51, PB-02).

    Accepts JSON or form data with 'email' and 'password' fields.
    On successful authentication, stores user_id and email in Flask session.

    Responses:
        200 OK: Authentication successful, user session created.
        400 Bad Request: Missing email or password fields.
        401 Unauthorized: Invalid email or password.
    """
    data = request.get_json(silent=True) or request.form

    email = data.get("email") if data else None
    password = data.get("password") if data else None

    if not email or not str(email).strip() or not password:
        return jsonify({
            "error": "E-posta ve şifre zorunludur."
        }), 400

    try:
        user = authenticate_user(email=str(email), password=str(password))
        # TG-51: Flask session altyapısı ile oturum başlatma
        session.clear()
        session["user_id"] = user["id"]
        session["user_email"] = user["email"]
        session["user_role"] = user["role"]

        return jsonify({
            "message": "Giriş başarılı.",
            "user": user,
        }), 200

    except ValueError as e:
        return jsonify({
            "error": str(e)
        }), 401


@bp.route("/logout", methods=["POST"])
def logout():
    """User logout endpoint (TG-51, PB-02).

    Clears the current user session.

    Responses:
        200 OK: Session successfully terminated.
    """
    session.clear()
    return jsonify({
        "message": "Oturum başarıyla kapatıldı."
    }), 200


@bp.route("/me", methods=["GET"])
def get_current_user():
    """Returns the currently logged in user from session (TG-51).

    Responses:
        200 OK: User is authenticated.
        401 Unauthorized: No active session.
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "error": "Oturum açılmamış."
        }), 401

    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return jsonify({
            "error": "Kullanıcı bulunamadı."
        }), 401

    return jsonify({
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
        }
    }), 200
