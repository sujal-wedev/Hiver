"""
Interactive CLI Labeling Assistant for building/re-annotating golden set items.
"""

import os
import sys
import pandas as pd

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.taxonomy import ALL_INTENTS

def main():
    golden_path = os.path.join(PROJECT_ROOT, "golden_set", "golden_eval_v1.csv")
    if not os.path.exists(golden_path):
        golden_path = os.path.join(BACKEND_DIR, "golden_set", "golden_eval_v1.csv")

    if not os.path.exists(golden_path):
        print(f"Golden dataset file not found at {golden_path}")
        return

    df = pd.read_csv(golden_path)
    print(f"Loaded {len(df)} golden evaluation dataset items.")
    print("Taxonomy intents:")
    for idx, name in enumerate(ALL_INTENTS, 1):
        print(f"  {idx}. {name}")
    print("\nPress Ctrl+C to exit interactive labeling session.\n")

if __name__ == "__main__":
    main()
