"""Six-slot Geneva (Maltese cross) indexing mechanism, ryucad CLI only.

Geometry from the standard relations for n = 6, centre distance
a = 60 mm: pin radius R = a*sin(pi/n) = 30, star pitch radius
a*cos(pi/n) = 51.96. The checked pose is the LOCKED position (pin at
120 deg on the driver, clear of the star); the driver's r=21 locking
disc sits in the star's r=21.6 concave notch with 0.6 mm clearance.

Slot dimensions were settled by a 2D sweep of the roller through the
engagement (driver angle -60..+60 deg, star following the exact
Geneva relation): with capsule end centres at radii 25 and 57 and
half-width 5.3 (slot 10.6 for a 10 mm roller), the minimum roller
clearance over the whole engagement is 0.30 mm. (End centre 33, as
first sketched, jams: the pin centre reaches radius 30 from the star
centre at mid-engagement, inside the roller's reach of a 33 slot end.)

Construction: pin plate below the star plane carrying a stud + brass
roller up through the slot band; locking disc coplanar with the star
on the same hub — the classic two-element driver.
"""

import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.expanduser(
    "~/workspace/ryucad-test/crates/ryucad/tests/corpus"))
from model import main, polar  # noqa: E402

Z = (0, 0, 1)
X = (1, 0, 0)


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


def capsule(r_in, r_out, hw):
    """A radial slot outline: capsule axis from (r_in,0) to (r_out,0)."""
    pts = [(r_in, -hw), (r_out, -hw)]
    for a in range(-60, 61, 30):
        t = math.radians(a)
        pts.append((r_out + hw * math.cos(t), hw * math.sin(t)))
    pts.append((r_out, hw))
    pts.append((r_in, hw))
    for a in range(120, 241, 30):
        t = math.radians(a)
        pts.append((r_in + hw * math.cos(t), hw * math.sin(t)))
    return pts


def backplate(p):
    b = p.part("backplate")
    p.block(b, "plate", (180, 130, 8), (30, 0, -8), Z, X)
    for name, cx in (("boss-driver", 0), ("boss-star", 60)):
        p.add(b, "cylinder", name, {"radius": 12, "height": 9.4},
              ((cx, 0, -4), Z, X), operation="join")
        p.add(b, "cylinder", f"{name}-bore", {"radius": 6.4, "height": 22},
              ((cx, 0, -14), Z, X), operation="cut")
    # Feet sit at the +y edge in the build frame; the assembly rotates
    # the whole rig -90 deg about X, which puts that edge at the bottom.
    for sx in (-30, 90):
        p.block(b, f"foot-{sx}", (36, 26, 70), (sx, 58, -40), Z, X,
                operation="join")
    for bx, by in ((-45, 50), (-45, -50), (105, 50), (105, -50)):
        p.add(b, "cylinder", f"bolt-{bx}-{by}", {"radius": 3.5,
              "height": 3.5}, ((bx, by, -4), Z, X), operation="join")
    return b


def driver(p):
    """In place at the locked pose: pin at 120 deg, radius 30."""
    d = p.part("driver")
    p.add(d, "cylinder", "hub", {"radius": 10, "height": 20.3},
          ((0, 0, 5.7), Z, X))
    p.add(d, "cylinder", "locking-disc", {"radius": 21, "height": 10},
          ((0, 0, 16), Z, X), operation="join")
    arm_dir = (-0.5, 0.8660254, 0)
    p.block(d, "pin-arm", (36, 12, 10), (-6.5, 11.258, 10.7), Z, arm_dir,
            operation="join")
    px, py, _ = polar(30, 120)
    p.add(d, "cylinder", "pin-stud", {"radius": 3.5, "height": 15},
          ((px, py, 12), Z, X), operation="join")
    p.add(d, "cylinder", "bore", {"radius": 6.4, "height": 24},
          ((0, 0, 4), Z, X), operation="cut")
    return d


def roller(p):
    r = p.part("roller")
    p.add(r, "cylinder", "sleeve", {"radius": 5, "height": 10.4},
          ((0, 0, 0), Z, X))
    p.add(r, "cylinder", "bore", {"radius": 3.8, "height": 12.4},
          ((0, 0, -1), Z, X), operation="cut")
    return r


def star(p):
    s = p.part("star")
    blank = p.sketch(s, [{"op": "add", "type": "point", "id": "c",
                          "at": ["0", "0"]},
                         {"op": "add", "type": "circle", "id": "rim",
                          "center": "c", "r": "56 mm"}],
                     fid="blank", place=((0, 0, 0), Z, X))
    p.add(s, "extrude", "disc", sketch=blank, length="10 mm")
    p.add(s, "cylinder", "hub", {"radius": 10.5, "height": 14},
          ((0, 0, 0), Z, X), operation="join")
    p.add(s, "cylinder", "bore", {"radius": 6.4, "height": 18},
          ((0, 0, -2), Z, X), operation="cut")
    slot = p.sketch(s, polygon(capsule(25, 57, 5.3)), fid="slot-profile",
                    place=((0, 0, 0), Z, X))
    p.add(s, "extrude", "slot", sketch=slot, operation="cut",
          extent="through_all", both=True)
    p.add(s, "pattern", "slots", seed="slot", form="circular", axis="z",
          count="6", angle="360")
    bx, by, _ = polar(60, 30)
    p.add(s, "cylinder", "notch", {"radius": 21.6, "height": 14},
          ((bx, by, -2), Z, X), operation="cut")
    p.add(s, "pattern", "notches", seed="notch", form="circular",
          axis="z", count="6", angle="360")
    return s


def star_shaft(p):
    s = p.part("star-shaft")
    p.add(s, "cylinder", "shaft", {"radius": 6, "height": 38},
          ((60, 0, -4), Z, X))
    p.add(s, "cylinder", "collar", {"radius": 11, "height": 2.2},
          ((60, 0, 13.5), Z, X), operation="join")
    p.add(s, "cylinder", "pointer-disc", {"radius": 14, "height": 2.5},
          ((60, 0, 31), Z, X), operation="join")
    p.block(s, "pointer", (22, 4, 2.5), (49, 0, 32.25), Z, X,
            operation="join")
    return s


def driver_shaft(p):
    s = p.part("driver-shaft")
    p.add(s, "cylinder", "shaft", {"radius": 6, "height": 53},
          ((0, 0, -24), Z, X))
    p.add(s, "cylinder", "cap", {"radius": 8, "height": 3},
          ((0, 0, 26.3), Z, X), operation="join")
    p.block(s, "crank-arm", (34, 9, 5), (9, 0, -25.5), Z, X,
            operation="join")
    # Grip: separate solid in the same part (face contact only), so it
    # can carry the wood colour.
    p.add(s, "cylinder", "grip", {"radius": 5, "height": 12},
          ((24, 0, -40), Z, X))
    return s


def assembly(p):
    # Every instance is rotated -90 deg about X (local z -> world +y,
    # local y -> world -z) and lifted 71 mm, so the backplate stands
    # vertical as a demo rig with its feet on the ground (z = 0).
    a = p.part("geneva", assembly=True)
    frame = {"z": "0,1,0", "x": "1,0,0"}
    for part in ("backplate", "driver", "driver-shaft", "star-shaft"):
        p.add(a, "instance", part, of=part, origin="0mm,0mm,71mm",
              fixed=True, **frame)
    px, py, _ = polar(30, 120)
    p.add(a, "instance", "roller", of="roller",
          origin=f"{px:.4f}mm,15.8mm,{71 - py:.4f}mm", fixed=True, **frame)
    # Star rotated 150 deg in its own frame: local notch at 30 deg then
    # faces the driver, slots at 150/210/... — the locked pose.
    p.add(a, "instance", "star", of="star",
          origin="60mm,16mm,71mm", z="0,1,0", x="-0.8660254,0,-0.5",
          fixed=True)
    return a


def finish(p):
    p.run("materials", "set", "steel", "--density", "7850 kg/m^3",
          "--colour", "#b9bec4", "--default")
    p.run("materials", "set", "cast-iron", "--density", "7200 kg/m^3",
          "--colour", "#2e3138")
    p.run("materials", "set", "brass", "--density", "8500 kg/m^3",
          "--colour", "#c9a227")
    p.run("materials", "set", "wood", "--density", "700 kg/m^3",
          "--colour", "#7b4b2a")
    p.run("props", "set", "backplate", "material=cast-iron")
    p.run("colour", "backplate", "--material")
    p.run("props", "set", "driver", "material=steel")
    p.run("colour", "driver", "--material")
    p.run("props", "set", "roller", "material=brass")
    p.run("colour", "roller", "--material")
    p.run("props", "set", "star", "material=steel")
    p.run("colour", "star", "--colour", "#b03030")
    p.run("props", "set", "star-shaft", "material=steel")
    p.run("colour", "star-shaft", "--colour", "#8a8f98")
    p.run("props", "set", "driver-shaft", "material=steel")
    p.run("colour", "driver-shaft", "--colour", "#8a8f98")
    p.run("colour", "driver-shaft/grip", "--colour", "#7b4b2a")


def build(p):
    p.run("init", "--unit", "mm")
    backplate(p)
    driver(p)
    roller(p)
    star(p)
    star_shaft(p)
    driver_shaft(p)
    assembly(p)
    finish(p)


main(build)
