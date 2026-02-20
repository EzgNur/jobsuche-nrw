#!/usr/bin/env python3
"""
NRW'de özellikle TÜRK işletmelerinin verilerini toplar (firma adı, adres, telefon, web).
Varsayılan: Sadece ÜCRETSİZ kaynaklar (OpenStreetMap / Overpass API).
İsteğe bağlı: Google Places API ile ek sonuç (ücretli kotası vardır).
"""

import os
import time
from urllib.parse import quote

import requests

from export_utils import veri_yaz
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
BASE_URL = "https://maps.googleapis.com/maps/api/place"
LANGUAGE = "de"

# Google Places "types" -> işyeri sektörü (okunaklı)
GOOGLE_TYPE_TO_SEKTOR = {
    "restaurant": "Restaurant / Gastronomie",
    "food": "Gastronomie / Lebensmittel",
    "meal_takeaway": "Imbiss / Takeaway",
    "meal_delivery": "Essenslieferung",
    "cafe": "Café",
    "bakery": "Bäckerei",
    "bar": "Bar",
    "supermarket": "Supermarkt",
    "grocery_store": "Lebensmittelgeschäft",
    "store": "Einzelhandel",
    "convenience_store": "Spätkauf",
    "hair_care": "Friseur / Kosmetik",
    "beauty_salon": "Schönheitssalon",
    "moving_company": "Umzug / Spedition",
    "storage": "Lager / Logistik",
    "plumber": "Handwerk (Klempner)",
    "electrician": "Handwerk (Elektriker)",
    "general_contractor": "Bau / Generalunternehmer",
    "roofing_contractor": "Bau (Dach)",
    "cleaning_company": "Reinigung",
    "laundry": "Wäscherei",
    "lawyer": "Recht / Anwalt",
    "accounting": "Buchhaltung",
    "insurance_agency": "Versicherung",
    "real_estate_agency": "Immobilien",
    "travel_agency": "Reisebüro",
    "car_repair": "Kfz-Werkstatt",
    "gas_station": "Tankstelle",
    "pharmacy": "Apotheke",
    "doctor": "Arzt",
    "dentist": "Zahnarzt",
    "gym": "Fitness",
    "school": "Schule / Bildung",
    "point_of_interest": None,
    "establishment": None,
}


def _northdata_arama_metni(firma: str, adresse: str) -> str:
    """North Data için Google aramasında kullanılacak kısa metin: Firma + şehir (tam adres çok spesifik kalıyor)."""
    f = (firma or "").strip()
    # Adresin virgülden sonrası genelde PLZ + şehir (örn. "40215 Düsseldorf")
    adr = (adresse or "").strip()
    sehir_kismi = ""
    if "," in adr:
        sehir_kismi = adr.split(",")[-1].strip()
    elif adr:
        sehir_kismi = adr
    return f"{f} {sehir_kismi}".strip() or f or sehir_kismi


# ---------------------------------------------------------------------------
# ÜCRETSİZ KAYNAK: OpenStreetMap (Türk işletmeleri NRW)
# ---------------------------------------------------------------------------

def _osm_turk_nrw(
    sektorler: list[str] | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> list[dict]:
    """Ücretsiz: OSM'den NRW (veya verilen bbox) Türk işletmelerini al. bbox varsa sadece o alan sorgulanır (hızlı)."""
    try:
        from osm_turkish_nrw import turk_isletmeleri_nrw_topla
        if bbox:
            print("OpenStreetMap (Overpass) sorgulanıyor — seçilen şehir, kısa sürebilir...")
        else:
            print("OpenStreetMap (Overpass) sorgulanıyor — 1–3 dakika sürebilir, bekleyin...")
        return turk_isletmeleri_nrw_topla(sektorler=sektorler, bbox=bbox)
    except Exception as e:
        print(f"OSM kaynağı atlandı: {e}")
        return []


# ---------------------------------------------------------------------------
# İSTEĞE BAĞLI ÜCRETLİ: Google Places (Türk mutfağı / Türk işletmesi araması)
# ---------------------------------------------------------------------------

def text_search(query: str, api_key: str, next_page_token: str = None) -> dict:
    params = {
        "query": query,
        "key": api_key,
        "language": LANGUAGE,
        "region": "de",
    }
    if next_page_token:
        params["pagetoken"] = next_page_token
    r = requests.get(f"{BASE_URL}/textsearch/json", params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def place_details(place_id: str, api_key: str) -> dict | None:
    params = {
        "place_id": place_id,
        "key": api_key,
        "language": LANGUAGE,
        "fields": "name,formatted_address,formatted_phone_number,international_phone_number,website,types,geometry",
    }
    r = requests.get(f"{BASE_URL}/details/json", params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "OK":
        return None
    return data.get("result", {})


def _google_turk_nrw(
    max_firma: int = 40,
    sektorler: list[str] | None = None,
    sehir: str | None = None,
) -> list[dict]:
    """İsteğe bağlı: Google Places ile sektöre (ve isteğe bağlı şehre) göre aramalar."""
    if not API_KEY or API_KEY == "your_api_key_here":
        return []
    try:
        from config import SEKTORLER, SEKTOR_VARSAYILAN
        sec = sektorler if sektorler else SEKTOR_VARSAYILAN
        queries = []
        for sk in sec:
            if sk in SEKTORLER and "google_queries" in SEKTORLER[sk]:
                queries.extend(SEKTORLER[sk]["google_queries"])
        if not queries:
            queries = ["Türkisches Restaurant NRW", "Döner NRW", "Türkischer Supermarkt NRW"]
    except Exception:
        queries = ["Türkisches Restaurant NRW", "Döner NRW", "Türkischer Supermarkt NRW"]
    # Şehir seçiliyse aramayı o şehirle yap (örn. "Türkisches Restaurant Duisburg")
    if sehir and sehir.strip():
        yer = sehir.strip()
        queries = [q.replace(" NRW", f" {yer}").replace("Nrw", yer) for q in queries]
    sonuclar = []
    for query in queries:
        if len(sonuclar) >= max_firma:
            break
        try:
            data = text_search(query, API_KEY)
            if data.get("status") not in ("OK", "ZERO_RESULTS"):
                continue
            for pred in data.get("results", []):
                place_id = pred.get("place_id")
                if not place_id:
                    continue
                detay = place_details(place_id, API_KEY)
                telefon = ""
                website = ""
                sektor = "Sonstiges"
                lat, lon = None, None
                if detay:
                    telefon = detay.get("formatted_phone_number") or detay.get("international_phone_number") or ""
                    website = detay.get("website", "")
                    types_list = detay.get("types") or pred.get("types") or []
                    for t in types_list:
                        if t in GOOGLE_TYPE_TO_SEKTOR and GOOGLE_TYPE_TO_SEKTOR[t]:
                            sektor = GOOGLE_TYPE_TO_SEKTOR[t]
                            break
                    if sektor == "Sonstiges" and types_list:
                        sektor = types_list[0].replace("_", " ").title()
                    loc = detay.get("geometry", {}).get("location", {}) if detay.get("geometry") else {}
                    if loc:
                        lat, lon = loc.get("lat"), loc.get("lng")
                sonuclar.append({
                    "Firma": pred.get("name", ""),
                    "Adresse": pred.get("formatted_address", ""),
                    "Telefon": telefon,
                    "Website": website,
                    "Region": "NRW",
                    "Sektor": sektor,
                    "Quelle": "Google Places",
                    "lat": lat,
                    "lon": lon,
                })
                if len(sonuclar) >= max_firma:
                    break
                time.sleep(0.3)
        except Exception as e:
            print(f"Google araması atlandı ({query}): {e}")
        time.sleep(1)
    return sonuclar


# ---------------------------------------------------------------------------
# Birleştir ve CSV yaz
# ---------------------------------------------------------------------------

def _yelp_turk_nrw(max_sehir: int = 10, sektorler: list[str] | None = None) -> list[dict]:
    """Ücretsiz kota: Yelp Fusion API ile NRW Türk işletmeleri."""
    try:
        from yelp_turkish_nrw import turk_isletmeleri_yelp_nrw
        import os as _os
        key = _os.getenv("YELP_API_KEY")
        if not key or key == "your_yelp_api_key_here":
            return []
        print("Yelp Fusion API sorgulanıyor...")
        return turk_isletmeleri_yelp_nrw(api_key=key, max_sehir=max_sehir, sektorler=sektorler)
    except Exception as e:
        print(f"Yelp kaynağı atlandı: {e}")
        return []


def _birlestir_tekrarsiz(*listeler: list[dict]) -> list[dict]:
    """Aynı firma adı + adres tekrarını önle; tüm listeleri birleştirir."""
    gorulen = set()
    out = []
    for liste in listeler:
        for row in liste:
            key = (str(row.get("Firma", "")).strip().lower(), str(row.get("Adresse", "")).strip().lower())
            if key in gorulen or not row.get("Firma"):
                continue
            gorulen.add(key)
            out.append(row)
    return out


def topla_turk_isletmeleri_nrw(
    google_dahil: bool = False,
    yelp_dahil: bool = False,
    max_google: int = 40,
    max_yelp_sehir: int = 10,
    sektorler: list[str] | None = None,
    sadece_google: bool = False,
    sehir_filtre: str | None = None,
) -> list[dict]:
    """
    NRW'deki (veya seçilen şehirdeki) Türk işletmelerini toplar.
    sehir_filtre set edilirse OSM sadece o şehrin bbox'ında, Google o şehirle arama yapar.
    """
    bbox = None
    if sehir_filtre and str(sehir_filtre).strip():
        try:
            from config import SEHIR_BBOX
            bbox = SEHIR_BBOX.get(sehir_filtre.strip())
        except Exception:
            pass
    if sadece_google:
        firmalar = []
        n_osm = 0
    else:
        firmalar = _osm_turk_nrw(sektorler=sektorler, bbox=bbox)
        n_osm = len(firmalar)
    ekler = []
    if google_dahil and API_KEY and API_KEY != "your_api_key_here":
        print("Google Places API sorgulanıyor...")
        google_liste = _google_turk_nrw(max_firma=max_google, sektorler=sektorler, sehir=sehir_filtre)
        ekler.append(google_liste)
        if not sadece_google:
            print(f"  OSM: {n_osm} | Google: {len(google_liste)} (birleştiriliyor...)")
        else:
            print(f"  Google: {len(google_liste)} işletme alındı.")
    if yelp_dahil:
        ekler.append(_yelp_turk_nrw(max_sehir=max_yelp_sehir, sektorler=sektorler))
    if ekler:
        firmalar = _birlestir_tekrarsiz(firmalar, *ekler)
    return firmalar


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """İki koordinat arası mesafe (km)."""
    import math
    R = 6371  # Dünya yarıçapı km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _adresden_sehir(adresse: str) -> str:
    """Adres satırından şehir adı çıkarır (virgülden sonraki kısım)."""
    if not adresse or "," not in adresse:
        return ""
    return adresse.split(",")[-1].strip()


def firmalari_hbfye_gore_sirala(
    firmalar: list[dict],
    sehir_filtre: str | None = None,
) -> list[dict]:
    """
    Firmaları ilgili şehrin Hauptbahnhof'una uzaklığa göre sıralar (yakından uzağa).
    sehir_filtre varsa o şehrin HBF'si; yoksa her satırdaki adresten şehir çıkarılıp o şehrin HBF'si kullanılır.
    Koordinatı olmayan satırlar listenin sonuna atılır.
    """
    try:
        from config import SEHIR_HBF
    except Exception:
        return firmalar
    hbf = SEHIR_HBF

    def _mesafe(row: dict) -> float:
        lat, lon = row.get("lat"), row.get("lon")
        if lat is None or lon is None:
            return 1e9  # Koordinat yoksa en sona
        if sehir_filtre and sehir_filtre.strip():
            ref = hbf.get(sehir_filtre.strip())
        else:
            sehir = _adresden_sehir(row.get("Adresse") or "")
            ref = hbf.get(sehir) if sehir else None
        if ref is None:
            return 1e9
        return _haversine_km(ref[0], ref[1], float(lat), float(lon))

    return sorted(firmalar, key=_mesafe)


def firmalari_linklerle_zenginlestir(
    firmalar: list[dict],
    sektorler: list[str] | None = None,
) -> list[dict]:
    """Firma listesine Aranan_Sektorler, Google_Maps_Link, North_Data_Link, HRB ekler (mevcut satırları günceller)."""
    try:
        from config import SEKTORLER, SEKTOR_VARSAYILAN
        sec_keys = sektorler or SEKTOR_VARSAYILAN
        aranan_sektorler_str = ", ".join(SEKTORLER.get(sk, {}).get("label", sk) for sk in sec_keys)
    except Exception:
        aranan_sektorler_str = "tümü"
    for row in firmalar:
        row["Aranan_Sektorler"] = aranan_sektorler_str
        adres_arama = f"{row.get('Firma', '')} {row.get('Adresse', '')}".strip()
        row["Google_Maps_Link"] = "https://www.google.com/maps/search/?api=1&query=" + quote(adres_arama) if adres_arama else ""
        row.setdefault("HRB", "")
        hrb = (row.get("HRB") or "").strip()
        nd_arama = _northdata_arama_metni(row.get("Firma", ""), row.get("Adresse", ""))
        if hrb and nd_arama:
            firma_enc = quote(row.get("Firma", "").strip())
            sehir = (row.get("Adresse", "") or "").strip()
            if "," in sehir:
                sehir = sehir.split(",")[-1].strip()
            sehir_enc = quote(sehir)
            row["North_Data_Link"] = f"https://www.northdata.com/{firma_enc},%20{sehir_enc}/{quote(hrb)}"
        elif nd_arama:
            row["North_Data_Link"] = "https://www.google.com/search?q=" + quote("site:northdata.com " + nd_arama)
        else:
            row["North_Data_Link"] = "https://www.northdata.com/"
    return firmalar


def veri_topla_ve_zenginlestir(
    sektorler: list[str] | None = None,
    sehir_filtre: str | None = None,
    google_dahil: bool = False,
    sadece_google: bool = False,
    max_google: int = 40,
) -> list[dict]:
    """
    Bölge/şehir/sektör/kaynak seçimine göre veri toplar ve link sütunlarıyla zenginleştirir.
    sehir_filtre: Sadece bu şehri içeren adresleri tutar (örn. "Düsseldorf"). None = tümü.
    """
    firmalar = topla_turk_isletmeleri_nrw(
        google_dahil=google_dahil,
        sadece_google=sadece_google,
        max_google=max_google,
        sektorler=sektorler,
        sehir_filtre=sehir_filtre,
    )
    # Şehir seçiliyse sonuçlar zaten o şehirden; yine de adres filtresi (Google bazen başka şehir dönebilir)
    if sehir_filtre and sehir_filtre.strip():
        sehir = sehir_filtre.strip()
        firmalar = [r for r in firmalar if sehir in (r.get("Adresse") or "")]
    firmalar = firmalari_linklerle_zenginlestir(firmalar, sektorler=sektorler)
    # Sadece tek şehir seçildiyse HBF'ye yakınlığa göre sırala (Düsseldorf, Duisburg vb.)
    if sehir_filtre and sehir_filtre.strip():
        firmalar = firmalari_hbfye_gore_sirala(firmalar, sehir_filtre=sehir_filtre)
    for r in firmalar:
        r.pop("lat", None)
        r.pop("lon", None)
    return firmalar


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="NRW'de Türk işletmelerini toplar (varsayılan: sadece ücretsiz kaynaklar)."
    )
    parser.add_argument(
        "--cikti", "-o",
        default="turk_isletmeleri_nrw.csv",
        help="Çıktı dosyası (CSV veya .xlsx = Excel)",
    )
    parser.add_argument(
        "--google",
        action="store_true",
        help="Google Places API ile ek arama yap (API anahtarı gerekir, ücretli kota)",
    )
    parser.add_argument(
        "--max-google",
        type=int,
        default=40,
        help="Google ile alınacak maksimum ek firma (varsayılan 40)",
    )
    parser.add_argument(
        "--yelp",
        action="store_true",
        help="Yelp Fusion API ile ek arama (ücretsiz kota, API anahtarı gerekir)",
    )
    parser.add_argument(
        "--max-yelp-sehir",
        type=int,
        default=10,
        help="Yelp ile kaç NRW şehrinde aranacak (varsayılan 10)",
    )
    parser.add_argument(
        "--sektor",
        "-s",
        type=str,
        default="",
        help="Sektörler (virgülle: restoran,lojistik,temizlik,bau,nakliye,kuaför,market,güvenlik,yazılım,danışmanlık). Boş = hepsi",
    )
    parser.add_argument(
        "--tarihli",
        action="store_true",
        help="Her çalıştırmada ayrı dosya: çıktı adına tarih-saat eklenir (örn. sonuc_2026-02-20_14-30.xlsx)",
    )
    parser.add_argument(
        "--sadece-google",
        action="store_true",
        help="OSM kullanma, sadece Google Places ile veri topla (--google ile birlikte kullanın)",
    )
    args = parser.parse_args()

    sektorler = None
    if args.sektor and args.sektor.strip():
        sektorler = [x.strip().lower() for x in args.sektor.split(",") if x.strip()]

    # Tarihli dosya adı (her çalıştırma ayrı dosya)
    cikti_dosya = args.cikti
    if args.tarihli:
        import datetime
        taban, ext = os.path.splitext(args.cikti)
        cikti_dosya = f"{taban}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')}{ext}"

    if args.sadece_google and not args.google:
        args.google = True  # sadece-google verilince Google'ı otomatik aç
    print("NRW'de Türk işletmeleri toplanıyor...")
    firmalar = topla_turk_isletmeleri_nrw(
        google_dahil=args.google,
        yelp_dahil=args.yelp,
        max_google=args.max_google,
        max_yelp_sehir=args.max_yelp_sehir,
        sektorler=sektorler,
        sadece_google=args.sadece_google,
    )

    firmalar = firmalari_linklerle_zenginlestir(firmalar, sektorler=sektorler)
    for r in firmalar:
        r.pop("lat", None)
        r.pop("lon", None)
    veri_yaz(cikti_dosya, firmalar)
    print(f"{len(firmalar)} işletme '{cikti_dosya}' dosyasına yazıldı.")


if __name__ == "__main__":
    main()
