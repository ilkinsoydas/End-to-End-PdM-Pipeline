import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

index_names = ["unit_nr", "time_cycles"]
setting_names = ['setting_1', 'setting_2', 'setting_3']
sensor_names = [f"s_{i}" for i in range(1, 22)]
col_names = index_names + setting_names + sensor_names

def load_data(file_path):

    df = pd.read_csv(file_path, header = None, sep = r"\s+", names = col_names)
    return df

def add_rul(df, clip_threshold = 125):
    max_cycles = df.groupby("unit_nr")["time_cycles"].transform("max")
    df["RUL"] = max_cycles - df["time_cycles"]

    if clip_threshold is not None:
        df["RUL"] = df["RUL"].clip(upper = clip_threshold)

    return df

def preprocess_data(df_train, df_test):
    drop_columns = ["setting_3", "s_1", "s_5", "s_10", "s_16", "s_18", "s_19"]
    df_train = df_train.drop(columns = drop_columns)
    df_test = df_test.drop(columns = drop_columns)

    features = [col for col in df_train.columns if col not in index_names]
    scaler = MinMaxScaler()
    df_train[features] = scaler.fit_transform(df_train[features])
    df_test[features] = scaler.transform(df_test[features])

    df_train = add_rul(df_train, clip_threshold=125)
    return df_train, df_test

if __name__ == "__main__":
    print("Datas loading...")
    train_raw = load_data("dataset/train_FD001.txt")
    test_raw = load_data("dataset/test_FD001.txt")

    print("Preprocessing...")
    train_processed, test_processed = preprocess_data(train_raw, test_raw)

    print(f"Train size: {train_processed.shape}")
    print(f"Test size: {test_processed.shape}")
    print("\nFirst 3 rows of train set: ")
    print(train_processed.head(3))

    train_processed.to_csv("dataset/train_processed.csv", index=False)
    test_processed.to_csv("dataset/test_processed.csv", index=False)









