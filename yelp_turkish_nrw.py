#!/usr/bin/env python3
"""
NRW'de Türk işletmelerini Yelp Fusion API ile toplar (ücretsiz kota: günde 5000 istek).
API anahtarı: https://www.yelp.com/developers/v3/manage_app
"""

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

YELP_API_KEY = os.getenv("YELP_API_KEY")
YELP_SEARCH_URL = "https://api.yelp.com/v3/businesses/search"

from config import BOLGELER_NRW, SEKTORLER


def _yelp_arama(api_key: str, term: str, location: str, limit: int = 50, offset: int = 0) -> dict:
    """Yelp Fusion API v3 business search."""
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "term": term,
        "location": f"{location}, Germany",
        "limit": min(limit, 50),
        "offset": offset,
    }
    r = requests.get(YELP_SEARCH_URL, headers=headers, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def _adres_from_location(loc: dict) -> str:
    """Yelp location objesinden adres satırı."""
    if not loc:
        return ""
    parcalar = []
    if loc.get("address1"):
        parcalar.append(loc["address1"])
    if loc.get("address2"):
        parcalar.append(loc["address2"])
    if loc.get("city"):
        parcalar.append(loc["city"])
    if loc.get("zip_code"):
        parcalar.append(loc["zip_code"])
    if loc.get("country"):
        parcalar.append(loc["country"])
    return ", ".join(parcalar)


def turk_isletmeleri_yelp_nrw(
    api_key: str = None,
    max_sehir: int = 10,
    limit_per_sehir: int = 50,
    sektorler: list[str] | None = None,
) -> list[dict]:
    """
    Yelp'ten NRW'deki Türk işletmelerini toplar.
    sektorler: restoran, market, lojistik, temizlik, bau, nakliye, kuaför, ... (config.SEKTORLER)
    Boş/None = config.SEKTOR_VARSAYILAN veya tüm sektörlerin terimleri.
    """
    key = api_key or YELP_API_KEY
    if not key or key == "your_yelp_api_key_here":
        return []

    sec = list(sektorler) if sektorler else None
    try:
        varsayilan = getattr(__import__("config", fromlist=["SEKTOR_VARSAYILAN"]), "SEKTOR_VARSAYILAN", list(SEKTORLER.keys()))
    except Exception:
        varsayilan = list(SEKTORLER.keys())
    kullanilacak = sec if sec else varsayilan

    arama_terimleri = []
    for sk in kullanilacak:
        if sk in SEKTORLER and "yelp_terms" in SEKTORLER[sk]:
            arama_terimleri.extend(SEKTORLER[sk]["yelp_terms"])
    if not arama_terimleri:
        arama_terimleri = ["turkish restaurant", "döner", "türkisches restaurant"]

    gorulen = set()
    sonuclar = []

    sehirler = BOLGELER_NRW[:max_sehir]
    for sehir in sehirler:
        for term in arama_terimleri:
            try:
                data = _yelp_arama(key, term, sehir, limit=limit_per_sehir, offset=0)
                for b in data.get("businesses", []):
                    name = (b.get("name") or "").strip()
                    loc = b.get("location") or {}
                    adres = _adres_from_location(loc)
                    key_dedup = (name.lower(), adres.lower())
                    if key_dedup in gorulen:
                        continue
                    gorulen.add(key_dedup)
                    sonuclar.append({
                        "Firma": name,
                        "Adresse": adres or "-",
                        "Telefon": b.get("display_phone") or b.get("phone") or "",
                        "Website": b.get("url") or "",
                        "Region": sehir,
                        "Sektor": term,
                        "Quelle": "Yelp",
                    })
                time.sleep(0.5)
            except Exception as e:
                continue
        time.sleep(0.3)

    return sonuclar


def main():
    import argparse
    parser = argparse.ArgumentParser(description="NRW Türk işletmeleri — Yelp Fusion API.")
    parser.add_argument("-o", "--cikti", default="yelp_turk_nrw.csv", help="Çıktı (CSV veya .xlsx)")
    parser.add_argument("--max-sehir", type=int, default=10, help="Kaç NRW şehrinde aranacak (varsayılan 10)")
    parser.add_argument("--sektor", "-s", type=str, default="", help="Sektörler (virgülle: restoran,lojistik,temizlik,...). Boş = hepsi")
    args = parser.parse_args()
    sektorler = [x.strip().lower() for x in args.sektor.split(",") if x.strip()] if args.sektor else None

    from export_utils import veri_yaz
    print("Yelp Fusion API ile NRW Türk işletmeleri aranıyor...")
    firmalar = turk_isletmeleri_yelp_nrw(max_sehir=args.max_sehir, sektorler=sektorler)
    veri_yaz(args.cikti, firmalar)
    print(f"{len(firmalar)} işletme '{args.cikti}' dosyasına yazıldı.")


if __name__ == "__main__":
    main()
