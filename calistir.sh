#!/usr/bin/env bash
# HETEGA envanter üretim hattı — baştan sona.
# Kullanım:  HETEGA_KITAP_OCR=/yol/ocr ./calistir.sh
set -euo pipefail
cd "$(dirname "$0")"

if [ -z "${HETEGA_KITAP_OCR:-}" ]; then
  echo "UYARI: HETEGA_KITAP_OCR tanımlı değil; kitap OCR metinleri bulunamayacak."
  echo "       export HETEGA_KITAP_OCR=/yol/ocr   (*_djvu.txt dosyalarının klasörü)"
fi

adim() { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }

adim "1/8 parse_books.py  — kitaptan envanter blokları"
python3 uretim/parse_books.py

adim "2/8 reconcile.py    — kitap × site mutabakatı"
python3 uretim/reconcile.py

adim "3/8 build_envanter.py — kanonik envanter.json"
python3 uretim/build_envanter.py

adim "4/8 uygula_duzeltmeler.py — insan kararları (duzeltmeler.json)"
python3 uretim/uygula_duzeltmeler.py

adim "5/8 alimler.py      — âlim/kurum otorite listesi"
python3 uretim/alimler.py

adim "6/8 assign_images.py — boşta görsel havuzu (öneri üretir)"
python3 uretim/assign_images.py

adim "7/8 export.py       — CSV + koleksiyon ağacı"
python3 uretim/export.py

adim "8/8 sergi_motoru.py — sergi tanımlarını doğrula"
for f in sergiler/*.json; do
  slug=$(basename "$f" .json)
  echo "  · $slug"
  python3 uretim/sergi_motoru.py "$slug" --ozet
done

printf '\n\033[1mBitti.\033[0m envanter/envanter.json güncellendi.\n'
echo "İnsan hakemlemesi döngüsü:"
echo "  1. HETEGA_WEBSITE=/yol/hetega-website python3 uretim/hakem_arayuzu.py   # arayüzü üret"
echo "  2. /calisma/hakemleme/ sayfasında kararları ver, JSON'u indir"
echo "  3. indirilen dosyayı envanter/hakem_kararlari.json olarak koy"
echo "  4. python3 uretim/hakem_uygula.py                                       # envantere işle"
echo ""
echo "Site sayfalarını üretmek için (website checkout'u gerekir):"
echo "  HETEGA_WEBSITE=/yol/hetega-website python3 uretim/site_uret.py"
