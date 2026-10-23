import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

h5_path = '/Users/melihsiskular/PycharmProjects/End-to-End-PdM-Pipeline/n_cmapss/data/N-CMAPSS_DS02-006.h5'

print("--- Veriler okunuyor ve yakıt parametresi ekleniyor ---")
with h5py.File(h5_path, 'r') as f:
    units = f['A_dev'][:, 0]
    unit2_mask = (units == 2.0)

    xs_names = [x.decode('utf-8') for x in f['X_s_var'][:]]
    t_names = [x.decode('utf-8') for x in f['T_var'][:]]

    # İlgili tüm sensörlerin indeksleri
    wf_idx = xs_names.index('Wf')  # Yakıt Akışı (Fuel Flow)
    t48_idx = xs_names.index('T48')  # Sıcaklık 48
    t50_idx = xs_names.index('T50')  # Sıcaklık 50
    hpt_idx = t_names.index('HPT_eff_mod')
    lpt_idx = t_names.index('LPT_eff_mod')

    cycles = f['A_dev'][unit2_mask, 1]

    # Verileri hafızaya al
    Wf_data = f['X_s_dev'][unit2_mask, wf_idx]
    T48_data = f['X_s_dev'][unit2_mask, t48_idx]
    T50_data = f['X_s_dev'][unit2_mask, t50_idx]
    HPT_data = f['T_dev'][unit2_mask, hpt_idx]
    LPT_data = f['T_dev'][unit2_mask, lpt_idx]

# Döngü bazında ortalama alarak sadeleştirme
raw_df = pd.DataFrame({
    'cycle': cycles,
    'Wf': Wf_data,
    'T48': T48_data,
    'T50': T50_data,
    'HPT_eff_mod': HPT_data,
    'LPT_eff_mod': LPT_data
})
df_plot = raw_df.groupby('cycle').mean().reset_index()

# --- 3 KATMANLI GRAFİK ÇIZIMI ---
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(11, 10), sharex=True)

# 1. Katman: Gizli Arıza (T Matrisi)
ax1.plot(df_plot['cycle'], df_plot['HPT_eff_mod'], label='HPT Verimlilik Sapması (HPT_eff_mod)', color='#d9534f',
         linewidth=2.5)
ax1.plot(df_plot['cycle'], df_plot['LPT_eff_mod'], label='LPT Verimlilik Sapması (LPT_eff_mod)', color='#f0ad4e',
         linewidth=2.5, linestyle='--')
ax1.axhline(0, color='black', linestyle=':', alpha=0.5)
ax1.set_title("1. Adım: Motor İçi Gizli Sağlık Parametrelerinin Çöküşü (T Matrisi)", fontsize=12, fontweight='bold')
ax1.set_ylabel("Verim Sapması", fontsize=10)
ax1.legend(loc='upper right', frameon=True, facecolor='white')
ax1.grid(True, alpha=0.3)

# 2. Katman: SİSTEMİN REAKSİYONU (YAKIT ARTIŞI) - YENİ EKLENEN KISIM
ax2.plot(df_plot['cycle'], df_plot['Wf'], label='Yakıt Akış Miktarı (Wf)', color='#5cb85c', linewidth=2.5)
ax2.set_title("2. Adım: Düşen İtkiyi Karşılamak İçin Yakıt Akışının Artırılması (Wf)", fontsize=12, fontweight='bold')
ax2.set_ylabel("Yakıt Akışı (pps)", fontsize=10)
ax2.legend(loc='upper left', frameon=True, facecolor='white')
ax2.grid(True, alpha=0.3)

# 3. Katman: Fiziksel Çıktı (Sıcaklık Tırmanışı)
ax3.plot(df_plot['cycle'], df_plot['T48'], label='HPT Çıkış Sıcaklığı (T48)', color='#0275d8', linewidth=2.5)
ax3.plot(df_plot['cycle'], df_plot['T50'], label='LPT Çıkış Sıcaklığı (T50)', color='#5bc0de', linewidth=2.5,
         linestyle='-.')
ax3.set_title("3. Adım: Fazla Yakıt Sonucu Egzoz Sıcaklıklarının Tırmanması (X_s Matrisi)", fontsize=12,
              fontweight='bold')
ax3.set_xlabel("Uçuş Döngüsü (Flight Cycle)", fontsize=11, fontweight='bold')
ax3.set_ylabel("Toplam Sıcaklık (°R)", fontsize=10)
ax3.legend(loc='upper left', frameon=True, facecolor='white')
ax3.grid(True, alpha=0.3)

# Arıza dikey çizgisi
max_cycle = df_plot['cycle'].max()
for ax in [ax1, ax2, ax3]:
    ax.axvline(max_cycle, color='red', linestyle='--', alpha=0.7, linewidth=1.5)

plt.tight_layout()
plt.savefig('/Users/melihsiskular/PycharmProjects/End-to-End-PdM-Pipeline/n_cmapss/outputs/cnn_fold1_20261023_001946/analysis/yakit_ve_turbin_asınma_kaniti.png', dpi=300)
plt.show()
print("[BAŞARILI] 3 katmanlı grafik kaydedildi.")

