# Testçi (QA / Test Engineer) Rehberi

**Ürün kalitesine dair bilgiyi üreten ve görünür kılan kişi**

## 1. Rolün özü

Testçi, ürünün kalitesi hakkında **güvenilir bilgi üretir**: Ne çalışıyor, ne
çalışmıyor, risk nerede? Scrum açısından Back ve Front ile birlikte **Developers**
sorumluluğunu taşırsınız. ISTQB'nin "bütün ekip yaklaşımı"na göre kalite tüm ekibin
sorumluluğudur; siz bu sorumluluğun **uzmanı ve savunucususunuz**.

**Sorumluluklarınız:**

- Hikâyelerin kabul kriterlerinin **test edilebilir** olmasını sağlamak
- Sprint için **test yaklaşımını** belirlemek
- Test tasarım teknikleriyle **test durumları** tasarlamak
- **Playwright** ile uçtan uca (E2E) testler yazmak ve **regresyon paketini** korumak
- **Keşif testi** (exploratory testing) yapmak
- Hataları **raporlamak** ve takip etmek
- CI kalite kapısını izlemek; sprint sonunda **test özeti** hazırlamak
- `tests/e2e/` değişikliklerini onaylamak (CODEOWNERS: `qa` takımı)

**Ne değilsiniz?** Ekibin "hata avcısı" veya "son kontrol noktası" değilsiniz.
Geliştiriciler kendi birim testlerini yazar; siz test **stratejisinden** ve
**kullanıcı gözünden** doğrulamadan sorumlusunuz.

## 2. Haftalık ritim

| Ne zaman? | Ne yaparsınız? |
|---|---|
| Backlog iyileştirme | Kabul kriterlerini sorgularsınız: "Sınır nerede? Hata durumunda ne olur?" |
| Sprint planlama | Her hikâyeye test görevleri eklersiniz, puana test yükünü katarsınız |
| Sprint başı | Test durumlarını tasarlarsınız (kod yazılırken!) |
| Geliştirme sırasında | E2E testlerini hazırlarsınız; birleşen işleri test edersiniz |
| PR'lar | Geliştiricilerin testlerine bakarsınız; `tests/e2e/` PR'larını onaylarsınız |
| Sprint sonu | Test özeti, açık hatalar, review'da sunum |

> **Shift-left:** Testi en sona bırakmayın. Kabul kriterleri yazılırken başlayan test,
> en ucuz testtir.

## 3. Backlog iyileştirmede testçi: "Üç Amigo"

PO (ne istiyoruz?), geliştirici (nasıl yaparız?) ve testçi (nasıl doğrularız?)
hikâyeyi birlikte inceler. Sizin sorularınız:

- "Bu kriter nasıl **ölçülür**?" ("hızlı" → "kaç saniye?")
- "**Sınır** nerede?" (son boş yer mi, dolu kontenjan mı? 60. dakika mı, 59. dakika mı?)
- "**Hata** durumunda kullanıcı ne görür? Mesaj metni tam olarak ne?"
- "Hangi **rollerle** denemeliyiz?" (katılımcı, organizatör, yönetici)
- "Başka bir modüle **bağımlı** mı? Test verisi nereden gelecek?"

Cevapları kabul kriteri olarak hikâyeye eklemesi için PO'ya iletin.

## 4. Test yaklaşımı: Hangi seviyede test?

| Seviye | Kim yazar? | Araç | Ne için? |
|---|---|---|---|
| **Birim** | Back (ve Front) | pytest | İş kuralları, hesaplamalar, sınırlar |
| **Entegrasyon** | Back | pytest + Flask test istemcisi | Sayfalar, modüller arası çağrılar, veritabanı |
| **Uçtan uca (E2E)** | **Testçi** | Playwright | Kullanıcı akışları, kabul kriterleri |
| **Keşif** | **Testçi** (ve herkes) | Elle | Beklenmeyen hatalar, kullanılabilirlik |

**Test piramidi:** Çok sayıda hızlı birim testi, daha az entegrasyon testi, **en az**
sayıda ama **en kritik akışları** kapsayan E2E testi. Her sınır değerini E2E ile test
etmeyin; o iş birim testinin. E2E, akışın uçtan uca çalıştığını gösterir.

Her hikâye için kısa bir test yaklaşımı yazın (Taiga'da hikâye yorumu):

```text
Test yaklaşımı (#42 Katılımcı bilet alır):
- Birim (Back): BR-3.2 kontenjan sınırları (kapasite 100: satılan 98/99/100),
  BR-3.3 satış kapanışı (başlangıca 61/60/59 dakika)
- Entegrasyon (Back): Dolu etkinlikte "Kontenjan dolu." mesajı dönüyor
- E2E (ben): Mutlu yol + kontenjan dolu mesajı (2 test)
- Keşif: Son boş yeri iki sekmeden aynı anda alma denemesi
```

## 5. Test tasarım teknikleri

Teknikleri teori derslerinde ayrıntılı öğreneceksiniz (CTFL Bölüm 4). Projede nerede
kullanılacakları:

| Teknik | Hafta | Projede örnek |
|---|---|---|
| **Denklik sınıfı bölümleme** | 6 | Roller: katılımcı / organizatör / yönetici; etkinlik: ücretli / ücretsiz; kart: geçerli / `0000` ile biten / 16 haneli olmayan |
| **Sınır değer analizi** | 6 | Kapasite (salon 100: 99/100/101), satış kapanışı (61/60/59 dk), şifre uzunluğu (7/8, 20/21) |
| **Karar tablosu** | 7 | "Bilet alabilir mi?": etkinlik yayında mı × kontenjan dolu mu × satış açık mı × giriş yapılmış mı |
| **Durum geçişi** | 7 | Bilet: ayrıldı → geçerli → kullanıldı; etkinlik: taslak → yayında → satışa kapalı → tamamlandı |
| **Hata tahmini** | 9 | Boş arama, Türkçe karakterler ("ISIK" / "Işık"), çift tıklama |
| **Keşif testi** | 9 | Zaman sınırlı, amaçlı serbest test |

### Test durumu şablonu

Test durumlarını Taiga'da hikâyenin altına **görev** olarak veya hikâye yorumunda
tablo olarak yazın:

| ID | Teknik | Ön koşul | Adımlar | Beklenen sonuç | BR |
|---|---|---|---|---|---|
| TC-42-01 | Sınır | Kapasite 100, 99 bilet satılmış | Bilet al | Başarılı, bilet QR koduyla oluşur | BR-3.2 |
| TC-42-02 | Sınır | Kapasite 100, 100 bilet satılmış | Bilet almayı dene | "Kontenjan dolu." ve bekleme listesi düğmesi | BR-3.2 |
| TC-42-03 | Sınır | Başlamasına 59 dk kalmış etkinlik | Bilet almayı dene | "Bilet satışı kapanmıştır." | BR-3.3 |

## 6. Playwright ile E2E testleri

### Temel kurallar

```python
# tests/e2e/test_tickets.py
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def test_full_event_shows_capacity_message(page: Page, full_event):
    """TC-42-02 · BR-3.2: Kontenjanı dolu etkinlikte bilet alınamaz."""
    # full_event: kapasitesi dolmuş bir etkinlik oluşturan yardımcı fixture (ekibinizin)
    page.goto(f"/events/{full_event['id']}")
    page.get_by_role("button", name="Bilet Al").click()
    expect(page.get_by_role("alert")).to_have_text("Kontenjan dolu.")
    expect(page.get_by_role("button", name="Bekleme listesine katıl")).to_be_visible()
```

| Kural | Neden? |
|---|---|
| Elemanları **kullanıcı gibi** bulun: `get_by_role`, `get_by_label`, `get_by_text` | Tasarım değişince test kırılmaz; erişilebilirliği de dolaylı test eder |
| CSS sınıfı veya XPath **kullanmayın** | Kırılgan testler |
| `time.sleep` **kullanmayın**; `expect(...)` kullanın | Playwright otomatik bekler; sleep yavaş ve kararsızdır |
| Her test **bağımsız** olsun | Sıra değişince veya tek başına çalışınca da geçmeli |
| Test adı **ne test ettiğini** söylesin, docstring'de **TC ve BR** olsun | İzlenebilirlik: hikâye → test durumu → otomatik test |
| Her testte **net bir doğrulama** (`expect`) olsun | "Sayfa açıldı" test değildir |

### Çalıştırma ve hata ayıklama

```bash
pytest tests/e2e                         # hepsi
pytest tests/e2e -k capacity             # adında "capacity" geçenler
pytest tests/e2e --headed --slowmo 500   # tarayıcıyı görerek
pytest tests/e2e --tracing=on            # iz kaydı; sonra:
python -m playwright show-trace test-results/<klasör>/trace.zip
```

CI'da başarısız olan E2E testlerinin izleri, GitHub Actions çalıştırmasının
**Artifacts** bölümünde `playwright-traces` adıyla indirilebilir (Hafta 7'den itibaren).

### Test verisi

E2E testleri boş bir veritabanıyla başlar (`tests/e2e/conftest.py`). Kullanıcı, salon,
etkinlik, bilet gibi verileri hazırlamak için ekiplerle birlikte **yardımcı fixture'lar**
yazın (ör. `full_event`, `participant_with_ticket`). Bu fixture'lar `tests/e2e/conftest.py`'de durur ve
`qa` takımının onayıyla değişir.

## 7. Keşif testi

Keşif testi rastgele tıklamak değil, **amaçlı ve zaman sınırlı** bir öğrenme
etkinliğidir. Her seans için bir **görev kâğıdı (charter)** yazın:

```text
Görev: Bilet modülünü, kontenjan ve zaman sınırlarına odaklanarak keşfet
       ve kullanıcıyı yanlış yönlendiren durumları bul.
Süre: 45 dakika
Kapsam: Bilet alma, iptal, QR ile giriş (ödeme hariç)
Fikirler: Aynı anda iki sekme, çift tıklama, geri tuşu, sayfayı yenileme,
          son boş yer, satışın kapandığı dakika, aynı QR kodu iki kez okutma

Notlar:
- 10:05 Bilet iptalinden sonra geri tuşu → bilet hâlâ "Geçerli" görünüyor (hata mı?)
- ...
Bulunan hatalar: #57, #58
Sorular (PO'ya): İptal edilen bilet tekrar satışa açılınca kim önce alır?
```

Çapraz test haftalarında (Hafta 9 ve 12) başka bir ekibin modülünü bu yöntemle test edeceksiniz.

## 8. Hata raporlamak

Hata raporları **Taiga → Issues**'a, tür **Bug** olarak girilir. Şablon:
`docs/bug-report-template.md`

### İyi hata raporu

```text
Başlık: Kontenjanı dolu etkinlikte bilet alınabiliyor

İlgili hikâye: #42 · Kural: BR-3.2
Ortam: Chrome 130, main, commit a1b2c3d
Ön koşullar: Kapasitesi 100 olan ve 100 bileti satılmış ücretsiz bir etkinlik;
             katılımcı rolünde giriş yapılmış
Adımlar:
  1. Etkinliğin sayfasına git
  2. "Bilet Al"a tıkla
Beklenen: "Kontenjan dolu." mesajı, bilet oluşturulmaz
Gerçekleşen: Bilet oluşturuluyor, satılan bilet sayısı 101 oluyor
Nasıl bulundu: Sınır değer analizi (TC-42-02)
Ekler: https://github.com/iu-dev-hub/eventhub/issues/12
```

### Önem derecesi (severity) ve öncelik (priority)

| | Kim belirler? | Soru |
|---|---|---|
| **Önem derecesi** | Testçi | Hata sisteme ne kadar zarar veriyor? |
| **Öncelik** | PO | Ne kadar çabuk düzeltilmeli? |

| Önem | Örnek |
|---|---|
| **Kritik** | Uygulama çöküyor, veri kayboluyor, iade tutarı yanlış hesaplanıyor |
| **Yüksek** | Ana akış çalışmıyor (bilet alınamıyor), geçici çözüm yok |
| **Orta** | Özellik kısmen çalışıyor veya geçici çözüm var |
| **Düşük** | Yazım hatası, hizalama sorunu |

Yazım hatası düşük önemlidir ama müşteri demosundan önce **yüksek öncelikli** olabilir.
İkisi ayrı kavramlardır.

### Ekler

Taiga'ya dosya eklemeyin (10 MB sınır). Ekran görüntüsü ve logları GitHub'da
**Issues → New issue → Bug attachments** şablonuyla yükleyin, bağlantısını Taiga'ya yapıştırın.

### Hatanın yaşam döngüsü

```text
Yeni → Kabul edildi → Düzeltiliyor → Test edilecek → Kapandı
                                                   ↘ Tekrar açıldı
Yeni → Reddedildi (hata değil / tekrar edilemiyor / kapsam dışı)
```

Düzeltme gelince **onay testi** (confirmation test) yapın: Hata gerçekten düzeldi mi?
Sonra **regresyon** kontrolü: Düzeltme başka bir şeyi bozdu mu? Mümkünse hatayı
yakalayan bir otomatik test ekleyin ki bir daha geri gelmesin.

## 9. CI ve regresyon

- Her PR'da CI'ın sonucunu takip edin. `main`'de kırmızı CI **en yüksek önceliklidir**:
  Ekibe ve SM'ye hemen haber verin.
- **Kararsız (flaky) test:** Bazen geçip bazen kalan test güveni yok eder. Görmezden
  gelmeyin; nedenini bulun (genellikle bekleme veya test verisi sorunu).
- Kritik akışların E2E testleri **regresyon paketiniz**dir; her değişiklikte çalışır.
- Dönem içinde CI'a yeni kalite kapıları eklenecek (Hafta 5, 7, 9). Bu eklemeleri
  testçiler PR olarak yapabilir.

## 10. PR incelerken testçi

`tests/e2e/` değişikliklerinde onay sizden gelir. Diğer PR'larda da şunlara bakın:

- [ ] Her kabul kriteri için bir test var mı?
- [ ] Sınır değerler test edilmiş mi?
- [ ] Beklenen değerler iş kuralından mı yazılmış?
- [ ] Bir test **silinmiş, atlanmış (`skip`) veya gevşetilmiş** mi? Nedeni açıklanmış mı?
- [ ] Testler bağımsız ve anlaşılır mı?

## 11. Sprint sonu test özeti

Sprint review'dan önce kısa bir özet hazırlayın (Taiga Wiki, ekip sayfası):

```text
## Sprint 4 Test Özeti — team-tickets
Sprint hedefi: Katılımcılar ücretsiz etkinliklere bilet alabilsin

Test edilen hikâyeler: #42 ✅, #44 ✅, #45 ⚠️ (1 açık hata)
Otomatik testler: 18 birim, 6 entegrasyon, 4 E2E — hepsi yeşil
Kapsama (Hafta 9'dan itibaren): %82
Bulunan hatalar: 5 (Kritik 0, Yüksek 1, Orta 3, Düşük 1)
Açık hatalar: #57 (Yüksek): İptalden sonra geri tuşu bileti hâlâ geçerli gösteriyor
Riskler: Bekleme listesi akışı henüz test edilmedi (sonraki sprint)
Öneri: #57 düzelmeden #45 kabul edilmemeli
```

Review'da bunu 30 saniyede özetleyin. Amacınız: **PO'ya kabul kararı için bilgi vermek.**

## 12. YZ ile test

Önce teknik, sonra YZ: Ayrıntılar `docs/guides/soft-vibe-coding.md`, Bölüm 6.
Özellikle YZ'nin "kendini doğrulayan" testlerine ve atladığı sınırlara dikkat edin.

## 13. Kontrol listesi (her sprint)

- [ ] Sprintteki her hikâyenin test yaklaşımı yazıldı
- [ ] Test durumları tekniklerle tasarlandı, BR'ye bağlandı
- [ ] Kabul kriterleri için E2E testleri yazıldı, CI'da yeşil
- [ ] Keşif testi seansı yapıldı, notları tutuldu
- [ ] Bulunan hatalar Taiga'da, önem derecesiyle raporlandı
- [ ] Düzeltilen hataların onay testi yapıldı
- [ ] Test özeti hazırlandı

## 14. Sık yapılan hatalar

- **Testi sona bırakmak:** Kod bitince başlamak, sprint sonunda yığılma demektir.
- **Her şeyi E2E ile test etmek:** Yavaş ve kırılgan; sınırlar birim testinin işi.
- **Belirsiz hata raporu:** "Ödünç çalışmıyor" kimseye yardımcı olmaz.
- **Hatayı kişiselleştirmek:** "Ahmet'in kodu bozuk" değil, "Kontenjan kontrolü uygulanmıyor".
- **`sleep` ile test:** Yavaş ve kararsız.
- **Kırmızı CI'a alışmak:** "Zaten hep kırmızı" denen yerde kalite yoktur.

İlgili rehberler: [pull-requests.md](pull-requests.md) ·
[soft-vibe-coding.md](soft-vibe-coding.md) · [communication.md](communication.md)
