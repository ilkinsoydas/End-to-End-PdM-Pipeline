# N-CMAPSS DS02 — keşifsel veri analizi

Bu bölüm, NASA N-CMAPSS DS02 verileriyle turbofan motorlarının kalan faydalı ömrünü (Remaining Useful Life, RUL) anlamayı amaçlayan bitirme projesinin keşifsel analizlerini içerir. Ortak deponun eski C-MAPSS `dataset/` ve `src/` çalışmaları korunur; N-CMAPSS dosyaları ayrı tutulur.

## Klasör yapısı

```text
End-to-End-PdM-Pipeline/
├── dataset/                  # Mevcut C-MAPSS çalışmaları
├── src/                      # Mevcut kaynak kodlar
└── n_cmapss/
    ├── README.md
    ├── requirements.txt
    ├── data/                 # Yalnızca yerel HDF5 dosyasının varsayılan konumu
    │   └── .gitkeep
    ├── notebooks/            # Beş paylaşım notebook'u
    └── outputs/              # Çalıştırıldığında üretilir; Git tarafından dışlanır
```

`data/N-CMAPSS_DS02-006.h5` **repoya dahil değildir**. Büyük veri dosyasını commit etmeyin. Bu hazırlıkta HDF5 dosyası klon klasörüne kopyalanmamıştır; veri dosyası sağlanmadan Run All veri bulunamadı mesajıyla durur.

## Veri yapısı ve analiz kapsamı

DS02 dosyasında aşağıdaki dev dizileri aynı satır indeksleriyle hizalıdır:

| Dataset | Boyut | İçerik |
|---|---|---|
| `A_dev` | 5.263.447 × 4 | `unit`, `cycle`, `Fc`, `hs` |
| `W_dev` | 5.263.447 × 4 | `alt`, `Mach`, `TRA`, `T2` çalışma koşulları |
| `X_s_dev` | 5.263.447 × 14 | Fiziksel sensörler |
| `X_v_dev` | 5.263.447 × 14 | Sanal sensörler |
| `T_dev` | 5.263.447 × 10 | Simülasyonun iç sağlık parametreleri |
| `Y_dev` | 5.263.447 × 1 | RUL, kalan uçuş döngüsü |

Değişken adları `A_var`, `W_var`, `X_s_var`, `X_v_var`, `T_var` dizilerinden okunur. Altı dev motoru: **2, 5, 10, 16, 18, 20**; toplam **446 uçuş**. Ölçüm dizileri float64, Y_dev int64'tür. Dosyada test dizileri de vardır: 01 yalnızca yapı/metadata envanterinde isimlerini gösterir; test ölçümleri analize alınmaz. Analiz notebook'ları dev kullanır.

Altı ana grubun birleşimi 47 özgün değişkendir. Uçuş inceleyicisindeki ek `sample_index` ile 48 sütun olur. `sample_index` uçuş içi örnek sırasıdır, saniye değildir. T_dev gerçek sensör ölçümü veya doğrudan verim kaybı yüzdesi değildir. Ham sensör değişimleri çalışma koşullarından etkilenebilir.

## Notebook'lar

| Dosya | Görevi |
|---|---|
| `01_DS02_Data_Exploration.ipynb` | HDF5 yapısı, boyut/veri tipleri, değişken adları, hizalama kontrolü ve ilk 10 dev satırı. |
| `02_DS02_Engine_Flight_Explorer.ipynb` | Motor/uçuş seçimi, 48 sütunlu tablo, sütun grupları, 50 satırlık sayfalama ve tam uçuş CSV dışa aktarımı. |
| `03_DS02_Sensor_Analysis.ipynb` | Seçili uçuşun 28 sensörü, ayrıntılı sensör seçimi ve dört çalışma koşulunun grafikleri. |
| `04_DS02_Lifecycle_Degradation_Analysis.ipynb` | Motorun bütün uçuşlarında RUL, sağlık, sensör ve koşul özetleri. Bütün ölçümler ana EDA'dır; benzer koşul alt grubu ayrı, isteğe bağlı yardımcı karşılaştırmadır. Kapsam/benzerlik kontrol tabloları bulunur. |
| `05_DS02_Cross_Engine_Comparison.ipynb` | Altı dev motorunun ömür, ölçüm sayısı, sağlık durum matrisi, 28 sensör ve koşul karşılaştırmaları. Ana analizde koşul filtresi uygulanmaz. |

Notebook'lar bağımsız çalışır; önceki notebook'u çalıştırmaya veya eski CSV dosyalarını taşımaya ihtiyaç duymaz. HDF5 salt okunur açılır; tüm DS02 tek DataFrame'e yüklenmez. Model eğitimi, veri bölme, sensör elemesi veya model preprocessing'i yoktur. Normalize yaşam ilerlemesi yalnızca geriye dönük görsel hizalamadır; fiziksel sağlık ölçümü veya model girdisi değildir.

## Kurulum ve VS Code kernel'i

Python **3.11 veya üzeri** kullanın. Mevcut kodlar ve gereksinim aralıkları yerel **Python 3.14.0** ortamıyla kontrol edilmiştir; diğer Python/paket kombinasyonları burada ayrıca çalıştırılmamıştır. Sürüm aralıkları tam tekrarlanabilirlik sağlayan bir lock dosyası değildir.

Ortak deponun kökünde PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r n_cmapss/requirements.txt
```

VS Code'da Microsoft Python ve Jupyter uzantıları kurulu olmalıdır. Notebook'u açın, **Select Kernel → Python Environments → ortak deponun `.venv` ortamı** seçin. Kaynak projeye ait eski/kernel-özel adlar paylaşım kopyalarında genel `Python 3` metadata'sıyla değiştirilmiştir; gerçek yorumlayıcıyı VS Code'dan seçin.

İncelenen yerel sürümler: numpy 2.5.4, pandas 3.0.6, h5py 3.16.0, matplotlib 3.11.2, ipywidgets 8.1.9, ipython 9.17.1, ipykernel 7.4.0, nbformat 5.11.1, nbclient 0.11.0. Notebook'lar bu kopyalama hazırlığında tam EDA için yeniden çalıştırılmamıştır.

## Veri yolunu sağlama — kopyalamadan test seçeneği

Varsayılan yol, çalışma dizini ortak repo kökü, `n_cmapss/` veya `n_cmapss/notebooks/` olduğunda aynı `n_cmapss/data/N-CMAPSS_DS02-006.h5` konumuna çözülür. Üretilen çıktılar her durumda `n_cmapss/outputs/` altında kalır.

HDF5'i taşımadan veya klona kopyalamadan kullanmak için **`N_CMAPSS_H5` ortam değişkenine mevcut dosyanın tam yolunu** verin. Bu yalnızca yerel bir ayardır; kendi dosya yolunuzu commit etmeyin.

Yeni VS Code sürecini açmadan önce PowerShell'de:

```powershell
$env:N_CMAPSS_H5 = 'C:\yerel\veri\N-CMAPSS_DS02-006.h5'
code .
```

Zaten açık VS Code penceresi yeni terminal ortamını kernel'e otomatik aktarmayabilir. Alternatif olarak notebook'ta, ilk kurulum hücresinden önce **geçici bir hücreyi** çalıştırın:

```python
import os
os.environ['N_CMAPSS_H5'] = r'C:\yerel\veri\N-CMAPSS_DS02-006.h5'
```

Bu yerel hücreyi paylaşım/commit öncesinde kaldırın. Ardından kurulum ve 01'in yapı envanteri hücresini çalıştırmak, büyük ölçüm dizilerini RAM'e yüklemeden salt okunur erişimi test eder. Diğer notebook'ların Run All komutu ilgili EDA hesaplarını gerçekten yeniden yapar; 04/05 yeni CSV klasörleri oluşturur.

Symlink/hardlink veya veri kopyası zorunlu değildir. Ortam değişkeni ayarlıysa varsayılan data yoluna göre önceliklidir; varsayılanı kullanmak için kernel ortamından kaldırın.

## Çıktılar, paylaşım boyutu ve Git güvenliği

Paylaşım kopyalarında **bütün kayıtlı hücre çıktıları, execution count ve widget durumu temizlenmiştir**. Analiz hücreleri ve açıklamalar korunur; veri yolu/önbellek taşınabilirliği ve genel kernel metadata'sı uyarlanmıştır. Kaynak notebook'ların kayıtlı çıktıları değişmemiştir. Bazı açıklamalar önceki gerçek çalıştırmaların bulgularını içerir; yeniden doğrulamak için veriyle Run All çalıştırın.

02'nin CSV düğmesi ve 04/05'in özetleri `n_cmapss/outputs/` altında yeni dosyalar oluşturur. 04/05'te eski CSV'ler üzerine yazılmaz. `.gitignore`, yerel sanal ortamı, HDF5'i, N-CMAPSS yerel verisini, çıktı klasörünü, notebook checkpoint ve geçici dosyalarını dışlar. Eski projedeki takip edilen CSV'lere genel `*.csv` kuralı eklenmemiştir.

04'te alt gruba girmeyen ölçümler genel EDA'dan çıkarılmaz; seçim yanlılığı ve rejim temsili sınırları açıklanır. 05'te altı motorun bütün 5.263.447 dev ölçümü kapsam dahilindedir. Grafik farkları tek başına nedensellik, arıza başlangıcı veya sensör önem sırası göstermez.
