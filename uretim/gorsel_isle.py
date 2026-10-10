# -*- coding: utf-8 -*-
"""
HETEGA — Kitap PDF'lerinden görsel bağlama hattı

Girdi : cilt başına PDF (taranmış kitap) + envanter.json (kitap.cilt/kitap.sayfa)
Çıktı : <website>/kutuphane/cilt<N>/s<sayfa>-<n>.jpg   (web için sıkıştırılmış)
        envanter.json gorseller alanları (kaynak='kitap-tarama')
        envanter/gorsel_baglama.json (denetim kaydı / elle override listesi)

Nasıl çalışır:
  1. OFSET KALİBRASYONU: kitap basılı sayfa no'su PDF fiziksel sayfasından farklıdır
     (ön kapak/iç kapak/telif sayfaları). PDF'in metin katmanı varsa basılı sayfa
     numarası otomatik bulunur (--ofset ile elle de verilebilir).
  2. envanter'den (cilt, sayfa) -> nesne listesi çıkar.
  3. Yalnızca gerekli sayfalar render edilir (150 dpi, en çok 1500px, JPEG ~%82).
  4. Bir sayfada birden çok nesne varsa (set kayıtları) aynı sayfa görseli tümüne
     'sayfa_gorseli' güven etiketiyle bağlanır; 2+ görsel varsa ikincisi ARKA YÜZ
     olarak thumb-row'a girer.
  5. Mevcut katalog3 görselleri KORUNUR; yeni görsel eklenir (override edilmez).

Kullanım:
  pip install pymupdf
  python3 gorsel_isle.py --pdf /yol/cilt2.pdf --cilt II [--ofset 12] [--kurulama]
  --kurulama: dosya yazmaz, ne bağlanacağını raporlar (dry-run)
"""
import re, os, sys, json, argparse, collections, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
try:
    import yollar
    ENVF = os.path.join(yollar.ENV, 'envanter.json')
    BAGF = os.path.join(yollar.ENV, 'gorsel_baglama.json')
    HEDEF = os.environ.get('HETEGA_WEBSITE', yollar.WEBSITE)
except ImportError:
    ENVF = os.path.join(HERE, 'envanter.json')
    BAGF = os.path.join(HERE, 'gorsel_baglama.json')
    HEDEF = os.environ.get('HETEGA_WEBSITE', '/home/user/hetega-website')

import pymupdf

MAXPX = 1500        # uzun kenar
DPI = 150
KALITE = 82

# ------------------------------------------------------------------ ofset
def ofset_bul(doc, cilt, ipucu_sayfalar):
    """PDF fiziksel sayfa - basılı sayfa farkını bul.
    Metin katmanından: sayfa köşesinde tek başına duran sayılar aranır."""
    oy = collections.Counter()
    deneme = 0
    for fiz in range(0, min(len(doc), 400)):
        metin = doc[fiz].get_text() or ''
        # köşe satırları: kısa sayı satırları
        for m in re.finditer(r'(?m)^\s*(\d{1,3})\s*$', metin):
            basili = int(m.group(1))
            if 0 < basili < 400:
                oy[fiz - basili] += 1
        deneme += 1
    if not oy:
        return None, 'metin katmanı yok / sayfa numarası bulunamadı'
    (eniyi, adet), = oy.most_common(1)
    guven = adet / max(1, sum(oy.values()))
    return eniyi, 'en güçlü aday %d (destek %d/%d, %.0f%%)' % (eniyi, adet, sum(oy.values()), guven * 100)

def dogrula(doc, ofset, kontroller):
    """kontroller: [(basili_sayfa, beklenen_kelime)] — ofset doğru mu?"""
    sonuc = []
    for basili, beklenen in kontroller:
        fiz = basili + ofset
        if 0 <= fiz < len(doc):
            t = (doc[fiz].get_text() or '').lower()
            ok = beklenen.lower() in t
            sonuc.append((basili, beklenen, ok))
    return sonuc

# ------------------------------------------------------------------ render
def sayfa_render(doc, fiz, hedef_yol):
    page = doc[fiz]
    zoom = DPI / 72.0
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
    if max(pix.width, pix.height) > MAXPX:
        oran = MAXPX / max(pix.width, pix.height)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(DPI / 72.0 * oran,
                                                    DPI / 72.0 * oran), alpha=False)
    os.makedirs(os.path.dirname(hedef_yol), exist_ok=True)
    pix.save(hedef_yol, jpg_quality=KALITE)
    return os.path.getsize(hedef_yol)

# ------------------------------------------------------------------ ana
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pdf', required=True)
    ap.add_argument('--cilt', required=True, help='I|II|III|IV|V')
    ap.add_argument('--ofset', type=int, default=None)
    ap.add_argument('--kurulama', action='store_true', help='dry-run: dosya yazma')
    ap.add_argument('--dogrula', default='', help='"16:planetaryum,43:nisangah" biçimi kontroller')
    a = ap.parse_args()

    env = json.load(open(ENVF, encoding='utf-8'))
    N = env['nesneler']

    # (sayfa) -> nesneler
    sayfa_nesne = collections.defaultdict(list)
    for o in N:
        k = o.get('kitap') or {}
        if k.get('cilt') == a.cilt and k.get('sayfa'):
            sayfa_nesne[int(k['sayfa'])].append(o)
    print('Cilt %s: envanterde %d nesne, %d farklı kitap sayfası'
          % (a.cilt, sum(len(v) for v in sayfa_nesne.values()), len(sayfa_nesne)))

    doc = pymupdf.open(a.pdf)
    print('PDF: %d sayfa, metin katmanı: %s' % (len(doc), 'VAR' if doc[10].get_text().strip() else 'YOK'))

    ofset = a.ofset
    if ofset is None:
        ofset, bilgi = ofset_bul(doc, a.cilt, None)
        print('ofset otomatik: %s (%s)' % (ofset, bilgi))
        if ofset is None:
            print('HATA: ofset bulunamadı; --ofset N ile elle verin '
                  '(PDF\'de kitap s.16 kaçıncı fiziksel sayfaysa N = fiziksel-16).')
            return 2
    if a.dogrula:
        kontroller = []
        for parca in a.dogrula.split(','):
            if ':' in parca:
                s, k = parca.split(':', 1)
                kontroller.append((int(s), k.strip()))
        sonuc = dogrula(doc, ofset, kontroller)
        print('doğrulama:', sonuc)
        if sonuc and not all(x[2] for x in sonuc):
            print('UYARI: doğrulama başarısız — ofseti kontrol edin!')

    # gereken sayfalar (nesnesi olan)
    gereken = sorted(sayfa_nesne)
    print('render edilecek kitap sayfası: %d' % len(gereken))

    kutuphane = os.path.join(HEDEF, 'kutuphane', 'cilt' + {'I':'1','II':'2','III':'3','IV':'4','V':'5'}[a.cilt])
    atamalar = []
    boyut_toplam = 0
    for basili in gereken:
        fiz = basili + ofset
        if not (0 <= fiz < len(doc)):
            print('  ! s.%d -> fiziksel %d aralık dışında' % (basili, fiz)); continue
        dosya = 's%03d.jpg' % basili
        yol = os.path.join(kutuphane, dosya)
        url = '/kutuphane/cilt%s/%s' % ({'I':'1','II':'2','III':'3','IV':'4','V':'5'}[a.cilt], dosya)
        if not a.kurulama:
            boyut_toplam += sayfa_render(doc, fiz, yol)
        for o in sayfa_nesne[basili]:
            coklu = len(sayfa_nesne[basili]) > 1
            atamalar.append({'nesne': o['id'], 'baslik': o['baslik'][:50],
                             'cilt': a.cilt, 'kitap_sayfa': basili, 'pdf_sayfa': fiz,
                             'url': url, 'guven': 'sayfa_paylasimli' if coklu else 'sayfa_birebir',
                             'ayni_sayfadaki_nesne': len(sayfa_nesne[basili])})
            if not a.kurulama:
                g = {'url': url, 'kaynak': 'kitap-tarama',
                     'etiket': 'Kitap taraması: Cilt %s, s.%d%s' % (a.cilt, basili,
                               ' (sayfa %d nesneyi içeriyor)' % len(sayfa_nesne[basili]) if coklu else ''),
                     'atama_guveni': 'sayfa_paylasimli' if coklu else 'sayfa_birebir'}
                if g['url'] not in [x.get('url') for x in o.get('gorseller', [])]:
                    o.setdefault('gorseller', []).append(g)

    if not a.kurulama:
        json.dump(env, open(ENVF, 'w'), ensure_ascii=False, indent=1)
        json.dump({'cilt': a.cilt, 'pdf': os.path.basename(a.pdf), 'ofset': ofset,
                   'tarih': datetime.datetime.now().isoformat(timespec='minutes'),
                   'render_sayfa': len(gereken), 'atama': len(atamalar),
                   'toplam_mb': round(boyut_toplam / 1048576, 1),
                   'atamalar': atamalar},
                  open(BAGF, 'w'), ensure_ascii=False, indent=1)
    print('atama: %d nesne | render: %d sayfa%s'
          % (len(atamalar), len(gereken), ' (dry-run)' if a.kurulama else ' | %.1f MB yazıldı' % (boyut_toplam / 1048576)))
    birebir = sum(1 for x in atamalar if x['guven'] == 'sayfa_birebir')
    print('   birebir sayfa: %d | paylaşımlı sayfa: %d' % (birebir, len(atamalar) - birebir))
    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
