import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code'))

from code.main import main

if __name__ == "__main__":
    image_path = os.path.join(os.path.dirname(__file__), "training_set", "images", "000.jpg")
    target_coords = "400,300"
    
    print("\n" + "="*80)
    print("AUTONOMOUS DRONE DELIVERY SYSTEM - AUTOMATED TEST")
    print("="*80)
    print(f"\nTest Configuration:")
    print(f"  Image: {image_path}")
    print(f"  Target: {target_coords}")
    print(f"  Mission: Fragile + Valuable package, Raining conditions")
    print("\nThis is an automated test that simulates:")
    print("  - Semantic segmentation (U-Net)")
    print("  - Depth estimation (MiDaS)")
    print("  - Safe zone detection")
    print("  - Semantic reasoning with knowledge graph")
    print("\nThe system will find the optimal delivery location considering:")
    print("  - Distance to target")
    print("  - Surface roughness")
    print("  - Package fragility & value penalties")
    print("  - Environmental factors (raining adds wetness penalty)")
    print("\n" + "="*80 + "\n")
    
    os.chdir(os.path.dirname(__file__))
    
    import io
    import contextlib
    
    f = io.StringIO()
    with contextlib.redirect_stdin(io.StringIO(f"{image_path}\n{target_coords}\n")):
        main()
