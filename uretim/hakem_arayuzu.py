# -*- coding: utf-8 -*-
"""
HETEGA — Hakemleme Arayüzü Üreteci

envanter.json + book_blocks.json'dan, insan kararı bekleyen kayıtlar için
tek dosyalık (self-contained) bir iç çalışma sayfası üretir:

  G1  eksik_baslik_bekliyor  (153)  -> başlık yaz / nesne değil / atla
  G2  yayında_numarasız      (40)   -> numara ata (çoklu) / kapsam dışı / numarasız kalsın
  G3  yayında_doğrulanmadı   (33)   -> müzede var / numarayı düzelt / mükerrer / kaldır

Kararlar tarayıcıda localStorage'da tutulur, `hakem-kararlari-*.json` olarak
dışa aktarılır; uretim/hakem_uygula.py bu dosyayı envanter.json'a işler.

Çıktı: <HETEGA_WEBSITE>/calisma/hakemleme/index.html
"""
import re, os, json, sys, collections, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
try:
    import yollar
    ENVF = os.path.join(yollar.ENV, 'envanter.json')
    ARAF = os.path.join(yollar.ARA, 'book_blocks.json')
    HEDEF = os.environ.get('HETEGA_WEBSITE', yollar.WEBSITE)
except ImportError:
    ENVF = os.path.join(HERE, 'envanter.json')
    ARAF = os.path.join(HERE, 'book_blocks.json')
    HEDEF = os.environ.get('HETEGA_WEBSITE', '/home/user/hetega-website')

VOLN = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5}

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

# ------------------------------------------------------------------ veri
env = json.load(open(ENVF, encoding='utf-8'))
N = env['nesneler']
blocks = {}
for b in json.load(open(ARAF, encoding='utf-8')):
    for n in b['envanter_nolar']:
        blocks.setdefault(n, b)

G1 = [o for o in N if o['yayin']['durum'] == 'eksik_baslik_bekliyor']
G2 = [o for o in N if o['yayin']['durum'] == 'yayında_numarasız']
G3 = [o for o in N if o['yayin']['durum'] == 'yayında_doğrulanmadı']

# kitabın sitede bağlı olmayan kayıtları (G2 adayları için)
kitap_bosta = [o for o in N if o.get('kitap') and not o['dogrulama']['sitede']]

def baglam_kisalt(bl, n=14):
    bl = [re.sub(r'\s+', ' ', x).strip() for x in (bl or []) if x.strip()]
    return bl[-n:]

g1_data = []
for o in sorted(G1, key=lambda x: (VOLN.get((x.get('kitap') or {}).get('cilt', ''), 9),
                                   (x.get('kitap') or {}).get('sayfa') or 0, x['id'])):
    b = blocks.get(o['id'], {})
    kardes = []
    if o.get('set'):
        for uid in o['set'].get('uyeler', []):
            x = next((z for z in N if z['id'] == uid), None)
            if x and x['id'] != o['id'] and x.get('baslik'):
                kardes.append('%s: %s' % (x['envanter_gosterim'], x['baslik'][:60]))
    g1_data.append({
        'id': o['id'], 'no': o['envanter_gosterim'],
        'baslik_mevcut': o.get('baslik', ''), 'kalite': o.get('baslik_kalite', ''),
        'cilt': o['hiyerarsi'].get('cilt', ''), 'sayfa': (o.get('kitap') or {}).get('sayfa'),
        'hiyerarsi': ' > '.join(x for x in [o['hiyerarsi'].get('bolum'),
                       o['hiyerarsi'].get('alt_bolum'), o['hiyerarsi'].get('alt_baslik')] if x),
        'ust_baslik': (o.get('kitap') or {}).get('ust_baslik', ''),
        'model': (o.get('kitap') or {}).get('model_metni', ''),
        'malzeme': o['teknik'].get('malzeme', []), 'boyutlar': o['teknik'].get('boyutlar', []),
        'set': (o['set'] or {}).get('ham', ''), 'set_uye': (o['set'] or {}).get('uye_sayisi', 0),
        'kardes': kardes[:6],
        'baglam': baglam_kisalt(b.get('baglam')),
        'ham_envanter': (o.get('kitap') or {}).get('ham_envanter', ''),
        'onek_cikarim': (o.get('kitap') or {}).get('onek_cikarim', False),
    })

g2_data = []
for o in sorted(G2, key=lambda x: x['baslik']):
    vol, pages = parse_kaynak(o.get('kitap_kaynak_site', ''))
    adaylar = []
    if vol and pages:
        p0, p1 = min(pages) - 1, max(pages) + 1
        for k in kitap_bosta:
            kk = k.get('kitap') or {}
            if kk.get('cilt') == vol and kk.get('sayfa') and p0 <= kk['sayfa'] <= p1:
                bb = blocks.get(k['id'], {})
                adaylar.append({'id': k['id'], 'no': k['envanter_gosterim'],
                                'baslik': k.get('baslik') or '(kitapta başlığı okunamadı)',
                                'sayfa': kk.get('sayfa'),
                                'durum': k['yayin']['durum'],
                                'baglam': baglam_kisalt(bb.get('baglam'), 8)})
    g2_data.append({
        'id': o['id'], 'baslik': o['baslik'], 'url': o['yayin'].get('url', ''),
        'kategori': (o.get('site_kategori') or {}).get('kategori', o.get('koleksiyon', '')),
        'islev': o.get('islev', ''), 'ozellikler': o.get('ozellikler', '')[:220],
        'kaynak': o.get('kitap_kaynak_site', ''), 'gorsel': (o.get('gorseller') or [{}])[0].get('url', ''),
        'adaylar': adaylar[:8],
    })

g3_data = []
for o in sorted(G3, key=lambda x: x['id']):
    vol, pages = parse_kaynak(o.get('kitap_kaynak_site', ''))
    ayni_sayfa = []
    if vol and pages:
        for k in N:
            kk = k.get('kitap') or {}
            if k['id'] != o['id'] and kk.get('cilt') == vol and kk.get('sayfa') in pages:
                ayni_sayfa.append('%s — %s' % (k['envanter_gosterim'], (k.get('baslik') or '?')[:44]))
    g3_data.append({
        'id': o['id'], 'no': o['envanter_gosterim'], 'baslik': o['baslik'],
        'url': o['yayin'].get('url', ''), 'kaynak': o.get('kitap_kaynak_site', ''),
        'kategori': o.get('koleksiyon', ''),
        'gorsel': (o.get('gorseller') or [{}])[0].get('url', ''),
        'notlar': [x for x in o['dogrulama'].get('notlar', []) if not x.startswith('İNSAN')][:2],
        'ayni_sayfa': ayni_sayfa[:8],
    })

DATA = {'uretim_tarihi': datetime.date.today().isoformat(),
        'g1': g1_data, 'g2': g2_data, 'g3': g3_data,
        'sayilar': {'g1': len(g1_data), 'g2': len(g2_data), 'g3': len(g3_data)}}

print('G1=%d G2=%d G3=%d  (veri ~%d KB)' % (len(g1_data), len(g2_data), len(g3_data),
                                            len(json.dumps(DATA, ensure_ascii=False)) // 1024))

# ------------------------------------------------------------------ HTML
TEMPLATE = r'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Hakemleme — HETEGA Envanter Çalışması</title>
<style>
:root{--ink:#3c4654;--paper:#fdfcf9;--line:#e2e2e2;--brass:#b6874f;--brass-deep:#8a6238;
--muted:#6b7280;--green:#3f7d4f;--red:#a5483f;--blue:#123c5a;--card:#fff;--amber:#c08a2e}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Inter",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-size:14px;line-height:1.55}
.topbar{position:sticky;top:0;z-index:50;background:var(--blue);color:#f3ede1;padding:.6rem 1.2rem;display:flex;flex-wrap:wrap;gap:.7rem;align-items:center;box-shadow:0 2px 10px rgba(0,0,0,.25)}
.topbar h1{font-size:.95rem;margin:0;font-weight:700;letter-spacing:.02em}
.topbar .sub{font-size:.7rem;opacity:.75;margin-left:.2rem}
.tabs{display:flex;gap:.4rem;flex-wrap:wrap}
.tab{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.22);color:#f3ede1;padding:.42rem .85rem;border-radius:999px;cursor:pointer;font-size:.76rem;font-weight:600}
.tab.active{background:var(--brass);border-color:var(--brass);color:#fff}
.tab .cnt{opacity:.8;font-weight:400}
.spacer{flex:1}
.btn{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.3);color:#f3ede1;padding:.42rem .8rem;border-radius:8px;cursor:pointer;font-size:.74rem;font-weight:600}
.btn:hover{background:rgba(255,255,255,.2)}
.btn.gold{background:var(--brass);border-color:var(--brass);color:#fff}
.progress{font-size:.74rem;background:rgba(0,0,0,.25);padding:.35rem .7rem;border-radius:999px}
.progress b{color:#9fd6a8}
.filterbar{display:flex;gap:.6rem;align-items:center;padding:.7rem 1.2rem;background:#fff;border-bottom:1px solid var(--line);flex-wrap:wrap;position:sticky;top:52px;z-index:40}
.filterbar input[type=search]{padding:.45rem .8rem;border:1px solid var(--line);border-radius:999px;font-size:.8rem;min-width:220px;background:var(--paper)}
.chip{border:1px solid var(--line);background:var(--paper);padding:.35rem .75rem;border-radius:999px;cursor:pointer;font-size:.73rem;font-weight:600;color:var(--muted)}
.chip.active{border-color:var(--brass);color:var(--brass-deep);background:#f7efdf}
main{padding:1.2rem;max-width:1280px;margin:0 auto;display:flex;flex-direction:column;gap:1rem}
.card{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--line);border-radius:10px;overflow:hidden}
.card.decided{border-left-color:var(--green)}
.card.skipped{border-left-color:var(--amber)}
.card-head{display:flex;gap:.8rem;align-items:baseline;padding:.85rem 1.1rem .35rem;flex-wrap:wrap}
.card-head .no{font-family:ui-monospace,Menlo,Consolas,monospace;font-weight:700;color:var(--brass-deep);font-size:.95rem}
.card-head h2{font-size:1.02rem;margin:0;font-weight:700}
.card-head .meta{font-size:.72rem;color:var(--muted)}
.badge{font-size:.64rem;font-weight:700;padding:.18rem .55rem;border-radius:999px;letter-spacing:.03em;text-transform:uppercase}
.badge.kitap{background:#eef3f8;color:#31597a}.badge.site{background:#f4ecdd;color:#8a6238}
.badge.set{background:#f0e9f6;color:#6d4a86}.badge.warn{background:#f9e9e7;color:#a5483f}
.badge.ok{background:#e7f2e9;color:#3f7d4f}
.grid{display:grid;grid-template-columns:1.15fr .85fr;gap:0}
@media(max-width:900px){.grid{grid-template-columns:1fr}}
.pane{padding:.7rem 1.1rem 1rem}
.pane.left{border-right:1px solid var(--line)}
@media(max-width:900px){.pane.left{border-right:none;border-bottom:1px solid var(--line)}}
.pane h3{font-size:.68rem;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);margin:.7rem 0 .35rem;font-weight:700}
.ctx{background:#faf7f0;border:1px solid #ece5d5;border-radius:8px;padding:.6rem .8rem;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.73rem;line-height:1.65;max-height:230px;overflow:auto;white-space:pre-wrap;color:#5a5346}
.ctx .inv{background:#f3e2c2;color:#7a5a17;font-weight:700;border-radius:3px;padding:0 3px}
.hiy{font-size:.78rem;color:#31597a;background:#eef3f8;border-radius:6px;padding:.3rem .6rem;display:inline-block;margin-bottom:.4rem}
.kv{font-size:.8rem;margin:.15rem 0}
.kv b{color:var(--muted);font-weight:600;font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;display:inline-block;min-width:86px}
.deco{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:.3rem}
.thumb{width:110px;height:110px;object-fit:contain;background:#ececec;border-radius:8px;border:1px solid var(--line);padding:6px}
.aday{border:1px solid var(--line);border-radius:8px;padding:.5rem .7rem;margin:.35rem 0;background:#fcfbf7;cursor:pointer;display:block;width:100%;text-align:left;font-size:.78rem}
.aday:hover{border-color:var(--brass)}
.aday.sel{border-color:var(--brass);background:#f7efdf;box-shadow:0 0 0 1px var(--brass)}
.aday .no{font-family:ui-monospace,monospace;font-weight:700;color:var(--brass-deep)}
.aday .sayfa{color:var(--muted);font-size:.7rem}
.aday details{margin-top:.3rem}
.aday summary{font-size:.7rem;color:var(--muted);cursor:pointer}
.aday .mini{font-family:ui-monospace,monospace;font-size:.68rem;color:#5a5346;white-space:pre-wrap;margin-top:.3rem}
.deci{background:#fbfaf6;border-radius:8px;border:1px solid var(--line);padding:.7rem .8rem}
.deci h3{margin-top:0}
label.opt{display:flex;gap:.5rem;align-items:flex-start;padding:.34rem .3rem;border-radius:6px;cursor:pointer;font-size:.82rem}
label.opt:hover{background:#f2eee2}
label.opt input{margin-top:.22rem}
.opt .desc{font-size:.7rem;color:var(--muted);display:block}
.fields{margin:.5rem 0 0 .2rem;display:none;gap:.45rem;flex-direction:column}
.fields.show{display:flex}
.fields input[type=text],.fields textarea,.fields select{width:100%;padding:.5rem .65rem;border:1px solid var(--line);border-radius:7px;font-size:.82rem;font-family:inherit;background:#fff}
.fields textarea{min-height:64px;resize:vertical}
.fields .hint{font-size:.68rem;color:var(--muted)}
.rowbtns{display:flex;gap:.5rem;margin-top:.6rem;flex-wrap:wrap}
.save{background:var(--green);border:none;color:#fff;padding:.5rem 1.1rem;border-radius:8px;cursor:pointer;font-size:.8rem;font-weight:700}
.save:hover{filter:brightness(1.08)}
.clear{background:#fff;border:1px solid var(--line);color:var(--muted);padding:.5rem .9rem;border-radius:8px;cursor:pointer;font-size:.78rem}
.decided-note{display:none;margin-top:.55rem;font-size:.76rem;background:#e7f2e9;border:1px solid #c9e2ce;color:#2f5e3b;border-radius:7px;padding:.45rem .7rem}
.card.decided .decided-note{display:block}
.empty{padding:3rem 1rem;text-align:center;color:var(--muted)}
.empty .big{font-size:2.2rem}
footer{padding:1.6rem 1.2rem 3rem;text-align:center;color:var(--muted);font-size:.72rem}
a{color:var(--brass-deep)}
</style>
</head>
<body>
<div class="topbar">
  <h1>⚖ HETEGA · Envanter Hakemleme <span class="sub">iç çalışma — __TARIH__</span></h1>
  <div class="tabs">
    <button class="tab active" data-g="g1">1 · Başlık bekleyen <span class="cnt" id="cnt-g1"></span></button>
    <button class="tab" data-g="g2">2 · Numarasız sayfalar <span class="cnt" id="cnt-g2"></span></button>
    <button class="tab" data-g="g3">3 · Kitapta doğrulanamayan <span class="cnt" id="cnt-g3"></span></button>
  </div>
  <div class="spacer"></div>
  <span class="progress" id="prog"></span>
  <button class="btn gold" id="btn-export">⬇ Kararları indir (JSON)</button>
  <button class="btn" id="btn-import">⬆ Yükle</button>
  <input type="file" id="file-import" accept=".json" style="display:none">
  <button class="btn" id="btn-clear" title="Bu sekmedeki tüm kararları siler">✕ Temizle</button>
</div>
<div class="filterbar">
  <span class="chip active" data-f="hepsi">Hepsi</span>
  <span class="chip" data-f="bekleyen">Karar bekleyen</span>
  <span class="chip" data-f="verilen">Karar verilen</span>
  <span class="chip" data-f="atlanan">Atlanan</span>
  <input type="search" id="q" placeholder="Ara: başlık, numara, bölüm…">
</div>
<main id="list"></main>
<footer>Bu sayfa hetega-kaynaklar/envanter verisinden üretildi · kararlar yalnızca bu tarayıcıda saklanır,
bitirince <b>Kararları indir</b> ile JSON'u depoya geri iletin (uretim/hakem_uygula.py işler).</footer>

<script>
const DATA = __DATA__;
const LS = 'hetega-hakem-v1';
let decisions = {};
try { decisions = JSON.parse(localStorage.getItem(LS) || '{}'); } catch(e) { decisions = {}; }
let curG = 'g1', curF = 'hepsi', curQ = '';

const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c =>
  ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dkey = (g, id) => g + ':' + id;
function saveLS(){ localStorage.setItem(LS, JSON.stringify(decisions)); }

/* ---------- kayıt şablonları ---------- */
function ctxHtml(b){
  let t = esc(b || '');
  t = t.replace(/\(Envanter[^)]*\)/g, m => '<span class="inv">' + m + '</span>');
  t = t.replace(/Envanter N[o0]\s*:?\s*[A-Za-z0-9 .,;-]+/g, m => '<span class="inv">' + m + '</span>');
  return t;
}

function g1Card(r){
  const k = dkey('g1', r.id), d = decisions[k] || {};
  const setInfo = r.set ? `<span class="badge set">set: ${esc(r.set)} (${r.set_uye} üye)</span>` : '';
  const cik = r.onek_cikarim ? `<span class="badge warn">önek OCR'dan tamamlandı</span>` : '';
  const kardes = (r.kardes && r.kardes.length) ?
    `<h3>Aynı setten kardeş kayıtlar (başlığı bilinen)</h3><div class="kv">${r.kardes.map(x=>'• '+esc(x)).join('<br>')}</div>` : '';
  return `<div class="card ${d.karar ? (d.karar==='atla'?'skipped':'decided') : ''}" data-g="g1" data-id="${esc(r.id)}">
  <div class="card-head"><span class="no">${esc(r.no)}</span><h2>${esc(r.baslik_mevcut || '(başlık yok)')}</h2>
    <span class="badge kitap">kitap kaydı</span>${setInfo}${cik}
    <span class="meta">${esc(r.cilt)}${r.sayfa ? ' · s.' + r.sayfa : ''} · ${esc(r.hiyerarsi)}</span></div>
  <div class="grid">
    <div class="pane left">
      ${r.ust_baslik ? `<div class="hiy">kitap üst başlığı: ${esc(r.ust_baslik)}</div>` : ''}
      ${r.model ? `<h3>Model / teknik metni</h3><div class="kv">${esc(r.model)}</div>` : ''}
      ${(r.malzeme.length||r.boyutlar.length) ? `<h3>Malzeme · ölçü</h3><div class="kv">${esc(r.malzeme.join(', '))}${r.boyutlar.length?' · '+esc(r.boyutlar.join('; ')):''}</div>`:''}
      ${kardes}
      <h3>Kitap bağlamı (OCR — envanter no vurgulu)</h3>
      <div class="ctx">${ctxHtml((r.baglam||[]).join('\n'))}</div>
      ${r.ham_envanter ? `<h3>Kitapta yazıldığı gibi</h3><div class="kv">“${esc(r.ham_envanter)}”</div>`:''}
    </div>
    <div class="pane">
      <div class="deci">
        <h3>Karar</h3>
        <label class="opt"><input type="radio" name="k_${esc(r.id)}" value="baslik" ${d.karar==='baslik'?'checked':''}>
          <span>Bu bir müze nesnesi — <b>başlığını yaz</b><span class="desc">kitap bağlamından okuyabildiğin ad</span></span></label>
        <div class="fields ${d.karar==='baslik'?'show':''}" data-for="baslik">
          <input type="text" placeholder="Başlık (ör. Katarakt İğnesi)" data-f="baslik" value="${esc(d.baslik||'')}">
          <input type="text" placeholder="İşlevi (opsiyonel)" data-f="islev" value="${esc(d.islev||'')}">
        </div>
        <label class="opt"><input type="radio" name="k_${esc(r.id)}" value="nesne_degil" ${d.karar==='nesne_degil'?'checked':''}>
          <span><b>Nesne değil</b> — katalog kapsamı dışına al<span class="desc">alet parçası, bölüm başlığı, çizim/kavram, mineral örneği açıklaması…</span></span></label>
        <div class="fields ${d.karar==='nesne_degil'?'show':''}" data-for="nesne_degil">
          <select data-f="kayit_tipi">
            <option value="">— tip seç —</option>
            ${[['parca','Parça (bir aletin bölümü — ör. usturlap ana kısmı)'],
               ['bolum','Bölüm / konu başlığı'],
               ['kavram','Kavram, tarif veya çizim'],
               ['cizim','Yazma çizimi / levha (ayrı nesne yok)'],
               ['grup','Grup / toplu kayıt (tek künyede eriyor)'],
               ['diger','Diğer (nota yaz)']].map(o=>`<option value="${o[0]}" ${d.kayit_tipi===o[0]?'selected':''}>${esc(o[1])}</option>`).join('')}
          </select>
        </div>
        <label class="opt"><input type="radio" name="k_${esc(r.id)}" value="mukerrer" ${d.karar==='mukerrer'?'checked':''}>
          <span><b>Mükerrer</b> — sitede zaten var<span class="desc">hangi envanter no / URL olduğunu nota yaz</span></span></label>
        <div class="fields ${d.karar==='mukerrer'?'show':''}" data-for="mukerrer">
          <input type="text" placeholder="Mükerrer olduğu kayıt (ör. A 4.16 veya /products/k3-10-…)" data-f="hedef" value="${esc(d.hedef||'')}">
        </div>
        <label class="opt"><input type="radio" name="k_${esc(r.id)}" value="atla" ${d.karar==='atla'?'checked':''}>
          <span>Şimdilik <b>atla</b></span></label>
        <div class="fields" data-for="hep">
          <input type="text" placeholder="Not (opsiyonel)" data-f="not" value="${esc(d.not||'')}">
        </div>
        <div class="rowbtns"><button class="save">Kaydet</button><button class="clear">Kararı sil</button></div>
        <div class="decided-note"></div>
      </div>
    </div>
  </div></div>`;
}

function g2Card(r){
  const k = dkey('g2', r.id), d = decisions[k] || {};
  const sec = new Set((d.no || []).map(x => x));
  const adaylar = (r.adaylar||[]).map(a => `<button type="button" class="aday ${sec.has(a.id)?'sel':''}" data-aday="${esc(a.id)}">
      <span class="no">${esc(a.no)}</span> — ${esc(a.baslik)} <span class="sayfa">· s.${a.sayfa} · ${esc(a.durum)}</span>
      <details><summary>kitap bağlamı</summary><div class="mini">${ctxHtml((a.baglam||[]).join('\n'))}</div></details>
    </button>`).join('');
  return `<div class="card ${d.karar ? (d.karar==='atla'?'skipped':'decided') : ''}" data-g="g2" data-id="${esc(r.id)}">
  <div class="card-head"><span class="badge site">site sayfası</span><h2>${esc(r.baslik)}</h2>
    <span class="meta">${esc(r.kategori)} · kaynak: ${esc(r.kaynak)} · <a href="${esc(r.url)}" target="_blank">sayfayı aç ↗</a></span></div>
  <div class="grid">
    <div class="pane left">
      ${r.gorsel ? `<div class="deco"><img class="thumb" src="${esc(r.gorsel)}" alt=""></div>` : ''}
      ${r.islev ? `<h3>İşlevi</h3><div class="kv">${esc(r.islev)}</div>` : ''}
      ${r.ozellikler ? `<h3>Özellikler</h3><div class="kv">${esc(r.ozellikler)}</div>` : ''}
      <h3>Aynı sayfadaki kitlenmemiş kitap kayıtları (aday numaralar)</h3>
      ${adaylar || '<div class="kv" style="color:var(--muted)">Bu sayfada aday kitap kaydı bulunamadı.</div>'}
      <p class="hint" style="font-size:.7rem;color:var(--muted)">Birden fazla seçebilirsin (ör. “iki model” sayfaları).</p>
    </div>
    <div class="pane">
      <div class="deci">
        <h3>Karar</h3>
        <label class="opt"><input type="radio" name="k2_${esc(r.id)}" value="numara_ata" ${d.karar==='numara_ata'?'checked':''}>
          <span>Yukarıdan <b>numara(lar) ata</b><span class="desc">sayfa bu envanter numaralarına bağlansın</span></span></label>
        <div class="fields ${d.karar==='numara_ata'?'show':''}" data-for="numara_ata">
          <input type="text" placeholder="veya elle numara yaz (ör. C 1.12; virgülle ayır)" data-f="no_elle" value="${esc((d.no_elle||''))}">
        </div>
        <label class="opt"><input type="radio" name="k2_${esc(r.id)}" value="nesne_degil" ${d.karar==='nesne_degil'?'checked':''}>
          <span><b>Nesne değil</b> — sayfa kapsam dışı<span class="desc">parça/bölüm/kavram anlatan sayfa</span></span></label>
        <div class="fields ${d.karar==='nesne_degil'?'show':''}" data-for="nesne_degil">
          <select data-f="kayit_tipi">
            <option value="">— tip seç —</option>
            ${[['parca','Parça'],['bolum','Bölüm / konu başlığı'],['kavram','Kavram / çizim'],['grup','Grup kaydı'],['diger','Diğer']].map(o=>`<option value="${o[0]}" ${d.kayit_tipi===o[0]?'selected':''}>${esc(o[1])}</option>`).join('')}
          </select>
        </div>
        <label class="opt"><input type="radio" name="k2_${esc(r.id)}" value="numarasiz_kalsin" ${d.karar==='numarasiz_kalsin'?'checked':''}>
          <span>Numarasız <b>yayında kalsın</b><span class="desc">müzede karşılığı belirsiz ama içerik doğru</span></span></label>
        <label class="opt"><input type="radio" name="k2_${esc(r.id)}" value="atla" ${d.karar==='atla'?'checked':''}>
          <span>Şimdilik <b>atla</b></span></label>
        <div class="fields" data-for="hep">
          <input type="text" placeholder="Not (opsiyonel)" data-f="not" value="${esc(d.not||'')}">
        </div>
        <div class="rowbtns"><button class="save">Kaydet</button><button class="clear">Kararı sil</button></div>
        <div class="decided-note"></div>
      </div>
    </div>
  </div></div>`;
}

function g3Card(r){
  const k = dkey('g3', r.id), d = decisions[k] || {};
  return `<div class="card ${d.karar ? (d.karar==='atla'?'skipped':'decided') : ''}" data-g="g3" data-id="${esc(r.id)}">
  <div class="card-head"><span class="no">${esc(r.no)}</span><h2>${esc(r.baslik)}</h2>
    <span class="badge warn">kitapta doğrulanamadı</span>
    <span class="meta">${esc(r.kategori)} · site kaynağı: ${esc(r.kaynak)} · <a href="${esc(r.url)}" target="_blank">sayfa ↗</a></span></div>
  <div class="grid">
    <div class="pane left">
      <div class="deco">${r.gorsel ? `<img class="thumb" src="${esc(r.gorsel)}" alt="">` : ''}</div>
      ${r.notlar.length ? `<h3>Neden işaretli</h3><div class="kv">${r.notlar.map(esc).join('<br>')}</div>` : ''}
      <h3>Kitapta aynı sayfada geçen numaralar</h3>
      <div class="kv">${r.ayni_sayfa.length ? r.ayni_sayfa.map(esc).join('<br>') : '— bu sayfada kitapta hiç envanter no geçmiyor —'}</div>
    </div>
    <div class="pane">
      <div class="deci">
        <h3>Karar</h3>
        <label class="opt"><input type="radio" name="k3_${esc(r.id)}" value="muzede_var" ${d.karar==='muzede_var'?'checked':''}>
          <span><b>Müzede var, kitapta yok</b> — bayrakla yayında kalsın</span></label>
        <label class="opt"><input type="radio" name="k3_${esc(r.id)}" value="numara_duzelt" ${d.karar==='numara_duzelt'?'checked':''}>
          <span>Numara <b>hatalı — doğrusu:</b></span></label>
        <div class="fields ${d.karar==='numara_duzelt'?'show':''}" data-for="numara_duzelt">
          <input type="text" placeholder="Doğru envanter no (ör. A 1.03)" data-f="yeni_no" value="${esc(d.yeni_no||'')}">
        </div>
        <label class="opt"><input type="radio" name="k3_${esc(r.id)}" value="mukerrer" ${d.karar==='mukerrer'?'checked':''}>
          <span><b>Mükerrer</b> — başka bir kaydın kopyası</span></label>
        <div class="fields ${d.karar==='mukerrer'?'show':''}" data-for="mukerrer">
          <input type="text" placeholder="Hedef kayıt (no veya URL)" data-f="hedef" value="${esc(d.hedef||'')}">
        </div>
        <label class="opt"><input type="radio" name="k3_${esc(r.id)}" value="kaldir" ${d.karar==='kaldir'?'checked':''}>
          <span><b>Yayından kaldır</b><span class="desc">uydurma/hatalı kayıt</span></span></label>
        <label class="opt"><input type="radio" name="k3_${esc(r.id)}" value="atla" ${d.karar==='atla'?'checked':''}>
          <span>Şimdilik <b>atla</b></span></label>
        <div class="fields" data-for="hep">
          <input type="text" placeholder="Not (opsiyonel)" data-f="not" value="${esc(d.not||'')}">
        </div>
        <div class="rowbtns"><button class="save">Kaydet</button><button class="clear">Kararı sil</button></div>
        <div class="decided-note"></div>
      </div>
    </div>
  </div></div>`;
}

/* ---------- render ---------- */
const CARDS = {g1: g1Card, g2: g2Card, g3: g3Card};
function render(){
  const list = document.getElementById('list');
  const rows = DATA[curG] || [];
  let html = '';
  let shown = 0;
  for(const r of rows){
    const k = dkey(curG, r.id), d = decisions[k];
    if(curF==='bekleyen' && d && d.karar) continue;
    if(curF==='verilen' && !(d && d.karar && d.karar!=='atla')) continue;
    if(curF==='atlanan' && !(d && d.karar==='atla')) continue;
    if(curQ){
      const blob = JSON.stringify(r).toLocaleLowerCase('tr');
      if(!blob.includes(curQ)) continue;
    }
    html += CARDS[curG](r); shown++;
  }
  list.innerHTML = html || `<div class="empty"><div class="big">🏺</div>Bu filtrede kayıt yok.</div>`;
  updateDecidedNotes();
  updateProgress();
}
function updateProgress(){
  for(const g of ['g1','g2','g3']){
    const tot = DATA[g].length;
    const dec = DATA[g].filter(r => { const d = decisions[dkey(g,r.id)]; return d && d.karar && d.karar!=='atla'; }).length;
    document.getElementById('cnt-'+g).textContent = `(${dec}/${tot})`;
  }
  const tot = DATA.g1.length + DATA.g2.length + DATA.g3.length;
  let dec = 0;
  for(const g of ['g1','g2','g3']) dec += DATA[g].filter(r => { const d = decisions[dkey(g,r.id)]; return d && d.karar; }).length;
  document.getElementById('prog').innerHTML = `toplam karar: <b>${dec}</b>/${tot}`;
}
function updateDecidedNotes(){
  document.querySelectorAll('#list .card').forEach(c => {
    const g = c.dataset.g, id = c.dataset.id, d = decisions[dkey(g,id)];
    c.classList.toggle('decided', !!(d && d.karar && d.karar!=='atla'));
    c.classList.toggle('skipped', !!(d && d.karar==='atla'));
    const n = c.querySelector('.decided-note');
    if(n && d && d.karar) n.textContent = 'Karar: ' + d.karar + (d.baslik ? ' — “'+d.baslik+'”' : '') + (d.no && d.no.length ? ' — no: '+d.no.join(', ') : '') + (d.kayit_tipi ? ' — tip: '+d.kayit_tipi : '') + (d.not ? ' — not: '+d.not : '');
  });
}

/* ---------- olaylar ---------- */
document.querySelectorAll('.tab').forEach(t => t.addEventListener('click', () => {
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  t.classList.add('active'); curG = t.dataset.g; render();
}));
document.querySelectorAll('.filterbar .chip').forEach(c => c.addEventListener('click', () => {
  document.querySelectorAll('.filterbar .chip').forEach(x=>x.classList.remove('active'));
  c.classList.add('active'); curF = c.dataset.f; render();
}));
document.getElementById('q').addEventListener('input', e => {
  curQ = e.target.value.toLocaleLowerCase('tr').trim(); render();
});

document.getElementById('list').addEventListener('click', e => {
  const card = e.target.closest('.card'); if(!card) return;
  const g = card.dataset.g, id = card.dataset.id, k = dkey(g,id);

  // aday seçimi (g2 çoklu)
  const aday = e.target.closest('.aday');
  if(aday){
    const aid = aday.dataset.aday;
    const d = decisions[k] || {};
    d.no = d.no || [];
    const i = d.no.indexOf(aid);
    if(i>=0) d.no.splice(i,1); else d.no.push(aid);
    decisions[k] = d;
    aday.classList.toggle('sel');
    // numara_ata otomatik seç
    const rad = card.querySelector('input[value="numara_ata"]');
    if(rad && d.no.length){ rad.checked = true; d.karar = 'numara_ata'; }
    if(rad && !d.no.length && d.karar==='numara_ata'){ delete d.karar; rad.checked=false; }
    card.querySelectorAll('.fields').forEach(f => f.classList.toggle('show',
      f.dataset.for === d.karar || f.dataset.for === 'hep'));
    saveLS(); updateProgress(); updateDecidedNotes();
    return;
  }
  // radyo
  if(e.target.matches('input[type=radio]')){
    const d = decisions[k] || {};
    d.karar = e.target.value;
    decisions[k] = d; saveLS();
    card.querySelectorAll('.fields').forEach(f => f.classList.toggle('show',
      f.dataset.for === d.karar || f.dataset.for === 'hep'));
    card.classList.toggle('decided', d.karar && d.karar!=='atla');
    card.classList.toggle('skipped', d.karar==='atla');
    updateProgress(); updateDecidedNotes();
    return;
  }
  // alan -> anlık kaydet
  if(e.target.matches('[data-f]')){
    e.target.addEventListener('change', () => {
      const d = decisions[k] || {};
      d[e.target.dataset.f] = e.target.value;
      decisions[k] = d; saveLS(); updateDecidedNotes();
    }, {once:true});
    return;
  }
  // kaydet / sil
  if(e.target.matches('.save')){
    const d = decisions[k] || {};
    card.querySelectorAll('[data-f]').forEach(inp => { d[inp.dataset.f] = inp.value; });
    if(g==='g2'){
      const elle = (d.no_elle||'').split(/[,;]/).map(x=>x.trim()).filter(Boolean);
      const secili = (d.no||[]).concat(elle);
      if(d.karar==='numara_ata') d.no = [...new Set(secili)];
    }
    if(d.karar==='baslik' && !(d.baslik||'').trim()){ alert('Başlık alanı boş — karar “başlık yaz” ise bir ad gir.'); return; }
    if(d.karar==='nesne_degil' && !(d.kayit_tipi)){ alert('“Nesne değil” için tip seç (parça/bölüm/kavram…).'); return; }
    if(d.karar==='numara_duzelt' && !(d.yeni_no||'').trim()){ alert('Doğru numarayı yaz.'); return; }
    d.tarih = new Date().toISOString().slice(0,16);
    decisions[k] = d; saveLS(); render();
    return;
  }
  if(e.target.matches('.clear')){
    delete decisions[k]; saveLS(); render();
  }
});

/* ---------- dışa/içe ---------- */
document.getElementById('btn-export').addEventListener('click', () => {
  const out = { uretim: 'hetega hakemleme arayüzü', tarih: new Date().toISOString(),
                kaynak_uretim_tarihi: DATA.uretim_tarihi,
                karar_sayisi: Object.keys(decisions).filter(k=>decisions[k].karar).length,
                kararlar: Object.entries(decisions)
                  .filter(([k,v]) => v && v.karar)
                  .map(([k,v]) => Object.assign({tur: k.split(':')[0], id: k.split(/:(.+)/)[1]}, v)) };
  const blob = new Blob([JSON.stringify(out, null, 1)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'hakem-kararlari-' + new Date().toISOString().slice(0,10) + '.json';
  a.click();
});
document.getElementById('btn-import').addEventListener('click', () => document.getElementById('file-import').click());
document.getElementById('file-import').addEventListener('change', e => {
  const f = e.target.files[0]; if(!f) return;
  const rd = new FileReader();
  rd.onload = () => {
    try{
      const j = JSON.parse(rd.result);
      const arr = j.kararlar || j;
      let n = 0;
      for(const it of arr){ if(it && it.tur && it.id){ decisions[dkey(it.tur,it.id)] = it; n++; } }
      saveLS(); render(); alert(n + ' karar içe aktarıldı.');
    }catch(err){ alert('JSON okunamadı: ' + err.message); }
  };
  rd.readAsText(f);
});
document.getElementById('btn-clear').addEventListener('click', () => {
  if(!confirm('Bu sekmedeki (' + DATA[curG].length + ' kayıt) tüm kararlar silinsin mi?')) return;
  for(const r of DATA[curG]) delete decisions[dkey(curG, r.id)];
  saveLS(); render();
});

render();
</script>
</body>
</html>
'''

_json = json.dumps(DATA, ensure_ascii=False).replace('</', '<\\/')   # </script> kırılmasın
html_out = (TEMPLATE
            .replace('__TARIH__', DATA['uretim_tarihi'])
            .replace('__DATA__', _json))

outdir = os.path.join(HEDEF, 'calisma', 'hakemleme')
os.makedirs(outdir, exist_ok=True)
outp = os.path.join(outdir, 'index.html')
open(outp, 'w', encoding='utf-8').write(html_out)
print('-> %s (%d KB)' % (outp, len(html_out) // 1024))
