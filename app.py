# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
import os

# TARAYICI SEKMESİ BAŞLIĞI
st.set_page_config(page_title="MSP KALİTE YÖNETİM SİSTEMİ", layout="wide", page_icon="🏭")

# Tarayıcı Otomatik Çeviri Engeli
st.markdown("""
    <html lang="tr" class="notranslate" translate="no">
    <head>
        <meta name="google" content="notranslate" />
    </head>
    </html>
""", unsafe_allow_html=True)

# Veri ve Fotoğraf Depolama Klasörleri
VERI_DOSYASI = "kalite_onetim_sistemi.csv"
FOTO_KLASORU = "yuklenen_fotograflar"

if not os.path.exists(FOTO_KLASORU):
    os.makedirs(FOTO_KLASORU)

def verileri_yukle():
    try:
        return pd.read_csv(VERI_DOSYASI, encoding="utf-8-sig")
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "Tarih", "Personel", "Parca", "RetNedeni", 
            "OperatorAdi", "CncNo", "RetAciklamasi", 
            "RetMiktari", "UretimMiktari", "FotografYolu"
        ])

def veri_kaydet(yeni_veri):
    df = verileri_yukle()
    df = pd.concat([df, pd.DataFrame([yeni_veri])], ignore_index=True)
    df.to_csv(VERI_DOSYASI, index=False, encoding="utf-8-sig")

# --- SESSION STATE BAŞLANGIÇ DEĞERLERİ ---
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
if "foto_id" not in st.session_state:
    st.session_state.foto_id = 0
if "mesaj" not in st.session_state:
    st.session_state.mesaj = None

# --- BUTONA BASILDIĞINDA ÇALIŞACAK SIFIRLAMA VE KAYIT FONKSİYONU ---
def kaydet_ve_sifirla():
    personel = st.session_state.key_personel
    parca = st.session_state.key_parca
    ret_nedeni = st.session_state.key_ret_nedeni
    op_adi = st.session_state.get("key_op_adi", "")
    cnc_no = st.session_state.get("key_cnc_no", "")
    aciklama = st.session_state.key_aciklama
    ret_miktari = st.session_state.key_ret_miktari
    uretim_miktari = st.session_state.key_uretim_miktari
    fotograf = st.session_state.get(f"foto_{st.session_state.foto_id}", None)

    # Doğrulama Kontrolleri
    if personel == "-- Seçiniz --" or parca == "-- Seçiniz --" or ret_nedeni == "-- Seçiniz --":
        st.session_state.mesaj = ("warning", "⚠️ Lütfen Kalite Personeli, Parça ve Ret Nedeni alanlarını seçiniz!")
        return

    foto_yolu = ""
    if fotograf is not None:
        zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
        foto_yolu = os.path.join(FOTO_KLASORU, f"{zaman_damgasi}_{fotograf.name}")
        with open(foto_yolu, "wb") as f:
            f.write(fotograf.getbuffer())

    kayit = {
        "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Personel": personel,
        "Parca": parca,
        "RetNedeni": ret_nedeni,
        "OperatorAdi": op_adi,
        "CncNo": cnc_no,
        "RetAciklamasi": aciklama,
        "RetMiktari": ret_miktari,
        "UretimMiktari": uretim_miktari,
        "FotografYolu": foto_yolu
    }
    veri_kaydet(kayit)

    # FORMUN SIFIRLANMASI
    st.session_state.key_personel = "-- Seçiniz --"
    st.session_state.key_parca = "-- Seçiniz --"
    st.session_state.key_ret_nedeni = "-- Seçiniz --"
    st.session_state.key_op_adi = ""
    st.session_state.key_cnc_no = ""
    st.session_state.key_aciklama = ""
    st.session_state.key_ret_miktari = 0
    st.session_state.key_uretim_miktari = 0
    st.session_state.foto_id += 1
    st.session_state.mesaj = ("success", "✅ Veri başarıyla kaydedildi ve tüm form sıfırlandı!")

# SAYFA İÇİ ANA BAŞLIK
st.title("🏭 MSP KALİTE YÖNETİM SİSTEMİ")

# Sekmeler: Saha Veri Girişi ve Yönetici Paneli
sekme_saha, sekme_yonetici = st.tabs(["📱 SAHA VERİ GİRİŞİ", "📊 YÖNETİCİ PANELİ"])

# --- SAHA VERİ GİRİŞİ SEKMESİ ---
with sekme_saha:
    st.header("Kalite Kontrol Formu")
    
    # Uyarı veya Başarı Mesajı Gösterimi
    if st.session_state.mesaj:
        m_tur, m_metin = st.session_state.mesaj
        if m_tur == "warning":
            st.warning(m_metin)
        elif m_tur == "success":
            st.success(m_metin)
        st.session_state.mesaj = None

    # 1. Kalite Personeli
    personel_listesi = [
        "-- Seçiniz --",
        "YURDAL BULDU (CNC)",
        "AHMET TİFTİK (MONTAJ-SON KONTROL)",
        "ENES TÜKEL (GİRİŞ KALİTE)",
        "YENİ PERSONEL (ROTOR STATOR)"
    ]
    st.selectbox("Kalite Personeli", personel_listesi, key="key_personel")
    
    # 2. Parça Seçimi
    parcalar = [
        "-- Seçiniz --",
        "6\" ALT YATAK", "6\" ÜST YATAK", "7\" ALT YATAK", "7\" ÜST YATAK", 
        "8\" ALT YATAK", "8\" ÜST YATAK", "10\" ALT YATAK", "10\" ÜST YATAK",
        "6\" FLANŞ", "7\" FLANŞ", "8\" FLANŞ", "10\" FLANŞ"
    ]
    st.selectbox("Parça Seçin", parcalar, key="key_parca")
    
    # 3. Ret Nedeni
    ret_nedenleri = [
        "-- Seçiniz --",
        "OPRT. HATASI", "DÖKÜM HATASI", "TEKNİK HATA", "DİĞER"
    ]
    ret_nedeni = st.selectbox("RET NEDENİ", ret_nedenleri, key="key_ret_nedeni")
    
    # OPRT. HATASI SEÇİLDİĞİNDE AÇILAN ALT MENÜLER
    if ret_nedeni == "OPRT. HATASI":
        st.info("ℹ️ Operatör hatası seçildi. Lütfen operatör adını ve CNC'yi giriniz.")
        st.text_input("OPERATÖRÜN ADI", placeholder="Örn: MELİH ÇAKILLI", key="key_op_adi")
        st.text_input("CNC NO", placeholder="Örn: CNC5", key="key_cnc_no")
    
    # 4. MANUEL RET AÇIKLAMASI
    st.text_input("RET AÇIKLAMASI (Manuel Detay Giriniz)", placeholder="Örn: ÖLÇÜ DÜŞÜK", key="key_aciklama")
    
    # 5. Sayısal Girişler
    st.number_input("RET ADEDİ", min_value=0, step=1, key="key_ret_miktari")
    st.number_input("Üretim Miktarı (Adet)", min_value=0, step=1, key="key_uretim_miktari")
    
    # 6. FOTOĞRAF YÜKLEME
    st.file_uploader("Hatalı Parça Fotoğrafı Ekle (İsteğe Bağlı)", type=["jpg", "jpeg", "png"], key=f"foto_{st.session_state.foto_id}")
    
    # KAYDET VE GÖNDER BUTONU
    st.button("KAYDET VE GÖNDER", use_container_width=True, on_click=kaydet_ve_sifirla)

# --- YÖNETİCİ PANELİ SEKMESİ ---
with sekme_yonetici:
    st.header("Anlık Kalite Takip Ekranı")
    
    df = verileri_yukle()
    
    if not df.empty:
        secilen_parca = st.selectbox("Filtrele: Parça", ["GENEL"] + list(df["Parca"].unique()))
        
        filtered_df = df if secilen_parca == "GENEL" else df[df["Parca"] == secilen_parca]
        
        ret_kolonu = "RetMiktari" if "RetMiktari" in filtered_df.columns else "RedMiktari"
        
        toplam_ret = filtered_df[ret_kolonu].sum()
        toplam_uretim = filtered_df["UretimMiktari"].sum()
        hata_orani = (toplam_ret / toplam_uretim * 100) if toplam_uretim > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Toplam Ret", f"{toplam_ret} Adet")
        col2.metric("Toplam Üretim", f"{toplam_uretim} Adet")
        col3.metric("Hata Oranı", f"%{hata_orani:.2f}")
        
        st.subheader("Son Girilen Veriler")
        st.table(filtered_df.tail(10))
    else:
        st.info("Henüz sistemde kayıtlı veri bulunmuyor.")
