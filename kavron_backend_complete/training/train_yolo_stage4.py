from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='yolo11n.pt')
    parser.add_argument('--data', default='training/dataset.yaml')
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--imgsz', type=int, default=640)
    parser.add_argument('--batch', type=int, default=8)
    parser.add_argument('--device', default='cpu')
    parser.add_argument('--project', default='training/runs')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    data = (root / args.data).resolve()
    model_path = (root / 'models' / args.model).resolve() if not Path(args.model).is_absolute() else Path(args.model)
    if not data.exists():
        print(f'DATASET NOT READY: {data}')
        print('Create training/dataset.yaml and provide labeled train/val images + YOLO labels before fine-tuning.')
        return 2
    if not model_path.exists():
        print(f'MODEL NOT FOUND: {model_path}')
        return 2
    from ultralytics import YOLO
    model = YOLO(str(model_path))
    model.train(data=str(data), epochs=args.epochs, imgsz=args.imgsz, batch=args.batch, device=args.device,
                project=str(root / args.project), name=f'stage4_{model_path.stem}', exist_ok=True,
                pretrained=True, cache=False, workers=0 if args.device == 'cpu' else 2, verbose=True)
    metrics = model.val(data=str(data), imgsz=args.imgsz, device=args.device)
    report = {'model': str(model_path), 'dataset': str(data), 'epochs': args.epochs, 'imgsz': args.imgsz,
              'device': args.device, 'metrics': getattr(metrics, 'results_dict', {}),
              'status': 'trained_and_validated', 'promotion': 'manual benchmark gate required before replacing production model'}
    report_path = root / args.project / f'stage4_{model_path.stem}' / 'promotion_report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    print(json.dumps(report, indent=2, default=str))
    return 0
if __name__ == '__main__': raise SystemExit(main())
