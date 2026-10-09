# Front (Frontend Developer) Rehberi

**Kullanıcının gördüğü ve etkileşime girdiği her şeyden sorumlu kişi**

## 1. Rolün özü

Front geliştirici, modülün **sayfalarını, formlarını ve kullanıcı mesajlarını**
geliştirir. Scrum açısından Back ve Testçi ile birlikte **Developers**
sorumluluğunu taşırsınız.

**Sorumluluklarınız:**

- Sayfa şablonlarını (`app/templates/<modül>/`) ve formları geliştirmek
- Kullanıcı mesajlarını kabul kriterlerine **birebir** uygun yazmak
- Back'in servis fonksiyonlarını sayfalara bağlamak (route'lar üzerinden)
- **Erişilebilirlik** temellerini uygulamak
- Arayüzü **test edilebilir** kılmak
- Back'in PR'larını incelemek

## 2. Haftalık ritim

| Ne zaman? | Ne yaparsınız? |
|---|---|
| Sprint planlama | Sayfa ve form görevlerini çıkarırsınız, puan verirsiniz |
| Geliştirme | Görev al → dal aç → şablon + test → PR |
| Her gün (hafta içi) | PR incelemeleri, Discussions günlüğü |
| Backlog iyileştirme | "Kullanıcı bu sayfada ne görecek, hangi mesajları alacak?" |

## 3. Şablon yapısı

Projede şablon motoru **Jinja2** kullanılır. Her sayfa ortak düzeni `base.html`'den alır:

```html
{# app/templates/tickets/index.html #}
{% extends "base.html" %}
{% block title %}Biletlerim{% endblock %}
{% block content %}
<h1>Biletlerim</h1>
<p>Satın aldığınız biletler ve QR kodları aşağıda listelenir.</p>
{% endblock %}
```

**Kurallar:**

- Her sayfada **tek bir `<h1>`** başlık olsun (hem erişilebilirlik hem testler için).
- `{% block title %}` sayfaya uygun doldurulsun (tarayıcı sekmesindeki başlık).
- Bağlantılarda adres yazmayın, `url_for` kullanın:
  `<a href="{{ url_for('tickets.index') }}">Biletlerim</a>`
- **İş kuralı şablona yazılmaz.** `{% if event.sold < event.capacity %}` gibi bir kontrol
  yerine Back'in servisinden gelen sonucu kullanın (`{% if can_purchase %}`).

## 4. Formlar: Erişilebilir ve test edilebilir

```html
<form method="post" action="{{ url_for('accounts.login') }}">
  <label for="email">E-posta</label>
  <input id="email" name="email" type="email" required autocomplete="username">

  <label for="password">Şifre</label>
  <input id="password" name="password" type="password" required
         minlength="8" maxlength="20" autocomplete="current-password">

  <button type="submit">Giriş Yap</button>
</form>
```

**Neden önemli?**

| Uygulama | Kullanıcıya faydası | Teste faydası |
|---|---|---|
| Her alanda `<label for="...">` | Ekran okuyucular alanı okur; etikete tıklayınca alan seçilir | `page.get_by_label("Şifre")` çalışır |
| Düğmede anlamlı metin ("Giriş Yap") | Ne yapacağı açık | `page.get_by_role("button", name="Giriş Yap")` |
| Doğru `type` (`email`, `password`) | Mobilde uygun klavye, şifre gizlenir | Davranış tutarlı |
| `required`, `minlength` | Anında geri bildirim | Testçi tarayıcı ve sunucu doğrulamasını ayrı test eder |

> **Erişilebilir arayüz, test edilebilir arayüzdür.** Etiketsiz bir form alanını
> testçi kullanıcı gibi bulamaz; ekran okuyucu kullanan bir katılımcı da bulamaz.

Tarayıcıdaki doğrulama (`required`, `minlength`) kolaylık içindir; **güvenlik için
değil**. Back aynı kontrolleri sunucuda da yapar.

## 5. Kullanıcı mesajları

Projede mesajlar Flask'ın `flash` mekanizmasıyla gösterilir; `base.html` bunları
`role="alert"` ile sayfanın üstünde zaten gösteriyor. Route'ta:

```python
flash("Kontenjan dolu.", "error")  # kırmızı
flash("Biletiniz oluşturuldu.", "success")  # yeşil
```

**Kurallar:**

- Mesaj metni **kabul kriterindeki metinle harfi harfine aynı** olmalı.
  Testçi bu metni arayacak; bir nokta farkı bile testi kırar.
- Mesajlar kullanıcının dilinde, kısa ve **ne yapması gerektiğini** söyleyen biçimde:
  "Hata oluştu." değil, "Şifre en az 8 karakter olmalıdır."
- Teknik ayrıntı göstermeyin (hata kodu, SQL, Python hatası).
- Bir mesaj değişecekse PO'ya ve testçiye haber verin.

## 6. Listeler ve tablolar

```html
<table>
  <caption>Biletlerim</caption>
  <thead>
    <tr><th scope="col">Etkinlik</th><th scope="col">Tarih</th><th scope="col">Durum</th></tr>
  </thead>
  <tbody>
    {% for ticket in tickets %}
      <tr>
        <td>{{ ticket.event_title }}</td>
        <td>{{ ticket.starts_at }}</td>
        <td>{{ ticket.status_label }}</td>
      </tr>
    {% else %}
      <tr><td colspan="3">Henüz biletiniz yok.</td></tr>
    {% endfor %}
  </tbody>
</table>
```

- `<caption>` ve `<th scope="col">` tabloyu hem ekran okuyucular hem testler için anlamlı kılar.
- **Boş durumu** unutmayın (`{% else %}`): Liste boşsa kullanıcı ne görecek?
- Jinja değişkenleri otomatik olarak güvenli hale getirilir (HTML kaçışı); `|safe`
  filtresini kullanmayın.

## 7. Menü bağlantısı ve ortak dosyalar

`base.html` ve `app/static/style.css` tüm ekiplerin ortak dosyalarıdır (SM onayı gerekir).

- **Sprint 1:** Modülünüzün menü bağlantısını `base.html`'e ekleyin. Dört ekip aynı
  satırları değiştireceği için birleştirme çatışması yaşayabilirsiniz:
  `docs/guides/pull-requests.md`, Bölüm 6.
- Stilleri mümkün olduğunca mevcut CSS sınıflarıyla (`info`, `message`) çözün.
  Yeni stil gerekiyorsa Scrum of Scrums'ta konuşun; tüm sitenin görünümü etkilenir.

## 8. Testçiyle çalışmak

- Bir sayfayı bitirmeden önce testçiye gösterin: "Bu sayfayı nasıl test edeceksin?"
- Testçi bir elemanı bulamıyorsa (etiket yok, düğme metni belirsiz) bu bir
  **test edilebilirlik kusurudur**; düzeltin.
- CSS sınıfı veya `id`'ye dayalı test yazılmasını önlemek sizin de işiniz: Görünür
  etiketler ve rolleri kullanın.

## 9. Back'in PR'ını incelerken

- [ ] Route, şablona ihtiyaç duyduğum veriyi doğru adla gönderiyor mu?
- [ ] Hata durumlarında kullanıcıya bir mesaj (`flash`) gösteriliyor mu?
- [ ] Mesaj metinleri kabul kriterleriyle aynı mı?
- [ ] Genel PR inceleme kontrol listesi: `docs/guides/pull-requests.md`

## 10. Kendi işinizi denemek

1. Uygulamayı çalıştırın (`python run.py`) ve sayfayı **kullanıcı gibi** kullanın.
2. Yalnızca mutlu yolu değil, hata durumlarını da deneyin: boş form, çok uzun girdi,
   dolu kontenjan.
3. Tarayıcıyı daraltın: Sayfa dar ekranda da kullanılabilir mi?
4. **Klavye testi:** Fareyi bırakın, yalnızca **Tab** ve **Enter** ile formu
   doldurup gönderebiliyor musunuz?
5. Entegrasyon testi ekleyin (sayfa açılıyor mu, mesaj görünüyor mu):

```python
# tests/integration/test_accounts.py
def test_login_page_has_form(client):
    html = client.get("/accounts/login").get_data(as_text=True)
    assert 'for="email"' in html
    assert "Giriş Yap" in html
```

## 11. Kontrol listesi (her PR öncesi)

- [ ] Sayfa `base.html`'i genişletiyor, tek `<h1>` var, `title` dolu
- [ ] Her form alanının `<label>`'ı var; düğme metinleri anlamlı
- [ ] Mesajlar kabul kriterleriyle harfi harfine aynı
- [ ] Şablonda iş kuralı yok
- [ ] Boş durumlar ve hata durumları gösteriliyor
- [ ] Klavyeyle kullanılabiliyor
- [ ] `pytest` yerelde geçiyor
- [ ] PR şablonu dolduruldu (YZ kullanımı dahil)

## 12. Sık yapılan hatalar

- **Etiketsiz form alanı** veya yalnızca `placeholder` ile açıklanan alan
- **"Tıklayın" yazan bağlantılar:** Bağlantı metni nereye gittiğini söylemeli.
- **Mesaj metnini "benzer" yazmak:** "Kontenjan doldu" ≠ "Kontenjan dolu."
- **Şablona iş kuralı yazmak**
- **Adresleri elle yazmak** (`href="/tickets/"`): URL değişince bağlantılar kırılır; `url_for` kullanın.
- **Yalnızca kendi ekranında denemek:** Dar ekran ve klavye kullanımı unutulur.

İlgili rehberler: [pull-requests.md](pull-requests.md) ·
[soft-vibe-coding.md](soft-vibe-coding.md) · [communication.md](communication.md)
