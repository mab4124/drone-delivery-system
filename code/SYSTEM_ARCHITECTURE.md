AUTONOMOUS DRONE PACKAGE DELIVERY - SEMANTIC REASONING WITH GRAPH-BASED ENGINE
================================================================================================

## SYSTEM ARCHITECTURE

### 3-Layer Graph-Based Knowledge Base

#### LAYER 1: SOURCE NODES
These are active mission factors extracted from mission_config.json:
- From Package: Fragile, Valuable, Biohazard
- From Environment: Rain, Snow, Wind, Night, Dusk

Example (current config):
  Active Sources: [Fragile, Valuable, Rain, Night]

#### LAYER 2: PROPERTY NODES  
These are abstract physical properties that inherit penalties from source nodes:
- Hard, Visible, Dirty, Wet, Slippery, Contaminated, Dark, LowVisibility, Cold, Unstable

Edge Definitions (SOURCE -> PROPERTY):
  Fragile -> Hard (0.8)
  Valuable -> Visible (0.6), Dirty (0.4)
  Biohazard -> Contaminated (1.0)
  Rain -> Wet (0.5), Slippery (0.3)
  Snow -> Slippery (0.8), Cold (0.6)
  Wind -> Unstable (0.7)
  Night -> Dark (0.7), LowVisibility (0.5)
  Dusk -> Dark (0.4), LowVisibility (0.3)

#### LAYER 3: TERRAIN NODES
These are the physical landing zones:
- Pavement, Grass, Dirt, Water

Edge Definitions (PROPERTY -> TERRAIN):
  Hard -> Pavement (1.0)
  Visible -> Pavement (1.0)
  Wet -> Dirt (1.0), Grass (0.6)
  Slippery -> Grass (0.8), Dirt (0.7)
  Contaminated -> Water (1.0), Grass (0.5)
  Dark -> Grass (0.3), Dirt (0.2)
  LowVisibility -> Pavement (0.2), Grass (0.2)
  Cold -> Grass (0.4)
  Dirty -> Dirt (1.0)
  Unstable -> Grass (0.6), Pavement (0.2)

### SPREADING ACTIVATION ALGORITHM

The think(active_source_nodes) function performs 2-step spreading activation:

STEP 1: Accumulate Property Activation
  For each active source node:
    For each connected property:
      property_activation += edge_weight

  Example with [Fragile, Valuable, Rain, Night]:
    Hard: 0.8 (from Fragile)
    Visible: 0.6 (from Valuable)
    Dirty: 0.4 (from Valuable)
    Wet: 0.5 (from Rain)
    Slippery: 0.3 (from Rain)
    Dark: 0.7 (from Night)
    LowVisibility: 0.5 (from Night)

STEP 2: Propagate to Terrain Penalties
  For each property with activation level:
    For each connected terrain:
      terrain_penalty += property_activation × edge_weight

  Example:
    Pavement += 0.8×1.0 (Hard) + 0.6×1.0 (Visible) + 0.5×0.2 (LowVisibility) = 1.50 → capped at 1.0
    Grass += 0.5×0.6 (Wet) + 0.3×0.8 (Slippery) + 0.7×0.3 (Dark) + 0.5×0.2 (LowVisibility) = 0.85
    Dirt += 0.4×1.0 (Dirty) + 0.5×1.0 (Wet) + 0.3×0.7 (Slippery) + 0.7×0.2 (Dark) = 1.25 → capped at 1.0
    Water = 0.0 (no connected properties)

### SEMANTIC PENALTY CALCULATION

The get_semantic_penalty(active_factors, terrain_class) function:
  1. Calls think(active_factors) to get terrain penalties via spreading activation
  2. Returns the specific terrain's penalty
  3. NO if/elif/else chains - pure graph traversal

### COST FUNCTION INTEGRATION

Candidate Cost = 0.4 × distance + 0.3 × roughness + 0.3 × semantic_penalty

Where semantic_penalty comes from graph-based spreading activation (0.0 to 1.0)

### TEST RESULTS

Mission Config: OP-DELTA-9
Package: Medical vials (fragile=true, valuable=true, biohazard=false)
Environment: Rain, Night (battery=85%)

Active Source Nodes: [Fragile, Valuable, Rain, Night]

Final Terrain Penalties (via spreading activation):
  Pavement: 1.0000 (AVOID - hard for fragile, visible for thieves)
  Grass: 0.8500 (MODERATE - wet/slippery from rain, dark from night)
  Dirt: 1.0000 (AVOID - dirty, wet (mud), slippery, dark)
  Water: 0.0000 (NOT PENALIZED - no connected properties)

### CONTRAST: Why Not If/Else?

OLD APPROACH (if/elif):
  if fragile and pavement:
    penalty += 0.8
  if valuable and pavement:
    penalty += 0.4
  ...
Problem: Hard-coded, not scalable, missing emergent properties from combinations

NEW APPROACH (graph-based spreading activation):
  - Automatic combination of multiple constraints
  - Weights flow through edges
  - New constraints can be added by adding edges
  - Properties activate based on accumulated evidence
  - Capping at 1.0 prevents overflow
  - Extensible to new terrains, properties, and sources

### FILES MODIFIED

1. knowledge_graph.py
   - COMPLETELY REWRITTEN with 3-layer graph architecture
   - SOURCE_TO_PROPERTY_EDGES dictionary
   - PROPERTY_TO_TERRAIN_EDGES dictionary  
   - think() function for spreading activation
   - analyze_reasoning_path() for debugging

2. mission_config.json
   - Updated to new schema with simulated_environment block
   - Added mission_id for tracking
   - Added package type field

3. sim_environment.py
   - Now delegates to knowledge_graph.parse_mission_config()

4. semantic_brain.py
   - Already uses knowledge_graph penalties via geometry.py

5. geometry.py
   - Already integrated to call semantic penalties (no changes needed)

### USAGE

1. Modify mission_config.json to set mission parameters
2. Run python main.py
3. Enter image path
4. Enter target coordinates
5. System calculates candidate placements using:
   - Binary U-Net segmentation
   - MiDaS depth estimation
   - Graph-based semantic reasoning
   - Combined cost function

### TESTING THE GRAPH

Run: python test_graph.py

This shows:
- Active source nodes extracted from JSON
- Layer 2 property spreading
- Property activation levels
- Layer 3 terrain penalty propagation
- Final terrain penalties
