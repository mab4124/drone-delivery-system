PROJECT STRUCTURE AND COMPONENTS

ROOT DIRECTORY (d:\aip\aitapp2)
├── code/                          # Core implementation
│   ├── main.py                   # Pipeline entry point
│   ├── model.py                  # U-Net architecture with type hints
│   ├── dataset.py                # Dataset loading with type hints
│   ├── train.py                  # Training loop
│   ├── evaluate_model.py         # Performance evaluation framework
│   ├── geometry.py               # Geometric algorithms (safe zones, optimization)
│   ├── knowledge_graph.py        # 3-layer semantic reasoning engine
│   ├── semantic_brain.py         # Semantic analysis utilities
│   ├── utils.py                  # Helper functions
│   ├── config.py                 # Global configuration parameters
│   ├── requirements.txt          # Python dependencies
│   ├── best_model.pth            # Trained model checkpoint
│   ├── mission_config.json       # Mission parameters
│   └── SYSTEM_ARCHITECTURE.md    # Detailed architecture documentation

├── tests/                         # Unit test suite
│   └── test_model.py             # Model and configuration tests

├── training_set/                  # Dataset
│   ├── images/                   # 400 training images (6000x4000)
│   └── gt/                        # Ground truth annotations
│       ├── semantic/              # Semantic labels (24 classes)
│       └── bounding_box/          # Bounding box data

├── evaluate/                      # Evaluation scripts
│   ├── eval_0642.py              # Specific evaluation
│   ├── mission_default.json      # Default mission config
│   ├── mission_fragile_valuable.json  # Alternative mission config
│   └── run_all_eval.py           # Batch evaluation

├── evaluation_results/            # Generated metrics and visualizations
│   ├── per_class_iou.png         # Per-class IoU scores
│   ├── per_class_f1.png          # Per-class F1 scores
│   ├── confusion_matrix.png      # Confusion matrix heatmap
│   └── metrics_summary.png       # Overall metrics summary

├── results/                       # Pipeline output visualizations
│   ├── segmentation/             # Segmentation maps
│   ├── depth/                    # Depth predictions
│   └── placements/               # Optimal drop zone locations

├── docs/                          # Documentation
│   ├── API_DOCUMENTATION.md      # API reference
│   ├── GETTING_STARTED.md        # Quick start guide
│   └── ARCHITECTURE_DEEP_DIVE.md # Detailed architecture

├── Dockerfile                    # Container build specification
├── docker-compose.yml            # Multi-container orchestration
├── .gitignore                    # Git ignore rules
├── ANALYSIS_COMPLETE.md          # Complete project analysis and interview guide
├── DEPLOYMENT.md                 # Deployment instructions
├── Readme.md                     # Project overview
├── SYSTEM_ARCHITECTURE.md        # System architecture explanation
├── GRAPH_EXPLANATION.md          # Knowledge graph explanation
└── GRAPH_QUICK_REFERENCE.md      # Knowledge graph quick reference

KEY MODULES

model.py
- ConvBlock: Double convolution with batch norm and ReLU
- UNet: 4-level encoder-decoder semantic segmentation architecture
- 24-class output for terrain classification
- Type hints for all functions

dataset.py
- GrazDataset: PyTorch Dataset for TU Graz Semantic Drone Dataset
- Automatic train/val split (80/20)
- Image resizing and normalization
- Type hints for all functions

main.py
- load_model: Loads pre-trained U-Net checkpoint
- load_midas: Loads Intel MiDaS depth estimation
- segment_image: Performs semantic segmentation
- get_depth_map: Estimates depth from RGB
- find_safe_zones: Identifies suitable placement areas
- Type hints for all functions

geometry.py
- build_safe_mask: Creates safe landing zones
- find_candidate_placements: Grid search optimization
- calculate_roughness: Sobel-based surface analysis
- Constraint satisfaction for mission requirements

knowledge_graph.py
- 3-layer spreading activation graph
- SOURCE_TO_PROPERTY_EDGES: Package property mapping
- PROPERTY_TO_TERRAIN_EDGES: Terrain penalty mapping
- Semantic reasoning for context-aware constraints

evaluate_model.py
- ModelEvaluator: Comprehensive evaluation framework
- Metrics: mIoU, F1, precision, recall per class
- Visualizations: Class-wise plots and confusion matrix
- CSV export for detailed analysis

train.py
- Training loop with validation
- 25 epochs, batch size 4
- CrossEntropyLoss and Adam optimizer
- Checkpoint saving and early stopping

CONFIGURATION PARAMETERS (config.py)

Model Parameters:
- NUM_CLASSES: 24 terrain types
- PROCESSING_WIDTH: 256 pixels
- PROCESSING_HEIGHT: 256 pixels
- LEARNING_RATE: 0.001

Optimization Weights:
- WEIGHT_DISTANCE: 0.4
- WEIGHT_ROUGHNESS: 0.3
- WEIGHT_SEMANTIC: 0.3

Safe Zone Classification:
- SAFE_CLASSES: [1, 3, 4] (pavement, dirt, grass)
- UNSAFE_CLASSES: [0, 2, 5] (building, water, roof)

Training Configuration:
- BATCH_SIZE: 4
- NUM_EPOCHS: 25
- DEVICE: 'cuda' or 'cpu' (auto-detected)

DEPENDENCIES

Core ML:
- torch >= 2.0.0
- torchvision >= 0.14.1
- timm (for model utilities)

Computer Vision:
- opencv-python >= 4.8.0
- Pillow >= 10.0.0

Scientific Computing:
- numpy >= 1.24.0
- scipy >= 1.10.0

Visualization:
- matplotlib >= 3.7.0
- seaborn >= 0.12.0

Testing:
- pytest >= 7.0.0
- scikit-learn >= 1.0.0

Depth Estimation:
- intel-isl/MiDaS (downloaded at runtime)

DATA FLOW

Input: Raw UAV image (6000x4000 RGB)
   |
   v
Perception Pipeline:
   - Segmentation: 24-class terrain classification
   - Depth: Relative depth from single image
   - Roughness: Sobel gradient analysis
   |
   v
Knowledge Graph:
   - Mission config: Package properties and constraints
   - Spreading activation: Layer 1 (source) -> Layer 2 (property) -> Layer 3 (terrain)
   - Output: Penalty scores (0-1) for each terrain class
   |
   v
Optimization Pipeline:
   - Safe zones: Pixels where conditions met
   - Grid search: Evaluate all candidate locations
   - Cost function: 0.4*distance + 0.3*roughness + 0.3*penalty
   |
   v
Output:
   - Optimal drop zone (x, y coordinates)
   - Confidence score
   - Visual feedback with segmentation overlay

PERFORMANCE PROFILE

Memory Usage:
- Model weights: 64 MB
- Batch processing (B=4): 2-3 GB
- Single image inference: 512 MB

Compute Requirements:
- CPU (i7, 16GB RAM): 1-2 seconds per image
- GPU (RTX 3070, 8GB VRAM): 0.3-0.5 seconds per image

Dataset Size:
- Training images: 400 (6000x4000 RGB JPEG)
- Validation images: 100
- Total disk: ~2.5 GB

Model Size:
- Uncompressed checkpoint: 64 MB
- Quantized checkpoint: 16 MB

EXTENSIBILITY POINTS

Adding New Constraints:
1. Add new source node to SOURCE_TO_PROPERTY_EDGES in knowledge_graph.py
2. Define edges to property nodes (automatic penalty propagation)
3. No code changes to optimization pipeline

Adding New Terrain Classes:
1. Retrain with additional class in training_set/gt/semantic/
2. Update NUM_CLASSES in config.py
3. Model architecture scales automatically

Hardware Acceleration:
1. GPU: Automatically uses CUDA if available
2. Quantization: Use code/quantize_model.py for INT8 inference
3. ONNX Export: Add torch.onnx.export() call

Real-time Integration:
1. Replace file loading with camera stream
2. Create async pipeline wrapper
3. Buffer frames for batch processing

Multi-modal Fusion:
1. Add thermal, LiDAR, or multispectral inputs
2. Modify dataset.py to load multiple modalities
3. Update UNet input channels and architecture

VERSION TRACKING

Current: v1.0.0
- Initial release with core functionality
- U-Net semantic segmentation
- 3-layer knowledge graph reasoning
- Comprehensive evaluation framework
- Docker containerization
- Full type hints and documentation

Planned: v1.1.0
- YOLOv8 obstacle detection
- REST API with FastAPI
- Model quantization (INT8)
- Real-time video processing

Planned: v2.0.0
- Reinforcement learning for continuous improvement
- Multi-modal sensor fusion
- Real drone hardware integration
- Trajectory planning and collision avoidance
