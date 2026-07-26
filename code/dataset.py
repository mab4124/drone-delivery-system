from typing import Tuple, Optional
import os
import torch
import numpy as np
from PIL import Image
from torch.utils.data import Dataset
import cv2
from config import PROCESSING_WIDTH, PROCESSING_HEIGHT, NUM_CLASSES, CLASS_DICT
from utils import rgb_to_mask

class GrazDataset(Dataset):
    """TU Graz Semantic Drone Dataset for semantic segmentation."""
    
    def __init__(self, dataset_root: str, split: str = "train", train_val_split: float = 0.8) -> None:
        """Initialize dataset.
        
        Args:
            dataset_root: Root directory containing training_set folder
            split: 'train' or 'val' split
            train_val_split: Fraction of data for training
        """
        self.dataset_root = dataset_root
        self.split = split
        self.train_val_split = train_val_split
        
        images_dir = os.path.join(dataset_root, "training_set", "images")
        masks_dir = os.path.join(dataset_root, "training_set", "gt", "semantic", "label_images")
        
        self.image_files = sorted([f for f in os.listdir(images_dir) if f.endswith(".jpg")])
        
        num_total = len(self.image_files)
        num_train = int(num_total * train_val_split)
        
        if split == "train":
            self.image_files = self.image_files[:num_train]
        else:
            self.image_files = self.image_files[num_train:]
        
        self.images_dir = images_dir
        self.masks_dir = masks_dir
    
    def __len__(self) -> int:
        """Return dataset size."""
        return len(self.image_files)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get image and mask pair.
        
        Args:
            idx: Index of sample
            
        Returns:
            Tuple of (image_tensor, mask_tensor)
        img_filename = self.image_files[idx]
        mask_filename = img_filename.replace(".jpg", ".png")
        
        img_path = os.path.join(self.images_dir, img_filename)
        mask_path = os.path.join(self.masks_dir, mask_filename)
        
        image = cv2.imread(img_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (PROCESSING_WIDTH, PROCESSING_HEIGHT), interpolation=cv2.INTER_LINEAR)
        image = image.astype(np.float32) / 255.0
        image = torch.from_numpy(image.transpose(2, 0, 1))
        
        mask_pil = Image.open(mask_path).convert('RGB')
        mask_pil = mask_pil.resize((PROCESSING_WIDTH, PROCESSING_HEIGHT), Image.NEAREST)
        mask_array = np.array(mask_pil)
        
        mask_tensor = torch.from_numpy(rgb_to_mask(mask_array, CLASS_DICT)).long()
        
        return image, mask_tensor