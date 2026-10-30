from flask import Blueprint

bp = Blueprint("events", __name__, url_prefix="/events")

# Ruff'ın E402 ve F401 uyarılarını susturmak için # noqa kullanıyoruz
from app.events import routes  # noqa: E402, F401
