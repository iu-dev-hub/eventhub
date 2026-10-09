# Back (Backend Developer) Rehberi

**Sunucu tarafı iş mantığından ve verinin doğruluğundan sorumlu kişi**

## 1. Rolün özü

Back geliştirici, modülün **iş kurallarını**, **veri işlemlerini** ve **sayfa
yönlendirmelerini** geliştirir. Scrum açısından Front ve Testçi ile birlikte
**Developers** sorumluluğunu taşırsınız: Artımı (çalışan ürün parçasını) birlikte üretirsiniz.

**Sorumluluklarınız:**

- İş kurallarını `services.py`'de uygulamak (kontenjan, süreler, fiyat ve iade)
- Veritabanı tablolarını tasarlamak ve sorguları yazmak
- Sayfa yönlendirmelerini (`routes.py`) yazmak, girdileri **sunucu tarafında** doğrulamak
- Diğer ekiplerin kullanacağı fonksiyonları **arayüz sözleşmesine** göre geliştirmek
- **Birim** ve **entegrasyon** testlerini yazmak
- Front'un PR'larını incelemek
- Planning poker sonucunu Taiga'ya girmek

## 2. Haftalık ritim

| Ne zaman? | Ne yaparsınız? |
|---|---|
| Sprint planlama | Hikâyeleri teknik görevlere bölersiniz, puan verirsiniz |
| Geliştirme | Görev al → dal aç → test + kod → PR |
| Her gün (hafta içi) | PR incelemeleri (24 saat içinde), Discussions günlüğü |
| Backlog iyileştirme | Teknik sorular: "Başka ekibe ihtiyacımız var mı? Tablo değişecek mi?" |
| Scrum of Scrums öncesi | Arayüz sözleşmesi veya şema değişikliği varsa SM'ye bildirin |

## 3. Kod yapısı: Katmanları ayırın

```text
routes.py     → İsteği al, servisi çağır, sonucu göster (ince katman)
services.py   → İş kuralları (BR) ve veritabanı işlemleri (kalın katman)
templates/    → Front'un alanı
```

**Neden?** İş kuralları `services.py`'de olunca **tarayıcı açmadan** birim testiyle
doğrulanabilir. `routes.py`'ye iş kuralı yazarsanız test etmesi zorlaşır.

### Kurallar

- İş kuralı sayılarını **sabit** olarak tanımlayın, koda gömmeyin:
  `SALES_CLOSE_MINUTES = 60`
- Fonksiyonların docstring'inde **BR koduna** atıf yapın.
- Mümkün olduğunca **saf fonksiyon** yazın: Girdi alır, çıktı verir, yan etkisi yoktur.
  Veritabanı işlemlerini ayrı fonksiyonlarda tutun.
- İsimler İngilizce, kullanıcı mesajları Türkçe.

## 4. Örnek: Bir iş kuralının baştan sona yolculuğu

> Örnek amaçlıdır; kendi modülünüzde kendi tasarımınızı yaparsınız.

**Kural:** BR-2.3 (etkinlik kapasitesi salon kapasitesini aşamaz)

### Adım 1: Önce test (TDD)

Kabul kriterlerinden ve sınır değer analizinden testleri yazın. Kod henüz yok; testler
kırmızı olmalı.

```python
# tests/unit/test_events.py
import pytest

from app.events.services import validate_event_capacity

VENUE_CAPACITY = 100


@pytest.mark.parametrize("capacity", [1, 99, 100])  # en küçük, sınırın altı, tam sınır
def test_valid_capacities_are_accepted(capacity):
    validate_event_capacity(capacity, VENUE_CAPACITY)  # hata fırlatmamalı


@pytest.mark.parametrize("capacity", [0, -5, 101])  # sıfır, negatif, sınırın üstü
def test_invalid_capacities_are_rejected(capacity):
    with pytest.raises(ValueError):
        validate_event_capacity(capacity, VENUE_CAPACITY)
```

### Adım 2: Kodu yazın

```python
# app/events/services.py
MIN_EVENT_CAPACITY = 1


def validate_event_capacity(capacity: int, venue_capacity: int) -> None:
    """Etkinlik kapasitesini doğrular (BR-2.3).

    Kural ihlalinde kullanıcıya gösterilebilecek Türkçe mesajlı ValueError fırlatır.
    """
    if capacity < MIN_EVENT_CAPACITY:
        raise ValueError("Etkinlik kapasitesi en az 1 olmalıdır.")
    if capacity > venue_capacity:
        raise ValueError("Etkinlik kapasitesi salon kapasitesini aşamaz.")
```

### Adım 3: Veritabanı işlemi (parametreli sorgu!)

```python
# app/tickets/services.py
from app.core.db import get_db

ACTIVE_TICKET_STATUSES = ("reserved", "paid", "used")


def count_active_tickets(event_id: int) -> int:
    """Etkinlik için kontenjandan düşülen bilet sayısı (BR-3.2 için kullanılır)."""
    row = get_db().execute(
        """
        SELECT COUNT(*) AS total
        FROM tickets
        WHERE event_id = ? AND status IN (?, ?, ?)
        """,
        (event_id, *ACTIVE_TICKET_STATUSES),
    ).fetchone()
    return row["total"]
```

> ⚠️ **Asla** `f"... WHERE event_id = {event_id}"` yazmayın: SQL enjeksiyonu açığıdır.
> Değerler her zaman `?` ve ayrı bir demet (tuple) ile verilir.

### Adım 4: İnce bir route

```python
# app/tickets/routes.py
from flask import Blueprint, flash, redirect, render_template, url_for

from app.tickets import services

bp = Blueprint("tickets", __name__, url_prefix="/tickets")


@bp.route("/")
def index():
    return render_template("tickets/index.html")


@bp.post("/<int:ticket_id>/cancel")
def cancel_ticket(ticket_id: int):
    try:
        services.cancel_ticket(ticket_id)
    except ValueError as error:
        flash(str(error), "error")
    else:
        flash("Biletiniz iptal edildi.", "success")
    return redirect(url_for("tickets.index"))
```

### Adım 5: Entegrasyon testi

```python
# tests/integration/test_tickets.py
def test_tickets_page_loads(client):
    assert client.get("/tickets/").status_code == 200
```

Gerçek verili entegrasyon testlerinde, test başında veritabanına gereken kayıtları
ekleyin (`app` fixture'ı her test için boş bir veritabanı verir):

```python
from app.core.db import get_db
from app.tickets import services


def test_cancelled_tickets_do_not_use_capacity(app):
    with app.app_context():
        db = get_db()
        # ... venues, events, users, tickets tablolarına test verisi ekleyin:
        #     2 "paid" ve 1 "cancelled" bilet ...
        db.commit()
        assert services.count_active_tickets(event_id=1) == 2
```

## 5. Veritabanı şeması (Sprint 2 ve sonrası)

Şema tüm ekiplerin ortak dosyasındadır: `app/core/schema.sql` (SM onayı gerekir).

- Tablo adları **çoğul**, sütunlar `snake_case`: `events.starts_at`
- Her tablonun başında sahibi yazılır: `-- Owner: team-tickets`
- Başka ekibin tablosuna referans (`REFERENCES users (id)`) Scrum of Scrums'ta konuşulur.
- Tarihleri **ISO biçiminde** metin olarak saklayın: `2026-10-15`
- Para değerlerini **tam sayı** (TL) olarak saklayın; ondalıklı sayı (float) kullanmayın.
- Şema değişince herkes `flask --app app init-db` ile veritabanını yeniden oluşturur
  (yerel veri silinir; bu derste sorun değil).

## 6. Arayüz sözleşmesi

Başka ekiplerin çağıracağı fonksiyonlar `docs/interface-contract.md`'de tanımlıdır
(Sprint 2'de SM'ler oluşturur). Sizin göreviniz:

- Sözleşmedeki fonksiyonu **tam olarak** tanımlandığı imza ve dönüş değeriyle yazmak
- İmzayı değiştirmeniz gerekiyorsa **önce** Scrum of Scrums'ta konuşmak; sözleşme ve
  kod **aynı PR'da** güncellenir
- Diğer ekibin fonksiyonu henüz hazır değilse, beklerken testlerde sahte (mock) sürüm
  kullanmak:

```python
# tests/unit/test_tickets.py  (team-tickets)
# app/tickets/services.py içinde: from app.events.services import get_event
from app.tickets.services import can_purchase


def test_purchase_blocked_when_event_is_not_published(monkeypatch):
    # team-events'in fonksiyonu yerine sahte sürüm: taslak durumda bir etkinlik
    fake_event = {"id": 7, "status": "draft", "capacity": 100}
    monkeypatch.setattr("app.tickets.services.get_event", lambda event_id: fake_event)
    user = {"id": 1, "role": "participant"}
    assert can_purchase(user, event_id=7) is False
```

## 7. Sunucu tarafı doğrulama

Front'ta form kontrolü olsa bile **sunucu her girdiyi yeniden doğrular**. Kullanıcı
tarayıcıyı atlatarak istek gönderebilir.

- Boş, çok uzun veya yanlış biçimli girdiyi reddedin (ör. negatif kapasite, geçmiş tarih).
- Yetkiyi kontrol edin (ör. salon tanımlama yalnızca yönetici: BR-2.1).
- Hata mesajını kullanıcıya Türkçe ve anlaşılır gösterin (`flash(..., "error")`).

## 8. Front ile çalışmak

- **Kullanıcı mesajlarını birlikte belirleyin:** PO'nun kabul kriterindeki metin,
  servisin döndürdüğü mesaj ve sayfadaki metin **birebir aynı** olmalı. Testçi bu metni arayacak.
- Servis fonksiyonlarınızın ne döndürdüğünü Front'a açıklayın (dönüş değeri, hata durumları).
- Birbirinizin PR'larını inceleyin; Front'un şablonunda iş kuralı varsa `services.py`'ye taşıyın.

## 9. Front'un PR'ını incelerken

- [ ] Şablonda iş kuralı (ör. `{% if count < 3 %}`) var mı? Varsa servise taşınmalı.
- [ ] Form alanlarının `name` değerleri route'taki `request.form[...]` ile uyumlu mu?
- [ ] Kullanıcı mesajları kabul kriterleriyle aynı mı?
- [ ] Genel PR inceleme kontrol listesi: `docs/guides/pull-requests.md`

## 10. Taiga'da Back

- Puanı ekip planning poker ile belirler; uzlaşılan sayıyı **Back alanına** siz girersiniz.
- Görevleri kendiniz oluşturup üstlenin; durumları güncel tutun.
- PR açınca hikâyeyi **İncelemede**, birleşince **Testte**'ye taşıyın.

## 11. Kontrol listesi (her PR öncesi)

- [ ] İş kuralları `services.py`'de, BR kodlarıyla belgelenmiş
- [ ] Sınır değerler için birim testleri var
- [ ] SQL sorguları parametreli
- [ ] Sunucu tarafı girdi doğrulaması var
- [ ] `pytest` yerelde geçiyor
- [ ] Arayüz sözleşmesi etkilendiyse güncellendi
- [ ] PR şablonu dolduruldu (YZ kullanımı dahil)

## 12. Sık yapılan hatalar

- **İş kuralını route'a veya şablona yazmak:** Test edilemez hale gelir.
- **Sihirli sayılar:** Kodda açıklamasız `60`, `14`, `4`. Kural değişince (değişecek!) bulamazsınız.
- **Off-by-one:** "En fazla 3" için `< 3` mü `<= 3` mü? Testle kanıtlayın.
- **Yalnızca mutlu yolu test etmek:** Dolu kontenjan, kapanmış satış, yetkisiz kullanıcı da test edilmeli.
- **Şemayı habersiz değiştirmek:** Diğer ekiplerin kodu ve testleri bozulur.
- **Float ile para hesabı:** `0.1 + 0.2 != 0.3`. Tam sayı kullanın.

İlgili rehberler: [pull-requests.md](pull-requests.md) ·
[soft-vibe-coding.md](soft-vibe-coding.md) · [communication.md](communication.md)
