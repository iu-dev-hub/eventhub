"""Koltuk kilitleme ve ödeme iş kuralları."""
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path

# Koltuk kilidi süresi (dakika)
LOCK_MINUTES = 10
# Geçerli kart numarası uzunluğu (BR-4.3)
CARD_LENGTH = 16

# Log dosyası proje kök klasöründe oluşur
LOG_FILE = Path(__file__).resolve().parents[2] / "payment_logs.json"

# Aynı anda gelen isteklerde çakışmayı önlemek için kilit
_mutex = threading.Lock()

locked_seats = {}   # {"A1": kilidin bitiş zamanı}
sold_seats = set()  # satın alınmış ("dolu") koltuklar
payment_logs = []   # tüm ödeme denemeleri


def reset_state():
    """Tüm durumu sıfırlar (testlerde kullanılır)."""
    with _mutex:
        locked_seats.clear()
        sold_seats.clear()
        payment_logs.clear()


def _clean_expired(now):
    """Süresi dolan kilitleri kaldırır. Çağıran kişi _mutex'i tutmalıdır."""
    expired = [seat for seat, exp in locked_seats.items() if exp <= now]
    for seat in expired:
        del locked_seats[seat]


def _write_log(seats, success, message):
    """Ödeme denemesini listeye ve JSON dosyasına yazar."""
    payment_logs.append({
        "tarih": datetime.now().isoformat(timespec="seconds"),
        "koltuklar": seats,
        "success": success,
        "mesaj": message,
    })
    LOG_FILE.write_text(
        json.dumps(payment_logs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def lock_seats(seats, now=None):
    """Koltukları 10 dk kilitler.

    Başarılıysa (True, None, bitiş_zamanı), bir koltuk zaten kilitli
    veya doluysa (False, çakışan_koltuklar, None) döner.
    """
    now = now or datetime.now()
    with _mutex:
        _clean_expired(now)
        taken = [s for s in seats if s in locked_seats or s in sold_seats]
        if taken:
            return False, taken, None
        expires = now + timedelta(minutes=LOCK_MINUTES)
        for seat in seats:
            locked_seats[seat] = expires
        return True, None, expires


def process_payment(card_number, amount, seats):
    """Sahte ödeme: önce kart ve koltuklar doğrulanır, sonra son 4 haneye bakılır.

    amount şimdilik sadece alınıyor, tutar kontrolü bu görevin dışında.
    """
    with _mutex:
        _clean_expired(datetime.now())

        # BR-4.3: kart tam 16 haneli ve yalnızca rakam olmalı.
        # isascii(), "²" gibi rakama benzeyen karakterleri dışarıda bırakır.
        if (
            len(card_number) != CARD_LENGTH
            or not card_number.isascii()
            or not card_number.isdigit()
        ):
            _write_log(seats, False, "Geçersiz kart")
            return {"success": False, "message": "Geçersiz kart"}

        # Satılmış koltuk ikinci kez satılamaz
        already_sold = [seat for seat in seats if seat in sold_seats]
        if already_sold:
            _write_log(seats, False, "Koltuk zaten satılmış")
            return {"success": False, "message": "Koltuk zaten satılmış"}

        if card_number.endswith("4242"):
            # Başarılı ödeme: kilitli koltuklar "dolu" olur
            for seat in seats:
                locked_seats.pop(seat, None)
                sold_seats.add(seat)
            _write_log(seats, True, "Ödeme başarılı")
            return {"success": True, "ticketId": "T12345"}

        if card_number.endswith("0000"):
            _write_log(seats, False, "Yetersiz bakiye")
            return {"success": False, "message": "Yetersiz bakiye"}

                # Ödemeden önce koltuk kilitli olmalı
        not_locked = [seat for seat in seats if seat not in locked_seats]
        if not_locked:
            _write_log(seats, False, "Koltuk kilitli değil")
            return {"success": False, "message": "Koltuk kilitli değil"}

        # Tanımsız kartlar da loglanır ("tüm denemeler" kuralı)
        _write_log(seats, False, "Geçersiz kart")
        return {"success": False, "message": "Geçersiz kart"}
