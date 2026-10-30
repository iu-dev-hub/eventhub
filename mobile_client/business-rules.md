# İhtiyaç Dokümanı (Business Rules) — Sürüm 1.0

**EventHub**
Hazırlayan: EventHub Teknoloji, Ürün Ekibi (müşteri)

> Bu doküman, yeni platformdan ne beklediğimizi anlatır. Yazılımcı değiliz; bazı
> konuları eksik veya yeterince açık yazmamış olabiliriz.
> **Anlamadığınız veya eksik gördüğünüz her şeyi Product Owner'larınız aracılığıyla
> bize sorun.** Cevaplarımız bu dokümanın yeni sürümlerine eklenecektir.
> Kural kodları (ör. `BR-3.2`) testlerde ve kodda bu kurallara atıf yapmak için kullanılır.

## BR-1. Hesaplar (team-accounts)

- **BR-1.1** Platformu katılımcılar (`participant`), organizatörler (`organizer`) ve
  yöneticiler (`admin`) kullanır.
- **BR-1.2** Herkes e-posta adresiyle kayıt olur. Bir e-posta adresiyle yalnızca bir
  hesap açılabilir.
- **BR-1.3** Şifre 8–20 karakter olmalı, en az bir harf ve bir rakam içermelidir.
- **BR-1.4** Güvenlik için, art arda çok sayıda hatalı giriş denemesinde hesap geçici
  olarak kilitlenmelidir.
- **BR-1.5** Organizatör olarak kaydolan kullanıcılar, bir yönetici hesaplarını
  onaylayana kadar etkinlik oluşturamaz.
- **BR-1.6** Öğrenci olan katılımcılar öğrenci indiriminden (BR-4.2) yararlanabilir.

## BR-2. Etkinlikler ve salonlar (team-events)

- **BR-2.1** Salonları yalnızca yöneticiler tanımlar. Her salonun adı, adresi ve
  kapasitesi vardır.
- **BR-2.2** Her etkinliğin başlığı, kategorisi, salonu, başlangıç ve bitiş zamanı,
  kapasitesi ve bilet fiyatı vardır. Fiyatı 0 TL olan etkinlik ücretsizdir.
- **BR-2.3** Etkinlik kapasitesi, salonun kapasitesini aşamaz.
- **BR-2.4** Aynı salonda zamanı çakışan iki etkinlik olamaz.
- **BR-2.5** Etkinlikler, katılımcıların hazırlanabilmesi için yeterince önceden yayınlanmalıdır.
- **BR-2.6** Katılımcılar etkinlikleri başlık, kategori ve tarihe göre arayabilmelidir.
  Arama hızlı ve kullanımı kolay olmalıdır.
- **BR-2.7** Bileti satılmış bir etkinlik silinemez; yalnızca iptal edilebilir.

## BR-3. Bilet ve kontenjan (team-tickets)

- **BR-3.1** Bir kullanıcı bir etkinlik için en fazla **4** bilet alabilir.
- **BR-3.2** Kontenjan dolduğunda bilet satışı durur; kullanıcı bekleme listesine katılabilir.
- **BR-3.3** Bilet satışı, etkinlik başlangıcından **1 saat** önce kapanır.
- **BR-3.4** Biletini iptal eden kullanıcının yeri, bekleme listesindeki ilk kişiye teklif edilir.
- **BR-3.5** Ücretli etkinliklerde ayrılan bilet **15 dakika** içinde ödenmezse serbest bırakılır.
- **BR-3.6** Her biletin benzersiz bir QR kodu vardır. Girişte QR kod okutulur;
  bir bilet yalnızca **bir kez** kullanılabilir.
- **BR-3.7** Girişler, etkinlik başlangıcından **1 saat** önce açılır.

> **Ürün ekibinin notu:** Popüler etkinliklerde biletlerin toplanıp yüksek fiyata
> satılmasını önlemek için kimse bir etkinliğe 2'den fazla bilet alamamalıdır.

## BR-4. Ödeme, iade ve raporlar (team-payments)

- **BR-4.1** **Erken kayıt indirimi:** Etkinliğe 14 gün veya daha fazla varken alınan
  biletlerde %20 indirim uygulanır.
- **BR-4.2** **Öğrenci indirimi:** Öğrencilere %25 indirim uygulanır.
- **BR-4.3** Ödeme simüle edilir. Kart numarası 16 haneli olmalıdır; `0000` ile biten
  kart numaraları "bakiye yetersiz" nedeniyle reddedilir (test kartı).
- **BR-4.4** **İade:** Etkinliğe 7 gün veya daha fazla varken yapılan iptallerde tam iade,
  2–6 gün kala %50 iade yapılır; 48 saatten az kala iade yapılmaz.
- **BR-4.5** Organizatör etkinliği iptal ederse tüm biletler için tam iade yapılır.
- **BR-4.6** Ücretsiz etkinliklerde ödeme adımı yoktur.
- **BR-4.7** Organizatörler kendi etkinliklerinin, yöneticiler tüm etkinliklerin
  raporlarını görebilmelidir.

## Durumlar

**Etkinlik (`events.status`)**

| Kodda | Arayüzde |
|---|---|
| `draft` | Taslak |
| `published` | Yayında |
| `sales_closed` | Satışa kapalı |
| `completed` | Tamamlandı |
| `cancelled` | İptal edildi |

**Bilet (`tickets.status`)**

| Kodda | Arayüzde |
|---|---|
| `reserved` | Ayrıldı (ödeme bekleniyor) |
| `paid` | Geçerli |
| `used` | Kullanıldı |
| `refunded` | İade edildi |
| `cancelled` | İptal edildi |

## Kapsam dışı (bu dönem)

Mobil uygulama, gerçek ödeme altyapısı, e-posta veya SMS gönderimi, koltuk numaralı
salonlar, harita entegrasyonu. Bildirimler yalnızca platform içinde gösterilir.

## Değişiklik geçmişi

| Sürüm | Tarih | Değişiklik | Kaynak |
|---|---|---|---|
| 1.0 | | İlk sürüm | Müşteri açılış toplantısı |
