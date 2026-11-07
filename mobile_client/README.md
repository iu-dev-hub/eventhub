# mobile_client — EventHub Android Uygulaması (AURA Events - Flet)

**Sahip:** team-mobile (CODEOWNERS) · **Epic:** Mobil Uygulama

Bu klasör Flask uygulamasının parçası **değildir**. Flet ile geliştirilen modern Android mobil biletleme ve etkinlik keşif istemcisini barındırır. Uygulama sunucuyla yalnızca `/api/...` uç noktaları üzerinden, standart JSON ile konuşur.

---

## 🌟 Tasarım Felsefesi ve Özellikler

**AURA Events**, futbol veya karmaşık spor portalları (Passo vb.) yerine yalnızca **tiyatro, konser, bale, opera, stand-up ve seminer** gibi seçkin kültür-sanat etkinliklerine odaklanır:

- **Ergonomik & Oval Geometri:** Köşeli ve sert kutular yerine `border_radius=20-28px` arası akıcı oval kartlar ve butonlar kullanılmıştır.
- **Canlı Android Deneyimi:** Saat, pil ve Wi-Fi simgeleri içeren simüle Android durum çubuğu ve modern Android jest çubuğu (Home Indicator).
- **Kültür Odaklı Renk Paleti:** Gece laciverti (`#0B0E14`), derin arduvaz (`#161B26`), canlı menekşe (`#8B5CF6`) ve enerji veren fildişi/amber vurguları.
- **İnteraktif Koltuk Krokisi (Seat Matrix):** Sahne önü VIP, 1. Kategori ve standart koltuk bloklarından seçim yapma.
- **Dinamik Dijital Bilet & QR Kod:** Satın alınan etkinlik biletleri anında cüzdana eklenir ve kapı girişi için yüksek çözünürlüklü dinamik QR kod oluşturulur.
- **AYRI Yönetici (Admin) Paneli:** API açma/kapama, canlı/çevrimdışı simülasyon anahtarı ve sunucu logları son kullanıcı arayüzünden tamamen ayrı bir yönetim paneline taşınmıştır.

---

## 📂 Klasör ve Mimari Yapı

Proje, **Feature-first / MVVM** prensipleriyle modüler olarak yapılandırılmıştır:

```text
mobile_client/
├── main.py                     # Kök başlatıcı (Flet giriş noktası)
├── run_android.sh              # Hızlı çalıştırma, canlı yayın ve APK derleme betiği
├── requirements.txt            # Mobil istemci bağımlılıkları (Ana repoya eklenmez!)
├── business-rules.md           # İş kuralları ve mobil limitler
├── features.md                 # Ekranlar ve özellik listesi
├── rules.md                    # Kodlama ve mimari standartlar
└── src/
    ├── main.py                 # Flet uygulama rotaları ve pencere yöneticisi
    ├── core/                   # Tema (Theme), renk paletleri ve sabitler
    ├── components/             # Yeniden kullanılabilir parçalar (EventCard, SeatMatrix, TopBar vb.)
    ├── views/                  # Sayfa görünümleri
    │   ├── home/               # Ana sayfa vitrini, arama ve filtreler
    │   ├── event_detail/       # Etkinlik tanıtımı, seans ve fiyat bilgisi
    │   ├── seat_selection/     # İnteraktif tribün/koltuk matrisi
    │   ├── checkout/           # Ödeme ve bilet onay özeti
    │   ├── profile/            # Kullanıcı biletleri ve dijital QR kodlar
    │   └── admin/              # AYRI Yönetici Paneli & Canlı API İstasyonu
    ├── services/               # API, Kimlik Doğrulama ve QR üretim servisleri
    └── models/                 # Veri modelleri (Event, Seat, Ticket vb.)
```

---

## ⚙️ Kurulum ve Çalıştırma

Projenin Conda ortamını (`flet`) veya mevcut Python 3.12+ sanal ortamını kullanabilirsiniz:

```bash
# Bağımlılıkları yükleme (ana requirements.txt dosyasına eklenmez!)
pip install -r mobile_client/requirements.txt
```

### 1. Kullanıcı Mobil Uygulamasını Başlatma (Masaüstü Android Formu)
```bash
./mobile_client/run_android.sh
# veya
flet run mobile_client/main.py
```

### 2. Ayrı Yönetici Paneli & API Kontrol Merkezi
```bash
./mobile_client/run_android.sh admin
# veya
python mobile_client/src/main.py --admin
```

### 3. Canlı Ağ Yayını (Android Telefonda veya Tarayıcıda Açma)
```bash
./mobile_client/run_android.sh live
# veya
flet run --port 8550 --host 0.0.0.0 --web mobile_client/main.py
```
Telefonunuzdan `http://<BILGISAYAR_YEREL_IP>:8550` adresine girerek test edebilirsiniz.

---

## 🌐 Sunucuya Bağlanma ve API Kuralları

- Telefon ve bilgisayar aynı ağda olmalıdır.
- Sunucuyu ağa açmak için:
  ```bash
  flask --app app run --host 0.0.0.0 --port 5000
  ```
  *(Asla `--debug` ile çalıştırmayın: debug modu ağdaki herkese sunucuda kod çalıştırma imkânı verir).*
- Android şifresiz HTTP'yi varsayılan olarak engeller. Geliştirme için Flet yapılandırmasında `android:usesCleartextTraffic="true"` gerekir.
- API kuralları ve veri sözleşmesi: `docs/interface-contract.md` ve `app/api/README.md`.

---

## 📦 APK Derleme

Ayrıntılar: [Flet: Android](https://docs.flet.dev/publish/android)

```bash
./mobile_client/run_android.sh apk
# veya
flet build apk --project "AURA" --org "com.aura.events"
```
- Java (JDK 17) ve Android SDK gerekir; Flutter SDK ilk derlemede otomatik iner.
- Derleme çıktısı (`build/`, `.apk`, `.aab`) depoya **eklenmez** (`.gitignore`).
