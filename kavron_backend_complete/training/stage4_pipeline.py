from __future__ import annotations
import argparse, json
from pathlib import Path

COMPONENTS = {
    'detector': 'YOLO11n/YOLO26n/YOLO26s',
    'pose': 'YOLO11n-Pose/RTMPose-S',
    'anpr': 'LPD-YuNet + PP-OCRv5',
    'face': 'YuNet + SFace',
}

def main():
    parser=argparse.ArgumentParser(description='KAVRON Stage 4 multimodel training preflight')
    parser.add_argument('--component', choices=['all', *COMPONENTS], default='all')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    dataset=root/'training'/'dataset.yaml'
    out={"stage":4,"component":args.component,"components":COMPONENTS,"dataset_ready":dataset.exists(),"status":"ready_to_train" if dataset.exists() else "labels_required"}
    print(json.dumps(out,indent=2))
    if not dataset.exists():
        print('\nNo supervised training is executed until reviewed labels exist.')
        return 2
    print('\nUse train_yolo_stage4.py for detector/pose training; use the vendor-specific training recipe for OCR/face adaptation after the matching labeled crops are prepared.')
    return 0
if __name__=='__main__': raise SystemExit(main())
