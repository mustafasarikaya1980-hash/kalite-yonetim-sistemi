# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import altair as alt

st.set_page_config(page_title="MSP KALİTE YÖNETİM SİSTEMİ", layout="wide", page_icon="🏭")

# --- GÜNCEL E-TABLO VE SEKME BİLGİLERİ ---
SPREADSHEET_ID = "1O8qGTDrwv0RRv2Qv7jeux93Y8vz4uT2pwJRQ8U1Vq8o"
SHEET_GID = "1834241278"         # Saha Verileri
GKK_SHEET_GID = "1709999332"     # GÜNCEL GİRİŞ KALİTE (Form Yanıtları 6)

CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET_GID}"
CSV_GIRIS_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GKK_SHEET_GID}"

@st.cache_data(ttl=5, show_spinner=False)
def giris_kalite_yukle():
    try:
        df = pd.read_csv(CSV_GIRIS_URL)
        return df.dropna(how="all")
    except Exception as e:
        return pd.DataFrame()

# --- ANALİZ PANELİ KISMI ---
with st.container():
    st.header("Anlık Kalite Takip ve Canlı Analiz Ekranı")
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()

    df_gkk = giris_kalite_yukle()
    
    if not df_gkk.empty:
        # Sütun isimlerindeki boşlukları temizleyelim
        df_gkk.columns = [str(c).strip() for c in df_gkk.columns]
        
        st.subheader("📋 Giriş Kalite Kontrol Detaylı Veri Tablosu")
        st.dataframe(df_gkk, use_container_width=True)
    else:
        st.warning("Veri çekilemiyor veya sekme boş. Lütfen CSV bağlantısını ve sekme ID'sini (1709999332) kontrol edin.")
