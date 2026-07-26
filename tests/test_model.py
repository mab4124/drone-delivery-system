import pytest
import torch
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from model import UNet
from config import NUM_CLASSES, PROCESSING_WIDTH, PROCESSING_HEIGHT


class TestUNetModel:
    """Test suite for U-Net semantic segmentation model."""
    
    @pytest.fixture
    def model(self) -> UNet:
        """Fixture to provide initialized U-Net model."""
        return UNet(in_channels=3)
    
    def test_model_creation(self, model: UNet) -> None:
        """Test that model can be created without errors."""
        assert model is not None
        assert isinstance(model, UNet)
    
    def test_model_forward_pass(self, model: UNet) -> None:
        """Test that model forward pass works correctly."""
        batch_size = 2
        input_tensor = torch.randn(batch_size, 3, PROCESSING_HEIGHT, PROCESSING_WIDTH)
        output = model(input_tensor)
        
        assert output.shape == (batch_size, NUM_CLASSES, PROCESSING_HEIGHT, PROCESSING_WIDTH)
    
    def test_model_output_range(self, model: UNet) -> None:
        """Test that model outputs are in valid range."""
        input_tensor = torch.randn(1, 3, PROCESSING_HEIGHT, PROCESSING_WIDTH)
        output = model(input_tensor)
        
        assert torch.isfinite(output).all()
    
    def test_model_different_batch_sizes(self, model: UNet) -> None:
        """Test model with different batch sizes."""
        for batch_size in [1, 2, 4]:
            input_tensor = torch.randn(batch_size, 3, PROCESSING_HEIGHT, PROCESSING_WIDTH)
            output = model(input_tensor)
            assert output.shape[0] == batch_size
    
    def test_model_gradients(self, model: UNet) -> None:
        """Test that gradients can be computed."""
        input_tensor = torch.randn(1, 3, PROCESSING_HEIGHT, PROCESSING_WIDTH, requires_grad=True)
        output = model(input_tensor)
        loss = output.sum()
        loss.backward()
        
        assert input_tensor.grad is not None
    
    def test_model_cpu_device(self) -> None:
        """Test model on CPU device."""
        model = UNet(in_channels=3)
        model = model.to('cpu')
        
        input_tensor = torch.randn(1, 3, PROCESSING_HEIGHT, PROCESSING_WIDTH)
        output = model(input_tensor)
        
        assert output.device.type == 'cpu'
    
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_model_gpu_device(self) -> None:
        """Test model on GPU device (if available)."""
        model = UNet(in_channels=3)
        model = model.to('cuda')
        
        input_tensor = torch.randn(1, 3, PROCESSING_HEIGHT, PROCESSING_WIDTH).to('cuda')
        output = model(input_tensor)
        
        assert output.device.type == 'cuda'
    
    def test_model_eval_mode(self, model: UNet) -> None:
        """Test model in evaluation mode."""
        model.eval()
        
        with torch.no_grad():
            input_tensor = torch.randn(1, 3, PROCESSING_HEIGHT, PROCESSING_WIDTH)
            output = model(input_tensor)
        
        assert output is not None
    
    def test_model_train_mode(self, model: UNet) -> None:
        """Test model in training mode."""
        model.train()
        
        input_tensor = torch.randn(1, 3, PROCESSING_HEIGHT, PROCESSING_WIDTH)
        output = model(input_tensor)
        
        assert output is not None


class TestSegmentationOutput:
    """Test suite for segmentation output validation."""
    
    @pytest.fixture
    def model(self) -> UNet:
        """Fixture to provide initialized U-Net model."""
        model = UNet(in_channels=3)
        model.eval()
        return model
    
    def test_segmentation_argmax(self, model: UNet) -> None:
        """Test argmax operation on segmentation output."""
        input_tensor = torch.randn(1, 3, PROCESSING_HEIGHT, PROCESSING_WIDTH)
        
        with torch.no_grad():
            output = model(input_tensor)
            segmentation = torch.argmax(output, dim=1)
        
        assert segmentation.shape == (1, PROCESSING_HEIGHT, PROCESSING_WIDTH)
        assert segmentation.max() < NUM_CLASSES
        assert segmentation.min() >= 0
    
    def test_segmentation_class_range(self, model: UNet) -> None:
        """Test that all predicted classes are within valid range."""
        input_tensor = torch.randn(2, 3, PROCESSING_HEIGHT, PROCESSING_WIDTH)
        
        with torch.no_grad():
            output = model(input_tensor)
            segmentation = torch.argmax(output, dim=1)
        
        assert segmentation.max() <= NUM_CLASSES - 1
        assert segmentation.min() >= 0


class TestConfigurationValues:
    """Test suite for configuration values."""
    
    def test_config_imports(self) -> None:
        """Test that all required config values can be imported."""
        from config import (NUM_CLASSES, PROCESSING_WIDTH, PROCESSING_HEIGHT, 
                           DEVICE, BATCH_SIZE, LEARNING_RATE)
        
        assert NUM_CLASSES > 0
        assert PROCESSING_WIDTH > 0
        assert PROCESSING_HEIGHT > 0
        assert BATCH_SIZE > 0
        assert LEARNING_RATE > 0
    
    def test_config_values_reasonable(self) -> None:
        """Test that config values are reasonable."""
        from config import NUM_CLASSES, PROCESSING_WIDTH, PROCESSING_HEIGHT
        
        assert NUM_CLASSES >= 2
        assert PROCESSING_WIDTH == PROCESSING_HEIGHT or abs(PROCESSING_WIDTH - PROCESSING_HEIGHT) < 100
        assert PROCESSING_WIDTH >= 128


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
