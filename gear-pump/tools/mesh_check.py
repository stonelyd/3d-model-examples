"""Optional 2D check of the gear pair's geometric meshing (needs shapely):
rotates the drive outline by theta and the idler by 15 deg - theta, as the
assembly's revolute mates do, over one tooth pitch in 3,000 steps, and
prints the largest overlap area and the smallest gap between the outlines.

    python3 tools/mesh_check.py
"""
import os
from shapely.geometry import Polygon
from shapely import affinity

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "gear-pump.py")).read().replace("main(build)\n", "")
g = {"__file__": os.path.join(here, "gear-pump.py"), "__name__": "gear_pump"}
exec(compile(src, "gear-pump.py", "exec"), g)
P = Polygon(g["gear_outline"]())
cd = g["CD"]
overlap, gap = 0.0, 1e9
for i in range(3000):
    th = 30.0 * i / 3000
    d = affinity.translate(affinity.rotate(P, th, origin=(0, 0)), 0, cd / 2)
    q = affinity.translate(affinity.rotate(P, 15 - th, origin=(0, 0)), 0, -cd / 2)
    overlap = max(overlap, d.intersection(q).area)
    gap = min(gap, d.distance(q))
print(f"largest overlap {overlap:.6f} mm2, smallest gap {gap:.4f} mm")
