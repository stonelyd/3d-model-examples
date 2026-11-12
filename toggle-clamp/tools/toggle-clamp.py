"""A horizontal hold-down toggle clamp in the manner of a Destaco 225-U
(the ~200 kg holding-capacity class of horizontal clamps), as a ryucad
assembly built through the CLI only.

Over-centre four-bar linkage, all pivots parallel to world y:

  ground  the stamped base (a flat flange with four M6 clearance holes and
          two uprights bent up from it) carrying two pivots, H (handle) and
          A (arm), 36.4 mm apart at 32 mm above the mounting face;
  crank   the handle, a U-channel turning on H, with its crank pin C at
          20.8 mm, and a bar with a red vinyl grip running out rearward;
  coupler two connecting links, one each side, from C to D (26.7 mm);
  rocker  the clamp arm, a U-channel turning on A, with its link pin D at
          13 mm, carrying an M8 spindle 75 mm ahead of A: a hex bolt locked
          by two nuts through the arm's web, its head under a neoprene cap.

Clamped, H, C and D lie 3 deg past collinear (C above the line HD): the
toggle is over centre, so a push up on the spindle compresses the links
and drives C up into the lock rather than opening the clamp.

Every part is authored in world coordinates (x forward towards the
spindle, y across, z up) and each instance is placed in the "linkage
frame" (local z = world -y, local x = world x), so every pivot is a local
z axis and the revolute mates' offsets are plain origins.
"""
import json
import math
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from model import main  # noqa: E402

# ------------------------------------------------------------ the linkage
ZP = 32.0                       # pivot height above the mounting face
S = 1.3                         # linkage scale (designed at unit size)
H = (0.0, ZP)
A = (28.0 * S, ZP)
D = (A[0] + 8.0 * S, ZP + 6.0 * S)
HC = 16.0 * S
OVER = 3.0                      # degrees past the H-D line when clamped
_t = math.degrees(math.atan2(D[1] - H[1], D[0] - H[0])) + OVER
C = (H[0] + HC * math.cos(math.radians(_t)), H[1] + HC * math.sin(math.radians(_t)))
AD = math.dist(A, D)
CD = math.dist(C, D)
XS = A[0] + 75.0                # spindle axis

# lateral stack (|y|, mm)
UP = (8.0, 10.5)          # base uprights
ARM = (12.0, 14.5)        # clamp arm side plates
LINK = (16.3, 18.8)       # connecting links
HAN = (19.3, 21.8)        # handle side plates
YL = (LINK[0] + LINK[1]) / 2

COL = dict(zinc="#c4c8cd", base="#b3b8be", pin="#d6d9dd", clip="#2b2d31",
           steel="#8d939b", grip="#c0392b", rubber="#1c1d20", plate="#5d646d",
           work="#8fb3d1", screw="#1b1c1f")


def solve(handle_deg):
    """The arm angle (deg, + opens) for a handle angle (deg, + opens, i.e.
    clockwise seen from -y), on the branch the clamped pose is on."""
    a0 = math.radians(_t - handle_deg)
    c = (H[0] + HC * math.cos(a0), H[1] + HC * math.sin(a0))
    dang = math.atan2(D[1] - A[1], D[0] - A[0])
    d = math.dist(A, c)
    aa = (AD * AD - CD * CD + d * d) / (2 * d)
    hh = math.sqrt(max(0.0, AD * AD - aa * aa))
    ux, uy = (c[0] - A[0]) / d, (c[1] - A[1]) / d
    px, py = A[0] + aa * ux, A[1] + aa * uy
    best = None
    for s in (1, -1):
        dd = (px - s * hh * uy, py + s * hh * ux)
        ph = math.degrees(math.atan2(dd[1] - A[1], dd[0] - A[0]) - dang)
        ph = (ph + 180) % 360 - 180
        if best is None or abs(ph) < abs(best):
            best = ph
    return best


# --------------------------------------------- world -> part-local frame
def L(w):
    return (w[0], w[2], -w[1])


def cross(a, b):
    return (a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0])


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


def hull(points):
    pts = sorted(set((round(x, 6), round(y, 6)) for x, y in points))

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0]-out[-2][0])*(p[1]-out[-2][1])
                                     - (out[-1][1]-out[-2][1])*(p[0]-out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out
    lo, up = half(pts), half(reversed(pts))
    return lo[:-1] + up[:-1]


def disc(c, r, n=96):
    return [(c[0] + r*math.cos(2*math.pi*i/n), c[1] + r*math.sin(2*math.pi*i/n))
            for i in range(n)]


def rect(x0, x1, z0, z1):
    return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]


def plate(p, part, fid, poly, y1, y2, **flags):
    """Extrude an (x, z) outline across world y from y1 to y2 (y1 < y2)."""
    sk = p.sketch(part, pts_lines(poly), fid=f"{fid}-outline",
                  place=(L((0, y2, 0)), L((0, -1, 0)), L((1, 0, 0))))
    return p.add(part, "extrude", fid, sketch=sk, length=f"{y2-y1:.6f} mm", **flags)


def wcyl(p, part, fid, r, p0, p1, **flags):
    d = tuple(b - a for a, b in zip(p0, p1))
    n = math.sqrt(sum(c*c for c in d))
    z = tuple(c / n for c in d)
    x = (1, 0, 0) if abs(z[0]) < 0.9 else (0, 0, 1)
    return p.add(part, "cylinder", fid, {"radius": f"{r:.6f}", "height": f"{n:.6f}"},
                 (L(p0), L(z), L(x)), **flags)


def wbox(p, part, fid, lo, hi, **flags):
    """An axis-aligned world box from corner lo to corner hi."""
    size = (hi[0]-lo[0], hi[2]-lo[2], hi[1]-lo[1])     # local x, y(=world z), z(=-world y)
    corner = (lo[0], lo[2], -hi[1])
    params = {"x": size[0], "y": size[1], "z": size[2]}
    return p.add(part, "box", fid, params, (corner, (0, 0, 1), (1, 0, 0)), **flags)


def rev(p, part, fid, P, a, n, prof, **flags):
    """Revolve a closed (axial, radial) profile about the world axis through
    P along a; n is a world direction perpendicular to a."""
    zs = cross(n, a)
    pts = [(r, ax) for ax, r in prof]
    axs = [ax for ax, _ in prof]
    ops = pts_lines(pts)
    ops += [{"op": "add", "type": "point", "id": "ax1", "at": ["0 mm", f"{min(axs)-1:.6f} mm"]},
            {"op": "add", "type": "point", "id": "ax2", "at": ["0 mm", f"{max(axs)+1:.6f} mm"]},
            {"op": "add", "type": "line", "id": "axis", "start": "ax1", "end": "ax2"}]
    sk = p.sketch(part, ops, fid=f"{fid}-profile", place=(L(P), L(zs), L(n)))
    return p.add(part, "revolve", fid, sketch=sk, axis="axis", angle="full", **flags)


def hexagon(p, part, fid, P, a, n, af, z0, length, **flags):
    R = af / math.sqrt(3)
    pts = [(R*math.cos(math.radians(30+60*i)), R*math.sin(math.radians(30+60*i)))
           for i in range(6)]
    o = tuple(P[i] + a[i]*z0 for i in range(3))
    sk = p.sketch(part, pts_lines(pts), fid=f"{fid}-profile", place=(L(o), L(a), L(n)))
    return p.add(part, "extrude", fid, sketch=sk, length=f"{length:.6f} mm", **flags)


def colour(p, part, c):
    p.run("colour", part, "--colour", c)


def ring(lo, hi, r0, r1):
    return [(lo, r0), (hi, r0), (hi, r1), (lo, r1)]


Y = (0, 1, 0)
ZU = (0, 0, 1)
XF = (1, 0, 0)


# ----------------------------------------------------------------- parts
def base(p):
    b = p.part("base")
    wbox(p, b, "flange", (-16, -26, 0), (56, 26, 3))
    up = hull(disc(H, 9) + disc(A, 9) + rect(-11, 47, 1.5, 20))
    for side, (y1, y2) in (("l", UP), ("r", (-UP[1], -UP[0]))):
        plate(p, b, f"upright-{side}", up, y1, y2, operation="join", target="flange")
    for name, (px, pz) in (("h", H), ("a", A)):
        wcyl(p, b, f"bore-{name}", 3.1, (px, -12, pz), (px, 12, pz), operation="cut")
    for i, (x, y) in enumerate(((-8, 19), (-8, -19), (48, 19), (48, -19))):
        wcyl(p, b, f"mount-{i+1}", 3.3, (x, y, -1), (x, y, 4), operation="cut")
    colour(p, b, COL["base"])


def arm(p):
    a = p.part("clamp-arm")
    lug = hull(disc(A, 9.5) + disc(D, 6.5))
    bar = [(A[0], ZP - 7), (XS + 11, ZP - 7), (XS + 14, ZP - 3), (XS + 14, ZP + 12),
           (A[0] + 4, ZP + 12)]
    for side, (y1, y2) in (("l", ARM), ("r", (-ARM[1], -ARM[0]))):
        plate(p, a, f"plate-{side}", lug, y1, y2, **({} if side == "l" else
                                                      dict(operation="new")))
        plate(p, a, f"bar-{side}", bar, y1, y2, operation="join", target=f"plate-{side}")
    wbox(p, a, "web", (A[0] + 22, -ARM[1] + 0.5, ZP + 9), (XS + 13.5, ARM[1] - 0.5, ZP + 11.5))
    p.add(a, "boolean", "channel", op="unite", target="plate-l",
          tool=["plate-r", "web"])
    wcyl(p, a, "bore-a", 3.1, (A[0], -16, A[1]), (A[0], 16, A[1]), operation="cut")
    wcyl(p, a, "bore-d", 2.6, (D[0], -16, D[1]), (D[0], 16, D[1]), operation="cut")
    wcyl(p, a, "spindle-hole", 4.5, (XS, 0, ZP + 8), (XS, 0, ZP + 13), operation="cut")
    colour(p, a, COL["zinc"])


def handle(p):
    h = p.part("handle")
    crank = hull(disc(H, 8.5) + disc(C, 6.5))
    tail = hull(disc(H, 9) + rect(-58, -30, ZP - 1, ZP + 13))
    for side, (y1, y2) in (("l", HAN), ("r", (-HAN[1], -HAN[0]))):
        plate(p, h, f"tail-{side}", tail, y1, y2, **({} if side == "l" else
                                                      dict(operation="new")))
        plate(p, h, f"crank-{side}", crank, y1, y2, operation="join", target=f"tail-{side}")
    wbox(p, h, "web", (-58, -HAN[1], ZP + 10), (-26, HAN[1], ZP + 13))
    wcyl(p, h, "bar", 6.0, (-54, 0, ZP + 6.5), (-128, 0, ZP + 6.5))
    p.add(h, "boolean", "frame", op="unite", target="tail-l",
          tool=["tail-r", "web", "bar"])
    wcyl(p, h, "bore-h", 3.1, (H[0], -23, H[1]), (H[0], 23, H[1]), operation="cut")
    wcyl(p, h, "bore-c", 2.6, (C[0], -23, C[1]), (C[0], 23, C[1]), operation="cut")
    colour(p, h, COL["zinc"])


def grip(p):
    g = p.part("grip")
    zg = ZP + 6.5
    # axial coordinate runs rearward (-x) from x = -60
    prof = [(0, 6.05), (68.3, 6.05), (68.3, 0.0), (72.0, 0.0), (72.0, 9.0), (70.5, 10.8),
            (6, 10.0), (0, 9.2)]
    rev(p, g, "sleeve", (-60, 0, zg), (-1, 0, 0), (0, 0, 1), prof)
    colour(p, g, COL["grip"])


def link(p):
    k = p.part("link")
    t = (LINK[1] - LINK[0]) / 2
    plate(p, k, "plate", hull(disc(C, 6) + disc(D, 6)), -t, t)
    wcyl(p, k, "bore-c", 2.6, (C[0], -3, C[1]), (C[0], 3, C[1]), operation="cut")
    wcyl(p, k, "bore-d", 2.6, (D[0], -3, D[1]), (D[0], 3, D[1]), operation="cut")
    colour(p, k, COL["steel"])


def pin(p, name, r, head_r, y_head, y_end, y_groove, head_t):
    """A headed pin along world y at x = z = 0, head from y_head outwards
    (sign of y_end opposite), an e-clip groove at y_groove (0.9 wide)."""
    c = p.part(name)
    s = 1 if y_end > y_head else -1         # the shank's direction
    g0, g1 = sorted((y_groove, y_groove + s * 0.9))
    lo, hi = sorted((y_head - s * head_t, y_end))
    prof = [(lo, 0), (hi, 0)]
    # walk the outline in axial order: build radial at each station
    stations = []
    if s > 0:
        stations = [(lo, head_r), (y_head, head_r), (y_head, r), (g0, r), (g0, r - 0.45),
                    (g1, r - 0.45), (g1, r), (hi - 0.4, r), (hi, r - 0.4)]
    else:
        stations = [(lo, r - 0.4), (lo + 0.4, r), (g0, r), (g0, r - 0.45), (g1, r - 0.45),
                    (g1, r), (y_head, r), (y_head, head_r), (hi, head_r)]
    prof = [(lo, 0)] + stations + [(hi, 0)]
    # remove duplicate consecutive points
    clean = []
    for q in prof:
        if not clean or (abs(q[0]-clean[-1][0]) > 1e-9 or abs(q[1]-clean[-1][1]) > 1e-9):
            clean.append(q)
    rev(p, c, "pin", (0, 0, 0), Y, XF, clean)
    colour(p, c, COL["pin"])


def clip(p, name, r_groove, r_out):
    c = p.part(name)
    rev(p, c, "ring", (0, 0, 0), Y, XF, ring(0, 0.85, r_groove + 0.02, r_out))
    p.block(c, "gap", (r_out, 2.4, 2.0), L((r_out * 0.75, 0.4, 0)), (0, 0, 1), (1, 0, 0),
            operation="cut")
    colour(p, c, COL["clip"])


def spacer(p):
    c = p.part("spacer-h")
    rev(p, c, "tube", (0, 0, 0), Y, XF, ring(0, HAN[0] - UP[1] - 0.2, 3.05, 5.0))
    colour(p, c, COL["pin"])


def spindle(p):
    b = p.part("spindle-bolt")       # M8 x 35 hex bolt, head down, axis world z at x=y=0
    hexagon(p, b, "head", (0, 0, 0), ZU, XF, 13.0, 0, 5.3)
    rev(p, b, "shank", (0, 0, 0), ZU, XF, [(5.0, 0), (5.0, 4.0), (39.4, 4.0), (40.3, 3.1),
                                            (40.3, 0)], operation="join", target="head")
    colour(p, b, COL["steel"])
    n = p.part("nut-m8")             # ISO 4032 M8, m = 6.8
    hexagon(p, n, "body", (0, 0, 0), ZU, XF, 13.0, 0, 6.8)
    wcyl(p, n, "bore", 4.05, (0, 0, -1), (0, 0, 8), operation="cut")
    colour(p, n, COL["steel"])
    t = p.part("spindle-cap")        # neoprene cap over the bolt head
    rev(p, t, "cap", (0, 0, 0), ZU, XF, [(0, 0), (0, 9.2), (0.8, 10.0), (10.9, 10.0),
                                          (10.9, 4.1), (7.5, 4.1), (7.5, 7.65),
                                          (2.0, 7.65), (2.0, 0)])
    colour(p, t, COL["rubber"])


def fixture(p):
    f = p.part("fixture-plate")
    wbox(p, f, "plate", (-40, -50, -12), (150, 50, 0))
    for i, (x, y) in enumerate(((-8, 19), (-8, -19), (48, 19), (48, -19))):
        wcyl(p, f, f"tap-{i+1}", 3.02, (x, y, -13), (x, y, 1), operation="cut")
    colour(p, f, COL["plate"])
    w = p.part("workpiece")
    wbox(p, w, "block", (92, -22, 0), (132, 22, 12))
    colour(p, w, COL["work"])
    s = p.part("screw-m6x16")        # ISO 4762 socket head cap screw, head up
    wcyl(p, s, "shank", 3.0, (0, 0, -16), (0, 0, 0))
    wcyl(p, s, "head", 5.0, (0, 0, 0), (0, 0, 6), operation="join", target="shank")
    hexagon(p, s, "socket", (0, 0, 0), ZU, XF, 5.0, 2.8, 3.5, operation="cut", target="shank")
    colour(p, s, COL["screw"])
    wsh = p.part("washer-m6")        # ISO 7089 6.4 x 12 x 1.6
    rev(p, wsh, "washer", (0, 0, 0), ZU, XF, ring(0, 1.6, 3.2, 6.0))
    colour(p, wsh, COL["pin"])


# --------------------------------------------------------------- assembly
ASM = "toggle-clamp"
POSE = {}     # instance -> its frame's origin, world


def inst(p, iid, part, at=(0, 0, 0), fixed=False):
    POSE[iid] = at
    flags = dict(of=part, origin=",".join(f"{c:.6f}mm" for c in at),
                 z="0,-1,0", x="1,0,0")
    if fixed:
        flags["fixed"] = True
    p.add(ASM, "instance", iid, **flags)


def local(iid, w):
    o = POSE[iid]
    return L(tuple(w[i] - o[i] for i in range(3)))


def off(iid, w, flip=False):
    o = {"origin": [f"{c:.6f} mm" for c in local(iid, w)]}
    if flip:
        o["flip"] = True
    return json.dumps(o)


def fasten(p, a, b):
    p.add(ASM, "mate", f"{b}-on-{a}", form="fastened", a=f"{ASM}/{a}",
          a_offset=off(a, POSE[b]), b=f"{ASM}/{b}", b_offset="{}")


def pivot(p, mid, a, b, w, angle=None, flip=False):
    flags = dict(form="revolute", a=f"{ASM}/{a}", a_offset=off(a, w, flip),
                 b=f"{ASM}/{b}", b_offset=off(b, w, flip))
    if angle:
        flags["angle"] = angle
    p.add(ASM, "mate", mid, **flags)


PROPS = {  # part: (name, description, make or buy, material)
    "base": ("Base", "Stamped flanged base, two uprights, 4x 6.6 mm mounting holes", "make",
             "Steel, zinc plated"),
    "clamp-arm": ("Clamp arm", "U-channel arm, pivot A and link pin D, M8 spindle hole", "make",
                  "Steel, zinc plated"),
    "handle": ("Handle", "U-channel handle with crank pin C and grip bar", "make",
               "Steel, zinc plated"),
    "grip": ("Handle grip", "Vinyl grip sleeve, closed end", "buy", "PVC"),
    "link": ("Connecting link", "C to D link, 26.7 mm centres", "make", "Steel, zinc plated"),
    "pin-a": ("Pivot pin A", "6 mm headed pivot pin, e-clip groove", "make", "Steel, hardened"),
    "pin-h": ("Pivot pin H", "6 mm headed pivot pin, e-clip groove", "make", "Steel, hardened"),
    "pin-c": ("Link pin C (left)", "5 mm headed pin, e-clip groove", "make", "Steel, hardened"),
    "pin-c-r": ("Link pin C (right)", "5 mm headed pin, e-clip groove", "make",
                "Steel, hardened"),
    "pin-d": ("Link pin D (left)", "5 mm headed pin, e-clip groove", "make", "Steel, hardened"),
    "pin-d-r": ("Link pin D (right)", "5 mm headed pin, e-clip groove", "make",
                "Steel, hardened"),
    "clip-6": ("Retaining clip 6 mm", "E-style clip for 6 mm pin (groove 5.1 mm)", "buy",
               "Spring steel"),
    "clip-5": ("Retaining clip 5 mm", "E-style clip for 5 mm pin (groove 4.1 mm)", "buy",
               "Spring steel"),
    "spacer-h": ("Spacer", "6.1 x 10 x 8.6 mm spacer tube on pivot H", "make", "Steel"),
    "spindle-bolt": ("Spindle bolt", "Hex bolt M8 x 35 (thread not modelled)", "buy",
                     "Steel 8.8, zinc plated"),
    "nut-m8": ("Hex nut M8", "ISO 4032 M8", "buy", "Steel 8, zinc plated"),
    "spindle-cap": ("Spindle cap", "Neoprene cap over the spindle bolt head, 20 mm", "buy",
                    "Neoprene"),
    "fixture-plate": ("Fixture plate", "190 x 100 x 12 mm plate, 4x M6 tapped", "make",
                      "Aluminium 6061"),
    "workpiece": ("Workpiece", "40 x 44 x 12 mm sample block (context only)", "make",
                  "Aluminium"),
    "screw-m6x16": ("Socket head cap screw M6 x 16", "ISO 4762 M6 x 16", "buy",
                    "Steel 12.9"),
    "washer-m6": ("Washer M6", "ISO 7089 6.4 x 12 x 1.6", "buy", "Steel"),
}


def properties(p):
    for part, (name, desc, mb, mat) in PROPS.items():
        p.run("props", "set", part, f"name={name}", f"description={desc}", f"make_buy={mb}",
              f"material={mat}")


def build(p):
    p.run("init", "--unit", "mm")
    base(p)
    arm(p)
    handle(p)
    grip(p)
    link(p)
    # pins: A and H through the middle (head +y, clip -y); C and D one per side
    pin(p, "pin-a", 3.0, 5.0, ARM[1] + 0.1, -(ARM[1] + 1.6), -(ARM[1] + 0.1), 1.4)
    pin(p, "pin-h", 3.0, 5.0, HAN[1] + 0.1, -(HAN[1] + 1.6), -(HAN[1] + 0.1), 1.6)
    for sg, sfx in ((1, ""), (-1, "-r")):
        # C: head outside the handle, clip inside the link
        pin(p, f"pin-c{sfx}", 2.5, 4.2, sg * (HAN[1] + 0.1), sg * (LINK[0] - 1.4),
            sg * (LINK[0] - 0.05), 1.3)
        # D: head inside the arm plate, clip outside the link
        pin(p, f"pin-d{sfx}", 2.5, 4.2, sg * (ARM[0] - 0.1), sg * (LINK[1] + 1.4),
            sg * (LINK[1] + 0.05), 1.3)
    clip(p, "clip-5", 2.05, 4.5)
    clip(p, "clip-6", 2.55, 5.4)
    spacer(p)
    spindle(p)
    fixture(p)
    properties(p)
    build_assembly(p)


def build_assembly(p):
    p.part(ASM, assembly=True)
    p.run("param", "set", ASM, "handle=0 deg")
    inst(p, "fixture-plate", "fixture-plate", fixed=True)
    for iid in ("workpiece", "base", "clamp-arm", "handle", "grip"):
        inst(p, iid, iid)
    fasten(p, "fixture-plate", "workpiece")
    fasten(p, "fixture-plate", "base")
    fasten(p, "handle", "grip")
    for i, (x, y) in enumerate(((-8, 19), (-8, -19), (48, 19), (48, -19))):
        inst(p, f"washer-{i+1}", "washer-m6", (x, y, 3.0))
        inst(p, f"screw-{i+1}", "screw-m6x16", (x, y, 4.65))
        fasten(p, "base", f"washer-{i+1}")
        fasten(p, "base", f"screw-{i+1}")
    # pivot A
    inst(p, "pin-a", "pin-a", (A[0], 0, A[1]))
    inst(p, "clip-a", "clip-6", (A[0], -(ARM[1] + 1.0) + 0.02, A[1]))
    fasten(p, "base", "pin-a")
    fasten(p, "pin-a", "clip-a")
    # pivot H
    inst(p, "pin-h", "pin-h", (H[0], 0, H[1]))
    inst(p, "clip-h", "clip-6", (H[0], -(HAN[1] + 1.0) + 0.02, H[1]))
    inst(p, "spacer-h-l", "spacer-h", (H[0], UP[1] + 0.1, H[1]))
    inst(p, "spacer-h-r", "spacer-h", (H[0], -(HAN[0] - 0.1), H[1]))
    for iid in ("pin-h", "spacer-h-l", "spacer-h-r"):
        fasten(p, "base", iid)
    fasten(p, "pin-h", "clip-h")
    # spindle
    inst(p, "spindle-cap", "spindle-cap", (XS, 0, 12.1))
    inst(p, "spindle-bolt", "spindle-bolt", (XS, 0, 14.2))
    inst(p, "nut-lower", "nut-m8", (XS, 0, ZP + 9 - 0.1 - 6.8))
    inst(p, "nut-upper", "nut-m8", (XS, 0, ZP + 11.5 + 0.1))
    for iid in ("spindle-bolt", "spindle-cap", "nut-lower", "nut-upper"):
        fasten(p, "clamp-arm", iid)
    # links and their pins
    for side, sg in (("l", 1), ("r", -1)):
        inst(p, f"link-{side}", "link", (0, sg * YL, 0))
        inst(p, f"pin-c-{side}", "pin-c" if sg > 0 else "pin-c-r", (C[0], 0, C[1]))
        inst(p, f"pin-d-{side}", "pin-d" if sg > 0 else "pin-d-r", (D[0], 0, D[1]))
        inst(p, f"clip-c-{side}", "clip-5", (C[0], (LINK[0] - 0.95 + 0.02) if sg > 0 else -(LINK[0] - 0.05) + 0.02, C[1]))
        inst(p, f"clip-d-{side}", "clip-5", (D[0], (LINK[1] + 0.05 + 0.02) if sg > 0 else -(LINK[1] + 0.95) + 0.02, D[1]))
        fasten(p, "handle", f"pin-c-{side}")
        fasten(p, "clamp-arm", f"pin-d-{side}")
        fasten(p, f"pin-c-{side}", f"clip-c-{side}")
        fasten(p, f"pin-d-{side}", f"clip-d-{side}")
    # the four-bar
    pivot(p, "arm-pivot", "base", "clamp-arm", (A[0], 0, A[1]))
    pivot(p, "handle-pivot", "base", "handle", (H[0], 0, H[1]), angle="handle", flip=True)
    for side, sg in (("l", 1), ("r", -1)):
        pivot(p, f"link-{side}-on-handle", "handle", f"link-{side}", (C[0], sg * YL, C[1]))
        pivot(p, f"link-{side}-on-arm", "clamp-arm", f"link-{side}", (D[0], sg * YL, D[1]))


if __name__ == "__main__" and len(sys.argv) == 2 and sys.argv[1] == "--kin":
    print(json.dumps(dict(H=H, A=A, C=C, D=D, AD=AD, CD=CD, HC=HC, XS=XS,
                          poses={h: solve(h) for h in (0, 2, 5, 10, 20, 40, 60, 70)})))
    sys.exit(0)


main(build)
