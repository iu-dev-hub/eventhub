# Sprint 4 Accounts altyapı incelemesi

Taiga **TG-164** kapsamında, Sprint 3 Accounts birleştirmesini içeren `main` üzerindeki `dc40ab9` commit’i incelendi. [Sprint 3 ekran kataloğu](screenshots/EKRAN_KATALOGU.md)

## Rotalar ve servisler

Accounts, `/accounts` önekiyle kayıtlı bir Flask Blueprint’tir. Ekranlar Jinja şablonlarından sunulur. Bazı rotalar `Accept` başlığına göre JSON yanıtı da verir. Aşağıdaki yollar `/accounts` önekine göredir. [Blueprint](../app/accounts/routes.py#L25)

| Akış | Mevcut rotalar ve servisler |
| --- | --- |
| Kayıt ve oturum | GET/POST `/register`, `/login`, `/logout`; GET `/me`. `register_user()` kullanıcıyı kaydeder ve parolayı scrypt ile özetler. `authenticate_user()` parolayı doğrular. Oturum ve rol kontrolleri ile geçici giriş kilidi mevcuttur. [Rotalar](../app/accounts/routes.py#L52) · [Servisler](../app/accounts/services.py#L166) · [Yetkilendirme](../app/accounts/security.py#L108) |
| Profil ve ayarlar | GET `/guest`, `/dashboard`, `/profile`, `/settings`; POST `/profile/edit`, `/preferences`. `get_user_by_id()` kullanıcı verisini okur. `update_user_profile()` ad ve soyadı, `update_notification_preferences()` e-posta bildirim tercihini kaydeder. [Rotalar](../app/accounts/routes.py#L268) · [Servisler](../app/accounts/services.py#L307) |
| Şifre işlemleri | GET/POST `/change-password`, `/forgot-password`, `/reset-password/<token>`. `change_password()`, `create_password_reset_token()` ve `reset_password_with_token()` kullanılır. Sıfırlama akışı demo bağlantısıyla çalışır. [Rotalar](../app/accounts/routes.py#L366) · [Servisler](../app/accounts/services.py#L364) |
| Yasal sayfalar | GET `/terms`, `/privacy`, `/kvkk`. Kayıt ekranında kullanım koşulları ve gizlilik bildirimi modalları da bulunur. [Rotalar](../app/accounts/routes.py#L439) |

## Öğrenci statüsü ve indirim

`users` tablosunda kullanıcının beyan ettiği `is_student` (varsayılan `0`) ve isteğe bağlı `student_number` alanları kalıcı olarak saklanır. `register_user()` bu alanları yazar, `get_user_by_id()` profil için okur. Eski Sprint 1/2 şemasına yönelik uyumluluk kodu bu alanları ekler. Profil ad soyad, e-posta ve rolü gösterir. `is_student` doğru olduğunda **Öğrenci Hesabı** rozeti görünür. [SQLite şeması](../app/core/schema.sql#L45) · [Şema uyumluluğu](../app/accounts/services.py#L116) · [Profil şablonu](../app/templates/accounts/profile.html#L34)

**Öğrenci indirim bilgisi mevcut sistemde bulunmuyor.** BR-1.6 öğrenci katılımcıların indirimden yararlanabileceğini, BR-4.2 oranı %25 olarak belirtir. Mevcut şemada öğrenci indirimi hakkı, oranı veya uygulanma durumu için ayrı bir alan yok. Bilet ve ödeme kodunda öğrenci indirimi hesabı bulunmuyor. [İş kuralları](business-rules.md#br-1-hesaplar-team-accounts) · [Ödeme kuralları](business-rules.md#br-4-ödeme-iade-ve-raporlar-team-payments)

## Test kapsamı

- Birim testleri kayıt, kimlik doğrulama, öğrenci statüsünün saklanması, profil düzenleme, şifre ve token işlemleri ile eski şema uyumluluğunu kapsar. [Accounts birim testleri](../tests/unit/test_accounts.py)
- Entegrasyon testleri ekranların açılmasını, oturum akışını, profil düzenlemeyi, şifre işlemlerini ve `/me` yanıtındaki öğrenci alanlarını kapsar. İnceleme tabanında form dönüş hedefleri ve profil HTML’indeki rozet için doğrudan doğrulama yok. [Accounts entegrasyon testleri](../tests/integration/test_accounts.py)

## Sprint 4 görev durumu

| Görev | Durum |
| --- | --- |
| **TG-165 · Form navigasyonu** | **İnceleme tabanında kısmen var.** Şifre formlarında bazı dönüş bağlantıları ve çıkış onayında iptal seçeneği bulunuyor. Giriş, kayıt, profil ve ayar formlarında belirgin form dönüşü veya iptal eksik. Uygulama ve navigasyon testleri ayrı `feature/sprint4-accounts-form-nav` branch’inde commit öncesi incelemede. |
| **TG-166 · Accounts ana sayfası** | **Eksik.** `/accounts/` HTML sayfası başlık ve açıklama gösteriyor. Formlara erişim düğmeleri eksik. Profil, ayarlar ve şifre değiştirme hedefleri oturum gerektiriyor. [Index şablonu](../app/templates/accounts/index.html) |
| **TG-167 · Profil ve öğrenci indirimi** | **Kısmen var.** Profil bilgileri ve öğrenci rozeti mevcut. Ayrı öğrenci indirim durumu eksik. Rozetin öğrenci ve öğrenci olmayan hesaplarda gösterimini doğrulayan HTML testi de eksik. |
