"""A 100 mm (4 in) machinist's milling vise, as a ryucad assembly, through
the CLI only.

World axes: x along the lead screw (the moving jaw travels +x as the vise
opens), y across the jaws, z up. The table the vise is bolted to is the
plane z = 0. Every part is drawn where it sits at opening = 0 and placed
at the identity; mates then carry the moving parts.

Parts:
  body           the cast body: base with a keyway underneath and four
                 slotted mounting ears, two rails with inward lips (the
                 guided way), the fixed jaw, and the end wall the lead
                 screw is journalled in
  fixed-jaw-plate, moving-jaw-plate
                 hardened, ground jaw plates 100 x 32 x 10, each held by
                 two M6 socket-head cap screws in counterbores
  moving-jaw     the moving jaw: a block on the rail tops with a tongue
                 running down the slot between the lips
  gib-strip      two gib strips between the tongue and the lips, each
                 held by two M3 screws from the jaw's top
  clamp-plate    the hold-down plate under the lips
  lead-nut       the bronze lead-screw nut, bolted with the clamp plate
                 to the tongue by four M6 screws
  lead-screw     20 mm Acme-style screw, 4 mm lead, its thread drawn as
                 stacked trapezoidal rings (no helix), a thrust shoulder
                 and a 16 mm journal
  thrust-*       two axial ball thrust bearings, either side of the end
                 wall: shaft washer, housing washer, a cage of 12 balls
  thrust-collar  the collar locking the screw axially outside
  handle, handle-grip
                 crank handle (hub and crank bar) and its grip
  tenon-key      two tenon keys in the keyway, each held by an M6 screw
  m12 T-bolts and washers holding the ears down

Motion: the assembly parameter `opening` (mm between the jaw plates) is
clamped to 0..100 mm and drives the nut's slider mate; the lead screw's
revolute is driven from the same parameter, 360 deg per 4 mm lead, and
the thrust cages turn at half the screw's angle.
"""
import json
import math
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")
from model import main  # noqa: E402

X = (1, 0, 0)
Y = (0, 1, 0)
Z = (0, 0, 1)
NX = (-1, 0, 0)
NZ = (0, 0, -1)

ZA = 33.0          # lead screw axis height
LEAD = 4.0         # mm per turn
ASM = "vise"

PAINT = "#2f5f8f"
STEEL = "#b9bec5"
GROUND = "#d4d7db"
BRONZE = "#b5884a"
BLACK = "#1c1d20"
OXIDE = "#2c2e33"

CLAMP = "min(max(opening, 0 mm), 100 mm)"


# --------------------------------------------------------------- helpers
def f6(v):
    return f"{v:.6f}"


def box(p, part, fid, x0, x1, y0, y1, z0, z1, **flags):
    return p.block(part, fid, (x1 - x0, y1 - y0, z1 - z0),
                   ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), Z, X, **flags)


def zcyl(p, part, fid, r, x, y, z0, z1, **flags):
    return p.add(part, "cylinder", fid, {"radius": f6(r), "height": f6(z1 - z0)},
                 ((x, y, z0), Z, X), **flags)


def xcyl(p, part, fid, r, x0, x1, y=0.0, z=ZA, **flags):
    return p.add(part, "cylinder", fid, {"radius": f6(r), "height": f6(x1 - x0)},
                 ((x0, y, z), X, Y), **flags)


def pts_lines(points):
    ops = []
    for i, (a, b) in enumerate(points):
        ops.append({"op": "add", "type": "point", "id": f"p{i+1}",
                    "at": [f"{a:.6f} mm", f"{b:.6f} mm"]})
    n = len(points)
    for i in range(n):
        ops.append({"op": "add", "type": "line", "id": f"l{i+1}",
                    "start": f"p{i+1}", "end": f"p{(i+1) % n + 1}"})
    return ops


def xrev(p, part, fid, prof, **flags):
    """Revolve a closed (x, r) profile about the screw axis (y = 0, z = ZA)."""
    xs = [a for a, _ in prof]
    ops = pts_lines(prof)
    ops += [{"op": "add", "type": "point", "id": "ax1", "at": [f"{min(xs)-1:.6f} mm", "0 mm"]},
            {"op": "add", "type": "point", "id": "ax2", "at": [f"{max(xs)+1:.6f} mm", "0 mm"]},
            {"op": "add", "type": "line", "id": "axis", "start": "ax1", "end": "ax2"}]
    # sketch x -> world x, sketch y -> world z (z_sketch = -y)
    sk = p.sketch(part, ops, fid=f"{fid}-profile", place=((0, 0, ZA), (0, -1, 0), X))
    return p.add(part, "revolve", fid, sketch=sk, axis="axis", angle="full", **flags)


def ring_prof(r0, r1, x0, x1):
    return [(x0, r0), (x1, r0), (x1, r1), (x0, r1)]


def colour(p, part, c):
    p.run("colour", part, "--colour", c)


# ------------------------------------------------------------ the parts
EARS = (15.0, 155.0)     # x of the mounting ears' slots
EAR_Y = 71.0             # y of the T-bolts
KEYS = (0.0, 170.0)      # x of the tenon keys' centres


def body(p):
    b = p.part("body")
    box(p, b, "block", -50, 220, -55, 55, 0, 68)
    box(p, b, "fixed-jaw", -50, -10, -52, 52, 60, 108, operation="join", target="block")
    for i, c in enumerate(EARS):
        for s in (1, -1):
            fid = f"ear-{i+1}{'a' if s > 0 else 'b'}"
            box(p, b, fid, c - 20, c + 20, *sorted((s * 50, s * 85)), 0, 14,
                operation="join", target="block")
    # the guided way: a lower channel and a slot between the lips
    box(p, b, "channel", -2, 195, -38, 38, 16, 54, operation="cut", target="block")
    box(p, b, "slot", -2, 195, -24, 24, 53, 70, operation="cut", target="block")
    # keyway underneath, for tenon keys in the table's T-slot
    box(p, b, "keyway", -51, 221, -9, 9, -1, 5, operation="cut", target="block")
    # mounting slots, open at the ears' ends
    for i, c in enumerate(EARS):
        for s in (1, -1):
            box(p, b, f"slot-{i+1}{'a' if s > 0 else 'b'}", c - 7, c + 7,
                *sorted((s * 64, s * 90)), -1, 15, operation="cut", target="block")
            zcyl(p, b, f"slot-end-{i+1}{'a' if s > 0 else 'b'}", 7, c, s * 64, -1, 15,
                 operation="cut", target="block")
    # cast pockets in the side walls, lightening and stiffening ribs between
    for s in (1, -1):
        for i, (xa, xb) in enumerate(((5, 85), (100, 185))):
            box(p, b, f"pocket-{i+1}{'a' if s > 0 else 'b'}", xa, xb,
                *sorted((s * 50, s * 56)), 24, 48, operation="cut", target="block")
    # lead screw journal bore in the end wall
    xcyl(p, b, "journal-bore", 8.3, 194, 221, operation="cut", target="block")
    # tapped holes: fixed jaw plate (M6), tenon keys (M6)
    for y in (-30, 30):
        xcyl(p, b, f"jaw-tap-{'a' if y > 0 else 'b'}", 3.05, -28, -9, y=y, z=88,
             operation="cut", target="block")
    for i, c in enumerate(KEYS):
        zcyl(p, b, f"key-tap-{i+1}", 3.05, c, 0, 4, 16, operation="cut", target="block")
    colour(p, b, PAINT)


def jaw_plate(p, name, x_face, direction):
    """A hardened jaw plate: clamping face at x_face, its body behind it
    (direction +1 for the moving jaw's plate, -1 for the fixed jaw's)."""
    c = p.part(name)
    x0, x1 = sorted((x_face, x_face + 10 * direction))
    box(p, c, "plate", x0, x1, -50, 50, 72, 104)
    # a light horizontal V groove for round stock, and the screw counterbores
    for y in (-30, 30):
        tag = "a" if y > 0 else "b"
        cb0, cb1 = sorted((x_face - direction, x_face + 6.5 * direction))
        xcyl(p, c, f"cbore-{tag}", 5.3, cb0, cb1, y=y, z=88, operation="cut", target="plate")
        h0, h1 = sorted((x_face + 6 * direction, x_face + 11 * direction))
        xcyl(p, c, f"hole-{tag}", 3.3, h0, h1, y=y, z=88, operation="cut", target="plate")
    colour(p, c, GROUND)


def moving_jaw(p):
    c = p.part("moving-jaw")
    box(p, c, "jaw", 10, 60, -52, 52, 68.1, 108)
    box(p, c, "tongue", 10, 60, -19.9, 19.9, 53.9, 68.6, operation="join", target="jaw")
    # the top's relief, cast in
    box(p, c, "relief", 35, 61, -53, 53, 100, 109, operation="cut", target="jaw")
    for y in (-30, 30):
        xcyl(p, c, f"plate-tap-{'a' if y > 0 else 'b'}", 3.05, 9, 28, y=y, z=88,
             operation="cut", target="jaw")
    for i, (x, y) in enumerate(NUT_BOLTS):
        zcyl(p, c, f"nut-tap-{i+1}", 3.05, x, y, 53, 66, operation="cut", target="jaw")
    for i, (x, y) in enumerate(GIB_SCREWS):
        top = 100 if x > 35 else 108
        zcyl(p, c, f"gib-hole-{i+1}", 1.7, x, y, 67.9, top + 1, operation="cut", target="jaw")
        zcyl(p, c, f"gib-cbore-{i+1}", 3.0, x, y, top - 3.5, top + 1, operation="cut",
             target="jaw")
    colour(p, c, PAINT)


NUT_BOLTS = [(23, 16), (23, -16), (47, 16), (47, -16)]
GIB_SCREWS = [(20, 21.95), (50, 21.95), (20, -21.95), (50, -21.95)]


def gib(p):
    for s in (1, -1):
        name = f"gib-strip-{'a' if s > 0 else 'b'}"
        c = p.part(name)
        y0, y1 = sorted((s * 20.0, s * 23.9))
        box(p, c, "strip", 10, 60, y0, y1, 54.5, 68.0)
        for i, (x, y) in enumerate(g for g in GIB_SCREWS if g[1] * s > 0):
            zcyl(p, c, f"tap-{i+1}", 1.55, x, y, 55.5, 68.5, operation="cut", target="strip")
        colour(p, c, "#8a8f96")


def clamp_plate(p):
    c = p.part("clamp-plate")
    box(p, c, "plate", 10, 60, -36, 36, 47.6, 53.9)
    for i, (x, y) in enumerate(NUT_BOLTS):
        zcyl(p, c, f"hole-{i+1}", 3.3, x, y, 47, 54.5, operation="cut", target="plate")
    colour(p, c, "#5d6168")


def nut(p):
    c = p.part("lead-nut")
    box(p, c, "nut", 15, 55, -22, 22, 18, 47.6)
    xcyl(p, c, "bore", 10.2, 14, 56, operation="cut", target="nut")
    for i, (x, y) in enumerate(NUT_BOLTS):
        zcyl(p, c, f"cbore-{i+1}", 5.3, x, y, 17, 24.5, operation="cut", target="nut")
        zcyl(p, c, f"hole-{i+1}", 3.3, x, y, 24, 48.5, operation="cut", target="nut")
    colour(p, c, BRONZE)


def lead_screw(p):
    c = p.part("lead-screw")
    # Acme-style thread as stacked trapezoidal rings: 20 mm major, 16 mm minor
    x0, x1, minor, major = 3.0, 184.0, 8.0, 10.0
    prof = [(x0, 0.0), (x0, major - 0.5), (x0 + 0.5, major)]
    x = x0 + 0.5
    while x + LEAD <= x1 - 0.5:
        prof += [(x + 1.5, major), (x + 2.0, minor), (x + 3.5, minor), (x + 4.0, major)]
        x += LEAD
    prof += [(x1, major)]
    # thrust shoulder, then the 16 mm journal to the handle end
    prof += [(x1, 14.0), (189.0, 14.0), (189.0, 8.0), (262.0, 8.0), (263.0, 7.0),
             (263.0, 0.0)]
    xrev(p, c, "screw", prof)
    colour(p, c, "#9ca2a9")


def thrust_bearing(p, tag, x_shaft, x_house):
    """Shaft washer (x_shaft..+1.5, turns with the screw), housing washer
    (x_house..+1.5, still), 12 balls of 2.4 mm in a cage between them."""
    s = p.part(f"thrust-{tag}-shaft-washer")
    xrev(p, s, "washer", ring_prof(8.1, 14.0, x_shaft, x_shaft + 1.5))
    h = p.part(f"thrust-{tag}-housing-washer")
    xrev(p, h, "washer", ring_prof(8.4, 14.0, x_house, x_house + 1.5))
    xc = (min(x_shaft, x_house) + max(x_shaft, x_house) + 1.5) / 2
    b = p.part(f"thrust-{tag}-balls")
    xrev(p, b, "cage", ring_prof(10.6, 11.4, xc - 0.3, xc + 0.3))
    for i in range(12):
        a = math.radians(30 * i + 15)
        p.add(b, "sphere", f"ball-{i+1}", {"radius": "1.2"},
              ((xc, 11 * math.cos(a), ZA + 11 * math.sin(a)), Z, X), operation="join",
              target="cage")
    colour(p, s, STEEL)
    colour(p, h, STEEL)
    colour(p, b, "#e2e4e7")


def collar_and_handle(p):
    c = p.part("thrust-collar")
    xrev(p, c, "collar", ring_prof(8.05, 14.0, 225.8, 233.0))
    zcyl(p, c, "set-screw-hole", 2.0, 229.4, 0, ZA + 7, ZA + 15, operation="cut",
         target="collar")
    colour(p, c, OXIDE)
    h = p.part("handle")
    xrev(p, h, "hub", ring_prof(8.05, 15.0, 234.0, 262.0))
    box(p, h, "crank", 248, 260, -9, 9, ZA + 12, ZA + 117, operation="join", target="hub")
    xcyl(p, h, "boss", 12, 248, 260, z=ZA + 117, operation="join", target="hub")
    colour(p, h, OXIDE)
    g = p.part("handle-grip")
    xrev(p, g, "grip", [(260.1, 0.0), (260.1, 9.0), (262.0, 11.0), (296.0, 11.0),
                        (300.0, 8.0), (300.0, 0.0)])
    # built on the screw axis; its instance puts it at the crank's end
    colour(p, g, BLACK)


def tenon_key(p):
    c = p.part("tenon-key")
    box(p, c, "key", -15, 15, -8.9, 8.9, -5, 4.9)
    zcyl(p, c, "cbore", 5.3, 0, 0, -6, 1.5, operation="cut", target="key")
    zcyl(p, c, "hole", 3.3, 0, 0, 1, 6, operation="cut", target="key")
    colour(p, c, "#3a3d42")


def washer(p):
    c = p.part("washer-m12")
    zcyl(p, c, "washer", 12, 0, 0, 0, 2.5)
    zcyl(p, c, "hole", 6.6, 0, 0, -0.5, 3, operation="cut", target="washer")
    colour(p, c, STEEL)


def screw(p, name, head_r, head_h, r, length, socket, col=BLACK, hexhead=False):
    """Shank along -z from 0, head 0..head_h along +z."""
    c = p.part(name)
    zcyl(p, c, "shank", r, 0, 0, -length, 0)
    if hexhead:
        hexagon = [(head_r * math.cos(math.radians(60 * i + 30)),
                    head_r * math.sin(math.radians(60 * i + 30))) for i in range(6)]
        sk = p.sketch(c, pts_lines(hexagon), fid="head-profile", place=((0, 0, 0), Z, X))
        p.add(c, "extrude", "head", sketch=sk, operation="join", target="shank",
              length=f"{head_h:.6f} mm")
    else:
        zcyl(p, c, "head", head_r, 0, 0, 0, head_h, operation="join", target="shank")
        hexagon = [(socket * math.cos(math.radians(60 * i)),
                    socket * math.sin(math.radians(60 * i))) for i in range(6)]
        sk = p.sketch(c, pts_lines(hexagon), fid="socket-profile",
                      place=((0, 0, head_h * 0.4), Z, X))
        p.add(c, "extrude", "socket", sketch=sk, operation="cut", target="shank",
              length=f"{head_h * 0.7:.6f} mm")
    colour(p, c, col)


# ------------------------------------------------------------- the frames
def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0])


class Frame:
    def __init__(self, o, z, x):
        self.o, self.z, self.x = tuple(o), tuple(z), tuple(x)
        self.y = cross(self.z, self.x)

    def local(self, w):
        d = [w[i] - self.o[i] for i in range(3)]
        return (dot(d, self.x), dot(d, self.y), dot(d, self.z))


def offset_onto(A, B):
    """The connector offset taking frame A onto frame B: origin (in A's
    axes), a turn about z, then a flip about x."""
    flip = dot(A.z, B.z) < 0
    theta = math.degrees(math.atan2(dot(B.x, A.y), dot(B.x, A.x)))
    off = {"origin": [f"{c:.6f} mm" for c in A.local(B.o)], "rotate": f"{theta:.6f} deg"}
    if flip:
        off["flip"] = True
    return off


def cyl_face(p, part, radius, point, direction):
    """A cylindrical face of `part` with this radius whose axis runs through
    `point` along `direction` (part coordinates, mm): its reference and its
    connector frame."""
    for b in p.bodies(part):
        for f in b["faces"]:
            s = f["surface"]
            if s["type"] != "cylinder" or abs(s["radius"] * 1000 - radius) > 1e-6:
                continue
            fr = s["frame"]
            ax = tuple(fr["z"])
            if abs(dot(ax, direction)) < 0.999999:
                continue
            o = [c * 1000 for c in fr["origin"]]
            d = [point[i] - o[i] for i in range(3)]
            t = dot(d, ax)
            off = [d[i] - t * ax[i] for i in range(3)]
            if dot(off, off) > 1e-8:
                continue
            t0 = -dot(o, ax)
            foot = tuple(o[i] + t0 * ax[i] for i in range(3))
            return f"{b['solid']}/{f['name']}", Frame(foot, ax, tuple(fr["x"]))
    raise RuntimeError(f"no cylinder r={radius} through {point} along {direction} in {part}")


def flags_of(o, z, x):
    return dict(origin=",".join(f"{c:.6f}mm" for c in o),
                z=",".join(f"{c:.6f}" for c in z), x=",".join(f"{c:.6f}" for c in x))


def place(p, inst, part, fixed=False):
    if fixed:
        p.add(ASM, "instance", inst, of=part, fixed=True)
    else:
        p.add(ASM, "instance", inst, of=part)


def fasten(p, inst, to):
    p.add(ASM, "mate", f"{inst}-on-{to}", form="fastened", a=f"{ASM}/{to}", a_offset="{}",
          b=f"{ASM}/{inst}", b_offset="{}")


def screw_in(p, inst, part, host_inst, host_part, hole_r, at, head_dir):
    """A screw (part `part`, head along +z, shank along -z) with its head's
    underside at `at`, its head toward `head_dir`, fastened in its host's
    hole (radius hole_r, through `at` along head_dir)."""
    ref, A = cyl_face(p, host_part, hole_r, at, head_dir)
    x = A.x
    p.add(ASM, "instance", inst, of=part, **flags_of(at, head_dir, x))
    B = Frame(at, head_dir, x)
    p.add(ASM, "mate", f"{inst}-in-{host_inst}", form="fastened",
          a=f"{ASM}/{host_inst}/{ref}", a_offset=json.dumps(offset_onto(A, B)),
          b=f"{ASM}/{inst}", b_offset="{}")


def assembly(p):
    p.part(ASM, assembly=True)
    p.run("param", "set", ASM, "opening=0 mm", "lead=4 mm")
    place(p, "body", "body", fixed=True)

    # still parts on the body
    for inst in ("fixed-jaw-plate", "thrust-in-housing-washer", "thrust-out-housing-washer"):
        place(p, inst, inst)
        fasten(p, inst, "body")
    for i, c in enumerate(KEYS):
        inst = f"tenon-key-{i+1}"
        p.add(ASM, "instance", inst, of="tenon-key", **flags_of((c, 0, 0), Z, X))
        ref, A = cyl_face(p, "body", 3.05, (c, 0, 10), Z)
        # the key's own frame is the part's: z up, at its centre
        p.add(ASM, "mate", f"{inst}-in-body", form="fastened", a=f"{ASM}/body/{ref}",
              a_offset=json.dumps(offset_onto(A, Frame((c, 0, 0), Z, X))),
              b=f"{ASM}/{inst}", b_offset="{}")
        screw_in(p, f"key-screw-{i+1}", "m6x12", "body", "body", 3.05, (c, 0, 1.5), NZ)
    for y, tag in ((30, "a"), (-30, "b")):
        screw_in(p, f"fixed-plate-screw-{tag}", "m6x20", "body", "body", 3.05,
                 (-6.5, y, 88), X)
    k = 0
    for c in EARS:
        for s in (1, -1):
            k += 1
            at = (c, s * EAR_Y, 14)
            ref, A = cyl_face(p, "body", 7, (c, s * 64, 5), Z)
            p.add(ASM, "instance", f"ear-washer-{k}", of="washer-m12", **flags_of(at, Z, X))
            p.add(ASM, "mate", f"ear-washer-{k}-on-body", form="fastened",
                  a=f"{ASM}/body/{ref}", a_offset=json.dumps(offset_onto(A, Frame(at, Z, X))),
                  b=f"{ASM}/ear-washer-{k}", b_offset="{}")
            top = (c, s * EAR_Y, 16.5)
            p.add(ASM, "instance", f"t-bolt-{k}", of="m12x40-hex", **flags_of(top, Z, X))
            p.add(ASM, "mate", f"t-bolt-{k}-on-washer", form="fastened",
                  a=f"{ASM}/ear-washer-{k}",
                  a_offset=json.dumps({"origin": ["0 mm", "0 mm", "2.5 mm"]}),
                  b=f"{ASM}/t-bolt-{k}", b_offset="{}")

    # the lead screw: a revolute in the end wall, driven from `opening`
    place(p, "lead-screw", "lead-screw")
    ref_a, A = cyl_face(p, "body", 8.3, (200, 0, ZA), X)
    ref_b, B = cyl_face(p, "lead-screw", 8.0, (200, 0, ZA), X)
    sign = 1 if dot(A.z, X) > 0 else -1   # crank clockwise from the handle end closes
    p.add(ASM, "mate", "lead-screw-revolute", form="revolute", a=f"{ASM}/body/{ref_a}",
          a_offset=json.dumps(offset_onto(A, B)), b=f"{ASM}/lead-screw/{ref_b}",
          b_offset="{}", angle=f"{CLAMP} / lead * ({sign * 360} deg)")
    for inst in ("thrust-in-shaft-washer", "thrust-out-shaft-washer", "thrust-collar",
                 "handle"):
        place(p, inst, inst)
        fasten(p, inst, "lead-screw")
    grip_at = (0, 0, 117.0)
    p.add(ASM, "instance", "handle-grip", of="handle-grip", **flags_of(grip_at, Z, X))
    p.add(ASM, "mate", "handle-grip-on-handle", form="fastened", a=f"{ASM}/handle",
          a_offset=json.dumps({"origin": ["0 mm", "0 mm", "117 mm"]}),
          b=f"{ASM}/handle-grip", b_offset="{}")
    # the cages turn at half the screw's angle
    for tag, xc in (("in", 191.9), ("out", 222.9)):
        inst = f"thrust-{tag}-balls"
        place(p, inst, inst)
        ref_c, C = cyl_face(p, inst, 10.6, (xc, 0, ZA), X)
        p.add(ASM, "mate", f"{inst}-revolute", form="revolute", a=f"{ASM}/body/{ref_a}",
              a_offset=json.dumps(offset_onto(A, C)), b=f"{ASM}/{inst}/{ref_c}",
              b_offset="{}", angle=f"{CLAMP} / lead * ({sign * 180} deg)")

    # the moving jaw, on the nut's slider along the screw axis
    place(p, "lead-nut", "lead-nut")
    ref_n, N = cyl_face(p, "lead-nut", 10.2, (30, 0, ZA), X)
    dsign = "" if dot(A.z, X) > 0 else "0 mm - "
    p.add(ASM, "mate", "lead-nut-slider", form="slider", a=f"{ASM}/body/{ref_a}",
          a_offset=json.dumps(offset_onto(A, N)), b=f"{ASM}/lead-nut/{ref_n}",
          b_offset="{}", distance=f"{dsign}{CLAMP}")
    for inst in ("moving-jaw", "clamp-plate", "gib-strip-a", "gib-strip-b"):
        place(p, inst, inst)
        fasten(p, inst, "lead-nut" if inst == "moving-jaw" else "moving-jaw")
    place(p, "moving-jaw-plate", "moving-jaw-plate")
    fasten(p, "moving-jaw-plate", "moving-jaw")
    for y, tag in ((30, "a"), (-30, "b")):
        screw_in(p, f"moving-plate-screw-{tag}", "m6x20", "moving-jaw", "moving-jaw", 3.05,
                 (6.5, y, 88), NX)
    for i, (x, y) in enumerate(NUT_BOLTS):
        screw_in(p, f"nut-bolt-{i+1}", "m6x40", "moving-jaw", "moving-jaw", 3.05,
                 (x, y, 24.5), NZ)
    for i, (x, y) in enumerate(GIB_SCREWS):
        top = 100 if x > 35 else 108
        screw_in(p, f"gib-screw-{i+1}", "m3x40", "moving-jaw", "moving-jaw", 1.7,
                 (x, y, top - 3.5), Z)


DESCRIPTIONS = {
    "body": ("make", "Vise body, cast iron, ground ways, 100 mm jaw width"),
    "fixed-jaw-plate": ("make", "Jaw plate 100 x 32 x 10, hardened and ground"),
    "moving-jaw-plate": ("make", "Jaw plate 100 x 32 x 10, hardened and ground"),
    "moving-jaw": ("make", "Moving jaw, cast iron"),
    "gib-strip-a": ("make", "Gib strip 50 x 13.5 x 3.9, steel"),
    "gib-strip-b": ("make", "Gib strip 50 x 13.5 x 3.9, steel"),
    "clamp-plate": ("make", "Hold-down plate under the ways"),
    "lead-nut": ("make", "Lead screw nut, bronze, 20 mm x 4 mm lead"),
    "lead-screw": ("make", "Lead screw 20 mm Acme-style, 4 mm lead, 16 mm journal"),
    "thrust-in-shaft-washer": ("buy", "Axial ball thrust bearing 16 x 28: shaft washer"),
    "thrust-in-housing-washer": ("buy", "Axial ball thrust bearing 16 x 28: housing washer"),
    "thrust-in-balls": ("buy", "Axial ball thrust bearing 16 x 28: cage, 12 x 2.4 mm balls"),
    "thrust-out-shaft-washer": ("buy", "Axial ball thrust bearing 16 x 28: shaft washer"),
    "thrust-out-housing-washer": ("buy", "Axial ball thrust bearing 16 x 28: housing washer"),
    "thrust-out-balls": ("buy", "Axial ball thrust bearing 16 x 28: cage, 12 x 2.4 mm balls"),
    "thrust-collar": ("make", "Thrust collar, 16 mm bore, with set screw hole"),
    "handle": ("make", "Crank handle, 117 mm throw"),
    "handle-grip": ("make", "Handle grip, 22 mm"),
    "tenon-key": ("make", "Tenon key 30 x 17.8, for an 18 mm T-slot"),
    "washer-m12": ("buy", "Washer M12, 24 OD"),
    "m6x20": ("buy", "ISO 4762 M6 x 20 socket head cap screw"),
    "m6x12": ("buy", "ISO 4762 M6 x 12 socket head cap screw"),
    "m6x40": ("buy", "ISO 4762 M6 x 40 socket head cap screw"),
    "m3x40": ("buy", "ISO 4762 M3 x 40 socket head cap screw"),
    "m12x40-hex": ("buy", "M12 x 40 hex head bolt (T-slot hold-down, simplified)"),
}


def properties(p):
    for part, (mb, desc) in DESCRIPTIONS.items():
        p.run("props", "set", part, f"make_buy={mb}", f"description={desc}")


def build(p):
    p.run("init", "--unit", "mm")
    body(p)
    jaw_plate(p, "fixed-jaw-plate", 0.0, -1)
    jaw_plate(p, "moving-jaw-plate", 0.0, 1)
    moving_jaw(p)
    gib(p)
    clamp_plate(p)
    nut(p)
    lead_screw(p)
    thrust_bearing(p, "in", 189.1, 193.2)
    thrust_bearing(p, "out", 224.2, 220.1)
    collar_and_handle(p)
    tenon_key(p)
    washer(p)
    screw(p, "m6x20", 5.0, 6.0, 3.0, 20, 2.5)
    screw(p, "m6x12", 5.0, 6.0, 3.0, 12, 2.5)
    screw(p, "m6x40", 5.0, 6.0, 3.0, 40, 2.5)
    screw(p, "m3x40", 2.75, 3.0, 1.5, 40, 1.25)
    screw(p, "m12x40-hex", 10.4, 8.0, 6.0, 40, 0, col="#4a4d52", hexhead=True)
    properties(p)
    assembly(p)
    p.run("param", "set", ASM, "opening=20 mm")


main(build)
