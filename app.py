# -*- coding: utf-8 -*-
import base64
import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import datetime

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
    button[data-baseweb="tab"] { padding: 0.9rem 1.4rem; }
    button[data-baseweb="tab"] p { font-size: 1.35rem !important; font-weight: 800 !important; }

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
SHEET_GID = "1834241278"         # Saha Verileri Sekmesi
SHEET2_GID = "1493441004"        # Ekstra Listeler Sekmesi
GKK_SHEET_GID = "1866719555"     # GÜNCEL GİRİŞ KALİTE SEKME GID (Form Yanıtları 7)

CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET_GID}"
CSV2_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET2_GID}"
CSV_GIRIS_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GKK_SHEET_GID}"

# Güncel Apps Script Web App URL'i
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

if "form_key" not in st.session_state:
    st.session_state.form_key = 0
if "mesaj" not in st.session_state:
    st.session_state.mesaj = None
if "gkk_mesaj" not in st.session_state:
    st.session_state.gkk_mesaj = None
if "gkk_hata" not in st.session_state:
    st.session_state.gkk_hata = None

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
        return df.dropna(how="all")
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

def dosyalari_yukle(dosyalar):
    if not dosyalar:
        return []
    payload_dosyalar = []
    for f in dosyalar:
        payload_dosyalar.append({
            "name": f.name,
            "mimeType":
