"""unlock_seats servis fonksiyonu birim testleri (TG-132).

Test tasarımı: Her test tek bir davranışı doğrular.
Teknik: Durum geçişleri (locked → available, sold → değişmez, available → değişmez).
"""
from datetime import datetime, timedelta

import pytest

from app import create_app
from app.core.db import init_db
from app.payments import services


@pytest.fixture
def app(tmp_path):
    """Her test için ayrı geçici veritabanıyla uygulama örneği."""
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        init_db()
    return app


@pytest.fixture
def ctx(app):
    """Uygulama bağlamı: servis fonksiyonlarını doğrudan çağırmak için."""
    with app.app_context():
        yield


def _lock(ctx_unused, seats, app, now=None):
    """Yardımcı: verilen koltukları kilitler."""
    with app.app_context():
        return services.lock_seats(seats, now=now)


def _pay(app, seats, card="4242424242424242"):
    """Yardımcı: kiltli koltukları öder ve 'sold' yapar."""
    with app.app_context():
        return services.process_payment(card, 100, seats)


# --- unlock_seats: temel davranış ---

def test_unlock_releases_locked_seat(app):
    """Kilitli koltuk başarıyla serbest bırakılır."""
    with app.app_context():
        services.lock_seats(["A1"])
        ok, released = services.unlock_seats(["A1"])
    assert ok is True
    assert released == ["A1"]


def test_unlocked_seat_becomes_available_again(app):
    """Serbest bırakılan koltuk tekrar kilitlenebilir."""
    with app.app_context():
        services.lock_seats(["A1"])
        services.unlock_seats(["A1"])
        ok, _, _ = services.lock_seats(["A1"])
    assert ok is True


def test_unlock_returns_false_for_available_seat(app):
    """Kilitsiz (available) koltuk için unlock False döner."""
    with app.app_context():
        ok, released = services.unlock_seats(["B1"])
    assert ok is False
    assert released == []


def test_unlock_returns_false_for_sold_seat(app):
    """Satılmış koltuk serbest bırakılamaz."""
    with app.app_context():
        services.lock_seats(["A1"])
        services.process_payment("4242424242424242", 100, ["A1"])
        ok, released = services.unlock_seats(["A1"])
    assert ok is False
    assert released == []


def test_unlock_does_not_change_sold_seat_status(app):
    """Satılmış koltuk unlock sonrası hâlâ 'sold' olmalı."""
    with app.app_context():
        services.lock_seats(["A1"])
        services.process_payment("4242424242424242", 100, ["A1"])
        services.unlock_seats(["A1"])
        # Koltuk hâlâ satılmış olmalı: tekrar kilitlenemez
        ok, _, _ = services.lock_seats(["A1"])
    assert ok is False


# --- unlock_seats: karışık listeler ---

def test_unlock_releases_only_locked_seats_in_mixed_list(app):
    """Listede kilitli ve kilitsiz koltuklar varsa yalnızca kilitliler serbest bırakılır."""
    with app.app_context():
        services.lock_seats(["A1"])
        # A2 kilitsiz
        ok, released = services.unlock_seats(["A1", "A2"])
    assert ok is True
    assert "A1" in released
    assert "A2" not in released


def test_unlock_releases_multiple_locked_seats_at_once(app):
    """Birden fazla kilitli koltuk tek seferde serbest bırakılabilir."""
    with app.app_context():
        services.lock_seats(["A1", "A2", "A3"])
        ok, released = services.unlock_seats(["A1", "A2", "A3"])
    assert ok is True
    assert set(released) == {"A1", "A2", "A3"}


def test_unlock_returns_false_for_empty_list(app):
    """Boş liste için unlock False döner."""
    with app.app_context():
        ok, released = services.unlock_seats([])
    assert ok is False
    assert released == []


# --- unlock_seats: süresi dolmuş kilitle etkileşim ---

def test_unlock_releases_expired_lock_then_returns_false(app):
    """Süresi dolmuş kilit, unlock çağrısında 'available'a geçer
    ve unlock False döner (zaten serbest bırakıldı)."""
    start = datetime(2026, 1, 1, 12, 0, 0)
    with app.app_context():
        services.lock_seats(["A1"], now=start)
        # 10 dakika sonra kilit süresi dolmuş → unlock çağrısı
        expired_time = start + timedelta(minutes=10)
        ok, released = services.unlock_seats(["A1"], now=expired_time)
    # Süresi dolmuş koltuk 'available' oldu, 'locked' değil, dolayısıyla released = []
    assert ok is False
    assert released == []
