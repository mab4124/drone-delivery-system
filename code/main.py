from typing import Tuple, Any, Optional
import os
import torch
import cv2
import numpy as np
import matplotlib.pyplot as plt

from config import (
    PROCESSING_WIDTH, PROCESSING_HEIGHT, DEVICE, DEPTH_MODEL_ID, CLASS_DICT,
    WEIGHT_DISTANCE, WEIGHT_ROUGHNESS, WEIGHT_SEMANTIC
)
from model import UNet
from geometry import build_safe_mask, find_candidate_placements
from utils import mask_to_rgb, timer_decorator
from knowledge_graph import parse_mission_config


@timer_decorator
def load_model(model_path: str, device: torch.device) -> UNet:
    """Load pre-trained U-Net model from checkpoint.
    
    Args:
        model_path: Path to model checkpoint
        device: Device to load model on
        
    Returns:
        Loaded U-Net model in evaluation mode
    """
    model = UNet(in_channels=3).to(device)
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=device))
        print(f"Loaded model from {model_path}")
    else:
        print(f"Model not found at {model_path}, using randomly initialized weights")
    model.eval()
    return model


@timer_decorator
def load_midas(device: torch.device) -> Tuple[Any, Any]:
    """Load Intel MiDaS depth estimation model.
    
    Args:
        device: Device to load model on
        
    Returns:
        Tuple of (model, transform)
    """
    midas = torch.hub.load("intel-isl/MiDaS", DEPTH_MODEL_ID)
    midas.to(device)
    midas.eval()
    
    midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
    transform = midas_transforms.small_transform
    
    return midas, transform


@timer_decorator
def segment_image(image: np.ndarray, model: UNet, device: torch.device) -> np.ndarray:
    """Perform semantic segmentation on image.
    
    Args:
        image: Input RGB image [H x W x 3]
        model: Trained U-Net model
        device: Device to run model on
        
    Returns:
        Segmentation map [H x W]
    """
    h, w = image.shape[:2]
    
    image_resized = cv2.resize(image, (PROCESSING_WIDTH, PROCESSING_HEIGHT), interpolation=cv2.INTER_LINEAR)
    image_normalized = image_resized.astype(np.float32) / 255.0
    image_tensor = torch.from_numpy(image_normalized.transpose(2, 0, 1)).unsqueeze(0).to(device)
    
    with torch.no_grad():
        output = model(image_tensor)
        segmentation = torch.argmax(output, dim=1).squeeze(0).cpu().numpy()
    
    segmentation_full = cv2.resize(segmentation.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
    
    return segmentation_full


@timer_decorator
def get_depth_map(image, midas, transform, device):
    input_batch = transform(image).to(device)
    
    with torch.no_grad():
        depth = midas(input_batch)
        depth = torch.nn.functional.interpolate(
            depth.unsqueeze(1),
            size=image.shape[:2],
            mode="bicubic",
            align_corners=False,
        ).squeeze()
    
    depth_map = depth.cpu().numpy()
    depth_map = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min() + 1e-8) * 255.0
    depth_map = depth_map.astype(np.uint8)
    
    return depth_map


def main():
    print("\n" + "="*80)
    print("AUTONOMOUS DRONE PACKAGE SAFE DROP SYSTEM")
    print("="*80 + "\n")
    
    print("Step 1: Image Selection")
    print("-" * 40)
    image_path = input("Enter the path to the drone image (relative or absolute): ").strip()
    
    if not image_path:
        print("Error: Image path cannot be empty")
        return
    
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        return
    
    print("\nStep 2: Target Coordinate Selection")
    print("-" * 40)
    print("Enter target coordinates in 800x600 image space.")
    print("(Tip: Center is 400,300 for middle of image)")
    target_str = input("Enter target pixel coordinate as x,y: ").strip()
    
    try:
        target_x, target_y = map(int, target_str.split(","))
    except ValueError:
        print("Error: Invalid coordinate format. Expected: x,y (e.g., 400,300)")
        return
    
    if not (0 <= target_x <= 800) or not (0 <= target_y <= 600):
        print(f"Warning: Target ({target_x}, {target_y}) is outside 800x600 bounds")
    
    device = torch.device(DEVICE)
    
    print("\n" + "="*80)
    print("LOADING MODELS AND PROCESSING IMAGE")
    print("="*80 + "\n")
    
    print("Loading U-Net model...")
    model_path = os.path.join(os.path.dirname(__file__), "best_model.pth")
    model = load_model(model_path, device)
    
    print("Loading MiDaS depth estimator...")
    midas, transform = load_midas(device)
    
    print("Reading image...")
    original_image = cv2.imread(image_path)
    if original_image is None:
        print(f"Error: Could not read image {image_path}")
        return
    original_image = cv2.resize(original_image, (800, 600))
    original_image_rgb = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
    print(f"Image loaded and resized to 800x600")
    print(f"Target coordinate: ({target_x}, {target_y})")
    
    print("\nLoading mission configuration...")
    config_path = os.path.join(os.path.dirname(__file__), "mission_config.json")
    active_factors = parse_mission_config(config_path)
    print(f"Active mission factors: {active_factors}")
    
    print("\nRunning semantic segmentation (U-Net)...")
    segmentation_map = segment_image(original_image_rgb, model, device)
    
    print("Estimating depth map (MiDaS)...")
    depth_map = get_depth_map(original_image_rgb, midas, transform, device)
    
    print("Building safe zone mask...")
    safe_mask = build_safe_mask(segmentation_map)
    
    print("Finding candidate placements with semantic reasoning...")
    candidates = find_candidate_placements(
        safe_mask, depth_map, (target_x, target_y),
        segmentation_map=segmentation_map,
        active_factors=active_factors
    )
    
    print("\n" + "="*80)
    print("CANDIDATE PLACEMENTS (Top 5)")
    print("="*80)
    
    for i, candidate in enumerate(candidates[:5]):
        print(f"\nCandidate {i+1}:")
        print(f"  Position: ({candidate['cx']}, {candidate['cy']})")
        print(f"  Angle: {candidate['angle']}°")
        print(f"  Terrain: {candidate.get('terrain', 'Unknown')}")
        print(f"  Distance from target: {candidate['distance']:.2f} pixels")
        print(f"  Roughness (slope): {candidate['roughness']:.4f}")
        print(f"  Semantic Penalty: {candidate.get('kg_penalty', 0.0):.4f}")
        print(f"  Total Cost: {candidate['cost']:.4f}")
        print(f"    Cost Breakdown:")
        print(f"      Distance ({WEIGHT_DISTANCE}): {WEIGHT_DISTANCE * candidate['distance']:.4f}")
        print(f"      Roughness ({WEIGHT_ROUGHNESS}): {WEIGHT_ROUGHNESS * candidate['roughness']:.4f}")
        print(f"      Semantic ({WEIGHT_SEMANTIC}): {WEIGHT_SEMANTIC * candidate.get('kg_penalty', 0.0):.4f}")
    
    print("\n" + "="*80)
    
    if not candidates:
        print("No valid placements found!")
        return
    
    best = candidates[0]
    cx, cy = best['cx'], best['cy']
    angle = best['angle']
    corners = best['corners']
    terrain = best.get('terrain', 'Unknown')
    kg_penalty = best.get('kg_penalty', 0.0)
    
    output_image = original_image_rgb.copy()
    
    corners_int = corners.astype(int)
    cv2.polylines(output_image, [corners_int], isClosed=True, color=(0, 255, 0), thickness=2)
    
    cv2.circle(output_image, (target_x, target_y), radius=5, color=(0, 0, 255), thickness=-1)
    
    cv2.putText(output_image, f"Best: ({cx},{cy}) @ {angle}deg | {terrain}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(output_image, f"Cost: {best['cost']:.4f}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    print("\n" + "="*80)
    print("SAVING INDIVIDUAL IMAGES")
    print("="*80 + "\n")
    
    # Save 5 individual images
    img1_bgr = cv2.cvtColor(original_image_rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite("image_1_original.jpg", img1_bgr)
    print("✓ Saved: image_1_original.jpg")
    
    segmentation_rgb = mask_to_rgb(segmentation_map, CLASS_DICT)
    img2_bgr = cv2.cvtColor(segmentation_rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite("image_2_segmentation.jpg", img2_bgr)
    print("✓ Saved: image_2_segmentation.jpg")
    
    depth_colored = cv2.applyColorMap(depth_map, cv2.COLORMAP_VIRIDIS)
    cv2.imwrite("image_3_depth.jpg", depth_colored)
    print("✓ Saved: image_3_depth.jpg")
    
    img4_bgr = cv2.cvtColor(cv2.cvtColor(safe_mask, cv2.COLOR_GRAY2BGR), cv2.COLOR_RGB2BGR)
    cv2.imwrite("image_4_safe_mask.jpg", img4_bgr)
    print("✓ Saved: image_4_safe_mask.jpg")
    
    img5_bgr = cv2.cvtColor(output_image, cv2.COLOR_RGB2BGR)
    cv2.imwrite("image_5_best_placement.jpg", img5_bgr)
    print("✓ Saved: image_5_best_placement.jpg")
    
    output_filename = "image_5_best_placement.jpg"
    print(f"\nResult saved to: {output_filename}")
    
    print("\n" + "="*80)
    print("GENERATING MATPLOTLIB ANALYSIS")
    print("="*80 + "\n")
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    axes[0, 0].imshow(original_image_rgb)
    axes[0, 0].set_title("Original Image (800x600)")
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(segmentation_rgb)
    axes[0, 1].set_title("Semantic Segmentation (U-Net)")
    axes[0, 1].axis('off')
    
    axes[0, 2].imshow(depth_map, cmap='viridis')
    axes[0, 2].set_title("Depth Map (MiDaS)")
    axes[0, 2].axis('off')
    
    axes[1, 0].imshow(safe_mask, cmap='gray')
    axes[1, 0].set_title("Safe Zone Mask")
    axes[1, 0].axis('off')
    
    axes[1, 1].imshow(output_image)
    axes[1, 1].plot(target_x, target_y, 'r*', markersize=15)
    axes[1, 1].set_title(f"Best Placement (Cost: {best['cost']:.4f})")
    axes[1, 1].axis('off')
    
    axes[1, 2].axis('off')
    cost_text = f"BEST PLACEMENT (SEMANTIC REASONING)\n\n"
    cost_text += f"Position: ({cx}, {cy})\n"
    cost_text += f"Angle: {angle}°\n"
    cost_text += f"Terrain: {terrain}\n"
    cost_text += f"Distance: {best['distance']:.2f}px\n"
    cost_text += f"Roughness: {best['roughness']:.4f}\n"
    cost_text += f"Semantic Penalty: {kg_penalty:.4f}\n"
    cost_text += f"\nMission Factors:\n"
    cost_text += f"{', '.join(active_factors) if active_factors else 'None'}\n"
    cost_text += f"\nCost Breakdown:\n"
    cost_text += f"Distance ({WEIGHT_DISTANCE}): {WEIGHT_DISTANCE * best['distance']:.4f}\n"
    cost_text += f"Roughness ({WEIGHT_ROUGHNESS}): {WEIGHT_ROUGHNESS * best['roughness']:.4f}\n"
    cost_text += f"Semantic ({WEIGHT_SEMANTIC}): {WEIGHT_SEMANTIC * kg_penalty:.4f}\n"
    cost_text += f"TOTAL: {best['cost']:.4f}"
    axes[1, 2].text(0.05, 0.5, cost_text, fontsize=10, family='monospace',
                    verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    analysis_filename = "image_6_analysis.jpg"
    plt.savefig(analysis_filename, dpi=100, bbox_inches='tight')
    print(f"✓ Saved: {analysis_filename}")
    
    print("\n" + "="*80)
    print("MISSION SUMMARY")
    print("="*80)
    print(f"Image: {image_path}")
    print(f"Target: ({target_x}, {target_y})")
    print(f"Mission Factors: {active_factors}")
    print(f"\nBest Placement Found:")
    print(f"  Position: ({cx}, {cy})")
    print(f"  Rotation: {angle}°")
    print(f"  Terrain Type: {terrain}")
    print(f"  Total Cost: {best['cost']:.4f}")
    print("\n" + "="*80)
    print("OUTPUT FILES GENERATED:")
    print("="*80)
    print("✓ image_1_original.jpg          - Original input image")
    print("✓ image_2_segmentation.jpg      - U-Net semantic segmentation")
    print("✓ image_3_depth.jpg             - MiDaS depth estimation")
    print("✓ image_4_safe_mask.jpg         - Safe landing zone mask")
    print("✓ image_5_best_placement.jpg    - Best candidate with annotations")
    print("✓ image_6_analysis.jpg          - Complete analysis grid (matplotlib)")
    print("="*80 + "\n")
    
    print("Displaying matplotlib analysis...")
    plt.show()


if __name__ == "__main__":
    main()
