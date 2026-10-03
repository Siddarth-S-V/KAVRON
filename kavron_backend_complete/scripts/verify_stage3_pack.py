from __future__ import annotations
import importlib.util
from pathlib import Path
import cv2

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / 'models'
REQUIRED = [
    ('yolo11n.pt', 1_000_000),
    ('yolo11n_pose.pt', 1_000_000),
    ('yolo26n.pt', 1_000_000),
    ('yolo26s.pt', 5_000_000),
    ('face_detection_yunet_2023mar.onnx', 100_000),
    ('license_plate_detection_lpd_yunet_2023mar.onnx', 1_000_000),
    ('face_recognition_sface_2021dec.onnx', 10_000_000),
    ('face_recognition_sface_2021dec_int8bq.onnx', 1_000_000),
    ('paddleocr/en_PP-OCRv5_mobile_rec/inference.pdiparams', 1_000_000),
    ('rtmpose/rtmpose-s_simcc-coco_pt-aic-coco_420e-256x192-8edcf0d7_20230127.pth', 10_000_000),
]

def main() -> int:
    failed = False
    for rel, minimum in REQUIRED:
        p = MODELS / rel
        ok = p.exists() and p.stat().st_size >= minimum
        print(('OK  ' if ok else 'FAIL'), rel, p.stat().st_size if p.exists() else 'missing')
        failed |= not ok
    for rel in ('face_detection_yunet_2023mar.onnx','license_plate_detection_lpd_yunet_2023mar.onnx'):
        p = MODELS / rel
        try:
            net = cv2.dnn.readNet(str(p))
            print('OK  ONNX', rel, 'empty=', net.empty())
            failed |= net.empty()
        except Exception as exc:
            print('FAIL ONNX', rel, exc)
            failed = True
    for rel in ('face_recognition_sface_2021dec.onnx','face_recognition_sface_2021dec_int8bq.onnx'):
        p = MODELS / rel
        try:
            recognizer = cv2.FaceRecognizerSF.create(str(p), '')
            print('OK  SFace', rel, 'loaded=', recognizer is not None)
            failed |= recognizer is None
        except Exception as exc:
            print('FAIL SFace', rel, exc)
            failed = True
    print('INFO ultralytics installed:', bool(importlib.util.find_spec('ultralytics')))
    print('INFO paddleocr installed:', bool(importlib.util.find_spec('paddleocr')))
    print('RESULT:', 'PASS' if not failed else 'FAIL')
    return 1 if failed else 0

if __name__ == '__main__':
    raise SystemExit(main())
