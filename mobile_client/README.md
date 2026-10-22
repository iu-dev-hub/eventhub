# mobile_client — EventHub Android uygulaması (Flet)

**Sahip:** team-mobile (CODEOWNERS) · **Epic:** Mobil Uygulama

Bu klasör Flask uygulamasının parçası **değildir**. Uygulama sunucuyla yalnızca
`/api/...` uç noktaları üzerinden, JSON ile konuşur.

## Kurulum ve çalıştırma

Projenin mevcut sanal ortamını kullanabilirsiniz:

```bash
pip install -r mobile_client/requirements.txt
flet run mobile_client/main.py
```

Flet, aynı arayüzü bilgisayarda bir masaüstü penceresinde açar. Günlük geliştirme
ve demolar bu şekilde yapılabilir; APK yalnızca kilometre taşlarında derlenir.

> `flet` paketi ana `requirements.txt` dosyasına **eklenmez**. Eklenirse sınıftaki
> herkesin kurulumu ve CI uzar.

## Hedef klasör yapısı

```text
mobile_client/
  main.py            # Flet ekranları: ince tutulur, iş mantığı içermez
  <istemci paketi>/  # API çağrıları ve veri dönüşümü: flet İÇE AKTARILMAZ
  requirements.txt
tests/unit/test_mobile_client.py   # istemci mantığının testleri (CI'da çalışır)
```

**Test edilebilirlik kuralı:** İstemcinin mantığı (`/api` çağrıları, JSON'u ekran
verisine çevirme, hata mesajları) `flet`'i hiç içe aktarmayan modüllerde yazılır.
Böylece testleri `flet` kurulmadan, mevcut CI'da çalışır. Flet ekranları elle ve
keşif testiyle test edilir.

## Sunucuya bağlanma

- Telefon ve bilgisayar aynı ağda olmalıdır. Kampüs Wi-Fi'ı cihazların birbirini
  görmesini engelleyebilir; telefonun kişisel erişim noktası genellikle çalışır.
- Sunucuyu ağa açmak için: `flask --app app run --host 0.0.0.0 --port 5000`
  **Asla `--debug` ile çalıştırmayın**: debug modu ağdaki herkese sunucuda kod
  çalıştırma imkânı verir.
- Android şifresiz HTTP'yi varsayılan olarak engeller. Geliştirme için Flet
  yapılandırmasında `android:usesCleartextTraffic="true"` gerekir; nedenini PR'da
  açıklayın.

## APK derleme

Ayrıntılar: [Flet: Android](https://docs.flet.dev/publish/android)

- Java (JDK 17) ve Android SDK gerekir; Flutter SDK ilk derlemede otomatik iner.
- İlk derleme uzun sürer ve diskte ciddi yer kaplar; kurulum süresini spike
  notuna yazın.
- Derleme çıktısı (`build/`, `.apk`, `.aab`) depoya **eklenmez** (`.gitignore`).

## Bağlantılar

- Spike hikâyesi ve karar kaydı: `docs/decisions/0001-mobile-client.md`
- API kuralları: `app/api/README.md`
