Deployment and API Documentation

DOCKER SETUP

Prerequisites:
- Docker Desktop installed and running
- Project folder d:\aip\aitapp2

Building the Docker Image:
cd d:\aip\aitapp2
docker build -t drone-delivery:latest .

Running the Container:
docker run --name drone-delivery -v %cd%\results:/app/results drone-delivery:latest

Using Docker Compose (Recommended):
cd d:\aip\aitapp2
docker-compose up --build

Stopping the Container:
docker-compose down

Viewing Logs:
docker logs drone-delivery

Accessing Results:
All outputs are mounted to the results/ folder on your host machine.

RUNNING EVALUATION

Inside Container:
docker run --rm -v %cd%\evaluation_results:/app/evaluation_results drone-delivery:latest python code/evaluate_model.py

On Host Machine (Local):
cd d:\aip\aitapp2
python code/evaluate_model.py

Expected Outputs:
- EVALUATION_RESULTS.md: Detailed metrics report
- evaluation_results/per_class_iou.png: IoU visualization
- evaluation_results/per_class_f1.png: F1 score visualization
- evaluation_results/confusion_matrix.png: Confusion matrix heatmap
- evaluation_results/metrics_summary.png: Summary metrics bar chart

RUNNING TESTS

Local Testing:
cd d:\aip\aitapp2
pytest tests/ -v

Docker Testing:
docker run --rm drone-delivery:latest pytest tests/ -v

Test Coverage:
- test_model_creation: U-Net initialization
- test_model_forward_pass: Forward pass with correct output shape
- test_model_output_range: Valid tensor values
- test_model_different_batch_sizes: Variable batch sizes
- test_model_gradients: Gradient computation
- test_model_cpu_device: CPU execution
- test_model_gpu_device: GPU execution (if available)
- test_model_eval_mode: Evaluation mode
- test_segmentation_argmax: Class prediction
- test_segmentation_class_range: Valid class indices
- test_config_imports: Configuration loading
- test_config_values_reasonable: Configuration validity

PERFORMANCE METRICS

Expected Model Performance:
- Overall Accuracy: 82-88%
- Mean IoU: 0.65-0.72
- Mean F1: 0.60-0.70
- Inference Time: 150-200ms per image

System Performance:
- Segmentation: 150-200ms
- Depth Estimation: 200-300ms
- Optimization: 100-200ms
- Total: 1-2 seconds per image

GPU Acceleration (if available):
- Segmentation: 50-100ms
- Depth Estimation: 100-150ms
- Optimization: 50-100ms
- Total: 300-500ms per image

TROUBLESHOOTING

Out of Memory:
Reduce batch size in config.py (BATCH_SIZE = 1 or 2)

CUDA Not Found:
Model automatically falls back to CPU
Install CUDA 11.8+ for GPU acceleration

Model File Not Found:
Code automatically uses random weights for testing
Run training with: python code/train.py

Missing Dependencies:
docker build --no-cache -t drone-delivery:latest .
pip install -r code/requirements.txt

File Permissions in Docker:
docker run --user root -v %cd%:/app drone-delivery:latest python code/main.py
