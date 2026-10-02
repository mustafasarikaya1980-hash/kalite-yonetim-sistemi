import requests
import streamlit as st

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Giriş Kalite Kontrol Sistemi", page_icon="⚙️", layout="wide"
)

# Google Form Hedef URL'si (viewform yerine formResponse kullanılır)
# Not: Kendi form linkinizdeki 'viewform' kısmını 'formResponse' ile değiştirdiğinizden emin olun.
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd.../formResponse"


def submit_to_google_forms(data):
  """Form verilerini Google Form endpoint'ine POST eder."""
  payload = {
      "entry.1707834702": data.get("tarih"),
      "entry.602500017": data.get("rapor_no"),
      "entry.2395152516": data.get("gelen_urun"),
      "entry.1427845": data.get("tedarikci_firma"),
      "entry.1206155217": data.get("irsaliye_no"),
  }

  try:
    # Google Forms genellikle başarılı kayıtlarda 200 veya 302 yönlendirmesi döner
    response = requests.post(FORM_URL, data=payload)
    if response.status_code in [200, 302]:
      return True
    else:
      return False
  except Exception as e:
    st.error(f"Bağlantı hatası oluştu: {e}")
    return False


# --- Ana Arayüz ---
st.title("🛡️ Giriş Kalite Kontrol Takip ve Form Entegrasyonu")
st.markdown(
    "Bu panel üzerinden girdiğiniz kalite kontrol verileri hem sisteme kaydedilir"
    " hem de arka planda Google Formunuza iletilir."
)

with st.form("kalite_kontrol_formu", clear_on_submit=True):
  st.subheader("Muayene ve Parça Bilgileri")

  col1, col2 = st.columns(2)

  with col1:
    tarih = st.date_input("İnceleme Tarihi")
    rapor_no = st.text_input(
        "Rapor No", placeholder="Örn: RPR-2026-001"
    )  # entry.602500017
    gelen_urun = st.text_input(
        "Gelen Ürün / Parça Adı", placeholder="Örn: Stator / Rotor"
    )  # entry.2395152516

  with col2:
    tedarikci_firma = st.text_input(
        "Tedarikçi Firma"
    )  # entry.1427845 (veya ilgili entry)
    irsaliye_no = st.text_input("İrsaliye No")  # entry.1206155217

  st.markdown("---")

  # Form Gönderim Butonu
  submitted = st.form_submit_button(
      "🚀 Verileri Kaydet ve Google Form'a Gönder", use_container_width=True
  )

  if submitted:
    if not rapor_no or not gelen_urun:
      st.warning("⚠️ Lütfen Rapor No ve Gelen Ürün alanlarını boş bırakmayın!")
    else:
      form_data = {
          "tarih": str(tarih),
          "rapor_no": rapor_no,
          "gelen_urun": gelen_urun,
          "tedarikci_firma": tedarikci_firma,
          "irsaliye_no": irsaliye_no,
      }

      # Spinner ile gönderim süreci gösterilir
      with st.spinner("Veriler Google Form sistemine işleniyor..."):
        success = submit_to_google_forms(form_data)

      if success:
        st.success(
            "✅ Kalite kontrol verisi başarıyla kaydedildi ve Google"
            " Form/Sheet'e aktarıldı!"
        )
        st.balloons()
      else:
        st.error(
            "❌ Veri gönderilemedi. Lütfen Form URL adresini ve ağ bağlantınızı"
            " kontrol edin."
        )

# Uygulama Alt Bilgisi
st.markdown("---")
st.caption(
    "Kalite Yönetim Sistemi • Otomatik Veri Aktarım Modülü v2.0 (Streamlit +"
    " Google Forms)"
)
