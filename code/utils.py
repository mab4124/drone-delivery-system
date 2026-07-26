import time
import functools
import numpy as np

def rgb_to_mask(img_array, color_dict):
    h, w = img_array.shape[:2]
    mask = np.zeros((h, w), dtype=np.int64)
    
    for class_idx, rgb_color in color_dict.items():
        r, g, b = rgb_color
        matches = np.all(img_array[:, :, :3] == [r, g, b], axis=2)
        mask[matches] = class_idx
        
    return mask

def mask_to_rgb(mask_array, color_dict):
    h, w = mask_array.shape
    rgb_image = np.zeros((h, w, 3), dtype=np.uint8)
    
    for class_idx, rgb_color in color_dict.items():
        r, g, b = rgb_color
        mask_indices = mask_array == class_idx
        rgb_image[mask_indices] = [r, g, b]
        
    return rgb_image

def timer_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"{func.__name__} took {elapsed:.4f} seconds")
        return result
    return wrapper