"""TG-168 browser coverage for returning from and cancelling account forms."""

import re

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize("form", ["login", "register"])
def test_guest_can_return_from_auth_form_on_mobile(page, form):
    page.set_viewport_size({"width": 320, "height": 720})
    page.goto(f"/accounts/{form}")
    page.locator('input[name="email"]').fill("qa-draft@example.com")
    page.get_by_role("link", name="Hesaplara Dön", exact=True).click()
    expect(page).to_have_url(re.compile(r"/accounts/$"))
    expect(page.get_by_role("heading", name="Hesap Yönetimi")).to_be_visible()


def test_password_form_returns_to_dashboard(organizer_page):
    organizer_page.goto("/accounts/change-password")
    organizer_page.get_by_role("link", name="Panele Geri Dön").click()
    expect(organizer_page).to_have_url(re.compile(r"/accounts/dashboard$"))


@pytest.mark.parametrize(
    ("path", "form_id", "field", "draft"),
    [
        ("profile", "profile-form", "first_name", "Kaydedilmemiş ad"),
        ("settings", "password-form", "new_password", "UnsavedPass123"),
        ("settings", "preferences-form", "notify_email", None),
    ],
)
def test_cancel_does_not_submit_account_changes(organizer_page, path, form_id, field, draft):
    page = organizer_page
    page.set_viewport_size({"width": 320, "height": 720})
    url = f"/accounts/{path}"
    page.goto(url)
    form = page.locator(f"#{form_id}")
    control = form.locator(f'[name="{field}"]')
    if draft is None:
        original = control.is_checked()
        control.set_checked(not original)
    else:
        original = control.input_value()
        control.fill(draft)

    posts = []

    def record_post(request):
        if request.method == "POST":
            posts.append(request.url)

    page.on("request", record_post)
    form.get_by_role("link", name="İptal", exact=True).click()
    expect(page).to_have_url(re.compile(r"/accounts/$"))
    assert posts == []

    page.goto(url)
    if draft is None:
        expect(control).to_be_checked(checked=original)
    else:
        expect(control).to_have_value(original)


@pytest.mark.parametrize("path", ["settings", "change-password"])
def test_private_forms_reject_guest_navigation(page, path):
    response = page.goto(f"/accounts/{path}")
    assert response is not None
    assert response.status == 401
