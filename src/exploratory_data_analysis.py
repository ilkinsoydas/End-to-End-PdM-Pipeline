import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def check_basic_stats(df_train, df_test, df_rul):
    print("--- Train Data Info ---")
    print(df_train.info())
    print("\n--- Train Null Values ---")
    print(df_train.isnull().sum())
    
    std = df_train.std()
    constant_cols = std[std == 0].index.tolist()
    print("\n--- Invariant Features (Constant) ---")
    print(constant_cols)
    
    max_cycle_per_engine = df_train.groupby("unit_nr")["time_cycles"].max()
    print("\n--- Engine Lifespans ---")
    print(f"Shortest life: {max_cycle_per_engine.min()} cycles")
    print(f"Longest life: {max_cycle_per_engine.max()} cycles")

def plot_sensor_trend(df, unit_id, sensors_to_plot):
    engine_data = df[df["unit_nr"] == unit_id]
    
    plt.figure(figsize=(12, 5))
    for sensor in sensors_to_plot:
        if sensor in engine_data.columns:
            plt.plot(engine_data["time_cycles"], engine_data[sensor], label=f"{sensor} data", alpha=0.7)
            
    plt.title(f"Sensor Trends for Engine {unit_id}")
    plt.xlabel("Time (cycles)")
    plt.ylabel("Sensor Value")
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_correlation_heatmap(df, title="Feature Correlation Heatmap"):
    plt.figure(figsize=(16, 12))
    
    # Sadece korelasyon matrisini hesapla
    corr_matrix = df.corr(method="pearson")
    
    sns.heatmap(corr_matrix, annot=False, cmap="coolwarm", center=0)
    plt.title(title)
    plt.show()

if __name__ == "__main__":
    print("EDA Başlatılıyor...")
    
    index_names = ["unit_nr", "time_cycles"]
    setting_names = ['setting_1', 'setting_2', 'setting_3']
    sensor_names = [f"s_{i}" for i in range(1, 22)]
    col_names = index_names + setting_names + sensor_names

    train_raw = pd.read_csv("dataset/train_FD001.txt", header=None, sep=r"\s+", names=col_names)
    test_raw = pd.read_csv("dataset/test_FD001.txt", header=None, sep=r"\s+", names=col_names)
    rul_raw = pd.read_csv("dataset/RUL_FD001.txt", header=None, names=["true_rul"])
    
    check_basic_stats(train_raw, test_raw, rul_raw)
    
    train_engineered = pd.read_csv("dataset/train_engineered.csv")
  
    plot_sensor_trend(train_engineered, unit_id=1, sensors_to_plot=["s_2", "s_3"])
    
    plot_correlation_heatmap(train_engineered, title="Engineered Features Correlation Heatmap")
    
