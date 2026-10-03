from app.ai.tracker import SimpleTracker, classify_posture
from app.core.types import Detection

def det(box, pose=None):
    d=Detection("C",1,0,"person",0.9,tuple(box),1.0,["test"])
    d.pose=pose
    return d

def test_tracker_keeps_id_and_smooths_box():
    tr=SimpleTracker(max_distance=100, max_age=2, smoothing=0.5)
    a=tr.update([det((0,0,100,200))])[0]
    b=tr.update([det((10,0,110,200))])[0]
    assert a.track_id == b.track_id
    assert 0 < b.bbox[0] < 10

def test_posture_classification_standing():
    pts=[[50,10,1],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[40,30,1],[60,30,1],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[42,80,1],[58,80,1],[40,130,1],[60,130,1],[38,185,1],[62,185,1]]
    assert classify_posture(pts,(20,5,80,195)) == "standing"
