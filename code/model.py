from typing import Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
from config import NUM_CLASSES


class ConvBlock(nn.Module):
    """Convolutional block with double convolution, batch normalization, and ReLU."""
    
    def __init__(self, in_channels: int, out_channels: int) -> None:
        """Initialize convolutional block.
        
        Args:
            in_channels: Number of input channels
            out_channels: Number of output channels
        """
        super(ConvBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(out_channels)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through convolution block.
        
        Args:
            x: Input tensor [B x C x H x W]
            
        Returns:
            Output tensor [B x out_channels x H x W]
        """
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.conv2(x)
        x = self.bn2(x)
        x = self.relu(x)
        return x


class UNet(nn.Module):
    """U-Net architecture for semantic segmentation of 24 terrain classes."""
    
    def __init__(self, in_channels: int = 3, out_channels: Optional[int] = None) -> None:
        """Initialize U-Net model.
        
        Args:
            in_channels: Number of input channels (default: 3 for RGB)
            out_channels: Number of output classes (default: NUM_CLASSES)
        """
        if out_channels is None:
            out_channels = NUM_CLASSES
        super(UNet, self).__init__()
        
        self.encoder1 = ConvBlock(in_channels, 64)
        self.pool1 = nn.MaxPool2d(2, 2)
        
        self.encoder2 = ConvBlock(64, 128)
        self.pool2 = nn.MaxPool2d(2, 2)
        
        self.encoder3 = ConvBlock(128, 256)
        self.pool3 = nn.MaxPool2d(2, 2)
        
        self.encoder4 = ConvBlock(256, 512)
        self.pool4 = nn.MaxPool2d(2, 2)
        
        self.bottleneck = ConvBlock(512, 1024)
        
        self.upconv4 = nn.ConvTranspose2d(1024, 512, kernel_size=2, stride=2)
        self.decoder4 = ConvBlock(512 + 512, 512)
        
        self.upconv3 = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        self.decoder3 = ConvBlock(256 + 256, 256)
        
        self.upconv2 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.decoder2 = ConvBlock(128 + 128, 128)
        
        self.upconv1 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.decoder1 = ConvBlock(64 + 64, 64)
        
        self.final_conv = nn.Conv2d(64, out_channels, kernel_size=1)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through U-Net.
        
        Args:
            x: Input tensor [B x 3 x H x W]
            
        Returns:
            Output segmentation map [B x NUM_CLASSES x H x W]
        """
        enc1 = self.encoder1(x)
        x = self.pool1(enc1)
        
        enc2 = self.encoder2(x)
        x = self.pool2(enc2)
        
        enc3 = self.encoder3(x)
        x = self.pool3(enc3)
        
        enc4 = self.encoder4(x)
        x = self.pool4(enc4)
        
        x = self.bottleneck(x)
        
        x = self.upconv4(x)
        enc4_resized = F.interpolate(enc4, size=x.shape[-2:], mode='bilinear', align_corners=False)
        x = torch.cat([x, enc4_resized], dim=1)
        x = self.decoder4(x)
        
        x = self.upconv3(x)
        enc3_resized = F.interpolate(enc3, size=x.shape[-2:], mode='bilinear', align_corners=False)
        x = torch.cat([x, enc3_resized], dim=1)
        x = self.decoder3(x)
        
        x = self.upconv2(x)
        enc2_resized = F.interpolate(enc2, size=x.shape[-2:], mode='bilinear', align_corners=False)
        x = torch.cat([x, enc2_resized], dim=1)
        x = self.decoder2(x)
        
        x = self.upconv1(x)
        enc1_resized = F.interpolate(enc1, size=x.shape[-2:], mode='bilinear', align_corners=False)
        x = torch.cat([x, enc1_resized], dim=1)
        x = self.decoder1(x)
        
        x = self.final_conv(x)
        return x
