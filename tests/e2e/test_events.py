"""Events modülü uçtan uca (E2E) testleri - Görev #119 (#32 PB-08).

Yerelde çalıştırma:
    pytest tests/e2e/test_events.py
    pytest tests/e2e/test_events.py --headed
"""

import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

SUCCESS_MSG = "Etkinlik bilgileri doğrulandı. (Kayıt işlemi Sprint 2'de yapılacaktır.)"
CAPACITY_EXCEEDED_MSG = "Etkinlik kapasitesi (101), salon kapasitesini (100) aşamaz."


def fill_form(page: Page, capacity: str, price: str = "100"):
    page.goto("/events/create")
    page.get_by_label("Etkinlik Başlığı").fill("Yazılım Semineri")
    page.get_by_label("Kategori").select_option("Eğitim")
    
    # Salon seçimi doğrudan venue_id (value="1") üzerinden yapılıyor ve doğrulanıyor
    venue_select = page.get_by_label("Salon")
    venue_select.select_option(value="1")
    expect(venue_select).to_have_value("1")
    
    page.get_by_label("Başlangıç Tarihi ve Saati").fill("2026-12-01T10:00")
    page.get_by_label("Bitiş Tarihi ve Saati").fill("2026-12-01T12:00")
    page.get_by_label("Etkinlik Kapasitesi").fill(capacity)
    page.get_by_label("Bilet Fiyatı (TL)").fill(price)


def test_create_form_page_opens(page: Page):
    page.goto("/events/create")
    expect(page).to_have_title(re.compile("Etkinlik Oluştur"))
    expect(page.get_by_role("heading", level=1)).to_have_text("Etkinlik Oluştur")
    expect(page.get_by_role("button", name="Taslak Kaydet")).to_be_visible()


def test_user_can_select_form_fields(page: Page):
    fill_form(page, capacity="50")
    expect(page.get_by_label("Etkinlik Başlığı")).to_have_value("Yazılım Semineri")
    expect(page.get_by_label("Etkinlik Kapasitesi")).to_have_value("50")


def test_e2e_01_valid_capacity_shows_success_message(page: Page):
    fill_form(page, capacity="50")
    page.get_by_role("button", name="Taslak Kaydet").click()
    expect(page).to_have_url(re.compile(r"/events/$"))
    expect(page.locator("p[role='alert']")).to_have_text(SUCCESS_MSG)


def test_e2e_02_capacity_over_hall_limit_shows_error(page: Page):
    fill_form(page, capacity="101")
    page.get_by_role("button", name="Taslak Kaydet").click()
    expect(page.locator("p[role='alert']")).to_have_text(CAPACITY_EXCEEDED_MSG)


def test_zero_price_is_shown_as_free(page: Page):
    page.goto("/events/create")
    page.get_by_label("Bilet Fiyatı (TL)").fill("0")
    expect(page.locator("#price_text")).to_have_text("Ücretsiz")