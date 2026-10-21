"""EventHub - application factory.

Bu, çalışan en küçük uygulamadır. Modüller (accounts, events, tickets,
payments) Sprint 1'de ekipler tarafından eklenecektir.
Nasıl yapılacağı: CONTRIBUTING.md, "Yeni modül ekleme" bölümü.
"""

import os

from flask import Flask, jsonify, render_template

from app.core import db

VERSION = "0.1.0"


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("EVENTHUB_SECRET_KEY", "dev-secret-key"),
        DATABASE=os.path.join(app.instance_path, "eventhub.sqlite"),
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    # --- Module blueprints -------------------------------------------------
    # Her ekip Sprint 1'de kendi modülünü buraya kaydeder (alfabetik sırayla):
    #
    #   from app.tickets import bp as tickets_bp
    #   app.register_blueprint(tickets_bp)
    # -----------------------------------------------------------------------
    from app.accounts import bp as accounts_bp

    app.register_blueprint(accounts_bp)

    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/health")
    def health():
        """Sistemin ayakta olup olmadığını gösterir (smoke test için)."""
        return jsonify(status="ok", version=VERSION)

    return app
