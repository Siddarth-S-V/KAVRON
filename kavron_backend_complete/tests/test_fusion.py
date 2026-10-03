from app.ai.fusion import DetectionFusion
from app.core.types import Detection

def test_fuses_overlapping():
    d1=Detection('c',1,0,'person',.8,(0,0,10,10),0,['a'])
    d2=Detection('c',1,0,'person',.9,(1,1,11,11),0,['b'])
    out=DetectionFusion(.5).fuse([d1,d2])
    assert len(out)==1
    assert out[0].confidence==.9
