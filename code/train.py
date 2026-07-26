import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import os
from config import (
    NUM_EPOCHS, BATCH_SIZE, LEARNING_RATE, DEVICE, PROCESSING_WIDTH, PROCESSING_HEIGHT
)
from model import UNet
from dataset import GrazDataset
from utils import timer_decorator

@timer_decorator
def train_epoch(model, train_loader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    
    for images, masks in train_loader:
        images = images.to(device)
        masks = masks.to(device, dtype=torch.long)
        
        optimizer.zero_grad()
        
        outputs = model(images)
        loss = criterion(outputs, masks)
        
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
    
    avg_loss = total_loss / len(train_loader)
    return avg_loss

@timer_decorator
def validate(model, val_loader, criterion, device):
    model.eval()
    total_loss = 0.0
    
    with torch.no_grad():
        for images, masks in val_loader:
            images = images.to(device)
            masks = masks.to(device, dtype=torch.long)
            
            outputs = model(images)
            loss = criterion(outputs, masks)
            
            total_loss += loss.item()
    
    avg_loss = total_loss / len(val_loader)
    return avg_loss

def train():
    device = torch.device(DEVICE)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    dataset_root = project_root
    
    print(f"Dataset root: {dataset_root}")
    
    train_dataset = GrazDataset(dataset_root, split="train")
    val_dataset = GrazDataset(dataset_root, split="val")
    
    print(f"Training samples: {len(train_dataset)}, Validation samples: {len(val_dataset)}")
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    
    model = UNet(in_channels=3).to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    best_val_loss = float('inf')
    
    for epoch in range(NUM_EPOCHS):
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss = validate(model, val_loader, criterion, device)
        
        print(f"Epoch [{epoch+1}/{NUM_EPOCHS}] Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), os.path.join(script_dir, "best_model.pth"))
            print(f"Model saved with validation loss: {best_val_loss:.4f}")

if __name__ == "__main__":
    train()