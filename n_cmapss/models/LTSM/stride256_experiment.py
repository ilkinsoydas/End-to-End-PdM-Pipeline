from pathlib import Path
import gc

import h5py
import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.preprocessing import StandardScaler
from tensorflow.keras.callbacks import EarlyStopping

from lstm_architectures import build_vanilla_lstm


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "N-CMAPSS_DS02-006.h5"
OUTPUT_DIR = PROJECT_ROOT / "processed" / "experiments"
OUTPUT_CSV = OUTPUT_DIR / "vanilla_stride256_seed42.csv"

WINDOW_SIZE = 256
STRIDE = 256
SEED = 42
UNITS = 32
DROPOUT = 0.2
LEARNING_RATE = 0.001
BATCH_SIZE = 64
EPOCHS = 50
DEV_UNITS = [2, 5, 10, 16, 18, 20]


def discover_windows() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with h5py.File(DATA_PATH, mode="r") as h5_file:
        identifiers = h5_file["A_dev"][:, :2].astype(np.int32)
        features = np.concatenate(
            [h5_file["W_dev"][:], h5_file["X_s_dev"][:]],
            axis=1,
        ).astype(np.float32)
        rul = h5_file["Y_dev"][:, 0].astype(np.float32)

    units = identifiers[:, 0]
    cycles = identifiers[:, 1]
    changed = (units[1:] != units[:-1]) | (cycles[1:] != cycles[:-1])
    starts = np.concatenate(([0], np.flatnonzero(changed) + 1))
    ends = np.concatenate((starts[1:], [len(units)]))

    sequences = []
    targets = []
    window_units = []

    for start, end in zip(starts, ends):
        last_start = end - WINDOW_SIZE
        if last_start < start:
            continue

        for window_start in range(start, last_start + 1, STRIDE):
            sequences.append(features[window_start:window_start + WINDOW_SIZE])
            targets.append(rul[window_start])
            window_units.append(int(units[window_start]))

    return (
        np.asarray(sequences, dtype=np.float32),
        np.asarray(targets, dtype=np.float32),
        np.asarray(window_units, dtype=np.int32),
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    X, y, window_units = discover_windows()

    print(f"Stride 256 windows: {len(X):,}")
    print(f"X shape: {X.shape}")

    results = []

    for validation_motor in DEV_UNITS:
        train_units = [unit for unit in DEV_UNITS if unit != validation_motor]
        train_mask = np.isin(window_units, train_units)
        val_mask = window_units == validation_motor

        X_train = X[train_mask]
        X_val = X[val_mask]
        y_train = y[train_mask]
        y_val = y[val_mask]

        feature_scaler = StandardScaler()
        n_features = X_train.shape[2]

        X_train_scaled = feature_scaler.fit_transform(
            X_train.reshape(-1, n_features)
        ).reshape(X_train.shape).astype("float32")

        X_val_scaled = feature_scaler.transform(
            X_val.reshape(-1, n_features)
        ).reshape(X_val.shape).astype("float32")

        y_mean = float(y_train.mean())
        y_std = float(y_train.std())
        y_train_scaled = ((y_train - y_mean) / y_std).astype("float32")
        y_val_scaled = ((y_val - y_mean) / y_std).astype("float32")

        tf.keras.backend.clear_session()
        tf.keras.utils.set_random_seed(SEED)

        model = build_vanilla_lstm(
            units=UNITS,
            dropout=DROPOUT,
            window_size=WINDOW_SIZE,
            n_features=n_features,
        )
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
            loss="mse",
            metrics=["mae"],
        )

        history = model.fit(
            X_train_scaled,
            y_train_scaled,
            validation_data=(X_val_scaled, y_val_scaled),
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            callbacks=[
                EarlyStopping(
                    monitor="val_loss",
                    patience=5,
                    restore_best_weights=True,
                )
            ],
            verbose=0,
        )

        pred_scaled = model.predict(X_val_scaled, verbose=0).ravel()
        pred = pred_scaled * y_std + y_mean

        mae = float(np.mean(np.abs(y_val - pred)))
        rmse = float(np.sqrt(np.mean((y_val - pred) ** 2)))
        best_epoch = int(np.argmin(history.history["val_loss"])) + 1

        results.append({
            "window_size": WINDOW_SIZE,
            "stride": STRIDE,
            "seed": SEED,
            "units": UNITS,
            "dropout": DROPOUT,
            "learning_rate": LEARNING_RATE,
            "batch_size": BATCH_SIZE,
            "epochs": EPOCHS,
            "fold": DEV_UNITS.index(validation_motor) + 1,
            "validation_motor": validation_motor,
            "train_windows": len(X_train),
            "validation_windows": len(X_val),
            "train_rul_mean": y_mean,
            "train_rul_std": y_std,
            "best_epoch": best_epoch,
            "val_mae": mae,
            "val_rmse": rmse,
        })

        pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
        print(f"Motor {validation_motor}: MAE={mae:.3f}, RMSE={rmse:.3f}")

        del model, history, pred_scaled, pred
        gc.collect()

    results_df = pd.DataFrame(results)
    print("\nStride 256 sonuç özeti")
    print(results_df[["validation_motor", "val_mae", "val_rmse", "best_epoch"]].round(3).to_string(index=False))
    print("\nOrtalama MAE:", round(results_df["val_mae"].mean(), 3))
    print("Ortalama RMSE:", round(results_df["val_rmse"].mean(), 3))
    print(f"Sonuç dosyası: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
