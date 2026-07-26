#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
run_all_eval.py  — Run each group's pipeline on the 4 rubric test cases.
Adapted for Windows: d:\\aip\\aitapp2\\evaluate\\
"""

import os
import shutil
import subprocess
import sys
import json
import time
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
PY   = sys.executable          # current Python interpreter
ROOT = Path(__file__).parent   # d:\aip\aitapp2\evaluate

RESULTS_DIR     = ROOT / "results"
MISSION_DEFAULT = ROOT / "mission_default.json"
MISSION_FV      = ROOT / "mission_fragile_valuable.json"

# ── Group definitions: (label, folder_name, src_subdir) ──────────────────────
# src_subdir is where main.py lives; "." means project root
GROUPS = [
    ("2022A3PS0642H_2022A8PS0740H", "CSF407_2026_2022A3PS0642H_2022A8PS0740H", "src"),
    ("2022A4PS1124H",               "CSF407_2026_2022A4PS1124H_Assignment-2-main", "src"),
    ("2022A7PS0234H",               "CSF407_2026_2022A7PS0234H-main",             "src"),
    ("2022B4A70894H",               "CSF407_2026_2022B4A70894H_Assignment-II",    "src"),
    ("2023A7PS0047H",               "CSF407_2026_2023A7PS0047H_Assignment-II",    "src"),
]

# ── Test cases: (id, image_file, target_x, target_y, mission_json) ────────────
# Images are in results/ folder
TESTCASES = [
    ("t1_065", "065.jpg",  400, 600, MISSION_DEFAULT),   # easy, no unsafe zone
    ("t2_078", "078.jpg",  500, 300, MISSION_FV),         # reasoning: fragile+valuable→grass
    ("t3_157", "157.jpg",  200, 120, MISSION_DEFAULT),   # hard: water/pavement/roof
    ("t4_601", "601.jpeg", 400, 500, MISSION_DEFAULT),    # generalization, new image
]

OUTPUT_EVAL_DIR = ROOT / "eval_results"


# ─────────────────────────────────────────────────────────────────────────────
def run_process(cmd, cwd, stdin_text=None, log_path=None, timeout=600):
    """Run a subprocess, capture output, write to log, return (returncode, output)."""
    print(f"  >> {' '.join(map(str, cmd))}")
    print(f"     cwd = {cwd}")
    try:
        proc = subprocess.run(
            list(map(str, cmd)),
            cwd=str(cwd),
            input=stdin_text,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        out = (proc.stdout or "")
        err = proc.stderr or ""
        combined = out + ("\n[STDERR]\n" + err if err.strip() else "")
        if log_path:
            Path(log_path).write_text(combined, encoding="utf-8")
        return proc.returncode, combined
    except subprocess.TimeoutExpired as e:
        msg = (e.stdout or "") + "\n[TIMEOUT after {}s]".format(timeout)
        if log_path:
            Path(log_path).write_text(msg, encoding="utf-8")
        print("  [TIMEOUT]")
        return -99, msg
    except Exception as ex:
        msg = f"[EXCEPTION] {ex}"
        if log_path:
            Path(log_path).write_text(msg, encoding="utf-8")
        print(f"  {msg}")
        return -1, msg


def copy_outputs(src_dir, outdir, filenames=("output.jpg", "output_analysis.jpg")):
    """Copy output images from src_dir into outdir."""
    for fname in filenames:
        src = Path(src_dir) / fname
        if src.exists():
            shutil.copy(str(src), str(outdir / fname))
            print(f"  Copied: {fname}")
        else:
            print(f"  [MISSING] {fname} not found in {src_dir}")


def install_mission_config(mission_json: Path, target_dir: Path):
    """Copy the mission config JSON into the project src folder."""
    dst = target_dir / "mission_config.json"
    shutil.copy(str(mission_json), str(dst))
    print(f"  mission_config → {dst}")


# ─────────────────────────────────────────────────────────────────────────────
def run_group(label, project_dir, src_subdir, tid, img_path, tx, ty, mission_json, outdir):
    """Run one group on one test case. Returns (returncode, log_text)."""
    src_dir = project_dir / src_subdir
    if not src_dir.exists():
        src_dir = project_dir   # fallback

    # Place correct mission_config.json in the src folder
    install_mission_config(mission_json, src_dir)

    log_path = outdir / "log.txt"

    # Each group's main.py has slightly different CLI / stdin interface —
    # detect by reading their main.py approach.
    # Groups 1 (2022A3PS0642H_2022A8PS0740H): python -m src.main --image .. --tx .. --ty ..
    # Group 2 (2022A4PS1124H): cd src && python main.py (stdin)
    # Group 3 (2022A7PS0234H): cd src && python main.py --image .. --tx .. --ty ..
    # Group 4 (2022B4A70894H): cd src && python main.py --image .. --x .. --y ..
    # Group 5 (2023A7PS0047H): cd src && python main.py (stdin)

    if label == "2022A3PS0642H_2022A8PS0740H":
        # Needs to be run as module from project root
        cmd = [
            PY, "-m", "src.main",
            "--image", str(img_path),
            "--tx", str(tx),
            "--ty", str(ty),
            "--mission", str(src_dir / "mission_config.json"),
            "--checkpoint", str(src_dir / "best_model.pth"),
            "--output-dir", str(outdir),
        ]
        rc, log = run_process(cmd, cwd=project_dir, log_path=log_path)
        # outputs written directly to outdir by --output-dir flag

    elif label == "2022A4PS1124H":
        # Interactive stdin: image path, tx, ty
        stdin = f"{img_path}\n{tx}\n{ty}\n"
        cmd = [PY, "main.py"]
        rc, log = run_process(cmd, cwd=src_dir, stdin_text=stdin, log_path=log_path)
        copy_outputs(src_dir, outdir)

    elif label == "2022A7PS0234H":
        # CLI args: --image .. --tx .. --ty .. (reads x y on same line in interactive mode)
        # main.py supports --image --tx --ty flags
        cmd = [
            PY, "main.py",
            "--image", str(img_path),
            "--tx", str(tx),
            "--ty", str(ty),
            "--config", str(src_dir / "mission_config.json"),
            "--model",  str(src_dir / "best_model.pth"),
            "--out",    str(outdir / "output.jpg"),
            "--analysis", str(outdir / "output_analysis.jpg"),
        ]
        rc, log = run_process(cmd, cwd=src_dir, log_path=log_path)
        # outputs written to outdir via --out and --analysis flags

    elif label == "2022B4A70894H":
        # CLI: --image .. --x .. --y .. --config .. --model ..
        cmd = [
            PY, "main.py",
            "--image",  str(img_path),
            "--x",      str(tx),
            "--y",      str(ty),
            "--config", str(src_dir / "mission_config.json"),
            "--model",  str(src_dir / "best_model.pth"),
            "--output", str(outdir / "output.jpg"),
            "--analysis", str(outdir / "output_analysis.jpg"),
        ]
        rc, log = run_process(cmd, cwd=src_dir, log_path=log_path)

    elif label == "2023A7PS0047H":
        # Interactive stdin only: image path, tx, ty
        stdin = f"{img_path}\n{tx}\n{ty}\n"
        cmd = [PY, "main.py"]
        rc, log = run_process(cmd, cwd=src_dir, stdin_text=stdin, log_path=log_path)
        copy_outputs(src_dir, outdir)

    else:
        rc, log = -1, f"[Unknown group label: {label}]"

    return rc, log


# ─────────────────────────────────────────────────────────────────────────────
def main():
    if OUTPUT_EVAL_DIR.exists():
        shutil.rmtree(OUTPUT_EVAL_DIR)
    OUTPUT_EVAL_DIR.mkdir(parents=True)

    summary = {}

    for label, dirname, sub in GROUPS:
        project_dir = ROOT / dirname
        if not project_dir.exists():
            print(f"\n[SKIP] Project folder not found: {project_dir}")
            continue

        summary[label] = {}
        print(f"\n{'='*70}")
        print(f"  GROUP: {label}  |  {dirname}")
        print(f"{'='*70}")

        for tid, img_fname, tx, ty, mission_json in TESTCASES:
            img_path = RESULTS_DIR / img_fname
            if not img_path.exists():
                print(f"\n  [SKIP] Image not found: {img_path}")
                continue

            outdir = OUTPUT_EVAL_DIR / label / tid
            outdir.mkdir(parents=True, exist_ok=True)

            print(f"\n  -- {tid}: {img_fname}  target=({tx},{ty})  mission={mission_json.stem}")
            t0 = time.time()
            rc, log = run_group(label, project_dir, sub, tid, img_path, tx, ty, mission_json, outdir)
            elapsed = time.time() - t0

            status = "OK" if rc == 0 else ("TIMEOUT" if rc == -99 else f"ERROR(rc={rc})")
            summary[label][tid] = {
                "status": status,
                "returncode": rc,
                "elapsed_s": round(elapsed, 1),
                "has_output": (outdir / "output.jpg").exists(),
                "has_analysis": (outdir / "output_analysis.jpg").exists(),
            }
            print(f"  Status: {status}  |  {elapsed:.1f}s  |  "
                  f"output={'Y' if summary[label][tid]['has_output'] else 'N'}  "
                  f"analysis={'Y' if summary[label][tid]['has_analysis'] else 'N'}")

    # Write summary JSON
    summary_path = OUTPUT_EVAL_DIR / "run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\n\nSummary written to: {summary_path}")
    print("\nDone. Results in:", OUTPUT_EVAL_DIR)


if __name__ == "__main__":
    main()
