from pathlib import Path
import sys

import torch
from torch import nn

project_root = next(
    (
        path
        for path in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents, Path.cwd(), *Path.cwd().parents]
        if (path / "n_cmapss" / "features" / "dl_sequences.py").is_file()
    ),
    None,
)

if project_root is None:
    raise FileNotFoundError("Proje kökü bulunamadı.")

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from n_cmapss.features.dl_sequences import (
    DLSequenceConfig,
    build_dl_loaders,
)


def run_fold(fold, seed, experiment_dir, max_epochs=50, patience=8):
    torch.manual_seed(seed)
    print("Proje kökü:", project_root)

    config = DLSequenceConfig(
        fold_number=fold,
        batch_size=64,
        random_seed=seed,
    )

    train_loader, val_loader, scaler, feature_names = build_dl_loaders(config)

    print("Eğitim pencereleri:", len(train_loader.dataset))
    print("Doğrulama pencereleri:", len(val_loader.dataset))
    print("Girdi kanalları:", feature_names)

    class CNNRegressor(nn.Module):
        def __init__(self, input_channels=18):
            super().__init__()

            self.feature_extractor = nn.Sequential(
                nn.Conv1d(input_channels, 32, kernel_size=5, padding=2),
                nn.ReLU(),

                nn.Conv1d(32, 64, kernel_size=5, padding=2),
                nn.ReLU(),

                nn.AdaptiveAvgPool1d(1),
            )

            self.regressor = nn.Sequential(
                nn.Flatten(),
                nn.Linear(64, 32),
                nn.ReLU(),
                nn.Linear(32, 1),
            )

        def forward(self, x):
            features = self.feature_extractor(x)
            predictions = self.regressor(features)
            return predictions.squeeze(-1)


    model = CNNRegressor(input_channels=len(feature_names))
    print(model)

    features, targets = next(iter(val_loader))

    model.eval()

    with torch.no_grad():
        predictions = model(features)

    print("Girdi:", features.shape)
    print("Gerçek RUL:", targets.shape)
    print("Tahmin:", predictions.shape)

    assert predictions.shape == targets.shape
    assert torch.isfinite(predictions).all()

    parameter_count = sum(
        parameter.numel()
        for parameter in model.parameters()
        if parameter.requires_grad
    )

    print("Eğitilebilir parametre sayısı:", parameter_count)
    print("İlk 5 gerçek RUL:", targets[:5])
    print("İlk 5 başlangıç tahmini:", predictions[:5])

    # ============================================================
    # 5. Eğitim ayarları
    # ============================================================

    import copy
    import csv
    import json
    import pickle
    import time
    from datetime import datetime

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    device = torch.device("cpu")
    torch.set_num_threads(4)
    model = model.to(device)

    MAX_EPOCHS = max_epochs
    PATIENCE = patience
    LEARNING_RATE = 0.001

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
    )

    output_dir = experiment_dir / f"fold_{fold}"
    output_dir.mkdir(parents=True, exist_ok=False)

    print("\nCihaz:", device)
    print("Çıktı klasörü:", output_dir)


    # ============================================================
    # 6. Değerlendirme fonksiyonu
    # ============================================================

    def evaluate(model, loader):
        model.eval()

        predictions_list = []
        targets_list = []

        with torch.no_grad():
            for features, targets in loader:
                features = features.to(device)
                predictions = model(features)

                predictions_list.append(predictions.cpu())
                targets_list.append(targets.cpu())

        predictions = torch.cat(predictions_list)
        targets = torch.cat(targets_list)

        errors = predictions - targets
        mse = errors.square().mean().item()
        mae = errors.abs().mean().item()
        rmse = mse ** 0.5

        return mse, mae, rmse, predictions, targets


    # ============================================================
    # 7. Basit referans: her pencereye eğitim RUL ortalamasını söyle
    # ============================================================

    training_targets = train_loader.dataset.tensors[1]
    validation_targets = val_loader.dataset.tensors[1]

    baseline_value = training_targets.mean().item()
    baseline_errors = baseline_value - validation_targets

    baseline_mae = baseline_errors.abs().mean().item()
    baseline_rmse = baseline_errors.square().mean().sqrt().item()

    print(f"\nReferans sabit tahmin: {baseline_value:.2f} döngü")
    print(f"Referans doğrulama MAE: {baseline_mae:.2f}")
    print(f"Referans doğrulama RMSE: {baseline_rmse:.2f}")


    # ============================================================
    # 8. Eğitim döngüsü ve erken durdurma
    # ============================================================

    history = []
    best_val_mse = float("inf")
    best_state = None
    best_epoch = None
    epochs_without_improvement = 0
    training_start = time.perf_counter()

    for epoch in range(1, MAX_EPOCHS + 1):
        epoch_start = time.perf_counter()
        model.train()

        total_squared_error = 0.0
        sample_count = 0

        for features, targets in train_loader:
            features = features.to(device)
            targets = targets.to(device)

            optimizer.zero_grad(set_to_none=True)

            predictions = model(features)
            loss = criterion(predictions, targets)

            if not torch.isfinite(loss).item():
                raise RuntimeError("Eğitim kaybı NaN/Inf oldu.")

            loss.backward()
            optimizer.step()

            batch_size = targets.size(0)
            total_squared_error += loss.item() * batch_size
            sample_count += batch_size

        train_mse = total_squared_error / sample_count
        train_rmse = train_mse ** 0.5

        val_mse, val_mae, val_rmse, _, _ = evaluate(model, val_loader)

        if not all(
            value < float("inf")
            for value in [val_mse, val_mae, val_rmse]
        ):
            raise RuntimeError("Doğrulama metriği NaN/Inf oldu.")

        improved = val_mse < best_val_mse

        if improved:
            best_val_mse = val_mse
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            epochs_without_improvement = 0

            torch.save(
                {
                    "model_state_dict": best_state,
                    "epoch": epoch,
                    "validation_mse": val_mse,
                    "input_channels": len(feature_names),
                    "feature_names": feature_names,
                    "window_size": 256,
                    "fold": config.fold_number,
                    "seed": config.random_seed,
                    "learning_rate": LEARNING_RATE,
                },
                output_dir / "best_model.pt",
            )
        else:
            epochs_without_improvement += 1

        elapsed = time.perf_counter() - epoch_start

        history.append({
            "epoch": epoch,
            "train_mse": train_mse,
            "train_rmse": train_rmse,
            "validation_mse": val_mse,
            "validation_mae": val_mae,
            "validation_rmse": val_rmse,
            "seconds": elapsed,
        })

        # Her epoch sonunda kaydet: eğitim kesilse de geçmiş korunsun.
        with (output_dir / "history.csv").open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=history[0].keys())
            writer.writeheader()
            writer.writerows(history)

        marker = " <-- en iyi" if improved else ""

        print(
            f"Epoch {epoch:02d}/{MAX_EPOCHS} | "
            f"Train RMSE: {train_rmse:.3f} | "
            f"Val RMSE: {val_rmse:.3f} | "
            f"Val MAE: {val_mae:.3f} | "
            f"{elapsed:.1f} sn{marker}",
            flush=True,
        )

        if epochs_without_improvement >= PATIENCE:
            print(f"\nErken durdurma: {PATIENCE} epoch iyileşme yok.")
            break

    training_seconds = time.perf_counter() - training_start


    # ============================================================
    # 9. En iyi modele dön ve sonuçları kaydet
    # ============================================================

    model.load_state_dict(best_state)

    _, cnn_mae, cnn_rmse, predictions, targets = evaluate(
        model, val_loader
    )

    # Eğitimin sonunda eğitim kümesini de sabit modelle değerlendir.
    _, final_train_mae, final_train_rmse, _, _ = evaluate(
        model, train_loader
    )

    metrics = {
        "fold": config.fold_number,
        "seed": config.random_seed,
        "validation_windows": len(val_loader.dataset),
        "training_windows": len(train_loader.dataset),
        "best_epoch": best_epoch,
        "epochs_run": len(history),
        "training_seconds": training_seconds,
        "baseline_validation_mae": baseline_mae,
        "baseline_validation_rmse": baseline_rmse,
        "cnn_validation_mae": cnn_mae,
        "cnn_validation_rmse": cnn_rmse,
        "cnn_train_mae": final_train_mae,
        "cnn_train_rmse": final_train_rmse,
        "evaluation_level": "window",
        "split": "development_validation",
    }

    with (output_dir / "metrics.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(metrics, file, indent=2)

    # Gelecekte tahmin üretirken aynı ölçekleyici kullanılmalı.
    with (output_dir / "scaler.pkl").open("wb") as file:
        pickle.dump(scaler.scaler, file)

    print("\n--- EN İYİ MODELİN SONUÇLARI ---")
    print(f"En iyi epoch: {best_epoch}")
    print(f"Eğitim RMSE: {final_train_rmse:.3f}")
    print(f"Doğrulama MAE: {cnn_mae:.3f}")
    print(f"Doğrulama RMSE: {cnn_rmse:.3f}")
    print(f"Referans RMSE: {baseline_rmse:.3f}")
    print(f"Toplam eğitim süresi: {training_seconds:.1f} saniye")


    # ============================================================
    # 10. Tahminleri motor/uçuş bilgileriyle kaydet
    # ============================================================

    from n_cmapss.preprocessing.data_loader import (
        load_window_metadata,
        split_windows_by_fold,
    )

    _, validation_records = split_windows_by_fold(
        load_window_metadata(),
        fold_number=config.fold_number,
    )

    assert len(validation_records) == len(targets)

    expected_targets = torch.tensor(
        [record.rul for record in validation_records],
        dtype=targets.dtype,
    )
    assert torch.allclose(targets, expected_targets)

    with (output_dir / "validation_predictions.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "window_id", "unit", "cycle",
            "true_rul", "predicted_rul", "error",
        ])

        for record, actual, predicted in zip(
            validation_records, targets.tolist(), predictions.tolist()
        ):
            writer.writerow([
                record.window_id,
                record.unit,
                record.cycle,
                actual,
                predicted,
                predicted - actual,
            ])


    # ============================================================
    # 11. Sunum grafikleri
    # ============================================================

    epochs = [row["epoch"] for row in history]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(
        epochs,
        [row["train_rmse"] for row in history],
        label="Training RMSE (during updates)",
    )
    ax.plot(
        epochs,
        [row["validation_rmse"] for row in history],
        label="Validation RMSE",
    )
    ax.axvline(
        best_epoch, color="gray", linestyle="--",
        label=f"Best epoch: {best_epoch}",
    )
    ax.set_xlabel("Epoch")
    ax.set_ylabel("RMSE (flight cycles)")
    ax.set_title(f"CNN learning curves — Fold {fold}")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_dir / "learning_curves.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(targets.numpy(), predictions.numpy(), alpha=0.35, s=15)

    lower = min(targets.min().item(), predictions.min().item())
    upper = max(targets.max().item(), predictions.max().item())
    ax.plot([lower, upper], [lower, upper], "r--", label="Perfect prediction")

    ax.set_xlabel("True RUL (flight cycles)")
    ax.set_ylabel("Predicted RUL (flight cycles)")
    ax.set_title(f"Validation windows — Fold {fold}")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_dir / "true_vs_predicted.png", dpi=180)
    plt.close(fig)

    print("\nModel, ölçekleyici, sonuçlar ve grafikler kaydedildi:")
    print(output_dir)
    return metrics


def main():
    import argparse
    import csv
    import json
    import statistics
    from datetime import datetime

    parser = argparse.ArgumentParser(description="CNN development motor validation")
    parser.add_argument("--folds", nargs="+", type=int, choices=range(1, 7), default=[1])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-epochs", type=int, default=50)
    parser.add_argument("--patience", type=int, default=8)
    args = parser.parse_args()
    if args.max_epochs < 1 or args.patience < 1:
        parser.error("max-epochs and patience must be positive")
    if len(set(args.folds)) != len(args.folds):
        parser.error("Duplicate folds are not allowed")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    experiment_dir = project_root / "n_cmapss" / "outputs" / f"cnn_cv_{stamp}"
    experiment_dir.mkdir(parents=True, exist_ok=False)
    settings = dict(vars(args), learning_rate=0.001, batch_size=64,
                    device="cpu", evaluation="development_validation",
                    epoch_selection="minimum held-out motor validation MSE",
                    note="Not an independent test estimate; validation selects epoch.")
    (experiment_dir / "experiment_config.json").write_text(
        json.dumps(settings, indent=2), encoding="utf-8")
    # Keep exact training source alongside the results.
    (experiment_dir / "training_source.py").write_text(
        Path(__file__).read_text(encoding="utf-8"), encoding="utf-8")
    results = []
    for fold in args.folds:
        print(f"\n===== FOLD {fold} / seed {args.seed} =====", flush=True)
        metrics = run_fold(fold, args.seed, experiment_dir,
                           args.max_epochs, args.patience)
        results.append(metrics)
        with (experiment_dir / "fold_results.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        summary = {"completed_folds": [r["fold"] for r in results],
                   "requested_folds": args.folds,
                   "evaluation": "development_validation",
                   "std_definition": "sample standard deviation across motors (ddof=1)"}
        for key in ["cnn_validation_mae", "cnn_validation_rmse",
                    "baseline_validation_mae", "baseline_validation_rmse"]:
            values = [r[key] for r in results]
            summary[key] = {"macro_mean": statistics.mean(values),
                            "std": statistics.stdev(values) if len(values) > 1 else None}
        count = sum(r["validation_windows"] for r in results)
        summary["pooled_window_mae"] = sum(
            r["validation_windows"] * r["cnn_validation_mae"] for r in results) / count
        summary["pooled_window_rmse"] = (sum(
            r["validation_windows"] * r["cnn_validation_rmse"] ** 2 for r in results) / count) ** 0.5
        (experiment_dir / "summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8")
    print("\nCompleted. Results:", experiment_dir)
    for r in results:
        print(f"Fold {r['fold']}: MAE={r['cnn_validation_mae']:.3f}, RMSE={r['cnn_validation_rmse']:.3f}")


if __name__ == "__main__":
    main()
