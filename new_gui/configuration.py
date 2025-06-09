#!/usr/bin/env python3

import sys
import pathlib
import subprocess
import threading
import os
import time

# ────────── Configuration ──────────
BASE_DIR = pathlib.Path(__file__).resolve().parent
PY = sys.executable
LOG_FILE = BASE_DIR / "log.txt"   # Change to BASE_DIR.parent / "log.txt" to write one level up
# ───────────────────────────────────

def is_target(p: pathlib.Path) -> bool:
    """Check if a file should be launched based on its name"""
    s = p.stem.lower()
    return s.endswith("gui") or s.endswith("setup") or s.endswith("init")

# Aggregate log file (line-buffered: write to disk immediately after each line)
log_fh = open(LOG_FILE, "w", buffering=1, encoding="utf-8")

def start_gui(path: pathlib.Path):
    """Thread target: start a GUI subprocess and wait for it to exit"""
    proc = subprocess.Popen(
        [PY, str(path)],
        cwd=path.parent,                     # Ensure correct resource path
        stdout=log_fh,
        stderr=subprocess.STDOUT,
        env={**os.environ, "REM_MULTI_INST": "1"}
    )
    print(f"▶ {path.name} started (pid={proc.pid})")
    proc.wait()
    print(f"⏹ {path.name} exited (rc={proc.returncode})")

def main():
    targets = sorted(p for p in BASE_DIR.rglob("*.py") if is_target(p))
    if not targets:
        print("⚠️  No *gui.py / *setup.py found"); return

    print(f"Logging all output to: {LOG_FILE}\n")

    threads = []
    for mod in targets:
        th = threading.Thread(target=start_gui, args=(mod,), daemon=True)
        th.start()
        threads.append(th)
        time.sleep(0.3)  # Slight delay to reduce initial IO/memory peak

    print("All GUIs started. Press Ctrl‑C to exit.")
    try:
        for th in threads:
            th.join()  # Wait for all GUI threads to finish
    except KeyboardInterrupt:
        print("\n⏹ Ctrl‑C received, exiting main process. All subprocesses will terminate automatically.")

if __name__ == "__main__":
    main()
