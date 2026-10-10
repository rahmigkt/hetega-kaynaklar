# -*- coding: utf-8 -*-
"""
HETEGA — Envanter numarası normalizasyonu (v2)

Kitapta ve sitede görülen BÜTÜN biçimleri tek kanonik şemaya indirger.
Kanonik şema:  <HARF><2 hane grup>.<2 hane sıra>   örn. A01.05
               <HARF><sayı>  (noktasız seriler)     örn. J224
Alt-öğe:       A01.05-1
Sonek:         C01.18A

Kapsanan OCR varyantları:
  'A 1.05'  'A. 1.08'  'H. 3.05'  'd 1.08' (küçük harf)  'F 04'  'A01.04'
  'Kİ. 10'  -> K 1.10  (OCR: 'İ' aslında '1')
  'H 8.01-26' / 'A 6.07-6.10' / 'J 234-36' / 'J 239-58' / 'J 22-27'  -> aralık
  'D 1.32 ve 1.33' / 'H 4.07 ve H 4.01'  -> SAYMA (aralık değil)
  'H 9.01 ila H 9.14'  -> aralık
  'H 1.06-1' / 'J 354-1, 354-2, 354-3'  -> alt-öğe
  'C 1.18A' / 'H5.02A'  -> sonek varyantı
  'H 4.01/H'  -> artık harf atılır
  'E 2.01 1472'  -> OCR artığı atılır
  '2. 21' / '3.13' / '6.04'  -> harf OCR'da düşmüş; harfsonrasi=None döner,
                                 çağıran taraf bölüm önekinden tamamlar
  '15354'  -> başka müzenin (Kahire) numarası: yok sayılır
"""
import re

GECERLI_ONEK = set('ABCDEFGHJK')          # müze önekleri (I kullanılmıyor)
EOL = r'\s*([A-Za-z]?)\Z'

# 'Kİ' gibi: harf + İ/I/l/1  -> harf + rakam
HARF_KARISIK = re.compile(r'\A([A-Za-zÇĞİÖŞÜçğıöşü])[İIl1](?=\s*[\.\s]|\Z)')


def _canon(L, g, k=None):
    L = L.upper()
    if L == 'İ': L = 'I'
    if k in (None, ''):
        return '%s%d' % (L, int(g))
    return '%s%02d.%02d' % (L, int(g), int(k))


def _abbrev_range(a, z):
    """J234-36 -> (234,236) ; J239-58 -> (239,258). Olmuyorsa None."""
    if z > a:
        return (a, z)
    sa, sz = str(a), str(z)
    if len(sz) < len(sa):
        cand = int(sa[:len(sa) - len(sz)] + sz)
        if cand > a and cand - a <= 300:
            return (a, cand)
    return None


ATOM = re.compile(r'\A([A-Za-zÇĞİÖŞÜçğıöşü])\s*\.?\s*(\d{1,3})\s*(?:\.\s*(\d{1,3}))?\Z')
BARE = re.compile(r'\A(\d{1,3})\s*\.\s*(\d{1,3})\Z')          # '2. 21' / '3.13'
BARE2 = re.compile(r'\A(\d{1,3})\Z')                            # '21'


def _fix_letter(tok):
    """'Kİ. 10' -> 'K 1.10' ; 'd 1.08' -> 'D 1.08'"""
    tok = tok.strip()
    m = HARF_KARISIK.match(tok)
    if m:
        rest = tok[m.end():].strip().lstrip('.').strip()
        digit = '1' if tok[m.end() - 1] in 'İIl' else tok[m.end() - 1]
        return '%s %s.%s' % (m.group(1), digit, rest) if rest else '%s %s' % (m.group(1), digit)
    return tok


def _parse_atom(tok, carry=None):
    """-> (kanonik numara | None, sonek, 'bare' ise (grup,sıra))"""
    tok = _fix_letter(tok.strip().rstrip('.,;:()'))
    if not tok:
        return None, '', None
    suf = ''
    ms = re.match(r'\A(.*\d)\s*([A-Za-z])\Z', tok)
    if ms and ms.group(2).upper() not in ('M', 'N'):
        tok, suf = ms.group(1), ms.group(2).upper()
        tok = tok.strip()
    msub = re.match(r'\A([A-Za-zÇĞİÖŞÜçğıöşü])\s*\.?\s*(\d{1,4})\s*-\s*(\d{1,2})\Z', tok)
    if msub:
        L, base, sub = msub.groups()
        if L.upper() in GECERLI_ONEK:
            return '%s%s-%s' % (L.upper(), int(base), sub), suf, None
    m = ATOM.match(tok)
    if m:
        L, g, k = m.groups()
        if L.upper() not in GECERLI_ONEK and L.upper() != 'I':
            return None, suf, None
        return _canon(L, g, k), suf, None
    mb = BARE.match(tok)
    if mb:
        if carry:
            return _canon(carry, mb.group(1), mb.group(2)), suf, None
        return None, suf, ('%s.%s' % (mb.group(1), mb.group(2)))
    mb2 = BARE2.match(tok)
    if mb2 and carry:
        return _canon(carry, mb2.group(1)), suf, None
    return None, suf, None


def _validate(out, parents, susp, s, bare):
    good = []
    for n in out:
        m = re.match(r'\A([A-ZÇĞİÖŞÜ])(\d)', n)
        if m and m.group(1) in GECERLI_ONEK:
            if n not in good:
                good.append(n)
        else:
            susp = True
    parents = [p for p in parents
               if re.match(r'\A[A-ZÇĞİÖŞÜ]\d', p) and p[0] in GECERLI_ONEK]
    return good, parents, (susp or (not good and not bare)), s, bare


def _range_body(g1, k1, g2, k2, L):
    try:
        if k1:
            if k2: g, a, z = int(g2 or g1), int(k1), int(k2)
            else:  g, a, z = int(g1), int(k1), int(g2)
            rg = _abbrev_range(a, z)
            if rg and rg[1] >= rg[0]:
                return [_canon(L, g, '%d' % n) for n in range(rg[0], rg[1] + 1)], False
            return ['%s-%s' % (_canon(L, g1, k1), z)], False      # alt-öğe
        a, z = int(g1), int(g2)
        if z <= 9 and a >= 10 and z != a - 1:
            # 'J 90-1' -> alt-öğe (bitişik aralık 'J 89-90' biçiminde yazılır)
            return ['%s%d-%d' % (L, a, z)], False
        rg = _abbrev_range(a, z)
        if rg:
            return [_canon(L, '%d' % n) for n in range(rg[0], rg[1] + 1)], False
    except Exception:
        pass
    return [_canon(L, g1, k1)], True


NUMPAT = r'([A-Za-zÇĞİÖŞÜçğıöşüİ])\s*\.?\s*(\d{1,3})\s*(?:\.\s*(\d{1,3}))?'
NUMPAT_BARE = r'(\d{1,3})\s*\.\s*(\d{1,3})'


def expand(raw):
    """-> (kanonik numaralar, üst numaralar, şüpheli mi, normalize ham, harfsizler)"""
    bare = []
    if not raw:
        return [], [], False, '', bare
    s = re.sub(r'\s+', ' ', raw.replace('\u00a0', ' ')).strip()
    susp = False
    out, parents = [], []

    def add(n, parent=None):
        if n and n not in out:
            out.append(n)
        if parent and parent not in parents and parent not in out:
            parents.append(parent)

    s2 = _fix_letter(s)

    # --- alt-öğe listesi: 'J 354-1, 354-2, 354-3' / 'J354-1/2/3' ---
    m = re.match(r'\A([A-Za-z])\s*\.?\s*(\d{1,4})\s*-\s*(\d{1,2})'
                 r'((?:\s*[,;/]\s*(?:\d{1,4}\s*-\s*)?\d{1,2})+)\Z', s2)
    if m:
        L, base, sub, rest = m.groups()
        L = L.upper()
        add('%s%s-%s' % (L, base, sub), parent='%s%s' % (L, int(base)))
        for piece in re.split(r'[,;/]', rest):
            mm = re.match(r'\s*(?:(\d{1,4})\s*-\s*)?(\d{1,2})\s*\Z', piece)
            if mm:
                b2 = mm.group(1) or base
                add('%s%s-%s' % (L, b2, mm.group(2)), parent='%s%s' % (L, int(b2)))
        return _validate(out, parents, susp, s, bare)

    # --- 'ila' / 'bis' / 'kadar' => aralık ---
    m = re.match(r'\A' + NUMPAT + r'\s+(?:ila|bis|to|kadar)\s+(?:([A-Za-z])\s*\.?\s*)?'
                 r'(\d{1,3})\s*(?:\.\s*(\d{1,3}))?\Z', s2, re.I)
    if m:
        L, g1, k1, _L2, g2, k2 = m.groups()
        nums, sp = _range_body(g1, k1, g2, k2, L)
        for n in nums: add(n)
        return _validate(out, parents, sp, s, bare)

    # --- '-' => aralık VEYA alt-öğe ---
    m = re.match(r'\A' + NUMPAT + r'\s*[-–—]\s*(?:([A-Za-z])\s*\.?\s*)?(\d{1,3})'
                 r'\s*(?:\.\s*(\d{1,3}))?' + EOL, s2)
    if m:
        L, g1, k1, _L2, g2, k2, _suf = m.groups()
        nums, sp = _range_body(g1, k1, g2, k2, L)
        for n in nums:
            if re.match(r'\A[A-Z]\d+\.\d+-\d+\Z', n) or re.match(r'\A[A-Z]\d+-\d+\Z', n):
                add(n, parent=n.split('-')[0])
            else:
                add(n)
        return _validate(out, parents, sp, s, bare)

    # --- 've' / ',' / ';' => SAYMA ---
    if re.search(r'\s+ve\s+|[,;]', s2):
        carry = None; sub_base = None
        for p in re.split(r'\s+ve\s+|[,;]', s2):
            p = p.strip()
            if not p:
                continue
            if not carry:
                cm = re.match(r'\A\s*([A-Za-zÇĞİÖŞÜ])', _fix_letter(p))
                if cm and cm.group(1).upper() in GECERLI_ONEK:
                    carry = cm.group(1).upper()
            # çıplak sayı + aktif alt-öğe tabanı: 'J 84-1, 2 ve 3' -> J84-2, J84-3
            if sub_base and re.fullmatch(r'\d{1,2}', p):
                add('%s%s-%s' % (sub_base[0], sub_base[1], p),
                    parent='%s%s' % sub_base)
                continue
            n, suf, br = _parse_atom(p, carry)
            if n:
                carry = n[0]
                m2 = re.match(r'\A([A-Z])(\d{1,4})-(\d{1,2})\Z', n)
                if m2:
                    sub_base = (m2.group(1), m2.group(2))
                    add(n, parent='%s%s' % sub_base)
                else:
                    add(n + suf if suf else n, parent=(n if suf else None))
            elif br:
                bare.append(br)
            else:
                susp = True
        return _validate(out, parents, susp, s, bare)

    # --- '/' => parçala ---
    if '/' in s2:
        carry = None
        for p in s2.split('/'):
            if not p.strip():
                continue
            if re.fullmatch(r'[A-Za-z]', p.strip()):
                susp = True
                continue
            if not carry:
                cm = re.match(r'\A\s*([A-Za-zÇĞİÖŞÜ])', _fix_letter(p))
                if cm and cm.group(1).upper() in GECERLI_ONEK:
                    carry = cm.group(1).upper()
            n, suf, br = _parse_atom(p, carry)
            if n:
                add(n + suf if suf else n, parent=(n if suf else None))
            elif br:
                bare.append(br)
            else:
                susp = True
        return _validate(out, parents, susp, s, bare)

    # --- tek atom ---
    n, suf, br = _parse_atom(s2)
    if n:
        add(n + suf if suf else n, parent=(n if suf else None))
        return _validate(out, parents, susp, s, bare)

    # --- yedek: metin içindeki tüm atomları topla ('E 2.01 1472') ---
    for fnd in re.findall(r'[A-Za-zÇĞİÖŞÜ]\s*\.?\s*\d{1,3}(?:\s*\.\s*\d{1,3})?', s2):
        nn, ss, _ = _parse_atom(fnd)
        if nn:
            add(nn + ss if ss else nn, parent=(nn if ss else None))
    if not out:
        mb = BARE.match(s2.strip())
        if mb:
            bare.append('%s.%s' % mb.groups()[:2])
        elif re.fullmatch(r'\d{4,}', s2.strip()):
            pass                      # başka müzenin numarası (örn. Kahire 15354)
        else:
            susp = True
    return _validate(out, parents, susp, s, bare)


if __name__ == '__main__':
    tests = ['A 1.05', 'A. 1.08', 'A. 1.09', 'H. 3.05', 'd 1.08', 'Kİ. 10', 'F 04',
             'J 224', 'H 8.01-26', 'A 6.07-6.10', 'J 234-36', 'J 239-58', 'J 22-27',
             'J 2.27-32', 'D 1.32 ve 1.33', 'H 4.07 ve H 4.01', 'H 9.01 ila H 9.14',
             'J 93 ve 94', 'H 1.06-1', 'C 1.18A', 'H 4.01/H', 'E 2.01 1472',
             'J 354-1, 354-2, 354-3', 'J 357-1, 357-2', '2. 21', '3.13', '6.04',
             '15354', 'A 2.16', 'D', 'K', 'A01.04']
    for t in tests:
        nums, par, susp, norm, br = expand(t)
        show = nums if len(nums) <= 6 else nums[:4] + ['…(%d)' % len(nums)]
        extra = ('harfsiz:' + ','.join(br)) if br else ''
        print('%-26s -> %-40s %s%s' % (t, ','.join(show), extra + ' ',
                                        'ŞÜPHELİ' if susp else ''))
