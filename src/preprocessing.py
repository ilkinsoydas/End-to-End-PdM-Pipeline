import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

index_names = ["unit_nr", "time_cycles"]
setting_names = ['setting_1', 'setting_2', 'setting_3']
sensor_names = [f"s_{i}" for i in range(1, 22)]
col_names = index_names + setting_names + sensor_names

df_train = pd.read_csv("dataset/train_FD001.txt", header=None, sep=r"\s+", names=col_names)
df_test = pd.read_csv("dataset/test_FD001.txt", header=None, sep=r"\s+", names=col_names)
print("Train size: ", df_train.shape)
print("Test size: ", df_test.shape)

drop_columns = ["setting_3", "s_1", "s_5", "s_10", "s_16", "s_18", "s_19"]

df_train = df_train.drop(columns = drop_columns)
df_test = df_test.drop(columns = drop_columns)

print("---After Dropping Columns---")
print("\nSize of train data: ", df_train.shape)
print("\nSize of test data: ", df_test.shape)

features = [col for col in df_train.columns if col not in index_names]
scaler = MinMaxScaler()
df_train[features] = scaler.fit_transform(df_train[features])
df_test[features] = scaler.transform(df_test[features])

print("\n---Scaled Data Sample ---")
print(df_train[features].head())

max_cycles = df_train.groupby("unit_nr")["time_cycles"].transform("max")
df_train["RUL"] = max_cycles - df_train["time_cycles"]

clip_rul_threshold = 125
df_train["RUL"] = df_train["RUL"].clip(upper = clip_rul_threshold)

print("\n---First 10 RUL Values After Clipping (Max 125) ---")
print(df_train[["unit_nr", "time_cycles", "RUL"]].head(10))
print("\n---The Final Lines of the First Engine (The Moment It Broke Down)---")
print(df_train[df_train["unit_nr"] == 1][["unit_nr", "time_cycles", "RUL"]].tail(5))






