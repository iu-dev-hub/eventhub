#!/usr/bin/env python3
"""Test script to verify that all model files can be imported and instantiated correctly."""


def test_event_model():
    """Test Event model instantiation."""
    try:
        from mobile_client.models.event import Event

        _ = Event(
            id=1,
            title="Test Event",
            category="Conference",
            venue_id=1,
            start_time="2026-12-01T10:00:00Z",
            end_time="2026-12-01T18:00:00Z",
            capacity=100,
            price=50.0,
            status="published",
            organizer_id=1,
        )
        print("PASS: Event model instantiated successfully")
        return True
    except Exception as e:
        print(f"FAIL: Event model test failed: {e}")
        return False


def test_seat_model():
    """Test Seat model instantiation."""
    try:
        from mobile_client.models.seat import Seat

        _ = Seat(
            id=1,
            event_id=1,
            seat_code="A1",
            status="available",
            locked_until=None,
        )
        print("PASS: Seat model instantiated successfully")
        return True
    except Exception as e:
        print(f"FAIL: Seat model test failed: {e}")
        return False


def test_ticket_model():
    """Test Ticket model instantiation."""
    try:
        from mobile_client.models.ticket import Ticket

        _ = Ticket(
            id=1,
            event_id=1,
            user_id=1,
            status="reserved",
            qr_code="QR123456789",
            created_at="2026-11-01T10:00:00Z",
        )
        print("PASS: Ticket model instantiated successfully")
        return True
    except Exception as e:
        print(f"FAIL: Ticket model test failed: {e}")
        return False


def test_user_model():
    """Test User model instantiation."""
    try:
        from mobile_client.models.user import User

        _ = User(
            id=1,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            role="participant",
            is_student=False,
            student_number=None,
            notify_email=True,
            avatar_url=None,
            created_at="2026-11-01T10:00:00Z",
            approved=False,
        )
        print("PASS: User model instantiated successfully")
        return True
    except Exception as e:
        print(f"FAIL: User model test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing mobile client models...")
    print("=" * 40)

    tests = [
        test_event_model,
        test_seat_model,
        test_ticket_model,
        test_user_model,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 40)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("ALL TESTS PASSED!")
        return 0
    else:
        print("SOME TESTS FAILED!")
        return 1


if __name__ == "__main__":
    exit(main())
