# Autonomous Drone Package Safe Drop System

## Project Overview
The Autonomous Drone Package Safe Drop System is a sophisticated computer vision and semantic reasoning pipeline designed for UAV (Unmanned Aerial Vehicle) package delivery. The system evaluates drone imagery to identify the optimal landing and package drop zones by analyzing terrain semantics, depth/surface roughness, distance to the target, and context-aware mission parameters (e.g., package fragility, environmental conditions). 

By integrating deep learning-based perception with a novel 3-layer graph-based knowledge engine, the system moves beyond simple rule-based heuristics to provide adaptive, emergent decision-making for safe payload delivery under varying constraints.

## Core Features
- **Semantic Segmentation:** Utilizes a custom PyTorch U-Net architecture to segment aerial imagery into 24 distinct classes, identifying safe terrain types (pavement, grass, dirt).
- **Monocular Depth Estimation:** Integrates Intel's MiDaS model to generate depth maps from 2D images, enabling the calculation of surface slope and roughness.
- **Graph-Based Semantic Reasoning:** Employs a 3-layer spreading activation knowledge graph that dynamically penalizes terrain types based on mission-specific variables (e.g., penalizing "Hard" pavement for "Fragile" packages, or "Slippery" grass during "Rain").
- **Multi-Objective Cost Optimization:** Evaluates thousands of candidate drop orientations and positions using a weighted cost function combining distance, roughness, and semantic penalty.
- **Comprehensive Analysis Visualization:** Automatically generates matplotlib summaries and diagnostic images highlighting the reasoning process and optimal drop location.

## System Architecture

The system is divided into three primary pipelines:

### 1. Perception Pipeline (Computer Vision)
- **U-Net Segmentation (`model.py`, `train.py`, `dataset.py`)**: A fully convolutional U-Net model trained on a custom drone dataset (GrazDataset) to perform pixel-wise classification of the environment.
- **Depth & Roughness (`geometry.py`)**: Uses the MiDaS depth model to estimate 3D structures. Sobel filters are applied to the depth map to calculate a gradient (slope) map, ensuring packages are not dropped on steep or uneven surfaces.

### 2. Semantic Reasoning Engine (`knowledge_graph.py`)
Replaces rigid `if/else` logic with a dynamic, graph-based spreading activation algorithm:
- **Layer 1: Source Nodes**: Active mission factors parsed from `mission_config.json` (e.g., Fragile, Valuable, Heavy, Biohazard, Rain, Snow, Night).
- **Layer 2: Property Nodes**: Abstract physical properties that inherit activation from source nodes (e.g., Hard, Visible, Wet, Slippery, Contaminated).
- **Layer 3: Terrain Nodes**: Physical landing zones (e.g., Pavement, Grass, Dirt, Water).
*Activation spreads from Source -> Property -> Terrain, generating a continuous penalty score (0.0 to 1.0) for each terrain type based on current mission constraints.*

### 3. Optimization & Planning (`geometry.py`, `main.py`)
Grid-search optimization across the identified safe zones. For each candidate location and rotation angle, the system calculates a cost:
`Cost = (0.4 * Distance) + (0.2 * Roughness) + (0.4 * Semantic Penalty)`
The candidate with the lowest cost is selected as the optimal drop zone.

## Codebase Structure
- `main.py`: The entry point. Orchestrates the loading of models, image processing, candidate search, and visualization.
- `model.py` / `dataset.py` / `train.py`: PyTorch definitions for the U-Net segmentation model, data loading pipeline, and training loop.
- `geometry.py`: Core algorithms for bounding box transformations, safe mask morphological operations, roughness calculation, and the candidate grid-search.
- `knowledge_graph.py`: The 3-layer spreading activation algorithm and terrain penalty calculator.
- `semantic_brain.py`: Helper functions to map segmentation classes to terrain strings for the knowledge graph.
- `config.py`: Global configuration parameters, hyper-parameters, weights, and class mappings.
- `utils.py`: Decorators for performance profiling (timers) and mask-to-RGB conversion utilities.
- `mission_config.json`: JSON configuration for the current mission's parameters (package type, conditions).

## Usage Instructions

### Running the Inference Pipeline
1. Ensure your mission parameters are set in `mission_config.json`.
2. Run the main script:
   ```bash
   python main.py
   ```
3. When prompted, enter the path to the drone image (e.g., `test_image.jpg`).
4. Enter the target delivery coordinates (e.g., `400,300`).
5. The system will process the image and output 6 diagnostic files, including `image_5_best_placement.jpg` (the final decision) and `image_6_analysis.jpg` (a matplotlib grid breakdown).

### Training the Segmentation Model
To retrain the U-Net model on the dataset:
```bash
python train.py
```
This will output a `best_model.pth` file to be used by `main.py`.

## Example Mission Configuration
`mission_config.json`:
```json
{
  "mission_id": "OP-DELTA-9",
  "package": {
    "type": "medical_vials",
    "heavy": false,
    "fragile": true,
    "valuable": true,
    "biohazard": false
  }
}
```
*In this scenario, the reasoning engine will penalize Pavement (too Hard for fragile vials) and penalize highly visible areas (Valuable package), forcing the algorithm to find a soft, concealed drop zone like Grass or Dirt.*
