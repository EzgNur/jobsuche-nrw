# Jobsuche – NRW Türk İşletmeleri (Ücretsiz Veri)

Bu proje **Almanya NRW** bölgesinde, **sahibi/özelliği Türk olan işletmelerin** verilerini toplar: **firma adı**, **adres**, **telefon**, **web sitesi**. Mümkün olduğunca **ücretsiz** kaynaklardan veri alır.

## Türk işletmesi nasıl tespit ediliyor?

Açık verilerde “firma sahibi Türk” bilgisi bulunmaz. Bu yüzden **dolaylı göstergeler** kullanılır:

- **OpenStreetMap:** `cuisine=turkish`, `cuisine=döner`, `cuisine=kebab` veya isimde **Türk, Turkish, Döner, Anatolien, Istanbul, Ankara** geçen restoran, kafe, fast food, market vb.
- Bu etiketler genelde Türk mutfağı / Türk işletmesi ile eşleşir; liste bire bir “Türk sahip” garantisi vermez ama pratikte büyük kısmı Türk işletmesidir.

## Veri kaynakları

| Kaynak | Açıklama | Ücret |
|--------|----------|--------|
| **OpenStreetMap (Overpass API)** | NRW içinde Türk mutfağı ve isimde Türk/Döner geçen işletmeler | **Ücretsiz**, API anahtarı yok |
| **Yelp Fusion API** | NRW şehirlerinde "turkish restaurant", "döner" araması | **Ücretsiz kota** (günde 5000 istek), API anahtarı gerekir |
| **Google Places API** | "Türkisches Restaurant NRW", "Döner NRW" vb. | Ücretli kota, API anahtarı gerekir |

## Kurulum

1. **Python 3.9+** yüklü olsun.

2. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

3. **Sadece OSM** kullanacaksanız başka ayar gerekmez.  
   **Google** kullanacaksanız: [Google Cloud Console](https://console.cloud.google.com/) → Proje → Places API etkinleştir → API key oluştur → `.env` dosyasına `GOOGLE_PLACES_API_KEY=...` yazın (bkz. `.env.example`).  
   (İsteğe bağlı: **Yelp** için [Yelp Developers](https://www.yelp.com/developers/v3/manage_app) → API Key → `.env` içine `YELP_API_KEY=...`.)

## Scriptleri nasıl çalıştırırsınız?

1. **Terminal açın** (Mac: Terminal veya Cursor içinde Terminal).
2. **Proje klasörüne gidin:**
   ```bash
   cd /Users/ezginuruyaroglu/Desktop/Jobsuche
   ```
3. **İlk kez kullanıyorsanız bağımlılıkları yükleyin:**
   ```bash
   pip3 install -r requirements.txt
   ```
4. **Aşağıdaki komutlardan birini çalıştırın** (Python komutu sisteminizde `python` veya `python3` olabilir; çalışmazsa diğerini deneyin).

---

## Web arayüzü (bölge / şehir / sektör / kaynak seçerek Excel)

Bölge, şehir, sektör ve veri kaynağını (OSM / Google API / OSM+Google) seçip tek tıkla Excel indirebilirsiniz. Excel’de **Google Maps**, **North Data** ve **Website** sütunları tıklanabilir linktir.

1. Bağımlılıkları yükleyin: `pip install -r requirements.txt` (Streamlit dahil).
2. Tarayıcıda arayüzü açın:
   ```bash
   streamlit run app_ui.py
   ```
3. Açılan sayfada **Bölge** (şu an NRW), **Şehir** (Tümü veya tek şehir), **Sektör** (çoklu seçim, boş = tümü) ve **Veri kaynağı** (Sadece OSM / Sadece Google API / OSM + Google API) seçin.
4. **Excel oluştur** butonuna tıklayın. Veri toplandıktan sonra **Excel dosyasını indir** ile .xlsx indirilir.

OSM seçiliyse ilk veri toplama 1–3 dakika sürebilir.

---

## Yayınlama (başkalarının erişebilmesi)

Arayüzü sadece kendi bilgisayarında değil, internette yayınlamak için **Streamlit Community Cloud** (ücretsiz) kullanabilirsiniz. Başkaları tarayıcıdan sizin paylaştığınız linke girip Excel oluşturabilir.

### Adımlar

1. **Projeyi GitHub’a yükleyin**
   - [GitHub](https://github.com) → New repository.
   - Proje klasörünü repo olarak başlatıp kodu push edin. `.env` dosyası `.gitignore`’da olduğu için repo’ya **girmemeli** (API anahtarları açığa çıkmaz).

2. **Streamlit Cloud’a bağlayın**
   - [share.streamlit.io](https://share.streamlit.io) → GitHub ile giriş yapın.
   - **New app** → Repository: `kullanici_adiniz/jobsuche`, Branch: `main`, Main file path: **`app_ui.py`**.
   - **Advanced settings**’e tıklayın; **Secrets** alanına aşağıdaki gibi yapıştırın (Google kullanacaksanız):

   ```toml
   GOOGLE_PLACES_API_KEY = "buraya_google_api_anahtariniz"
   # İsteğe bağlı:
   # OPENREGISTER_API_KEY = "openregister_anahtari"
   ```

   Bu değerler sunucuda `.env` gibi kullanılır; herkese açık sayfada görünmez.

3. **Deploy**’a tıklayın. Birkaç dakika sonra uygulama yayında olur; size bir link verilir (örn. `https://jobsuche-xxx.streamlit.app`). Bu linki paylaşırsanız herkes arayüze erişebilir.

### Dikkat

- **Google Places** kullanıyorsanız API anahtarınız **sizin** Google Cloud kotanızdan tüketilir; başkaları arayüzü kullandıkça sizin krediniz azalır. İsterseniz kotaları veya anahtarı kısıtlayabilirsiniz.
- **OSM**, Streamlit sunucularından bazen timeout/engel alabiliyor; yayında da “OSM kaynağı atlandı” görebilirsiniz. O zaman kullanıcılar sadece Google (veya sadece OSM’nin çalıştığı anlar) ile devam eder.

Alternatif olarak projeyi **Railway**, **Render**, **Google Cloud Run** veya kendi VPS’inizde de çalıştırabilirsiniz; Streamlit’i `streamlit run app_ui.py --server.port=8080` gibi bir portla başlatıp dışarıya açmanız yeterli.

---

## Kullanım (komut satırı)

### Sadece OSM (ücretsiz, Google/Yelp yok)

```bash
# Tek dosya (her çalıştırmada üzerine yazar)
python3 firma_verisi_topla.py -o turk_isletmeleri_nrw.xlsx

# Her çalıştırmada ayrı dosya (tarihli) + sektör + Google Maps linki Excel’de
python3 firma_verisi_topla.py --tarihli -o turk_isletmeleri_nrw.xlsx
```

Çıktı varsayılan: `turk_isletmeleri_nrw.csv`

Farklı dosya adı veya **Excel** çıktısı:

```bash
python firma_verisi_topla.py -o sonuclar.csv
python firma_verisi_topla.py -o turk_isletmeleri_nrw.xlsx
```

Çıktı dosyası `.xlsx` ile bitiyorsa veriler **Excel** formatında yazılır; aksi halde CSV.

### OSM + Yelp (ücretsiz / ücretsiz kota)

Yelp API anahtarınızı `.env` içine ekledikten sonra:

```bash
python firma_verisi_topla.py --yelp -o turk_isletmeleri_nrw.xlsx
```

### OSM + Google (ek sonuç, ücretli kota)

Google Places API anahtarınız varsa:

```bash
python firma_verisi_topla.py --google -o turk_isletmeleri_nrw.csv
```

### Sektör seçimi (restoran dışında: lojistik, temizlik, inşaat vb.)

Sadece belirli sektörlerde arama yapmak için `--sektor` kullanın (virgülle ayırın):

```bash
# Sadece lojistik ve temizlik
python firma_verisi_topla.py --sektor lojistik,temizlik -o lojistik_temizlik.xlsx

# Sadece inşaat ve nakliye
python firma_verisi_topla.py -s bau,nakliye -o bau_nakliye.xlsx

# Restoran + market (gastronomi)
python firma_verisi_topla.py --sektor restoran,market --yelp -o gastronomi.xlsx
```

**Kullanılabilir sektörler:** `restoran`, `market`, `lojistik`, `temizlik`, `bau`, `nakliye`, `kuaför`, `güvenlik`, `yazılım`, `danışmanlık`  
`--sektor` vermezseniz varsayılan sektörler kullanılır (restoran, market, lojistik, temizlik, bau, nakliye, kuaför).

### OSM + Yelp + Google (hepsi)

```bash
python firma_verisi_topla.py --yelp --google -o sonuc.xlsx
```

### Sadece OSM veya sadece Yelp (tek başına)

```bash
python osm_turkish_nrw.py -o osm_turk_nrw.csv
python osm_turkish_nrw.py -o osm_turk_nrw.xlsx

python yelp_turkish_nrw.py -o yelp_turk_nrw.xlsx
```

## Çıktı (CSV veya Excel)

Çıktı dosya adı **`.xlsx`** ile bitiyorsa veriler **Excel** formatında, aksi halde **CSV** olarak yazılır. Excel için `openpyxl` kullanılır (`pip install -r requirements.txt` ile yüklenir).

- **Firma** – İşletme adı  
- **Adresse** – Adres (OSM’de varsa)  
- **Telefon** – Telefon (OSM’de varsa)  
- **Website** – Web sitesi (OSM’de varsa)  
- **Region** – NRW  
- **Sektor** – OSM’deki tür (cuisine/shop/amenity)  
- **Quelle** – Veri kaynağı (OpenStreetMap / Yelp / Google Places)  
- **Aranan_Sektorler** – Bu aramada hangi sektörlerin kullanıldığı (Restoran, Lojistik, …)  
- **Google_Maps_Link** – İşletmeyi Google Maps’te açan link  
- **HRB** – Handelsregister numarası (HRB/HRA); boş bırakılabilir. Doldurulursa North Data linki direkt firma sayfasına gider.
- **North_Data_Link** – North Data’da firma araması veya (HRB doluysa) direkt firma sayfası linki.

Birçok OSM kaydında telefon veya web sitesi olmayabilir; bu alanlar boş kalır. Her çalıştırmada ayrı dosya için `--tarihli` kullanın. Excel’de sütunlar aynı isimlerle yer alır.

### HRB sütununu otomatik doldurma (OpenRegister API)

Excel’deki **HRB** sütununu [OpenRegister](https://openregister.de) API ile otomatik doldurmak için:

1. [openregister.de/keys](https://openregister.de/keys) adresinden ücretsiz API anahtarı alın (ayda 50 istek).
2. `.env` dosyasına ekleyin: `OPENREGISTER_API_KEY=your_api_key_here`
3. Çalıştırın:
   ```bash
   python3 excel_hrb_doldur.py turk_isletmeleri_nrw_2026-02-20_13-42.xlsx
   ```
   Dosya belirtmezseniz projedeki ilk `turk_isletmeleri_nrw*.xlsx` kullanılır. Script boş HRB hücreleri için firma adıyla OpenRegister’da arama yapar, bulduğu kayıt numarasını (HRB/HRA) yazar ve ilgili satırın North_Data_Link’ini direkt North Data firma sayfasına günceller.

## Neden ücretsiz kaynak?

- **Maliyet:** Google Places ücretli kota tüketir; OSM tamamen ücretsiz.
- **Hedef:** Özellikle **Türk işletmeleri** arandığı için OSM’deki `cuisine=turkish` ve “Türk/Döner/Anatolien” isimleri doğrudan bu amaca uyar.
- **Şeffaflık:** Overpass API herkese açık; ek API anahtarı gerekmez.

## Sınırlamalar

- **“Türk sahip” kesin değil:** Sadece mutfak ve isim etiketleriyle çıkarım yapılır; resmî bir “Türk işletmesi” listesi değildir.
- **Eksik veri:** OSM’de birçok işletmede telefon/web eksik; liste sadece OSM’de kayıtlı olanları içerir.
- **Sadece NRW:** Overpass sorgusu şu an NRW sınır kutusu ile kısıtlı (Köln, Düsseldorf, Dortmund, Essen vb. dahil).
- **Overpass 504 / 0 sonuç:** Bazen Overpass 0 işletme döner; o zaman sadece Google sonuçları yazılır. Google varsayılan 40 ile sınırlıdır; daha fazlası için `--max-google 200` kullanın.

## Lisans ve sorumluluk

Eğitim ve kişisel kullanım içindir. OpenStreetMap verisi [ODbL](https://www.openstreetmap.org/copyright) kapsamındadır. Toplanan veriyi kullanırken yerel veri koruma kurallarına (DSGVO vb.) uygun davranmak sizin sorumluluğunuzdadır.
