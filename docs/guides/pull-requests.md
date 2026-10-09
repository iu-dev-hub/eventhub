# Pull Request Rehberi

**Herkes için: PR açmak, incelemek ve birleştirmek**

`main` dalına doğrudan kod gönderilemez. Her değişiklik bir **dal (branch)** üzerinde
yapılır ve bir **pull request (PR)** ile önerilir. PR, en az bir kişi tarafından
incelenip onaylanır ve otomatik testler (CI) geçince birleştirilir.

## 1. Bir PR'ın yaşam döngüsü

```text
Taiga'da görevi üstlen
   → main'i güncelle → dal aç → kodla + test yaz → commit → push
   → PR aç → CI çalışır → inceleme → (değişiklik istenirse düzelt)
   → onay + yeşil CI → Squash and merge → dalı sil → Taiga'da durumu güncelle
```

## 2. PR hazırlamak (yazar)

### Adım adım komutlar

```bash
# 1. main'i güncelleyin
git switch main
git pull

# 2. Yeni dal açın: <tür>/TG-<no>-<kısa-açıklama>
git switch -c feature/TG-42-ticket-purchase

# 3. Kodlayın, test yazın, testleri çalıştırın
pytest

# 4. Değişikliklerinizi gözden geçirin ve commit edin
git status
git diff
git add app/tickets/services.py tests/unit/test_tickets.py
git commit -m "feat(tickets): add capacity check for ticket purchase (TG-42)"

# 5. Dalı GitHub'a gönderin
git push -u origin feature/TG-42-ticket-purchase
```

Push sonrası terminalde veya GitHub'da çıkan **"Compare & pull request"** bağlantısıyla
PR'ı açın.

### İyi bir PR'ın özellikleri

| Özellik | Neden? |
|---|---|
| **Tek bir iş** (bir hikâye veya görev) | İnceleyen ne aradığını bilir |
| **Küçük** (ideal: 200 satırdan az değişiklik) | Büyük PR'lar yüzeysel incelenir, hatalar kaçar |
| **Testleriyle birlikte** | Test içermeyen PR onaylanmaz |
| **Açıklayıcı başlık** | `feat(tickets): add capacity check for ticket purchase (TG-42)` |
| **Doldurulmuş şablon** | Ne yapıldı, nasıl test edildi, YZ kullanımı |
| **Kendi gözden geçirmesi yapılmış** | Açmadan önce "Files changed" sekmesini siz de okuyun |

### PR şablonunu doldurma

```text
## Related work item (Taiga)
TG-42

## What changed?
Bilet satın alırken kontenjan kontrolü (BR-3.2) eklendi. Kontenjan doluysa
"Kontenjan dolu." mesajı ve "Bekleme listesine katıl" düğmesi gösteriliyor.

## How was it tested?
- Unit tests: tests/unit/test_tickets.py, sınır değer analizi
  (kapasite 100: satılan 98 / 99 / 100)
- Integration tests: tests/integration/test_tickets.py, dolu etkinlikte uyarı mesajı
- E2E tests: Testçi ayrı PR'da ekleyecek (TG-43)

## AI usage
- Tool: ...
- Used for: ...
- What I changed / corrected in the AI output: ...
```

### Taslak (Draft) PR

İş bitmeden erken geri bildirim istiyorsanız PR'ı **Create draft pull request** ile
açın. Taslak PR birleştirilemez; hazır olduğunuzda **Ready for review**'a tıklayın.

### PR açtıktan sonra

1. **CI'ı izleyin.** Kırmızıysa önce kendiniz düzeltin; inceleyenin vaktini almayın.
2. **İnceleme isteyin.** CODEOWNERS ilgili takımı otomatik ekler; ayrıca bir ekip
   arkadaşınızı **Reviewers** bölümünden seçin.
3. **Taiga'yı güncelleyin.** Hikâyeyi **İncelemede** durumuna taşıyın.
4. **Discussions'taki günlükte** PR'ınızdan bahsedin.

## 3. PR incelemek (inceleyen)

Kod incelemesi bir **statik test** etkinliğidir (ISTQB Bölüm 3): Kod çalıştırılmadan
kusur bulunur. Sektörde en etkili kalite uygulamalarından biridir.

### Ne kontrol edilir?

**Doğruluk**

- [ ] Kod, hikâyenin **kabul kriterlerini** karşılıyor mu?
- [ ] İlgili **iş kuralları** (BR) eksiksiz uygulanmış mı?
- [ ] **Sınır durumlar** ele alınmış mı (tam limit, sıfır, boş girdi, negatif)?
- [ ] Hata durumlarında kullanıcıya anlamlı bir mesaj gösteriliyor mu?

**Testler**

- [ ] Her kabul kriteri için test var mı?
- [ ] Beklenen değerler iş kuralından mı yazılmış, yoksa kodun çıktısından mı?
- [ ] Mevcut bir test **silinmiş veya gevşetilmiş** mi? (Varsa nedenini sorun.)

**Okunabilirlik ve kurallar**

- [ ] İsimler İngilizce ve anlamlı mı? Arayüz metinleri Türkçe mi?
- [ ] İş kuralları `services.py`'de, sayfa mantığı `routes.py`'de mi?
- [ ] Anlamadığınız bir yer var mı? (Varsa sorun; bu bir eksiklik değil, katkıdır.)

**Güvenlik ve kapsam**

- [ ] SQL sorguları parametreli mi?
- [ ] Kodda şifre, anahtar veya kişisel veri var mı?
- [ ] PR yalnızca bu işle ilgili dosyaları mı değiştiriyor?
- [ ] Başka bir ekibin klasörü değişmişse o ekip haberdar mı?

### Yorum yazmak

Yorumun türünü başta belirtin; yazar neyin zorunlu olduğunu hemen anlar:

| Önek | Anlamı | Örnek |
|---|---|---|
| **zorunlu:** | Düzeltilmeden onay yok | `zorunlu: Satış kapanışı kontrolü (BR-3.3) eksik.` |
| **soru:** | Anlamak istiyorum | `soru: Burada neden <= kullandık? Kural "en fazla 3" diyor.` |
| **öneri:** | Yazar karar verir | `öneri: Bu sabiti modülün başına taşısak okunurluk artar.` |
| **küçük:** | Önemsiz ayrıntı | `küçük: Yorumdaki yazım hatası.` |
| **teşekkür:** | İyi olanı söyleyin | `teşekkür: Sınır değer testleri çok açık olmuş.` |

**İyi yorumun kuralları:**

- Koda yorum yapın, kişiye değil: "Bu fonksiyon…" deyin, "Sen…" demeyin.
- Nedenini yazın: "Bu yanlış" değil, "BR-3.3'e göre satış 60 dk önce kapanmalı, burada 30 dk olmuş".
- Mümkünse öneri verin: GitHub'da **Add a suggestion** ile düzeltilmiş satırı önerebilirsiniz.

### Karar vermek

**Review changes** düğmesinden:

- **Approve:** Birleştirilebilir.
- **Request changes:** "zorunlu" yorumlar var; düzeltilmeden onay yok.
- **Comment:** Yalnızca soru veya öneri; onay da ret de değil.

İncelemeyi **aynı gün veya en geç 24 saat içinde** yapın. Bekleyen PR, ekibin tamamını yavaşlatır.

## 4. İncelemeye yanıt vermek (yazar)

- Her yoruma yanıt verin: düzelttiyseniz "düzeltildi" yazıp konuşmayı **Resolve** edin;
  katılmıyorsanız nedenini kibarca açıklayın.
- Düzeltmeleri **aynı dala** yeni commit olarak gönderin; PR otomatik güncellenir.
- Yeni commit sonrası önceki onaylar geçersiz olur (kural böyle); inceleyenden tekrar
  bakmasını isteyin.
- Tartışma uzarsa (3 yorumdan fazla) yüz yüze veya derste konuşun, sonucu PR'a yazın.

## 5. `main` değiştiyse: Dalı güncellemek

Siz çalışırken başkaları `main`'e kod birleştirmiş olabilir. GitHub "This branch is out
of date" derse:

```bash
git switch feature/TG-42-ticket-purchase
git pull origin main        # main'deki son değişiklikleri dalınıza alır
pytest                      # her şey hâlâ çalışıyor mu?
git push
```

## 6. Birleştirme çatışması (merge conflict) çözmek

İki kişi aynı dosyanın aynı satırlarını değiştirdiyse Git hangisinin doğru olduğuna
karar veremez ve sizden ister. **Bu bir hata değil, çok ekipli çalışmanın olağan bir
parçasıdır.**

```bash
git pull origin main
# CONFLICT (content): Merge conflict in app/__init__.py
```

Çatışan dosyayı VS Code'da açın. Şöyle bir bölüm göreceksiniz:

```text
<<<<<<< HEAD
    from app.tickets import bp as tickets_bp
    app.register_blueprint(tickets_bp)
=======
    from app.events import bp as events_bp
    app.register_blueprint(events_bp)
>>>>>>> main
```

- `<<<<<<< HEAD` ile `=======` arası **sizin** değişikliğiniz,
- `=======` ile `>>>>>>>` arası **main'deki** değişiklik.

Çoğu zaman **ikisi de** kalmalıdır. İşaret satırlarını silip doğru sonucu yazın:

```python
    from app.events import bp as events_bp
    from app.tickets import bp as tickets_bp

    app.register_blueprint(events_bp)
    app.register_blueprint(tickets_bp)
```

Sonra:

```bash
pytest                                   # her şey çalışıyor mu?
git add app/__init__.py
git commit -m "chore: resolve merge conflict with main"
git push
```

VS Code çatışmalı dosyada **Accept Current / Accept Incoming / Accept Both** düğmeleri
de gösterir; ama sonucu mutlaka okuyup test edin. Emin değilseniz diğer değişikliği
yapan ekipten biriyle birlikte çözün.

## 7. Birleştirme ve sonrası

1. Onay + yeşil CI varsa **Squash and merge** ile birleştirin. (Tüm commit'leriniz
   `main`'de tek bir temiz commit olur; başlığın Conventional Commits biçiminde
   olduğunu kontrol edin.)
2. **Delete branch** ile dalı silin.
3. Yerelde:

   ```bash
   git switch main
   git pull
   git branch -d feature/TG-42-ticket-purchase
   ```

4. Taiga'da hikâyeyi **Testte** durumuna taşıyın; testçiye haber verin.

## 8. Yapılmaması gerekenler

- ❌ Testi silerek veya gevşeterek CI'ı yeşile çevirmek
- ❌ Kendi PR'ınızı başkasına "bak geçiver" diyerek incelemesiz onaylatmak
- ❌ Bir PR'da birden fazla işi karıştırmak
- ❌ Haftalarca açık kalan dev bir PR
- ❌ `git push --force` (ortak dallarda başkalarının işini silebilir)
- ❌ İnceleme yorumlarını yanıtsız bırakmak

## 9. Git komutları kısa özet

| Ne yapmak istiyorum? | Komut |
|---|---|
| main'i güncelle | `git switch main && git pull` |
| Yeni dal aç | `git switch -c feature/TG-42-kisa-aciklama` |
| Durumu gör | `git status` |
| Değişiklikleri gör | `git diff` |
| Commit | `git add <dosyalar>` ve `git commit -m "feat(scope): ... (TG-42)"` |
| Dalı gönder | `git push -u origin <dal-adı>` (ilk sefer), sonra `git push` |
| main'deki değişiklikleri dala al | `git pull origin main` |
| Son commit mesajını düzelt (push etmeden önce) | `git commit --amend` |
| Hangi daldayım? | `git branch --show-current` |
