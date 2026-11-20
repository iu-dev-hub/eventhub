"""TG-169 browser coverage for account home navigation and responsive controls."""

import re
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e

GUEST_LINKS = {
    "Giriş Yap": "login",
    "Kayıt Ol": "register",
    "Şifremi Unuttum": "forgot-password",
}
MEMBER_LINKS = {"Profilim": "profile", "Ayarlar": "settings", "Şifre Değiştir": "change-password"}


def test_guest_links_are_tappable_on_narrow_screen(browser, base_url):
    with browser.new_context(
        base_url=base_url,
        viewport={"width": 320, "height": 720},
        has_touch=True,
        is_mobile=True,
    ) as context:
        page = context.new_page()
        response = page.goto("/accounts")
        assert response is not None
        assert response.ok
        expect(page).to_have_url(re.compile(r"/accounts/$"))
        nav = page.get_by_role("navigation", name="Hesap işlemleri")
        expect(nav.get_by_role("link")).to_have_count(len(GUEST_LINKS))
        previous_bottom = 0
        for label, target in GUEST_LINKS.items():
            link = nav.get_by_role("link", name=label, exact=True)
            box = link.bounding_box()
            assert box is not None
            assert box["height"] >= 44
            assert box["y"] >= previous_bottom
            previous_bottom = box["y"] + box["height"]
            with page.expect_navigation() as navigation:
                link.tap()
            assert navigation.value.ok
            assert urlsplit(page.url).path == f"/accounts/{target}"
            page.goto("/accounts/")


@pytest.mark.parametrize(("label", "target"), MEMBER_LINKS.items())
def test_signed_in_account_home_links_open_with_keyboard(organizer_page, label, target):
    page = organizer_page
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto("/accounts/")
    nav = page.get_by_role("navigation", name="Hesap işlemleri")
    expect(nav.get_by_role("link")).to_have_count(len(MEMBER_LINKS))
    link = nav.get_by_role("link", name=label, exact=True)
    link.focus()
    expect(link).to_be_focused()
    with page.expect_navigation() as navigation:
        page.keyboard.press("Enter")
    assert navigation.value.ok
    assert urlsplit(page.url).path == f"/accounts/{target}"
