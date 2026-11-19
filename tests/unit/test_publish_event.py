"""Etkinlik yayınlama servisi birim testleri (TG-174, TG-172, PB-04; BR-1.5)."""

import pytest

from app.core.db import get_db
from app.events.services import EventPermissionError, get_event, publish_event


@pytest.fixture
def db(app):
    with app.app_context():
        db = get_db()
        columns = {row["name"] for row in db.execute("PRAGMA table_info(users)").fetchall()}
        if "organizer_approved" not in columns:
            db.execute("ALTER TABLE users ADD COLUMN organizer_approved INTEGER NOT NULL DEFAULT 0")
        db.execute(
            "INSERT INTO venues (id, name, address, capacity) "
            "VALUES (1, 'Büyük Salon', 'Adres', 100)"
        )
        db.execute(
            "INSERT INTO users (id, email, password_hash, role, organizer_approved) "
            "VALUES (1, 'org1@example.com', 'x', 'organizer', 1)"
        )
        db.execute(
            "INSERT INTO users (id, email, password_hash, role, organizer_approved) "
            "VALUES (2, 'org2@example.com', 'x', 'organizer', 1)"
        )
        db.execute(
            "INSERT INTO users (id, email, password_hash, role, organizer_approved) "
            "VALUES (3, 'unapproved@example.com', 'x', 'organizer', 0)"
        )
        db.commit()
        yield db


def _insert_event(db, **kwargs):
    defaults = {
        "title": "Bahar Konseri",
        "category": "Müzik",
        "venue_id": 1,
        "start_time": "2026-12-01T18:00",
        "end_time": "2026-12-01T21:00",
        "capacity": 80,
        "price": 50.0,
        "status": "draft",
        "organizer_id": 1,
    }
    data = {**defaults, **kwargs}
    cursor = db.execute(
        "INSERT INTO events ("
        "title, category, venue_id, start_time, end_time, capacity, price, status, organizer_id"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            data["title"],
            data["category"],
            data["venue_id"],
            data["start_time"],
            data["end_time"],
            data["capacity"],
            data["price"],
            data["status"],
            data["organizer_id"],
        ),
    )
    db.commit()
    return cursor.lastrowid


def test_publish_event_success_for_approved_organizer(db):
    """Onaylı organizatör kendi geçerli taslak etkinliğini yayınlayabilir."""
    event_id = _insert_event(db, organizer_id=1, status="draft")

    ok, event, errors = publish_event(db, event_id, organizer_id=1)

    assert ok is True
    assert errors == []
    assert event is not None
    assert event["status"] == "published"
    assert event["id"] == event_id

    refetched = get_event(db, event_id)
    assert refetched["status"] == "published"


def test_publish_event_blocked_for_unapproved_organizer(db):
    """BR-1.5: Yönetici onayı olmayan organizatör etkinlik yayınlayamaz."""
    event_id = _insert_event(db, organizer_id=3, status="draft")

    with pytest.raises(EventPermissionError) as exc_info:
        publish_event(db, event_id, organizer_id=3)

    assert "onay" in str(exc_info.value).lower()
    assert get_event(db, event_id)["status"] == "draft"


def test_publish_event_blocked_when_no_approval_column_in_users(app):
    """Kullanıcı tablosunda onay sütunu yoksa güvenli varsayılan olarak yayınlama engellenir."""
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO venues (id, name, address, capacity) VALUES (1, 'V1', 'A', 100)")
        db.execute(
            "INSERT INTO users (id, email, password_hash, role) "
            "VALUES (1, 'org@e.com', 'x', 'organizer')"
        )
        db.execute(
            "INSERT INTO events ("
            "id, title, category, venue_id, start_time, end_time, "
            "capacity, price, status, organizer_id"
            ") VALUES (1, 'T', 'C', 1, '2026-12-01T10:00', '2026-12-01T12:00', 50, 0, 'draft', 1)"
        )
        db.commit()

        with pytest.raises(EventPermissionError):
            publish_event(db, 1, organizer_id=1)

        row = db.execute("SELECT status FROM events WHERE id = 1").fetchone()
        assert row["status"] == "draft"


def test_publish_event_idor_protection_different_organizer(db):
    """IDOR koruması: Organizatör başka bir organizatörün taslağını yayınlayamaz."""
    event_id = _insert_event(db, organizer_id=1, status="draft")

    with pytest.raises(EventPermissionError) as exc_info:
        publish_event(db, event_id, organizer_id=2)

    assert "etkinlik sahibi" in str(exc_info.value).lower()
    assert get_event(db, event_id)["status"] == "draft"


def test_publish_event_not_found(db):
    """Var olmayan etkinlik ID'si verildiğinde hata dönmelidir."""
    ok, event, errors = publish_event(db, 9999, organizer_id=1)

    assert ok is False
    assert event is None
    assert "Etkinlik bulunamadı." in errors


def test_publish_event_already_published(db):
    """Zaten yayınlanmış bir etkinlik tekrar yayınlanamaz."""
    event_id = _insert_event(db, organizer_id=1, status="published")

    ok, event, errors = publish_event(db, event_id, organizer_id=1)

    assert ok is False
    assert event is None
    assert errors == ["Yalnızca taslak etkinlikler yayınlanabilir."]


@pytest.mark.parametrize("invalid_id", [0, -1, None, "abc", True])
def test_publish_event_invalid_id(db, invalid_id):
    """Geçersiz etkinlik ID'si reddedilir."""
    ok, event, errors = publish_event(db, invalid_id, organizer_id=1)

    assert ok is False
    assert event is None
    assert errors == ["Geçersiz etkinlik kimliği."]


def test_publish_event_leaves_other_events_intact(db):
    """Bir etkinliğin yayınlanması diğer etkinliklerin taslak durumunu etkilemez."""
    e1 = _insert_event(db, title="Etkinlik 1", organizer_id=1, status="draft")
    e2 = _insert_event(db, title="Etkinlik 2", organizer_id=1, status="draft")

    ok, event, errors = publish_event(db, e1, organizer_id=1)

    assert ok is True
    assert event["status"] == "published"
    assert get_event(db, e1)["status"] == "published"
    assert get_event(db, e2)["status"] == "draft"


# --- TG-176: Birim Seviyesi İş Kuralları, Sınır Değer ve Hata Kurtarma Testleri ---


def _set_raw_field(db, event_id, field, value):
    """Test veritabanında CHECK kısıtını geçici kapatarak bozuk taslak verisi simüle eder."""
    db.execute("PRAGMA ignore_check_constraints = ON")
    try:
        db.execute(f"UPDATE events SET {field} = ? WHERE id = ?", (value, event_id))
        db.commit()
    finally:
        db.execute("PRAGMA ignore_check_constraints = OFF")


@pytest.mark.parametrize(
    "role,approved",
    [
        ("participant", 0),
        ("participant", 1),
        ("admin", 0),
        ("admin", 1),
    ],
)
def test_non_organizer_roles_cannot_publish_even_if_approved_flag_is_set(db, role, approved):
    """TC-176-U02 · BR-1.5: Yalnızca yönetici onaylı 'organizer' rolü etkinlik yayınlayabilir."""
    uid = db.execute(
        "INSERT INTO users (email, password_hash, role, organizer_approved) VALUES (?, 'x', ?, ?)",
        (f"{role}_{approved}@example.com", role, approved),
    ).lastrowid
    event_id = _insert_event(db, organizer_id=uid, status="draft")

    with pytest.raises(EventPermissionError):
        publish_event(db, event_id, organizer_id=uid)

    assert get_event(db, event_id)["status"] == "draft"


@pytest.mark.parametrize(
    "valid_capacity,start_time,end_time",
    [
        (1, "2026-12-02T10:00", "2026-12-02T12:00"),
        (99, "2026-12-03T10:00", "2026-12-03T12:00"),
        (100, "2026-12-04T10:00", "2026-12-04T12:00"),
    ],
)
def test_publish_event_capacity_boundary_valid_values(db, valid_capacity, start_time, end_time):
    """TC-176-U06 · BR-2.3: Salon kapasitesi (100) sınır değerlerinde (1, 99, 100) yayınlanır."""
    event_id = _insert_event(
        db,
        organizer_id=1,
        capacity=valid_capacity,
        start_time=start_time,
        end_time=end_time,
    )

    ok, event, errors = publish_event(db, event_id, organizer_id=1)

    assert ok is True
    assert errors == []
    assert event["status"] == "published"
    assert get_event(db, event_id)["status"] == "published"


@pytest.mark.parametrize(
    "invalid_capacity,expected_error",
    [
        (101, "Etkinlik kapasitesi salon kapasitesini aşamaz."),
        (500, "Etkinlik kapasitesi salon kapasitesini aşamaz."),
        (0, "Etkinlik kapasitesi en az 1 olmalıdır."),
        (-5, "Etkinlik kapasitesi en az 1 olmalıdır."),
        ("abc", "Etkinlik kapasitesi geçerli bir tam sayı olmalıdır."),
    ],
)
def test_publish_event_capacity_boundary_invalid_values(db, invalid_capacity, expected_error):
    """TC-176-U06 · BR-2.3: Salon kapasitesini aşan veya geçersiz kapasiteli taslak yayınlanamaz."""
    event_id = _insert_event(db, organizer_id=1, capacity=50)
    _set_raw_field(db, event_id, "capacity", invalid_capacity)

    ok, event, errors = publish_event(db, event_id, organizer_id=1)

    assert ok is False
    assert event is None
    assert expected_error in errors
    assert get_event(db, event_id)["status"] == "draft"


@pytest.mark.parametrize("valid_price", [0, 0.0, 0.01, 150.75])
def test_publish_event_price_boundary_valid_values(db, valid_price):
    """TC-176-U07 · BR-2.2: Ücretsiz (0) ve pozitif bilet fiyatlı taslaklar yayınlanabilir."""
    event_id = _insert_event(db, organizer_id=1, price=valid_price)

    ok, event, errors = publish_event(db, event_id, organizer_id=1)

    assert ok is True
    assert errors == []
    assert event["status"] == "published"


@pytest.mark.parametrize("invalid_price", [-0.01, -10, "gecersiz", "nan", "inf", float("inf")])
def test_publish_event_price_boundary_invalid_values(db, invalid_price):
    """TC-176-U07 · BR-2.2: Negatif veya sayısal olmayan bilet fiyatıyla yayınlama engellenir."""
    event_id = _insert_event(db, organizer_id=1, price=10.0)
    _set_raw_field(db, event_id, "price", invalid_price)

    ok, event, errors = publish_event(db, event_id, organizer_id=1)

    assert ok is False
    assert event is None
    assert "Bilet fiyatı sıfır veya pozitif bir sayı olmalıdır." in errors
    assert get_event(db, event_id)["status"] == "draft"


@pytest.mark.parametrize(
    "start_time,end_time",
    [
        ("2026-12-01T18:00", "2026-12-01T18:01"),  # Başlangıçtan 1 dk içeride
        ("2026-12-01T20:59", "2026-12-01T22:00"),  # Bitişten 1 dk içeride
        ("2026-12-01T17:59", "2026-12-01T18:01"),  # Sol sınırda 1 dk kesişim
        ("2026-12-01T18:00", "2026-12-01T21:00"),  # Birebir aynı aralık
    ],
)
def test_publish_event_one_minute_time_overlap_is_rejected(db, start_time, end_time):
    """TC-176-U09 · BR-2.4: Aynı salonda 1 dakikalık zaman kesişimi dahi yayınlamayı engeller."""
    _insert_event(
        db,
        organizer_id=2,
        status="published",
        start_time="2026-12-01T18:00",
        end_time="2026-12-01T21:00",
    )
    candidate_id = _insert_event(
        db,
        organizer_id=1,
        status="draft",
        start_time=start_time,
        end_time=end_time,
    )

    ok, event, errors = publish_event(db, candidate_id, organizer_id=1)

    assert ok is False
    assert event is None
    assert errors == ["Aynı salonda bu saatlerde yayınlanmış başka bir etkinlik var."]
    assert get_event(db, candidate_id)["status"] == "draft"


def test_publish_event_database_error_triggers_rollback_and_keeps_draft(db):
    """TC-176-U10: UPDATE sırasında DB hatası oluşursa rollback yapılır ve durum draft kalır."""
    import sqlite3

    event_id = _insert_event(db, organizer_id=1, status="draft")

    class FailingUpdateDb:
        def __init__(self, real_db):
            self.real_db = real_db
            self.rolled_back = False

        def execute(self, sql, *params):
            if sql.lstrip().upper().startswith("UPDATE"):
                raise sqlite3.OperationalError("simulated disk error on update")
            return self.real_db.execute(sql, *params)

        def commit(self):
            self.real_db.commit()

        def rollback(self):
            self.rolled_back = True
            self.real_db.rollback()

    wrapper = FailingUpdateDb(db)
    ok, event, errors = publish_event(wrapper, event_id, organizer_id=1)

    assert ok is False
    assert event is None
    assert errors == ["Etkinlik yayınlanırken veritabanı hatası oluştu."]
    assert wrapper.rolled_back is True
    assert get_event(db, event_id)["status"] == "draft"
