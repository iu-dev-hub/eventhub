"""TG-187 organizer status in real browser sessions."""

from threading import Thread

import pytest
from playwright.sync_api import expect
from werkzeug.serving import make_server

from app.accounts.services import register_user
from app.core.db import get_db

pytestmark = pytest.mark.e2e
PASSWORD = "BrowserTest123"
ACCOUNT_PAGES = ("profile", "dashboard")
STATUS = ".organizer-approval-status"


@pytest.fixture
def status_site(app):
    with make_server("127.0.0.1", 0, app) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join()


def sign_in(page, origin, email):
    page.goto(f"{origin}/accounts/login")
    page.locator("#email").fill(email)
    page.locator("#password").fill(PASSWORD)
    page.locator("#login-submit-btn").click()
    expect(page).to_have_url(f"{origin}/accounts/dashboard")


def test_organizer_status_refreshes_in_open_tabs_and_survives_login(
    page, app, status_site, tmp_path
):
    email = "qa-status-organizer@example.com"
    with app.app_context():
        user_id = register_user(email, PASSWORD, role="organizer")["id"]
        approval = (
            get_db()
            .execute("SELECT organizer_approved FROM users WHERE id = ?", (user_id,))
            .fetchone()
        )
        assert approval[0] == 0

    sign_in(page, status_site, email)
    tabs = {"dashboard": page, "profile": page.context.new_page()}
    for name, tab in tabs.items():
        tab.set_viewport_size({"width": 320, "height": 800})
        assert tab.goto(f"{status_site}/accounts/{name}").ok
        indicator = tab.locator(STATUS)
        expect(indicator).to_be_visible()
        expect(indicator).to_have_text("Organizatör onayı Onay Bekliyor")
        box = indicator.bounding_box()
        assert box is not None
        assert 0 <= box["x"] <= box["x"] + box["width"] <= 320
        tab.screenshot(path=tmp_path / f"tg187-{name}-pending.png")

    # PR #88 only displays status. Simulate the state change in the temporary database.
    with app.app_context():
        db = get_db()
        db.execute("UPDATE users SET organizer_approved = 1 WHERE id = ?", (user_id,))
        db.commit()

    for name, tab in tabs.items():
        assert tab.reload().ok
        status = tab.locator(f"{STATUS}.is-approved")
        expect(status).to_be_visible()
        expect(status).to_have_text("Organizatör onayı Onaylandı")
        tab.screenshot(path=tmp_path / f"tg187-{name}-approved.png")

    page.goto(f"{status_site}/accounts/logout")
    page.locator('form[action="/accounts/logout"] button[type="submit"]').click()
    assert page.goto(f"{status_site}/accounts/dashboard").status == 401
    sign_in(page, status_site, email)
    for name in ACCOUNT_PAGES:
        assert page.goto(f"{status_site}/accounts/{name}").ok
        expect(page.locator(STATUS)).to_have_text("Organizatör onayı Onaylandı")


@pytest.mark.parametrize(
    ("role", "is_student"), [("participant", False), ("participant", True), ("admin", False)]
)
def test_other_roles_have_no_organizer_status(page, app, status_site, role, is_student):
    email = "qa-status-other@example.com"
    with app.app_context():
        register_user(email, PASSWORD, role=role, is_student=is_student)
    sign_in(page, status_site, email)
    for name in ACCOUNT_PAGES:
        assert page.goto(f"{status_site}/accounts/{name}").ok
        expect(page.locator(STATUS)).to_have_count(0)
        if name == "profile":
            expect(page.locator(".profile-identity").get_by_text(email, exact=True)).to_be_visible()
            if is_student:
                expect(page.get_by_text("Öğrenci Hesabı", exact=True)).to_be_visible()


def test_guest_cannot_view_organizer_status(page, status_site):
    for name in ACCOUNT_PAGES:
        assert page.goto(f"{status_site}/accounts/{name}").status == 401
        expect(page.locator(STATUS)).to_have_count(0)
