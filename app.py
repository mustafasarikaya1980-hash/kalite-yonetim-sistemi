# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="MSP KALİTE YÖNETİM SİSTEMİ", layout="wide", page_icon="🏭")

# TARAYICI OTOMATİK ÇEVİRİ ENGELİ (HATA ÖNLEYİCİ)
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

# GÖRSEL İYİLEŞTİRMELER (renkler .streamlit/config.toml içinde ayarlanır)
st.markdown(
    """
    <style>
    /* Üst sekme çubuğunu sabitle — kaydırınca ekranın üstünde kalır */
    div[data-testid="stTabs"] > div:first-child {
        position: sticky;
        top: 2.6rem;
        z-index: 999;
        background-color: var(--background-color, #F8FAFC);
        padding-top: 0.4rem;
        padding-bottom: 0.3rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    }

    button[data-baseweb="tab"] {
        font-size: 1.05rem;
        font-weight: 600;
    }

    /* Form alanları arası biraz daha ferah */
    div[data-testid="stVerticalBlockBorderWrapper"] { margin-bottom: 0.25rem; }

    /* Girdi kutularının köşelerini yuvarla */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    textarea {
        border-radius: 10px !important;
    }

    /* Kaydet butonunu belirginleştir */
    div[data-testid="stButton"] button {
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1rem;
    }

    /* Ana içerik üstündeki boşluğu azalt */
    div.block-container { padding-top: 1.2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# 🔗 GOOGLE FORM (YAZMA) VE GOOGLE E-TABLO (OKUMA) AYARLARI
# Servis hesabı / secrets.toml / API anahtarı GEREKMİYOR — kayıt, sizin
# oluşturduğunuz Google Form'a arka planda gönderilir; okuma ise tablonun
# herkese açık CSV linki üzerinden yapılır.
# ==============================================================================

# --- Form 1: Kalite kontrol kayıtları ---
FORM_RESPONSE_URL = (
    "https://docs.google.com/forms/d/e/1FAIpQLSc2GWwoN4UOcWHSZxNQNNT-rNBJrI1I4E1xN8CHMA-cO1BxqA/formResponse"
)
ENTRY_PERSONEL = "entry.1505600207"
ENTRY_PARCA = "entry.1034697779"
ENTRY_RET_NEDENI = "entry.1351128780"
ENTRY_OP_ADI = "entry.108790685"
ENTRY_CNC_NO = "entry.657669024"
ENTRY_ACIKLAMA = "entry.686625208"
ENTRY_RET_MIKTARI = "entry.410490317"
ENTRY_URETIM_MIKTARI = "entry.958612329"

# --- Form 2: Yeni personel / parça ekleme (kalıcı, herkese ortak liste) ---
FORM2_RESPONSE_URL = (
    "https://docs.google.com/forms/d/e/1FAIpQLSd3tGU9I4FX9OfoHT_EMRb_NHZsbcpMk-ZZmu0sQflfC_tt_A/formResponse"
)
ENTRY2_TIP = "entry.1056493377"
ENTRY2_DEGER = "entry.1752462997"

# Form ayarları e-posta adresi toplayacak şekilde kurulduğu için Google her iki
# formda da otomatik bir "E-posta" sorusu ekledi. Bu, normal bir soru gibi
# "entry.xxx" değil, özel "emailAddress" adıyla gönderilmesi gereken bir alan.
# Kullanıcıdan gerçek bir e-posta istemiyoruz; sabit bir yer tutucu değer
# gönderiyoruz.
SABIT_EPOSTA = "veri@msp-kalite.local"

# Yanıtların düştüğü Google E-Tablo (her iki form da aynı dosyaya, farklı
# sekmelere yazıyor)
SPREADSHEET_ID = "1O8qGTDrwv0RRv2Qv7jeux93Y8vz4uT2pwJRQ8U1Vq8o"
SHEET_GID = "1834241278"          # Kalite kontrol kayıtları sekmesi
SHEET2_GID = "1493441004"         # Yeni personel/parça kayıtları sekmesi

CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET_GID}"
CSV2_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET2_GID}"

_HEADERS = {"User-Agent": "Mozilla/5.0 (MSP Kalite Sistemi)"}


@st.cache_data(ttl=10, show_spinner=False)
def verileri_yukle():
    """Google E-Tablodaki kalite kayıtlarını herkese açık CSV linkinden okur."""
    try:
        df = pd.read_csv(CSV_URL)
        df = df.dropna(how="all")
        return df
    except Exception as e:
        st.session_state["_son_okuma_hatasi"] = str(e)
        return pd.DataFrame()


@st.cache_data(ttl=10, show_spinner=False)
def ekstra_liste_yukle():
    """Arayüzden eklenmiş yeni personel/parça isimlerini okur (tüm kullanıcılar
    ve cihazlar için ortak, kalıcı liste)."""
    try:
        df = pd.read_csv(CSV2_URL)
        df = df.dropna(how="all")
        if df.empty or "Tip" not in df.columns or "Değer" not in df.columns:
            return [], []
        tip = df["Tip"].astype(str).str.strip().str.upper()
        deger = df["Değer"].astype(str).str.strip()
        personeller = deger[tip == "PERSONEL"].tolist()
        parcalar = deger[tip == "PARCA"].tolist()
        # Tekilleştir, sırayı koru
        personeller = list(dict.fromkeys(p for p in personeller if p and p.lower() != "nan"))
        parcalar = list(dict.fromkeys(p for p in parcalar if p and p.lower() != "nan"))
        return personeller, parcalar
    except Exception:
        return [], []


def veri_kaydet(yeni_veri: dict) -> bool:
    """Google Form'un formResponse adresine POST göndererek e-tabloya
    yeni bir kalite kaydı düşürür. Servis hesabı / API anahtarı gerekmez."""
    payload = {
        ENTRY_PERSONEL: yeni_veri["personel"],
        ENTRY_PARCA: yeni_veri["parca"],
        ENTRY_RET_NEDENI: yeni_veri["ret_nedeni"],
        ENTRY_OP_ADI: yeni_veri["op_adi"],
        ENTRY_CNC_NO: yeni_veri["cnc_no"],
        ENTRY_ACIKLAMA: yeni_veri["aciklama"],
        ENTRY_RET_MIKTARI: yeni_veri["ret_miktari"],
        ENTRY_URETIM_MIKTARI: yeni_veri["uretim_miktari"],
        "emailAddress": SABIT_EPOSTA,
    }
    try:
        resp = requests.post(FORM_RESPONSE_URL, data=payload, headers=_HEADERS, timeout=15)
        if resp.status_code in (200, 302):
            verileri_yukle.clear()  # önbelleği temizle ki yeni kayıt hemen görünsün
            return True
        st.error(f"❌ Google Form'a gönderilirken beklenmeyen bir yanıt alındı (kod: {resp.status_code}).")
        return False
    except Exception as e:
        st.error(f"❌ Kaydedilirken bağlantı hatası oluştu: {e}")
        return False


def kalici_liste_ekle(tip: str, deger: str) -> bool:
    """Yeni bir personel/parça adını, ikinci Google Form üzerinden kalıcı ve
    tüm kullanıcılar için ortak olacak şekilde kaydeder."""
    payload = {
        ENTRY2_TIP: tip,
        ENTRY2_DEGER: deger,
        "emailAddress": SABIT_EPOSTA,
    }
    try:
        resp = requests.post(FORM2_RESPONSE_URL, data=payload, headers=_HEADERS, timeout=15)
        if resp.status_code in (200, 302):
            ekstra_liste_yukle.clear()
            return True
        st.error(f"❌ Kaydedilirken beklenmeyen bir yanıt alındı (kod: {resp.status_code}).")
        return False
    except Exception as e:
        st.error(f"❌ Kaydedilirken bağlantı hatası oluştu: {e}")
        return False


# Not: Personel ve parça listeleri artık kodda sabit değil — tamamen Google
# E-Tablodaki "Form Yanıtları 3" sekmesinden okunuyor (bkz. ekstra_liste_yukle).
# Listeyi eklemek/silmek/düzeltmek için doğrudan o sekmeyi düzenlemeniz yeterli,
# kod değişikliği gerekmez.

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
}
for _k, _v in _varsayilanlar.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


def kaydet_ve_sifirla():
    personel = st.session_state.key_personel
    parca = st.session_state.key_parca
    ret_nedeni = st.session_state.key_ret_nedeni
    aciklama = st.session_state.key_aciklama
    ret_miktari = st.session_state.key_ret_miktari
    uretim_miktari = st.session_state.key_uretim_miktari

    if personel == "-- Seçiniz --" or parca == "-- Seçiniz --" or ret_nedeni == "-- Seçiniz --":
        st.session_state.mesaj = ("warning", "⚠️ Lütfen Kalite Personeli, Parça ve Ret Nedeni alanlarını seçiniz!")
        return

    if ret_nedeni == "OPRT. HATASI":
        op_adi = st.session_state.get("key_op_adi", "")
        cnc_no = st.session_state.get("key_cnc_no", "")
    else:
        op_adi = ""
        cnc_no = ""

    kayit = {
        "personel": personel,
        "parca": parca,
        "ret_nedeni": ret_nedeni,
        "op_adi": op_adi,
        "cnc_no": cnc_no,
        "aciklama": aciklama,
        "ret_miktari": ret_miktari,
        "uretim_miktari": uretim_miktari,
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
        st.session_state.mesaj = ("success", "✅ Veri Google E-Tablonuza doğrudan kaydedildi!")


def personel_ekle(kaynak_key: str):
    yeni = st.session_state[kaynak_key].strip()
    if not yeni:
        return
    if kalici_liste_ekle("PERSONEL", yeni):
        st.session_state[kaynak_key] = ""
        st.session_state.mesaj = ("success", f"✅ '{yeni}' personel listesine kalıcı olarak eklendi!")


def parca_ekle(kaynak_key: str):
    yeni = st.session_state[kaynak_key].strip()
    if not yeni:
        return
    if kalici_liste_ekle("PARCA", yeni):
        st.session_state[kaynak_key] = ""
        st.session_state.mesaj = ("success", f"✅ '{yeni}' parça listesine kalıcı olarak eklendi!")


st.markdown(
    """
    <div style="
        background: linear-gradient(135deg, #2563EB 0%, #1E3A8A 100%);
        padding: 1.3rem 1.8rem;
        border-radius: 14px;
        margin-bottom: 0.8rem;
        box-shadow: 0 4px 14px rgba(37,99,235,0.25);
    ">
        <h1 style="color: white; margin: 0; font-size: 1.7rem; line-height: 1.2;">
            🏭 MSP KALİTE YÖNETİM SİSTEMİ
        </h1>
        <p style="color: #DBEAFE; margin: 0.35rem 0 0 0; font-size: 0.95rem;">
            Saha kalite kontrol veri girişi ve canlı takip
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

sekme_saha, sekme_yonetici, sekme_ayarlar = st.tabs([
    "📱 SAHA VERİ GİRİŞİ",
    "📊 YÖNETİCİ PANELİ",
    "⚙️ YÖNETİM & AYARLAR",
])

ekstra_personeller, ekstra_parcalar = ekstra_liste_yukle()

with sekme_saha:
    st.header("Kalite Kontrol Formu")

    if st.session_state.mesaj:
        m_tur, m_metin = st.session_state.mesaj
        if m_tur == "warning":
            st.warning(m_metin)
        elif m_tur == "success":
            st.success(m_metin)
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
    st.number_input("RET ADEDİ", min_value=0, step=1, key="key_ret_miktari")
    st.number_input("Üretim Miktarı (Adet)", min_value=0, step=1, key="key_uretim_miktari")

    st.button("KAYDET VE GÖNDER", use_container_width=True, on_click=kaydet_ve_sifirla)

with sekme_yonetici:
    st.header("Anlık Kalite Takip Ekranı (Canlı E-Tablo)")
    if st.button("🔄 Verileri Yenile"):
        verileri_yukle.clear()
        ekstra_liste_yukle.clear()
        st.rerun()

    df = verileri_yukle()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Henüz tabloya kaydedilmiş veri bulunmuyor.")
        if st.session_state.get("_son_okuma_hatasi"):
            with st.expander("Teknik detay (veri okunamadıysa)"):
                st.code(st.session_state["_son_okuma_hatasi"])

with sekme_ayarlar:
    st.header("Personel ve Parça Listesini Yönet")
    st.caption("Buradan eklediğiniz isimler kalıcıdır ve tüm cihazlar/kullanıcılar için ortaktır.")
    st.info(
        "🗑️ Bir ismi **silmek** veya **düzeltmek** için buradan yapamazsınız (Google Form sadece "
        "ekleme yapabilir) — bunun için doğrudan Google E-Tablodaki "
        "[Form Yanıtları 3 sekmesini](https://docs.google.com/spreadsheets/d/"
        f"{SPREADSHEET_ID}/edit#gid={SHEET2_GID}) açın, ilgili satırı bulup hücreyi düzenleyin "
        "ya da satırı silin. Değişiklik uygulamaya en geç 10 saniyede (veya 'Verileri Yenile'ye "
        "basınca hemen) yansır."
    )
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.subheader("👤 Yeni Personel Ekle")
        st.text_input("Personel Adı Soyadı", key="key_yeni_personel_ayarlar")
        st.button(
            "Personel Ekle",
            key="btn_personel_ekle_ayarlar",
            on_click=personel_ekle,
            args=("key_yeni_personel_ayarlar",),
        )
        if ekstra_personeller:
            st.caption("Şu ana kadar eklenenler: " + ", ".join(ekstra_personeller))
    with col_p2:
        st.subheader("🧩 Yeni Parça Ekle")
        st.text_input("Parça Adı", key="key_yeni_parca_ayarlar")
        st.button(
            "Parça Ekle",
            key="btn_parca_ekle_ayarlar",
            on_click=parca_ekle,
            args=("key_yeni_parca_ayarlar",),
        )
        if ekstra_parcalar:
            st.caption("Şu ana kadar eklenenler: " + ", ".join(ekstra_parcalar))
