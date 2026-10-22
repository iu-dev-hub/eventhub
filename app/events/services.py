def validate_event_creation(title, capacity, price):
    """Etkinlik oluşturma formundan gelen verileri iş kurallarına göre doğrular."""
    errors = []
    hall_capacity = 100  # Sprint 1 prototipi için sabit kapasite

    # Zorunlu alan kontrolü
    if not title or not capacity or not price:
        errors.append("Tüm zorunlu alanların doldurulması gerekmektedir.")
        return False, errors

    try:
        cap_val = int(capacity)
        price_val = float(price)
    except ValueError:
        errors.append("Kapasite ve fiyat geçerli sayısal değerler olmalıdır.")
        return False, errors

    # Kapasite kontrolü (BR-2.2, BR-2.3)
    if cap_val > hall_capacity:
        errors.append(f"Etkinlik kapasitesi ({cap_val}), salon kapasitesini ({hall_capacity}) aşamaz.")
    
    if price_val < 0:
        errors.append("Bilet fiyatı negatif olamaz.")

    if errors:
        return False, errors

    # Başarılı durum ve ücretsiz etkinlik mesajı
    success_msg = "Doğrulama başarılı. (Kayıt işlemi Sprint 2'de yapılacaktır.)"
    if price_val == 0:
        success_msg = "Ücretsiz etkinlik doğrulaması başarılı. (Kayıt işlemi Sprint 2'de yapılacaktır.)"

    return True, [success_msg]