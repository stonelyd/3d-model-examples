"""An external spur-gear hydraulic pump, Group-1 size, as a ryucad assembly,
built through the CLI only.

Gears: module 2, 12 teeth, 20 deg pressure angle, 18 mm face width, on a
24 mm centre distance. Tooth flanks are polyline involutes (the connector
takes no splines); the addendum is shortened to 13.8 mm tip radius and the
teeth thinned for 0.25 mm backlash, so the pair clears at every angle.

The drive gear is integral with its keyed drive shaft (14 mm, 5x5 feather
key); the idler gear is pressed on its own shaft. Both shafts run in four
14x16x10 sleeve bushings in the covers. The body holds the figure-8 gear
cavity and the inlet (13 mm, +x) and outlet (10 mm, -x) ports; front and
rear covers locate on dowel pins, seal on O-rings in face grooves and are
clamped by four M8x45 socket head cap screws from the rear. A 14x24x7 lip
seal sits in the front cover's pilot. Straight port adapters with bonded
seals stand in both ports.

Both gears turn on revolute mates. ryucad has no gear-ratio mate, so the
coupling is geometric only: the assembly parameter `theta` drives the drive
gear's revolute, and the idler's revolute is driven by the expression
`15 deg - theta` (equal gears, opposite turn, half a tooth out of phase).
"""
import json
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import main  # noqa: E402

Z, X, Y = (0, 0, 1), (1, 0, 0), (0, 1, 0)
ASM = "gear-pump"

# ---------------------------------------------------------------- numbers
M, NT, ALPHA = 2.0, 12, 20.0          # module, teeth, pressure angle
RP = M * NT / 2                        # 12 mm pitch radius
CD = 2 * RP                            # 24 mm centre distance
RA, RF = 13.8, 9.4                     # tip and root radius
BACKLASH = 0.25
FACE = 18.0                            # gear face width
BODY_T = 18.2                          # body thickness (0.1 mm end float each side)
YD, YI = CD / 2, -CD / 2               # drive and idler axes (x = 0)
R_CAV = 14.0                           # cavity bores (0.2 mm radial tip clearance)
R_JOURNAL = 7.0                        # 14 mm shafts
PORT_Z = BODY_T / 2
R_IN, R_OUT = 6.5, 5.0                 # inlet 13 mm, outlet 10 mm
BOLTS = [(sx * 23.0, sy * 30.0) for sx in (1, -1) for sy in (1, -1)]
DOWELS = [(0.0, 35.0), (0.0, -35.0)]
FRONT_Z0 = -16.0                       # front cover, z -16..0 (pilot to -20)
REAR_Z1 = BODY_T + 14.0                # rear cover, z 18.2..32.2


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


def xcyl(p, part, fid, r, x0, x1, y=0.0, z=PORT_Z, **flags):
    """A cylinder along x from x0 to x1 (either way round)."""
    d = (1, 0, 0) if x1 > x0 else (-1, 0, 0)
    return p.add(part, "cylinder", fid, {"radius": f"{r:.6f}", "height": f"{abs(x1-x0):.6f}"},
                 ((x0, y, z), d, Y), **flags)


def prism(p, part, fid, pts, z0, h, **flags):
    sk = p.sketch(part, pts_lines(pts), fid=f"{fid}-profile", place=((0, 0, z0), Z, X))
    return p.add(part, "extrude", fid, sketch=sk, length=f"{h:.6f} mm", **flags)


def chamfered_rect(hx, hy, c, cx=0.0, cy=0.0):
    return [(cx + x, cy + y) for x, y in
            [(hx - c, -hy), (hx, -hy + c), (hx, hy - c), (hx - c, hy),
             (-hx + c, hy), (-hx, hy - c), (-hx, -hy + c), (-hx + c, -hy)]]


def colour(p, part, c):
    p.run("colour", part, "--colour", c)


# ------------------------------------------------------------ gear tooth
def inv(a):
    return math.tan(a) - a


def gear_outline(nf=5, phase=15.0):
    """The gear's outline, tooth centres at phase + 30k deg: involute
    flanks as polylines from the base to the tip circle, a radial flank
    below the base circle, a polyline root arc."""
    rb = RP * math.cos(math.radians(ALPHA))
    ap = math.radians(ALPHA)
    psip = (math.pi * M / 2 - BACKLASH / 2) / (2 * RP)

    def psi(r):
        return psip + inv(ap) - inv(math.acos(min(1.0, rb / r)))
    pitch = 2 * math.pi / NT
    flank = [(RF, psi(rb) - 0.02), ((RF + rb) / 2, psi(rb))]
    flank += [(rb + (RA - rb) * (i / nf) ** 0.8, psi(rb + (RA - rb) * (i / nf) ** 0.8))
              for i in range(nf + 1)]
    pts = []
    for k in range(NT):
        c = math.radians(phase) + k * pitch
        pts += [(r, c - a) for r, a in flank]
        pts.append((RA, c))
        pts += [(r, c + a) for r, a in reversed(flank)]
        a0, a1 = c + flank[0][1], c + pitch - flank[0][1]
        pts += [(RF, a0 + (a1 - a0) * j / 4) for j in range(1, 4)]
    return [(r * math.cos(a), r * math.sin(a)) for r, a in pts]


# ------------------------------------------------------------------ parts
def body(p):
    b = p.part("body")
    prism(p, b, "block", chamfered_rect(32, 40, 4), 0, BODY_T)
    for fid, y in (("bore-drive", YD), ("bore-idler", YI)):
        cyl(p, b, fid, R_CAV, -0.5, BODY_T + 0.5, at=(0, y), operation="cut")
    xcyl(p, b, "inlet", R_IN, 33, 5, operation="cut")
    xcyl(p, b, "outlet", R_OUT, -33, -5, operation="cut")
    for i, (x, y) in enumerate(BOLTS):
        cyl(p, b, f"bolt-hole-{i+1}", 4.25, -0.5, BODY_T + 0.5, at=(x, y), operation="cut")
    for i, (x, y) in enumerate(DOWELS):
        cyl(p, b, f"dowel-hole-{i+1}", 2.5, -0.5, BODY_T + 0.5, at=(x, y), operation="cut")
    colour(p, b, "#c4c8cd")


def front_cover(p):
    c = p.part("front-cover")
    prism(p, c, "flange", chamfered_rect(52, 46, 8), FRONT_Z0, 10)
    prism(p, c, "block", chamfered_rect(32, 40, 4), -6.5, 6.5, operation="join",
          target="flange")
    cyl(p, c, "pilot", 16, -20, FRONT_Z0 + 0.5, at=(0, YD), operation="join", target="flange")
    cyl(p, c, "seal-pocket", 12, -20.5, -12.5, at=(0, YD), operation="cut")
    cyl(p, c, "shaft-hole", 7.5, -21, -10.5, at=(0, YD), operation="cut")
    for fid, y in (("bush-drive", YD), ("bush-idler", YI)):
        cyl(p, c, fid, 8, -11, 0.5, at=(0, y), operation="cut")
    for i, (x, y) in enumerate(BOLTS):
        cyl(p, c, f"tap-{i+1}", 4.0, -14, 0.5, at=(x, y), operation="cut")
    for i, (x, y) in enumerate(DOWELS):
        cyl(p, c, f"dowel-hole-{i+1}", 2.5, -6.5, 0.5, at=(x, y), operation="cut")
    rev(p, c, "o-ring-groove", ring_prof(28.0, 31.2, -2.0, 0.5), operation="cut")
    for i, (sx, sy) in enumerate([(1, 1), (-1, 1), (-1, -1), (1, -1)]):
        cyl(p, c, f"mount-{i+1}", 4.5, FRONT_Z0 - 0.5, -5.5, at=(43 * sx, 36 * sy),
            operation="cut")
    colour(p, c, "#4f5d6e")


def rear_cover(p):
    c = p.part("rear-cover")
    prism(p, c, "block", chamfered_rect(32, 40, 4), BODY_T, REAR_Z1 - BODY_T)
    for fid, y in (("bush-drive", YD), ("bush-idler", YI)):
        cyl(p, c, fid, 8, BODY_T - 0.5, 29.7, at=(0, y), operation="cut")
    for i, (x, y) in enumerate(BOLTS):
        cyl(p, c, f"bolt-hole-{i+1}", 4.25, BODY_T - 0.5, REAR_Z1 + 0.5, at=(x, y),
            operation="cut")
    for i, (x, y) in enumerate(DOWELS):
        cyl(p, c, f"dowel-hole-{i+1}", 2.5, BODY_T - 0.5, BODY_T + 6.5, at=(x, y),
            operation="cut")
    rev(p, c, "o-ring-groove", ring_prof(28.0, 31.2, BODY_T - 0.5, BODY_T + 2.0),
        operation="cut")
    colour(p, c, "#4f5d6e")


def drive_gear(p):
    g = p.part("drive-gear-shaft")
    cyl(p, g, "shaft", R_JOURNAL, -55, 29.2)
    prism(p, g, "gear", gear_outline(), 0.1, FACE, operation="join", target="shaft")
    p.block(g, "keyway", (3.6, 5.0, 24.0), (5.8, 0, -40), Z, X, operation="cut")
    colour(p, g, "#8d9299")


def idler_gear(p):
    g = p.part("idler-gear")
    prism(p, g, "gear", gear_outline(), 0.1, FACE)
    cyl(p, g, "bore", R_JOURNAL, -0.5, FACE + 0.6, operation="cut")
    colour(p, g, "#8d9299")
    s = p.part("idler-shaft")
    cyl(p, s, "shaft", R_JOURNAL, -10.7, 29.2)
    colour(p, s, "#b4b8be")


def small_parts(p):
    k = p.part("key-5x5x20")
    p.block(k, "key", (5.0, 5.0, 20.0), (6.5, 0, -40), Z, X)
    colour(p, k, "#a7acb4")

    b = p.part("bushing-14x16x10")
    rev(p, b, "sleeve", ring_prof(7.0, 8.0, 0, 10))
    colour(p, b, "#b08d57")

    s = p.part("lip-seal-14x24x7")
    rev(p, s, "seal", [(-19.7, 12.0), (-12.7, 12.0), (-12.7, 11.0), (-18.0, 11.0),
                       (-18.0, 9.5), (-13.5, 7.6), (-14.2, 7.0), (-16.0, 7.0),
                       (-19.7, 8.5)])
    colour(p, s, "#1f1f22")

    o = p.part("o-ring-56x3")
    n = 16
    sec = [(0.95 * math.sin(2 * math.pi * i / n), 29.6 + 1.5 * math.cos(2 * math.pi * i / n))
           for i in range(n)]
    rev(p, o, "ring", sec)
    colour(p, o, "#2a2a2e")

    d = p.part("dowel-5x12")
    cyl(p, d, "pin", 2.5, -6.0, 6.0)
    colour(p, d, "#d0d3d7")

    w = p.part("washer-m8")
    rev(p, w, "washer", ring_prof(4.3, 8.0, 0, 1.6))
    colour(p, w, "#b9bdc3")

    sc = p.part("shcs-m8x45")
    cyl(p, sc, "shank", 4.0, -45, 0.5)
    cyl(p, sc, "head", 6.5, 0, 8, operation="join", target="shank")
    hexagon = [(3.46 * math.cos(math.radians(60 * i)), 3.46 * math.sin(math.radians(60 * i)))
               for i in range(6)]
    sk = p.sketch(sc, pts_lines(hexagon), fid="socket-profile", place=((0, 0, 3.5), Z, X))
    p.add(sc, "extrude", "socket", sketch=sk, operation="cut", length="5 mm")
    colour(p, sc, "#1b1c1f")


def port_adapter(p, name, side, r_spigot, af, r_stub, r_bore, colour_hex):
    """A straight male port adapter standing in a port on side +1 (+x) or -1
    (-x): spigot in the port, a hex, a tube stub; and its bonded seal."""
    a = p.part(f"adapter-{name}")
    x = lambda v: side * v
    xcyl(p, a, "spigot", r_spigot, x(21), x(34.5))
    hexagon = [(af / math.sqrt(3) * math.cos(math.radians(60 * i + 30)),
                af / math.sqrt(3) * math.sin(math.radians(60 * i + 30))) for i in range(6)]
    sk = p.sketch(a, pts_lines(hexagon), fid="hex-profile",
                  place=((x(34), 0, PORT_Z), (side, 0, 0), Y))
    p.add(a, "extrude", "hex", sketch=sk, length="10 mm", operation="join", target="spigot")
    xcyl(p, a, "stub", r_stub, x(43.5), x(58), operation="join", target="spigot")
    xcyl(p, a, "bore", r_bore, x(20), x(59), operation="cut")
    colour(p, a, colour_hex)
    s = p.part(f"bonded-seal-{name}")
    xcyl(p, s, "washer", r_spigot + 4.5, x(32), x(34))
    xcyl(p, s, "hole", r_spigot + 0.1, x(31.5), x(34.5), operation="cut")
    colour(p, s, "#3a3c40")


PROPS = {  # part: (make or buy, description)
    "body": ("make", "Pump body, figure-8 gear cavity, inlet 13 mm / outlet 10 mm ports"),
    "front-cover": ("make", "Front (mounting) cover: 4-hole flange, 32 mm pilot, seal pocket"),
    "rear-cover": ("make", "Rear cover"),
    "drive-gear-shaft": ("make", "Drive gear m2 z12 b18, integral 14 mm keyed shaft"),
    "idler-gear": ("make", "Idler gear m2 z12 b18, 14 mm bore"),
    "idler-shaft": ("make", "Idler shaft 14 mm"),
    "key-5x5x20": ("buy", "Parallel key 5x5x20, square ends (DIN 6885 B)"),
    "bushing-14x16x10": ("buy", "Sleeve bushing 14x16x10 (PAP 1410 P10 type)"),
    "lip-seal-14x24x7": ("buy", "Radial shaft seal 14x24x7 (DIN 3760 type)"),
    "o-ring-56x3": ("buy", "O-ring, about 56 mm ID x 3 mm, modelled squeezed in its groove"),
    "dowel-5x12": ("buy", "Dowel pin 5 m6 x 12 (ISO 8734)"),
    "washer-m8": ("buy", "Washer M8 (ISO 7089)"),
    "shcs-m8x45": ("buy", "Socket head cap screw M8x45 (ISO 4762), thread not modelled"),
    "adapter-inlet": ("buy", "Straight port adapter, inlet (simplified, threads not modelled)"),
    "adapter-outlet": ("buy", "Straight port adapter, outlet (simplified, threads not modelled)"),
    "bonded-seal-inlet": ("buy", "Bonded seal for the inlet adapter"),
    "bonded-seal-outlet": ("buy", "Bonded seal for the outlet adapter"),
}


# --------------------------------------------------------------- assembly
def build(p):
    p.run("init", "--unit", "mm")
    body(p)
    front_cover(p)
    rear_cover(p)
    drive_gear(p)
    idler_gear(p)
    small_parts(p)
    port_adapter(p, "inlet", 1, R_IN, 22, 9.0, 5.5, "#c2c6cb")
    port_adapter(p, "outlet", -1, R_OUT, 19, 7.0, 4.0, "#c2c6cb")

    for part, (mb, desc) in PROPS.items():
        p.run("props", "set", part, f"make_buy={mb}", f"description={desc}")

    a = p.part(ASM, assembly=True)
    p.run("param", "set", ASM, "theta=0 deg")

    def place(iid, of, at=(0, 0, 0), rot=0.0, fixed=False):
        t = math.radians(rot)
        flags = dict(of=of, origin=",".join(f"{c:.6f}mm" for c in at), z="0,0,1",
                     x=f"{math.cos(t):.9f},{math.sin(t):.9f},0")
        if fixed:
            flags["fixed"] = True
        p.add(a, "instance", iid, **flags)

    def fasten(iid, to, at=None):
        off = "{}" if at is None else json.dumps(
            {"origin": [f"{c:.6f} mm" for c in at]})
        p.add(a, "mate", f"{iid}-fastened", form="fastened", a=f"{ASM}/{to}", a_offset=off,
              b=f"{ASM}/{iid}", b_offset="{}")

    place("body", "body", fixed=True)
    for iid in ("front-cover", "rear-cover", "adapter-inlet", "adapter-outlet",
                "bonded-seal-inlet", "bonded-seal-outlet"):
        place(iid, iid)
        fasten(iid, "body")

    # the rotating group
    place("drive-gear", "drive-gear-shaft", (0, YD, 0))
    p.add(a, "mate", "drive-revolute", form="revolute", a=f"{ASM}/body",
          a_offset=json.dumps({"origin": ["0 mm", f"{YD} mm", "0 mm"]}),
          b=f"{ASM}/drive-gear", b_offset="{}", angle="theta")
    place("idler-gear", "idler-gear", (0, YI, 0), rot=15.0)
    p.add(a, "mate", "idler-revolute", form="revolute", a=f"{ASM}/body",
          a_offset=json.dumps({"origin": ["0 mm", f"{YI} mm", "0 mm"]}),
          b=f"{ASM}/idler-gear", b_offset="{}", angle="15 deg - theta")
    place("idler-shaft", "idler-shaft", (0, YI, 0), rot=15.0)
    fasten("idler-shaft", "idler-gear")
    place("key", "key-5x5x20", (0, YD, 0))
    fasten("key", "drive-gear")

    # bushings, seal, O-rings in the covers
    for iid, y, z, cover in (("bushing-front-drive", YD, -10.6, "front-cover"),
                             ("bushing-front-idler", YI, -10.6, "front-cover"),
                             ("bushing-rear-drive", YD, 18.8, "rear-cover"),
                             ("bushing-rear-idler", YI, 18.8, "rear-cover")):
        place(iid, "bushing-14x16x10", (0, y, z))
        fasten(iid, cover, (0, y, z))
    place("lip-seal", "lip-seal-14x24x7", (0, YD, 0))
    fasten("lip-seal", "front-cover", (0, YD, 0))
    place("o-ring-front", "o-ring-56x3", (0, 0, -0.98))
    fasten("o-ring-front", "front-cover", (0, 0, -0.98))
    place("o-ring-rear", "o-ring-56x3", (0, 0, BODY_T + 0.98))
    fasten("o-ring-rear", "rear-cover", (0, 0, BODY_T + 0.98))

    # dowels, washers and screws
    for i, (x, y) in enumerate(DOWELS):
        for side, z, cover in (("front", 0.0, "front-cover"), ("rear", BODY_T, "rear-cover")):
            iid = f"dowel-{side}-{i+1}"
            place(iid, "dowel-5x12", (x, y, z))
            fasten(iid, cover, (x, y, z))
    for i, (x, y) in enumerate(BOLTS):
        place(f"washer-{i+1}", "washer-m8", (x, y, REAR_Z1))
        fasten(f"washer-{i+1}", "rear-cover", (x, y, REAR_Z1))
        place(f"screw-{i+1}", "shcs-m8x45", (x, y, REAR_Z1 + 1.6))
        fasten(f"screw-{i+1}", "rear-cover", (x, y, REAR_Z1 + 1.6))


main(build)
