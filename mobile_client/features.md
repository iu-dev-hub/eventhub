---


```markdown
# Özellik ve Kapsam Dokümanı (FEATURES.md)
## Etkinlik Keşif & Biletleme Platformu

Bu belge, Flet ile geliştirilen etkinlik keşif ve biletleme uygulamasının modüllerini, teknik gereksinimlerini, MVP (Minimum Viable Product) ve gelecek faz özelliklerini tanımlar.

---

## 1. Modül Özeti ve Öncelik Matrisi

| Modül Adı | Kapsam | MVP Durumu | Öncelik |
|---|---|---|---|
| **Kimlik & Profil (Auth)** | Giriş, kayıt, SMS OTP simülasyonu, profil | Faz 1 | Yüksek |
| **Keşfet & Arama (Discovery)** | Kategori filtreleri, arama, popüler bannerlar | Faz 1 | Yüksek |
| **Etkinlik Detay (Detail)** | Mekan, tarih/saat, fiyatlandırma, kurallar | Faz 1 | Yüksek |
| **Koltuk & Kategori Seçimi (Seating)** | Kademeli blok seçimi, koltuk matrisi, kilit mekanizması | Faz 1 | Kritik |
| **Ödeme & Sepet (Checkout)** | Sepet geri sayımı, kart formu, sipariş onayı | Faz 1 | Kritik |
| **Bilet Cüzdanı (Wallet/Tickets)** | Satın alınan biletler, dinamik QR kod, detaylar | Faz 1 | Kritik |
| **Bilet Transferi (Transfer)** | Başka bir kullanıcıya bilet devretme | Faz 2 | Orta |
| **Favoriler & Bildirimler** | Takip edilen takımlar/sanatçılar, hatırlatmalar | Faz 2 | Düşük |

---

## 2. Detaylı Özellik Listesi

### A. Kimlik ve Üyelik Yönetimi (`views/auth`)
- **E-posta veya Telefon ile Kayıt & Giriş:**
  - Ad, soyad, e-posta, telefon numarası ve şifre ile doğrudan hesap oluşturma.
  - Kayıtlı e-posta/telefon ve şifre ile doğrudan giriş yapabilme.
  - "Şifremi Unuttum" bağlantısı ve yeni şifre belirleme ekranı.
- **Profil Bilgileri:**
  - Kullanıcı iletişim bilgileri (ad, soyad, telefon, e-posta).
  - Kayıtlı fatura ve teslimat adresi yönetimi.
  - İlgi alanları, tutulan takım ve favori etkinlik türleri seçimi.

---

### B. Keşfet ve Etkinlik Listeleme (`views/home`)
- **Dinamik Öne Çıkanlar (Hero Slider):**
  - Yaklaşan büyük müsabakalar, konserler ve festivaller için yatay kaydırılabilir görsel banner alanı.
- **Kategori Filtreleme Çipleri:**
  - *Tümü, Futbol, Basketbol, Konser, Tiyatro, Stand-Up, Festival*.
- **Etkinlik Kartı (`EventCard`):**
  - Etkinlik görseli, başlık, mekan/şehir, tarih-saat ve "X TL'den başlayan fiyatlarla" etiketi.
- **Arama ve Hızlı Filtre:**
  - Etkinlik adı, sanatçı veya stadyum/salon adına göre anlık filtreleme.

---

### C. Etkinlik Detay Ekranı (`views/event_detail`)
- **Etkinlik Bilgi Başlığı:**
  - Etkinlik posteri, geri sayım sayacı ve mekan harita bilgisi.
- **Bilet Satış Kuralları:**
  - Yaş sınırı (+18 vb.), e-bilet kullanım koşulları ve kapı açılış saati uyarısı.
- **Kategori / Fiyat Listesi:**
  - Tribün/kategori bazında fiyat tablosu ve kalan bilet durumu rozeti (*Tükendi*, *Son 10 Bilet*, *Satışta*).
- **"Bilet Al" Eylemi:**
  - Kullanıcıyı doğrudan koltuk krokisine veya ayakta kategori seçim ekranına yönlendirme.

---

### D. İnteraktif Koltuk Seçim Krokisi (`views/seat_selection`)
- **Kademeli Yükleme (2 Aşamalı Mimari):**
  1. **Aşama 1 (Blok Seçimi):** Stadyum/salon genel görünümü üzerinden tribün seçimi (Örn: *Kuzey Tribünü - Blok 104*).
  2. **Aşama 2 (Koltuk Matrisi):** Seçilen bloğun satır ve sütun bazlı koltuk grid'i (Örn: *Sıra 4, Koltuk 12*).
- **Durum Gösterimi:**
  - **Boş:** Tıklanabilir, fiyat rozetini gösterir.
  - **Seçili:** Kullanıcının o anda sepetine eklediği koltuklar (Maksimum 4 bilet sınırı).
  - **Dolu:** Satılmış, tıklanamaz nötr durum.
- **Geçici Rezervasyon Sayacı (Cart Timer):**
  - Koltuk seçildiği anda 10 dakikalık geri sayım başlar. Süre bitiminde koltuk otomatik serbest bırakılır.

---

### E. Sepet ve Ödeme Simülasyonu (`views/checkout`)
- **Bilet Özeti:**
  - Etkinlik adı, seçilen blok/sıra/koltuk numaraları ve hizmet bedeli dökümü.
- **Geri Sayım Rozeti:**
  - Kalan rezervasyon süresini gösteren canlı sayaç barı.
- **Ödeme Yöntemi:**
  - Kredi/Banka kartı giriş formu (Luhn algoritması kontrolü, CVC, son kullanma tarihi maskesi).
  - 3D Secure simülasyon diyaloğu.
- **Sipariş Onay Ekranı:**
  - Başarılı sipariş kodu (PNR) ve "Biletlerime Git" yönlendirme butonu.

---

### F. Bilet Cüzdanı ve Turnike QR Ekranı (`views/profile`)
- **Aktif Biletler Listesi:**
  - Henüz tarihi geçmemiş biletlerin kart görünümü.
- **Tam Ekran Turnike Modu:**
  - Bilet seçildiğinde açılan ve kapıda okutulacak yüksek kontrastlı, beyaz zeminli dinamik QR kod.
  - Turnike girişinde barkodun kopyalanmasını önlemek için 30 saniyede bir kendini tazeleyen dinamik token yapısı.
- **Geçmiş Etkinlikler:**
  - Kullanılmış veya tarihi geçmiş biletlerin arşiv listesi.

---

## 3. Gelecek Fazlar (Roadmap)

### Faz 2 (Sonraki Güncellemeler)
- **Bilet Transferi:** Kullanıcının biletini başka bir T.C. Kimlik / Telefon numarasına devretmesi.
- **Kombine Yönetimi:** Sezonluk kombine sahipleri için "Müsabakaya Gelemeyeceğim, Koltuğumu Kulübe Devret" özelliği.
- **PDF Bilet İndirme:** QR kodlu resmi bilet belgesinin PDF olarak yerel diske kaydedilmesi.

### Faz 3 (Gelişmiş Entegrasyonlar)
- Gerçek SMS sağlayıcı (Netgsm, Twilio vb.) entegrasyonu.
- Gerçek sanal POS (Iyzico, PayTR vb.) iframe/webview ödeme akışı.
- Push bildirimleri (Müsabaka/etkinlik saati yaklaştığında veya biletler satışa çıktığında bildirim).