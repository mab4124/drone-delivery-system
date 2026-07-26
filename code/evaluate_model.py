import torch
import torch.nn as nn
import cv2
import numpy as np
from sklearn.metrics import confusion_matrix, f1_score
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
from torch.utils.data import DataLoader
from pathlib import Path
import json

from config import PROCESSING_WIDTH, PROCESSING_HEIGHT, DEVICE, NUM_CLASSES
from model import UNet
from dataset import GrazDataset


class ModelEvaluator:
    """Evaluates semantic segmentation model performance."""
    
    def __init__(self, model_path: str, device: str = "cpu") -> None:
        """Initialize evaluator with trained model.
        
        Args:
            model_path: Path to saved model weights
            device: Device to use ('cpu' or 'cuda')
        """
        self.device = torch.device(device)
        self.model = UNet(in_channels=3).to(self.device)
        
        model_file = Path(model_path)
        if model_file.exists():
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()
    
    def evaluate(self, dataset_root: str, split: str = "val") -> dict:
        """Evaluate model on validation/test set.
        
        Args:
            dataset_root: Root directory of dataset
            split: 'val' or 'test' split
            
        Returns:
            Dictionary containing evaluation metrics
        """
        dataset = GrazDataset(dataset_root, split=split)
        dataloader = DataLoader(dataset, batch_size=1, shuffle=False)
        
        all_preds = []
        all_gts = []
        
        with torch.no_grad():
            for images, masks in tqdm(dataloader, desc=f"Evaluating on {split} set"):
                images = images.to(self.device)
                outputs = self.model(images)
                predictions = torch.argmax(outputs, dim=1).cpu().numpy()
                all_preds.append(predictions.flatten())
                all_gts.append(masks.numpy().flatten())
        
        all_preds = np.concatenate(all_preds)
        all_gts = np.concatenate(all_gts)
        
        return self._calculate_metrics(all_preds, all_gts)
    
    def _calculate_metrics(self, predictions: np.ndarray, ground_truths: np.ndarray) -> dict:
        """Calculate comprehensive evaluation metrics.
        
        Args:
            predictions: Model predictions [N]
            ground_truths: Ground truth labels [N]
            
        Returns:
            Dictionary with all metrics
        """
        results = {}
        
        # Overall accuracy
        overall_acc = np.sum(predictions == ground_truths) / len(predictions)
        results['overall_accuracy'] = float(overall_acc)
        
        # Per-class metrics
        results['per_class_iou'] = {}
        results['per_class_f1'] = {}
        results['per_class_precision'] = {}
        results['per_class_recall'] = {}
        
        for class_id in range(NUM_CLASSES):
            # IoU
            intersection = np.sum((predictions == class_id) & (ground_truths == class_id))
            union = np.sum((predictions == class_id) | (ground_truths == class_id))
            iou = intersection / (union + 1e-6)
            results['per_class_iou'][class_id] = float(iou)
            
            # F1, Precision, Recall
            tp = np.sum((predictions == class_id) & (ground_truths == class_id))
            fp = np.sum((predictions == class_id) & (ground_truths != class_id))
            fn = np.sum((predictions != class_id) & (ground_truths == class_id))
            
            precision = tp / (tp + fp + 1e-6)
            recall = tp / (tp + fn + 1e-6)
            f1 = 2 * (precision * recall) / (precision + recall + 1e-6)
            
            results['per_class_precision'][class_id] = float(precision)
            results['per_class_recall'][class_id] = float(recall)
            results['per_class_f1'][class_id] = float(f1)
        
        # Mean metrics
        results['mean_iou'] = float(np.mean(list(results['per_class_iou'].values())))
        results['mean_f1'] = float(np.mean(list(results['per_class_f1'].values())))
        results['mean_precision'] = float(np.mean(list(results['per_class_precision'].values())))
        results['mean_recall'] = float(np.mean(list(results['per_class_recall'].values())))
        
        # Confusion matrix
        results['confusion_matrix'] = confusion_matrix(
            ground_truths, predictions, labels=range(NUM_CLASSES)
        ).tolist()
        
        return results
    
    def visualize_results(self, results: dict, output_dir: str = "evaluation_results") -> None:
        """Generate visualization plots.
        
        Args:
            results: Results dictionary from evaluate()
            output_dir: Directory to save visualizations
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Plot 1: Per-class IoU
        fig, ax = plt.subplots(figsize=(14, 6))
        classes = [str(c) for c in range(NUM_CLASSES)]
        ious = [results['per_class_iou'].get(str(i), results['per_class_iou'].get(i, 0)) 
                for i in range(NUM_CLASSES)]
        colors = ['green' if x > 0.6 else 'orange' if x > 0.4 else 'red' for x in ious]
        ax.bar(classes, ious, color=colors)
        ax.set_ylabel('IoU Score', fontsize=12)
        ax.set_title(f"Per-Class IoU (Mean: {results['mean_iou']:.4f})", fontsize=14, fontweight='bold')
        ax.axhline(y=results['mean_iou'], color='blue', linestyle='--', label='Mean IoU')
        ax.set_ylim([0, 1])
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path / 'per_class_iou.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 2: Per-class F1
        fig, ax = plt.subplots(figsize=(14, 6))
        f1s = [results['per_class_f1'].get(str(i), results['per_class_f1'].get(i, 0)) 
               for i in range(NUM_CLASSES)]
        colors = ['green' if x > 0.6 else 'orange' if x > 0.4 else 'red' for x in f1s]
        ax.bar(classes, f1s, color=colors)
        ax.set_ylabel('F1 Score', fontsize=12)
        ax.set_title(f"Per-Class F1 (Mean: {results['mean_f1']:.4f})", fontsize=14, fontweight='bold')
        ax.axhline(y=results['mean_f1'], color='blue', linestyle='--', label='Mean F1')
        ax.set_ylim([0, 1])
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path / 'per_class_f1.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 3: Confusion Matrix
        fig, ax = plt.subplots(figsize=(12, 10))
        cm = np.array(results['confusion_matrix'])
        sns.heatmap(cm, annot=False, fmt='d', cmap='Blues', ax=ax, cbar_kws={'label': 'Count'})
        ax.set_title('Confusion Matrix', fontsize=14, fontweight='bold')
        ax.set_xlabel('Predicted Class')
        ax.set_ylabel('Ground Truth Class')
        plt.tight_layout()
        plt.savefig(output_path / 'confusion_matrix.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 4: Metrics Comparison
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        metrics = [results['mean_iou'], results['mean_f1'], 
                   results['mean_precision'], results['mean_recall']]
        metric_names = ['Mean IoU', 'Mean F1', 'Mean Precision', 'Mean Recall']
        colors_bar = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        
        for idx, (ax, metric, name, color) in enumerate(zip(axes.flat, metrics, metric_names, colors_bar)):
            ax.barh([name], [metric], color=color)
            ax.set_xlim([0, 1])
            ax.text(metric + 0.02, 0, f'{metric:.4f}', va='center', fontweight='bold')
            ax.set_xlabel('Score')
            ax.set_title(name, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_path / 'metrics_summary.png', dpi=300, bbox_inches='tight')
        plt.close()


def save_evaluation_report(results: dict, output_file: str = "EVALUATION_RESULTS.md") -> None:
    """Save evaluation results to markdown report.
    
    Args:
        results: Results dictionary from evaluate()
        output_file: Output markdown file path
    """
    with open(output_file, 'w') as f:
        f.write("# Evaluation Results\n\n")
        f.write("## Overall Metrics\n\n")
        f.write(f"- Overall Accuracy: {results['overall_accuracy']:.4f}\n")
        f.write(f"- Mean IoU: {results['mean_iou']:.4f}\n")
        f.write(f"- Mean F1: {results['mean_f1']:.4f}\n")
        f.write(f"- Mean Precision: {results['mean_precision']:.4f}\n")
        f.write(f"- Mean Recall: {results['mean_recall']:.4f}\n\n")
        
        f.write("## Per-Class Metrics\n\n")
        f.write("| Class ID | IoU | F1 | Precision | Recall |\n")
        f.write("|----------|-----|----|-----------|---------|\n")
        
        for class_id in range(NUM_CLASSES):
            iou = results['per_class_iou'].get(str(class_id), results['per_class_iou'].get(class_id, 0))
            f1 = results['per_class_f1'].get(str(class_id), results['per_class_f1'].get(class_id, 0))
            prec = results['per_class_precision'].get(str(class_id), results['per_class_precision'].get(class_id, 0))
            rec = results['per_class_recall'].get(str(class_id), results['per_class_recall'].get(class_id, 0))
            f.write(f"| {class_id} | {iou:.4f} | {f1:.4f} | {prec:.4f} | {rec:.4f} |\n")
        
        f.write("\n## Visualizations\n\n")
        f.write("- Per-class IoU: `per_class_iou.png`\n")
        f.write("- Per-class F1: `per_class_f1.png`\n")
        f.write("- Confusion Matrix: `confusion_matrix.png`\n")
        f.write("- Metrics Summary: `metrics_summary.png`\n")


if __name__ == "__main__":
    dataset_root = str(Path(__file__).parent.parent)
    model_path = str(Path(__file__).parent / "best_model.pth")
    
    print("Starting model evaluation...")
    evaluator = ModelEvaluator(model_path, device="cuda" if torch.cuda.is_available() else "cpu")
    results = evaluator.evaluate(dataset_root, split="val")
    
    print(f"\n{'='*60}")
    print("EVALUATION RESULTS")
    print(f"{'='*60}")
    print(f"Overall Accuracy: {results['overall_accuracy']:.4f}")
    print(f"Mean IoU: {results['mean_iou']:.4f}")
    print(f"Mean F1: {results['mean_f1']:.4f}")
    print(f"Mean Precision: {results['mean_precision']:.4f}")
    print(f"Mean Recall: {results['mean_recall']:.4f}")
    print(f"{'='*60}\n")
    
    evaluator.visualize_results(results)
    save_evaluation_report(results)
    
    print("Evaluation complete!")
    print("Check evaluation_results/ for visualizations")
    print("Check EVALUATION_RESULTS.md for detailed report")
