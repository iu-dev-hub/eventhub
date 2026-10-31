"""get_seats_status servis fonksiyonu birim testleri (TG-133).

Test tasarımı: Her test tek bir davranışı doğrular.
Teknik: Durum geçişleri ve sorgulama (available, locked, sold, expired).
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


def test_get_seats_status_returns_all_registered_seats(app):
    """Etkinliğe ait tüm kayıtlı koltukların durumu döner."""
    with app.app_context():
        services.lock_seats(["A1", "A2"])
        status = services.get_seats_status()
    codes = [s["seat_code"] for s in status]
    assert "A1" in codes
    assert "A2" in codes
    assert all(s["status"] == "locked" for s in status)


def test_get_seats_status_for_specific_seats(app):
    """Yalnızca istenen koltukların durumları filtrelenerek döner."""
    with app.app_context():
        services.lock_seats(["A1", "A2"])
        status = services.get_seats_status(["A1"])
    assert len(status) == 1
    assert status[0]["seat_code"] == "A1"
    assert status[0]["status"] == "locked"
    assert status[0]["locked_until"] is not None


def test_get_seats_status_creates_available_for_new_seat(app):
    """Henüz kilitlenmemiş koltuk sorgulandığında available olarak döner."""
    with app.app_context():
        status = services.get_seats_status(["B5"])
    assert len(status) == 1
    assert status[0]["seat_code"] == "B5"
    assert status[0]["status"] == "available"
    assert status[0]["locked_until"] is None


def test_get_seats_status_releases_expired_locks_before_query(app):
    """Süresi dolmuş kilitler sorgulama anında available duruma geçer."""
    start = datetime(2026, 1, 1, 10, 0, 0)
    with app.app_context():
        services.lock_seats(["A1"], now=start)
        # 15 dakika sonra sorgula
        later = start + timedelta(minutes=15)
        status = services.get_seats_status(["A1"], now=later)
    assert len(status) == 1
    assert status[0]["seat_code"] == "A1"
    assert status[0]["status"] == "available"
    assert status[0]["locked_until"] is None


def test_get_seats_status_shows_sold_status_after_payment(app):
    """Ödeme tamamlandıktan sonra koltuğun durumu 'sold' olarak döner."""
    with app.app_context():
        services.lock_seats(["A1"])
        services.process_payment("4242424242424242", 100, ["A1"])
        status = services.get_seats_status(["A1"])
    assert len(status) == 1
    assert status[0]["seat_code"] == "A1"
    assert status[0]["status"] == "sold"
    assert status[0]["locked_until"] is None
