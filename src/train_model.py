import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import classification_report, confusion_matrix, f1_score

def train_and_evaluate(train_path="dataset/train_engineered.csv"):
    df = pd.read_csv(train_path)

    drop_cols = ["unit_nr", "time_cycles", "RUL", "label_1"]
    feature_cols = [col for col in df.columns if col not in drop_cols]

    X = df[feature_cols]
    y = df["label_1"]
    groups = df["unit_nr"]

    neg_count = (y == 0).sum()
    pos_count = (y == 1).sum()
    scale_weight = neg_count / pos_count

    gkf = GroupKFold(n_splits=5)
    
    models = {
        "Random Forest": RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=42),
        "XGBoost": XGBClassifier(n_estimators=100, scale_pos_weight=scale_weight, eval_metric="logloss", random_state=42)
    }

    best_model_name = None
    best_avg_f1 = 0
    trained_best_model = None

    for name, model in models.items():
        print(f"\n==================== {name} ====================")
        f1_scores = []
        
        for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups), 1):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            model.fit(X_train, y_train)
            preds = model.predict(X_val)
            score = f1_score(y_val, preds)
            f1_scores.append(score)
            print(f"Fold {fold} - F1 Skoru: {score:.4f}")
            
        avg_f1 = np.mean(f1_scores)
        print(f">>> {name} ORTALAMA F1: {avg_f1:.4f}")
        
        if avg_f1 > best_avg_f1:
            best_avg_f1 = avg_f1
            best_model_name = name
            trained_best_model = model
            
    print(f"\nŞAMPİYON MODEL: {best_model_name} (Ortalama F1: {best_avg_f1:.4f})")
    
    best_name = best_model_name
    model_obj = trained_best_model
    
    # Grafikler için son fold'un verilerini (X_val, y_val) kullanıyoruz
    best_preds = model_obj.predict(X_val)
    cm = confusion_matrix(y_val, best_preds)
    
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Normal", "Fault"], yticklabels=["Normal", "Fault"])
    plt.title(f"{best_name} Confusion Matrix (Ortalama F1: {best_avg_f1:.4f})")
    plt.xlabel("Tahmin Edilen")
    plt.ylabel("Gerçek Değer")
    plt.tight_layout()
    plt.savefig("confusion_matrix.png")

    if hasattr(model_obj, "feature_importances_"):
        importances = pd.Series(model_obj.feature_importances_, index=feature_cols)
        top_features = importances.nlargest(10)
        plt.figure(figsize=(10, 5))
        top_features.plot(kind="barh", color="steelblue")
        plt.title(f"{best_name} - En Belirleyici İlk 10 Özellik")
        plt.xlabel("Önem Skoru")
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig("feature_importance.png")

if __name__ == "__main__":
    train_and_evaluate()
