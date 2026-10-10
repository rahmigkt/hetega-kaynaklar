# Site Kurgu Düzeltmeleri — 10 Ekim 2026

`hetega-website` @ `envanter-v1`, commit `b5f98f8` (638 dosya).
**Tasarım değişmedi** — yalnızca kurgu/veri tutarlılığı düzeltildi.

## Tespit edilen sorunlar

| # | Sorun | Etki |
|---|---|---|
| 1 | Kök `/` "Yapım Aşamasında" placeholder'ı (`noindex`); gerçek giriş içeriği iç taslak sayfada (`/calisma-tam/`, o da `noindex`) | Fiili anasayfa aramalara tamamen kapalı; marka linki 637 sayfada taslağa gidiyor |
| 2 | Bayat + çelişkili sayaçlar: taslak "483 eser, 11 koleksiyon"; landing'ler eski TAM(483) kataloğu sayıları (Astronomi 109, Tıp 30, Kimya 57…) — kendi `/tumu/` sayfalarıyla bile tutarsız | Kullanıcı aynı koleksiyon için sayfadan sayfaya değişen sayılar görüyordu |
| 3 | `/#koleksiyonlar` çapası hiçbir sayfada tanımsız | Nav'daki "Koleksiyonlar" linki ölü |
| 4 | Antik Objeler (146 nesne — envanterin en büyük 2. koleksiyonu) kurguda yok | Kök grid'de kartı yok, landing sayfası yok |
| 5 | Eski iç analiz sayfaları (`calisma/sayfa-karsilastirma`, `belirsiz-eslesmeler`) Eylül temizliğinde silinen eski katalog slug'larına link veriyor (225 kırık) | İç sayfalar; kamusal etkisi yok ama yanıltıcı |

## Yapılan düzeltmeler

1. **`index.html` = calisma-tam'ın güncellenmiş hali** (birebir aynı tasarım):
   `603 eser · 12 koleksiyon`, `noindex` kaldırıldı, koleksiyonlar bölümüne
   `id="koleksiyonlar"` eklendi, nadide kart linkleri doğrulandı (3/3 geçerli).
2. **Marka linki** 637 dosyada `/calisma-tam/` → `/`. (Taslak arşiv olarak duruyor.)
3. **Landing sayaçları** 11 koleksiyonda gerçek `/tumu/` kart sayısına sabitlendi:
   Astronomi 109→72, Tıp 30→107, Kimya 57→96, Coğrafya 51→42, Fizik 53→66,
   Saatler 36→40, Askeri 29→23, Tesviye 27→21, Optik 11→8, Usturlaplar 71→45, Mimari 9 (aynı).
4. **Antik Objeler koleksiyonu**: kök grid'ine kart (109 eser) +
   `/koleksiyonlar/antik-objeler/` landing (astronomi şablonundan; öne çıkanlar
   J224 havan, J233 altın terazisi, J357-1 Lobmeyr vazoları, J239 kozmetik seti).
5. **Arşiv notu**: iki eski iç analiz sayfasına "Eylül 2026 anlık görüntüsü,
   bağlantılar çalışmayabilir" bandı + güncel `/calisma/hakemleme/` linki.

## Doğrulama

- Link QA (tüm ağaç, `_astro` hariç): kamusal sayfalarda **0 kırık**; kalan 225 kırık
  yalnızca arşiv notu eklenen iki iç sayfada (bilinçli, belgelendi).
- Sayaç zinciri tutarlı: kök(603/12) → koleksiyon kartı(109) → landing(109) → tumu(109).

## Bilinen sınır (sonraki iş)

Kategori taksonomisi hâlâ ikili: sitenin eski şeması (Usturlaplar ve Optik ayrı
kategori) ile kitap önek şeması (A…K) birlikte yaşıyor; ~35 Antik Objeler kaydı hem
eski kategori sayfasında hem antik-objeler/tumu'da görünüyor (çift sayım ~14).
Kalıcı çözüm, hakemleme sonrası tek taksonomiye geçiş (envanter.json'da
`kategori_uyuşmuyor` bayraklı 87+ kayıt).

## Tekrar çalıştırma

`uretim/site_yapi_duzelt.py` bu düzeltmenin üretecidir (landing sayaçları +
antik landing idempotent kısımlar içerir; kök index üretimi calisma-tam'a dayanır).
