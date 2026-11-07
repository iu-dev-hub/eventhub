#!/usr/bin/env python3
"""Test script for EventHub mobile client shared components (TG-161).

Tests all 4 required components:
1) EventCard (event list item)
2) TicketCard (ticket list item)
3) SeatMatrix (seat layout and selection)
4) BottomNavBar (navigation bar)
"""

import os
import sys
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Mock flet if not installed in current environment
try:
    import flet as ft
except ImportError:
    mock_ft = MagicMock()
    mock_ft.Container = type("Container", (), {"__init__": lambda self, **kw: None})
    mock_ft.Column = type("Column", (), {"__init__": lambda self, **kw: None})
    mock_ft.Row = type("Row", (), {"__init__": lambda self, **kw: None})
    mock_ft.Text = type("Text", (), {"__init__": lambda self, *a, **kw: None})
    mock_ft.Icon = type("Icon", (), {"__init__": lambda self, *a, **kw: None})
    mock_ft.NavigationBar = type("NavigationBar", (), {"__init__": lambda self, **kw: None})
    mock_ft.NavigationDestination = type(
        "NavigationDestination", (), {"__init__": lambda self, **kw: None}
    )
    mock_ft.FontWeight.BOLD = "bold"
    mock_ft.FontWeight.W_500 = "w500"
    mock_ft.TextOverflow.ELLIPSIS = "ellipsis"
    mock_ft.MainAxisAlignment.SPACE_BETWEEN = "space_between"
    mock_ft.MainAxisAlignment.CENTER = "center"
    mock_ft.CrossAxisAlignment.CENTER = "center"
    mock_ft.alignment.center = "center"
    mock_ft.border.all = lambda *a, **kw: None
    mock_ft.padding.symmetric = lambda *a, **kw: None
    sys.modules["flet"] = mock_ft
    import flet as ft  # noqa: F401

from mobile_client.components.event_card import EventCard, _format_event_datetime
from mobile_client.components.navbar import BottomNavBar
from mobile_client.components.seat_matrix import SeatMatrix
from mobile_client.components.ticket_card import TicketCard
from mobile_client.models.event import Event
from mobile_client.models.seat import Seat
from mobile_client.models.ticket import Ticket


def test_event_card():
    """Verify EventCard creation and date formatting."""
    print("Testing EventCard...")
    event = Event(
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
    clicked = []
    card = EventCard(event=event, on_click=lambda ev: clicked.append(ev.id))
    card._handle_click(None)
    assert clicked == [1], "Click callback did not receive event id"

    assert _format_event_datetime("2026-11-18T20:30:00Z") == "2026-11-18 - 20:30"
    assert _format_event_datetime("2026-12-01 14:00:00") == "2026-12-01 - 14:00"
    print("PASS: EventCard tests succeeded")
    return True


def test_ticket_card():
    """Verify TicketCard active and used behavior (BUG-14)."""
    print("Testing TicketCard...")
    paid_ticket = Ticket(
        id=10,
        event_id=1,
        user_id=101,
        status="paid",
        qr_code="QR-10",
        created_at="2026-11-01T10:00:00Z",
    )
    clicked = []
    paid_card = TicketCard(ticket=paid_ticket, on_click=lambda t: clicked.append(t.id))
    paid_card._handle_click(None)
    assert clicked == [10], "Paid ticket should trigger click"

    used_ticket = Ticket(
        id=11,
        event_id=1,
        user_id=101,
        status="used",
        qr_code="QR-11",
        created_at="2026-11-01T10:00:00Z",
    )
    used_card = TicketCard(ticket=used_ticket, on_click=lambda t: clicked.append(t.id))
    used_card._handle_click(None)
    assert clicked == [10], "Used ticket must not trigger click (BUG-14)"
    print("PASS: TicketCard tests succeeded")
    return True


def test_seat_matrix():
    """Verify SeatMatrix toggling and boundary limit (BR-3.1)."""
    print("Testing SeatMatrix...")
    seats = [
        Seat(id=1, event_id=1, seat_code="A1", status="available", locked_until=None),
        Seat(id=2, event_id=1, seat_code="A2", status="available", locked_until=None),
        Seat(id=3, event_id=1, seat_code="A3", status="available", locked_until=None),
        Seat(id=4, event_id=1, seat_code="A4", status="available", locked_until=None),
        Seat(id=5, event_id=1, seat_code="A5", status="available", locked_until=None),
        Seat(id=6, event_id=1, seat_code="B1", status="occupied", locked_until=None),
    ]
    selections = []
    matrix = SeatMatrix(
        seats=seats,
        on_selection_change=lambda s: selections.append(list(s)),
        max_selection=4,
    )

    # Select 4 seats
    for code in ["A1", "A2", "A3", "A4"]:
        matrix._toggle_seat(code)
    assert len(matrix.selected_codes) == 4, "Should have 4 selected seats"

    # 5th seat must be rejected
    matrix._toggle_seat("A5")
    assert len(matrix.selected_codes) == 4, "5th seat should be rejected"
    assert "A5" not in matrix.selected_codes

    # Deselect A1
    matrix._toggle_seat("A1")
    assert len(matrix.selected_codes) == 3
    print("PASS: SeatMatrix tests succeeded")
    return True


def test_navbar():
    """Verify BottomNavBar destinations."""
    print("Testing BottomNavBar...")
    nav = BottomNavBar(selected_index=0)
    assert nav.selected_index == 0
    print("PASS: BottomNavBar tests succeeded")
    return True


def main():
    print("=" * 50)
    print("Running Mobile Client Shared Components Tests (TG-161)...")
    print("=" * 50)
    tests = [test_event_card, test_ticket_card, test_seat_matrix, test_navbar]
    passed = 0
    for t in tests:
        if t():
            passed += 1
        print()

    print("=" * 50)
    print(f"Components Tests Passed: {passed}/{len(tests)}")
    print("=" * 50)
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())
