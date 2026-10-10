# -*- coding: utf-8 -*-
"""
HETEGA — Sergi Motoru

Bir sergi TANIM'dır (JSON), içerik kopyası değil. Motor tanımı envanter.json'a
karşı çözer ve bölümleri sıralı nesne listelerine dönüştürür. Envanter
güncellendiğinde bütün sergiler kendiliğinden güncellenir.

Desteklenen sorgu dili:
  {"ve":   [koşul, …]}        tümü sağlanmalı
  {"veya": [koşul, …]}        biri sağlanmalı
  koşul:
    {"etiket": "altbolum:rasathaneler"}       sergi_etiketleri içinde geçmeli
    {"alan": "bilgin_tur", "esittir": "kişi"}  alan değeri eşit olmalı
    {"alan": "bilgin_id", "liste": [...]}      alan değeri listede olmalı
    {"alan": "kitap.sayfa", "aralik": [38,62]} sayısal aralık (dahil)
    {"alan": "...", "dolu": true}              alan boş olmamalı
  dinamik referans:
    {"liste": ["$bolum2.bilgin_id"]}  -> 2. bölümün sonuç kümesinden alan değerleri

Kullanım:
    python3 sergi_motoru.py bilginin-dolasimi [--json çıktı.json]
"""
import re, os, json, sys, argparse, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
ENV  = os.path.join(ROOT, 'envanter', 'envanter.json')
SERGI_DIR = os.path.join(ROOT, 'sergiler')


# ------------------------------------------------------------------ yardımcılar
def alan_get(o, yol):
    cur = o
    for p in yol.split('.'):
        if isinstance(cur, dict):
            cur = cur.get(p)
        else:
            return None
        if cur is None:
            return None
    return cur


def bos_mu(v):
    if v is None:
        return True
    if isinstance(v, str):
        return not v.strip()
    if isinstance(v, (list, dict)):
        return not v
    return False


def karsilastir(v):
    """Sıralama anahtarı: sayısal alanları sayıya, metni katlanmış biçime çevirir."""
    if isinstance(v, (int, float)):
        return (0, v, '')
    if v is None or v == '':
        return (2, 0, '')
    return (1, 0, str(v))


# ------------------------------------------------------------------ sorgu
def kosul_uyar(o, k, baglam):
    if 'etiket' in k or 'etikel' in k:
        et = k.get('etiket') or k.get('etikel')
        return et in (o.get('sergi_etiketleri') or [])
    if 'alan' in k:
        v = alan_get(o, k['alan'])
        if 'esittir' in k:
            return v == k['esittir']
        if 'esit_degil' in k:
            return v != k['esit_degil']
        if 'liste' in k:
            liste = k['liste']
            if liste and isinstance(liste[0], str) and liste[0].startswith('$'):
                liste = baglam.get(liste[0], [])
            return v in liste
        if 'aralik' in k:
            lo, hi = k['aralik']
            try:
                return v is not None and lo <= float(v) <= hi
            except (TypeError, ValueError):
                return False
        if 'dolu' in k:
            return (not bos_mu(v)) if k['dolu'] else bos_mu(v)
        if 'icerir' in k:
            return isinstance(v, str) and k['icerir'].lower() in v.lower()
    return False


def _alt(o, x, baglam):
    """İç içe koşul: 've'/'veya' içeriyorsa özyinele, değilse düz koşul."""
    if 've' in x or 'veya' in x:
        return sorgu_uyar(o, x, baglam)
    return kosul_uyar(o, x, baglam)


def sorgu_uyar(o, s, baglam):
    if not s:
        return True
    if 've' in s:
        return all(_alt(o, x, baglam) for x in s['ve'])
    if 'veya' in s:
        return any(_alt(o, x, baglam) for x in s['veya'])
    if 'tek' in s:
        return kosul_uyar(o, s['tek'], baglam)
    return kosul_uyar(o, s, baglam)


def sirala(nesneler, anahtarlar):
    if not anahtarlar:
        return nesneler
    return sorted(nesneler, key=lambda o: tuple(
        karsilastir(alan_get(o, a)) for a in anahtarlar))


def grupla(nesneler, alan, bolum=None):
    """Alan değerine göre grupla; grup_sirasi verildiyse o sırayı, kalanları
    alfabetik olarak sona ekle."""
    g = collections.OrderedDict()
    for o in nesneler:
        k = alan_get(o, alan) if alan else ''
        k = k or '(diğer)'
        g.setdefault(k, []).append(o)
    if bolum and bolum.get('grup_sirasi'):
        istenen = bolum['grup_sirasi']
        sirali = collections.OrderedDict()
        for ad in istenen:
            if ad in g:
                sirali[ad] = g.pop(ad)
        for ad in sorted(g):
            sirali[ad] = g[ad]
        return sirali
    return collections.OrderedDict(sorted(g.items(), key=lambda x: (-len(x[1]), x[0])))


# ------------------------------------------------------------------ çözümleme
def coz(sergi, envanter):
    nesneler = envanter['nesneler']
    alimler = {a['id']: a for a in envanter.get('alimler', [])}
    koleksiyonlar = sergi.get('koleksiyonlar')
    if koleksiyonlar:
        nesneler = [o for o in nesneler if o.get('koleksiyon') in koleksiyonlar]

    cikti = {
        'slug': sergi['slug'], 'baslik': sergi['baslik'],
        'alt_baslik': sergi.get('alt_baslik', ''),
        'aciklama': sergi.get('aciklama', ''),
        'kapak_gorsel': sergi.get('kapak_gorsel'),
        'sure_dk': sergi.get('sure_dk'),
        'bolumler': [],
    }
    baglam = {}
    onceki_bolumler = {}

    for b in sorted(sergi.get('bolumler', []), key=lambda x: x.get('sira', 0)):
        secim = [o for o in nesneler if sorgu_uyar(o, b.get('sorgu'), baglam)]
        secim = sirala(secim, b.get('sirala'))

        # bağlam: bu bölümün alan değerlerini sonraki bölümlere aç
        bkey = 'bolum%d' % b.get('sira', 0)
        onceki_bolumler[bkey] = secim
        for alan in ('bilgin_id', 'eser', 'koleksiyon', 'id', 'mense', 'donem'):
            baglam['$%s.%s' % (bkey, alan)] = sorted(
                {str(alan_get(o, alan)) for o in secim
                 if not bos_mu(alan_get(o, alan))})
        # bir önceki bölüm referansı
        if b.get('sira', 0) > 1:
            pk = 'bolum%d' % (b.get('sira') - 1)
            for alan in ('bilgin_id', 'eser', 'id'):
                baglam.setdefault('$%s.%s' % (pk, alan),
                                  baglam.get('$%s.%s' % (pk, alan), []))

        parca = {'sira': b.get('sira'), 'baslik': b['baslik'],
                 'giris': b.get('giris', ''), 'gorunum': b.get('gorunum', 'kart'),
                 'nesne_sayisi': len(secim)}

        if b.get('grupla'):
            gruplar = grupla(secim, b['grupla'], b)
            parca['gruplar'] = []
            for ad, uyeler in gruplar.items():
                bilgi = alimler.get(ad)
                baslik = alan_get(uyeler[0], b['grup_baslik_alani']) if b.get('grup_baslik_alani') else ad
                parca['gruplar'].append({
                    'anahtar': ad,
                    'baslik': baslik or ad,
                    'alt_baslik': (bilgi or {}).get('donem', ''),
                    'alan': (bilgi or {}).get('alan', ''),
                    'nesne_sayisi': len(uyeler),
                    'nesneler': [ozet(o, b.get('secilen_alanlar')) for o in uyeler],
                })
            parca['nesne_sayisi'] = len(secim)
        else:
            parca['nesneler'] = [ozet(o, b.get('secilen_alanlar')) for o in secim]

        if b.get('not'):
            parca['not'] = b['not']
        cikti['bolumler'].append(parca)

    cikti['toplam_nesne'] = sum(x['nesne_sayisi'] for x in cikti['bolumler'])
    return cikti


def ozet(o, alanlar):
    if not alanlar:
        alanlar = ['id', 'envanter_gosterim', 'baslik', 'koleksiyon',
                   'bilgin_kanonik', 'donem', 'yayin.durum', 'gorseller']
    out = {}
    for a in alanlar:
        out[a] = alan_get(o, a)
    out['_id'] = o.get('id')
    return out


# ------------------------------------------------------------------ CLI
def main():
    ap = argparse.ArgumentParser(description='HETEGA sergi motoru')
    ap.add_argument('sergi', help='sergi slug\'ı (sergiler/<slug>.json) veya dosya yolu')
    ap.add_argument('--json', help='çıktıyı bu dosyaya yaz')
    ap.add_argument('--envanter', default=ENV)
    ap.add_argument('--ozet', action='store_true', help='sadece bölüm özetlerini bas')
    a = ap.parse_args()

    yol = a.sergi if os.path.exists(a.sergi) else os.path.join(SERGI_DIR, a.sergi + '.json')
    sergi = json.load(open(yol, encoding='utf-8'))
    env = json.load(open(a.envanter, encoding='utf-8'))
    sonuc = coz(sergi, env)

    print('=' * 72)
    print('SERGİ: %s' % sonuc['baslik'])
    print('=' * 72)
    if sonuc.get('alt_baslik'):
        print('%s\n' % sonuc['alt_baslik'])
    for b in sonuc['bolumler']:
        print('  %d. %-34s %3d nesne  [%s]' % (b['sira'], b['baslik'][:34],
                                               b['nesne_sayisi'], b['gorunum']))
        if not a.ozet:
            if b.get('gruplar'):
                for g in b['gruplar'][:10]:
                    print('       ▸ %-38s %2d nesne  %s' % (str(g['baslik'])[:38],
                          g['nesne_sayisi'], g.get('alt_baslik', '')[:18]))
            else:
                for n in b.get('nesneler', [])[:8]:
                    print('       · %-12s %s' % (n.get('envanter_gosterim') or n['_id'],
                                                 str(n.get('baslik'))[:56]))
                if len(b.get('nesneler', [])) > 8:
                    print('       … (%d nesne daha)' % (len(b['nesneler']) - 8))
    print('\ntoplam nesne (bölüm tekrarlarıyla): %d' % sonuc['toplam_nesne'])

    if a.json:
        json.dump(sonuc, open(a.json, 'w'), ensure_ascii=False, indent=1)
        print('-> %s yazıldı' % a.json)


if __name__ == '__main__':
    main()
