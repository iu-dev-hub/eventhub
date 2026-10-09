# Soft Vibe Coding Rehberi

**Yapay zekâ ile kod geliştirme: hızlı ama sorumlu**

## 1. Vibe coding ve soft vibe coding

**Vibe coding:** Yapay zekâya (YZ) ne istediğinizi söyleyip, üretilen kodu okumadan
ve anlamadan kabul etmek. Hızlıdır ama kimse kodun gerçekte ne yaptığını bilmez;
hatalar, güvenlik açıkları ve bakım sorunları gizli kalır.

**Soft vibe coding (bu derste kullandığımız yaklaşım):** YZ kodu üretir; **siz her
satırı okur, anlar, test eder ve sorumluluğunu alırsınız.** YZ hızlı bir yardımcıdır,
mühendis sizsiniz.

> Bu dersin ana fikri: **"Kodu YZ yazabilir; kodun doğru olduğunu göstermek sizin işiniz."**

Sektörde de durum bu: YZ araçları yaygınlaştıkça, üretilen kodu **değerlendirebilen ve
test edebilen** mühendislere ihtiyaç artıyor.

## 2. Altın kurallar

1. **Açıklayamadığın kodu gönderme.** Sprint review'da PR'ınızın herhangi bir bölümünü
   açıklamanız istenebilir. Açıklayamadığınız kod birleştirilmiş sayılmaz.
2. **Kod testleriyle birlikte gelir.** YZ'ye test yazdırabilirsiniz ama testleri siz
   kontrol edersiniz. Test içermeyen PR onaylanmaz.
3. **Şeffaf ol.** PR şablonundaki "AI usage" bölümünü dürüstçe doldurun. YZ kullanmak
   serbesttir; gizlemek değildir.
4. **Gizli bilgi paylaşma.** Şifre, API anahtarı, kişisel veri (gerçek ad, e-posta,
   öğrenci numarası) YZ'ye yapıştırılmaz.
5. **Önerilen paketleri doğrula.** YZ bazen var olmayan veya güvenilmez paket adları
   uydurur. Yeni paket eklemek öğretim üyesinin onayını gerektirir (`requirements.txt`).
6. **Başka ekibin koduna dokunma.** YZ "şu dosyayı da değiştirelim" diyebilir. O dosya
   başka ekibinse önce Scrum of Scrums'ta konuşun.
7. **Küçük adımlarla ilerle.** Tek seferde bütün modülü değil, bir fonksiyonu veya bir
   sayfayı isteyin. Küçük parça = anlaşılır kod = kolay inceleme.

## 3. Bir işi YZ ile yapma akışı

```text
1. Anla     → Hikâyeyi ve kabul kriterlerini okuyun. İlgili BR kurallarını bulun.
2. Planla   → İşi küçük adımlara bölün (ör. önce servis fonksiyonu, sonra sayfa).
3. Bağlam   → YZ'ye ilgili dosyaları, kuralları ve isimlendirme kurallarını verin.
4. Üret     → Tek bir küçük parçayı isteyin.
5. Oku      → Her satırı okuyun. Anlamadığınızı YZ'ye "bunu açıkla" diye sorun.
6. Çalıştır → Kodu çalıştırın, testleri çalıştırın (pytest).
7. Sorgula  → "Bu kodda hangi sınır durumlar eksik?" diye YZ'ye ve kendinize sorun.
8. Gönder   → Commit, PR; "AI usage" bölümünü doldurun.
```

## 4. İyi bir istemin (prompt) anatomisi

| Bölüm | Ne yazılır? | Örnek |
|---|---|---|
| **Bağlam** | Proje, teknoloji, ilgili dosyalar | "Flask ile yazılan bir etkinlik ve bilet platformunda çalışıyorum." |
| **Görev** | Tek ve net bir iş | "`app/tickets/services.py` dosyasına `can_purchase` fonksiyonu yaz." |
| **Kurallar** | İş kuralları (BR kodlarıyla) | "BR-3.3: Bilet satışı etkinlik başlangıcından 1 saat önce kapanır." |
| **Kısıtlar** | Projenin kuralları | "İsimler İngilizce, kullanıcı mesajları Türkçe; yalnızca standart kütüphane." |
| **Çıktı** | Ne istediğiniz | "Önce kodu, sonra satır satır kısa açıklamasını ver." |
| **Doğrulama** | Kendini kontrol | "Sınır değerleri kapsayan pytest testleri de öner." |

### Şablon

```text
Bağlam: Flask + SQLite ile geliştirilen "EventHub" projesinde,
<modül adı> modülünde çalışıyorum. İlgili dosyalar aşağıda.

Görev: <tek ve net bir iş>

Kurallar:
- <BR-x.y: kural>
- <BR-x.y: kural>

Kısıtlar:
- Kod, fonksiyon ve değişken adları İngilizce (PEP 8, snake_case).
- Kullanıcıya gösterilen mesajlar Türkçe.
- Yalnızca Flask ve Python standart kütüphanesi kullan; yeni paket ekleme.
- Veritabanı sorgularında parametreli sorgu kullan (f-string ile SQL yazma).
- Başka dosyayı değiştirmeyi önerme; gerekiyorsa sadece belirt.

Çıktı: Önce kodu ver, sonra kısa açıklamasını yaz.
Ardından sınır değerleri kapsayan pytest testlerini öner.

<ilgili dosyaların içeriği>
```

## 5. Örnek istemler

### Sprint 1: Modül iskeleti

```text
Flask projemize "tickets" adında bir modül ekleyeceğim. Proje kuralları şöyle:
- Klasör: app/tickets/ ; içinde __init__.py, routes.py, services.py
- Blueprint adı "tickets", url_prefix "/tickets"
- Şablon: app/templates/tickets/index.html, base.html'i extend etmeli
- __init__.py, "bp" nesnesini dışa açmalı
Bu dosyaları oluştur. Ayrıca app/__init__.py'ye eklenecek iki satırı ve
base.html menüsüne eklenecek bağlantı satırını ayrıca göster.
Son olarak /tickets/ sayfasının açıldığını test eden bir entegrasyon testi yaz
(tests/integration/test_tickets.py, "client" fixture'ı hazır).

[app/__init__.py ve app/templates/base.html içeriğini buraya yapıştırın]
```

### İş kuralı fonksiyonu

```text
app/events/services.py dosyasına
validate_event_capacity(capacity: int, venue_capacity: int) -> None fonksiyonunu yaz.
Kurallar:
- BR-2.3: Etkinlik kapasitesi, salonun kapasitesini aşamaz.
- Kapasite en az 1 olmalıdır.
- Kural ihlalinde Türkçe mesajlı ValueError fırlat.
Docstring'de BR koduna atıf yap.
```

### Hata ayıklama

```text
pytest çalıştırınca şu hatayı alıyorum. Hatanın nedenini açıkla ve en küçük
düzeltmeyi öner. Testi değiştirmeyi önerme; sorun kodda olabilir.

<hata mesajının tamamı>
<ilgili fonksiyon>
<ilgili test>
```

### Kod incelemesi istemek

```text
Aşağıdaki kodu bir kıdemli geliştirici gibi incele. Özellikle:
- BR-3.2 ve BR-3.3 kurallarına uyuyor mu?
- Sınır durumlar (tam limit, sıfır, negatif) doğru ele alınmış mı?
- Güvenlik sorunu var mı (SQL enjeksiyonu, girdi doğrulama)?
Bulduklarını öncelik sırasıyla listele; kodu yeniden yazma.
```

## 6. YZ ile test tasarımı: Önce teknik!

YZ'ye test yazdırmak cazip ama tehlikelidir. Sıra şöyle olmalı:

1. **Tekniği uygulayın:** Derste öğrendiğiniz tekniği (denklik sınıfları, sınır değer,
   karar tablosu…) kullanarak test durumlarını **önce kendiniz** çıkarın.
2. **YZ'ye sorun:** Aynı gereksinim için test durumları isteyin.
3. **Karşılaştırın:** YZ neyi atladı? Siz neyi kaçırdınız? Hangi testler gereksiz?
4. **Birleştirin ve otomatikleştirin.**

### YZ'nin test yazarken sık yaptığı hatalar

| Hata | Örnek | Neden sorun? |
|---|---|---|
| **Kendini doğrulayan test** | Fonksiyonun mevcut çıktısını "beklenen" diye yazmak | Kod yanlışsa test de yanlışı onaylar |
| **Sınırı atlamak** | Boş ve tamamen dolu etkinlik test ediliyor, son boş yer yok | Hataların çoğu sınırlardadır |
| **Her şeyi taklit etmek (mock)** | Test edilen fonksiyonun kendisi bile mock'lanıyor | Test hiçbir şeyi test etmez |
| **Tek senaryo** | Yalnızca "mutlu yol" | Hata durumları test edilmez |
| **Belirsiz doğrulama** | `assert result` | "Bir şey döndü" yeterli değil; değeri kontrol edin |

> **Kural:** Beklenen değeri **iş kuralından** (BR) yazın, kodun çıktısından değil.

## 7. YZ'nin sık yaptığı kod hataları: Kontrol listesi

- [ ] **Uydurma paket veya fonksiyon:** Var olmayan bir kütüphane veya API mi kullanılmış?
- [ ] **Eski API:** Kütüphanenin eski sürümüne ait bir kullanım mı var?
- [ ] **SQL enjeksiyonu:** SQL, f-string veya `+` ile mi birleştirilmiş?
  Her zaman parametreli sorgu: `db.execute("SELECT * FROM events WHERE id = ?", (event_id,))`
- [ ] **Bir eksik / bir fazla (off-by-one):** `<` ile `<=` doğru mu? Limit tam sınırda nasıl davranıyor?
- [ ] **İş kuralı atlanmış:** BR'deki her koşul kodda var mı (ör. satışın kapandığı etkinlik)?
- [ ] **Türkçe karakterler:** `"I".lower()` Türkçede "ı" olmalı; büyük/küçük harf
  duyarsız aramalar Türkçe karakterlerle denendi mi?
- [ ] **Gömülü sır:** Kodda şifre, anahtar veya gerçek e-posta var mı?
- [ ] **Gereksiz karmaşıklık:** Basit bir iş için sınıflar, katmanlar, tasarım kalıpları mı eklenmiş?
- [ ] **İlgisiz değişiklik:** İstemediğiniz dosyalar veya satırlar değişmiş mi?
- [ ] **Test silme / gevşetme:** "Testi geçirmek için" test değiştirilmiş veya silinmiş mi?

## 8. PR göndermeden önce kendinize sorun

1. Bu kodun **her satırını** bir arkadaşıma açıklayabilir miyim?
2. Kabul kriterlerinin **her biri** için bir test var mı?
3. Sınır değerler test edildi mi?
4. `pytest` yerelde geçiyor mu?
5. Değiştirdiğim dosyalar yalnızca bu işle mi ilgili?
6. PR'daki "AI usage" bölümü dürüst mü?

### "AI usage" bölümüne örnek

```text
## AI usage
- Tool: ChatGPT (ücretsiz sürüm)
- Used for: can_purchase fonksiyonunun ilk sürümü ve test önerileri
- What I changed / corrected in the AI output:
  - YZ, BR-3.3'ü (satış başlangıçtan 1 saat önce kapanır) atlamıştı; ekledim.
  - Önerilen testlerde kontenjan sınırı (son boş yer ve dolu etkinlik) yoktu;
    sınır değer analiziyle ekledim.
  - YZ SQL'i f-string ile yazmıştı; parametreli sorguya çevirdim.
```

## 9. İyi alışkanlıklar

- **Her iş için yeni sohbet açın.** Uzun sohbetlerde YZ eski bağlamı karıştırır.
- **Yalnızca ilgili dosyaları verin.** Bütün projeyi yapıştırmak dikkati dağıtır.
- **"Neden?" diye sorun.** "Bu satır neden gerekli?" sorusu hem öğretir hem hatayı yakalar.
- **YZ'ye itiraz edin.** YZ kendinden emin konuşur ama yanılabilir. Kural ile kod
  çelişiyorsa kural kazanır; emin değilseniz PO'ya sorun.
- **Hangi aracı kullandığınız önemli değil.** Ücretsiz sürümlere erişebildiğiniz herhangi
  bir sohbet asistanını kullanabilirsiniz.

## 10. Akademik dürüstlük

YZ kullanmak bu derste **serbest ve teşvik edilir**. Ancak:

- Kodun sorumluluğu **PR'ı açan kişidedir**, YZ'de değil.
- Açıklayamadığınız kodu kendi katkınız gibi sunmak akademik dürüstlüğe aykırıdır.
- Değerlendirmede kodun miktarı değil, **anlamanız, testleriniz ve inceleme kaliteniz**
  ölçülür.
