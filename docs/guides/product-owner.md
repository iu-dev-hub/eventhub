# Product Owner Rehberi

**Ürünün değerinden sorumlu kişi**

## 1. Rolün özü

Scrum Rehberi'ne göre Product Owner, ürünün değerini en üst düzeye çıkarmaktan ve
**ürün backlog'unun** yönetiminden sorumludur. Bu projede siz, **modülünüzün** Product
Owner'ısınız; ürünün bütününden sorumlu Baş PO ise öğretim üyesidir (müşteri).

**Ne yaparsınız?**

- Müşterinin ihtiyacını anlarsınız (soru sorarak, dinleyerek).
- İhtiyacı **kullanıcı hikâyelerine** ve **kabul kriterlerine** çevirirsiniz.
- Backlog'u **sıralarsınız**: Önce en değerli ve en riskli işler.
- Ekibin sorularını yanıtlarsınız; bilmiyorsanız müşteriye sorarsınız.
- Tamamlanan işi kabul kriterlerine göre **kabul eder veya reddedersiniz**.

**Ne yapmazsınız?**

- Ekibe **nasıl** yapacaklarını söylemezsiniz; **ne** ve **neden** sorularını yanıtlarsınız.
- Sprint ortasında sprint backlog'una iş eklemezsiniz (acil durumda SM ile konuşursunuz).
- Görevleri (task) yönetmezsiniz: Sprint backlog'u geliştiricilerindir.
- Kendi tahmininizi dayatmazsınız: Puanı geliştiriciler verir.

## 2. Haftalık ritim

| Ne zaman? | Ne yaparsınız? |
|---|---|
| Uygulama dersi başı | Sprint review'da kabul durumunu açıklarsınız |
| Uygulama dersi | Sprint planlamada sprint hedefini ve öncelikleri sunarsınız |
| Uygulama dersi | Geliştirme sırasında ekibin sorularını yanıtlarsınız |
| Hafta içi (1 kez, ~45 dk) | **Backlog iyileştirme:** Gelecek sprintin hikâyelerini hazırlarsınız |
| Hafta içi (sürekli) | Testte bekleyen hikâyeleri kontrol edip kabul edersiniz |
| Hafta içi | Müşteriye iletilecek soruları toplarsınız |

## 3. Müşteriyle çalışmak

Müşteri (öğretim üyesi) ile ekibiniz adına konuşan **tek kişi** sizsiniz.

### Müşteri görüşmesine hazırlık

1. İhtiyaç dokümanını (`docs/business-rules.md`) ekiple birlikte okuyun.
2. Soruları ekipten toplayın ve şu türlere ayırın:
   - **Eksik:** "Bir organizatör kendi etkinliğine bilet alabilir mi?"
   - **Belirsiz:** "Sayfa 'kullanışlı' olmalı diyorsunuz; bunu nasıl ölçeceğiz?"
   - **Çelişkili:** "Şu kural ile şu not birbirini tutmuyor; hangisi geçerli?"
   - **Örnekle doğrulama:** "Etkinlik 19:00'da başlıyorsa, 18:00'de bilet alınabilir mi?"
3. Soruları önceliklendirin: Görüşme süresi kısa (10 dk).

### İyi soru teknikleri

- **"Ne olur eğer…?"** soruları sınır durumları ortaya çıkarır.
- **Somut örnek isteyin:** "Bir örnekle anlatır mısınız?"
- **Ölçülebilir cevap isteyin:** "Kolay" yerine "kaç tıklama", "hızlı" yerine "kaç saniye".
- **Cevabı tekrar edin:** "Yani, ücretsiz etkinlikte ödeme adımı olmadan bilet hemen geçerli oluyor, doğru mu?"

### Görüşme sonrası

1. Cevapları **aynı gün** Taiga'daki ilgili hikâyeye yorum olarak yazın.
2. Kurala dönüşen cevapları `docs/business-rules.md`'ye eklemek için PR açın
   (müşteri belgesi olduğu için öğretim üyesi onaylar). "Değişiklik geçmişi"
   tablosuna yeni sürümü ve kaynağı yazın:

   ```text
   | 1.1 | 2026-10-16 | BR-2.8 eklendi: Etkinlik başlığı en fazla 100 karakter olabilir | team-events sorusu |
   ```

3. Cevabı diğer ekiplerin PO'larıyla da paylaşın (Discussions → Scrum of Scrums).

## 4. Backlog hazırlamak

### Hiyerarşi

```text
Epic (büyük özellik, ör. "Ödünç İşlemleri")      ← müşteri/Baş PO belirler
 └── User Story (kullanıcıya değer veren parça)   ← siz yazarsınız
      └── Task (teknik iş adımı)                  ← geliştiriciler yazar
```

### Kullanıcı hikâyesi biçimi

```text
Bir <rol> olarak, <istek> istiyorum, böylece <fayda>.
```

Örnek: *Bir katılımcı olarak, etkinliğe bilet almak istiyorum, böylece etkinliğe katılabilirim.*

### İyi hikâye: INVEST

| Harf | Anlamı | Kontrol sorusu |
|---|---|---|
| **I**ndependent | Bağımsız | Başka hikâyeye sıkı sıkıya bağlı mı? |
| **N**egotiable | Pazarlığa açık | Çözümü dayatıyor mu, yoksa ihtiyacı mı anlatıyor? |
| **V**aluable | Değerli | Kullanıcıya veya müşteriye bir fayda sağlıyor mu? |
| **E**stimable | Tahmin edilebilir | Ekip büyüklüğünü kestirebiliyor mu? |
| **S**mall | Küçük | Bir sprintte bitebilir mi (en fazla 8 puan)? |
| **T**estable | Test edilebilir | Bittiğini nasıl anlayacağız? |

### Kabul kriterleri: Given / When / Then

Kabul kriterleri, hikâyenin **bittiğini nasıl anlayacağımızı** söyler. Testçi
testlerini bunlardan yazar; bu yüzden **somut ve ölçülebilir** olmalıdır.

```text
Hikâye #42: Bir katılımcı olarak etkinliğe bilet almak istiyorum,
            böylece etkinliğe katılabilirim.

Kabul kriterleri:
1. Given yayında, ücretsiz ve kontenjanında 1 boş yer kalmış bir etkinlik,
   When giriş yapmış bir katılımcı "Bilet Al"a tıkladığında,
   Then bilet oluşturulur ve "Biletlerim" sayfasında QR koduyla görünür.
2. Given kontenjanı dolmuş bir etkinlik,
   When katılımcı bilet almak istediğinde,
   Then "Kontenjan dolu." mesajı ve "Bekleme listesine katıl" düğmesi gösterilir. (BR-3.2)
3. Given başlamasına 59 dakika kalmış bir etkinlik,
   When katılımcı bilet almak istediğinde,
   Then "Bilet satışı kapanmıştır." mesajı gösterilir ve bilet oluşturulmaz. (BR-3.3)
4. Given giriş yapmamış bir ziyaretçi,
   When "Bilet Al"a tıkladığında,
   Then giriş sayfasına yönlendirilir.
```

**İpuçları:**

- **Sınırları** yazın: "1 boş yer varken" ve "kontenjan doluyken" ayrı kriterlerdir.
- **Kullanıcı mesajlarını birebir** yazın; testler bu metni arayacak.
- **BR kodunu** ekleyin; izlenebilirlik sağlar.
- **Mutsuz yolları** unutmayın: Hata, limit aşımı, yetkisiz kullanıcı.

### Kötü ve iyi hikâye

| ❌ Kötü | ✅ İyi |
|---|---|
| "Bilet sistemi yapılacak" | "Bir katılımcı olarak, etkinliğe bilet almak istiyorum…" + 4 kabul kriteri |
| "Veritabanına tickets tablosu ekle" | Bu bir **görev**dir, hikâye değil; hikâyenin altına task olarak eklenir |
| "Bilet almak kolay olmalı" | "…Then katılımcı etkinlik sayfasından en fazla 2 tıklamayla bilet alır" |
| "Organizatör etkinlik açar, katılımcı bilet alır, öder, iade alır" | Dört ayrı hikâyeye bölünmeli |

### Büyük hikâyeyi bölmek

| Bölme yolu | Örnek |
|---|---|
| **İş kuralına göre** | "Kontenjan kontrolü" ve "satış kapanışı" ayrı hikâyeler |
| **Kullanıcı rolüne göre** | Önce katılımcı, sonra organizatör ekranları |
| **Mutlu / mutsuz yol** | Önce başarılı bilet alma, sonra hata durumları |
| **İşleme göre** | Bilet al / bileti iptal et |
| **Basitten karmaşığa** | Önce ücretsiz etkinlik, sonra ücretli (ödemeli) |

### Sıralama (önceliklendirme)

Backlog'un en üstünde şunlar olmalı:

1. **MVP için gerekenler** (Hafta 8: kayıt → giriş → etkinlik arama → bilet alma → QR ile giriş)
2. **Başka ekiplerin beklediği işler** (ör. team-events'in `get_event` fonksiyonu)
3. **Riskli veya belirsiz işler** (erken öğrenmek daha ucuz)
4. Diğer değerli işler

Modüller arası önceliği müşteri (Baş PO) belirler; çatışma varsa ona danışın.

### Hazır Tanımı (Definition of Ready)

Bir hikâyeyi **Hazır** durumuna almadan önce ekibinizin Hazır Tanımı'nı kontrol edin
(`docs/definition-of-ready-and-done.md`). Tipik olarak: hikâye biçiminde, kabul
kriterleri var, bağımlılıklar yazılı, ekip tahmin etmiş, bir sprinte sığıyor.

## 5. Taiga'da backlog yönetimi

**Hikâye oluşturma:**

1. **Scrum → Backlog → + New user story**
2. **Subject:** Kısa başlık (ör. "Katılımcı bilet alır")
3. **Description:** Hikâye cümlesi + kabul kriterleri + ilgili BR kodları + bağımlılıklar
4. **Tags:** Ekibinizin etiketi (`team-tickets` vb.)
5. **Epic:** İlgili epic'e bağlayın
6. **Status:** **Yeni** (hazır olunca **Hazır**)

**Sıralama:** Backlog listesinde hikâyeleri sürükleyip bırakarak sıralayın.
En üstteki, en önce yapılacak olandır.

**Açıklama şablonu:**

```text
Bir <rol> olarak, <istek> istiyorum, böylece <fayda>.

Kabul kriterleri:
1. Given ... When ... Then ...
2. Given ... When ... Then ...

İlgili kurallar: BR-x.y, BR-x.y
Bağımlılıklar: #17 (team-events, get_event fonksiyonu)
Notlar: Müşteri görüşmesi 2026-10-09: ...
```

## 6. Toplantılarda PO

### Backlog iyileştirme (hafta içi, ~45 dk)

Gelecek sprint için hikâyeleri hazırlarsınız. Katılımcılar: siz, en az bir geliştirici
ve testçi ("Üç Amigo").

1. Sıradaki 3–5 hikâyeyi okuyun.
2. Geliştirici: "Bunu nasıl yaparız, başka ekibe ihtiyacımız var mı?"
3. Testçi: "Bunu nasıl test ederiz, hangi sınırlar var?"
4. Eksik kabul kriterlerini ekleyin; çok büyük hikâyeleri bölün.
5. Cevaplayamadığınız soruları müşteri listesine ekleyin.

### Sprint planlama

1. **Sprint hedefini** tek cümleyle önerin: *"Katılımcılar ücretsiz etkinliklere bilet alabilsin."*
2. Backlog'un en üstündeki hikâyeleri sırayla anlatın.
3. Ekip ne kadarını alabileceğine **kendisi** karar verir; zorlamayın.
4. Hedefe katkısı olmayan işleri sprinte sokmayın.

### Sprint review

1. Sprintte **Bitti** olan ve olmayan hikâyeleri açıklayın.
2. Demoyu geliştiriciler yapar; siz bağlamı anlatırsınız.
3. Müşterinin geri bildirimini **not alın** ve backlog'a yansıtın.

## 7. Kabul etmek veya reddetmek

Testçi bir hikâyenin testlerini tamamladığında:

1. Kabul kriterlerini **tek tek** kendiniz de deneyin (uygulamayı çalıştırarak).
2. Testçinin sonuçlarına ve açık hata kayıtlarına bakın.
3. Bitti Tanımı'nın sağlandığını kontrol edin.
4. **Kabul:** Hikâyeyi Taiga'da **Bitti**'ye taşıyın, kısa bir yorum yazın:
   *"Kabul: 4 kriterin 4'ü sağlandı, E2E testleri CI'da yeşil."*
5. **Red:** Hikâyeyi **Yapılıyor**'a geri alın ve **hangi kriterin** neden sağlanmadığını
   yazın. "Beğenmedim" değil: *"Kriter 2: Kontenjan mesajı farklı metinle gösteriliyor."*

Kabul kriterinde olmayan yeni bir isteğiniz varsa hikâyeyi reddetmeyin; **yeni bir
hikâye** yazın.

## 8. İletişim

| Kiminle? | Nasıl? |
|---|---|
| Müşteri | Derste müşteri görüşmesi; hafta içinde soru listesi biriktirilir |
| Ekibiniz | Taiga hikâye yorumları, derste yüz yüze |
| Diğer PO'lar | Discussions → Scrum of Scrums (bağımlılıklar, ortak kurallar) |
| Öğretim üyesi (müşteri değil, koç olarak) | Süreçle ilgili sorular için |

## 9. Haftalık kontrol listesi

- [ ] Gelecek sprint için en az 3–5 hikâye **Hazır** durumunda
- [ ] Hazır hikâyelerin kabul kriterleri somut ve sınır durumları içeriyor
- [ ] Müşteri soruları listesi güncel; cevaplar Taiga'ya ve dokümana işlendi
- [ ] Testte bekleyen hikâyeler kontrol edildi, kabul/red kararı verildi
- [ ] Bağımlı olduğunuz ekiplerin PO'larıyla konuşuldu
- [ ] Backlog sıralaması güncel

## 10. Sık yapılan hatalar

- **Hikâye yerine görev yazmak** ("tablo oluştur"): Kullanıcı ve fayda yoksa hikâye değildir.
- **Belirsiz kabul kriteri** ("doğru çalışmalı"): Test edilemez.
- **Müşteri adına tahmin etmek:** Bilmiyorsanız sorun; yanlış tahmin pahalıya mal olur.
- **Her şeyi öncelikli yapmak:** Sıralamanın anlamı, bazı işlerin **sonra** yapılmasıdır.
- **Kabulü geciktirmek:** Testte bekleyen iş, ekibin hızını görünmez kılar.
- **Sprint ortasında hedef değiştirmek.**
