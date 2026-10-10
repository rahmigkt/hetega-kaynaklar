# -*- coding: utf-8 -*-
"""
HETEGA — Âlim / Yapımcı Otorite Listesi

Sitedeki `Yapımcı / Bilgin` alanı serbest metin: kişi adı, kurum, yazma adı,
mülkiyet notu ve OCR çöpü karışık (348 benzersiz ham değer, 429 nesnede).
Sergi motoru "şu âlimin eserleri" diyebilmek için kanonik kimlik şart.

Bu modül:
  1) ham değeri katlanır (aksan/özel harf duyarsız)
  2) SIRALI kurallarla en özgün eşleşmeyi bulur (belirsiz→özgün sıra önemli)
  3) tür atar: kişi | kurum | yazma_eser | mulkiyet | anonim_gelenek |
              model_atolyesi | avrupa_uretici | ocr_copu | belirsiz
  4) envanter.json'a bilgin_id / bilgin_tur yazar, alimler.json üretir

KURALLAR en özgünden en genele sıralanmalıdır: 'hazini' (Abdurrahman el-Hâzinî)
'hazin'den (Ebû Caʿfer el-Hâzin) ÖNCE gelmeli, yoksa yanlış kişiye bağlanır.
"""
import re, os, json, unicodedata, collections

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ katlama
# NFKD + Türkçe harf düzleştirme -> sadece [a-z0-9 ] kalır.
# KELİME SINIRI korunur: 'er razi' eşleşir, 'terazi' içindeki 'razi' eşleşmez.
_OZEL = {'İ':'i','ı':'i','ʿ':'','ʾ':'','’':'',"'":'','`':''}
_TR = {'ş':'s','ğ':'g','ü':'u','ö':'o','ç':'c','â':'a','î':'i','û':'u','ā':'a',
       'ī':'i','ū':'u','ḳ':'k','ḫ':'h','ḥ':'h','ṣ':'s','ṭ':'t','ẓ':'z','ẕ':'z',
       'ḍ':'d','ñ':'n','ṯ':'t','ḏ':'d','ẖ':'h','ǧ':'g','ḇ':'b','ṙ':'r','ē':'e',
       'ā':'a','ō':'o','ė':'e','ṃ':'m','ḳ':'k','ṿ':'v','ṭ':'t'}

def katla(s):
    """-> boşluklu, aksansız, küçük harfli biçim."""
    if not s: return ''
    s = ''.join(_OZEL.get(c, c) for c in s)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = ''.join(_TR.get(c, c) for c in s)
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()

def sikistir(s):
    return katla(s).replace(' ', '')

def esles(desen, bosluklu, sikisik):
    """desen (boşluklu yazılmış) metinde kelime sınırlı mı geçiyor?"""
    db = katla(desen)
    if not db: return False
    # sol sınır zorunlu; sağ taraf serbest (Türkçe ekler: "Osorius'un", "Cezeri'nin")
    if re.search(r'(?<![a-z0-9])' + re.escape(db), bosluklu):
        return True
    ds = db.replace(' ', '')
    # sıkışık alt-dizi: yalnızca yeterince uzun/özgün desenler için
    return len(ds) >= 9 and ds in sikisik

# ------------------------------------------------------------------ otorite
# (kimlik, tür, kanonik ad, dönem, alan, [eşleşme kalıpları])
# Kalıplar KATLANMIŞ metin üzerinde `in` ile aranır; liste sırası = öncelik.
OTORITE = [
 # --- İslam dünyası: tıp ---
 ('zehravi','kişi','Ebü’l-Kāsım ez-Zehrâvî','4./10. yy','Tıp · cerrahi',
  ['zehravi','zehrav','abulcasis','albucasis']),
 ('ibn-sina','kişi','Ebû ʿAlî İbn Sînâ (Avicenna)','360-428/980-1037','Tıp · felsefe',
  ['ibn sina','avicenna','ebu ali ibn sina']),
 ('razi','kişi','Ebû Bekr er-Râzî (Rhazes)','ö. 313/925','Kimya · tıp',
  ['ebubekirrazi','erhazi','errazi','razi']),

 # --- astronomi: İslam ---
 ('heysem','kişi','İbnü’l-Heysem (Alhazen)','354-432/965-1040','Optik · astronomi',
  ['ibn el heysem','elhazen','alhazen','ibn al haytham','heysem']),
 ('biruni','kişi','Ebû Reyhân el-Bîrûnî','362-440/973-1048','Astronomi · coğrafya',
  ['biruni','el biruni','birouni']),
 ('urdi','kişi','Müʾeyyededdîn el-ʿUrḍî','ö. 660/1262','Astronomi · alet yapımı',
  ['el urdi','el uri','urdi','muyyededin']),
 ('urdi-ogul','kişi','Muḥammed b. el-ʿUrḍî','7./13. yy','Astronomi',
  ['el urdi nin oglu','urdi nin oğlu']),
 ('tusî-serefeddin','kişi','Şerefeddîn el-Muẓaffer eṭ-Ṭûsî','6./12. yy','Astronomi · usturlap',
  ['serefeddin el muzaffer','serafeddin','eṭ tusi','et tusi']),
 ('sirazî','kişi','Ḳuṭbeddîn eş-Şîrâzî','634-710/1236-1311','Astronomi · optik',
  ['kutbeddin es sirazi','kutbeddin eş şirazi','sirazi']),
 ('kasi','kişi','Ġıyâseddîn Cemşîd el-Kâşî','ö. 832/1429','Astronomi · matematik',
  ['giyaseddin','el kasi','alkashi','kasi']),
 ('uluk-bey','kişi','Uluğ Bey','794-853/1394-1449','Astronomi · rasathane',
  ['uluğ bey','ulug bey']),
 ('takiyyeddin','kişi','Taḳıyyeddîn el-Mıṣrî (Râṣıd)','932-993/1526-1585','Astronomi · saat',
  ['takiyyeddin','taqiyyuddin','takıyyeddin','rasıd']),
 ('hucendi','kişi','Ebû Maḥmûd Ḥâmid b. el-Hıḍr el-Ḫucendî','4./10. yy','Astronomi',
  ['el hucendi','hucendi']),
 ('hazini','kişi','ʿAbdurrahmân el-Ḫâzinî','6./12. yy','Fizik · terazi',
  ['el hazini','hazini','abdurrahman el hazini']),
 ('hazin-ebucafer','kişi','Ebû Caʿfer el-Ḫâzin','ö. ~360/971','Astronomi · matematik',
  ['ebu cafer el hazin','hazin']),
 ('suff','kişi','ʿAbdurrahmân es-Sûfî (Azophi)','291-376/903-986','Astronomi · yıldız kataloğu',
  ['es suff','suffi','azophi','abdurrahman b ömer']),
 ('siczi','kişi','Ebû Saʿîd Ahmed b. Muḥammed es-Siczî','4./10. yy','Astronomi · matematik',
  ['es siczi','siczi']),
 ('zerkal','kişi','İbrâhîm b. Yahyâ ez-Zerḳālî (Arzachel)','421-480/1029-1087','Astronomi · usturlap',
  ['ez zerkali','zerkal','arzachel']),
 ('ibn-es-satir','kişi','ʿAlî b. İbrâhîm İbn eş-Şâṭır','704-776/1304-1375','Astronomi · mîkât',
  ['ibn eş şatir','ibn es satir','eş şatir']),
 ('ibn-yunis','kişi','ʿAlî b. ʿAbdurrahmân İbn Yûnis','ö. 399/1009','Astronomi',
  ['ibn yunis','ibn yunus']),
 ('marrakusi','kişi','Ebû ʿAlî el-Ḥasan b. ʿAlî el-Marrâkuşî','7./13. yy','Astronomi · mîkât',
  ['el marrakuşi','marrakuşi']),
 ('mardinî','kişi','Cemâleddîn ʿAbdullâh b. Halîl el-Mâridînî','825-906/1423-1500','Astronomi · mîkât',
  ['el maridini','mardini']),
 ('kindî','kişi','Yaʿḳūb b. İsḥāḳ el-Kindî','ö. ~252/866','Felsefe · optik · kimya',
  ['el kindi','yakub b ishak']),
 ('idrisî','kişi','Muḥammed b. Muḥammed eş-Şerîf el-İdrīsî','493-560/1100-1166','Coğrafya',
  ['el idrisi','idrisi','eş şerif']),
 ('neccar','kişi','ʿAbdurrahmân b. Sinân en-Neccâr','?','Alet yapımı',
  ['en neccar','abdurrahman b sinan']),
 ('samuel-magribi','kişi','es-Semuʾel b. Yahyâ el-Maġribî','6./12. yy','Matematik · astronomi',
  ['es samuel','samuel','el magribi']),
 ('ibn-luyun','kişi','Ebû ʿOsmân Saʿîd b. Aḥmed İbn Luyûn','ö. 749/1349','Astronomi · mîkât',
  ['ibn luyun','ibn luy','luyun','ebu osman said']),
 ('isfizari','kişi','Ebû Ḥātim el-Muẓaffer el-İsfizārī','6./12. yy','Mekanik',
  ['el isfizari','isfizari','ebu hatim el muzaffer']),
 ('muradi','kişi','Muḥammed (veya Aḥmed) b. Ḫalef el-Murādî','5./11. yy','Mekanik',
  ['el muradi','muradi','b halef']),
 ('hazimi','kişi','Muḥammed b. Aḥmed el-Hâzimî','?','Astronomi',
  ['el hazimi','hazimi']),
 ('mizzi','kişi','Muḥammed b. Ahmed el-Mizzî','7-8./13-14. yy','Astronomi · mîkât',
  ['el mizzi','muhallibi','zeyneddin']),
 ('isfehani','kişi','Muḥammed b. Ebî Bekr el-İṣfehānī','7./13. yy','Astronomi · usturlap',
  ['el isfehani','isfehani','muhammed b ebi bekr']),
 ('asturlabi-yusuf','kişi','Yūsuf el-Uṣṭurlābî','?','Usturlap yapımı',
  ['yusuf el usturlabi','el usturlabi']),
 ('asturlabi-sehl','kişi','es-Sehl el-Uṣṭurlābî en-Nīsābūrī','?','Usturlap yapımı',
  ['es sehl el usturlabi','nisaburi']),
 ('nastulus','kişi','Nasṭūlus','3-4./9-10. yy','Usturlap yapımı',
  ['nastulus','nastulus']),
 ('vasiti','kişi','Ebû er-Rebîʿ Aḥmed b. ʿAlî el-Vâsiṭî','?','Alet yapımı',
  ['ebu er rabi','el vasiti','vasiti']),
 ('ibn-es-serrac','kişi','Aḥmed b. es-Serrâc','8./14. yy','Astronomi · alet',
  ['es serrac','ahmed b es serrac']),
 ('nakkas','kişi','Aḥmed b. Muḥammed en-Naḳḳāş','?','Alet yapımı',
  ['en nakkas','nakkaş']),
 ('raqqam','kişi','Ebû ʿAbdullāh Muḥammed b. İbrâhîm er-Raḳḳām','?','Astronomi',
  ['er rakkam','rakkam','ibn ibrahim']),
 ('umeyye','kişi','Ebû ʿAṣalt Ümeyye b. ʿAbdulʿazīz','?','Astronomi',
  ['ebu asalt','umeyye b abdulaziz']),
 ('hamairi','kişi','Muḥammed b. Futūḥ el-Ḫamāʾirī','6./12. yy','Usturlap yapımı',
  ['el hamairi','hamairi','futuh']),
 ('huzeyl','kişi','Muḥammed b. Muḥammed b. Huzeyl','?','Astronomi',
  ['huzeyl','b muhammed huzeyl']),
 ('saffar','kişi','Şemseddîn Muḥammed eṣ-Ṣaffār','ö. 826/1423','Astronomi · usturlap',
  ['şemseddin muhammed saffar','es saffar','saffar']),
 ('savi','kişi','Zeyneddîn ʿÖmer b. Sehlân es-Sâvî','?','Tıp · felsefe',
  ['zeyneddin ömer','es sevi','sehlân']),
 ('dimaski','kişi','Şemseddîn ed-Dımaşḳī','7-8./13-14. yy','Coğrafya · kozmografya',
  ['ed dımaşki','dimaski','nuhbet ed dehr']),
 ('kuhi','kişi','Ebû Sehl el-Kūhī','ö. ~390/1000','Matematik · geometri',
  ['ebu sehl el kuhi','el kuhi']),
 ('cebair','kişi','Câbir b. Aflaḥ','6./12. yy','Astronomi',
  ['câbir b eflah','cabir b aflah','aflah']),
 ('rammah','kişi','Necmeddîn Ḥasan er-Rammāḥ','ö. 693/1294','Savaş tekniği',
  ['er remmah','rammah','necmeddin hasan']),
 ('tarsusi','kişi','Murḍā eṭ-Ṭarsūsī','6./12. yy','Savaş tekniği',
  ['et tarsusi','tarsusi','murda']),
 ('zerdkas','kişi','İbn Erenbuġā ez-Zerdkāş','8./14. yy','Savaş tekniği · okçuluk',
  ['ez zerdkas','zerdkas','ibn erenbuga']),
 ('ibn-macid','kişi','İbn Mācid','826-906/1432-1500','Denizcilik',
  ['ibn macid','ibn majid','macid']),
 ('mehri','kişi','Süleymân el-Mehrî','9-10./16. yy','Denizcilik',
  ['süleymân el mehri','el mehri']),
 ('piri-reis','kişi','Pîrî Reʾīs','~1470-1554','Denizcilik · haritacılık',
  ['piri reis','piri re is']),
 ('sidi-ali-reis','kişi','Sîdî ʿAlî Reʾīs','1498-1563','Denizcilik · astronomi',
  ['sidi ali reis','sidî ali reis']),
 ('mumin','kişi','Halife el-Meʾmûn','170-218/786-833','Himaye · rasathane',
  ['halife el me mun','me mun','memun']),
 ('el-melik-el-esref','kişi','el-Melik el-Eşref ʿÖmer b. Yūsuf (Resûlî)','ö. 694/1295','Himaye · rasathane',
  ['el melik el eşref','yemen resuli','yemen sultanı']),
 ('nureddin-zengi','kişi','Nūreddīn Maḥmūd b. Zengī','511-569/1118-1174','Himaye · hastane',
  ['nureddin mahmud','emir nureddin','zengi']),
 ('lagari','kişi','Lāgarī Ḥasan Çelebî','11./17. yy','Havacılık',
  ['lagari hasan','lagar hasan çelebi']),
 ('ibn-hatib','kişi','Lisâneddîn İbn el-Ḫaṭīb','713-776/1313-1374','Tıp · tarih',
  ['lisaneddin ibn el hatib','ibn el hatib']),
 ('cezairi','kişi','İbn er-Rezzâz el-Cezerî','ö. 602/1206 sonrası','Mekanik · otomat',
  ['el cezeri','cezeri','ibn er rezzaz']),
 ('benumusa','kişi','Benū Mūsā kardeşler','3./9. yy','Mekanik · geometri',
  ['benū musa','benumusab','benumusa','banu musa']),
 ('harezmi','kişi','Muḥammed b. Mūsâ el-Ḫârizmî','ö. ~232/847 sonrası','Matematik · astronomi',
  ['el harezmi','harezmi','harizmi']),
 ('kindi-mimar','kişi','Mimar Sinan','895-996/1490-1588','Mimari',
  ['mimar sinan']),
 ('ptoleme','kişi','Batlamyus (Ptoleme)','~100-170','Astronomi (miras)',
  ['ptoleme','batlamyus','ptolemy']),
 ('arsimed','kişi','Arşimet','MÖ 287-212','Mekanik (miras)',
  ['arşimet','arsimet','archimedes']),
 ('jaisingh','kişi','Savai Jai Singh II','1688-1743','Astronomi · rasathane',
  ['jai singh savai','jai singh','jaisingh']),

 ('halife-halebi','kişi','Ḫalīfe b. Ebî el-Mehâsin el-Halebî','7./13. yy','Tıp · cerrahi',
  ['halife b ebi el mehasin','el kafi','khalifa','halife']),
 # --- Avrupa: yapımcı / bilgin ---
 ('tycho','kişi','Tycho Brahe','1546-1601','Astronomi · rasathane',
  ['tycho brahe','tycho']),
 ('vinci','kişi','Leonardo da Vinci','1452-1519','Mekanik · mühendislik',
  ['leonardo da vinci','vinci']),
 ('munster','kişi','Sebastian Münster','1488-1552','Astronomi · alet',
  ['sebastian munster','munster']),
 ('schoner','kişi','Johannes Schöner','1477-1547','Astronomi · alet',
  ['johannes schoner','schoner']),
 ('apian','kişi','Peter Apian','1495-1552','Astronomi · kartografya',
  ['peter apian','apian']),
 ('peregrinus','kişi','Petrus Peregrinus de Maricourt','13. yy','Manyetizma',
  ['petrus peregrinus','peregrinus']),
 ('nunes','kişi','Pedro Nunes','1502-1578','Denizcilik · matematik',
  ['pedro nunes','nunes']),
 ('davis','kişi','John Davis','~1550-1605','Denizcilik · alet',
  ['john davis']),
 ('ribeiro','kişi','Diogo Ribeiro','ö. 1533','Kartografya',
  ['diogo ribeiro','ribeiro']),
 ('osorius','kişi','Hieronimus Osorius','1506-1580','Denizcilik · tarih',
  ['osorius']),
 ('chaucer','kişi','Geoffrey Chaucer','~1343-1400','Astronomi · usturlap',
  ['chaucer']),
 ('coronelli','kişi','Vincenzo Coronelli','1650-1718','Kartografya · gök küre',
  ['coronelli']),
 ('habermel','kişi','Erasmus Habermel','ö. 1606','Alet yapımı (Prag)',
  ['habermel']),
 ('arsenius','kişi','Gualterus Arsenius','16. yy','Usturlap yapımı (Leuven)',
  ['arsenius']),
 ('campano','kişi','Giovanni Campano da Novara','13. yy','Astronomi',
  ['campanus de novara','campano']),
 ('lupitus','kişi','Lupitus of Barcelona','11. yy','Astronomi',
  ['lupitus','barselonalı lupitus']),
 ('villard','kişi','Villard de Honnecourt','13. yy','Mimari · çizim',
  ['villard de honnecourt','honnecourt']),
 ('barozzi','kişi','Francesco Barozzi','1537-1604','Geometri',
  ['barozzi']),
 ('deck','avrupa_uretici','Théodore Deck','1823-1891','Seramik (Paris)',
  ['theodore deck','théodore deck','deck']),
 ('lobmeyr','avrupa_uretici','J. & L. Lobmeyr','19. yy','Cam (Viyana)',
  ['lobmeyr']),
 ('brunold','model_atolyesi','Martin Brunold (Abtwil, İsviçre)','20-21. yy','Model atölyesi',
  ['martin brunold','m brunold','brunold']),
 ('farre','model_atolyesi','Eduard Farré-Olivé (Barselona)','20-21. yy','Model atölyesi',
  ['eduard farre','farre olive','farre']),
 ('oestmann','model_atolyesi','G. Oestmann & F. Lühring (Bremen)','20-21. yy','Model atölyesi',
  ['oestmann','luhring']),
 ('freudemann','model_atolyesi','W. Freudemann','20-21. yy','Model atölyesi',
  ['freudemann']),
 ('zamorano','model_atolyesi','Zamorano (Compendio rekonstrüksiyonu)','20-21. yy','Model atölyesi',
  ['zamorano']),
 ('stanley','avrupa_uretici','Stanley (London)','19-20. yy','Alet üreticisi',
  ['stanley']),
 ('cooke','avrupa_uretici','T. Cooke & Sons (London)','19-20. yy','Alet üreticisi',
  ['t cooke','cooke']),
 ('brocard','avrupa_uretici','Brocard','?','Alet üreticisi',
  ['brocard']),
 ('seemann','model_atolyesi','H. Seemann','20. yy','Model atölyesi',
  ['seemann']),

 ('sehlî','kişi','İbrâhîm b. Saʿîd es-Sehlî','5./11. yy','Usturlap yapımı',
  ['ibrahim b said es sehli','es sehli','sehli']),
 ('saffar-2','kişi','Muḥammed b. eṣ-Ṣaffār','5./11. yy','Usturlap yapımı',
  ['muhammed b es affar','es affar','affar','saffar']),
 ('abdulkerim-misri','kişi','ʿAbdulkerîm el-Mısrî','7./13. yy','Alet yapımı',
  ['abdulkerim el misri','el misri']),
 ('yezdi','kişi','Muḥammed Muḳīm el-Yezdî','11./17. yy','Usturlap yapımı',
  ['muhammed mukim el yezdi','el yezdi','yezdi']),
 ('ali-b-sihab','kişi','ʿAlî b. eş-Şihâb','8./14. yy','Alet yapımı',
  ['ali b es sihab','es sihab']),
 ('guzuli','kişi','Muḥammed b. el-Ġuzūlî (hakkâk)','8./14. yy','Hakkâklık',
  ['muhammed b el guzuli','el guzuli','guzuli']),
 ('mutaim','kişi','ʿAlî b. İbrâhîm el-Muṭaʿʿim','8./14. yy','Usturlap yapımı',
  ['ali b ibrahim el mutaim','el mutaim','mutaim']),
 ('ibn-es-semh','kişi','Ebü’l-Ḳāsım Eṣba b. Muḥammed b. es-Semḥ','ö. 426/1035','Astronomi · usturlap',
  ['ebu el kasim esba','b es semh','el arnati','arnati','esba']),
 ('ridvan-saati','kişi','Rıdvân es-Sâʿātî','ö. 618/1231 sonrası','Saat · mekanik',
  ['ridvan es saati','ridvan es sâʿâtî','es saati']),
 ('fournier','kişi','Georges Fournier','1595-1652','Denizcilik · hidrografi',
  ['fournier']),
 ('rabica-isak','kişi','Rabí Çag / Isak İbn Sid (Toledo)','13. yy','Astronomi · çeviri',
  ['rabicag','isak ibn sid','ibn sid']),
 ('magribi-gelenek','anonim_gelenek','Mağrib kökenli (anonim)','?','Üretim çevresi',
  ['magrib kökenli','mağrib kökenli','magrib']),
 ('anadolu-gelenek','anonim_gelenek','Anadolu kökenli (anonim)','?','Üretim çevresi',
  ['anadolu kökenli','anadolu']),
 ('cin-gelenek','anonim_gelenek','Çin (anonim)','?','Üretim çevresi',
  ['çin']),

 # --- kurumlar ---
 ('jaipur-rasathane','kurum','Jaipur Rasathanesi (Jantar Mantar)','1727-1734','Rasathane',
  ['jaipur','jantar mantar']),
 ('delhi-rasathane','kurum','Delhi Rasathanesi (Jantar Mantar)','18. yy','Rasathane',
  ['delhi jantar mantar','delhi rasathanesi']),
 ('istanbul-rasathane','kurum','İstanbul Rasathanesi (Tophane)','1575-1580','Rasathane',
  ['istanbul rasathanesi']),
 ('maraga-rasathane','kurum','Merâğa Rasathanesi','1259-','Rasathane',
  ['meraga','merâğa']),
 ('igaiw','kurum','Frankfurt İGAIW (Fuat Sezgin Enstitüsü)','1982-','Enstitü · koleksiyon',
  ['igaiw','institut fur geschichte','enstitü','frankfurt']),
 ('kahire-muzesi','kurum','Kahire İslâm Sanatları Müzesi','1881-','Müze · orijinal',
  ['kahire islâm sanatları','kahire islam','kahire']),
 ('oxford-mhs','kurum','Museum of the History of Science, Oxford','1924-','Müze · orijinal',
  ['museum of the history of science','evans collection','oxford']),
 ('barselona-maritim','kurum','Museu Marítim, Barselona','1936-','Müze · orijinal',
  ['museu maritim','muse maritim']),
 ('ripoll','kurum','Santa Maria de Ripoll Benedikt Manastırı','9. yy','Manastır · yazma',
  ['ripoll','benedikt']),
 ('osmanli','kurum','Osmanlı (genel)','14.-20. yy','Üretim çevresi',
  ['osmanlı','osmanli']),
 ('selcuklu','kurum','Selçuklu (genel)','11.-13. yy','Üretim çevresi',
  ['selçuklu','selcuklu']),
 ('enstitu-atolye','kurum','Enstitü atölyesi (İGAIW rekonstrüksiyonu)','20-21. yy','Model atölyesi',
  ['enstitü mülkiyeti','ensitutul','atölye','atolye']),

 # --- mülkiyet / koleksiyon ---
 ('baytop-koleksiyon','mulkiyet','Turhan Baytop koleksiyonu','?','Koleksiyon',
  ['turhan baytop','baytop']),
 ('pompadour','mulkiyet','Madame de Pompadour (eski mülkiyet)','1721-1764','Koleksiyon',
  ['pompadour']),
 ('rautenstrauch','mulkiyet','Rautenstrauch-Joest-Museum, Köln','1906-','Müze · orijinal',
  ['rautenstrauch','koln']),

 # --- anonim / gelenek ---
 ('anonim-mecmua','anonim_gelenek','Anonim Arapça teknik mecmua','?','Anonim',
  ['anonim arapça','anonim arapca','fragman halinde yazma']),
 ('akdeniz-geleneği','anonim_gelenek','Akdeniz / Arap-İslam denizcilik geleneği','?','Gelenek',
  ['akdeniz','hintokyanusu','arapislamkulturevresi','yunanlarvediger',
   'gelenekselalet','antikteknikler','devamedenantik']),
 ('avrupalı-harita','anonim_gelenek','Avrupalı haritacılar geleneği','15-18. yy','Gelenek',
  ['avrupa tipi','arap örneğin latince','fournier','joao de barros','cihannüma']),

 # --- yazma / eser referansları (kişi değil) ---
 ('yazma-libros','yazma_eser','Libros del saber de astronomía (X. Alfons)','1276-1277','Yazma kaynak',
  ['libros del saber','kastilya kralı','alfons']),
 ('yazma-liber-florum','yazma_eser','Liber florum Geberti','10-11. yy','Yazma kaynak',
  ['liber florum geberti','gebert']),
 ('yazma-gotha','yazma_eser','Gotha yazması','?','Yazma kaynak',
  ['gotha']),
 ('yazma-riccardiana','yazma_eser','Riccardiana yazması (er-Râzî, Latince)','?','Yazma kaynak',
  ['riccardiana']),
 ('yazma-enik','yazma_eser','el-Enîḳ fî’l-Manâcnîḳ','8./14. yy','Yazma kaynak',
  ['el enik fi el manacnik','enik fi','manacnik']),
 ('yazma-tabira','yazma_eser','eṭ-Ṭarsūsī, Tabṣirat Erbāb el-Elbâb','8./14. yy','Yazma kaynak',
  ['tabsirat','tabsirat erbâb']),
 ('yazma-turuk','yazma_eser','Taḳıyyeddîn, eṭ-Ṭuruḳ es-Seniyye','10./16. yy','Yazma kaynak',
  ['et turuk es seniyye','turuk es seniyye']),
 ('yazma-istiab','yazma_eser','el-Bîrûnî, İstîʿâb el-Vucūh','5./11. yy','Yazma kaynak',
  ['istiab','istîâb','vucuh']),
 ('yazma-tasrif','yazma_eser','ez-Zehrâvî, Kitāb et-Taṣrīf','4-5./10-11. yy','Yazma kaynak',
  ['et tasrif','kitab et tasrif','tasrif']),
 ('yazma-kuhl','yazma_eser','Kitāb el-Kuḥl','?','Yazma kaynak',
  ['kuhl']),
 ('yazma-quatremere','yazma_eser','Quatremère yazması / neşri','19. yy','Yazma kaynak',
  ['quatremere']),

 # --- mineral / nesne adı (yanlış alana sızmış) ---
 ('mineral','belirsiz','(mineral adı — bilgin değil)','?','Kimya/Mineral',
  ['galenit','vitriyoller','tinkal','bicâdî','ametist','kuvars','mermer','alçı taşı','kükürt']),
]

# OCR çöpü: kısa, anlamsız, cümle parçası
COP_DESEN = re.compile(
    r'\A(izgisi|se|lar|im|in|klar|kubbe|lat|o|sayfa|avlu|disk|alt|hayvanlar|tekne|'
    r'camkab|r|nandan eser|problemler|rif|ney|lde|un|birincisi|bumineral|'
    r'vid|yayla|ceneninde|zerindebulunankab|yorlar|cocuklar|cokgen|uyarlama|'
    r'ekininde|birkitap|devam|diger|den|de|ve|ile|i|a|e|o|u|n|y|z|s|t|k|m|l|b|c|d|g|h|j|p|r|v)\Z')

def siniflandir(ham):
    """ham 'Yapımcı / Bilgin' değeri -> (kimlik, tür, kanonik ad, eşleşen desen)"""
    if not ham or ham.strip() in ('-', '—', '–'):
        return (None, 'bos', '', None)
    bosluklu = katla(ham); sikisik = sikistir(ham)
    if not sikisik:
        return (None, 'bos', '', None)
    if COP_DESEN.match(sikisik) or len(sikisik) < 3:
        return (None, 'ocr_copu', '', None)
    for kimlik, tur, ad, donem, alan, desenler in OTORITE:
        for d in desenler:
            if esles(d, bosluklu, sikisik):
                return (kimlik, tur, ad, d)
    # mülkiyet/orijinal kalıpları
    if re.search(r'orijinal|museum|muse|müze|koleksiyon|collection|mülkiyet|yazma', ham, re.I):
        return (None, 'mulkiyet', '', None)
    if len(ham) < 14 and not re.search(r'\d', ham):
        return (None, 'belirsiz', '', None)
    return (None, 'belirsiz', '', None)


def oz_denetim():
    """Her otorite girdisinin kanonik adı, kendi desenlerinden biriyle
    eşleşmeli. Yazım hatalarını (ör. 'arsimed' vs 'arşimet') yakalar."""
    hatalar = []
    for kimlik, tur, ad, donem, alan, desenler in OTORITE:
        bl, sk = katla(ad), sikistir(ad)
        if not any(esles(d, bl, sk) for d in desenler):
            hatalar.append((kimlik, ad, desenler))
    return hatalar


if __name__ == '__main__':
    hata = oz_denetim()
    print('öz-denetim: %d/%d girdi kendi adıyla eşleşmiyor' % (len(hata), len(OTORITE)))
    for k, a, d in hata:
        print('   ! %-22s %-40s desenler=%s' % (k, a[:40], [x for x in d][:4]))
    print()
    env = json.load(open(os.path.join(HERE, 'envanter.json'), encoding='utf-8'))
    N = env['nesneler']

    otorite = {}
    for kimlik, tur, ad, donem, alan, desenler in OTORITE:
        otorite[kimlik] = {'id': kimlik, 'tur': tur, 'ad': ad, 'donem': donem,
                           'alan': alan, 'varyantlar': desenler, 'nesneler': []}

    tur_say = collections.Counter()
    eslesmeyen = collections.Counter()
    for o in N:
        ham = o.get('bilgin') or ''
        kimlik, tur, ad, desen = siniflandir(ham)
        o['bilgin_tur'] = tur
        o['bilgin_id'] = kimlik
        o['bilgin_kanonik'] = ad if kimlik else ''
        o['bilgin_ham'] = ham
        tur_say[tur] += 1
        if kimlik:
            otorite[kimlik]['nesneler'].append(o['id'])
        elif tur == 'belirsiz' and ham:
            eslesmeyen[ham[:70]] += 1

    # eser referansını da bağla
    for o in N:
        o['eser_kalite'] = o.get('eser_kalite', '')

    env['alimler'] = [v for v in otorite.values() if v['tur'] == 'kişi']
    env['kurumlar'] = [v for v in otorite.values() if v['tur'] in
                       ('kurum', 'avrupa_uretici', 'model_atolyesi')]
    env['yazma_kaynaklar'] = [v for v in otorite.values() if v['tur'] == 'yazma_eser']
    for grp in ('alimler', 'kurumlar', 'yazma_kaynaklar'):
        env[grp].sort(key=lambda x: -len(x['nesneler']))

    json.dump(env, open(os.path.join(HERE, 'envanter.json'), 'w'),
              ensure_ascii=False, indent=1)
    json.dump({'alimler': env['alimler'], 'kurumlar': env['kurumlar'],
               'yazma_kaynaklar': env['yazma_kaynaklar'],
               'eslesmeyenler': [{'ham': k, 'adet': v}
                                 for k, v in eslesmeyen.most_common()]},
              open(os.path.join(HERE, 'alimler.json'), 'w'),
              ensure_ascii=False, indent=1)

    print('=' * 70)
    print('ÂLİM OTORİTE LİSTESİ')
    print('=' * 70)
    print('nesne sayısı           : %d' % len(N))
    print('bilgin alanı dolu      : %d' % sum(1 for o in N if o.get('bilgin_ham')))
    print('\n--- sınıflandırma ---')
    for k, v in tur_say.most_common():
        print('   %-20s %d' % (k, v))
    print('\n--- en çok nesneye bağlı âlimler ---')
    for a in env['alimler'][:22]:
        print('   %3d  %-42s %s' % (len(a['nesneler']), a['ad'][:42], a['donem']))
    print('\n--- en çok nesneye bağlı kurum/atölye ---')
    for a in env['kurumlar'][:12]:
        print('   %3d  %-42s %s' % (len(a['nesneler']), a['ad'][:42], a['tur']))
    print('\n--- eşleşmeyen (inceleme) %d benzersiz değer, ilk 20 ---' % len(eslesmeyen))
    for k, v in eslesmeyen.most_common(20):
        print('   %3d  %s' % (v, k))
