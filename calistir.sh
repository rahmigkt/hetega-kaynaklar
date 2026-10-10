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

adim "1/7 parse_books.py  — kitaptan envanter blokları"
python3 uretim/parse_books.py

adim "2/7 reconcile.py    — kitap × site mutabakatı"
python3 uretim/reconcile.py

adim "3/7 build_envanter.py — kanonik envanter.json"
python3 uretim/build_envanter.py

adim "4/7 alimler.py      — âlim/kurum otorite listesi"
python3 uretim/alimler.py

adim "5/7 assign_images.py — boşta görsel havuzu (öneri üretir)"
python3 uretim/assign_images.py

adim "6/7 export.py       — CSV + koleksiyon ağacı"
python3 uretim/export.py

adim "7/7 sergi_motoru.py — sergi tanımlarını doğrula"
for f in sergiler/*.json; do
  slug=$(basename "$f" .json)
  echo "  · $slug"
  python3 uretim/sergi_motoru.py "$slug" --ozet
done

printf '\n\033[1mBitti.\033[0m envanter/envanter.json güncellendi.\n'
