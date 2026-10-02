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
    button[data-baseweb="tab"] { font-size: 1.05rem; font-weight: 600; }
    div[data-testid="stVerticalBlockBorderWrapper"] { margin-bottom: 0.25rem; }
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, textarea { border-radius: 10px !important; }
    div[data-testid="stButton"] button { border-radius: 10px; font-weight: 600; padding: 0.6rem 1rem; }
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

# 3. Giriş Kalite Kontrol Formu
GKK_FORM_RESPONSE_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdIvt5WtIPuMWgszpd04VD4WBP7lsOGaVcdAsY1BfKRG1jPrQ/formResponse"
GKK_ENTRY_TARIH = "entry.1982855167"      
GKK_ENTRY_RAPOR = "entry.1205608639"      
GKK_ENTRY_URUN = "entry.1393152516"
GKK_ENTRY_FIRMA = "entry.1427845717"
GKK_ENTRY_IRSALIYE = "entry.1390158217"
GKK_ENTRY_ONAY = "entry.1302512463"
GKK_ENTRY_PUAN = "entry.55313535"

SABIT_EPOSTA = "veri@msp-kalite.local"

# ANA E-TABLO VE SEKME BİLGİLERİ
SPREADSHEET_ID = "1O8qGTDrwv0RRv2Qv7jeux93Y8vz4uT2pwJRQ8U1Vq8o"
SHEET_GID = "1834241278"         # Saha Verileri Sekmesi
SHEET2_GID = "1493441004"        # Ekstra Listeler Sekmesi
GKK_SHEET_GID = "1709999332"     # GÜNCEL GİRİŞ KALİTE (Form Yanıtları 6)

CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET_GID}"
CSV2_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET2_GID}"
CSV_GIRIS_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GKK_SHEET_GID}"

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwAlEBWccxzs1M_myglp-eMq_dhc8VjNejUoaVcv68Axn8ugVyImCFXlu9Y/exec"

_HEADERS = {"User-Agent": "Mozilla/5.0 (MSP Kalite Sistemi)"}

if "form_key" not in st.session_state:
    st.session_state.form_key = 0
if "mesaj" not in st.session_state:
    st.session_state.mesaj = None
if "gkk_mesaj" not in st.session_state:
    st.session_state.gkk_mesaj = None

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
    payload = {
        GKK_ENTRY_TARIH: gkk_veri["tarih"],
        GKK_ENTRY_RAPOR: gkk_veri["rapor_no"],
        GKK_ENTRY_URUN: gkk_veri["urun"],
        GKK_ENTRY_FIRMA: gkk_veri["firma"],
        GKK_ENTRY_IRSALIYE: gkk_veri["irsaliye"],
        GKK_ENTRY_ONAY: gkk_veri["onay"],
        GKK_ENTRY_PUAN: str(gkk_veri["tedarikci_puani"]),
        "emailAddress": SABIT_EPOSTA,
    }
    try:
        resp = requests.post(GKK_FORM_RESPONSE_URL, data=payload, headers=_HEADERS, timeout=15)
        if resp.status_code in (200, 302):
            giris_kalite_yukle.clear()
            return True
        return False
    except Exception:
        return False

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
        <h1 style="color: white; margin: 0; font-size: 1.7rem; line-height: 1.2;">🏭 MSP KALİTE YÖNETİM SİSTEMİ</h1>
        <p style="color: #DBEAFE; margin: 0.35rem 0 0 0; font-size: 0.95rem;">Saha & Giriş Kalite Kontrol Veri Girişi ve Yönetim Raporları</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# 4 SEKME
sekme_saha, sekme_giris, sekme_yonetici, sekme_ayarlar = st.tabs([
    "📱 SAHA VERİ GİRİŞİ",
    "📦 GİRİŞ KALİTE KONTROL",
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
    st.header("📦 Giriş Kalite Kontrol Takip Formu")
    if st.session_state.gkk_mesaj:
        st.success(st.session_state.gkk_mesaj)
        st.session_state.gkk_mesaj = None

    gkk_fk = f"gkk_{st.session_state.form_key}"
    col_gkk1, col_gkk2 = st.columns(2)
    with col_gkk1:
        # Tarih alanı varsayılan olarak 01.01.1900 yerine bugünden başlar ama takvimden 01.01.1900 seçilebilir
        gkk_tarih = st.date_input("Tarih", value=datetime(1900, 1, 1), key=f"gkk_tarih_{gkk_fk}")
        gkk_urun = st.text_input("Gelen Ürün Tipi ve Ölçüsü / İsmi", placeholder="Örn: 6\"x8\" KARBON BURÇ", key=f"gkk_urun_{gkk_fk}")
        gkk_firma = st.text_input("Tedarikçi Firma", placeholder="Örn: SIRMA", key=f"gkk_firma_{gkk_fk}")
        gkk_irsaliye = st.text_input("İrsaliye No", placeholder="Örn: EFT2026000000008", key=f"gkk_irsaliye_{gkk_fk}")

    with col_gkk2:
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            gkk_miktar = st.number_input("Gelen Ürün Adedi", min_value=0.0, step=1.0, key=f"gkk_miktar_{gkk_fk}")
        with col_m2:
            gkk_birim = st.selectbox("Birim", ["ADET", "KG", "METRE", "PAKET"], key=f"gkk_birim_{gkk_fk}")
        gkk_numune = st.number_input("Numune Adedi", min_value=0, step=1, key=f"gkk_numune_{gkk_fk}")
        gkk_red_numune = st.number_input("Red Edilen Numune Adedi", min_value=0, step=1, key=f"gkk_red_numune_{gkk_fk}")
        gkk_frekans = st.selectbox("Kontrol Frekansı (%)", ["10%", "20%", "50%", "100%", "1%"], key=f"gkk_frekans_{gkk_fk}")

    st.markdown("---")
    col_gkk3, col_gkk4 = st.columns(2)
    with col_gkk3:
        gkk_onay = st.selectbox("Onay Durumu", ["KABUL", "ŞARTLI KABUL", "RED"], key=f"gkk_onay_{gkk_fk}")
        # Rapor No, Onay Durumu ile Açıklama arasına alındı
        gkk_rapor_no = st.text_input("Rapor No", placeholder="Örn: KK1-260328", key=f"gkk_rapor_no_{gkk_fk}")
        gkk_aciklama = st.text_area("Ek Açıklama", placeholder="Açıklama...", key=f"gkk_aciklama_{gkk_fk}")

    with col_gkk4:
        st.subheader("⭐ Tedarikçi Değerlendirme Puanları (0-100)")
        p_paket = st.slider("Paketleme Puanı", 0, 100, 70, key=f"p_paket_{gkk_fk}")
        p_sevkiyat = st.slider("Sevkiyat Puanı", 0, 100, 70, key=f"p_sevkiyat_{gkk_fk}")
        p_kalite = st.slider("Ürün Kalitesi Puanı", 0, 100, 70, key=f"p_kalite_{gkk_fk}")
        p_etiket = st.slider("Ürün Tanıtım Etiketi", 0, 100, 70, key=f"p_etiket_{gkk_fk}")
        genel_puan = round((p_paket + p_sevkiyat + p_kalite + p_etiket) / 4, 2)
        st.metric("100 Üzerinden Değerlendirme", f"{genel_puan}")

    if st.button("GİRİŞ KALİTE KAYDINI KAYDET", use_container_width=True):
        if not gkk_urun or not gkk_firma:
            st.warning("⚠️ Lütfen Gelen Ürün Tipi ve Tedarikçi Firma alanlarını doldurunuz!")
        else:
            gkk_kayit = {
                "tarih": str(gkk_tarih), "rapor_no": gkk_rapor_no, "urun": gkk_urun, "firma": gkk_firma,
                "irsaliye": gkk_irsaliye, "miktar": gkk_miktar, "birim": gkk_birim,
                "numune": gkk_numune, "red_numune": gkk_red_numune, "frekans": gkk_frekans,
                "onay": gkk_onay, "rapor_no": gkk_rapor_no, "aciklama": gkk_aciklama, "tedarikci_puani": genel_puan
            }
            if giris_kalite_kaydet(gkk_kayit):
                st.session_state.form_key += 1
                st.session_state.gkk_mesaj = "✅ Giriş Kalite Kontrol kaydı başarıyla işlendi!"
                st.rerun()
            else:
                st.error("❌ Kayıt gönderilirken bir hata oluştu!")

# --- 3. SEKME: YÖNETİCİ PANELİ & ANALİZ ---
with sekme_yonetici:
    st.header("Anlık Kalite Takip ve Canlı Analiz Ekranı")
    if st.button("🔄 Verileri Yenile", key="btn_yenile_yonetici"):
        verileri_yukle.clear()
        ekstra_liste_yukle.clear()
        giris_kalite_yukle.clear()
        st.rerun()

    alt_sekme1, alt_sekme2 = st.tabs(["⚙️ SAHA KALİTE ANALİZLERİ", "📦 GİRİŞ KALİTE & TEDARİKÇİ ROL VE ANALİZLERİ"])

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
            
            c_tarih = next((cols_map[k] for k in cols_map if "tarih" in k), df_gkk.columns[0])
            c_urun = next((cols_map[k] for k in cols_map if "ürün" in k or "urun" in k), None)
            c_firma = next((cols_map[k] for k in cols_map if "firma" in k or "tedarikçi" in k or "company" in k), None)
            c_rapor = next((cols_map[k] for k in cols_map if "rapor" in k), None)
            c_onay = next((cols_map[k] for k in cols_map if "onay" in k), None)
            c_puan = next((cols_map[k] for k in cols_map if "puan" in k or "100" in k), None)

            toplam_parti = len(df_gkk)
            ortalama_puan = 0.0
            min_puan, max_puan = None, None
            min_firma, max_firma = "-", "-"
            
            if c_puan:
                puan_serisi = pd.to_numeric(df_gkk[c_puan], errors="coerce")
                if puan_serisi.notna().any():
                    ortalama_puan = round(puan_serisi.mean(), 2)
                    min_idx = puan_serisi.idxmin()
                    max_idx = puan_serisi.idxmax()
                    min_puan = puan_serisi.loc[min_idx]
                    max_puan = puan_serisi.loc[max_idx]
                    if c_firma:
                        min_firma = str(df_gkk.loc[min_idx, c_firma])
                        max_firma = str(df_gkk.loc[max_idx, c_firma])

            with st.expander("📊 Yönetim Özet Tablosu İstatistikleri (Toplam / Ortalama / En Düşük / En Yüksek)", expanded=True):
                col_st1, col_st2, col_st3, col_st4 = st.columns(4)
                col_st1.metric("TOPLAM ADET", f"{toplam_parti}")
                col_st2.metric("ORTALAMA", f"{ortalama_puan}")
                col_st3.metric("EN KÜÇÜK PUAN & FİRMA", f"{min_puan}", f"{min_firma}")
                col_st4.metric("EN BÜYÜK PUAN & FİRMA", f"{max_puan}", f"{max_firma}")

            st.markdown("---")

            col_tablo, col_grafik = st.columns([1.3, 0.7])

            with col_tablo:
                st.subheader("📅 Haftalık Bazda Resmi Yönetim Tablosu")
                
                if c_tarih:
                    df_gkk["_dt"] = pd.to_datetime(df_gkk[c_tarih], errors="coerce")
                    df_gkk["_hafta"] = df_gkk["_dt"].dt.isocalendar().week.fillna(0).astype(int)
                    
                    haftalar = sorted(df_gkk["_hafta"].unique(), reverse=True)
                    
                    for h in haftalar:
                        h_df = df_gkk[df_gkk["_hafta"] == h]
                        if h_df.empty:
                            continue
                        
                        min_t = h_df["_dt"].dt.strftime("%d.%m.%Y").min()
                        max_t = h_df["_dt"].dt.strftime("%d.%m.%Y").max()
                        
                        baslik = f"📌 {h}. Hafta ({min_t} / {max_t})" if min_t else f"📌 {h}. Hafta Raporu"
                        
                        with st.expander(baslik, expanded=True):
                            sub_df = pd.DataFrame()
                            sub_df["Tarih / Date"] = h_df[c_tarih]
                            sub_df["Gelen Ürün Tipi ve Ölçüsü"] = h_df[c_urun] if c_urun else "-"
                            sub_df["Gelen Ürün Şirket"] = h_df[c_firma] if c_firma else "-"
                            sub_df["RAPOR NO"] = h_df[c_rapor] if c_rapor else "-"
                            sub_df["Onay Durumu"] = h_df[c_onay] if c_onay else "-"
                            sub_df["100 ÜZERİNDEN DEĞERLENDİRME"] = h_df[c_puan] if c_puan else "-"
                            
                            st.dataframe(sub_df, use_container_width=True, hide_index=True)
                else:
                    yonetim_df = pd.DataFrame()
                    yonetim_df["Tarih / Date"] = df_gkk[c_tarih] if c_tarih else "-"
                    yonetim_df["Gelen Ürün Tipi ve Ölçüsü"] = df_gkk[c_urun] if c_urun else "-"
                    yonetim_df["Gelen Ürün Şirket"] = df_gkk[c_firma] if c_firma else "-"
                    yonetim_df["RAPOR NO"] = df_gkk[c_rapor] if c_rapor else "-"
                    yonetim_df["Onay Durumu"] = df_gkk[c_onay] if c_onay else "-"
                    yonetim_df["100 ÜZERİNDEN DEĞERLENDİRME"] = df_gkk[c_puan] if c_puan else "-"
                    st.dataframe(yonetim_df, use_container_width=True, hide_index=True)

            with col_grafik:
                st.subheader("📊 Tedarikçi Puan Fikstürü")
                if c_puan and c_firma:
                    grafik_df = df_gkk[[c_firma, c_puan]].copy()
                    grafik_df[c_puan] = pd.to_numeric(grafik_df[c_puan], errors="coerce")
                    grafik_df = grafik_df.dropna()
                    
                    if not grafik_df.empty:
                        puan_chart = alt.Chart(grafik_df).mark_bar(color="#2563EB", cornerRadiusEnd=6).encode(
                            x=alt.X(f"{c_puan}:Q", title="Değerlendirme Puanı (100 üzerinden)"),
                            y=alt.Y(f"{c_firma}:N", sort="-x", title="Tedarikçi Firma"),
                            tooltip=[c_firma, c_puan]
                        ).properties(height=400)
                        st.altair_chart(puan_chart, use_container_width=True)
                    else:
                        st.info("Grafik için yeterli sayısal puan bulunmuyor.")
                else:
                    st.info("Puan veya firma sütunu eksik.")
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
