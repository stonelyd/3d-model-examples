"""A modern three-blade wind turbine on a grass hill disc, built
through ryucad's CLI only.

Tower is a revolved taper with flange rings; the nacelle points +Y;
the rotor (hub + three blades) sits at (0, 38, 152). Blades are
silhouette extrusions with a separate red tip solid, instanced at
10/130/250 degrees about the Y axis. Five low-poly trees (trunk +
two stacked cones) dot the hill.
"""

import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.expanduser(
    "~/workspace/ryucad-test/crates/ryucad/tests/corpus"))
from model import main, mm  # noqa: E402

Z = (0, 0, 1)
X = (1, 0, 0)
Y = (0, 1, 0)


def polygon(points, prefix=""):
    ops = []
    for i, (x, y) in enumerate(points):
        ops.append({"op": "add", "type": "point", "id": f"{prefix}p{i + 1}",
                    "at": [f"{x} mm", f"{y} mm"]})
    n = len(points)
    for i in range(n):
        ops.append({"op": "add", "type": "line", "id": f"{prefix}l{i + 1}",
                    "start": f"{prefix}p{i + 1}",
                    "end": f"{prefix}p{(i + 1) % n + 1}"})
    return ops


def ground(p):
    g = p.part("ground")
    p.add(g, "cylinder", "hill", {"radius": 170, "height": 10},
          ((0, 0, -10), Z, X))
    return g


def tower(p):
    t = p.part("tower")
    profile = [(0, 0), (0, 17), (3, 17), (4.5, 15.2), (12, 14.3),
               (60, 11.6), (120, 9.4), (140, 8.8), (144, 8.6),
               (144, 10.6), (148, 10.6), (148, 0)]
    sk = p.sketch(t, polygon(profile), fid="profile", plane="zx")
    p.add(t, "revolve", "body", sketch=sk, axis=f"l{len(profile)}",
          angle="full")
    return t


def nacelle(p):
    n = p.part("nacelle")
    p.block(n, "body", (20, 52, 20), (0, 2, 0), Z, X)
    p.add(n, "cylinder", "nose", {"radius": 9.5, "height": 12},
          ((0, 24, 0), Y, X), operation="join")
    p.add(n, "cylinder", "spinner-base", {"radius": 6, "height": 5},
          ((0, 34, 0), Y, X), operation="join")
    p.add(n, "cylinder", "tail", {"radius": 9, "height": 6},
          ((0, -24, 0), (0, -1, 0), X), operation="join")
    p.add(n, "sphere", "tail-cap", {"radius": 9}, ((0, -30, 0), Z, X),
          operation="join")
    p.block(n, "vent", (10, 18, 3), (0, -6, 11), Z, X, operation="join")
    p.add(n, "cylinder", "yaw-drum", {"radius": 10, "height": 6},
          ((0, 0, -13), Z, X), operation="join")
    # Shaft socket: the hub shaft (r5) runs in this r5.3 bore.
    p.add(n, "cylinder", "shaft-socket", {"radius": 5.3, "height": 13},
          ((0, 27, 0), Y, X), operation="cut")
    return n


def hub(p):
    h = p.part("hub")
    p.add(h, "sphere", "ball", {"radius": 8.5}, ((0, 0, 0), Z, X))
    p.add(h, "cylinder", "shaft", {"radius": 5, "height": 14},
          ((0, -14, 0), Y, X), operation="join")
    # Blade sockets (r4.6) along the three blade axes: blade roots
    # (r4.5) sit in them with 0.1 mm clearance, never overlapping.
    for deg in (10, 130, 250):
        t = math.radians(deg)
        d = (math.sin(t), 0, math.cos(t))
        org = (10 * d[0], 0, 10 * d[2])
        p.add(h, "cylinder", f"socket-{deg}", {"radius": 4.6,
              "height": 6.5}, (org, (-d[0], 0, -d[2]), Y),
              operation="cut")
    return h


# Blade silhouette: (chord offset u, length v). Main blade stops at
# v=52; the tip is a second solid sharing the v=52 face.
BLADE_MAIN = [(-3.9, 5.5), (4.4, 5.5), (3.2, 18), (2.6, 36), (1.8, 52),
              (-1.2, 52), (-2, 36), (-2.8, 18)]
BLADE_TIP = [(1.8, 52), (0.8, 63), (0, 64.5), (-1.2, 52)]


def blade(p):
    b = p.part("blade")
    place = ((0, 1.1, 0), (0, -1, 0), X)  # extrude -Y, u->X, v->+Z
    sk = p.sketch(b, polygon(BLADE_MAIN), fid="profile", place=place)
    p.add(b, "extrude", "body", sketch=sk, length="2.2 mm")
    p.add(b, "cylinder", "root", {"radius": 4.5, "height": 6},
          ((0, 0, 5.5), Z, X), operation="join")
    sk2 = p.sketch(b, polygon(BLADE_TIP), fid="tip-profile", place=place)
    p.add(b, "extrude", "tip", sketch=sk2, length="2.2 mm")
    return b


def trees(p):
    ta = p.part("trunk-a")
    p.add(ta, "cylinder", "trunk", {"radius": 1.2, "height": 4},
          ((0, 0, 0), Z, X))
    tb = p.part("trunk-b")
    p.add(tb, "cylinder", "trunk", {"radius": 1.5, "height": 5},
          ((0, 0, 0), Z, X))
    fa = p.part("foliage-a")
    p.add(fa, "cone", "cone-1", {"radius": 5, "height": 10},
          ((0, 0, 4), Z, X))
    p.add(fa, "cone", "cone-2", {"radius": 3.6, "height": 8},
          ((0, 0, 10), Z, X), operation="join")
    fb = p.part("foliage-b")
    p.add(fb, "cone", "cone-1", {"radius": 6.5, "height": 13},
          ((0, 0, 5), Z, X))
    p.add(fb, "cone", "cone-2", {"radius": 4.6, "height": 10},
          ((0, 0, 13), Z, X), operation="join")


SPOTS = [(62, 44, "a"), (-84, 28, "b"), (104, -58, "a"),
         (-52, -96, "b"), (34, -124, "a")]


def assembly(p):
    a = p.part("wind-turbine", assembly=True)
    p.add(a, "instance", "ground", of="ground", fixed=True)
    p.add(a, "instance", "tower", of="tower", fixed=True)
    p.add(a, "instance", "nacelle", of="nacelle",
          origin="0mm,0mm,161mm", fixed=True)
    p.add(a, "instance", "hub", of="hub",
          origin="0mm,47.5mm,161mm", fixed=True)
    for i, deg in enumerate((10, 130, 250)):
        t = math.radians(deg)
        d = (math.sin(t), 0, math.cos(t))
        c = (math.cos(t), 0, -math.sin(t))
        p.add(a, "instance", f"blade-{i + 1}", of="blade",
              origin="0mm,47.5mm,161mm",
              z=",".join(mm(v) for v in d),
              x=",".join(mm(v) for v in c), fixed=True)
    for i, (x, y, s) in enumerate(SPOTS):
        p.add(a, "instance", f"trunk-{i + 1}", of=f"trunk-{s}",
              origin=f"{x}mm,{y}mm,0mm", fixed=True)
        p.add(a, "instance", f"foliage-{i + 1}", of=f"foliage-{s}",
              origin=f"{x}mm,{y}mm,0mm", fixed=True)
    return a


def finish(p):
    p.run("materials", "set", "painted-steel", "--density", "7850 kg/m^3",
          "--colour", "#eef0ee")
    p.run("materials", "set", "composite", "--density", "1600 kg/m^3",
          "--colour", "#d7dadb")
    p.run("materials", "set", "fibreglass", "--density", "1900 kg/m^3",
          "--colour", "#f2f3f2")
    p.run("materials", "set", "earth", "--density", "1400 kg/m^3",
          "--colour", "#5d8a4a")
    p.run("materials", "set", "wood", "--density", "700 kg/m^3",
          "--colour", "#6b4a2f")
    p.run("materials", "set", "foliage", "--density", "350 kg/m^3",
          "--colour", "#2f5d33")
    for part, mat in [("tower", "painted-steel"), ("nacelle", "composite"),
                      ("hub", "composite"), ("blade", "fibreglass"),
                      ("ground", "earth"), ("trunk-a", "wood"),
                      ("trunk-b", "wood"), ("foliage-a", "foliage"),
                      ("foliage-b", "foliage")]:
        p.run("props", "set", part, f"material={mat}")
        p.run("colour", part, "--material")
    p.run("colour", "blade/tip", "--colour", "#c8373c")


def build(p):
    p.run("init", "--unit", "mm")
    ground(p)
    tower(p)
    nacelle(p)
    hub(p)
    blade(p)
    trees(p)
    assembly(p)
    finish(p)


main(build)
