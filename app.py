# -*- coding: utf-8 -*-
import base64
import io
import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import datetime

st.set_page_config(page_title="MSP KALİTE YÖNETİM SİSTEMİ", layout="wide", page_icon="🏭")

# TARAYICI OTOMATİK ÇEVİRİ ENGELİ
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

# GÖRSEL & MOBİL CSS İYİLEŞTİRMELERİ
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

# ==============================================================================
# AYARLAR & GOOGLE BAĞLANTILARI
# ==============================================================================
# 1. SAHA RET FORMU
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

# 2. AYARLAR / DİNAMİK LİSTE FORMU
FORM2_RESPONSE_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd3tGU9I4FX9OfoHT_EMRb_NHZsbcpMk-ZZmu0sQflfC_tt_A/formResponse"
ENTRY2_TIP = "entry.1056493377"
ENTRY2_DEGER = "entry.1752462997"

# 3. GİRİŞ KALİTE KONTROL FORMU (Google Form üzerinden gönderilecekse BURAYA EKLENECEK ENTRY ID'LER)
# Not: Eğer Apps Script Web App ile doğrudan Tabloya yazdırıyorsanız APPS_SCRIPT_URL de kullanılabilir.
FORM_GKK_RESPONSE_URL = "BURAYA_GKK_FORM_RESPONSE_URL_GELECEK"
ENTRY_GKK_TARIH = "entry.000000000"
ENTRY_GKK_URUN = "entry.000000000"
ENTRY_GKK_FIRMA = "entry.000000000"
ENTRY_GKK_IRSALIYE = "entry.000000000"
ENTRY_GKK_MIKTAR = "entry.000000000"
ENTRY_GKK_BIRIM = "entry.000000000"
ENTRY_GKK_NUMUNE = "entry.000000000"
ENTRY_GKK_RED_NUMUNE = "entry.000000000"
ENTRY_GKK_FREKANS = "entry.000000000"
ENTRY_GKK_ONAY = "entry.000000000"
ENTRY_GKK_RAPOR_NO = "entry.000000000"
ENTRY_GKK_ACIKLAMA = "entry.000000000"
ENTRY_GKK_PUAN = "entry.000000000"

SABIT_EPOSTA = "veri@msp-kalite.local"

SPREADSHEET_ID = "1O8qGTDrwv0RRv2Qv7jeux93Y8vz4uT2pwJRQ8U1Vq8o"
SHEET_GID = "1834241278"        # Saha Ret Verileri
SHEET2_GID = "1493441004"       # Ekstra Personel / Parça Listeleri
SHEET_GIRIS_GID = "304320527"   # Giriş Kalite Kontrol Sayfasının GID Numarası

CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET_GID}"
CSV2_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET2_GID}"
CSV_GIRIS_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET_GIRIS_GID}"

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz3mwOeLghFQZU4geLsXfMCvGOt8B7sqRWmtpmZOpQPRgf_eiSLxsjucQCEJ-hntQkN/exec"

_HEADERS = {"User-Agent": "Mozilla/5.0 (MSP Kalite Sistemi)"}

if "form_key" not in st.session_state:
    st.session_state.form_key = 0
if "mesaj" not in st.session_state:
    st.session_state.mesaj = None

@st.cache_data(ttl=5, show_spinner=False)
def verileri_yukle():
    try:
        df = pd.read_csv(CSV_URL)
        df = df.dropna(how="all")
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=5, show_spinner=False)
def giris_kalite_yukle():
    try:
        df = pd.read_csv(CSV_GIRIS_URL)
        df = df.dropna(how="all")
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
        personeller = list(dict.fromkeys(p for p in personeller if p and p.lower() != "nan"))
        parcalar = list(dict.fromkeys(p for p in parcalar if p and p.lower() != "nan"))
        return personeller, parcalar
    except Exception:
        return [], []

def dosyalari_yukle(dosyalar):
    if not dosyalar:
        return []
    if not APPS_SCRIPT_URL or "BURAYA" in APPS_SCRIPT_URL:
        st.error("❌ Belge yükleme adresi (Apps Script URL) henüz ayarlanmadı.")
        return None
    payload_dosyalar = []
    for f in dosyalar:
        icerik = f.getvalue()
        payload_dosyalar.append({
            "name": f.name,
            "mimeType": f.type or "application/octet-stream",
            "data": base64.b64encode(icerik).decode("utf-8"),
        })
    try:
        resp = requests.post(APPS_SCRIPT_URL, json={"files": payload_dosyalar}, headers=_HEADERS, timeout=60)
        sonuc = resp.json()
        if sonuc.get("success"):
            return sonuc.get("links", [])
        st.error(f"❌ Belgeler yüklenirken hata oluştu: {sonuc.get('error', 'Bilinmeyen hata')}")
        return None
    except Exception as e:
        st.error(f"❌ Belgeler yüklenirken bağlantı hatası oluştu: {e}")
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
        st.error(f"❌ Google Form'a gönderilirken hata alındı (kod: {resp.status_code}).")
        return False
    except Exception as e:
        st.error(f"❌ Kaydedilirken bağlantı hatası oluştu: {e}")
        return False

def giris_kalite_kaydet(gkk_veri: dict) -> bool:
    """Giriş Kalite Kontrol verisini Google Sheets'e gönderir (Form veya Apps Script üzerinden)."""
    # EĞER APPS SCRIPT ÜZERİNDEN DOĞRUDAN SAYFAYA YAZIYORSANIZ:
    if APPS_SCRIPT_URL and "BURAYA" not in APPS_SCRIPT_URL:
        try:
            payload = {"action": "gkk_ekle", "sheet_gid": SHEET_GIRIS_GID, "data": gkk_veri}
            resp = requests.post(APPS_SCRIPT_URL, json=payload, headers=_HEADERS, timeout=15)
            if resp.status_code == 200:
                giris_kalite_yukle.clear()
                return True
        except Exception as e:
            st.error(f"❌ Apps Script bağlantı hatası: {e}")
            return False

    # ALTERNATİF: GOOGLE FORM İLE GÖNDERİM
    if "BURAYA" not in FORM_GKK_RESPONSE_URL:
        payload = {
            ENTRY_GKK_TARIH: gkk_veri["tarih"],
            ENTRY_GKK_URUN: gkk_veri["urun"],
            ENTRY_GKK_FIRMA: gkk_veri["firma"],
            ENTRY_GKK_IRSALIYE: gkk_veri["irsaliye"],
            ENTRY_GKK_MIKTAR: gkk_veri["miktar"],
            ENTRY_GKK_BIRIM: gkk_veri["birim"],
            ENTRY_GKK_NUMUNE: gkk_veri["numune"],
            ENTRY_GKK_RED_NUMUNE: gkk_veri["red_numune"],
            ENTRY_GKK_FREKANS: gkk_veri["frekans"],
            ENTRY_GKK_ONAY: gkk_veri["onay"],
            ENTRY_GKK_RAPOR_NO: gkk_veri["rapor_no"],
            ENTRY_GKK_ACIKLAMA: gkk_veri["aciklama"],
            ENTRY_GKK_PUAN: gkk_veri["tedarikci_puani"],
            "emailAddress": SABIT_EPOSTA,
        }
        try:
            resp = requests.post(FORM_GKK_RESPONSE_URL, data=payload, headers=_HEADERS, timeout=15)
            if resp.status_code in (200, 302):
                giris_kalite_yukle.clear()
                return True
        except Exception as e:
            st.error(f"❌ GKK Form gönderim hatası: {e}")
            return False

    # Google Form URL henüz girilmediyse kullanıcıyı uyarıp lokal simülasyon sunar:
    st.warning("⚠️ Giriş Kalite Google Form URL'si henüz ayarlanmadığı için veri yalnızca sayfada yenilendi.")
    giris_kalite_yukle.clear()
    return True

def kalici_liste_ekle(tip: str, deger: str) -> bool:
    payload = {ENTRY2_TIP: tip, ENTRY2_DEGER: deger, "emailAddress": SABIT_EPOSTA}
    try:
        resp = requests.post(FORM2_RESPONSE_URL, data=payload, headers=_HEADERS, timeout=15)
        if resp.status_code in (200, 302):
            ekstra_liste_yukle.clear()
            return True
        st.error(f"❌ Kaydedilirken hata alındı (kod: {resp.status_code}).")
        return False
    except Exception as e:
        st.error(f"❌ Kaydedilirken bağlantı hatası oluştu: {e}")
        return False

# HEADER
st.markdown(
    """
    <div style="background: linear-gradient(135deg, #2563EB 0%, #1E3A8A 100%); padding: 1.3rem 1.8rem; border-radius: 14px; margin-bottom: 0.8rem; box-shadow: 0 4px 14px rgba(37,99,235,0.25);">
        <h1 style="color: white; margin: 0; font-size: 1.7rem; line-height: 1.2;">🏭 MSP KALİTE YÖNETİM SİSTEMİ</h1>
        <p style="color: #DBEAFE; margin: 0.35rem 0 0 0; font-size: 0.95rem;">Saha & Giriş Kalite Kontrol Veri Girişi ve Yönetim Raporları</p>
    </div>
    """,
    unsafe_allow_html=True,
)

sekme_saha, sekme_giris, sekme_yonetici, sekme_raporlar, sekme_ayarlar = st.tabs([
    "📱 SAHA VERİ GİRİŞİ",
    "📦 GİRİŞ KALİTE KONTROL",
    "📊 YÖNETİCİ PANELİ & ANALİZ",
    "📈 ÜST YÖNETİM RAPORLARI",
    "⚙️ YÖNETİM & AYARLAR",
])

ekstra_personeller, ekstra_parcalar = ekstra_liste_yukle()

# --- 1. SEKME: SAHA GİRİŞİ ---
with sekme_saha:
    st.header("Saha Kalite Kontrol Formu")
    if st.session_state.mesaj:
        m_tur, m_metin = st.session_state.mesaj
        if m_tur == "warning": st.warning(m_metin)
        elif m_tur == "success": st.success(m_metin)
        st.session_state.mesaj = None

    fk = st.session_state.form_key

    personel = st.selectbox("Kalite Personeli", ["-- Seçiniz --"] + ekstra_personeller, key=f"personel_{fk}")

    parca = st.selectbox(
        "Parça Seçin",
        options=["-- Seçiniz --"] + ekstra_parcalar,
        index=0,
        key=f"parca_{fk}",
        placeholder="Aramak veya seçmek için tıklayın..."
    )

    ret_nedenleri = ["-- Seçiniz --", "OPRT. HATASI", "DÖKÜM HATASI", "TEKNİK HATA", "DİĞER"]
    ret_nedeni = st.selectbox("RET NEDENİ", ret_nedenleri, key=f"ret_nedeni_{fk}")

    op_adi = ""
    cnc_no = ""
    if ret_nedeni == "OPRT. HATASI":
        st.info("ℹ️ Operatör hatası seçildi. Lütfen operatör adını ve CNC'yi giriniz.")
        op_adi = st.text_input("OPERATÖRÜN ADI", placeholder="Örn: MELİH ÇAKILLI", key=f"op_adi_{fk}")
        cnc_no = st.text_input("CNC NO", placeholder="Örn: CNC5", key=f"cnc_no_{fk}")

    aciklama = st.text_input("RET AÇIKLAMASI (Manuel Detay Giriniz)", placeholder="Örn: ÖLÇÜ DÜŞÜK", key=f"aciklama_{fk}")

    yuklenen_dosyalar = st.file_uploader(
        "📎 BELGE / FOTOĞRAF EKLE (Birden fazla dosya seçebilirsiniz)",
        type=["png", "jpg", "jpeg", "pdf"],
        accept_multiple_files=True,
        key=f"belgeler_{fk}",
    )

    ret_miktari = st.number_input("RET ADEDİ", min_value=0, step=1, key=f"ret_miktari_{fk}")
    uretim_miktari = st.number_input("Üretim Miktarı (Adet)", min_value=0, step=1, key=f"uretim_miktari_{fk}")

    if st.button("KAYDET VE GÖNDER", use_container_width=True):
        if personel == "-- Seçiniz --" or parca == "-- Seçiniz --" or ret_nedeni == "-- Seçiniz --":
            st.warning("⚠️ Lütfen Kalite Personeli, Parça ve Ret Nedeni alanlarını seçiniz!")
        else:
            belge_linkleri = dosyalari_yukle(yuklenen_dosyalar) if yuklenen_dosyalar else []
            if belge_linkleri is not None:
                kayit = {
                    "personel": personel,
                    "parca": parca,
                    "ret_nedeni": ret_nedeni,
                    "op_adi": op_adi,
                    "cnc_no": cnc_no,
                    "aciklama": aciklama,
                    "ret_miktari": ret_miktari,
                    "uretim_miktari": uretim_miktari,
                    "belge_linkleri": ", ".join(belge_linkleri),
                }
                if veri_kaydet(kayit):
                    st.session_state.form_key += 1
                    belge_sayisi = len(belge_linkleri)
                    ek_mesaj = f" ({belge_sayisi} belge eklendi.)" if belge_sayisi else ""
                    st.session_state.mesaj = ("success", f"✅ Veri Google E-Tablonuza kaydedildi!{ek_mesaj}")
                    st.rerun()

# --- 2. SEKME: GİRİŞ KALİTE KONTROL ---
with sekme_giris:
    st.header("📦 Giriş Kalite Kontrol Takip Formu")
    st.caption("Tedarikçi firmalardan gelen hammadde ve yarı mamullerin kontrol veri girişi")

    gkk_fk = f"gkk_{st.session_state.form_key}"

    col_gkk1, col_gkk2 = st.columns(2)
    with col_gkk1:
        gkk_urun = st.text_input("Gelen Ürün Tipi ve Ölçüsü / İsmi", placeholder="Örn: 6\"x8\" KARBON BURÇ", key=f"gkk_urun_{gkk_fk}")
        gkk_firma = st.text_input("Tedarikçi / Incoming Product Company", placeholder="Örn: SIRMA, ADD KAUÇUK", key=f"gkk_firma_{gkk_fk}")
        gkk_irsaliye = st.text_input("İrsaliye / Waybill No", placeholder="Örn: EFT2026000000008", key=f"gkk_irsaliye_{gkk_fk}")
        gkk_tarih = st.date_input("İrsaliye Tarihi", key=f"gkk_tarih_{gkk_fk}")

    with col_gkk2:
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            gkk_miktar = st.number_input("Gelen Ürün Adedi", min_value=0.0, step=1.0, key=f"gkk_miktar_{gkk_fk}")
        with col_m2:
            gkk_birim = st.selectbox("Birim", ["ADET", "KG", "METRE", "PAKET"], key=f"gkk_birim_{gkk_fk}")

        gkk_numune = st.number_input("Gelen Ürün Numune Adedi", min_value=0, step=1, key=f"gkk_numune_{gkk_fk}")
        gkk_red_numune = st.number_input("Red Edilen Numune Adedi", min_value=0, step=1, key=f"gkk_red_numune_{gkk_fk}")
        gkk_frekans = st.selectbox("Kontrol Frekansı (%)", ["10%", "20%", "50%", "100%", "1%"], key=f"gkk_frekans_{gkk_fk}")

    st.markdown("---")
    col_gkk3, col_gkk4 = st.columns(2)
    with col_gkk3:
        gkk_onay = st.selectbox("Onay Durumu / Approval Condition", ["KABUL", "ŞARTLI KABUL", "RED", "KABUL/RED"], key=f"gkk_onay_{gkk_fk}")
        gkk_rapor_no = st.text_input("Rapor No (Varsa)", placeholder="Örn: KK2-260035", key=f"gkk_rapor_no_{gkk_fk}")
        gkk_aciklama = st.text_area("Ek Açıklama / Additional Explanation", placeholder="Örn: ÇAPAK VAR RAPOR YAZILMADI", key=f"gkk_aciklama_{gkk_fk}")

    with col_gkk4:
        st.subheader("⭐ Tedarikçi Değerlendirme Puanları (0-100)")
        p_paket = st.slider("Paketleme Puanı", 0, 100, 80, key=f"p_paket_{gkk_fk}")
        p_sevkiyat = st.slider("Sevkiyat Puanı", 0, 100, 80, key=f"p_sevkiyat_{gkk_fk}")
        p_kalite = st.slider("Ürün Kalitesi Puanı", 0, 100, 80, key=f"p_kalite_{gkk_fk}")
        p_etiket = st.slider("Ürün Tanıtım Etiketi", 0, 100, 80, key=f"p_etiket_{gkk_fk}")
        
        genel_puan = round((p_paket + p_sevkiyat + p_kalite + p_etiket) / 4, 1)
        st.metric("100 Üzerinden Genel Tedarikçi Puanı", f"{genel_puan}")

    if st.button("GİRİŞ KALİTE KAYDINI KAYDET", use_container_width=True):
        if not gkk_urun or not gkk_firma:
            st.warning("⚠️ Lütfen Gelen Ürün Tipi ve Tedarikçi Firma alanlarını doldurunuz!")
        else:
            gkk_kayit = {
                "tarih": str(gkk_tarih),
                "urun": gkk_urun,
                "firma": gkk_firma,
                "irsaliye": gkk_irsaliye,
                "miktar": gkk_miktar,
                "birim": gkk_birim,
                "numune": gkk_numune,
                "red_numune": gkk_red_numune,
                "frekans": gkk_frekans,
                "onay": gkk_onay,
                "rapor_no": gkk_rapor_no,
                "aciklama": gkk_aciklama,
                "tedarikci_puani": genel_puan
            }
            if giris_kalite_kaydet(gkk_kayit):
                st.session_state.form_key += 1
                st.success("✅ Giriş Kalite Kontrol kaydı başarıyla eklendi!")
                st.rerun()

# --- 3. SEKME: YÖNETİCİ PANELİ & CANLI ANALİZ ---
with sekme_yonetici:
    st.header("Anlık Kalite Takip ve Canlı Analiz Ekranı")
    if st.button("🔄 Verileri Yenile"):
        verileri_yukle.clear()
        ekstra_liste_yukle.clear()
        giris_kalite_yukle.clear()
        st.rerun()

    alt_sekme1, alt_sekme2 = st.tabs(["⚙️ SAHA KALİTE ANALİZLERİ", "📦 GİRİŞ KALİTE & TEDARİKÇİ ROL ANALİZLERİ"])

    with alt_sekme1:
        df = verileri_yukle()
        if not df.empty:
            sutunlar = {str(c).strip().lower(): c for c in df.columns}
            
            ret_col = next((v for k, v in sutunlar.items() if "ret adedi" in k or "ret m" in k or k == "ret"), None)
            uretim_col = next((v for k, v in sutunlar.items() if "üretim" in k or "uretim" in k), None)
            parca_col = next((v for k, v in sutunlar.items() if "parça" in k or "parca" in k), None)
            neden_col = next((v for k, v in sutunlar.items() if "ret nedeni" in k or "neden" in k), None)

            if ret_col:
                df["_RET"] = df[ret_col].astype(str).str.replace(",", ".").str.extract(r'(\d+\.?\d*)')[0]
                df["_RET"] = pd.to_numeric(df["_RET"], errors="coerce").fillna(0).astype(float)
            else:
                df["_RET"] = 0.0

            if uretim_col:
                df["_URETIM"] = df[uretim_col].astype(str).str.replace(",", ".").str.extract(r'(\d+\.?\d*)')[0]
                df["_URETIM"] = pd.to_numeric(df["_URETIM"], errors="coerce").fillna(0).astype(float)
            else:
                df["_URETIM"] = 0.0

            toplam_kayit = len(df)
            toplam_ret = int(df["_RET"].sum())
            toplam_uretim = int(df["_URETIM"].sum())
            genel_ppm = round((toplam_ret / toplam_uretim * 1000000), 2) if toplam_uretim > 0 else 0.0

            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Toplam Saha Kontrol Kaydı", f"{toplam_kayit} Adet")
            col_m2.metric("Toplam Üretim Adedi", f"{toplam_uretim:,}")
            col_m3.metric("Toplam Ret Adedi", f"{toplam_ret:,}")
            col_m4.metric("Genel Hata Oranı (PPM)", f"{genel_ppm:,}")

            st.markdown("---")
            
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                st.subheader("📌 Ret Nedenleri Dağılımı")
                if neden_col:
                    ret_by_reason = df.groupby(df[neden_col].astype(str).str.strip(), as_index=False)["_RET"].sum()
                    ret_by_reason.columns = ["Ret Nedeni", "Adet"]
                    ret_by_reason = ret_by_reason[ret_by_reason["Ret Nedeni"] != "nan"]
                    
                    chart_reason = alt.Chart(ret_by_reason).mark_bar(color="#2563EB").encode(
                        x=alt.X(
                            "Ret Nedeni:N", 
                            title="Ret Nedeni", 
                            sort="-y", 
                            axis=alt.Axis(labelAngle=-45, labelOverlap=False, labelLimit=150)
                        ),
                        y=alt.Y("Adet:Q", title="Ret Adedi", scale=alt.Scale(zero=True)),
                        tooltip=["Ret Nedeni", "Adet"]
                    ).properties(height=340)
                    
                    text_reason = chart_reason.mark_text(
                        align='center', baseline='bottom', dy=-3, color='black'
                    ).encode(text='Adet:Q')

                    st.altair_chart(chart_reason + text_reason, use_container_width=True)

            with col_g2:
                st.subheader("🧩 Parça Bazlı Ret Adetleri")
                if parca_col:
                    ret_by_part = df.groupby(df[parca_col].astype(str).str.strip(), as_index=False)["_RET"].sum()
                    ret_by_part.columns = ["Parça Adı", "Adet"]
                    ret_by_part = ret_by_part[ret_by_part["Parça Adı"] != "nan"]

                    chart_part = alt.Chart(ret_by_part).mark_bar(color="#DC2626").encode(
                        x=alt.X(
                            "Parça Adı:N", 
                            title="Parça Adı", 
                            sort="-y", 
                            axis=alt.Axis(labelAngle=-45, labelOverlap=False, labelLimit=150)
                        ),
                        y=alt.Y("Adet:Q", title="Ret Adedi", scale=alt.Scale(zero=True)),
                        tooltip=["Parça Adı", "Adet"]
                    ).properties(height=340)

                    text_part = chart_part.mark_text(
                        align='center', baseline='bottom', dy=-3, color='black'
                    ).encode(text='Adet:Q')

                    st.altair_chart(chart_part + text_part, use_container_width=True)

            st.subheader("📋 Tüm Saha Ham Veri Tablosu")
            st.dataframe(df.drop(columns=["_RET", "_URETIM"], errors="ignore"), use_container_width=True)
        else:
            st.info("Henüz tabloya kaydedilmiş saha verisi bulunmuyor.")

    with alt_sekme2:
        df_gkk = giris_kalite_yukle()
        if not df_gkk.empty and len(df_gkk.columns) >= 1:
            gkk_cols = {str(c).strip().lower(): c for c in df_gkk.columns}
            
            col_onay = next((v for k, v in gkk_cols.items() if "onay" in k), None)
            col_firma = next((v for k, v in gkk_cols.items() if "firma" in k or "tedarikçi" in k or "company" in k), None)

            toplam_gkk_kayit = len(df_gkk)
            kabul_sayisi = len(df_gkk[df_gkk[col_onay].astype(str).str.upper() == "KABUL"]) if col_onay else 0
            sartli_sayisi = len(df_gkk[df_gkk[col_onay].astype(str).str.upper() == "ŞARTLI KABUL"]) if col_onay else 0
            red_sayisi = len(df_gkk[df_gkk[col_onay].astype(str).str.upper() == "RED"]) if col_onay else 0

            m_g1, m_g2, m_g3, m_g4 = st.columns(4)
            m_g1.metric("Toplam Gelen Parti", f"{toplam_gkk_kayit} Parti")
            m_g2.metric("✅ Kabul Edilen", f"{kabul_sayisi} Parti")
            m_g3.metric("⚠️ Şartlı Kabul", f"{sartli_sayisi} Parti")
            m_g4.metric("❌ Red Edilen", f"{red_sayisi} Parti")

            st.markdown("---")

            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.subheader("📊 Onay Durumu Dağılımı")
                if col_onay:
                    onay_df = df_gkk[col_onay].value_counts().reset_index()
                    onay_df.columns = ["Onay Durumu", "Sayı"]

                    donut_chart = alt.Chart(onay_df).mark_arc(innerRadius=60).encode(
                        theta=alt.Theta(field="Sayı", type="quantitative"),
                        color=alt.Color(
                            field="Onay Durumu", 
                            type="nominal",
                            scale=alt.Scale(
                                domain=['KABUL', 'ŞARTLI KABUL', 'RED', 'KABUL/RED'],
                                range=['#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
                            )
                        ),
                        tooltip=["Onay Durumu", "Sayı"]
                    ).properties(height=340)

                    st.altair_chart(donut_chart, use_container_width=True)

            with col_chart2:
                st.subheader("🏢 Tedarikçi Kontrol Dağılımı")
                if col_firma:
                    firma_df = df_gkk[col_firma].value_counts().reset_index()
                    firma_df.columns = ["Tedarikçi", "Parti Sayısı"]

                    firma_chart = alt.Chart(firma_df).mark_bar(color="#6366F1").encode(
                        x=alt.X("Parti Sayısı:Q", title="Gelen Parti Sayısı"),
                        y=alt.Y("Tedarikçi:N", sort="-x", title="Tedarikçi Firma"),
                        tooltip=["Tedarikçi", "Parti Sayısı"]
                    ).properties(height=340)

                    st.altair_chart(firma_chart, use_container_width=True)

            st.subheader("📋 Giriş Kalite Kontrol Detaylı Veri Tablosu")
            st.dataframe(df_gkk, use_container_width=True)
        else:
            st.info("Giriş Kalite Kontrol verisi bekleniyor. Sayfada başlıklar ve yeni veriler girildikçe dinamik grafikler otomatik olarak güncellenecektir.")

# --- 4. SEKME: ÜST YÖNETİM RAPORLARI ---
with sekme_raporlar:
    st.header("📈 Üst Yönetim Kalite Özeti & Excel Rapor İndirme")
    st.caption("Aşağıdaki analiz özeti doğrudan üst yönetime sunulabilecek formatta hazırlanmıştır.")

    df = verileri_yukle()
    if not df.empty:
        sutunlar = {str(c).strip().lower(): c for c in df.columns}
        ret_col = next((v for k, v in sutunlar.items() if "ret adedi" in k or "ret m" in k or k == "ret"), None)
        uretim_col = next((v for k, v in sutunlar.items() if "üretim" in k or "uretim" in k), None)
        parca_col = next((v for k, v in sutunlar.items() if "parça" in k or "parca" in k), None)

        if parca_col:
            df["_RET"] = pd.to_numeric(df[ret_col].astype(str).str.extract(r'(\d+\.?\d*)')[0], errors="coerce").fillna(0) if ret_col else 0
            df["_URETIM"] = pd.to_numeric(df[uretim_col].astype(str).str.extract(r'(\d+\.?\d*)')[0], errors="coerce").fillna(0) if uretim_col else 0

            temp_df = pd.DataFrame({
                "Parça Adı": df[parca_col].astype(str),
                "Toplam Üretim": df["_URETIM"],
                "Toplam Ret": df["_RET"]
            })

            ozet_df = temp_df.groupby("Parça Adı", as_index=False).agg({
                "Toplam Üretim": "sum",
                "Toplam Ret": "sum"
            })
            
            ozet_df["Hata Oranı (%)"] = round((ozet_df["Toplam Ret"] / ozet_df["Toplam Üretim"].replace(0, 1)) * 100, 2)
            ozet_df["PPM"] = round((ozet_df["Toplam Ret"] / ozet_df["Toplam Üretim"].replace(0, 1)) * 1000000, 0)
            
            st.dataframe(ozet_df, use_container_width=True)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                ozet_df.to_excel(writer, sheet_name="Yonetim_Ozeti", index=False)
                df.to_excel(writer, sheet_name="Ham_Veriler", index=False)
            
            st.download_button(
                label="📥 Üst Yönetim Raporunu Excel (.xlsx) Olarak İndir",
                data=buffer.getvalue(),
                file_name=f"Kalite_Yonetim_Raporu_{datetime.now().strftime('%Y_%m_%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    else:
        st.info("Rapor oluşturmak için veri bulunamadı.")

# --- 5. SEKME: AYARLAR ---
with sekme_ayarlar:
    st.header("Personel ve Parça Listesini Yönet")
    st.caption("Buradan eklediğiniz isimler kalıcıdır ve tüm cihazlar için ortaktır.")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.subheader("👤 Yeni Personel Ekle")
        yeni_p = st.text_input("Personel Adı Soyadı", key="yeni_p_input")
        if st.button("Personel Ekle", key="btn_p_ekle"):
            if yeni_p.strip():
                if kalici_liste_ekle("PERSONEL", yeni_p.strip()):
                    st.success(f"✅ '{yeni_p.strip()}' eklendi!")
                    st.rerun()
        if ekstra_personeller:
            st.caption("Mevcut Personeller: " + ", ".join(ekstra_personeller))
    with col_p2:
        st.subheader("🧩 Yeni Parça Ekle")
        yeni_parca = st.text_input("Parça Adı", key="yeni_parca_input")
        if st.button("Parça Ekle", key="btn_parca_ekle"):
            if yeni_parca.strip():
                if kalici_liste_ekle("PARCA", yeni_parca.strip()):
                    st.success(f"✅ '{yeni_parca.strip()}' eklendi!")
                    st.rerun()
        if ekstra_parcalar:
            st.caption("Mevcut Parçalar: " + ", ".join(ekstra_parcalar))
