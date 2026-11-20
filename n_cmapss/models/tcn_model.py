import torch
from torch import nn
from n_cmapss.models.tcn_blocks import TemporalBlock

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