# -*- coding: utf-8 -*-
"""
HETEGA — Site Yapı Düzeltmeleri (tasarıma dokunmadan)

Tespit edilen kurgu sorunları ve çözümleri:
  1. Kök / "Yapım Aşamasında" placeholder'ı (noindex) — asıl içerik bir iç
     taslak sayfada (calisma-tam) duruyor ve marka linki oraya gidiyor.
     -> calisma-tam'ın GÜNCELLENMİŞ hali kök index.html olur (aynı tasarım),
        noindex kalkar, marka linki tüm sayfalarda "/" olur.
  2. Bayat sayaçlar: calisma-tam "483 eser, 11 koleksiyon"; koleksiyon
     landing'leri eski TAM kataloğu sayılarıyla duruyor (109/71/57...) ve
     kendi /tumu/ sayfalarıyla çelişiyor.
     -> tüm sayaçlar envanter + gerçek kart sayılarıyla senkronlanır.
  3. /#koleksiyonlar çapası hiçbir sayfada yok (nav linki ölü).
     -> kökteki koleksiyonlar bölümüne id="koleksiyonlar" eklenir.
  4. Antik Objeler koleksiyonu (146 nesne) kurguda hiç yok: ne kökte kartı
     ne landing sayfası.
     -> kök koleksiyon grid'ine kart + /koleksiyonlar/antik-objeler/ landing
        (mevcut landing şablonuyla) üretilir.

İdempotent değildir (tek seferlik yapı düzeltmesi); çalıştırma öncesi
working-tree temiz olmalıdır.
"""
import re, os, json, sys, html as H

HERE = os.path.dirname(os.path.abspath(__file__))
try:
    import yollar
    HEDEF = os.environ.get('HETEGA_WEBSITE', yollar.WEBSITE)
    ENVF = os.path.join(yollar.ENV, 'envanter.json')
except ImportError:
    HEDEF = os.environ.get('HETEGA_WEBSITE', '/home/user/hetega-website')
    ENVF = os.path.join(HERE, 'envanter.json')

env = json.load(open(ENVF, encoding='utf-8'))
N = env['nesneler']

def esc(s): return H.escape(str(s or ''), quote=True)

# ---------------------------------------------------------- güncel sayılar
toplam_urun = len([d for d in os.listdir(os.path.join(HEDEF, 'products'))
                   if d.startswith('k3-')])
tumu_say = {}
kdir = os.path.join(HEDEF, 'koleksiyonlar')
for k in os.listdir(kdir):
    p = os.path.join(kdir, k, 'tumu', 'index.html')
    if os.path.exists(p):
        tumu_say[k] = open(p, encoding='utf-8').read().count('<a href="/products/k3-')
koleksiyon_sayisi = len(tumu_say)
print('ürün sayfası: %d | koleksiyon (tumu olan): %d' % (toplam_urun, koleksiyon_sayisi))
print('tumu kart sayıları:', tumu_say)

# ---------------------------------------------------------- 1) kök index
ct = open(os.path.join(HEDEF, 'calisma-tam', 'index.html'), encoding='utf-8').read()
t = ct
# noindex kaldır
t = re.sub(r'<meta name="robots" content="noindex[^"]*">\s*', '', t)
# sayaçlar
t = t.replace('>483<', '>%d<' % toplam_urun)
t = re.sub(r'\b483\b(?=\s*(Enstrüman|enstrüman))', str(toplam_urun), t)
t = t.replace('483 eser, 11 koleksiyon.', '%d eser, %d koleksiyon.' % (toplam_urun, koleksiyon_sayisi))
t = re.sub(r'483(\s*)eser,(\s*)11(\s*)koleksiyon', '%d\\1eser,\\2%d\\3koleksiyon'
           % (toplam_urun, koleksiyon_sayisi), t)
# koleksiyon bölümüne çapa
i = t.find('Tüm Koleksiyonlar')
if i > 0:
    j = t.rfind('<section', 0, i)
    t = t[:j] + '<section id="koleksiyonlar"' + t[j + len('<section'):]
# koleksiyon kartlarındaki 'N eser' sayaçları (kart linkinden slug yakala)
SLUG_ESKI = {'astronomi': None, 'usturlaplar': None, 'cografya-ve-seyrusefer': None,
             'saatler': None, 'tesviye-ve-geometri': None, 'optik': None,
             'fizik-ve-teknik': None, 'askeri-teknoloji': None, 'kimya': None,
             'tip': None, 'mimari': None}
for slug in SLUG_ESKI:
    if slug not in tumu_say: continue
    # kartın 'N eser' satırı: href="/koleksiyonlar/<slug>/" öncesindeki en yakın
    for m in re.finditer(r'(<p[^>]*>)(\d+)(\s*eser</p>)', t):
        pass
# daha sağlam yol: her kart bloğunu h2 başlığından tanı
KART_BASLIK = {'astronomi': 'Astronomi', 'usturlaplar': 'Usturlaplar',
               'cografya-ve-seyrusefer': 'Coğrafya ve Seyrüsefer', 'saatler': 'Saatler',
               'tesviye-ve-geometri': 'Tesviye ve Geometri', 'optik': 'Optik',
               'fizik-ve-teknik': 'Fizik ve Teknik', 'askeri-teknoloji': 'Askeri Teknoloji',
               'kimya': 'Kimya', 'tip': 'Tıp', 'mimari': 'Mimari'}
for slug, ad in KART_BASLIK.items():
    if slug not in tumu_say: continue
    m = re.search(r'>%s</h2>\s*<p[^>]*>\d+ eser</p>' % re.escape(ad), t)
    if m:
        t = t[:m.start()] + m.group(0).replace(re.search(r'\d+ eser', m.group(0)).group(0),
                                               '%d eser' % tumu_say[slug]) + t[m.end():]
    else:
        print('  ! kart bulunamadı:', slug)
# Antik Objeler kartı (Mimari kartından sonra)
m = re.search(r'(<article[^>]*>(?:(?!</article>).)*?/koleksiyonlar/mimari/(?:(?!</article>).)*?</article>)', t, re.S)
if not m:
    # article değilse: Mimari bağlantısını içeren en yakın blok
    mi = t.find('/koleksiyonlar/mimari/')
    print('  mimari kartı article değil; ham konum:', mi)
antik_kart = None
if m:
    kart = m.group(1)
    antik_kart = (kart.replace('/koleksiyonlar/mimari/', '/koleksiyonlar/antik-objeler/')
                      .replace('>Mimari</h2>', '>Antik Objeler</h2>'))
    antik_kart = re.sub(r'\d+ eser', '%d eser' % tumu_say.get('antik-objeler', 0), antik_kart, count=1)
    antik_kart = re.sub(r'(<p style="font-size:\.9rem[^>]*>)[^<]*(</p>)',
                        r'\1Kitabın 13. bölümü: metal, cam, seramik, ahşap ve taş orijinal objeler ile Orientleştirici üslupta Avrupa cam ve seramikleri.\2',
                        antik_kart, count=1)
    antik_kart = re.sub(r'>[^<>]{0,60}(İncele|Keşfet|Gözat)[^<>]{0,10}<', '>Koleksiyonu Aç<', antik_kart)
    t = t[:m.end()] + antik_kart + t[m.end():]
    print('  + Antik Objeler kartı eklendi')
else:
    print('  ! Mimari kartı bulunamadı — Antik Objeler kartı eklenemedi')
open(os.path.join(HEDEF, 'index.html'), 'w', encoding='utf-8').write(t)
print('kök index.html yazıldı (%d KB)' % (len(t) // 1024))

# ---------------------------------------------------------- 2) marka linki
degisen = 0
for kok, dirs, files in os.walk(HEDEF):
    dirs[:] = [d for d in dirs if d != '.git']
    for f in files:
        if not f.endswith('.html'): continue
        p = os.path.join(kok, f)
        s = open(p, encoding='utf-8').read()
        s2 = s.replace('href="/calisma-tam/" class="brand"', 'href="/" class="brand"')
        if s2 != s:
            open(p, 'w', encoding='utf-8').write(s2)
            degisen += 1
print('marka linki düzeltilen dosya: %d' % degisen)

# ---------------------------------------------------------- 3) landing sayaçları
for slug, adet in tumu_say.items():
    lp = os.path.join(kdir, slug, 'index.html')
    if not os.path.exists(lp) or slug == 'antik-objeler':
        continue
    s = open(lp, encoding='utf-8').read()
    s0 = s
    s = re.sub(r'Tüm \d+ eseri incele', 'Tüm %d eseri incele' % adet, s)
    s = re.sub(r'(<div class="hero-note"><span>)\d+(</span>)', r'\g<1>%d\g<2>' % adet, s)
    if s != s0:
        open(lp, 'w', encoding='utf-8').write(s)
        print('  landing güncellendi: %-26s -> %d' % (slug, adet))

# ---------------------------------------------------------- 4) antik landing
tmpl = open(os.path.join(kdir, 'astronomi', 'index.html'), encoding='utf-8').read()
a = tmpl
a = a.replace('<title>Astronomi — HETEGA Koleksiyonu</title>',
              '<title>Antik Objeler — HETEGA Koleksiyonu</title>')
a = re.sub(r'(<meta property="og:title" content=")[^"]*(")', r'\1Antik Objeler — HETEGA Koleksiyonu\2', a)
a = a.replace('<span style="color:var(--ink)">Astronomi</span>',
              '<span style="color:var(--ink)">Antik Objeler</span>')
a = re.sub(r'(HETEGA · Koleksiyon</p>\s*<h1[^>]*>)Astronomi\.(</h1>)',
           r'\1Antik Objeler.\2', a)
# açıklama
esk_ac = re.search(r'(<p[^>]*>)Rasathaneler, gözlem aletleri[^<]*(</p>)', a)
YENI_AC = ('Orijinal nesneler: kitabın 13. bölümü (Cilt V) — metal, cam, seramik, '
           'ahşap ve taş objeler; teraziler, havanlar, mühürler, vazolar ve '
           'Orientleştirici üslupta Avrupa cam ve seramikleri. Enstitü modeli '
           'değil, çoğu bizzat tarihî eserdir.')
if esk_ac:
    a = a[:esk_ac.start(1)] + esk_ac.group(1) + YENI_AC + esk_ac.group(2) + a[esk_ac.end():]
else:
    a = re.sub(r'(</h1>\s*<p[^>]*>)[^<]*(</p>)', r'\1' + YENI_AC + r'\2', a, count=1)
a = re.sub(r'Tüm \d+ eseri incele', 'Tüm %d eseri incele' % tumu_say.get('antik-objeler', 0), a)
a = re.sub(r'(<div class="hero-note"><span>)\d+(</span>)',
           r'\g<1>%d\g<2>' % tumu_say.get('antik-objeler', 0), a)
a = a.replace('/koleksiyonlar/astronomi/tumu/', '/koleksiyonlar/antik-objeler/tumu/')
# öne çıkanlar: antik koleksiyonundan görselli 4 nesne
antikler = [o for o in N if o['koleksiyon'] == 'Antik Objeler' and o.get('gorseller')
            and o['yayin'].get('url') and o['yayin']['durum'] == 'yayında']
tercih = ['J238', 'J355', 'J357-1', 'J233', 'J224', 'J347']
sec = []
for tid in tercih:
    for o in antikler:
        if o['id'] == tid and o not in sec: sec.append(o)
for o in antikler:
    if len(sec) >= 4: break
    if o not in sec: sec.append(o)
sec = sec[:4]
KART = ('<a href="{url}" style="display:flex;flex-direction:column;color:inherit;text-decoration:none;'
        'background:radial-gradient(ellipse at 50% 30%, var(--card-bg) 0%, var(--card-bg) 55%, rgba(0,0,0,.1) 100%);'
        'border-radius:2px;box-shadow:0 18px 40px -14px rgba(0,0,0,.4), 0 4px 10px rgba(0,0,0,.15);overflow:hidden">'
        '<div style="aspect-ratio:1/1;display:flex;align-items:center;justify-content:center;overflow:hidden">'
        '<img src="{img}" alt="{baslik}" loading="lazy" style="width:100%;height:100%;object-fit:contain;padding:1.25rem"/></div>'
        '<div style="padding:1.25rem 1.25rem 1.5rem;flex:1;display:flex;flex-direction:column;justify-content:flex-end">'
        '<h3 style="font-family:var(--font-display), Georgia, serif;font-weight:400;font-size:.85rem;line-height:1.3;'
        'margin:0 0 .6rem;color:var(--ink);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">{baslik}</h3>'
        '<p style="font-size:.8rem;color:var(--muted-text);line-height:1.4;margin:0">{no}</p></div></a>')
kartlar = ''.join(KART.format(url=o['yayin']['url'], img=o['gorseller'][0]['url'],
                              baslik=esc(o['baslik']), no=esc(o['envanter_gosterim'])) for o in sec)
m = re.search(r'(<section style="padding:0 4\.5vw 5rem;display:grid;[^>]*>)(.*?)(</section>)', a, re.S)
if m:
    a = a[:m.start(2)] + kartlar + a[m.end(2):]
adir = os.path.join(kdir, 'antik-objeler')
os.makedirs(adir, exist_ok=True)
open(os.path.join(adir, 'index.html'), 'w', encoding='utf-8').write(a)
print('antik-objeler landing yazıldı (öne çıkanlar: %s)' % [o['id'] for o in sec])

print('\nBİTTİ — link kontrolü ayrıca çalıştırılmalı.')
