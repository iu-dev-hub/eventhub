"""
Koltuk Veri Modeli
"""
from dataclasses import dataclass

@dataclass
class Seat:
    id: str
    event_id: str
    block: str
    row: int
    number: int
    price: float
    status: str = "available"  # available | selected | reserved | occupied | vip

    @property
    def label(self) -> str:
        return f"{self.block} Sıra {self.row} No {self.number}"
