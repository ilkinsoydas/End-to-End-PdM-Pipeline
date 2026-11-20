import torch
from torch import nn
from torch.utils.data import DataLoader
from n_cmapss.models.tcn_model import TCNRegressor
from n_cmapss.features.dl_sequences import (
    DLSequenceConfig,
    build_dl_loaders,
)
from n_cmapss.preprocessing.data_loader import load_window_metadata, split_windows_by_fold
import math
import csv
import time
from pathlib import Path
from datetime import datetime

def get_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")

    return torch.device("cpu")

def prepare_data(fold_number: int):
    config = DLSequenceConfig(
        fold_number=fold_number,
        batch_size=64,
        random_seed=42,
    )
    return build_dl_loaders(config)

def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> float:
    model.train()
    
    total_loss = 0.0
    total_samples = 0
    
    for features, targets in loader:
        features = features.to(device)
        targets = targets.to(device)
        
        optimizer.zero_grad(set_to_none=True)
        
        predictions = model(features)
        loss = criterion(predictions, targets)
        
        if not torch.isfinite(loss).item():
            raise RuntimeError("Training loss became NaN or infinite.")
        
        loss.backward()
        
        nn.utils.clip_grad_norm_(
            model.parameters(),
            max_norm=1.0,
            error_if_nonfinite=True,
        )
        
        optimizer.step()
        
        batch_size = features.size(0)
        total_loss += loss.item() * batch_size
        total_samples += batch_size
        
    if total_samples == 0:
        raise ValueError("Train loader is empty")

    return total_loss / total_samples

@torch.no_grad()
def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> float:
    model.eval()

    total_loss = 0.0
    total_samples = 0

    for features, targets in loader:
        features = features.to(device)
        targets = targets.to(device)

        predictions = model(features)
        loss = criterion(predictions, targets)

        if not torch.isfinite(loss).item():
            raise RuntimeError("Validation loss became NaN or infinite.")

        batch_size = features.size(0)
        total_loss += loss.item() * batch_size
        total_samples += batch_size

    if total_samples == 0:
        raise ValueError("Validation DataLoader is empty.")

    return total_loss / total_samples

def save_history(history: list[dict], output_path: Path) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(history[0].keys()),
        )
        writer.writeheader()
        writer.writerows(history)


@torch.no_grad()
def save_validation_results(model, loader, fold_number, output_dir, device):
    checkpoint = torch.load(output_dir / "best_model.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    _, records = split_windows_by_fold(load_window_metadata(), fold_number)
    # build_dl_loaders preserves metadata order for validation (shuffle=False).
    rows = []
    for features, targets in loader:
        predictions = model(features.to(device)).cpu().tolist()
        for target, prediction in zip(targets.tolist(), predictions, strict=True):
            record = records[len(rows)]
            if target != record.rul or not math.isfinite(prediction):
                raise ValueError(f"Invalid validation result for window {record.window_id}")
            rows.append(dict(window_id=record.window_id, unit=record.unit, cycle=record.cycle,
                             actual_rul=target, predicted_rul=prediction))

    if not rows or len(rows) != len(records):
        raise ValueError("Validation window count mismatch")
    errors = [row["predicted_rul"] - row["actual_rul"] for row in rows]
    mae = sum(abs(error) for error in errors) / len(errors)
    rmse = math.sqrt(sum(error ** 2 for error in errors) / len(errors))
    save_history(rows, output_dir / "predictions.csv")
    save_history([dict(fold=fold_number, validation_unit=records[0].unit,
                       best_epoch=checkpoint["epoch"], windows=len(rows),
                       mae=mae, rmse=rmse)], output_dir / "metrics.csv")
    print(f"Fold {fold_number} | Validation MAE: {mae:.4f} | RMSE: {rmse:.4f}")


def train_fold(fold_number: int) -> None:
    torch.manual_seed(42)
    
    device = get_device()
    
    train_loader, validation_loader, scaler, feature_names = (
        prepare_data(fold_number=fold_number)
    )

    model = TCNRegressor(
        input_channels = len(feature_names),
    ).to(device)
    
    criterion = nn.MSELoss()
    
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=1e-3,
    )
    max_epochs = 100
    patience = 20
    
    best_validation_mse = float("inf")
    best_epoch = 0
    epochs_without_improvement = 0
    history = []

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_name = f"fold_{fold_number}_{timestamp}"
    
    output_dir = (
        Path(__file__).resolve().parents[1]
        / "outputs"
        / "tcn"
        / run_name
    )
    output_dir.mkdir(parents=True, exist_ok=False)

    print("Device:", device)
    print("Prediction window:", len(train_loader.dataset))
    print("Validation window:", len(validation_loader.dataset))
    
    training_start = time.perf_counter()

    for epoch in range(1, max_epochs + 1):
        epoch_start = time.perf_counter()
        
        train_mse = train_one_epoch(
            model=model,
            loader=train_loader,
            optimizer=optimizer,
            criterion=criterion,
            device=device,
        )
        
        validation_mse = evaluate(
            model=model,
            loader=validation_loader,
            criterion=criterion,
            device=device,
        )
        
        epoch_seconds = time.perf_counter() - epoch_start
        improved = validation_mse < best_validation_mse
        
        if improved:
            best_validation_mse = validation_mse
            best_epoch = epoch
            epochs_without_improvement = 0

            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": {
                        name: tensor.detach().cpu().clone()
                        for name, tensor in model.state_dict().items()
                    },
                    "validation_mse": validation_mse,
                    "validation_rmse": validation_mse ** 0.5,
                    "model_config": {
                        "input_channels": len(feature_names),
                        "channels": (32, 32, 64, 64, 64, 64, 64),
                        "kernel_size": 3,
                        "dropout": 0.2,
                    },
                    "feature_names": feature_names,
                    "scaler_mean": scaler.scaler.mean_.tolist(),
                    "scaler_scale": scaler.scaler.scale_.tolist(),
                    "fold": fold_number,
                    "seed": 42,
                },
                output_dir / "best_model.pt",
            )
        else:
            epochs_without_improvement += 1

        history.append(
            {
                "epoch": epoch,
                "train_mse": train_mse,
                "validation_mse": validation_mse,
                "validation_rmse": validation_mse ** 0.5,
                "epoch_seconds": epoch_seconds,
                "elapsed_seconds": time.perf_counter() - training_start,
                "is_best": improved,
            }
        )

        save_history(history, output_dir / "history.csv")

        
        print(
            f"Epoch {epoch}/{max_epochs} | "
            f"Train MSE: {train_mse:.4f} | "
            f"Validation MSE: {validation_mse:.4f} | "
            f"Validation RMSE: {validation_mse ** 0.5:.4f}",
            flush=True,
        )
        
        if epochs_without_improvement >= patience:
            print("Early stopping: training stopped.")
            break

    print(
        f"Best epoch: {best_epoch} | "
        f"Validation RMSE: {best_validation_mse ** 0.5:.4f}"
    )
    save_validation_results(model, validation_loader, fold_number, output_dir, device)
    print("Results:", output_dir)
    
def main() -> None:
    for fold_number in range(2, 7):
        print(f"\nFold {fold_number} starting..")
        train_fold(fold_number=fold_number)
    

if __name__ == "__main__":
    main()