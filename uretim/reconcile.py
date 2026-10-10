# -*- coding: utf-8 -*-
"""
HETEGA — Envanter Mutabakatı (v2)

  KİTAP  = otorite: envanter no, cilt/sayfa, bölüm hiyerarşisi, model tanımı
  SİTE   = mevcut yayın: başlık, görsel, açıklama, kategori

Her iki tarafta da envanter numaraları `numnorm.expand` ile kanonik biçime
açılır (aralıklar genişletilir), sonra numaradan birleştirilir.
Numarası olmayan site kayıtları (cilt, sayfa) + başlık benzerliği ile eşlenir.
"""
import re, os, json, csv, collections, unicodedata, difflib
import numnorm

import yollar
HERE = yollar.ARA
ROOT = yollar.KOK

blocks = json.load(open(os.path.join(HERE, 'book_blocks.json'), encoding='utf-8'))
site   = json.load(open(os.path.join(yollar.ARA, 'site_products.json'), encoding='utf-8'))

CULT = {'A':'Astronomi','B':'Saatler','C':'Coğrafya ve Seyrüsefer',
        'D':'Tesviye ve Geometri','E':'Fizik ve Teknik','F':'Mimari',
        'G':'Askeri Teknoloji','H':'Tıp','J':'Antik Objeler','K':'Kimya'}
VOLNUM = {'I':1,'II':2,'III':3,'IV':4,'V':5}

# ---------------------------------------------------------------- yardımcı
def fold(s):
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return (s.replace('ı','i').replace('İ','i').replace('ş','s').replace('Ş','S')
             .replace('ğ','g').replace('Ğ','G').replace('ü','u').replace('Ü','U')
             .replace('ö','o').replace('Ö','O').replace('ç','c').replace('Ç','C')
             .replace('â','a').replace('î','i').replace('û','u').lower())

def slug(s):
    s = fold(s)
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:60]

def words(s):
    return set(w for w in re.split(r'\W+', fold(s)) if len(w) > 3)

def sim(a, b):
    wa, wb = words(a), words(b)
    if not wa or not wb: return 0.0
    j = len(wa & wb) / len(wa | wb)
    return max(j, difflib.SequenceMatcher(None, fold(a), fold(b)).ratio())

def parse_kaynak(s):
    if not s: return (None, [])
    m = re.search(r'C(?:ilt)?\.?\s*([IV]+)', s)
    vol = m.group(1) if m else None
    pages = []
    for mm in re.finditer(r's\.?\s*(\d{1,3})\s*(?:-|–)\s*(\d{1,3})', s):
        a, b = int(mm.group(1)), int(mm.group(2))
        if 0 < b - a < 40: pages += list(range(a, b + 1))
    for mm in re.finditer(r's\.?\s*(\d{1,3})', s):
        p = int(mm.group(1))
        if p not in pages: pages.append(p)
    return (vol, sorted(set(pages)))

# ---------------------------------------------------------------- kitap indeksi
book_by_num = collections.defaultdict(list)
for b in blocks:
    for n in b['envanter_nolar']:
        book_by_num[n].append(b)

# ---------------------------------------------------------------- site indeksi
site_map = collections.defaultdict(list)     # kanonik no -> site kayıtları
site_unnum = []
for s in site:
    nums, par, susp, norm, bare = numnorm.expand(s.get('envanter_no', ''))
    s['_nums'], s['_nums_susp'], s['_bare'] = nums, susp, bare
    s['_vol'], s['_pages'] = parse_kaynak(s.get('Kaynak', ''))
    if nums:
        for n in nums: site_map[n].append(s)
    else:
        site_unnum.append(s)

# ---------------------------------------------------------------- 1) numaralı birleştirme
matched_site = set()
records = []

for num in sorted(set(book_by_num) | set(site_map)):
    bs = book_by_num.get(num, [])
    ss = site_map.get(num, [])
    b = bs[0] if bs else None
    s = ss[0] if ss else None
    if s: matched_site.add(s['_file'])
    pre = re.match(r'[A-ZÇĞİÖŞÜ]', num)
    pre = pre.group(0) if pre else ''

    r = {
      'envanter_no': num,
      'prefiks': pre,
      'koleksiyon': CULT.get(pre, ''),
      # ---- kitap (otorite) ----
      'kitap': bool(b),
      'cilt': ('Cilt ' + b['cilt']) if b else '',
      'cilt_no': VOLNUM.get(b['cilt']) if b else None,
      'kitap_sayfa': b['kitap_sayfa'] if b else None,
      'bolum': b['bolum'] if b else '',
      'alt_bolum': b['alt_bolum'] if b else '',
      'alt_baslik': b['alt_baslik'] if b else '',
      'kitap_ust_baslik': b['kitap_ust_baslik'] if b else '',
      'baslik_kitap': b['baslik'] if b else '',
      'baslik_kitap_kalite': b['baslik_kalite'] if b else '',
      'bilgin_kitap': b['bilgin'] if b else '',
      'eser_kitap': b['eser'] if b else '',
      'mense_kitap': b['mense'] if b else '',
      'donem_kitap': b['donem_kitap'] if b else '',
      'boyutlar_kitap': b['boyutlar'] if b else [],
      'malzeme_kitap': b['malzeme'] if b else [],
      'ham_envanter': b['ham_envanter'] if b else '',
      'numara_supheli': (b['numara_supheli'] if b else False),
      'kitap_baglam': b['baglam'] if b else [],
      # ---- site (yayın) ----
      'site': bool(s),
      'site_url': ('/' + s['_file'].replace('/index.html', '')) if s else '',
      'baslik': s['title'] if s else '',
      'kategori': s['Kategori'] if s else '',
      'alt_kategori': s['Alt Kategori'] if s else '',
      'bilgin': s['Yapımcı / Bilgin'] if s else '',
      'donem': s['Dönem'] if s else '',
      'orijinal': s['Orijinalin Yeri'] if s else '',
      'kaynak': s['Kaynak'] if s else '',
      'islev': s['İşlevi'] if s else '',
      'ozellikler': s['Özellikler'] if s else '',
      'gorsel': s['img'] if s else '',
      'site_coklu_nesne': bool(s and len(s['_nums']) > 1),
      'site_kapsadigi_nesne': len(s['_nums']) if s else 0,
    }

    # ---- birleşik alanlar ----
    r['baslik_kanonik'] = r['baslik'] or r['baslik_kitap']
    r['bilgin_kanonik'] = r['bilgin'] or r['bilgin_kitap']
    r['slug_onerisi'] = slug(r['baslik_kanonik'] or num)

    flags = []
    if b and s:
        r['durum'] = 'eşleşti'
        if r['baslik'] and r['baslik_kitap'] and \
           sim(r['baslik'], r['baslik_kitap']) < 0.34:
            flags.append('başlık_farklı')
        if r['cilt'] and s['_vol'] and s['_vol'] != b['cilt']:
            flags.append('cilt_uyuşmuyor')
        elif b['kitap_sayfa'] and s['_pages'] and b['kitap_sayfa'] not in s['_pages']:
            flags.append('sayfa_uyuşmuyor')
        if r['koleksiyon'] and r['kategori'] and \
           fold(r['koleksiyon']) != fold(r['kategori']) and r['kategori'] != 'Usturlaplar':
            flags.append('kategori_uyuşmuyor')
        if len(ss) > 1: flags.append('site_mükerrer_numara')
        if len(bs) > 1: flags.append('kitap_mükerrer_numara')
    elif b:
        r['durum'] = 'sitede_yok'
        flags.append('sitede_yok')
        if r['baslik_kitap_kalite'] == 'yok': flags.append('başlık_yok')
        elif r['baslik_kitap_kalite'] == 'tahmin': flags.append('başlık_tahmin')
    else:
        r['durum'] = 'kitapta_yok'
        flags.append('kitapta_yok')
    if r['numara_supheli']: flags.append('numara_şüpheli')
    if r['site_coklu_nesne']: flags.append('grup_kaydı')
    r['bayraklar'] = flags
    records.append(r)

# ---------------------------------------------------------------- 2) numarasız site kayıtları
book_by_page = collections.defaultdict(list)
for b in blocks:
    if b['kitap_sayfa']:
        book_by_page[(b['cilt'], b['kitap_sayfa'])].append(b)

unmatched = []
for s in site_unnum:
    best, bs = None, 0.0
    for p in s['_pages']:
        for b in book_by_page.get((s['_vol'], p), []):
            sc = sim(s['title'], b['baslik']) if b['baslik'] else 0.0
            if sc > bs: bs, best = sc, b
    unmatched.append({'site_baslik': s['title'], 'kaynak': s['Kaynak'],
                      'kategori': s['Kategori'], 'url': '/' + s['_file'].replace('/index.html',''),
                      'en_yakin_kitap_baslik': best['baslik'] if best else '',
                      'en_yakin_envanter': (best['envanter_nolar'][0] if best and best['envanter_nolar'] else ''),
                      'benzerlik': round(bs, 2)})

# ---------------------------------------------------------------- rapor + çıktı
print('=' * 80)
print('HETEGA — ENVANTER MUTABAKAT RAPORU')
print('=' * 80)
print('Kitap bloğu (Envanter No geçen yer)  : %d' % len(blocks))
print('Kitap benzersiz envanter no          : %d' % len(book_by_num))
print('Site kaydı                           : %d  (numaralı %d / numarasız %d)'
      % (len(site), len(site) - len(site_unnum), len(site_unnum)))
print('Kanonik kayıt (birleşim)             : %d' % len(records))
c = collections.Counter(r['durum'] for r in records)
for k in ['eşleşti', 'sitede_yok', 'kitapta_yok']:
    print('   %-14s %d' % (k, c[k]))

print('\n--- bayrak dağılımı ---')
for k, v in collections.Counter(f for r in records for f in r['bayraklar']).most_common():
    print('   %-24s %d' % (k, v))

print('\n--- SİTEDE YOK: koleksiyonlara göre eksik nesneler ---')
gap = [r for r in records if r['durum'] == 'sitede_yok']
for k, v in collections.Counter(r['koleksiyon'] or '?' for r in gap).most_common():
    good = sum(1 for r in gap if r['koleksiyon'] == k and r['baslik_kitap_kalite'] == 'iyi')
    print('   %-26s %3d eksik  (bunun %d tanesinin başlığı kitapta net)' % (k, v, good))

print('\n--- KİTAPTA YOK: sitede olup kitapta doğrulanamayan numaralar (%d) ---' % c['kitapta_yok'])
for r in sorted([x for x in records if x['durum'] == 'kitapta_yok'],
                key=lambda x: x['envanter_no']):
    print('   %-12s %-44s %s' % (r['envanter_no'], (r['baslik'] or '')[:44], r['kaynak'][:20]))

print('\n--- numarasız site kayıtları (%d) için en yakın kitap künyesi ---' % len(unmatched))
for u in sorted(unmatched, key=lambda x: -x['benzerlik'])[:18]:
    print('   %.2f  %-42s ~ %-30s %s' % (u['benzerlik'], u['site_baslik'][:42],
          u['en_yakin_kitap_baslik'][:30], u['en_yakin_envanter']))

# ---------------------------------------------------------------- dosyalar
json.dump(records, open(os.path.join(HERE, 'envanter_kanonik.json'), 'w'),
          ensure_ascii=False, indent=1)
json.dump(unmatched, open(os.path.join(HERE, 'site_numarasiz.json'), 'w'),
          ensure_ascii=False, indent=1)

COLS = ['envanter_no','durum','koleksiyon','bolum','alt_bolum','alt_baslik',
        'baslik_kanonik','baslik_kitap','baslik','bilgin_kanonik','eser_kitap',
        'mense_kitap','donem_kitap','cilt','kitap_sayfa','kategori','alt_kategori',
        'gorsel','site_url','bayraklar']
with open(os.path.join(HERE, 'envanter_kanonik.csv'), 'w', newline='',
          encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(COLS)
    for r in sorted(records, key=lambda x: x['envanter_no']):
        w.writerow([('; '.join(r[k]) if isinstance(r[k], list) else r[k]) for k in COLS])

print('\n-> envanter_kanonik.json / .csv / site_numarasiz.json yazıldı')
