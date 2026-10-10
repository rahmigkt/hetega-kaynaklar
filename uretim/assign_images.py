# -*- coding: utf-8 -*-
"""
Katalog3 görsel havuzunu kitaptaki eksik nesnelere eşler.

Temel bulgu: `kutuphane/katalog3/k<ürün>-<M>.jpg` dosyalarındaki M indeksi,
kitabın (cilt, sayfa) sırasına göre BİREBİR ARTAN küresel bir figür dizinidir
(456 atanmış üründe sapma = 0). 534 figürün 456'sı atanmış, 78'i boştadır.

Bu yüzden: kitabın bir sayfasındaki eksik nesne için, o sayfayı iki yandan
çevreleyen atanmış figürlerin M aralığındaki BOŞ M değerleri aday görseldir.
"""
import re, os, json, collections

import yollar
HERE = yollar.ENV
ROOT = yollar.KOK

VOL = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5}

# ---------------------------------------------------------------- girdiler
tree = open(os.path.join(yollar.ARA, 'repo-tree-hetega-website.txt'), encoding='utf-8').read().splitlines()
pool = {}                                   # M -> dosya yolu
for l in tree:
    p = l.split('\t')[2]
    m = re.match(r'\A.*/katalog3/k(\d+)-(\d+)\.(jpg|png)\Z', p)
    if m:
        pool[int(m.group(2))] = '/' + p
pool2 = {}
for l in tree:
    p = l.split('\t')[2]
    m = re.match(r'\A.*/katalog2/k(\d+)-(\d+)\.(jpg|png)\Z', p)
    if m:
        pool2[int(m.group(2))] = '/' + p

env = json.load(open(os.path.join(HERE, 'envanter.json'), encoding='utf-8'))
N = env['nesneler']

# ---------------------------------------------------------------- çıpa noktaları
# M -> (cilt, sayfa). Set üyeleri aynı görseli paylaştığı için M bazında
# teke indirilir; kitap sayfası bilinen kayıtlar önceliklidir.
M_sayfa = {}
M_sahip = collections.defaultdict(list)
for o in N:
    for g in o['gorseller']:
        m = re.match(r'\A.*/katalog([23])/k\d+-(\d+)\.\w+\Z', g['url'])
        if not m:
            continue
        M = int(m.group(2))
        M_sahip[M].append(o['id'])
        k = o['kitap']
        if k and k.get('sayfa') and M not in M_sayfa:
            M_sayfa[M] = (k['cilt'], int(k['sayfa']))

usedM = set(M_sahip)
anchors = sorted((M, c, s) for M, (c, s) in M_sayfa.items())
sirali = [(VOL[c], s) for M, c, s in anchors]
sapmalar = [(a, b) for a, b in zip(sirali, sirali[1:]) if b < a]
print('görseli olan nesne     : %d (benzersiz figür M: %d)'
      % (sum(1 for o in N if o['gorseller']), len(usedM)))
print('sayfası bilinen çıpa   : %d' % len(anchors))
print('(cilt,sayfa) monoton mu: %s  (sapma %d)'
      % ('EVET' if not sapmalar else 'HAYIR', len(sapmalar)))
if sapmalar:
    print('   sapmalar:', sapmalar[:6])

freeM = sorted(set(pool) - usedM)
print('toplam figür (M)       : %d' % len(pool))
print('atanmış                : %d' % len(usedM))
print('boşta                  : %d' % len(freeM))

# ---------------------------------------------------------------- boş M'lerin sayfa aralığı
def sayfa_ara(M):
    """M için (cilt, sayfa_lo, sayfa_hi, kesin_mi).
    kesin_mi=True  -> iki komşu çıpa da aynı cilt+sayfada, figür o sayfaya ait.
    değilse -> figür [lo..hi] sayfa aralığından birinde."""
    prev = nxt = None
    for a in anchors:
        if a[0] < M: prev = a
        elif a[0] > M and nxt is None: nxt = a
    if prev and nxt:
        if prev[1] == nxt[1]:
            lo, hi = min(prev[2], nxt[2]), max(prev[2], nxt[2])
            return (prev[1], lo, hi, lo == hi)
        # cilt geçişi -> aralık ciltler arası, belirsiz
        return (prev[1], prev[2], None, False)
    if prev: return (prev[1], prev[2], prev[2], True)
    if nxt:  return (nxt[1], nxt[2], nxt[2], True)
    return (None, None, None, False)

free_info = []
for M in freeM:
    c, lo, hi, tek = sayfa_ara(M)
    free_info.append({'M': M, 'dosya': pool[M], 'cilt': c, 'sayfa_lo': lo,
                      'sayfa_hi': hi, 'tek_sayfa': tek,
                      'katalog2_karsiligi': pool2.get(M, '')})
json.dump(free_info, open(os.path.join(HERE, 'gorsel_bosta_havuz.json'), 'w'),
          ensure_ascii=False, indent=1)

kesin = [f for f in free_info if f['tek_sayfa']]
print('\nboşta figürlerin konumu:')
print('   tek sayfaya sıkışan (güvenli) : %d' % len(kesin))
print('   aralıkta belirsiz             : %d' % (len(free_info) - len(kesin)))
print('   cilt dağılımı                 :',
      dict(collections.Counter(f['cilt'] for f in free_info).most_common()))

# ---------------------------------------------------------------- eksik nesnelere eşle
eksik = [o for o in N if o['yayin']['durum'] in
         ('eklenmeye_hazır', 'eksik_baslik_bekliyor', 'set_üyesi_bölünecek')]
print('\ngörsel bekleyen eksik nesne : %d' % len(eksik))

# eksikleri (cilt, sayfa) bazında grupla
grup = collections.defaultdict(list)
for o in eksik:
    k = o['kitap']
    if k and k.get('sayfa'):
        grup[(k['cilt'], int(k['sayfa']))].append(o)

atandi = 0
onerilen = []
for f in free_info:
    if f['tek_sayfa']:
        aday_sayfalar = [(f['cilt'], f['sayfa_lo'])]
        guven = 'sayfa_kesin'
    elif f['cilt'] and f['sayfa_lo'] is not None:
        # aralıktaki tüm sayfalar: sadece BİR tanesinde eksik nesne varsa ata
        span = []
        for (c, s_) in sorted(grup, key=lambda x: (VOL[x[0]], x[1])):
            if c != f['cilt']:
                continue
            if f['sayfa_lo'] <= s_ and (f['sayfa_hi'] is None or s_ <= f['sayfa_hi']):
                if any(not o['gorseller'] for o in grup[(c, s_)]):
                    span.append((c, s_))
        if len(span) == 1:
            aday_sayfalar, guven = span, 'sayfa_aralik_tek'
        else:
            continue
    else:
        continue
    hedef = grup.get(aday_sayfalar[0], [])
    hedef = [o for o in hedef if not o['gorseller']]
    if not hedef:
        continue
    f['sayfa_lo'] = aday_sayfalar[0][1]; f['cilt'] = aday_sayfalar[0][0]
    f['atama_guveni'] = guven
    o = hedef[0]
    atandi += 1
    onerilen.append({
        'envanter_no': o['id'], 'baslik': o['baslik'][:60],
        'cilt': f['cilt'], 'sayfa': f['sayfa_lo'], 'M': f['M'],
        'onenen_gorsel': f['dosya'], 'katalog2_muadili': f['katalog2_karsiligi'],
        'guven': guven, 'ayni_sayfadaki_rakip': len(hedef) - 1,
        'not': ('envanter.json\'a YAZILMADI — insan onayı bekliyor. '
                'Figür %d, %s s.%s civarı. Görsel içerik olarak doğrulanmalı.'
                % (f['M'], f['cilt'], f['sayfa_lo']))})

print('   -> görsel atanan nesne       : %d' % atandi)
print('   -> hâlâ görselsiz            : %d'
      % sum(1 for o in eksik if not o['gorseller']))

# NOT: envanter.json bilinçli olarak DEĞİŞTİRİLMİYOR — atamalar spekülatif,
#      görsel kararı insan onayına bırakılıyor (İngilizce PDF'ler daha iyi kaynak).
json.dump(onerilen, open(os.path.join(HERE, 'gorsel_atama_onerileri.json'), 'w'),
          ensure_ascii=False, indent=1)
print('\n-> SADECE gorsel_atama_onerileri.json yazıldı (envanter.json değişmedi)')

print('\n--- örnek atamalar ---')
for x in onerilen[:14]:
    print('   %-10s %-44s Cilt %s s.%-4s fig %-4d %s'
          % (x['envanter_no'], x['baslik'][:44], x['cilt'], x['sayfa'], x['M'],
             ('(rakip %d)' % x['ayni_sayfadaki_rakip']) if x['ayni_sayfadaki_rakip'] else ''))
