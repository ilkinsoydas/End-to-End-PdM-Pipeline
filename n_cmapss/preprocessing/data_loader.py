import csv
from types import TracebackType
import h5py
import numpy as np
import json

from .config import (
    DATA_PATH,
    INPUT_DATASETS,
    OUTPUT_DIR,
    WINDOW_SIZE,
    FEATURE_NAME_DATASETS,
)
from .create_windows import WindowRecord
from collections.abc import Iterable, Iterator, Sequence


WINDOW_METADATA_PATH = OUTPUT_DIR / "window_metadata.csv"
SPLIT_FOLDS_PATH = OUTPUT_DIR / "split_folds.json"


def load_window_metadata() -> list[WindowRecord]:
    with WINDOW_METADATA_PATH.open(
        mode="r",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        windows = [
            WindowRecord(
                window_id=int(row["window_id"]),
                unit=int(row["unit"]),
                cycle=int(row["cycle"]),
                rul=float(row["rul"]),
                start_row=int(row["start_row"]),
                end_row=int(row["end_row"]),
            )
            for row in reader
        ]

    return windows

def split_windows_by_fold(
    windows: list[WindowRecord],
    fold_number: int,
) -> tuple[list[WindowRecord], list[WindowRecord]]:
    with SPLIT_FOLDS_PATH.open(
        mode="r",
        encoding="utf-8",
    ) as json_file:
        split_config = json.load(json_file)

    selected_fold = next(
        (
            fold
            for fold in split_config["folds"]
            if fold["fold"] == fold_number
        ),
        None,
    )

    if selected_fold is None:
        raise ValueError(
            f"Fold {fold_number} does not exist."
        )

    train_units = set(selected_fold["train_units"])
    validation_units = set(
        selected_fold["validation_units"]
    )

    train_windows = [
        window
        for window in windows
        if window.unit in train_units
    ]

    validation_windows = [
        window
        for window in windows
        if window.unit in validation_units
    ]

    return train_windows, validation_windows

class NCmapssDataLoader:
    
    def __init__(self) -> None:
        self._h5_file: h5py.File | None = None

    def __enter__(self) -> "NCmapssDataLoader":
        self._h5_file = h5py.File(DATA_PATH, mode="r")
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._h5_file is not None:
            self._h5_file.close()
            self._h5_file = None

    def _require_open_file(self) -> h5py.File:
        if self._h5_file is None:
            raise RuntimeError(
                "Data loader must be used inside a with block."
            )

        return self._h5_file
    
    
    def load_window(
        self,
        window: WindowRecord,
    ) -> tuple[np.ndarray, np.float32]:
        h5_file = self._require_open_file()

        feature_parts = [
            h5_file[dataset_name][
                window.start_row:window.end_row
            ]
            for dataset_name in INPUT_DATASETS
        ]

        features = np.concatenate(
            feature_parts,
            axis=1,
        ).astype(np.float32)

        expected_shape = (WINDOW_SIZE, 18)

        if features.shape != expected_shape:
            raise ValueError(
                f"Window {window.window_id} shape is "
                f"{features.shape}, expected {expected_shape}."
            )

        target = np.float32(window.rul)

        return features, target
    
    def iter_windows(
        self,
        windows: Iterable[WindowRecord],
    ) -> Iterator[
        tuple[WindowRecord, np.ndarray, np.float32]
    ]:
        
        for window in windows:
            features, target = self.load_window(window)

            yield window, features, target
            
    def iter_batches(
        self,
        windows: Sequence[WindowRecord],
        batch_size: int = 64,
    ) -> Iterator[
        tuple[np.ndarray, np.ndarray, list[WindowRecord]]
    ]:
        
        if batch_size <= 0:
            raise ValueError("Batch size must be positive.")

        for start_index in range(
            0,
            len(windows),
            batch_size,
        ):
            batch_windows = list(
                windows[start_index:start_index + batch_size]
            )

            loaded_windows = [
                self.load_window(window)
                for window in batch_windows
            ]

            batch_features = np.stack(
                [features for features, _ in loaded_windows]
            )

            batch_targets = np.asarray(
                [target for _, target in loaded_windows],
                dtype=np.float32,
            )

            yield (
                batch_features,
                batch_targets,
                batch_windows,
            )
            
def load_feature_names() -> list[str]:
    with h5py.File(DATA_PATH, mode="r") as h5_file:
        feature_names = [
            value.decode("utf-8")
            for dataset_name in FEATURE_NAME_DATASETS
            for value in h5_file[dataset_name][:]
        ]

    if len(feature_names) != 18:
        raise ValueError(
            f"Expected 18 feature names, found {len(feature_names)}."
        )

    return feature_names
    
    