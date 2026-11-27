"""TG-188: organizer approval across Accounts and Events."""

import re
from datetime import datetime, timedelta
from threading import Thread

import pytest
from playwright.sync_api import expect
from werkzeug.serving import make_server

from app.accounts.services import register_user
from app.core.db import get_db

pytestmark = pytest.mark.e2e
PASSWORD = "BrowserTest123"
ADMIN_EMAIL = "tg188-admin@example.com"
ORGANIZER_EMAIL = "tg188-organizer@example.com"
APPROVAL_PAGE = "/accounts/admin/organizers"
EVENT_TITLE = "TG-188 QA Semineri"
ACCOUNT_PAGES = ("/accounts/profile", "/accounts/dashboard")


@pytest.fixture
def workflow_site(app):
    with app.app_context():
        register_user(ADMIN_EMAIL, PASSWORD, role="admin")
        register_user("tg188-other@example.com", PASSWORD, role="organizer")
        db = get_db()
        db.execute(
            "INSERT INTO venues (id, name, address, capacity) VALUES (1, 'QA Salon', 'Ankara', 100)"
        )
        db.commit()

    with make_server("127.0.0.1", 0, app) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join()


def sign_in(page, origin, email):
    page.goto("/accounts/login")
    page.locator("#email").fill(email)
    page.locator("#password").fill(PASSWORD)
    page.locator("#login-submit-btn").click()
    expect(page).to_have_url(f"{origin}/accounts/dashboard")


def approval_values(app):
    with app.app_context():
        return {
            row["id"]: row["organizer_approved"]
            for row in get_db().execute("SELECT id, organizer_approved FROM users")
        }


def test_admin_approval_updates_organizer_session_and_enables_events(
    browser, app, workflow_site, tmp_path
):
    with (
        browser.new_context(base_url=workflow_site) as organizer,
        browser.new_context(base_url=workflow_site) as admin,
    ):
        page = organizer.new_page()
        registration = page.request.post(
            "/accounts/register",
            data={
                "email": ORGANIZER_EMAIL,
                "password": PASSWORD,
                "role": "organizer",
                "terms_accepted": True,
            },
        )
        assert registration.status == 201
        organizer_id = registration.json()["user"]["id"]
        assert approval_values(app)[organizer_id] == 0
        sign_in(page, workflow_site, ORGANIZER_EMAIL)

        dashboard = page
        profile = organizer.new_page()
        for tab, path in ((profile, ACCOUNT_PAGES[0]), (dashboard, ACCOUNT_PAGES[1])):
            assert tab.goto(path).ok
            expect(tab.locator(".organizer-approval-status")).to_have_text(
                "Organizatör onayı Onay Bekliyor"
            )
            tab.screenshot(path=tmp_path / f"{path.rsplit('/', 1)[1]}-pending.png")

        events = organizer.new_page()
        assert events.goto("/events/create").status == 403
        start = (datetime.now() + timedelta(days=7)).replace(hour=10, minute=0)
        event_form = {
            "title": EVENT_TITLE,
            "category": "Eğitim",
            "venue_id": "1",
            "start_time": start.isoformat(timespec="minutes"),
            "end_time": (start + timedelta(hours=2)).isoformat(timespec="minutes"),
            "capacity": "50",
            "price": "100",
        }
        assert events.request.post("/events/create", form=event_form).status == 403
        with app.app_context():
            assert get_db().execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0

        admin_page = admin.new_page()
        sign_in(admin_page, workflow_site, ADMIN_EMAIL)
        assert admin_page.goto(APPROVAL_PAGE).ok
        approve = admin_page.get_by_role("button", name=f"{ORGANIZER_EMAIL} hesabını onayla")
        expect(approve).to_be_visible()
        admin_page.screenshot(path=tmp_path / "admin-pending.png")
        before = approval_values(app)
        action = f"{workflow_site}{APPROVAL_PAGE}/{organizer_id}/approve"
        with admin_page.expect_response(action) as submitted:
            approve.click()
        assert submitted.value.request.method == "POST"
        assert submitted.value.status == 303
        assert submitted.value.headers["location"] == APPROVAL_PAGE
        expect(admin_page.get_by_role("alert")).to_have_text("Organizatör onaylandı.")
        expect(approve).to_have_count(0)
        expect(
            admin_page.get_by_role("button", name="tg188-other@example.com hesabını onayla")
        ).to_be_visible()
        assert approval_values(app) == {**before, organizer_id: 1}
        admin_page.screenshot(path=tmp_path / "admin-approved.png")

        for tab in (profile, dashboard):
            assert tab.reload().ok
            expect(tab.locator(".organizer-approval-status.is-approved")).to_have_text(
                "Organizatör onayı Onaylandı"
            )
            tab.screenshot(path=tmp_path / f"{tab.url.rsplit('/', 1)[1]}-approved.png")

        assert events.goto("/events/create").ok
        events.get_by_label("Etkinlik Başlığı").fill(event_form["title"])
        events.get_by_label("Kategori").select_option(event_form["category"])
        events.get_by_label("Salon").select_option(event_form["venue_id"])
        events.get_by_label("Başlangıç Tarihi ve Saati").fill(event_form["start_time"])
        events.get_by_label("Bitiş Tarihi ve Saati").fill(event_form["end_time"])
        events.get_by_label("Etkinlik Kapasitesi").fill(event_form["capacity"])
        events.get_by_label("Bilet Fiyatı (TL)").fill(event_form["price"])
        events.get_by_role("button", name="Taslak Kaydet").click()
        expect(events).to_have_url(f"{workflow_site}/events/")
        expect(events.get_by_role("alert")).to_have_text(
            re.compile(r"^Taslak etkinlik kaydedildi\. \(Etkinlik No: \d+\)$")
        )
        with app.app_context():
            draft = (
                get_db()
                .execute(
                    "SELECT id, status, organizer_id FROM events WHERE title = ?", (EVENT_TITLE,)
                )
                .fetchone()
            )
            event_id = draft["id"]
            assert (draft["status"], draft["organizer_id"]) == ("draft", organizer_id)

        # Publishing exercises the Events regression contract.
        events.screenshot(path=tmp_path / "event-draft.png")
        publish_path = f"/events/{event_id}/publish"
        with events.expect_response(f"{workflow_site}{publish_path}") as published:
            events.locator(f'form[action="{publish_path}"]').get_by_role(
                "button", name="Yayınla"
            ).click()
        assert published.value.request.method == "POST"
        assert published.value.status == 302
        assert published.value.headers["location"] == "/events/"
        expect(events.get_by_role("alert")).to_have_text(
            f"Etkinlik başarıyla yayınlandı. (Etkinlik No: {event_id})"
        )
        with app.app_context():
            event = (
                get_db()
                .execute("SELECT status, organizer_id FROM events WHERE id = ?", (event_id,))
                .fetchone()
            )
            assert (event["status"], event["organizer_id"]) == ("published", organizer_id)
        events.screenshot(path=tmp_path / "event-published.png")

        page.goto("/accounts/logout")
        page.locator('form[action="/accounts/logout"] button[type="submit"]').click()
        assert page.goto("/accounts/profile").status == 401
        sign_in(page, workflow_site, ORGANIZER_EMAIL)
        for path in ACCOUNT_PAGES:
            assert page.goto(path).ok
            expect(page.locator(".organizer-approval-status")).to_have_text(
                "Organizatör onayı Onaylandı"
            )
