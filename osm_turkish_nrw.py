#!/usr/bin/env python3
"""
NRW'de Türk işletmelerini ÜCRETSİZ toplar (OpenStreetMap / Overpass API).
Firma sahibinin Türk olduğu, mutfak/isim/ticaret türü ile çıkarımlanır:
- cuisine=turkish, cuisine=döner, vb.
- İsimde Türk, Turkish, Döner, Anatolien, Istanbul, Ankara geçen işletmeler
- Türk market, berber, restoran vb. shop/amenity etiketleri
API anahtarı gerekmez; tamamen ücretsizdir.
"""

import time

import requests

from export_utils import veri_yaz

# NRW (Nordrhein-Westfalen) sınır kutusu: güney, batı, kuzey, doğu
NRW_BBOX = (50.0, 5.8, 52.6, 9.5)

# Önce bu sunucu; 504/timeout olursa alternatif kullanılır
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_ALTERNATIV = "https://overpass.kumi.systems/api/interpreter"
OVERPASS_SUNUCULARI = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# NRW'yi timeout'u azaltmak için kaç parçaya böleceğiz (2x2 = 4 bölge)
NRW_GRID_ROWS = 2
NRW_GRID_COLS = 2
OVERPASS_TIMEOUT_SANIYE = 60
REQUESTS_TIMEOUT_SANIYE = 120


def _nrw_alt_bboxlar() -> list[tuple[float, float, float, float]]:
    """NRW bbox'ı grid parçalara böler (timeout'u azaltmak için). (south, west, north, east) listesi."""
    south, west, north, east = NRW_BBOX
    bboxlar = []
    for row in range(NRW_GRID_ROWS):
        for col in range(NRW_GRID_COLS):
            s = south + (north - south) * row / NRW_GRID_ROWS
            n = south + (north - south) * (row + 1) / NRW_GRID_ROWS
            w = west + (east - west) * col / NRW_GRID_COLS
            e_ = west + (east - west) * (col + 1) / NRW_GRID_COLS
            bboxlar.append((s, w, n, e_))
    return bboxlar


def overpass_sorgu_restoran(south: float, west: float, north: float, east: float) -> str:
    """Sadece restoran / mutfak / market (cuisine, amenity, shop)."""
    return f"""
    [out:json][timeout:{OVERPASS_TIMEOUT_SANIYE}];
    (
      node["cuisine"="turkish"]({south},{west},{north},{east});
      node["cuisine"="türkisch"]({south},{west},{north},{east});
      node["cuisine"="döner"]({south},{west},{north},{east});
      node["cuisine"="kebab"]({south},{west},{north},{east});
      node["amenity"]["name"~"Türk|Turkish|Döner|Anatolien|Kebab|Kebap",i]({south},{west},{north},{east});
      node["shop"]["name"~"Türk|Turkish|Anatolien",i]({south},{west},{north},{east});
      way["cuisine"="turkish"]({south},{west},{north},{east});
      way["cuisine"="döner"]({south},{west},{north},{east});
      way["amenity"]["name"~"Türk|Döner|Kebab",i]({south},{west},{north},{east});
    );
    out body;
    >;
    out skel qt;
    """


def overpass_sorgu_diger_sektorler(south: float, west: float, north: float, east: float) -> str:
    """İsimde Türk geçen ofis, dükkan, atölye (lojistik, temizlik, inşaat vb.)."""
    return f"""
    [out:json][timeout:{OVERPASS_TIMEOUT_SANIYE}];
    (
      node["office"]["name"~"Türk|Turkish",i]({south},{west},{north},{east});
      node["shop"]["name"~"Türk|Turkish",i]({south},{west},{north},{east});
      node["craft"]["name"~"Türk|Turkish",i]({south},{west},{north},{east});
      way["office"]["name"~"Türk|Turkish",i]({south},{west},{north},{east});
      way["shop"]["name"~"Türk|Turkish",i]({south},{west},{north},{east});
      way["craft"]["name"~"Türk|Turkish",i]({south},{west},{north},{east});
    );
    out body;
    >;
    out skel qt;
    """


def _hangi_osm_sorgulari(sektorler: list[str] | None) -> tuple[bool, bool]:
    """(restoran_sorgusu_mu, diger_sektorler_sorgusu_mu) döner."""
    try:
        from config import SEKTORLER
        sec = set(sektorler or [])
        restoran_dahil = "restoran" in sec or "market" in sec or not sec
        diger_dahil = bool(sec - {"restoran", "market"}) or not sec
        return (restoran_dahil, diger_dahil)
    except Exception:
        return (True, True)


def _etiket(elem: dict, key: str, default: str = "") -> str:
    tags = elem.get("tags") or {}
    return (tags.get(key) or "").strip() or default


def _adres_birlestir(elem: dict) -> str:
    """OSM tags'den adres satırı oluştur."""
    tags = elem.get("tags") or {}
    parcalar = []
    if tags.get("addr:street"):
        s = tags.get("addr:street", "")
        if tags.get("addr:housenumber"):
            s += " " + tags.get("addr:housenumber", "")
        parcalar.append(s)
    if tags.get("addr:postcode"):
        parcalar.append(tags.get("addr:postcode", ""))
    if tags.get("addr:city"):
        parcalar.append(tags.get("addr:city", ""))
    if not parcalar and tags.get("addr:full"):
        return tags.get("addr:full", "")
    return ", ".join(parcalar)


def _osm_elemanlarini_firmalara_cevir(elements: list[dict]) -> list[dict]:
    """Overpass JSON çıktısındaki node/way'leri Firma, Adresse, Telefon, Website listesine çevirir."""
    gorulen_isimler = set()
    firmalar = []
    for elem in elements:
        if elem.get("type") not in ("node", "way"):
            continue
        name = _etiket(elem, "name") or _etiket(elem, "name:de") or _etiket(elem, "name:en")
        if not name and not (_etiket(elem, "cuisine") or _etiket(elem, "amenity") or _etiket(elem, "shop") or _etiket(elem, "office") or _etiket(elem, "craft")):
            continue
        if not name:
            name = "Unbenannt"
        # Aynı isim + aynı adres tekrarlarını azalt
        adres = _adres_birlestir(elem)
        key = (name.strip().lower(), adres.strip().lower())
        if key in gorulen_isimler:
            continue
        gorulen_isimler.add(key)

        telefon = _etiket(elem, "phone") or _etiket(elem, "contact:phone")
        website = _etiket(elem, "website") or _etiket(elem, "contact:website")
        cuisine = _etiket(elem, "cuisine")
        shop = _etiket(elem, "shop")
        amenity = _etiket(elem, "amenity")
        office = _etiket(elem, "office")
        craft = _etiket(elem, "craft")
        sektor = cuisine or shop or amenity or office or craft or ""
        # Konum: HBF'ye uzaklık sıralaması için (node: doğrudan; way: bounds merkezi)
        lat, lon = None, None
        if elem.get("type") == "node":
            lat, lon = elem.get("lat"), elem.get("lon")
        elif elem.get("type") == "way" and elem.get("bounds"):
            b = elem["bounds"]
            lat = (b.get("minlat", 0) + b.get("maxlat", 0)) / 2 if b.get("minlat") is not None else None
            lon = (b.get("minlon", 0) + b.get("maxlon", 0)) / 2 if b.get("minlon") is not None else None

        firmalar.append({
            "Firma": name,
            "Adresse": adres or "-",
            "Telefon": telefon,
            "Website": website,
            "Region": "NRW",
            "Sektor": sektor,
            "Quelle": "OpenStreetMap",
            "lat": lat,
            "lon": lon,
        })
    return firmalar


def overpass_istek(sorgu: str) -> list[dict]:
    """Overpass API'ye istek atar; 504/timeout veya geçersiz JSON olursa yedek sunucu dener."""
    son_hata = None
    for url in OVERPASS_SUNUCULARI:
        try:
            r = requests.post(url, data={"data": sorgu}, timeout=REQUESTS_TIMEOUT_SANIYE)
            r.raise_for_status()
            # Boş veya HTML yanıt JSON parse'ı patlatır; önce kontrol et
            icerik = r.text.strip()
            if not icerik or not icerik.startswith("{"):
                son_hata = RuntimeError(
                    "Overpass JSON yerine boş veya HTML döndü (ağ/proxy sorunu olabilir)."
                )
                continue
            data = r.json()
            elements = [
                e for e in data.get("elements", [])
                if e.get("type") in ("node", "way")
            ]
            remark = data.get("remark", "")
            if remark and "error" in remark.lower():
                continue
            return elements
        except requests.RequestException as e:
            if getattr(e, "response", None) and getattr(e.response, "status_code", None) == 504:
                son_hata = e
                continue
            if "timeout" in str(e).lower() or "Timeout" in type(e).__name__:
                son_hata = e
                continue
            raise
        except ValueError as e:
            son_hata = RuntimeError(
                "Overpass yanıtı geçerli JSON değil (sunucu hata sayfası dönmüş olabilir). "
                "VPN/proxy kapatıp tekrar deneyin veya bir süre sonra tekrar deneyin."
            )
            continue
    raise son_hata if son_hata else RuntimeError(
        "Overpass sunucuları yanıt vermedi. Bir süre sonra tekrar deneyin."
    )


def _overpass_minimal_sorgu(south: float, west: float, north: float, east: float) -> str:
    """Yedek: Sadece cuisine=turkish node'ları (en basit sorgu)."""
    return f"""
    [out:json][timeout:{OVERPASS_TIMEOUT_SANIYE}];
    node["cuisine"="turkish"]({south},{west},{north},{east});
    out body;
    """


def turk_isletmeleri_nrw_topla(
    sektorler: list[str] | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> list[dict]:
    """
    NRW'deki (veya verilen bbox'taki) Türk işletmelerini Overpass API ile toplar (ücretsiz).
    bbox verilirse sadece o alan sorgulanır (tek şehir, hızlı); None ise tüm NRW grid ile.
    sektorler: restoran, market, lojistik, ... Boş = tüm sektörler.
    """
    if bbox is not None:
        south, west, north, east = bbox
        bboxlar = [(south, west, north, east)]
    else:
        bboxlar = _nrw_alt_bboxlar()
    restoran_q, diger_q = _hangi_osm_sorgulari(sektorler)
    elements = []
    n_bbox = len(bboxlar)
    for i, (south, west, north, east) in enumerate(bboxlar):
        try:
            if restoran_q:
                elements.extend(overpass_istek(overpass_sorgu_restoran(south, west, north, east)))
            if diger_q:
                elements.extend(overpass_istek(overpass_sorgu_diger_sektorler(south, west, north, east)))
            if i < n_bbox - 1:
                time.sleep(2)
        except RuntimeError:
            continue
    if not elements and restoran_q:
        for south, west, north, east in bboxlar:
            try:
                elements.extend(overpass_istek(_overpass_minimal_sorgu(south, west, north, east)))
                break
            except RuntimeError:
                continue
    firmalar = _osm_elemanlarini_firmalara_cevir(elements)
    return firmalar


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="NRW'de Türk işletmelerini ücretsiz toplar (OpenStreetMap)."
    )
    parser.add_argument(
        "--cikti", "-o",
        default="turk_isletmeleri_nrw.csv",
        help="Çıktı dosyası (CSV veya .xlsx = Excel)",
    )
    parser.add_argument(
        "--sektor", "-s",
        type=str,
        default="",
        help="Sektörler (virgülle: restoran,lojistik,temizlik,bau,...). Boş = hepsi",
    )
    args = parser.parse_args()
    sektorler = [x.strip().lower() for x in args.sektor.split(",") if x.strip()] if args.sektor else None

    print("NRW'de Türk işletmeleri aranıyor (OpenStreetMap, ücretsiz) — 1–3 dakika sürebilir...")
    firmalar = turk_isletmeleri_nrw_topla(sektorler=sektorler)
    veri_yaz(args.cikti, firmalar)
    print(f"{len(firmalar)} işletme '{args.cikti}' dosyasına yazıldı.")


if __name__ == "__main__":
    main()
