# -*- coding: utf-8 -*-
"""
HETEGA — İnsan düzeltmelerini envanter.json'a uygular.

Girdi:  envanter/envanter.json + envanter/duzeltmeler.json
Çıktı:  envanter/envanter.json (yerinde güncellenir)

Hat arasında build_envanter.py ile alimler.py arasında çalışır; böylece
yeniden üretimde insan kararları kaybolmaz.

duzeltmeler.json bölümleri:
  numara_atamalari     site sayfası <-> kitap numarası eşleştirmesi (record taşır/birleştirir)
  baslik_duzeltmeleri  id -> {baslik, islev, donem, mense, bilgin, not, ozgun_ad}
  dusurulen_basliklar  id -> gerekçe; 'eklenmeye_hazır' ise 'eksik_baslik_bekliyor'a düşür
"""
import re, os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numnorm

try:
    import yollar
    ENV = yollar.ENV
except ImportError:                      # geliştirme düzeni (inventory/)
    ENV = os.path.dirname(os.path.abspath(__file__))

ENVF = os.path.join(ENV, 'envanter.json')
DUZF = os.path.join(ENV, 'duzeltmeler.json')

SITE_ALANLAR = ['yayin', 'gorseller', 'baslik', 'baslik_kaynagi', 'baslik_kalite',
                'islev', 'ozellikler', 'orijinal', 'bilgin', 'bilgin_kaynagi',
                'site_kategori', 'kitap_kaynak_site']


def main():
    env = json.load(open(ENVF, encoding='utf-8'))
    dzl = json.load(open(DUZF, encoding='utf-8'))
    nesneler = env['nesneler']
    idx = {o['id']: o for o in nesneler}
    by_url = {o['yayin']['url']: o for o in nesneler if o.get('yayin', {}).get('url')}

    log = []

    # ------------------------------------------------ 1) numara atamaları
    for a in dzl.get('numara_atamalari', []):
        hedef = idx.get(a['envanter_no'])
        if not hedef:
            log.append('!! numara_atamalari: hedef yok: %s' % a['envanter_no']); continue
        src = None
        if a.get('site_url'):
            src = by_url.get(a['site_url'])
        elif a.get('eski_numara'):
            ids, *_ = numnorm.expand(a['eski_numara'])
            for oid in ids:
                cand = idx.get(oid)
                if cand and cand['dogrulama']['sitede']:
                    src = cand; break
        if not src:
            log.append('!! numara_atamalari: kaynak bulunamadı: %s' % a); continue
        if src is hedef:
            log.append('=  zaten eşleşmiş: %s' % a['envanter_no']); continue

        # site verisini hedefe taşı
        for k in SITE_ALANLAR:
            v = src.get(k)
            if v not in (None, '', [], {}):
                hedef[k] = v
        hedef['dogrulama']['sitede'] = True
        if 'sitede_yok' in hedef['dogrulama']['bayraklar']:
            hedef['dogrulama']['bayraklar'].remove('sitede_yok')
        hedef['dogrulama']['bayraklar'].append('numara_insan_kararıyla_atandı')
        hedef['dogrulama']['notlar'].append('İNSAN KARARI: ' + a['gerekce'])
        # hedef artık kitap + site doğrulamalı -> durum ve bayrakları tazele
        for f in ['kitapta_doğrulanamadı', 'sitede_yok', 'envanter_no_yok']:
            if f in hedef['dogrulama']['bayraklar']:
                hedef['dogrulama']['bayraklar'].remove(f)
        hedef['dogrulama']['kitapta'] = bool(hedef.get('kitap'))
        hedef['yayin']['durum'] = 'yayında'
        hedef['dogrulama']['notlar'].append(
            'Kitap doğrulaması: %s s.%s.' % (hedef['hiyerarsi'].get('cilt', '?'),
            (hedef.get('kitap') or {}).get('sayfa', '?')))

        # kaynağı temizle
        src['dogrulama']['sitede'] = False
        for k in ['gorseller', 'site_kategori', 'kitap_kaynak_site']:
            src[k] = [] if k == 'gorseller' else (src.get(k) if False else None)
        src.pop('site_kategori', None); src.pop('kitap_kaynak_site', None)
        if src.get('baslik_kaynagi') == 'site':
            src['baslik'] = src.get('baslik_kitap') or ''
            src['baslik_kaynagi'] = 'kitap' if src['baslik'] else ''
            src['baslik_kalite'] = 'üstbaşlık' if src['baslik'] else 'yok'
        if src.get('kitap'):
            hazir = src['baslik_kalite'] == 'iyi' and len(src['baslik']) >= 4
            src['yayin'] = {'durum': 'eklenmeye_hazır' if hazir else 'eksik_baslik_bekliyor',
                            'url': '', 'slug': src['yayin'].get('slug', '')}
            src['dogrulama']['bayraklar'].append('sitede_yok')
            src['dogrulama']['notlar'].append(
                'Sayfası %s numarasına taşındı (insan kararı); bu nesne kitapta ayrı bir kayıt.'
                % a['envanter_no'])
            log.append('~  %s site verisi -> %s (kaynak kitap nesnesi olarak kaldı)'
                       % (src['id'], a['envanter_no']))
        else:
            src['_sil'] = True
            log.append('-  %s silindi (kitapta yoktu, site verisi %s numarasına taşındı)'
                       % (src['id'], a['envanter_no']))

    # ------------------------------------------------ 2) başlık düzeltmeleri
    for oid, d in dzl.get('baslik_duzeltmeleri', {}).items():
        o = idx.get(oid)
        if not o:
            log.append('!! baslik_duzeltmeleri: nesne yok: %s' % oid); continue
        for k, v in d.items():
            if k == 'not':
                o['dogrulama']['notlar'].append('İNSAN DÜZELTMESİ: ' + v)
            elif k == 'ozgun_ad':
                o['ozgun_ad'] = v
            else:
                o[k] = v
        if d.get('baslik'):
            o['baslik_kaynagi'] = 'insan'
            o['baslik_kalite'] = 'insan'
            if 'başlık_yok' in o['dogrulama']['bayraklar']:
                o['dogrulama']['bayraklar'].remove('başlık_yok')
            o['dogrulama']['bayraklar'].append('başlık_insan_düzeltmesi')
            if o['yayin']['durum'] == 'eksik_baslik_bekliyor' and not o['dogrulama']['sitede']:
                o['yayin']['durum'] = 'eklenmeye_hazır'
        log.append('✓  %s başlık düzeltildi: %r' % (oid, (d.get('baslik') or '')[:50]))

    # ------------------------------------------------ 3) başlık düşürme
    for oid, gerekce in dzl.get('dusurulen_basliklar', {}).items():
        if oid.startswith('_'):
            continue
        o = idx.get(oid)
        if not o:
            log.append('!! dusurulen_basliklar: nesne yok: %s' % oid); continue
        if o['yayin']['durum'] == 'eklenmeye_hazır':
            o['yayin']['durum'] = 'eksik_baslik_bekliyor'
            o['baslik_kalite'] = 'yetersiz'
            o['dogrulama']['notlar'].append('BAŞLIK DÜŞÜRÜLDÜ: ' + gerekce)
            o['dogrulama']['bayraklar'].append('başlık_düşürüldü')
            log.append('↓  %s eklenmeye_hazır -> eksik_baslik_bekliyor' % oid)

    # ------------------------------------------------ 4) sil ve yaz
    once = len(nesneler)
    env['nesneler'] = [o for o in nesneler if not o.get('_sil')]
    json.dump(env, open(ENVF, 'w'), ensure_ascii=False, indent=1)

    print('=' * 70)
    print('DÜZELTMELER UYGULANDI (%s)' % os.path.basename(DUZF))
    print('=' * 70)
    for l in log:
        print('  ' + l)
    import collections
    durum = collections.Counter(o['yayin']['durum'] for o in env['nesneler'])
    print('\nnesne: %d -> %d' % (once, len(env['nesneler'])))
    for k, v in durum.most_common():
        print('   %-26s %d' % (k, v))


if __name__ == '__main__':
    main()
