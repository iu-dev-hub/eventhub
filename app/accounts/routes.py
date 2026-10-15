"""Account routes and HTTP request handlers (TG-8).

Provides user registration endpoints supporting both JSON API and form payloads.
"""

from flask import Blueprint, jsonify, render_template, request

from app.accounts.services import DuplicateEmailError, register_user

bp = Blueprint("accounts", __name__, url_prefix="/accounts")


@bp.route("/", methods=["GET"])
def index():
    """Accounts module index endpoint."""
    if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
        return render_template("accounts/index.html")
    return jsonify({
        "module": "accounts",
        "description": "EventHub Hesap Yönetimi Modülü",
        "endpoints": {
            "register": "/accounts/register"
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
