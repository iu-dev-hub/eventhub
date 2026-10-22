def validate_event_data(title, category, venue, start_time, end_time, capacity, price):
    """Etkinlik verilerini doğrular (BR-2.2, BR-2.3). Veritabanına kaydetmez."""
    
    # 9. Madde: Zorunlu alanlardan biri boş bırakıldığında
    if not all([title, category, venue, start_time, end_time, capacity is not None, price is not None]):
        raise ValueError("Lütfen tüm zorunlu alanları doldurun.")

    if capacity < 1:
        raise ValueError("Etkinlik kapasitesi en az 1 olmalıdır.")
        
    # 7. Madde: Kapasite salon sınırını aştığında verilecek hata (BR-2.3)
    venue_capacity = 100 # Prototip için örnek bir salon kapasitesi sınırı
    if capacity > venue_capacity:
        raise ValueError("Etkinlik kapasitesi salonun kapasitesini aşamaz.")

    if price < 0:
        raise ValueError("Bilet fiyatı negatif olamaz.")
        
    return True