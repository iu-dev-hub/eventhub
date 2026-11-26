"""TG-191: Etkinlik detay ve rol bazlı görünürlük servisinin birim testleri.

SQLite :memory: kullanılır; Flask route'u, oturum ve gerçek proje DB'si gerekmez.
TG-189 get_event ve TG-190 get_event_detail davranışları bağımsız test edilir.
"""

import sqlite3

import pytest

from app.events.services import get_event, get_event_detail


@pytest.fixture
def detail_db():
    """Her test için tamamen ayrı, bellekte çalışan küçük bir veritabanı oluştur."""
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")

    db.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            role TEXT NOT NULL
        );

        CREATE TABLE venues (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            capacity INTEGER NOT NULL
        );

        CREATE TABLE events (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            venue_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL,
            organizer_id INTEGER NOT NULL,
            FOREIGN KEY (venue_id) REFERENCES venues(id),
            FOREIGN KEY (organizer_id) REFERENCES users(id)
        );
        """
    )

    db.executemany(
        "INSERT INTO users (id, role) VALUES (?, ?)",
        [(10, "organizer"), (11, "organizer"), (12, "participant"), (13, "admin")],
    )
    db.executemany(
        "INSERT INTO venues (id, name, address, capacity) VALUES (?, ?, ?, ?)",
        [
            (1, "Ana Salon", "Iğdır Merkez", 120),
            (2, "Küçük Salon", "Kampüs", 30),
        ],
    )
    db.executemany(
        """
        INSERT INTO events (
            id, title, category, venue_id, start_time, end_time,
            capacity, price, status, organizer_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                101,
                "Ücretsiz Seminer",
                "Eğitim",
                1,
                "2026-12-03T10:00",
                "2026-12-03T12:00",
                80,
                0.0,
                "published",
                10,
            ),
            (
                102,
                "Gizli Taslak",
                "Atölye",
                2,
                "2026-12-04T13:00",
                "2026-12-04T15:00",
                20,
                150.0,
                "draft",
                10,
            ),
            (
                103,
                "Diğer Salon Etkinliği",
                "Konser",
                2,
                "2026-12-05T19:00",
                "2026-12-05T21:00",
                25,
                49.5,
                "published",
                11,
            ),
        ],
    )
    db.commit()

    try:
        yield db
    finally:
        db.close()


def test_published_event_returns_all_fields_and_correct_venue(detail_db):
    """Yayındaki etkinliğin bütün alanları ve doğru salon bilgileri gelir."""
    event = get_event(detail_db, 101)

    assert event == {
        "id": 101,
        "title": "Ücretsiz Seminer",
        "category": "Eğitim",
        "venue_id": 1,
        "start_time": "2026-12-03T10:00",
        "end_time": "2026-12-03T12:00",
        "capacity": 80,
        "price": 0.0,
        "status": "published",
        "organizer_id": 10,
        "venue_name": "Ana Salon",
        "venue_address": "Iğdır Merkez",
        "venue_capacity": 120,
    }


def test_another_event_does_not_receive_wrong_venue(detail_db):
    """JOIN, farklı salondaki etkinlik için yanlış salon bilgisi getirmemeli."""
    event = get_event(detail_db, 103)

    assert event["venue_id"] == 2
    assert event["venue_name"] == "Küçük Salon"
    assert event["venue_address"] == "Kampüs"
    assert event["venue_capacity"] == 30
    assert event["price"] == 49.5


def test_missing_venue_does_not_hide_event_from_internal_reader(detail_db):
    """LEFT JOIN, silinmiş salon referansında da etkinlik kaydını okuyabilmeli."""
    detail_db.execute("PRAGMA foreign_keys = OFF")
    try:
        detail_db.execute("UPDATE events SET venue_id = 9999 WHERE id = 102")
        detail_db.commit()
    finally:
        detail_db.execute("PRAGMA foreign_keys = ON")

    event = get_event(detail_db, 102)
    assert event is not None
    assert event["status"] == "draft"
    assert event["venue_name"] is None
    assert event["venue_address"] is None
    assert event["venue_capacity"] is None


def test_event_price_and_dates_are_usable_types(detail_db):
    """Ücretsiz fiyat sayısal sıfır, tarihler route/UI için metin olmalı."""
    event = get_event(detail_db, 101)

    assert event["price"] == 0.0
    assert isinstance(event["price"], (int, float))
    assert event["start_time"] == "2026-12-03T10:00"
    assert event["end_time"] == "2026-12-03T12:00"
    assert isinstance(event["start_time"], str)
    assert isinstance(event["end_time"], str)


@pytest.mark.parametrize(
    "user_id,user_role",
    [
        (None, None),  # Anonim
        (12, "participant"),  # Katılımcı
        (10, "organizer"),  # Sahibi
        (11, "organizer"),  # Başka organizatör
        (13, "admin"),  # Yönetici
        (999, "participant"),  # Yayındaki etkinlik oturum gerektirmez
    ],
)
def test_published_event_is_visible_to_every_role(detail_db, user_id, user_role):
    """Yayınlanmış etkinliği tüm roller ve anonim kullanıcı görebilir."""
    event = get_event_detail(detail_db, 101, user_id=user_id, user_role=user_role)

    assert event is not None
    assert event["status"] == "published"
    assert event["venue_name"] == "Ana Salon"
    assert event["venue_address"] == "Iğdır Merkez"
    assert event["venue_capacity"] == 120


@pytest.mark.parametrize(
    "user_id,user_role",
    [
        (10, "organizer"),  # Taslağın sahibi
        (13, "admin"),  # Yönetici
    ],
)
def test_draft_visible_to_owner_or_admin(detail_db, user_id, user_role):
    """Taslak etkinliği yalnızca sahibi organizatör veya admin görebilir."""
    event = get_event_detail(detail_db, 102, user_id=user_id, user_role=user_role)

    assert event is not None
    assert event["title"] == "Gizli Taslak"
    assert event["status"] == "draft"
    assert event["venue_name"] == "Küçük Salon"


@pytest.mark.parametrize(
    "user_id,user_role",
    [
        (None, None),  # Anonim
        (12, "participant"),  # Başka katılımcı
        (10, "participant"),  # Kullanıcı ID'si eşleşse bile rol yanlış
        (11, "organizer"),  # Başka organizatör
        (None, "admin"),  # Admin rolü var, fakat ID yok
        (0, "admin"),  # Geçersiz ID
        (-1, "admin"),  # Geçersiz ID
        (True, "admin"),  # bool, int gibi kabul edilmemeli
        ("10", "organizer"),  # ID metin olamaz
        (10, None),  # Rol yok
        (10, "unknown"),  # Bilinmeyen rol
    ],
)
def test_draft_is_hidden_from_other_users(detail_db, user_id, user_role):
    """Yetkisiz tüm taslak erişimleri bilgi sızdırmadan None döndürür."""
    assert get_event_detail(detail_db, 102, user_id=user_id, user_role=user_role) is None


@pytest.mark.parametrize("event_id", [0, -1, 9999, None, True, "101", 1.5])
def test_get_event_rejects_unknown_or_invalid_ids(detail_db, event_id):
    """Eski okuma servisi geçersiz/bulunmayan ID'lerde None döndürür."""
    assert get_event(detail_db, event_id) is None


@pytest.mark.parametrize("event_id", [0, -1, 9999, None, True, "102", 1.5])
def test_get_event_detail_rejects_unknown_or_invalid_ids(detail_db, event_id):
    """Görünürlük servisi geçersiz/bulunmayan ID'lerde None döndürür."""
    assert get_event_detail(detail_db, event_id, user_id=13, user_role="admin") is None


def test_legacy_get_event_can_still_read_drafts(detail_db):
    """İç servislerin kullandığı get_event, erişim kontrolüne tabi tutulmamalı."""
    event = get_event(detail_db, 102)

    assert event is not None
    assert event["status"] == "draft"


def test_detail_service_does_not_modify_database(detail_db):
    """Sorgular etkinlik durumunu veya veritabanındaki verileri değiştirmemeli."""
    changes_before = detail_db.total_changes

    assert get_event_detail(detail_db, 102, user_id=12, user_role="participant") is None
    assert get_event_detail(detail_db, 102, user_id=10, user_role="organizer") is not None

    assert detail_db.total_changes == changes_before
    assert (
        detail_db.execute("SELECT status FROM events WHERE id = 102").fetchone()["status"]
        == "draft"
    )


def test_get_event_uses_one_select_for_event_and_venue(detail_db):
    """TG-189: Etkinlik ve salon tek SELECT sorgusunda birleştirilmeli."""
    statements = []
    detail_db.set_trace_callback(statements.append)
    try:
        event = get_event(detail_db, 101)
    finally:
        detail_db.set_trace_callback(None)

    assert event["venue_name"] == "Ana Salon"
    selects = [sql for sql in statements if sql.lstrip().upper().startswith("SELECT")]
    assert len(selects) == 1
    assert "JOIN venues" in selects[0]
