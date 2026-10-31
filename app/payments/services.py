"""Koltuk kilitleme ve ödeme iş kuralları (SQLite üzerinden)."""
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from app.core.db import get_db

# Koltuk kilidi süresi (dakika)
LOCK_MINUTES = 10

# Geçerli kart numarası uzunluğu (BR-4.3)
CARD_LENGTH = 16

# İstekte etkinlik numarası gelmezse kullanılır
DEFAULT_EVENT_ID = 1

# Eski kabul kriteri: log dosyası da oluşmaya devam eder
LOG_FILE = Path(__file__).resolve().parents[2] / "payment_logs.json"


def _iso(moment):
    """Tarihleri ISO metin olarak saklarız; metin olarak da doğru sıralanır."""
    return moment.isoformat(timespec="seconds")


def _release_expired(db, now):
    """Süresi dolan kilitleri serbest bırakır."""
    db.execute(
        "UPDATE seats SET status = 'available', locked_until = NULL "
        "WHERE status = 'locked' AND locked_until <= ?",
        (_iso(now),),
    )


def lock_seats(seats, event_id=DEFAULT_EVENT_ID, now=None):
    """Koltukları 10 dk kilitler.

    Başarılıysa (True, None, bitiş_zamanı), çakışma varsa
    (False, çakışan_koltuklar, None) döner.
    """
    now = now or datetime.now()
    expires = now + timedelta(minutes=LOCK_MINUTES)
    db = get_db()

    # BEGIN IMMEDIATE: yazma kilidini hemen alır, iki istek aynı anda
    # aynı koltuğu kilitleyemez (eski _mutex'in yerini alır).
    db.execute("BEGIN IMMEDIATE")
    try:
        _release_expired(db, now)

        taken = []
        for code in seats:
            # Koltuk kaydı yoksa oluştur, varsa dokunma
            db.execute(
                "INSERT OR IGNORE INTO seats (event_id, seat_code) VALUES (?, ?)",
                (event_id, code),
            )
            row = db.execute(
                "SELECT status FROM seats WHERE event_id = ? AND seat_code = ?",
                (event_id, code),
            ).fetchone()
            if row["status"] != "available":
                taken.append(code)

        if taken:
            # Bir koltuk bile doluysa hiçbirini kilitleme: işlemi geri al
            db.rollback()
            return False, taken, None

        for code in seats:
            db.execute(
                "UPDATE seats SET status = 'locked', locked_until = ? "
                "WHERE event_id = ? AND seat_code = ?",
                (_iso(expires), event_id, code),
            )
        db.commit()
        return True, None, expires
    except sqlite3.Error:
        # Veritabanı hatasında yarım işlem kalmasın, hata yukarı iletilir
        db.rollback()
        raise


def unlock_seats(seats, event_id=DEFAULT_EVENT_ID, now=None):
    """Kilitli koltukları manuel olarak serbest bırakır.

    Yalnızca 'locked' durumdaki koltuklar serbest bırakılır;
    'sold' veya 'available' koltuklar değiştirilmez.

    Başarılıysa (True, serbest_bırakılan_koltuklar) döner.
    Hiç 'locked' koltuk bulunamazsa (False, []) döner.
    """
    now = now or datetime.now()
    db = get_db()

    db.execute("BEGIN IMMEDIATE")
    try:
        # Önce süresi dolan kilitleri serbest bırak
        _release_expired(db, now)

        released = []
        for code in seats:
            row = db.execute(
                "SELECT status FROM seats WHERE event_id = ? AND seat_code = ?",
                (event_id, code),
            ).fetchone()
            # Yalnızca 'locked' olan koltuklar serbest bırakılır
            if row is not None and row["status"] == "locked":
                db.execute(
                    "UPDATE seats SET status = 'available', locked_until = NULL "
                    "WHERE event_id = ? AND seat_code = ?",
                    (event_id, code),
                )
                released.append(code)

        db.commit()
        if released:
            return True, released
        return False, []
    except sqlite3.Error:
        db.rollback()
        raise

 feature/TG-133-add-seats-status-endpoint
def get_seats_status(seats=None, event_id=DEFAULT_EVENT_ID, now=None):
    """Koltukların güncel durumlarını döner.

    Süresi dolan kilitler varsa sorgulamadan önce serbest bırakılır.
    `seats` None ise ilgili etkinliğe ait kayıtlı tüm koltuklar döner.
    `seats` liste ise listedeki her koltuk (kayıt yoksa 'available' olarak eklenerek) döner.
    """
    now = now or datetime.now()
    db = get_db()

    db.execute("BEGIN IMMEDIATE")
    try:
        _release_expired(db, now)

        if seats is not None:
            for code in seats:
                db.execute(
                    "INSERT OR IGNORE INTO seats (event_id, seat_code) VALUES (?, ?)",
                    (event_id, code),
                )
            placeholders = ",".join("?" for _ in seats)
            rows = db.execute(
                f"SELECT seat_code, status, locked_until FROM seats "
                f"WHERE event_id = ? AND seat_code IN ({placeholders}) "
                f"ORDER BY seat_code",
                [event_id, *seats],
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT seat_code, status, locked_until FROM seats "
                "WHERE event_id = ? ORDER BY seat_code",
                (event_id,),
            ).fetchall()

        db.commit()
        return [
            {
                "seat_code": row["seat_code"],
                "status": row["status"],
                "locked_until": row["locked_until"],
            }
            for row in rows
        ]
    except sqlite3.Error:
        db.rollback()
        raise



def _decide_payment(db, card_number, seats, event_id):
    """Ödeme kurallarını uygular, (success, message) döner.

    Başarılıysa koltukları "sold" yapar. Commit işini çağıran yapar.
    """
    # BR-4.3: kart tam 16 haneli ve yalnızca rakam olmalı.
    if (
        len(card_number) != CARD_LENGTH
        or not card_number.isascii()
        or not card_number.isdigit()
    ):
        return False, "Geçersiz kart"

    sold = []
    not_locked = []
    for code in seats:
        row = db.execute(
            "SELECT status FROM seats WHERE event_id = ? AND seat_code = ?",
            (event_id, code),
        ).fetchone()
        if row is not None and row["status"] == "sold":
            sold.append(code)
        elif row is None or row["status"] != "locked":
            not_locked.append(code)

    # Satılmış koltuk ikinci kez satılamaz
    if sold:
        return False, "Koltuk zaten satılmış"
    # Ödemeden önce koltuk kilitli olmalı
    if not_locked:
        return False, "Koltuk kilitli değil"

    if card_number.endswith("4242"):
        # Başarılı ödeme: kilitli koltuklar "dolu" olur
        for code in seats:
            db.execute(
                "UPDATE seats SET status = 'sold', locked_until = NULL "
                "WHERE event_id = ? AND seat_code = ?",
                (event_id, code),
            )
        return True, "Ödeme başarılı"

    if card_number.endswith("0000"):
        return False, "Yetersiz bakiye"

    # Tanımsız kartlar da reddedilir ve loglanır
    return False, "Geçersiz kart"


def process_payment(card_number, amount, seats, event_id=DEFAULT_EVENT_ID, now=None):
    """Sahte ödeme. Her deneme (başarılı/başarısız) payments tablosuna yazılır."""
    now = now or datetime.now()
    db = get_db()

    db.execute("BEGIN IMMEDIATE")
    try:
        _release_expired(db, now)
        success, message = _decide_payment(db, card_number, seats, event_id)

        # Kartın tamamını saklamayız; yalnızca son 4 hane
        last4 = card_number[-4:] if card_number.isdigit() else None
        db.execute(
            "INSERT INTO payments (amount, card_last4, success, message, seats, "
            "created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (amount, last4, int(success), message, json.dumps(seats), _iso(now)),
        )
        db.commit()
    except sqlite3.Error:
        db.rollback()
        raise

    _export_log(db)

    if success:
        return {"success": True, "ticketId": "T12345"}
    return {"success": False, "message": message}


def _export_log(db):
    """payments tablosunu payment_logs.json dosyasına yazar (eski kabul kriteri)."""
    rows = db.execute(
        "SELECT created_at, seats, success, message FROM payments ORDER BY id"
    ).fetchall()
    logs = [
        {
            "tarih": row["created_at"],
            "koltuklar": json.loads(row["seats"]),
            "success": bool(row["success"]),
            "mesaj": row["message"],
        }
        for row in rows
    ]
    LOG_FILE.write_text(
        json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8"
    )
