import numpy as np
import cv2
from config import (
    SAFE_CLASSES, ANGLE_START, ANGLE_END, ANGLE_STEP,
    WEIGHT_DISTANCE, WEIGHT_ROUGHNESS, MAX_SLOPE,
    MORPH_KERNEL_SIZE, MORPH_ITERATIONS, MIN_CONTOUR_AREA,
    INTERIOR_GRID_SIZE, PLACEMENT_GRID_STEP, PACKAGE_WIDTH, PACKAGE_HEIGHT,
    DISTANCE_NORMALIZATION, ROUGHNESS_NORMALIZATION
)


def build_safe_mask(segmentation_map):
    safe_mask = np.zeros_like(segmentation_map, dtype=np.uint8)
    
    for safe_class in SAFE_CLASSES:
        safe_mask[segmentation_map == safe_class] = 255
    
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (MORPH_KERNEL_SIZE, MORPH_KERNEL_SIZE))
    safe_mask = cv2.morphologyEx(safe_mask, cv2.MORPH_CLOSE, kernel, iterations=MORPH_ITERATIONS)
    safe_mask = cv2.morphologyEx(safe_mask, cv2.MORPH_OPEN, kernel, iterations=MORPH_ITERATIONS)
    
    return safe_mask


def get_box_corners(cx, cy, width, height, angle_deg):
    angle_rad = np.deg2rad(angle_deg)
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)
    
    hw = width / 2.0
    hh = height / 2.0
    
    corners_local = np.array([
        [-hw, -hh],
        [hw, -hh],
        [hw, hh],
        [-hw, hh]
    ])
    
    rotation_matrix = np.array([
        [cos_a, -sin_a],
        [sin_a, cos_a]
    ])
    
    corners_rotated = corners_local @ rotation_matrix.T
    
    corners_global = corners_rotated + np.array([cx, cy])
    
    return corners_global


def get_box_interior_points(cx, cy, width, height, angle_deg):
    angle_rad = np.deg2rad(angle_deg)
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)
    
    hw = width / 2.0
    hh = height / 2.0
    
    points = []
    step = max(1.0, float(INTERIOR_GRID_SIZE))
    
    num_x = int(hw / step)
    num_y = int(hh / step)
    
    for i in range(-num_x, num_x + 1):
        for j in range(-num_y, num_y + 1):
            lx = i * step
            ly = j * step
            gx = lx * cos_a - ly * sin_a + cx
            gy = lx * sin_a + ly * cos_a + cy
            points.append((int(gx), int(gy)))
            
    if not points:
        points.append((int(cx), int(cy)))
        
    return points


def calculate_roughness(slope_map, interior_points):
    if len(interior_points) < 2 or slope_map is None:
        return 0.0

    roughness_values = []
    for x, y in interior_points:
        x = max(0, min(int(x), slope_map.shape[1] - 1))
        y = max(0, min(int(y), slope_map.shape[0] - 1))
        roughness_values.append(slope_map[y, x])

    if roughness_values:
        return float(np.mean(roughness_values))
    return 0.0


from semantic_brain import classify_terrain_from_mask
from knowledge_graph import get_semantic_penalty
from config import WEIGHT_SEMANTIC


def find_candidate_placements(safe_mask, depth_map, target_xy, segmentation_map=None, active_factors=None):
    h, w = safe_mask.shape
    target_x, target_y = target_xy
    
    if depth_map is not None:
        depth_float = depth_map.astype(np.float32) / 255.0
        sobelx = cv2.Sobel(depth_float, cv2.CV_32F, 1, 0, ksize=3)
        sobely = cv2.Sobel(depth_float, cv2.CV_32F, 0, 1, ksize=3)
        slope_map = np.sqrt(sobelx**2 + sobely**2)
    else:
        slope_map = None

    contours, _ = cv2.findContours(safe_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    candidates = []
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < MIN_CONTOUR_AREA:
            continue
        
        # Calculate the centroid of this safe region
        M = cv2.moments(contour)
        if M["m00"] != 0:
            region_cx = int(M["m10"] / M["m00"])
            region_cy = int(M["m01"] / M["m00"])
        else:
            x_min, y_min, contour_w, contour_h = cv2.boundingRect(contour)
            region_cx = x_min + contour_w // 2
            region_cy = y_min + contour_h // 2
            
        # Distance penalty is based on the distance from the target to the center of the safe region
        distance_raw = np.sqrt((region_cx - target_x)**2 + (region_cy - target_y)**2)
        distance = distance_raw / DISTANCE_NORMALIZATION
        
        x_min, y_min, contour_w, contour_h = cv2.boundingRect(contour)
        x_max = x_min + contour_w
        y_max = y_min + contour_h
        
        for cx in range(x_min + PLACEMENT_GRID_STEP, x_max, PLACEMENT_GRID_STEP):
            for cy in range(y_min + PLACEMENT_GRID_STEP, y_max, PLACEMENT_GRID_STEP):
                for angle in range(ANGLE_START, ANGLE_END + 1, ANGLE_STEP):
                    corners = get_box_corners(cx, cy, PACKAGE_WIDTH, PACKAGE_HEIGHT, angle)
                    
                    x_coords = corners[:, 0]
                    y_coords = corners[:, 1]
                    
                    if (np.min(x_coords) < 0 or np.max(x_coords) >= w or
                        np.min(y_coords) < 0 or np.max(y_coords) >= h):
                        continue
                    
                    interior_points = get_box_interior_points(cx, cy, PACKAGE_WIDTH, PACKAGE_HEIGHT, angle)
                    
                    if not interior_points:
                        continue
                    
                    in_safe_zone = all(safe_mask[min(int(y), h - 1), min(int(x), w - 1)] > 0 for x, y in interior_points)
                    
                    if not in_safe_zone:
                        continue
                    
                    roughness_raw = calculate_roughness(slope_map, interior_points)
                    roughness = roughness_raw / ROUGHNESS_NORMALIZATION
                    
                    if roughness_raw > MAX_SLOPE:
                        continue

                    kg_penalty = 0.0
                    terrain_string = "Unknown"
                    
                    if segmentation_map is not None and active_factors is not None:
                        terrain_string = classify_terrain_from_mask(segmentation_map, interior_points)
                        kg_penalty = get_semantic_penalty(active_factors, terrain_string)
                    
                    cost = WEIGHT_DISTANCE * distance + WEIGHT_ROUGHNESS * roughness + WEIGHT_SEMANTIC * kg_penalty
                    
                    candidates.append({
                        'cx': cx,
                        'cy': cy,
                        'angle': angle,
                        'corners': corners,
                        'distance': distance,
                        'roughness': roughness,
                        'kg_penalty': kg_penalty,
                        'terrain': terrain_string,
                        'cost': cost
                    })
    
    candidates.sort(key=lambda x: x['cost'])
    
    return candidates
