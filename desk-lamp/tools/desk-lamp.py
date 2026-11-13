"""An articulated architect's desk lamp, built through ryucad's CLI.

Anglepoise stance in the XZ plane, all joint axes along Y: a domed
base with a clevis, a lower arm tilted 32 deg from vertical, an upper
arm leaning back at -38 deg, and a bell shade aimed down-forward.
Joints are one shared part (disc + through cap + centre bore); the
arms are twin bars with cross pins that run in the joint bores.

Everything is placed with fixed instances at computed positions — no
mates — and the clearances are real: arm pins (r4) sit in joint bores
(r4.5), joint caps (r7) pass through the base clevis bores (r7.5),
bars flank the joint discs with 2.5 mm to spare, and the shade neck
rests tangent against the head joint disc.
"""

import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from model import main  # noqa: E402

Z = (0, 0, 1)
X = (1, 0, 0)
Y = (0, 1, 0)

ORANGE = "#d96c33"
STEEL = "#8a8f94"

# Pose: joints and arm directions.
J0 = (0.0, 0.0, 44.0)
D0 = (math.sin(math.radians(32)), 0.0, math.cos(math.radians(32)))
D1 = (-math.sin(math.radians(38)), 0.0, math.cos(math.radians(38)))
L_LO, L_HI = 210.0, 190.0
J1 = tuple(J0[i] + L_LO * D0[i] for i in range(3))
J2 = tuple(J1[i] + L_HI * D1[i] for i in range(3))
# Shade: local +Z (rim -> neck) against the aim (0.94, 0, -0.34).
# The aim is 32 deg off the upper arm: at 15 deg the bell's cone
# stayed within a few mm of the arm bars for its whole length and
# grazed them. The neck sits 4 mm off the head joint disc (99 not
# 95): exactly tangent made the pair's boolean "uncertain".
SZ = (-0.94, 0.0, 0.34)
SX = (0.34, 0.0, 0.94)
SHADE_O = tuple(J2[i] - 99.0 * SZ[i] for i in range(3))  # rim centre
BULB_C = tuple(SHADE_O[i] + 26.0 * SZ[i] for i in range(3))


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


def revolve(p, part, profile, fid="body", **kw):
    sk = p.sketch(part, polygon(profile), fid=f"{fid}-profile", plane="zx")
    p.add(part, "revolve", fid, sketch=sk, axis=f"l{len(profile)}",
          angle="full", **kw)


def fmt(v):
    return ",".join(f"{c:.5f}".rstrip("0").rstrip(".") for c in v)


def org(v):
    return ",".join(f"{c:.3f}mm" for c in v)


def base(p):
    b = p.part("base")
    revolve(p, b, [(0, 0), (0, 85), (10, 85), (14, 78), (19, 50),
                   (23, 34), (26, 30), (26, 0)])
    # Clevis cheeks flank the base joint; bores take its cap.
    for tag, s in (("a", -1), ("b", 1)):
        p.block(b, f"cheek-{tag}", (16, 3.5, 30), (0, 14.75 * s, 37), Z, X,
                operation="join")
    p.add(b, "cylinder", "cheek-bore", {"radius": 7.5, "height": 40},
          ((0, -20, 44), Y, X), operation="cut")
    return b


def joint(p):
    j = p.part("joint")
    p.add(j, "cylinder", "disc", {"radius": 17, "height": 10},
          ((0, -5, 0), Y, X))
    p.add(j, "cylinder", "cap", {"radius": 7, "height": 34},
          ((0, -17, 0), Y, X), operation="join")
    p.add(j, "cylinder", "bore", {"radius": 4.5, "height": 40},
          ((0, -20, 0), Y, X), operation="cut")
    return j


def arm(p, name, length, both_pins):
    a = p.part(name)
    # Bars stop 8 mm short of each joint centre: the joint cap (r7)
    # occupies the axis there, and a bar end on the centre plane would
    # bury its inner corner in the cap. The pins bridge the gap.
    for tag, s in (("a", -1), ("b", 1)):
        p.block(a, f"bar-{tag}", (10, 3.5, length - 16),
                (0, 11 * s, length / 2), Z, X)
    p.add(a, "cylinder", "pin-hi", {"radius": 4, "height": 18},
          ((0, -9, length), Y, X))
    if both_pins:
        p.add(a, "cylinder", "pin-lo", {"radius": 4, "height": 18},
              ((0, -9, 0), Y, X))
    return a


def springs(p):
    s = p.part("springs")
    # The head springs end at 72% of the upper arm: run to 80% their
    # tips reach the shade's bell wall where the cone widens past them.
    specs = [("lo", J0, D0, L_LO, 0.80), ("hi", J1, D1, L_HI, 0.72)]
    for tag, jnt, d, length, end in specs:
        xdir = (d[2], 0.0, -d[0])
        for stag, sgn in (("a", -1), ("b", 1)):
            start = tuple(jnt[i] + 0.15 * length * d[i] for i in range(3))
            start = (start[0], 15.5 * sgn, start[2])
            p.add(s, "cylinder", f"spring-{tag}-{stag}",
                  {"radius": 2, "height": (end - 0.15) * length},
                  (start, d, xdir))
    return s


def shade(p):
    s = p.part("shade")
    # Slim neck (r9): a r12 neck grazes the upper arm's bars where
    # they pass the head joint; the slim neck clears them everywhere.
    revolve(p, s, [(0, 0), (0, 52), (8, 50), (20, 44), (34, 35),
                   (46, 27), (54, 20), (60, 14), (66, 10.5), (78, 9),
                   (78, 0)], fid="outer")
    revolve(p, s, [(0, 0), (0, 49.5), (6, 47.8), (18, 41.8), (32, 32.8),
                   (44, 24.8), (52, 17.5), (58, 11.5), (64, 8.2),
                   (72, 6.8), (74, 6.5), (74, 0)], fid="inner",
            operation="cut")
    return s


def bulb(p):
    b = p.part("bulb")
    p.add(b, "sphere", "globe", {"radius": 11}, ((0, 0, 0), Z, X))
    return b


def assembly(p):
    a = p.part("desk-lamp", assembly=True)
    p.add(a, "instance", "base", of="base", fixed=True)
    p.add(a, "instance", "joint-base", of="joint", origin=org(J0),
          fixed=True)
    x0 = (D0[2], 0.0, -D0[0])
    p.add(a, "instance", "arm-lower", of="arm-lower", origin=org(J0),
          z=fmt(D0), x=fmt(x0), fixed=True)
    p.add(a, "instance", "joint-elbow", of="joint", origin=org(J1),
          fixed=True)
    x1 = (D1[2], 0.0, -D1[0])
    p.add(a, "instance", "arm-upper", of="arm-upper", origin=org(J1),
          z=fmt(D1), x=fmt(x1), fixed=True)
    p.add(a, "instance", "joint-head", of="joint", origin=org(J2),
          fixed=True)
    p.add(a, "instance", "springs", of="springs", fixed=True)
    p.add(a, "instance", "shade", of="shade", origin=org(SHADE_O),
          z=fmt(SZ), x=fmt(SX), fixed=True)
    p.add(a, "instance", "bulb", of="bulb", origin=org(BULB_C), fixed=True)
    return a


def finish(p):
    p.run("materials", "set", "enamel", "--density", "2700 kg/m^3",
          "--colour", ORANGE, "--default")
    p.run("materials", "set", "steel", "--density", "7850 kg/m^3",
          "--colour", STEEL)
    p.run("materials", "set", "glass", "--density", "1200 kg/m^3",
          "--colour", "#fff2cf")
    for part, mat in [("base", "enamel"), ("shade", "enamel"),
                      ("joint", "steel"), ("springs", "steel"),
                      ("bulb", "glass"), ("arm-lower", "enamel"),
                      ("arm-upper", "enamel")]:
        p.run("props", "set", part, f"material={mat}")
    for part in ["base", "shade", "joint", "springs", "bulb"]:
        p.run("colour", part, "--material")
    # Arm bars are enamel; their cross pins are steel (per solid).
    for part in ["arm-lower", "arm-upper"]:
        for bar in ["bar-a", "bar-b"]:
            p.run("colour", f"{part}/{bar}", "--colour", ORANGE)
        p.run("colour", f"{part}/pin-hi", "--colour", STEEL)
    p.run("colour", "arm-lower/pin-lo", "--colour", STEEL)


def build(p):
    p.run("init", "--unit", "mm")
    base(p)
    joint(p)
    arm(p, "arm-lower", L_LO, both_pins=True)
    arm(p, "arm-upper", L_HI, both_pins=False)
    springs(p)
    shade(p)
    bulb(p)
    assembly(p)
    finish(p)


main(build)
