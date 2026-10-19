import h5py

from .config import (
    DATA_PATH,
    INPUT_DATASETS,
    OUTPUT_DIR,
    REQUIRED_DATASETS,
    STRIDE,
    WINDOW_SIZE,
)


def validate_paths() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def decode_column_names(h5_file: h5py.File, dataset_name: str) -> list[str]:
    return [value.decode("utf-8") for value in h5_file[dataset_name][:]]


def inspect_dataset() -> None:
    with h5py.File(DATA_PATH, mode="r") as h5_file:
        print(f"Data path: {DATA_PATH}")
        print("\nHDF5 sections:")

        for dataset_name in sorted(h5_file.keys()):
            dataset = h5_file[dataset_name]
            print(f" {dataset_name}: {dataset.shape}")

        a_columns = decode_column_names(h5_file, "A_var")
        w_columns = decode_column_names(h5_file, "W_var")
        sensor_columns = decode_column_names(h5_file, "X_s_var")
        feature_columns = w_columns + sensor_columns

        print(f"\nIdentifier columns ({len(a_columns)}): {a_columns}")
        print(f"Operating conditions ({len(w_columns)}): {w_columns}")
        print(f"Physical sensors ({len(sensor_columns)}): {sensor_columns}")
        print(f"Model features ({len(feature_columns)}): {feature_columns}")


def validate_dataset_structure() -> None:
    with h5py.File(DATA_PATH, mode="r") as h5_file:
        missing_datasets = [
            name for name in REQUIRED_DATASETS if name not in h5_file
        ]

        if missing_datasets:
            raise KeyError(f"Missing HDF5 sections: {missing_datasets}")

        row_counts = {
            name: h5_file[name].shape[0] for name in REQUIRED_DATASETS
        }

        if len(set(row_counts.values())) != 1:
            raise ValueError(
                f"The tables do not have the same number of rows: {row_counts}"
            )

        feature_count = sum(
            h5_file[name].shape[1] for name in INPUT_DATASETS
        )

        if feature_count != 18:
            raise ValueError(
                "The expected number of features is 18; "
                f"the number found is: {feature_count}"
            )

        if h5_file["Y_dev"].shape[1] != 1:
            raise ValueError("Y_dev yalnızca bir RUL sütunu içermeli.")

        print("\nDataset structure validation passed.")
        print(f"Development rows: {row_counts['A_dev']:,}")
        print(f"Input features: {feature_count}")
        print(f"Window size: {WINDOW_SIZE}")
        print(f"Stride: {STRIDE}")
