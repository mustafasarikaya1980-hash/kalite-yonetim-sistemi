# -*- coding: utf-8 -*-
import base64
import io
import streamlit as st
import pandas as pd
import requests
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

# GÖRSEL CSS İYİLEŞTİRMELERİ
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
# AYARLAR
# ==============================================================================
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

FORM2_RESPONSE_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd3tGU9I4FX9OfoHT_EMRb_NHZsbcpMk-ZZmu0sQflfC_tt_A/formResponse"
ENTRY2_TIP = "entry.1056493377"
ENTRY2_DEGER = "entry.1752462997"

SABIT_EPOSTA = "veri@msp-kalite.local"

SPREADSHEET_ID = "1O8qGTDrwv0RRv2Qv7jeux93Y8vz4uT2pwJRQ8U1Vq8o"
SHEET_GID = "1834241278"
SHEET2_GID = "1493441004"

CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET_GID}"
CSV2_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET2_GID}"

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz3mwOeLghFQZU4geLsXfMCvGOt8B7sqRWmtpmZOpQPRgf_eiSLxsjucQCEJ-hntQkN/exec"

_HEADERS = {"User-Agent": "Mozilla/5.0 (MSP Kalite Sistemi)"}

# SESSION STATE BAŞLATMA
_varsayilanlar = {
    "key_personel": "-- Seçiniz --",
    "key_parca": "-- Seçiniz --",
    "key_ret_nedeni": "-- Seçiniz --",
    "key_op_adi": "",
    "key_cnc_no": "",
    "key_aciklama": "",
    "key_ret_miktari": 0,
    "key_uretim_miktari": 0,
    "mesaj": None,
    "key_yeni_personel_ayarlar": "",
    "key_yeni_parca_ayarlar": "",
    "uploader_versiyon": 0,
}
for _k, _v in _varsayilanlar.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

@st.cache_data(ttl=10, show_spinner=False)
def verileri_yukle():
    try:
        df = pd.read_csv(CSV_URL)
        df = df.dropna(how="all")
        return df
    except Exception as e:
        st.session_state["_son_okuma_hatasi"] = str(e)
        return pd.DataFrame()

@st.cache_data(ttl=10, show_spinner=False)
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

def kaydet_ve_sifirla():
    personel = st.session_state.get("key_personel", "-- Seçiniz --")
    parca = st.session_state.get("key_parca", "-- Seçiniz --")
    ret_nedeni = st.session_state.get("key_ret_nedeni", "-- Seçiniz --")
    aciklama = st.session_state.get("key_aciklama", "")
    ret_miktari = st.session_state.get("key_ret_miktari", 0)
    uretim_miktari = st.session_state.get("key_uretim_miktari", 0)

    if personel == "-- Seçiniz --" or parca == "-- Seçiniz --" or ret_nedeni == "-- Seçiniz --":
        st.session_state.mesaj = ("warning", "⚠️ Lütfen Kalite Personeli, Parça ve Ret Nedeni alanlarını seçiniz!")
        return

    if ret_nedeni == "OPRT. HATASI":
        op_adi = st.session_state.get("key_op_adi", "")
        cnc_no = st.session_state.get("key_cnc_no", "")
    else:
        op_adi = ""
        cnc_no = ""

    uploader_key = f"key_belgeler_{st.session_state.get('uploader_versiyon', 0)}"
    yuklenen_dosyalar = st.session_state.get(uploader_key, [])

    belge_linkleri = dosyalari_yukle(yuklenen_dosyalar)
    if belge_linkleri is None:
        return

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

    basarili = veri_kaydet(kayit)
    if basarili:
        st.session_state.key_personel = "-- Seçiniz --"
        st.session_state.key_parca = "-- Seçiniz --"
        st.session_state.key_ret_nedeni = "-- Seçiniz --"
        st.session_state.key_op_adi = ""
        st.session_state.key_cnc_no = ""
        st.session_state.key_aciklama = ""
        st.session_state.key_ret_miktari = 0
        st.session_state.key_uretim_miktari = 0
        st.session_state.uploader_versiyon = st.session_state.get("uploader_versiyon", 0) + 1
        belge_sayisi = len(belge_linkleri)
        ek_mesaj = f" ({belge_sayisi} belge eklendi.)" if belge_sayisi else ""
        st.session_state.mesaj = ("success", f"✅ Veri Google E-Tablonuza kaydedildi!{ek_mesaj}")

def personel_ekle(kaynak_key: str):
    yeni = st.session_state.get(kaynak_key, "").strip()
    if not yeni: return
    if kalici_liste_ekle("PERSONEL", yeni):
        st.session_state[kaynak_key] = ""
        st.session_state.mesaj = ("success", f"✅ '{yeni}' eklendi!")

def parca_ekle(kaynak_key: str):
    yeni = st.session_state.get(kaynak_key, "").strip()
    if not yeni: return
    if kalici_liste_ekle("PARCA", yeni):
        st.session_state[kaynak_key] = ""
        st.session_state.mesaj = ("success", f"✅ '{yeni}' eklendi!")

# HEADER
st.markdown(
    """
    <div style="background: linear-gradient(135deg, #2563EB 0%, #1E3A8A 100%); padding: 1.3rem 1.8rem; border-radius: 14px; margin-bottom: 0.8rem; box-shadow: 0 4px 14px rgba(37,99,235,0.25);">
        <h1 style="color: white; margin: 0; font-size: 1.7rem; line-height: 1.2;">🏭 MSP KALİTE YÖNETİM SİSTEMİ</h1>
        <p style="color: #DBEAFE; margin: 0.35rem 0 0 0; font-size: 0.95rem;">Saha kalite kontrol veri girişi, otomatik analiz ve yönetim raporlama</p>
    </div>
    """,
    unsafe_allow_html=True,
)

sekme_saha, sekme_yonetici, sekme_raporlar, sekme_ayarlar = st.tabs([
    "📱 SAHA VERİ GİRİŞİ",
    "📊 YÖNETİCİ PANELİ & ANALİZ",
    "📈 ÜST YÖNETİM RAPORLARI",
    "⚙️ YÖNETİM & AYARLAR",
])

ekstra_personeller, ekstra_parcalar = ekstra_liste_yukle()

# --- 1. SEKME: SAHA GİRİŞİ ---
with sekme_saha:
    st.header("Kalite Kontrol Formu")
    if st.session_state.mesaj:
        m_tur, m_metin = st.session_state.mesaj
        if m_tur == "warning": st.warning(m_metin)
        elif m_tur == "success": st.success(m_metin)
        st.session_state.mesaj = None

    tum_personeller = ekstra_personeller
    st.selectbox("Kalite Personeli", ["-- Seçiniz --"] + tum_personeller, key="key_personel")

    tum_parcalar = ekstra_parcalar
    st.selectbox("Parça Seçin", ["-- Seçiniz --"] + tum_parcalar, key="key_parca")

    ret_nedenleri = ["-- Seçiniz --", "OPRT. HATASI", "DÖKÜM HATASI", "TEKNİK HATA", "DİĞER"]
    ret_nedeni = st.selectbox("RET NEDENİ", ret_nedenleri, key="key_ret_nedeni")

    if ret_nedeni == "OPRT. HATASI":
        st.info("ℹ️ Operatör hatası seçildi. Lütfen operatör adını ve CNC'yi giriniz.")
        st.text_input("OPERATÖRÜN ADI", placeholder="Örn: MELİH ÇAKILLI", key="key_op_adi")
        st.text_input("CNC NO", placeholder="Örn: CNC5", key="key_cnc_no")

    st.text_input("RET AÇIKLAMASI (Manuel Detay Giriniz)", placeholder="Örn: ÖLÇÜ DÜŞÜK", key="key_aciklama")

    st.file_uploader(
        "📎 BELGE / FOTOĞRAF EKLE (Birden fazla dosya seçebilirsiniz)",
        type=["png", "jpg", "jpeg", "pdf"],
        accept_multiple_files=True,
        key=f"key_belgeler_{st.session_state.get('uploader_versiyon', 0)}",
    )

    st.number_input("RET ADEDİ", min_value=0, step=1, key="key_ret_miktari")
    st.number_input("Üretim Miktarı (Adet)", min_value=0, step=1, key="key_uretim_miktari")

    st.button("KAYDET VE GÖNDER", use_container_width=True, on_click=kaydet_ve_sifirla)

# GÜVENLİ SÜTUN BULUCU
def sutun_isimi_getir(df, kelimeler):
    for c in df.columns:
        if any(k.upper() in str(c).upper() for k in kelimeler):
            return c
    return None

# --- 2. SEKME: YÖNETİCİ PANELİ & CANLI ANALİZ ---
with sekme_yonetici:
    st.header("Anlık Kalite Takip ve Canlı Analiz Ekranı")
    if st.button("🔄 Verileri Yenile"):
        verileri_yukle.clear()
        ekstra_liste_yukle.clear()
        st.rerun()

    df = verileri_yukle()
    if not df.empty:
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        toplam_kayit = len(df)
        
        ret_c = sutun_isimi_getir(df, ["RET MİKTARI", "RET MIKTARI", "RET ADEDİ", "RET"])
        uretim_c = sutun_isimi_getir(df, ["ÜRETİM MİKTARI", "URETIM MIKTARI", "ÜRETİM ADEDİ", "URETIM"])
        parca_c = sutun_isimi_getir(df, ["PARÇA", "PARCA"])
        neden_c = sutun_isimi_getir(df, ["NEDEN", "RET NEDENİ"])

        toplam_ret = 0
        toplam_uretim = 0
        if ret_c:
            toplam_ret = int(pd.to_numeric(df[ret_c], errors="coerce").fillna(0).sum())
        if uretim_c:
            toplam_uretim = int(pd.to_numeric(df[uretim_c], errors="coerce").fillna(0).sum())

        genel_ppm = round((toplam_ret / toplam_uretim * 1000000), 2) if toplam_uretim > 0 else 0.0

        col_m1.metric("Toplam Kontrol Kaydı", f"{toplam_kayit} Adet")
        col_m2.metric("Toplam Üretim Adedi", f"{toplam_uretim:,}")
        col_m3.metric("Toplam Ret Adedi", f"{toplam_ret:,}")
        col_m4.metric("Genel Hata Oranı (PPM)", f"{genel_ppm:,}")

        st.markdown("---")
        
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("📌 Ret Nedenleri Dağılımı")
            if neden_c and ret_c:
                try:
                    # HATA ÖNLENMİŞ GRUPLAMA (as_index=False ile çakışma tamamen engellendi)
                    temp_df = pd.DataFrame({
                        "Nedeni": df[neden_c].astype(str),
                        "Adet": pd.to_numeric(df[ret_c], errors="coerce").fillna(0)
                    })
                    ret_by_reason = temp_df.groupby("Nedeni", as_index=False)["Adet"].sum()
                    st.bar_chart(data=ret_by_reason, x="Nedeni", y="Adet")
                except Exception as ex:
                    st.warning(f"Grafik çizdirilemedi: {ex}")

        with col_g2:
            st.subheader("🧩 Parça Bazlı Ret Adetleri")
            if parca_c and ret_c:
                try:
                    temp_df = pd.DataFrame({
                        "Parca": df[parca_c].astype(str),
                        "Adet": pd.to_numeric(df[ret_c], errors="coerce").fillna(0)
                    })
                    ret_by_part = temp_df.groupby("Parca", as_index=False)["Adet"].sum()
                    st.bar_chart(data=ret_by_part, x="Parca", y="Adet")
                except Exception as ex:
                    st.warning(f"Grafik çizdirilemedi: {ex}")

        st.subheader("📋 Tüm Ham Veri Tablosu")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Henüz tabloya kaydedilmiş veri bulunmuyor.")

# --- 3. SEKME: ÜST YÖNETİM RAPORLARI ---
with sekme_raporlar:
    st.header("📈 Üst Yönetim Kalite Özeti & Excel Rapor İndirme")
    st.caption("Aşağıdaki analiz özeti doğrudan üst yönetime sunulabilecek formatta hazırlanmıştır.")

    df = verileri_yukle()
    if not df.empty:
        st.subheader("📊 Yönetim Özet Tablosu")
        
        ret_c = sutun_isimi_getir(df, ["RET MİKTARI", "RET MIKTARI", "RET ADEDİ", "RET"])
        uretim_c = sutun_isimi_getir(df, ["ÜRETİM MİKTARI", "URETIM MIKTARI", "ÜRETİM ADEDİ", "URETIM"])
        parca_c = sutun_isimi_getir(df, ["PARÇA", "PARCA"])

        if parca_c and ret_c and uretim_c:
            try:
                temp_df = pd.DataFrame({
                    "Parça Adı": df[parca_c].astype(str),
                    "Toplam Üretim": pd.to_numeric(df[uretim_c], errors="coerce").fillna(0),
                    "Toplam Ret": pd.to_numeric(df[ret_c], errors="coerce").fillna(0)
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
            except Exception as ex:
                st.dataframe(df, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Kalite_Verileri", index=False)
            st.download_button(
                label="📥 Raporu Excel (.xlsx) Olarak İndir",
                data=buffer.getvalue(),
                file_name=f"Kalite_Raporu_{datetime.now().strftime('%Y_%m_%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    else:
        st.info("Rapor oluşturmak için veri bulunamadı.")

# --- 4. SEKME: AYARLAR ---
with sekme_ayarlar:
    st.header("Personel ve Parça Listesini Yönet")
    st.caption("Buradan eklediğiniz isimler kalıcıdır ve tüm cihazlar için ortaktır.")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.subheader("👤 Yeni Personel Ekle")
        st.text_input("Personel Adı Soyadı", key="key_yeni_personel_ayarlar")
        st.button("Personel Ekle", key="btn_personel_ekle_ayarlar", on_click=personel_ekle, args=("key_yeni_personel_ayarlar",))
        if ekstra_personeller:
            st.caption("Mevcut Personeller: " + ", ".join(ekstra_personeller))
    with col_p2:
        st.subheader("🧩 Yeni Parça Ekle")
        st.text_input("Parça Adı", key="key_yeni_parca_ayarlar")
        st.button("Parça Ekle", key="btn_parca_ekle_ayarlar", on_click=parca_ekle, args=("key_yeni_parca_ayarlar",))
        if ekstra_parcalar:
            st.caption("Mevcut Parçalar: " + ", ".join(ekstra_parcalar))
