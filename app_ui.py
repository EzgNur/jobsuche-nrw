#!/usr/bin/env python3
"""
NRW Türk işletmeleri – bölge, şehir, sektör ve kaynak seçerek Excel oluşturma arayüzü.
Çalıştırma: streamlit run app_ui.py
"""

import datetime
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# Proje kökü
PROJE_KOK = Path(__file__).resolve().parent
os.chdir(PROJE_KOK)

st.set_page_config(
    page_title="NRW Türk İşletmeleri – Excel",
    page_icon="📋",
    layout="centered",
)

st.title("📋 NRW Türk İşletmeleri – Excel Oluşturucu")
st.caption("Bölge, şehir ve sektör seçin; veri kaynağını (OSM / Google / ikisi) belirleyin. Excel’de Google Maps ve North Data linkleri tıklanabilir olur.")

try:
    from config import BOLGELER_NRW, SEKTORLER
except ImportError:
    st.error("config.py bulunamadı. Proje klasöründe çalıştırın.")
    st.stop()

# Bölge: şimdilik sadece NRW
bolge_secim = st.selectbox(
    "**Bölge**",
    options=["NRW"],
    index=0,
    help="Şu an sadece NRW destekleniyor.",
)

# Şehir: Tümü + NRW şehirleri
sehir_liste = ["Tümü"] + list(BOLGELER_NRW)
sehir_secim = st.selectbox(
    "**Şehir**",
    options=sehir_liste,
    index=0,
    help="Sadece bu şehre ait adresleri almak için seçin. 'Tümü' = tüm NRW.",
)

# Sektör: çoklu seçim (label ile göster)
sektor_opts = list(SEKTORLER.keys())
sektor_etiket = {k: SEKTORLER[k].get("label", k) for k in sektor_opts}
sektor_secim = st.multiselect(
    "**Sektör**",
    options=sektor_opts,
    default=[],
    format_func=lambda x: sektor_etiket.get(x, x),
    help="Boş bırakırsanız tüm sektörler dahil edilir.",
)

# Veri kaynağı
kaynak_secim = st.radio(
    "**Veri kaynağı**",
    options=[
        "Sadece OSM (ücretsiz)",
        "Sadece Google API",
        "OSM + Google API",
    ],
    index=0,
    horizontal=True,
    help="OSM = OpenStreetMap (ücretsiz, 1–3 dk sürebilir). Google = Places API (kota gerekir).",
)

if st.button("📥 Excel oluştur", type="primary"):
    sektorler = sektor_secim if sektor_secim else None
    sehir_filtre = None if sehir_secim == "Tümü" else sehir_secim
    google_dahil = "Google" in kaynak_secim
    sadece_google = kaynak_secim == "Sadece Google API"

    if sadece_google or google_dahil:
        # Önce Streamlit secrets'ten dene (Cloud ortamı)
        secret_key = None
        try:
            secret_key = st.secrets.get("GOOGLE_PLACES_API_KEY", None)
        except Exception:
            secret_key = None

        if secret_key:
            os.environ["GOOGLE_PLACES_API_KEY"] = secret_key
        else:
            # Lokal geliştirme: .env dosyasından oku
            from dotenv import load_dotenv
            load_dotenv()

        api_key = os.getenv("GOOGLE_PLACES_API_KEY", "")
        if not api_key or api_key == "your_api_key_here":
            st.warning("Google API kullanmak için Streamlit secrets veya .env dosyasında GOOGLE_PLACES_API_KEY tanımlayın.")
            if not sadece_google:
                st.info("Şimdilik sadece OSM ile devam ediliyor.")
                google_dahil = False
                sadece_google = False
            else:
                st.stop()

    spinner_msg = "Veri toplanıyor…"
    if not google_dahil and sehir_filtre:
        spinner_msg = "Veri toplanıyor (seçilen şehir + sektör, kısa sürebilir)…"
    elif not google_dahil:
        spinner_msg = "Veri toplanıyor (tüm NRW, OSM 1–3 dakika sürebilir)…"
    with st.spinner(spinner_msg):
        try:
            from firma_verisi_topla import veri_topla_ve_zenginlestir
            from export_utils import excel_bytes, google_maps_rota_url

            firmalar = veri_topla_ve_zenginlestir(
                sektorler=sektorler,
                sehir_filtre=sehir_filtre,
                google_dahil=google_dahil,
                sadece_google=sadece_google,
                max_google=80,
            )
        except Exception as e:
            st.error(f"Veri toplanırken hata: {e}")
            st.exception(e)
            st.stop()

    if not firmalar:
        st.warning("Seçtiğiniz kriterlere uyan işletme bulunamadı. Bölge, şehir veya sektörü değiştirip tekrar deneyin.")
        st.stop()

    excel_data = excel_bytes(firmalar)
    tarih = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    dosya_adi = f"turk_isletmeleri_nrw_{tarih}.xlsx"

    st.success(f"**{len(firmalar)}** işletme hazır. Aşağıdan indirin.")
    st.download_button(
        label="📥 Excel dosyasını indir",
        data=excel_data,
        file_name=dosya_adi,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )
    rota_url = google_maps_rota_url(firmalar)
    if rota_url:
        st.link_button(
            "🗺️ Tümünü Google Maps'te rota olarak aç (ilk 25 durak)",
            rota_url,
            help="Firmalar sırayla (HBF'ye yakından uzağa) tek haritada rota olarak açılır.",
        )
        components.html(
            f"""
            <iframe
                width="100%"
                height="600"
                style="border:0"
                loading="lazy"
                allowfullscreen
                referrerpolicy="no-referrer-when-downgrade"
                src="{rota_url}">
            </iframe>
            """,
            height=600,
        )
    st.caption("Excel’de Google_Maps_Link, North_Data_Link ve Website sütunları tıklanabilir linktir.")
