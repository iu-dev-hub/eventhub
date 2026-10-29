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
        errors.append(f"Etkinlik kapasitesi ({cap_val}), salon kapasitesini ({hall_capacity}) aşamaz.")
    
    if price_val < 0:
        errors.append("Bilet fiyatı negatif olamaz.")

    if errors:
        return False, errors

    # 4. Başarılı durum ve ücretsiz etkinlik mesajı (TG-22)
    success_msg = "Etkinlik bilgileri doğrulandı. (Kayıt işlemi Sprint 2'de yapılacaktır.)"
    if price_val == 0:
        success_msg = "Ücretsiz etkinlik doğrulaması başarılı. (Kayıt işlemi Sprint 2'de yapılacaktır.)"

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
