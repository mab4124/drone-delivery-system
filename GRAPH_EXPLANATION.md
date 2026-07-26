# 3-Layer Graph-Based Semantic Reasoning System - Complete Explanation

## SYSTEM OVERVIEW

The system uses a **3-layer spreading activation graph** to convert package properties into terrain penalties without any conditional logic (no if/elif/else chains). All penalties emerge purely from edge weight accumulation.

---

## ARCHITECTURE: 3-LAYER SPREADING ACTIVATION GRAPH

### Layer Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      LAYER 1: SOURCE NODES                                  │
│            (Package Properties - Starting Points for Activation)             │
│                                                                             │
│  Fragile ──────┐  Valuable ──────┐  Biohazard ─────┐  Heavy ────────┐     │
│                │                 │                 │                │     │
└────────────────┼─────────────────┼─────────────────┼────────────────┼─────┘
                 │                 │                 │                │
           (weights)          (weights)          (weights)         (weights)
                 │                 │                 │                │
└────────────────┼─────────────────┼─────────────────┼────────────────┼─────┘
│                │                 │                 │                │     │
│   Hard ────────┴─────────────┐   │                 │                │     │
│   Visible ────────────────────┼──┴──────┐          │          Soft ─┴─┐   │
│   Dirty ──────────────────────┼─────────┼─────┐    │          Unstable┼─┐ │
│   Wet ────────────────────────┼─────────┼──┬──┴────┼─────┐           │ │ │
│   Slippery ───────────────────┼─────────┼──┼───┐   │     │           │ │ │
│   Contaminated ───────────────┼─────────┼──┼───┼─┬─┘     │           │ │ │
│   Cold ───────────────────────┼─────────┼──┼───┼─┼────┐  │           │ │ │
│   LowVisibility ───────────────┼─────────┼──┼───┼─┼────┼──┼──────┐    │ │ │
│                                │         │  │   │ │    │  │      │    │ │ │
│              LAYER 2: PROPERTY NODES     │  │   │ │    │  │      │    │ │ │
│        (Abstract Physical Properties)    │  │   │ │    │  │      │    │ │ │
│                                          │  │   │ │    │  │      │    │ │ │
└──────────────────────────────────────────┼──┼───┼─┼────┼──┼──────┼────┼─┼─┘
                                           │  │   │ │    │  │      │    │ │
                                      (weights)│   │ │    │  │      │    │ │
                                           │  │   │ │    │  │      │    │ │
┌──────────────────────────────────────────┼──┼───┼─┼────┼──┼──────┼────┼─┼─┐
│                                          │  │   │ │    │  │      │    │ │ │
│                   Pavement ──────────────┼──┼───┼─┘    │  │      │    │ │ │
│                   Grass ─────────────────┼──┼───┼──────┼──┼──────┘    │ │ │
│                   Dirt ──────────────────┼──┼───┼──────┼──┘           │ │ │
│                   Water ─────────────────┼──┼───┼──────┘              │ │ │
│                                          │  │   │                     │ │ │
│              LAYER 3: TERRAIN NODES      │  │   │              Unstable│ │
│         (Physical Landing Zones)         └──┴───┴────────────────────┘ ┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## LAYER 1: SOURCE NODES (Package Properties)

These are **active mission factors** extracted from `mission_config.json`:

```json
{
  "package": {
    "fragile": false,
    "valuable": false,
    "biohazard": false,
    "heavy": true
  }
}
```

**Active Source Nodes** (only if `true`):
- **Fragile** → Package breaks easily (high impact on terrain choice)
- **Valuable** → Package worth protecting from theft (visible = bad)
- **Biohazard** → Toxic/dangerous (must avoid contamination spread)
- **Heavy** → Package is heavy (soft surfaces may deform, needs stability)

### Current Example:
If `heavy=true` in config → **Active Source Nodes: ["Heavy"]**

---

## LAYER 2: PROPERTY NODES (Abstract Physical Properties)

These are **intermediate abstract properties** that receive activation from source nodes:

| Property | Meaning | Activated By |
|----------|---------|--------------|
| **Hard** | Rigid, supportive surface | Fragile → needs hard support |
| **Visible** | Easy to spot from above | Valuable → visibility = theft risk |
| **Dirty** | Surface has contamination | Valuable → gets dirty |
| **Wet** | Moisture present | (environment-based, not in current config) |
| **Slippery** | Low friction surface | Water, snow effects |
| **Contaminated** | Has biohazard material | Biohazard → spreads contamination |
| **Soft** | Absorbs impact | Heavy → needs soft landing to protect |
| **Unstable** | Movement risk | Heavy, Wind → instability |
| **Cold** | Low temperature | Snow environment |
| **LowVisibility** | Hard to see landing zone | Night environment |
| **Dark** | Little light | Night/Dusk environment |

### Edge Weights: SOURCE → PROPERTY

```python
SOURCE_TO_PROPERTY_EDGES = {
    "Fragile":    {"Hard": 0.8},                           # Fragile needs hard support
    "Valuable":   {"Visible": 0.6, "Dirty": 0.4},         # Valuable gets exposed, gets dirty
    "Biohazard":  {"Contaminated": 1.0},                  # Biohazard = 100% contamination
    "Heavy":      {"Soft": 0.9, "Unstable": 0.5}          # Heavy needs soft landing, risks instability
}
```

**Key Insight**: Edge weights (0.0-1.0) represent the **strength of influence**.
- 1.0 = strong influence
- 0.5 = moderate influence
- 0.3 = weak influence

---

## LAYER 3: TERRAIN NODES (Landing Zones)

These are the **physical location types** where the drone can land:

- **Pavement** → Hard concrete/asphalt (ideal for hard packages)
- **Grass** → Soft, natural surface (absorbs impact, but slippery when wet)
- **Dirt** → Earth/mud (dirty but stable when dry)
- **Water** → Not viable (package gets wet/damaged)

---

## THE SPREADING ACTIVATION ALGORITHM

The algorithm is implemented in `knowledge_graph.py` as the `think()` function. It's a **2-step process**:

### STEP 1: SOURCE → PROPERTY ACTIVATION

For each **active source node**, accumulate activation in connected property nodes based on edge weights.

**Algorithm (Pseudocode):**
```
property_activations = {}

FOR EACH active_source_node:
    FOR EACH connected property (from SOURCE_TO_PROPERTY_EDGES):
        property_activation += edge_weight
```

### EXAMPLE WITH "Heavy" PACKAGE:

```
Active Sources: ["Heavy"]

Step 1 - Source to Property Activation:
  Heavy → Soft (weight 0.9)   → property_activations["Soft"] = 0.9
  Heavy → Unstable (weight 0.5) → property_activations["Unstable"] = 0.5

Result: property_activations = {
  "Soft": 0.9,
  "Unstable": 0.5
}
```

---

### STEP 2: PROPERTY → TERRAIN PROPAGATION

For each **activated property**, propagate its activation to connected terrains, **multiplying by edge weights**.

**Algorithm (Pseudocode):**
```
terrain_penalties = {}

FOR EACH property_node WITH activation_level:
    FOR EACH connected terrain (from PROPERTY_TO_TERRAIN_EDGES):
        terrain_penalty += activation_level × edge_weight
```

### EXAMPLE CONTINUING "Heavy" PACKAGE:

```
Property Activations: {
  "Soft": 0.9,
  "Unstable": 0.5
}

Step 2 - Property to Terrain Propagation:

From "Soft" (activation 0.9):
  Soft → Grass (weight 1.0)  → Grass += 0.9 × 1.0 = 0.9
  Soft → Dirt (weight 0.8)   → Dirt += 0.9 × 0.8 = 0.72

From "Unstable" (activation 0.5):
  Unstable → Grass (weight 0.8)    → Grass += 0.5 × 0.8 = 0.4
  Unstable → Pavement (weight 0.0) → Pavement += 0.5 × 0.0 = 0.0

Accumulated Terrain Penalties:
  Pavement: 0.0    (no penalties)
  Grass:    0.9 + 0.4 = 1.3 → capped to 1.0 (max penalty)
  Dirt:     0.72   (moderate penalty)
  Water:    0.0    (no penalties from Heavy)

Final Capped Penalties (all must be 0.0-1.0):
  Pavement: 0.0
  Grass:    1.0 (AVOID - soft but unstable)
  Dirt:     0.72 (UNSAFE - muddy/soft)
  Water:    0.0 (not penalized)
```

**Result**: For a heavy package, the system says:
- ✅ **Pavement**: SAFE (hard, stable)
- ⚠️ **Dirt**: MODERATE RISK (soft but not ideal)
- ❌ **Grass**: HIGH RISK (too soft, too unstable)
- ❌ **Water**: NOT AN OPTION

---

## EDGE WEIGHT REFERENCE TABLE

### SOURCE → PROPERTY EDGES (Layer 1 → Layer 2)

```python
SOURCE_TO_PROPERTY_EDGES = {
    "Fragile":    {"Hard": 0.8},
    "Valuable":   {"Visible": 0.6, "Dirty": 0.4},
    "Biohazard":  {"Contaminated": 1.0},
    "Heavy":      {"Soft": 0.9, "Unstable": 0.5},
}
```

### PROPERTY → TERRAIN EDGES (Layer 2 → Layer 3)

```python
PROPERTY_TO_TERRAIN_EDGES = {
    "Hard":           {"Pavement": 1.0},
    "Visible":        {"Pavement": 1.0},
    "Soft":           {"Grass": 1.0, "Dirt": 0.8},
    "Wet":            {"Dirt": 1.0, "Grass": 0.85},
    "Slippery":       {"Grass": 0.9, "Dirt": 0.7},
    "Contaminated":   {"Water": 1.0, "Grass": 0.5},
    "Dark":           {"Grass": 0.9, "Dirt": 0.9},
    "LowVisibility":  {"Pavement": 0.2, "Grass": 0.2},
    "Cold":           {"Grass": 0.4},
    "Dirty":          {"Dirt": 1.0},
    "Unstable":       {"Grass": 0.8, "Pavement": 0.0}
}
```

---

## CODE FLOW: WHERE PENALTIES ARE USED

```python
# Step 1: Parse package config
active_factors = parse_mission_config("mission_config.json")
# Result: ["Heavy"]

# Step 2: Find landing zones (geometry.py calls semantic reasoning)
candidates = find_candidate_placements(
    safe_mask, depth_map, target,
    segmentation_map=segmentation_map,
    active_factors=active_factors  # ← Passed to reasoning
)

# Step 3: Inside find_candidate_placements (geometry.py)
# For each candidate location:
terrain_class = classify_terrain_from_mask(segmentation_map, interior_points)
# Result: "Grass"

kg_penalty = get_semantic_penalty(active_factors, terrain_class)
# This calls: knowledge_graph.think(["Heavy"]) → returns terrain_penalties
# Then returns terrain_penalties.get("Grass", 0.0) = 1.0

# Step 4: Total cost calculation
total_cost = 0.4 × distance + 0.3 × roughness + 0.3 × kg_penalty
#          = 0.4 × 50 + 0.3 × 0.05 + 0.3 × 1.0
#          = 20.0 + 0.015 + 0.3
#          = 20.315 (HIGH due to semantic penalty)
```

---

## IMAGE RESIZING: COMPLETE FLOW

### **The Image Journey: Original → Processing → Output**

```
STAGE 1: INPUT (User provides image)
├─ Raw image: arbitrary resolution (e.g., 1920×1200)
│
STAGE 2: STANDARDIZATION TO 800×600 (main.py - Line 131)
├─ original_image = cv2.imread(image_path)        # Load raw
├─ original_image = cv2.resize(original_image, (800, 600))  ← FIRST RESIZE
├─ original_image_rgb = cv2.cvtColor(...)
│
│  WHY 800×600 HERE?
│  • Creates consistent working resolution
│  • User inputs coordinates in 800×600 space (e.g., "400,300")
│  • All processing uses this coordinate system
│  • Simplifies calculations and consistency
│
STAGE 3: MODEL PROCESSING (Two parallel paths)
│
  PATH A: SEGMENTATION (semantic segmentation)
  ├─ Input: original_image (800×600, RGB)
  ├─ segment_image() downsamples to 256×256 for U-Net
  │  └─ image_resized = cv2.resize(image, (256, 256))  ← SECOND RESIZE
  │     (Why? U-Net was trained on 256×256 patches for efficiency)
  │
  ├─ U-Net processes (256×256) → outputs segmentation (256×256)
  │
  ├─ RESIZE BACK TO 800×600
  │  └─ segmentation_full = cv2.resize(segmentation, (800, 600))  ← THIRD RESIZE
  │     (Why? Match original_image size, preserve all spatial details)
  │
  └─ Output: segmentation_map (800×600, class labels)

  PATH B: DEPTH ESTIMATION (MiDaS depth model)
  ├─ Input: original_image (800×600, RGB)
  ├─ MiDaS internally handles resizing (transforms applied)
  ├─ MiDaS processes → outputs depth
  ├─ RESIZE TO MATCH original_image
  │  └─ depth = torch.nn.functional.interpolate(..., size=original_image.shape[:2])
  │     (Why? Match 800×600 for coordinate alignment)
  │
  └─ Output: depth_map (800×600, depth values)
│
STAGE 4: REASONING & CANDIDATE FINDING
├─ Both maps (segmentation, depth) are 800×600
├─ Process candidates at this resolution
├─ Use coordinates in 800×600 space
│
STAGE 5: OUTPUT VISUALIZATION (original_image_rgb copied)
├─ output_image = original_image_rgb.copy()  # 800×600
├─ Draw results on 800×600 space
├─ Save as output.jpg
│
└─ All coordinates stay in 800×600 space
```

---

## KEY RESIZING SUMMARY TABLE

| Stage | Input Res. | Output Res. | Purpose | Which Image |
|-------|-----------|-----------|---------|------------|
| 1. Load | Any | n/a | Read disk | Original (any size) |
| **2. Standardize** | **Any** | **800×600** | **Coordinate system** | **Original image** |
| 3A. Segment (down) | 800×600 | 256×256 | Model efficiency | Original image (RGB) |
| 3A. Segment (Process) | 256×256 | 256×256 | U-Net inference | Downsampled version |
| 3A. Segment (up) | 256×256 | **800×600** | **Spatial precision** | **Segmentation map** |
| 3B. Depth | 800×600 | **800×600** | **Coordinate match** | **Original image (RGB)** |
| 4. Reasoning | 800×600 | 800×600 | Find candidates | Segmentation + Depth |
| 5. Output | 800×600 | 800×600 | Draw results | Original image RGB |

---

## WHY RESIZE TO 800×600?

### Three Key Reasons:

1. **CONSISTENCY** - All coordinates, masks, depth maps must align
   - User enters target: "400,300" (assumes 800×600 space)
   - Segmentation map: 800×600 (matches coordinate system)
   - Depth map: 800×600 (matches coordinate system)
   - Any mismatch = wrong terrain classification

2. **MODEL TRAINING** - Models were trained on specific resolutions
   - U-Net expects ~256×256 input → trained on that
   - MiDaS has its transforms (internally standard)
   - Must resize to match training data

3. **PERFORMANCE** - Balance accuracy vs. speed
   - 800×600 provides good detail retention
   - 256×256 is fast enough for U-Net
   - Upscaling back to 800×600 preserves edge details

---

## EXAMPLE: ANALYZING A "FRAGILE + VALUABLE" PACKAGE

**Config:**
```json
{
  "package": {
    "fragile": true,
    "valuable": true,
    "biohazard": false,
    "heavy": false
  }
}
```

**Step 1: Active Sources**
```
Active Sources = ["Fragile", "Valuable"]
```

**Step 2: Property Activations**
```
From Fragile:
  Hard: 0.8

From Valuable:
  Visible: 0.6
  Dirty: 0.4

Complete: property_activations = {
  "Hard": 0.8,
  "Visible": 0.6,
  "Dirty": 0.4
}
```

**Step 3: Terrain Penalties**
```
From Hard (0.8):
  Pavement: 0.8 × 1.0 = 0.8

From Visible (0.6):
  Pavement: 0.6 × 1.0 = 0.6

From Dirty (0.4):
  Dirt: 0.4 × 1.0 = 0.4

Accumulated:
  Pavement: 0.8 + 0.6 = 1.4 → capped to 1.0 ✅ BEST (hard, protected)
  Grass:    0.0                ⚠️ NEUTRAL
  Dirt:     0.4                ❌ RISKY (gets dirty)
  Water:    0.0                ❌ WORST (damages package)
```

**Decision**: Land on **Pavement** (hard surface for fragile item, minimizes visibility)

---

## NO CONDITIONAL LOGIC!

The system achieves all reasoning **purely through graph multiplication and accumulation**:

```python
# ✅ CORRECT (Graph-based)
for source in active_sources:
    for property, weight in EDGES[source]:
        activation[property] += weight

# ❌ WRONG (Conditional)
if "Fragile" in active_sources:
    if terrain == "Pavement":
        penalty = 0.1
    else:
        penalty = 0.5
```

All intelligence comes from edge weights — **NO if/elif/else chains**.

---

## SUMMARY

| Component | Role | Example |
|-----------|------|---------|
| **Source Nodes** | Package properties | Fragile, Heavy |
| **Property Nodes** | Abstract properties | Hard, Soft, Unstable |
| **Terrain Nodes** | Landing zones | Pavement, Grass, Dirt |
| **SOURCE→PROPERTY Edges** | Property importance | Fragile→Hard (0.8) |
| **PROPERTY→TERRAIN Edges** | Terrain suitability | Hard→Pavement (1.0) |
| **Spreading Activation** | Computation engine | Accumulate weights |
| **Semantic Penalty** | Final score (0-1) | 0.72 = risky, 0.0 = safe |

**NO RULES, ONLY EDGES** ✨
