# Sergiler

Bir sergi burada **tanımdır**, içerik kopyası değil. `envanter.json` güncellendiğinde
bütün sergiler kendiliğinden güncellenir — ayrı bakım gerektirmez.

## Çalıştırma

```bash
python3 uretim/sergi_motoru.py bilginin-dolasimi            # insan-okur özet
python3 uretim/sergi_motoru.py bilginin-dolasimi --ozet     # sadece bölüm başlıkları
python3 uretim/sergi_motoru.py bilginin-dolasimi --json cikti.json
```

## Tanım biçimi

```jsonc
{
  "slug": "bilginin-dolasimi",
  "baslik": "Bilginin Dolaşımı",
  "koleksiyonlar": ["Astronomi"],        // isteğe bağlı ön filtre
  "bolumler": [
    {
      "sira": 1,
      "baslik": "Rasathaneler",
      "giris": "…",                       // bölüm metni
      "sorgu": { "ve": [ { "etiket": "altbolum:rasathaneler" } ] },
      "grupla": "hiyerarsi.alt_baslik",   // gruplama alanı
      "grup_sirasi": ["Rey Rasathanesi", "Merâğa Rasathanesi", …],
      "sirala": ["kitap.sayfa"],
      "gorunum": "gruplu-kart",
      "secilen_alanlar": ["baslik", "gorseller", "kitap.sayfa"]
    },
    {
      "sira": 2,
      "sorgu": { "ve": [
        { "etiket": "altbolum:rasathaneler" },
        { "alan": "bilgin_tur", "esittir": "kişi" }
      ]},
      "grupla": "bilgin_id",
      "grup_baslik_alani": "bilgin_kanonik"
    },
    {
      "sira": 3,
      "sorgu": { "veya": [
        { "ve": [ { "alan": "bilgin_id", "liste": ["$bolum2.bilgin_id"] } ] }
      ]}                                   // ← dinamik referans
    }
  ]
}
```

### Koşullar

| Biçim | Anlamı |
|---|---|
| `{"etiket": "altbolum:rasathaneler"}` | `sergi_etiketleri` içinde geçiyor |
| `{"alan": "bilgin_tur", "esittir": "kişi"}` | alan değeri eşit |
| `{"alan": "bilgin_id", "liste": [...]}` | alan değeri listede |
| `{"alan": "kitap.sayfa", "aralik": [38, 62]}` | sayısal aralık (dahil) |
| `{"alan": "eser", "dolu": true}` | alan boş değil |
| `{"alan": "baslik", "icerir": "usturlap"}` | alt-dizi (harf duyarsız) |
| `{"ve": [...]}` / `{"veya": [...]}` | iç içe birleştirme |
| `{"liste": ["$bolum2.bilgin_id"]}` | **önceki bölümün sonuç kümesinden** alan değerleri |

### Görünüm türleri

`gruplu-kart` · `kisi-listesi` · `kaynak-eser-gruplu` · `zaman-seridi` · `kart`

Bunlar üretim tarafında şablona karşılık gelir; motor yalnızca veriyi çözer.

## Planlanan sergiler

| Slug | Eksen | Kapsam |
|---|---|---|
| `bilginin-dolasimi` | rasathane → âlim → eser | Astronomi, 30 nesne, 8 âlim ✅ taslak hazır |
| `zamanin-olcumu` | saat → geometri aletleri | B (37) + D (33) |
| `cerrahinin-aletleri` | ez-Zehrâvî ve cerrahi aletler | H (126), ez-Zehrâvî 45 nesne |
| `islam-kimyasinin-laboratuvari` | er-Râzî → laboratuvar araçları → mineraller | K (156) |
| `denizde-yon-bulmak` | pusula → harita → denizci âlimler | C (39), İbn Mācid, Pîrî Reʾīs |
| `kagit-uzerindeki-evren` | yazma eser → alet rekonstrüksiyonu | `yazma_kaynaklar` üzerinden |

Yeni sergi eklemek için: `sergiler/<slug>.json` yazın, `./calistir.sh` doğrulasın.
