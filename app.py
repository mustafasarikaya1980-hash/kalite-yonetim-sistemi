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

SABIT_EPOSTA = "veri@msp-kalite.local"

# ANA E-TABLO VE GKK SEKME GID'Sİ ("Form Yanıtları 7" / 1866719555)
SPREADSHEET_ID = "1O8qGTDrwv0RRv2Qv7jeux93Y8vz4uT2pwJRQ8U1Vq8o"
SHEET_GID = "1834241278"         # Saha Verileri Sekmesi
SHEET2_GID = "1493441004"        # Ekstra Listeler Sekmesi
GKK_SHEET_GID = "1866719555"     # GÜNCEL GİRİŞ KALİTE SEKME GID (Form Yanıtları 7)

CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET_GID}"
CSV2_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET2_GID}"
CSV_GIRIS_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GKK_SHEET_GID}"

# Güncel Apps Script Web App URL'i
# ÖNEMLİ: Apps Script'te "Web uygulaması > URL > Kopyala" ile aldığınız adresle birebir aynı olmalı.
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycby9xKz14pVGDNPDkUlUsztvrOK6WEAUOmbXDWBNcpwL70lcg8QRR1AVwKNEXAEoi40P/exec"

_HEADERS = {"User-Agent": "Mozilla/5.0 (MSP Kalite Sistemi)"}

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
                }
                if giris_kalite_kaydet(gkk_kayit):
                    st.session_state.form_key += 1
                    st.session_state.gkk_mesaj = "✅ Giriş Kalite Kontrol kaydı Form Yanıtları 7 sekmesine başarıyla işlendi!"
                    st.rerun()
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
            # Puan sütunu: adayların içinden en çok sayısal değer içereni seç
            _puan_adaylari = [c for c in df_gkk.columns if any(x in c.lower() for x in ("puan", "100", "değerlendirme"))]
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

                col_sol, col_sag = st.columns([1.3, 0.7])

                # ---------- SOL: seçilen haftanın raporu ----------
                with col_sol:
                    st.subheader("📅 Haftalık Rapor")
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

                    if not gecersiz_df.empty:
                        with st.expander("⚠️ Tarihi okunamayan kayıtlar", expanded=False):
                            st.dataframe(gecersiz_df.drop(columns=["_dt", "_hafta", "_hafta_bas"], errors="ignore"), use_container_width=True, hide_index=True)

                # ---------- SAĞ: üstte tedarikçi fikstürü, altta aylık grafik ----------
                with col_sag:
                    st.subheader("📊 Tedarikçi Puan Fikstürü")
                    st.caption(secilen_hafta)
                    if c_puan and c_firma:
                        grafik_df = h_df[[c_firma, c_puan]].copy()
                        grafik_df[c_puan] = pd.to_numeric(grafik_df[c_puan], errors="coerce")
                        grafik_df = grafik_df.dropna()
                        if not grafik_df.empty:
                            grafik_df = grafik_df.groupby(c_firma, as_index=False)[c_puan].mean()
                            grafik_df[c_puan] = grafik_df[c_puan].round(2)
                            puan_chart = alt.Chart(grafik_df).mark_bar(color="#2563EB", cornerRadiusEnd=6).encode(
                                x=alt.X(f"{c_puan}:Q", title="Değerlendirme Puanı (100 üzerinden)", scale=alt.Scale(domain=[0, 100])),
                                y=alt.Y(f"{c_firma}:N", sort="-x", title="Tedarikçi Firma"),
                                tooltip=[c_firma, c_puan]
                            ).properties(height=max(120, 45 * len(grafik_df) + 50))
                            st.altair_chart(puan_chart, use_container_width=True)
                        else:
                            st.info("Bu hafta için sayısal puan bulunmuyor.")
                    else:
                        st.info("Puan veya firma sütunu eksik.")

                    st.subheader("📈 Aylık Puan Grafiği")
                    st.caption("Tedarikçi bazında aylık ortalama puan (tüm kayıtlar)")
                    if c_puan and c_firma:
                        trend_df = df_gkk[["_dt", c_firma, c_puan]].copy()
                        trend_df[c_puan] = pd.to_numeric(trend_df[c_puan], errors="coerce")
                        trend_df = trend_df.dropna()
                        if not trend_df.empty:
                            trend_df["Ay"] = trend_df["_dt"].dt.to_period("M").dt.to_timestamp()
                            aylik = trend_df.groupby(["Ay", c_firma], as_index=False)[c_puan].mean()
                            aylik[c_puan] = aylik[c_puan].round(2)
                            trend_chart = alt.Chart(aylik).mark_line(point=True).encode(
                                x=alt.X("Ay:T", title="Ay", axis=alt.Axis(format="%m.%Y")),
                                y=alt.Y(f"{c_puan}:Q", title="Ortalama Puan", scale=alt.Scale(domain=[0, 100])),
                                color=alt.Color(f"{c_firma}:N", title="Tedarikçi"),
                                tooltip=[alt.Tooltip("Ay:T", format="%m.%Y"), c_firma, c_puan],
                            ).properties(height=300)
                            st.altair_chart(trend_chart, use_container_width=True)
                        else:
                            st.info("Aylık grafik için tarihli ve puanlı kayıt bulunmuyor.")
                    else:
                        st.info("Aylık grafik için puan ve firma sütunları gerekli.")
