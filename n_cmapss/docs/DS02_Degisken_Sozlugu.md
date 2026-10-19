# NASA N-CMAPSS DS02 — Türkçe değişken sözlüğü ve okuma rehberi

Bu sözlük `N-CMAPSS_DS02-006.h5` dosyasındaki **47 özgün değişkeni** açıklar: A=4, W=4, X_s=14, X_v=14, T=10, Y=1. `sample_index` ve uçuş özetleri bunlardan ayrı, notebook tarafından türetilmiş alanlardır.

## Kaynak ve doğrulama yöntemi

Ana kaynak: Manuel Arias Chao, Chetan Kulkarni, Kai Goebel ve Olga Fink (2021), *Aircraft Engine Run-to-Failure Dataset under Real Flight Conditions for Prognostics and Diagnostics*, Data 6(1), 5. [Makale/DOI](https://doi.org/10.3390/data6010005), [yayıncı PDF'si](https://mdpi-res.com/d_attachment/data/data-06-00005/article_deploy/data-06-00005-v2.pdf?version=1611240730). Esas alınan bölümler: Tables 4–8 (PDF s.6–8), uçuş sınıfları için Table 1 ve Section 2.2, sağlık için Sections 3.1–3.2 ve 4.2. Makale **CC BY 4.0** lisanslıdır; bu doküman kaynak gösterilerek hazırlanmış Türkçe açıklama/uyarlamadır. İngilizce adlar kısaltmaların genişletildiği öğretici karşılıklardır; birebir alıntı listesi değildir.

**Makale tanımı**, **dosyada gözlenen kapsam** ve **öğretici yorum** birbirinden ayrılır. A/W/X_s/X_v/T adları HDF5'in beş `*_var` dizisinden salt okunur olarak kontrol edilmiştir. Y için `Y_var` yoktur; `RUL`, notebook'un Y_dev sütununa verdiği addır ve makale Table 3'teki etiketle uyumludur. Tablo sırası dosyanın gerçek metadata sırasını izler. Özellikle X_s'nin sırası makale Table 5'in basım sırasından farklıdır: eşleştirmeyi sıra numarasıyla değil **adla** yapın.

DS02 dev bölümünde 2, 5, 10, 16, 18, 20 motorları, 446 uçuş ve 5.263.447 hizalı ölçüm satırı bulunur. Kapsam/sağlık gözlemleri önceki 05 çalıştırmasının CSV özetleriyle karşılaştırılmıştır; bu dokümantasyon görevinde EDA yeniden hesaplanmamıştır. 01 metadata envanterinde test adlarını da listeler; test ölçümleri analiz edilmez. HDF5 değiştirilmez ve tüm veri RAM'e alınmaz.

## İçindekiler

- [Motor ve fizik](#motor-ve-fizik)
- [A](#a-yardimci), [W](#w-kosullar), [X_s](#xs-fiziksel), [X_v](#xv-sanal), [T](#t-saglik), [Y](#y-rul)
- [Fc sınıfları](#fc-siniflari), [hs–HI–RUL–EOL](#saglik-kavramlari)
- [Birimler ve kaynak uyuşmazlıkları](#birimler)
- [Türetilmiş sütunlar](#turetilmis), [model sınırları](#model-sinirlari), [notebook rehberi](#notebook-rehberi)

<a id="motor-ve-fizik"></a>
## Motoru ve fiziksel kavramları anlamak

### Akış yolu ve bileşenler

Çekirdek akış yolu öğretici olarak **giriş → fan → LPC → HPC → combustor → HPT → LPT → çıkış** şeklinde okunur. Fanın beslediği havanın önemli bir kısmı çekirdeğe girmeden bypass kanalından geçer. Bu şema soğutma/bleed devrelerinin tam çizimi değildir. Destekleyici kaynaklar: [NASA Glenn turbofan rehberi](https://www.grc.nasa.gov/www/k-12/airplane/Animation/turbtyp/etfp.html), [NASA gaz türbini rehberi](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/turbine-engines/).

| Bileşen | İngilizce açılım | Türkçe karşılık ve işlev |
|---|---|---|
| Fan | Fan | Öndeki döner eleman; havayı hızlandırır, bypass ve çekirdek yollarını besler. Nf fan hızını betimler. |
| LPC | Low-pressure compressor | Alçak basınç kompresörü; çekirdekte ilk sıkıştırma bölümüdür. |
| HPC | High-pressure compressor | Yüksek basınç kompresörü; havayı yanma öncesinde daha fazla sıkıştırır. |
| Combustor / burner | Combustion chamber | Yanma odası; yakıt eklenmesi ve yanmayla akışın enerjisi yükseltilir. |
| HPT | High-pressure turbine | Yüksek basınç türbini; sıcak gazdan iş alarak yüksek basınç/çekirdek milini ve HPC'yi sürer. |
| LPT | Low-pressure turbine | Alçak basınç türbini; gazdan iş alarak düşük basınç milini, fan ve LPC tarafını sürer. |

İki milli motor bağlamında Nf düşük basınç/fan, Nc yüksek basınç/çekirdek tarafının dönüş hızıdır. HPT/LPT iki farklı türbin bölümüdür; veri tablosundaki ayrı motorları belirtmez.

### Sıcaklık ve basınç

Sıcaklık akışın termal durumudur. Sıkıştırma ve yanma sıcaklığı artırabilir; türbinde iş çekilmesi sıcaklığı düşürebilir. Ancak güç talebi, irtifa ve kontrol davranışı da değiştiği için tek yüksek sıcaklıktan arıza sonucu çıkarılmaz.

**Total/stagnation** akışın durdurulmasıyla tanımlanan toplam durumu, **static** hareketli akışın yerel termodinamik durumunu anlatır. Ps30 statik, P30 toplam basınçtır; aynı HPC çıkışını anlatsalar da aynı büyüklük değildir. P40 veya T48 değişimi koşullar eşitlenmeden tek başına sağlık kanıtı değildir. İsimlerdeki 24/30/40 sayıları CMAPSS istasyon adlarıdır; zaman veya sensör sıra indeksi değildir.

### Dönüş hızı ve debi

rpm devir/dakikadır. Nf ve Nc farklı mil sistemleridir. Daha yüksek hız otomatik olarak daha sağlıklı motor anlamına gelmez; kontrol komutu ve yük etkili olabilir.

Kütlesel debi bir noktadan birim zamanda geçen kütledir. Wf yakıt; W21/W22/W25 hava akışını; W48/W50 türbin çıkış gaz akışını; W31/W32 soğutmaya ayrılan akışı temsil eder. lbm/s hacimsel debi değildir ve pound-force (lbf) kuvvetiyle karıştırılmaz. Yakıt debisinin artması güç talebi artışından da kaynaklanabilir; tek başına verimsizlik kanıtı değildir.

### Stall / surge margin

Fan ve kompresörlerin kararlı çalışma sınırları vardır. Stall yerel aerodinamik akış ayrılmasıyla, surge daha geniş sistem düzeyinde kararsız akışla ilişkilidir. Margin ilgili kararsızlık sınırına olan operasyonel payı anlatır. Daha büyük pozitif pay genellikle daha fazla kararlılık rezervidir; kesin eşik ve hesap model tanımına bağlıdır. Makale Table 6'da **stall margin**, Section 3.2'de **surge margins** ifadesini kullanır; terim farkı gizlenmemiştir. Tabloda birim **—** olduğundan 20 gibi bir değeri doğrulamadan “%20 verim” veya “%20 sağlık” diye okumayın.

### X_s fiziksel, X_v sanal ne demektir?

X_s fiziksel olarak ölçülebilir condition-monitoring kanallarıdır. Fakat N-CMAPSS'te motor yanıtları simülatörden gelir; makale X_s'ye ölçüm gürültüsü ekler. “Fiziksel sensör” demek bütün değerlerin gerçek bir arızalı uçak motorundan doğrudan kaydedildiği anlamına gelmez. Gerçek uçuş profilleri simülatörü sürer. X_v aynı modelin doğrudan gözlenmeyen iç çıktılarıdır; notebook'umuz X_s'den yeni bir sanal sensör kestiricisi eğitmemiştir. [Makale, Sections 2.1 ve 3.3](https://doi.org/10.3390/data6010005).

<a id="a-yardimci"></a>
## A — Yardımcı bilgiler: 4 değişken

Kaynak: [Table 8 ve Section 4.2](https://doi.org/10.3390/data6010005). “—” bu grupta fiziksel birim değil etiket/sayım bilgisidir.

| Kod | Tam İngilizce ad | Türkçe | Birim | Bileşen / konum | Temsil ve yorum |
|---|---|---|---|---|---|
| `unit` | Engine unit identifier | Motor kimliği | — | Motorun bütünü | Aynı motorun satırlarını ilişkilendirir. 2 ve 20 sayıları sağlık sıralaması değildir; kimlik ezberlenmesi genellemeyi bozabilir. |
| `cycle` | Flight cycle number | Uçuş döngüsü numarası | —, uçuş sayacı | Kullanım geçmişi | Motorun kaçıncı uçuşu olduğunu gösterir. Bir uçuş birçok örnek içerir; farklı motorlarda cycle 40 aynı sağlık/RUL değildir. |
| `Fc` | Flight class | Uçuş sınıfı | —, kategorik | Görev/uçuş profili | 1 kısa, 2 orta, 3 uzun sınıftır. Arıza etiketi veya uçuş içi tırmanış/seyir fazı değildir. |
| `hs` | Health state label | Sağlık durumu etiketi | —, ikili | Bozulma rejimi | 1 normal, 0 anormal bozulma dönemi. 0 anlık duruş veya yaşam sonu demek değildir; doğrudan ölçülen sensör değildir. |

<a id="w-kosullar"></a>
## W — Uçuş ve çalışma koşulları: 4 değişken

Kaynak: [Table 4](https://doi.org/10.3390/data6010005).

| Kod | Tam İngilizce ad | Türkçe | Birim | Bileşen / konum | Temsil ve yorum |
|---|---|---|---|---|---|
| `alt` | Flight altitude | Uçuş irtifası | ft | Uçuş ortamı / giriş | Atmosfer ve motor çalışma noktasını etkiler; tek başına motor sağlığı göstergesi değildir. |
| `Mach` | Flight Mach number | Uçuş Mach sayısı | Boyutsuz | Uçuş hızı / giriş | Hızın yerel ses hızına oranı. 0,7 sabit bir km/saat değeri değildir; ses hızı ortamla değişir. |
| `TRA` | Throttle-resolver angle | Gaz kolu / güç talebi göstergesi | % | Güç yönetimi / kumanda | Adında angle olsa da Table 4 yüzde verir; derece yazmayın. Doğrudan Newton cinsinden itki değildir. |
| `T2` | Fan-inlet total temperature | Fan giriş toplam sıcaklığı | °R | Fan girişi | Giriş akışının toplam sıcaklığı; uçuş/ortam koşulu. X_s içindeki T24 gibi iç istasyon sıcaklıklarından ayrı W değişkenidir. |

<a id="xs-fiziksel"></a>
## X_s — Fiziksel olarak ölçülebilir sensörler: 14 değişken

Kaynak: [Table 5](https://doi.org/10.3390/data6010005). Sıra dosyanın X_s_var sırasıdır; basılı tablonun sırası değildir.

| Kod | Tam İngilizce ad | Türkçe | Birim | Bileşen / konum | Temsil ve yorum |
|---|---|---|---|---|---|
| `T24` | Low-pressure-compressor discharge total temperature | LPC çıkış toplam sıcaklığı | °R | LPC çıkışı | Sıkıştırma sonrası termal durum. T2 ve koşullarla birlikte okunur; tek başına verim hesabı değildir. |
| `T30` | High-pressure-compressor discharge total temperature | HPC çıkış toplam sıcaklığı | °R | HPC çıkışı | Yanma öncesi sıkıştırılmış havanın sıcaklığı. Yük ve sıkıştırma durumundan etkilenir. |
| `T48` | High-pressure-turbine discharge total temperature | HPT çıkış toplam sıcaklığı | °R | HPT çıkışı | Türbinde enerji çekilmesi sonrası termal durum. HI tanımında referans koşullardaki T48 kullanılır; ham T48 doğrudan HI değildir. |
| `T50` | Low-pressure-turbine discharge total temperature | LPT çıkış toplam sıcaklığı | °R | LPT çıkışı | Türbin zinciri sonundaki termal durum; T48 ile farklı konumdadır. |
| `P15` | Bypass-duct total pressure | Bypass kanalı toplam basıncı | psia | Fan bypass kanalı | Çekirdeği dolaşan akışın basıncı; HPC basıncıyla aynı yer değildir. |
| `P2` | Fan-inlet total pressure | Fan giriş toplam basıncı | psia | Fan girişi | İrtifa/Mach etkisini taşır; mutlak toplam basınçtır, gösterge basıncı değil. |
| `P21` | Fan-discharge total pressure | Fan çıkış toplam basıncı | psia | Fan çıkışı | Fan sonrası akış durumu. P2 ile birlikte incelenebilir; kendisi hesaplanmış basınç oranı değildir. |
| `P24` | Low-pressure-compressor discharge total pressure | LPC çıkış toplam basıncı | psia | LPC çıkışı | T24 ile aynı bileşen çıkışının farklı fiziksel büyüklüğünü betimler. |
| `Ps30` | High-pressure-compressor discharge static pressure | HPC çıkış statik basıncı | psia | HPC çıkışı | Yerel statik mutlak basınç. Sanal P30 toplam basınçtır; birbirinin yerine kullanılmaz. |
| `P40` | Combustor-discharge total pressure | Yanma odası çıkış toplam basıncı | psia | Combustor çıkışı / HPT girişi | Yanma sonrası basınç durumu. Yanma sıcaklığı artırsa da basınç mutlaka artmaz. |
| `P50` | Low-pressure-turbine discharge total pressure | LPT çıkış toplam basıncı | psia | LPT çıkışı | Türbin sonrası basınç; çıkış akışı ve ortam koşullarıyla birlikte yorumlanır. |
| `Nf` | Physical fan rotational speed | Fanın fiziksel dönüş hızı | rpm | Fan / düşük basınç mili | Fiziksel mil hızı; sıcaklıkla düzeltilmiş hız olduğu varsayılmaz. Güç talebine bağlıdır. |
| `Nc` | Physical core rotational speed | Çekirdeğin fiziksel dönüş hızı | rpm | Yüksek basınç / çekirdek mili | Nf ile aynı mil değildir; iki hızın ölçekleri farklı olabilir. |
| `Wf` | Fuel mass-flow rate | Yakıt kütlesel debisi | pps = lbm/s | Yakıt beslemesi / combustor | Birim zamanda verilen yakıt kütlesi. Hava debisi veya yakıt/hava oranı değildir; yük/komut etkisi içerir. |

<a id="xv-sanal"></a>
## X_v — Modelden hesaplanan sanal sensörler: 14 değişken

Kaynak: [Table 6](https://doi.org/10.3390/data6010005). Bu kanalların uygulamada erişilebilirliği ayrıca doğrulanmalıdır.

| Kod | Tam İngilizce ad | Türkçe | Birim | Bileşen / konum | Temsil ve yorum |
|---|---|---|---|---|---|
| `T40` | Combustor-discharge total temperature | Yanma odası çıkış toplam sıcaklığı | °R | Combustor çıkışı / HPT girişi | İç model sıcaklık çıktısı. T48 sonraki HPT çıkışıdır; aynı yer değildir. |
| `P30` | High-pressure-compressor discharge total pressure | HPC çıkış toplam basıncı | psia | HPC çıkışı | Sanal toplam basınç. Fiziksel Ps30 statik basınçtır; eşit varsayılmaz. |
| `P45` | High-pressure-turbine discharge total pressure | HPT çıkış toplam basıncı | psia | HPT çıkışı | Table 6'nın verdiği konum. T48 ile istasyon numarasının aynı olması gerekmez; isimden yeni konum türetilmez. |
| `W21` | Fan mass-flow rate | Fan kütlesel debisi | pps = lbm/s | Fan | Fan akışının model çıktısı. Çekirdek debileriyle aynı büyüklükte olmak zorunda değildir. |
| `W22` | Low-pressure-compressor outlet mass-flow rate | LPC çıkış kütlesel debisi | lbm/s | LPC çıkışı (Table 6) | Basılı kaynak açıklaması esas alınır. W25 ile ilişkili olsa da aynı kolon değildir; istasyon adından farklı konum varsaymayın. |
| `W25` | High-pressure-compressor inlet mass-flow rate | HPC giriş kütlesel debisi | lbm/s | HPC girişi | Kompresöre giren model akışı. Bleed/akış yolları nedeniyle diğer debilerle eşit varsayılmaz. |
| `W31` | High-pressure-turbine cooling bleed mass-flow rate, W31 channel | HPT soğutma bleed debisi, W31 | lbm/s | HPT soğutması | Soğutma için ayrılan akış. Kaynak W31/W32 için aynı genel açıklamayı verir; özel kademe/rotor ataması doğrulanmamıştır. |
| `W32` | High-pressure-turbine cooling bleed mass-flow rate, W32 channel | HPT soğutma bleed debisi, W32 | lbm/s | HPT soğutması | Ayrı bir model kanalıdır. Tam devre/kademe ataması için model dokümanı gerekir; isimden uydurulmaz. |
| `W48` | High-pressure-turbine outlet mass-flow rate | HPT çıkış kütlesel debisi | lbm/s | HPT çıkışı | Türbin gaz akışı. Yanma/soğutma yolları nedeniyle önceki hava debisinin kopyası sayılmaz. |
| `W50` | Low-pressure-turbine outlet mass-flow rate | LPT çıkış kütlesel debisi | lbm/s | LPT çıkışı | Türbin sonrası model akışı. Kütlesel ve hacimsel debi aynı kavram değildir. |
| `SmFan` | Fan stall margin | Fan stall marjı | — (Table 6) | Fan kararlılık payı | Kararlı çalışma sınırına ilişkin model rezervi. Birimi kaynakta yüzde verilmez; fan verimi veya HI değildir. |
| `SmLPC` | Low-pressure-compressor stall margin | LPC stall marjı | — (Table 6) | LPC kararlılık payı | Koşullara bağlı sanal çıktı. Ham değişim tek başına bozulma kanıtı değildir. |
| `SmHPC` | High-pressure-compressor stall margin | HPC stall marjı | — (Table 6) | HPC kararlılık payı | Yüksek basınç kompresörü rezervi. HI modelinde referans koşullarda değerlendirilir. |
| `phi` | Fuel-flow-to-Ps30 ratio (paper definition) | Yakıt debisinin Ps30'a oranı (makale tanımı) | pps/psi (Table 6; dosya ölçeği belirsiz) | Yakıt / HPC çıkış basıncı ilişkisi | Boyutsuz fuel–air ratio veya eşdeğerlik oranı diye adlandırmayın. Yerel ilk satır yalın oranla uyuşmuyor; aşağıdaki notu okuyun. |

<a id="t-saglik"></a>
## T — Simülasyon iç sağlık parametreleri: 10 değişken

Kaynak: [Table 7, Sections 2.1 ve 3.1](https://doi.org/10.3390/data6010005). Bunlar sensör değil, bileşenin verim/akış kapasitesi davranışını değiştiren **model parametreleridir**. Gerçek termodinamik verim veya lbm/s debi değildir. Her satırda işaret ve ölçek korunmalı; `-0,018` doğrudan “%1,8 gerçek verim kaybı” diye sunulmamalıdır. Böyle bir nicel dönüşüm için parametrenin modelde nasıl uygulandığı, nominal harita ve referans tanımı doğrulanmalıdır.

| Kod | Tam İngilizce ad | Türkçe | Birim | Bileşen | Temsil ve yorum |
|---|---|---|---|---|---|
| `fan_eff_mod` | Fan efficiency modifier | Fan verim değiştiricisi | Boyutsuz | Fan | Fan verim davranışının iç ayarı; ölçülmüş verim değil. Sıfır, bu parametrede değişim uygulanmadığını belirtir; bütün motor sağlıklı demek değildir. |
| `fan_flow_mod` | Fan flow-capacity modifier | Fan akış kapasitesi değiştiricisi | Boyutsuz | Fan | Fan akış kapasitesinin iç ayarı; W21 debisi değil. Nominal modele göre yorumlanır. |
| `LPC_eff_mod` | Low-pressure-compressor efficiency modifier | LPC verim değiştiricisi | Boyutsuz | LPC | LPC verim davranışının iç ayarı. İşareti/ölçeği yüzde kayıp varsayımıyla değiştirilmez. |
| `LPC_flow_mod` | Low-pressure-compressor flow-capacity modifier | LPC akış kapasitesi değiştiricisi | Boyutsuz | LPC | LPC akış kapasitesinin iç ayarı; W22 gibi lbm/s sinyali değildir. |
| `HPC_eff_mod` | High-pressure-compressor efficiency modifier | HPC verim değiştiricisi | Boyutsuz | HPC | HPC verim davranışının iç ayarı. Tek başına gerçek motor verimini vermez. |
| `HPC_flow_mod` | High-pressure-compressor flow-capacity modifier | HPC akış kapasitesi değiştiricisi | Boyutsuz | HPC | HPC akış kapasitesinin iç ayarı; W25 ile farklı tür değişkendir. |
| `HPT_eff_mod` | High-pressure-turbine efficiency modifier | HPT verim değiştiricisi | Boyutsuz | HPT | HPT verim davranışının iç ayarı. Başlangıç aşınması nedeniyle ilk uçuşta sıfırdan farklı olabilir; ilk ≠0 arıza başlangıcı değildir. |
| `HPT_flow_mod` | High-pressure-turbine flow-capacity modifier | HPT akış kapasitesi değiştiricisi | Boyutsuz | HPT | HPT akış kapasitesinin iç ayarı; W48 debisinden ayrı. Sıfır olması diğer sağlık parametrelerinin de sıfır olduğu anlamına gelmez. |
| `LPT_eff_mod` | Low-pressure-turbine efficiency modifier | LPT verim değiştiricisi | Boyutsuz | LPT | LPT verim davranışının iç ayarı. Eğrisi açıklayıcı model bilgisidir, doğrudan ölçülebilir sensör değildir. |
| `LPT_flow_mod` | Low-pressure-turbine flow-capacity modifier (symbol-based interpretation) | LPT akış kapasitesi değiştiricisi | Boyutsuz | LPT; basılı açıklama çelişkisine bakın | Sembol/parametre ailesine dayalı yorum. Table 7 açıklamasında HPT yazılmıştır; bu çelişki aşağıda açıkça kaydedilir. |

<a id="y-rul"></a>
## Y — Kalan faydalı ömür: 1 değişken

Kaynak: [Table 3 ve Sections 3.2/4.1](https://doi.org/10.3390/data6010005).

| Kod | Tam İngilizce ad | Türkçe | Birim | Bileşen / kapsam | Temsil ve yorum |
|---|---|---|---|---|---|
| `RUL` | Remaining useful life | Kalan faydalı ömür | Uçuş döngüsü (cycle) | Motorun kalan operasyonel ömrü | Y_dev hedefidir; Y_var yoktur. DS02 dev'de aynı uçuş içinde sabittir. Motor 2 ilk uçuş RUL=74, son uçuş RUL=0. Saniye değil kalan uçuş sayısıdır; hedefi kendi girdisi yapmak sızıntıdır. |

<a id="fc-siniflari"></a>
## Fc sınıfları ve DS02 dev kapsamı

| Fc | Adlandırma | Table 1 örnek süre aralığı | Yorum |
|---|---|---|---|
| 1 | Kısa uçuş | 1–3 saat | Kısa görev profili; motorun toplam ömrünün kısa olması demek değildir. |
| 2 | Orta uçuş | 3–5 saat | Orta görev profili. Sınırda kalan uçuşları kendi başınıza yeniden sınıflandırmayın. |
| 3 | Uzun uçuş | >5 saat | Section 3.4.1 örneği 5–7 saat anlatır; bunu tüm uzun uçuşlar için evrensel üst sınır saymayın. |

Sınıf gerçek uçuş profilinin süresine göre tanımlanır ve modelleme yaklaşımında motor başına bir kez atanır. **Yerel DS02 dev'nin altı motorunun hepsi Fc=3**; önceki 05 dağılımı bütün 5.263.447 dev satırında bunu doğrulamıştır. Bu alt bölümün uzun uçuş sınıfı motorları kapsaması bir örneklem özelliğidir; analizde kısa/orta uçuşları filtreleyip sildiğimiz anlamına gelmez.

Makale Table 2 DS02 bütünü için 1,2,3 sınıflarını listeler. Section 3.4.3, dev dışında kalan Unit 11/14/15 için sırasıyla 3/1/2 sınıflarını anlatır. Bu **makaledeki kapsam bilgisidir**; burada test ölçümleri okunmamış/analize alınmamıştır. “Bütün N-CMAPSS'te yalnızca Fc=3 var” ve “DS02'nin tamamı tek sınıflı” ifadeleri yanlıştır. [Tables 1–2, Sections 2.2 ve 3.4.3](https://doi.org/10.3390/data6010005).

Kayıtlı satır sayısından doğrudan saat hesabı yapılmaz: örnekleme bilgisi ve kaydın kapsadığı uçuş bölümü doğrulanmalıdır. Makaledeki uçuş izleri alt >10.000 ft profillerini anlatır. `sample_index` zaman damgası değildir; Fc, kaydedilmiş alt bölümün örnek sayısından yeniden tanımlanmaz.

<a id="saglik-kavramlari"></a>
## hs, HI, RUL ve EOL birbirinden nasıl ayrılır?

| Kavram | Tür | Sorduğu soru | Kritik ayrım |
|---|---|---|---|
| hs | İkili bozulma rejimi etiketi | Normal mi anormal dönem mi? | 1 normal, 0 anormal; yüzde veya kalan ömür değildir. |
| HI — Health Index | Referans koşullara dayalı sağlık indeksi | Operasyonel sınıra ne kadar pay kaldı? | Sürekli indeks; hs'nin başka yazımı değildir. 47 sütun içinde ayrı HI kolonu yoktur. |
| RUL | Hedef, uçuş döngüsü | Kaydedilmiş yaşam sonuna kaç uçuş kaldı? | Aynı hs altında farklı RUL olabilir. |
| EOL — End of Life | Yaşam sonu olayı / sınırı | Yaşam hangi cycle'da sonlanıyor? | hs=0'a geçilen anla aynı değildir; fiziksel anlık motor duruşu kaydı sayılmaz. |

Section 4.2 sağlıklı rejimde hs=1 olduğunu ve normal bozulma yaşandığını açıklar. Başlangıç aşınması ve kullanıma bağlı değişimler normal dönemde de vardır: **hs=1 kusursuz/yepyeni motor demek değildir.** Anormal rejime geçiş bozulma mekanizmasının değişmesidir; motor sonrasında birçok uçuş boyunca çalışabilir. hs=0 “o satırda motor durdu” anlamına gelmez.

Section 3.2'de HI, dört normalize kalan operasyonel payın **minimumu** olarak tanımlanır. Referans koşullarda fan/LPC/HPC marjları ve T48 değerlendirilir; aşınma payları operasyonel eşiklere göre normalize edilir. Referans örneği alt=20.000 ft, Mach=0,7, TRA=%100'dür. Ham uçuş SmFan/T48 değerlerinin min'ini alarak HI hesaplanamaz: temiz motor referansı, eşikler ve referans koşul değerlendirmesi gerekir. Bu projede HI türetilmemiştir.

Makale yaşam sonu için HI=0 ölçütünü anlatır; Section 3.2 ayrıca 100 operasyonel cycle'ın aşılmasını simülasyon durdurma sınırı olarak verir. Bunları gerçek uçakta ani mekanik duruşla eşitlemeyin. Yerel dev yaşamları 63–89 cycle olduğundan 100-cycle sınırı hakkında veri içinden yeni bir sonuç çıkarmıyoruz.

**Somut örnek:** Motor 2 son cycle=75; cycle 40 için RUL=35'tir. hs=0 ise anormal bozulma dönemindeyken kayıtlı yaşam sonuna hâlâ 35 uçuş kaldığını anlatır; HI=0 demek değildir. RUL=0 son uçuş etiketi olabilir ve o uçuş birçok örnek içerebilir; arızanın uçuş içi saniyesini vermez. **Temsili örnek:** hs=1 ile HI=0,95 birlikte mümkün olabilir; normal aşınmada HI tam 1 olmak zorunda değildir. Bu HI sayısı yerel dosyada ölçülmüş bir değer değildir. [Sections 3.1–3.2 ve 4.2](https://doi.org/10.3390/data6010005).

### T parametreleri ile hs ilişkisi

Başlangıç aşınması/normal dönem nedeniyle T ilk uçuşta sıfırdan farklı olabilir. İlk ≠0 cycle, hs geçişi veya belirgin arıza başlangıcıyla eşitlenmez. Önceki tam-kapsam 05 çalıştırmasında:

| Motorlar | Sıfırdan farklı parametreler | Diğer T parametreleri |
|---|---|---|
| 2, 5, 10 | HPT_eff_mod | İlgili motorlarda dokuzu sabit sıfır |
| 16, 18, 20 | HPT_eff_mod, LPT_eff_mod, LPT_flow_mod | İlgili motorlarda yedisi sabit sıfır |

Bu bir sensör veya arıza şiddeti sıralaması değildir. Örneğin HPT_eff_mod=-0,018'i doğrudan yüzde 1,8 gerçek verim kaybına çevirmek için yeterli bilgi yoktur. Değiştirici ile gerçek termodinamik verim η aynı nicelik değildir.

<a id="birimler"></a>
## Birimleri doğru okumak

| Birim | Anlam | Öğretici dönüşüm / uyarı |
|---|---|---|
| °R | Rankine, mutlak sıcaklık | K=°R×5/9; °C=°R×5/9−273,15. 600 °R yaklaşık 60,18 °C; 600 °C değildir. |
| psia | Pounds-force per square inch, absolute | Vakum referanslı mutlak basınç. 1 psi yaklaşık 6.894,757 Pa. Atmosfer referanslı psig ile aynı değildir. |
| rpm | Revolutions per minute | Devir/dakika; 60 rpm=1 devir/s. Düzeltilmiş hız olduğu varsayılmaz. |
| pps / lbm/s | Pounds mass per second | Kütlesel debi; 1 lbm/s=0,45359237 kg/s. Yakıt/hava kanalları aynı birimde olsa da farklı akışlardır. |
| ft | Foot | 1 ft=0,3048 m; irtifa birimi. |
| Mach | Hız / yerel ses hızı | Boyutsuz; sabit km/saat dönüşüm katsayısı yoktur. |
| % | Yüzde gösterimi | TRA için kaynak birimi; derece, Newton veya verim yüzdesi değildir. |
| — | Birim verilmemiş / boyutsuz | Fc/unit/hs etiket, T model parametresi, marjlar kaynakta boyutsuz gösterimdir. Aynı işaret aynı fiziksel anlam demek değildir. |
| pps/psi | Kütlesel debi / basınç | phi için kaynak birimi; boyutsuz değildir. Bu dosyanın ölçek uyumu belirsizdir. |
| cycle | Uçuş döngüsü | RUL kalan uçuş sayısıdır; A'daki cycle sayacı Table 8'de — gösterilir. |

Dönüşümler öğretici bilgi içindir; hiçbir veri dönüştürülmemiştir. [NIST SP 811 birim rehberi](https://www.nist.gov/pml/special-publication-811/nist-guide-si-appendix-b-conversion-factors/nist-guide-si-appendix-b8) destekleyici kaynaktır. Grafik kodları korunur; “özgün değer” Y etiketlerinin fiziksel birimleri bu sözlükten okunur.

### Kaynak–dosya eşleştirmesindeki açık noktalar

1. **TRA:** adına bakıp derece yazmayın; Table 4 `%` verir. T2 bir W koşuludur, aynı °R birimine sahip X_s sıcaklıklarıyla aynı görevde değildir.
2. **Stall margin:** Table 6 — kullanır; yüzde/sağlık yüzdesi eklenmemiştir. Sağlık metnindeki surge terimi farkı not edilmiştir; ayrıntılı konvansiyon için model dokümanı gerekir.
3. **LPT_flow_mod:** Table 7'de sembol LPT_flow_mod, açıklama HPT flow modifier olarak basılmıştır. Bu sözlük **sembol ve simetrik parametre ailesine dayalı yorum** olarak LPT der; çelişki gizlenmez ve resmi bir düzeltme iddiası taşımaz.
4. **W22/W31/W32:** W22 için Table 6 LPC çıkışını verir. W31/W32 aynı genel HPT coolant bleed açıklamasına sahiptir; rotor/stator/kademe ayrımı burada doğrulanmamıştır.
5. **phi:** Table 6 yakıt debisinin Ps30'a oranını, pps/psi birimini verir. Ancak aşağıdaki ilk dev satır kontrolünde yalın oran dosyadaki değerle uyuşmaz. Ölçekleme/çıktı tanımı resmi CMAPSS uygulamasından doğrulanmadan phi yeniden hesaplanmamalı veya boyutsuz fuel–air equivalence ratio diye anlatılmamalıdır.

| İlk dev satır kontrolü | Değer |
|---|---:|
| Wf (pps) | 3,85533723901 |
| Ps30 (psia) | 331,293679213 |
| Yalın Wf/Ps30 | 0,0116372194247 |
| Dosyadaki phi | 41,8939899289 |

Bu tek satır **uyuşmazlık kanıtıdır**, bütün dosyanın dönüşüm kuralı değildir. Dosyanın bozuk olduğunu da kanıtlamaz. Veri/hesaplama değiştirilmemiş; konu açık doğrulama sorusu olarak bırakılmıştır.

<a id="turetilmis"></a>
## Türetilmiş sütunlar — özgün 47 değişkene dahil değil

| Sütun / aile | Anlam | Birim / kapsam ve yorum |
|---|---|---|
| sample_index | Seçili uçuşta 0'dan başlayan örnek sırası | Örnek sayacı; saniye değil. Artan HDF5 satır sırasını korur, zaman aralığını vermez. |
| satır_indeksi | 01 ilk 10 satır tablosunun indeks adı | Satır konumu; sensör değildir. |
| life_progress | (cycle−ilk cycle)/(son cycle−ilk cycle) | 0–1; geriye dönük görsel hizalama. Son cycle gelecek bilgisidir, doğrudan tahmin girdisi olmaz. |
| n_samples, satır_sayısı | Uçuş/grup ölçüm sayısı | Ölçüm adedi; uçuş süresi veya motor ömrüyle aynı kavram değil. |
| n_flights, uçuş_sayısı | Kayıtlı uçuş sayısı | Uçuş adedi; toplam yaşam uçuşu tahmin anında bilinmeyebilir. |
| *_median, *_q1, *_q3 | İlgili uçuşun tüm ölçümlerinden medyan/%25/%75 kuantili | Temel değişkenin birimi. Q1–Q3 dağılımdır, güven aralığı değil. Medyanların medyanı ile tüm satırların medyanı genel olarak eşit değildir. |
| *_min, *_max | Uçuş/motor bazında uç değerler | Temel değişken birimi; kapsam tabloya göre okunur. Uç değer otomatik hata değildir. |
| RUL_first/median/min/max, first_RUL, last_RUL | Hedef özetleri | Kalan uçuş döngüsü; model girdisi değil EDA/etiket denetimi. RUL_constant uçuş içi sabitlik kontrolüdür. |
| Fc_values, hs_values, *_counts, *_nunique | Etiket kümeleri/dağılımları | Ölçüm ağırlıklı sayı ile sınıfı içeren uçuş sayısı farklıdır; hs ortalaması sağlık yüzdesi değildir. |
| first_nonzero_cycle, nonzero_samples, *_nonzero_n | T'deki ilk tam ≠0 gözlemi ve sayısı | Cycle/ölçüm adedi; belirgin bozulma veya hs geçişi kararı değil. |
| matched_n, matched_fraction, seçilen_yüzde | 04 yardımcı koşul kutusu kapsamı | Adet/0–1 oranı/%. Veri silme değil karşılaştırma kapsamıdır. |
| *_matched_q1/median/q3 | Yardımcı alt grup kuantilleri | Temel değişken birimi. Ham özetlerin yerine geçmez; seçim yanlılığı vardır. |
| alt_grup_dışındaki, genel_analizde, yardımcı_karşılaştırmada | 04 kapsam kontrolü | Adet/Boolean. Cycle 13,24,31,63 ana EDA'da kalır; yalnızca kutuda temsil edilmeyebilir. |
| nonfinite_count, n_valid, status | Veri kalitesi / sabitlik | Adet/kategori; değişken, sabit sıfır, sabit sıfır dışı ayrılır. Önem sıralaması değildir. |

### Grafik okuma örnekleri

- **02:** unit=2/cycle=1 olan her satır bir örnektir; bütün uçuşun özeti değildir. hs=1 ve RUL=74 birlikte olabilir. 47 özgün değişken+sample_index=48 sütun; A/Y sensör diye adlandırılmaz.
- **03:** X adımı örnektir. T24 eğrisi uçuş koşullarını ve motor yanıtını birlikte taşır. Aynı uçuşta RUL sabitken sensörlerin değişmesi çelişki değildir.
- **04:** her nokta bir uçuşun bütün ölçümlerinden medyandır. X adımı uçuş, 03'te örnektir. T eğrisi sensör değil iç sağlık bilgisidir. Koşul alt grubu ana EDA yerine geçmez.
- **05:** aynı cycle farklı motorlarda aynı sağlık değildir. Normalize yaşam yalnızca geriye dönük hizalar; aynı Fc koşulları eşitlemez.

<a id="model-sinirlari"></a>
## Gerçekçi RUL modeline bütün sütunlar neden otomatik girdi olmaz?

| Aile | EDA rolü | Model kararı için sınır |
|---|---|---|
| RUL ve hedef özetleri | Etiket/doğrulama | Hedefin kendisini veya kalan ömrü kodlayan özetini girdi yapmak hedef sızıntısıdır. |
| T_dev / iç sağlık özetleri | Açıklama/doğrulama | Gerçek uçakta doğrudan ölçülmez. Oracle veya ayrı fizik-bilgili senaryo tanımlanmadan standart sensör girdisi sayılmaz. |
| hs | Normal/anormal etiketi | Gerçek kullanımda biliniyor mu? Simülasyon ground-truth etiketini vermek modelin bilmemesi gereken sağlığı açığa çıkarabilir. Ayrı hs kestirimi burada yapılmamıştır. |
| X_v | İç model çıktıları | Uygulamada hangi erişilebilir sinyaller/modelle üretilecek? Gerçek sanal sensörün kestirim hatası bilinmeden ücretsiz sensör kabul edilmez. |
| X_s / W | Ölçülebilir yanıtlar/koşullar | Aday bilgi kaynakları; erişim, birim, örnekleme, nedensel zaman penceresi ve koşul farkları doğrulanmalıdır. Bu sözlük özellik seçmez. |
| unit | Motorları ayırma | Kimlik ezberlenmesi motorlar arası genellemeyi bozabilir; otomatik sayısal sensör değildir. |
| cycle / Fc | Kullanım/görev bilgisi | Tahmin anında bilinirliği ve veri kapsamı değerlendirilmeli; sağlık etiketleri değildir. |
| life_progress / son cycle / toplam yaşam uçuşu | Tam yaşamların karşılaştırılması | Gelecekteki yaşam sonunu kullanır; tahmin anında bilinmeyen bilgi içerir. |
| Bütün uçuş örneklerinden özet | EDA | Uçuş bitiminde erişilebilir olabilir; uçuş ortasında gelecekteki örnekleri kullanmak sızıntı yaratır. Tahmin anı açıkça tanımlanmalıdır. |

Bu modelleme veya sensör elemesi değildir. Makale Section 4.1 W/X_s/Y ile prognostik problemi, Section 4.2 sağlık etiketleriyle tanılama problemini ayrı kurar. Simülasyon iç bilgisini kullanan araştırma, gerçek sensör erişimiyle aynı iddiayı taşımaz. [Sections 4.1–4.2](https://doi.org/10.3390/data6010005).

<a id="notebook-rehberi"></a>
## Danışmana beş notebook'u anlatma sırası

1. **01:** HDF5 grupları fiziksel cihaz değil dizilerdir; metadata, 47 sütun, satır hizası ve bellek sınırı açıklanır.
2. **02:** motor/uçuş seçimiyle örnek satırının anlamı gösterilir. A kimlik/etiket, W koşul, X_s/X_v yanıt, T iç sağlık, Y hedef diye okunur. CSV'nin eksiksiz olması model girdisi seçildiği anlamına gelmez.
3. **03:** tek uçuşta sensör ve koşul değişimleri birlikte okunur. X ekseni saniye değil örnek; farklı birimler ayrı Y eksenlerindedir.
4. **04:** tek motorun bütün uçuşlarından medyan/kuantiller, sağlık rejimi ve T'nin açıklayıcı rolü gösterilir. Yardımcı kutu bir seçimdir; nedensellik sağlamaz.
5. **05:** altı motorun kapsamı, farklı iç sağlık parametreleri ve koşulları birlikte değerlendirilir. Sağlık durum matrisi şiddet sıralaması değildir.

## Açık kalan sorular ve sürüm notu

- phi ölçeği/çıktı tanımı, Table 7 LPT_flow_mod açıklama çelişkisi ve W31/W32 devre ayrımı resmi CMAPSS uygulamasıyla ayrıca netleştirilmelidir. Bu doküman veri düzeltmesi veya model varsayımı uygulamaz.
- HI ayrı kolon olmadığı için gerçek bir HI eğrisi çıkarılmış gibi sunulmaz.
- Birimler artık kaynakla açıklanmıştır; önceki genel “özgün değer” eksenleri ve kod içindeki birim doğrulama notları değiştirilmemiştir. Yeni Markdown bu eski üretim bağlamına güncel kaynak açıklamasını ekler.
- Kaynak notebook'ların çıktıları ve paylaşım notebook'larının taşınabilir yolları/temiz çıktıları ayrı ayrı korunur. Bu görev yalnızca yeni Markdown ve sözlük ekler; tam EDA/model eğitimi çalıştırılmaz.

## Kaynaklar

1. [Arias Chao vd. (2021), DOI: 10.3390/data6010005](https://doi.org/10.3390/data6010005). [Yayıncı PDF, CC BY 4.0](https://mdpi-res.com/d_attachment/data/data-06-00005/article_deploy/data-06-00005-v2.pdf?version=1611240730). Tables 1–8; Sections 2.1–2.3, 3.1–3.3, 3.4.3, 4.1–4.2.
2. [NASA NTRS makale kaydı](https://ntrs.nasa.gov/citations/20210020068).
3. [NASA Glenn turbofan](https://www.grc.nasa.gov/www/k-12/airplane/Animation/turbtyp/etfp.html), [gaz türbini](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/turbine-engines/): öğretici bileşen bağlamı.
4. [NIST SP 811 Appendix B.8](https://www.nist.gov/pml/special-publication-811/nist-guide-si-appendix-b-conversion-factors/nist-guide-si-appendix-b8): birim dönüşümleri.
5. Yerel HDF5 metadata dizileri ve önceden üretilmiş 05 `engine_summary.csv`, `class_distribution.csv`, `health_summary.csv`: gerçek adlar ve dev kapsamı. HDF5 dokümana/Git deposuna kopyalanmaz.


## Görsel atlas ve güncel grafik etiketleri

[DS02 Motor ve Sensör Atlası](DS02_Motor_ve_Sensor_Atlasi.md), özgün temsili kesit/akış şemaları ve 28 sensörün fiziksel yorum rehberini içerir. Notebook 02–05'in ad/birim etiketleri artık [merkezi metadata dosyasından](assets/ds02_variable_metadata.json) alınır; önceki “yalnız Markdown ekleme” ve genel eksen etiketleri hakkındaki sürüm notları önceki dokümantasyon aşamasını anlatır. Yeni aşamada yalnızca görsel etiket eşlemeleri eklenmiş; veri ve istatistikler değiştirilmemiştir. TRA makale Table 4'e göre %; phi ve LPT_flow_mod belirsizlikleri aynen korunur.
