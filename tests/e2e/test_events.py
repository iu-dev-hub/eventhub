"""Events modülü uçtan uca (E2E) testleri - Görev #24 (BR-2.2, BR-2.3).

Yerelde çalıştırma:
    pytest tests/e2e/test_events.py
    pytest tests/e2e/test_events.py --headed

Not: Formda salon seçimi yoktur; "Salon" metin alanıdır ve salon kapasitesi
(100) serviste prototip için sabittir. Bu yüzden "kapasitesi 100 olan örnek
salon" adımı, salon adı olarak "Salon A" yazılarak karşılanır.
"""

import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

# Servis (TG-22) mesajları güncellendi: başarılı durumda "(Kayıt işlemi Sprint 2'de
# yapılacaktır.)" eki var ve kullanıcı Events ana sayfasına yönlendirilir; kapasite
# aşımında mesaj gerçek kapasite değerlerini içerir.
SUCCESS_MSG = "Etkinlik bilgileri doğrulandı. (Kayıt işlemi Sprint 2'de yapılacaktır.)"
CAPACITY_EXCEEDED_MSG = "Etkinlik kapasitesi (101), salon kapasitesini (100) aşamaz."


def fill_form(page: Page, capacity: str, price: str = "100"):
    page.get_by_label("Etkinlik Başlığı").fill("Yazılım Semineri")
    page.get_by_label("Kategori").select_option("Eğitim")
    page.get_by_label("Salon").fill("Salon A")
    page.get_by_label("Başlangıç Tarihi ve Saati").fill("2026-12-01T10:00")
    page.get_by_label("Bitiş Tarihi ve Saati").fill("2026-12-01T12:00")
    page.get_by_label("Etkinlik Kapasitesi").fill(capacity)
    page.get_by_label("Bilet Fiyatı (TL)").fill(price)


def test_create_form_page_opens(page: Page):
    page.goto("/events/create")
    expect(page).to_have_title(re.compile("Etkinlik Oluştur"))
    expect(page.get_by_role("heading", level=1)).to_have_text("Etkinlik Oluştur")
    expect(page.get_by_role("button", name="Kontrol Et")).to_be_visible()


def test_user_can_type_into_form_fields(page: Page):
    page.goto("/events/create")
    fill_form(page, capacity="50")
    expect(page.get_by_label("Etkinlik Başlığı")).to_have_value("Yazılım Semineri")
    expect(page.get_by_label("Salon")).to_have_value("Salon A")
    expect(page.get_by_label("Etkinlik Kapasitesi")).to_have_value("50")


def test_e2e_01_valid_capacity_shows_success_message(page: Page):
    page.goto("/events/create")
    fill_form(page, capacity="50")
    page.get_by_role("button", name="Kontrol Et").click()
    expect(page).to_have_url(re.compile(r"/events/$"))
    expect(page.get_by_role("alert")).to_have_text(SUCCESS_MSG)


def test_e2e_02_capacity_over_hall_limit_shows_error(page: Page):
    page.goto("/events/create")
    fill_form(page, capacity="101")
    page.get_by_role("button", name="Kontrol Et").click()
    expect(page.get_by_role("alert")).to_have_text(CAPACITY_EXCEEDED_MSG)


def test_zero_price_is_shown_as_free(page: Page):
    page.goto("/events/create")
    page.get_by_label("Bilet Fiyatı (TL)").fill("0")
    expect(page.locator("#price_text")).to_have_text("Ücretsiz")
