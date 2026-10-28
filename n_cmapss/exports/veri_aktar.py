import json
from pathlib import Path

from export_dataset import export

# =========================================================
# ==========================================================
# KULLANILABİLİR SÜTUNLAR — TOPLAM 47
# Sütun isimlerinde büyük/küçük harf önemlidir.
# ==========================================================

# A — Kimlik ve yardımcı bilgiler (4)
KIMLIK_BILGILERI = [
    "unit",   # Motor numarası
    "cycle",  # Uçuş/döngü numarası
    "Fc",     # Uçuş sınıfı
    "hs",     # Sağlık durumu etiketi
]

# W — Çalışma koşulları (4)
CALISMA_KOSULLARI = [
    "alt",
    "Mach",
    "TRA",
    "T2",
]

# X_s — Fiziksel sensör kanalları (14)
FIZIKSEL_SENSORLER = [
    "T24",
    "T30",
    "T48",
    "T50",
    "P15",
    "P2",
    "P21",
    "P24",
    "Ps30",
    "P40",
    "P50",
    "Nf",
    "Nc",
    "Wf",
]

# X_v — Sanal sensör kanalları (14)
SANAL_SENSORLER = [
    "T40",
    "P30",
    "P45",
    "W21",
    "W22",
    "W25",
    "W31",
    "W32",
    "W48",
    "W50",
    "SmFan",
    "SmLPC",
    "SmHPC",
    "phi",
]

# T — Simülasyon iç sağlık/bozulma parametreleri (10)
# Bunlar sıcaklık sensörleri değildir.
SAGLIK_PARAMETRELERI = [
    "fan_eff_mod",
    "fan_flow_mod",
    "LPC_eff_mod",
    "LPC_flow_mod",
    "HPC_eff_mod",
    "HPC_flow_mod",
    "HPT_eff_mod",
    "HPT_flow_mod",
    "LPT_eff_mod",
    "LPT_flow_mod",
]

# Y — Tahmin hedefi (1)
HEDEF = ["RUL"]

TUM_SUTUNLAR = (
    KIMLIK_BILGILERI
    + CALISMA_KOSULLARI
    + FIZIKSEL_SENSORLER
    + SANAL_SENSORLER
    + SAGLIK_PARAMETRELERI
    + HEDEF
)

# Mevcut CNN deneylerinde kullanılan 18 girdi:
MEVCUT_18_GIRDI = CALISMA_KOSULLARI + FIZIKSEL_SENSORLER


# ==========================================================
# FİLTRE OPERATÖRLERİ
# Her sütunda kullanılabilir. Koşullar VE mantığıyla birleşir.
# ==========================================================

# "ge": büyük veya eşit     Örnek: {"ge": 20}
# "gt": büyük               Örnek: {"gt": 20}
# "le": küçük veya eşit     Örnek: {"le": 50}
# "lt": küçük               Örnek: {"lt": 50}
# "eq": eşit                Örnek: {"eq": 1}
# "ne": eşit değil          Örnek: {"ne": 0}
# "in": listedekilerden biri Örnek: {"in": [1, 2, 3]}

# ÖRNEKLER — bunlar yorumdur, kendiliğinden uygulanmaz:
#
# "filters": {}                              # Filtre yok
#
# "filters": {
#     "RUL": {"ge": 10, "le": 50},            # 10 <= RUL <= 50
#     "Mach": {"ge": 0.6},                   # Mach >= 0.6
#     "alt": {"ge": 20000, "lt": 35000},      # İrtifa aralığı
#     "hs": {"eq": 0},                       # hs etiketi 0
#     "Fc": {"in": [1, 2]},                  # Seçilen uçuş sınıfları
#     "HPT_eff_mod": {"lt": 0},              # Negatif değerler
# }
#
# Filtrelenen sütunun "columns" listesinde olması gerekmez.


# ==========================================================
# MOTOR VE PENCERELEME REFERANSI
# ==========================================================

DEV_MOTORLARI = [2, 5, 10, 16, 18, 20]
TEST_MOTORLARI = [11, 14, 15]

# "units": [2, 5]           # Seçilen motorlar
# "cycles": [1, 2, 3]       # Seçilen uçuşlar
# Tümünü almak için ilgili ayarı AYARLAR'dan kaldır.
#
# "window": None           # Pencereleme yok
# "window": {
#     "size": 256,         # Pencere başına örnek sayısı
#     "stride": 128,       # Başlangıçlar arası örnek sayısı
#     "target": "last",    # "last": son satır RUL
# }                       # "mean": pencerenin ortalama RUL'u
#
# stride < size  → örtüşen pencereler
# stride = size  → bitişik pencereler
# stride > size  → aralarında kullanılmayan kayıtlar bulunur


# ÖRNEK
"""
# Bütün 47 sütun:
"columns": TUM_SUTUNLAR,

# Veya kimlikler + fiziksel sensörler + RUL:
"columns": KIMLIK_BILGILERI + FIZIKSEL_SENSORLER + HEDEF,

# Veya mevcut 18 girdi + RUL:
"columns": MEVCUT_18_GIRDI + HEDEF,

# Veya yalnızca elle seçtiklerin:
"columns": ["unit", "cycle", "T48", "T50", "HPT_eff_mod", "RUL"],
"""


# ==========================================================
# SEÇİMLERİNİ BU BÖLÜMDEN DEĞİŞTİR
# ==========================================================

AYARLAR = {
    "name": "motor2_ornek",

    "data_path": "n_cmapss/data/N-CMAPSS_DS02-006.h5",
    "output_root": "n_cmapss/exports",
    "partition": "dev",

    # CSV'de görmek istediğin sütunlar ve sıraları:
     "columns": [
    "alt",
    "Mach",
    "TRA",
    "T2",
    "T24",
    "T30",
    "T48",
    "T50",
    "P15",
    "P2",
    "P21",
    "P24",
    "Ps30",
    "P40",
    "P50",
    "Nf",
    "Nc",
    "Wf"
  ],

    # Tüm motorlar için units satırını kaldır
    "units": [2],

    # Tüm uçuşlar için cycles satırını kaldır
    "cycles": [1, 2],

    # Filtre yoksa {} bırak.
    "filters": {},

    # Pencereleme istemiyorsan None yaz.
    "window": {
        "size": 256,
        "stride": 128,
        "target": "last",
    },

    # İstediğin çıktıları True yap.
    "exports": {
        "raw": True,
        "window_values": True,
        "statistics": True,
        "sequences": False,
    },

    # Dosyayı parça parça okumak için:
    "chunk_rows": 100_000,
}


# ==========================================================
# RUN
# ==========================================================
def proje_kokunu_bul():
    for aday in Path(__file__).resolve().parents:
        if (aday / "n_cmapss" / "data").is_dir():
            return aday

    raise FileNotFoundError(
        "Proje kökü bulunamadı: üst dizinlerde n_cmapss/data aranıyor."
    )

def main():
    proje_koku = proje_kokunu_bul()
    export(AYARLAR, base=proje_koku)


if __name__ == "__main__":
    main()