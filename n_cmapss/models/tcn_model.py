import torch
from torch import nn
from n_cmapss.models.tcn_blocks import TemporalBlock


print("PyTorch:", torch.__version__)
print("CUDA:", torch.cuda.is_available())
print("MPS:", torch.backends.mps.is_available())

device = torch.device(
    "mps" if torch.backends.mps.is_available() else "cpu"
)

print("Eğitim cihazı:", device)

from n_cmapss.features.dl_sequences import (
    DLSequenceConfig,
    build_dl_loaders,
)

config = DLSequenceConfig(
    fold_number=1,
    batch_size=64,
)

train_loader, val_loader, scaler, feature_names = (
    build_dl_loaders(config)
)

features, targets = next(iter(train_loader))

print("Train windows:", len(train_loader.dataset))
print("Validation windows:", len(val_loader.dataset))
print("Input size:", features.shape)
print("Target size:", targets.shape)

class TCNRegressor(nn.Module):
    def __init__(
        self,
        input_channels: int = 18,
        channels: tuple[int, ...] = (32, 32, 64, 64, 64, 64, 64),
        kernel_size: int = 3,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        
        if not channels:
            raise ValueError("At least one temporal block is required.")
        
        blocks = []
        in_channels = input_channels
        
        for level, out_channels in enumerate(channels):
            blocks.append(
                TemporalBlock(
                    in_channels=in_channels,
                    out_channels=out_channels,
                    kernel_size=kernel_size,
                    dilation=2 ** level,
                    dropout=dropout,
                )
            )
            in_channels = out_channels
            
        self.backbone = nn.Sequential(*blocks)
        self.regressor = nn.Linear(channels[-1], 1)
        
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        features = self.backbone(inputs)
        
        last_step = features[:, :, -1]
        
        predictions = self.regressor(last_step)
        
        return predictions.squeeze(-1)