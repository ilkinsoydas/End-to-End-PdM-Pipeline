import numpy as np

from preprocessing.data_loader import NCmapssDataLoader


def build_sequences(windows):

    X_sequences = []
    y_values = []

    with NCmapssDataLoader() as loader:

        for i, window in enumerate(windows):

            X_window, y_rul = loader.load_window(window)

            X_sequences.append(X_window)
            y_values.append(y_rul)

            if (i + 1) % 500 == 0:
                print(
                    f"İşlenen pencere: {i + 1}/{len(windows)}"
                )

    X = np.asarray(X_sequences, dtype=np.float32)
    y = np.asarray(y_values, dtype=np.float32)

    return X, y