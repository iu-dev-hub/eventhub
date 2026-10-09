# Product Vision (Ürün Vizyonu): EventHub

**Müşteri:** EventHub Teknoloji (kurgusal girişim)

**Kimin için?**

- **Katılımcılar:** Etkinlikleri keşfetmek ve kolayca bilet almak isteyenler
- **Organizatörler:** Öğrenci kulüpleri, kurumlar ve şirketler; etkinliklerini
  yayınlamak, kontenjanı ve katılımı yönetmek isteyenler
- **Yöneticiler:** Platformu, salonları ve organizatörleri yöneten ekip

**Sorun ne?** Etkinlik kayıtları bugün çoğunlukla çevrim içi formlar, tablolar ve
mesajlaşma gruplarıyla yürütülüyor. Kontenjan aşılıyor, aynı kişi birden çok kez kayıt
oluyor, girişte liste kontrolü uzun kuyruklar oluşturuyor, iptal ve iadeler karmaşaya
dönüşüyor. Organizatörler, kaç kişinin gerçekten geldiğini bile bilmiyor.

**Ürün ne yapacak?**

- Organizatörler, tanımlı salonlarda etkinlik oluşturup yayınlayabilecek.
- Katılımcılar etkinlik arayıp bilet alabilecek; kontenjan dolunca bekleme listesine
  katılabilecek.
- Her bilet benzersiz bir QR koda sahip olacak; girişte QR kod okutulacak.
- Ücretli etkinliklerde indirimler, ödeme (simülasyon) ve iade kuralları uygulanacak.
- Organizatörler ve yöneticiler doluluk, satış ve katılım raporlarını görebilecek.

**Başarıyı nasıl ölçeceğiz?**

- **Hafta 8 — Yatırımcı demo günü (MVP):** Kayıt → giriş → etkinlik arama →
  bilet alma → QR ile giriş akışı uçtan uca çalışıyor.
- **Hafta 14 — Pilot (v1.0):** Tüm modüller, ödeme, iade ve raporlar dahil;
  bir üniversite kampüsünde pilot kullanıma hazır.
- Tüm iş kuralları otomatik testlerle doğrulanmış, CI yeşil.

**Kapsam dışı (bu dönem):** Mobil uygulama, gerçek ödeme altyapısı, e-posta veya SMS
gönderimi, koltuk numaralı salonlar, harita entegrasyonu.

**Uzun vadeli hedef:** EventHub'ın çekirdeği (etkinlik, salon, kontenjan, kayıt ve
giriş yönetimi) farklı kurumların ihtiyaçlarına uyarlanabilecek şekilde tasarlanmalı.
