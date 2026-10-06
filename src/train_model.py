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
    train_idx, val_idx = next(gkf.split(X, y, groups))

    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

    models = {
        "Random Forest": RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=42),
        "XGBoost": XGBClassifier(n_estimators=100, scale_pos_weight=scale_weight, eval_metric="logloss", random_state=42)
    }

    best_model = None
    best_f1 = 0

    for name, model in models.items():
        print(f"\n==================== {name} ====================")
        model.fit(X_train, y_train)
        preds = model.predict(X_val)
        print(classification_report(y_val, preds, digits=4))
        score = f1_score(y_val, preds)
        if score > best_f1:
            best_f1 = score
            best_model = (name, model)

    best_name, model_obj = best_model
    best_preds = model_obj.predict(X_val)
    cm = confusion_matrix(y_val, best_preds)
    
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Normal", "Fault"], yticklabels=["Normal", "Fault"])
    plt.title(f"{best_name} Confusion Matrix (F1: {best_f1:.4f})")
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
