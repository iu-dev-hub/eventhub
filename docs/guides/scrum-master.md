# Scrum Master Rehberi

**Scrum'ın etkin uygulanmasından sorumlu kişi**

## 1. Rolün özü

Scrum Rehberi'ne göre Scrum Master, ekibin Scrum'ı anlamasına ve uygulamasına yardım
eder; ekibin **etkinliğinden** sorumludur.

**Ne yaparsınız?**

- Scrum olaylarının (planlama, günlük, review, retrospektif) yapılmasını ve
  **zaman sınırına** uyulmasını sağlarsınız.
- Ekibin önündeki **engelleri** kaldırırsınız veya kaldırabilecek kişiye taşırsınız.
- Ekibi gözlemler, süreç sorunlarını görünür kılarsınız.
- Ekibinizi **Scrum of Scrums**'ta temsil edersiniz.
- PO'ya backlog yönetiminde destek olursunuz.

**Ne değilsiniz?**

- **Yönetici değilsiniz:** Kime hangi işin verileceğine ekip karar verir.
- **Sekreter değilsiniz:** Herkes kendi Taiga kaydını kendisi günceller.
- **Her sorunu çözen kişi değilsiniz:** Ekibin kendi sorununu çözmesine yardım edersiniz.

## 2. Haftalık ritim

| Ne zaman? | Ne yaparsınız? |
|---|---|
| Uygulama dersi 0:00–0:25 | **Sprint review**'u zamanında başlatır, süreyi tutarsınız |
| 0:25–0:40 | **Retrospektifi** yönetirsiniz |
| 0:40–1:00 | **Sprint planlamayı** yönetirsiniz; Taiga'da yeni sprinti açarsınız |
| 1:00–1:10 | **Scrum of Scrums**'a katılırsınız |
| 1:10–2:50 | Ekip çalışırken engelleri takip edersiniz |
| 2:50–3:00 | Pano kapanış kontrolü |
| Hafta içi | Discussions günlüğünü takip eder, engellere yanıt verirsiniz |

## 3. Sprint review (25 dk, tüm sınıf)

Her ekibin **5 dakikası** var. Zamanı siz tutarsınız.

1. PO: Sprint hedefi neydi, hangi hikâyeler bitti, hangileri bitmedi (1 dk)
2. Geliştiriciler: **Çalışan ürünün demosu** (3 dk): Slayt değil, uygulama
3. Testçi: Test özeti: kaç test, kaç hata, açık kritik hata var mı (30 sn)
4. Müşteri geri bildirimi (30 sn)

Siz de Taiga'daki **burndown grafiğini** gösterirsiniz (bkz. Bölüm 7).

## 4. Retrospektif (15 dk, ekip içi)

Amaç: **Nasıl çalıştığımızı** iyileştirmek. Ürün değil, süreç konuşulur.

### Format 1: Başla / Bırak / Devam Et (önerilen)

| 🟢 Başla | 🔴 Bırak | 🔵 Devam et |
|---|---|---|
| Neyi yapmaya başlamalıyız? | Neyi yapmayı bırakmalıyız? | Neyi iyi yapıyoruz? |

### Format 2: 4L (dönem ortasında çeşitlilik için)

**Liked** (sevdim), **Learned** (öğrendim), **Lacked** (eksikti), **Longed for** (özledim/isterdim)

### Akış

1. **Güvenli ortam (1 dk):** "Burada kişileri değil, süreci konuşuyoruz."
2. **Önceki aksiyonlar (2 dk):** Geçen hafta karar verdiğimiz şeyleri yaptık mı?
3. **Fikir toplama (5 dk):** Herkes sessizce yazar (Taiga Wiki veya kâğıt).
4. **Tartışma (5 dk):** Benzer fikirleri gruplayın; en önemli 1–2 konuyu seçin.
5. **Aksiyon (2 dk):** **En fazla 2** somut aksiyon, her birinin **sorumlusu** olsun.

### İyi ve kötü aksiyon

| ❌ Kötü | ✅ İyi |
|---|---|
| "Daha iyi iletişim kuracağız." | "Her PR açıldığında Discussions günlüğüne link atılacak. Sorumlu: Ayşe" |
| "Testleri daha çok yazacağız." | "PR şablonundaki test bölümü boşsa inceleyen 'Request changes' verecek. Sorumlu: Mehmet" |

Retrospektif notlarını Taiga Wiki'de **ekip sayfasına** yazın:

```text
## Sprint 3 Retrospektifi (2026-10-23)
Önceki aksiyonlar: [x] PR linkleri günlüğe yazıldı  [ ] ...
Başla: ...
Bırak: ...
Devam et: ...
Aksiyonlar:
1. ... — Sorumlu: ...
2. ... — Sorumlu: ...
```

## 5. Sprint planlama (20 dk)

1. **Kapasite (2 dk):** Bu hafta kim var, kim yok? Eksik bir rol varsa öğretim üyesi
   o rolü üstlenir; geliştirici eksikse daha az iş alınır.
2. **Sprint hedefi (3 dk):** PO önerir, ekip netleştirir. Tek cümle.
3. **Hikâye seçimi (10 dk):** PO sırayla anlatır; ekip **puan verir** (planning poker)
   ve kapasiteye göre kaç hikâye alacağına karar verir.
4. **Görevlere bölme (5 dk):** Geliştiriciler ve testçi her hikâyeyi görevlere böler
   (ör. "servis fonksiyonu + birim testi", "sayfa", "E2E testi").
5. Taiga'da sprinti başlatın.

### Planning poker

1. PO hikâyeyi okur; sorular sorulur.
2. Herkes aynı anda puanını gösterir (1, 2, 3, 5, 8). Parmakla veya kartla.
3. En düşük ve en yüksek puanı veren nedenini açıklar.
4. Tekrar oylanır; uzlaşılan puanı **Back** geliştirici Taiga'ya girer.
5. 8'den büyükse hikâye bölünmelidir.

### Hız (velocity)

Önceki sprintlerde **Bitti** olan hikâyelerin puan toplamı ekibin hızıdır. Planlamada
"son 2–3 sprintin ortalaması kadar" iş almak gerçekçidir. İlk sprintlerde hız bilinmez;
az iş alın.

## 6. Scrum of Scrums (10 dk, tüm SM'ler + öğretim üyesi)

Her SM sırayla dört soruyu yanıtlar (en fazla 2 dk):

1. Ekibimiz geçen haftadan bu yana ne bitirdi?
2. Bu hafta ne yapacak?
3. **Başka bir ekibe ihtiyacımız var mı?** (ör. "team-events'in `get_event`'i lazım")
4. **Başka bir ekibi etkileyecek bir değişiklik yapacak mıyız?**
   (ör. `schema.sql`'e sütun ekleme, `base.html` değişikliği)

Kararları aynı gün **Discussions → Scrum of Scrums**'a yazın:

```text
## Scrum of Scrums — 2026-10-16
- team-tickets, team-events'ten get_event(event_id) bekliyor
  → Sprint 3 sonuna kadar (sorumlu: team-events)
- schema.sql'e events.category sütunu eklenecek
  → team-events PR açacak, SM'ler onaylayacak
- Ortak karar: Tarih alanları ISO formatında (YYYY-MM-DD) saklanacak
```

## 7. Taiga'da Scrum Master

| İş | Nerede? |
|---|---|
| Sprint oluşturma | Scrum → Backlog → **New sprint** (başlangıç/bitiş: uygulama dersi günleri) |
| Hikâyeleri sprinte alma | Backlog'dan sprint kutusuna sürükleyip bırakma |
| Sprint panosu | Sprint adına tıklayınca açılan **Taskboard** |
| Burndown | Taskboard'un üstündeki grafik |
| Sprint kapatma | Sprint bitince; bitmeyen hikâyeler backlog'a veya sonraki sprinte taşınır |

### Burndown nasıl okunur?

- **İdeal çizgi:** Sprintin başından sonuna düzgün azalan kalan iş.
- **Gerçek çizgi** ideal çizginin üstündeyse ekip geride.
- **Düz bir çizgi, sonra son gün sert düşüş:** İşler "Bitti"ye geç taşınıyor
  (genellikle PO kabulü gecikiyor). Retrospektifte konuşun.

### Pano hijyeni (her derste kontrol edin)

- [ ] Her "Yapılıyor" görevinin bir sahibi var mı?
- [ ] Bir haftadan uzun süredir aynı durumda bekleyen iş var mı?
- [ ] "İncelemede" hikâyelerin açık PR'ı var mı?
- [ ] "Testte" bekleyen hikâyeler testçinin ve PO'nun gündeminde mi?

## 8. Engellerle çalışmak

| Engel türü | Örnek | Ne yaparsınız? |
|---|---|---|
| Teknik | "Kurulum çalışmıyor" | Ekipten yardım bulun; çözülmezse Soru-Cevap'a yazdırın |
| Başka ekip | "team-events'in fonksiyonu hazır değil" | Scrum of Scrums; beklerken sahte veriyle (mock) çalışma önerin |
| Belirsiz gereksinim | "Kural ne diyor bilmiyoruz" | PO'ya; PO müşteriye |
| Ekip içi | "Bir üye hiç katkı vermiyor" | Önce birebir konuşun; sürerse retrospektif; yine sürerse öğretim üyesi |
| Süreç | "PR'lar 3 gündür incelenmiyor" | Ekip anlaşmasını hatırlatın; retrospektifte aksiyon |

Discussions günlüğünde **"engel var"** yazan herkese **24 saat içinde** yanıt verin.

## 9. Ortak kodun bekçisi

CODEOWNERS gereği `app/__init__.py`, `app/core/` (veritabanı şeması dahil),
`base.html` ve `app/static/` değişiklikleri **Scrum Master'ların onayını** gerektirir.
Bu PR'ları incelerken:

- [ ] Değişiklik Scrum of Scrums'ta konuşuldu mu?
- [ ] Diğer ekiplerin kodunu veya testlerini bozuyor mu? (CI'a bakın)
- [ ] `schema.sql` değişikliğinde: Tablo ve sütun adları kurallara uygun mu, sahibi
  yorumda yazıyor mu, arayüz sözleşmesi güncellendi mi?

**Sprint 1'de özel görev:** Dört ekip aynı hafta `app/__init__.py` ve `base.html`'e
satır ekleyecek. SM'ler PR'ları **sırayla** birleştirmeyi koordine eder; her birleştirmeden
sonra diğer ekiplere "main güncellendi, `git pull origin main` yapın" diye haber verir.

## 10. Bitti Tanımı'nın bekçisi

Sprint 1'de tüm sınıf **Hazır ve Bitti Tanımı**'nı birlikte yazar
(`docs/definition-of-ready-and-done.md`). Bu oturumu SM'ler yürütür. Sonrasında:

- Review'da "Bitti" denen her hikâye Bitti Tanımı'nı sağlıyor mu, kontrol edin.
- Sağlamıyorsa hikâye bitmemiştir; bu yüzleşmeyi yapmak sizin göreviniz.

## 11. Eksik üye ve devamsızlık

- Planlamanın başında kimin olmadığını kontrol edin.
- Eksik rolü öğretim üyesi üstlenir (karar, onay, inceleme, kabul testi); ona haber verin.
- Eksik geliştirici varsa sprinte **daha az iş** alın (kapasite planlaması).
- Gelmeyen kişinin yarım işi Taiga'daki notlardan devam ettirilir; not yoksa
  bunu retrospektifte konuşun.

## 12. Haftalık kontrol listesi

- [ ] Review, retrospektif ve planlama zamanında yapıldı
- [ ] Retrospektif notları ve en fazla 2 aksiyon Taiga Wiki'de
- [ ] Önceki retrospektif aksiyonları takip edildi
- [ ] Taiga'da yeni sprint açıldı, sprint hedefi yazıldı
- [ ] Scrum of Scrums kararları Discussions'ta
- [ ] Günlükteki engellere 24 saat içinde yanıt verildi
- [ ] Pano hijyeni kontrol edildi

## 13. Sık yapılan hatalar

- **Toplantıları uzatmak:** Zaman sınırı Scrum'ın parçasıdır. Süre bitince bitirin.
- **Retrospektifi atlamak:** "Vakit yok" denen retrospektif, en çok gereken retrospektiftir.
- **Herkesin işini yapmak:** Siz yaparsanız ekip öğrenmez.
- **Sorunları gizlemek:** Kötü burndown'ı saklamayın; görünür kılmak sizin işiniz.
- **Aksiyonsuz retrospektif:** Konuşup karar vermemek, retrospektif yapmamakla aynıdır.
