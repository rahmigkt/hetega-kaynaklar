# hetega-kaynaklar

**HETEGA müze envanterinin tek doğru kaynağı.**

Prof. Dr. Fuat Sezgin'in *İslam'da Bilim ve Teknik* adlı 5 ciltlik eserinden çıkarılan
müze nesnesi kayıtları, [hetega.com](https://hetega.com) canlı kataloğuyla mutabakatı
yapılmış halde burada tutulur. `hetega-website` reposu bu veriden **üretilen çıktıdır**;
içerik burada düzenlenir, site orada yayınlanır.

```
envanter/envanter.json   ←  TEK DOĞRU KAYNAK (745 nesne)
        │
        ├── hetega-website   /products/* sayfaları, koleksiyonlar, arama
        └── sergiler/*       tema bazlı dinamik sergiler
```

---

## Depo yerleşimi

| Dizin | İçerik |
|---|---|
| `envanter/` | **Nihai veri.** `envanter.json` (745 nesne), `alimler.json` (96 âlim + 23 kurum + 11 yazma), `envanter.csv` (Excel görünümü), `koleksiyon_agaci.json`, `sema/nesne.schema.json` |
| `uretim/` | Üretim hattı betikleri. `calistir.sh` ile sırayla çalışır |
| `ara-veri/` | Ara çıktılar: kitaptan çıkarılan ham bloklar, site kazıntısı, mutabakat raporu |
| `sergiler/` | Sergi **tanımları** (JSON). İçerik kopyası değil, sorgu |
| `raporlar/` | Denetim raporları |
| `kaynak-metinler/` | Kitap OCR metinleri için yer tutucu — **telif nedeniyle depoya konmaz** |

---

## Üretim hattı

```bash
# 1) kitap OCR metinlerinin yerini belirt (telif nedeniyle depoda değil)
export HETEGA_KITAP_OCR=/yol/ocr           # *_djvu.txt dosyalarının klasörü

# 2) tüm hattı çalıştır
./calistir.sh
```

Hat şu adımlardan oluşur:

| # | Betik | Girdi | Çıktı |
|---|---|---|---|
| 1 | `numnorm.py` | — | Envanter no normalizasyonu (17 yazım varyantı → tek şema) |
| 2 | `parse_books.py` | OCR metinleri | `ara-veri/book_blocks.json` — 589 blok, 672 benzersiz numara |
| 3 | `reconcile.py` | kitap + site | `ara-veri/envanter_kanonik.json` — mutabakat ve bayraklar |
| 4 | `build_envanter.py` | yukarıdakiler | **`envanter/envanter.json`** — 747 kanonik nesne |
| 4b | `uygula_duzeltmeler.py` | envanter + `duzeltmeler.json` | insan kararları uygulanmış envanter (745 nesne) |
| 5 | `alimler.py` | envanter | `envanter/alimler.json` + nesnelere `bilgin_id` |
| 6 | `assign_images.py` | envanter + görsel havuzu | `envanter/gorsel_atama_onerileri.json` *(öneri; envanteri değiştirmez)* |
| 7 | `export.py` | envanter | `envanter/envanter.csv`, `koleksiyon_agaci.json` |
| 7b | `site_uret.py` | envanter + website checkout | yeni ürün sayfaları + set bölme, index/koleksiyon/sitemap (idempotent, manifest'li) |
| 7c | `sergi_sayfa.py` | envanter + sergi tanımı | `/sergiler/<slug>/` sayfaları + dizin |
| 8 | `sergi_motoru.py` | envanter + sergi tanımı | çözümlenmiş sergi |
| H1 | `hakem_arayuzu.py` | envanter + kitap blokları | `/calisma/hakemleme/` — 226 kayıt için karar arayüzü |
| G1 | `gorsel_isle.py` | cilt PDF'leri + envanter | `kutuphane/ciltN/sXXX.jpg` + nesnelere görsel bağlama (ofset otomatik) |
| H2 | `hakem_uygula.py` | `hakem_kararlari.json` | kararlar envantere işlenir |

Site kazıntısını tazelemek için (`ara-veri/site_products.json`) `hetega-website`
reposunun yerel kopyası gerekir: `export HETEGA_WEBSITE=/yol/hetega-website`.

---

## Envanter numarası şeması

Kanonik biçim: `<HARF><2 hane grup>.<2 hane sıra>` → `A04.16`  
Alt-öğe: `H01.06-1` · Sonek varyantı: `C01.18A` · Noktasız seri: `J224`, `F4`

| Önek | Koleksiyon | Kitap bölümü | Nesne |
|---|---|---|---|
| A | Astronomi | Cilt II, Bölüm 1 | 123 |
| B | Saatler | Cilt III, Bölüm 4 | 37 |
| C | Coğrafya ve Seyrüsefer | Cilt III, Bölüm 2–3 | 39 |
| D | Tesviye ve Geometri | Cilt III, Bölüm 5 | 33 |
| E | Fizik ve Teknik / Optik | Cilt III Böl. 6, Cilt V Böl. 10 | 34 |
| F | Mimari | Cilt V, Bölüm 11 | 9 |
| G | Askeri Teknoloji | Cilt V, Bölüm 12 | 37 |
| H | Tıp | Cilt IV, Bölüm 7 | 126 |
| J | Antik Objeler | Cilt V, Bölüm 13 | 146 |
| K | Kimya + Mineraller | Cilt IV, Bölüm 8–9 | 156 |

Kitapta numaralar **17 farklı biçimde** yazılmıştır (`A. 1.08`, `d 1.08`, `Kİ. 10`,
`H 8.01-26`, `J 239-58`, `D 1.32 ve 1.33`, `H 9.01 ila H 9.14`, `H 1.06-1`,
`K 3.27a`, `E 2.01 1472`…). `numnorm.py` bunların hepsini tek şemaya indirger;
bu yapılmadan yapılan her eşleştirme yanlış sonuç verir.

---

## Hakemleme döngüsü (insan kararı gerektiren kayıtlar)

Bazı kayıtlar OCR'dan çözülemez ya da **zaten müze nesnesi değildir** (bir aletin
parçası, bölüm başlığı, yazma çizimi…). Bunlar zorla eşleştirilmez; hakem karar verir:

```bash
HETEGA_WEBSITE=/yol/hetega-website python3 uretim/hakem_arayuzu.py   # sayfayı üret
# tarayıcıda /calisma/hakemleme/ -> kararları ver -> "Kararları indir (JSON)"
cp ~/Downloads/hakem-kararlari-*.json envanter/hakem_kararlari.json
python3 uretim/hakem_uygula.py                                        # envantere işle
```

| Sekme | Kayıt | Kararlar |
|---|---|---|
| 1 | başlık bekleyen 153 kitap kaydı | **başlık yaz** · **nesne değil** (parça/bölüm/kavram/çizim/grup) · mükerrer · atla |
| 2 | numarasız 40 site sayfası | **numara ata** (aynı sayfadaki adaylar listelenir, çoklu seçim) · nesne değil · numarasız kalsın |
| 3 | kitapta doğrulanamayan 33 numara | müzede var · numarayı düzelt · mükerrer · yayından kaldır |

Kararlar `hakem` iziyle kayda yazılır (idempotent), kapsam dışına alınanlar
`yayin.durum='kapsam_disi'` + `kayit_tipi` alır ve site üretiminde elenir.

## Görsel bağlama (kitap PDF'lerinden)

```bash
pip install pymupdf
python3 uretim/gorsel_isle.py --pdf /yol/cilt2.pdf --cilt II --dogrula "16:planetaryum,43:nişangâh"
```

* **Ofset otomatik**: basılı sayfa no ≠ PDF fiziksel sayfa; metin katmanından
  kalibrasyon bulunur (`--ofset N` ile elle de verilebilir), `--dogrula` ile
  anahtar kelimelerden teyit edilir.
* Yalnızca **nesnesi olan sayfalar** render edilir (150 dpi, ≤1500 px, JPEG ~%82).
* Aynı sayfada birden çok nesne varsa (set kayıtları) görsel hepsine
  `sayfa_paylasimli` güven etiketiyle bağlanır.
* Mevcut `katalog3` görselleri korunur; tarama **eklenir** (thumb-row'da arka yüz).
* Tüm atamalar `envanter/gorsel_baglama.json`'a yazılır — elle override denetimi buradan.
* PDF'ler teliflidir: `hetega-gorseller` (private) reposunda tutulur, bu depoya konmaz.

## Sergi motoru

Bir sergi **tanımdır**, içerik kopyası değil. `sergiler/<slug>.json` içinde
bölümler, sorgular ve sıralama anahtarları yazılır; `sergi_motoru.py` bunları
`envanter.json`'a karşı çözer. Envanter güncellenince tüm sergiler kendiliğinden güncellenir.

```bash
python3 uretim/sergi_motoru.py bilginin-dolasimi          # insan-okur özet
python3 uretim/sergi_motoru.py bilginin-dolasimi --json /tmp/cikti.json
```

**"Bilginin Dolaşımı"** örneği gerçek veriyle şu sonucu verir:

| Bölüm | Sorgu | Sonuç |
|---|---|---|
| 1. Rasathaneler | `etiket: altbolum:rasathaneler` | 30 nesne, 8 rasathaneye gruplu |
| 2. O Rasathanelerin Âlimleri | aynı küme + `bilgin_tur: kişi` | 28 nesne, 8 âlime gruplu (el-ʿUrḍî 12, Tycho Brahe 7, Taḳıyyeddîn 3, Jai Singh 2, el-Ḫucendî, İbn Sînâ, Uluğ Bey, Batlamyus) |
| 3. Eserleri ve Aletleri | `$bolum2.bilgin_id` (dinamik referans) | 32 nesne |
| 4. Ağın Avrupa Ucu | `bilgin_id ∈ {tycho, munster, schoner, campano, chaucer, coronelli}` | 15 nesne |

Aynı mekanizmayla kurulabilecek diğer sergiler: **Zamanın Ölçümü** (B+D salonları),
**Cerrahinin Aletleri** (H, ez-Zehrâvî 45 nesne), **İslam Kimyasının Laboratuvarı** (K),
**Denizde Yön Bulmak** (C, İbn Mācid + Pîrî Reʾīs).

---

## Veri kalitesi durumu (10 Eki 2026)

```
756 kanonik nesne
  380  yayında                     kitap + site birbirini doğruluyor
  147  üretildi (push bekliyor)    79 bağımsız + 63 set üyesi + 5 yeni = envanter-v1 dalında
  157  eksik_baslik_bekliyor       hakemleme arayüzünde sırada
  0  set_üyesi_bölünecek         (bölündü — manifest'e işlendi)
  40  yayında_numarasız           hakemlemede 2. sekme
  32  yayında_doğrulanmadı        hakemlemede 3. sekme
```

Ayrıntı: [`raporlar/ENVANTER-DENETIM-RAPORU.md`](raporlar/ENVANTER-DENETIM-RAPORU.md)

### Bilinen zayıf alanlar

- **`eser` alanı güvenilir değil.** Kitaptan otomatik çıkarım ~%27 doğrulukta;
  "kitab", "birbirler", "altıdabir" gibi çöp değerler üretiyor. Sergi motorunun
  3. bölümü bu yüzden zayıf gruplanıyor. **Eser/yazma katmanı ayrıca
  çalışılmalı** — `envanter/alimler.json` içindeki 11 yazma kaynak iyi bir başlangıç.
- **`başlık_kitap_kalite` = `üstbaşlık` olan 140 kayıt** gerçek nesne adını değil,
  kitabın bölüm başlığını taşır. İnsan hakemlemesi gerekiyor (`ara-veri/incelemeye_muhtac.json`).
- **92 "eklenmeye hazır" nesnenin görseli yok.** `katalog3` havuzunun 534 figürü
  mevcut 456 sayfaya atanmış; boşta kalan 81 figürün sayfa eşleşmesiyle yalnızca
  9'una güvenli aday bulunabildi (`envanter/gorsel_atama_onerileri.json`).
  Kalıcı çözüm: İngilizce ciltlerin PDF'lerindeki görseller.
- **Kitap sayfası takibi ~%95 doğru.** 378 çıpanın 4'ünde sıra sapması var;
  `sayfa_uyuşmuyor` bayrağıyla işaretli 24 kayıt incelenmeli.

---

## Kararlar

1. Kitapta doğrulanamayan envanter numaraları **silinmez**; `yayında_doğrulanmadı`
   durumu ve `kitapta_doğrulanamadı` bayrağıyla yayında kalır. Müzede kitapta
   yer almayan nesneler olabilir.
2. Kitapta tek künyede geçen nesne setleri (`H 8.01-26` = 26 alet) **ayrı
   kayıtlara bölünür**; set bağlığı `set` alanında korunur.
3. Koleksiyon ataması **envanter önekinden** yapılır. Sitenin eski kategori şeması
   (`Usturlaplar`'ı ayrı kategori sayması gibi) `site_kategori` alanında not olarak saklanır.
4. `envanter.json` elle düzenlenmez. İnsan kararları `envanter/duzeltmeler.json`
   yama dosyasına yazılır; `uygula_duzeltmeler.py` bunları her yeniden üretimde
   otomatik uygular (başlık düzeltmesi, numara atama/birleştirme, başlık düşürme).

---

## Telif

Kitap metinleri (Fuat Sezgin, *İslam'da Bilim ve Teknik*, İBB Kültür A.Ş. / TÜBA)
**bu depoya dahil edilmemiştir.** Yalnızca kısa künye alıntıları (başlık, envanter
no, sayfa, malzeme/ölçü) türetilmiş veri olarak tutulur. OCR metinlerini
`kaynak-metinler/ocr/` altına yerel olarak koyun veya `HETEGA_KITAP_OCR` ile gösterin.
