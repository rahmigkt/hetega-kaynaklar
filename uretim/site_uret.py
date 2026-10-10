# -*- coding: utf-8 -*-
"""
HETEGA — Site Üreteci

envanter.json'dan, mevcut sitenin tasarım şablonunu birebir kullanarak
yeni nesne sayfaları üretir ve index/koleksiyon/sitemap dosyalarını günceller.

Kapsam (bu sürüm):
  * yayin.durum == 'eklenmeye_hazır' olan nesneler -> /products/k3-<n>-<slug>/
  * products/index.html      -> yeni kartlar + kategori sayaçları + Antik Objeler düğmesi
  * koleksiyonlar/antik-objeler/(tumu) -> yeni koleksiyon sayfaları
  * sitemap.xml              -> yeni URL'ler

Çıktı: hedef working-tree'ye yazılır + uretim_manifest.json üretilir.
"""
import re, os, json, html, sys, unicodedata, collections, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
try:
    import yollar
    ENVF = os.path.join(yollar.ENV, 'envanter.json')
    HEDEF = os.environ.get('HETEGA_WEBSITE', yollar.WEBSITE)
except ImportError:
    ENVF = os.path.join(HERE, 'envanter.json')
    HEDEF = os.environ.get('HETEGA_WEBSITE', '/home/user/hetega-website')

# ------------------------------------------------------------------ yardımcı
TR = {'ç':'c','ğ':'g','ı':'i','i':'i','ö':'o','ş':'s','ü':'u','â':'a','î':'i','û':'u',
      'ʿ':'','ʾ':'','’':"'",'«':'','»':'','‘':"'",'é':'e','ā':'a','ī':'i','ū':'u',
      'ḥ':'h','ḳ':'k','ṣ':'s','ṭ':'t','ẓ':'z','ñ':'n','ā':'a'}

def slugify(s, maxlen=58):
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = ''.join(TR.get(c, c) for c in s).lower()
    s = re.sub(r"[^a-z0-9]+", '-', s).strip('-')
    return s[:maxlen].rstrip('-') or 'nesne'

def esc(s):
    return html.escape(s or '', quote=True).replace('&#x27;', '&#x27;')

def nrm(s):
    return re.sub(r'\s+', ' ', s or '').strip()

# ------------------------------------------------------------------ şablon
def sablonlar():
    """Mevcut bir ürün sayfasından head/header/footer şablonlarını söker."""
    ornek = None
    for kok, dizinler, dosyalar in os.walk(os.path.join(HEDEF, 'products')):
        if os.path.basename(kok).startswith('k3-') and 'index.html' in dosyalar:
            ornek = os.path.join(kok, 'index.html'); break
    t = open(ornek, encoding='utf-8').read()
    head = t[:t.index('<body>') + len('<body>')]
    footer_i = t.index('<footer')
    footer = t[footer_i:]
    # header: banner + site-header (body sonrası, product-mock öncesi)
    bi = t.index('<body>') + 6
    hi = t.index('<div class="product-mock">')
    header = t[bi:hi].lstrip()
    # örnek sayfanın kendi banner'ını sök (yenisini sayfa_uret ekliyor)
    header = re.sub(r'^<div class="deneme-banner">.*?</div>\s*', '', header, flags=re.S)
    assert 'deneme-banner' not in header, 'banner sökülemedi'
    return head, header, footer

BANNER = ('<div class="deneme-banner"><strong>📖 KATALOG</strong> — Fuat Sezgin, '
          'İslam&#x27;da Bilim ve Teknik, %s, s. %s</div>')

def sayfa_uret(o, head, header, footer, iliskili_html):
    h = o['hiyerarsi']; k = o.get('kitap') or {}
    banner = BANNER % (esc(h.get('cilt') or '?'), esc(str(k.get('sayfa') or '?')))
    krumb = ' / '.join(x for x in ['Envanter', esc(o['koleksiyon']),
                                   esc(h.get('alt_bolum') or ''), esc(h.get('alt_baslik') or '')] if x)
    baslik = esc(o['baslik'])
    kisa = ''
    if o.get('ozgun_ad'):
        kisa = '<p class="kisa-aciklama">Özgün ad: %s</p>' % esc(o['ozgun_ad'])
    elif o.get('islev'):
        kisa = '<p class="kisa-aciklama">%s</p>' % esc(o['islev'])

    med = ('<div class="no-image"><span style="font-size:2.4rem">🏺</span>'
           '<span style="font-size:.78rem;line-height:1.6">Görsel hazırlanıyor<br>'
           'kitap figürü işleme sırasında</span></div>')

    spec = [
        ('Kategori', esc(o['koleksiyon'])),
        ('Alt Kategori', esc(h.get('alt_baslik') or h.get('alt_bolum') or '—')),
        ('Yapımcı / Bilgin', esc(o.get('bilgin') or '—')),
        ('Dönem', esc(o.get('donem') or 'belirtilmemiş')),
        ('Menşe', esc(o.get('mense') or '—')),
        ('Kaynak', esc('%s, s. %s' % (h.get('cilt') or '?', k.get('sayfa') or '?'))),
    ]
    specs = ''.join('<div class="spec"><span>%s</span><strong>%s</strong></div>' % s
                    for s in spec)

    oz = []
    mm = nrm(k.get('model_metni') or '')
    if mm:
        oz.append('<li>%s</li>' % esc(mm))
    if o['teknik'].get('malzeme'):
        oz.append('<li>Malzeme: %s</li>' % esc(', '.join(o['teknik']['malzeme'])))
    if o['teknik'].get('boyutlar'):
        oz.append('<li>Ölçüler: %s</li>' % esc('; '.join(o['teknik']['boyutlar'])))
    if o.get('orijinal'):
        oz.append('<li>%s</li>' % esc(o['orijinal']))
    ozellikler = ('<p class="tag">Kitap kaydı</p><ul>%s</ul>' % ''.join(oz)) if oz else ''
    islev_html = ('<p class="tag">İşlevi</p><p class="body-text">%s</p>'
                  % esc(o['islev'])) if o.get('islev') and o.get('ozgun_ad') else \
                 ('' if kisa and o['islev'] in kisa else
                  ('<p class="tag">İşlevi</p><p class="body-text">%s</p>'
                   % esc(o['islev']) if o.get('islev') else ''))

    set_html = ''
    if o.get('set'):
        st = o['set']
        set_html = ('<div class="model-box">Bu nesne kitapta tek künyede geçen %d parçalık '
                    'bir grubun üyesidir: «%s» (%s).</div>'
                    % (st['uye_sayisi'], esc(nrm(st.get('baslik') or '')[:60]),
                       esc(st.get('ham') or '')))

    model_box = '<div class="model-box">Envanter No: %s%s</div>' % (
        esc(o['envanter_gosterim']), ' · Orijinal' if o['prefiks'] == 'J' else ' · Enstitü modeli')

    notlar = ''.join('<p class="body-text" style="font-size:.8rem;color:var(--muted-text)">%s</p>'
                     % esc(x) for x in o['dogrulama'].get('notlar', [])
                     if x.startswith('İNSAN') or x.startswith('BAŞLIK'))

    title = '%s — HETEGA' % baslik
    head2 = head.replace('<title>es-Siczî&#x27;nin Planetaryumu — HETEGA</title>',
                         '<title>%s</title>' % title)
    head2 = re.sub(r'<title>.*?</title>', '<title>%s</title>' % title, head2, count=1, flags=re.S)

    return f'''{head2}
{banner}{header}
<div class="product-mock"><div class="product-detail">
  <div class="media-col">
    <div class="product-detail-image" id="main-img-box">{med}</div>
  </div>
  <div class="copy-col">
    <a class="product-back" href="/products"><span>←</span> Envantere dön</a>
    <p class="product-breadcrumb"><span>{krumb.replace(' / ', '</span> / <span>')}</span></p>
    <p class="eyebrow">{esc(o['envanter_gosterim'])} · {esc(o['koleksiyon'])}</p><h1>{baslik}</h1>
    {kisa}
    <div class="spec-row">{specs}</div>
    <div class="uzun-aciklama">
      {islev_html}
      {ozellikler}
      {set_html}
      {model_box}
      {notlar}
    </div>
    {iliskili_html}
'''

FOOTER_KAPAT = '</div></div>'

def iliskili(o, url_map, idx_nesne):
    """Aynı set üyeleri + aynı alt başlık kardeşleri."""
    ogeler = []
    def ekle(x, etiket):
        if x['id'] == o['id']: return
        u = url_map.get(x['id'])
        ad = esc(nrm(x['baslik'])[:60])
        if u:
            ogeler.append('<div class="related-item"><div class="ri-head"><h4><a href="%s" '
                          'style="color:inherit;text-decoration:none">%s</a></h4>'
                          '<span class="badge guclu">%s</span></div>'
                          '<p style="font-size:.8rem;color:var(--muted-text)">%s · %s s.%s</p></div>'
                          % (u, ad, etiket, esc(x['envanter_gosterim']),
                             esc(x['hiyerarsi'].get('cilt') or ''), esc(str((x.get('kitap') or {}).get('sayfa') or ''))))
    if o.get('set'):
        for uid in o['set'].get('uyeler', []):
            if uid in idx_nesne: ekle(idx_nesne[uid], 'set üyesi')
    kardes = [x for x in idx_nesne.values()
              if x['hiyerarsi'].get('alt_baslik') and
              x['hiyerarsi']['alt_baslik'] == o['hiyerarsi'].get('alt_baslik')
              and x['id'] != o['id']][:5]
    for x in kardes:
        ekle(x, 'aynı bölüm')
    if not ogeler:
        return ''
    return ('<div class="related-section"><p class="tag">📜 İlişkili Kayıtlar</p>%s</div>'
            % ''.join(ogeler[:8]))

# ------------------------------------------------------------------ index kartı
KART = ('<a href="/products/{slug}" style="display:flex;flex-direction:column;color:inherit;'
        'text-decoration:none;background:radial-gradient(ellipse at 50% 30%, var(--card-bg) 0%, '
        'var(--card-bg) 55%, rgba(0,0,0,.1) 100%);border-radius:2px;box-shadow:0 18px 40px -14px '
        'rgba(0,0,0,.4), 0 4px 10px rgba(0,0,0,.15);overflow:hidden">'
        '<div style="aspect-ratio:1/1;display:flex;align-items:center;justify-content:center;'
        'overflow:hidden;background:var(--card-bg)"><span style="font-size:2.2rem;opacity:.5">🏺</span></div>'
        '<div style="padding:1.25rem 1.25rem 1.5rem;flex:1;display:flex;flex-direction:column;'
        'justify-content:flex-end"><h3 style="font-family:var(--font-display), Georgia, serif;'
        'font-weight:400;font-size:.85rem;line-height:1.3;margin:0 0 .6rem;color:var(--ink);'
        'display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">{baslik}</h3>'
        '<p style="font-size:.8rem;color:var(--muted-text);line-height:1.4;margin:0;display:-webkit-box;'
        '-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden">{alt}</p></div></a>')

# ------------------------------------------------------------------ ana
def main():
    env = json.load(open(ENVF, encoding='utf-8'))
    N = env['nesneler']
    idx_nesne = {o['id']: o for o in N}

    head, header, footer = sablonlar()

    # mevcut slug -> id haritası (yayındakiler)
    url_map = {}
    for o in N:
        if o['yayin'].get('url'):
            url_map[o['id']] = o['yayin']['url']

    hazir = [o for o in N if o['yayin']['durum'] == 'eklenmeye_hazır']
    hazir.sort(key=lambda o: (o['prefiks'], o['id']))
    print('üretilecek sayfa: %d' % len(hazir))

    # slug numaralandırma: mevcut en yüksek k3-<n>
    maxn = 0
    pdir = os.path.join(HEDEF, 'products')
    for d in os.listdir(pdir):
        m = re.match(r'k3-(\d+)-', d)
        if m: maxn = max(maxn, int(m.group(1)))
    print('mevcut en yüksek ürün no: %d' % maxn)

    manifest = []
    n = maxn
    for o in hazir:
        n += 1
        sl = 'k3-%d-%s' % (n, slugify(o['baslik']))
        url = '/products/' + sl
        o['yayin']['slug'] = sl
        o['yayin']['url'] = url
        o['yayin']['durum'] = 'uretildi'
        url_map[o['id']] = url
        icerik = sayfa_uret(o, head, header, footer, iliskili(o, url_map, idx_nesne)) + \
                 FOOTER_KAPAT + footer
        yol = os.path.join(pdir, sl)
        os.makedirs(yol, exist_ok=True)
        open(os.path.join(yol, 'index.html'), 'w', encoding='utf-8').write(icerik)
        manifest.append({'id': o['id'], 'slug': sl, 'url': url,
                         'baslik': o['baslik'], 'koleksiyon': o['koleksiyon'],
                         'cilt': o['hiyerarsi'].get('cilt'),
                         'sayfa': (o.get('kitap') or {}).get('sayfa')})

    # ------------------------------------------------ products/index.html
    ipath = os.path.join(pdir, 'index.html')
    t = open(ipath, encoding='utf-8').read()
    kartlar = ''.join(KART.format(slug=m['slug'], baslik=esc(m['baslik']),
                                  alt=esc('%s · %s' % (m['id'].replace('SITE-', ''),
                                      (m['cilt'] or '') + (' s.%s' % m['sayfa'] if m['sayfa'] else ''))))
                      for m in manifest)
    if kartlar:
        # kartlar 2. <section> içinde; son kartın kapanışından hemen önce ekle
        pos = t.rfind('</a></section>')
        if pos > 0:
            t = t[:pos + len('</a>')] + kartlar + t[pos + len('</a>'):]
        else:
            t = t.replace('</section>', kartlar + '</section>', 1)
    # kategori sayaçları: yeni koleksiyonlara göre güncelle
    yeni_say = collections.Counter(m['koleksiyon'] for m in manifest)
    SITE_ESLEME = {'Coğrafya ve Seyrüsefer': 'coğrafya-ve-seyrüsefer', 'Tesviye ve Geometri': 'tesviye-ve-geometri',
                   'Saatler': 'saatler', 'Kimya': 'kimya', 'Tıp': 'tip', 'Astronomi': 'astronomi',
                   'Fizik ve Teknik': 'fizik-ve-teknik', 'Askeri Teknoloji': 'askeri-teknoloji',
                   'Mimari': 'mimari', 'Optik': 'optik'}
    for kol, adet in yeni_say.items():
        slugk = SITE_ESLEME.get(kol, slugify(kol))
        m = re.search(r'(/koleksiyonlar/%s/tumu/"[^>]*>)%s \((\d+)\)' % (re.escape(slugk), re.escape(kol)), t)
        if m:
            t = t[:m.start()] + m.group(1) + '%s (%d)' % (kol, int(m.group(2)) + adet) + t[m.end():]
        elif adet >= 5:   # Antik Objeler gibi yeni koleksiyon -> düğme ekle
            dugme = ('<a href="/koleksiyonlar/%s/tumu/" class="button button-outline" '
                     'style="min-height:40px;font-size:.68rem;display:inline-flex;align-items:center;'
                     'text-decoration:none">%s (%d)</a>' % (slugk, kol, adet))
            t = t.replace('<input type="search"', dugme + '<input type="search"', 1)
    open(ipath, 'w', encoding='utf-8').write(t)

    # ---------------------------------------------- yeni koleksiyon sayfası
    # Antik Objeler sitede yoktu; /koleksiyonlar/antik-objeler/tumu/ üret
    if yeni_say.get('Antik Objeler'):
        tmpl_path = os.path.join(HEDEF, 'koleksiyonlar', 'askeri-teknoloji', 'tumu', 'index.html')
        tt = open(tmpl_path, encoding='utf-8').read()
        govde_bas = tt.index('<nav aria-label="breadcrumb"')
        kabuk_head = tt[:govde_bas]
        footer_k = tt[tt.index('<footer'):]
        antikler = [o for o in N if o['koleksiyon'] == 'Antik Objeler'
                    and o['yayin'].get('url')]
        antikler.sort(key=lambda o: o['id'])
        kartlar2 = ''.join(
            ('<a href="%s" style="display:flex;flex-direction:column;color:inherit;text-decoration:none;'
             'background:radial-gradient(ellipse at 50%% 30%%, var(--card-bg) 0%%, var(--card-bg) 55%%, '
             'rgba(0,0,0,.1) 100%%);border-radius:2px;box-shadow:0 18px 40px -14px rgba(0,0,0,.4), '
             '0 4px 10px rgba(0,0,0,.15);overflow:hidden">'
             '<div style="aspect-ratio:1/1;display:flex;align-items:center;justify-content:center;overflow:hidden">'
             '%s</div>'
             '<div style="padding:1.25rem 1.25rem 1.5rem;flex:1;display:flex;flex-direction:column;'
             'justify-content:flex-end"><h3 style="font-family:var(--font-display), Georgia, serif;'
             'font-weight:400;font-size:.85rem;line-height:1.3;margin:0 0 .6rem;color:var(--ink);'
             'display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">%s</h3>'
             '<p style="font-size:.8rem;color:var(--muted-text);line-height:1.4;margin:0">%s</p></div></a>')
            % (o['yayin']['url'],
               ('<img src="%s" alt="%s" loading="lazy" style="width:100%%;height:100%%;object-fit:contain;'
                'padding:1.25rem"/>' % (o['gorseller'][0]['url'], esc(o['baslik'])))
               if o.get('gorseller') else '<span style="font-size:2.2rem;opacity:.5">🏺</span>',
               esc(o['baslik']), esc(o['envanter_gosterim']))
            for o in antikler)
        sayfa = kabuk_head.replace('<title>Askeri Teknoloji — Tüm Eserler — HETEGA</title>',
                                   '<title>Antik Objeler — Tüm Eserler — HETEGA</title>')
        sayfa = re.sub(r'<title>.*?</title>', '<title>Antik Objeler — Tüm Eserler — HETEGA</title>',
                       sayfa, count=1, flags=re.S)
        sayfa += (
            '<nav aria-label="breadcrumb" style="padding:1.5rem 4.5vw 0;font-size:.75rem;'
            'color:var(--muted-text);font-family:var(--font-body)"><a href="/" style="color:inherit">'
            'Anasayfa</a> / <span style="color:var(--ink)">Antik Objeler — Tüm Eserler</span></nav>\n'
            '<section style="padding:2.5rem 4.5vw 1rem;max-width:900px">'
            '<p class="eyebrow">HETEGA · Antik Objeler</p>'
            '<h1 style="font-family:var(--font-display), Georgia, serif;font-weight:700;'
            'font-size:clamp(2rem,4vw,3rem);color:var(--ink);line-height:1.1;margin:.5rem 0 0">'
            'Antik Objeler — %d Eser</h1>'
            '<p style="color:var(--muted-text);font-size:.85rem;margin-top:.8rem;line-height:1.7">'
            'Kitabın 13. bölümü (Cilt V): metal, cam, seramik, ahşap ve taş objeler ile '
            'Orientleştirici üslupta Avrupa cam ve seramikleri.</p></section>\n'
            '<section style="padding:2rem 4.5vw 5rem;display:grid;grid-template-columns:'
            'repeat(auto-fill, minmax(240px, 1fr));gap:2rem 1.5rem">%s</section>\n'
            % (len(antikler), kartlar2)) + footer_k
        kdir = os.path.join(HEDEF, 'koleksiyonlar', 'antik-objeler', 'tumu')
        os.makedirs(kdir, exist_ok=True)
        open(os.path.join(kdir, 'index.html'), 'w', encoding='utf-8').write(sayfa)
        print('koleksiyonlar/antik-objeler/tumu/ üretildi (%d kart)' % len(antikler))

    # ------------------------------------------------ sitemap.xml
    spath = os.path.join(HEDEF, 'sitemap.xml')
    st = open(spath, encoding='utf-8').read()
    bugun = datetime.date.today().isoformat()
    ekler = ''.join('<url><loc>https://hetega.com%s/</loc><lastmod>%s</lastmod></url>'
                    % (m['url'], bugun) for m in manifest)
    st = st.replace('</urlset>', ekler + '</urlset>')
    open(spath, 'w', encoding='utf-8').write(st)

    # ------------------------------------------------ envanter.json güncelle
    json.dump(env, open(ENVF, 'w'), ensure_ascii=False, indent=1)
    man_yol = os.path.join(os.path.dirname(ENVF), 'uretim_manifest.json')
    json.dump({'uretim_tarihi': bugun, 'sayfa_sayisi': len(manifest),
               'hedef': HEDEF, 'sayfalar': manifest},
              open(man_yol, 'w'), ensure_ascii=False, indent=1)

    print('üretilen: %d sayfa' % len(manifest))
    print('index + sitemap güncellendi; koleksiyon düğmeleri:', dict(yeni_say))
    print('manifest -> %s' % man_yol)
    for m in manifest[:8]:
        print('   %-10s %s' % (m['id'], m['url']))


if __name__ == '__main__':
    main()
