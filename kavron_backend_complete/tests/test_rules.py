from app.events.rules import point_in_polygon

def test_point_in_polygon():
    poly=[[0,0],[10,0],[10,10],[0,10]]
    assert point_in_polygon((5,5),poly)
    assert not point_in_polygon((15,5),poly)
