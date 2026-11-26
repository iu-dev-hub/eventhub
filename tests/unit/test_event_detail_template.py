"""Etkinlik detay ve liste şablonları birim/render testleri (TG-194, PB-07 / #31)."""

import pytest
from flask import render_template

from app.core.db import get_db


def _make_event(**overrides):
    data = {
        "id": 42,
        "title": "Yazılım Mimarisi Zirvesi",
        "category": "Konferans",
        "venue_id": 5,
        "start_time": "2026-12-15T10:00",
        "end_time": "2026-12-15T17:00",
        "capacity": 120,
        "price": 0,
        "status": "published",
        "organizer_id": 10,
        "venue_name": "Merkez Konferans Salonu",
        "venue_address": "Beyazıt Kampüsü, İstanbul",
        "venue_capacity": 200,
    }
    data.update(overrides)
    return data


@pytest.mark.parametrize("free_price", [0, 0.0])
def test_detail_template_renders_published_free_event(app, free_price):
    """Yayınlanmış ücretsiz etkinlikte tüm alanlar, 'Ücretsiz' ve dönüş linki görünür."""
    event = _make_event(price=free_price, status="published")
    with app.test_request_context("/events/42"):
        html = render_template(
            "events/detail.html",
            event=event,
            user_role="participant",
            current_user_id=99,
        )

    assert "Yazılım Mimarisi Zirvesi" in html
    assert "Konferans" in html
    assert "Yayında" in html
    assert "Merkez Konferans Salonu" in html
    assert "Beyazıt Kampüsü, İstanbul" in html
    assert "200" in html
    assert "2026-12-15T10:00" in html
    assert "2026-12-15T17:00" in html
    assert "120" in html
    assert "Ücretsiz" in html
    assert "Etkinlikler Listesine Dön" in html
    assert 'href="/events/"' in html
    assert "/events/42/publish" not in html
    assert "Yayınla" not in html


@pytest.mark.parametrize(
    ("price", "expected_text", "unexpected_text"),
    [
        (150, "150 TL", "150.0 TL"),
        (150.0, "150 TL", "150.0 TL"),
        (150.5, "150.50 TL", "150.5 TL"),
        (150.75, "150.75 TL", None),
    ],
)
def test_detail_template_formats_paid_event_prices(app, price, expected_text, unexpected_text):
    """Ücretli etkinlik fiyatları temiz TL biçiminde gösterilir ve 'Ücretsiz' yazmaz."""
    event = _make_event(price=price, status="published")
    with app.test_request_context("/events/42"):
        html = render_template(
            "events/detail.html",
            event=event,
            user_role="participant",
            current_user_id=99,
        )

    assert expected_text in html
    if unexpected_text is not None:
        assert unexpected_text not in html
    assert "Ücretsiz" not in html


def test_detail_template_handles_missing_or_none_venue_fields_safely(app):
    """Salon bilgileri None veya eksik olduğunda şablon hata vermeden render edilir."""
    event_with_none = _make_event(
        venue_name=None,
        venue_address=None,
        venue_capacity=None,
    )
    with app.test_request_context("/events/42"):
        html_none = render_template("events/detail.html", event=event_with_none)

    assert "Yazılım Mimarisi Zirvesi" in html_none
    assert "Etkinlikler Listesine Dön" in html_none

    event_without_venue_keys = _make_event()
    del event_without_venue_keys["venue_name"]
    del event_without_venue_keys["venue_address"]
    del event_without_venue_keys["venue_capacity"]
    with app.test_request_context("/events/42"):
        html_missing = render_template("events/detail.html", event=event_without_venue_keys)

    assert "Yazılım Mimarisi Zirvesi" in html_missing
    assert "Etkinlikler Listesine Dön" in html_missing


def test_detail_template_shows_publish_form_only_for_draft_owner_organizer(app):
    """Taslak etkinlikte 'Yayınla' formu yalnızca taslağın sahibi organizatör için görünür."""
    draft_event = _make_event(status="draft", organizer_id=10)
    with app.test_request_context("/events/42"):
        html = render_template(
            "events/detail.html",
            event=draft_event,
            user_role="organizer",
            current_user_id=10,
        )

    assert "Taslak" in html
    assert "/events/42/publish" in html
    assert 'method="post"' in html.lower()
    assert "Yayınla" in html


@pytest.mark.parametrize(
    ("role", "user_id"),
    [
        ("admin", 1),
        ("organizer", 99),
        ("participant", 50),
        (None, None),
    ],
)
def test_detail_template_hides_publish_form_for_non_owners_and_other_roles(app, role, user_id):
    """Admin, başka organizatör, katılımcı ve anonim kullanıcı için 'Yayınla' render edilmez."""
    draft_event = _make_event(status="draft", organizer_id=10)
    with app.test_request_context("/events/42"):
        html = render_template(
            "events/detail.html",
            event=draft_event,
            user_role=role,
            current_user_id=user_id,
        )

    assert "Taslak" in html
    assert "/events/42/publish" not in html
    assert "btn-publish" not in html


def test_detail_template_renders_safely_without_user_context_vars(app):
    """Şablona user_role veya current_user_id verilmediğinde hata vermez ve 'Yayınla' gizlenir."""
    draft_event = _make_event(status="draft", organizer_id=10)
    with app.test_request_context("/events/42"):
        html = render_template("events/detail.html", event=draft_event)

    assert "Taslak" in html
    assert "/events/42/publish" not in html


def test_detail_template_hides_publish_form_when_organizer_id_is_none(app):
    """Etkinliğin organizer_id değeri None ise hiçbir kullanıcı için 'Yayınla' render edilmez."""
    draft_event = _make_event(status="draft", organizer_id=None)
    with app.test_request_context("/events/42"):
        html_none_user = render_template(
            "events/detail.html",
            event=draft_event,
            user_role="organizer",
            current_user_id=None,
        )
        html_valid_user = render_template(
            "events/detail.html",
            event=draft_event,
            user_role="organizer",
            current_user_id=10,
        )

    assert "/events/42/publish" not in html_none_user
    assert "/events/42/publish" not in html_valid_user


@pytest.mark.parametrize(
    ("raw_status", "escaped_status"),
    [
        ("<script>alert(1)</script>", "&lt;script&gt;alert(1)&lt;/script&gt;"),
        ("cancelled & paused", "cancelled &amp; paused"),
    ],
)
def test_detail_template_escapes_fallback_unknown_status(app, raw_status, escaped_status):
    """Bilinmeyen veya özel karakterli durum değerleri HTML kaçışı uygulanarak render edilir."""
    event = _make_event(status=raw_status)
    with app.test_request_context("/events/42"):
        html = render_template("events/detail.html", event=event)

    assert raw_status not in html
    assert escaped_status in html
    assert "/events/42/publish" not in html


@pytest.fixture
def index_seeded(app):
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (id, email, password_hash, role) "
            "VALUES (10, 'org10@example.com', 'x', 'organizer')"
        )
        db.execute(
            "INSERT INTO users (id, email, password_hash, role) "
            "VALUES (20, 'part20@example.com', 'x', 'participant')"
        )
        db.execute(
            "INSERT INTO users (id, email, password_hash, role) "
            "VALUES (30, 'admin30@example.com', 'x', 'admin')"
        )
        db.execute(
            "INSERT INTO venues (id, name, address, capacity) "
            "VALUES (1, 'Büyük Salon', 'Merkez', 100)"
        )
        cols = (
            "id, title, category, venue_id, start_time, end_time, "
            "capacity, price, status, organizer_id"
        )
        db.execute(
            f"INSERT INTO events ({cols}) VALUES "
            "(101, 'Açık Konser', 'Konser', 1, '2026-12-20T20:00', "
            "'2026-12-20T22:00', 80, 100.0, 'published', 10)"
        )
        db.execute(
            f"INSERT INTO events ({cols}) VALUES "
            "(102, 'Taslak Atölye', 'Eğitim', 1, '2026-12-21T10:00', "
            "'2026-12-21T12:00', 30, 0.0, 'draft', 10)"
        )
        db.commit()
    return app


def test_index_shows_detail_links_for_anonymous_user(index_seeded, client):
    """Anonim kullanıcı /events/ sayfasında yayınlanmış etkinliklerde 'Detayları Gör' görür."""
    response = client.get("/events/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Açık Konser" in html
    assert "Detayları Gör" in html
    assert 'href="/events/101"' in html
    assert "Taslak Atölye" not in html
    assert "btn-publish" not in html


def test_index_shows_detail_links_for_participant(index_seeded, client):
    """Katılımcı /events/ sayfasında yayınlanmış etkinliklerde 'Detayları Gör' görür."""
    with client.session_transaction() as sess:
        sess["user_id"] = 20
        sess["user_email"] = "part20@example.com"
        sess["user_role"] = "participant"

    response = client.get("/events/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Açık Konser" in html
    assert "Detayları Gör" in html
    assert 'href="/events/101"' in html
    assert "Taslak Atölye" not in html
    assert "btn-publish" not in html


def test_index_shows_detail_links_for_organizer_on_both_published_and_draft(index_seeded, client):
    """Organizatör hem yayınlanmış hem taslak kartlarında 'Detayları Gör' linkini görür."""
    with client.session_transaction() as sess:
        sess["user_id"] = 10
        sess["user_email"] = "org10@example.com"
        sess["user_role"] = "organizer"

    response = client.get("/events/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Açık Konser" in html
    assert "Taslak Atölye" in html
    assert "Detayları Gör" in html
    assert 'href="/events/101"' in html
    assert 'href="/events/102"' in html
    # Mevcut 'Yayınla' butonu kendi taslağında korunmalı
    assert "/events/102/publish" in html


def test_index_shows_detail_links_for_admin_without_publish_button(index_seeded, client):
    """Admin tüm etkinliklerde 'Detayları Gör' linkini görür fakat 'Yayınla' butonunu görmez."""
    with client.session_transaction() as sess:
        sess["user_id"] = 30
        sess["user_email"] = "admin30@example.com"
        sess["user_role"] = "admin"

    response = client.get("/events/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert 'href="/events/101"' in html
    assert 'href="/events/102"' in html
    assert "Detayları Gör" in html
    assert "btn-publish" not in html
