"""Event details, seat selection, reservation, sales close, and participation service (TG-184).

Bu modül Flet içe aktarmaz; böylece tüm iş kuralları (BR-2.5, BR-3.1, BR-3.2, BR-3.3,
BR-3.5, BR-4.1, BR-4.2, BR-4.6) CI ortamında Flet kurulmadan doğrudan test edilebilir
(mobile_client/README.md - test edilebilirlik kuralı).
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from mobile_client.core.constants import (
    EARLY_BIRD_DAYS_THRESHOLD,
    MAX_TICKETS_PER_EVENT,
    MINUTES_BEFORE_EVENT_START_SALES_CLOSE,
    TIMEOUT_FOR_PAYMENT_RESERVATION,
)
from mobile_client.core.routes import ROUTE_PAYMENT
from mobile_client.models.event import Event
from mobile_client.models.seat import Seat
from mobile_client.models.ticket import Ticket
from mobile_client.services.event_service import (
    DEFAULT_API_DIR,
    EventService,
    parse_iso_datetime,
)

EARLY_BIRD_DISCOUNT_RATE = 0.20  # BR-4.1 (%20 indirim)
STUDENT_DISCOUNT_RATE = 0.25  # BR-4.2 (%25 indirim)
ACTIVE_TICKET_STATUSES = ("paid", "reserved", "used")


@dataclass
class EventDetail:
    """Etkinlik detay ekranı için birleştirilmiş veri modeli (TG-184)."""

    event: Event
    venue_name: str
    venue_address: str
    venue_capacity: int
    description: str
    participant_count: int
    remaining_capacity: int
    seats: List[Seat] = field(default_factory=list)
    is_sales_closed: bool = False
    is_full: bool = False
    sales_status_message: str = ""


@dataclass
class ReservationResult:
    """Koltuk seçimi, rezervasyon ve satın alma yönlendirme sonucu (TG-184)."""

    success: bool
    message: str
    error_code: str = ""
    reserved_seats: List[str] = field(default_factory=list)
    locked_until: Optional[str] = None
    redirect_route: Optional[str] = None
    total_price: float = 0.0


def _ensure_utc(dt: Optional[datetime] = None) -> datetime:
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def dict_to_seat(raw: Dict[str, Any]) -> Seat:
    """JSON sözlüğünü Seat model nesnesine dönüştürür."""
    locked_val = raw.get("locked_until")
    return Seat(
        id=int(raw["id"]),
        event_id=int(raw["event_id"]),
        seat_code=str(raw.get("seat_code", "")).strip(),
        status=str(raw.get("status", "available")).strip(),
        locked_until=str(locked_val).strip() if locked_val else None,
    )


def dict_to_ticket(raw: Dict[str, Any]) -> Ticket:
    """JSON sözlüğünü Ticket model nesnesine dönüştürür."""
    qr_val = raw.get("qr_code")
    return Ticket(
        id=int(raw["id"]),
        event_id=int(raw["event_id"]),
        user_id=int(raw["user_id"]),
        status=str(raw.get("status", "reserved")).strip(),
        qr_code=str(qr_val) if qr_val else "",
        created_at=str(raw.get("created_at", "")).strip(),
    )


def is_seat_lock_expired(seat: Seat, now: Optional[datetime] = None) -> bool:
    """Ücretli etkinliklerde ayrılan koltuk 15 dk içinde ödenmezse serbest kalır (BR-3.5)."""
    if seat.status != "locked":
        return False
    if not seat.locked_until:
        return True
    current = _ensure_utc(now)
    locked_until_dt = parse_iso_datetime(seat.locked_until)
    if locked_until_dt == datetime.max.replace(tzinfo=timezone.utc):
        return True
    return current >= locked_until_dt


def is_event_sales_closed(event: Event, now: Optional[datetime] = None) -> bool:
    """Bilet satışı etkinlik başlangıcından 1 saat (60 dk) önce kapanır (BR-3.3)."""
    if event.status != "published":
        return True
    current = _ensure_utc(now)
    start_dt = parse_iso_datetime(event.start_time)
    if start_dt == datetime.max.replace(tzinfo=timezone.utc):
        return False
    remaining_time = start_dt - current
    return remaining_time <= timedelta(minutes=MINUTES_BEFORE_EVENT_START_SALES_CLOSE)


def calculate_price_summary(
    event: Event,
    seat_count: int,
    is_student: bool = False,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Bilet fiyatını erken kayıt (BR-4.1), öğrenci (BR-4.2) ve ücretsiz (BR-4.6) ile hesaplar."""
    count = max(0, int(seat_count))
    base_unit = max(0.0, float(event.price))
    if base_unit == 0.0 or count == 0:
        return {
            "is_free": base_unit == 0.0,
            "is_early_bird": False,
            "is_student": bool(is_student),
            "base_total": 0.0,
            "discount_amount": 0.0,
            "final_total": 0.0,
        }

    is_early_bird = False
    current = _ensure_utc(now)
    start_dt = parse_iso_datetime(event.start_time)
    if start_dt != datetime.max.replace(tzinfo=timezone.utc):
        is_early_bird = (start_dt - current) >= timedelta(days=EARLY_BIRD_DAYS_THRESHOLD)

    unit_price = base_unit
    if is_early_bird:
        unit_price = unit_price * (1.0 - EARLY_BIRD_DISCOUNT_RATE)
    if is_student:
        unit_price = unit_price * (1.0 - STUDENT_DISCOUNT_RATE)

    base_total = round(base_unit * count, 2)
    final_total = round(unit_price * count, 2)
    discount_amount = round(base_total - final_total, 2)

    return {
        "is_free": False,
        "is_early_bird": is_early_bird,
        "is_student": bool(is_student),
        "base_total": base_total,
        "discount_amount": discount_amount,
        "final_total": final_total,
    }


class ParticipationService:
    """../app/api JSON dosyalarından etkinlik detayı, koltuk seçimi ve rezervasyon servisi."""

    def __init__(
        self,
        api_dir: Optional[Path] = None,
        events_json_path: Optional[Path] = None,
        venues_json_path: Optional[Path] = None,
        seats_json_path: Optional[Path] = None,
        tickets_json_path: Optional[Path] = None,
    ) -> None:
        base_dir = Path(api_dir) if api_dir else DEFAULT_API_DIR
        self.events_json_path = (
            Path(events_json_path) if events_json_path else base_dir / "events.json"
        )
        self.venues_json_path = (
            Path(venues_json_path) if venues_json_path else base_dir / "venues.json"
        )
        self.seats_json_path = Path(seats_json_path) if seats_json_path else base_dir / "seats.json"
        self.tickets_json_path = (
            Path(tickets_json_path) if tickets_json_path else base_dir / "tickets.json"
        )
        self.event_service = EventService(events_json_path=self.events_json_path)
        self._waitlist: Dict[int, Set[int]] = {}
        self._in_memory_seat_overrides: Dict[Tuple[int, str], Tuple[str, Optional[str]]] = {}
        self._in_memory_tickets: List[Ticket] = []

    def _read_json_list(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def _write_json_list(self, path: Path, payload: List[Dict[str, Any]]) -> None:
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)

    def get_venue_by_id(self, venue_id: int) -> Dict[str, Any]:
        """venues.json içinden salon bilgisini döndürür (BR-2.1, BR-2.2)."""
        for item in self._read_json_list(self.venues_json_path):
            if isinstance(item, dict) and int(item.get("id", -1)) == int(venue_id):
                return {
                    "id": int(item["id"]),
                    "name": str(item.get("name", "Bilinmeyen Salon")),
                    "address": str(item.get("address", "")),
                    "capacity": int(item.get("capacity", 0)),
                }
        return {
            "id": int(venue_id),
            "name": f"Salon #{venue_id}",
            "address": "Belirtilmedi",
            "capacity": 0,
        }

    def get_event_seats(self, event_id: int, now: Optional[datetime] = None) -> List[Seat]:
        """Etkinlik koltuklarını çeker ve süresi dolan kilitleri serbest bırakır (BR-3.5)."""
        raw_seats = self._read_json_list(self.seats_json_path)
        seats: List[Seat] = []
        for item in raw_seats:
            if not isinstance(item, dict) or int(item.get("event_id", -1)) != int(event_id):
                continue
            try:
                seat = dict_to_seat(item)
            except (KeyError, TypeError, ValueError):
                continue

            override = self._in_memory_seat_overrides.get((int(event_id), seat.seat_code))
            if override is not None:
                seat.status = override[0]
                seat.locked_until = override[1]

            if is_seat_lock_expired(seat, now=now):
                seat.status = "available"
                seat.locked_until = None

            seats.append(seat)

        return sorted(seats, key=lambda s: s.seat_code)

    def get_event_tickets(self, event_id: int) -> List[Ticket]:
        """tickets.json ve oturum içi rezervasyonlardan etkinliğin biletlerini döndürür."""
        raw_tickets = self._read_json_list(self.tickets_json_path)
        tickets: List[Ticket] = []
        seen_ids: Set[int] = set()
        for item in raw_tickets:
            if not isinstance(item, dict) or int(item.get("event_id", -1)) != int(event_id):
                continue
            try:
                t = dict_to_ticket(item)
                tickets.append(t)
                seen_ids.add(t.id)
            except (KeyError, TypeError, ValueError):
                continue

        for mem_ticket in self._in_memory_tickets:
            if mem_ticket.event_id == int(event_id) and mem_ticket.id not in seen_ids:
                tickets.append(mem_ticket)

        return tickets

    def get_user_active_ticket_count(self, event_id: int, user_id: Optional[int]) -> int:
        """Kullanıcının bu etkinlik için sahip olduğu aktif bilet sayısını döndürür (BR-3.1)."""
        if user_id is None:
            return 0
        tickets = self.get_event_tickets(event_id)
        return sum(
            1 for t in tickets if t.user_id == int(user_id) and t.status in ACTIVE_TICKET_STATUSES
        )

    def get_event_detail(
        self,
        event_id: int,
        now: Optional[datetime] = None,
    ) -> Optional[EventDetail]:
        """Etkinlik ID'si ile konum, tarih, açıklama, katılımcı sayısı ve koltukları döndürür."""
        raw_events = self._read_json_list(self.events_json_path)
        target_raw: Optional[Dict[str, Any]] = None
        for item in raw_events:
            if isinstance(item, dict) and int(item.get("id", -1)) == int(event_id):
                target_raw = item
                break

        if target_raw is None:
            return None

        all_events = self.event_service.load_all_events()
        event = next((ev for ev in all_events if ev.id == int(event_id)), None)
        if event is None:
            return None

        venue = self.get_venue_by_id(event.venue_id)
        seats = self.get_event_seats(event.id, now=now)
        tickets = self.get_event_tickets(event.id)

        active_ticket_count = sum(1 for t in tickets if t.status in ACTIVE_TICKET_STATUSES)
        occupied_seat_count = sum(1 for s in seats if s.status in ("sold", "occupied", "locked"))
        participant_count = min(event.capacity, max(active_ticket_count, occupied_seat_count))
        remaining_capacity = max(0, event.capacity - participant_count)

        all_seats_taken = len(seats) > 0 and all(s.status != "available" for s in seats)
        is_full = remaining_capacity == 0 or all_seats_taken
        if is_full:
            remaining_capacity = 0

        sales_closed = is_event_sales_closed(event, now=now)

        raw_desc = str(target_raw.get("description", "")).strip()
        description = (
            raw_desc
            if raw_desc
            else (
                f"{event.title}, {event.category} kategorisinde {venue['name']} "
                f"({venue['address']}) konumunda gerçekleştirilecektir."
            )
        )

        status_msg = ""
        if event.status == "cancelled":
            status_msg = "Bu etkinlik iptal edilmiştir."
        elif event.status == "draft":
            status_msg = "Bu etkinlik henüz yayınlanmamıştır."
        elif sales_closed:
            status_msg = "Bilet satışı etkinlik başlangıcından 1 saat önce kapanmıştır."
        elif is_full:
            status_msg = "Kontenjan dolu. Bekleme listesine katılabilirsiniz."

        return EventDetail(
            event=event,
            venue_name=venue["name"],
            venue_address=venue["address"],
            venue_capacity=venue["capacity"],
            description=description,
            participant_count=participant_count,
            remaining_capacity=remaining_capacity,
            seats=seats,
            is_sales_closed=sales_closed,
            is_full=is_full,
            sales_status_message=status_msg,
        )

    def validate_seat_selection(
        self,
        event_id: int,
        seat_codes: List[str],
        user_id: Optional[int] = None,
        now: Optional[datetime] = None,
    ) -> Tuple[bool, str, str]:
        """Koltuk seçimi ve satın alma öncesi iş kurallarını doğrular (BR-3.1, BR-3.2, BR-3.3)."""
        detail = self.get_event_detail(event_id, now=now)
        if detail is None:
            return False, "Etkinlik bulunamadı.", "EVENT_NOT_FOUND"

        if detail.event.status != "published":
            return False, "Bu etkinlik satışa açık değil.", "EVENT_NOT_PUBLISHED"

        if detail.is_sales_closed:
            return (
                False,
                "Bilet satışı etkinlik başlangıcından 1 saat önce kapanmıştır.",
                "SALES_CLOSED",
            )

        if detail.is_full:
            return (
                False,
                "Kontenjan dolu. Bekleme listesine katılabilirsiniz.",
                "CAPACITY_FULL",
            )

        cleaned_codes = [str(code).strip() for code in (seat_codes or []) if str(code).strip()]
        if not cleaned_codes:
            return False, "Lütfen en az bir koltuk seçin.", "EMPTY_SELECTION"

        if len(set(cleaned_codes)) != len(cleaned_codes):
            return False, "Aynı koltuk birden fazla kez seçilemez.", "DUPLICATE_SEAT"

        existing_count = self.get_user_active_ticket_count(event_id, user_id)
        if (
            len(cleaned_codes) > MAX_TICKETS_PER_EVENT
            or (existing_count + len(cleaned_codes)) > MAX_TICKETS_PER_EVENT
        ):
            return (
                False,
                f"Bir etkinlik için en fazla {MAX_TICKETS_PER_EVENT} bilet alabilirsiniz.",
                "MAX_TICKETS_EXCEEDED",
            )

        if len(cleaned_codes) > detail.remaining_capacity:
            return (
                False,
                "Seçilen koltuk sayısı kalan kontenjanı aşıyor.",
                "INSUFFICIENT_CAPACITY",
            )

        seat_map = {s.seat_code: s for s in detail.seats}
        for code in cleaned_codes:
            seat = seat_map.get(code)
            if seat is None:
                return False, f"Geçersiz koltuk kodu: {code}.", "INVALID_SEAT"
            if seat.status != "available":
                return (
                    False,
                    f"{code} numaralı koltuk dolu veya rezerve edilmiş.",
                    "SEAT_UNAVAILABLE",
                )

        return True, "", ""

    def reserve_seats_for_purchase(
        self,
        event_id: int,
        seat_codes: List[str],
        user_id: Optional[int] = None,
        is_student: bool = False,
        now: Optional[datetime] = None,
        persist: bool = False,
    ) -> ReservationResult:
        """Seçilen koltukları 15 dk süreyle rezerve eder ve ödeme ekranına yönlendirir (BR-3.5)."""
        is_valid, err_msg, err_code = self.validate_seat_selection(
            event_id=event_id,
            seat_codes=seat_codes,
            user_id=user_id,
            now=now,
        )
        if not is_valid:
            return ReservationResult(
                success=False,
                message=err_msg,
                error_code=err_code,
            )

        detail = self.get_event_detail(event_id, now=now)
        assert detail is not None
        cleaned_codes = [str(code).strip() for code in seat_codes if str(code).strip()]
        current = _ensure_utc(now)
        locked_until_str = (current + timedelta(minutes=TIMEOUT_FOR_PAYMENT_RESERVATION)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        for code in cleaned_codes:
            self._in_memory_seat_overrides[(int(event_id), code)] = ("locked", locked_until_str)

        effective_user_id = int(user_id) if user_id is not None else 1
        existing_tickets = self._read_json_list(self.tickets_json_path)
        next_ticket_id = (
            max(
                [int(t.get("id", 0)) for t in existing_tickets if isinstance(t, dict)]
                + [t.id for t in self._in_memory_tickets]
                + [0]
            )
            + 1
        )
        created_at_str = current.strftime("%Y-%m-%dT%H:%M:%SZ")

        for offset, _ in enumerate(cleaned_codes):
            self._in_memory_tickets.append(
                Ticket(
                    id=next_ticket_id + offset,
                    event_id=int(event_id),
                    user_id=effective_user_id,
                    status="reserved",
                    qr_code="",
                    created_at=created_at_str,
                )
            )

        if persist:
            raw_seats = self._read_json_list(self.seats_json_path)
            for item in raw_seats:
                if (
                    isinstance(item, dict)
                    and int(item.get("event_id", -1)) == int(event_id)
                    and str(item.get("seat_code", "")).strip() in cleaned_codes
                ):
                    item["status"] = "locked"
                    item["locked_until"] = locked_until_str
            self._write_json_list(self.seats_json_path, raw_seats)

            for offset, _ in enumerate(cleaned_codes):
                existing_tickets.append(
                    {
                        "id": next_ticket_id + offset,
                        "event_id": int(event_id),
                        "user_id": effective_user_id,
                        "status": "reserved",
                        "qr_code": None,
                        "created_at": created_at_str,
                    }
                )
            self._write_json_list(self.tickets_json_path, existing_tickets)

        pricing = calculate_price_summary(
            detail.event,
            seat_count=len(cleaned_codes),
            is_student=is_student,
            now=now,
        )

        return ReservationResult(
            success=True,
            message="Koltuklarınız 15 dakika süreyle ayrıldı. Ödeme ekranına yönlendiriliyorsunuz.",
            reserved_seats=cleaned_codes,
            locked_until=locked_until_str,
            redirect_route=ROUTE_PAYMENT,
            total_price=pricing["final_total"],
        )

    def join_waitlist(
        self,
        event_id: int,
        user_id: int,
        now: Optional[datetime] = None,
    ) -> Tuple[bool, str]:
        """Kontenjan dolu olduğunda kullanıcıyı bekleme listesine ekler (BR-3.2)."""
        detail = self.get_event_detail(event_id, now=now)
        if detail is None:
            return False, "Etkinlik bulunamadı."
        if detail.is_sales_closed:
            return False, "Bilet satışı kapandığı için bekleme listesine katılamazsınız."
        if not detail.is_full:
            return False, "Etkinlikte boş kontenjan mevcut, doğrudan koltuk seçebilirsiniz."

        waitlist_users = self._waitlist.setdefault(int(event_id), set())
        if int(user_id) in waitlist_users:
            return False, "Zaten bu etkinliğin bekleme listesindesiniz."

        waitlist_users.add(int(user_id))
        return True, "Bekleme listesine eklendiniz."
