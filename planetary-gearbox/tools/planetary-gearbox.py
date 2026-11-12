"""A NEMA 17 single-stage planetary gearbox, 5:1, as a ryucad assembly built
through the CLI only.

    python3 -I tools/planetary-gearbox.py <ryucad> <empty folder>

Gearing: module 1, 25 deg pressure angle (so the 12-tooth sun needs no
undercut), sun 12T, three planets 18T, fixed ring 48T: i = 1 + 48/12 = 5.
Tooth flanks are true involutes sampled as polylines (8 segments a flank),
thinned 0.06 mm a flank for backlash; every tooth space is cut once and
circularly patterned.

Frame: z is the motor axis, z = 0 the motor's mounting face, output toward
+z. Parts that appear once are modelled where the assembly places them;
repeated parts (planets and what rides with them, bearings, screws) in their
own frame.

Motion: the carrier's revolute is driven by the assembly parameter `out`.
ryucad has no gear mate, so the sun and the planets are revolutes driven by
the derived parameters `sun = out * 5` and `planet = out * -8 / 3` (planet
spin relative to the carrier): the gear train's kinematics are imposed by
those expressions, not solved from tooth contact.
"""
import json
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import main  # noqa: E402

Z, X = (0, 0, 1), (1, 0, 0)
A = "gearbox"

# ------------------------------------------------------------ gear data
M, PA, BL = 1.0, math.radians(25), 0.06
ZS, ZP, ZR = 12, 18, 48
CD = M * (ZS + ZP) / 2           # 15 mm sun-planet centre distance
PLANET_PHASE = 10.0              # deg: a planet tooth on +10 deg meshes at carrier 0

# z levels (mm)
PLATE = (0.0, 5.0)
SUN_HUB = (6.0, 10.15)
SUN_TEETH = (10.0, 18.5)
PLANET_MID, PLANET_W = 14.25, 8.0
PIN_Z0, PIN_L = 9.5, 13.0
CARRIER = (19.5, 23.5)
RING = (5.0, 24.0)
COVER = (24.0, 30.0, 40.5)
BRG_A, BRG_B = 25.0, 33.0
HOUSING_SCREW_R, MOTOR_SCREW = 28.0, 15.5

STEEL, BLUE, DARK = "#9aa0a8", "#3b6ea5", "#2a2c30"


def inv(a):
    return math.tan(a) - a


# --------------------------------------------------------------- helpers
def pts_lines(points, pre="p", lpre="l"):
    ops = []
    for i, (a, b) in enumerate(points):
        ops.append({"op": "add", "type": "point", "id": f"{pre}{i+1}",
                    "at": [f"{a:.6f} mm", f"{b:.6f} mm"]})
    n = len(points)
    for i in range(n):
        ops.append({"op": "add", "type": "line", "id": f"{lpre}{i+1}",
                    "start": f"{pre}{i+1}", "end": f"{pre}{(i+1) % n + 1}"})
    return ops


def rev(p, part, fid, prof, **flags):
    """Revolve a closed (z, r) profile about the part's z axis."""
    zs = [a for a, _ in prof]
    ops = pts_lines(prof)
    ops += [{"op": "add", "type": "point", "id": "ax1", "at": [f"{min(zs)-1:.6f} mm", "0 mm"]},
            {"op": "add", "type": "point", "id": "ax2", "at": [f"{max(zs)+1:.6f} mm", "0 mm"]},
            {"op": "add", "type": "line", "id": "axis", "start": "ax1", "end": "ax2"}]
    sk = p.sketch(part, ops, fid=f"{fid}-profile", plane="zx")
    return p.add(part, "revolve", fid, sketch=sk, axis="axis", angle="full", **flags)


def ring_prof(r0, r1, z0, z1):
    return [(z0, r0), (z1, r0), (z1, r1), (z0, r1)]


def cyl(p, part, fid, r, z0, z1, at=(0, 0), **flags):
    return p.add(part, "cylinder", fid, {"radius": f"{r:.6f}", "height": f"{z1-z0:.6f}"},
                 ((at[0], at[1], z0), Z, X), **flags)


def polar(r, deg):
    a = math.radians(deg)
    return (r * math.cos(a), r * math.sin(a))


def circ(p, part, fid, seeds, n, **flags):
    return p.add(part, "pattern", fid, seed=seeds, form="circular", axis="z", count=str(n),
                 angle="360", **flags)


def colour(p, part, c):
    p.run("colour", part, "--colour", c)


def extrude_poly(p, part, fid, poly, z0, length, **flags):
    sk = p.sketch(part, pts_lines(poly), fid=f"{fid}-profile", place=((0, 0, z0), Z, X))
    return p.add(part, "extrude", fid, sketch=sk, length=f"{length:.6f} mm", **flags)


# ------------------------------------------------------- involute spaces
def ext_space(z, n=8):
    """One tooth space of an external gear (teeth centred on 0 deg and on
    360/z deg), centred on 180/z deg, as a polygon reaching past the tip
    circle by 0.5 mm."""
    rp = M * z / 2
    rb, ra, rf = rp * math.cos(PA), rp + M, rp - 1.25 * M
    psi = (math.pi / 2) / z - BL / rp

    def th(r):
        return psi + inv(PA) - inv(math.acos(rb / max(r, rb)))
    r0 = max(rb, rf)
    rs = [r0 + (ra - r0) * i / n for i in range(n + 1)]
    pitch = 2 * math.pi / z
    right = [(r, th(r)) for r in rs]                    # tooth at 0, its +side flank
    if rf < rb:
        right.insert(0, (rf, th(rb)))
    left = [(r, pitch - a) for r, a in reversed(right)]  # next tooth's -side flank
    out = ra + 0.5
    pts = right + [(out, right[-1][1] - 0.02), (out, left[0][1] + 0.02)] + left
    # root arc between the two root ends, through the space's centre
    a0, a1 = right[0][1], left[-1][1]
    pts += [(rf, a1 + (a0 - a1) * i / 3) for i in range(1, 3)]
    return [(r * math.cos(a), r * math.sin(a)) for r, a in pts]


def int_space(z, n=8):
    """One tooth space of an internal gear (teeth centred on 0 deg), centred
    on 180/z deg, reaching inside the tip circle by 0.5 mm."""
    rp = M * z / 2
    rb, ra, rf = rp * math.cos(PA), rp - M, rp + 1.25 * M
    psi = (math.pi / 2) / z + BL / rp
    c = math.pi / z

    def th(r):
        return psi + inv(PA) - inv(math.acos(rb / r))
    rs = [ra + (rf - ra) * i / n for i in range(n + 1)]
    lo = [(r, c - th(r)) for r in rs]
    hi = [(r, c + th(r)) for r in reversed(rs)]
    root = [(rf, c - th(rf) + 2 * th(rf) * i / 3) for i in range(1, 3)]
    inner = ra - 0.5
    pts = lo + root + hi + [(inner, c + th(ra) + 0.02), (inner, c - th(ra) - 0.02)]
    return [(r * math.cos(a), r * math.sin(a)) for r, a in pts]


def rot(poly, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(x * ca - y * sa, x * sa + y * ca) for x, y in poly]


# ------------------------------------------------------------------ parts
def motor(p):
    c = p.part("nema17-motor")
    s = 42.3
    p.block(c, "body", (s, s, 40), (0, 0, -20), Z, X)
    for i in range(4):
        d = (math.cos(math.radians(45 + 90 * i)), math.sin(math.radians(45 + 90 * i)), 0)
        r = 25.4 + 5   # chamfer faces 25.4 mm from the axis (about 4.4 mm across)
        p.block(c, f"chamfer-{i+1}", (10, 20, 42), (r * d[0], r * d[1], -20), Z, d,
                operation="cut", target="body")
    cyl(p, c, "pilot", 11.0, -0.5, 2.0, operation="join", target="body")
    cyl(p, c, "shaft-bore", 2.6, -9.0, 2.5, operation="cut", target="body")
    cyl(p, c, "tap", 1.5, -4.5, 0.5, at=(MOTOR_SCREW, MOTOR_SCREW), operation="cut",
        target="body")
    circ(p, c, "taps", ["tap"], 4)
    # the connector housing on the back
    p.block(c, "connector", (16, 6, 6), (0, -s / 2 - 2.5, -34), Z, X, operation="join",
            target="body")
    colour(p, c, DARK)

    sh = p.part("motor-shaft")
    cyl(p, sh, "shaft", 2.5, -7.0, 18.2)
    p.block(sh, "flat", (4, 8, 15.2), (2.0 + 2, 0, 4.0 + 7.6), Z, X, operation="cut",
            target="shaft")
    colour(p, sh, "#c8ccd2")


def input_plate(p):
    c = p.part("input-plate")
    cyl(p, c, "plate", 32.0, *PLATE)
    cyl(p, c, "pilot-recess", 11.2, -0.5, 2.5, operation="cut", target="plate")
    cyl(p, c, "bore", 6.5, -0.5, 5.5, operation="cut", target="plate")
    cyl(p, c, "motor-hole", 1.7, -0.5, 5.5, at=(MOTOR_SCREW, MOTOR_SCREW), operation="cut",
        target="plate")
    cyl(p, c, "motor-cbore", 3.1, 1.8, 5.5, at=(MOTOR_SCREW, MOTOR_SCREW), operation="cut",
        target="plate")
    circ(p, c, "motor-holes", ["motor-hole", "motor-cbore"], 4)
    cyl(p, c, "tap", 1.5, -0.5, 5.5, at=(HOUSING_SCREW_R, 0), operation="cut", target="plate")
    circ(p, c, "taps", ["tap"], 6)
    colour(p, c, BLUE)


def sun_gear(p):
    c = p.part("sun-gear")
    ra = M * ZS / 2 + M
    cyl(p, c, "blank", ra, *SUN_TEETH)
    extrude_poly(p, c, "space", ext_space(ZS), SUN_TEETH[0] - 0.5,
                 SUN_TEETH[1] - SUN_TEETH[0] + 1.0, operation="cut", target="blank")
    circ(p, c, "spaces", ["space"], ZS)
    cyl(p, c, "hub", 5.0, *SUN_HUB, operation="join", target="blank")
    # 5 mm D bore: r 2.55, flat 2.05 from the axis on +x
    yb = math.sqrt(2.55 ** 2 - 2.05 ** 2)
    ops = [{"op": "add", "type": "point", "id": "o", "at": ["0 mm", "0 mm"]},
           {"op": "add", "type": "point", "id": "a", "at": ["2.05 mm", f"{yb:.6f} mm"]},
           {"op": "add", "type": "point", "id": "b", "at": ["2.05 mm", f"{-yb:.6f} mm"]},
           {"op": "add", "type": "line", "id": "flat", "start": "b", "end": "a"},
           {"op": "add", "type": "arc", "id": "round", "center": "o", "start": "a",
            "end": "b"}]
    sk = p.sketch(c, ops, fid="bore-profile", place=((0, 0, SUN_HUB[0] - 0.5), Z, X))
    p.add(c, "extrude", "bore", sketch=sk, operation="cut", target="blank",
          length=f"{SUN_TEETH[1] - SUN_HUB[0] + 1.0:.6f} mm")
    # M3 set screw hole, radial on +x, onto the shaft's flat
    p.add(c, "cylinder", "set-screw-hole", {"radius": "1.5", "height": "3.7"},
          ((1.8, 0, 8.0), X, Z), operation="cut", target="blank")
    colour(p, c, "#c79a4f")


def planet_gear(p):
    c = p.part("planet-gear")
    ra = M * ZP / 2 + M
    h = PLANET_W / 2
    cyl(p, c, "blank", ra, -h, h)
    extrude_poly(p, c, "space", rot(ext_space(ZP), PLANET_PHASE), -h - 0.5, PLANET_W + 1.0,
                 operation="cut", target="blank")
    circ(p, c, "spaces", ["space"], ZP)
    cyl(p, c, "bore", 4.0, -h - 0.5, h + 0.5, operation="cut", target="blank")
    colour(p, c, "#aab1b9")


def planet_small_parts(p):
    pin = p.part("planet-pin-4x13")
    cyl(p, pin, "pin", 2.0, 0, PIN_L)
    colour(p, pin, "#d6d9dd")

    h = PLANET_W / 2
    cup = p.part("needle-bearing-cup")
    rev(p, cup, "cup", [(-h, 2.6), (-h + 0.3, 2.6), (-h + 0.3, 3.5), (h - 0.3, 3.5),
                        (h - 0.3, 2.6), (h, 2.6), (h, 3.98), (-h, 3.98)])
    colour(p, cup, "#b9bdc3")

    nd = p.part("needle-rollers")
    rev(p, nd, "cage", ring_prof(2.2, 3.3, -h + 0.5, -h + 1.0))
    rev(p, nd, "cage-2", ring_prof(2.2, 3.3, h - 1.0, h - 0.5), operation="join", target="cage")
    cyl(p, nd, "needle", 0.72, -h + 0.45, h - 0.45, at=(2.75, 0), operation="join",
        target="cage")
    circ(p, nd, "needles", ["needle"], 11)
    colour(p, nd, "#e3e4e6")

    w = p.part("thrust-washer")
    rev(p, w, "washer", ring_prof(2.1, 4.8, 0, 0.7))
    colour(p, w, "#c9a86a")


def carrier(p):
    c = p.part("carrier")
    cyl(p, c, "plate", 22.0, *CARRIER)
    cyl(p, c, "shoulder", 5.5, CARRIER[1] - 0.5, BRG_A, operation="join", target="plate")
    cyl(p, c, "shaft", 4.0, BRG_A - 0.5, 58.0, operation="join", target="plate")
    p.block(c, "d-flat", (2, 10, 15), (3.5 + 1, 0, 44 + 7.5), Z, X, operation="cut",
            target="plate")
    cyl(p, c, "pin-hole", 2.0, CARRIER[0] - 0.5, PIN_Z0 + PIN_L, at=(CD, 0),
        operation="cut", target="plate")
    cyl(p, c, "window", 3.0, CARRIER[0] - 0.5, CARRIER[1] + 0.5, at=polar(13.5, 60),
        operation="cut", target="plate")
    circ(p, c, "pin-holes", ["pin-hole", "window"], 3)
    colour(p, c, "#b4b9c0")


def ring_gear(p):
    c = p.part("ring-gear")
    cyl(p, c, "housing", 32.0, *RING)
    cyl(p, c, "bore", M * ZR / 2 - M, RING[0] - 0.5, RING[1] + 0.5, operation="cut",
        target="housing")
    extrude_poly(p, c, "space", int_space(ZR), RING[0] - 0.5, RING[1] - RING[0] + 1.0,
                 operation="cut", target="housing")
    circ(p, c, "spaces", ["space"], ZR)
    cyl(p, c, "hole", 1.7, RING[0] - 0.5, RING[1] + 0.5, at=(HOUSING_SCREW_R, 0),
        operation="cut", target="housing")
    circ(p, c, "holes", ["hole"], 6)
    colour(p, c, "#7d848c")


def output_cover(p):
    c = p.part("output-cover")
    z0, zf, zt = COVER
    cyl(p, c, "flange", 32.0, z0, zf)
    cyl(p, c, "boss", 16.0, zf - 0.5, zt, operation="join", target="flange")
    cyl(p, c, "bore", 9.5, z0 - 0.5, zt + 0.5, operation="cut", target="flange")
    cyl(p, c, "seat-a", 11.0, z0 - 0.5, BRG_A + 7.0, operation="cut", target="flange")
    cyl(p, c, "seat-b", 11.0, BRG_B, zt + 0.5, operation="cut", target="flange")
    cyl(p, c, "hole", 1.7, z0 - 0.5, zf + 0.5, at=(HOUSING_SCREW_R, 0), operation="cut",
        target="flange")
    cyl(p, c, "cbore", 3.1, 26.8, zf + 0.5, at=(HOUSING_SCREW_R, 0), operation="cut",
        target="flange")
    circ(p, c, "screw-holes", ["hole", "cbore"], 6)
    cyl(p, c, "mount-tap", 1.5, 25.0, zf + 0.5, at=polar(22.0, 45), operation="cut",
        target="flange")
    circ(p, c, "mount-taps", ["mount-tap"], 4)
    colour(p, c, BLUE)


def bearing_608(p):
    """608: 8 x 22 x 7, seven 5/32 in balls on a 15 mm pitch circle, races
    grooved by a 16-gon of radius 2.1 mm (no torus)."""
    pitch, br, w = 7.5, 1.984, 7.0
    groove = [(w / 2 + 2.1 * math.cos(2 * math.pi * k / 16 + 0.1),
               pitch + 2.1 * math.sin(2 * math.pi * k / 16 + 0.1)) for k in range(16)]
    i = p.part("bearing-608-inner")
    rev(p, i, "race", ring_prof(4.0, 6.3, 0, w))
    rev(p, i, "groove", groove, operation="cut", target="race")
    o = p.part("bearing-608-outer")
    rev(p, o, "race", ring_prof(8.7, 11.0, 0, w))
    rev(p, o, "groove", groove, operation="cut", target="race")
    b = p.part("bearing-608-balls")
    rev(p, b, "cage", ring_prof(6.9, 8.1, w / 2 - 0.5, w / 2 + 0.5))
    p.add(b, "sphere", "ball", {"radius": f"{br:.6f}"}, ((pitch, 0, w / 2), Z, X),
          operation="join", target="cage")
    circ(p, b, "balls", ["ball"], 7)
    for part, col in ((i, "#b9bdc3"), (o, "#b9bdc3"), (b, "#e3e4e6")):
        colour(p, part, col)


def shcs(p, name, length, head_r=2.75, head_h=3.0, r=1.45, socket=1.25):
    c = p.part(name)
    cyl(p, c, "shank", r, -length, 0.2)
    cyl(p, c, "head", head_r, 0, head_h, operation="join", target="shank")
    hexagon = [(socket * math.cos(math.radians(60 * k)), socket * math.sin(math.radians(60 * k)))
               for k in range(6)]
    sk = p.sketch(c, pts_lines(hexagon), fid="socket-profile", place=((0, 0, head_h * 0.45), Z, X))
    p.add(c, "extrude", "socket", sketch=sk, operation="cut", target="shank",
          length=f"{head_h * 0.6:.6f} mm")
    colour(p, c, "#1b1c1f")


def set_screw(p):
    """M3 x 3 cup-point set screw, axis along the part's +x (it sits radially
    in the sun's hub), tip at x = 0."""
    c = p.part("m3x3-set-screw")
    p.add(c, "cylinder", "body", {"radius": "1.45", "height": "2.8"}, ((0, 0, 0), X, Z))
    hexagon = [(0.75 * math.cos(math.radians(60 * k)), 0.75 * math.sin(math.radians(60 * k)))
               for k in range(6)]
    sk = p.sketch(c, pts_lines(hexagon), fid="socket-profile", place=((1.3, 0, 0), X, Z))
    p.add(c, "extrude", "socket", sketch=sk, operation="cut", target="body", length="1.6 mm")
    colour(p, c, "#1b1c1f")


# --------------------------------------------------------------- assembly
def pose(origin=(0, 0, 0), z=Z, x=X):
    return dict(origin=",".join(f"{c:.6f}mm" for c in origin),
                z=",".join(f"{c:.6f}" for c in z), x=",".join(f"{c:.6f}" for c in x))


def off(origin=(0, 0, 0), rotate=None, flip=False):
    o = {"origin": [f"{c:.6f} mm" for c in origin]}
    if rotate is not None:
        o["rotate"] = f"{rotate:.6f} deg"
    if flip:
        o["flip"] = True
    return json.dumps(o)


def inst(p, iid, part, at=(0, 0, 0), fixed=False, z=Z, x=X):
    flags = pose(at, z, x)
    if fixed:
        flags["fixed"] = True
    p.add(A, "instance", iid, of=part, **flags)


def mate(p, mid, form, a, b, a_offset="{}", b_offset="{}", **flags):
    p.add(A, "mate", mid, form=form, a=f"{A}/{a}", b=f"{A}/{b}", a_offset=a_offset,
          b_offset=b_offset, **flags)


def assembly(p):
    p.part(A, assembly=True)
    p.run("param", "set", A, "out=0 deg", "sun=out * 5", "planet=out * -8 / 3")
    inst(p, "motor", "nema17-motor", fixed=True)
    for iid, part in (("input-plate", "input-plate"), ("ring-gear", "ring-gear"),
                      ("output-cover", "output-cover"), ("motor-shaft", "motor-shaft"),
                      ("sun-gear", "sun-gear"), ("carrier", "carrier")):
        inst(p, iid, part)
    mate(p, "plate-on-motor", "fastened", "motor", "input-plate")
    mate(p, "ring-on-plate", "fastened", "input-plate", "ring-gear")
    mate(p, "cover-on-ring", "fastened", "ring-gear", "output-cover")
    mate(p, "input", "revolute", "motor", "motor-shaft", angle="sun")
    mate(p, "sun-on-shaft", "fastened", "motor-shaft", "sun-gear")
    mate(p, "output", "revolute", "input-plate", "carrier", angle="out")

    inst(p, "set-screw", "m3x3-set-screw", at=(2.1, 0, 8.0))
    mate(p, "set-screw-in-sun", "fastened", "sun-gear", "set-screw",
         a_offset=off((2.1, 0, 8.0)))

    for k in range(3):
        phi = 120 * k
        cx, cy = polar(CD, phi)
        n = k + 1
        inst(p, f"pin-{n}", "planet-pin-4x13", at=(cx, cy, PIN_Z0))
        mate(p, f"pin-{n}-in-carrier", "fastened", "carrier", f"pin-{n}",
             a_offset=off((cx, cy, PIN_Z0)))
        inst(p, f"planet-{n}", "planet-gear", at=(cx, cy, PLANET_MID))
        mate(p, f"planet-{n}-on-pin", "revolute", "carrier", f"planet-{n}",
             a_offset=off((cx, cy, PLANET_MID)), angle="planet")
        inst(p, f"needle-cup-{n}", "needle-bearing-cup", at=(cx, cy, PLANET_MID))
        mate(p, f"needle-cup-{n}-in-planet", "fastened", f"planet-{n}", f"needle-cup-{n}")
        inst(p, f"needles-{n}", "needle-rollers", at=(cx, cy, PLANET_MID))
        mate(p, f"needles-{n}-on-pin", "revolute", f"pin-{n}", f"needles-{n}",
             a_offset=off((0, 0, PLANET_MID - PIN_Z0)))
        inst(p, f"washer-{n}", "thrust-washer", at=(cx, cy, 18.5))
        mate(p, f"washer-{n}-on-pin", "fastened", f"pin-{n}", f"washer-{n}",
             a_offset=off((0, 0, 18.5 - PIN_Z0)))

    for tag, z0 in (("a", BRG_A), ("b", BRG_B)):
        inst(p, f"brg-{tag}-inner", "bearing-608-inner", at=(0, 0, z0))
        mate(p, f"brg-{tag}-inner-on-shaft", "fastened", "carrier", f"brg-{tag}-inner",
             a_offset=off((0, 0, z0)))
        inst(p, f"brg-{tag}-outer", "bearing-608-outer", at=(0, 0, z0))
        mate(p, f"brg-{tag}-outer-in-cover", "fastened", "output-cover", f"brg-{tag}-outer",
             a_offset=off((0, 0, z0)))
        inst(p, f"brg-{tag}-balls", "bearing-608-balls", at=(0, 0, z0))
        mate(p, f"brg-{tag}-balls-turn", "revolute", "output-cover", f"brg-{tag}-balls",
             a_offset=off((0, 0, z0)))

    inst(p, "motor-screw", "m3x6-shcs", at=(MOTOR_SCREW, MOTOR_SCREW, 1.8))
    mate(p, "motor-screw-in-plate", "fastened", "input-plate", "motor-screw",
         a_offset=off((MOTOR_SCREW, MOTOR_SCREW, 1.8)))
    p.add(A, "instance_pattern", "motor-screws", instance="motor-screw", form="circular",
          axis=f"{A}/motor", count="4", angle="360deg")
    inst(p, "housing-screw", "m3x25-shcs", at=(HOUSING_SCREW_R, 0, 26.8))
    mate(p, "housing-screw-in-cover", "fastened", "output-cover", "housing-screw",
         a_offset=off((HOUSING_SCREW_R, 0, 26.8)))
    p.add(A, "instance_pattern", "housing-screws", instance="housing-screw", form="circular",
          axis=f"{A}/motor", count="6", angle="360deg")


PROPS = {
    "nema17-motor": ("buy", "NEMA 17 hybrid stepper, 42.3 mm square, 40 mm body, 31 mm M3 pattern, 22 mm pilot"),
    "motor-shaft": ("buy", "Stepper rotor shaft, 5 mm with 0.5 mm D-flat (part of the motor)"),
    "input-plate": ("make", "Input plate: motor pilot recess, 4x M3 counterbored to the motor, 6x M3 tapped for the housing screws"),
    "sun-gear": ("make", "Sun gear 12T m1 PA25, 5 mm D bore, M3 set screw hub"),
    "planet-gear": ("make", "Planet gear 18T m1 PA25, 8 mm bore for drawn-cup needle bearing"),
    "planet-pin-4x13": ("buy", "Dowel pin 4 x 13 mm, planet axle pressed in the carrier"),
    "needle-bearing-cup": ("buy", "Drawn-cup needle bearing outer cup, 4 x 8 x 8 (HK0408 envelope)"),
    "needle-rollers": ("buy", "Needle roller set and cage for the HK0408 envelope, 11 rollers 1.44 mm"),
    "thrust-washer": ("buy", "Thrust washer 4.2 x 9.6 x 0.7 mm, planet to carrier"),
    "carrier": ("make", "Planet carrier with integral 8 mm output shaft (D-flat 0.5 mm)"),
    "ring-gear": ("make", "Ring gear housing 48T internal m1 PA25, 64 mm OD"),
    "output-cover": ("make", "Output cover: two 608 bearing seats, 32 mm spigot, 4x M3 mounting taps"),
    "bearing-608-inner": ("buy", "608 deep-groove ball bearing 8 x 22 x 7: inner ring"),
    "bearing-608-outer": ("buy", "608 deep-groove ball bearing 8 x 22 x 7: outer ring"),
    "bearing-608-balls": ("buy", "608 deep-groove ball bearing 8 x 22 x 7: 7 balls 5/32 in and cage"),
    "m3x6-shcs": ("buy", "ISO 4762 M3 x 6 socket head cap screw"),
    "m3x25-shcs": ("buy", "ISO 4762 M3 x 25 socket head cap screw"),
    "m3x3-set-screw": ("buy", "ISO 4029 M3 x 3 cup-point set screw"),
}


def build(p):
    p.run("init", "--unit", "mm")
    motor(p)
    input_plate(p)
    sun_gear(p)
    planet_gear(p)
    planet_small_parts(p)
    carrier(p)
    ring_gear(p)
    output_cover(p)
    bearing_608(p)
    shcs(p, "m3x6-shcs", 6)
    shcs(p, "m3x25-shcs", 25)
    set_screw(p)
    for part, (mb, desc) in PROPS.items():
        p.run("props", "set", part, f"make_buy={mb}", f"description={desc}")
    assembly(p)
    p.run("param", "set", A, "out=36 deg")


main(build)
