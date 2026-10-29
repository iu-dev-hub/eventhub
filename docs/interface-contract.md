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
> alanlar mevcut form/doğrulama alanlarından, Tickets'in beklentisinden ve Sprint 3'te
> taslak etkinlik kaydedilecek olmasından türetilmiş **önerilen** yapıdır. `status` ve
> `organizer_id` **öneridir**; ilgili ekiplerle kesinleşene kadar **açık karardır** (bkz. 2.6).

| Alan | Tür | Kısıt | Durum | Açıklama |
|---|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Öneri | Etkinlik kimliği |
| `title` | TEXT | NOT NULL | Öneri | Başlık |
| `category` | TEXT | NOT NULL | Öneri | Kategori |
| `venue_id` | INTEGER | NOT NULL, FOREIGN KEY → `venues(id)` | Öneri | Salon (BR-2.2) |
| `start_time` | TEXT | NOT NULL | Öneri | Başlangıç, ISO 8601 (`2026-12-01T10:00`) |
| `end_time` | TEXT | NOT NULL | Öneri | Bitiş, ISO 8601 |
| `capacity` | INTEGER | NOT NULL, `> 0` | Öneri | Etkinlik kapasitesi; salon kapasitesini aşamaz (BR-2.3) |
| `price` | REAL | NOT NULL, `>= 0` | Öneri | Bilet fiyatı; `0` = ücretsiz (BR-4.6) |
| `status` | TEXT | NOT NULL, DEFAULT `'draft'` | **Açık karar** | Etkinlik durumu. Öneri: `draft` (taslak, Sprint 3), `published` (yayında), `cancelled` (iptal, BR-2.7/BR-4.5) |
| `organizer_id` | INTEGER | NOT NULL, FOREIGN KEY → `users(id)` | **Açık karar** | Etkinliği oluşturan kullanıcı; değer `session["user_id"]` (bkz. 1) |

Doğrulama kuralları: zorunlu alanlar, `capacity >= 1`, `capacity <= venues.capacity`
(BR-2.3), `price >= 0`.

**`status` ile ilgili öneriler (açık karar):**
- Yeni kayıt varsayılan olarak `draft` olur; yalnızca `published` etkinlikler katılımcılara
  listelenir ve Tickets'te satışa açılır. Tickets/Payments `draft` ve `cancelled`
  etkinlikler için bilet satmamalıdır.
- Taslakta hangi alanların zorunlu olacağı (tam doğrulama mı, gevşetilmiş mi) Sprint 3'te
  netleştirilecektir; bu sürümde tablo önerisi tam alan setini varsayar.

**`organizer_id` ile ilgili öneriler (açık karar):**
- Etkinliği yalnızca `organizer` veya `admin` rolü oluşturur; `organizer_id` istek gövdesinden
  değil, oturumdan (`g.user_id`) alınır.
- Tickets/Payments tarafında BR-4.7 (organizatör kendi etkinliklerinin raporunu görür) için
  gereklidir.

### 2.5 Events'in diğer modüllere sağladığı veriler

| Tüketen | Gereken | Events'in sağladığı |
|---|---|---|
| Tickets | Etkinliğin kapasitesi, başlangıç zamanı (satış kapanışı, BR-3.3/3.7) | `events.id`, `events.capacity`, `events.start_time` |
| Tickets | Etkinliğin satışa açık olup olmadığı | `events.status` (**öneri**, bkz. 2.4) |
| Payments | Etkinlik fiyatı, başlangıç zamanı (erken kayıt/iade, BR-4.1/4.4), ücretsiz mi | `events.price`, `events.start_time` |
| Payments / raporlar | Etkinliği oluşturan organizatör (BR-4.7) | `events.organizer_id` (**öneri**, bkz. 2.4) |

`tickets.event_id` → `events.id` ilişkisidir. Tickets/Payments `events` tablosuna
**yalnızca okuma** yapar; yazma yalnızca Events servislerindendir.

### 2.6 Açık kararlar ve ekip doğrulama durumu

Aşağıdaki tablo, hangi sözleşme maddesinin hangi ekiple doğrulanması gerektiğini ve
durumunu gösterir. **Onaylanmayan maddeler açık karar olarak kalır;** onay alındıkça
ilgili ekip durumu günceller. Durum sütunundaki "Koddan teyit" ifadesi, ilgili ekibin
kodunun incelenmesiyle bulunan bilgiyi belirtir; ekibin yazılı onayı anlamına **gelmez**.

| # | Madde | Ekip | Durum |
|---|---|---|---|
| 1 | Oturum anahtarları (`user_id`, `user_email`, `user_role`) ve `@role_required("admin")` yanıtları: 401 oturum yok, 403 yetki yok | Accounts | Koddan teyit (`app/accounts/security.py`). Ekip onayı **bekleniyor** |
| 2 | `events.organizer_id` → `users.id` ilişkisi ve değerin `session["user_id"]`'den alınması | Accounts | **Açık karar**, onay bekleniyor |
| 3 | `events` tablosu ve alanları (2.4). `app/tickets/services.py` şimdiden `SELECT capacity FROM events WHERE id = ?` çalıştırıyor, ancak tablo yok | Tickets | Koddan teyit: `id` ve `capacity` bekleniyor. Diğer alanlar **açık karar** |
| 4 | `event_id` türü: `tickets.event_id` şemada INTEGER, Tickets mock verisinde (`app/api/tickets.json`, TG-67) metin (`"evt-001"`). `events.id` INTEGER önerilir | Tickets | **Açık karar** — mock verinin INTEGER'a uyarlanması gerekir |
| 5 | `events.status` değerleri ve satışa açık olma kuralı (`published` dışında satış yok) | Tickets | **Açık karar**, onay bekleniyor |
| 6 | `events.price` (REAL) ve `events.start_time` (ISO 8601 metin) alanlarının Payments hesaplarına uygunluğu (BR-4.1, BR-4.4) | Payments | Koddan teyit **yapılamadı** (Payments kodu `events` tablosunu henüz kullanmıyor). **Açık karar** |
| 7 | `events.organizer_id` ile organizatör raporu (BR-4.7) | Payments | **Açık karar**, onay bekleniyor |
| 8 | `events` tablosunun eklenmesi: Events ekibi ayrı görevle ekler; Tickets o zamana kadar tabloyu kendi testlerinde oluşturmaz | Events / Tickets | **Açık karar** |
| 9 | Salon adı UNIQUE kısıtı (2.1) | Scrum Master | **Açık karar**, Scrum Master netleştirecek |
| 10 | Salon listeleme servis imzaları (2.3) | Events | **Açık karar** |
| 11 | Kapasite/zaman çakışması (BR-2.3, BR-2.4) hata biçimi. Öneri: 400 `{"error", "errors"}` (2.2 ile aynı) | Events | **Açık karar** |

### 2.7 Ortak hata yanıtı biçimi (Events uçları)

JSON hata yanıtları `{"error": "<mesaj>"}` biçimindedir (Accounts ile uyumlu); birden
fazla doğrulama hatası varsa ek olarak `"errors": ["..."]` listesi döner.

---

## 3. Tickets

> Sahibi team-tickets. Bu bölümü Tickets ekibi doldurur.

## 4. Payments

> Sahibi team-payments. Bu bölümü Payments ekibi doldurur.
