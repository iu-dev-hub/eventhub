from flask import Blueprint

bp = Blueprint("tickets", __name__, url_prefix="/tickets")

from app.tickets import routes