"""The impeller again, its 7 blades now real sweeps: a rectangular
section swept along a circular-arc path from root to tip, scaled to 0.65
on the way so each blade tapers in height and thickness. The sweep is in
ryucad 0.9.0-pre.3's CLI (`feature add ... sweep`)."""
import json, math, os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, "/workspace/work/ryucad/crates/ryucad/tests/corpus")
from model import main

Z = (0, 0, 1); X = (1, 0, 0)
BLADES = 7
R0, R1, SWEEP, RC = 22.0, 61.0, 75.0, 48.0   # root, tip, turn (deg), arc radius (mm)
T, H, SCALE = 3.2, 18.0, "0.65"


def arc_geometry(base):
    a0, a1 = math.radians(base), math.radians(base + SWEEP)
    p0 = (R0 * math.cos(a0), R0 * math.sin(a0))
    p1 = (R1 * math.cos(a1), R1 * math.sin(a1))
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    h = math.sqrt(RC ** 2 - (L / 2) ** 2)
    nx, ny = -dy / L, dx / L               # left of p0->p1: centre there makes p0->p1 CCW
    c = (mx + nx * h, my + ny * h)
    t = (-(p0[1] - c[1]), p0[0] - c[0])   # CCW tangent at p0
    tl = math.hypot(*t)
    return p0, p1, c, (t[0] / tl, t[1] / tl)


def pt(i, x, y):
    return {"op": "add", "type": "point", "id": i, "at": [f"{x:.5f} mm", f"{y:.5f} mm"]}


def build(p):
    p.run("init", "--unit", "mm")
    c = p.part("impeller")
    p.add(c, "cylinder", "plate", {"radius": 70, "height": 6}, ((0, 0, 0), Z, X))
    p.add(c, "cone", "hub", {"radius": 26, "height": 30, "top_radius": 15},
          ((0, 0, 6), Z, X), operation="join")
    sweeps = []
    for b in range(BLADES):
        p0, p1, cc, t = arc_geometry(b * 360 / BLADES)
        path = p.sketch(c, [pt("s", *p0), pt("e", *p1), pt("c", *cc),
                            {"op": "add", "type": "arc", "id": "a1", "center": "c",
                             "start": "s", "end": "e"}],
                        fid=f"blade-{b+1}-path", place=((0, 0, 6), Z, X))
        # section at the root, normal to the path: sketch x is up, y across
        rect = [(-1, -T / 2), (H, -T / 2), (H, T / 2), (-1, T / 2)]
        ops = [pt(f"p{i+1}", *q) for i, q in enumerate(rect)]
        ops += [{"op": "add", "type": "line", "id": f"l{i+1}", "start": f"p{i+1}",
                 "end": f"p{(i+1) % 4 + 1}"} for i in range(4)]
        prof = p.sketch(c, ops, fid=f"blade-{b+1}-section",
                        place=((p0[0], p0[1], 6), (t[0], t[1], 0), Z))
        sweeps.append((f"blade-{b+1}", prof, path))
    for fid, prof, path in sweeps:
        p.add(c, "sweep", fid, sketch=prof, path=f"{c}/{path}/a1", law="minimal",
              scale=SCALE, operation="join", target="plate")
    p.add(c, "cylinder", "bore", {"radius": 8, "height": 50}, ((0, 0, -5), Z, X),
          operation="cut")
    p.block(c, "key", (4, 6, 50), (9, 0, 20), Z, X, operation="cut")
    for k in range(BLADES):
        a = math.radians(k * 360 / BLADES + SWEEP + 180 / BLADES)
        p.add(c, "cylinder", f"bolt-{k+1}", {"radius": 2.5, "height": 10},
              ((65.5 * math.cos(a), 65.5 * math.sin(a), -2), Z, X), operation="cut")
    p.run("materials", "set", "6061-T6", "--density", "2700 kg/m^3", "--colour", "#b8c4cf")
    p.run("props", "set", "impeller", "material=6061-T6")


if __name__ == "__main__":
    main(build)
