from __future__ import annotations
from datetime import datetime

def point_in_polygon(point, polygon) -> bool:
    x,y=point; inside=False
    if len(polygon)<3: return False
    j=len(polygon)-1
    for i in range(len(polygon)):
        xi,yi=polygon[i]; xj,yj=polygon[j]
        intersects=((yi>y)!=(yj>y)) and (x < (xj-xi)*(y-yi)/(yj-yi+1e-12)+xi)
        if intersects: inside=not inside
        j=i
    return inside

def bottom_center(b): return ((b[0]+b[2])/2, b[3])
