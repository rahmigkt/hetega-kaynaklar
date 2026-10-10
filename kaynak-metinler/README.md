# Kaynak metinler

Bu klasör **boş tutulur**. Fuat Sezgin, *İslam'da Bilim ve Teknik* (Cilt I–V,
İBB Kültür A.Ş. / TÜBA, 2. basım 2008) OCR metinleri telif nedeniyle depoya
**dahil edilmemiştir**.

## Yerel kurulum

OCR metinlerini buraya `ocr/` alt klasörüne koyun:

```
kaynak-metinler/ocr/
  Fuat Sezgin-İslamda Bilim ve Teknik - cilt I_djvu.txt
  Fuat Sezgin-İslamda Bilim ve Teknik - cilt II_djvu.txt
  Fuat Sezgin-İslamda Bilim ve Teknik - cilt III_djvu.txt
  Fuat Sezgin-İslamda Bilim ve Teknik - cilt IV_djvu.txt
  Fuat Sezgin-İslamda Bilim ve Teknik - cilt V_djvu.txt
```

ya da başka bir konumu ortam değişkeniyle gösterin:

```bash
export HETEGA_KITAP_OCR=/yol/ocr
```

Dosya adlarında `cilt <Romen rakamı>` geçmesi yeterlidir; `parse_books.py`
cilt numarasını dosya adından okur.

## OCR hakkında

Metinler DjVu taramasından dönüştürülmüştür ve belirgin gürültü içerir:

- kelimeler arasında **çift boşluk** (`El  tırnağı  formunda`)
- Arapça ayn (ع) harfi `c`, `°` veya `'` olarak okunmuş (`cAbdurrahmân`)
- `ı` / `I` / `1` ve `İ` / `l` karışması (`Kİ. 10` = aslında `K 1.10`)
- satır sonu tireleri (`yüksek¬` + `lik:`)
- **envanter numaraları satıra bölünebiliyor** (`(Envanter No: D` ↵ `1.04 ve D 1.05)`)
- başlık satırları boş satırlarla ayrık, gövde metni bitişik satırlar halinde gelir
  (ayırt etmede kullanılan ana sinyal)

`uretim/parse_books.py` bu desenlerin hepsini ele alır; kalıntı sorunlar
`ara-veri/incelemeye_muhtac.json` içinde insan hakemlemesine bırakılır.

## İngilizce ciltler

Beş cildin İngilizce baskısı PDF olarak ayrıca mevcut ve **görselleri daha iyi**.
Görsel katmanı iyileştirmesi oradan yapılacak (envanteri sağlamlaştırma işi
bittikten sonraki adım).
