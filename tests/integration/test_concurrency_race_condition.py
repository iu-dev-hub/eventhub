"""Eş zamanlı yarış durumu (race condition) ve kilit stres testleri (TG-147)."""
import threading

import pytest

from app import create_app
from app.core.db import get_db, init_db
from app.payments import services

VALID_CARD = "4242424242424242"


@pytest.fixture
def test_app(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "LOG_FILE", tmp_path / "payment_logs.json")
    services._FAILED_ATTEMPTS.clear()
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        init_db()
    return app


def test_concurrent_threads_locking_same_seat_exact_one_winner(test_app):
    """Aynı anda 10 paralel thread aynı koltuğu kilitlemek istediğinde yalnızca 1 tanesi kazanır."""
    num_threads = 10
    barrier = threading.Barrier(num_threads)
    results = []

    def try_lock(thread_id):
        barrier.wait()  # Tüm thread'ler aynı anda start alır
        with test_app.app_context():
            try:
                ok, taken, expires = services.lock_seats(["Z1"], event_id=1)
                results.append((ok, thread_id))
            except Exception as e:
                results.append((False, str(e)))

    threads = [
        threading.Thread(target=try_lock, args=(i,)) for i in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Tam olarak 1 adet True (başarılı kilit), 9 adet False olmalı
    successes = [r for r in results if r[0] is True]
    failures = [r for r in results if r[0] is False]

    assert len(successes) == 1
    assert len(failures) == num_threads - 1

    # Veritabanında koltuk durumu locked olmalı ve tek kayıt bulunmalı
    with test_app.app_context():
        db = get_db()
        row = db.execute(
            "SELECT status FROM seats WHERE event_id = 1 AND seat_code = 'Z1'"
        ).fetchone()
        assert row is not None
        assert row["status"] == "locked"


def test_concurrent_threads_paying_for_locked_seat_exact_one_succeeds(test_app):
    """Kilitli bir koltuk için eş zamanlı ödeme yapıldığında yalnızca 1 ödeme ve bilet oluşur."""
    with test_app.app_context():
        services.lock_seats(["Z2"], event_id=1)

    num_threads = 5
    barrier = threading.Barrier(num_threads)
    pay_results = []

    def try_pay(thread_id):
        barrier.wait()
        with test_app.app_context():
            res = services.process_payment(
                VALID_CARD,
                100,
                ["Z2"],
                event_id=1,
                user_id=thread_id,
            )
            pay_results.append(res)

    threads = [threading.Thread(target=try_pay, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    successes = [r for r in pay_results if r.get("success") is True]
    failures = [r for r in pay_results if r.get("success") is False]

    assert len(successes) == 1
    assert len(failures) == num_threads - 1

    # DB doğrulaması: reservations tablosunda Z2 için yalnızca 1 kayıt oluşmalı
    with test_app.app_context():
        db = get_db()
        count = db.execute(
            "SELECT COUNT(*) AS c FROM reservations WHERE id = ?",
            (successes[0]["reservationId"],),
        ).fetchone()["c"]
        assert count == 1

        seat_row = db.execute(
            "SELECT status FROM seats WHERE event_id = 1 AND seat_code = 'Z2'"
        ).fetchone()
        assert seat_row["status"] == "sold"
