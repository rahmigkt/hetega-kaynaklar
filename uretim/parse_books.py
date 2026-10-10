# -*- coding: utf-8 -*-
"""
HETEGA — Kitap Envanteri Çıkarımı (v4)
Fuat Sezgin, "İslam'da Bilim ve Teknik" Cilt I-V (İBB Kültür A.Ş. / TÜBA, 2007-2008)

OCR sayfa düzeni:
  A) [sayfa] [BÜYÜK HARF head] / Başlık (boş satırla ayrık kısa satırlar) /
     gövde paragrafı (3+ bitişik satır) / Modelimiz: / (Envanter No: X)
  B) [head] [sayfa] "2 Havan" / menşe-dönem / malzeme / ölçü / (Envanter No: X)
  C) [head] [sayfa] Modelimiz: ... / (Envanter No: X)   -> başlık resim altında
"""
import re, glob, os, json, collections
import numnorm

import yollar
HERE = yollar.ARA
UP_DIR = yollar.OCR

# ============================================================ İÇİNDEKİLER
TOC = {
 'II': [(1,1,'Astronomi'),(3,2,'Giriş'),(16,2,'Planetaryumlar ve Gök-küreler'),
  (19,2,'Rasathaneler'),(25,3,'Rey Rasathanesi'),(26,3,'Hemedân Rasathanesi'),
  (28,3,'Merâğa Rasathanesi'),(34,3,'İstanbul Rasathanesi'),(36,3,'Hven Rasathanesi'),
  (38,3,'Merâğa Rasathanesi Aletleri'),(53,3,'İstanbul Rasathanesi Aletleri'),
  (62,3,'Hven Rasathanesi Aletleri'),(69,3,'Semerkant Rasathanesi'),
  (72,3,'Jaipur Rasathanesi'),(76,3,'Delhi Rasathanesi'),(78,2,'Astronomi Aletleri'),
  (79,3,'Usturlaplar'),(116,3,'Evrensel Diskler'),(120,3,'Küresel Usturlap'),
  (136,3,'Kadranlar'),(145,3,'Diğer Aletler'),(173,3,'Ekvatoryumlar')],
 'III': [(1,1,'Coğrafya'),(3,2,'Giriş'),(9,2,'Avrupalı Haritaların Arap Kökeni'),
  (21,2,'Yerküreleri ve Dünya Haritaları'),(30,2,'Modeller'),(33,1,'Denizcilik'),
  (35,2,'Giriş'),(45,2,'Denizcilik Aletleri'),(54,2,'Gemi Modelleri'),(57,2,'Pusulalar'),
  (83,1,'Saatler'),(85,2,'Doğu ve Kuzey Afrika Saatleri'),
  (108,2,'İspanyol-Arap Saatleri'),(118,2,'Takıyyeddîn’in Mekanik Saatleri'),
  (123,1,'Geometri'),(125,2,'Giriş'),(140,2,'Ölçüm ve Çizim Aletleri'),
  (163,1,'Optik'),(165,2,'Optik Aletler ve Deney Düzenekleri')],
 'IV': [(1,1,'Tıp'),(3,2,'Tıbbi Aletler'),(7,2,'Anatomik Resim Serileri'),
  (16,2,'Görme Organının Anatomik Çizimleri'),(28,2,'Ünlü Tabiplerin Portreleri'),
  (35,2,'Aletler ve Modeller'),(35,3,'Hacamat'),(36,3,'Koterizasyon'),
  (39,3,'Kafa ve Yüz Tedavileri'),(42,3,'Göz Tedavileri'),
  (54,3,'Kulak-Burun-Boğaz Tedavisi'),(61,3,'Diş Tedavisi'),
  (67,3,'Sinir Hastalıkları Tedavisi'),(69,3,'İdrar Yolları Tedavisi'),
  (73,3,'Jinekolojik Aletler'),(81,3,'Ortopedi'),(83,3,'Genel Cerrahi'),
  (86,3,'Kaza Cerrahisi'),(92,3,'el-Fustât’tan Muhtelif Aletler'),
  (95,1,'Kimya'),(97,2,'Giriş'),(109,2,'Laboratuvar Araçları'),
  (155,1,'Mineraller ve Fosil Oluşumlar'),(157,2,'Giriş'),(166,2,'Örnekler')],
 'V': [(1,1,'Fizik ve Teknik'),(3,2,'Teraziler ve Ölçüm Araçları'),
  (16,2,'Pompa Düzenekleri'),(30,2,'Değirmenler'),(35,2,'Muhtelif Aparatlar'),
  (49,2,'Otomatlar'),(56,2,'Kilitler'),(60,2,'Perpetua mobilia'),(63,1,'Mimari'),
  (65,2,'Yüksek Okullar'),(68,2,'Hastaneler'),(76,2,'Camiler'),(91,1,'Savaş Tekniği'),
  (93,2,'Giriş'),(106,2,'Mancınıklar ve Büyük Ok Atarlar'),(120,2,'Bombalar ve Roketler'),
  (131,2,'Ateşli Silahlar'),(136,2,'Savaş Makineleri'),(139,1,'Antik Objeler'),
  (141,2,'Metal, Cam, Seramik, Ahşap ve Taş Objeler'),
  (177,2,'Orientleştirici Stilde Avrupa Camı ve Seramiği')],
 'I': [],
}

# ============================================================ YARDIMCI
def nrm(s): return re.sub(r'\s+', ' ', s).strip()

OCR_FIX = [
    (r'\bc(?=[A-ZÇĞİÖŞÜ][a-z])', ''), (r'\bcb(?=[a-z])', 'Ebû'),
    (r'Siczf', 'Siczî'), (r'Süfı', 'Sûfî'), (r'BIrün', 'Bîrûn'),
    (r'Blrün', 'Bîrûn'), (r'Zahrâvı', 'Zehrâvî'), (r'Takiyyeddln', 'Takıyyeddîn'),
    (r'el-ldrls', 'el-İdrîs'), (r'şerlf', 'Şerîf'), (r'Hâzinf', 'Hâzinî'),
    (r'el-Hâzinı', 'el-Hâzinî'), (r"Me°mun", "Me'mûn"), (r'el-Urdf', 'el-Urdî'),
    (r'Ala°uddevle', 'Alâüddevle'), (r'ebVasitı', 'eb-Vâsıtî'), (r'\bAlı\b', 'Alî'),
    (r'°', "'"), (r'[•♦❖✦◊]', ' '), (r'\s+', ' '),
]
def fix_ocr(s):
    for a, b in OCR_FIX: s = re.sub(a, b, s)
    s = s.replace('\u00ad', '').replace('¬ ', '').replace('¬', '')
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'^[\W_]+', '', s).strip()          # baştaki !!♦ / y I - artıkları
    s = re.sub(r'\s{2,}', ' ', s)
    return s

def is_page(s): return bool(re.fullmatch(r'\d{1,3}', s))

def is_caps(s):
    L = [c for c in s if c.isalpha()]
    if len(L) < 3 or len(s) > 48: return False
    return sum(1 for c in L if c.isupper()) / len(L) > 0.85

def is_foot(s): return bool(re.match(r'^\d{1,2}\s{2,}[A-ZÇĞİÖŞÜa-z(]', s)) and len(s) > 45

STOP = re.compile(r'^(Modelimiz|Modellerimiz|Model\b|Şekil|Şekiller|Resim|Resimler|'
    r'Malzeme|Çap|Uzunluk|Yükseklik|Genişlik|Boy\b|Boyu|Toplam|Ahşap|Pirinç|Bakır|'
    r'Çelik|Cam\b|Leclerc|Sezgin|Krş|Bkz|a\.e\.|a\.y\.|Ölçek|Ölçüler|Ağırlık|'
    r'Kalınlık|Envanter|Demir|Balmumu|Mürekkep|Dekoratif|Hâkkedilmiş|Sert ağaç|'
    r'Altlık|İçinde|Üzerinde|Beş|Dört|İki|Üç|Cam,|Pirinç,|Bakır alaşım|'
    r'Metin|Levha|Kâğıt|Skalalar|Nlşâpür|Buluntu|Geç antikite|Osmanlı\b|'
    r'Mısır\b|İran\b|Suriye\b|Anadolu\b|Endülüs|Bronz|Kalaylı)', re.I)

SRC_RE = re.compile(
    r"([A-ZÇĞİÖŞÜa-z'’\.\- ]{2,70}?)\s*(?:\(([^)]{0,45}y(?:üzyıl|y\.)[^)]{0,20})\)\s*)?"
    r"[’']?(?:nin|nın|nun|nün|in|ın|un|ün)\s+"
    r"([A-Za-zÇĞİÖŞÜçğıöşü'’\-\.\s]{3,80}?)\s*(?:inden|ından|undan|ünden|den|dan|ında)")

ORIGIN_RE = re.compile(r"^([A-ZÇĞİÖŞÜ][\wÇĞİÖŞÜçğıöşü'’\- ]{2,40}?),\s*"
                       r"(.{0,60}?y(?:üzyıl|y\.).{0,25})\.?\Z", re.I)

DIM_RE = re.compile(r'((?:Çap|Uzunluk|Yükseklik|Genişlik|Boy|Toplam yükseklik|Ölçü|'
    r'Ağırlık|Kalınlık|En|Derinlik|Ölçek)\s*[:=]?\s*[0-9][0-9\.,;x× /\-]*'
    r'(?:\s*(?:cm|mm|m|kg|gr))?)', re.I)
MAT = ('pirinç|ahşap|bakır|çelik|cam|demir|bronz|altın|gümüş|maun|meşe|armut ağacı|'
       'ceviz|kemik|fildişi|seramik|taş|mermer|plastik cam|alüminyum|paslanmaz çelik|'
       'kâğıt|kağıt|deri|kumaş|ipek|balmumu|kalay|bakır alaşım|altın yaldız|gümüş yaldız')
MAT_RE = re.compile(r'\b(%s)\b' % MAT, re.I)

# Envanter referansı iki biçimde geçer:
#   (a) parantezli  : "(Envanter No: D 1.04 ve D 1.05)"  — satıra bölünebilir
#   (b) parantezsiz : "Envanter No: A 4.27"
# Bu yüzden eşleştirme satır sonlarından bağımsız (S2) yapılır.
_NB   = r'(?:[A-Za-zÇĞİÖŞÜçğıöşü]\s*\.?\s*\d{1,3}(?:\s*\.\s*\d{1,3})?|\d{1,3}\s*\.\s*\d{1,3})'
_TAIL = r'(?:\s*(?:[-–—]|ve|ila|[,;])\s*(?:[A-Za-zÇĞİÖŞÜçğıöşü]\s*\.?\s*)?\d{1,3}(?:\s*\.\s*\d{1,3})?)*'
INV_PAREN = re.compile(r'\(\s*Envanter\s+N[or]{1,2}\s*\.?\s*:?\s*([^)]{1,220})\)', re.I)
INV_PLAIN = re.compile(r'Envanter\s+N[or]{1,2}\s*\.?\s*:\s*((' + _NB + r')' + _TAIL + r')', re.I)

def find_inv(S2):
    """S2 (satır sonları boşluğa çevrilmiş metin) üzerinde tüm envanter
    referanslarını bul -> [(start, end, blob)], konuma göre sıralı, çakışmasız."""
    found = [(m.start(), m.end(), m.group(1)) for m in INV_PAREN.finditer(S2)]
    for m in INV_PLAIN.finditer(S2):
        if any(not (m.end() <= a or m.start() >= b) for a, b, _ in found):
            continue
        found.append((m.start(), m.end(), m.group(1)))
    found.sort()
    return found


# (cilt, bölüm) -> envanter öneki. Kitaptaki doğrulanmış bloklardan türetildi;
# OCR'da harfi düşmüş numaraları ('2. 21', '3.13', '6.04') tamamlamak için.
SECTION_PREFIX = {
 ('II','Astronomi'):'A',
 ('III','Coğrafya'):'A', ('III','Denizcilik'):'C', ('III','Saatler'):'B',
 ('III','Geometri'):'D', ('III','Optik'):'E',
 ('IV','Tıp'):'H', ('IV','Kimya'):'K', ('IV','Mineraller ve Fosil Oluşumlar'):'K',
 ('V','Fizik ve Teknik'):'E', ('V','Mimari'):'F', ('V','Savaş Tekniği'):'G',
 ('V','Antik Objeler'):'J',
}

# ============================================================ BAŞLIK
def group_lines(raw_window):
    groups = []; cur = []
    for raw in raw_window:
        s = nrm(raw)
        if not s:
            if cur: groups.append(cur); cur = []
        else:
            cur.append(s)
    if cur: groups.append(cur)
    return groups

def guess_title(groups):
    cand = []; fig_no = ''; origin = ''; date = ''
    for g in groups:
        j = nrm(' '.join(g))
        if len(g) >= 3:            break          # paragraf = gövde
        if is_caps(j):             break          # yeni bölüm başlığı
        if STOP.match(j):          break
        if SRC_RE.search(j):       break
        if is_foot(j):             break
        mo = ORIGIN_RE.match(j)
        if mo:
            origin, date = mo.group(1).strip(), nrm(mo.group(2)); break
        if len(j) > 62:            break
        m = re.match(r'^(\d{1,3})\s+(.{2,50})\Z', j)
        if m and not cand:
            fig_no = m.group(1); cand.append(m.group(2)); continue
        cand.append(j)
        if len(cand) >= 4: break
    return fix_ocr(' '.join(cand)), fig_no, origin, date

def guess_source(ctx):
    for s, kind in ctx:
        if kind in ('page', 'head') or len(s) > 230: continue
        m = SRC_RE.search(s)
        if m:
            return {'bilgin': fix_ocr(m.group(1)), 'donem': nrm(m.group(2) or ''),
                    'eser': fix_ocr(m.group(3)), 'kaynak_ham': nrm(s)}
    return {'bilgin': '', 'donem': '', 'eser': '', 'kaynak_ham': ''}

def guess_tech(ctx, tail):
    txt = re.sub(r'\s+', ' ', ' '.join(s for s, k in ctx if k == 'body') + ' ' + tail)
    return {'boyutlar': [nrm(d) for d in DIM_RE.findall(txt)][:6],
            'malzeme': sorted({mm.lower() for mm in MAT_RE.findall(txt)})}

# ============================================================ AYRIŞTIRMA
def toc_lookup(vol, page):
    e = TOC.get(vol, [])
    if not e or page is None: return ('', '', '')
    c1 = c2 = c3 = ''
    for p, lvl, t in e:
        if p > page: break
        if lvl == 1:   c1, c2, c3 = t, '', ''
        elif lvl == 2: c2, c3 = t, ''
        else:          c3 = t
    return (c1, c2, c3)

def parse_volume(vol, lines):
    ents = []; page = None; head = None
    for i, raw in enumerate(lines):
        s = nrm(raw)
        if not s: continue
        kind = 'body'
        if is_page(s):
            kind = 'page'
            try: page = int(s)
            except Exception: pass
        elif is_caps(s):
            kind = 'head'; head = s
        elif is_foot(s):
            kind = 'foot'
        ents.append({'i': i, 's': s, 'k': kind, 'p': page, 'h': head})

    S = '\n'.join(e['s'] for e in ents)
    S2 = S.replace('\n', ' ')          # aynı uzunluk -> offset haritası geçerli
    offs = []; pos = 0
    for e in ents:
        offs.append(pos); pos += len(e['s']) + 1

    def off2idx(o):
        lo, hi = 0, len(offs) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if offs[mid] <= o: lo = mid
            else: hi = mid - 1
        return lo

    recs = []; prev = -1
    for _st, _en, blob_raw in find_inv(S2):
        idx = off2idx(_st)
        if idx <= prev: continue

        nums, parents, susp, blob, bare = numnorm.expand(blob_raw)
        if not nums and not bare: continue

        lo = max(prev + 1, idx - 50)
        ctx = [(ents[j]['s'], ents[j]['k']) for j in range(lo, idx + 1)]

        zstart = lo
        for j in range(lo, idx + 1):
            if ents[j]['k'] in ('page', 'head'): zstart = j + 1
        if zstart > idx: zstart = max(lo, idx - 14)
        groups = group_lines(lines[ents[zstart]['i']: ents[idx]['i'] + 1])
        if not groups:
            groups = group_lines(lines[max(0, ents[idx]['i'] - 30): ents[idx]['i'] + 1])
        title, fig, origin, date = guess_title(groups)

        e = ents[idx]
        b1, b2, b3 = toc_lookup(vol, e['p'])

        # desen C yedeği: başlık yoksa önce kitabın büyük-harf üst başlığı,
        # sonra daha geniş pencerede son izole satır grubu
        tquality = 'iyi'
        if len(title) < 4 or re.search(r'Envanter|^\d{3,}|^\d+[.,]', title):
            hd = fix_ocr(e['h'] or '')
            if len(hd) > 3 and hd.upper() not in (b1.upper(), b2.upper()):
                title, tquality = hd, 'üstbaşlık'
            else:
                wide = group_lines(lines[max(0, ents[idx]['i'] - 70): ents[idx]['i'] + 1])
                for g in reversed(wide):
                    j = nrm(' '.join(g))
                    if len(g) <= 2 and 3 < len(j) < 55 and not STOP.match(j) \
                       and not is_caps(j) and not is_page(j) and not is_foot(j) \
                       and 'Envanter' not in j \
                       and not re.search(r'a\.e\.|a\.y\.|Krş|Bkz|s\.\s*\d', j) \
                       and not SRC_RE.search(j) and not ORIGIN_RE.match(j):
                        title, tquality = fix_ocr(j), 'tahmin'
                        break
                else:
                    title, tquality = '', 'yok'

        if not origin:
            for s, k in ctx:
                mo = ORIGIN_RE.match(s)
                if mo: origin, date = mo.group(1).strip(), nrm(mo.group(2)); break

        src = guess_source(ctx); tech = guess_tech(ctx, blob_raw)

        # harfi OCR'da dusmus numaralari (orn. '2. 21') bolum onekinden tamamla
        if bare:
            inferred = SECTION_PREFIX.get((vol, b1)) or SECTION_PREFIX.get((vol, b2))
            filled = []
            for br in bare:
                gk = br.split('.')
                if inferred and len(gk) == 2:
                    filled.append('%s%02d.%02d' % (inferred, int(gk[0]), int(gk[1])))
            for fnum in filled:
                if fnum not in nums: nums.append(fnum)
            if filled: susp = True   # cikarim oldugu isaretlensin

        recs.append(dict({
            'cilt': vol, 'kitap_sayfa': e['p'], 'satir': e['i'] + 1,
            'bolum': b1, 'alt_bolum': b2, 'alt_baslik': b3,
            'kitap_ust_baslik': e['h'], 'kitap_fig_no': fig,
            'envanter_nolar': nums, 'ust_nolar': parents,
            'ham_envanter': blob, 'numara_supheli': susp,
            'onek_cikarim': bool(bare and nums),
            'baslik': title, 'baslik_kalite': tquality,
            'mense': origin, 'donem_kitap': date,
            'baglam': [s for s, k in ctx][-26:],
        }, **src, **tech))
        prev = idx
    return recs

def load():
    v = {}
    for f in sorted(glob.glob(os.path.join(UP_DIR, '*_djvu.txt'))):
        m = re.search(r'cilt\s+([IV]+)', os.path.basename(f))
        if m:
            v[m.group(1)] = open(f, encoding='utf-8', errors='replace').read().split('\n')
    return v

# ============================================================ ANA
if __name__ == '__main__':
    vols = load(); blocks = []
    for v in ['II', 'III', 'IV', 'V']:
        r = parse_volume(v, vols[v])
        print('Cilt %-3s -> %3d blok' % (v, len(r)))
        blocks += r

    flat = []
    for b in blocks:
        for num in b['envanter_nolar']:
            rr = dict(b); rr['envanter_no'] = num
            rr['coklu'] = len(b['envanter_nolar']) > 1
            flat.append(rr)

    uniq = sorted({r['envanter_no'] for r in flat})
    print('\n%d blok -> %d kayıt / %d benzersiz envanter no'
          % (len(blocks), len(flat), len(uniq)))
    q = collections.Counter(b['baslik_kalite'] for b in blocks)
    print('başlık kalitesi : iyi=%d  üstbaşlık=%d  tahmin=%d  yok=%d'
          % (q['iyi'], q['üstbaşlık'], q['tahmin'], q['yok']))
    ws = sum(1 for b in blocks if b['bilgin'] or b['eser'])
    print('bilgin/eser bulunan : %d/%d (%.0f%%)' % (ws, len(blocks), 100.0 * ws / len(blocks)))

    json.dump(blocks, open(os.path.join(HERE, 'book_blocks.json'), 'w'),
              ensure_ascii=False, indent=1)
    json.dump(flat, open(os.path.join(HERE, 'book_items.json'), 'w'),
              ensure_ascii=False, indent=1)
    json.dump(uniq, open(os.path.join(HERE, 'book_numbers.json'), 'w'),
              ensure_ascii=False, indent=1)

    print('\n--- önek dağılımı (benzersiz) ---')
    pc = collections.Counter()
    bad = []
    for n in uniq:
        m = re.match(r'[A-ZÇĞİÖŞÜ]+', n)
        if m: pc[m.group(0)] += 1
        else: bad.append(n)
    print('   ', dict(pc.most_common()))
    if bad: print('    geçersiz biçim:', bad[:20])
    print('\n--- örnek: iyi başlıklar ---')
    k = 0
    for b in blocks:
        if b['baslik_kalite'] == 'iyi' and k < 12:
            print('  %-14s s.%-4s %-44s | %s > %s' % (
                ','.join(b['envanter_nolar'])[:14], b['kitap_sayfa'], b['baslik'][:44],
                b['bolum'][:11], (b['alt_bolum'] or b['alt_baslik'])[:20]))
            k += 1
    print('\n--- örnek: tahmin başlıklar ---')
    k = 0
    for b in blocks:
        if b['baslik_kalite'] == 'tahmin' and k < 8:
            print('  %-14s s.%-4s %-44s' % (','.join(b['envanter_nolar'])[:14],
                  b['kitap_sayfa'], b['baslik'][:44]))
            k += 1
