from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ai.model_manager import ModelAssetManager  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Download KAVRON Stage 3 specialist models")
    parser.add_argument("--all", action="store_true", help="download all specialist OpenCV Zoo assets")
    parser.add_argument("keys", nargs="*", help="specific keys: face_detector face_recognizer plate_detector")
    args = parser.parse_args()
    manager = ModelAssetManager(str(ROOT / "models"))
    keys = list(manager.status()) if args.all or not args.keys else args.keys
    for key in keys:
        print(f"[KAVRON] downloading {key} ...")
        path = manager.ensure(key)
        print(f"[KAVRON] ready: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
