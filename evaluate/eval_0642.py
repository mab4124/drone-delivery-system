import os
import subprocess
import time
from pathlib import Path
import sys, io

# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PY = "C:/Users/bokde/AppData/Local/Programs/Python/Python313/python.exe"
ROOT = Path("d:/aip/aitapp2/evaluate")
RESULTS_DIR = ROOT / "results"
MISSION_DEFAULT = ROOT / "mission_default.json"
MISSION_FV = ROOT / "mission_fragile_valuable.json"

TESTCASES = [
    ("t1_065", "065.jpg",  400, 600, MISSION_DEFAULT),
    ("t2_078", "078.jpg",  500, 300, MISSION_FV),
    ("t3_157", "157.jpg",  200, 120, MISSION_DEFAULT),
    ("t4_601", "601.jpeg", 400, 500, MISSION_DEFAULT),
]

label = "2022A3PS0642H_2022A8PS0740H"
project_dir = ROOT / "CSF407_2026_2022A3PS0642H_2022A8PS0740H"

def run_process(cmd, cwd, log_path):
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)
    out = (proc.stdout or "")
    err = proc.stderr or ""
    combined = out + ("\n[STDERR]\n" + err if err.strip() else "")
    Path(log_path).write_text(combined, encoding="utf-8", errors="replace")
    return proc.returncode, combined

for tid, img_fname, tx, ty, mission_json in TESTCASES:
    img_path = RESULTS_DIR / img_fname
    outdir = ROOT / "eval_results" / label / tid
    outdir.mkdir(parents=True, exist_ok=True)
    log_path = outdir / "log.txt"
    
    cmd = [
        PY, "-m", "src.main",
        "--image", str(img_path),
        "--tx", str(tx),
        "--ty", str(ty),
        "--mission", str(mission_json),
        "--checkpoint", str(project_dir / "best_model.pth"),
        "--output-dir", str(outdir),
    ]
    print(f"Running {tid}...")
    run_process(cmd, cwd=project_dir, log_path=log_path)
print("Done!")
