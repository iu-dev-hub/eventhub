"""
Etkinlik Veri Modeli
Kültür, Konser, Tiyatro ve Sergi Etkinlikleri
"""
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Event:
    id: str
    title: str
    category: str                      # concert, theatre, festival, standup, exhibition, workshop
    venue_name: str
    city: str
    date_str: str                      # ör: '18 Kasım 2026'
    days_until_event: int              # Erken kayıt indirimi hesabı için (BR-4.1)
    time_str: str                      # ör: '20:30'
    base_price: float                  # BR-2.2: 0 ise ücretsiz
    capacity: int
    sold_count: int = 0
    status: str = "published"          # draft | published | sales_closed | completed | cancelled
    image_url: str = ""
    description: str = ""
    organizer_id: str = "org-aura-1"
    blocks: List[str] = field(default_factory=lambda: ["Parter VIP", "Parter Orta", "Balkon Salon"])
    
    @property
    def remaining(self) -> int:
        return max(0, self.capacity - self.sold_count)

    @property
    def is_early_bird(self) -> bool:
        return self.days_until_event >= 14
