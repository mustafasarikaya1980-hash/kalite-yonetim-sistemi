# -*- coding: utf-8 -*-
import base64
import os
import re
import streamlit as st
import pandas as pd
import requests
import altair as alt
import hashlib
import hmac
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="MSP KALİTE YÖNETİM SİSTEMİ", layout="wide", page_icon="🏭")

st.components.v1.html(
    """
    <script>
        try {
            const doc = window.parent.document.documentElement;
            doc.setAttribute('lang', 'tr');
            doc.setAttribute('class', 'notranslate');
            doc.setAttribute('translate', 'no');
        } catch (e) {}

        // Sekme (menü) başlıklarını doğrudan boya: CSS seçicileri Streamlit sürümüne göre tutmayabiliyor
        function sekmeleriBoya() {
            try {
                const d = window.parent.document;
                d.querySelectorAll('[role="tab"]').forEach(function (b) {
                    const sec = b.getAttribute('aria-selected') === 'true';
                    const yaz = sec ? '#FFFFFF' : '#1E3A8A';
                    const st = function (el, k, v) { el.style.setProperty(k, v, 'important'); };
                    st(b, 'background', sec ? 'linear-gradient(135deg, #2563EB 0%, #1E3A8A 100%)' : '#E0E7FF');
                    st(b, 'border', '2px solid ' + (sec ? '#1E3A8A' : '#C7D2FE'));
                    st(b, 'border-bottom', 'none');
                    st(b, 'border-radius', '12px 12px 0 0');
                    st(b, 'padding', '0.8rem 1.5rem');
                    st(b, 'height', 'auto');
                    st(b, 'margin-right', '0.4rem');
                    if (sec) st(b, 'box-shadow', '0 -3px 10px rgba(37,99,235,0.35)'); else b.style.removeProperty('box-shadow');
                    [b].concat(Array.from(b.querySelectorAll('*'))).forEach(function (el) {
                        st(el, 'font-size', '1.5rem');
                        st(el, 'font-weight', '900');
                        st(el, 'color', yaz);
                        st(el, 'line-height', '1.3');
                    });
                });
                d.querySelectorAll('[data-baseweb="tab-highlight"]').forEach(function (h) {
                    h.style.setProperty('background-color', '#F59E0B', 'important');
                    h.style.setProperty('height', '5px', 'important');
                });
                d.querySelectorAll('[data-baseweb="tab-border"]').forEach(function (h) {
                    h.style.setProperty('background-color', '#1E3A8A', 'important');
                    h.style.setProperty('height', '3px', 'important');
                });
            } catch (e) {}
        }
        sekmeleriBoya();
        setInterval(sekmeleriBoya, 300);
    </script>
    """,
    height=0,
)
st.markdown('<meta name="google" content="notranslate" />', unsafe_allow_html=True)

st.markdown(
    """
    <style>
    /* Sekme çubuğu (sabit) */
    div[data-testid="stTabs"],
    div[data-testid="stTabs"] > div:first-child,
    div[data-baseweb="tab-list"] {
        position: sticky !important;
        top: 0 !important;
        z-index: 999;
        background-color: #F8FAFC;
        padding-top: 0.4rem;
        padding-bottom: 0.3rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    }
    /* Sekme başlıkları büyük */
    /* TÜM SEKME MENÜLERİ (ana ve alt): büyük, kalın, renkli */
    div[role="tablist"], div[data-baseweb="tab-list"] { gap: 0.5rem !important; }
    button[role="tab"],
    button[data-baseweb="tab"],
    button[data-testid="stTab"] {
        padding: 0.9rem 1.6rem !important;
        border-radius: 12px 12px 0 0 !important;
        background: #E0E7FF !important;
        border: 2px solid #C7D2FE !important;
        border-bottom: none !important;
        height: auto !important;
        transition: all 0.15s ease;
    }
    button[role="tab"] p,
    button[data-baseweb="tab"] p,
    button[data-testid="stTab"] p,
    button[role="tab"] span,
    button[data-baseweb="tab"] span,
    button[data-testid="stTab"] span,
    button[role="tab"] div,
    button[data-baseweb="tab"] div,
    button[data-testid="stTab"] div {
        font-size: 1.55rem !important;
        font-weight: 900 !important;
        letter-spacing: 0.3px;
        color: #1E3A8A !important;
        line-height: 1.3 !important;
    }
    button[role="tab"]:hover,
    button[data-baseweb="tab"]:hover,
    button[data-testid="stTab"]:hover { background: #C7D2FE !important; transform: translateY(-2px); }
    button[role="tab"][aria-selected="true"],
    button[data-baseweb="tab"][aria-selected="true"],
    button[data-testid="stTab"][aria-selected="true"] {
        background: linear-gradient(135deg, #2563EB 0%, #1E3A8A 100%) !important;
        border-color: #1E3A8A !important;
        box-shadow: 0 -3px 10px rgba(37,99,235,0.35);
    }
    button[role="tab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] p,
    button[data-testid="stTab"][aria-selected="true"] p,
    button[role="tab"][aria-selected="true"] span,
    button[data-baseweb="tab"][aria-selected="true"] span,
    button[data-testid="stTab"][aria-selected="true"] span,
    button[role="tab"][aria-selected="true"] div,
    button[data-baseweb="tab"][aria-selected="true"] div,
    button[data-testid="stTab"][aria-selected="true"] div { color: #FFFFFF !important; }
    div[data-baseweb="tab-highlight"] { background-color: #F59E0B !important; height: 5px !important; }
    div[data-baseweb="tab-border"] { background-color: #1E3A8A !important; height: 3px !important; }

    /* BÖLÜM BAŞLIKLARI */
    h2, h3, div[data-testid="stHeading"] h2, div[data-testid="stHeading"] h3 {
        color: #1E3A8A !important;
        font-weight: 900 !important;
        border-left: 8px solid #F59E0B;
        padding-left: 0.8rem;
    }
    h2, div[data-testid="stHeading"] h2 { font-size: 2.3rem !important; }
    h3, div[data-testid="stHeading"] h3 { font-size: 1.9rem !important; }
    h4 { font-size: 1.5rem !important; font-weight: 800 !important; color: #1D4ED8 !important; }

    /* Sayfa başlıkları */
    h1 { font-size: 2.4rem !important; font-weight: 800 !important; }
    h2, div[data-testid="stHeading"] h2 { font-size: 2.2rem !important; font-weight: 800 !important; color: #0F172A; }
    h3, div[data-testid="stHeading"] h3 { font-size: 1.7rem !important; font-weight: 700 !important; color: #1E293B; }
    h4 { font-size: 1.35rem !important; font-weight: 700 !important; color: #1E293B; }

    /* Alan etiketleri ve girişler */
    div[data-testid="stWidgetLabel"] p, label p { font-size: 1.15rem !important; font-weight: 600 !important; color: #1E293B; }
    input, textarea, div[data-baseweb="select"] div { font-size: 1.1rem !important; }
    div[data-testid="stCaptionContainer"], div[data-testid="stCaptionContainer"] p { font-size: 1.05rem !important; color: #475569; }
    div[data-testid="stMetricLabel"] p { font-size: 1.1rem !important; font-weight: 600 !important; }
    div[data-testid="stMetricValue"] { font-size: 2.2rem !important; }
    div[data-testid="stAlert"] p { font-size: 1.1rem !important; }

    div[data-testid="stVerticalBlockBorderWrapper"] { margin-bottom: 0.25rem; }
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, textarea { border-radius: 10px !important; }
    div[data-testid="stButton"] button { border-radius: 10px; font-weight: 700; padding: 0.7rem 1.1rem; }
    div[data-testid="stButton"] button p { font-size: 1.1rem !important; }
    div.block-container { padding-top: 1.2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# 1. Form (Saha Veri Girişi)
FORM_RESPONSE_URL = "https://docs.google.com/forms/d/e/1FAIpQLSc2GWwoN4UOcWHSZxNQNNT-rNBJrI1I4E1xN8CHMA-cO1BxqA/formResponse"
ENTRY_PERSONEL = "entry.1505600207"
ENTRY_PARCA = "entry.1034697779"
ENTRY_RET_NEDENI = "entry.1351128780"
ENTRY_OP_ADI = "entry.108790685"
ENTRY_CNC_NO = "entry.657669024"
ENTRY_ACIKLAMA = "entry.686625208"
ENTRY_RET_MIKTARI = "entry.410490317"
ENTRY_URETIM_MIKTARI = "entry.958612329"
ENTRY_BELGE_LINKLERI = "entry.795755675"

# 2. Form (Ekstra Listeler)
FORM2_RESPONSE_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd3tGU9I4FX9OfoHT_EMRb_NHZsbcpMk-ZZmu0sQflfC_tt_A/formResponse"
ENTRY2_TIP = "entry.1056493377"
ENTRY2_DEGER = "entry.1752462997"

SABIT_EPOSTA = "veri@msp-kalite.local"

# ANA E-TABLO VE GKK SEKME GID'Sİ ("Form Yanıtları 7" / 1866719555)
SPREADSHEET_ID = "1O8qGTDrwv0RRv2Qv7jeux93Y8vz4uT2pwJRQ8U1Vq8o"
SHEET_GID = "1834241278"         # Saha Verileri Sekmesi
SHEET2_GID = "1493441004"        # Ekstra Listeler Sekmesi
GKK_SHEET_GID = "1866719555"     # GÜNCEL GİRİŞ KALİTE SEKME GID (Form Yanıtları 7)

CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET_GID}"
CSV2_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET2_GID}"
CSV_GIRIS_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GKK_SHEET_GID}"

# Güncel Apps Script Web App URL'i (6 numaralı sürüm dağıtımı)
# ÖNEMLİ: Apps Script'te "Web uygulaması > URL > Kopyala" ile aldığınız adresle birebir aynı olmalı.
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycby9xKz14pVGDNPDkUlUsztvrOK6WEAUOmbXDWBNcpwL70lcg8QRR1AVwKNEXAEoi40P/exec"

_HEADERS = {"User-Agent": "Mozilla/5.0 (MSP Kalite Sistemi)"}

# Bu puanın altında neden yazmak zorunlu
DUSUK_PUAN_ESIGI = 70

# E-tablodaki alt puan / neden sütun başlıkları (Kod.gs ile aynı olmalı)
ALT_PUANLAR = [
    ("Paketleme", "Paketleme Puanı", "Paketleme Nedeni"),
    ("Sevkiyat", "Sevkiyat Puanı", "Sevkiyat Nedeni"),
    ("Ürün Kalitesi", "Kalite Puanı", "Kalite Nedeni"),
    ("Etiket", "Etiket Puanı", "Etiket Nedeni"),
]

# Alt puanlara ait belge/foto bağlantılarının e-tablodaki sütun başlıkları (Kod.gs ile aynı olmalı)
ALT_BELGE = {
    "Paketleme": "Paketleme Belge",
    "Sevkiyat": "Sevkiyat Belge",
    "Ürün Kalitesi": "Kalite Belge",
    "Etiket": "Etiket Belge",
}

AY_ADLARI = ["OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN",
             "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"]

def temiz_ad(metin):
    """Dosya adında kullanılabilecek, boşluksuz ve güvenli metin üretir."""
    t = re.sub(r"[^\w\-]+", "-", str(metin).strip(), flags=re.UNICODE).strip("-")
    return t[:40] if t else "belge"

if "form_key" not in st.session_state:
    st.session_state.form_key = 0
if "mesaj" not in st.session_state:
    st.session_state.mesaj = None
if "gkk_mesaj" not in st.session_state:
    st.session_state.gkk_mesaj = None
if "gkk_hata" not in st.session_state:
    st.session_state.gkk_hata = None
if "belge_hata" not in st.session_state:
    st.session_state.belge_hata = None

@st.cache_data(ttl=5, show_spinner=False)
def verileri_yukle():
    try:
        df = pd.read_csv(CSV_URL)
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=5, show_spinner=False)
def giris_kalite_yukle():
    try:
        df = pd.read_csv(CSV_GIRIS_URL)
        df = df.dropna(how="all")
        # Puan sütunlarında virgüllü ondalıkları (61,5) sayıya çevir
        for c in df.columns:
            if any(x in str(c).lower() for x in ("puan", "100", "değerlendirme")):
                df[c] = pd.to_numeric(df[c].astype(str).str.strip().str.replace(",", ".", regex=False), errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=5, show_spinner=False)
def ekstra_liste_yukle():
    try:
        df = pd.read_csv(CSV2_URL)
        df = df.dropna(how="all")
        if df.empty or "Tip" not in df.columns or "Değer" not in df.columns:
            return [], []
        tip = df["Tip"].astype(str).str.strip().str.upper()
        deger = df["Değer"].astype(str).str.strip()
        personeller = deger[tip == "PERSONEL"].tolist()
        parcalar = deger[tip == "PARCA"].tolist()
        return list(dict.fromkeys(p for p in personeller if p and p.lower() != "nan")), list(dict.fromkeys(p for p in parcalar if p and p.lower() != "nan"))
    except Exception:
        return [], []

def dosyalari_yukle(dosyalar, on_ad=None):
    """Dosyaları Apps Script ile Drive'a yükler. on_ad verilirse dosya adı 'on_ad_1.uzanti' olur."""
    if not dosyalar:
        return []
    payload_dosyalar = []
    for i, f in enumerate(dosyalar, start=1):
        uzanti = os.path.splitext(f.name)[1].lower()
        yeni_ad = f"{on_ad}_{i}{uzanti}" if on_ad else f.name
        payload_dosyalar.append({
            "name": yeni_ad,
            "mimeType": f.type or "application/octet-stream",
            "data": base64.b64encode(f.getvalue()).decode("utf-8"),
        })
    st.session_state.belge_hata = None
    try:
        resp = requests.post(APPS_SCRIPT_URL, json={"files": payload_dosyalar}, headers=_HEADERS, timeout=120)
        try:
            sonuc = resp.json()
        except Exception:
            st.session_state.belge_hata = f"HTTP {resp.status_code} - Yanıt JSON değil: {resp.text[:300]}"
            return None
        if sonuc.get("success"):
            return sonuc.get("links", [])
        st.session_state.belge_hata = f"Apps Script hatası: {sonuc.get('error')}"
        return None
    except Exception as e:
        st.session_state.belge_hata = f"Bağlantı hatası: {e}"
        return None

def veri_kaydet(yeni_veri: dict) -> bool:
    payload = {
        ENTRY_PERSONEL: yeni_veri["personel"],
        ENTRY_PARCA: yeni_veri["parca"],
        ENTRY_RET_NEDENI: yeni_veri["ret_nedeni"],
        ENTRY_OP_ADI: yeni_veri["op_adi"],
        ENTRY_CNC_NO: yeni_veri["cnc_no"],
        ENTRY_ACIKLAMA: yeni_veri["aciklama"],
        ENTRY_RET_MIKTARI: yeni_veri["ret_miktari"],
        ENTRY_URETIM_MIKTARI: yeni_veri["uretim_miktari"],
        ENTRY_BELGE_LINKLERI: yeni_veri.get("belge_linkleri", ""),
        "emailAddress": SABIT_EPOSTA,
    }
    try:
        resp = requests.post(FORM_RESPONSE_URL, data=payload, headers=_HEADERS, timeout=15)
        if resp.status_code in (200, 302):
            verileri_yukle.clear()
            return True
        return False
    except Exception:
        return False

def giris_kalite_kaydet(gkk_veri: dict) -> bool:
    """Giriş kalite kaydını Apps Script'e gönderir. Hata olursa nedenini session_state.gkk_hata içine yazar."""
    st.session_state.gkk_hata = None
    try:
        resp = requests.post(APPS_SCRIPT_URL, json={"veri": gkk_veri}, headers=_HEADERS, timeout=30)
        try:
            sonuc = resp.json()
        except Exception:
            st.session_state.gkk_hata = f"HTTP {resp.status_code} - Yanıt JSON değil: {resp.text[:300]}"
            return False
        if sonuc.get("success"):
            giris_kalite_yukle.clear()
            return True
        st.session_state.gkk_hata = f"Apps Script hatası: {sonuc.get('error')}"
        return False
    except Exception as e:
        st.session_state.gkk_hata = f"Bağlantı hatası: {e}"
        return False

def puan_metni(seri):
    """Puanları sola hizalı, okunur metne çevirir (tabloda sağda taşıp kaybolmasın diye)."""
    sayi = pd.to_numeric(seri, errors="coerce")
    return [f"{v:g}" if pd.notna(v) else ("" if pd.isna(o) else str(o)) for v, o in zip(sayi, seri)]

def bolum_baslik(metin):
    """Renkli sol çizgili, belirgin bölüm başlığı."""
    st.markdown(
        f'<div style="border-left: 7px solid #2563EB; padding: 0.15rem 0 0.15rem 0.9rem; margin: 0.4rem 0 0.6rem 0; '
        f'font-size: 1.7rem; font-weight: 800; color: #0F172A;">{metin}</div>',
        unsafe_allow_html=True,
    )

def ayirici():
    """Bölümler arasına belirgin yatay çizgi koyar."""
    st.markdown(
        '<hr style="border: none; border-top: 3px solid #CBD5E1; margin: 2rem 0 1.6rem 0;">',
        unsafe_allow_html=True,
    )

def kalici_liste_ekle(tip: str, deger: str) -> bool:
    payload = {ENTRY2_TIP: tip, ENTRY2_DEGER: deger, "emailAddress": SABIT_EPOSTA}
    try:
        resp = requests.post(FORM2_RESPONSE_URL, data=payload, headers=_HEADERS, timeout=15)
        if resp.status_code in (200, 302):
            ekstra_liste_yukle.clear()
            return True
        return False
    except Exception:
        return False

# ======================================================================
# KULLANICI GİRİŞİ VE YETKİ
# Kullanıcılar Streamlit "Secrets" bölümünde tanımlanır (bkz. secrets_ornek.toml)
# ======================================================================
SECIM = "-- Seçiniz --"
BIRIM_SIRASI = ["GIRIS", "CNC", "ROTOR", "MONTAJ", "POMPA"]

BIRIMLER = {
    "GIRIS": {"baslik": "📦 GİRİŞ KALİTE KONTROL", "ad": "Giriş Kalite Kontrol"},
    "CNC": {"baslik": "🔧 CNC SAHA KONTROL", "ad": "CNC Saha Kontrol"},
    "ROTOR": {
        "baslik": "🧲 ROTOR & STATOR KONTROL",
        "ad": "Rotor & Stator Kontrol",
        "listeler": {
            "PERSONEL": "Kalite Personeli",
            "MALZEME": "Rotor / Stator Modelleri",
            "ASAMA": "Kontrol Aşamaları",
            "HATA": "Hata / Ret Nedenleri",
        },
        "varsayilan": {
            "MALZEME": ["ROTOR", "STATOR"],
            "ASAMA": ["GELEN MALZEME", "PROSES ARASI", "SON KONTROL"],
            "HATA": ["SARGI HATASI", "İZOLASYON HATASI", "ÖLÇÜ HATASI", "YÜZEY HATASI", "BALANS HATASI", "DİĞER"],
        },
        "alanlar": [
            {"anahtar": "Rotor / Stator Modeli", "tip": "secim", "liste": "MALZEME", "zorunlu": True},
            {"anahtar": "Kontrol Aşaması", "tip": "secim", "liste": "ASAMA", "zorunlu": True},
            {"anahtar": "Hata Nedeni", "tip": "secim", "liste": "HATA"},
            {"anahtar": "Açıklama", "tip": "metin", "ornek": "Örn: Sargı uç bağlantısı gevşek"},
            {"anahtar": "Ret Adedi", "tip": "sayi"},
            {"anahtar": "Kontrol Edilen Adet", "tip": "sayi"},
        ],
        "model_alani": "Rotor / Stator Modeli",
        "ret_alani": "Ret Adedi", "hata_alani": "Hata Nedeni", "adet_alani": "Kontrol Edilen Adet",
    },
    "MONTAJ": {
        "baslik": "⚡ MOTOR MONTAJ & SON KONTROL",
        "ad": "Motor Montaj & Son Kontrol",
        "listeler": {
            "PERSONEL": "Kalite Personeli",
            "MALZEME": "Motor Modelleri",
            "KONTROL": "Kontrol Listesi Maddeleri",
        },
        "varsayilan": {
            "MALZEME": ["4\" MOTOR", "6\" MOTOR", "8\" MOTOR"],
            "KONTROL": ["Sargı direnci", "İzolasyon direnci (megger)", "Yatak / rulman kontrolü", "Mil salgısı",
                        "Kablo ve bağlantılar", "Etiket ve seri no", "Boya ve görünüm", "Boşta çalışma testi"],
        },
        "alanlar": [
            {"anahtar": "Motor Modeli", "tip": "secim", "liste": "MALZEME", "zorunlu": True},
            {"anahtar": "Seri No", "tip": "metin", "ornek": "Örn: 26-0458", "zorunlu": True},
            {"anahtar": "Kontrol Listesi", "tip": "kontrol", "liste": "KONTROL"},
            {"anahtar": "Açıklama", "tip": "metin", "ornek": "Uygunsuzluk varsa nedenini yazın"},
        ],
        "model_alani": "Motor Modeli",
    },
    "POMPA": {
        "baslik": "💧 POMPA ÜRETİM & TEST KONTROL",
        "ad": "Pompa Üretim & Test Kontrol",
        "listeler": {
            "PERSONEL": "Kalite Personeli",
            "MALZEME": "Pompa Modelleri",
            "KONTROL": "Kontrol Listesi Maddeleri",
        },
        "varsayilan": {
            "MALZEME": [],
            "KONTROL": ["Basınç testi", "Debi testi", "Sızdırmazlık", "Gürültü / titreşim", "Akım değeri", "Görünüm ve etiket"],
        },
        "alanlar": [
            {"anahtar": "Pompa Modeli", "tip": "secim", "liste": "MALZEME", "zorunlu": True},
            {"anahtar": "Seri No", "tip": "metin", "ornek": "Örn: P-26-0012", "zorunlu": True},
            {"anahtar": "Kontrol Listesi", "tip": "kontrol", "liste": "KONTROL"},
            {"anahtar": "Basınç (bar)", "tip": "olcum", "ornek": "Örn: 4,5"},
            {"anahtar": "Debi (m³/h)", "tip": "olcum", "ornek": "Örn: 12,3"},
            {"anahtar": "Akım (A)", "tip": "olcum", "ornek": "Örn: 6,8"},
            {"anahtar": "Açıklama", "tip": "metin", "ornek": "Uygunsuzluk varsa nedenini yazın"},
        ],
        "model_alani": "Pompa Modeli",
    },
}
YENI_BIRIMLER = ["ROTOR", "MONTAJ", "POMPA"]


def kullanicilari_al():
    """Secrets içindeki kullanıcıları döndürür; tanımlı değilse None."""
    try:
        ham = st.secrets["kullanicilar"]
        sonuc = {}
        for kadi in ham:
            u = ham[kadi]
            sonuc[str(kadi).strip().lower()] = {
                "ad": str(u.get("ad", kadi)),
                "rol": str(u.get("rol", "personel")).lower(),
                "birimler": [str(b).upper() for b in u.get("birimler", [])],
                "sifre": str(u["sifre"]) if "sifre" in u else None,
                "sifre_hash": str(u["sifre_hash"]).lower() if "sifre_hash" in u else None,
            }
        return sonuc or None
    except Exception:
        return None


def giris_dogrula(kullanicilar, kadi, sifre):
    u = kullanicilar.get(str(kadi).strip().lower())
    if not u:
        return None
    dogru = False
    if u["sifre_hash"]:
        dogru = hmac.compare_digest(hashlib.sha256(sifre.encode("utf-8")).hexdigest(), u["sifre_hash"])
    elif u["sifre"] is not None:
        dogru = hmac.compare_digest(sifre.encode("utf-8"), u["sifre"].encode("utf-8"))
    if not dogru:
        return None
    birimler = list(BIRIM_SIRASI) if u["rol"] == "yonetici" else [b for b in u["birimler"] if b in BIRIMLER]
    return {"kadi": str(kadi).strip().lower(), "ad": u["ad"], "rol": u["rol"], "birimler": birimler}


# ======================================================================
# YENİ BİRİMLER İÇİN VERİ / LİSTE İŞLEMLERİ (Apps Script üzerinden)
# ======================================================================
def apps_script_gonder(payload, zaman_asimi=30):
    """Apps Script'e JSON gönderir. (basarili, hata_metni) döndürür."""
    try:
        resp = requests.post(APPS_SCRIPT_URL, json=payload, headers=_HEADERS, timeout=zaman_asimi)
        try:
            sonuc = resp.json()
        except Exception:
            return False, f"HTTP {resp.status_code} - Yanıt JSON değil: {resp.text[:300]}"
        if sonuc.get("success"):
            return True, None
        return False, f"Apps Script hatası: {sonuc.get('error')}"
    except Exception as e:
        return False, f"Bağlantı hatası: {e}"


@st.cache_data(ttl=10, show_spinner=False)
def birim_kayitlari_yukle(birim):
    try:
        r = requests.get(APPS_SCRIPT_URL, params={"islem": "oku", "birim": birim}, headers=_HEADERS, timeout=30)
        s = r.json()
        if s.get("success"):
            return pd.DataFrame(s.get("rows", []))
    except Exception:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=10, show_spinner=False)
def birim_listeleri_yukle():
    """{birim: {tip: [değerler]}} sözlüğü döndürür."""
    sonuc = {}
    try:
        r = requests.get(APPS_SCRIPT_URL, params={"islem": "listeler"}, headers=_HEADERS, timeout=30)
        s = r.json()
        if s.get("success"):
            for satir in s.get("rows", []):
                sonuc.setdefault(satir["Birim"], {}).setdefault(satir["Tip"], []).append(satir["Deger"])
    except Exception:
        pass
    return sonuc


def liste_getir(kod, tip, listeler):
    cfg = BIRIMLER[kod]
    return listeler.get(kod, {}).get(tip) or cfg.get("varsayilan", {}).get(tip, [])


def liste_islem(islem, kod, tip, deger):
    ok, hata = apps_script_gonder({"liste_islem": {"islem": islem, "birim": kod, "tip": tip, "deger": deger}})
    if ok:
        birim_listeleri_yukle.clear()
    else:
        st.error(f"❌ İşlem yapılamadı. {hata}")
    return ok


def kayit_tablosu_ve_galeri(df, ozet_anahtarlari):
    """Kayıt tablosunu belge bağlantılarıyla (tıklanabilir) ve belgeli kayıtların küçük resimleriyle gösterir."""
    belge_kolonlari = [c for c in df.columns if "belge" in str(c).lower()]

    def _satir_linkleri(i):
        bulunan = []
        for c in belge_kolonlari:
            ham = str(df.iloc[i][c])
            if ham.strip().lower() in ("", "nan", "none"):
                continue
            bulunan += [l for l in re.split(r"[,\s]+", ham) if l.startswith("http")]
        return list(dict.fromkeys(bulunan))

    link_listesi = [_satir_linkleri(i) for i in range(len(df))]
    en_cok = max([len(l) for l in link_listesi] + [1])

    df_goster = df.drop(columns=belge_kolonlari)
    bos_kolonlar = [c for c in df_goster.columns
                    if (str(c).startswith("Unnamed") or re.match(r"^\d+\. sütun$", str(c))) and df_goster[c].isna().all()]
    df_goster = df_goster.drop(columns=bos_kolonlar)
    kolon_ayari = {}
    for k in range(en_cok):
        ad = f"Belge {k + 1}"
        df_goster[ad] = [l[k] if len(l) > k else None for l in link_listesi]
        kolon_ayari[ad] = st.column_config.LinkColumn(ad, display_text="📎 Aç")
    st.dataframe(df_goster, use_container_width=True, hide_index=True, column_config=kolon_ayari)

    belgeli = [i for i, l in enumerate(link_listesi) if l]
    if not belgeli:
        st.caption("Henüz belge / fotoğraf eklenmiş kayıt yok.")
        return
    ayirici()
    bolum_baslik("🖼️ Belgeler ve Fotoğraflar")
    st.caption("Küçük resme veya bağlantıya tıklayınca belge yeni sekmede açılır. En yeni 20 belgeli kayıt gösterilir.")

    def _kol_bul(anahtarlar):
        for c in df.columns:
            if any(a in str(c).lower() for a in anahtarlar):
                return c
        return None

    kolonlar_ozet = [_kol_bul(a) for a in ozet_anahtarlari]

    def _g(satir, kol):
        if not kol:
            return None
        v = str(satir[kol]).strip()
        return None if v.lower() in ("", "nan", "none") else v

    for i in reversed(belgeli[-20:]):
        satir = df.iloc[i]
        linkler = link_listesi[i]
        parcalar = [p for p in (_g(satir, k) for k in kolonlar_ozet) if p]
        with st.container(border=True):
            st.markdown("**" + " — ".join(parcalar) + "**" if parcalar else "**Kayıt**")
            for baslangic in range(0, len(linkler), 4):
                kolonlar = st.columns(4)
                for kol, (k, link) in zip(kolonlar, enumerate(linkler[baslangic:baslangic + 4], start=baslangic + 1)):
                    m = re.search(r"/d/([\w-]+)", link) or re.search(r"[?&]id=([\w-]+)", link)
                    with kol:
                        if m:
                            kucuk = f"https://drive.google.com/thumbnail?id={m.group(1)}&sz=w400"
                            st.markdown(
                                f"<a href='{link}' target='_blank'><img src='{kucuk}' alt='Belge {k}' "
                                f"style='width:100%;border-radius:8px;border:1px solid #CBD5E1'></a>",
                                unsafe_allow_html=True)
                        st.markdown(f"<a href='{link}' target='_blank' style='font-weight:700;color:#1D4ED8'>📎 Belge {k}</a>", unsafe_allow_html=True)


def cubuk_grafik(seri, renk="#2563EB"):
    """Sıralı (verilen sırada) basit çubuk grafik. seri: pandas Series (indeks=etiket)."""
    veri = pd.DataFrame({"Etiket": [str(i) for i in seri.index], "Adet": list(seri.values)})
    grafik = alt.Chart(veri).mark_bar(color=renk).encode(
        x=alt.X("Etiket:N", sort=list(veri["Etiket"]), title=None, axis=alt.Axis(labelAngle=-30)),
        y=alt.Y("Adet:Q", title=None),
        tooltip=["Etiket", "Adet"],
    ).properties(height=280)
    st.altair_chart(grafik, use_container_width=True, theme=None)


def genel_form(kod, oturum):
    cfg = BIRIMLER[kod]
    fk = st.session_state.get(f"fk_{kod}", 0)
    mk = f"mesaj_{kod}"
    if st.session_state.get(mk):
        st.success(st.session_state[mk])
        st.session_state[mk] = None
    listeler = birim_listeleri_yukle()
    satir = {}
    uygunsuzlar = []
    eksikler = []

    # Kalite personeli
    if oturum["rol"] == "yonetici":
        pl = liste_getir(kod, "PERSONEL", listeler)
        if pl:
            personel = st.selectbox("Kalite Personeli", [SECIM] + pl, key=f"{kod}_personel_{fk}")
        else:
            personel = st.text_input("Kalite Personeli", placeholder="Ad Soyad (listeye eklemek için Listeler sekmesini kullanın)", key=f"{kod}_personel_{fk}")
        if personel in ("", SECIM):
            eksikler.append("Kalite Personeli")
    else:
        personel = oturum["ad"]
        st.text_input("Kalite Personeli", value=personel, disabled=True, key=f"{kod}_personel_sabit_{fk}")
    satir["Personel"] = personel

    for a in cfg["alanlar"]:
        ad = a["anahtar"]
        key = f"{kod}_{ad}_{fk}"
        tip = a["tip"]
        if tip == "secim":
            secenekler = liste_getir(kod, a["liste"], listeler)
            if not secenekler:
                st.warning(f"'{ad}' listesi boş. Önce Listeler sekmesinden ekleyin.")
            deger = st.selectbox(ad, [SECIM] + secenekler, key=key)
            if deger == SECIM:
                deger = ""
                if a.get("zorunlu"):
                    eksikler.append(ad)
            satir[ad] = deger
        elif tip == "metin":
            deger = st.text_input(ad, placeholder=a.get("ornek", ""), key=key).strip()
            if a.get("zorunlu") and not deger:
                eksikler.append(ad)
            satir[ad] = deger
        elif tip == "sayi":
            satir[ad] = int(st.number_input(ad, min_value=0, step=1, key=key))
        elif tip == "olcum":
            ham = st.text_input(ad, placeholder=a.get("ornek", ""), key=key).strip()
            try:
                satir[ad] = float(ham.replace(",", ".")) if ham else ""
            except ValueError:
                satir[ad] = ham
        elif tip == "kontrol":
            st.markdown(f"**{ad}**")
            maddeler = liste_getir(kod, a["liste"], listeler)
            if not maddeler:
                st.info("Kontrol listesi boş. Listeler sekmesinden madde ekleyin.")
            with st.container(border=True):
                for madde in maddeler:
                    v = st.radio(madde, ["UYGUN", "UYGUNSUZ", "UYGULANAMAZ"], horizontal=True, key=f"{kod}_k_{madde}_{fk}")
                    satir[madde] = v
                    if v == "UYGUNSUZ":
                        uygunsuzlar.append(madde)

    dosyalar = st.file_uploader("📎 BELGE / FOTOĞRAF EKLE", type=["png", "jpg", "jpeg", "pdf"],
                                accept_multiple_files=True, key=f"{kod}_foto_{fk}")

    if st.button("KAYDET VE GÖNDER", use_container_width=True, key=f"{kod}_kaydet_{fk}"):
        ret_alani = cfg.get("ret_alani")
        ret = satir.get(ret_alani, 0) if ret_alani else 0
        hata_alani = cfg.get("hata_alani")
        if hata_alani and ret and not satir.get(hata_alani):
            eksikler.append(f"{hata_alani} (ret adedi 0'dan büyük)")
        if uygunsuzlar and not satir.get("Açıklama"):
            eksikler.append("Açıklama (uygunsuz madde işaretlendi)")
        if eksikler:
            st.warning("⚠️ Lütfen şu alanları doldurun: " + ", ".join(eksikler))
            return
        satir["Uygunsuz Maddeler"] = ", ".join(uygunsuzlar)
        satir["Sonuç"] = "UYGUNSUZ" if (uygunsuzlar or ret) else "UYGUN"
        satir["Kaydeden"] = oturum["kadi"]
        model = satir.get(cfg.get("model_alani", ""), "") or kod
        on_ad = f"{kod}_{temiz_ad(model)}_{datetime.today().strftime('%d-%m-%Y')}"
        linkler = dosyalari_yukle(dosyalar, on_ad=on_ad) if dosyalar else []
        if linkler is None:
            st.error("❌ Belge / fotoğraf yüklenemedi. Kayıt yapılmadı, lütfen tekrar deneyin.")
            if st.session_state.belge_hata:
                st.code(st.session_state.belge_hata)
            return
        satir["Belge Linkleri"] = ", ".join(linkler)
        ok, hata = apps_script_gonder({"birim_kayit": {"birim": kod, "satir": satir}})
        if ok:
            birim_kayitlari_yukle.clear()
            st.session_state[f"fk_{kod}"] = fk + 1
            st.session_state[mk] = "✅ Kayıt başarıyla alındı."
            st.rerun()
        else:
            st.error("❌ Kayıt gönderilirken bir hata oluştu!")
    
