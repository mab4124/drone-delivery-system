from collections import Counter
from config import TERRAIN_MAPPING_DICT


def classify_terrain_from_mask(segmentation_map, interior_points):
    if not interior_points:
        return "Water"
    
    h, w = segmentation_map.shape
    
    classes = []
    for x, y in interior_points:
        x_idx = max(0, min(int(x), w - 1))
        y_idx = max(0, min(int(y), h - 1))
        classes.append(segmentation_map[y_idx, x_idx])
    
    if not classes:
        return "Water"
    
    dominant_class = Counter(classes).most_common(1)[0][0]
    
    terrain_string = TERRAIN_MAPPING_DICT.get(dominant_class, "Water")
    
    return terrain_string
