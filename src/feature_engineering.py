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
    if "RUL" in df_engineered.columns:
        df_engineered["label_1"] = np.where(df_engineered["RUL"] <= w0, 1, 0)
    
    return df_engineered

def select_features(df, target_col = "RUL", threshold = 0.30):

    df_engineered = df.copy()

    correlations = df_engineered.corr(method = "pearson")[target_col].abs()
    cols_to_keep = correlations[correlations >= threshold].index.tolist()

    feature_cols = [col for col in cols_to_keep if col not in ["unit_nr", "time_cycles", "RUL", "label_1"]]
    
    final_order = ["unit_nr", "time_cycles"] + feature_cols + ["RUL", "label_1"]
    
    final_order = [col for col in final_order if col in df_engineered.columns]
    
    return df_engineered[final_order]

if __name__ == "__main__":

    train_df = pd.read_csv("dataset/train_processed.csv")
    test_df = pd.read_csv("dataset/test_processed.csv")

    train_eng = add_rolling_features(train_df, window_size=15)
    test_eng = add_rolling_features(test_df, window_size=15)

    train_eng = add_classification_labels(train_eng, w0 = 30)
    test_eng = add_classification_labels(test_eng, w0=30)

    train_final = select_features(train_eng, target_col = "RUL", threshold=0.30)

    final_columns = train_final.columns.tolist()

    test_columns = [col for col in final_columns if col in test_eng.columns]
    test_final = test_eng[test_columns]

    train_final.to_csv("dataset/train_engineered.csv", index=False)
    test_final.to_csv("dataset/test_engineered.csv", index=False)

    print(f"Feature engineering completed. Train size: {train_final.shape}, Test size: {test_final.shape}")

    deleted = set(train_eng.columns) - set(train_final.columns)
    print(f"Deleted features: {deleted}")

