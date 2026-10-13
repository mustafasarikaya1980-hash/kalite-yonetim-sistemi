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
    button[role="tab"] p, button[role="tab"] span, button[role="tab"] div {
        font-size: 1.55rem !important;
        font-weight: 900 !important;
        color: #1E3A8A !important;
    }
    button[role="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #2563EB 0%, #1E3A8A 100%) !important;
        border-color: #1E3A8A !important;
    }
    button[role="tab"][aria-selected="true"] p, button[role="tab"][aria-selected="true"] span, button[role="tab"][aria-selected="true"] div {
        color: #FFFFFF !important;
    }
    h2, h3, div[data-testid="stHeading"] h2, div[data-testid="stHeading"] h3 {
        color: #1E3A8A !important;
        font-weight: 900 !important;
        border-left: 8px solid #F59E0B;
        padding-left: 0.8rem;
    }
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

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycby9xKz14pVGDNPDkUlUsztvrOK6WEAUOmbXDWBNcpwL70lcg8QRR1AVwKNEXAEoi40P/exec"

_HEADERS = {"User-Agent": "Mozilla/5.0 (MSP Kalite Sistemi)"}

def temiz_ad(metin):
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

def giris_kalite_kaydet(gkk_veri: dict) -> bool:
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

def kayit_sil(satir_index: int) -> bool:
    """Yönetici panelinden seçilen satırı Apps Script aracılığıyla siler."""
    try:
        # CSV tablosu 0 tabanlıdır. Excel/E-Tablo başlığı 1. satırdır.
        # Gerçek satır numarası = satir_index + 2
        gercek_satir = satir_index + 2
        resp = requests.post(APPS_SCRIPT_URL, json={"islem": "sil", "satir_index": gercek_satir}, headers=_HEADERS, timeout=15)
        if resp.status_code in (200, 302):
            sonuc = resp.json()
            if sonuc.get("success"):
                giris_kalite_yukle.clear()
                return True
        return False
    except Exception:
        return False

def bolum_baslik(metin):
    st.markdown(
        f'<div style="border-left: 7px solid #2563EB; padding: 0.15rem 0 0.15rem 0.9rem; margin: 0.4rem 0 0.6rem 0; '
        f'font-size: 1.7rem; font-weight: 800; color: #0F172A;">{metin}</div>',
        unsafe_allow_html=True,
    )

def ayirici():
    st.markdown(
        '<hr style="border: none; border-top: 3px solid #CBD5E1; margin: 2rem 0 1.6rem 0;">',
        unsafe_allow_html=True,
    )

def apps_script_gonder(payload, zaman_asimi=30):
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

# Ana Sekme Yapısı
st.markdown(
    """
    <div style="background: linear-gradient(135deg, #2563EB 0%, #1E3A8A 100%); padding: 1.3rem 1.8rem; border-radius: 14px; margin-bottom: 0.8rem; box-shadow: 0 4px 14px rgba(37,99,235,0.25);">
        <h1 style="color: white; margin: 0; font-size: 1.7rem; line-height: 1.2;">🏭 MSP KALİTE YÖNETİM SİSTEMİ</h1>
        <p style="color: #DBEAFE; margin: 0.35rem 0 0 0; font-size: 0.95rem;">Saha & Giriş Kalite Kontrol Veri Girişi ve Yönetim Raporları</p>
    </div>
    """,
    unsafe_allow_html=True,
)

sekme_giris, sekme_yonetici, sekme_ayarlar = st.tabs([
    "📦 GİRİŞ KALİTE KONTROL",
    "📊 YÖNETİCİ PANELİ & KAYIT YÖNETİMİ",
    "⚙️ YÖNETİM & AYARLAR",
])

# --- 1. SEKME: GİRİŞ KALİTE KONTROL ---
with sekme_giris:
    st.markdown("### 🛡️ Giriş Kalite Kontrol Takip ve Form Entegrasyonu")
    
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
            gkk_frekans = st.selectbox("Kontrol Frekansı (%)", ["10%", "20%", "50%", "100%", "1%"], key=f"gkk_frekans_{gkk_fk}")
            gkk_onay = st.selectbox("Onay Durumu", ["KABUL", "ŞARTLI KABUL", "RED"], key=f"gkk_onay_{gkk_fk}")

        gkk_aciklama = st.text_area("Ek Açıklama / Notlar", placeholder="Açıklama...", key=f"gkk_aciklama_{gkk_fk}")

        st.markdown("#### ⭐ Tedarikçi Değerlendirme Puanları (0-100)")
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            p_paket = st.slider("Paketleme Puanı", 0, 100, 70, key=f"p_paket_{gkk_fk}")
            p_sevkiyat = st.slider("Sevkiyat Puanı", 0, 100, 70, key=f"p_sevkiyat_{gkk_fk}")
        with p_col2:
            p_kalite = st.slider("Ürün Kalitesi Puanı", 0, 100, 70, key=f"p_kalite_{gkk_fk}")
            p_etiket = st.slider("Ürün Tanıtım Etiketi", 0, 100, 70, key=f"p_etiket_{gkk_fk}")
        
        genel_puan = round((p_paket + p_sevkiyat + p_kalite + p_etiket) / 4, 2)
        st.metric("100 Üzerinden Genel Tedarikçi Puanı", f"{genel_puan}")

        if st.button("🚀 Verileri Kaydet ve E-Tabloya Gönder", use_container_width=True):
            if not gkk_urun or not gkk_firma:
                st.warning("⚠️ Lütfen Gelen Ürün / Parça Adı ve Tedarikçi Firma alanlarını doldurunuz!")
            else:
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
                    "puan_paket": p_paket,
                    "puan_sevkiyat": p_sevkiyat,
                    "puan_kalite": p_kalite,
                    "puan_etiket": p_etiket
                }
                if giris_kalite_kaydet(gkk_kayit):
                    st.session_state.form_key += 1
                    st.session_state.gkk_mesaj = "✅ Giriş Kalite Kontrol kaydı başarıyla işlendi!"
                    st.rerun()
                else:
                    st.error(f"❌ Kayıt gönderilirken hata oluştu: {st.session_state.gkk_hata}")

# --- 2. SEKME: YÖNETİCİ PANELİ & KAYIT YÖNETİMİ ---
with sekme_yonetici:
    st.header("Anlık Kalite Takip ve Kayıt Silme Paneli")
    if st.button("🔄 Verileri Yenile", key="btn_yenile_yonetici"):
        giris_kalite_yukle.clear()
        st.rerun()

    df_gkk = giris_kalite_yukle()
    if not df_gkk.empty:
        st.subheader("🗑️ Hatalı Kayıtları Yönet ve Sil")
        st.caption("Tablodan silmek istediğiniz kaydı seçip aşağıdaki sil butonuna basabilirsiniz.")
        
        secilen_satir = st.selectbox(
            "Silinecek Kaydı Seçin (Satır Numarası - Zaman - Firma)",
            options=range(len(df_gkk)),
            format_func=lambda i: f"Satır {i+1} | Zaman: {df_gkk.iloc[i].values[0]} | Firma/Ürün: {str(df_gkk.iloc[i].values[4]) if len(df_gkk.iloc[i].values) > 4 else '-'}"
        )
        
        if st.button("🔴 Seçilen Kaydı Kalıcı Olarak Sil", use_container_width=True):
            if kayit_sil(secilen_satir):
                st.success("✅ Seçilen kayıt başarıyla silindi!")
                st.rerun()
            else:
                st.error("❌ Kayıt silinirken bir hata oluştu!")

        st.markdown("---")
        st.subheader("📊 Canlı Veri Tablosu")
        st.dataframe(df_gkk, use_container_width=True)
    else:
        st.info("Giriş Kalite Kontrol sekmesinde kayıt bulunmuyor.")

# --- 3. SEKME: YÖNETİM & AYARLAR ---
with sekme_ayarlar:
    st.header("Sistem ve Liste Yönetimi")
    st.info("Bu alandan sistem parametrelerini ve dinamik listeleri yönetebilirsiniz.")
