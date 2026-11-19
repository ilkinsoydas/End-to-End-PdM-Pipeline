import torch
from torch import nn
from torch.nn import functional as F

class CausalConv1D(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels:int,
        kernel_size: int,
        dilation: int = 1,
    ) -> None:
        super().__init__()
        
        self.left_padding = (kernel_size - 1) *  dilation
        
        self.conv = nn.Conv1d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=kernel_size,
            dilation=dilation,
            padding=0,
        )
        
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        padded_inputs = F.pad(
            inputs,
            (self.left_padding, 0),
        )
        return self.conv(padded_inputs)
    

class TemporalBlock(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        dilation: int,
        dropout: float=0.2,
    ) ->None:
        super().__init__()
        
        self.network = nn.Sequential(
            CausalConv1D(
                in_channels,
                out_channels,
                kernel_size,
                dilation,
            ),
            nn.ReLU(),
            nn.Dropout(dropout),
            CausalConv1D(
                out_channels,
                out_channels,
                kernel_size,
                dilation,
            ),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        
        self.residual = (
            nn.Conv1d(in_channels, out_channels, kernel_size=1)
            if in_channels != out_channels
            else nn.Identity()
        )
        
        self.activation = nn.ReLU()
        
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        output = self.network(inputs)
        residual = self.residual(inputs)
        
        return self.activation(output + residual)