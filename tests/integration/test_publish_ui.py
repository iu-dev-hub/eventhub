"""Taslak Yönetim / Etkinlik Ekranında Yayınlama Aksiyonu ve Flash Mesajları UI testleri (TG-175).

Kapsam:
- Taslak (draft) etkinliklerde "Yayınla" butonunun/formunun (POST /events/<id>/publish) görünmesi,
  yayınlanmış (published) etkinliklerde görünmemesi.
- Taslak ve yayınlanmış etkinliklerin durum rozetlerinin/etiketlerinin arayüzde net ayırt edilmesi.
- Başarılı yayınlama ve hata durumlarında (yetki, kapasite, eksik alan, zaman çakışması)
  flash mesajlarının arayüzde doğru görüntülenmesi.
"""

import pytest

from app.core.db import get_db

ORGANIZER = 20
OTHER_ORGANIZER = 21
UNAPPROVED = 22
PARTICIPANT = 23
ADMIN = 24


def _setup_db(app):
    with app.app_context():
        db = get_db()
        columns = {row["name"] for row in db.execute("PRAGMA table_info(users)").fetchall()}
        if "organizer_approved" not in columns:
            db.execute("ALTER TABLE users ADD COLUMN organizer_approved INTEGER NOT NULL DEFAULT 0")

        users = [
            (ORGANIZER, "org20@example.com", "organizer", 1),
            (OTHER_ORGANIZER, "org21@example.com", "organizer", 1),
            (UNAPPROVED, "unapp22@example.com", "organizer", 0),
            (PARTICIPANT, "part23@example.com", "participant", 0),
            (ADMIN, "admin24@example.com", "admin", 1),
        ]
        for uid, email, role, approved in users:
            db.execute(
                "INSERT INTO users (id, email, password_hash, role, organizer_approved) "
                "VALUES (?, ?, 'x', ?, ?)",
                (uid, email, role, approved),
            )

        db.execute(
            "INSERT INTO venues (id, name, address, capacity) "
            "VALUES (1, 'Büyük Salon', 'Adres', 100)"
        )
        db.execute(
            "INSERT INTO venues (id, name, address, capacity) "
            "VALUES (2, 'Küçük Salon', 'Adres', 20)"
        )

        cols = (
            "id, title, category, venue_id, start_time, end_time, "
            "capacity, price, status, organizer_id"
        )

        # 1: ORGANIZER taslak etkinlik
        db.execute(
            f"INSERT INTO events ({cols}) VALUES "
            "(1, 'Caz Festivali', 'Konser', 1, '2026-12-01T20:00', "
            "'2026-12-01T23:00', 50, 100.0, 'draft', ?)",
            (ORGANIZER,),
        )

        # 2: ORGANIZER yayınlanmış etkinlik
        db.execute(
            f"INSERT INTO events ({cols}) VALUES "
            "(2, 'Tiyatro Gecesi', 'Tiyatro', 1, '2026-12-02T19:00', "
            "'2026-12-02T21:00', 60, 50.0, 'published', ?)",
            (ORGANIZER,),
        )

        # 3: ORGANIZER kapasite aşan taslak (Kapasite 50, Salon 2 kapasitesi 20)
        db.execute(
            f"INSERT INTO events ({cols}) VALUES "
            "(3, 'Aşırı Kapasiteli Standup', 'Komedi', 2, '2026-12-03T19:00', "
            "'2026-12-03T21:00', 50, 0, 'draft', ?)",
            (ORGANIZER,),
        )

        # 4: ORGANIZER eksik alanlı taslak (Başlık boş)
        db.execute(
            f"INSERT INTO events ({cols}) VALUES "
            "(4, '', 'Seminer', 1, '2026-12-04T10:00', "
            "'2026-12-04T12:00', 30, 0, 'draft', ?)",
            (ORGANIZER,),
        )

        # 5: OTHER_ORGANIZER yayınlanmış etkinlik (Salon 1, 2026-12-05 14:00 - 17:00)
        db.execute(
            f"INSERT INTO events ({cols}) VALUES "
            "(5, 'Mevcut Seminer', 'Eğitim', 1, '2026-12-05T14:00', "
            "'2026-12-05T17:00', 40, 0, 'published', ?)",
            (OTHER_ORGANIZER,),
        )

        # 6: ORGANIZER zaman çakışan taslak (5 ile çakışır: Salon 1, 15:00 - 18:00)
        db.execute(
            f"INSERT INTO events ({cols}) VALUES "
            "(6, 'Çakışan Atölye', 'Eğitim', 1, '2026-12-05T15:00', "
            "'2026-12-05T18:00', 30, 0, 'draft', ?)",
            (ORGANIZER,),
        )

        # 7: UNAPPROVED taslak etkinlik
        db.execute(
            f"INSERT INTO events ({cols}) VALUES "
            "(7, 'Onaysız Taslak', 'Diğer', 1, '2026-12-06T10:00', "
            "'2026-12-06T12:00', 20, 0, 'draft', ?)",
            (UNAPPROVED,),
        )

        # 8: OTHER_ORGANIZER taslak etkinlik
        db.execute(
            f"INSERT INTO events ({cols}) VALUES "
            "(8, 'Gizli Diğer Taslak', 'Eğitim', 2, '2026-12-07T10:00', "
            "'2026-12-07T12:00', 15, 0, 'draft', ?)",
            (OTHER_ORGANIZER,),
        )

        db.commit()


@pytest.fixture
def seeded(app):
    _setup_db(app)
    return app


def login(client, user_id, role):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_email"] = f"user{user_id}@example.com"
        sess["user_role"] = role


def test_draft_event_shows_publish_button_and_draft_badge(seeded, client):
    """Taslak etkinlikte 'Yayınla' butonu/formu ve 'Taslak' rozeti görüntülenir."""
    login(client, ORGANIZER, "organizer")
    response = client.get("/events/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # 1 nolu taslak etkinlik görüntülenmeli
    assert "Caz Festivali" in html
    # Taslak rozeti bulunmalı
    assert "Taslak" in html
    assert "status-draft" in html or "badge-draft" in html or "Taslak" in html
    # Yayınla butonu ve POST formu bulunmalı
    assert "/events/1/publish" in html
    assert "Yayınla" in html


def test_published_event_does_not_show_publish_button(seeded, client):
    """Yayınlanmış etkinlikte 'Yayınla' butonu görünmez ve 'Yayında' rozeti görüntülenir."""
    login(client, ORGANIZER, "organizer")
    response = client.get("/events/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # 2 nolu yayınlanmış etkinlik görüntülenmeli
    assert "Tiyatro Gecesi" in html
    # Yayında rozeti bulunmalı
    assert "Yayında" in html
    # Yayınlanmış etkinlik için publish aksiyonu olmamalı
    assert "/events/2/publish" not in html


def test_status_badges_clearly_distinguished(seeded, client):
    """Taslak ve yayında durumları arayüzde birbirinden net ayırt edilir."""
    login(client, ORGANIZER, "organizer")
    response = client.get("/events/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Taslak" in html
    assert "Yayında" in html


def test_successful_publish_action_shows_flash_message_and_updates_ui(seeded, client):
    """Yayınla butonuna basıldığında başarı flash mesajı gösterilir ve durum 'Yayında' olur."""
    login(client, ORGANIZER, "organizer")

    # 1 nolu taslağı yayınla (HTML tarayıcı isteği)
    response = client.post(
        "/events/1/publish",
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Başarı flash mesajı ve güncel 'Yayında' durumu yönlenilen /events/ sayfasında görünmeli
    assert "başarıyla yayınlandı" in html.lower()
    assert "/events/1/publish" not in html
    assert "Yayında" in html


def test_publish_failure_unapproved_organizer_shows_flash_message(seeded, client):
    """Onaysız organizatör yayınlama denediğinde yetki hatası flash mesajı görüntülenir."""
    login(client, UNAPPROVED, "organizer")

    response = client.post(
        "/events/7/publish",
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Yetki/onay hata flash mesajı HTML sayfasında görüntülenmeli
    assert "onay" in html.lower()


def test_publish_failure_already_published_shows_flash_message(seeded, client):
    """Zaten yayınlanmış etkinlik tekrar yayınlandığında hata flash mesajı görüntülenir."""
    login(client, ORGANIZER, "organizer")

    # 2 nolu etkinlik zaten 'published'
    response = client.post(
        "/events/2/publish",
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    page = client.get("/events/")
    html = page.get_data(as_text=True)
    # Servisin gerçek hata mesajı: "Yalnızca taslak etkinlikler yayınlanabilir."
    assert "yalnızca taslak etkinlikler yayınlanabilir" in html.lower()


def test_publish_failure_capacity_exceeded_shows_flash_message(seeded, client):
    """Salon kapasitesi aşıldığında hata flash mesajı görüntülenir."""
    login(client, ORGANIZER, "organizer")

    # 3 nolu taslak: Kapasite 50, Salon kapasitesi 20
    response = client.post(
        "/events/3/publish",
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    page = client.get("/events/")
    html = page.get_data(as_text=True)
    # Servisin gerçek hata mesajı: "Etkinlik kapasitesi salon kapasitesini aşamaz."
    assert "etkinlik kapasitesi salon kapasitesini aşamaz" in html.lower()


def test_publish_failure_missing_fields_shows_flash_message(seeded, client):
    """Eksik alan durumunda hata flash mesajı görüntülenir."""
    login(client, ORGANIZER, "organizer")

    # 4 nolu taslak: Başlık boş
    response = client.post(
        "/events/4/publish",
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    page = client.get("/events/")
    html = page.get_data(as_text=True)
    # Servisin gerçek hata mesajı: "Etkinlik başlığı zorunludur."
    assert "etkinlik başlığı zorunludur" in html.lower()


def test_publish_failure_time_conflict_shows_flash_message(seeded, client):
    """Zaman çakışması durumunda hata flash mesajı görüntülenir."""
    login(client, ORGANIZER, "organizer")

    # 6 nolu taslak, 5 nolu yayınlanmış etkinlik ile Salon 1'de çakışır
    response = client.post(
        "/events/6/publish",
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    page = client.get("/events/")
    html = page.get_data(as_text=True)
    # Servisin gerçek hata mesajı: "Aynı salonda bu saatlerde yayınlanmış başka bir etkinlik var."
    assert "aynı salonda bu saatlerde yayınlanmış başka bir etkinlik var" in html.lower()


# --- TG-176: Uçtan Uca Kabul Kriteri Yaşam Döngüsü ve Görünürlük Testleri ---


def test_full_lifecycle_create_draft_then_publish_updates_visibility_for_all_roles(seeded, client):
    """TC-176-I04 · PB-04 (#28) Kabul Kriteri: Taslak oluşturma -> yayınlama -> görünürlük geçişi.

    1. Onaylı organizatör form üzerinden yeni bir taslak oluşturur.
    2. Yayınlama öncesi katılımcı ve anonim kullanıcı taslağı /events/ ve /events/<id> (404)
       üzerinde göremez.
    3. Organizatör /events/<id>/publish ile taslağı yayınlar.
    4. Yayınlama sonrası durum DB'de kalıcı olarak 'published' olur, organizatörde 'Yayında' rozeti
       görünür, 'Yayınla' butonu kalkar ve katılımcı/anonim kullanıcı etkinliği görebilir.
    """
    login(client, ORGANIZER, "organizer")
    create_resp = client.post(
        "/events/create",
        data={
            "title": "TG-176 Kabul Testi Semineri",
            "category": "Eğitim",
            "venue_id": "1",
            "start_time": "2026-12-10T10:00",
            "end_time": "2026-12-10T12:00",
            "capacity": "100",
            "price": "0",
        },
        follow_redirects=True,
    )
    assert create_resp.status_code == 200
    assert "Taslak etkinlik kaydedildi" in create_resp.get_data(as_text=True)

    with seeded.app_context():
        row = (
            get_db()
            .execute(
                "SELECT id, status FROM events WHERE title = ?", ("TG-176 Kabul Testi Semineri",)
            )
            .fetchone()
        )
        assert row is not None
        event_id = row["id"]
        assert row["status"] == "draft"

    # Yayınlama öncesi: katılımcı listede göremez ve detayda 404 alır
    login(client, PARTICIPANT, "participant")
    participant_list_before = client.get("/events/").get_data(as_text=True)
    assert "TG-176 Kabul Testi Semineri" not in participant_list_before
    assert client.get(f"/events/{event_id}").status_code == 404

    # Yayınlama: sahibi olan onaylı organizatör yayınlar
    login(client, ORGANIZER, "organizer")
    pub_resp = client.post(
        f"/events/{event_id}/publish",
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert pub_resp.status_code == 200
    org_list_after = pub_resp.get_data(as_text=True)

    # Organizatör listesinde başarı mesajı ve 'Yayında' durumu görünür, publish butonu kalkar
    assert f"Etkinlik başarıyla yayınlandı. (Etkinlik No: {event_id})" in org_list_after
    assert f"/events/{event_id}/publish" not in org_list_after

    # Yayınlama sonrası: katılımcı hem listede hem detay uç noktasında (200) etkinliği görür
    login(client, PARTICIPANT, "participant")
    participant_list_after = client.get("/events/").get_data(as_text=True)
    assert "TG-176 Kabul Testi Semineri" in participant_list_after

    detail_after = client.get(f"/events/{event_id}")
    assert detail_after.status_code == 200
    assert detail_after.get_json()["status"] == "published"


def test_html_publish_redirect_target_is_documented_for_qa_finding(seeded, client):
    """TC-176-I05: HTML yayınlama isteğinin events.index yönlendirmesini ve flash'ı doğrular."""
    login(client, ORGANIZER, "organizer")
    response = client.post(
        "/events/1/publish",
        headers={"Accept": "text/html"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/events/"

    with client.session_transaction() as sess:
        flashes = sess.get("_flashes", [])
        assert ("success", "Etkinlik başarıyla yayınlandı. (Etkinlik No: 1)") in flashes


def test_html_publish_redirects_to_events_index_and_shows_flash_immediately(seeded, client):
    """HTML yayınlama sonrası doğrudan /events/ sayfasına yönlenir ve flash mesajı görünür."""
    login(client, ORGANIZER, "organizer")
    response = client.post(
        "/events/1/publish",
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Başarı flash mesajı anında yönlenilen HTML yanıtında görünmeli
    assert "etkinlik başarıyla yayınlandı" in html.lower()
    # 1 nolu etkinlik için yayınla butonu kaldırılmış olmalı
    assert "/events/1/publish" not in html
    # Durum Yayında olmalı
    assert "Yayında" in html


def test_organizer_sees_other_organizers_published_events_but_not_drafts(seeded, client):
    """Organizatör diğer organizatörün yayınlanmış etkinliğini görür, taslağını göremez."""
    login(client, ORGANIZER, "organizer")
    response = client.get("/events/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Kendi taslak etkinliğini görür (1 nolu Caz Festivali)
    assert "Caz Festivali" in html
    # Diğer organizatörün yayınlanmış etkinliğini görür (5 nolu Mevcut Seminer)
    assert "Mevcut Seminer" in html
    # Diğer organizatörün taslağını göremez (8 nolu Gizli Diğer Taslak)
    assert "Gizli Diğer Taslak" not in html


def test_admin_sees_draft_events_without_publish_button(seeded, client):
    """Admin rolü /events/ sayfasında taslakları görür fakat 'Yayınla' butonunu görmez."""
    login(client, ADMIN, "admin")
    response = client.get("/events/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Admin tüm taslakları görür
    assert "Caz Festivali" in html
    assert "Gizli Diğer Taslak" in html
    assert "Taslak" in html

    # Ancak admin rolü için 'Yayınla' formu/butonu render edilmemelidir
    assert "/events/1/publish" not in html
    assert "/events/8/publish" not in html
    assert "btn-publish" not in html
