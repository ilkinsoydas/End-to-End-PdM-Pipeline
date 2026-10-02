import pandas as pd

index_names = ["unit_nr", "time_cycles"]
setting_names = ['setting_1', 'setting_2', 'setting_3']
sensor_names = [f"s_{i}" for i in range(1, 22)]
col_names = index_names + setting_names + sensor_names

df_train = pd.read_csv("dataset/train_FD001.txt", header = None, sep=r"\s+" , names=col_names)
print(df_train.head())

print("---Data Info---")
print(df_train.info())

print("\n---Number of None Values---")
print(df_train.isnull().sum())

print("\n---Summary Statistics---")
pd.set_option("display.max_columns", None)
print(df_train.describe())

std = df_train.std()
constant_cols = std[std == 0].index.tolist()
print("\n---Invariant Features---") #değeri hiç değişmeyen sabit sütunlar
print(constant_cols)

max_cycle_per_engine = df_train.groupby("unit_nr")["time_cycles"].max()
print("\n---Engine Lifespans (Max Cycles) Summary---")
print(max_cycle_per_engine.describe())

print("\nShortes lives engine lifetime: ", max_cycle_per_engine.min(), "cycles")
print("\nLonges lives engine lifetime: ", max_cycle_per_engine.max(), "cycles")

df_test = pd.read_csv("dataset/test_FD001.txt", header = None, sep=r"\s+" , names=col_names)
df_rul = pd.read_csv("dataset/RUL_FD001.txt", header = None , names=["true_rul"])

print("\n--- Test Data Summary ---")
print("Test shape              :", df_test.shape)
print("Unique engines in test  :", df_test['unit_nr'].nunique())
print("Test null values total  :", df_test.isnull().sum().sum())

test_last_cycle = df_test.groupby("unit_nr")["time_cycles"].max()
print("\n--- Test Engines Last Recorded Cycles ---")
print(test_last_cycle.describe())

print("\n--- Ground Truth RUL Summary (RUL_FD001.txt) ---")
print(df_rul.describe())

