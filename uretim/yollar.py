# -*- coding: utf-8 -*-
"""Ortak yol sabitleri — depo yerleşimi:
    uretim/          bu betikler
    ara-veri/        ara çıktılar (kitap blokları, site kazıntısı)
    envanter/        nihai veri (envanter.json = TEK DOĞRU KAYNAK)
    kaynak-metinler/ kitap OCR metinleri (telif nedeniyle depoda DEĞİL)
"""
import os

URETIM  = os.path.dirname(os.path.abspath(__file__))
KOK     = os.path.abspath(os.path.join(URETIM, '..'))
ARA     = os.path.join(KOK, 'ara-veri')
ENV     = os.path.join(KOK, 'envanter')
SERGI   = os.path.join(KOK, 'sergiler')
RAPOR   = os.path.join(KOK, 'raporlar')
# Kitap OCR metinleri depoda tutulmaz; yerel yolu ortam değişkeniyle verin:
#   export HETEGA_KITAP_OCR=/yol/ocr
OCR     = os.environ.get('HETEGA_KITAP_OCR', os.path.join(KOK, 'kaynak-metinler', 'ocr'))
WEBSITE = os.environ.get('HETEGA_WEBSITE', os.path.join(KOK, '..', 'hetega-website'))
