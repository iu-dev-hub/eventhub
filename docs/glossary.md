# Glossary (Terimler Sözlüğü)

Kodda İngilizce, arayüzde ve belgelerde Türkçe kullandığımız terimler.
Yeni bir terim kullanmaya başladığınızda buraya ekleyin (PR ile).

## Alan (domain) terimleri

| Kodda (English) | Türkçe | Örnek kullanım |
|---|---|---|
| `user`, `account` | kullanıcı, hesap | `users` tablosu, `app/accounts/` |
| `participant` | katılımcı | `role = "participant"` |
| `organizer` | organizatör | `role = "organizer"` |
| `admin` | yönetici | `role = "admin"` |
| `event` | etkinlik | `events` tablosu |
| `venue` | salon, mekân | `venues` tablosu |
| `capacity` | kapasite, kontenjan | `events.capacity` |
| `category` | kategori | `events.category` |
| `starts_at` / `ends_at` | başlangıç / bitiş zamanı | `events.starts_at` |
| `publish`, `draft` | yayınlamak, taslak | `status = "published"` |
| `ticket` | bilet | `tickets` tablosu |
| `reserve`, `reservation` | (bileti) ayırmak, ayırma | `status = "reserved"` |
| `purchase` | satın almak | `can_purchase()` |
| `sold out`, `full` | kontenjan dolu | `is_full()` |
| `waitlist` | bekleme listesi | `join_waitlist()` |
| `sales close` | satış kapanışı | `SALES_CLOSE_MINUTES = 60` |
| `check-in` | giriş (yoklama) | `check_in(ticket_code)` |
| `QR code` | QR kod | `tickets.qr_code` |
| `price` | fiyat | `events.price` |
| `discount`, `early bird` | indirim, erken kayıt | `EARLY_BIRD_DISCOUNT` |
| `payment` | ödeme | `app/payments/` |
| `refund` | iade | `calculate_refund()` |
| `occupancy rate` | doluluk oranı | rapor |
| `revenue` | gelir, satış tutarı | rapor |

## Süreç ve test terimleri

| English | Türkçe |
|---|---|
| backlog / product backlog | ürün iş listesi |
| user story | kullanıcı hikâyesi |
| acceptance criteria | kabul kriterleri |
| definition of ready / done | hazır tanımı / bitti tanımı |
| sprint / increment | sprint / artım |
| refinement | backlog iyileştirme |
| retrospective | retrospektif |
| impediment | engel |
| pull request (PR) | birleştirme isteği |
| code review | kod incelemesi |
| continuous integration (CI) | sürekli entegrasyon |
| test case | test durumu |
| test suite | test paketi |
| regression testing | regresyon testi |
| smoke test | duman testi |
| unit / integration / end-to-end (E2E) test | birim / entegrasyon / uçtan uca test |
| equivalence partitioning | denklik sınıfı bölümleme |
| boundary value analysis | sınır değer analizi |
| decision table testing | karar tablosu testi |
| state transition testing | durum geçiş testi |
| statement / branch coverage | komut / karar (dal) kapsamı |
| exploratory testing | keşif testi |
| error / defect / failure | hata / kusur / arıza |
| root cause | kök neden |
| severity / priority | önem derecesi / öncelik |
| testability | test edilebilirlik |
| mock / stub | sahte nesne / taslak |
| fixture | (pytest) test hazırlığı |
