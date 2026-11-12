"""A small industrial power-transmission line, as a ryucad assembly built
through the CLI only.

  * a fabricated steel base: 15 mm plate on two skid rails, motor slots and
    corner anchor slots, two riser pads with tapped M12 holes;
  * an IEC 80 (B3, foot-mounted) style motor, simplified: finned frame with
    four feet (A = 125 mm, B = 100 mm, shaft height 80 mm), end shields,
    fan and fan cowl, terminal box with a cable gland, and a rotor with a
    19 mm x 40 mm shaft extension keyed 6 x 6;
  * an L-100 style jaw coupling: two hubs (bores 19 and 25 mm, keyways, M6
    set screws) with three jaws each, and a six-leg elastomer spider;
  * a 25 mm line shaft keyed 8 x 7 at both ends, carried by two UCP205 style
    pillow blocks (cast housing with bolt slots and a grease nipple, a UC205
    insert: spherical outer ring, extended inner ring with two M6 set
    screws, nine 5/16 in balls in a cage, two seals);
  * two 25 mm set-screw shaft collars;
  * a single-groove SPA V-belt pulley, 140 mm pitch diameter, keyed and set
    screwed, on the output end;
  * M8 motor bolts with washers and nuts, M12 pillow-block bolts with washers.

Every part is modelled in one frame F, the drive frame: its z along the
shaft, x up, origin on the shaft axis 80 mm above the base's top. Fasteners'
axes are their part's x. The rotating group (rotor, hub A, spider, keys,
line shaft, hub B, inner rings, collars, pulley, their set screws) turns on
two revolutes driven by the assembly parameter `shaft`; each ball set turns
on a revolute driven at `shaft * 0.4` (the cage speed of this bearing,
(1 - d/Dpw) / 2 with d = 7.94 mm, Dpw = 39.5 mm).
"""
import json
import math
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from model import main  # noqa: E402

Z = (0, 0, 1)
X = (1, 0, 0)
Y = (0, 1, 0)
ASM = "drive"

PB1, PB2 = 110.0, 290.0          # pillow-block centres along the shaft (w)
H = 80.0                        # shaft height above the base top


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


def ring(r0, r1, z0, z1):
    return [(z0, r0), (z1, r0), (z1, r1), (z0, r1)]


def circle_pts(zc, rc, rad, n=36):
    return [(zc + rad * math.cos(2 * math.pi * i / n), rc + rad * math.sin(2 * math.pi * i / n))
            for i in range(n)]


def cyl(p, part, fid, r, z0, z1, at=(0, 0), **flags):
    """A cylinder along the part's z (the shaft axis)."""
    return p.add(part, "cylinder", fid, {"radius": f"{r:.6f}", "height": f"{z1-z0:.6f}"},
                 ((at[0], at[1], z0), Z, X), **flags)


def xcyl(p, part, fid, r, x0, x1, y=0.0, z=0.0, **flags):
    """A cylinder along the part's x (up in the drive frame)."""
    return p.add(part, "cylinder", fid, {"radius": f"{r:.6f}", "height": f"{x1-x0:.6f}"},
                 ((x0, y, z), X, Y), **flags)


def ycyl(p, part, fid, r, y0, y1, x=0.0, z=0.0, **flags):
    return p.add(part, "cylinder", fid, {"radius": f"{r:.6f}", "height": f"{y1-y0:.6f}"},
                 ((x, y0, z), Y, Z), **flags)


def box(p, part, fid, x0, x1, y0, y1, z0, z1, **flags):
    return p.block(part, fid, (x1 - x0, y1 - y0, z1 - z0),
                   ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), Z, X, **flags)


def radial_cyl(p, part, fid, r, r0, r1, ang, z, **flags):
    """A cylinder pointing radially out from the shaft axis at angle `ang`
    (degrees from x towards y), from radius r0 to r1, at axial z."""
    a = math.radians(ang)
    d = (math.cos(a), math.sin(a), 0)
    o = (r0 * d[0], r0 * d[1], z)
    perp = (0, 0, 1)
    return p.add(part, "cylinder", fid, {"radius": f"{r:.6f}", "height": f"{r1-r0:.6f}"},
                 (o, d, perp), **flags)


def hexagon(af, rot=30.0):
    rc = af / math.sqrt(3)
    return [(rc * math.cos(math.radians(rot + 60 * i)), rc * math.sin(math.radians(rot + 60 * i)))
            for i in range(6)]


def hex_x(p, part, fid, af, x0, length, **flags):
    """A hexagonal prism along the part's x, from x0, across flats af."""
    sk = p.sketch(part, pts_lines(hexagon(af)), fid=f"{fid}-profile",
                  place=((x0, 0, 0), X, Y))
    return p.add(part, "extrude", fid, sketch=sk, length=f"{length:.6f} mm", **flags)


def sector(r0, r1, a0, a1, n=6):
    pts = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((r1 * math.cos(a), r1 * math.sin(a)))
    for i in range(n + 1):
        a = math.radians(a1 - (a1 - a0) * i / n)
        pts.append((r0 * math.cos(a), r0 * math.sin(a)))
    return pts


def sectors_sketch(p, part, fid, secs, z0):
    ops = []
    for k, s in enumerate(secs):
        ops += pts_lines(s, pre=f"s{k}p", lpre=f"s{k}l")
    return p.sketch(part, ops, fid=f"{fid}-profile", place=((0, 0, z0), Z, X))


def colour(p, part, c):
    p.run("colour", part, "--colour", c)


def obround_x(p, part, fid, x0, x1, y, z, length_y, width, **flags):
    """An obround slot through x, its length along y, centred at (y, z)."""
    r = width / 2
    s = length_y - width
    box(p, part, f"{fid}-mid", x0, x1, y - s / 2, y + s / 2, z - r, z + r, **flags)
    xcyl(p, part, f"{fid}-e1", r, x0, x1, y - s / 2, z, **flags)
    xcyl(p, part, f"{fid}-e2", r, x0, x1, y + s / 2, z, **flags)


def obround_x_alongz(p, part, fid, x0, x1, y, z, length_z, width, **flags):
    r = width / 2
    s = length_z - width
    box(p, part, f"{fid}-mid", x0, x1, y - r, y + r, z - s / 2, z + s / 2, **flags)
    xcyl(p, part, f"{fid}-e1", r, x0, x1, y, z - s / 2, **flags)
    xcyl(p, part, f"{fid}-e2", r, x0, x1, y, z + s / 2, **flags)


# ------------------------------------------------------------------ base
def base(p):
    b = p.part("base")
    box(p, b, "plate", -H - 15, -H, -130, 130, -340, 390)
    for i, (y0, y1) in enumerate(((-130, -115), (115, 130))):
        box(p, b, f"rail-{i+1}", -H - 55, -H - 14.5, y0, y1, -340, 390, operation="join")
    for i, w in enumerate((PB1, PB2)):
        box(p, b, f"riser-{i+1}", -H - 0.5, -36.5, -80, 80, w - 30, w + 30, operation="join")
        for j, v in enumerate((-52.5, 52.5)):
            xcyl(p, b, f"tap-{i+1}-{j+1}", 6.1, -66.5, -36.0, v, w, operation="cut")
    # motor slots (lateral adjustment) and anchor slots in the corners
    for i, w in enumerate((-210, -110)):
        for j, v in enumerate((-62.5, 62.5)):
            obround_x(p, b, f"motor-slot-{i+1}-{j+1}", -H - 15.5, -H + 0.5, v, w, 20, 9,
                      operation="cut")
    for i, w in enumerate((-310, 360)):
        for j, v in enumerate((-95, 95)):
            obround_x_alongz(p, b, f"anchor-slot-{i+1}-{j+1}", -H - 15.5, -H + 0.5, v, w, 36, 18,
                             operation="cut")
    colour(p, b, "#34495e")


# ----------------------------------------------------------------- motor
FIN_ANGLES = [a for a in range(-120, 121, 15) if abs(a) >= 30]


def motor(p):
    f = p.part("motor-frame")
    rev(p, f, "body", ring(64, 75, -250, -70))
    box(p, f, "tb-pad", 70, 85, -35, 35, -195, -125, operation="join")
    for a in FIN_ANGLES:
        d = (math.cos(math.radians(a)), math.sin(math.radians(a)), 0)
        p.block(f, f"fin{a:+d}".replace("+", "p").replace("-", "m"), (10, 3, 170),
                (79 * d[0], 79 * d[1], -160), Z, d, operation="join")
    for i, w in enumerate((-210, -110)):
        for j, s in enumerate((-1, 1)):
            box(p, f, f"foot-{i+1}-{j+1}", -80, -68, min(s * 40, s * 80), max(s * 40, s * 80),
                w - 15, w + 15, operation="join")
            box(p, f, f"web-{i+1}-{j+1}", -68.5, -40, min(s * 40, s * 53), max(s * 40, s * 53),
                w - 15, w + 15, operation="join")
            xcyl(p, f, f"foot-hole-{i+1}-{j+1}", 4.5, -80.5, -67.5, s * 62.5, w, operation="cut")
    colour(p, f, "#2e6aa1")

    de = p.part("motor-de-shield")
    rev(p, de, "shield", [(-70, 10.5), (-50, 10.5), (-50, 35), (-55, 35), (-55, 75), (-70, 75)])
    for i in range(4):
        a = 45 + 90 * i
        cyl(p, de, f"tie-{i+1}", 5, -55.5, -51, at=(68 * math.cos(math.radians(a)),
                                                   68 * math.sin(math.radians(a))),
            operation="join")
    colour(p, de, "#2e6aa1")

    nde = p.part("motor-nde-shield")
    rev(p, nde, "shield", ring(10.5, 75, -265, -250))
    colour(p, nde, "#2e6aa1")

    c = p.part("fan-cowl")
    rev(p, c, "cowl", [(-320, 12), (-317, 12), (-317, 68), (-265, 68), (-265, 73), (-320, 73)])
    cyl(p, c, "vent", 6, -320.5, -316.5, at=(40, 0), operation="cut")
    p.add(c, "pattern", "vents", seed=["vent"], form="circular", axis="z", count="10",
          angle="360")
    colour(p, c, "#2a2d31")

    r = p.part("motor-rotor")
    cyl(p, r, "shaft", 9.5, -300, -9)
    rev(p, r, "core", ring(9, 55, -235, -85), operation="join")
    rev(p, r, "fan-hub", ring(9, 18, -300, -288), operation="join")
    p.block(r, "blade", (42.5, 3, 12), (38.5, 0, -294), Z, X, operation="join")
    p.add(r, "pattern", "blades", seed=["blade"], form="circular", axis="z", count="6",
          angle="360")
    box(p, r, "keyway", 6, 11, -3, 3, -45, -13, operation="cut")
    colour(p, r, "#b9bec5")

    t = p.part("terminal-box")
    box(p, t, "box", 85, 133, -40, 40, -200, -120)
    box(p, t, "lid", 132.5, 139, -43, 43, -203, -117, operation="join")
    for i, (v, w) in enumerate(((-36, -196), (36, -196), (-36, -124), (36, -124))):
        xcyl(p, t, f"lid-screw-{i+1}", 2.5, 138.5, 141, v, w, operation="join")
    colour(p, t, "#2e6aa1")

    g = p.part("cable-gland")
    sk = p.sketch(g, pts_lines(hexagon(22)), fid="hex-profile", place=((110, 40, -160), Y, X))
    p.add(g, "extrude", "hex", sketch=sk, length="8 mm")
    ycyl(p, g, "cap", 9, 47.5, 56, x=110, z=-160, operation="join")
    ycyl(p, g, "cable", 5, 55.5, 80, x=110, z=-160, operation="join")
    colour(p, g, "#1d1f22")

    k = p.part("key-6x6x28")
    box(p, k, "key", 6.0, 12.0, -2.99, 2.99, -43, -15)
    colour(p, k, "#d4d7db")


# -------------------------------------------------------------- coupling
def coupling(p):
    a = p.part("jaw-hub-a")
    cyl(p, a, "body", 32, -45, -8)
    sk = sectors_sketch(p, a, "jaws", [sector(13.5, 32, c - 25, c + 25) for c in (0, 120, 240)],
                        -8.5)
    p.add(a, "extrude", "jaws", sketch=sk, length="18.5 mm", operation="join")
    cyl(p, a, "bore", 9.55, -46, -7, operation="cut")
    box(p, a, "keyway", 8, 12.3, -3, 3, -46, -7, operation="cut")
    xcyl(p, a, "set-hole", 3, 9, 33, 0, -27, operation="cut")
    colour(p, a, "#8f949b")

    b = p.part("jaw-hub-b")
    cyl(p, b, "body", 32, 12, 49)
    sk = sectors_sketch(p, b, "jaws", [sector(13.5, 32, c - 25, c + 25) for c in (60, 180, 300)],
                        12.5)
    p.add(b, "extrude", "jaws", sketch=sk, length="18.5 mm", operation="join", reverse=True)
    cyl(p, b, "bore", 12.55, 11, 50, operation="cut")
    box(p, b, "keyway", 10, 15.8, -4, 4, 11, 50, operation="cut")
    xcyl(p, b, "set-hole", 3, 13, 33, 0, 32, operation="cut")
    colour(p, b, "#8f949b")

    s = p.part("jaw-spider")
    rev(p, s, "centre", ring(6, 13, -5.5, 9.5))
    sk = sectors_sketch(p, s, "legs", [sector(12, 31, c - 4, c + 4, n=2)
                                        for c in (30, 90, 150, 210, 270, 330)], -5.5)
    p.add(s, "extrude", "legs", sketch=sk, length="15 mm", operation="join")
    colour(p, s, "#e0a800")


# ----------------------------------------------------------------- shaft
def line_shaft(p):
    s = p.part("line-shaft")
    cyl(p, s, "shaft", 12.5, 14, 374)
    box(p, s, "keyway-coupling", 8.5, 13.5, -4, 4, 17, 45, operation="cut")
    box(p, s, "keyway-pulley", 8.5, 13.5, -4, 4, 334, 366, operation="cut")
    colour(p, s, "#c7ccd2")
    for name, z0, z1 in (("key-8x7x26", 18, 44), ("key-8x7x30", 335, 365)):
        k = p.part(name)
        box(p, k, "key", 8.5, 15.5, -3.99, 3.99, z0, z1)
        colour(p, k, "#d4d7db")

    c = p.part("shaft-collar-25")
    rev(p, c, "collar", ring(12.55, 21, -8, 8))
    xcyl(p, c, "set-hole", 3, 12, 22, 0, 0, operation="cut")
    colour(p, c, "#25272b")


def pulley(p):
    q = p.part("pulley-spa-140")
    t = math.tan(math.radians(19))
    # outline of hub, web and rim in (w, r), the groove cut out of the rim
    prof = [(330, 12.55), (370, 12.55), (370, 25), (355, 25), (355, 52), (360, 52),
            (360, 72.75)]
    rp = 70.0
    top, bot = 72.75, 59.0
    wt, wb = 5.5 + (top - rp) * t, 5.5 + (bot - rp) * t
    prof += [(350 + wt, top), (350 + wb, bot), (350 - wb, bot), (350 - wt, top),
             (340, 72.75), (340, 52), (345, 52), (345, 25), (330, 25)]
    rev(p, q, "body", prof)
    cyl(p, q, "lighten", 8, 344, 356, at=(38.5, 0), operation="cut")
    p.add(q, "pattern", "lightening", seed=["lighten"], form="circular", axis="z", count="5",
          angle="360")
    box(p, q, "keyway", 10, 15.8, -4, 4, 329, 371, operation="cut")
    xcyl(p, q, "set-hole", 3, 13, 26, 0, 335, operation="cut")
    colour(p, q, "#505459")


# ---------------------------------------------------------- pillow block
def pillow_block(p):
    h = p.part("ucp205-housing")
    rev(p, h, "ring", ring(20, 34.5, -12, 12))
    box(p, h, "base", -36.5, -22.5, -70, 70, -19, 19, operation="join")
    box(p, h, "web", -23, -15, -30, 30, -9, 9, operation="join")
    cyl(p, h, "bore", 26, -20, 20, operation="cut")
    for j, v in enumerate((-52.5, 52.5)):
        obround_x(p, h, f"slot-{j+1}", -37, -22, v, 0, 19, 13, operation="cut")
    xcyl(p, h, "grease-hole", 2.5, 24, 35, operation="cut")
    colour(p, h, "#4b5157")

    o = p.part("uc205-outer-ring")
    prof = [(-8.5, 21.5), (8.5, 21.5)]
    R = 25.95
    for i in range(13):
        w = 8.5 - 17.0 * i / 12
        prof.append((w, math.sqrt(R * R - w * w)))
    rev(p, o, "ring", prof)
    rev(p, o, "groove", circle_pts(0, 19.75, 4.1), operation="cut")
    colour(p, o, "#c9cdd3")

    i = p.part("uc205-inner-ring")
    rev(p, i, "ring", ring(12.55, 17.5, -20.4, 13.7))
    rev(p, i, "groove", circle_pts(0, 19.75, 4.1), operation="cut")
    for k, a in enumerate((0, 120)):
        radial_cyl(p, i, f"set-hole-{k+1}", 3, 11, 19, a, -15.5, operation="cut")
    colour(p, i, "#d5d8dd")

    b = p.part("uc205-balls")
    rev(p, b, "cage", ring(19.35, 20.15, -0.6, 0.6))
    p.add(b, "sphere", "ball", {"radius": "3.97"}, ((19.75, 0, 0), Z, X), operation="join")
    p.add(b, "pattern", "balls", seed=["ball"], form="circular", axis="z", count="9",
          angle="360")
    colour(p, b, "#eef0f2")

    s = p.part("uc205-seals")
    rev(p, s, "seal-1", ring(17.6, 21.4, 6.0, 7.0))
    rev(p, s, "seal-2", ring(17.6, 21.4, -7.0, -6.0))
    colour(p, s, "#1c1c1c")

    n = p.part("grease-nipple-m6")
    xcyl(p, n, "thread", 2.45, -4, 0.5)
    hex_x(p, n, "hex", 7, 0, 5, operation="join")
    xcyl(p, n, "neck", 2, 4.5, 7.5, operation="join")
    p.add(n, "sphere", "head", {"radius": "3"}, ((9, 0, 0), Z, X), operation="join")
    colour(p, n, "#c8a24a")


# ------------------------------------------------------------ fasteners
def set_screw(p, name, length):
    s = p.part(name)
    xcyl(p, s, "body", 2.95, 0, length)
    sk = p.sketch(s, pts_lines(hexagon(3)), fid="socket-profile",
                  place=((length - 2.5, 0, 0), X, Y))
    p.add(s, "extrude", "socket", sketch=sk, length="3 mm", operation="cut")
    colour(p, s, "#1b1c1f")


def hex_bolt(p, name, d, length, af, k):
    b = p.part(name)
    xcyl(p, b, "shank", d / 2, -length, 0.5)
    hex_x(p, b, "head", af, 0, k, operation="join")
    colour(p, b, "#a9aeb5")


def washer(p, name, di, do, t):
    w = p.part(name)
    xcyl(p, w, "disc", do / 2, 0, t)
    xcyl(p, w, "hole", di / 2, -0.5, t + 0.5, operation="cut")
    colour(p, w, "#c3c7cc")


def hex_nut(p, name, d, af, m):
    n = p.part(name)
    hex_x(p, n, "body", af, 0, m)
    xcyl(p, n, "bore", d / 2 + 0.05, -0.5, m + 0.5, operation="cut")
    colour(p, n, "#a9aeb5")


# ------------------------------------------------------------- assembly
class Fr:
    def __init__(self, o, x, y, z):
        self.o, self.x, self.y, self.z = o, x, y, z

    def apply(self, origin=(0, 0, 0), rotate=0.0, flip=False):
        o = tuple(self.o[i] + origin[0] * self.x[i] + origin[1] * self.y[i] + origin[2] * self.z[i]
                  for i in range(3))
        c, s = math.cos(math.radians(rotate)), math.sin(math.radians(rotate))
        x = tuple(c * self.x[i] + s * self.y[i] for i in range(3))
        y = tuple(-s * self.x[i] + c * self.y[i] for i in range(3))
        z = self.z
        if flip:
            y = tuple(-v for v in y)
            z = tuple(-v for v in z)
        return Fr(o, x, y, z)


F = Fr((0, 0, H), (0, 0, 1), (0, -1, 0), (1, 0, 0))   # the drive frame in the world
FRAMES = {}


def off_json(origin=None, rotate=0.0, flip=False):
    d = {}
    if origin is not None:
        d["origin"] = [f"{c:.6f} mm" for c in origin]
    if rotate:
        d["rotate"] = f"{rotate:.6f} deg"
    if flip:
        d["flip"] = True
    return json.dumps(d)


def place(p, inst, part, parent=None, form="fastened", origin=None, rotate=0.0, flip=False,
          angle=None, fixed=False):
    """An instance of `part` posed where its mate to `parent` puts it, and the mate."""
    base_fr = FRAMES[parent] if parent else F
    fr = base_fr.apply(origin or (0, 0, 0), rotate, flip)
    FRAMES[inst] = fr
    flags = dict(of=part, origin=",".join(f"{c:.6f}mm" for c in fr.o),
                 z=",".join(f"{c:.6f}" for c in fr.z), x=",".join(f"{c:.6f}" for c in fr.x))
    if fixed:
        flags["fixed"] = True
    p.add(ASM, "instance", inst, **flags)
    if parent:
        mflags = dict(form=form, a=f"{ASM}/{parent}", b=f"{ASM}/{inst}",
                      a_offset=off_json(origin, rotate, flip), b_offset="{}")
        if angle:
            mflags["angle"] = angle
        p.add(ASM, "mate", f"{inst}-{form}", **mflags)


def assemble(p):
    p.part(ASM, assembly=True)
    p.run("param", "set", ASM, "shaft=0 deg")
    place(p, "base", "base", fixed=True)
    # motor
    place(p, "motor-frame", "motor-frame", "base")
    for inst in ("motor-de-shield", "motor-nde-shield", "fan-cowl", "terminal-box"):
        place(p, inst, inst, "motor-frame")
    place(p, "cable-gland", "cable-gland", "terminal-box")
    place(p, "motor-rotor", "motor-rotor", "motor-frame", form="revolute", angle="shaft")
    place(p, "motor-key", "key-6x6x28", "motor-rotor")
    # coupling
    place(p, "hub-a", "jaw-hub-a", "motor-rotor")
    place(p, "hub-a-set-screw", "set-screw-m6x8", "hub-a", origin=(12.4, 0, -27))
    place(p, "spider", "jaw-spider", "hub-a")
    # pillow blocks, the line shaft and what it carries
    for k, w in ((1, PB1), (2, PB2)):
        place(p, f"pb{k}-housing", "ucp205-housing", "base", origin=(0, 0, w))
        place(p, f"pb{k}-outer-ring", "uc205-outer-ring", f"pb{k}-housing")
        place(p, f"pb{k}-seals", "uc205-seals", f"pb{k}-outer-ring")
        place(p, f"pb{k}-grease-nipple", "grease-nipple-m6", f"pb{k}-housing",
              origin=(34.5, 0, 0))
        for j, v in enumerate((-52.5, 52.5)):
            place(p, f"pb{k}-washer-{j+1}", "washer-m12", "base", origin=(-22.5, v, w))
            place(p, f"pb{k}-bolt-{j+1}", "hex-bolt-m12x40", "base", origin=(-20.0, v, w))
    place(p, "line-shaft", "line-shaft", "pb1-housing", form="revolute", origin=(0, 0, -PB1),
          angle="shaft")
    place(p, "coupling-key", "key-8x7x26", "line-shaft")
    place(p, "pulley-key", "key-8x7x30", "line-shaft")
    place(p, "hub-b", "jaw-hub-b", "line-shaft")
    place(p, "hub-b-set-screw", "set-screw-m6x8", "hub-b", origin=(15.9, 0, 32))
    place(p, "pulley", "pulley-spa-140", "line-shaft")
    place(p, "pulley-set-screw", "set-screw-m6x8", "pulley", origin=(15.9, 0, 335))
    for k, w, flip in ((1, PB1, False), (2, PB2, True)):
        place(p, f"pb{k}-inner-ring", "uc205-inner-ring", "line-shaft", origin=(0, 0, w),
              flip=flip)
        for j, a in enumerate((0, 120)):
            place(p, f"pb{k}-insert-set-screw-{j+1}", "set-screw-m6x5", f"pb{k}-inner-ring",
                  origin=(12.6 * math.cos(math.radians(a)), 12.6 * math.sin(math.radians(a)),
                          -15.5), rotate=a)
        place(p, f"pb{k}-balls", "uc205-balls", f"pb{k}-housing", form="revolute",
              angle="shaft * 0.4")
    for k, w in ((1, 136.0), (2, 264.0)):
        place(p, f"collar-{k}", "shaft-collar-25", "line-shaft", origin=(0, 0, w))
        place(p, f"collar-{k}-set-screw", "set-screw-m6x8", f"collar-{k}", origin=(12.6, 0, 0))
    # motor hold-down: bolt, washer on the foot; washer and nut under the plate
    n = 0
    for w in (-210, -110):
        for v in (-62.5, 62.5):
            n += 1
            place(p, f"motor-washer-top-{n}", "washer-m8", "base", origin=(-68.0, v, w))
            place(p, f"motor-bolt-{n}", "hex-bolt-m8x40", "base", origin=(-66.4, v, w))
            place(p, f"motor-washer-bottom-{n}", "washer-m8", "base", origin=(-96.6, v, w))
            place(p, f"motor-nut-{n}", "hex-nut-m8", "base", origin=(-103.4, v, w))


def build(p):
    p.run("init", "--unit", "mm")
    base(p)
    motor(p)
    coupling(p)
    line_shaft(p)
    pulley(p)
    pillow_block(p)
    set_screw(p, "set-screw-m6x8", 8)
    set_screw(p, "set-screw-m6x5", 5)
    hex_bolt(p, "hex-bolt-m12x40", 12, 40, 18, 7.5)
    hex_bolt(p, "hex-bolt-m8x40", 8, 40, 13, 5.3)
    washer(p, "washer-m12", 13, 24, 2.5)
    washer(p, "washer-m8", 8.4, 16, 1.6)
    hex_nut(p, "hex-nut-m8", 8, 13, 6.8)
    assemble(p)


main(build)
