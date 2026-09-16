# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# TARAYICI SEKMESİ BAŞLIĞI VE SİMGE
st.set_page_config(page_title="MSP KALİTE YÖNETİM SİSTEMİ", layout="wide", page_icon="🏭")

# TARAYICI OTOMATİK ÇEVİRİ ENGELİ (HATA ÖNLEYİCİ)
st.markdown("""
    <script>
        document.documentElement.setAttribute('lang', 'tr');
        document.documentElement.setAttribute('class', 'notranslate');
        document.documentElement.setAttribute('translate', 'no');
    </script>
    <meta name="google" content="notranslate" />
""", unsafe_allow_html=True)

# ==============================================================================
# 🔗 GOOGLE E-TABLO LINKI
# ==============================================================================
TABLO_LINKI = "https://docs.google.com/spreadsheets/d/1PHo0U3tXy1H7A__E0_Bn18jPZpDoHqSa77R9rr-40xM/edit?usp=sharing"

def verileri_yukle(conn):
    try:
        df = conn.read(spreadsheet=TABLO_LINKI, ttl=0)
        return df
    except Exception as e:
        return pd.DataFrame()

def veri_kaydet(conn, yeni_veri):
    try:
        df_mevcut = verileri_yukle(conn)
        yeni_df = pd.DataFrame([yeni_veri])
        df_guncel = pd.concat([df_mevcut, yeni_df], ignore_index=True)
        conn.update(spreadsheet=TABLO_LINKI, data=df_guncel)
        return True
    except Exception as e:
        st.error(f"E-Tabloya kaydedilirken hata oluştu: {e}")
        return False

# Google Sheets Bağlantısını Başlat
conn = st.connection("gsheets", type=GSheetsConnection)

# --- DİNAMİK LİSTELER ---
VARSAYILAN_AYARLAR = {
    "personeller": [
        "YURDAL BULDU (CNC)",
        "AHMET TİFTİK (MONTAJ-SON KONTROL)",
        "ENES TÜKEL (GİRİŞ KALİTE)",
        "YENİ PERSONEL (ROTOR STATOR)"
    ],
    "parcalar": [
        '6" ALT YATAK (304)', '6" ALT YATAK (316)', '6" ALT YATAK (PİK)',
        '6" ÜST YATAK (304)', '6" ÜST YATAK (316)', '6" ÜST YATAK (PİK)',
        '6" FLANŞ (304)', '6" FLANŞ (316)', '6" FLANŞ (PİK)',
        '7" ALT YATAK (304)', '7" ALT YATAK (316)', '7" ALT YATAK (PİK)',
        '7" ÜST YATAK (304)', '7" ÜST YATAK (316)', '7" ÜST YATAK (PİK)',
        '7" FLANŞ (304)', '7" FLANŞ (316)', '7" FLANŞ (PİK)',
        '8" ALT YATAK (304)', '8" ALT YATAK (316)', '8" ALT YATAK (PİK)',
        '8" ÜST YATAK (304)', '8" ÜST YATAK (316)', '8" ÜST YATAK (PİK)',
        '8" FLANŞ (304)', '8" FLANŞ (316)', '8" FLANŞ (PİK)',
        '10" ALT YATAK (304)', '10" ALT YATAK (316)', '10" ALT YATAK (PİK)',
        '10" ÜST YATAK (304)', '10" ÜST YATAK (316)', '10" ÜST YATAK (PİK)',
        '10" FLANŞ (304)', '10" FLANŞ (316)', '10" FLANŞ (PİK)'
    ]
}

if "ekstra_personeller" not in st.session_state:
    st.session_state.ekstra_personeller = []
if "ekstra_parcalar" not in st.session_state:
    st.session_state.ekstra_parcalar = []

# --- SESSION STATE DEĞERLERİ ---
if "key_personel" not in st.session_state:
    st.session_state.key_personel = "-- Seçiniz --"
if "key_parca" not in st.session_state:
    st.session_state.key_parca = "-- Seçiniz --"
if "key_ret_nedeni" not in st.session_state:
    st.session_state.key_ret_nedeni = "-- Seçiniz --"
if "key_op_adi" not in st.session_state:
    st.session_state.key_op_adi = ""
if "key_cnc_no" not in st.session_state:
    st.session_state.key_cnc_no = ""
if "key_aciklama" not in st.session_state:
    st.session_state.key_aciklama = ""
if "key_ret_miktari" not in st.session_state:
    st.session_state.key_ret_miktari = 0
if "key_uretim_miktari" not in st.session_state:
    st.session_state.key_uretim_miktari = 0
if "mesaj" not in st.session_state:
    st.session_state.mesaj = None

def kaydet_ve_sifirla():
    personel = st.session_state.key_personel
    parca = st.session_state.key_parca
    ret_nedeni = st.session_state.key_ret_nedeni
    op_adi = st.session_state.get("key_op_adi", "")
    cnc_no = st.session_state.get("key_cnc_no", "")
    aciklama = st.session_state.key_aciklama
    ret_miktari = st.session_state.key_ret_miktari
    uretim_miktari = st.session_state.key_uretim_miktari

    if personel == "-- Seçiniz --" or parca == "-- Seçiniz --" or ret_nedeni == "-- Seçiniz --":
        st.session_state.mesaj = ("warning", "⚠️ Lütfen Kalite Personeli, Parça ve Ret Nedeni alanlarını seçiniz!")
        return

    # E-Tablonuzdaki sütun isimleriyle birebir eşleşen kayıt verisi
    kayit = {
        "1.SORU:TARİH": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "2.SORU:PERSONEL": personel,
        "3.SORU: PARÇA": parca,
        "4.SORU: RETNEDENİ": ret_nedeni,
        "5.SORU: OPERATÖRADI": op_adi,
        "6.SORU: CNCNO": cnc_no,
        "7.SORU: RETAÇIKLAMASI": aciklama,
        "8.SORU: RETMİKTARI": ret_miktari,
        "9.SORU: ÜRETİMMİKTARI": uretim_miktari
    }
    
    basarili = veri_kaydet(conn, kayit)
    if basarili:
        st.session_state.key_personel = "-- Seçiniz --"
        st.session_state.key_parca = "-- Seçiniz --"
        st.session_state.key_ret_nedeni = "-- Seçiniz --"
        st.session_state.key_op_adi = ""
        st.session_state.key_cnc_no = ""
        st.session_state.key_aciklama = ""
        st.session_state.key_ret_miktari = 0
        st.session_state.key_uretim_miktari = 0
        st.session_state.mesaj = ("success", "✅ Veri Google E-Tablonuza doğrudan kaydedildi!")

st.title("🏭 MSP KALİTE YÖNETİM SİSTEMİ")

sekme_saha, sekme_yonetici, sekme_ayarlar = st.tabs([
    "📱 SAHA VERİ GİRİŞİ", 
    "📊 YÖNETİCİ PANELİ", 
    "⚙️ YÖNETİM & AYARLAR"
])

with sekme_saha:
    st.header("Kalite Kontrol Formu")
    
    if st.session_state.mesaj:
        m_tur, m_metin = st.session_state.mesaj
        if m_tur == "warning":
            st.warning(m_metin)
        elif m_tur == "success":
            st.success(m_metin)
        st.session_state.mesaj = None

    tum_personeller = VARSAYILAN_AYARLAR["personeller"] + st.session_state.ekstra_personeller
    st.selectbox("Kalite Personeli", ["-- Seçiniz --"] + tum_personeller, key="key_personel")
    
    tum_parcalar = VARSAYILAN_AYARLAR["parcalar"] + st.session_state.ekstra_parcalar
    st.selectbox("Parça Seçin", ["-- Seçiniz --"] + tum_parcalar, key="key_parca")
    
    ret_nedenleri = ["-- Seçiniz --", "OPRT. HATASI", "DÖKÜM HATASI", "TEKNİK HATA", "DİĞER"]
    ret_nedeni = st.selectbox("RET NEDENİ", ret_nedenleri, key="key_ret_nedeni")
    
    if ret_nedeni == "OPRT. HATASI":
        st.info("ℹ️ Operatör hatası seçildi. Lütfen operatör adını ve CNC'yi giriniz.")
        st.text_input("OPERATÖRÜN ADI", placeholder="Örn: MELİH ÇAKILLI", key="key_op_adi")
        st.text_input("CNC NO", placeholder="Örn: CNC5", key="key_cnc_no")
    
    st.text_input("RET AÇIKLAMASI (Manuel Detay Giriniz)", placeholder="Örn: ÖLÇÜ DÜŞÜK", key="key_aciklama")
    st.number_input("RET ADEDİ", min_value=0, step=1, key="key_ret_miktari")
    st.number_input("Üretim Miktarı (Adet)", min_value=0, step=1, key="key_uretim_miktari")
    
    st.button("KAYDET VE GÖNDER", use_container_width=True, on_click=kaydet_ve_sifirla)

with sekme_yonetici:
    st.header("Anlık Kalite Takip Ekranı (Canlı E-Tablo)")
    if st.button("🔄 Verileri Yenile"):
        st.rerun()
        
    df = verileri_yukle(conn)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Henüz tabloya kaydedilmiş veri bulunmuyor.")

with sekme_ayarlar:
    st.header("Arayüzden Personel ve Parça Ekleme")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.subheader("👤 Yeni Personel Ekle")
        y_pers = st.text_input("Personel Adı Soyadı")
        if st.button("Personel Ekle"):
            if y_pers and y_pers not in st.session_state.ekstra_personeller:
                st.session_state.ekstra_personeller.append(y_pers)
                st.success(f"'{y_pers}' eklendi!")
                st.rerun()
    with col_p2:
        st.subheader("🧩 Yeni Parça Ekle")
        y_prc = st.text_input("Parça Adı")
        if st.button("Parça Ekle"):
            if y_prc and y_prc not in st.session_state.ekstra_parcalar:
                st.session_state.ekstra_parcalar.append(y_prc)
                st.success(f"'{y_prc}' eklendi!")
                st.rerun()
