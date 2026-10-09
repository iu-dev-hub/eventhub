# İletişim Rehberi

**Herkes için: Kiminle, nerede, nasıl konuşulur?**

Çok ekipli projelerde sorunların çoğu teknik değil, iletişimseldir: Bilgi yanlış yere
yazılır, kaybolur veya hiç paylaşılmaz. Bu rehber, bilginin **doğru yerde ve kalıcı**
olmasını sağlar.

## 1. Hangi bilgi nereye?

| Konu | Kanal | Neden orada? |
|---|---|---|
| Bir hikâye, görev veya hata hakkında her şey | **Taiga** (ilgili kaydın yorumları) | İş ile ilgili bilgi işin yanında durur |
| Kod hakkında soru, öneri, inceleme | **GitHub PR** yorumları | Kod satırına bağlı kalır |
| Asenkron günlük toplantı | **Discussions → Günlük** (ekip başlığı) | Herkes ne yapıldığını görür |
| Ekipler arası kararlar, bağımlılıklar | **Discussions → Scrum of Scrums** | Tüm ekipleri bağlar |
| Teknik soru, kurulum sorunu | **Discussions → Soru-Cevap** | Başkası da aynı sorunu yaşıyor olabilir |
| Ders ve öğretim üyesi duyuruları | **Discussions → Duyurular**, Classroom | Resmî kaynak |
| Müşteriye soru | **Yalnızca ekibinizin PO'su aracılığıyla** | Müşteri tek muhatap ister |
| Hızlı, günlük konuşmalar | Ders saati, yüz yüze | Ama **kararı yazıya dökün** |

> **Altın kural:** Yazılmayan karar alınmamış sayılır. Yüz yüze veya mesajlaşma
> uygulamasında konuştuğunuz önemli bir kararı ilgili Taiga kaydına veya Discussions'a yazın.

Mesajlaşma uygulamaları (WhatsApp vb.) kullanabilirsiniz, ama oradaki bilgi
**kaybolur ve değerlendirmede görünmez.** Kararları her zaman yukarıdaki kanallara taşıyın.

## 2. İyi bir soru nasıl sorulur?

Kötü:

> "Testler çalışmıyor, yardım edin."

İyi:

> "`pytest tests/integration` çalıştırınca `test_tickets_page_loads` 404 veriyor.
> `app/__init__.py`'de `tickets_bp`'yi kaydettim, menü bağlantısı da çalışıyor.
> Hata mesajı aşağıda. Blueprint'in url_prefix'i yanlış olabilir mi?
> ```
> <hata mesajının tamamı, metin olarak>
> ```"

**İyi sorunun parçaları:**

1. **Ne yapmaya çalışıyorum?**
2. **Ne oldu?** (Hata mesajı **metin olarak**, ekran görüntüsü değil)
3. **Ne denedim?**
4. **Tahminim ne?**

Sorunuzu kendiniz çözerseniz, çözümü de yazın. Bir sonraki kişi teşekkür edecek.

## 3. Yanıt süreleri

| Ne? | Beklenen yanıt süresi |
|---|---|
| PR inceleme isteği | Aynı gün, en geç **24 saat** |
| Taiga'da size atanan soru | **24 saat** |
| Discussions'ta ekip arkadaşınızın engeli | **24 saat** |
| Müşteriye iletilen soru (PO aracılığıyla) | Bir sonraki uygulama dersine kadar |
| Hafta sonu ve tatil | Yanıt beklenmez |

Bir işe yetişemeyecekseniz **önceden** haber verin. "Yetişmiyor" demek ayıp değil;
son anda sessizce yetiştirememek ekibin tamamına zarar verir.

## 4. Sorun yükseltme (eskalasyon) yolu

Bir engelle karşılaştığınızda şu sırayı izleyin:

```text
1. Kendiniz deneyin (en fazla 30 dakika)
2. Ekip arkadaşınıza sorun
3. Scrum Master'a engel olarak bildirin (Discussions günlüğü veya derste)
4. Başka bir ekiple ilgiliyse → SM, Scrum of Scrums'ta gündeme getirir
5. Çözülemezse → SM, öğretim üyesine iletir
```

Ürünle ilgili belirsizlik (kural ne diyor?) için yol farklıdır:
**Geliştirici/Testçi → PO → Müşteri (öğretim üyesi)**.

## 5. Geri bildirim vermek ve almak

Kod incelemesi, retrospektif ve akran değerlendirmesi geri bildirim gerektirir.

**Verirken:**

- **Davranışa ve işe odaklanın**, kişiye değil: "Bu PR'da test yok" — "Sen hiç test yazmıyorsun" değil.
- **Somut olun:** "Mesaj kabul kriteriyle aynı değil: 'Kontenjan dolu.' yerine 'Kontenjan doldu' yazılmış."
- **İyi olanı da söyleyin.**
- **Öneriyle bitirin:** "Bir dahaki sefere PR'ı açmadan önce Files changed'e bakmak işe yarayabilir."

**Alırken:**

- Savunmaya geçmeden önce **anlamaya** çalışın: "Biraz daha açar mısın?"
- Katılmıyorsanız gerekçenizi açıklayın; karar verilemiyorsa SM'ye veya PO'ya taşıyın.
- Teşekkür edin. Birinin vaktini ayırıp kodunuzu okuması bir iyiliktir.

## 6. Dil

| Nerede? | Dil |
|---|---|
| Kod, dosya adı, dal, commit mesajı, PR başlığı | **İngilizce** |
| PR açıklaması, inceleme yorumları | Türkçe (veya İngilizce) |
| Taiga, Discussions, belgeler | Türkçe |
| Kullanıcı arayüzü | Türkçe |

## 7. Ekip çalışma anlaşması

Her ekip ilk sprintte kısa bir çalışma anlaşması yapar ve Taiga Wiki'deki ekip
sayfasına yazar. Örnek:

```text
Ekip: team-tickets — Çalışma Anlaşması

- PR incelemelerini 24 saat içinde yaparız.
- Derse gelemeyecek olan, en geç bir gün önce ekibe haber verir.
- Günlüğe haftada en az 2 kez yazarız (Pazartesi ve Perşembe).
- Takıldığımızda 30 dakikadan fazla tek başımıza uğraşmayız, sorarız.
- Kararları Taiga'ya yazarız; mesajlaşma grubunda kalan karar geçersizdir.
- Birbirimizin kodunu eleştiririz, birbirimizi değil.
```

Anlaşma retrospektiflerde gözden geçirilir ve gerekirse güncellenir.
