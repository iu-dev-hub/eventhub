import math
import sqlite3
from datetime import datetime

from app.accounts import services as accounts_services


def validate_event_creation(title, category, venue, start_time, end_time, capacity, price):
    """Etkinlik oluşturma formundan gelen verileri iş kurallarına göre doğrular."""
    errors = []
    hall_capacity = 100  # Sprint 1 prototipi için sabit kapasite

    # 1. Zorunlu alan kontrolü (TG-21'deki tüm alanlar eklendi)
    if not all([title, category, venue, start_time, end_time, capacity, price]):
        errors.append("Lütfen tüm zorunlu alanları doldurun.")
        return False, errors

    # 2. Sayısal değer dönüşümleri (TG-22)
    try:
        cap_val = int(capacity)
        price_val = float(price)
    except ValueError:
        errors.append("Kapasite ve fiyat geçerli sayısal değerler olmalıdır.")
        return False, errors

    # 3. Mantıksal kontroller (BR-2.2, BR-2.3 vb.)
    if cap_val < 1:
        errors.append("Etkinlik kapasitesi en az 1 olmalıdır.")

    if cap_val > hall_capacity:
        errors.append(
            f"Etkinlik kapasitesi ({cap_val}), salon kapasitesini ({hall_capacity}) aşamaz."
        )

    if price_val < 0:
        errors.append("Bilet fiyatı negatif olamaz.")

    if errors:
        return False, errors

    # 4. Başarılı durum ve ücretsiz etkinlik mesajı (TG-22)
    success_msg = "Etkinlik bilgileri doğrulandı. (Kayıt işlemi Sprint 2'de yapılacaktır.)"
    if price_val == 0:
        success_msg = (
            "Ücretsiz etkinlik doğrulaması başarılı. (Kayıt işlemi Sprint 2'de yapılacaktır.)"
        )

    return True, [success_msg]


MAX_VENUE_NAME_LENGTH = 100


def create_venue(db, name, address, capacity):
    """Yeni salon kaydeder (BR-2.1, TG-41).

    Yetki kontrolü route katmanında (role_required("admin")) yapılır.
    Dönüş: (True, venue_dict, []) veya (False, None, [hata mesajları]).
    Hata durumlarında veritabanına kayıt yazılmaz.
    """
    errors = []
    name = str(name or "").strip()
    address = str(address or "").strip()

    if not name or not address or capacity is None or str(capacity).strip() == "":
        return False, None, ["Salon adı, adresi ve kapasitesi zorunludur."]

    if len(name) > MAX_VENUE_NAME_LENGTH:
        errors.append(f"Salon adı en fazla {MAX_VENUE_NAME_LENGTH} karakter olabilir.")

    try:
        if isinstance(capacity, bool):
            raise ValueError
        cap_val = int(str(capacity).strip())
    except ValueError:
        errors.append("Salon kapasitesi geçerli bir tam sayı olmalıdır.")
    else:
        if cap_val < 1:
            errors.append("Salon kapasitesi en az 1 olmalıdır.")

    if errors:
        return False, None, errors

    if db.execute("SELECT 1 FROM venues WHERE name = ?", (name,)).fetchone():
        return False, None, ["Bu isimde bir salon zaten mevcut."]

    cursor = db.execute(
        "INSERT INTO venues (name, address, capacity) VALUES (?, ?, ?)",
        (name, address, cap_val),
    )
    db.commit()
    venue = {"id": cursor.lastrowid, "name": name, "address": address, "capacity": cap_val}
    return True, venue, []


def get_all_venues():
    """Tüm salonları veritabanından çeker ve isme göre sıralı liste olarak döndürür."""
    from app.core.db import get_db

    db = get_db()

    # try-except bloğu tamamen kaldırıldı, hata oluşursa doğal olarak fırlatılacak.
    # Emircan'ın isteği üzerine sıralama için ORDER BY name eklendi.
    venues = db.execute("SELECT id, name, address, capacity FROM venues ORDER BY name").fetchall()
    return venues


class EventPermissionError(PermissionError):
    """Kullanıcı taslak etkinlik oluşturmaya yetkili değil (BR-1.5)."""


_EVENT_COLUMNS = (
    "id, title, category, venue_id, start_time, end_time, capacity, price, status, organizer_id"
)
_PERMISSION_MSG = "Etkinlik oluşturmak için yönetici onaylı organizatör olmalısınız."
ORGANIZER_APPROVAL_COLUMN = "organizer_approved"
_DB_ERROR_MSG = "Etkinlik kaydedilirken bir veritabanı hatası oluştu. Lütfen tekrar deneyin."


def is_approved_organizer(user_id: int, db=None) -> bool:
    """Kullanıcının yönetici onaylı organizatör olup olmadığını döndürür (BR-1.5, TG-118).

    Güvenli varsayılan: Accounts ekibinin kalıcı organizatör onay mekanizması henüz
    tamamlanmadığından, `app.accounts.services.is_approved_organizer` tanımlı değilse ve
    `users.organizer_approved` sütunu şemada yoksa her zaman False döner (yetki reddedilir).
    Accounts servisi eklendiğinde doğrulama doğrudan o servise delege edilir.
    """
    if not user_id or isinstance(user_id, bool) or not isinstance(user_id, int):
        return False
    if db is None:
        from app.core.db import get_db

        db = get_db()

    accounts_checker = getattr(accounts_services, "is_approved_organizer", None)
    if callable(accounts_checker):
        return bool(accounts_checker(user_id, db))

    columns = {r["name"] for r in db.execute("PRAGMA table_info(users)").fetchall()}
    if ORGANIZER_APPROVAL_COLUMN not in columns:
        return False
    row = db.execute(
        f"SELECT role, {ORGANIZER_APPROVAL_COLUMN} AS approved FROM users WHERE id = ? LIMIT 1",
        (user_id,),
    ).fetchone()
    return row is not None and row["role"] == "organizer" and bool(row["approved"])


def _parse_form_datetime(value):
    try:
        return datetime.fromisoformat(str(value).strip())
    except ValueError:
        return None


def create_draft_event(
    db, organizer_id, title, category, venue, start_time, end_time, capacity, price
):
    """Etkinliği `draft` durumunda kaydeder (TG-118, PB-08; BR-1.5, BR-2.2, BR-2.3).

    - Yetki: `organizer_id` Accounts üzerinden doğrulanır; kullanıcı yönetici onaylı
      organizatör değilse `EventPermissionError` fırlatılır ve kayıt yazılmaz.
    - `venue` salon adıdır; salon `venues` tablosundan bulunur ve etkinlik kapasitesi
      gerçek salon kapasitesiyle karşılaştırılır.
    - `organizer_id` istek verisinden değil, oturumdan (g.user_id) verilmelidir.
    - Durum her zaman `draft`'tır. Veritabanı hatalarında işlem geri alınır.

    Dönüş: (True, event_dict, []) veya (False, None, [hata mesajları]).
    """
    if not is_approved_organizer(organizer_id, db):
        raise EventPermissionError(_PERMISSION_MSG)

    title = str(title or "").strip()
    category = str(category or "").strip()
    venue = str(venue or "").strip()
    start_time = str(start_time or "").strip()
    end_time = str(end_time or "").strip()
    capacity_s = str(capacity if capacity is not None else "").strip()
    price_s = str(price if price is not None else "").strip()

    if not all([title, category, venue, start_time, end_time, capacity_s, price_s]):
        return False, None, ["Lütfen tüm zorunlu alanları doldurun."]

    errors = []
    try:
        if isinstance(capacity, bool):
            raise ValueError
        cap_val = int(capacity_s)
    except ValueError:
        cap_val = None
        errors.append("Etkinlik kapasitesi geçerli bir tam sayı olmalıdır.")
    try:
        price_val = float(price_s)
        if not math.isfinite(price_val):
            raise ValueError
    except ValueError:
        price_val = None
        errors.append("Bilet fiyatı geçerli bir sayı olmalıdır.")
    if errors:
        return False, None, errors

    start_dt = _parse_form_datetime(start_time)
    end_dt = _parse_form_datetime(end_time)
    if start_dt is None or end_dt is None:
        errors.append("Başlangıç ve bitiş zamanı geçerli bir tarih olmalıdır.")
    elif end_dt <= start_dt:
        errors.append("Bitiş zamanı başlangıç zamanından sonra olmalıdır.")
    if cap_val < 1:
        errors.append("Etkinlik kapasitesi en az 1 olmalıdır.")
    if price_val < 0:
        errors.append("Bilet fiyatı negatif olamaz.")

    try:
        venue_row = db.execute(
            "SELECT id, capacity FROM venues WHERE name = ?", (venue,)
        ).fetchone()
        if venue_row is None:
            errors.append("Seçilen salon bulunamadı.")
        elif cap_val > venue_row["capacity"]:
            errors.append(
                f"Etkinlik kapasitesi ({cap_val}), salon kapasitesini "
                f"({venue_row['capacity']}) aşamaz."
            )
        if errors:
            return False, None, errors

        cursor = db.execute(
            "INSERT INTO events (title, category, venue_id, start_time, end_time, "
            "capacity, price, status, organizer_id) VALUES (?, ?, ?, ?, ?, ?, ?, 'draft', ?)",
            (
                title,
                category,
                venue_row["id"],
                start_time,
                end_time,
                cap_val,
                price_val,
                organizer_id,
            ),
        )
        db.commit()
    except sqlite3.Error:
        db.rollback()
        return False, None, [_DB_ERROR_MSG]

    return True, get_event(db, cursor.lastrowid), []


def get_event(db, event_id):
    """Etkinliği `events` tablosundan okur; yoksa `None` döner (TG-118).

    Dönüş biçimi: interface-contract.md 2.4'teki alanlar (`dict`).
    """
    if isinstance(event_id, bool) or not isinstance(event_id, int):
        return None
    row = db.execute(f"SELECT {_EVENT_COLUMNS} FROM events WHERE id = ?", (event_id,)).fetchone()
    return dict(row) if row else None


def list_events_by_organizer(db, organizer_id):
    """Organizatörün etkinliklerini (taslaklar dahil) yeniden eskiye sıralı döndürür."""
    rows = db.execute(
        f"SELECT {_EVENT_COLUMNS} FROM events WHERE organizer_id = ? ORDER BY id DESC",
        (organizer_id,),
    ).fetchall()
    return [dict(r) for r in rows]
