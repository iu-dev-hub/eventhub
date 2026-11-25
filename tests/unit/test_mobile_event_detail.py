"""Unit tests for mobile event details, seat selection, reservation, and Business Rules (TG-184)."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mobile_client.core.routes import (
    ROUTE_EVENT_DETAIL,
    ROUTE_PAYMENT,
    normalize_route,
)
from mobile_client.models.event import Event
from mobile_client.models.seat import Seat
from mobile_client.services.participation_service import (
    ParticipationService,
    calculate_price_summary,
    is_event_sales_closed,
    is_seat_lock_expired,
)


@pytest.fixture
def mock_api_dir(tmp_path: Path) -> Path:
    """Testler için izole ../app/api JSON dosyaları oluşturur."""
    events = [
        {
            "id": 1,
            "title": "Yazılım Doğrulama Konferansı",
            "category": "Eğitim",
            "venue_id": 1,
            "start_time": "2026-06-20T12:00:00Z",
            "end_time": "2026-06-20T18:00:00Z",
            "capacity": 10,
            "price": 100.0,
            "status": "published",
            "organizer_id": 1,
        },
        {
            "id": 2,
            "title": "Dolu Etkinlik",
            "category": "Teknoloji",
            "venue_id": 2,
            "start_time": "2026-06-25T15:00:00Z",
            "end_time": "2026-06-25T17:00:00Z",
            "capacity": 2,
            "price": 0.0,
            "status": "published",
            "organizer_id": 1,
        },
        {
            "id": 3,
            "title": "Taslak Etkinlik",
            "category": "Eğitim",
            "venue_id": 1,
            "start_time": "2026-07-01T10:00:00Z",
            "end_time": "2026-07-01T12:00:00Z",
            "capacity": 50,
            "price": 50.0,
            "status": "draft",
            "organizer_id": 1,
        },
    ]
    venues = [
        {
            "id": 1,
            "name": "Konferans Salonu A",
            "address": "İTÜ Ayazağa Kampüsü, İstanbul",
            "capacity": 500,
        },
        {
            "id": 2,
            "name": "Seminer Salonu B",
            "address": "Maslak, İstanbul",
            "capacity": 100,
        },
    ]
    seats = [
        {"id": 1, "event_id": 1, "seat_code": "A1", "status": "sold", "locked_until": None},
        {"id": 2, "event_id": 1, "seat_code": "A2", "status": "available", "locked_until": None},
        {"id": 3, "event_id": 1, "seat_code": "A3", "status": "available", "locked_until": None},
        {"id": 4, "event_id": 1, "seat_code": "A4", "status": "available", "locked_until": None},
        {"id": 5, "event_id": 1, "seat_code": "A5", "status": "available", "locked_until": None},
        {"id": 6, "event_id": 1, "seat_code": "A6", "status": "available", "locked_until": None},
        {
            "id": 7,
            "event_id": 1,
            "seat_code": "B1",
            "status": "locked",
            "locked_until": "2026-06-01T10:15:00Z",
        },
        {"id": 8, "event_id": 2, "seat_code": "A1", "status": "sold", "locked_until": None},
        {"id": 9, "event_id": 2, "seat_code": "A2", "status": "sold", "locked_until": None},
    ]
    tickets = [
        {
            "id": 1,
            "event_id": 1,
            "user_id": 20,
            "status": "paid",
            "qr_code": "QR-1",
            "created_at": "2026-06-01T09:00:00Z",
        },
        {
            "id": 2,
            "event_id": 2,
            "user_id": 21,
            "status": "paid",
            "qr_code": "QR-2",
            "created_at": "2026-06-01T09:00:00Z",
        },
        {
            "id": 3,
            "event_id": 2,
            "user_id": 22,
            "status": "paid",
            "qr_code": "QR-3",
            "created_at": "2026-06-01T09:00:00Z",
        },
    ]

    (tmp_path / "events.json").write_text(json.dumps(events), encoding="utf-8")
    (tmp_path / "venues.json").write_text(json.dumps(venues), encoding="utf-8")
    (tmp_path / "seats.json").write_text(json.dumps(seats), encoding="utf-8")
    (tmp_path / "tickets.json").write_text(json.dumps(tickets), encoding="utf-8")
    return tmp_path


def test_default_api_event_detail_loads_venue_and_counts():
    """../app/api altındaki gerçek JSON dosyalarından etkinlik detayı çekilebilmelidir."""
    service = ParticipationService()
    detail = service.get_event_detail(1)

    assert detail is not None
    assert detail.event.id == 1
    assert detail.venue_name == "Konferans Salonu A"
    assert "İTÜ" in detail.venue_address
    assert detail.participant_count >= 2
    assert detail.remaining_capacity == detail.event.capacity - detail.participant_count
    assert len(detail.seats) == 3
    assert detail.description != ""


def test_get_event_detail_returns_none_for_unknown_id(mock_api_dir: Path):
    """Var olmayan etkinlik ID'si için None döndürülmelidir."""
    service = ParticipationService(api_dir=mock_api_dir)
    assert service.get_event_detail(999) is None


@pytest.mark.parametrize(
    ("now_str", "expected_closed"),
    [
        ("2026-06-20T10:59:00Z", False),  # Başlangıca 61 dk var -> Açık
        ("2026-06-20T11:00:00Z", True),  # Başlangıca tam 60 dk var -> Kapalı (BR-3.3)
        ("2026-06-20T11:01:00Z", True),  # Başlangıca 59 dk var -> Kapalı (BR-3.3)
        ("2026-06-20T13:00:00Z", True),  # Başlangıç geçmiş -> Kapalı
    ],
)
def test_sales_closing_60_minutes_boundary_values_br_3_3(now_str: str, expected_closed: bool):
    """BR-3.3: Bilet satışı başlangıçtan tam 60 dk önce kapanmalıdır (BVA: 61, 60, 59 dk)."""
    event = Event(
        id=1,
        title="Sınır Değer Testi",
        category="Eğitim",
        venue_id=1,
        start_time="2026-06-20T12:00:00Z",
        end_time="2026-06-20T15:00:00Z",
        capacity=100,
        price=50.0,
        status="published",
        organizer_id=1,
    )
    now_dt = datetime.fromisoformat(now_str.replace("Z", "+00:00"))
    assert is_event_sales_closed(event, now=now_dt) is expected_closed


def test_seat_lock_expiration_15_minutes_boundary_br_3_5(mock_api_dir: Path):
    """BR-3.5: 15 dakikalık rezervasyon süresi dolan koltuk serbest bırakılmalıdır."""
    service = ParticipationService(api_dir=mock_api_dir)

    # B1 koltuğu 2026-06-01T10:15:00Z'ye kadar kilitli
    before_expiry = datetime(2026, 6, 1, 10, 14, 59, tzinfo=timezone.utc)
    seats_before = {s.seat_code: s for s in service.get_event_seats(1, now=before_expiry)}
    assert seats_before["B1"].status == "locked"

    at_expiry = datetime(2026, 6, 1, 10, 15, 0, tzinfo=timezone.utc)
    seats_after = {s.seat_code: s for s in service.get_event_seats(1, now=at_expiry)}
    assert seats_after["B1"].status == "available"
    assert seats_after["B1"].locked_until is None

    # Doğrudan yardımcı fonksiyon sınır testi
    seat_no_time = Seat(id=1, event_id=1, seat_code="C1", status="locked", locked_until="")
    assert is_seat_lock_expired(seat_no_time, now=at_expiry) is True


def test_reserve_seats_and_payment_redirect_success(mock_api_dir: Path):
    """Geçerli koltuk seçiminde Satın Al koltukları 15 dk ayırmalı ve /payment'a yönlendirmeli."""
    service = ParticipationService(api_dir=mock_api_dir)
    now_dt = datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

    result = service.reserve_seats_for_purchase(
        event_id=1,
        seat_codes=["A2", "A3"],
        user_id=50,
        now=now_dt,
        persist=True,
    )

    assert result.success is True
    assert result.redirect_route == ROUTE_PAYMENT
    assert result.reserved_seats == ["A2", "A3"]
    assert result.locked_until == "2026-06-01T10:15:00Z"
    # Etkinliğe 19 gün var (>= 14 gün -> BR-4.1 %20 erken kayıt indirimi: 2 * 100 * 0.8 = 160.0)
    assert result.total_price == 160.0

    # Koltuklar artık kilitli olmalı ve tekrar seçilememeli
    retry = service.reserve_seats_for_purchase(
        event_id=1,
        seat_codes=["A2"],
        user_id=51,
        now=now_dt,
    )
    assert retry.success is False
    assert retry.error_code == "SEAT_UNAVAILABLE"


def test_max_4_tickets_per_user_across_multiple_orders_br_3_1(mock_api_dir: Path):
    """BR-3.1: Kullanıcı tek seferde veya parçalı siparişlerde toplam 4 bileti aşamaz."""
    service = ParticipationService(api_dir=mock_api_dir)
    now_dt = datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

    # Tek siparişte 5 koltuk reddedilmeli
    res_five = service.reserve_seats_for_purchase(
        event_id=1,
        seat_codes=["A2", "A3", "A4", "A5", "A6"],
        user_id=77,
        now=now_dt,
    )
    assert res_five.success is False
    assert res_five.error_code == "MAX_TICKETS_EXCEEDED"

    # İlk siparişte 3 koltuk başarılı olmalı
    res_three = service.reserve_seats_for_purchase(
        event_id=1,
        seat_codes=["A2", "A3", "A4"],
        user_id=77,
        now=now_dt,
    )
    assert res_three.success is True

    # Aynı kullanıcının 2 koltuk daha almaya çalışması (3 + 2 = 5 > 4) reddedilmeli
    res_two_more = service.reserve_seats_for_purchase(
        event_id=1,
        seat_codes=["A5", "A6"],
        user_id=77,
        now=now_dt,
    )
    assert res_two_more.success is False
    assert res_two_more.error_code == "MAX_TICKETS_EXCEEDED"

    # Ancak 1 koltuk daha alması (3 + 1 = 4) kabul edilmeli
    res_fourth = service.reserve_seats_for_purchase(
        event_id=1,
        seat_codes=["A5"],
        user_id=77,
        now=now_dt,
    )
    assert res_fourth.success is True


def test_empty_sold_and_sales_closed_rejections(mock_api_dir: Path):
    """Boş koltuk, satılmış koltuk, taslak etkinlik ve kapanmış satış reddedilmelidir."""
    service = ParticipationService(api_dir=mock_api_dir)
    now_dt = datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

    # Boş seçim
    empty_res = service.reserve_seats_for_purchase(1, [], user_id=10, now=now_dt)
    assert empty_res.success is False
    assert empty_res.error_code == "EMPTY_SELECTION"

    # Satılmış koltuk (A1)
    sold_res = service.reserve_seats_for_purchase(1, ["A1"], user_id=10, now=now_dt)
    assert sold_res.success is False
    assert sold_res.error_code == "SEAT_UNAVAILABLE"

    # Taslak etkinlik (id=3)
    draft_res = service.reserve_seats_for_purchase(3, ["A1"], user_id=10, now=now_dt)
    assert draft_res.success is False
    assert draft_res.error_code == "EVENT_NOT_PUBLISHED"

    # Satışı kapanmış etkinlik (başlangıca 30 dk kala)
    closed_time = datetime(2026, 6, 20, 11, 30, 0, tzinfo=timezone.utc)
    closed_res = service.reserve_seats_for_purchase(1, ["A2"], user_id=10, now=closed_time)
    assert closed_res.success is False
    assert closed_res.error_code == "SALES_CLOSED"


def test_full_capacity_stops_sales_and_allows_waitlist_br_3_2(mock_api_dir: Path):
    """BR-3.2: Kontenjan dolduğunda satış durmalı ve bekleme listesine katılınabilmelidir."""
    service = ParticipationService(api_dir=mock_api_dir)
    now_dt = datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

    detail_full = service.get_event_detail(2, now=now_dt)
    assert detail_full is not None
    assert detail_full.is_full is True
    assert detail_full.remaining_capacity == 0

    # Satın alma reddedilmeli
    res = service.reserve_seats_for_purchase(2, ["A1"], user_id=99, now=now_dt)
    assert res.success is False
    assert res.error_code == "CAPACITY_FULL"

    # Bekleme listesine katılım başarılı olmalı
    ok, msg = service.join_waitlist(2, user_id=99, now=now_dt)
    assert ok is True
    assert "Bekleme listesine eklendiniz" in msg

    # Aynı kullanıcı tekrar katılmak isterse uyarılmalı
    ok_dup, _ = service.join_waitlist(2, user_id=99, now=now_dt)
    assert ok_dup is False

    # Kontenjanı dolu olmayan etkinlikte bekleme listesi reddedilmeli
    ok_open, _ = service.join_waitlist(1, user_id=99, now=now_dt)
    assert ok_open is False


def test_price_calculation_decision_table_br_4_1_4_2_4_6():
    """BR-4.1 (%20 erken kayıt), BR-4.2 (%25 öğrenci) ve BR-4.6 (ücretsiz) karar tablosu."""
    paid_event = Event(
        id=1,
        title="Ücretli Etkinlik",
        category="Eğitim",
        venue_id=1,
        start_time="2026-06-20T12:00:00Z",
        end_time="2026-06-20T15:00:00Z",
        capacity=100,
        price=100.0,
        status="published",
        organizer_id=1,
    )
    free_event = Event(
        id=2,
        title="Ücretsiz Etkinlik",
        category="Eğitim",
        venue_id=1,
        start_time="2026-06-20T12:00:00Z",
        end_time="2026-06-20T15:00:00Z",
        capacity=100,
        price=0.0,
        status="published",
        organizer_id=1,
    )

    early_now = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)  # 19 gün var (>= 14)
    late_now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)  # 5 gün var (< 14)

    # Normal (geç kayıt, öğrenci değil) -> 100 TL
    p1 = calculate_price_summary(paid_event, 1, is_student=False, now=late_now)
    assert p1["final_total"] == 100.0

    # Erken kayıt (%20) -> 80 TL
    p2 = calculate_price_summary(paid_event, 1, is_student=False, now=early_now)
    assert p2["final_total"] == 80.0

    # Öğrenci (%25, geç kayıt) -> 75 TL
    p3 = calculate_price_summary(paid_event, 1, is_student=True, now=late_now)
    assert p3["final_total"] == 75.0

    # Ücretsiz etkinlik -> 0 TL
    p4 = calculate_price_summary(free_event, 2, is_student=True, now=early_now)
    assert p4["is_free"] is True
    assert p4["final_total"] == 0.0


def test_new_routes_normalize_properly():
    """/event-detail ve /payment rotaları normalize_route tarafından korunmalıdır."""
    assert normalize_route(ROUTE_EVENT_DETAIL) == ROUTE_EVENT_DETAIL
    assert normalize_route(ROUTE_PAYMENT) == ROUTE_PAYMENT


def test_event_detail_and_payment_view_with_flet(mock_api_dir: Path):
    """Flet kuruluysa detay görünümü, koltuk seçimi ve ödeme ekranına yönlendirme doğrulanır."""
    pytest.importorskip("flet")
    from mobile_client.views.event_detail_view import (
        build_event_detail_view,
        build_payment_view,
    )

    service = ParticipationService(api_dir=mock_api_dir)
    redirected = []

    view = build_event_detail_view(
        event_id=1,
        participation_service=service,
        on_purchase_success=lambda res: redirected.append(res),
        now=datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
    )

    assert view.route == ROUTE_EVENT_DETAIL
    matrix = view.data["seat_matrix"]
    matrix._toggle_seat("A2")
    assert view.data["selected_seats"] == ["A2"]

    res = view.data["trigger_purchase"]()
    assert res.success is True
    assert len(redirected) == 1
    assert redirected[0].redirect_route == ROUTE_PAYMENT

    pay_view = build_payment_view(reservation=res)
    assert pay_view.route == ROUTE_PAYMENT
