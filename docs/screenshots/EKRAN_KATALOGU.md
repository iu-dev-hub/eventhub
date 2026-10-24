# 📅 EventHub — Sprint 3 Accounts Modülü Ekran Kataloğu

> **Ders / Kurum:** Iğdır Üniversitesi Mühendislik Fakültesi — Yazılım Mühendisliği 4. Sınıf  
> **Ders Adı:** Yazılım Sınama ve Doğrulama Dersi  
> **Modül:** `team-accounts`  
> **Geliştirici:** Yusuf Şanverdi ([@yusufsanverdi](https://github.com/yusufsanverdi))  
> **Product Owner:** Abdülselam Onakbaş ([@abdulselam-code](https://github.com/abdulselam-code))  
> **Scrum Master:** Fatma Sümeyye ([@fatmasumeyye](https://github.com/fatmasumeyye))  
> **QA / Tester:** Polat Bilir ([@polat1443](https://github.com/polat1443))  
> **İlgili PR:** [#30: feat(accounts): sprint 3 interfaces and services (TG-68 - TG-82)](https://github.com/iu-dev-hub/eventhub/pull/30)  
> **Otomatik Test Başarısı:** %100 Yeşil (159 / 159 test başarılı)

---

## 📱 Mobil Görünümler Neden Geliştirildi?

1. **Product Owner Onaylı 13 Ekran Taslak Prototipi:**
   Sprint başında belirlenen UI taslağında **Ekran 2 (Giriş Mobil)**, **Ekran 4 (Kayıt Mobil)**, **Ekran 7 (Misafir Mobil)**, **Ekran 9 (Dashboard Mobil)** ve **Ekran 10 (Profil Mobil)** bağımsız kabul kriteri olarak yer almıştır.
2. **Taiga Görev Gereksinimleri:**
   - **TG-70 (`PB-03` - Responsive Giriş ve Kayıt Tasarımı):** Masaüstü çift panelli düzenin mobil ekranlarda tek sütuna uyarlanması zorunlu tutulmuştur.
   - **TG-80 (`PB-13` - Ortak Görsel Tasarım ve Bileşen Standardizasyonu):** 768px altı mobil breakpoint'lerde dokunmatik hedeflerin (`min-height: 44px`) ve esnek kartların sunulması şart koşulmuştur.
3. **Kullanıcı Ergonomisi & Etkinlik Katılımcı Profili:**
   Etkinlik biletleme ve katılım platformlarında kullanıcıların %70'inden fazlası mobil cihazlardan erişir. Masaüstü geniş düzeni mobilde yatay kayma yapmaması için mobil arayüzler optimize edilmiştir.

---

## 🖼️ Ekran Görüntüleri Galerisi

### 1. Giriş Arayüzü (Ekran 1 & Ekran 2)
* **Rota:** `GET /accounts/login` | **Taiga:** TG-69, TG-70
* **Açıklama:** Masaüstünde çift panelli marka ve form alanı; mobilde başparmak odaklı tek sütunlu akış.

| Ekran 1: Masaüstü Görünümü | Ekran 2: Mobil Görünüm |
| :---: | :---: |
| ![Ekran 1](01_giris_desktop.png) | ![Ekran 2](02_giris_mobile.png) |

---

### 2. Kayıt Arayüzü (Ekran 3 & Ekran 4)
* **Rota:** `GET /accounts/register` | **Taiga:** TG-68, TG-70, TG-78
* **Açıklama:** Ad, Soyad, E-posta, Şifre kuralları, Dinamik Öğrenci Numarası alanı ve Hukuki Onay kutuları.

| Ekran 3: Masaüstü Kayıt Formu | Ekran 4: Mobil Kayıt Formu |
| :---: | :---: |
| ![Ekran 3](03_kayit_desktop.png) | ![Ekran 4](04_kayit_mobile.png) |

---

### 3. Şifremi Unuttum ve Sıfırlama Akışı (Ekran 5a, 5b, 5c)
* **Rota:** `GET /accounts/forgot-password` & `GET /accounts/reset-password/<token>` | **Taiga:** TG-76 (`PB-09`)
* **Açıklama:** OWASP kriptografik token standardı; e-posta sunucusu olmadığından yeşil demo bilgilendirme kutusu üzerinden şifre yenileme.

| 5a: Talep Formu | 5b: Başarı & Demo Token | 5c: Yeni Şifre Belirleme |
| :---: | :---: | :---: |
| ![Ekran 5a](05a_sifremi_unuttum_desktop.png) | ![Ekran 5b](05b_sifremi_unuttum_success_desktop.png) | ![Ekran 5c](05c_sifre_sifirla_desktop.png) |

---

### 4. Misafir Karşılama Ekranı (Ekran 6 & Ekran 7)
* **Rota:** `GET /accounts/guest` | **Taiga:** TG-77 (`PB-10`)
* **Açıklama:** Kayıtsız kullanıcılar için etkinlik keşif kartları aktif; bilet alma ve favorilere ekleme kilitli.

| Ekran 6: Masaüstü Misafir Karşılama | Ekran 7: Mobil Misafir Karşılama |
| :---: | :---: |
| ![Ekran 6](06_misafir_desktop.png) | ![Ekran 7](07_misafir_mobile.png) |

---

### 5. Giriş Sonrası Karşılama Paneli / Dashboard (Ekran 8 & Ekran 9)
* **Rota:** `GET /accounts/dashboard` | **Taiga:** TG-71 (`PB-04`)
* **Açıklama:** Ad-soyad karşılama, geçici izleme paneli bilgilendirmesi ve hızlı eylem butonları.

| Ekran 8: Masaüstü Dashboard | Ekran 9: Mobil Dashboard |
| :---: | :---: |
| ![Ekran 8](08_dashboard_desktop.png) | ![Ekran 9](09_dashboard_mobile.png) |

---

### 6. Profil Bilgileri & Hesap Ayarları (Ekran 10a, 10b, 10c)
* **Rota:** `GET /accounts/profile` & `GET /accounts/settings` | **Taiga:** TG-72, TG-73, TG-74, TG-75, TG-81
* **Açıklama:** PO kararı gereği yalnızca Ad ve Soyad düzenlenebilir; E-posta ve Rol salt-okunurdur. Ayarlar sekmesinde şifre değiştirme ve e-posta bildirim tercihleri yer alır.

| 10a: Masaüstü Profil | 10b: Mobil Profil | 10c: Hesap Ayarları & Bildirimler |
| :---: | :---: | :---: |
| ![Ekran 10a](10a_profil_desktop.png) | ![Ekran 10b](10b_profil_mobile.png) | ![Ekran 10c](10c_ayarlar_desktop.png) |

---

### 7. Hukuki Bilgilendirme Sayfaları (Ekran 11, 12, 12b)
* **Rota:** `GET /accounts/terms`, `GET /accounts/privacy`, `GET /accounts/kvkk` | **Taiga:** TG-79 (`PB-12`)
* **Açıklama:** Iğdır Üniversitesi Yazılım Mühendisliği 4. Sınıf Yazılım Sınama ve Doğrulama Dersi kapsamında hazırlanan demo taslak metinleri.

| Ekran 11: Kullanım Koşulları | Ekran 12: Gizlilik Politikası | Ekran 12b: KVKK Aydınlatma Metni |
| :---: | :---: | :---: |
| ![Ekran 11](11_kullanim_kosullari_desktop.png) | ![Ekran 12](12_gizlilik_politikasi_desktop.png) | ![Ekran 12b](12b_kvkk_desktop.png) |

---

### 8. Oturum Kapatma Onay Modalı (Ekran 13)
* **Rota:** `POST /accounts/logout` (Modal Diyaloğu) | **Taiga:** TG-69, TG-75
* **Açıklama:** Yanlışlıkla çıkışı önlemek için güvenlik onayı; onaylandığında oturum (`session.clear`) sonlandırılır.

![Ekran 13](13_cikis_onay_desktop.png)

---
*EventHub Projesi — team-accounts Sprint 3 Çıktısı*
