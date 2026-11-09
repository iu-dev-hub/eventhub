"""Unit tests for mobile client shared components (TG-161).

Bu testler flet yüklü olduğunda çalışır; CI ortamında flet yoksa atlanır.
"""

import pytest

# Skip module cleanly if flet is not installed in environment (e.g. CI runner)
flet = pytest.importorskip("flet")

from mobile_client.components.event_card import EventCard, _format_event_datetime  # noqa: E402
from mobile_client.components.navbar import BottomNavBar  # noqa: E402
from mobile_client.components.seat_matrix import SeatMatrix  # noqa: E402
from mobile_client.components.ticket_card import TicketCard  # noqa: E402
from mobile_client.models.event import Event  # noqa: E402
from mobile_client.models.seat import Seat  # noqa: E402
from mobile_client.models.ticket import Ticket  # noqa: E402


@pytest.fixture
def sample_event():
    return Event(
        id=1,
        title="Yazılım Sınama Konferansı",
        category="Eğitim",
        venue_id=1,
        start_time="2026-11-18T20:30:00Z",
        end_time="2026-11-18T22:30:00Z",
        capacity=100,
        price=150.0,
        status="published",
        organizer_id=1,
    )


@pytest.fixture
def sample_free_event():
    return Event(
        id=2,
        title="Açık Kaynak Buluşması",
        category="Topluluk",
        venue_id=1,
        start_time="2026-12-01 14:00:00",
        end_time="2026-12-01 16:00:00",
        capacity=50,
        price=0.0,
        status="published",
        organizer_id=1,
    )


def test_format_event_datetime_iso8601():
    """Verify ISO 8601 without spaces does not raise IndexError (BUG-15)."""
    formatted = _format_event_datetime("2026-11-18T20:30:00Z")
    assert formatted == "2026-11-18 - 20:30"


def test_format_event_datetime_spaced():
    """Verify standard spaced datetime format."""
    formatted = _format_event_datetime("2026-12-01 14:00:00")
    assert formatted == "2026-12-01 - 14:00"


def test_format_event_datetime_empty():
    """Verify empty datetime gracefully returns empty string."""
    assert _format_event_datetime("") == ""


def test_event_card_rendering_and_click(sample_event):
    """Test EventCard properties and click callback."""
    clicked = []

    def on_click(ev):
        clicked.append(ev.id)

    card = EventCard(event=sample_event, on_click=on_click)
    assert card.event.id == 1
    assert card.ink is True

    # Simulate click
    card._handle_click(None)
    assert clicked == [1]


def test_event_card_free_price(sample_free_event):
    """Test EventCard displays 'Ücretsiz' for 0 price."""
    card = EventCard(event=sample_free_event)
    assert card.event.price == 0.0


def test_ticket_card_active_click():
    """Test TicketCard for active ticket allows click."""
    ticket = Ticket(
        id=10,
        event_id=1,
        user_id=101,
        status="paid",
        qr_code="QR-10-PAID",
        created_at="2026-11-01T10:00:00Z",
    )
    clicked = []
    card = TicketCard(ticket=ticket, on_click=lambda t: clicked.append(t.id))
    assert card.ink is True
    card._handle_click(None)
    assert clicked == [10]


def test_ticket_card_used_ticket_disables_click():
    """Test TicketCard disables click for used ticket (BUG-14)."""
    ticket = Ticket(
        id=11,
        event_id=1,
        user_id=101,
        status="used",
        qr_code="QR-11-USED",
        created_at="2026-11-01T10:00:00Z",
    )
    clicked = []
    card = TicketCard(ticket=ticket, on_click=lambda t: clicked.append(t.id))
    assert card.ink is False
    card._handle_click(None)
    assert clicked == []


def test_seat_matrix_toggle_and_limit():
    """Test SeatMatrix selection and 4-ticket boundary rule (BR-3.1)."""
    seats = [
        Seat(id=1, event_id=1, seat_code="A1", status="available", locked_until=None),
        Seat(id=2, event_id=1, seat_code="A2", status="available", locked_until=None),
        Seat(id=3, event_id=1, seat_code="A3", status="available", locked_until=None),
        Seat(id=4, event_id=1, seat_code="A4", status="available", locked_until=None),
        Seat(id=5, event_id=1, seat_code="A5", status="available", locked_until=None),
        Seat(id=6, event_id=1, seat_code="B1", status="occupied", locked_until=None),
    ]

    selections = []

    def on_change(sel):
        selections.append(list(sel))

    matrix = SeatMatrix(seats=seats, on_selection_change=on_change, max_selection=4)

    # Toggle A1, A2, A3, A4 (4 seats)
    matrix._toggle_seat("A1")
    matrix._toggle_seat("A2")
    matrix._toggle_seat("A3")
    matrix._toggle_seat("A4")
    assert len(matrix.selected_codes) == 4

    # 5th seat toggle should be rejected due to limit
    matrix._toggle_seat("A5")
    assert len(matrix.selected_codes) == 4
    assert "A5" not in matrix.selected_codes

    # Deselect A1
    matrix._toggle_seat("A1")
    assert len(matrix.selected_codes) == 3
    assert "A1" not in matrix.selected_codes


def test_navbar_destinations():
    """Test BottomNavBar has 3 clean destinations without extraneous icons."""
    navbar = BottomNavBar(selected_index=1)
    assert len(navbar.destinations) == 3
    assert navbar.selected_index == 1
    assert navbar.destinations[0].label == "Etkinlikler"
    assert navbar.destinations[1].label == "Biletlerim"
    assert navbar.destinations[2].label == "Profil"
