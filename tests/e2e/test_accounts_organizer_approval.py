"""TG-186 browser coverage for organizer approval."""

from threading import Thread

import pytest
from playwright.sync_api import expect
from werkzeug.serving import make_server

from app.accounts.services import register_user
from app.core.db import get_db

pytestmark = pytest.mark.e2e
APPROVAL_PAGE = "/accounts/admin/organizers"
PASSWORD = "Password123"


@pytest.fixture
def approval_site(app):
    with app.app_context():
        users = {
            name: register_user(f"{name}@example.com", PASSWORD, role=role)["id"]
            for name, role in {
                "admin": "admin",
                "pending": "organizer",
                "approved": "organizer",
                "participant": "participant",
            }.items()
        }
        db = get_db()
        db.execute("UPDATE users SET organizer_approved = 1 WHERE id = ?", (users["approved"],))
        db.commit()

    with make_server("127.0.0.1", 0, app) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}", users
        finally:
            server.shutdown()
            thread.join()


def sign_in(page, url, account):
    page.goto(f"{url}/accounts/login")
    page.locator("#email").fill(f"{account}@example.com")
    page.locator("#password").fill(PASSWORD)
    page.locator("#login-submit-btn").click()
    expect(page).to_have_url(f"{url}/accounts/dashboard")


def approval_values(app):
    with app.app_context():
        return {
            row["id"]: row["organizer_approved"]
            for row in get_db().execute("SELECT id, organizer_approved FROM users")
        }


def test_admin_approves_pending_organizer_in_browser(page, app, approval_site, tmp_path):
    url, users = approval_site
    before = approval_values(app)
    assert before[users["pending"]] == 0
    sign_in(page, url, "admin")
    page.goto(f"{url}/accounts/")
    page.get_by_role("link", name="Organizatör Onayları").click()
    expect(page).to_have_url(f"{url}{APPROVAL_PAGE}")
    expect(page.get_by_role("heading", name="Organizatör Onayları")).to_be_visible()
    expect(page.locator(".organizer-approval-card")).to_have_count(1)
    approve = page.get_by_role("button", name="pending@example.com hesabını onayla")
    expect(approve).to_be_visible()
    page.screenshot(path=tmp_path / "tg186-before-approval.png")

    action = f"{url}{APPROVAL_PAGE}/{users['pending']}/approve"
    with page.expect_response(action) as submitted:
        approve.click()
    assert submitted.value.request.method == "POST"
    assert submitted.value.status == 303
    assert submitted.value.headers["location"] == APPROVAL_PAGE
    expect(page).to_have_url(f"{url}{APPROVAL_PAGE}")
    expect(page.get_by_role("alert")).to_have_text("Organizatör onaylandı.")
    expect(page.get_by_text("Onay bekleyen organizatör bulunmuyor.")).to_be_visible()
    expect(approve).to_have_count(0)
    page.screenshot(path=tmp_path / "tg186-after-approval.png")
    assert approval_values(app) == {**before, users["pending"]: 1}

    page.goto(f"{url}/accounts/logout")
    page.locator('form[action="/accounts/logout"] button[type="submit"]').click()
    response = page.goto(f"{url}{APPROVAL_PAGE}")
    assert response.status == 401


@pytest.mark.parametrize(
    ("account", "status"), [(None, 401), ("participant", 403), ("pending", 403), ("approved", 403)]
)
def test_non_admin_cannot_access_organizer_approval(page, app, approval_site, account, status):
    url, users = approval_site
    before = approval_values(app)
    if account is not None:
        sign_in(page, url, account)

    response = page.goto(f"{url}{APPROVAL_PAGE}")
    assert response.status == status
    expect(page.get_by_role("heading", name="Organizatör Onayları")).to_have_count(0)
    response = page.request.post(f"{url}{APPROVAL_PAGE}/{users['pending']}/approve")
    assert response.status == status
    assert approval_values(app) == before
