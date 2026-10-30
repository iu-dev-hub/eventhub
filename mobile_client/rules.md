# Proje Geliştirme Kuralları

Bu belge, projenin mimari yapısını, kodlama standartlarını, UI/UX kurallarını ve geliştirme süreçlerini tanımlar. Projeye katkı sağlayan tüm geliştiricilerin bu kurallara uyması zorunludur.

---

## 1. Mimari ve Dizin Düzeni

Uygulama monolitik dosya yapısından kaçınarak **Feature-first / MVVM** prensipleriyle modüler yapıda geliştirilecektir.

```text
src/
├── core/                  # Çekirdek konfigürasyon, tema, sabitler, rota yönetimi
│   ├── config.py
│   ├── constants.py
│   └── theme.py
├── components/            # Yeniden kullanılabilir arayüz parçaları
│   ├── event_card.py      # Etkinlik kartı bileşeni
│   ├── seat_matrix.py     # Koltuk seçim matrisi/krokisi
│   ├── navbar.py
│   └── loading_dialog.py
├── views/                 # Sayfa görünümleri (View bazlı)
│   ├── auth/              # Giriş, kayıt, doğrulama
│   ├── home/              # Bannerlar, etkinlik listeleri, filtreler
│   ├── event_detail/      # Etkinlik detayları ve tarih seçimi
│   ├── seat_selection/    # Tribün/blok ve koltuk seçim krokisi
│   ├── checkout/          # Bilet özeti ve ödeme akışı
│   └── profile/           # Biletlerim (QR kodlar) ve profil ayarları
├── services/              # API, veritabanı, QR üretim servisleri
│   ├── api_service.py
│   ├── qr_service.py
│   └── auth_service.py
├── models/                # Veri modelleri (Pydantic / Dataclasses)
│   ├── user.py
│   ├── event.py
│   ├── seat.py
│   └── ticket.py
└── main.py                # Başlangıç noktası ve rota yönlendirici
