# NRW (Nordrhein-Westfalen) – Türk işletmeleri projesi

# NRW büyük şehirler
# Şehir adı -> (güney, batı, kuzey, doğu) bbox; OSM tek şehir sorgusu için
SEHIR_BBOX = {
    "Köln": (50.89, 6.85, 51.02, 7.15),
    "Düsseldorf": (51.15, 6.72, 51.28, 6.92),
    "Dortmund": (51.45, 7.37, 51.58, 7.62),
    "Essen": (51.38, 6.92, 51.52, 7.15),
    "Duisburg": (51.38, 6.68, 51.48, 6.82),
    "Bochum": (51.43, 7.15, 51.52, 7.30),
    "Wuppertal": (51.22, 7.08, 51.28, 7.25),
    "Bielefeld": (51.95, 8.48, 52.06, 8.58),
    "Bonn": (50.68, 7.05, 50.76, 7.22),
    "Münster": (51.90, 7.55, 52.02, 7.68),
    "Mönchengladbach": (51.16, 6.40, 51.24, 6.52),
    "Gelsenkirchen": (51.48, 7.05, 51.58, 7.15),
    "Aachen": (50.74, 6.05, 50.82, 6.18),
    "Krefeld": (51.30, 6.52, 51.38, 6.65),
    "Oberhausen": (51.44, 6.82, 51.52, 6.95),
    "Hagen": (51.32, 7.42, 51.42, 7.52),
    "Hamm": (51.64, 7.76, 51.72, 7.88),
    "Mülheim": (51.40, 6.86, 51.48, 6.92),
    "Leverkusen": (51.00, 6.95, 51.08, 7.08),
    "Solingen": (51.14, 7.02, 51.20, 7.15),
    "Herne": (51.51, 7.18, 51.56, 7.25),
    "Neuss": (51.16, 6.66, 51.24, 6.73),
    "Paderborn": (51.70, 8.70, 51.78, 8.82),
}

# Her şehrin Hauptbahnhof (ana tren istasyonu) koordinatları (lat, lon) — HBF'ye yakınlığa göre sıralama için
SEHIR_HBF = {
    "Köln": (50.9425, 6.9585),
    "Düsseldorf": (51.2202, 6.7945),
    "Dortmund": (51.5179, 7.4594),
    "Essen": (51.4514, 7.0139),
    "Duisburg": (51.4300, 6.7761),
    "Bochum": (51.4788, 7.2227),
    "Wuppertal": (51.2562, 7.1506),
    "Bielefeld": (52.0286, 8.5321),
    "Bonn": (50.7319, 7.0970),
    "Münster": (51.9566, 7.6329),
    "Mönchengladbach": (51.1962, 6.4453),
    "Gelsenkirchen": (51.5062, 7.0986),
    "Aachen": (50.7672, 6.0912),
    "Krefeld": (51.3311, 6.5622),
    "Oberhausen": (51.4731, 6.8514),
    "Hagen": (51.3606, 7.4631),
    "Hamm": (51.6800, 7.8089),
    "Mülheim": (51.4272, 6.8828),
    "Leverkusen": (51.0456, 6.9889),
    "Solingen": (51.1647, 7.0847),
    "Herne": (51.5383, 7.2256),
    "Neuss": (51.2042, 6.6872),
    "Paderborn": (51.7194, 8.7543),
}

BOLGELER_NRW = [
    "Köln",
    "Düsseldorf",
    "Dortmund",
    "Essen",
    "Duisburg",
    "Bochum",
    "Wuppertal",
    "Bielefeld",
    "Bonn",
    "Münster",
    "Mönchengladbach",
    "Gelsenkirchen",
    "Aachen",
    "Krefeld",
    "Oberhausen",
    "Hagen",
    "Hamm",
    "Mülheim",
    "Leverkusen",
    "Solingen",
    "Herne",
    "Neuss",
    "Paderborn",
]

BOLGELER = BOLGELER_NRW

# Sektörler: her biri için OSM / Yelp / Google arama terimleri
# Komut: --sektor restoran,lojistik,temizlik veya --sektor hepsi
SEKTORLER = {
    "restoran": {
        "label": "Restoran / Gastronomi",
        "yelp_terms": ["turkish restaurant", "döner", "türkisches restaurant", "türkische küche"],
        "google_queries": ["Türkisches Restaurant NRW", "Döner NRW", "Türkischer Imbiss NRW"],
        "osm_restoran": True,  # Özel: mutfak/restoran Overpass sorgusu kullan
    },
    "market": {
               "label": "Market / Lebensmittel",
        "yelp_terms": ["türkischer supermarkt", "türkischer markt", "oriental supermarket"],
        "google_queries": ["Türkischer Supermarkt NRW", "Türkischer Markt NRW"],
        "osm_restoran": False,
    },
    "lojistik": {
        "label": "Lojistik / Spedition",
        "yelp_terms": ["türkische Spedition", "Logistik", "transport company"],
        "google_queries": ["Türkische Spedition NRW", "Türkisches Logistikunternehmen NRW"],
        "osm_restoran": False,
    },
    "temizlik": {
        "label": "Temizlik / Reinigung",
        "yelp_terms": ["türkisches Reinigungsunternehmen", "Reinigung", "cleaning service"],
        "google_queries": ["Türkisches Reinigungsunternehmen NRW", "Reinigungsfirma NRW"],
        "osm_restoran": False,
    },
    "bau": {
        "label": "İnşaat / Bau",
        "yelp_terms": ["türkisches Bauunternehmen", "Bau", "construction"],
        "google_queries": ["Türkisches Bauunternehmen NRW", "Türkischer Handwerker NRW"],
        "osm_restoran": False,
    },
    "nakliye": {
        "label": "Nakliye / Umzug",
        "yelp_terms": ["türkische Umzugsfirma", "Umzug", "Möbeltransport"],
        "google_queries": ["Türkische Umzugsfirma NRW", "Umzugsunternehmen NRW"],
        "osm_restoran": False,
    },
    "kuaför": {
        "label": "Kuaför / Friseur",
        "yelp_terms": ["türkischer Friseur", "Friseur", "barber"],
        "google_queries": ["Türkischer Friseur NRW", "türkischer Barbier NRW"],
        "osm_restoran": False,
    },
    "güvenlik": {
        "label": "Güvenlik / Sicherheit",
        "yelp_terms": ["Sicherheitsdienst", "security company"],
        "google_queries": ["Türkischer Sicherheitsdienst NRW", "Sicherheitsfirma NRW"],
        "osm_restoran": False,
    },
    "yazılım": {
        "label": "Yazılım / IT",
        "yelp_terms": ["türkische IT Firma", "Software", "IT Dienstleistung"],
        "google_queries": ["Türkische IT Firma NRW", "Software Unternehmen NRW"],
        "osm_restoran": False,
    },
    "danışmanlık": {
        "label": "Danışmanlık / Beratung",
        "yelp_terms": ["Beratung", "consulting", "Steuerberatung"],
        "google_queries": ["Türkische Beratungsfirma NRW", "Unternehmensberatung NRW"],
        "osm_restoran": False,
    },
}

# Varsayılan sektör listesi (--sektor verilmezse bunlar kullanılır; boş = hepsi)
SEKTOR_VARSAYILAN = ["restoran", "market", "lojistik", "temizlik", "bau", "nakliye", "kuaför"]
