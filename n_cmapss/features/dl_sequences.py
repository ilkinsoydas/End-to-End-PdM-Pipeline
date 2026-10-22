from dataclasses import dataclass
from collections.abc import Sequence
from torch.utils.data import DataLoader, TensorDataset
from n_cmapss.preprocessing.create_windows import WindowRecord
from sklearn.preprocessing import StandardScaler
from n_cmapss.preprocessing.config import WINDOW_SIZE


import numpy as np
import torch 


from n_cmapss.preprocessing.data_loader import (
    NCmapssDataLoader,
    load_feature_names,
    load_window_metadata,
    split_windows_by_fold,
)

@dataclass(frozen=True)
class DLSequenceConfig:
    fold_number: int = 1
    batch_size: int = 64
    random_seed: int = 42
    num_workers: int = 0
    pin_memory: bool = False
    
    def __post_init__(self) -> None:
        if not 1 <= self.fold_number <= 6:
            raise ValueError("Fold number must be between 1 and 6.")
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive.")
        if self.num_workers < 0:
            raise ValueError("num_workers cannot be negative.")
        
@dataclass(frozen=True)
class FeatureStandardizer:
    scaler: StandardScaler
    
    @classmethod
    def fit(
        cls, windows: Sequence[WindowRecord],
        read_batch_size: int = 64,
    ) -> "FeatureStandardizer":
        if not windows:
            raise ValueError("Training windows cannot be empty.")
        
        scaler = StandardScaler()
        
        with NCmapssDataLoader() as loader:
            for features, _, _ in loader.iter_batches(
                windows,
                batch_size=read_batch_size,
            ):
                flattened = features.reshape(-1, 18)
                
                if not np.isfinite(flattened).all():
                    raise ValueError(
                        "Training features contain NaN or infinite values."
                    )
                scaler.partial_fit(flattened)
        return cls(scaler=scaler)
        
    def transform(self, features: np.ndarray) -> np.ndarray:
        if features.ndim not in (2, 3) or features.shape[-1] != 18:
            raise ValueError(
                "Expected shape (time, 18) or (batch, time, 18)."
            )
        if not np.isfinite(features).all():
            raise ValueError(
                "Features contain NaN or infinite values."
            )
                
        normalized = self.scaler.transform(
            features.reshape(-1, 18)
        )
        return normalized.reshape(features.shape).astype(
            np.float32,
            copy = False,
        )
            
def prepare_fold(
    config: DLSequenceConfig,
) -> tuple[
    list[WindowRecord],
    list[WindowRecord],
    FeatureStandardizer,
]:
    windows = load_window_metadata()
    
    train_windows, validation_windows = split_windows_by_fold(
        windows,
        fold_number=config.fold_number
    )
    scaler = FeatureStandardizer.fit(
        train_windows,
        read_batch_size=config.batch_size,
    )
    return train_windows, validation_windows, scaler

def load_normalized_sequences(
    windows: Sequence[WindowRecord],
    scaler: FeatureStandardizer,
    read_batch_size: int = 64,
) -> tuple[np.ndarray, np.ndarray]:
    if not windows:
        raise ValueError("Windows list cannot be empty")
    
    sequences = np.empty(
        (len(windows), WINDOW_SIZE, 18),
        dtype = np.float32,
    )
    targets = np.empty(len(windows), dtype=np.float32)
    
    offset = 0
    
    with NCmapssDataLoader() as loader:
        for features, batch_targets, records in loader.iter_batches(
            windows,
            batch_size=read_batch_size,
        ):
            batch_end = offset + len(records)
            
            sequences[offset:batch_end] = scaler.transform(features)
            targets[offset:batch_end] = batch_targets
            
            offset = batch_end
    return sequences, targets

def create_tensor_dataset(
    sequences: np.ndarray,
    targets: np.ndarray,
) -> TensorDataset:
    if sequences.ndim != 3 or sequences.shape[1:] != (WINDOW_SIZE, 18):
        raise ValueError(
            f"Expected shape (N, {WINDOW_SIZE}, 18), "
            f"found {sequences.shape}."
        )
    
    if targets.shape != (len(sequences),):
        raise ValueError("Each sequence must have one RUL target")

    features_tensor = torch.from_numpy(
        np.ascontiguousarray(
            sequences.transpose(0, 2, 1),
            dtype=np.float32,
        )
    )
    
    targets_tensor = torch.from_numpy(
        np.ascontiguousarray(targets, dtype=np.float32)
    )
    
    return TensorDataset(features_tensor, targets_tensor)

def build_dl_loaders(
    config: DLSequenceConfig,
) -> tuple[DataLoader, DataLoader, FeatureStandardizer, list[str]]:
    train_windows, validation_windows, scaler = prepare_fold(config)
    
    train_sequences, train_targets = load_normalized_sequences(
        train_windows,
        scaler,
        read_batch_size=config.batch_size,
    )
    
    validation_sequences, validation_targets = load_normalized_sequences(
        validation_windows,
        scaler,
        read_batch_size=config.batch_size,
    )
    
    train_dataset = create_tensor_dataset(
        train_sequences,
        train_targets,
    )
    
    validation_dataset = create_tensor_dataset(
        validation_sequences,
        validation_targets,
    )
    
    generator = torch.Generator()
    generator.manual_seed(config.random_seed)
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        shuffle=True,
        generator=generator,
        num_workers=config.num_workers,
        pin_memory=config.pin_memory,
        drop_last=False,
    )
    
    validation_loader = DataLoader(
        validation_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers,
        pin_memory=config.pin_memory,
        drop_last=False,
    )

    return train_loader, validation_loader, scaler, load_feature_names()


if __name__ == "__main__":
    config = DLSequenceConfig(fold_number=1, batch_size=64)

    train_loader, validation_loader, scaler, feature_names = (
        build_dl_loaders(config)
    )

    features, targets = next(iter(train_loader))

    print("Train windows:", len(train_loader.dataset))
    print("Validation windows:", len(validation_loader.dataset))
    print("Input shape:", features.shape)
    print("Target shape:", targets.shape)






