import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="MSP KALİTE YÖNETİM SİSTEMİ", layout="wide")

st.title("MSP KALİTE YÖNETİM SİSTEMİ")

# Google Sheet CSV Bağlantısı
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR6zS3GkM9Yc_5kM8H2jB10f13_Y8/pub?output=csv"

@st.cache_data(ttl=10)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.strip()
    return df

try:
    df = load_data()
    
    # Kolon İsimlerini Tespit Etme
    ret_col = next((c for c in df.columns if "ret" in c.lower() and "adedi" in c.lower()), None)
    uretim_col = next((c for c in df.columns if "üretim" in c.lower() or "uretim" in c.lower()), None)
    neden_col = next((c for c in df.columns if "neden" in c.lower()), None)
    parca_col = next((c for c in df.columns if "parça" in c.lower() or "parca" in c.lower()), None)

    if ret_col:
        df["_RET"] = pd.to_numeric(df[ret_col], errors='coerce').fillna(0)
    else:
        df["_RET"] = 0

    if uretim_col:
        df["_URETIM"] = pd.to_numeric(df[uretim_col], errors='coerce').fillna(0)
    else:
        df["_URETIM"] = 0

    # Metrikler
    toplam_ret = int(df["_RET"].sum())
    toplam_uretim = int(df["_URETIM"].sum())
    toplam_kayit = len(df)
    
    ret_orani = (toplam_ret / toplam_uretim * 100) if toplam_uretim > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Ret Adedi", f"{toplam_ret:,} Adet")
    m2.metric("Toplam Üretim Miktarı", f"{toplam_uretim:,}")
    m3.metric("Toplam Kayıt Sayısı", f"{toplam_kayit}")
    m4.metric("Genel Ret Oranı (%)", f"%{ret_orani:.2f}")

    st.markdown("---")

    # Grafikler
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
                    axis=alt.Axis(
                        labelAngle=-45,
                        labelOverlap=False,
                        labelLimit=150
                    )
                ),
                y=alt.Y("Adet:Q", title="Ret Adedi", scale=alt.Scale(zero=True)),
                tooltip=["Ret Nedeni", "Adet"]
            ).properties(height=320)
            
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
                    axis=alt.Axis(
                        labelAngle=-45,
                        labelOverlap=False,
                        labelLimit=150
                    )
                ),
                y=alt.Y("Adet:Q", title="Ret Adedi", scale=alt.Scale(zero=True)),
                tooltip=["Parça Adı", "Adet"]
            ).properties(height=320)

            text_part = chart_part.mark_text(
                align='center', baseline='bottom', dy=-3, color='black'
            ).encode(text='Adet:Q')

            st.altair_chart(chart_part + text_part, use_container_width=True)

    st.markdown("---")

    # Tablo
    st.subheader("📋 Tüm Ham Veri Tablosu")
    st.dataframe(df.drop(columns=["_RET", "_URETIM"], errors="ignore"), use_container_width=True)

except Exception as e:
    st.error(f"Veri yüklenirken hata oluştu: {e}")
