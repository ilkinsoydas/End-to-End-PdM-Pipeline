from pathlib import Path


N_CMAPSS_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = N_CMAPSS_DIR / "data" / "N-CMAPSS_DS02-006.h5"
OUTPUT_DIR = N_CMAPSS_DIR / "processed"

WINDOW_SIZE = 256
STRIDE = 1024

INPUT_DATASETS = ("W_dev", "X_s_dev")
REQUIRED_DATASETS = ("A_dev", "W_dev", "X_s_dev", "Y_dev")
