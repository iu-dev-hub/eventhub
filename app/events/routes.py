from flask import render_template
from app.events import bp

@bp.route("/")
def index():
    return render_template("events/index.html")