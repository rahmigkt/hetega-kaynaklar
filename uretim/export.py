# -*- coding: utf-8 -*-
"""envanter.json -> CSV + koleksiyon ağacı + sayım özetleri üretir."""
import json, csv, os, collections, re

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, 'envanter.json'), encoding='utf-8'))
N = d['nesneler']

# ---------------------------------------------------------------- CSV
COLS = [
 ('id', 'envanter_no'), ('gosterim', 'envanter_gosterim'), ('koleksiyon', 'koleksiyon'),
 ('prefiks', 'prefiks'), ('durum', 'yayin.durum'), ('url', 'yayin.url'),
 ('baslik', 'baslik'), ('baslik_kaynagi', 'baslik_kaynagi'),
 ('baslik_kalite', 'baslik_kalite'), ('baslik_kitap', 'baslik_kitap'),
 ('cilt', 'hiyerarsi.cilt'), ('bolum', 'hiyerarsi.bolum'),
 ('alt_bolum', 'hiyerarsi.alt_bolum'), ('alt_baslik', 'hiyerarsi.alt_baslik'),
 ('bilgin', 'bilgin'), ('bilgin_id', 'bilgin_id'), ('bilgin_kanonik', 'bilgin_kanonik'),
 ('bilgin_tur', 'bilgin_tur'), ('bilgin_kaynagi', 'bilgin_kaynagi'), ('eser', 'eser'),
 ('eser_kalite', 'eser_kalite'), ('donem', 'donem'), ('mense', 'mense'),
 ('orijinal', 'orijinal'), ('islev', 'islev'), ('ozellikler', 'ozellikler'),
 ('malzeme', 'teknik.malzeme'), ('boyutlar', 'teknik.boyutlar'),
 ('kitap_sayfa', 'kitap.sayfa'), ('kitap_ham_envanter', 'kitap.ham_envanter'),
 ('gorsel', 'gorseller[0].url'),
 ('set', 'set.ham'), ('set_uye_sayisi', 'set.uye_sayisi'), ('set_uye_sira', 'set.uye_sira'),
 ('kitapta', 'dogrulama.kitapta'), ('sitede', 'dogrulama.sitede'),
 ('bayraklar', 'dogrulama.bayraklar'), ('notlar', 'dogrulama.notlar'),
 ('sergi_etiketleri', 'sergi_etiketleri'),
]

def get(o, path):
    cur = o
    for part in path.split('.'):
        m = re.match(r'\A(.+)\[(\d+)\]\Z', part)
        if m:
            cur = cur.get(m.group(1)) if isinstance(cur, dict) else None
            if not isinstance(cur, list) or len(cur) <= int(m.group(2)): return ''
            cur = cur[int(m.group(2))]
        else:
            if not isinstance(cur, dict): return ''
            cur = cur.get(part)
        if cur is None: return ''
    if isinstance(cur, list): return '; '.join(str(x) for x in cur)
    if isinstance(cur, bool): return 'evet' if cur else 'hayır'
    return cur

with open(os.path.join(HERE, 'envanter.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow([c[0] for c in COLS])
    for o in N:
        w.writerow([get(o, c[1]) for c in COLS])
print('envanter.csv  -> %d satır' % len(N))

# ---------------------------------------------------------------- koleksiyon ağacı
def node(): return {'nesne': 0, 'alt': collections.OrderedDict()}
tree = collections.OrderedDict()
for o in N:
    h = o['hiyerarsi']
    yol = [x for x in [o['koleksiyon'] or '(koleksiyonsuz)', h['bolum'],
                       h['alt_bolum'], h['alt_baslik']] if x]
    cur = tree
    for adim in yol:
        d = cur.setdefault(adim, node())
        d['nesne'] += 1
        cur = d['alt']

def sadelestir(t):
    out = collections.OrderedDict()
    for k, v in sorted(t.items(), key=lambda x: (-x[1]['nesne'], x[0])):
        out[k] = {'nesne': v['nesne']}
        alt = sadelestir(v['alt'])
        if alt: out[k]['alt'] = alt
    return out

json.dump(sadelestir(tree), open(os.path.join(HERE, 'koleksiyon_agaci.json'), 'w'),
          ensure_ascii=False, indent=1)
print('koleksiyon_agaci.json yazıldı')

# ---------------------------------------------------------------- iş yükü özeti
ozet = collections.Counter(o['yayin']['durum'] for o in N)
print('\n--- iş yükü ---')
yeni = ozet['eklenmeye_hazır'] + ozet['eksik_baslik_bekliyor'] + ozet['set_üyesi_bölünecek']
for k, v in ozet.most_common(): print('   %-26s %d' % (k, v))
print('   %-26s %d' % ('=> üretilecek YENİ sayfa', yeni))

gorselli = sum(1 for o in N if o['gorseller'])
print('\ngörseli olan nesne : %d / %d' % (gorselli, len(N)))
hazir_gorselsiz = [o for o in N if o['yayin']['durum'] == 'eklenmeye_hazır' and not o['gorseller']]
print('   eklenmeye hazır ama GÖRSELSİZ: %d / %d' % (len(hazir_gorselsiz), ozet['eklenmeye_hazır']))
