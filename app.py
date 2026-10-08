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
    /* ANA MENÜ SEKMELERİ: büyük, kalın, renkli */
    div[data-baseweb="tab-list"] { gap: 0.5rem; }
    button[data-baseweb="tab"] {
        padding: 0.9rem 1.6rem;
        border-radius: 12px 12px 0 0;
        background: #E0E7FF;
        border: 2px solid #C7D2FE;
        border-bottom: none;
        transition: all 0.15s ease;
    }
    button[data-baseweb="tab"] p {
        font-size: 1.55rem !important;
        font-weight: 900 !important;
        letter-spacing: 0.3px;
        color: #1E3A8A !important;
    }
    button[data-baseweb="tab"]:hover { background: #C7D2FE; transform: translateY(-2px); }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #2563EB 0%, #1E3A8A 100%);
        border-color: #1E3A8A;
        box-shadow: 0 -3px 10px rgba(37,99,235,0.35);
    }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #FFFFFF !important; }
    div[data-baseweb="tab-highlight"] { background-color: #F59E0B !important; height: 5px !important; }
    div[data-baseweb="tab-border"] { background-color: #1E3A8A !important; height: 3px !important; }

    /* TÜM MENÜ VE BÖLÜM BAŞLIKLARI: aynı büyük, kalın, renkli tema (alt menüler dahil) */
    div[data-baseweb="tab-panel"] button[data-baseweb="tab"] { margin-top: 0.3rem; }
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
SHEET_GID = "1834241278"         # Saha Verileri Sekmesi
SHEET2_GID = "1493441004"        # Ekstra Listeler Sekmesi
GKK_SHEET_GID = "1866719555"     # GÜNCEL GİRİŞ KALİTE SEKME GID (Form Yanıtları 7)

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
            st.code(hata)


def genel_rapor(kod):
    cfg = BIRIMLER[kod]
    df = birim_kayitlari_yukle(kod)
    if df.empty:
        st.info("Bu birim için henüz kayıt yok.")
        return
    df = df.copy()
    df["_t"] = pd.to_datetime(df["Zaman"], errors="coerce") if "Zaman" in df.columns else pd.NaT

    bugun = datetime.today().date()
    c1, c2, c3 = st.columns(3)
    bas = c1.date_input("Başlangıç tarihi", value=bugun - timedelta(days=30), key=f"{kod}_rbas")
    bit = c2.date_input("Bitiş tarihi", value=bugun, key=f"{kod}_rbit")
    personeller = sorted(df["Personel"].dropna().astype(str).unique()) if "Personel" in df.columns else []
    secili = c3.selectbox("Personel", ["Tümü"] + personeller, key=f"{kod}_rpers")

    maske = (df["_t"] >= pd.Timestamp(bas)) & (df["_t"] < pd.Timestamp(bit) + pd.Timedelta(days=1))
    if secili != "Tümü":
        maske &= df["Personel"].astype(str) == secili
    d = df[maske].sort_values("_t")
    if d.empty:
        st.info("Seçilen tarih aralığında kayıt yok.")
        return

    ret_alani, adet_alani = cfg.get("ret_alani"), cfg.get("adet_alani")
    uygunsuz_adet = int((d["Sonuç"] == "UYGUNSUZ").sum()) if "Sonuç" in d.columns else 0
    m = st.columns(4)
    m[0].metric("Toplam Kayıt", f"{len(d)}")
    m[1].metric("Uygunsuz Kayıt", f"{uygunsuz_adet}")
    m[2].metric("Uygunsuzluk Oranı", f"%{uygunsuz_adet / len(d) * 100:.1f}")
    if ret_alani and ret_alani in d.columns:
        ret_top = pd.to_numeric(d[ret_alani], errors="coerce").fillna(0).sum()
        kont_top = pd.to_numeric(d[adet_alani], errors="coerce").fillna(0).sum() if adet_alani in d.columns else 0
        m[3].metric("Toplam Ret / Oran", f"{int(ret_top)}" + (f"  (%{ret_top / kont_top * 100:.1f})" if kont_top else ""))

    ayirici()
    g1, g2 = st.columns(2)
    with g1:
        bolum_baslik("📅 Günlük Kayıt Sayısı")
        gun = d.groupby(d["_t"].dt.date).size()
        gun.index = [x.strftime("%d.%m") for x in gun.index]
        cubuk_grafik(gun)
    with g2:
        hata_alani = cfg.get("hata_alani")
        if hata_alani and hata_alani in d.columns:
            bolum_baslik("⚠️ Hata Nedenleri")
            dd = d[d[hata_alani].astype(str).str.strip() != ""]
            if ret_alani and ret_alani in dd.columns:
                dd = dd.assign(_r=pd.to_numeric(dd[ret_alani], errors="coerce").fillna(0))
                seri = dd.groupby(hata_alani)["_r"].sum().sort_values(ascending=False)
            else:
                seri = dd[hata_alani].value_counts()
            if len(seri):
                cubuk_grafik(seri, "#DC2626")
            else:
                st.caption("Hata nedeni girilmiş kayıt yok.")
        else:
            bolum_baslik("⚠️ En Çok Uygunsuz Çıkan Maddeler")
            sayilar = {c: int((d[c] == "UYGUNSUZ").sum()) for c in d.columns if (d[c] == "UYGUNSUZ").any() and c != "Sonuç"}
            if sayilar:
                cubuk_grafik(pd.Series(sayilar).sort_values(ascending=False), "#DC2626")
            else:
                st.caption("Uygunsuz madde yok. 👍")

    ayirici()
    bolum_baslik("📋 Kayıtlar")
    model = cfg.get("model_alani", "").lower()
    kayit_tablosu_ve_galeri(d.drop(columns=["_t"]), [("zaman",), ("personel",), (model,) if model else ("seri",), ("sonuç",)])


def liste_yonetimi(kod):
    cfg = BIRIMLER[kod]
    listeler = birim_listeleri_yukle()
    st.caption("Formlardaki seçim listelerini buradan değiştirebilirsiniz (örn. yeni model veya kontrol maddesi ekleme).")
    for tip, etiket in cfg["listeler"].items():
        sheet_degerleri = listeler.get(kod, {}).get(tip, [])
        varsayilan = cfg.get("varsayilan", {}).get(tip, [])
        with st.container(border=True):
            st.markdown(f"#### {etiket}")
            aktif = sheet_degerleri or varsayilan
            if aktif:
                st.write("  •  ".join(aktif))
            else:
                st.info("Liste boş.")
            c1, c2 = st.columns([3, 1])
            yeni = c1.text_input("Yeni öğe", key=f"{kod}_{tip}_yeni", label_visibility="collapsed", placeholder="Yeni öğe yazın")
            if c2.button("➕ Ekle", key=f"{kod}_{tip}_ekle", use_container_width=True) and yeni.strip():
                if not sheet_degerleri and varsayilan:
                    ok = liste_islem("toplu_ekle", kod, tip, varsayilan + [yeni.strip()])
                else:
                    ok = liste_islem("ekle", kod, tip, yeni.strip())
                if ok:
                    st.rerun()
            if sheet_degerleri:
                sil = st.multiselect("Silinecek öğeler", sheet_degerleri, key=f"{kod}_{tip}_sil")
                if st.button("🗑️ Seçilenleri Sil", key=f"{kod}_{tip}_silbtn") and sil:
                    if liste_islem("sil", kod, tip, sil):
                        st.rerun()
            elif varsayilan:
                st.caption("Şu an varsayılan liste kullanılıyor. Öğe silmek için listeyi düzenlenebilir yapın.")
                if st.button("✏️ Listeyi düzenlenebilir yap", key=f"{kod}_{tip}_duz"):
                    if liste_islem("toplu_ekle", kod, tip, varsayilan):
                        st.rerun()


def genel_birim(kod, oturum):
    cfg = BIRIMLER[kod]
    st.header(cfg["ad"])
    t_giris, t_rapor, t_liste = st.tabs(["📝 Veri Girişi", "📊 Rapor ve Analiz", "⚙️ Listeler"])
    with t_giris:
        genel_form(kod, oturum)
    with t_rapor:
        genel_rapor(kod)
    with t_liste:
        liste_yonetimi(kod)


st.markdown(
    """
    <div style="background: linear-gradient(135deg, #2563EB 0%, #1E3A8A 100%); padding: 1.3rem 1.8rem; border-radius: 14px; margin-bottom: 0.8rem; box-shadow: 0 4px 14px rgba(37,99,235,0.25);">
        <h1 style="color: white; margin: 0; font-size: 2.3rem; line-height: 1.2;">🏭 MSP KALİTE YÖNETİM SİSTEMİ</h1>
        <p style="color: #DBEAFE; margin: 0.4rem 0 0 0; font-size: 1.15rem;">Birim Bazlı Kalite Kontrol, Veri Girişi ve Yönetim Raporları</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------- OTURUM ----------------
if "oturum" not in st.session_state:
    st.session_state.oturum = None

_kullanicilar = kullanicilari_al()
if _kullanicilar is None:
    st.error("🔒 Kullanıcı tanımları bulunamadı. Streamlit Cloud → uygulamanız → Settings → Secrets bölümüne kullanıcıları ekleyin (secrets_ornek.toml dosyasındaki gibi).")
    st.stop()

if not st.session_state.oturum:
    _s1, _s2, _s3 = st.columns([1, 2, 1])
    with _s2:
        with st.container(border=True):
            st.markdown("### 🔐 Kullanıcı Girişi")
            with st.form("giris_formu"):
                _secenekler = list(_kullanicilar.keys())
                _kadi = st.selectbox(
                    "Kullanıcı", _secenekler,
                    format_func=lambda k: f"{_kullanicilar[k]['ad']}",
                )
                _sifre = st.text_input("Şifre", type="password")
                _gonder = st.form_submit_button("GİRİŞ YAP", use_container_width=True)
            if _gonder:
                _sonuc = giris_dogrula(_kullanicilar, _kadi, _sifre)
                if _sonuc and (_sonuc["birimler"] or _sonuc["rol"] == "yonetici"):
                    st.session_state.oturum = _sonuc
                    st.rerun()
                else:
                    time.sleep(1)
                    st.error("Şifre hatalı (ya da bu kullanıcıya yetkili birim tanımlanmamış).")
    st.stop()

oturum = st.session_state.oturum
_b1, _b2, _b3 = st.columns([5, 1.3, 1.3])
_b1.markdown(
    f"👤 **{oturum['ad']}** — {'Kalite Yöneticisi' if oturum['rol'] == 'yonetici' else 'Birim Kalite Personeli'}"
    + ("" if oturum["rol"] == "yonetici" else " | Yetkili birim: " + ", ".join(BIRIMLER[b]["ad"] for b in oturum["birimler"]))
)
if _b2.button("🔄 Verileri Yenile", use_container_width=True, key="btn_yenile_genel"):
    st.cache_data.clear()
    st.rerun()
if _b3.button("🚪 Çıkış", use_container_width=True, key="btn_cikis"):
    st.session_state.oturum = None
    st.rerun()

_sekme_listesi = [(b, BIRIMLER[b]["baslik"]) for b in BIRIM_SIRASI if b in oturum["birimler"]]
if oturum["rol"] == "yonetici":
    _sekme_listesi.append(("YONETIM", "🛠️ YÖNETİM"))
S = dict(zip([k for k, _ in _sekme_listesi], st.tabs([t for _, t in _sekme_listesi])))

ekstra_personeller, ekstra_parcalar = ekstra_liste_yukle()


# ---------------- GİRİŞ KALİTE KONTROL ----------------
if "GIRIS" in S:
    with S["GIRIS"]:
        gkk_giris, gkk_rapor = st.tabs(["📝 Veri Girişi", "📊 Takip ve Satınalma Değerlendirme Analizi"])
        with gkk_giris:
                st.markdown("### 🛡️ Giriş Kalite Kontrol Takip ve Form Entegrasyonu")
                st.caption("Bu panel üzerinden girdiğiniz kalite kontrol verileri doğrudan Form Yanıtları 7 sekmesine işlenir.")

                if st.session_state.gkk_mesaj:
                    st.success(st.session_state.gkk_mesaj)
                    st.session_state.gkk_mesaj = None

                gkk_fk = f"gkk_{st.session_state.form_key}"

                with st.container(border=True):
                    st.markdown("#### Muayene ve Parça Bilgileri")
                    col_gkk1, col_gkk2 = st.columns(2)
                    with col_gkk1:
                        gkk_tarih = st.date_input("İnceleme Tarihi", value=datetime.today(), key=f"gkk_tarih_{gkk_fk}")
                        gkk_rapor_no = st.text_input("Rapor No", placeholder="Örn: RPR-2026-001", key=f"gkk_rapor_no_{gkk_fk}")
                        gkk_urun = st.text_input("Gelen Ürün / Parça Adı", placeholder="Örn: Stator / Rotor", key=f"gkk_urun_{gkk_fk}")

                    with col_gkk2:
                        gkk_firma = st.text_input("Tedarikçi Firma", placeholder="Tedarikçi firma adı...", key=f"gkk_firma_{gkk_fk}")
                        gkk_irsaliye = st.text_input("İrsaliye No", placeholder="İrsaliye numarası...", key=f"gkk_irsaliye_{gkk_fk}")

                    st.markdown("---")
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        gkk_miktar = st.number_input("Gelen Ürün Adedi", min_value=0.0, step=1.0, key=f"gkk_miktar_{gkk_fk}")
                        gkk_birim = st.selectbox("Birim", ["ADET", "KG", "METRE", "PAKET"], key=f"gkk_birim_{gkk_fk}")
                    with col_m2:
                        gkk_numune = st.number_input("Numune Adedi", min_value=0, step=1, key=f"gkk_numune_{gkk_fk}")
                        gkk_red_numune = st.number_input("Red Edilen Numune Adedi", min_value=0, step=1, key=f"gkk_red_numune_{gkk_fk}")
                    with col_m3:
                        # Kontrol frekansı: Numune Adedi / Gelen Ürün Adedi x 100 (otomatik)
                        _frekans_sayi = (gkk_numune / gkk_miktar * 100) if gkk_miktar and gkk_miktar > 0 else 0
                        gkk_frekans = f"{round(_frekans_sayi, 1):g}%"
                        st.metric("Kontrol Frekansı (otomatik)", gkk_frekans)
                        st.caption("Numune Adedi ÷ Gelen Ürün Adedi × 100")
                        gkk_onay = st.selectbox("Onay Durumu", ["KABUL", "ŞARTLI KABUL", "RED"], key=f"gkk_onay_{gkk_fk}")

                    gkk_aciklama = st.text_area("Ek Açıklama / Notlar", placeholder="Açıklama...", key=f"gkk_aciklama_{gkk_fk}")

                    st.markdown("#### ⭐ Tedarikçi Değerlendirme Puanları (0-100)")
                    st.caption(f"Bir puan {DUSUK_PUAN_ESIGI}'in altındaysa nedenini yazmanız zorunludur (örn: Ambalaj kırılmış).")

                    def puan_alani(etiket, anahtar, ornek):
                        puan = st.slider(etiket, 0, 100, 70, key=f"p_{anahtar}_{gkk_fk}")
                        neden = st.text_input(
                            f"{etiket} - Neden / Açıklama",
                            placeholder=ornek,
                            key=f"n_{anahtar}_{gkk_fk}",
                        )
                        if puan < DUSUK_PUAN_ESIGI and not neden.strip():
                            st.markdown(f'<span style="color:#DC2626;font-weight:700;">⚠️ {etiket} düşük, neden yazınız!</span>', unsafe_allow_html=True)
                        dosyalar = st.file_uploader(
                            f"📎 {etiket} - Belge / Fotoğraf Ekle",
                            type=["png", "jpg", "jpeg", "pdf"],
                            accept_multiple_files=True,
                            key=f"d_{anahtar}_{gkk_fk}",
                        )
                        return puan, neden.strip(), dosyalar

                    p_col1, p_col2 = st.columns(2)
                    with p_col1:
                        p_paket, n_paket, d_paket = puan_alani("Paketleme Puanı", "paket", "Örn: Ambalaj kırılmış")
                        p_sevkiyat, n_sevkiyat, d_sevkiyat = puan_alani("Sevkiyat Puanı", "sevkiyat", "Örn: 3 gün geç geldi")
                    with p_col2:
                        p_kalite, n_kalite, d_kalite = puan_alani("Ürün Kalitesi Puanı", "kalite", "Örn: Ölçü toleransı dışında")
                        p_etiket, n_etiket, d_etiket = puan_alani("Ürün Tanıtım Etiketi", "etiket", "Örn: Etiket eksik / okunmuyor")

                    genel_puan = round((p_paket + p_sevkiyat + p_kalite + p_etiket) / 4, 2)
                    st.metric("100 Üzerinden Genel Tedarikçi Puanı", f"{genel_puan}")

                    if st.button("🚀 Verileri Kaydet ve E-Tabloya Gönder", use_container_width=True):
                        eksik_nedenler = [ad for ad, p, n in (
                            ("Paketleme", p_paket, n_paket), ("Sevkiyat", p_sevkiyat, n_sevkiyat),
                            ("Ürün Kalitesi", p_kalite, n_kalite), ("Ürün Tanıtım Etiketi", p_etiket, n_etiket),
                        ) if p < DUSUK_PUAN_ESIGI and not n]
                        if not gkk_urun or not gkk_firma:
                            st.warning("⚠️ Lütfen Gelen Ürün / Parça Adı ve Tedarikçi Firma alanlarını doldurunuz!")
                        elif eksik_nedenler:
                            st.warning("⚠️ Düşük puan verdiğiniz alanların nedenini yazınız: " + ", ".join(eksik_nedenler))
                        else:
                            # Belgeleri tedarikçi_tarih_ürün_kategori adıyla Drive'a yükle
                            _on_ad = f"{temiz_ad(gkk_firma)}_{gkk_tarih.strftime('%d-%m-%Y')}_{temiz_ad(gkk_urun)}"
                            belge_linkleri_gkk, yukleme_hatasi = {}, []
                            if any((d_paket, d_sevkiyat, d_kalite, d_etiket)):
                                with st.spinner("Belgeler yükleniyor..."):
                                    for _ad, _dosyalar in (("Paketleme", d_paket), ("Sevkiyat", d_sevkiyat),
                                                           ("Ürün Kalitesi", d_kalite), ("Etiket", d_etiket)):
                                        if _dosyalar:
                                            _sonuc = dosyalari_yukle(_dosyalar, on_ad=f"{_on_ad}_{temiz_ad(_ad)}")
                                            if _sonuc is None:
                                                yukleme_hatasi.append(_ad)
                                                break
                                            else:
                                                belge_linkleri_gkk[_ad] = ", ".join(_sonuc)
                            gkk_kayit = {
                                "tarih": gkk_tarih.strftime("%d.%m.%Y"),
                                "rapor_no": gkk_rapor_no,
                                "urun": gkk_urun,
                                "firma": gkk_firma,
                                "irsaliye": gkk_irsaliye,
                                "onay": gkk_onay,
                                "tedarikci_puani": genel_puan,
                                "miktar": gkk_miktar,
                                "birim": gkk_birim,
                                "numune": gkk_numune,
                                "red_numune": gkk_red_numune,
                                "frekans": gkk_frekans,
                                "aciklama": gkk_aciklama,
                                "puan_paket": p_paket, "neden_paket": n_paket,
                                "puan_sevkiyat": p_sevkiyat, "neden_sevkiyat": n_sevkiyat,
                                "puan_kalite": p_kalite, "neden_kalite": n_kalite,
                                "puan_etiket": p_etiket, "neden_etiket": n_etiket,
                                "belge_paket": belge_linkleri_gkk.get("Paketleme", ""),
                                "belge_sevkiyat": belge_linkleri_gkk.get("Sevkiyat", ""),
                                "belge_kalite": belge_linkleri_gkk.get("Ürün Kalitesi", ""),
                                "belge_etiket": belge_linkleri_gkk.get("Etiket", ""),
                            }
                            if not yukleme_hatasi and giris_kalite_kaydet(gkk_kayit):
                                st.session_state.form_key += 1
                                st.session_state.gkk_mesaj = "✅ Giriş Kalite Kontrol kaydı Form Yanıtları 7 sekmesine başarıyla işlendi!"
                                st.rerun()
                            elif yukleme_hatasi:
                                st.error("❌ Belge yüklenemedi (" + ", ".join(yukleme_hatasi) + "). Kayıt yapılmadı, lütfen tekrar deneyin.")
                                if st.session_state.belge_hata:
                                    st.code(st.session_state.belge_hata)
                            else:
                                st.error("❌ Kayıt gönderilirken bir hata oluştu!")
                                if st.session_state.gkk_hata:
                                    st.code(st.session_state.gkk_hata)
        with gkk_rapor:
                df_gkk = giris_kalite_yukle()
                if not df_gkk.empty:
                    df_gkk.columns = [str(c).strip() for c in df_gkk.columns]
                    cols_map = {c.lower(): c for c in df_gkk.columns}

                    c_tarih = None
                    for col in df_gkk.columns:
                        if "tarih" in col.lower() and "zaman" not in col.lower():
                            c_tarih = col
                            break

                    if not c_tarih or (c_tarih in df_gkk.columns and df_gkk[c_tarih].dropna().empty):
                        if len(df_gkk.columns) > 0:
                            c_tarih = df_gkk.columns[0]

                    c_urun = next((cols_map[k] for k in cols_map if "ürün" in k or "urun" in k), None)
                    c_firma = next((cols_map[k] for k in cols_map if "firma" in k or "tedarikçi" in k or "company" in k or "şirket" in k), None)
                    c_rapor = next((cols_map[k] for k in cols_map if "rapor" in k), None)
                    c_onay = next((cols_map[k] for k in cols_map if "onay" in k), None)
                    c_not = next((cols_map[k] for k in cols_map if k == "notlar"), None)
                    c_frekans = next((cols_map[k] for k in cols_map if "frekans" in k), None)
                    # Puan sütunu: adayların içinden en çok sayısal değer içereni seç
                    _alt_basliklar = {b for _, p, n in ALT_PUANLAR for b in (p, n)}
                    _puan_adaylari = [c for c in df_gkk.columns
                                      if c not in _alt_basliklar and any(x in c.lower() for x in ("puan", "100", "değerlendirme"))]
                    c_puan = None
                    if _puan_adaylari:
                        c_puan = max(_puan_adaylari, key=lambda c: pd.to_numeric(df_gkk[c], errors="coerce").notna().sum())

                    # --- Haftaları hazırla (Pazartesi başlangıçlı) ---
                    df_gkk["_dt"] = pd.to_datetime(df_gkk[c_tarih], errors="coerce", dayfirst=True)
                    df_gkk["_hafta"] = df_gkk["_dt"].dt.isocalendar().week.fillna(1).astype(int)
                    df_gkk["_hafta_bas"] = (df_gkk["_dt"].dt.normalize() - pd.to_timedelta(df_gkk["_dt"].dt.weekday, unit="D"))
                    gecersiz_df = df_gkk[df_gkk["_hafta_bas"].isna()]

                    hafta_secenekleri = {}
                    for _hb in sorted(df_gkk["_hafta_bas"].dropna().unique(), reverse=True):
                        _bas = pd.Timestamp(_hb)
                        _son = _bas + pd.Timedelta(days=6)
                        _no = int(df_gkk.loc[df_gkk["_hafta_bas"] == _hb, "_hafta"].iloc[0])
                        hafta_secenekleri[f"{_no}. Hafta ({_bas.strftime('%d.%m.%Y')} Pazartesi / {_son.strftime('%d.%m.%Y')} Pazar)"] = _hb

                    if not hafta_secenekleri:
                        st.warning("Tarihi okunabilen kayıt bulunmuyor.")
                        if not gecersiz_df.empty:
                            st.dataframe(gecersiz_df.drop(columns=["_dt", "_hafta", "_hafta_bas"], errors="ignore"), use_container_width=True, hide_index=True)
                    else:
                        secilen_hafta = st.selectbox("🔎 Hafta seç", list(hafta_secenekleri.keys()), key="hafta_sec")
                        h_df = df_gkk[df_gkk["_hafta_bas"] == hafta_secenekleri[secilen_hafta]]

                        ayirici()
                        col_sol, col_sag = st.columns([1.3, 0.7])

                        # ---------- SOL: seçilen haftanın raporu ----------
                        with col_sol:
                            bolum_baslik("📅 Haftalık Rapor")
                            st.caption(f"{secilen_hafta} — {len(h_df)} giriş kalite. Satır renkleri: KABUL yeşil, ŞARTLI KABUL sarı, RED kırmızı. Puana göre sıralıdır (en yüksek en üstte, en düşük en altta).")

                            # Puana göre sırala: en yüksek (1.) en üstte, en düşük (sonuncu) en altta
                            if c_puan:
                                h_df = h_df.assign(_p=pd.to_numeric(h_df[c_puan], errors="coerce"))
                                h_df = h_df.sort_values("_p", ascending=False, na_position="last", kind="stable")
                            else:
                                h_df = h_df.assign(_p=float("nan"))
                            h_df = h_df.reset_index(drop=True)

                            p_max, p_min = h_df["_p"].max(), h_df["_p"].min()
                            sira_no = h_df["_p"].rank(method="min", ascending=False)

                            def _sira_metni(i):
                                p = h_df["_p"].iloc[i]
                                if pd.isna(p):
                                    return "-"
                                if p == p_max:
                                    return "1."
                                if p == p_min and p_max != p_min:
                                    return "Sonuncu"
                                return f"{int(sira_no.iloc[i])}."

                            sub_df = pd.DataFrame()
                            sub_df["Sıra"] = [_sira_metni(i) for i in range(len(h_df))]
                            sub_df["Tarih / Date"] = h_df[c_tarih]
                            sub_df["Gelen Ürün Tipi ve Ölçüsü"] = h_df[c_urun] if c_urun else "-"
                            sub_df["Gelen Ürün Şirket"] = h_df[c_firma] if c_firma else "-"
                            sub_df["RAPOR NO"] = h_df[c_rapor] if c_rapor else "-"
                            sub_df["Onay Durumu"] = h_df[c_onay] if c_onay else "-"
                            sub_df["100 ÜZERİNDEN DEĞERLENDİRME"] = puan_metni(h_df[c_puan]) if c_puan else "-"


                            def _renk_satir(satir, _onay=(h_df[c_onay].astype(str) if c_onay else None)):
                                if _onay is None:
                                    return [""] * len(satir)
                                durum = _onay.iloc[satir.name].strip().upper()
                                if "ŞARTLI" in durum or "SARTLI" in durum:
                                    renk = "background-color: #FEF9C3; color: #713F12; font-weight: 600"
                                elif durum in ("RED", "RET") or durum.startswith("RED") or durum.startswith("RET"):
                                    renk = "background-color: #FEE2E2; color: #7F1D1D; font-weight: 600"
                                elif "KABUL" in durum:
                                    renk = "background-color: #DCFCE7; color: #14532D; font-weight: 600"
                                else:
                                    renk = ""
                                return [renk] * len(satir)

                            stilli = sub_df.style.apply(_renk_satir, axis=1).set_properties(**{"text-align": "left"})
                            st.dataframe(stilli, use_container_width=True, hide_index=True)

                            # --- Hafta özeti: adet, ortalama, en düşük, en yüksek ---
                            _puanlar = h_df["_p"].dropna()
                            with st.container(border=True):
                                bolum_baslik("📌 Hafta Özeti")
                                o1, o2, o3, o4 = st.columns(4)
                                o1.metric("Toplam Giriş Kontrol", f"{len(h_df)} Adet")
                                o2.metric("Ortalama Puan", f"{_puanlar.mean():.1f}" if not _puanlar.empty else "-")
                                o3.metric("En Düşük Puan", f"{_puanlar.min():g}" if not _puanlar.empty else "-")
                                o4.metric("En Yüksek Puan", f"{_puanlar.max():g}" if not _puanlar.empty else "-")

                            # --- Puan detayı: 4 alt puan ve nedenleri ---
                            ayirici()
                            bolum_baslik("🔍 Puan Detayı ve Nedenler")
                            if not any(p in h_df.columns for _, p, _ in ALT_PUANLAR):
                                st.info("E-tabloda henüz alt puan / neden sütunu yok. Apps Script'in yeni sürümü yayınlandıktan sonra Giriş Kalite formundan yeni bir kayıt girdiğinizde sütunlar otomatik oluşur ve nedenler burada görünür. Eski kayıtlarda alt puan bilgisi bulunmaz.")
                            else:
                                if h_df[[p for _, p, _ in ALT_PUANLAR if p in h_df.columns]].apply(pd.to_numeric, errors="coerce").isna().all(axis=None):
                                    st.info("Bu haftadaki kayıtlar alt puan girişinden önce yapıldığı için detay yok. Yeni kayıtlarda nedenler burada görünür.")
                                st.caption(f"Kırmızı kutular {DUSUK_PUAN_ESIGI} puanın altındaki alt puanları ve girilen nedenleri gösterir.")
                                def _belge_linkleri(satir, ad):
                                    kol_adi = ALT_BELGE.get(ad)
                                    ham = str(satir.get(kol_adi, "")).strip() if kol_adi and kol_adi in h_df.columns else ""
                                    if not ham or ham.lower() == "nan":
                                        return []
                                    return [l.strip() for l in ham.split(",") if l.strip().startswith("http")]

                                for i in range(len(h_df)):
                                    satir = h_df.iloc[i]
                                    firma_adi = str(satir[c_firma]) if c_firma else "-"
                                    rapor_no = str(satir[c_rapor]) if c_rapor else "-"
                                    genel = puan_metni(h_df[c_puan].iloc[[i]])[0] if c_puan else "-"
                                    with st.container(border=True):
                                        _frek = str(satir[c_frekans]).strip() if c_frekans else ""
                                        _frek_txt = f" — Kontrol Frekansı: **{_frek}**" if _frek and _frek.lower() != "nan" else ""
                                        st.markdown(f"**{firma_adi}** — Rapor: {rapor_no} — Genel Puan: **{genel}**{_frek_txt}")
                                        kolonlar = st.columns(4)
                                        for kol, (ad, c_p, c_n) in zip(kolonlar, ALT_PUANLAR):
                                            with kol:
                                                p = pd.to_numeric(satir.get(c_p), errors="coerce") if c_p in h_df.columns else float("nan")
                                                n = str(satir.get(c_n, "")).strip() if c_n in h_df.columns else ""
                                                if n.lower() == "nan":
                                                    n = ""
                                                _lk = _belge_linkleri(satir, ad)
                                                _bas = (f"<a href='{_lk[0]}' target='_blank' style='color:inherit;font-weight:700;text-decoration:underline'>{ad}</a>" if _lk else ad)
                                                _ek = ("<div style='margin-top:0.4rem'>" + " &nbsp; ".join(
                                                    f"<a href='{l}' target='_blank' style='font-weight:700;color:#1D4ED8;text-decoration:underline'>📎 Belge {k}</a>"
                                                    for k, l in enumerate(_lk, start=1)) + "</div>") if _lk else ""
                                                if pd.isna(p):
                                                    st.markdown(f"<div style='color:#94A3B8'>{_bas}<br><b>-</b>{_ek}</div>", unsafe_allow_html=True)
                                                elif p < DUSUK_PUAN_ESIGI:
                                                    st.markdown(
                                                        f"<div style='background:#FEE2E2;border-left:5px solid #DC2626;padding:0.5rem 0.7rem;border-radius:8px;color:#7F1D1D'>"
                                                        f"{_bas}<br><b style='font-size:1.4rem'>{p:g}</b><br>{n if n else 'Neden yazılmamış'}{_ek}</div>",
                                                        unsafe_allow_html=True)
                                                else:
                                                    st.markdown(
                                                        f"<div style='background:#F0FDF4;border-left:5px solid #16A34A;padding:0.5rem 0.7rem;border-radius:8px;color:#14532D'>"
                                                        f"{_bas}<br><b style='font-size:1.4rem'>{p:g}</b>{('<br>' + n) if n else ''}{_ek}</div>",
                                                        unsafe_allow_html=True)
                                        _not = str(satir[c_not]).strip() if c_not else ""
                                        if _not and _not.lower() != "nan":
                                            st.markdown(
                                                f"<div style='background:#F1F5F9;border-left:5px solid #64748B;padding:0.5rem 0.8rem;border-radius:8px;margin-top:0.5rem;color:#1E293B'>"
                                                f"📝 <b>Ek Açıklama:</b> {_not}</div>",
                                                unsafe_allow_html=True)

                            if not gecersiz_df.empty:
                                with st.expander("⚠️ Tarihi okunamayan kayıtlar", expanded=False):
                                    st.dataframe(gecersiz_df.drop(columns=["_dt", "_hafta", "_hafta_bas"], errors="ignore"), use_container_width=True, hide_index=True)

                        # ---------- SAĞ: üstte tedarikçi fikstürü, altta aylık grafik ----------
                        with col_sag:
                            PUAN_ARALIKLARI = ["85 - 100  Çok İyi", "70 - 84  İyi", "50 - 69  Orta", "0 - 49  Zayıf"]
                            PUAN_RENKLERI = ["#16A34A", "#2563EB", "#F59E0B", "#DC2626"]

                            def _aralik(p):
                                if p >= 85:
                                    return PUAN_ARALIKLARI[0]
                                if p >= 70:
                                    return PUAN_ARALIKLARI[1]
                                if p >= 50:
                                    return PUAN_ARALIKLARI[2]
                                return PUAN_ARALIKLARI[3]

                            def _tema(grafik):
                                return (
                                    grafik.configure_view(strokeWidth=0)
                                    .configure_axis(
                                        labelFontSize=13, titleFontSize=13, titleFontWeight="bold",
                                        labelColor="#334155", titleColor="#334155",
                                        gridColor="#E2E8F0", domainColor="#CBD5E1", tickColor="#CBD5E1",
                                    )
                                    .configure_legend(
                                        labelFontSize=13, titleFontSize=13, titleFontWeight="bold",
                                        orient="bottom", symbolType="square", symbolSize=140,
                                    )
                                )

                            with st.container(border=True):
                                bolum_baslik("📊 Tedarikçi Puan Fikstürü")
                                st.caption(secilen_hafta)
                                if c_puan and c_firma:
                                    grafik_df = h_df[[c_firma, c_puan]].copy()
                                    grafik_df.columns = ["Firma", "Puan"]
                                    grafik_df["Puan"] = pd.to_numeric(grafik_df["Puan"], errors="coerce")
                                    grafik_df = grafik_df.dropna()
                                    if not grafik_df.empty:
                                        grafik_df = grafik_df.groupby("Firma", as_index=False)["Puan"].mean()
                                        grafik_df["Puan"] = grafik_df["Puan"].round(2)
                                        grafik_df["PuanMetni"] = grafik_df["Puan"].apply(lambda v: f"{v:g}".replace(".", ","))
                                        grafik_df["Aralık"] = grafik_df["Puan"].apply(_aralik)
                                        # En yüksek puan en üstte olacak şekilde firma sırası
                                        firma_sirasi = grafik_df.sort_values("Puan", ascending=False)["Firma"].tolist()
                                        hafta_ort = round(float(grafik_df["Puan"].mean()), 2)

                                        bar = alt.Chart(grafik_df).mark_bar(cornerRadiusEnd=8).encode(
                                            x=alt.X("Puan:Q", title="Puan (100 üzerinden)", scale=alt.Scale(domain=[0, 105]),
                                                    axis=alt.Axis(values=[0, 20, 40, 60, 80, 100])),
                                            y=alt.Y("Firma:N", sort=firma_sirasi, title=None, scale=alt.Scale(paddingInner=0.45, paddingOuter=0.2),
                                                    axis=alt.Axis(labelLimit=240, labelFontSize=14, labelFontWeight="bold", labelPadding=12)),
                                            color=alt.Color("Aralık:N",
                                                            scale=alt.Scale(domain=PUAN_ARALIKLARI, range=PUAN_RENKLERI),
                                                            legend=alt.Legend(title="Puan Aralığı", columns=2)),
                                            tooltip=[alt.Tooltip("Firma:N"), alt.Tooltip("PuanMetni:N", title="Puan"), alt.Tooltip("Aralık:N")],
                                        )
                                        etiket = alt.Chart(grafik_df).mark_text(align="left", dx=6, fontSize=15, fontWeight="bold", color="#0F172A").encode(
                                            x=alt.X("Puan:Q", title="Puan (100 üzerinden)", scale=alt.Scale(domain=[0, 105])),
                                            y=alt.Y("Firma:N", sort=firma_sirasi, title=None, scale=alt.Scale(paddingInner=0.45, paddingOuter=0.2)),
                                            text=alt.Text("PuanMetni:N"),
                                        )
                                        ort_cizgi = alt.Chart(pd.DataFrame({"Ortalama": [hafta_ort]})).mark_rule(
                                            strokeDash=[6, 4], strokeWidth=2, color="#475569"
                                        ).encode(x=alt.X("Ortalama:Q", title="Puan (100 üzerinden)", scale=alt.Scale(domain=[0, 105])), tooltip=[alt.Tooltip("Ortalama:Q", title="Hafta ortalaması", format=".2~f")])

                                        fiksturu = _tema(alt.layer(bar, etiket, ort_cizgi).properties(
                                            height=max(160, 70 * len(grafik_df) + 60)
                                        ))
                                        st.altair_chart(fiksturu, use_container_width=True, theme=None)
                                        st.caption(f"Kesikli çizgi: haftanın ortalama puanı ({f'{hafta_ort:g}'.replace('.', ',')})")
                                    else:
                                        st.info("Bu hafta için sayısal puan bulunmuyor.")
                                else:
                                    st.info("Puan veya firma sütunu eksik.")

                            ayirici()

                            with st.container(border=True):
                                bolum_baslik("📈 Aylık Puan Grafiği")
                                st.caption("Seçilen haftanın ayındaki tedarikçi ortalama puanları (hafta değişince ay da değişir). Renkler: yeşil 85-100, mavi 70-84, turuncu 50-69, kırmızı 0-49.")
                                if c_puan and c_firma:
                                    trend_df = df_gkk[["_dt", c_firma, c_puan]].copy()
                                    trend_df.columns = ["Tarih", "Firma", "Puan"]
                                    trend_df["Puan"] = pd.to_numeric(trend_df["Puan"], errors="coerce")
                                    trend_df = trend_df.dropna()
                                    if not trend_df.empty:
                                        trend_df["Ay"] = trend_df["Tarih"].dt.to_period("M").dt.to_timestamp()
                                        aylik = trend_df.groupby(["Ay", "Firma"], as_index=False)["Puan"].mean()
                                        aylik["Puan"] = aylik["Puan"].round(2)
                                        aylik["PuanMetni"] = aylik["Puan"].apply(lambda v: f"{v:g}".replace(".", ","))
                                        aylik["Aralık"] = aylik["Puan"].apply(_aralik)
                                        # Seçilen haftanın ayı (hafta iki aya yayılıyorsa ikisi de) otomatik gelir
                                        aylar = sorted(h_df["_dt"].dropna().dt.to_period("M").dt.to_timestamp().unique(), reverse=True)
                                        if len(aylar) == 0:
                                            aylar = [pd.Timestamp(hafta_secenekleri[secilen_hafta]).to_period("M").to_timestamp()]

                                        for _sira, _ay in enumerate(aylar):
                                            if _sira > 0:
                                                st.markdown('<hr style="border: none; border-top: 2px dashed #CBD5E1; margin: 1rem 0 0.8rem 0;">', unsafe_allow_html=True)
                                            ay_df = aylik[aylik["Ay"] == _ay].sort_values("Puan", ascending=False)
                                            if ay_df.empty:
                                                st.info(f"{AY_ADLARI[pd.Timestamp(_ay).month - 1]} {pd.Timestamp(_ay).year} için puanlı kayıt bulunmuyor.")
                                                continue
                                            ay_sirasi = ay_df["Firma"].tolist()
                                            ay_adi = f"{AY_ADLARI[pd.Timestamp(_ay).month - 1]} {pd.Timestamp(_ay).year}"
                                            ay_ort = f"{round(float(ay_df['Puan'].mean()), 2):g}".replace(".", ",")
                                            st.markdown(
                                                f"<div style='font-size:2rem;font-weight:900;color:#0F172A;letter-spacing:0.5px;line-height:1.2;margin-top:0.3rem'>{ay_adi}</div>"
                                                f"<div style='font-size:1.05rem;color:#475569;margin-bottom:0.4rem'>{len(ay_df)} firma — ortalama {ay_ort}</div>",
                                                unsafe_allow_html=True)

                                            ay_bar = alt.Chart(ay_df).mark_bar(cornerRadiusEnd=6).encode(
                                                x=alt.X("Puan:Q", title=None, scale=alt.Scale(domain=[0, 110]),
                                                        axis=alt.Axis(values=[0, 20, 40, 60, 80, 100])),
                                                y=alt.Y("Firma:N", sort=ay_sirasi, title=None, scale=alt.Scale(paddingInner=0.4, paddingOuter=0.15),
                                                        axis=alt.Axis(labelLimit=200, labelFontSize=13, labelFontWeight="bold", labelPadding=10)),
                                                color=alt.Color("Aralık:N", scale=alt.Scale(domain=PUAN_ARALIKLARI, range=PUAN_RENKLERI), legend=None),
                                                tooltip=[alt.Tooltip("Firma:N"), alt.Tooltip("PuanMetni:N", title="Ortalama Puan"), alt.Tooltip("Aralık:N")],
                                            )
                                            ay_yazi = alt.Chart(ay_df).mark_text(align="left", dx=5, fontSize=14, fontWeight="bold", color="#0F172A").encode(
                                                x=alt.X("Puan:Q", scale=alt.Scale(domain=[0, 110])),
                                                y=alt.Y("Firma:N", sort=ay_sirasi, scale=alt.Scale(paddingInner=0.4, paddingOuter=0.15)),
                                                text=alt.Text("PuanMetni:N"),
                                            )
                                            st.altair_chart(
                                                _tema(alt.layer(ay_bar, ay_yazi).properties(height=max(110, 46 * len(ay_df) + 40))),
                                                use_container_width=True, theme=None,
                                            )
                                    else:
                                        st.info("Aylık grafik için tarihli ve puanlı kayıt bulunmuyor.")
                                else:
                                    st.info("Aylık grafik için puan ve firma sütunları gerekli.")
                else:
                    st.info("Giriş Kalite Kontrol sekmesinde veri bulunmuyor.")

# ---------------- CNC SAHA KONTROL ----------------
if "CNC" in S:
    with S["CNC"]:
        cnc_giris, cnc_rapor, cnc_liste = st.tabs(["📝 Veri Girişi", "📊 Saha Kalite Analizleri", "⚙️ Listeler"])
        with cnc_giris:
                st.header("CNC Saha Kalite Kontrol Formu")
                if st.session_state.mesaj:
                    m_tur, m_metin = st.session_state.mesaj
                    if m_tur == "warning": st.warning(m_metin)
                    elif m_tur == "success": st.success(m_metin)
                    st.session_state.mesaj = None

                fk = st.session_state.form_key
                _pl = ["-- Seçiniz --"] + ekstra_personeller
                _pi = _pl.index(oturum["ad"]) if (oturum["rol"] != "yonetici" and oturum["ad"] in _pl) else 0
                personel = st.selectbox("Kalite Personeli", _pl, index=_pi, key=f"personel_{fk}")
                parca = st.selectbox("Parça Seçin", options=["-- Seçiniz --"] + ekstra_parcalar, index=0, key=f"parca_{fk}")
                ret_nedenleri = ["-- Seçiniz --", "OPRT. HATASI", "DÖKÜM HATASI", "TEKNİK HATA", "DİĞER"]
                ret_nedeni = st.selectbox("RET NEDENİ", ret_nedenleri, key=f"ret_nedeni_{fk}")

                op_adi, cnc_no = "", ""
                if ret_nedeni == "OPRT. HATASI":
                    op_adi = st.text_input("OPERATÖRÜN ADI", placeholder="Örn: MELİH ÇAKILLI", key=f"op_adi_{fk}")
                    cnc_no = st.text_input("CNC NO", placeholder="Örn: CNC5", key=f"cnc_no_{fk}")

                aciklama = st.text_input("RET AÇIKLAMASI", placeholder="Örn: ÖLÇÜ DÜŞÜK", key=f"aciklama_{fk}")
                yuklenen_dosyalar = st.file_uploader("📎 BELGE / FOTOĞRAF EKLE", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True, key=f"belgeler_{fk}")
                ret_miktari = st.number_input("RET ADEDİ", min_value=0, step=1, key=f"ret_miktari_{fk}")
                uretim_miktari = st.number_input("Üretim Miktarı (Adet)", min_value=0, step=1, key=f"uretim_miktari_{fk}")

                if st.button("KAYDET VE GÖNDER", use_container_width=True):
                    if personel == "-- Seçiniz --" or parca == "-- Seçiniz --" or ret_nedeni == "-- Seçiniz --":
                        st.warning("⚠️ Lütfen Kalite Personeli, Parça ve Ret Nedeni alanlarını seçiniz!")
                    else:
                        # Dosya adı: parça_tarih_retnedeni_sıra
                        _on_ad = f"{temiz_ad(parca)}_{datetime.today().strftime('%d-%m-%Y')}_{temiz_ad(ret_nedeni)}"
                        belge_linkleri = dosyalari_yukle(yuklenen_dosyalar, on_ad=_on_ad) if yuklenen_dosyalar else []
                        if belge_linkleri is None:
                            st.error("❌ Belge / fotoğraf yüklenemedi. Kayıt yapılmadı, lütfen tekrar deneyin.")
                            if st.session_state.belge_hata:
                                st.code(st.session_state.belge_hata)
                        else:
                            kayit = {
                                "personel": personel, "parca": parca, "ret_nedeni": ret_nedeni,
                                "op_adi": op_adi, "cnc_no": cnc_no, "aciklama": aciklama,
                                "ret_miktari": ret_miktari, "uretim_miktari": uretim_miktari,
                                "belge_linkleri": ", ".join(belge_linkleri) if belge_linkleri else "",
                            }
                            if veri_kaydet(kayit):
                                st.session_state.form_key += 1
                                st.session_state.mesaj = ("success", "✅ Veri Google E-Tablonuza başarıyla kaydedildi!")
                                st.rerun()
        with cnc_rapor:
            df = verileri_yukle()
            if not df.empty:
                st.metric("Toplam Saha Kaydı", f"{len(df)} Adet")
                kayit_tablosu_ve_galeri(df, [("zaman",), ("personel",), ("parça", "parca"), ("ret nedeni",), ("ret aded",)])
            else:
                st.info("Saha verisi bulunmuyor.")
        with cnc_liste:
                st.header("Personel ve Parça Listesini Yönet")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    yeni_p = st.text_input("Personel Adı Soyadı", key="yeni_p_input")
                    if st.button("Personel Ekle", key="btn_p_ekle") and yeni_p.strip():
                        if kalici_liste_ekle("PERSONEL", yeni_p.strip()):
                            st.success("✅ Personel eklendi!")
                            st.rerun()
                with col_p2:
                    yeni_parca = st.text_input("Parça Adı", key="yeni_parca_input")
                    if st.button("Parça Ekle", key="btn_parca_ekle") and yeni_parca.strip():
                        if kalici_liste_ekle("PARCA", yeni_parca.strip()):
                            st.success("✅ Parça eklendi!")
                            st.rerun()

# ---------------- ROTOR / MONTAJ / POMPA ----------------
for _kod in YENI_BIRIMLER:
    if _kod in S:
        with S[_kod]:
            genel_birim(_kod, oturum)

# ---------------- YÖNETİM ----------------
if "YONETIM" in S:
    with S["YONETIM"]:
        st.header("Yönetim")
        bolum_baslik("👥 Kullanıcılar ve Yetkiler")
        st.caption("Kullanıcı ekleme/silme/şifre değiştirme: Streamlit Cloud → Settings → Secrets. Şifreler burada gösterilmez.")
        _satirlar = []
        for _k, _u in _kullanicilar.items():
            _satirlar.append({
                "Kullanıcı Adı": _k, "Ad": _u["ad"],
                "Rol": "Kalite Yöneticisi" if _u["rol"] == "yonetici" else "Birim Personeli",
                "Yetkili Birimler": "TÜMÜ" if _u["rol"] == "yonetici" else ", ".join(BIRIMLER[b]["ad"] for b in _u["birimler"] if b in BIRIMLER),
            })
        st.dataframe(pd.DataFrame(_satirlar), use_container_width=True, hide_index=True)

        ayirici()
        bolum_baslik("📈 Birim Özeti (Toplam Kayıt)")
        _ozet = {
            "Giriş Kalite Kontrol": len(giris_kalite_yukle()),
            "CNC Saha Kontrol": len(verileri_yukle()),
        }
        for _b in YENI_BIRIMLER:
            _ozet[BIRIMLER[_b]["ad"]] = len(birim_kayitlari_yukle(_b))
        _oc = st.columns(len(_ozet))
        for _c, (_ad, _n) in zip(_oc, _ozet.items()):
            _c.metric(_ad, f"{_n}")
