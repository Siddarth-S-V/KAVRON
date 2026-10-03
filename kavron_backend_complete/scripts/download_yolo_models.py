from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch official Ultralytics pretrained weights")
    parser.add_argument("models", nargs="*", default=["yolo26n.pt", "yolo11s.pt", "yolo11s-pose.pt"])
    args = parser.parse_args()
    from ultralytics import YOLO
    model_dir = ROOT / "models"
    model_dir.mkdir(exist_ok=True)
    for name in args.models:
        print(f"[KAVRON] fetching {name} from the official Ultralytics asset mechanism ...")
        model = YOLO(name)
        # Ultralytics resolves/downloads the asset if it is absent. If a local
        # file now exists, keep it under KAVRON/models as the canonical copy.
        resolved = Path(getattr(model, "ckpt_path", name))
        if resolved.exists() and resolved.resolve() != (model_dir / name).resolve():
            import shutil
            shutil.copy2(resolved, model_dir / name)
        print(f"[KAVRON] ready: {model_dir / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
