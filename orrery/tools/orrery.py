"""A brass-and-walnut table orrery, built through ryucad's CLI only.

Sun over a stepped walnut drum; Mercury, Venus, Earth and Mars on
staggered brass arms; three exposed drive gears under the top plate.

Gear geometry: pitch radii 26 / 18 / 18, teeth 24 / 16 / 16. Centres
on a circle of radius 40 (the brief's first sketch) cannot mesh --
the side of that triangle is 69.3 mm but the pitch sums are 44 / 36.
So the centres sit on the triangle whose sides ARE the pitch sums
minus 0.4 mm clearance: 43.6 / 43.6 / 35.6, circumradius 23.88,
centroid on the axis. Phasing is tooth-into-gap at every mesh; the
three phase conditions are not exactly commensurate (the triangle's
angles are not multiples of the tooth pitches), so each gear's phase
splits the difference between its two meshes -- worst misalignment
2.2 deg on the 24T gear, inside the gap clearance of the narrow
teeth (root half-width 0.19 pitch, tip half-width 0.09 pitch).

The base is an open drum -- pedestal flange (top z=24), top plate
(z=40..46), three walnut posts at r=56 -- because any solid central
column at gear level (z=30..36) would swallow the gear discs, whose
union reaches the axis. The gears ride on brass arbors spanning
flange to plate.
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


def revolve(p, part, profile):
    """profile: [(z, r), ...] from (0, 0) up the outside to (H, 0)."""
    sk = p.sketch(part, polygon(profile), fid="profile", plane="zx")
    p.add(part, "revolve", "body", sketch=sk,
          axis=f"l{len(profile)}", angle="full")


# ---------------------------------------------------------------- gears
# Centres: A = 24T (rp 26) at top, B / C = 16T (rp 18) below.
# AB = AC = 26 + 18 - 0.4 = 43.6, BC = 18 + 18 - 0.4 = 35.6.
# Circumcentre on the axis: A(0, 23.88), B(-17.8, -15.92), C(17.8, -15.92).
GEAR_Z = 30.0
CENTRES = {"A": (0.0, 23.88), "B": (-17.8, -15.92), "C": (17.8, -15.92)}


def mid_mod(r1, r2, period):
    """Average of two angles that are each known mod `period`."""
    while r2 - r1 > period / 2:
        r2 -= period
    while r1 - r2 > period / 2:
        r2 += period
    return ((r1 + r2) / 2) % period


def gear_phases():
    def dirn(p_from, p_to):
        return math.degrees(math.atan2(p_to[1] - p_from[1],
                                       p_to[0] - p_from[0]))
    A, B, C = CENTRES["A"], CENTRES["B"], CENTRES["C"]
    pa, pb = 360.0 / 24, 360.0 / 16
    # A tooth -> B, B gap -> A; B gap -> C, C tooth -> B;
    # C tooth -> A, A gap -> C.
    phase_a = mid_mod(dirn(A, B) % pa,
                      (dirn(A, C) - pa / 2) % pa, pa)
    phase_b = mid_mod((dirn(B, A) - pb / 2) % pb,
                      (dirn(B, C) - pb / 2) % pb, pb)
    phase_c = mid_mod(dirn(C, B) % pb, dirn(C, A) % pb, pb)
    return phase_a, phase_b, phase_c


def gear(p, name, teeth, rp):
    """A toothed disc as one closed polygon sketch, extruded, plus a
    centre arbor (local z -6..10: spans flange top to plate underside
    once placed at GEAR_Z). Teeth phase 0: a tooth centred on +x."""
    g = p.part(name)
    root, tip = rp - 2.6, rp + 1.8
    pitch = 2 * math.pi / teeth
    pts = []
    for k in range(teeth):
        c = k * pitch
        for frac, r in ((-0.19, root), (-0.09, tip),
                        (0.09, tip), (0.19, root)):
            a = c + frac * pitch
            pts.append((r * math.cos(a), r * math.sin(a)))
    sk = p.sketch(g, polygon(pts), fid="outline",
                  place=((0, 0, 0), Z, X))
    p.add(g, "extrude", "disc", sketch=sk, length="6 mm")
    p.add(g, "cylinder", "arbor", {"radius": 2.8, "height": 16},
          ((0, 0, -6), Z, X), operation="join")
    return g


# ------------------------------------------------------------------ base
def base(p):
    b = p.part("base")
    # Pedestal + flange (top z=24): foot r=95 stepping in to a r=48
    # neck, out to the r=60 flange at z=17..24 the arbors stand on.
    revolve(p, b, [(0, 0), (0, 95), (4, 95), (4, 84), (10, 84),
                   (10, 48), (17, 48), (17, 60), (24, 60), (24, 0)])
    # Three posts carry the top plate. At r=56, angles 30/150/270,
    # each post clears every gear disc by >15 mm in plan (checked
    # pairwise against tip radius + post radius); posts overlap
    # flange and plate by 1 mm each end.
    for k, ang in enumerate((30, 150, 270)):
        x, y, _ = polar(56, ang)
        p.add(b, "cylinder", f"post-{k + 1}", {"radius": 5.5, "height": 18},
              ((x, y, 23), Z, X), operation="join")
    p.add(b, "cylinder", "plate", {"radius": 88, "height": 6},
          ((0, 0, 40), Z, X), operation="join")
    return b


def column(p):
    c = p.part("column")
    p.add(c, "cylinder", "shaft", {"radius": 6, "height": 74},
          ((0, 0, 46), Z, X))
    p.add(c, "cylinder", "collar", {"radius": 9.5, "height": 4},
          ((0, 0, 46), Z, X), operation="join")
    p.add(c, "cylinder", "top-collar", {"radius": 8, "height": 3},
          ((0, 0, 114), Z, X), operation="join")
    return c


def ball(p, name, r):
    s = p.part(name)
    p.add(s, "sphere", "ball", {"radius": r}, ((0, 0, 0), Z, X))
    return s


# ------------------------------------------------------------------ arms
PLANETS = [  # name, orbit R, arm z, planet r, arm angle deg
    ("mercury", 34, 62, 3.5, 15),
    ("venus", 50, 78, 5.5, 125),
    ("earth", 68, 94, 6.0, 230),
    ("mars", 84, 110, 4.5, 325),
]


def arm(p, name, orbit, rplanet, rod_hole=False):
    a = p.part(f"arm-{name}")
    # Bar from the counterweight side (x=-16) to the planet (x=orbit).
    p.block(a, "bar", (orbit + 16, 5, 3), ((orbit - 16) / 2, 0, 0), Z, X)
    # Hub ring around the column (bore 6.2 over the r=6 column).
    p.add(a, "cylinder", "hub", {"radius": 7.5, "height": 7},
          ((0, 0, -3.5), Z, X), operation="join")
    p.add(a, "cylinder", "bore", {"radius": 6.2, "height": 9},
          ((0, 0, -4.5), Z, X), operation="cut")
    # Counterweight ball, intersecting the bar so the part is one solid.
    p.add(a, "sphere", "counterweight", {"radius": 4.5},
          ((-15, 0, 0), Z, X), operation="join")
    # Planet cup: a pocket of radius planet+0.3 cut into the bar top
    # (z 0.3..2.7). The planet centre sits at local z = rplanet + 1.1,
    # dipping 0.4 into the cup: its surface clears the cup wall (cross
    # radius at the bar top is sqrt(r^2-(r-0.4)^2), well under the cup
    # radius) and its underside stays 0.8 above the pocket floor. The
    # planets used to sink a full 1 mm into the solid bar.
    p.add(a, "cylinder", "cup", {"radius": rplanet + 0.3, "height": 2.4},
          ((orbit, 0, 0.3), Z, X), operation="cut")
    if rod_hole:
        # Earth's tilted axis rod crosses this bar on its way down
        # from the planet centre (local (orbit, 0, rplanet + 1.1)).
        # Drill the bar along the rod's own line: hole r 1.2 around
        # the r 0.9 rod (0.3 clearance). The crossing at bar mid-height
        # (z=0) is at x = orbit - (rplanet + 1.1) * tan(23.5 deg).
        tilt = math.radians(23.5)
        d = (math.sin(tilt), 0, math.cos(tilt))
        cross_x = orbit - (rplanet + 1.1) * math.tan(tilt)
        org = (cross_x - 4 * d[0], 0, -4 * d[2])
        p.add(a, "cylinder", "rod-hole", {"radius": 1.2, "height": 8},
              (org, d, (math.cos(tilt), 0, -math.sin(tilt))),
              operation="cut")
    return a


def earth_extras(p):
    """Tilted axis rod through Earth + the moon arm, one brass part.
    Modelled about Earth's centre, rod tilted 23.5 deg toward +x."""
    e = p.part("earth-extras")
    tilt = math.radians(23.5)
    d = (math.sin(tilt), 0, math.cos(tilt))
    xdir = (math.cos(tilt), 0, -math.sin(tilt))
    org = tuple(-11 * c for c in d)
    p.add(e, "cylinder", "rod", {"radius": 0.9, "height": 22},
          (org, d, xdir))
    # Moon arm out to local x=16 at z=7.5, where the rod passes
    # (rod crosses z=7.5 at x=3.26, inside the bar: the two join).
    p.block(e, "moon-arm", (14, 1.6, 1.6), (9, 0, 7.5), Z, X,
            operation="join")
    # Moon cup at x=14: pocket r 1.9 (moon r 1.7 + 0.2), floor at
    # z 7.3. The moon centre sits at local z 9.6, dipping 0.4 into
    # the cup mouth (arm top 8.3) with its underside 0.6 above the
    # floor; it used to sit with its centre inside the bar's z-range.
    # (r 1.9, not 2.0: at r 2.0 the cup wall is exactly tangent to
    # the arm's end face at x=16 and the kernel refuses the cut as
    # non-manifold.)
    p.add(e, "cylinder", "moon-cup", {"radius": 1.9, "height": 1.7},
          ((14, 0, 7.3), Z, X), operation="cut")
    return e


# -------------------------------------------------------------- assembly
def assembly(p):
    a = p.part("orrery", assembly=True)
    p.add(a, "instance", "base", of="base", fixed=True)
    p.add(a, "instance", "column", of="column", fixed=True)
    p.add(a, "instance", "sun", of="sun",
          origin="0mm,0mm,137mm", fixed=True)
    phase_a, phase_b, phase_c = gear_phases()
    for iid, of, key, phase in (
            ("gear-a", "gear-24", "A", phase_a),
            ("gear-b", "gear-18", "B", phase_b),
            ("gear-c", "gear-18", "C", phase_c)):
        cx, cy = CENTRES[key]
        r = math.radians(phase)
        p.add(a, "instance", iid, of=of,
              origin=f"{cx:.2f}mm,{cy:.2f}mm,{GEAR_Z:.0f}mm",
              z="0,0,1", x=f"{math.cos(r):.6f},{math.sin(r):.6f},0",
              fixed=True)
    for name, orbit, z, r, ang in PLANETS:
        rad = math.radians(ang)
        xdir = f"{math.cos(rad):.6f},{math.sin(rad):.6f},0"
        p.add(a, "instance", f"arm-{name}", of=f"arm-{name}",
              origin=f"0mm,0mm,{z}mm", z="0,0,1", x=xdir, fixed=True)
        px, py, _ = polar(orbit, ang)
        # Planet centre: bar top (local z +1.5) + r - 0.4 dip into
        # the arm's cup -> world z = arm z + r + 1.1.
        pz = z + r + 1.1
        kw = {}
        if name == "earth":
            # Earth carries the axis bore: instance it with the arm's
            # frame so the bore lines up with the tilted rod.
            kw = {"z": "0,0,1", "x": xdir}
        p.add(a, "instance", name, of=name,
              origin=f"{px:.2f}mm,{py:.2f}mm,{pz:.1f}mm", fixed=True, **kw)
        if name == "earth":
            p.add(a, "instance", "earth-extras", of="earth-extras",
                  origin=f"{px:.2f}mm,{py:.2f}mm,{pz:.1f}mm",
                  z="0,0,1", x=xdir, fixed=True)
            mx, my, _ = polar(14, ang)
            # Moon centre at extras-local (14, 0, 9.6): seated in the
            # moon-arm cup.
            p.add(a, "instance", "moon", of="moon",
                  origin=f"{px + mx:.2f}mm,{py + my:.2f}mm,"
                         f"{pz + 9.6:.1f}mm", fixed=True)
    return a


def finish(p):
    p.run("materials", "set", "walnut", "--density", "640 kg/m^3",
          "--colour", "#5a3a22", "--default")
    p.run("materials", "set", "brass", "--density", "8500 kg/m^3",
          "--colour", "#b98a3e")
    p.run("materials", "set", "gold", "--density", "19300 kg/m^3",
          "--colour", "#d9a441")
    p.run("materials", "set", "mercury-rock", "--density", "5427 kg/m^3",
          "--colour", "#9c8e82")
    p.run("materials", "set", "venus-rock", "--density", "5243 kg/m^3",
          "--colour", "#d9b380")
    p.run("materials", "set", "earth-rock", "--density", "5514 kg/m^3",
          "--colour", "#3f6fb5")
    p.run("materials", "set", "mars-rock", "--density", "3933 kg/m^3",
          "--colour", "#b5533c")
    p.run("materials", "set", "moon-rock", "--density", "3344 kg/m^3",
          "--colour", "#cfcfcf")
    mats = [("base", "walnut"), ("column", "brass"),
            ("gear-24", "brass"), ("gear-18", "brass"),
            ("sun", "gold"), ("earth-extras", "brass"),
            ("mercury", "mercury-rock"), ("venus", "venus-rock"),
            ("earth", "earth-rock"), ("mars", "mars-rock"),
            ("moon", "moon-rock")]
    mats += [(f"arm-{n}", "brass") for n, *_ in PLANETS]
    for part, mat in mats:
        p.run("props", "set", part, f"material={mat}")
        p.run("colour", part, "--material")


def build(p):
    p.run("init", "--unit", "mm")
    base(p)
    gear(p, "gear-24", 24, 26)
    gear(p, "gear-18", 16, 18)
    column(p)
    ball(p, "sun", 17)
    for name, orbit, _z, r, _ang in PLANETS:
        arm(p, name, orbit, r, rod_hole=(name == "earth"))
        s = ball(p, name, r)
        if name == "earth":
            # Axis bore r 1.2 along the 23.5 deg tilt, so the r 0.9
            # axis rod passes through the planet with 0.3 clearance
            # instead of occupying 30 mm^3 of it. The instance gets
            # the arm's frame (see assembly), which aligns the bore
            # with the rod.
            tilt = math.radians(23.5)
            d = (math.sin(tilt), 0, math.cos(tilt))
            org = tuple(-7 * c for c in d)
            p.add(s, "cylinder", "axis-bore",
                  {"radius": 1.2, "height": 14},
                  (org, d, (math.cos(tilt), 0, -math.sin(tilt))),
                  operation="cut")
    earth_extras(p)
    ball(p, "moon", 1.7)
    assembly(p)
    finish(p)
    pa, pb, pc = gear_phases()
    print(f"gear phases deg: A={pa:.2f} B={pb:.2f} C={pc:.2f}")


main(build)
