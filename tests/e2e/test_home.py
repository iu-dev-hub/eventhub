"""EXAMPLE end-to-end (E2E) tests with Playwright in a real browser.

E2E testleri CI'a Hafta 7'de eklenecektir. O zamana kadar yerel olarak çalıştırabilirsiniz:
    pytest tests/e2e                  # tarayıcı görünmez (headless)
    pytest tests/e2e --headed         # tarayıcıyı görerek
    pytest tests/e2e --slowmo 500     # adımları yavaşlatarak

İpucu: Elemanları kullanıcının gördüğü şekilde bulun (get_by_role, get_by_label,
get_by_text). Arayüz Türkçe olduğu için testlerdeki metinler de Türkçedir.
"""

import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def test_home_page_shows_welcome(page: Page):
    page.goto("/")
    expect(page).to_have_title(re.compile("Ana Sayfa"))
    expect(page.get_by_role("heading", level=1)).to_contain_text("Hoş Geldiniz")


def test_main_menu_has_home_link(page: Page):
    page.goto("/")
    menu = page.get_by_role("navigation", name="Ana menü")
    menu.get_by_role("link", name="Ana Sayfa").click()
    expect(page).to_have_url(re.compile(r"/$"))
