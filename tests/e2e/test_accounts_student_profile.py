"""TG-170 browser coverage for profile identity and declared student status."""

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize("width", [320, 1280])
@pytest.mark.parametrize(
    ("case", "is_student", "number", "role", "role_label"),
    [
        ("number", True, "120501099", "participant", "Katılımcı"),
        ("null", True, None, "participant", "Katılımcı"),
        ("blank", True, "", "participant", "Katılımcı"),
        ("nonstudent", False, None, "organizer", "Organizatör"),
    ],
)
def test_profile_shows_current_account(page, width, case, is_student, number, role, role_label):
    page.set_viewport_size({"width": width, "height": 800})
    email = f"qa-profile-{case}-{width}@example.com"
    credentials = {"email": email, "password": "BrowserTest123"}
    registration = page.request.post(
        "/accounts/register",
        data={
            **credentials,
            "first_name": "Deniz",
            "last_name": "Kaya",
            "is_student": is_student,
            "student_number": number,
            "role": role,
            "terms_accepted": True,
        },
    )
    assert registration.status == 201
    assert page.request.post("/accounts/login", data=credentials).ok

    response = page.goto("/accounts/profile")
    assert response is not None
    assert response.ok
    card = page.locator(".profile-card")
    expect(card.get_by_role("heading", name="Deniz Kaya", exact=True)).to_be_visible()
    expect(card.get_by_text(email, exact=True)).to_be_visible()
    expect(card.locator("#role")).to_have_value(role_label)
    expect(card.get_by_text("e2e-organizer@example.com", exact=True)).to_have_count(0)
    badge = card.get_by_text("Öğrenci Hesabı", exact=True)
    if is_student:
        expect(badge).to_be_visible()
    else:
        expect(badge).to_have_count(0)
        expect(card.get_by_text("Öğrenci beyanı yok")).to_be_visible()
    if number:
        expect(card.get_by_text(f"Öğrenci no. {number}")).to_be_visible()
    else:
        expect(card.get_by_text("Öğrenci no.")).to_have_count(0)

    box = card.bounding_box()
    assert box is not None
    assert box["x"] >= 0
    assert box["x"] + box["width"] <= width
