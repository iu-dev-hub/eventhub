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


def _decide_payment(db, card_number, seats, event_id):
    """Ödeme kurallarını uygular, (success, message) döner.

    Başarılıysa koltukları "sold" yapar. Commit işini çağıran yapar.
    """
    # BR-4.3: kart tam 16 haneli ve yalnızca rakam olmalı.
    if len(card_number) != CARD_LENGTH or not card_number.isascii() or not card_number.isdigit():
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


def process_payment(
    card_number,
    amount,
    seats,
    event_id=DEFAULT_EVENT_ID,
    user_id=None,
    idempotency_key=None,
    now=None,
):
    """Sahte ödeme. Her deneme (başarılı/başarısız) payments tablosuna yazılır.

    Başarılı ödemede tek bir transaction içinde reservation ve reservation_seats
    kayıtları ve bilet bilgisi oluşturulur.
    idempotency_key verilmişse ve daha önce kaydedilmişse mevcut rezervasyon döner.
    """
    now = now or datetime.now()
    db = get_db()

    db.execute("BEGIN IMMEDIATE")
    try:
        # Idempotency kontrolü: aynı anahtar varsa tekrar çekim yapma
        if idempotency_key:
            existing = db.execute(
                "SELECT r.id, r.event_id, r.ticket_code, r.created_at, p.amount, p.seats "
                "FROM reservations r "
                "JOIN payments p ON r.payment_id = p.id "
                "WHERE r.idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing:
                db.rollback()
                return {
                    "success": True,
                    "ticketId": existing["ticket_code"],
                    "ticketCode": existing["ticket_code"],
                    "reservationId": existing["id"],
                    "eventId": existing["event_id"],
                    "seats": json.loads(existing["seats"]),
                    "createdAt": existing["created_at"],
                    "idempotent": True,
                }

        _release_expired(db, now)
        success, message = _decide_payment(db, card_number, seats, event_id)

        # Kartın tamamını saklamayız; yalnızca son 4 hane
        last4 = card_number[-4:] if card_number.isdigit() else None
        cursor = db.execute(
            "INSERT INTO payments (amount, card_last4, success, message, seats, "
            "created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (amount, last4, int(success), message, json.dumps(seats), _iso(now)),
        )
        payment_id = cursor.lastrowid

        ticket_code = None
        reservation_id = None
        if success:
            ticket_code = f"T{payment_id:05d}"
            cursor_res = db.execute(
                "INSERT INTO reservations (payment_id, event_id, user_id, "
                "idempotency_key, ticket_code, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, 'confirmed', ?)",
                (
                    payment_id,
                    event_id,
                    user_id,
                    idempotency_key,
                    ticket_code,
                    _iso(now),
                ),
            )
            reservation_id = cursor_res.lastrowid

            for code in seats:
                db.execute(
                    "INSERT INTO reservation_seats (reservation_id, event_id, "
                    "seat_code, created_at) VALUES (?, ?, ?, ?)",
                    (reservation_id, event_id, code, _iso(now)),
                )

        db.commit()
    except sqlite3.Error:
        db.rollback()
        raise

    _export_log(db)

    if success:
        return {
            "success": True,
            "ticketId": ticket_code,
            "ticketCode": ticket_code,
            "reservationId": reservation_id,
            "eventId": event_id,
            "seats": seats,
            "createdAt": _iso(now),
        }
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
    LOG_FILE.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8")
