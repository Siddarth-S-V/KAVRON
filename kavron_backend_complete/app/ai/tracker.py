from __future__ import annotations
import math
from dataclasses import dataclass, field
from time import time

@dataclass
class Track:
    track_id: str
    class_name: str
    bbox: tuple[float,float,float,float]
    confidence: float
    first_seen: float
    last_seen: float
    hits: int = 1
    velocity: tuple[float,float] = (0.0, 0.0)
    posture: str | None = None
    pose: list[list[float]] | None = None
    pose_confidence: float = 0.0

class SimpleTracker:
    """Fast centroid tracker with EMA box/pose smoothing and motion state."""
    def __init__(self, max_distance: float = 120.0, max_age: float = 1.5, smoothing: float = 0.65, pose_smoothing: float = 0.55):
        self.max_distance = max_distance
        self.max_age = max_age
        self.smoothing = max(0.0, min(1.0, smoothing))
        self.pose_smoothing = max(0.0, min(1.0, pose_smoothing))
        self.counter = 0
        self.tracks: dict[str, Track] = {}

    @staticmethod
    def center(b): return ((b[0]+b[2])/2, (b[1]+b[3])/2)

    def _ema_box(self, old, new):
        a = self.smoothing
        return tuple(a * n + (1-a) * o for o,n in zip(old,new))

    def _ema_pose(self, old, new):
        if not old or not new or len(old) != len(new): return new
        a = self.pose_smoothing
        out=[]
        for op,np in zip(old,new):
            if len(op) < 3 or len(np) < 3: out.append(np); continue
            out.append([a*np[0]+(1-a)*op[0], a*np[1]+(1-a)*op[1], a*np[2]+(1-a)*op[2]])
        return out

    def update(self, detections):
        now=time(); used=set(); output=[]
        candidates = list(self.tracks.items())
        for d in sorted(detections, key=lambda x: x.confidence, reverse=True):
            cx, cy = self.center(d.bbox); best=None; best_dist=self.max_distance
            for tid,t in candidates:
                if tid in used or t.class_name != d.class_name: continue
                tx,ty=self.center(t.bbox)
                # Predict the next center to reduce ID swaps during fast movement.
                dt=max(0.001, now-t.last_seen)
                px,py=tx+t.velocity[0]*dt,ty+t.velocity[1]*dt
                dist=math.hypot(cx-px,cy-py)
                if dist < best_dist: best=tid; best_dist=dist
            if best is None:
                self.counter += 1; best=f"TRACK-{self.counter:04d}"
                self.tracks[best]=Track(best,d.class_name,d.bbox,d.confidence,now,now)
            else:
                t=self.tracks[best]
                old_c=self.center(t.bbox); new_c=self.center(d.bbox); dt=max(0.001, now-t.last_seen)
                inst_v=((new_c[0]-old_c[0])/dt,(new_c[1]-old_c[1])/dt)
                t.velocity=(0.6*t.velocity[0]+0.4*inst_v[0],0.6*t.velocity[1]+0.4*inst_v[1])
                t.bbox=self._ema_box(t.bbox,d.bbox)
                t.confidence=0.7*t.confidence+0.3*d.confidence
                t.last_seen=now; t.hits += 1
                if d.pose:
                    t.pose=self._ema_pose(t.pose,d.pose)
                    t.pose_confidence=sum(p[2] for p in t.pose if len(p)>2)/max(1,len(t.pose))
            if d.pose and best in self.tracks:
                t=self.tracks[best]; t.pose=self._ema_pose(t.pose,d.pose); t.pose_confidence=sum(p[2] for p in t.pose if len(p)>2)/max(1,len(t.pose))
            d.track_id=best
            if best in self.tracks and self.tracks[best].posture is None:
                self.tracks[best].posture=classify_posture(self.tracks[best].pose, self.tracks[best].bbox)
            elif best in self.tracks and d.pose:
                self.tracks[best].posture=classify_posture(self.tracks[best].pose, self.tracks[best].bbox)
            used.add(best); output.append(self.tracks[best])
        self.tracks={tid:t for tid,t in self.tracks.items() if now-t.last_seen <= self.max_age}
        return output

def classify_posture(points, bbox=None) -> str | None:
    """Lightweight posture classifier over COCO-17 keypoints.

    It is deliberately deterministic and cheap: use keypoint geometry rather
    than a second neural network, making it suitable for CPU-first deployments.
    """
    if not points or len(points) < 15: return None
    def pt(i):
        if i >= len(points) or len(points[i]) < 3 or points[i][2] < 0.25: return None
        return points[i][0], points[i][1]
    nose, ls, rs, lh, rh, lk, rk, la, ra = pt(0),pt(5),pt(6),pt(11),pt(12),pt(13),pt(14),pt(15),pt(16)
    if not (lh and rh and lk and rk and la and ra): return None
    shoulder_y = ((ls[1]+rs[1])/2) if ls and rs else (lh[1]+rh[1])/2
    hip_y=(lh[1]+rh[1])/2; knee_y=(lk[1]+rk[1])/2; ankle_y=(la[1]+ra[1])/2
    torso=max(1.0, abs(hip_y-shoulder_y)); leg=max(1.0, abs(ankle_y-hip_y))
    bbox_h=max(1.0, (bbox[3]-bbox[1]) if bbox else torso+leg)
    if abs(ankle_y-shoulder_y) < bbox_h*0.48 or leg < torso*0.55:
        return "sitting"
    if abs(ankle_y-shoulder_y) < bbox_h*0.38:
        return "lying"
    return "standing"

class DeepSortTracker:
    def __init__(self):
        self._trackers={}
        try:
            from deep_sort_realtime.deepsort_tracker import DeepSort
            self.DeepSort=DeepSort
        except ImportError:
            self.DeepSort=None
    def available(self): return self.DeepSort is not None
    def update(self, camera_id, detections, frame):
        if self.DeepSort is None: return None
        if camera_id not in self._trackers: self._trackers[camera_id]=self.DeepSort(max_age=20,n_init=2,nms_max_overlap=1.0)
        tracker=self._trackers[camera_id]
        raw=[]
        for d in detections:
            x1,y1,x2,y2=d.bbox; raw.append(([x1,y1,x2-x1,y2-y1],d.confidence,d.class_name))
        tracks=tracker.update_tracks(raw, frame=frame)
        output=[]
        for t in tracks:
            if not t.is_confirmed(): continue
            l,tb,r,b=t.to_ltrb(); output.append({"track_id":str(t.track_id),"class_name":t.get_det_class() or "object","bbox":[l,tb,r,b],"confidence":float(t.get_det_conf() or 0.0)})
        return output
