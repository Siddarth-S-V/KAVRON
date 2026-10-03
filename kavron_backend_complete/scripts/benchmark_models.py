from pathlib import Path
import time, statistics
import cv2
from app.core.config import get_settings
from app.ai.registry import ModelRegistry

s=get_settings(); image=cv2.imread(s.demo_video) if s.demo_video.lower().endswith(('.jpg','.png','.jpeg')) else None
if image is None:
    cap=cv2.VideoCapture(s.demo_video); ok,image=cap.read(); cap.release()
if not ok if 'ok' in locals() else image is None:
    raise SystemExit("Could not read benchmark frame")
reg=ModelRegistry(s.model_dir,s.device)
for mid, fn in [("general",s.general_model),("person",s.person_model),("pose",s.pose_model),("specialist",s.specialist_model),("pose_alt",s.pose_alt_model)]:
    try:
        m=reg.load(mid,fn); times=[]
        for _ in range(5):
            t=time.perf_counter(); m.predict(image,conf=s.confidence,verbose=False); times.append(time.perf_counter()-t)
        avg=statistics.mean(times); print(f"{mid:12} avg={avg*1000:.1f}ms fps={1/avg:.2f}")
    except Exception as exc: print(f"{mid:12} SKIP: {exc}")
