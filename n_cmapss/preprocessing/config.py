from pathlib import Path


N_CMAPSS_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = N_CMAPSS_DIR / "data" / "N-CMAPSS_DS02-006.h5"

WINDOW_SIZE = 256
STRIDE = 256

OUTPUT_DIR = (
    N_CMAPSS_DIR
    / "processed"
    / f"window_{WINDOW_SIZE}_stride_{STRIDE}"
)

INPUT_DATASETS = ("W_dev", "X_s_dev")
REQUIRED_DATASETS = ("A_dev", "W_dev", "X_s_dev", "Y_dev")

FEATURE_NAME_DATASETS = ("W_var", "X_s_var")
