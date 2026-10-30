"""
Bilet Veri Modeli
BR-3 ve BR-4 Kuralları
Durumlar: reserved | paid | used | refunded | cancelled
"""
from dataclasses import dataclass
import time
from typing import Optional

@dataclass
class Ticket:
    id: str
    pnr: str
    event_id: str
    event_title: str
    venue_name: str
    event_date: str
    event_time: str
    user_id: str
    user_name: str
    seat_label: str
    price: float
    status: str = "paid"               # reserved | paid | used | refunded | cancelled
    qr_token: str = ""
    purchase_time: float = 0.0
    reserved_until: float = 0.0        # BR-3.5: 15 dakika geri sayım sınırı

    def is_expired(self) -> bool:
        if self.status == "reserved" and time.time() > self.reserved_until:
            return True
        return False
