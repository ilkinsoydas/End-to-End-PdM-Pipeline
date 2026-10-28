# N-CMAPSS DS02: 1D-CNN Deney ve Analiz Raporu

**Hazırlayan:** Melih Şişkular  
**Durum:** İlk altı-fold referansı, fiziksel hata analizi ve fold 5 uzun eğitim deneyi tamamlandı.  
**Tarih:** 23 Ekim 2026

Bu rapor mevcut deneyleri bir araya getirir. Yeni seed ve ek özellik deneyleri henüz yapılmamıştır.

## 1. Araştırma amacı

Çalışma koşulları ve fiziksel sensör dizilerinden motorun kalan faydalı ömrünü (RUL) tahmin etmek; hataların motorlar ve ömür evreleri arasında nasıl değiştiğini incelemek. Bu çalışma RUL regresyonudur; henüz doğrulanmış bir arıza sınıflandırma veya erken uyarı sistemi değildir.

## 2. Veri ve deney düzeni

- Dosya: N-CMAPSS_DS02-006.h5.
- Geliştirme motorları: 2, 5, 10, 16, 18, 20. Toplam 446 uçuş ve 5.270 seçilmiş pencere.
- Girdiler: dört çalışma koşulu (alt, Mach, TRA, T2) ve 14 fiziksel sensör.
- Pencere uzunluğu: 256 örnek; stride: 1024. Pencereler arasında 768 örnek atlanır; uçuş sınırları aşılmaz.
- Altı fold: her deneyde beş motorla eğitim, kalan motorla doğrulama. Her fold sıfırdan eğitilir.
- StandardScaler yalnızca ilgili fold'un eğitim verisine fit edilir.
- T matrisindeki sağlık parametreleri sadece sonradan açıklayıcı analizde kullanılır. CNN girdisi değildir.
- Resmî test motorları 11, 14 ve 15 bu deneylere dahil edilmemiştir.

## 3. CNN mimarisi ve eğitim

Conv1d(18→32, kernel=5) → ReLU → Conv1d(32→64, kernel=5) → ReLU → zaman boyunca ortalama → Linear(64→32) → ReLU → Linear(32→1).

15.329 eğitilebilir parametre; Adam, öğrenme oranı 0,001; MSE kaybı; batch size 64; seed 42; en fazla 50 epoch; 8 epoch iyileşme olmazsa erken durdurma.

İki evrişim katmanının havuzlama öncesindeki yerel alıcı alanı 9 örnektir. Ortalama havuzlama bütün pencereyi özetler; model önceki uçuşları doğrudan görmez. En iyi epoch doğrulama MSE'siyle seçilir.

## 4. Altı fold sonuçları

| Fold | Doğrulama motoru | MAE | RMSE | Sabit referans RMSE | En iyi epoch |
|---|---:|---:|---:|---:|---:|
| 1 | 2 | 4,649 | 6,012 | 21,520 | 29 |
| 2 | 5 | 6,491 | 9,554 | 27,283 | 26 |
| 3 | 10 | 5,101 | 7,579 | 23,660 | 23 |
| 4 | 16 | 5,096 | 6,401 | 19,396 | 23 |
| 5 | 18 | 2,487 | 3,465 | 21,044 | 50 |
| 6 | 20 | 6,103 | 7,912 | 19,975 | 17 |

Motorlara eşit ağırlıkla MAE: **4,988 ± 1,407**; RMSE: **6,820 ± 2,065** döngü. ± değeri fold'lar arası örnek standart sapmasıdır; güven aralığı değildir.

Birleşik pencere MAE: 5,005; RMSE: 7,163. Referans ortalama RMSE'sine göre azalma yaklaşık %69,2'dir; bu oran sınıflandırma doğruluğu değildir. Referans, her fold'un eğitim RUL ortalamasını sabit tahmin eder.

İlk altı-fold deneyinde fold 5, 50 epoch sınırında bitmiştir. Sonradan yalnızca fold 5 için 150 epoch deneyi yapılmıştır; sonuçları aşağıdaki ayrı bölümde verilmiştir. Ana altı-fold tablo değiştirilmemiştir.

### İlk fold: öğrenme ve tahmin görselleri

![İlk fold öğrenme eğrileri](./CNN_Deney_ve_Analiz_Raporu/gorseller/ilk_fold_ogrenme.png)

İlk epoch'larda hata hızla düşer; sonraki kazançlar küçülür. En iyi epoch 29, durma epoch'u 37'dir. Eğitim RMSE'si güncellemeler sırasında, doğrulama RMSE'si epoch sonunda hesaplanır.

![İlk fold gerçek ve tahmin edilen RUL](./CNN_Deney_ve_Analiz_Raporu/gorseller/ilk_fold_tahmin.png)

Eşitlik çizgisinin üstü fazla kalan ömür tahmini, altı eksik tahmindir. Noktalar motor değil, penceredir.

![Motor 2 uçuş bazında tahmin](./CNN_Deney_ve_Analiz_Raporu/gorseller/ilk_fold_ucus.png)

Uçuş bazında MAE 4,540, RMSE 5,655'tir. Pencere tahminleri uçuş içinde ortalanmıştır; bu yeni bir eğitim sonucu değildir.

## 5. Hata ömür boyunca nasıl değişiyor?

| Gerçek RUL aralığı | Tüm pencerelerde MAE |
|---|---:|
| 0–10 | 1,72 |
| 11–25 | 2,56 |
| 26–50 | 5,58 |
| 51+ | 7,43 |

Altı motorun her birinde 0–10 aralığı en düşük MAE'ye sahiptir. Bu, son dönem örüntülerinin daha ayırt edilebilir olmasıyla uyumludur; tek başına erken uyarı başarısını veya nedenselliği kanıtlamaz.

Motor 5 ve 10 yüksek RUL'da eksik tahmin; motor 2, 16 ve 20 orta RUL'da fazla tahmin gösterir. Bütün tahminlere sabit düzeltme uygulamak uygun değildir.

![Motor ve ömür aralığına göre hata](./CNN_Deney_ve_Analiz_Raporu/gorseller/hata_haritasi.png)

## 6. Aynı kalan ömür, farklı sağlık durumları

Aşağıdaki değerler gerçek RUL 30–40 arasındaki uçuşların eşit ağırlıklı ortalamasıdır. Hata = tahmin − gerçek.

| Motor | Ortalama hata | HPT_eff_mod | LPT_eff_mod | LPT_flow_mod |
|---|---:|---:|---:|---:|
| 2 | +6,55 | −0,00242 | 0 | 0 |
| 5 | +0,20 | −0,00345 | 0 | 0 |
| 10 | −0,22 | −0,00322 | 0 | 0 |
| 16 | +9,79 | −0,00135 | −0,00120 | −0,00144 |
| 18 | +1,76 | −0,00147 | −0,00225 | −0,00190 |
| 20 | +10,94 | −0,00109 | −0,00138 | −0,00166 |

Aynı kalan ömür, aynı bileşen sağlık durumunu gerektirmiyor. Motor 16 ve 18'in HPT değerleri yakınken hatalarının farklı olması, yalnızca HPT ile açıklamanın eksik kaldığını gösteriyor. CNN bu gizli parametreleri kullanmadığı için bu tablo modelin karar mekanizmasını doğrudan açıklamaz.

## 7. Benzer HPT değeri, farklı kalan ömür

Her motorda HPT_eff_mod = −0,003 değerine en yakın uçuş seçilmiştir. Bu tek değişkene dayalı, keşifsel bir karşılaştırmadır; bütün sağlık durumu eşleştirilmiş değildir.

| Motor | Uçuş | HPT_eff_mod | Gerçek RUL |
|---|---:|---:|---:|
| 2 | 44 | −0,00295 | 31 |
| 5 | 51 | −0,00303 | 38 |
| 10 | 46 | −0,00301 | 36 |
| 16 | 43 | −0,00299 | 20 |
| 18 | 49 | −0,00300 | 22 |
| 20 | 48 | −0,00296 | 18 |

Yakın HPT değerlerinde kalan ömür 18–38 döngü arasında değişir. LPT durumları, bozulma seyri ve diğer farklılıklar birlikte incelenmelidir. Tek bir sağlık parametresinden evrensel bir RUL dönüşümü çıkarmak uygun değildir. Ardışık uçuş farkları gürültü içerdiğinden bozulma hızının etkisi bu tabloyla kanıtlanmış değildir.

## 8. Benzer sensör ortalamaları, farklı RUL

18 ham giriş sütununun pencere ortalamaları tüm geliştirme pencerelerinde standartlaştırıldı. Her pencerenin başka bir motordaki en yakın komşusu, 18 boyuttaki Öklid uzaklığı / √18 ile bulundu. RUL ve tahminler komşu seçiminde kullanılmadı. Bu ölçekleme yalnızca betimleyici analiz içindir; eğitime aktarılmamalıdır.

En yakın komşuların gerçek RUL farkının medyanı **9 döngü**; farkı en az 10 döngü olan pencerelerin oranı **%49,4**.

Somut bir örnekte motor 2'nin 1. uçuşundaki bir pencere (RUL 74), motor 10'un 37. uçuşundaki bir pencereye (RUL 45) yakın bulundu: standartlaştırılmış RMS uzaklık yaklaşık 0,0147; RUL farkı 29.

Bu, pencere ortalamalarının RUL'u tek başına belirlemeye yetmeyebileceğini destekler. **Ham 256 adımlık dizilerin aynı olduğunu göstermez.** Ortalamalar zaman içi bilgiyi kaybeder; ilişkili sensörler uzaklıkta tekrar ağırlık alır. Karşılaştırılan CNN tahminleri farklı fold modellerinden gelir. Çiftler bağımsız değildir ve aynı komşu tekrar kullanılabilir. Sonuç bir nedensellik veya model başarısızlığı testi değildir.

## 9. Çalışma koşullarını hesaba katınca ne kalıyor?

Yardımcı model, diğer beş motorda dört çalışma koşulundan sensör pencere ortalamalarını tahmin eden ikinci dereceden Ridge regresyonudur (alpha=10). Gözlenen sensör değeri eksi beklenen değer hesaplanır.

- Motor 2 ve 5'te T48, T50 ve Wf sapmaları geç dönemde yükselir; Nc, Ps30 ve P40 sapmaları düşer.
- Motor 20'de sıcaklık ve yakıt sapmaları yükselirken basınç ve devir davranışı farklılaşır.
- Çalışma koşulları ile uçuş bazındaki mutlak hatanın tek değişkenli Spearman ilişkilerinde |rho| < 0,28 bulunmuştur. Bu, doğrusal olmayan veya ortak koşul etkilerini dışlamaz.
- Pencere ortalama koşullarının eğitim motorlarındaki tekil min–max aralıklarının dışına çıkma oranı beş motorda %0, motor 20'de yaklaşık %0,26'dır. Ortak dağılım örtüşmesi bu testle doğrulanmaz.

**Önemli sınır:** Her motorun sapması farklı bir yardımcı modele göre hesaplanır. Motorlar arası sapma düzeyleri ortak bir fiziksel referans değildir. Aynı motor içindeki eğilimler daha güvenli yorumlanır. Yardımcı model tüm ömür evrelerini içerir; sağlıklı motor referansı değildir. Sıfır sapma, sıfır bozulma anlamına gelmez.

## 10. Kanıt, hipotez ve bilinmeyen

| Düzey | Açıklama |
|---|---|
| Gözlem | CNN altı fold'da da sabit referansı geçiyor. |
| Gözlem | Son ömür aralığında mutlak hata daha düşük. |
| Gözlem | Motorlara göre fazla/eksik tahmin yönü değişiyor. |
| Gözlem | Aynı RUL'da sağlık parametreleri farklı; yakın HPT değerlerinde RUL farklı. |
| Hipotez | Geç dönem sensör örüntüleri daha ayırt edilebilir olabilir. |
| Hipotez | Kısa gözlem penceresi ve motorlar arası bozulma farklılıkları RUL belirsizliği yaratabilir. |
| Bilinmeyen | CNN'in hangi sensörlere dayandığı; koşul sapmalarının eklenmesinin hatayı azaltıp azaltmayacağı. |

## 11. Sonraki kontrollü deney

Mevcut altı fold ilk CNN referansı olarak korunacaktır. Aday deney: çalışma koşullarına göre sensör sapmalarını ek özellik olarak kullanmak. Yardımcı model ve ölçekleyiciler her fold'da sadece eğitim motorlarıyla fit edilmelidir. Sağlık parametreleri girdilere eklenmeyecektir.

Önce aynı seed ve eğitim bütçesiyle karşılaştırma, ardından birden fazla seed ile kararlılık kontrolü yapılabilir. 18 girdiden daha fazla kanala geçiş parametre sayısını da artırır; iyileşmeyi yalnızca fiziksel açıklamaya bağlamamak için kapasite etkisi ayrıca dikkate alınmalıdır. Pencere ortalamalarıyla kurulan yardımcı model, zaman adımı düzeyine gerekçesiz aktarılmamalıdır.

Genel MAE/RMSE yanında orta RUL yanlılığı ve düşük RUL'daki fazla tahminler raporlanmalıdır. Resmî test kümesi son değerlendirmeye saklanacaktır.


## 13. Önemli sorular ve cevapları

**Neden test başarısı demiyoruz?** En iyi epoch doğrulama motoruyla seçildi. Sonuçlar geliştirme doğrulamasıdır; bağımsız test değildir.

**Neden yüzdelik doğruluk yok?** Hedef sürekli RUL değeridir. MAE ve RMSE döngü cinsinden hata ölçer.

**Neden T parametrelerini kullanmıyoruz?** Fiziksel sensörlerle tahmin hedefliyoruz; gizli simülasyon sağlık bilgileri yalnızca açıklayıcı analizde kullanılıyor.

**Neden son dönemde daha iyi?** Veriler daha belirgin sensör sapmalarıyla düşük hatanın birlikte görüldüğünü gösteriyor. Nedeni kesinleştirmek için kontrollü deney gerekir.

**Bu analiz arızanın fiziksel sebebini buldu mu?** Hayır. Bozulma örüntüleri ve hata arasındaki ilişkileri ortaya çıkardı; fiziksel nedensellik veya CNN açıklanabilirliği kanıtı değildir.

## 14. Veri kaynakları ve kapsam

Kullanıcının ürettiği fold_results.csv, summary.json, rul_band_metrics.csv, condition_support.csv, flight_correlations.csv, diagnostic_figures.pdf, window_diagnostics.csv ve flight_diagnostics.csv. Son iki dosyada sırasıyla 5.270 pencere ve 446 uçuş incelendi. Bütün bulgular mevcut DS02 geliştirme örneklemi ve seed 42 deneyine aittir. Uçuşlar ve pencereler bağımsız örnekler değildir; nedensel veya istatistiksel anlamlılık iddiası yapılmamıştır.


## 15. Ayrıntılı motor ve RUL aralığı sonuçları

Pozitif yanlılık fazla tahmin, negatif yanlılık eksik tahmindir. Fazla tahmin oranı hatanın büyüklüğünü göstermez.

| Motor | RUL aralığı | Pencere | MAE | RMSE | Yanlılık | Fazla tahmin oranı |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 0-10 | 118 | 1.288 | 1.614 | 1.086 | 0.856 |
| 2 | 11-25 | 177 | 2.024 | 2.500 | 1.763 | 0.853 |
| 2 | 26-50 | 284 | 7.424 | 8.245 | 7.414 | 0.996 |
| 2 | 51+ | 275 | 4.915 | 6.075 | -0.504 | 0.451 |
| 5 | 0-10 | 135 | 2.224 | 3.005 | 0.165 | 0.489 |
| 5 | 11-25 | 164 | 3.704 | 4.603 | -3.304 | 0.116 |
| 5 | 26-50 | 277 | 2.596 | 3.106 | 0.191 | 0.469 |
| 5 | 51+ | 458 | 11.103 | 13.783 | -10.682 | 0.111 |
| 10 | 0-10 | 110 | 1.576 | 1.999 | 0.089 | 0.482 |
| 10 | 11-25 | 178 | 2.469 | 2.915 | -2.322 | 0.079 |
| 10 | 26-50 | 299 | 2.280 | 2.918 | 0.375 | 0.522 |
| 10 | 51+ | 368 | 9.721 | 11.697 | -9.392 | 0.095 |
| 16 | 0-10 | 122 | 2.330 | 2.799 | 2.054 | 0.844 |
| 16 | 11-25 | 181 | 3.198 | 3.971 | 2.449 | 0.796 |
| 16 | 26-50 | 307 | 8.003 | 8.830 | 7.904 | 0.974 |
| 16 | 51+ | 158 | 3.756 | 4.852 | -0.137 | 0.506 |
| 18 | 0-10 | 153 | 1.141 | 1.422 | 0.268 | 0.569 |
| 18 | 11-25 | 183 | 1.237 | 1.623 | -0.380 | 0.448 |
| 18 | 26-50 | 310 | 3.067 | 4.083 | 1.722 | 0.710 |
| 18 | 51+ | 244 | 3.533 | 4.401 | -0.814 | 0.463 |
| 20 | 0-10 | 128 | 1.819 | 2.346 | 1.131 | 0.742 |
| 20 | 11-25 | 177 | 2.821 | 3.683 | 1.289 | 0.644 |
| 20 | 26-50 | 278 | 10.335 | 11.363 | 10.328 | 0.993 |
| 20 | 51+ | 186 | 5.849 | 7.009 | 4.535 | 0.812 |

## 16. Motor bazında görsel inceleme

Her grafikte sensörler aynı tahmin pencereleri üzerinden özetlenmiştir. Sağlık parametreleri CNN girdisi değildir. Koşul grafiğindeki z değerleri motor içinde hesaplanmıştır; motorlar arasında mutlak koşul karşılaştırması için kullanılmaz. Sensör panellerinin eksen ölçekleri farklıdır.

### Motor 2

Orta RUL’da fazla tahmin. Geç dönemde HPT değişimi hızlanırken hata azalıyor.

![Motor 2: Tahmin, hata, çalışma koşulları ve sağlık parametreleri](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_2_ozet.png)

![Motor 2: Fiziksel sensörlerin uçuş bazında değişimi](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_2_sensorler.png)

![Motor 2: Çalışma koşullarına göre beklenen değerden sapmalar](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_2_sapmalar.png)


### Motor 5

Yüksek RUL’da belirgin eksik tahmin. Orta ömürde tahminler gerçeğe yaklaşıyor.

![Motor 5: Tahmin, hata, çalışma koşulları ve sağlık parametreleri](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_5_ozet.png)

![Motor 5: Fiziksel sensörlerin uçuş bazında değişimi](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_5_sensorler.png)

![Motor 5: Çalışma koşullarına göre beklenen değerden sapmalar](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_5_sapmalar.png)


### Motor 10

Yüksek RUL’da eksik tahmin. Son ömür aralığında hata daha düşük.

![Motor 10: Tahmin, hata, çalışma koşulları ve sağlık parametreleri](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_10_ozet.png)

![Motor 10: Fiziksel sensörlerin uçuş bazında değişimi](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_10_sensorler.png)

![Motor 10: Çalışma koşullarına göre beklenen değerden sapmalar](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_10_sapmalar.png)


### Motor 16

Orta RUL’da fazla tahmin; HPT ve LPT parametrelerinde birlikte değişimler görülüyor.

![Motor 16: Tahmin, hata, çalışma koşulları ve sağlık parametreleri](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_16_ozet.png)

![Motor 16: Fiziksel sensörlerin uçuş bazında değişimi](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_16_sensorler.png)

![Motor 16: Çalışma koşullarına göre beklenen değerden sapmalar](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_16_sapmalar.png)


### Motor 18

İlk deneyde en düşük genel hata. Bu bölümdeki grafikler 50 epoch referansına aittir.

![Motor 18: Tahmin, hata, çalışma koşulları ve sağlık parametreleri](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_18_ozet.png)

![Motor 18: Fiziksel sensörlerin uçuş bazında değişimi](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_18_sensorler.png)

![Motor 18: Çalışma koşullarına göre beklenen değerden sapmalar](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_18_sapmalar.png)


### Motor 20

Orta RUL’da güçlü fazla tahmin; basınç ve devir sapmaları motor 2’den farklı davranıyor.

![Motor 20: Tahmin, hata, çalışma koşulları ve sağlık parametreleri](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_20_ozet.png)

![Motor 20: Fiziksel sensörlerin uçuş bazında değişimi](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_20_sensorler.png)

![Motor 20: Çalışma koşullarına göre beklenen değerden sapmalar](./CNN_Deney_ve_Analiz_Raporu/gorseller/motor_20_sapmalar.png)


## 17. İlk fiziksel grafiğin nasıl yorumlanması gerekiyor?

![İlk fiziksel inceleme](./CNN_Deney_ve_Analiz_Raporu/gorseller/ilk_fiziksel_inceleme.png)

**Başlıklardaki neden–sonuç ifadeleri doğrulanmış sonuç değildir.** Bu görsel ilk keşif aşamasını temsil eder. HPT parametresinin düşüşü görülüyor; ham Wf serisinde sürekli artış yok. “İtkiyi karşılamak için yakıt arttı” ve “fazla yakıt sıcaklığı artırdı” iddiaları yalnızca bu çizgilerden çıkarılamaz. Sunumda koşullara göre sensör sapması grafiklerine öncelik verilmeli. Bu ilk grafiğin hangi satırları özetlediği kodu görülmeden doğrulanmadığından, sonraki pencere eşleştirilmiş grafiklerle sayısal olarak aynı kabul edilmemelidir.

## 18. Fold 5: 50 ve 150 epoch deneyi

### Deney sorusu

Eğitim süresini artırmak motor 18 üzerindeki doğrulama başarısını iyileştiriyor mu, yoksa overfitting mi oluşuyor?

Aynı CNN, seed 42, öğrenme oranı 0,001 ve batch size 64 kullanıldı. Maksimum epoch ve patience 150 yapıldı. İlk 50 epoch'un eğitim/doğrulama hata değerleri önceki deneyle tam eşleşti; süreler karşılaştırmaya dahil edilmedi. Bu nedenle ilk 50 epoch sonrasındaki eğitim seyri doğrudan karşılaştırılabilir.

### Temel sonuç

| Ölçüm | 50 epoch koşusu: en iyi epoch 50 | 150 epoch koşusu: en iyi epoch 90 |
|---|---:|---:|
| Doğrulama MAE | 2,487 | 2,286 |
| Doğrulama RMSE | 3,465 | 3,149 |
| Sabit en iyi modelin eğitim RMSE'si | 7,232 | 7,060 |
| Toplam eğitim süresi | 166,7 sn | 568,0 sn |

MAE yaklaşık %8,1; RMSE yaklaşık %9,1 azaldı. Süre ortam yüküne bağlıdır; artış sadece epoch sayısına bağlanmamalıdır. Son 150. epoch'un doğrulama RMSE'si 3,876, MAE'si 2,884'tür: raporlanan en iyi model son epoch değildir.

### Overfitting oldu mu?

Bu koşuda belirgin ve kalıcı bir doğrulama kötüleşmesi görülmüyor. Eğitim hatası azalırken doğrulama hatasının sürekli yükselmesi şeklinde klasik bir ayrışma yok. Epoch bloklarının doğrulama RMSE medyanları:

| Epoch aralığı | Doğrulama RMSE medyanı |
|---|---:|
| 31–50 | 4,387 |
| 51–75 | 4,160 |
| 76–100 | 4,072 |
| 101–125 | 3,913 |
| 126–150 | 3,801 |

90. epoch'tan sonra yeni bir minimum elde edilmemesi tek başına overfitting kanıtı değildir. 51–150 arasında 12 epoch eski en iyi RMSE'yi geçti. Davranış, dalgalanan optimizasyon ve azalan ek kazançla uyumludur. “Overfitting kesinlikle yok” denemez; tek seed, tek doğrulama motoru ve aynı veriyle checkpoint seçimi söz konusudur.

### RUL aralıkları

| Gerçek RUL | Eski MAE | Yeni MAE | Yorum |
|---|---:|---:|---|
| 0–10 | 1,141 | 0,992 | İyileşti |
| 11–25 | 1,237 | 1,404 | Kötüleşti |
| 26–50 | 3,067 | 2,728 | İyileşti |
| 51+ | 3,533 | 3,196 | İyileşti |

11–25 aralığında yönlü hata −0,380'den −1,166'ya kaydı; eksik tahmin arttı. 26–50 aralığında fazla tahmin yanlılığı +1,722'den +1,209'a geriledi. Toplam skor iyileşmesi bütün ömür aralıklarında aynı düzeyde iyileşme anlamına gelmez.

### Grafik

![50 ve 150 epoch karşılaştırması](./CNN_Deney_ve_Analiz_Raporu/gorseller/fold5_50_vs_150.png)

Sol üst: bütün eğitim seyri. Sağ üst: 30. epoch sonrası doğrulama hatası ve o ana kadarki en iyi değer. Sol alt: eski ve yeni en iyi checkpoint'in uçuş başına ortalama tahmini. Sağ alt: pencere bazında RUL aralığı MAE karşılaştırması. Eğitim eğrisindeki değerler ağırlık güncellemeleri sırasında biriktirilir; sabit modelin son eğitim metriklerinden farklıdır.


## 19.Zamansal Duyarlılık (Temporal Probing) Analizi

1D-CNN modelinin zamanın yönünü ve fiziksel aşınma bağımlılıklarını ne ölçüde öğrendiğini test etmek amacıyla, doğrulama pencereleri üzerinde 3 farklı zamansal sabote/manipülasyon deneyi (*Permutation Test*) gerçekleştirilmiştir:

1.  **Reverse (Zamanı Tersine Çevirme):** 256 saniyelik pencere kronolojik sıra yerine, sondan başa doğru modele beslenmiştir.
2.  **Block Shuffle (Blok Karıştırma):** Pencere kendi içinde küçük zaman bloklarına bölünmüş ve blokların sırası rastgele karıştırılmıştır (lokal zaman sırası bozulmuştur).
3.  **Shuffle (Rastgele Kaos):** Zaman algısı tamamen yok edilerek, tüm saniyeler tamamen rastgele altüst edilmiştir.

Bu manipülasyonlar karşısında modelin gösterdiği RMSE duyarlılık çıktıları şu şekildedir:

```text
Fold 1: original reproduced
  - original (Orijinal Sıra)   : RMSE 6.012
  - reverse (Ters Kronoloji)    : RMSE 6.046
  - block_shuffle (Blok Kaos)   : RMSE 6.057
  - shuffle (Tam Kaos)          : RMSE 6.363

Fold 5: original reproduced
  - original (Orijinal Sıra)   : RMSE 3.465
  - reverse (Ters Kronoloji)    : RMSE 3.499
  - block_shuffle (Blok Kaos)   : RMSE 3.491
  - shuffle (Tam Kaos)          : RMSE 3.919
```

#### 📌 Zamansal Duyarlılık Sonuçlarının Analizi ve Değerlendirilmesi:
*   **Zaman Algısının İspatı:** Pencerelerin kronolojik yapısı tamamen yok edildiğinde (`shuffle`), modelin RMSE hatası tüm fold'larda (Örn: Fold 1'de `6.01`'den `6.36`'ya, Fold 5'te `3.46`'dan `3.91`'e) sert bir şekilde yükselmiştir. Bu durum, 1D-CNN modelinin sadece anlık sensör değerlerine bakmadığını, **zaman serisinin içindeki zamansal akışı ve fiziksel bozulma yönünü gerçekten öğrendiğini** kanıtlar.
*   **Gürültü Dayanıklılığı (Robustness):** Zaman tersine çevrildiğinde (`reverse`) veya lokal bloklar karıştırıldığında (`block_shuffle`), hata paylarındaki artışın son derece mikroskobik düzeyde kalması; modelin uçuş esnasındaki **anlık pilot hamlelerine, gürültülere veya anlık sinyal sıçramalarına karşı yüksek bir sönümleme ve kararlılık kapasitesine** sahip olduğunu, gürültüyü temizleyerek makroskobik aşınma trendine odaklanabildiğini göstermektedir.


### Sunumda söylenebilecek sonuç

“Eğitim bütçesini yalnızca fold 5'te 50'den 150 epoch'a çıkardık. İlk 50 epoch sonuçları birebir eşleşti. En iyi doğrulama RMSE'si 90. epoch'ta 3,465'ten 3,149'a düştü. Devam eden eğitimde kalıcı bir doğrulama kötüleşmesi gözlemedik; ancak kazanç sınırlı ve RUL aralıklarına göre farklıydı. Son epoch yerine en iyi doğrulama checkpoint'ini kullanmak önemliydi.”

### Kapsam ve sonraki adım

Bu deney geliştirme/doğrulama analizidir, bağımsız test sonucu değildir. Daha çok epoch arasından minimum seçmek doğrulama seçimi avantajı sağlar. İyileşmenin genellenmesi çoklu seed ve diğer motorlarda sınanmalıdır. Bu fold'un güncellenmiş skorunu eski altı-fold ortalamasına sessizce eklemeyin: başlangıç altı-fold tablosu aynı bütçeli referans olarak korunsun, bu deney ayrı raporlansın. 90 epoch bütün motorlar için optimum kabul edilmemelidir.

Bu belge ana CNN_RUL_Analiz_ve_Sunum_Notlari.md dosyasındaki “daha uzun eğitimin yararı henüz sınanmamıştır” ifadesini fold 5 için güncelleyen sunum ekidir. Kaynaklar: kullanıcının önceki Arşiv.zip içindeki fold_5 sonuçları ve yeni fold_5.zip içindeki history.csv, metrics.json, validation_predictions.csv.

### Eğitim bütçesi kararı

İyileşme gerçektir fakat mutlak kazanç sınırlıdır: MAE yaklaşık 0,20, RMSE yaklaşık 0,32 döngü azalmıştır. Eğitim süresi yaklaşık 3,4 katına çıkmıştır; eğitim CPU üzerindedir. Projenin mevcut aşamasında maksimum 50 epoch ve patience 8 referansı korunacaktır. Bu, 50 epoch’un evrensel optimum olduğunun ispatı değil, maliyet–kazanç tercihidir.

## 20. Henüz yapılmayan çalışmalar ve ekleme alanı

- [ ] Seed 7 ve 123 ile altı-fold tekrar: motor farkını başlangıç rastgeleliğinden ayırma.
- [ ] Ortak protokolde Random Forest / LSTM / TCN karşılaştırması.
- [ ] Koşullara göre sensör sapmalarını ek özellik olarak sınama.
- [ ] Tasarım kararları tamamlandıktan sonra resmî test değerlendirmesi.

Bu maddelerin sonuçları mevcut raporda yoktur. Yeni sonuçlar eklenirken deney adı, seed, fold, girdi listesi, eğitim bütçesi, model seçim yöntemi ve veri sızıntısı kontrolleri yazılmalıdır.
