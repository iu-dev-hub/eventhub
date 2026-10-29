# Modüller Arası Arayüz Sözleşmesi (Interface Contract)

Bu belge, modüllerin birbirinden beklediği veri alanlarını, servis arayüzlerini ve hata
durumlarını tanımlar. **Her ekip yalnızca kendi bölümünü düzenler**; başka ekibin bölümü
değişecekse o ekibin onayı PR'da belirtilir.

Kurallar: tablo/sütun adları İngilizce `snake_case`, tablo adları çoğul. Tüm modüller tek
SQLite veritabanını (`get_db()`) kullanır. İş kuralı kodları için `docs/business-rules.md`.

| Bölüm | Sahip | Durum |
|---|---|---|
| 1. Accounts | team-accounts | Bu PR'da yalnızca Events'in kullandığı kısım özetlendi; ekip tamamlayacak |
| 2. Events | team-events | Bu belge (TG-44) |
| 3. Tickets | team-tickets | Ekip dolduracak |
| 4. Payments | team-payments | Ekip dolduracak |

---

## 1. Accounts (Events'in kullandığı kısım)

> Sahibi team-accounts. Aşağıdaki özet, Accounts kodundaki gerçek yapıdan
> (`app/accounts/security.py`, `app/accounts/routes.py`) alınmıştır.

### Oturum anahtarları (Flask `session`)

| Anahtar | Tür | Açıklama |
|---|---|---|
| `user_id` | int | Kullanıcı kimliği (`users.id`) |
| `user_email` | str | Kullanıcı e-postası |
| `user_role` | str | `participant`, `organizer` veya `admin` (BR-1.1) |

### Yetkilendirme decorator'ları

```python
from app.accounts.security import login_required, role_required
```

| Decorator | Oturum yok | Rol uymuyor | Başarılı |
|---|---|---|---|
| `@login_required` | 401 `{"error": "Oturum açılmamış."}` | – | `g.user_id`, `g.user_email`, `g.user_role` doldurulur |
| `@role_required("admin")` | 401 `{"error": "Oturum açılmamış."}` | 403 `{"error": "Bu işlem için yetkiniz bulunmamaktadır."}` | `g.*` doldurulur |

Events kullanımı: Salon oluşturma rotası `@role_required("admin")` ile korunur. Yetki
kontrolü yalnızca sunucu tarafında yapılır; arayüzde buton gizlemek yetki sayılmaz.
Events, rolü kendisi doğrulamaz ve `users` tablosuna doğrudan erişmez.

---

## 2. Events

### 2.1 Salon verisi (`venues`) — BR-2.1

Tablo: `venues` (`app/core/schema.sql`, TG-40). Sahibi team-events.

| Alan | Tür | Kısıt | Açıklama |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Salon kimliği |
| `name` | TEXT | NOT NULL, UNIQUE | Salon adı (en fazla 100 karakter, serviste kontrol edilir) |
| `address` | TEXT | NOT NULL | Salon adresi |
| `capacity` | INTEGER | NOT NULL, `> 0` | Salon kapasitesi |

Salon JSON gösterimi (servis/uç nokta yanıtlarında kullanılan biçim):

```json
{"id": 1, "name": "Salon A", "address": "Beyazıt, İstanbul", "capacity": 100}
```

> `name` üzerindeki UNIQUE kısıtı Scrum Master tarafından netleştirilecektir; karar
> değişirse bu bölüm güncellenir.

### 2.2 Salon oluşturma — `POST /events/venues` (TG-41)

Yetki: yalnızca `admin` (`@role_required("admin")`).

İstek (JSON veya form): `name`, `address`, `capacity`.

Servis: `app.events.services.create_venue(db, name, address, capacity)`
dönüş: `(ok: bool, venue: dict | None, errors: list[str])`.

| Durum | HTTP | Yanıt gövdesi |
|---|---|---|
| Başarılı | 201 | Salon nesnesi (`id`, `name`, `address`, `capacity`) |
| Alan eksik / kapasite geçersiz (`< 1`, sayı değil) / ad çok uzun | 400 | `{"error": "<ilk hata>", "errors": [...]}` |
| Aynı isimde salon var | 409 | `{"error": "Bu isimde bir salon zaten mevcut.", "errors": [...]}` |
| Oturum yok | 401 | Accounts decorator yanıtı (bkz. 1) |
| Rol `admin` değil (`organizer`, `participant`) | 403 | Accounts decorator yanıtı (bkz. 1) |

Hata durumlarında veritabanına kayıt yazılmaz.

### 2.3 Salon listeleme — PLANLANAN (henüz kodlanmadı)

Salon listeleme servisi/ekranı #26 (PB-02) kapsamındadır ve bu sözleşme sürümünde
kodlanmış değildir. Diğer modüllerin salon bilgisine ihtiyacı olursa **`venues` tablosunu
doğrudan okumak yerine** Events'in sağlayacağı servis kullanılmalıdır:

| Servis (planlanan) | Giriş | Dönüş | Hata |
|---|---|---|---|
| `list_venues(db)` | – | `list[venue]` (2.1 biçimi, `name`'e göre sıralı) | – |
| `get_venue(db, venue_id)` | `venue_id: int` | `venue` veya `None` | – |

Bu imzalar ilgili görev başlayınca kesinleşir; değişirse bu bölüm güncellenir.

### 2.4 Etkinlik verisi (`events`) — BR-2.2, BR-2.3

> **Durum:** `events` tablosu henüz `schema.sql` içinde **yoktur**. Etkinlik oluşturma
> şu an yalnızca form doğrulamasıdır (`validate_event_creation`; kayıt yapılmaz). Aşağıdaki
> alanlar mevcut form/doğrulama alanlarından ve Tickets'in beklentisinden türetilmiş
> **önerilen** yapıdır; tablo eklenirken Tickets ve Payments ile doğrulanacaktır.

| Alan | Tür | Kısıt | Açıklama |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Etkinlik kimliği |
| `title` | TEXT | NOT NULL | Başlık |
| `category` | TEXT | NOT NULL | Kategori |
| `venue_id` | INTEGER | NOT NULL, FOREIGN KEY → `venues(id)` | Salon (BR-2.2) |
| `start_time` | TEXT | NOT NULL | Başlangıç, ISO 8601 (`2026-12-01T10:00`) |
| `end_time` | TEXT | NOT NULL | Bitiş, ISO 8601 |
| `capacity` | INTEGER | NOT NULL, `> 0` | Etkinlik kapasitesi; salon kapasitesini aşamaz (BR-2.3) |
| `price` | REAL | NOT NULL, `>= 0` | Bilet fiyatı; `0` = ücretsiz (BR-4.6) |

Doğrulama kuralları: zorunlu alanlar, `capacity >= 1`, `capacity <= venues.capacity`
(BR-2.3), `price >= 0`.

### 2.5 Events'in diğer modüllere sağladığı veriler

| Tüketen | Gereken | Events'in sağladığı |
|---|---|---|
| Tickets | Etkinliğin kapasitesi, başlangıç zamanı (satış kapanışı, BR-3.3/3.7) | `events.id`, `events.capacity`, `events.start_time` |
| Payments | Etkinlik fiyatı, başlangıç zamanı (erken kayıt/iade, BR-4.1/4.4), ücretsiz mi | `events.price`, `events.start_time` |
| Tickets / Payments | Etkinliği oluşturan organizatör (BR-4.7 raporlar) | **Açık soru:** `events.organizer_id` eklensin mi (bkz. 2.6) |

`tickets.event_id` → `events.id` ilişkisidir. Tickets/Payments `events` tablosuna
**yalnızca okuma** yapar; yazma yalnızca Events servislerindendir.

### 2.6 Açık kararlar (ilgili ekiplerle doğrulanacak)

Bu maddeler kodda ve belgede henüz kesinleşmemiştir; PR incelemesinde ilgili ekipler
onaylamalıdır.

1. **Tickets:** `app/tickets/services.py` şimdiden `SELECT capacity FROM events WHERE id = ?`
   çalıştırıyor, ancak `events` tablosu yok. Tablo ne zaman, hangi alanlarla eklenecek?
   (Bu bölümdeki 2.4 önerisi kabul mü?)
2. **Etkinlik tablosunun sahibi/zamanı:** `events` tablosunu Events ekibi ayrı bir görevle
   ekleyecek; Tickets o zamana kadar testlerinde tabloyu kendisi oluşturmamalı.
3. **`organizer_id`:** Etkinlik sahibi alanı `events.organizer_id` (→ `users.id`) olarak
   eklensin mi? (Payments raporları ve BR-4.7 için gerekli olabilir.)
4. **Salon adı UNIQUE:** Scrum Master netleştirecek (2.1).
5. **Salon listeleme servis imzaları** (2.3) kesinleştirilecek.
6. **Kapasite/zaman çakışması** (BR-2.3, BR-2.4): Etkinlik kaydı eklenirken hangi hata
   kodu/mesaj biçimi kullanılacak? Öneri: oluşturma uçlarında 400 `{"error", "errors"}`
   biçimi (2.2 ile aynı).

### 2.7 Ortak hata yanıtı biçimi (Events uçları)

JSON hata yanıtları `{"error": "<mesaj>"}` biçimindedir (Accounts ile uyumlu); birden
fazla doğrulama hatası varsa ek olarak `"errors": ["..."]` listesi döner.

---

## 3. Tickets

> Sahibi team-tickets. Bu bölümü Tickets ekibi doldurur.

## 4. Payments

> Sahibi team-payments. Bu bölümü Payments ekibi doldurur.
