# -*- coding: utf-8 -*-
"""
HETEGA — Site Üreteci v2

envanter.json'dan, mevcut sitenin tasarım şablonuyla yeni nesne sayfaları üretir;
index / koleksiyon / set sayfaları / sitemap'i İDEMPOTENT günceller (işaretçi
bloklar: her çalışmada eski blok sökülüp yenisi konur).

Üretilenler:
  * yayin.durum == 'eklenmeye_hazır'       -> yeni ürün sayfası
  * yayin.durum == 'set_üyesi_bölünecek'   -> yeni ürün sayfası (set bağlamlı)
  * set ana sayfalarına "Set Üyeleri" çubukları
  * products/index.html: kartlar + kategori sayaçları + Antik Objeler düğmesi
  * koleksiyonlar/<slug>/tumu/: yeni kartlar + başlık sayacı
  * sitemap.xml: yeni URL'ler

Devamlılık: envanter/uretim_manifest.json okunur; daha önce üretilmiş kayıtlar
'durum=üretildi + url' olarak işaretlenir, sayfası diskte yoksa yeniden üretilir.
"""
import re, os, json, html, sys, unicodedata, collections, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
try:
    import yollar
    ENVF = os.path.join(yollar.ENV, 'envanter.json')
    MANF = os.path.join(yollar.ENV, 'uretim_manifest.json')
    HEDEF = os.environ.get('HETEGA_WEBSITE', yollar.WEBSITE)
except ImportError:
    ENVF = os.path.join(HERE, 'envanter.json')
    MANF = os.path.join(HERE, 'uretim_manifest.json')
    HEDEF = os.environ.get('HETEGA_WEBSITE', '/home/user/hetega-website')

M_BAS, M_BIT = '<!-- ENVANTER-V1 -->', '<!-- /ENVANTER-V1 -->'
TR = {'ç':'c','ğ':'g','ı':'i','i':'i','ö':'o','ş':'s','ü':'u','â':'a','î':'i','û':'u',
      'ʿ':'','ʾ':'','’':"'",'«':'','»':'','‘':"'",'é':'e','ā':'a','ī':'i','ū':'u',
      'ḥ':'h','ḳ':'k','ṣ':'s','ṭ':'t','ẓ':'z','ñ':'n'}
KOL_SLUG = {'Astronomi':'astronomi','Saatler':'saatler','Coğrafya ve Seyrüsefer':'cografya-ve-seyrusefer',
            'Tesviye ve Geometri':'tesviye-ve-geometri','Fizik ve Teknik':'fizik-ve-teknik',
            'Mimari':'mimari','Askeri Teknoloji':'askeri-teknoloji','Tıp':'tip',
            'Antik Objeler':'antik-objeler','Kimya':'kimya','Optik':'optik','Usturlaplar':'usturlaplar'}

def slugify(s, maxlen=58):
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = ''.join(TR.get(c, c) for c in s).lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:maxlen].rstrip('-') or 'nesne'

def esc(s): return html.escape(s or '', quote=True)
def nrm(s): return re.sub(r'\s+', ' ', s or '').strip()

def blok_koy(t, icerik):
    """Eski işaretçi bloğunu sök, yenisini tak."""
    t = re.sub(re.escape(M_BAS) + r'.*?' + re.escape(M_BIT), '', t, flags=re.S)
    return t, M_BAS + icerik + M_BIT

# ------------------------------------------------------------------ şablon
def sablonlar():
    ornek = None
    for kok, dizinler, dosyalar in os.walk(os.path.join(HEDEF, 'products')):
        if os.path.basename(kok).startswith('k3-') and 'index.html' in dosyalar:
            ornek = os.path.join(kok, 'index.html'); break
    t = open(ornek, encoding='utf-8').read()
    head = t[:t.index('<body>') + len('<body>')]
    footer = t[t.index('<footer'):]
    bi = t.index('<body>') + 6
    hi = t.index('<div class="product-mock">')
    header = t[bi:hi].lstrip()
    header = re.sub(r'^<div class="deneme-banner">.*?</div>\s*', '', header, flags=re.S)
    assert 'deneme-banner' not in header
    return head, header, footer

def sayfa_uret(o, head, header, footer, url_map, idx):
    h = o['hiyerarsi']; k = o.get('kitap') or {}
    banner = ('<div class="deneme-banner"><strong>📖 KATALOG</strong> — Fuat Sezgin, '
              'İslam&#x27;da Bilim ve Teknik, %s, s. %s</div>'
              % (esc(h.get('cilt') or '?'), esc(str(k.get('sayfa') or '?'))))
    krumb = ' / '.join(x for x in ['Envanter', esc(o['koleksiyon']),
               esc(h.get('alt_bolum') or ''), esc(h.get('alt_baslik') or '')] if x)
    setli = bool(o.get('set') and o['set'].get('uye_sayisi', 0) > 1)
    if setli and o['yayin'].get('_set_baslik_eki'):
        baslik = o['baslik'] + ' (%d/%d)' % (o['set'].get('uye_sira', 0), o['set']['uye_sayisi'])
    else:
        baslik = o['baslik']
    B = esc(baslik)

    if o.get('gorseller'):
        med = ('<div class="product-detail-image" id="main-img-box"><img src="%s" alt="%s"></div>'
               % (esc(o['gorseller'][0]['url']), B))
        if setli:
            med += ('<p style="font-size:.7rem;color:var(--muted-text);text-align:center;margin:.4rem 0 0">'
                    'Grup fotoğrafı: set üyeleri birlikte görüntülenir.</p>')
    else:
        med = ('<div class="product-detail-image" id="main-img-box"><div class="no-image">'
               '<span style="font-size:2.4rem">🏺</span><span style="font-size:.78rem;line-height:1.6">'
               'Görsel hazırlanıyor<br>kitap figürü işleme sırasında</span></div></div>')

    kisa = ''
    if o.get('ozgun_ad'):
        kisa = '<p class="kisa-aciklama">Özgün ad: %s</p>' % esc(o['ozgun_ad'])
    elif o.get('islev') and not setli:
        kisa = '<p class="kisa-aciklama">%s</p>' % esc(o['islev'])

    specs = [('Kategori', esc(o['koleksiyon'])),
             ('Alt Kategori', esc(h.get('alt_baslik') or h.get('alt_bolum') or '—')),
             ('Yapımcı / Bilgin', esc(o.get('bilgin') or '—')),
             ('Dönem', esc(o.get('donem') or 'belirtilmemiş')),
             ('Menşe', esc(o.get('mense') or '—')),
             ('Kaynak', esc('%s, s. %s' % (h.get('cilt') or '?', k.get('sayfa') or '?')))]
    if setli:
        specs.append(('Set', esc('%s · %d nesne' % (o['set'].get('ham', ''), o['set']['uye_sayisi']))))
    specs_html = ''.join('<div class="spec"><span>%s</span><strong>%s</strong></div>' % s for s in specs)

    oz = []
    mm = nrm(k.get('model_metni') or '')
    if mm: oz.append('<li>%s</li>' % esc(mm))
    if o['teknik'].get('malzeme'): oz.append('<li>Malzeme: %s</li>' % esc(', '.join(o['teknik']['malzeme'])))
    if o['teknik'].get('boyutlar'): oz.append('<li>Ölçüler: %s</li>' % esc('; '.join(o['teknik']['boyutlar'])))
    if o.get('orijinal'): oz.append('<li>%s</li>' % esc(o['orijinal']))
    ozellikler = ('<p class="tag">Kitap kaydı</p><ul>%s</ul>' % ''.join(oz)) if oz else ''

    islev_html = ''
    if o.get('islev') and o.get('ozgun_ad'):
        islev_html = '<p class="tag">İşlevi</p><p class="body-text">%s</p>' % esc(o['islev'])

    set_html = ''
    if setli:
        st = o['set']
        set_url = st.get('set_sayfasi') or ''
        link = (' <a href="%s">Set sayfası →</a>' % esc(set_url)) if set_url else ''
        set_html = ('<div class="model-box">Bu nesne, kitapta tek künyede geçen <b>%d parçalık</b> '
                    'bir grubun <b>%d.</b> üyesidir: «%s» (%s).%s</div>'
                    % (st['uye_sayisi'], st.get('uye_sira', 0),
                       esc(nrm(st.get('baslik') or ''))[:60], esc(st.get('ham', '')), link))

    model_box = '<div class="model-box">Envanter No: %s · %s</div>' % (
        esc(o['envanter_gosterim']),
        'Orijinal (antik obje)' if o['prefiks'] == 'J' else 'Enstitü modeli')

    notlar = ''.join('<p class="body-text" style="font-size:.78rem;color:var(--muted-text)">%s</p>'
                     % esc(x) for x in o['dogrulama'].get('notlar', [])
                     if x.startswith(('İNSAN', 'BAŞLIK', 'HAKEM')))

    # ilişkili kayıtlar: set üyeleri + aynı alt başlık
    ogeler = []
    def ekle(x, etiket):
        if x['id'] == o['id']: return
        u = url_map.get(x['id'])
        if not u: return
        ogeler.append('<div class="related-item"><div class="ri-head"><h4>'
                      '<a href="%s" style="color:inherit;text-decoration:none">%s</a></h4>'
                      '<span class="badge guclu">%s</span></div>'
                      '<p style="font-size:.78rem;color:var(--muted-text)">%s · %s s.%s</p></div>'
                      % (esc(u), esc(nrm(x['baslik'])[:58]), etiket, esc(x['envanter_gosterim']),
                         esc(x['hiyerarsi'].get('cilt') or ''), esc(str((x.get('kitap') or {}).get('sayfa') or ''))))
    if setli:
        for uid in o['set'].get('uyeler', []):
            if uid in idx: ekle(idx[uid], 'set üyesi')
    for x in [z for z in idx.values() if z['hiyerarsi'].get('alt_baslik')
              and z['hiyerarsi']['alt_baslik'] == o['hiyerarsi'].get('alt_baslik')
              and z['id'] != o['id']][:5]:
        ekle(x, 'aynı bölüm')
    iliskili = ('<div class="related-section"><p class="tag">📜 İlişkili Kayıtlar</p>%s</div>'
                % ''.join(ogeler[:8])) if ogeler else ''

    head2 = re.sub(r'<title>.*?</title>', '<title>%s — HETEGA</title>' % B, head, count=1, flags=re.S)
    return f'''{head2}
{banner}{header}
<div class="product-mock"><div class="product-detail">
  <div class="media-col">{med}</div>
  <div class="copy-col">
    <a class="product-back" href="/products"><span>←</span> Envantere dön</a>
    <p class="product-breadcrumb"><span>{krumb.replace(' / ', '</span> / <span>')}</span></p>
    <p class="eyebrow">{esc(o['envanter_gosterim'])} · {esc(o['koleksiyon'])}</p><h1>{B}</h1>
    {kisa}
    <div class="spec-row">{specs_html}</div>
    <div class="uzun-aciklama">
      {islev_html}
      {ozellikler}
      {set_html}
      {model_box}
      {notlar}
    </div>
    {iliskili}
</div></div>
{footer}'''

# ------------------------------------------------------------------ kartlar
def kart(url, baslik, alt, gorsel=None):
    img = ('<img src="%s" alt="%s" loading="lazy" style="width:100%%;height:100%%;object-fit:contain;'
           'padding:1.25rem"/>' % (esc(gorsel), esc(baslik))) if gorsel else \
          '<span style="font-size:2.2rem;opacity:.5">🏺</span>'
    return ('<a href="%s" style="display:flex;flex-direction:column;color:inherit;text-decoration:none;'
            'background:radial-gradient(ellipse at 50%% 30%%, var(--card-bg) 0%%, var(--card-bg) 55%%, '
            'rgba(0,0,0,.1) 100%%);border-radius:2px;box-shadow:0 18px 40px -14px rgba(0,0,0,.4), '
            '0 4px 10px rgba(0,0,0,.15);overflow:hidden">'
            '<div style="aspect-ratio:1/1;display:flex;align-items:center;justify-content:center;'
            'overflow:hidden">%s</div>'
            '<div style="padding:1.25rem 1.25rem 1.5rem;flex:1;display:flex;flex-direction:column;'
            'justify-content:flex-end"><h3 style="font-family:var(--font-display), Georgia, serif;'
            'font-weight:400;font-size:.85rem;line-height:1.3;margin:0 0 .6rem;color:var(--ink);'
            'display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">%s</h3>'
            '<p style="font-size:.8rem;color:var(--muted-text);line-height:1.4;margin:0;display:-webkit-box;'
            '-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden">%s</p></div></a>'
            % (esc(url), img, esc(baslik), esc(alt)))

def kart_mini(no, url, aktif=False):
    if aktif:
        return ('<span class="badge guclu" style="font-size:.72rem;padding:.3rem .6rem">%s (bu sayfa)</span>'
                % esc(no))
    return ('<a class="button button-outline" href="%s" style="min-height:34px;font-size:.7rem;'
            'display:inline-flex;align-items:center;text-decoration:none">%s</a>' % (esc(url), esc(no)))

# ------------------------------------------------------------------ ana
def main():
    env = json.load(open(ENVF, encoding='utf-8'))
    N = env['nesneler']
    idx = {o['id']: o for o in N}

    # ---- manifest'ten devam ----
    manifest = {'sayfalar': []}
    if os.path.exists(MANF):
        manifest = json.load(open(MANF, encoding='utf-8'))
    for m in manifest.get('sayfalar', []):
        o = idx.get(m['id'])
        if not o: continue
        sayfa_var = os.path.exists(os.path.join(HEDEF, 'products', m['slug'], 'index.html'))
        if sayfa_var:
            o['yayin'] = {'durum': 'uretildi', 'url': m['url'], 'slug': m['slug']}
            o['dogrulama']['sitede'] = True
        else:
            o['yayin']['durum'] = m.get('eski_durum', 'eklenmeye_hazır')
    url_map = {o['id']: o['yayin']['url'] for o in N if o['yayin'].get('url')}

    head, header, footer = sablonlar()

    # ---- üretilecekler ----
    hazir = [o for o in N if o['yayin']['durum'] == 'eklenmeye_hazır']
    bolunecek = [o for o in N if o['yayin']['durum'] == 'set_üyesi_bölünecek']
    for o in bolunecek:
        o['yayin']['_set_baslik_eki'] = True
    hedefler = sorted(hazir + bolunecek, key=lambda o: (o['prefiks'], o['id']))
    print('hazır: %d | set üyesi bölünecek: %d' % (len(hazir), len(bolunecek)))

    maxn = 0
    pdir = os.path.join(HEDEF, 'products')
    for d in os.listdir(pdir):
        m = re.match(r'k3-(\d+)-', d)
        if m: maxn = max(maxn, int(m.group(1)))

    yeni_manifest = [m for m in manifest.get('sayfalar', []) if m.get('id') in idx]
    n = maxn
    uretilen = 0
    for o in hedefler:
        sl_mevcut = o['yayin'].get('slug')
        if sl_mevcut and os.path.exists(os.path.join(pdir, sl_mevcut, 'index.html')):
            continue
        n += 1
        ad = o['baslik']
        if o.get('set') and o['set'].get('uye_sayisi', 0) > 1 and o['set'].get('uye_sira'):
            ad = '%s (%d/%d)' % (ad, o['set']['uye_sira'], o['set']['uye_sayisi'])
        sl = 'k3-%d-%s' % (n, slugify(ad))
        url = '/products/' + sl
        icerik = sayfa_uret(o, head, header, footer, url_map, idx)
        d = os.path.join(pdir, sl)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(icerik)
        o['yayin'] = {'durum': 'uretildi', 'url': url, 'slug': sl}
        o['dogrulama']['sitede'] = True
        url_map[o['id']] = url
        yeni_manifest.append({'id': o['id'], 'slug': sl, 'url': url, 'baslik': o['baslik'],
                              'koleksiyon': o['koleksiyon'], 'cilt': o['hiyerarsi'].get('cilt'),
                              'sayfa': (o.get('kitap') or {}).get('sayfa'),
                              'tur': 'set_üyesi' if o in bolunecek else 'yeni'})
        uretilen += 1
    print('bu çalışmada üretilen: %d sayfa (k3-%d … k3-%d)' % (uretilen, maxn + 1, n))

    # ikinci geçiş: ilişkili bağlantılar artık tam — üretilen sayfaları tazele
    for m in yeni_manifest:
        o = idx.get(m['id'])
        if not o: continue
        yol = os.path.join(pdir, m['slug'], 'index.html')
        if os.path.exists(yol):
            icerik = sayfa_uret(o, head, header, footer, url_map, idx)
            open(yol, 'w', encoding='utf-8').write(icerik)

    # ---- set ana sayfalarına üye çubukları ----
    setler = collections.defaultdict(list)
    for o in N:
        if o.get('set') and o['set'].get('uye_sayisi', 0) > 1 and o['set'].get('set_sayfasi'):
            setler[o['set']['set_sayfasi']].append(o)
    for set_url, uyeler in setler.items():
        rel = set_url.lstrip('/').split('/')[1] if set_url.startswith('/products/') else None
        if not rel: continue
        sayfa = os.path.join(pdir, rel, 'index.html')
        if not os.path.exists(sayfa): continue
        uyeler.sort(key=lambda x: x['set'].get('uye_sira') or 0)
        t = open(sayfa, encoding='utf-8').read()
        st = uyeler[0]['set']
        chips = ''.join(kart_mini('%s%s' % (u['envanter_gosterim'],
                                  ' · %d/%d' % (u['set'].get('uye_sira', 0), st['uye_sayisi'])
                                  if st['uye_sayisi'] > 1 else ''),
                        u['yayin'].get('url', '#'), aktif=(u['yayin'].get('url') == set_url))
                        for u in uyeler if u['yayin'].get('url'))
        blok = ('<div class="related-section"><div class="related-item"><p class="tag">'
                '🧩 Set Üyeleri — %s (%d nesne)</p><div style="display:flex;flex-wrap:wrap;gap:.45rem;'
                'margin-top:.5rem">%s</div><p style="font-size:.75rem;color:var(--muted-text);'
                'margin-top:.6rem">Kitapta tek künyede geçen bu grup, her nesne kendi envanter '
                'numarasıyla ayrı sayfaya bölündü.</p></div></div>'
                % (esc(st.get('ham', '')), st['uye_sayisi'], chips))
        t = re.sub(re.escape(M_BAS) + r'.*?' + re.escape(M_BIT), '', t, flags=re.S)
        if '<footer' in t:
            t = t.replace('<footer', M_BAS + blok + M_BIT + '<footer', 1)
        open(sayfa, 'w', encoding='utf-8').write(t)
    print('set ana sayfası güncellendi: %d' % len(setler))

    # ---- products/index.html ----
    yeni_kayitlar = [idx[m['id']] for m in yeni_manifest if m.get('id') in idx]
    ipath = os.path.join(pdir, 'index.html')
    t = open(ipath, encoding='utf-8').read()
    kartlar = ''.join(kart(o['yayin']['url'],
                           o['baslik'] + (' (%d/%d)' % (o['set']['uye_sira'], o['set']['uye_sayisi'])
                                          if o.get('set') and o['set'].get('uye_sayisi', 0) > 1
                                          and o['set'].get('uye_sira', 0) > 0 else ''),
                           '%s · %s s.%s' % (o['envanter_gosterim'], o['hiyerarsi'].get('cilt') or '',
                                             (o.get('kitap') or {}).get('sayfa') or ''),
                           (o.get('gorseller') or [{}])[0].get('url'))
                      for o in sorted(yeni_kayitlar, key=lambda x: x['yayin']['slug']))
    t = re.sub(re.escape(M_BAS) + r'.*?' + re.escape(M_BIT), '', t, flags=re.S)
    pos = t.rfind('</a></section>')
    if pos > 0:
        t = t[:pos + 4] + M_BAS + kartlar + M_BIT + t[pos + 4:]
    # kategori sayaçları (index.html her çalıştırmada git'ten temiz döndürüldüğü
    # için delta bir kez uygulanır — bkz. modül docstring'i ve calistir notu)
    delta = collections.Counter(o['koleksiyon'] for o in yeni_kayitlar)
    t = re.sub(r'(<a href="/koleksiyonlar/[^"]+/tumu/"[^>]*>)([^<>]+) \((\d+)\)</a>',
               lambda mo: button_fix2(mo, delta), t)
    # Antik Objeler düğmesi
    if delta.get('Antik Objeler') and 'koleksiyonlar/antik-objeler/tumu/' not in t:
        dugme = ('<a href="/koleksiyonlar/antik-objeler/tumu/" class="button button-outline" '
                 'style="min-height:40px;font-size:.68rem;display:inline-flex;align-items:center;'
                 'text-decoration:none">Antik Objeler (%d)</a>' % delta['Antik Objeler'])
        t = t.replace('<input type="search"', dugme + '<input type="search"', 1)
    open(ipath, 'w', encoding='utf-8').write(t)

    # ---- koleksiyonlar/<slug>/tumu ----
    for kol, adet in delta.items():
        slugk = KOL_SLUG.get(kol, slugify(kol))
        tp = os.path.join(HEDEF, 'koleksiyonlar', slugk, 'tumu', 'index.html')
        nes = [o for o in yeni_kayitlar if o['koleksiyon'] == kol]
        if not os.path.exists(tp):
            continue
        tt = open(tp, encoding='utf-8').read()
        tt = re.sub(re.escape(M_BAS) + r'.*?' + re.escape(M_BIT), '', tt, flags=re.S)
        kartlar2 = ''.join(kart(o['yayin']['url'], o['baslik'], o['envanter_gosterim'],
                                (o.get('gorseller') or [{}])[0].get('url')) for o in nes)
        pos2 = tt.rfind('</a></section>')
        if pos2 > 0:
            tt = tt[:pos2 + 4] + M_BAS + kartlar2 + M_BIT + tt[pos2 + 4:]
        # başlık sayacı: "Tıp — 53 Eser" -> +delta (sayfa git'ten temiz gelir)
        tt = re.sub(r'(%s — )(\d+)( Eser)' % re.escape(kol),
                    lambda mo: '%s%d%s' % (mo.group(1), int(mo.group(2)) + adet, mo.group(3)),
                    tt, count=1)
        open(tp, 'w', encoding='utf-8').write(tt)
    print('koleksiyon sayfaları güncellendi:', dict(delta))

    # ---- antik-objeler/tumu yeniden üret (tam liste) ----
    antikler = sorted([o for o in N if o['koleksiyon'] == 'Antik Objeler' and o['yayin'].get('url')],
                      key=lambda o: o['id'])
    tmpl_path = os.path.join(HEDEF, 'koleksiyonlar', 'askeri-teknoloji', 'tumu', 'index.html')
    if os.path.exists(tmpl_path) and antikler:
        tt = open(tmpl_path, encoding='utf-8').read()
        tt = re.sub(re.escape(M_BAS) + r'.*?' + re.escape(M_BIT), '', tt, flags=re.S)
        kabuk = tt[:tt.index('<nav aria-label="breadcrumb"')]
        footer_k = tt[tt.index('<footer'):]
        kabuk = re.sub(r'<title>.*?</title>', '<title>Antik Objeler — Tüm Eserler — HETEGA</title>',
                       kabuk, count=1, flags=re.S)
        kartlar3 = ''.join(kart(o['yayin']['url'], o['baslik'], o['envanter_gosterim'],
                                (o.get('gorseller') or [{}])[0].get('url')) for o in antikler)
        sayfa = kabuk + (
            '<nav aria-label="breadcrumb" style="padding:1.5rem 4.5vw 0;font-size:.75rem;'
            'color:var(--muted-text);font-family:var(--font-body)"><a href="/" style="color:inherit">'
            'Anasayfa</a> / <a href="/#koleksiyonlar" style="color:inherit">Koleksiyonlar</a> / '
            '<span style="color:var(--ink)">Antik Objeler — Tüm Eserler</span></nav>\n'
            '<section style="padding:2.5rem 4.5vw 1rem;max-width:900px">'
            '<p class="eyebrow">HETEGA · Antik Objeler</p>'
            '<h1 style="font-family:var(--font-display), Georgia, serif;font-weight:700;'
            'font-size:clamp(2rem,4vw,3rem);color:var(--ink);line-height:1.1;margin:.5rem 0 0">'
            'Antik Objeler — %d Eser</h1>'
            '<p style="color:var(--muted-text);font-size:.85rem;margin-top:.8rem;line-height:1.7">'
            'Kitabın 13. bölümü (Cilt V): metal, cam, seramik, ahşap ve taş objeler ile '
            'Orientleştirici üslupta Avrupa cam ve seramikleri.</p></section>\n'
            '<section style="padding:2rem 4.5vw 5rem;display:grid;grid-template-columns:'
            'repeat(auto-fill, minmax(240px, 1fr));gap:2rem 1.5rem">%s%s%s</section>\n'
            % (len(antikler), M_BAS, kartlar3, M_BIT)) + footer_k
        kdir = os.path.join(HEDEF, 'koleksiyonlar', 'antik-objeler', 'tumu')
        os.makedirs(kdir, exist_ok=True)
        open(os.path.join(kdir, 'index.html'), 'w', encoding='utf-8').write(sayfa)
        print('antik-objeler/tumu yeniden üretildi: %d kart' % len(antikler))

    # ---- sitemap ----
    spath = os.path.join(HEDEF, 'sitemap.xml')
    st = open(spath, encoding='utf-8').read()
    st = re.sub(re.escape(M_BAS) + r'.*?' + re.escape(M_BIT), '', st, flags=re.S)
    bugun = datetime.date.today().isoformat()
    ekler = ''.join('<url><loc>https://hetega.com%s/</loc><lastmod>%s</lastmod></url>'
                    % (m['url'], bugun) for m in yeni_manifest)
    st = st.replace('</urlset>', M_BAS + ekler + M_BIT + '</urlset>')
    open(spath, 'w', encoding='utf-8').write(st)

    # ---- envanter + manifest kaydet ----
    for o in N:
        o['yayin'].pop('_set_baslik_eki', None)
    json.dump(env, open(ENVF, 'w'), ensure_ascii=False, indent=1)
    json.dump({'uretim_tarihi': bugun, 'sayfa_sayisi': len(yeni_manifest),
               'hedef': HEDEF, 'sayfalar': yeni_manifest},
              open(MANF, 'w'), ensure_ascii=False, indent=1)
    print('manifest: %d sayfa | envanter.json güncellendi' % len(yeni_manifest))


def button_fix2(mo, delta):
    href, ad, sayi = mo.group(1), mo.group(2), int(mo.group(3))
    mslug = re.search(r'/koleksiyonlar/([^/]+)/tumu/', href)
    if mslug:
        kol = next((k for k, v in KOL_SLUG.items() if v == mslug.group(1)), None)
        if kol and kol in delta:
            return '%s%s (%d)</a>' % (href, ad, sayi + delta[kol])
    return mo.group(0)


if __name__ == '__main__':
    main()
