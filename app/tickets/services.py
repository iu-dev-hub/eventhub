from app.core.db import get_db

# İş kuralı sabitleri
ACTIVE_TICKET_STATUSES = ("reserved", "paid")  # Kontenjandan düşülen aktif/beklemedeki durumlar
CANCELLED_STATUS = "cancelled"

def count_active_tickets(event_id: int) -> int:
    """Etkinlik için kontenjandan düşülen toplam bilet sayısını hesaplar (BR-3.2)."""
    row = get_db().execute(
        """
        SELECT COUNT(*) AS total
        FROM tickets
        WHERE event_id = ? AND status IN (?, ?)
        """,
        (event_id, *ACTIVE_TICKET_STATUSES),
    ).fetchone()
    return row["total"]

def get_remaining_capacity(event_id: int) -> int:
    """Etkinliğin kalan kontenjanını hesaplar."""
    db = get_db()
    # Etkinlik özelindeki kapasiteyi sorgulama
    event_row = db.execute(
        "SELECT capacity FROM events WHERE id = ?", (event_id,)
    ).fetchone()
    
    if not event_row:
        raise ValueError("Etkinlik bulunamadı.")

    ## Negatif kontenjan riskine karşı max(0, ...) koruması    
    event_capacity = event_row["capacity"]
    active_tickets = count_active_tickets(event_id)
    
    remaining = event_capacity - active_tickets
    return max(0, remaining)

def purchase_ticket(event_id: int, user_id: int) -> int:
    """Etkinlik için bilet satın alır; kontenjan doluysa hata fırlatır (BR-3.2)."""
    db = get_db()
    
    # Kontenjan kontrolü (Kalan kontenjan 0 veya daha azsa engelle)
    remaining = get_remaining_capacity(event_id)
    if remaining <= 0:
        raise ValueError("Kontenjan dolu. Bilet satın alınamadı.")
        
    # Yeni bilet kaydı oluştur (aktif statüde: paid)
    cursor = db.execute(
        """
        INSERT INTO tickets (event_id, user_id, status, created_at)
        VALUES (?, ?, ?, datetime('now'))
        """,
        (event_id, user_id, "paid")
    )
    db.commit()
    return cursor.lastrowid

def cancel_ticket(ticket_id: int) -> None:
    """Bilet durumunu cancelled yaparak kontenjanı serbest bırakır."""
    db = get_db()

    #Biletin varlığı ve mevcut durum kontrolü
    ticket_row = db.execute(
        "SELECT status FROM tickets WHERE id = ?", (ticket_id,)
    ).fetchone()

    if not ticket_row:
        raise ValueError("Bilet bulunamadı.")

    if ticket_row["status"]==CANCELLED_STATUS:
        raise ValueError("Bu bilet zaten iptal edilmiş.")

    #Durumu iptal olarak güncelle
    db.execute(
        "UPDATE tickets SET status = ? WHERE id = ?",
        (CANCELLED_STATUS, ticket_id)
    )
    db.commit()