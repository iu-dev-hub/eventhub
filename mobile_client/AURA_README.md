# 🎭 AURA Events - Kültür & Sahne Sanatları Mobil Platformu

> **Modern, akıcı ve yormayan Android etkinlik ve biletleme deneyimi.**  
> Flet (Flutter Python) mobil istemcisi ve EventHub Flask REST API mimarisi üzerine inşa edilmiştir.

---

## 📌 İçindekiler
1. [Proje Hakkında](#-proje-hakkında)
2. [Tasarım İlkeleri ve Kullanıcı Deneyimi](#-tasarım-ilkeleri-ve-kullanıcı-deneyimi)
3. [Dizin ve Mimari Yapı](#-dizin-ve-mimari-yapı)
4. [Kurulum ve Gereksinimler](#-kurulum-ve-gereksinimler)
5. [Uygulamayı Çalıştırma (Kullanım Rehberi)](#-uygulamayı-çalıştırma-kullanım-rehberi)
6. [Ayrı Yönetici (Admin) Paneli & Canlı API İstasyonu](#-ayrı-yönetici-admin-paneli--canlı-api-istasyonu)
7. [Bilet Satın Alma ve Koltuk Seçim Akışı](#-bilet-satın-alma-ve-koltuk-seçim-akışı)
8. [Arka Uç (EventHub API) Entegrasyonu](#-arka-uç-eventhub-api-entegrasyonu)
9. [Testler ve Kod Kalitesi](#-testler-ve-kod-kalitesi)

---

## 🌟 Proje Hakkında

**AURA Events**, futbol veya karmaşık spor portalları (Passo vb.) yerine yalnızca **tiyatro, konser, bale, opera, stand-up ve seminer** gibi seçkin kültür-sanat etkinliklerine odaklanan bağımsız bir mobil biletleme platformudur.

Kullanıcıyı yormayan, göz alıcı koyu tema (Dark Glassmorphism), oval hatlar, interaktif koltuk seçim krokisi ve anında oluşturulan güvenlikli QR biletleme altyapısıyla donatılmıştır.

---

## 🎨 Tasarım İlkeleri ve Kullanıcı Deneyimi

- **Yumuşak ve Ergonomik Geometri:** Köşeli, sert ve hantal kutular yerine `border_radius=20-28px` arası akıcı oval kartlar ve butonlar kullanılmıştır.
- **Canlı Android Deneyimi:** Saat, pil ve Wi-Fi simgeleri içeren simüle Android durum çubuğu ve modern Android jest çubuğu (Home Indicator).
- **Kültür Odaklı Renk Paleti:** Gece laciverti (`#0B0E14`), derin arduvaz (`#161B26`), canlı menekşe (`#8B5CF6`) ve enerji veren fildişi/amber vurguları.
- **Mikro Animasyonlar ve Geri Bildirim:** Tıklama efektleri, akıcı sayfa geçişleri ve gerçek zamanlı koltuk seçim tepkileri.

---

## 📂 Dizin ve Mimari Yapı

Proje, **Feature-first / MVVM** prensipleriyle modüler olarak yapılandırılmıştır:

```text
yzsMobil/
├── main.py                     # Kök başlatıcı (Mobil İstemci)
├── run_android.sh              # Hızlı çalıştırma ve ağ yayınlama betiği
├── src/
│   ├── main.py                 # Flet uygulama rotaları ve pencere yöneticisi
│   ├── core/                   # Tema (Theme), renk paletleri ve sabitler
│   ├── components/             # Yeniden kullanılabilir parçalar (EventCard, SeatMatrix vb.)
│   ├── views/                  # Sayfa görünümleri
│   │   ├── home/               # Ana sayfa vitrini, arama ve filtreler
│   │   ├── event_detail/       # Etkinlik tanıtımı, seans ve fiyat bilgisi
│   │   ├── seat_selection/     # İnteraktif tribün/koltuk matrisi
│   │   ├── checkout/           # Ödeme ve bilet onay özeti
│   │   ├── profile/            # Kullanıcı biletleri ve dijital QR kodlar
│   │   └── admin/              # AYRI Yönetici Paneli & API Yönetim İstasyonu
│   ├── services/               # API, Kimlik Doğrulama ve QR üretim servisleri
│   └── models/                 # Veri modelleri (Event, Seat, Ticket vb.)
└── eventhub/                   # Flask REST API Arka Uç Sistemi
    ├── app/api/                # Mobil JSON uç noktaları (/api/events)
    ├── tests/                  # Entegrasyon ve birim testleri
    └── docs/                   # Arayüz sözleşmeleri (interface-contract.md)
```

---

## ⚙️ Kurulum ve Gereksinimler

Proje Conda sanal ortamı veya Python 3.12+ ile çalıştırılabilir:

```bash
# Gerekli kütüphaneleri içeren conda ortamını etkinleştirin
conda activate flet
# veya
conda activate /home/berkyilmaz/anaconda3/envs/flet
```

Gerekli Python paketleri:
- `flet`
- `qrcode`
- `requests`
- `flask` (arka uç için)
- `pytest` & `ruff` (testler ve linting için)

---

## 🚀 Uygulamayı Çalıştırma (Kullanım Rehberi)

Proje kök dizininde yer alan `run_android.sh` betiği ile tüm modlar tek komutla başlatılabilir:

### 1. Kullanıcı Mobil Uygulamasını Başlatma (Masaüstü Android Formu)
Kullanıcıların etkinlikleri inceleyebileceği, koltuk seçip bilet alabildiği ana mobil arayüz:
```bash
./run_android.sh
# veya
python main.py
```

### 2. Canlı Ağ Yayını (Android Telefonda veya Tarayıcıda Açma)
Uygulamayı yerel ağınızdaki herhangi bir Android cihazdan veya tarayıcıdan test etmek için:
```bash
./run_android.sh live
```
- Konsolda gösterilen adresi (Örn: `http://192.168.1.XX:8550` veya `http://localhost:8550`) telefonunuzun tarayıcısında açarak gerçek dokunmatik deneyimi test edebilirsiniz.

---

## 🛡️ Ayrı Yönetici (Admin) Paneli & Canlı API İstasyonu

> **Kritik Güvenlik İlkesi:** Mobil kullanıcı uygulamasında kafa karışıklığı yaratmamak ve güvenlik açığı oluşturmamak için API açma/kapama butonları, simülasyon anahtarları ve sunucu iletişim logları **son kullanıcı arayüzünden tamamen yalıtılmış ve ayrı bir Yönetici Paneline taşınmıştır.**

### Yönetici Panelini Başlatma:
```bash
./run_android.sh admin
# veya
python src/main.py --admin
```

### Yönetici Paneli Özellikleri:
- **Canlı REST API Entegrasyon Anahtarı:** İstediğiniz an tek tıkla canlı Flask sunucusu ile bağlantıyı açabilir ya da çevrimdışı önbellek moduna geçebilirsiniz.
- **Manuel Veri Eşitleme (Sync Button):** Backend'den anlık olarak yeni eklenen etkinlikleri çeker.
- **Sistem İletişim Konsolu (Logs):** Yapılan HTTP GET isteklerini, durum kodlarını ve gecikme sürelerini anlık izleme.
- **Etkinlik Yönetimi:** Yeni tiyatro/konser ekleme, kapasite ve fiyat düzenleme.

---

## 🎟️ Bilet Satın Alma ve Koltuk Seçim Akışı

1. **Etkinlik Keşfi:** Ana sayfadaki zengin kategorilerden (Tiyatro, Klasik Müzik, Bale, Caz) bir etkinlik seçin.
2. **Detay İnceleme:** Sahne bilgileri, sanatçı kadrosu ve seans takvimini görüntüleyin.
3. **Koltuk Matrisi (Seat Matrix):**
   - 🟣 **VIP Sahne Önü** (Özel konfor alanı)
   - 🔵 **Ön Sıralar / Kategori 1**
   - ⚪ **Standart Salon Koltukları**
   - 🔴 **Dolu / Satılmış Koltuklar** (Tıklanamaz)
4. **Biletlerim & QR Kod:** Satın alma tamamlandığında bilet anında **Profilim > Biletlerim** sekmesine eklenir. Kapı girişinde salon görevlisine gösterilecek yüksek çözünürlüklü dinamik QR kod otomatik üretilir.

---

## 🌐 Arka Uç (EventHub API) Entegrasyonu

Mobil uygulama, `/home/berkyilmaz/Projects/yzsMobil/eventhub` dizinindeki Flask servisi ile konuşur.

### Arka Uç Sunucusunu Başlatma:
```bash
cd eventhub
flask --app app run --port 5000
```

### Temel Uç Nokta (`GET /api/events`):
- **Sözleşme Kuralı:** Yalnızca `published` durumundaki etkinlikleri listeler.
- **Yuvarlama Koruması:** Fiyatlar float yerine iki ondalıklı metin (`"0.00"`, `"150.00"`) olarak döndürülür.
- **Tarihler:** Standart ISO 8601 biçimindedir.
- Detaylı API şeması için: [`eventhub/docs/interface-contract.md`](file:///home/berkyilmaz/Projects/yzsMobil/eventhub/docs/interface-contract.md)

---

## 🧪 Testler ve Kod Kalitesi

API ve mobil iş kuralları için entegrasyon testlerini çalıştırmak için:

```bash
cd eventhub

# Entegrasyon testleri (Flask test client)
pytest tests/integration/test_api.py -v

# Kod stili ve linting kontrolleri
ruff check app/api tests/integration/test_api.py app/__init__.py
```

---

## 👥 Geliştirici ve İletişim

- **Takım:** team-mobile & team-events (EventHub Projesi)
- **Lisans:** Eğitim ve Yazılım Sınama/Doğrulama Dersi Projesi kapsamında geliştirilmiştir.
