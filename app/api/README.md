# app/api — Mobil istemci için JSON API

**Sahip:** team-mobile (CODEOWNERS) · **Epic:** Mobil Uygulama

Flet ile yazılan Android istemcisinin (`mobile_client/`) konuştuğu JSON uç noktaları
bu klasörde yer alır.

## Kurallar

1. **Burada iş kuralı yazılmaz.** Veri, ilgili modülün `services.py` fonksiyonundan
   alınır (arayüz sözleşmesi) ve yalnızca JSON'a çevrilir. Örneğin bilet sınırı
   `app/tickets/services.py`'de denetlenir; API o fonksiyonu çağırır.
2. Tüm uç noktalar `/api` öneki altındadır.
3. Hata cevapları tek biçimdedir:
   `{"error": {"code": "<kisa_kod>", "message": "<Türkçe mesaj>"}}`
4. Para tutarları metin olarak gönderilir (`"150.00"`), tarihler ISO 8601 biçimindedir.
5. Yeni bir uç nokta eklenmeden önce `docs/interface-contract.md` güncellenir
   (SM onayı gerekir).

## İlk adım (M-02)

Bu klasörde henüz kod yok. Ekibin ilk işi:

- `app/api/__init__.py` ve `app/api/routes.py`: blueprint `api`, önek `/api`
- `GET /api/health` → `{"status": "ok"}`
- Bilinmeyen `/api/...` adresleri için JSON 404 cevabı
- `app/__init__.py`'ye blueprint kaydı (SM onayı gerekir)
- `tests/integration/test_api.py`

## Testler

| Ne | Nerede | CI'da |
|---|---|---|
| Uç noktalar (Flask `client`) | `tests/integration/test_api.py` | Evet |
| Yardımcı fonksiyonlar | `tests/unit/test_api.py` | Evet |
