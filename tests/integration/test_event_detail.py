"""Katılımcı ve anonim kullanıcı etkinlik detay entegrasyon testleri (TG-195, PB-07 / #31).

Kapsam:
- Giriş yapmış `participant` ve giriş yapmamış (anonim) kullanıcıların `/events/` listesinde
  yayınlanmış etkinliklerin detay bağlantısını (`href="/events/<id>"`, "Detayları Gör") görmesi.
- `GET /events/<id>` (`Accept: text/html`) isteğiyle 200 OK ve HTML yanıtı alınması.
- Dönen HTML içeriğinde etkinlik başlığı, kategori, salon adı, salon adresi, başlangıç/bitiş
  tarih aralığı, kapasite ve bilet fiyatı (hem Ücretsiz hem ücretli senaryoları) bilgilerinin
  eksiksiz yer alması.
- Taslak (draft) etkinliklerin listede detay bağlantısının görünmemesi ve doğrudan HTML detay
  isteğinde veri sızdırmadan 404 dönmesi.
"""

import re

import pytest

from app.core.db import get_db

ORGANIZER_ID = 10
PARTICIPANT_ID = 20

PAID_EVENT_ID = 101
FREE_EVENT_ID = 102
DECIMAL_PAID_EVENT_ID = 103
DRAFT_EVENT_ID = 104

HTML_HEADERS = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}


@pytest.fixture
def seeded_events(app):
    """Ücretli, ücretsiz ve taslak etkinlikler ile salon ve kullanıcı verilerini hazırlar."""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (id, email, password_hash, role, organizer_approved) "
            "VALUES (?, 'org195@example.com', 'hash', 'organizer', 1)",
            (ORGANIZER_ID,),
        )
        db.execute(
            "INSERT INTO users (id, email, password_hash, role) "
            "VALUES (?, 'part195@example.com', 'hash', 'participant')",
            (PARTICIPANT_ID,),
        )

        db.execute(
            "INSERT INTO venues (id, name, address, capacity) VALUES (1, ?, ?, ?)",
            ("Harbiye Açıkhava Sahnesi", "Harbiye, Şişli / İstanbul", 400),
        )
        db.execute(
            "INSERT INTO venues (id, name, address, capacity) VALUES (2, ?, ?, ?)",
            ("Teknopark Konferans Salonu", "Üniversite Kampüsü, B Blok No:4", 150),
        )

        cols = (
            "id, title, category, venue_id, start_time, end_time, "
            "capacity, price, status, organizer_id"
        )
        # 1. Ücretli (tam sayı fiyatlı) yayınlanmış etkinlik
        db.execute(
            f"INSERT INTO events ({cols}) VALUES (?, ?, ?, 1, ?, ?, ?, ?, 'published', ?)",
            (
                PAID_EVENT_ID,
                "Senfoni Orkestrası Özel Konseri",
                "Konser",
                "2026-12-15T20:00",
                "2026-12-15T22:30",
                350,
                250.0,
                ORGANIZER_ID,
            ),
        )
        # 2. Ücretsiz (0 TL) yayınlanmış etkinlik
        db.execute(
            f"INSERT INTO events ({cols}) VALUES (?, ?, ?, 2, ?, ?, ?, ?, 'published', ?)",
            (
                FREE_EVENT_ID,
                "Açık Kaynak Yazılım Zirvesi",
                "Eğitim",
                "2026-12-18T10:00",
                "2026-12-18T16:00",
                120,
                0.0,
                ORGANIZER_ID,
            ),
        )
        # 3. Ücretli (ondalıklı fiyatlı) yayınlanmış etkinlik
        db.execute(
            f"INSERT INTO events ({cols}) VALUES (?, ?, ?, 2, ?, ?, ?, ?, 'published', ?)",
            (
                DECIMAL_PAID_EVENT_ID,
                "Uygulamalı Test Otomasyonu Atölyesi",
                "Konferans",
                "2026-12-20T13:30",
                "2026-12-20T17:00",
                80,
                149.5,
                ORGANIZER_ID,
            ),
        )
        # 4. Taslak etkinlik (katılımcı ve anonime görünmemeli)
        db.execute(
            f"INSERT INTO events ({cols}) VALUES (?, ?, ?, 1, ?, ?, ?, ?, 'draft', ?)",
            (
                DRAFT_EVENT_ID,
                "Gizli Hazırlık Taslağı",
                "Spor",
                "2026-12-25T09:00",
                "2026-12-25T11:00",
                100,
                75.0,
                ORGANIZER_ID,
            ),
        )
        db.commit()
    return app


def _login_as_participant(client):
    with client.session_transaction() as sess:
        sess["user_id"] = PARTICIPANT_ID
        sess["user_email"] = "part195@example.com"
        sess["user_role"] = "participant"


@pytest.mark.parametrize("as_participant", [False, True], ids=["anonymous", "participant"])
def test_events_list_shows_detail_links_for_published_events(seeded_events, client, as_participant):
    """TC-195-01 · PB-07: Katılımcı ve anonim kullanıcı /events/ listesinde detay linkini görür."""
    if as_participant:
        _login_as_participant(client)

    list_resp = client.get("/events/", headers=HTML_HEADERS)
    assert list_resp.status_code == 200
    assert "text/html" in list_resp.content_type

    list_html = list_resp.get_data(as_text=True)

    # Yayınlanmış etkinliklerin başlıkları ve detay bağlantıları listede yer almalı
    assert "Senfoni Orkestrası Özel Konseri" in list_html
    assert "Açık Kaynak Yazılım Zirvesi" in list_html
    assert f'href="/events/{PAID_EVENT_ID}"' in list_html
    assert f'href="/events/{FREE_EVENT_ID}"' in list_html
    assert "Detayları Gör" in list_html

    # Taslak etkinlik veya detay bağlantısı listede yer almamalı
    assert "Gizli Hazırlık Taslağı" not in list_html
    assert f'href="/events/{DRAFT_EVENT_ID}"' not in list_html


@pytest.mark.parametrize("as_participant", [False, True], ids=["anonymous", "participant"])
def test_paid_event_detail_html_contains_all_required_fields(seeded_events, client, as_participant):
    """TC-195-02 · PB-07: Ücretli etkinliğin detay sayfası 200 OK ve tüm alanları eksiksiz döner."""
    if as_participant:
        _login_as_participant(client)

    # Önce /events/ listesinden detay bağlantısını doğrula ve takip et
    list_html = client.get("/events/", headers=HTML_HEADERS).get_data(as_text=True)
    match = re.search(rf'href="(/events/{PAID_EVENT_ID})"', list_html)
    assert match is not None
    detail_url = match.group(1)

    resp = client.get(detail_url, headers=HTML_HEADERS)
    assert resp.status_code == 200
    assert "text/html" in resp.content_type

    html = resp.get_data(as_text=True)
    # Başlık ve kategori
    assert "Senfoni Orkestrası Özel Konseri" in html
    assert "Konser" in html
    # Salon adı ve salon adresi
    assert "Harbiye Açıkhava Sahnesi" in html
    assert "Harbiye, Şişli / İstanbul" in html
    # Başlangıç ve bitiş tarih aralığı
    assert "2026-12-15T20:00" in html
    assert "2026-12-15T22:30" in html
    # Etkinlik kapasitesi ve salon kapasitesi
    assert "350 Kişi" in html
    assert "400 Kişi" in html
    # Ücretli bilet fiyatı ve durum rozeti
    assert "250 TL" in html
    assert "Yayında" in html
    # Katılımcı veya anonim kullanıcıda "Yayınla" butonu görünmemeli
    assert f"/events/{PAID_EVENT_ID}/publish" not in html
    # Listeye geri dönüş bağlantısı bulunmalı
    assert 'href="/events/"' in html


@pytest.mark.parametrize("as_participant", [False, True], ids=["anonymous", "participant"])
def test_free_event_detail_html_displays_free_label_and_all_fields(
    seeded_events, client, as_participant
):
    """TC-195-03 · PB-07: Ücretsiz (0 TL) etkinliğin detay sayfasında fiyat 'Ücretsiz' görünür."""
    if as_participant:
        _login_as_participant(client)

    list_html = client.get("/events/", headers=HTML_HEADERS).get_data(as_text=True)
    assert f'href="/events/{FREE_EVENT_ID}"' in list_html

    resp = client.get(f"/events/{FREE_EVENT_ID}", headers=HTML_HEADERS)
    assert resp.status_code == 200
    assert "text/html" in resp.content_type

    html = resp.get_data(as_text=True)
    # Başlık ve kategori
    assert "Açık Kaynak Yazılım Zirvesi" in html
    assert "Eğitim" in html
    # Salon adı ve salon adresi
    assert "Teknopark Konferans Salonu" in html
    assert "Üniversite Kampüsü, B Blok No:4" in html
    # Tarih aralığı
    assert "2026-12-18T10:00" in html
    assert "2026-12-18T16:00" in html
    # Kapasite bilgileri
    assert "120 Kişi" in html
    assert "150 Kişi" in html
    # Ücretsiz fiyat gösterimi ("0 TL" yerine "Ücretsiz")
    assert "Ücretsiz" in html
    assert "0 TL" not in html


@pytest.mark.parametrize("as_participant", [False, True], ids=["anonymous", "participant"])
def test_decimal_paid_event_detail_html_formats_price_correctly(
    seeded_events, client, as_participant
):
    """TC-195-04 · PB-07: Ondalıklı bilet fiyatı detay HTML sayfasında kuruşlarıyla gösterilir."""
    if as_participant:
        _login_as_participant(client)

    resp = client.get(f"/events/{DECIMAL_PAID_EVENT_ID}", headers=HTML_HEADERS)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    assert "Uygulamalı Test Otomasyonu Atölyesi" in html
    assert "Konferans" in html
    assert "Teknopark Konferans Salonu" in html
    assert "Üniversite Kampüsü, B Blok No:4" in html
    assert "2026-12-20T13:30" in html
    assert "2026-12-20T17:00" in html
    assert "80 Kişi" in html
    assert "149.50 TL" in html


@pytest.mark.parametrize("as_participant", [False, True], ids=["anonymous", "participant"])
def test_draft_and_nonexistent_event_detail_html_returns_404_without_leaking_data(
    seeded_events, client, as_participant
):
    """TC-195-05 · PB-07: Katılımcı ve anonim kullanıcı taslak veya olmayan etkinlikte 404 alır."""
    if as_participant:
        _login_as_participant(client)

    draft_resp = client.get(f"/events/{DRAFT_EVENT_ID}", headers=HTML_HEADERS)
    assert draft_resp.status_code == 404
    assert "text/html" in draft_resp.content_type
    draft_html = draft_resp.get_data(as_text=True)
    assert "Etkinlik bulunamadı" in draft_html
    assert "Gizli Hazırlık Taslağı" not in draft_html
    assert "75 TL" not in draft_html

    missing_resp = client.get("/events/99999", headers=HTML_HEADERS)
    assert missing_resp.status_code == 404
    assert "Etkinlik bulunamadı" in missing_resp.get_data(as_text=True)
