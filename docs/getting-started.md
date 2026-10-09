# Başlangıç Rehberi (Sprint 0)

**Yazılım Doğrulama ve Sınama** · EventHub projesi

Bu rehber, projede çalışmaya başlamak için gereken her şeyi adım adım anlatır.
Tahmini süre: **60–90 dakika**. Adımları sırayla izleyin; bir adımda takılırsanız
"Sık karşılaşılan sorunlar" bölümüne bakın, çözemezseniz yardım isteyin.

Bu rehberin sonunda:

- GitHub ve Taiga hesaplarınız hazır ve projeye katılmış olacaksınız,
- bilgisayarınızda Python, Git ve VS Code kurulu olacak,
- proje bilgisayarınızda çalışıyor ve testleri geçiyor olacak.

---

## 1. GitHub hesabı

GitHub, kodumuzun durduğu, kod incelemelerinin ve otomatik testlerin (CI) yapıldığı yerdir.

1. **github.com** adresinde hesap açın (hesabınız varsa bu adımı atlayın).
   - **Kullanıcı adı:** Mezun olduktan sonra da kullanacağınız, profesyonel bir ad
     seçin (ör. `ayse-yilmaz`). GitHub profiliniz, iş başvurularında portfolyonuzdur.
   - **E-posta:** Kalıcı kişisel e-postanızı kullanın; okul e-postanızı ayrıca
     ekleyebilirsiniz (Settings → Emails).
2. **Profil adınızı** gerçek adınız ve soyadınızla güncelleyin:
   Sağ üstteki profil resmi → **Settings → Public profile → Name**.
3. **İki adımlı doğrulamayı (2FA) açın:** Settings → **Password and authentication**
   → **Enable two-factor authentication**. GitHub, kod gönderen hesaplardan bunu ister.
   Telefonunuza bir doğrulayıcı uygulama (Google Authenticator, Microsoft Authenticator
   veya GitHub Mobile) kurun. **Kurtarma kodlarını (recovery codes) güvenli bir yere
   kaydedin.**
4. **İsteğe bağlı:** **education.github.com** adresinden öğrenci avantajlarına
   (GitHub Student Developer Pack) başvurun. Onay birkaç gün sürebilir; GitHub Copilot
   gibi araçlara ücretsiz erişim sağlar. Ders için zorunlu değildir.

## 2. Ders organizasyonuna katılma

Öğretim üyesi, GitHub kullanıcı adınızla sizi **`iu-dev-hub`** organizasyonuna
davet edecek.

1. GitHub hesabınızın e-postasına gelen daveti açın **veya**
   **github.com/iu-dev-hub** adresine gidin.
2. **Join iu-dev-hub** düğmesine tıklayın.
3. **github.com/iu-dev-hub/eventhub** adresindeki proje deposunu görebildiğinizi kontrol edin.

## 3. Taiga hesabı

Taiga, proje yönetimi aracımızdır: Backlog, kullanıcı hikâyeleri, sprintler ve hata
kayıtları burada tutulur.

1. **tree.taiga.io** adresine gidin.
2. **Sign in with GitHub** (GitHub ile giriş) seçeneğiyle kayıt olun.
   Böylece ayrı bir şifreye gerek kalmaz.
3. Öğretim üyesi sizi **EventHub** projesine davet edecek.
   Davet geldiğinde kabul edin.
4. Taiga'daki e-posta adresinizi not edin (Profil → Account). 5. adımda Git'e
   **aynı e-postayı** tanıtacaksınız.

## 4. Yazılımların kurulumu

Üç programa ihtiyacınız var: **Python 3.12** (veya daha yeni), **Git** ve **VS Code**.

### Windows

1. **Python:** **python.org/downloads** adresinden Python 3.12 veya daha yeni
   sürümü indirin. Kurulumun **ilk ekranında** alttaki
   **"Add python.exe to PATH"** kutusunu **mutlaka işaretleyin**, sonra *Install Now*.
2. **Git:** **git-scm.com/download/win** adresinden Git for Windows'u indirip
   varsayılan ayarlarla kurun. Bu kurulum, GitHub'a giriş için gereken
   "Git Credential Manager"ı da getirir.
3. **VS Code:** **code.visualstudio.com** adresinden indirip kurun.

### macOS

1. **Terminal**'i açın (Spotlight: `Terminal`).
2. Homebrew kurulu değilse **brew.sh** sitesindeki tek satırlık komutla kurun.
3. Kurulum:

   ```bash
   brew install python@3.12 git gh
   brew install --cask visual-studio-code
   ```

### Linux

Fedora:

```bash
sudo dnf install python3 python3-pip git gh
```

Ubuntu / Debian:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip git gh
```

VS Code için **code.visualstudio.com** adresinden dağıtımınıza uygun paketi indirin.
Linux'ta Python sürümünüzün **3.12 veya daha yeni** olduğunu kontrol edin
(`python3 --version`). Eskiyse öğretim üyesine danışın.

### Kontrol (tüm sistemler)

Yeni bir terminal açın (Windows'ta **PowerShell**) ve şunları çalıştırın:

```bash
python --version     # Python 3.12.x veya daha yeni
git --version        # git version 2.x
```

macOS ve Linux'ta `python` yerine `python3` yazmanız gerekebilir. Bu rehberdeki
komutlarda `python` gördüğünüz her yerde sizde hangisi çalışıyorsa onu kullanın.

### VS Code eklentisi

VS Code'u açın, soldaki **Extensions** (Ctrl+Shift+X) bölümünde **Python**
(yayıncı: Microsoft) eklentisini aratıp kurun.

## 5. Git ayarları

Git'e kim olduğunuzu tanıtın. **E-posta, Taiga hesabınızdaki e-postayla aynı olmalı**;
böylece commit'leriniz Taiga'da sizin adınızla görünür.

```bash
git config --global user.name "Adınız Soyadınız"
git config --global user.email "taiga-ve-github-epostaniz@ornek.com"
git config --global init.defaultBranch main
git config --global pull.rebase false
```

Son satır, `git pull` komutunun başkalarının değişikliklerini sizin dalınızla nasıl
birleştireceğini belirler (birleştirme yöntemi: merge). Bu ayar olmadan bazı Git
sürümleri `git pull` sırasında hata verir.

Yalnızca **Windows**'ta ek olarak:

```bash
git config --global core.autocrlf true
```

> **GitHub'da e-postanızı gizlediyseniz** (Settings → Emails → "Keep my email
> addresses private") ve "Block command line pushes that expose my email" seçeneği
> açıksa, push sırasında hata alabilirsiniz. Bu seçeneği kapatın veya öğretim üyesine danışın.

## 6. GitHub'a giriş (kimlik doğrulama)

Git'in GitHub'a sizin adınıza kod gönderebilmesi için bir kez giriş yapmanız gerekir.

- **Windows:** Ek bir şey yapmanıza gerek yok. İlk `git push` sırasında tarayıcı
  açılır ve GitHub'a giriş yapmanızı ister.
- **macOS ve Linux:** GitHub CLI ile giriş yapın:

  ```bash
  gh auth login
  ```

  Sorulara şu cevapları verin: **GitHub.com** → **HTTPS** →
  **Authenticate Git with your GitHub credentials? Yes** → **Login with a web browser**.
  Ekranda çıkan kodu tarayıcıda girin.

## 7. Projeyi bilgisayarınıza alma ve çalıştırma

Projeleri tuttuğunuz bir klasörde terminal açın ve sırayla çalıştırın.

**1. Depoyu klonlayın**

```bash
git clone https://github.com/iu-dev-hub/eventhub.git
cd eventhub
```

**2. Sanal ortam oluşturun ve etkinleştirin**

Sanal ortam, bu projenin paketlerini bilgisayarınızdaki diğer projelerden ayırır.

```bash
python -m venv .venv
```

Etkinleştirme:

| Sistem | Komut |
|---|---|
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| macOS / Linux | `source .venv/bin/activate` |

Etkinleşince komut satırının başında `(.venv)` yazısını görürsünüz. **Projede her
çalıştığınızda** yeni terminalde bu etkinleştirme komutunu tekrar çalıştırın.

**3. Paketleri ve test tarayıcısını kurun**

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

**4. Veritabanını oluşturun ve uygulamayı çalıştırın**

```bash
flask --app app init-db
python run.py
```

Tarayıcıda **http://127.0.0.1:5000** adresini açın. "EventHub'a Hoş Geldiniz"
sayfasını görmelisiniz. Uygulamayı durdurmak için terminalde **Ctrl+C**.

**5. Testleri çalıştırın**

```bash
pytest
```

Sonuçta `passed` yazmalı ve hiç `failed` olmamalı. Tebrikler, ortamınız hazır!

Tarayıcıda çalışan testleri izlemek isterseniz:

```bash
pytest tests/e2e --headed --slowmo 500
```

## 8. VS Code ile çalışma

1. VS Code'da **File → Open Folder** ile `eventhub` klasörünü açın.
2. **Ctrl+Shift+P** → `Python: Select Interpreter` → içinde **`.venv`** geçen
   seçeneği seçin.
3. **Terminal → New Terminal** ile VS Code içinde terminal açabilirsiniz; sanal ortam
   genellikle otomatik etkinleşir.
4. İsteğe bağlı: Soldaki deney tüpü simgeli **Testing** panelinden testleri
   tek tek çalıştırabilirsiniz.

## 9. Son adım: İlk günlük mesajınız

GitHub'da **github.com/iu-dev-hub/eventhub/discussions** adresine gidin, **Günlük**
kategorisinde ekibinizin başlığını bulun ve ilk mesajınızı yazın:

```text
1. Son yazımdan bu yana ne yaptım? Başlangıç rehberini tamamladım.
2. Şimdi ne yapacağım? CONTRIBUTING.md dosyasını okuyacağım.
3. Önümde bir engel var mı? Yok. (veya: ... adımında takıldım)
```

## Kontrol listesi

- [ ] GitHub hesabı, gerçek ad, iki adımlı doğrulama
- [ ] `iu-dev-hub` organizasyonuna katıldım, `eventhub` deposunu görebiliyorum
- [ ] Taiga'ya GitHub ile kaydoldum, projeye katıldım
- [ ] `python --version` 3.12 veya üstü, `git --version` çalışıyor
- [ ] `git config` ad ve e-posta (Taiga ile aynı e-posta)
- [ ] Depoyu klonladım, sanal ortamı kurdum
- [ ] Uygulama tarayıcıda açılıyor
- [ ] `pytest` çalıştı, tüm testler geçti
- [ ] Discussions'a ilk günlük mesajımı yazdım
- [ ] `README.md` ve `CONTRIBUTING.md` dosyalarını okudum

---

## Sık karşılaşılan sorunlar

**Windows: `python` yazınca Microsoft Store açılıyor veya komut bulunamıyor.**
Python kurulumunda "Add python.exe to PATH" işaretlenmemiştir. Python'u kaldırıp bu
kutuyu işaretleyerek yeniden kurun. Ayrıca *Ayarlar → Uygulamalar → Gelişmiş uygulama
ayarları → Uygulama yürütme diğer adları* bölümünden `python.exe` ve `python3.exe`
kısayollarını kapatın.

**Windows: `Activate.ps1` çalıştırılırken "running scripts is disabled" hatası.**
PowerShell'de bir kez şunu çalıştırın, sonra tekrar deneyin:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**`pip` veya `flask` komutu bulunamıyor.**
Sanal ortam etkin değildir. Satır başında `(.venv)` görünmüyorsa 7. bölümdeki
etkinleştirme komutunu çalıştırın.

**macOS: http://127.0.0.1:5000 açılmıyor veya "Address already in use" hatası.**
macOS'te 5000 numaralı portu *AirPlay Alıcısı* kullanabilir. Uygulamayı başka bir
portta çalıştırın ve tarayıcıda o adresi açın:

```bash
flask --app app run --debug --port 5001
```

**Linux: Playwright testleri tarayıcı bağımlılığı hatası veriyor.**
Sistem kütüphanelerini de kurun:

```bash
python -m playwright install --with-deps chromium
```

**`git clone` veya `git push` sırasında "Repository not found" / "Permission denied".**
Organizasyon davetini kabul etmemiş olabilirsiniz (2. bölüm) veya GitHub'a giriş
yapmamışsınızdır (6. bölüm).

**`git push` sırasında "protected branch" hatası.**
Bu normal: `main` dalına doğrudan kod gönderemezsiniz. Her değişiklik bir dal ve
pull request ile gelir. Ayrıntılar: `CONTRIBUTING.md`.

## Yardım

- Önce bu bölüme ve `README.md` dosyasına bakın.
- Ekip arkadaşlarınıza sorun.
- GitHub Discussions'ta **Soru-Cevap** kategorisine yazın. Hata mesajını ve
  çalıştırdığınız komutu **metin olarak** ekleyin; başkası da aynı sorunu yaşıyor
  olabilir.
