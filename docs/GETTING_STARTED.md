QUICK START GUIDE

INSTALLATION

1. Clone Repository:
git clone https://github.com/mab4124/drone-delivery-system
cd drone-delivery-system

2. Setup Virtual Environment (Local):
python -m venv .venv
.venv\Scripts\activate

3. Install Dependencies:
pip install -r code/requirements.txt

4. Verify Installation:
python -c "import torch; print('PyTorch version:', torch.__version__)"

RUNNING THE SYSTEM

Option 1: Docker (Recommended)
docker-compose up --build

Option 2: Local Python
cd d:\aip\aitapp2
python code/main.py

Option 3: With Custom Image
python code/main.py --image path/to/image.jpg

EVALUATION

Generate Performance Metrics:
python code/evaluate_model.py

This creates:
- EVALUATION_RESULTS.md: Detailed metrics
- evaluation_results/: Visualization plots
- per_class_iou.png: Class-wise IoU scores
- confusion_matrix.png: Full confusion matrix

TESTING

Run Unit Tests:
pytest tests/ -v

Run Single Test:
pytest tests/test_model.py::TestUNetModel::test_model_forward_pass -v

COMMON TASKS

Train Model:
python code/train.py --epochs 25 --batch-size 4

Segment Single Image:
from code.model import UNet
import torch
model = UNet(in_channels=3)
# Load weights and run segmentation

Get Depth Map:
from code.main import load_midas, get_depth_map
midas, transform = load_midas('cpu')
depth = get_depth_map(image, midas, transform, 'cpu')

Find Drop Zone:
from code.geometry import find_candidate_placements, build_safe_mask
safe_mask = build_safe_mask(segmentation, depth)
placements = find_candidate_placements(segmentation, depth, target=(400, 300))

TROUBLESHOOTING

Error: CUDA out of memory
Solution: Reduce batch size in config.py or use CPU mode

Error: Model file not found
Solution: Model weights are optional, system uses random initialization for testing

Error: Import errors
Solution: pip install -r code/requirements.txt --upgrade

Docker Build Fails:
docker build --no-cache -t drone-delivery:latest .

Need Help?
Read docs/PROJECT_STRUCTURE.md for detailed component information
Read ANALYSIS_COMPLETE.md for architecture and design decisions
Check DEPLOYMENT.md for containerization details

NEXT STEPS

1. Review ANALYSIS_COMPLETE.md to understand the system
2. Run evaluation to generate performance metrics
3. Explore code/ directory to understand implementation
4. Modify config.py to test different mission scenarios
5. Train on custom dataset following code/train.py

SYSTEM REQUIREMENTS

Minimum:
- Python 3.8+
- 8 GB RAM
- 50 GB disk space (including training data)
- CPU with 4+ cores

Recommended:
- Python 3.10
- 16 GB RAM
- GPU with 6+ GB VRAM (NVIDIA/AMD with CUDA/ROCm)
- SSD with 100 GB free space

Docker:
- Docker Desktop 4.0+
- 20 GB disk space for images
- 8 GB RAM allocation

SUPPORTED PLATFORMS

- Windows 10/11
- Linux (Ubuntu 20.04+)
- macOS (10.15+)

GPU Support:
- NVIDIA CUDA 11.8+
- AMD ROCm 5.0+
- Intel Arc (experimental)

API ENDPOINTS (Coming in v1.1.0)

POST /predict
- Input: Image file
- Output: Drop zone coordinates and confidence
- Status: In development

GET /health
- Status: System health check
- Status: In development

GET /metrics
- Output: Performance metrics
- Status: In development
