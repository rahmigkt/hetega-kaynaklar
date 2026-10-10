# -*- coding: utf-8 -*-
"""
HETEGA — Sergi Sayfası Üreteci

sergi_motoru.coz() çıktısını sitenin tasarım dilinde HTML sayfalarına çevirir:
  /sergiler/<slug>/   sergi sayfası
  /sergiler/          sergiler dizini
İdempotenttir: her çalıştırmada yeniden üretir; sitemap'e SERGI-V1 işaretçi
bloğuyla URL ekler.
"""
import re, os, json, sys, html, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sergi_motoru
try:
    import yollar
    HEDEF = os.environ.get('HETEGA_WEBSITE', yollar.WEBSITE)
    SERGI_DIR = yollar.SERGI
    ENVF = os.path.join(yollar.ENV, 'envanter.json')
except ImportError:
    HEDEF = os.environ.get('HETEGA_WEBSITE', '/home/user/hetega-website')
    SERGI_DIR = os.path.join(HERE, '..', 'sergiler')
    ENVF = os.path.join(HERE, 'envanter.json')

def esc(s): return html.escape(str(s if s is not None else ''), quote=True)

ROMEN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']

EXTRA_CSS = '''
<style>
.sergi-hero{background:linear-gradient(rgba(10,32,48,.88),rgba(10,32,48,.92)),url("__KAPAK__") center/cover no-repeat;color:#f3ede1;padding:clamp(3rem,8vw,6rem) 5vw clamp(2.4rem,5vw,4rem);text-align:center}
.sergi-hero .eyebrow{font-size:.72rem;letter-spacing:.22em;text-transform:uppercase;color:#c9a86a;margin:0 0 1rem;font-weight:700}
.sergi-hero h1{font-family:"Cinzel","EB Garamond",Georgia,serif;font-weight:700;font-size:clamp(2rem,5vw,3.4rem);margin:0 0 1rem;line-height:1.15}
.sergi-hero .alt{font-family:"EB Garamond",Georgia,serif;font-style:italic;font-size:clamp(1rem,2vw,1.2rem);color:#d8cdb8;max-width:760px;margin:0 auto 1.2rem;line-height:1.6}
.sergi-hero .aciklama{font-size:.88rem;color:#b9c3cc;max-width:720px;margin:0 auto 1.6rem;line-height:1.75}
.sergi-meta{display:flex;gap:.6rem;justify-content:center;flex-wrap:wrap}
.sergi-meta span{border:1px solid rgba(243,237,225,.3);border-radius:999px;padding:.34rem .9rem;font-size:.72rem;letter-spacing:.03em}
.bolum{padding:2.6rem 5vw;max-width:1240px;margin:0 auto}
.bolum + .bolum{border-top:1px solid var(--line,#e2e2e2)}
.bolum .roma{font-family:"Cinzel",Georgia,serif;color:#b6874f;font-size:.85rem;letter-spacing:.3em;text-transform:uppercase;margin:0 0 .5rem;font-weight:600}
.bolum h2{font-family:"Cinzel","EB Garamond",Georgia,serif;font-size:clamp(1.5rem,3vw,2.1rem);margin:0 0 .8rem;line-height:1.2;font-weight:700}
.bolum .giris{font-family:"EB Garamond",Georgia,serif;font-size:1.02rem;color:#55504a;line-height:1.75;max-width:820px;margin:0 0 1.8rem}
.grup{margin:1.6rem 0 2rem}
.grup-head{display:flex;align-items:baseline;gap:.7rem;flex-wrap:wrap;border-bottom:1px solid rgba(182,135,79,.35);padding-bottom:.5rem;margin-bottom:1rem}
.grup-head h3{font-family:"Cinzel",Georgia,serif;font-size:1.08rem;margin:0;font-weight:600}
.grup-head .adet{font-size:.72rem;color:#6b7280;background:#f0ead9;border-radius:999px;padding:.16rem .6rem}
.grup-head .alt{font-size:.74rem;color:#8a6238;font-style:italic}
.ozet-ust{display:flex;align-items:center;gap:.9rem;margin-bottom:.7rem}
.ozet-mark{width:44px;height:44px;border:1px solid #b6874f;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:"Cinzel",serif;color:#8a6238;font-size:1.05rem;flex:none}
.kartlar{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:1.3rem 1rem}
.nkart{display:flex;flex-direction:column;color:inherit;text-decoration:none;background:radial-gradient(ellipse at 50% 30%,#ececec 0%,#ececec 55%,rgba(0,0,0,.08) 100%);border-radius:4px;box-shadow:0 10px 24px -12px rgba(0,0,0,.35);overflow:hidden;border:1px solid rgba(0,0,0,.05)}
.nkart .im{aspect-ratio:1/1;display:flex;align-items:center;justify-content:center;overflow:hidden}
.nkart .im img{width:100%;height:100%;object-fit:contain;padding:.8rem}
.nkart .bd{padding:.7rem .8rem .9rem;display:flex;flex-direction:column;gap:.3rem;flex:1}
.nkart h4{font-family:"EB Garamond",Georgia,serif;font-weight:600;font-size:.86rem;margin:0;line-height:1.35;color:#3c4654}
.nkart .no{font-family:ui-monospace,Menlo,monospace;font-size:.66rem;color:#8a6238;font-weight:700}
.nkart .bl{font-size:.68rem;color:#6b7280;line-height:1.4}
.nkart.yakinda{opacity:.75}
.yakinda-rozet{font-size:.6rem;letter-spacing:.06em;text-transform:uppercase;color:#fff;background:#9aa0a8;border-radius:3px;padding:.1rem .4rem;align-self:flex-start}
.tseridi{display:flex;flex-direction:column;gap:.5rem}
.tsatir{display:grid;grid-template-columns:190px 1fr;gap:1rem;align-items:baseline;border-bottom:1px dashed #e2e2e2;padding:.55rem .2rem}
.tsatir .don{font-size:.74rem;color:#8a6238;font-weight:600}
.tsatir a{color:inherit;text-decoration:none;font-size:.9rem}
.tsatir a:hover{color:#8a6238}
.tsatir .no{font-family:ui-monospace,monospace;font-size:.68rem;color:#6b7280;margin-right:.5rem}
.sergi-not{font-size:.72rem;color:#9aa0a8;margin-top:1.2rem;font-style:italic}
.sergi-liste{padding:3rem 5vw;max-width:1100px;margin:0 auto}
.sergi-karti{display:block;border:1px solid #e2e2e2;border-radius:12px;overflow:hidden;text-decoration:none;color:inherit;background:#fff;box-shadow:0 14px 34px -18px rgba(0,0,0,.35);margin-bottom:1.4rem}
.sergi-karti .kapak{height:190px;background:linear-gradient(rgba(10,32,48,.55),rgba(10,32,48,.75)),url("__KAPAK__") center/cover}
.sergi-karti .ic{padding:1.2rem 1.4rem 1.5rem}
.sergi-karti h3{font-family:"Cinzel",Georgia,serif;margin:0 0 .4rem;font-size:1.25rem}
.sergi-karti p{margin:0;color:#6b7280;font-size:.84rem;line-height:1.6}
.sergi-karti .meta{margin-top:.7rem;font-size:.7rem;letter-spacing:.05em;text-transform:uppercase;color:#b6874f;font-weight:700}
@media(max-width:640px){.tsatir{grid-template-columns:1fr}.kartlar{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}}
</style>'''


def kabuk(HEDEF):
    """Koleksiyon sayfasından head/header/footer kabuğu al."""
    ornek = os.path.join(HEDEF, 'koleksiyonlar', 'askeri-teknoloji', 'tumu', 'index.html')
    t = open(ornek, encoding='utf-8').read()
    head = t[:t.index('<body>') + len('<body>')]
    bi = t.index('<body>') + 6
    hi = t.index('<nav aria-label="breadcrumb"')
    header = t[bi:hi]
    header = re.sub(r'<style>astro-island[^<]*</style>\s*', '', header)
    footer = t[t.index('<footer'):]
    return head, header, footer


def nesne_kart(n, yakinda_rozet=True):
    url = n.get('yayin.url') or n.get('_url') or ''
    g = (n.get('gorseller') or [{}])
    gurl = g[0].get('url') if isinstance(g[0], dict) else ''
    im = ('<img src="%s" alt="%s" loading="lazy">' % (esc(gurl), esc(n.get('baslik')))) \
        if gurl else '<span style="font-size:1.9rem;opacity:.5">🏺</span>'
    bl = ' · '.join(x for x in [n.get('bilgin_kanonik') or '', n.get('donem') or ''] if x)
    ic = '<div class="bd">%s<span class="no">%s</span><h4>%s</h4>%s</div>' % (
        '<span class="yakinda-rozet">yakında</span>' if (yakinda_rozet and not url and False) else '',
        esc(n.get('envanter_gosterim') or n.get('_id')), esc(n.get('baslik')),
        ('<span class="bl">%s</span>' % esc(bl)) if bl else '')
    if url:
        return '<a class="nkart" href="%s">%s<div class="im">%s</div>%s</a>' % (esc(url), '', im, ic)
    return '<div class="nkart yakinda"><div class="im">%s</div>%s</div>' % (im, ic)


def bolum_html(b, i):
    out = ['<section class="bolum">']
    out.append('<p class="roma">Bölüm %s</p>' % ROMEN[i] if i < len(ROMEN) else '')
    out.append('<h2>%s</h2>' % esc(b['baslik']))
    if b.get('giris'):
        out.append('<p class="giris">%s</p>' % esc(b['giris']))
    gorunum = b.get('gorunum', 'kart')

    if gorunum == 'zaman-seridi':
        nesneler = b.get('nesneler', [])
        out.append('<div class="tseridi">')
        for n in nesneler:
            url = n.get('yayin.url') or ''
            ad = esc(n.get('baslik'))
            satir = ('<a href="%s">%s%s</a>' % (esc(url),
                     '<span class="no">%s</span>' % esc(n.get('envanter_gosterim')), ad)) \
                    if url else ('%s<span class="no">%s</span>%s' % ('', esc(n.get('envanter_gosterim')), ad))
            out.append('<div class="tsatir"><span class="don">%s</span><span>%s</span></div>'
                       % (esc(n.get('donem') or '—'), satir))
        out.append('</div>')
    elif b.get('gruplar'):
        for g in b['gruplar']:
            out.append('<div class="grup"><div class="grup-head"><h3>%s</h3>'
                       '<span class="adet">%d nesne</span>%s%s</div>'
                       % (esc(g['baslik']), g['nesne_sayisi'],
                          '<span class="alt">%s</span>' % esc(g.get('alt_baslik')) if g.get('alt_baslik') else '',
                          '<span class="alt">%s</span>' % esc(g.get('alan')) if g.get('alan') else ''))
            if gorunum == 'kisi-listesi':
                ilk = (g.get('nesneler') or [{}])[0]
                ad = str(g.get('baslik') or '?')
                out.append('<div class="ozet-ust"><span class="ozet-mark">%s</span>'
                           '<span style="font-size:.8rem;color:#6b7280">%s</span></div>'
                           % (esc(ad[0]), esc(g.get('alt_baslik') or '')))
            out.append('<div class="kartlar">%s</div></div>'
                       % ''.join(nesne_kart(n) for n in g.get('nesneler', [])))
    else:
        out.append('<div class="kartlar">%s</div>'
                   % ''.join(nesne_kart(n) for n in b.get('nesneler', [])))
    if b.get('not'):
        out.append('<p class="sergi-not">Not: %s</p>' % esc(b['not']))
    out.append('</section>')
    return ''.join(out)


def uret(sergi_slug, env, head, header, footer):
    sergi = json.load(open(os.path.join(SERGI_DIR, sergi_slug + '.json'), encoding='utf-8'))
    cozum = sergi_motoru.coz(sergi, env)
    # nesne özetlerine url/bilgin taşımak için envanterden zenginleştir
    zengin = {o['id']: o for o in env['nesneler']}
    def zenginlestir(n):
        o = zengin.get(n.get('_id'))
        if o:
            n['yayin.url'] = o['yayin'].get('url', '')
            n['gorseller'] = o.get('gorseller', [])
            n['donem'] = o.get('donem') or n.get('donem')
            n['bilgin_kanonik'] = o.get('bilgin_kanonik') or n.get('bilgin_kanonik')
        return n
    for b in cozum['bolumler']:
        for n in b.get('nesneler', []): zenginlestir(n)
        for g in b.get('gruplar', []):
            for n in g.get('nesneler', []): zenginlestir(n)

    kapak = cozum.get('kapak_gorsel') or '/kapaklar/astronomi-2614.jpg'
    css = EXTRA_CSS.replace('__KAPAK__', esc(kapak))
    benzersiz = len({n['_id'] for b in cozum['bolumler']
                     for n in (b.get('nesneler', []) +
                               [x for g in b.get('gruplar', []) for x in g.get('nesneler', [])])})
    hero = ('<div class="sergi-hero"><p class="eyebrow">HETEGA · Dijital Sergi</p>'
            '<h1>%s</h1><p class="alt">%s</p><p class="aciklama">%s</p>'
            '<div class="sergi-meta"><span>%d nesne</span><span>%d bölüm</span>'
            '<span>~%d dakika</span><span>%s</span></div></div>'
            % (esc(cozum['baslik']), esc(cozum.get('alt_baslik')), esc(cozum.get('aciklama')),
               benzersiz, len(cozum['bolumler']), cozum.get('sure_dk') or 20,
               esc(', '.join(sergi.get('koleksiyonlar', [])))))
    govde = ''.join(bolum_html(b, i) for i, b in enumerate(cozum['bolumler']))
    tarih = datetime.date.today().isoformat()
    notlar = ('<div class="bolum"><p class="sergi-not">Bu sergi bir veri kopyası değil, tanımdır: '
              'hetega-kaynaklar/sergiler/%s.json dosyasındaki sorgular envanter.json\'a karşı '
              'çözümlenmiştir (%s). Envanter güncellendiğinde sergi de güncellenir.</p></div>'
              % (esc(sergi_slug), tarih))
    title = '%s — Dijital Sergi — HETEGA' % esc(cozum['baslik'])
    head2 = re.sub(r'<title>.*?</title>', '<title>%s</title>' % title, head, count=1, flags=re.S)
    head2 = head2.replace('</head>', css + '</head>') if '</head>' in head2 else head2 + css
    sayfa = head2 + header + hero + govde + notlar + footer

    d = os.path.join(HEDEF, 'sergiler', sergi_slug)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(sayfa)
    print('-> /sergiler/%s/ (%d KB, %d nesne)' % (sergi_slug, len(sayfa) // 1024, benzersiz))
    return {'slug': sergi_slug, 'baslik': cozum['baslik'],
            'alt_baslik': cozum.get('alt_baslik', ''), 'kapak': kapak,
            'nesne': benzersiz, 'bolum': len(cozum['bolumler'])}


def dizin(sergiler, head, header, footer):
    kartlar = ''.join(
        '<a class="sergi-karti" href="/sergiler/%s/"><div class="kapak" '
        'style="background-image:linear-gradient(rgba(10,32,48,.55),rgba(10,32,48,.75)),url(\'%s\')"></div>'
        '<div class="ic"><h3>%s</h3><p>%s</p><p class="meta">%d nesne · %d bölüm</p></div></a>'
        % (esc(s['slug']), esc(s['kapak']), esc(s['baslik']), esc(s['alt_baslik']),
           s['nesne'], s['bolum']) for s in sergiler)
    head2 = re.sub(r'<title>.*?</title>', '<title>Sergiler — HETEGA</title>', head, count=1, flags=re.S)
    css = EXTRA_CSS.replace('__KAPAK__', '/kapaklar/astronomi-2629.jpg')
    head2 = head2.replace('</head>', css + '</head>')
    sayfa = (head2 + header +
             '<section class="sergi-liste"><p class="eyebrow" style="font-size:.72rem;letter-spacing:.2em;'
             'text-transform:uppercase;color:#b6874f;font-weight:700;margin:0 0 .6rem">HETEGA · Dijital Sergiler</p>'
             '<h1 style="font-family:Cinzel,Georgia,serif;font-size:clamp(1.8rem,4vw,2.6rem);margin:0 0 .8rem">'
             'Bilginin izinde sergiler</h1>'
             '<p style="color:#6b7280;font-size:.9rem;max-width:760px;line-height:1.75;margin:0 0 2rem">'
             'Katalog envanterden okunur; sergiler ise envanterden <b>sorguyla</b> kurulur. '
             'Her sergi, koleksiyonun içinden geçen bir hikâye hattıdır — rasathaneler ve âlimleri, '
             'zamanın ölçümü, cerrahinin aletleri… Sergi tanımları hetega-kaynaklar deposunda tutulur; '
             'envanter zenginleştikçe sergiler kendiliğinden güncellenir.</p>'
             + kartlar + '</section>' + footer)
    d = os.path.join(HEDEF, 'sergiler')
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(sayfa)
    print('-> /sergiler/ dizini (%d sergi)' % len(sergiler))


def main():
    env = json.load(open(ENVF, encoding='utf-8'))
    head, header, footer = kabuk(HEDEF)
    uretilen = []
    for f in sorted(os.listdir(SERGI_DIR)):
        if f.endswith('.json'):
            uretilen.append(uret(f[:-5], env, head, header, footer))
    dizin(uretilen, head, header, footer)

    # sitemap
    sp = os.path.join(HEDEF, 'sitemap.xml')
    t = open(sp, encoding='utf-8').read()
    t = re.sub(r'<!-- SERGI-V1 -->.*?<!-- /SERGI-V1 -->', '', t, flags=re.S)
    bugun = datetime.date.today().isoformat()
    urls = ''.join('<url><loc>https://hetega.com/sergiler/%s/</loc><lastmod>%s</lastmod></url>'
                   % (s['slug'], bugun) for s in uretilen)
    urls += '<url><loc>https://hetega.com/sergiler/</loc><lastmod>%s</lastmod></url>' % bugun
    t = t.replace('</urlset>', '<!-- SERGI-V1 -->' + urls + '<!-- /SERGI-V1 --></urlset>')
    open(sp, 'w', encoding='utf-8').write(t)
    print('sitemap güncellendi (+%d URL)' % (len(uretilen) + 1))


if __name__ == '__main__':
    main()
