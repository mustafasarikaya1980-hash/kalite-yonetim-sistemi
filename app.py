# -*- coding: utf-8 -*-
import base64
import os
import re
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
    try:
        resp = requests.post(APPS_SCRIPT_URL, json={"files": payload_dosyalar}, headers=_HEADERS, timeout=60)
        sonuc = resp.json()
        return sonuc.get("links", []) if sonuc.get("success") else None
    except Exception:
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

st.markdown(
    """
    <div style="background: linear-gradient(135deg, #2563EB 0%, #1E3A8A 100%); padding: 1.3rem 1.8rem; border-radius: 14px; margin-bottom: 0.8rem; box-shadow: 0 4px 14px rgba(37,99,235,0.25);">
        <h1 style="color: white; margin: 0; font-size: 2.3rem; line-height: 1.2;">🏭 MSP KALİTE YÖNETİM SİSTEMİ</h1>
        <p style="color: #DBEAFE; margin: 0.4rem 0 0 0; font-size: 1.15rem;">Saha & Giriş Kalite Kontrol Veri Girişi ve Yönetim Raporları</p>
    </div>
    """,
    unsafe_allow_html=True,
)

sekme_giris, sekme_saha, sekme_yonetici, sekme_ayarlar = st.tabs([
    "📦 GİRİŞ KALİTE KONTROL",
    "📱 SAHA VERİ GİRİŞİ",
    "📊 YÖNETİCİ PANELİ & ANALİZ",
    "⚙️ YÖNETİM & AYARLAR",
])

ekstra_personeller, ekstra_parcalar = ekstra_liste_yukle()

# --- 1. SEKME ---
with sekme_saha:
    st.header("Saha Kalite Kontrol Formu")
    if st.session_state.mesaj:
        m_tur, m_metin = st.session_state.mesaj
        if m_tur == "warning": st.warning(m_metin)
        elif m_tur == "success": st.success(m_metin)
        st.session_state.mesaj = None

    fk = st.session_state.form_key
    personel = st.selectbox("Kalite Personeli", ["-- Seçiniz --"] + ekstra_personeller, key=f"personel_{fk}")
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
            belge_linkleri = dosyalari_yukle(yuklenen_dosyalar) if yuklenen_dosyalar else []
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

# --- 2. SEKME ---
with sekme_giris:
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
                else:
                    st.error("❌ Kayıt gönderilirken bir hata oluştu!")
                    if st.session_state.gkk_hata:
                        st.code(st.session_state.gkk_hata)

# --- 3. SEKME: YÖNETİCİ PANELİ & ANALİZ ---
with sekme_yonetici:
    st.header("Anlık Kalite Takip ve Canlı Analiz Ekranı")
    if st.button("🔄 Verileri Yenile", key="btn_yenile_yonetici"):
        verileri_yukle.clear()
        ekstra_liste_yukle.clear()
        giris_kalite_yukle.clear()
        st.rerun()

    alt_sekme1, alt_sekme2 = st.tabs(["⚙️ SAHA KALİTE ANALİZLERİ", "📦 GİRİŞ KALİTE KONTROL TAKİP VE SATINALMA DEĞERLENDİRME ANALİZ"])

    with alt_sekme1:
        df = verileri_yukle()
        if not df.empty:
            st.metric("Toplam Saha Kaydı", f"{len(df)} Adet")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Saha verisi bulunmuyor.")

    with alt_sekme2:
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

# --- 4. SEKME: YÖNETİM & AYARLAR ---
with sekme_ayarlar:
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
