import pandas as pd
import numpy as np

from preprocessing.data_loader import NCmapssDataLoader


def extract_window_features(X_window, feature_names):

    df = pd.DataFrame(
        X_window,
        columns=feature_names
    )

    # İstatistiksel özellikleri hesapla
    stats = df.agg(["mean", "std", "min", "max"])

    # Her sensörün istatistiklerini tek vektörde birleştir
    features = stats.T.stack()

    # Özellik isimlerini oluştur
    features.index = [
        f"{sensor}_{stat}"
        for sensor, stat in features.index
    ]

    return features



def build_feature_matrix(windows, feature_names):


    X_features = []  # Özellikleri
    y_values = []  # RUL değerleri

    # Veri dosyasını aç
    with NCmapssDataLoader() as loader:

        # Bütün pencereleri sırayla işle
        for i, window in enumerate(windows):

            # Pencerenin ölçümlerini ve RUL değerini yükle
            X_window, y_rul = loader.load_window(window)

            # Özellik çıkarımı
            features = extract_window_features(
                X_window,
                feature_names
            )

           
            X_features.append(features)
            y_values.append(y_rul)

            
            if (i + 1) % 500 == 0:
                print(f"İşlenen pencere: {i + 1}/{len(windows)}")

    # Özellik matrisini oluştur
    X = pd.DataFrame(X_features).reset_index(drop=True)

    # RUL vektörünü oluştur
    y = np.asarray(y_values)

    return X, y



    