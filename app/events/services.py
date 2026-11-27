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
    db,
    organizer_id,
    title,
    category,
    venue,
    start_time,
    end_time,
    capacity,
    price,
    *,
    venue_id=None,
):
    """Etkinliği `draft` durumunda kaydeder (TG-118, PB-08; BR-1.5, BR-2.2, BR-2.3).

    - Yetki: `organizer_id` Accounts üzerinden doğrulanır; kullanıcı yönetici onaylı
      organizatör değilse `EventPermissionError` fırlatılır ve kayıt yazılmaz.
    - Salon: formdan gelen `venue_id` (TG-119/TG-121) verilirse salon `venues.id` ile bulunur;
      verilmezse `venue` salon adıyla aranır. Etkinlik kapasitesi gerçek salon kapasitesiyle
      karşılaştırılır.
    - `organizer_id` istek verisinden değil, oturumdan (g.user_id) verilmelidir.
    - Durum her zaman `draft`'tır. Veritabanı hatalarında işlem geri alınır.

    Dönüş: (True, event_dict, []) veya (False, None, [hata mesajları]).
    """
    if not is_approved_organizer(organizer_id, db):
        raise EventPermissionError(_PERMISSION_MSG)

    title = str(title or "").strip()
    category = str(category or "").strip()
    venue = str(venue or "").strip()
    venue_id_s = str(venue_id if venue_id is not None else "").strip()
    start_time = str(start_time or "").strip()
    end_time = str(end_time or "").strip()
    capacity_s = str(capacity if capacity is not None else "").strip()
    price_s = str(price if price is not None else "").strip()

    if not all([title, category, venue or venue_id_s, start_time, end_time, capacity_s, price_s]):
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
        if venue_id_s:
            venue_row = None
            if venue_id_s.isascii() and venue_id_s.isdigit():
                venue_row = db.execute(
                    "SELECT id, capacity FROM venues WHERE id = ?", (int(venue_id_s),)
                ).fetchone()
        else:
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
    """TG-189: Etkinliği salon bilgileriyle birlikte tek sorguda döndürür.

    Mevcut etkinlik alanlarına venue_name, venue_address ve venue_capacity eklenir.
    Etkinlik yoksa veya kimlik geçersizse None döner.
    """
    if isinstance(event_id, bool) or not isinstance(event_id, int):
        return None

    row = db.execute(
        """
        SELECT
            e.id,
            e.title,
            e.category,
            e.venue_id,
            e.start_time,
            e.end_time,
            e.capacity,
            e.price,
            e.status,
            e.organizer_id,
            v.name AS venue_name,
            v.address AS venue_address,
            v.capacity AS venue_capacity
        FROM events AS e
        LEFT JOIN venues AS v ON e.venue_id = v.id
        WHERE e.id = ?
        """,
        (event_id,),
    ).fetchone()

    return dict(row) if row else None


def get_event_detail(db, event_id, user_id=None, user_role=None):
    """TG-190: Etkinlik detayını kullanıcı rolüne göre görünürse döndürür.

    Yayınlanmış etkinlikler anonim kullanıcılar dahil herkese açıktır.
    Taslakları sadece sahibi olan organizatör veya admin görebilir.
    Yetkisiz erişimde ve bulunamayan etkinlikte None döner.

    user_id ve user_role, istek verisinden değil güvenilir oturumdan alınmalıdır.
    """
    event = get_event(db, event_id)
    if event is None:
        return None

    # Yayınlanmış etkinliğin detayları herkese açıktır.
    if event["status"] == "published":
        return event

    # Sadece taslak durumuna yönelik erişim izni tanımlıdır.
    if event["status"] != "draft":
        return None

    # Anonim veya geçersiz kullanıcı taslaklara erişemez.
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id < 1:
        return None

    if user_role == "admin":
        return event

    if user_role == "organizer" and event["organizer_id"] == user_id:
        return event

    return None


def list_events_by_organizer(db, organizer_id):
    """Organizatörün etkinliklerini (taslaklar dahil) yeniden eskiye sıralı döndürür."""
    rows = db.execute(
        f"SELECT {_EVENT_COLUMNS} FROM events WHERE organizer_id = ? ORDER BY id DESC",
        (organizer_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def _validate_event_for_publishing(db, event):
    """TG-173: Yayınlamadan önce BR-2.2, BR-2.3 ve BR-2.4 kurallarını doğrular.

    Geçerli sonuç boş hata listesidir. Bu fonksiyon veritabanını değiştirmez.
    """
    errors = []

    # BR-2.2: Başlık ve kategori boş olmamalı.
    if not str(event.get("title") or "").strip():
        errors.append("Etkinlik başlığı zorunludur.")
    if not str(event.get("category") or "").strip():
        errors.append("Etkinlik kategorisi zorunludur.")

    # BR-2.2, BR-2.3: Salon mevcut olmalı; kapasite geçerli ve sınır içinde olmalı.
    venue = db.execute(
        "SELECT id, capacity FROM venues WHERE id = ?",
        (event.get("venue_id"),),
    ).fetchone()
    if venue is None:
        errors.append("Geçerli bir salon seçilmelidir.")

    try:
        if event.get("capacity") is None:
            raise ValueError
        capacity = int(str(event["capacity"]))
        if capacity < 1:
            errors.append("Etkinlik kapasitesi en az 1 olmalıdır.")
        elif venue is not None and capacity > venue["capacity"]:
            errors.append("Etkinlik kapasitesi salon kapasitesini aşamaz.")
    except (ValueError, TypeError):
        errors.append("Etkinlik kapasitesi geçerli bir tam sayı olmalıdır.")

    # BR-2.2: Fiyat 0 (ücretsiz) veya pozitif, sonlu sayı olmalı.
    try:
        if event.get("price") is None:
            raise ValueError
        price = float(event["price"])
        if not math.isfinite(price) or price < 0:
            raise ValueError
    except (ValueError, TypeError, OverflowError):
        errors.append("Bilet fiyatı sıfır veya pozitif bir sayı olmalıdır.")

    # BR-2.2: Tarihler doğru sırada ve karşılaştırılabilir olmalı.
    start = _parse_form_datetime(event.get("start_time"))
    end = _parse_form_datetime(event.get("end_time"))
    if start is None or end is None:
        errors.append("Başlangıç ve bitiş zamanı geçerli olmalıdır.")
    else:
        try:
            if end <= start:
                errors.append("Bitiş zamanı başlangıçtan sonra olmalıdır.")
        except TypeError:
            errors.append("Başlangıç ve bitiş saat dilimleri uyumsuz.")

    if errors:
        return errors

    # BR-2.4: Başka bir yayınlanmış etkinlikle salon ve zaman çakışması olmamalı.
    published_events = db.execute(
        """
        SELECT id, start_time, end_time
        FROM events
        WHERE venue_id = ? AND status = 'published' AND id != ?
        """,
        (event["venue_id"], event["id"]),
    ).fetchall()

    for other in published_events:
        other_start = _parse_form_datetime(other["start_time"])
        other_end = _parse_form_datetime(other["end_time"])
        if other_start is None or other_end is None:
            return ["Salondaki yayınlanmış etkinliğin tarihleri geçersiz."]
        try:
            # Birinin bittiği anda diğeri başlıyorsa çakışma sayılmaz.
            if start < other_end and end > other_start:
                return ["Aynı salonda bu saatlerde yayınlanmış başka bir etkinlik var."]
        except TypeError:
            return ["Etkinliklerin saat dilimi bilgileri uyumsuz."]

    return []


def publish_event(db, event_id, organizer_id):
    """TG-172/TG-173: Yetki ve yayınlama öncesi iş kurallarını doğrular.

    `organizer_id` doğrulanmış oturumdan gelmelidir; istek gövdesinden alınmamalıdır.
    Dönüş: (True, event_dict, []) veya (False, None, [hata mesajları]).
    Yetkisiz işlemlerde EventPermissionError fırlatılır.
    """
    # 1. Etkinlik kimliğinin geçerli olduğunu doğrula.
    if isinstance(event_id, bool) or not isinstance(event_id, int) or event_id < 1:
        return False, None, ["Geçersiz etkinlik kimliği."]

    permission_msg = (
        "Etkinliği yayınlamak için yönetici onaylı etkinlik sahibi organizatör olmalısınız."
    )

    # 2. Yayınlama isteyen kişi yönetici onaylı organizatör mü?
    if not is_approved_organizer(organizer_id, db):
        raise EventPermissionError(permission_msg)

    try:
        # 3. Etkinlik mevcut mu?
        event = get_event(db, event_id)
        if event is None:
            return False, None, ["Etkinlik bulunamadı."]

        # 4. Onaylı organizatör etkinliğin sahibi mi?
        if event["organizer_id"] != organizer_id:
            raise EventPermissionError(permission_msg)

        # TG-173: Yayınlama yalnızca taslak durumdaki etkinliklere uygulanır.
        if event["status"] != "draft":
            return False, None, ["Yalnızca taslak etkinlikler yayınlanabilir."]

        # TG-173: Eksik alan, salon kapasitesi ve zaman çakışması kontrolü.
        validation_errors = _validate_event_for_publishing(db, event)
        if validation_errors:
            return False, None, validation_errors

        # 5. Aynı etkinliği sadece taslaksa ve aynı kişiye aitse yayınla.
        cursor = db.execute(
            """
            UPDATE events
            SET status = 'published'
            WHERE id = ? AND organizer_id = ? AND status = 'draft'
            """,
            (event_id, organizer_id),
        )

        if cursor.rowcount == 0:
            db.rollback()
            return False, None, ["Yalnızca taslak etkinlikler yayınlanabilir."]

        # 6. Durum değişikliğini SQLite'a kalıcı olarak yaz.
        db.commit()
        return True, get_event(db, event_id), []

    except sqlite3.Error:
        db.rollback()
        return False, None, ["Etkinlik yayınlanırken veritabanı hatası oluştu."]
