# -*- coding: utf-8 -*-
"""
HETEGA — Hakem kararlarını envanter.json'a uygular.

Girdi : envanter/hakem_kararlari.json  (arayüzün "Kararları indir" çıktısı)
Çıktı : envanter/envanter.json (yerinde) + işlenmiş kararlar dosyadan düşülmez,
        her karara `hakem` izi yazılır (yeniden uygulanabilir, idempotent).

Karar türleri:
  G1 baslik          -> başlığı insan kaynağıyla yaz, durum 'eklenmeye_hazır'
  G1 nesne_degil     -> durum 'kapsam_disi', kayit_tipi (parca/bolum/kavram/cizim/grup/diger)
  G1 mukerrer        -> durum 'mukerrer', hedefe not
  G2 numara_ata      -> site sayfasını seçilen kitap numaralarına bağla (çoklu destekli)
  G2 nesne_degil     -> kapsam_disi (sayfa yayından kaldırılacaklar listesine girer)
  G2 numarasiz_kalsin-> bayrak: numarasız_onaylandı
  G3 muzede_var      -> bayrak: müzede_var_onaylı (yayında kalır)
  G3 numara_duzelt   -> numarayı değiştir/birleştir
  G3 mukerrer        -> hedef kayıtla birleştir
  G3 kaldir          -> durum 'yayından_kaldırıldı'
"""
import re, os, json, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numnorm

try:
    import yollar
    ENV = yollar.ENV
except ImportError:
    ENV = os.path.dirname(os.path.abspath(__file__))

ENVF = os.environ.get('HETEGA_ENVANTER', os.path.join(ENV, 'envanter.json'))
KARARF = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ENV, 'hakem_kararlari.json')

SITE_ALANLAR = ['yayin', 'gorseller', 'baslik', 'baslik_kaynagi', 'baslik_kalite',
                'islev', 'ozellikler', 'orijinal', 'bilgin', 'bilgin_kaynagi',
                'site_kategori', 'kitap_kaynak_site']


def tasir(src, hedef, gerekce):
    """Site verisini src kayıttan hedef kitaba taşır; src kitap nesnesiyse kalır."""
    for k in SITE_ALANLAR:
        v = src.get(k)
        if v not in (None, '', [], {}):
            hedef[k] = v
    hedef['dogrulama']['sitede'] = True
    for f in ['sitede_yok', 'kitapta_doğrulanamadı', 'envanter_no_yok']:
        if f in hedef['dogrulama']['bayraklar']:
            hedef['dogrulama']['bayraklar'].remove(f)
    hedef['dogrulama']['bayraklar'].append('hakem_numara_atadı')
    hedef['dogrulama']['notlar'].append('HAKEM KARARI: ' + gerekce)
    hedef['dogrulama']['kitapta'] = bool(hedef.get('kitap'))
    hedef['yayin']['durum'] = 'yayında'
    src['dogrulama']['sitede'] = False
    if src.get('baslik_kaynagi') == 'site':
        src['baslik'] = src.get('baslik_kitap') or ''
        src['baslik_kaynagi'] = 'kitap' if src['baslik'] else ''
        src['baslik_kalite'] = 'üstbaşlık' if src['baslik'] else 'yok'
    if src.get('kitap'):
        hazir = src['baslik_kalite'] in ('iyi', 'insan') and len(src['baslik']) >= 4
        src['yayin'] = {'durum': 'eklenmeye_hazır' if hazir else 'eksik_baslik_bekliyor',
                        'url': '', 'slug': src['yayin'].get('slug', '')}
        src['dogrulama']['bayraklar'].append('sitede_yok')
        return False
    return True   # src silinebilir


def main():
    env = json.load(open(ENVF, encoding='utf-8'))
    kararlar = json.load(open(KARARF, encoding='utf-8'))
    liste = kararlar.get('kararlar', kararlar if isinstance(kararlar, list) else [])
    N = env['nesneler']
    idx = {o['id']: o for o in N}
    silinecek = set()
    log = collections = __import__('collections').Counter()
    detay = []

    def bul(idv):
        if idv in idx: return idx[idv]
        # G2 SITE- anahtarları: url son parçasından da bul
        for o in N:
            if o['id'].endswith(idv) or (o['yayin'].get('url') or '') == idv:
                return o
        return None

    def iz(o, k):
        o.setdefault('hakem', {})
        o['hakem'] = {'karar': k.get('karar'), 'tarih': k.get('tarih', ''),
                      'not': k.get('not', ''), 'kaynak': 'hakem_arayuzu'}

    for k in liste:
        tur, kid = k.get('tur'), k.get('id')
        o = bul(kid)
        karar = k.get('karar')
        if not o or not karar or karar == 'atla':
            detay.append('= atlandı/nesne yok: %s %s' % (tur, kid)); continue
        if (o.get('hakem') or {}).get('karar') == karar and o.get('hakem', {}).get('tarih') == k.get('tarih'):
            detay.append('= zaten uygulanmış: %s' % kid); continue

        if tur == 'g1':
            if karar == 'baslik':
                o['baslik'] = k['baslik'].strip()
                o['baslik_kaynagi'] = 'insan'; o['baslik_kalite'] = 'insan'
                if k.get('islev'): o['islev'] = k['islev'].strip()
                if o['yayin']['durum'] == 'eksik_baslik_bekliyor':
                    o['yayin']['durum'] = 'eklenmeye_hazır'
                o['dogrulama']['bayraklar'].append('başlık_insan_düzeltmesi')
                log['g1_baslik'] += 1
            elif karar == 'nesne_degil':
                o['yayin']['durum'] = 'kapsam_disi'
                o['kayit_tipi'] = k.get('kayit_tipi') or 'diger'
                o['dogrulama']['bayraklar'].append('hakem_kapsam_dışı')
                log['g1_kapsam_disi'] += 1
            elif karar == 'mukerrer':
                o['yayin']['durum'] = 'mukerrer'
                o['mukerrer_hedef'] = k.get('hedef', '')
                o['dogrulama']['bayraklar'].append('hakem_mükerrer')
                log['g1_mukerrer'] += 1
            iz(o, k)
            detay.append('✓ %s %s -> %s' % (kid, karar, (k.get('baslik') or k.get('kayit_tipi') or '')))

        elif tur == 'g2':
            if karar == 'numara_ata':
                nos = k.get('no') or []
                if k.get('no_elle'):
                    for parca in re.split(r'[,;]', k['no_elle']):
                        genis, *_ = numnorm.expand(parca)
                        nos += genis
                hedefler = []
                for n in nos:
                    genis, *_ = numnorm.expand(n)
                    for g in genis:
                        if g in idx and idx[g] is not o:
                            hedefler.append(idx[g])
                if not hedefler:
                    detay.append('!! %s numara_ata: hedef bulunamadı %s' % (kid, nos)); continue
                kaynak_baslik = o['baslik'][:40]
                for i, h in enumerate(hedefler):
                    sil = tasir(o, h, 'Hakem, site sayfasını %s numarasına bağladı%s.'
                                % (h['envanter_gosterim'],
                                   ' (sayfa %d nesneyi kapsıyor)' % len(hedefler) if len(hedefler) > 1 else ''))
                    if i > 0:
                        h['dogrulama']['bayraklar'].append('set_üyesi_bölünecek')
                        h['dogrulama']['notlar'].append(
                            'Aynı site sayfası %d nesneyi kapsıyor; ayrı sayfa üretilecek.' % len(hedefler))
                    iz(h, k)
                if sil: silinecek.add(o['id'])
                log['g2_numara_ata'] += 1
                detay.append('✓ %s -> %s' % (kaynak_baslik, ','.join(h['id'] for h in hedefler)))
            elif karar == 'nesne_degil':
                o['yayin']['durum'] = 'kapsam_disi'
                o['kayit_tipi'] = k.get('kayit_tipi') or 'diger'
                o['dogrulama']['bayraklar'].append('hakem_kapsam_dışı')
                iz(o, k); log['g2_kapsam_disi'] += 1
                detay.append('✓ %s kapsam dışı (%s) — sayfa kaldırılacak' % (kid, o['kayit_tipi']))
            elif karar == 'numarasiz_kalsin':
                o['dogrulama']['bayraklar'].append('numarasız_onaylandı')
                iz(o, k); log['g2_onay'] += 1
                detay.append('✓ %s numarasız onaylandı' % kid)

        elif tur == 'g3':
            if karar == 'muzede_var':
                o['dogrulama']['bayraklar'].append('müzede_var_onaylı')
                iz(o, k); log['g3_muzede_var'] += 1
            elif karar == 'numara_duzelt':
                genis, *_ = numnorm.expand(k.get('yeni_no', ''))
                if not genis:
                    detay.append('!! %s geçersiz yeni no: %s' % (kid, k.get('yeni_no'))); continue
                yeni = genis[0]
                if yeni in idx:
                    sil = tasir(o, idx[yeni], 'Hakem numarayı %s olarak düzeltti.' % yeni)
                    iz(idx[yeni], k)
                    if sil: silinecek.add(o['id'])
                else:
                    o['eski_envanter_no'] = o['envanter_no']
                    o['envanter_no'] = yeni; o['id'] = yeni
                    m = re.match(r'\A([A-Z])(\d{2})\.(\d{2})', yeni)
                    if m: o['envanter_gosterim'] = '%s %d.%s' % (m.group(1), int(m.group(2)), m.group(3))
                    else: o['envanter_gosterim'] = yeni
                    o['dogrulama']['notlar'].append('HAKEM: numara %s -> %s' % (o['eski_envanter_no'], yeni))
                    o['dogrulama']['bayraklar'].append('numara_insan_kararıyla_atandı')
                    iz(o, k)
                    idx.pop(kid, None); idx[yeni] = o
                log['g3_numara_duzelt'] += 1
                detay.append('✓ %s numara düzeltildi -> %s' % (kid, k.get('yeni_no')))
            elif karar == 'mukerrer':
                o['yayin']['durum'] = 'mukerrer'
                o['mukerrer_hedef'] = k.get('hedef', '')
                iz(o, k); log['g3_mukerrer'] += 1
            elif karar == 'kaldir':
                o['yayin']['durum'] = 'yayından_kaldırıldı'
                o['dogrulama']['bayraklar'].append('hakem_kaldırdı')
                iz(o, k); log['g3_kaldir'] += 1
                detay.append('✓ %s yayından kaldırılacak' % kid)
            else:
                iz(o, k)

    env['nesneler'] = [o for o in N if o['id'] not in silinecek]
    env['ust_veri']['hakem_son_calisma'] = datetime.datetime.now().isoformat(timespec='minutes')
    json.dump(env, open(ENVF, 'w'), ensure_ascii=False, indent=1)

    import collections as C
    durum = C.Counter(o['yayin']['durum'] for o in env['nesneler'])
    print('=' * 66)
    print('HAKEM KARARLARI UYGULANDI — %d karar işlendi' % len(liste))
    print('=' * 66)
    for d in detay[:40]:
        print('  ' + d)
    if len(detay) > 40: print('  … (%d satır daha)' % (len(detay) - 40))
    print('\n--- işlem sayıları ---')
    for a, b in log.most_common(): print('   %-20s %d' % (a, b))
    print('\nsilinen kayıt: %d | yeni toplam: %d' % (len(silinecek), len(env['nesneler'])))
    print('--- durumlar ---')
    for a, b in durum.most_common(): print('   %-26s %d' % (a, b))


if __name__ == '__main__':
    main()
