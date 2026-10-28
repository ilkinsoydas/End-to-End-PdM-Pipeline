# N-CMAPSS — Ortak Veri Dışa Aktarma Aracı

Bu araç, `N-CMAPSS_DS02-006.h5` içinden seçilen motorları, uçuşları ve sütunları filtreleyerek incelenebilir CSV tabloları üretir. İsteğe bağlı olarak pencere dizilerini eğitimde kullanılmak üzere kaydeder. CNN, TCN, LSTM veya Random Forest gibi belirli bir modele bağlı değildir.

**Ana amaç veriyi incelemek ve paylaşmaktır. Model eğitimi kendiliğinden başlamaz.** Kaynak HDF5 dosyası değiştirilmez. Her çalıştırma ayrı bir çıktı klasörü oluşturur.

## 1. Üç Python dosyası ne yapıyor?

| Dosya | Görevi | Kullanıcı neyi değiştirir? |
|---|---|---|
| `veri_aktar.py` | Kullanıcının seçimlerini `AYARLAR` sözlüğünde toplar ve doğrudan dışa aktarma fonksiyonuna iletir. Üst bölümde sütun grupları ve filtre örnekleri bulunur. | Genellikle yalnızca `AYARLAR` sözlüğü. |
| `export_dataset.py` | HDF5 okuma, sütun doğrulama, filtreleme, pencere oluşturma, CSV/NumPy yazma ve işlem kayıtlarını yönetir. | Normal kullanımda değiştirilmez. |
| `export_training.py` | Kaydedilmiş pencere dizilerini motor bazında eğitim/doğrulamaya ayırır ve isteğe bağlı ölçekler. | Eğitim kodundan fonksiyon olarak çağrılır. Model içermez. |

## 2. Klasör düzeni ve kurulum

Dosyaların proje içindeki konumu:

```text
End-to-End-PdM-Pipeline/
    n_cmapss/
        data/
            N-CMAPSS_DS02-006.h5
        exports/
            README.md
            veri_aktar.py
            export_dataset.py
            export_training.py
            motor2_ornek_<kimlik>_<tarih>/
                column_catalog.csv
                config.json
                flights.csv
                manifest.json
                raw.csv
                window_statistics.csv
                window_values.csv
                windows.csv
```

`veri_aktar.py` doğrudan PyCharm Run ile çalıştırılırken aynı klasördeki dosyayı şöyle çağırır:

```python
from export_dataset import export
```

CSV üretimi için `h5py` ve `numpy`; eğitim adaptörü için ayrıca `pandas` ve `scikit-learn` gerekir. PyTorch yalnızca kendi PyTorch modelinizi çalıştırırken gereklidir; dışa aktarma aracının bağımlılığı değildir.

Seçili Python ortamına kurulum:

```bash
python -m pip install h5py numpy pandas scikit-learn
```

Kurulumda kullanılan Python ile PyCharm'ın seçili interpreter'ı aynı olmalıdır. Terminaldeki `(base)` ortamı, PyCharm'da seçilen farklı bir Conda ortamıyla aynı kütüphaneleri paylaşmak zorunda değildir.

### Proje kökü ayarı

`veri_aktar.py`, `n_cmapss/exports` içinde olduğundan yalnızca `Path(__file__).resolve().parent` kullanmak proje kökünü vermez. Dosyanızda henüz düzeltilmediyse `main()` üstüne şu fonksiyonu ekleyin:

```python
def proje_kokunu_bul():
    for aday in Path(__file__).resolve().parents:
        if (aday / "n_cmapss" / "data").is_dir():
            return aday
    raise FileNotFoundError("Üst dizinlerde n_cmapss/data bulunamadı.")
```

`main()` ayarları arada JSON dosyası oluşturmadan doğrudan aktarır:

```python
def main():
    proje_koku = proje_kokunu_bul()
    export(AYARLAR, base=proje_koku)


if __name__ == "__main__":
    main()
```

`export_dataset.py` içindeki `export()` hem Python sözlüğünü hem de isteğe bağlı JSON dosya yolunu kabul eder. Günlük kullanımda JSON dosyası hazırlamak gerekmez. Göreli kaynak ve çıktı yolları `base=proje_koku` üzerinden çözülür. HDF5 başka yerdeyse `data_path` için tam yol kullanılabilir; yukarıdaki kök bulucu yine `n_cmapss/data` klasörünü bekler.

## 3. İlk çalıştırma

1. PyCharm'da projenin Python interpreter'ını seçin.
2. `veri_aktar.py` dosyasındaki `AYARLAR` bölümünü düzenleyin.
3. Dosyaya sağ tıklayıp **Run 'veri_aktar'** seçin.
4. Konsoldaki `Complete:` satırında belirtilen klasörü açın.
5. `manifest.json` içindeki `status` değerinin `complete` olduğunu kontrol edin.

Başlangıçta bir motorun birkaç uçuşunu seçmek çıktıların kontrolünü kolaylaştırır. Dosyanın tepesindeki sütun listeleri yalnızca seçim yapmayı kolaylaştırır; hangi sütunların aktarılacağını `AYARLAR["columns"]` belirler.

**Ayarların tek düzenleme noktası `veri_aktar.py` içindeki `AYARLAR` sözlüğüdür.** `export_configs` klasörü ve `python_secimleri.json` oluşturulmaz. Her başarılı aktarım, kullanılan ayarları kendi çıktı klasöründeki `config.json` içine kaydeder. Çıktı klasörlerine otomatik `README.txt` yazılmaz; ortak kullanım rehberi bu `README.md` dosyasıdır.

Ekrandaki örnekte CSV çıktıları açık, `sequences=False` olduğu için `X.npy` ve `y.npy` bulunmaması normaldir. Bunlar yalnızca eğitim dizisi üretimi açıldığında eklenir.

## 4. Ayarlar

| Alan | Anlamı / örnek |
|---|---|
| `name` | Çıktı adı öneki; harf, rakam, `_` ve `-` kullanın. Örnek: `motor2_ornek`. |
| `data_path` | Kaynak HDF5 yolu. Göreli yollar `export(..., base=proje_koku)` köküne göre çözülür. |
| `output_root` | Çıktıların yerleştirileceği ana klasör. |
| `partition` | `dev` veya `test`. Motor listesi seçilen bölümle uyumlu olmalıdır. |
| `columns` | CSV'ye yazılacak sütunlar; sıra korunur, tekrar eden ad kabul edilmez. |
| `units` | Motor numaraları. Tüm motorlar için alanı kaldırın; `[]` veya `None` vermeyin. |
| `cycles` | Uçuş numaraları. Seçilen bütün motorlarda uygulanır. Tüm uçuşlar için alanı kaldırın. |
| `filters` | Sütun değerlerine uygulanacak koşullar; `{}` filtre yok demektir. |
| `window` | Pencere ayarları veya pencereleme yoksa `None`. |
| `exports` | Hangi CSV ve NumPy çıktılarının üretileceği. |
| `sequence_features` | İsteğe bağlı `X.npy` girdi sütunları. `columns` içinde de bulunmalıdır. |
| `chunk_rows` | Okuma parçalarının satır sayısı. Örnek: `100_000`. Pencere boyutu veya örnekleme adımı değildir. |

### Veri grupları ve sütunlar

| Grup | Adet | Sütunlar |
|---|---:|---|
| A — Kimlik/etiket | 4 | `unit`, `cycle`, `Fc`, `hs` |
| W — Çalışma koşulu | 4 | `alt`, `Mach`, `TRA`, `T2` |
| X_s — Fiziksel sensör | 14 | `T24`, `T30`, `T48`, `T50`, `P15`, `P2`, `P21`, `P24`, `Ps30`, `P40`, `P50`, `Nf`, `Nc`, `Wf` |
| X_v — Sanal sensör | 14 | `T40`, `P30`, `P45`, `W21`, `W22`, `W25`, `W31`, `W32`, `W48`, `W50`, `SmFan`, `SmLPC`, `SmHPC`, `phi` |
| T — İç sağlık parametresi | 10 | `fan_eff_mod`, `fan_flow_mod`, `LPC_eff_mod`, `LPC_flow_mod`, `HPC_eff_mod`, `HPC_flow_mod`, `HPT_eff_mod`, `HPT_flow_mod`, `LPT_eff_mod`, `LPT_flow_mod` |
| Y — Hedef | 1 | `RUL` — HDF5 içindeki `Y_dev` / `Y_test` sütununa verilen ad |

Toplam 47 değişken vardır. T grubu sıcaklık sensörü grubu değildir. Kod sütun adlarını HDF5 metadata dizilerinden okur ve istenen adları doğrular; büyük/küçük harf önemlidir.

DS02 için dev motorları `[2, 5, 10, 16, 18, 20]`, resmi test motorları `[11, 14, 15]` şeklindedir. Resmi testi model seçimi için tekrar tekrar kullanmayın.

### Filtreler

| Operatör | Anlamı |
|---|---|
| `ge` / `gt` | Büyük veya eşit / büyük |
| `le` / `lt` | Küçük veya eşit / küçük |
| `eq` / `ne` | Eşit / eşit değil |
| `in` | Verilen sayısal listedekilerden biri |

```python
"filters": {
    "RUL": {"ge": 10, "le": 50},
    "Mach": {"ge": 0.6},
    "Fc": {"in": [1, 2]},
},
```

Bu örnekte bütün koşullar birlikte sağlanmalıdır (VE mantığı). Filtrelenen sütunun CSV için seçilmiş olması gerekmez. Mevcut sürüm koşullar arasında VEYA ifadesi, metin filtresi veya rastgele örnekleme sunmaz. Sayısal eşitlik filtresi tolerans kullanmaz; sürekli sensörlerde aralık seçmek daha uygundur.

### Pencereleme kuralları

```python
"window": {"size": 256, "stride": 128, "target": "last"},
```

- `size`: pencere içindeki örnek sayısı; uçuş sayısı değildir.
- `stride`: pencere başlangıçları arasındaki örnek sayısı.
- `target="last"`: son örneğin RUL değeri; `"mean"`: pencere RUL ortalaması.
- `stride < size` örtüşme, `stride = size` bitişik pencereler, `stride > size` boşluklar oluşturur.
- Pencereler motor/uçuş sınırını geçmez. Her uçuşun orijinal başlangıcından itibaren sabit adımlarla oluşturulur.
- Eksik kalan son pencere atılır; doldurma yapılmaz.
- Bir pencerenin **bütün satırları** filtreleri sağlamalıdır. Elenen kayıtların iki tarafı birleştirilmez ve pencere ızgarası yeniden başlatılmaz.

## 5. Kullanım örnekleri

Aşağıdaki bölümler `AYARLAR` içinde değiştirilir; bağımsız çalıştırılacak tam programlar değildir.

### Yalnızca ham tablo

```python
"columns": TUM_SUTUNLAR,
"units": [2],
"cycles": [1, 2],
"filters": {},
"window": None,
"exports": {
    "raw": True,
    "window_values": False,
    "statistics": False,
    "sequences": False,
},
```

### Pencereleri inceleme ve isteğe bağlı eğitim dizisi

```python
"columns": KIMLIK_BILGILERI + MEVCUT_18_GIRDI + HEDEF,
"sequence_features": MEVCUT_18_GIRDI,
"units": DEV_MOTORLARI,
# Bütün uçuşlar için cycles alanını kaldırın.
"filters": {},
"window": {"size": 256, "stride": 1024, "target": "last"},
"exports": {
    "raw": False,
    "window_values": True,
    "statistics": True,
    "sequences": True,
},
```

Bu örnekte `sequence_features` CSV'de seçilmiş 18 W/X_s kanalını kullanır. CSV'de görünen kimlik ve hedef sütunları `X.npy` içine girmez. **Mevcut sürüm NumPy girdi dizisinde yalnızca W ve X_s gruplarını destekler; sanal sensörler CSV'ye alınabilse de `sequence_features` içinde kullanılamaz.** Alan verilmezse seçilmiş W/X_s sütunları varsayılan olarak kullanılır.

## 6. Üretilen dosyalar

| Dosya | İçerik / üretilme koşulu |
|---|---|
| `raw.csv` | `raw=True`: motor/uçuş ve değer filtrelerini sağlayan satırlar. Pencerelere girmeyen satırlar da bulunabilir. |
| `window_values.csv` | `window_values=True`: her kabul edilen pencerenin tüm satırları; `window_id`, `step`, kaynak satır ve motor/uçuş bilgileriyle. |
| `window_statistics.csv` | `statistics=True`: her pencere için seçilen her sütunun `__mean`, `__std`, `__min`, `__max` değerleri. Standart sapma `ddof=0` kullanır. |
| `windows.csv` | Pencereleme varsa: pencere kimliği, motor, uçuş, kaynak aralığı, uzunluk ve `target_rul`. |
| `flights.csv` | Seçilen uçuşlarda kaynak/filtrelenmiş satır sayıları, aday/kabul edilen pencere sayıları ve kapsama bilgisi. |
| `column_catalog.csv` | HDF5 sütun grupları, kaynak indisleri, seçilme durumları ve kullanım rolleri. |
| `X.npy` | `sequences=True`: ölçeklenmemiş float32 `[pencere, zaman, özellik]` dizisi. |
| `y.npy` | `sequences=True`: `windows.csv` satır sırasıyla eşleşen RUL hedefleri. |
| `config.json` | Başarılı aktarımda kullanılan ayarların kopyası. |
| `manifest.json` | Kaynak bilgileri, ayarlar, sayımlar ve işlem durumu: `building`, `complete`, `failed`. |

`config.json` ve `manifest.json` farklı amaçlara hizmet eder:

- **`config.json`:** Hangi motorların, sütunların, filtrelerin ve pencere ayarlarının seçildiğini saklar. Ayarları değiştirmek için bu dosyayı değil, `veri_aktar.py` dosyasını düzenleyin.
- **`manifest.json`:** Aktarımın tamamlanma durumunu, kaynak bilgisini, gerçek satır/pencere sayılarını ve eğitim dizisindeki sütun sırasını saklar. `export_training.py` bu dosyayı okuduğundan eğitimde kullanılacak çıktılarda korunmalıdır.

İstatistik tablosunun dosya adı **`window_statistics.csv`** şeklindedir.

### Satırları doğru okumak

- `source_row`, seçilen dev/test HDF5 bölümünde sıfırdan başlayan satır indisidir; CSV satır numarası veya zaman damgası değildir.
- `start_row` dahildir, `end_row` dahil değildir: `[start_row, end_row)`.
- `step`, pencere içinde sıfırdan başlayan örnek sırasıdır.
- `meta_unit` / `meta_cycle` araç tarafından eklenir; ayrıca `unit` / `cycle` seçildiyse iki biçimde de görünmeleri beklenir.
- Örtüşen pencerelerde aynı kaynak satır `window_values.csv` içinde birden fazla kez görünür. Bu hata değildir.
- `window_row_occurrences` tekrarları sayar; `unique_window_rows` benzersiz kullanılan kaynak satırları sayar. `uncovered_filtered_rows`, filtreyi geçtiği halde hiçbir kabul edilen pencereye girmeyen satırları gösterir.
- `window_id` yereldir; farklı aktarım klasörleri arasında tek başına benzersiz değildir.

## 7. Eğitim adaptörünün kullanımı

`export_training.py` içindeki `load_training_arrays` yalnızca `complete` durumundaki **dev** aktarımlarını okur. Önce `sequences=True` ile `X.npy` ve `y.npy` üretilmelidir. İçe aktarmak veya fonksiyonu çağırmak model eğitimi başlatmaz.

Aşağıdaki örnek `export_training.py` ile aynı klasörde bulunan bir eğitim dosyasından çağrılabilir:

```python
from export_training import load_training_arrays

CIKTI_KLASORU = "/tam/yol/n_cmapss/exports/olusturulan_klasor"

X_train, y_train, X_val, y_val, scaler, feature_names = (
    load_training_arrays(
        directory=CIKTI_KLASORU,
        validation_units=[2],
        standardize=True,
        layout="NCT",
    )
)

print("Girdiler:", feature_names)
print("Eğitim:", X_train.shape, y_train.shape)
print("Doğrulama:", X_val.shape, y_val.shape)
```

Motor 2 doğrulamaya, kalan motorlar eğitime ayrılır. Tek motorlu aktarım bu ayrım için yeterli değildir. `StandardScaler` yalnızca eğitim pencereleriyle öğrenilir; doğrulamaya aynı dönüşüm uygulanır. `standardize=False` ile ölçekleme kapatılabilir ve `scaler=None` döner.

| Model ailesi | Veri kullanımı |
|---|---|
| CNN / TCN | `layout="NCT"`: `[pencere, özellik, zaman]` |
| LSTM / GRU | `layout="NTC"`: `[pencere, zaman, özellik]` |
| Random Forest / XGBoost | Genellikle `window_statistics.csv` içinden seçilen sayısal özellikler; bu adaptör istatistik tablosunu otomatik hazırlamaz. |

Mevcut `train_cnn.py` otomatik olarak bu yeni çıktılara bağlanmaz. Eğitim kodunun veri yükleme bölümü ayrıca uyarlanmalıdır. Seçilen özellik sayısı değişirse modelin giriş boyutu da değiştirilmelidir. Pencere boyutuna bağlı katmanlar kullanan modellerde pencere uzunluğu değişikliği de uyarlama gerektirebilir.

### Deneylerin güvenilirliği

- CSV için seçilmiş her sütunu model girdisi kabul etmeyin. Kimlik, `hs`, iç sağlık parametreleri ve RUL açıklayıcı/etiket bilgileri içerir.
- İstatistik dosyası **seçilen bütün sütunların** özetlerini üretir. `RUL__mean`, `RUL__max` gibi hedef türevlerini RUL modeline girdi vermek hedef sızıntısına neden olur.
- Pencereleri rastgele bölmek yerine motor bazında ayırın; örtüşen aynı uçuş parçaları eğitim ve doğrulamaya dağılmamalıdır.
- Altı motor için her motoru sırayla doğrulamaya ayırarak altı fold yapılabilir. Her fold için ölçekleyici yeniden ve yalnızca o foldun eğitim motorlarıyla öğrenilmelidir.
- RUL/sağlık etiketine göre filtrelenmiş tablolar inceleme için faydalıdır; bunlarla eğitilen sonuçlar tüm ömür boyunca performansı temsil etmez.
- Eski altı fold CNN sonuçlarını referans olarak koruyun. Farklı sütun, pencere veya filtre denemelerini ayrı adlarla kaydedin.

## 8. Büyük veri, izlenebilirlik ve sınırlar

HDF5 parça parça okunur; kaynak dosyanın tamamı tek seferde belleğe alınmaz. Bununla birlikte uçuş maskeleri bellekte tutulur. Eğitim adaptörü eğitim/doğrulama dizilerini RAM'e kopyalar; çok büyük aktarımlar için özel bir toplu okuma/DataLoader çözümü gerekebilir.

Bütün veri ve özellikle küçük stride ile `window_values.csv` çok büyüyebilir. İnceleme için motor/uçuş seçin; yalnızca özetler gerekiyorsa `window_values=False`, `statistics=True` kullanın. CSV tablolarını açan uygulamaların satır ve bellek sınırları olabilir; CSV dosyasının üretilmesi tek bir çalışma sayfasında tümünün görüntülenebileceği anlamına gelmez.

CSV'ler UTF-8 BOM ile, virgül ayracıyla yazılır. Tek sütunda açılırsa uygulamanın içe aktarma ekranında ayraç olarak virgül seçin. CSV'ler ölçeklenmemiş kaynak değerlerini içerir; fiziksel birim dönüşümü yapılmaz. NumPy dizileri float32 olarak kaydedildiğinden kaynakla karşılaştırmada küçük yuvarlama farkları görülebilir.

Çıktı adı ayar/kaynak parmak izi ve zaman bilgisi içerir; eski çıktılar üzerine yazılmaz. Kaynak parmak izi dosyanın yolu, boyutu ve değiştirilme zamanı üzerinden hesaplanır; HDF5 içeriğinin tam kriptografik özeti değildir.

## 9. Sık karşılaşılan hatalar

| Hata / durum | Çözüm |
|---|---|
| `Cannot run program ... No such file or directory` | PyCharm eski/silinmiş Python ortamını kullanıyordur. Project Interpreter ve Run Configuration içindeki interpreter'ı düzeltin. |
| `No module named 'h5py'` | Paketi PyCharm'da seçili olan Python ortamına kurun. Başka ortamda kurulu olması yeterli değildir. |
| `expected str, bytes or os.PathLike object, not dict` | `export_dataset.py` eski sürümdedir; `export()` başlangıcı Python sözlüğünü kabul edecek şekilde güncellenmelidir. |
| `export_configs` yeniden oluşuyor | Çalıştırılan `veri_aktar.py` içinde eski `mkdir` / `write_text` satırları kalmıştır. `main()` yukarıdaki doğrudan çağrı biçiminde olmalıdır. Önceden oluşmuş klasörler kendiliğinden silinmez. |
| HDF5 için `FileNotFoundError` | `data_path`, proje kökü ve dosyanın gerçek konumunu kontrol edin. |
| `Unknown column` | Sütun adını ve büyük/küçük harfleri kontrol edin; `column_catalog.csv` dosyasından yararlanın. |
| `Unknown units` | Motorun seçilen `partition` içinde bulunduğunu kontrol edin. |
| `Window exports require a window configuration` | `window=None` ise `window_values`, `statistics`, `sequences` kapalı olmalıdır. |
| `No windows available for sequence export` | Filtreleri, uçuş uzunluklarını ve pencere boyutunu kontrol edin. |
| `Sequence features must be selected W/X_s columns` | `sequence_features` yalnızca CSV için de seçilmiş W/X_s sütunlarından oluşmalıdır. |
| Eğitim/doğrulama boş kalıyor | Aktarımda en az iki motor bulunsun; doğrulama için mevcut motorların yalnızca bir bölümünü seçin. |
| Başarısız çıktı klasörü kaldı | `status=failed` klasörü kısmi olabilir. Eğitimde kullanmayın; hatayı giderip yeniden aktarın. |

Bu README üç dosyanın mevcut davranışını açıklar. Araç kaynak verinin bilimsel doğruluğunu veya bir modelin başarısını doğrulamaz; seçimlerin ve veri hazırlamanın incelenebilir olmasını sağlar.
