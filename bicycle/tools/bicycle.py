"""A road bicycle, built through ryucad's CLI only.

Bike plane XZ, forward +X, ground z=0, wheels of outer radius 322.
The frame is one part modelled in place in world coordinates, every
tube its own solid, coloured per solid: candy-red frame, black
contact points, silver bar and stem, brown saddle. Wheels are a
separate part (rim, bored hub, 12 spokes) plus a tyre part; the
frame's axles run in the hub bores with 0.5 mm clearance, and the
fork and stay tips stop 1 mm short of the hub surface.
"""

import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.expanduser(
    "~/workspace/ryucad-test/crates/ryucad/tests/corpus"))
from model import main, cross  # noqa: E402

Z = (0, 0, 1)
X = (1, 0, 0)
Y = (0, 1, 0)

RW = (-485, 0, 322)      # rear axle
FW = (545, 0, 322)       # front axle
B = (-70, 0, 288)        # bottom bracket
S = (-212, 0, 712)       # seat cluster
HT = (415, 0, 725)       # head tube top
HB = (443, 0, 652)       # head tube bottom


def tube(p, part, fid, P1, P2, r, **flags):
    d = tuple(b - a for a, b in zip(P1, P2))
    L = math.sqrt(sum(c * c for c in d))
    z = tuple(c / L for c in d)
    ref = (0, 1, 0) if abs(z[1]) < 0.9 else (1, 0, 0)
    x = cross(z, ref)
    n = math.sqrt(sum(c * c for c in x))
    x = tuple(c / n for c in x)
    return p.add(part, "cylinder", fid, {"radius": r, "height": L},
                 (P1, z, x), **flags)


def short_of(P_from, P_to, gap):
    """Point `gap` mm before P_to, along P_from -> P_to."""
    d = tuple(b - a for a, b in zip(P_from, P_to))
    L = math.sqrt(sum(c * c for c in d))
    return tuple(b - gap * c / L for b, c in zip(P_to, d))


def wheel(p):
    w = p.part("wheel")
    p.add(w, "cylinder", "hub", {"radius": 16, "height": 76},
          ((0, -38, 0), Y, X))
    p.add(w, "cylinder", "bore", {"radius": 6.5, "height": 88},
          ((0, -44, 0), Y, X), operation="cut")
    for k in range(12):
        a = math.radians(30 * k)
        s = 1 if k % 2 == 0 else -1
        a2 = a + math.radians(12 * s)
        tube(p, w, f"spoke-{k + 1}",
             (10 * math.cos(a2), 31 * s, 10 * math.sin(a2)),
             (285 * math.cos(a), 0, 285 * math.sin(a)), 1.1,
             operation="join")
    p.add(w, "torus", "rim", {"major_radius": 285, "minor_radius": 6},
          ((0, 0, 0), Y, X))
    return w


def tyre(p):
    t = p.part("tyre")
    p.add(t, "torus", "tyre", {"major_radius": 307, "minor_radius": 15},
          ((0, 0, 0), Y, X))
    return t


RED = "#a41f24"
SILVER = "#c8ccd2"
DARK = "#3a3a3e"
BLACK = "#26262a"
STEEL = "#8a8f98"

COLOURS = {}


def T(p, f, fid, P1, P2, r, colour):
    tube(p, f, fid, P1, P2, r)
    COLOURS[fid] = colour


def BLK(p, f, fid, size, centre, colour):
    p.block(f, fid, size, centre, Z, X)
    COLOURS[fid] = colour


def CYL(p, f, fid, r, origin, h, colour):
    p.add(f, "cylinder", fid, {"radius": r, "height": h}, (origin, Y, X))
    COLOURS[fid] = colour


def frame(p):
    f = p.part("frame")
    # Main triangle. The down tube joins the head tube 55 mm above
    # its bottom (as real frames do) so it clears the front tyre.
    axis = tuple(b - a for a, b in zip(HB, HT))
    n = math.sqrt(sum(c * c for c in axis))
    J = tuple(b + 55 * c / n for b, c in zip(HB, axis))
    T(p, f, "down", B, J, 16, RED)
    T(p, f, "top", S, HT, 15, RED)
    T(p, f, "seat-tube", B, (-232, 0, 752), 14, RED)
    T(p, f, "head-tube", HT, HB, 15, RED)
    CYL(p, f, "bb-shell", 20, (-70, -30, 288), 60, RED)
    BLK(p, f, "cluster", (30, 62, 24), (-214, 0, 710), RED)
    # Stays, splayed out to the dropouts at y=+/-41. Tips stop well
    # short of the hub; dropout plates bridge the last stretch.
    for tag, sy in (("p", 1), ("m", -1)):
        T(p, f, f"seat-stay-{tag}", (-212, 28 * sy, 712),
          short_of((-212, 28 * sy, 712), (-485, 41 * sy, 330), 24), 6, RED)
        T(p, f, f"chain-stay-{tag}", (-70, 28 * sy, 288),
          short_of((-70, 28 * sy, 288), (-485, 41 * sy, 322), 34), 7, RED)
        BLK(p, f, f"dropout-r-{tag}", (52, 5, 44), (-472, 40.5 * sy, 330),
            RED)
        BLK(p, f, f"dropout-f-{tag}", (44, 5, 40), (536, 40.5 * sy, 334),
            RED)
    # Fork and cockpit.
    BLK(p, f, "crown", (34, 94, 26), (440, 0, 656), RED)
    for tag, sy in (("p", 1), ("m", -1)):
        T(p, f, f"fork-{tag}", (443, 41 * sy, 648),
          short_of((443, 41 * sy, 648), (545, 41 * sy, 322), 30), 12, RED)
    T(p, f, "stem", HT, (390, 0, 790), 12, SILVER)
    CYL(p, f, "bar", 12, (390, -200, 790), 400, SILVER)
    CYL(p, f, "grip-p", 14.5, (390, 146, 790), 60, BLACK)
    CYL(p, f, "grip-m", 14.5, (390, -206, 790), 60, BLACK)
    # Seat post and saddle.
    T(p, f, "seat-post", (-226, 0, 738), (-246, 0, 782), 10.5, DARK)
    BLK(p, f, "saddle", (150, 54, 20), (-258, 0, 788), "#6b4226")
    # Drivetrain on a real chainline: ring and cog near y=+47,
    # cranks angled out to pedals at y=+/-74.
    CYL(p, f, "ring", 84, (-70, 44, 288), 6, STEEL)
    CYL(p, f, "cog", 24, (-485, 44, 322), 5, STEEL)
    CYL(p, f, "bb-axle", 8, (-70, -52, 288), 104, STEEL)
    T(p, f, "crank-p", (-70, 50, 288), (28, 66, 192), 9, DARK)
    T(p, f, "crank-m", (-70, -50, 288), (-168, -66, 384), 9, DARK)
    BLK(p, f, "pedal-p", (38, 26, 14), (36, 74, 186), BLACK)
    BLK(p, f, "pedal-m", (38, 26, 14), (-176, -74, 390), BLACK)
    T(p, f, "chain-top", (-70, 47, 372), (-485, 47, 346), 3.5, "#2c2c2e")
    T(p, f, "chain-bottom", (-70, 47, 204), (-485, 47, 298), 3.5,
      "#2c2c2e")
    # Axles (run in the hub bores) with nuts outside the hub faces.
    CYL(p, f, "axle-f", 6, (545, -44, 322), 88, STEEL)
    CYL(p, f, "axle-r", 6, (-485, -44, 322), 88, STEEL)
    for fid, cx, oy in (("nut-f-p", 545, 38.5), ("nut-f-m", 545, -42.5),
                        ("nut-r-p", -485, 38.5), ("nut-r-m", -485, -42.5)):
        CYL(p, f, fid, 9, (cx, oy, 322), 4, STEEL)
    # Kickstand.
    T(p, f, "kickstand", (-150, -16, 278), (-262, -16, 2), 7, BLACK)
    return f


def assembly(p):
    a = p.part("bicycle", assembly=True)
    p.add(a, "instance", "frame", of="frame", fixed=True)
    for tag, pt in (("front", FW), ("rear", RW)):
        org = f"{pt[0]}mm,0mm,{pt[2]}mm"
        p.add(a, "instance", f"wheel-{tag}", of="wheel", origin=org,
              fixed=True)
        p.add(a, "instance", f"tyre-{tag}", of="tyre", origin=org,
              fixed=True)
    return a


def finish(p):
    p.run("materials", "set", "aluminium", "--density", "2700 kg/m^3",
          "--colour", "#a41f24")
    p.run("materials", "set", "wheel-metal", "--density", "2700 kg/m^3",
          "--colour", "#c8ccd2")
    p.run("materials", "set", "rubber", "--density", "1100 kg/m^3",
          "--colour", "#1c1c1e")
    p.run("props", "set", "frame", "material=aluminium")
    p.run("props", "set", "wheel", "material=wheel-metal")
    p.run("props", "set", "tyre", "material=rubber")
    p.run("colour", "wheel", "--material")
    p.run("colour", "tyre", "--material")
    for fid, c in COLOURS.items():
        p.run("colour", f"frame/{fid}", "--colour", c)


def build(p):
    p.run("init", "--unit", "mm")
    wheel(p)
    tyre(p)
    frame(p)
    assembly(p)
    finish(p)


main(build)
