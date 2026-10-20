import csv
import math
import h5py
import numpy as np
import json

from .config import DATA_PATH, OUTPUT_DIR, WINDOW_SIZE
from pathlib import Path

WINDOW_METADATA_PATH = OUTPUT_DIR / "window_metadata.csv"
SPLIT_FOLDS_PATH = OUTPUT_DIR / "split_folds.json"

def validate_output_files() -> None:
    required_files: tuple[Path, ...] = (
        WINDOW_METADATA_PATH,
        SPLIT_FOLDS_PATH,
    )

    for file_path in required_files:
        if not file_path.exists():
            raise FileNotFoundError(
                f"Output file not found: {file_path}"
            )

        if file_path.stat().st_size == 0:
            raise ValueError(
                f"Output file is empty: {file_path}"
            )

        print(f"Valid output file: {file_path.name}")
        
def validate_window_metadata() -> None:
    required_columns = {
        "window_id",
        "unit",
        "cycle",
        "rul",
        "start_row",
        "end_row",
    }

    with WINDOW_METADATA_PATH.open(
        mode="r",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        if reader.fieldnames is None:
            raise ValueError("Metadata has no header.")

        missing_columns = required_columns - set(reader.fieldnames)

        if missing_columns:
            raise ValueError(
                f"Missing metadata columns: {sorted(missing_columns)}"
            )

        rows = list(reader)

    if not rows:
        raise ValueError("Metadata contains no windows.")

    window_ids: list[int] = []
    window_ranges: set[tuple[int, int]] = set()

    for row in rows:
        window_id = int(row["window_id"])
        start_row = int(row["start_row"])
        end_row = int(row["end_row"])
        rul = float(row["rul"])

        if end_row - start_row != WINDOW_SIZE:
            raise ValueError(
                f"Window {window_id} does not contain "
                f"{WINDOW_SIZE} rows."
            )

        if start_row < 0 or end_row <= start_row:
            raise ValueError(
                f"Window {window_id} has invalid row boundaries."
            )

        if not math.isfinite(rul):
            raise ValueError(
                f"Window {window_id} has an invalid RUL."
            )

        window_range = (start_row, end_row)

        if window_range in window_ranges:
            raise ValueError(
                f"Duplicate window range: {window_range}"
            )

        window_ids.append(window_id)
        window_ranges.add(window_range)

    expected_ids = list(range(len(rows)))

    if window_ids != expected_ids:
        raise ValueError(
            "Window IDs are not unique and sequential."
        )

    print("\nWindow metadata validation passed.")
    print(f"Windows checked: {len(rows):,}")
    
def validate_windows_against_hdf5() -> None:
    with WINDOW_METADATA_PATH.open(
        mode="r",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        rows = list(csv.DictReader(csv_file))

    with h5py.File(DATA_PATH, mode="r") as h5_file:
        total_rows = h5_file["A_dev"].shape[0]

        for row in rows:
            window_id = int(row["window_id"])
            expected_unit = int(row["unit"])
            expected_cycle = int(row["cycle"])
            expected_rul = float(row["rul"])
            start_row = int(row["start_row"])
            end_row = int(row["end_row"])

            if end_row > total_rows:
                raise ValueError(
                    f"Window {window_id} exceeds HDF5 boundaries."
                )

            identifiers = h5_file["A_dev"][
                start_row:end_row,
                :2,
            ]

            rul_values = h5_file["Y_dev"][
                start_row:end_row,
                0,
            ]

            if not np.all(identifiers[:, 0] == expected_unit):
                raise ValueError(
                    f"Window {window_id} contains multiple units."
                )

            if not np.all(identifiers[:, 1] == expected_cycle):
                raise ValueError(
                    f"Window {window_id} contains multiple cycles."
                )

            if not np.all(rul_values == expected_rul):
                raise ValueError(
                    f"Window {window_id} has inconsistent RUL values."
                )

    print("\nHDF5 window validation passed.")
    print(f"Windows compared with HDF5: {len(rows):,}")
    
def validate_split_folds() -> None:
    """Train, validation ve test motor ayrımlarını doğrular."""
    with WINDOW_METADATA_PATH.open(
        mode="r",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        metadata_rows = list(csv.DictReader(csv_file))

    metadata_units = {
        int(row["unit"])
        for row in metadata_rows
    }

    with SPLIT_FOLDS_PATH.open(
        mode="r",
        encoding="utf-8",
    ) as json_file:
        split_config = json.load(json_file)

    dev_units = set(split_config["dev_units"])
    test_units = set(split_config["official_test_units"])
    folds = split_config["folds"]

    if dev_units != metadata_units:
        raise ValueError(
            "Split dev units do not match metadata units."
        )

    if dev_units & test_units:
        raise ValueError(
            "Test units overlap with development units."
        )

    validation_units_seen: list[int] = []

    for fold in folds:
        train_units = set(fold["train_units"])
        validation_units = set(fold["validation_units"])

        if train_units & validation_units:
            raise ValueError(
                f"Fold {fold['fold']} has train-validation overlap."
            )

        if train_units | validation_units != dev_units:
            raise ValueError(
                f"Fold {fold['fold']} does not contain all dev units."
            )

        if len(validation_units) != 1:
            raise ValueError(
                f"Fold {fold['fold']} must have one validation unit."
            )

        validation_units_seen.extend(validation_units)

    if sorted(validation_units_seen) != sorted(dev_units):
        raise ValueError(
            "Each dev unit must be validation exactly once."
        )

    print("\nSplit fold validation passed.")
    print(f"Folds checked: {len(folds)}")
    print(f"Development units: {sorted(dev_units)}")
    print(f"Official test units: {sorted(test_units)}")
    
if __name__ == "__main__":
    validate_output_files()
    validate_window_metadata()
    validate_windows_against_hdf5()
    validate_split_folds()