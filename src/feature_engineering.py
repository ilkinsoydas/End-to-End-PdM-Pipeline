import pandas as pd
import numpy as np

def add_rolling_features(df, window_size = 15):

    sensor_cols = [col for col in df.columns if col.startswith("s_")]
    df_engineered = df.copy()

    grouped = df_engineered.groupby("unit_nr")

    for col in sensor_cols:
        df_engineered[f"{col}_mean_{window_size}"] = grouped[col].transform(
            lambda x: x.rolling(window = window_size, min_periods = 1).mean()
        )

        df_engineered[f"{col}_std_{window_size}"] = grouped[col].transform(
            lambda x: x.rolling(window = window_size, min_periods = 1).std().fillna(0)
        )

    return df_engineered

def add_classification_labels(df, w0 = 30):

    df_engineered = df.copy()
    df_engineered["label_1"] = np.where(df_engineered["RUL"] <= w0, 1, 0)
    
    return df_engineered


