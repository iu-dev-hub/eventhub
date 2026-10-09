# Roles (Rol Dağılımı)

Roller her rol döneminin sonunda değişir. Değişiklik bu dosyada bir PR ile yapılır;
aynı gün **GitHub rol takımları** ve **Taiga'daki proje rolleri** de güncellenir.

| Rol dönemi | Sprintler | Haftalar |
|---|---|---|
| 1 | Sprint 1–4 | 2–5 |
| 2 | Sprint 5–8 | 6–9 |
| 3 | Sprint 9–12 | 10–13 |

## Güncel dönem: 1. Rol Dönemi (Sprint 1–4)

| Ekip | Product Owner | Scrum Master | Back | Front | Testçi |
|---|---|---|---|---|---|
| Team Accounts (Hesaplar) | @ | @ | @ | @ | @ |
| Team Events (Etkinlikler ve Salonlar) | @ | @ | @ | @ | @ |
| Team Tickets (Bilet ve Kontenjan) | @ | @ | @ | @ | @ |
| Team Payments (Ödeme, İade ve Raporlar) | @ | @ | @ | @ | @ |

**Baş Product Owner / Müşteri:** Dr. Öğr. Üyesi Hakan DUMAN

**Eksik üye:** Yedek veya joker yoktur. Bir rol boş kaldığında (devamsızlık veya eksik
ekip) o rolü öğretim üyesi üstlenir: karar, onay, kod incelemesi ve kabul testi işlerini
yapar, ekip adına kod yazmaz. Geliştirici eksikse ekip sprint kapsamını daraltır.

## Rol sorumlulukları (özet)

| Rol (Taiga) | Sektör unvanı | Temel sorumluluk |
|---|---|---|
| Product Owner | Product Owner | Backlog'u yönetir, kabul kriterlerini yazar, işi kabul eder |
| Scrum Master | Scrum Master / Agile Coach | Scrum'ın etkinliği, engeller, metrikler, Scrum of Scrums |
| Back | Backend Developer | İş kuralları, veri, sunucu doğrulaması, birim ve entegrasyon testleri |
| Front | Frontend Developer | Arayüz, formlar, mesajlar, erişilebilirlik ve test edilebilirlik |
| Testçi | QA / Test Engineer | Test tasarımı, E2E otomasyon, regresyon, hata yönetimi, test raporu |

Scrum Rehberi'ne göre Back, Front ve Testçi birlikte **Developers** sorumluluğunu taşır.

## Taiga rolleri

Taiga projesindeki roller: `Product Owner`, `Scrum Master`, `Back`, `Front`,
`Testçi` ve yalnızca görüntüleme yetkili `Stakeholder` (konuklar için).
Öğretim üyesi proje yöneticisidir (admin).

## GitHub takımları

| Takım | Üyeler | Kullanım |
|---|---|---|
| `@iu-dev-hub/team-accounts` | Ekibin 5 üyesi (dönem boyunca sabit) | Hesaplar modülü sahipliği |
| `@iu-dev-hub/team-events` | Ekibin 5 üyesi | Etkinlikler ve Salonlar modülü sahipliği |
| `@iu-dev-hub/team-tickets` | Ekibin 5 üyesi | Bilet ve Kontenjan modülü sahipliği |
| `@iu-dev-hub/team-payments` | Ekibin 5 üyesi | Ödeme, İade ve Raporlar modülü sahipliği |
| `@iu-dev-hub/product-owners` | 4 PO | Ürün belgeleri onayı, PO duyuruları |
| `@iu-dev-hub/scrum-masters` | 4 SM | Ortak kod onayı, Scrum of Scrums |
| `@iu-dev-hub/developers` | 4 Back + 4 Front | Geliştirici duyuruları |
| `@iu-dev-hub/qa` | 4 testçi | E2E test onayı |


## Geçmiş dönemler

<!-- Rol değişiminde güncel tabloyu buraya taşıyın. -->
