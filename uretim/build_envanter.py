# -*- coding: utf-8 -*-
"""
HETEGA — Kanonik Envanter İnşası

Girdiler:
  book_blocks.json   kitaptan çıkarılan 589 envanter bloğu (otorite)
  ../site_products.json   canlı siteden kazınan 456 yayın kaydı
  site_numarasiz.json     numarasız 46 site kaydı için en yakın kitap künyesi

Çıktı:
  envanter.json      TEK DOĞRU KAYNAK — nesne başına 1 kayıt
  envanter_istatistik.json
  incelemeye_muhtac.json   insan kararı bekleyen kayıtlar

Kurallar (kullanıcı kararları, 10 Eki 2026):
  * kitapta doğrulanamayan site numaraları SİLİNMEZ, 'doğrulanmadı' bayrağıyla yayında kalır
  * tek sayfada toplanmış nesne setleri AYRI kayıtlara bölünür
  * sitede olmayan 239 nesneden başlığı net olan 95'i 'eklenmeye_hazır' işaretlenir
"""
import re, os, json, collections, unicodedata, datetime, difflib
import numnorm

import yollar
HERE = yollar.ARA
OUT = yollar.ENV
TODAY = datetime.date.today().isoformat()

blocks = json.load(open(os.path.join(HERE, 'book_blocks.json'), encoding='utf-8'))
site   = json.load(open(os.path.join(yollar.ARA, 'site_products.json'), encoding='utf-8'))
yak    = json.load(open(os.path.join(HERE, 'site_numarasiz.json'), encoding='utf-8'))

# ---------------------------------------------------------------- sabitler
CULT = {'A':'Astronomi','B':'Saatler','C':'Coğrafya ve Seyrüsefer',
        'D':'Tesviye ve Geometri','E':'Fizik ve Teknik','F':'Mimari',
        'G':'Askeri Teknoloji','H':'Tıp','J':'Antik Objeler','K':'Kimya'}

# Sitenin mevcut kategori şeması -> kitap hiyerarşisi eşlemesi (87 uyumsuzluk için)
KATEGORI_DUZELTME = {
    'Usturlaplar': ('Astronomi', 'Astronomi Aletleri', 'Usturlaplar'),
}

# kitapta hangi cilt hangi bölümleri kapsar
BOLUM_CILT = {}
for b in blocks:
    BOLUM_CILT.setdefault(b['bolum'], b['cilt'])

def fold(s):
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return (s.replace('ı','i').replace('İ','i').replace('ş','s').replace('Ş','S')
             .replace('ğ','g').replace('Ğ','G').replace('ü','u').replace('Ü','U')
             .replace('ö','o').replace('Ö','O').replace('ç','c').replace('Ç','C')
             .replace('â','a').replace('î','i').replace('û','u').lower())

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', fold(s)).strip('-')[:64]

def words(s):
    return set(w for w in re.split(r'\W+', fold(s)) if len(w) > 3)

def sim(a, b):
    wa, wb = words(a), words(b)
    if not wa or not wb: return 0.0
    return max(len(wa & wb) / len(wa | wb),
               difflib.SequenceMatcher(None, fold(a), fold(b)).ratio())


COP = {'', '-', '—', '–', 'belirtilmemiş', 'belirtilmemis', 'yok', 'bilinmiyor',
       'anonim', '—;'}
def temiz(v):
    """Siteden gelen '—', 'belirtilmemiş' gibi dolgu değerlerini ayıklar."""
    if not v: return ''
    v = v.strip().strip(';').strip()
    if v.lower() in COP or v in COP: return ''
    if re.fullmatch(r'[\-—–\s;.,]+', v): return ''
    return v

ESER_OK = re.compile(r'(Kitâb|Kitab|Risâle|Risale|Makale|el-|et-|fî|fi |Zîc|Zic|'
                     r'Kanun|Şifâ|Tuhfe|Câmi|Kitab al|De |Liber|Almagest)', re.I)

def model_metni(baglam):
    """Kitap bloğunun bağlamından 'Modelimiz: ... (Envanter No' metnini ayıklar."""
    out = []; on = False
    for x in baglam or []:
        if re.match(r'^(\d\)|[ab]\))?\s*(Model(imiz|lerimiz)|Replikat(larımız|larımız))', x):
            on = True
        if on:
            if 'Envanter' in x:
                parca = x.split('(Envanter')[0].split('Envanter No')[0]
                if parca.strip(): out.append(parca)
                break
            out.append(x)
    return re.sub(r'\s+', ' ', ' '.join(out)).strip()

def gosterim(n):
    """A04.16 -> 'A 4.16' ; J224 -> 'J 224' ; H01.06-1 -> 'H 1.06-1'"""
    m = re.match(r'\A([A-Z])(\d{2})\.(\d{2})(.*)\Z', n)
    if m:
        L, g, k, ek = m.groups()
        return '%s %d.%s%s' % (L, int(g), k, ek)
    return n

# ---------------------------------------------------------------- indeksler
book_by_num = collections.defaultdict(list)
for b in blocks:
    for n in b['envanter_nolar']:
        book_by_num[n].append(b)

site_by_num = collections.defaultdict(list)
site_unnum = []
for s in site:
    nums, par, susp, norm, bare = numnorm.expand(s.get('envanter_no', ''))
    s['_nums'], s['_susp'] = nums, susp
    if nums:
        for n in nums: site_by_num[n].append(s)
    else:
        site_unnum.append(s)

# ================================================================ NESNELER
nesneler = {}
inceleme = []

def yeni_nesne(num):
    pre = re.match(r'\A[A-ZÇĞİÖŞÜ]', num)
    pre = pre.group(0) if pre else ''
    return {
        'id': num,
        'envanter_no': num,
        'envanter_gosterim': gosterim(num),
        'prefiks': pre,
        'koleksiyon': CULT.get(pre, ''),
        'hiyerarsi': {'cilt': '', 'bolum': '', 'alt_bolum': '', 'alt_baslik': ''},
        'baslik': '', 'baslik_kaynagi': '', 'baslik_kalite': '',
        'kisa_aciklama': '', 'aciklama': '', 'islev': '', 'ozellikler': '',
        'bilgin': '', 'bilgin_kaynagi': '', 'eser': '', 'donem': '', 'mense': '',
        'orijinal': '',
        'teknik': {'malzeme': [], 'boyutlar': []},
        'kitap': None,
        'gorseller': [],
        'set': None,
        'yayin': {'durum': 'eksik', 'url': '', 'slug': ''},
        'dogrulama': {'kitapta': False, 'sitede': False,
                      'bayraklar': [], 'notlar': []},
        'sergi_etiketleri': [],
    }

# ---- 1) kitap + numaralı site kayıtları ----
for num in sorted(set(book_by_num) | set(site_by_num)):
    o = yeni_nesne(num)
    bs = book_by_num.get(num, [])
    ss = site_by_num.get(num, [])
    b = bs[0] if bs else None
    s = ss[0] if ss else None

    if b:
        o['dogrulama']['kitapta'] = True
        o['hiyerarsi'] = {'cilt': 'Cilt ' + b['cilt'], 'bolum': b['bolum'],
                          'alt_bolum': b['alt_bolum'], 'alt_baslik': b['alt_baslik']}
        o['kitap'] = {'cilt': b['cilt'], 'sayfa': b['kitap_sayfa'],
                      'ham_envanter': b['ham_envanter'],
                      'ust_baslik': b['kitap_ust_baslik'],
                      'fig_no': b['kitap_fig_no'],
                      'satir': b['satir'],
                      'onek_cikarim': b.get('onek_cikarim', False),
                      'model_metni': model_metni(b['baglam'])}
        o['teknik'] = {'malzeme': b['malzeme'], 'boyutlar': b['boyutlar']}
        if b['bilgin'] or b['eser']:
            o['bilgin'], o['bilgin_kaynagi'] = temiz(b['bilgin']), 'kitap'
            o['eser'] = temiz(b['eser'])
            o['eser_kalite'] = ('olası' if ESER_OK.search(o['eser']) else 'şüpheli') \
                if o['eser'] else ''
        if b['mense']: o['mense'] = b['mense']
        if b['donem_kitap']: o['donem'] = b['donem_kitap']
        if b['numara_supheli']:
            o['dogrulama']['bayraklar'].append('numara_şüpheli')
        if len(bs) > 1:
            o['dogrulama']['bayraklar'].append('kitapta_mükerrer_blok')
            o['dogrulama']['notlar'].append(
                'Numara kitapta %d ayrı yerde geçiyor (satır %s).'
                % (len(bs), ', '.join(str(x['satir']) for x in bs)))
        # set üyeliği
        if len(b['envanter_nolar']) > 1:
            o['set'] = {'ham': b['ham_envanter'], 'kaynak': 'kitap',
                        'uye_sayisi': len(b['envanter_nolar']),
                        'uyeler': b['envanter_nolar'],
                        'baslik': b['baslik']}

    if s:
        o['dogrulama']['sitede'] = True
        o['yayin'] = {'durum': 'yayında',
                      'url': '/' + s['_file'].replace('/index.html', ''),
                      'slug': s['_file'].split('/')[1]}
        o['baslik'] = s['title']
        o['baslik_kaynagi'] = 'site'
        o['baslik_kalite'] = 'yayın'
        o['islev'] = s['İşlevi']
        o['ozellikler'] = s['Özellikler']
        o['orijinal'] = s['Orijinalin Yeri']
        if temiz(s['Yapımcı / Bilgin']):
            o['bilgin'], o['bilgin_kaynagi'] = temiz(s['Yapımcı / Bilgin']), 'site'
        if temiz(s['Dönem']): o['donem'] = temiz(s['Dönem'])
        if s['img']:
            o['gorseller'] = [{'url': s['img'], 'kaynak': 'katalog3', 'etiket': ''}]
        if len(s['_nums']) > 1:
            o['set'] = {'ham': s['envanter_no'], 'kaynak': 'site',
                        'uye_sayisi': len(s['_nums']), 'uyeler': s['_nums'],
                        'baslik': s['title'], 'url': o['yayin']['url']}
        if len(ss) > 1:
            o['dogrulama']['bayraklar'].append('sitede_mükerrer_numara')
            o['dogrulama']['notlar'].append(
                'Aynı numara sitede %d farklı sayfada: %s'
                % (len(ss), ', '.join(x['title'][:40] for x in ss)))
        # kategori: site kitapla çelişiyorsa kitabı esas al, not düş
        kat = s['Kategori']
        if o['koleksiyon'] and kat and fold(kat) != fold(o['koleksiyon']):
            o['dogrulama']['bayraklar'].append('kategori_uyuşmuyor')
            o['dogrulama']['notlar'].append(
                'Site kategorisi "%s", kitap önekine göre olması gereken "%s".'
                % (kat, o['koleksiyon']))
        o['site_kategori'] = {'kategori': kat, 'alt_kategori': s['Alt Kategori']}
        # kaynak doğrulama
        m = re.search(r'C(?:ilt)?\.?\s*([IV]+)', s['Kaynak'] or '')
        if m and b:
            sayfalar = [int(x) for x in re.findall(r'(\d{1,3})',
                        (s['Kaynak'] or '').split('s.')[-1])] if 's.' in (s['Kaynak'] or '') else []
            if m.group(1) != b['cilt']:
                o['dogrulama']['bayraklar'].append('cilt_uyuşmuyor')
            elif b['kitap_sayfa'] and sayfalar and b['kitap_sayfa'] not in sayfalar:
                o['dogrulama']['bayraklar'].append('sayfa_uyuşmuyor')
                o['dogrulama']['notlar'].append(
                    'Site "%s" diyor; nesne kitapta s.%s.' % (s['Kaynak'], b['kitap_sayfa']))
        o['kitap_kaynak_site'] = s['Kaynak']

    # ---- başlık kaynağı / kalite ----
    if not o['baslik'] and b:
        o['baslik'] = b['baslik']
        o['baslik_kaynagi'] = 'kitap'
        o['baslik_kalite'] = b['baslik_kalite']
    if o['baslik'] and b and o['baslik_kaynagi'] == 'site' and b['baslik']:
        if sim(o['baslik'], b['baslik']) < 0.34:
            o['dogrulama']['bayraklar'].append('başlık_kitaptan_farklı')
            o['baslik_kitap'] = b['baslik']
    if not o['baslik']:
        o['dogrulama']['bayraklar'].append('başlık_yok')

    # ---- yayın durumu ----
    if o['dogrulama']['sitede'] and not o['dogrulama']['kitapta']:
        o['yayin']['durum'] = 'yayında_doğrulanmadı'
        o['dogrulama']['bayraklar'].append('kitapta_doğrulanamadı')
        o['dogrulama']['notlar'].append(
            'Bu envanter numarası 5 cildin OCR metninde bulunamadı. '
            'Site kaynağı: %s. Müzede kitapta yer almayan bir nesne olabilir '
            'ya da numara hatalı atanmış olabilir.' % (o.get('kitap_kaynak_site') or '-'))
        inceleme.append({'tur': 'kitapta_doğrulanamadı', 'id': num,
                         'baslik': o['baslik'], 'site_kaynak': o.get('kitap_kaynak_site', ''),
                         'url': o['yayin']['url']})
    elif o['dogrulama']['kitapta'] and not o['dogrulama']['sitede']:
        hazir = bool(b) and b['baslik_kalite'] == 'iyi' and len(b['baslik']) >= 4
        o['yayin']['durum'] = 'eklenmeye_hazır' if hazir else 'eksik_baslik_bekliyor'
        o['dogrulama']['bayraklar'].append('sitede_yok')
    else:
        o['yayin']['durum'] = 'yayında'

    # ---- set üyeleri: tek sayfa -> nesne başına ayrı sayfa (kullanıcı kararı) ----
    # NOT: bölme yalnızca ZATEN yayında olan set sayfaları için geçerli.
    #      Kitapta olup sitede hiç olmayan set üyeleri 'eklenmeye_hazır' kalır.
    if o['set'] and o['set']['uye_sayisi'] > 1:
        uyeler = o['set']['uyeler']
        sira = uyeler.index(num) + 1 if num in uyeler else 0
        o['set']['uye_sira'] = sira
        o['set']['set_sayfasi'] = o['yayin']['url']
        if sira > 1 and o['dogrulama']['sitede']:
            # ilk üye mevcut sayfayı tutar, diğerleri yeni sayfa alır
            o['yayin'] = {'durum': 'set_üyesi_bölünecek', 'url': '',
                          'slug': slug('%s-%s' % (o['baslik'] or num, o['envanter_gosterim'])),
                          'bolunecegi_set': o['set']['set_sayfasi']}
            o['dogrulama']['bayraklar'].append('set_üyesi_bölünecek')
            o['dogrulama']['notlar'].append(
                'Bu nesne "%s" sayfasında %d nesnelik bir setin %d. üyesi olarak '
                'geçiyor; ayrı sayfaya bölünecek.'
                % (o['set']['baslik'][:50], o['set']['uye_sayisi'], sira))

    if not o['yayin']['slug']:
        o['yayin']['slug'] = slug(o['baslik'] or num)
    nesneler[num] = o

# ---- 2) numarasız 46 site kaydı ----
byakin = {y['site_baslik']: y for y in yak}
atanan = 0
for s in site_unnum:
    y = byakin.get(s['title'])
    hedef = y['en_yakin_envanter'] if y else ''
    benzerlik = y['benzerlik'] if y else 0
    url = '/' + s['_file'].replace('/index.html', '')
    if hedef and benzerlik >= 0.55 and hedef in nesneler and \
       not nesneler[hedef]['dogrulama']['sitede']:
        o = nesneler[hedef]
        o['dogrulama']['sitede'] = True
        o['baslik'] = s['title']; o['baslik_kaynagi'] = 'site'; o['baslik_kalite'] = 'yayın'
        o['islev'] = s['İşlevi']; o['ozellikler'] = s['Özellikler']
        o['orijinal'] = s['Orijinalin Yeri']
        if temiz(s['Yapımcı / Bilgin']):
            o['bilgin'], o['bilgin_kaynagi'] = temiz(s['Yapımcı / Bilgin']), 'site'
        if s['img']: o['gorseller'] = [{'url': s['img'], 'kaynak': 'katalog3', 'etiket': ''}]
        o['yayin'] = {'durum': 'yayında', 'url': url, 'slug': s['_file'].split('/')[1]}
        o['dogrulama']['notlar'].append(
            'Site sayfasında envanter no yazmıyordu; kitap künyesiyle %.0f%% benzerlik '
            'üzerinden %s numarasına otomatik bağlandı.' % (benzerlik * 100, hedef))
        o['dogrulama']['bayraklar'].append('numara_otomatik_atandı')
        sitede_yok = 'sitede_yok' in o['dogrulama']['bayraklar']
        if sitede_yok: o['dogrulama']['bayraklar'].remove('sitede_yok')
        atanan += 1
    else:
        key = 'SITE-' + (s['_file'].split('/')[1] or slug(s['title']))
        o = yeni_nesne(key)
        o['envanter_no'] = None
        o['envanter_gosterim'] = '(envanter no yok)'
        o['prefiks'] = ''; o['koleksiyon'] = s['Kategori']
        o['baslik'] = s['title']; o['baslik_kaynagi'] = 'site'; o['baslik_kalite'] = 'yayın'
        o['islev'] = s['İşlevi']; o['ozellikler'] = s['Özellikler']
        o['orijinal'] = s['Orijinalin Yeri']
        if temiz(s['Yapımcı / Bilgin']):
            o['bilgin'], o['bilgin_kaynagi'] = temiz(s['Yapımcı / Bilgin']), 'site'
        if temiz(s['Dönem']): o['donem'] = temiz(s['Dönem'])
        if s['img']: o['gorseller'] = [{'url': s['img'], 'kaynak': 'katalog3', 'etiket': ''}]
        o['yayin'] = {'durum': 'yayında_numarasız', 'url': url, 'slug': s['_file'].split('/')[1]}
        o['site_kategori'] = {'kategori': s['Kategori'], 'alt_kategori': s['Alt Kategori']}
        o['kitap_kaynak_site'] = s['Kaynak']
        o['dogrulama']['sitede'] = True
        o['dogrulama']['bayraklar'] = ['envanter_no_yok']
        o['dogrulama']['notlar'].append(
            'Sayfada envanter numarası yok. En yakın kitap künyesi: "%s" (%s), benzerlik %.0f%%.'
            % (y['en_yakin_kitap_baslik'] if y else '', hedef or '-', benzerlik * 100))
        nesneler[key] = o
        inceleme.append({'tur': 'envanter_no_yok', 'id': key, 'baslik': s['title'],
                         'oneri': hedef, 'benzerlik': round(benzerlik, 2), 'url': url})

# ---- 3) başlığı zayıf olanları inceleme kuyruğuna ----
for o in nesneler.values():
    if o['dogrulama']['kitapta'] and o['baslik_kalite'] in ('üstbaşlık', 'tahmin', 'yok') \
       and not o['dogrulama']['sitede']:
        inceleme.append({'tur': 'başlık_kitaptan_okunamadı', 'id': o['id'],
                         'baslik': o['baslik'], 'kalite': o['baslik_kalite'],
                         'kitap': '%s s.%s' % (o['hiyerarsi']['cilt'],
                                               (o['kitap'] or {}).get('sayfa')),
                         'bolum': ' > '.join(x for x in [o['hiyerarsi']['bolum'],
                                     o['hiyerarsi']['alt_bolum'], o['hiyerarsi']['alt_baslik']] if x),
                         'baglam': (o['kitap'] or {}).get('satir')})

# ---- 4) sergi etiketleri (dinamik sıralama altyapısı) ----
for o in nesneler.values():
    t = []
    h = o['hiyerarsi']
    if h['bolum'] and slug(h['bolum']): t.append('bolum:' + slug(h['bolum']))
    if h['alt_bolum']: t.append('altbolum:' + slug(h['alt_bolum']))
    if h['alt_baslik']: t.append('altbaslik:' + slug(h['alt_baslik']))
    if o['koleksiyon']: t.append('koleksiyon:' + slug(o['koleksiyon']))
    if o['bilgin']:
        parca = re.split(r'[;,]', o['bilgin'])[0]
        if slug(parca): t.append('bilgin:' + slug(parca)[:48])
    if o['eser'] and slug(o['eser']): t.append('eser:' + slug(o['eser'])[:48])
    if o['mense'] and slug(o['mense']): t.append('mense:' + slug(o['mense']))
    if o['donem'] and slug(o['donem']): t.append('donem:' + slug(o['donem'])[:40])
    if o['set']: t.append('set:' + slug(o['set']['ham'].replace(' ', ''))[:40])
    o['sergi_etiketleri'] = sorted(set(t))

# ================================================================ ÇIKTI
liste = sorted(nesneler.values(), key=lambda o: (o['prefiks'] or 'ZZ', o['id']))

durum = collections.Counter(o['yayin']['durum'] for o in liste)
bayrak = collections.Counter(f for o in liste for f in o['dogrulama']['bayraklar'])
kalite = collections.Counter(o['baslik_kalite'] or '-' for o in liste)
kol = collections.Counter(o['koleksiyon'] or '(belirsiz)' for o in liste)

cikti = {
  'ust_veri': {
    'ad': 'HETEGA — Müze Envanteri (kanonik)',
    'aciklama': ('Prof. Dr. Fuat Sezgin, "İslam\'da Bilim ve Teknik" (Cilt I-V, '
                 'İBB Kültür A.Ş. / TÜBA, 2. basım 2008) esas alınarak '
                 'hetega.com canlı kataloğuyla mutabakatı yapılmış tek doğru kaynak.'),
    'surum': '1.0.0',
    'uretim_tarihi': TODAY,
    'ureten': 'inventory/build_envanter.py',
    'kaynaklar': {
        'kitap': {'ciltler': ['I','II','III','IV','V'], 'blok': len(blocks),
                  'benzersiz_envanter_no': len(book_by_num)},
        'site': {'kayit': len(site), 'numarali': len(site) - len(site_unnum),
                 'numarasiz': len(site_unnum), 'cekrilen_tarih': TODAY},
    },
    'sayilar': {
        'toplam_nesne': len(liste),
        'yayin_durumu': dict(durum),
        'baslik_kalitesi': dict(kalite),
        'koleksiyonlar': dict(kol.most_common()),
        'bayraklar': dict(bayrak.most_common()),
        'incelemeye_muhtac': len(inceleme),
    },
    'kararlar': [
        'Kitapta doğrulanamayan numaralar silinmez, "yayında_doğrulanmadı" olarak işaretlenir.',
        'Nesne setleri (örn. H 8.01-26) ayrı kayıtlara bölünür, set bağlığı korunur.',
        'Öncelik: başlığı kitapta net olan eksik nesneler.',
        'Koleksiyon ataması envanter önekinden yapılır; site kategorisi not olarak saklanır.',
    ],
  },
  'koleksiyonlar': [
      {'id': slug(v), 'ad': v, 'onek': k,
       'kitap_bolumleri': sorted({b['bolum'] for b in blocks
                                  for n in b['envanter_nolar'] if n.startswith(k)}),
       'nesne_sayisi': kol[v]}
      for k, v in sorted(CULT.items())],
  'nesneler': liste,
}

json.dump(cikti, open(os.path.join(OUT, 'envanter.json'), 'w'), ensure_ascii=False, indent=1)
json.dump(inceleme, open(os.path.join(yollar.ARA, 'incelemeye_muhtac.json'), 'w'),
          ensure_ascii=False, indent=1)
json.dump(cikti['ust_veri']['sayilar'], open(os.path.join(HERE, 'envanter_istatistik.json'), 'w'),
          ensure_ascii=False, indent=1)

print('=' * 74)
print('ENVANTER.JSON ÜRETİLDİ')
print('=' * 74)
print('toplam nesne           : %d' % len(liste))
print('numarasız site kaydı   : %d otomatik atandı, %d ayrı kayıt olarak kaldı'
      % (atanan, len(site_unnum) - atanan))
print('\n--- yayın durumu ---')
for k, v in durum.most_common(): print('   %-26s %d' % (k, v))
print('\n--- başlık kalitesi ---')
for k, v in kalite.most_common(): print('   %-26s %d' % (k, v))
print('\n--- koleksiyonlar ---')
for k, v in kol.most_common(): print('   %-26s %d' % (k, v))
print('\n--- bayraklar ---')
for k, v in bayrak.most_common(): print('   %-26s %d' % (k, v))
print('\nincelemeye muhtaç kayıt  : %d' % len(inceleme))
print('   ', dict(collections.Counter(i['tur'] for i in inceleme).most_common()))
