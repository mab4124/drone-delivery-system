import json
import os

def parse_mission_config(config_path=None):
    """Parse package configuration from mission_config.json to extract active source nodes."""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "mission_config.json")
    
    if not os.path.exists(config_path):
        return []
    
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
    except:
        return []
    
    active_source_nodes = []
    
    # Extract package-based source nodes
    pkg = data.get("package", {})
    if pkg.get("fragile"):
        active_source_nodes.append("Fragile")
    if pkg.get("valuable"):
        active_source_nodes.append("Valuable")
    if pkg.get("biohazard"):
        active_source_nodes.append("Biohazard")
    if pkg.get("heavy"):
        active_source_nodes.append("Heavy")
    
    return active_source_nodes


SOURCE_TO_PROPERTY_EDGES = {
    "Fragile": {"Hard": 0.8},
    "Valuable": {"Visible": 0.6, "Dirty": 0.4},
    "Biohazard": {"Contaminated": 1.0},
    "Heavy": {"Soft": 0.9, "Unstable": 0.5},
    "Rain": {"Wet": 0.5, "Slippery": 0.3},
    "Snow": {"Slippery": 0.8, "Cold": 0.6},
    "Wind": {"Unstable": 0.7},
    "Night": {"Dark": 0.7, "LowVisibility": 0.5},
    "Dusk": {"Dark": 0.4, "LowVisibility": 0.3}
}


PROPERTY_TO_TERRAIN_EDGES = {
    "Hard": {"Pavement": 1.0},
    "Visible": {"Pavement": 1.0},
    "Soft": {"Grass": 1.0, "Dirt": 0.8},
    "Wet": {"Dirt": 1.0, "Grass": 0.85},
    "Slippery": {"Grass": 0.9, "Dirt": 0.7},
    "Contaminated": {"Water": 1.0, "Grass": 0.5},
    "Dark": {"Grass": 0.9, "Dirt": 0.9},
    "LowVisibility": {"Pavement": 0.2, "Grass": 0.2},
    "Cold": {"Grass": 0.4},
    "Dirty": {"Dirt": 1.0},
    "Unstable": {"Grass": 0.8, "Pavement": 0.0}
}


TERRAIN_NODES = ["Pavement", "Grass", "Dirt", "Water"]


def think(active_source_nodes):
    terrain_penalties = {terrain: 0.0 for terrain in TERRAIN_NODES}
    
    property_activations = {}
    
    for source_node in active_source_nodes:
        if source_node not in SOURCE_TO_PROPERTY_EDGES:
            continue
        
        connected_properties = SOURCE_TO_PROPERTY_EDGES[source_node]
        
        for property_node, source_weight in connected_properties.items():
            if property_node not in property_activations:
                property_activations[property_node] = 0.0
            
            property_activations[property_node] += source_weight
    
    for property_node, activation_level in property_activations.items():
        if property_node not in PROPERTY_TO_TERRAIN_EDGES:
            continue
        
        connected_terrains = PROPERTY_TO_TERRAIN_EDGES[property_node]
        
        for terrain_node, edge_weight in connected_terrains.items():
            terrain_penalties[terrain_node] += activation_level * edge_weight
    
    for terrain in TERRAIN_NODES:
        terrain_penalties[terrain] = min(1.0, max(0.0, terrain_penalties[terrain]))
    
    return terrain_penalties


def get_semantic_penalty(active_factors, terrain_class):
    active_source_nodes = active_factors if active_factors else []
    terrain_penalties = think(active_source_nodes)
    return terrain_penalties.get(terrain_class, 0.0)


def get_terrain_penalty(terrain_class, active_factors=None, active_source_nodes=None):
    if active_source_nodes is None:
        active_source_nodes = active_factors if active_factors else []
    
    terrain_penalties = think(active_source_nodes)
    
    return terrain_penalties.get(terrain_class, 0.0)


def analyze_reasoning_path(active_source_nodes):
    reasoning_log = {}
    
    reasoning_log["active_sources"] = active_source_nodes
    reasoning_log["source_to_property"] = {}
    
    property_activations = {}
    
    for source_node in active_source_nodes:
        if source_node not in SOURCE_TO_PROPERTY_EDGES:
            continue
        
        connected = SOURCE_TO_PROPERTY_EDGES[source_node]
        reasoning_log["source_to_property"][source_node] = connected
        
        for prop, weight in connected.items():
            if prop not in property_activations:
                property_activations[prop] = 0.0
            property_activations[prop] += weight
    
    reasoning_log["property_activations"] = property_activations
    reasoning_log["property_to_terrain"] = {}
    
    terrain_penalties = {terrain: 0.0 for terrain in TERRAIN_NODES}
    
    for property_node, activation in property_activations.items():
        if property_node not in PROPERTY_TO_TERRAIN_EDGES:
            continue
        
        connected = PROPERTY_TO_TERRAIN_EDGES[property_node]
        reasoning_log["property_to_terrain"][property_node] = {
            "activation": activation,
            "connections": connected
        }
        
        for terrain, weight in connected.items():
            penalty_contribution = activation * weight
            terrain_penalties[terrain] += penalty_contribution
    
    for terrain in TERRAIN_NODES:
        terrain_penalties[terrain] = min(1.0, max(0.0, terrain_penalties[terrain]))
    
    reasoning_log["final_terrain_penalties"] = terrain_penalties
    
    return reasoning_log