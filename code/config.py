import torch

PACKAGE_WIDTH = 15
PACKAGE_HEIGHT = 15

ANGLE_START = 0
ANGLE_END = 179
ANGLE_STEP = 10

WEIGHT_DISTANCE = 0.4
WEIGHT_ROUGHNESS = 0.2
WEIGHT_SEMANTIC = 0.4

DISTANCE_NORMALIZATION = 1000.0
ROUGHNESS_NORMALIZATION = 0.15

SAFE_CLASSES = [1, 3, 4]

TERRAIN_MAPPING_DICT = {
    1: "Pavement",
    3: "Grass",
    4: "Dirt"
}

DEPTH_MODEL_ID = "MiDaS_small"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

PROCESSING_WIDTH = 256
PROCESSING_HEIGHT = 256

MIN_CONTOUR_AREA = 10
INTERIOR_GRID_SIZE = 15
PLACEMENT_GRID_STEP = 20
MAX_SLOPE = 0.15

MORPH_KERNEL_SIZE = 5
MORPH_ITERATIONS = 2

CLASS_DICT = {
    0: (0, 0, 0),
    1: (128, 64, 128),
    2: (130, 76, 0),
    3: (0, 102, 0),
    4: (112, 103, 87),
    5: (28, 42, 168),
    6: (48, 41, 30),
    7: (0, 50, 89),
    8: (107, 142, 35),
    9: (70, 70, 70),
    10: (102, 102, 156),
    11: (254, 228, 12),
    12: (254, 148, 12),
    13: (190, 153, 153),
    14: (153, 153, 153),
    15: (255, 22, 96),
    16: (102, 51, 0),
    17: (9, 143, 150),
    18: (119, 11, 32),
    19: (51, 51, 0),
    20: (190, 250, 190),
    21: (112, 150, 146),
    22: (2, 135, 115),
    23: (255, 0, 0),
}

RGB_TO_CLASS = {v: k for k, v in CLASS_DICT.items()}

NUM_CLASSES = 24
NUM_EPOCHS = 25
BATCH_SIZE = 4
LEARNING_RATE = 0.001
TRAIN_VAL_SPLIT = 0.8
