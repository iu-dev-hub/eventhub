"""SQLite database connection and initialization.

Veritabanını oluşturmak için:
    flask --app app init-db
"""

import sqlite3
from pathlib import Path

import click
from flask import Flask, current_app, g
from flask.cli import with_appcontext

SCHEMA_FILE = Path(__file__).with_name("schema.sql")


def get_db() -> sqlite3.Connection:
    """İstek boyunca kullanılacak veritabanı bağlantısını döndürür."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _tickets_has_event_fk(db: sqlite3.Connection) -> bool:
    return any(r["table"] == "events" for r in db.execute("PRAGMA foreign_key_list(tickets)"))


def _migrate_tickets_event_fk(db: sqlite3.Connection) -> None:
    """Eski veritabanlarında tickets.event_id -> events.id FK'sini ekler (TG-117).

    schema.sql'deki CREATE TABLE IF NOT EXISTS mevcut tabloyu değiştirmediğinden, FK'siz
    oluşturulmuş tickets tablosu yeniden kurulur. Var olan biletler korunur. Geçerli bir
    etkinliğe bağlı olmayan (yetim) bilet varsa işlem geri alınır ve RuntimeError fırlatılır.
    Tablo yapısı schema.sql'deki tickets tanımıyla aynı tutulmalıdır.
    """
    if _tickets_has_event_fk(db):
        return
    db.commit()
    db.execute("PRAGMA foreign_keys = OFF")  # işlem dışında olmalı
    try:
        db.execute("BEGIN")
        db.execute(
            """CREATE TABLE tickets_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'reserved',
                qr_code TEXT UNIQUE,
                created_at TEXT NOT NULL,
                FOREIGN KEY (event_id) REFERENCES events(id)
            )"""
        )
        db.execute(
            "INSERT INTO tickets_new (id, event_id, user_id, status, qr_code, created_at) "
            "SELECT id, event_id, user_id, status, qr_code, created_at FROM tickets"
        )
        db.execute("DROP TABLE tickets")
        db.execute("ALTER TABLE tickets_new RENAME TO tickets")
        orphans = db.execute("PRAGMA foreign_key_check(tickets)").fetchall()
        if orphans:
            db.execute("ROLLBACK")
            raise RuntimeError(
                f"tickets tablosunda geçerli bir etkinliğe bağlı olmayan {len(orphans)} kayıt var; "
                "FK eklenemedi. Bu biletleri düzeltin/silin ve init-db'yi tekrar çalıştırın."
            )
        db.execute("COMMIT")
    except Exception:
        if db.in_transaction:
            db.execute("ROLLBACK")
        raise
    finally:
        db.execute("PRAGMA foreign_keys = ON")


def init_db() -> None:
    """Şemayı oluşturur; tekrar çalıştırılabilir ve mevcut tabloları/verileri korur."""
    db = get_db()
    db.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    db.commit()
    _migrate_tickets_event_fk(db)


@click.command("init-db")
@with_appcontext
def init_db_command() -> None:
    init_db()
    click.echo("Database initialized.")


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
