# HETEGA — Envanter Sağlamlaştırma Denetim Raporu

**Tarih:** 10 Ekim 2026  
**Kapsam:** `rahmigkt/hetega-website` (canlı yayın) × Fuat Sezgin, *İslam'da Bilim ve Teknik*, Cilt I–V (İBB Kültür A.Ş. / TÜBA, 2. basım 2008)

---

## 1. Özet: elimizde ne var

| Kaynak | İçerik | Durum |
|---|---|---|
| **Kitap (5 cilt OCR)** | 589 envanter bloğu → **672 benzersiz kanonik envanter numarası** | Otorite kabul edilecek kaynak |
| **Canlı site** | 456 yayınlanmış nesne sayfası (`/products/k3-*`) | 410'unda envanter no var, **46'sında yok** |
| **Kanonik birleşim** | **706 müze nesnesi** | Bu raporun çıktısı |
| **Eski katmanlar** | `TAM` (483 kayıt, eski katalog `p###`) + `YENI` (352 "aday künye" `a###`) | **Editoryal/AI üretimi**, kitap otoritesi değil — karışıklığın ana kaynağı |
| **Görsel varlığı** | `katalog2/` 534 + `katalog3/` 534 kitap-figürü görseli, 362 sayfa taraması, 8 `envanter-*.jpg`, 7 kapak | 456 figür atanmış, **~78 figür boşta** |

### Durum dağılımı (706 kanonik nesne)

```
eşleşti        433   kitap + site birbirini doğruluyor
sitede_yok     239   kitapta var, sitede YOK  ← asıl eksik
kitapta_yok     34   sitede var, kitapta doğrulanamıyor  ← şüpheli
```

---

## 2. Envanter numarası şeması (kitaptan çözüldü)

Kitap 13 bölümden oluşuyor; envanter önekleri müze salonlarına karşılık geliyor:

| Önek | Koleksiyon | Kitap bölümü | Kitaptaki nesne |
|---|---|---|---|
| **A** | Astronomi | Cilt II, Bölüm 1 | 98 |
| **B** | Saatler | Cilt III, Bölüm 4 | 33 |
| **C** | Coğrafya ve Seyrüsefer | Cilt III, Bölüm 2–3 | 35 |
| **D** | Tesviye ve Geometri | Cilt III, Bölüm 5 | 28 |
| **E** | Fizik ve Teknik / Optik | Cilt III Böl. 6 + Cilt V Böl. 10 | 31 |
| **F** | Mimari | Cilt V, Bölüm 11 | 8 |
| **G** | Askeri Teknoloji | Cilt V, Bölüm 12 | 31 |
| **H** | Tıp | Cilt IV, Bölüm 7 | 124 |
| **J** | Antik Objeler | Cilt V, Bölüm 13 | 143 |
| **K** | Kimya + Mineraller | Cilt IV, Bölüm 8–9 | 141 |

Hiyerarşi: **Cilt → Bölüm → Alt bölüm → Alt başlık → Eser (Envanter No)**.  
Örn. `A04.16` = Cilt II → Astronomi → Rasathaneler → Merâğa Rasathanesi Aletleri → "V. Hareket Edebilir Nişangâhlı Alet", s. 43.

### Numara biçimleri (hepsi tek şemaya indirgendi)

Kitapta numaralar **9 farklı biçimde** yazılmış; bu, mevcut karışıklığın teknik nedeni:

| Kitaptaki ham biçim | Kanonik | Not |
|---|---|---|
| `A 1.05` | `A01.05` | standart |
| `A. 1.08`, `H. 3.05` | `A01.08`, `H03.05` | harften sonra nokta |
| `d 1.08` | `D01.08` | küçük harf |
| `Kİ. 10` | `K01.10` | OCR: `İ` aslında `1` |
| `F 04` | `F4` | noktasız seri |
| `H 8.01-26` | `H08.01…H08.26` | **aralık → 26 nesne** |
| `J 234-36` | `J234, J235, J236` | kısaltılmış aralık |
| `J 239-58` | `J239…J258` | kısaltılmış aralık → 20 nesne |
| `D 1.32 ve 1.33` | `D01.32, D01.33` | `ve` = **sayma**, aralık değil |
| `H 4.07 ve H 4.01` | `H04.07, H04.01` | sırasız iki ayrı nesne |
| `H 9.01 ila H 9.14` | `H09.01…H09.14` | `ila` = aralık → 14 nesne |
| `H 1.06-1` | `H01.06-1` | **alt-öğe** (üst: `H01.06`) |
| `J 354-1, 354-2, 354-3` | `J354-1…3` | alt-öğe listesi |
| `K 3.27a`, `K 3.33e` | `K03.27A` | mineral örneklerinde harf soneki |
| `E 2.01 1472` | `E02.01` | OCR artığı atıldı |
| `2. 21`, `3.13`, `6.04` | `A02.21`, `B03.13`, `H06.04` | **harf OCR'da düşmüş** → bölüm önekinden tamamlandı |
| `(Envanter No: 15354)` | — | Kahire İslam Sanatları Müzesi'nin numarası, **yok sayıldı** |

> Bu 17 varyant çözülmeden yapılan her eşleştirme yanlış sonuç verir. Nitekim ilk turda "sitede olup kitapta yok" görünen **49 numaranın 15'i** aslında kitapta vardı — sadece farklı yazılmıştı.

---

## 3. Tespit edilen sorunlar

### 3.1 Sitede yayınlanmamış 239 nesne (en büyük eksik)

| Koleksiyon | Eksik | Başlığı kitapta net olan |
|---|---|---|
| Antik Objeler (J) | **79** | 38 |
| Kimya (K) | **75** | 20 |
| Tıp (H) | **48** | 32 |
| Askeri Teknoloji (G) | 16 | 0 |
| Tesviye ve Geometri (D) | 11 | 2 |
| Saatler (B) | 4 | 1 |
| Coğrafya ve Seyrüsefer (C) | 4 | 1 |
| Astronomi (A) | 1 | 1 |
| Fizik ve Teknik (E) | 1 | 0 |
| **Toplam** | **239** | **95** |

**95 nesne hemen eklenebilir durumda** (başlığı kitapta temiz okunuyor). Kalan 144'ün başlığı OCR'da resim altında kaldığı için ya üst-başlıktan türetildi ya da insan düzeltmesi gerekiyor.

### 3.2 Kitapta doğrulanamayan 34 site numarası

Örnekler — bunların **hiçbiri** kitabın OCR metninde geçmiyor:

| No | Sitedeki başlık | Sitenin verdiği kaynak |
|---|---|---|
| `A01.04` | Coronelli'nin Gök Küresi | Cilt II, s. 18 → **o sayfada hiç envanter no yok** |
| `A02.02` | ez-Zerḳâlî'nin Evrensel Diski | Cilt II, s. 118 → yok |
| `A06.04` | Chaucer'a Atfedilen Ekvatoryum | Cilt II, s. 189-191 → yok |
| `C03.02` | Karavela (Gemi Modeli) | Cilt III, s. 54 → yok |
| `D01.01` | Koni Kesiti Pergeli | Cilt III, s. 153 → yok |
| `F4` | Turhan Hatun Hastanesi Maketi | Cilt V, s. 70 → kitapta **F1,F2,F3,F5…F9 var, F4 yok** |
| `G01.01`, `G01.20`, `G02.02`, `G02.22` | Mancınık / Zırhlı araba / Alev püskürtücü | ilgili sayfalarda yok |
| `K01.21`, `K01.23`, `K01.35`, `K01.36`, `K01.69` | Fırın / İmbik / Filtre | kitapta K01.20 ve K01.22 var, aradakiler yok |
| `J233`, `J237` | Altın Terazisi Seti / Ağırlıklar | Cilt V, s. 155-157 → yok |

**İki olası açıklama:** (a) numaralar uydurulmuş/yanlış atanmış, (b) müzede kitapta yer almayan nesneler var. İkincisi mümkün — bu yüzden silmek yerine **bayraklayıp tek tek karara bağlamak** gerekir.

### 3.3 Diğer veri kalitesi sorunları

| Sorun | Adet | Örnek |
|---|---|---|
| Envanter no'su hiç olmayan site kaydı | **46** | Jaipur/Delhi Yantraları, biçimli usturlaplar, mineral örnekleri |
| Başlık kitapta ≠ sitede | **186** | kitap "Nastulus'un Usturlabı" / site başka adlandırma |
| Kategori şeması kitapla uyumsuz | **87** | site `Usturlaplar`'ı ayrı kategori yapmış; kitapta Astronomi'nin alt başlığı |
| Sayfa referansı uyuşmuyor | **22** | `Kaynak: Cilt II, s. 16` ama nesne kitapta s. 17'de |
| **Grup kaydı** (1 sayfa = çok nesne) | **7 sayfa / 67 nesne** | `el-Fustât Buluntusu Aletler` tek sayfada **26 nesne** (H08.01–H08.26); `Kozmetik Alet-Edevat` 20 nesne (J239–J258) |
| Aynı numara iki farklı kayıtta | **2** | `A01.08` → hem "Enlem Ölçüm Aleti" hem "en-Neyrîzî'nin Küresel Usturlabı"; `C03.02` → hem "Karavela" hem "Dāv Gemi Modeli" |
| Numarası çıkarılamayan/şüpheli | **10** | `J 87 1-84` gibi bozuk OCR |

### 3.4 Yapısal / teknik sorunlar

- **Repo'da Astro kaynak kodu YOK** — sadece build çıktısı (dist) commit'lenmiş. 4.110 dosyanın 2.476'sı üretilmiş HTML. Kaynak olmadan değişiklik yapmak her seferinde HTML'i elle düzenlemek anlamına gelir.
- **`index.html` hâlâ "Yapım Aşamasında"** placeholder'ı ve `noindex, nofollow` — katalog dolu ama kök sayfa kapalı.
- **`deneme/` klasörü: 1.990 dosya / 28,6 MB** eski deneme içeriği (`eski-katalog`, `eski-katalog-2`) hâlâ repoda ve yayınlanıyor.
- `kutuphane/` **208 MB** — repo'nun %90'ı. FTP deploy her push'ta bunu yeniden yüklemeye çalışıyor.
- `hetega-kaynaklar` reposu **tamamen boş** (0 commit) — kaynak/veri deposu olarak kullanılabilir.

---

## 4. Önerilen mimari: tek veri kaynağı + sergi motoru

Şu anki model *üretilmiş HTML'i depolamak*. Önerim **veri-merkezli** modele geçmek:

```
                    ┌──────────────────────────────────┐
   KİTAP (Cilt I-V) │  envanter.json  ← TEK DOĞRU KAYNAK │   İngilizce PDF
   OCR + OCR düzeltme│  706 nesne, tam künye, hiyerarşi,  │   (görseller, sonra)
        │           │  kaynakça, bayraklar, karar geçmişi │        │
        └──────────►│                                    │◄───────┘
                    └───────────────┬──────────────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 ▼                  ▼                  ▼
        /envanter (katalog)   /sergiler/<tema>    /calisma (hakemleme)
        koleksiyon + arama    tema = sorgu        kararsız kayıtlar
                              (dinamik sıralama)   için iç arayüz
```

**`envanter.json` şeması** (her nesne için):

```jsonc
{
  "id": "A04.16",                    // kanonik envanter no = birincil anahtar
  "koleksiyon": "Astronomi",
  "hiyerarsi": ["Cilt II","Astronomi","Rasathaneler","Merâğa Rasathanesi Aletleri"],
  "baslik": "V. Hareket Edebilir Nişangâhlı Alet",
  "baslik_kaynak": "site|kitap|insan",   // hangi katman yazdı
  "bilgin": "Müʾeyyededîn el-ʿUrḍî",
  "eser": "Kitâb fī ṣināʿat al-ālāt",    // ← "kitaptaki eserlere kadar inme"
  "donem": "İlhanlı (7./13. yy)",
  "mense": "Merâğa",
  "kitap": {"cilt": "II", "sayfa": 43, "ham_envanter": "A 4.16"},
  "teknik": {"malzeme": ["pirinç","bakır"], "boyutlar": ["Çap: 45 cm"]},
  "gorsel": ["/kutuphane/katalog3/k010-14.jpg"],
  "orijinal": "Orijinal yok (Enstitü modeli)",
  "durum": "yayinda|eksik|incelemede",
  "bayraklar": ["sayfa_uyuşmuyor"],
  "sergi_etiketleri": ["rasathane:meraga","bilgin:el-urdi","tema:bilgi-dolasimi"]
}
```

### Sergi motoru nasıl çalışır

Sergi = **sorgu + sıralama + anlatı**, ayrı bir veri kopyası değil. "Bilginin Dolaşımı" örneği:

```jsonc
{
  "slug": "bilginin-dolasimi",
  "baslik": "Bilginin Dolaşımı",
  "bolumler": [
    { "baslik": "Rasathaneler",
      "sorgu": {"hiyerarsi_icerir": "Rasathaneler"},
      "sirala": "kitap.sayfa" },
    { "baslik": "O Rasathanelerin Âlimleri",
      "kaynak": "onceki_bolumun_bilgin_alani",     // otomatik türetme
      "sirala": "donem" },
    { "baslik": "Eserleri ve Aletleri",
      "sorgu": {"bilgin": "$onceki_bolum"},
      "gorunum": "kaynak_eser_gruplu" }
  ]
}
```

Böylece bir sergi tanımlamak **kod yazmak değil, JSON yazmak** olur; envanter temizlendiği anda tüm sergiler otomatik güncellenir. Aynı mekanizma "Zamanın Ölçümü" (B+D salonları), "Cerrahinin Aletleri" (H), "İslam Kimyasının Laboratuvarı" (K) için de çalışır.

---

## 5. Önerilen iş sırası

| # | İş | Çıktı | Efor |
|---|---|---|---|
| **1** | Kararların verilmesi (aşağıdaki 4 soru) | net kapsam | — |
| **2** | 46 numarasız kaydın eşlenmesi + 34 şüpheli numaranın karara bağlanması | temiz `envanter.json` | orta |
| **3** | 7 grup kaydının alt nesnelere açılması (67 nesne) | +60 sayfa | orta |
| **4** | 95 "hazır" eksik nesnenin eklenmesi | +95 sayfa | orta |
| **5** | Kalan 144 eksik için başlık hakemleme arayüzü (`/calisma/baslik-duzeltme`) | +144 sayfa | yüksek |
| **6** | Kategori şemasını kitap hiyerarşisiyle birleştirme (87 uyumsuzluk) | tutarlı taksonomi | orta |
| **7** | Sergi motoru + ilk sergi: "Bilginin Dolaşımı" | `/sergiler/` | yüksek |
| **8** | `deneme/` temizliği, kök `index.html`, `kutuphane/` optimizasyonu | −28 MB, canlı kök | düşük |
| **9** | İngilizce PDF'lerden görsel iyileştirme | daha iyi görseller | yüksek (sonraya) |

---

## 6. Bu turda üretilen dosyalar

| Dosya | İçerik |
|---|---|
| `inventory/envanter_kanonik.json` | **706 kanonik nesne** — kitap + site birleşimi, bayraklarla |
| `inventory/envanter_kanonik.csv` | aynı verinin Excel'e açılabilir hali (UTF-8 BOM) |
| `inventory/book_blocks.json` | 589 ham kitap bloğu (bağlam metniyle, hakemleme için) |
| `inventory/book_items.json` | 694 kayıt (aralıklar açılmış) |
| `inventory/book_numbers.json` | 672 benzersiz kanonik envanter numarası |
| `inventory/site_numarasiz.json` | 46 numarasız site kaydı + en yakın kitap künyesi |
| `inventory/site_products.json` | siteden kazınan 456 kayıt |
| `inventory/parse_books.py` | kitaptan çıkarım (hiyerarşi + aralık + OCR onarımı) |
| `inventory/numnorm.py` | envanter no normalizasyonu (17 varyant) |
| `inventory/reconcile.py` | kitap × site mutabakatı |
