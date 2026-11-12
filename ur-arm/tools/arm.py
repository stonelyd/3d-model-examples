"""A six-axis collaborative robot arm in the manner of a Universal Robots
UR5e (about 850 mm reach), as a ryucad assembly, through the CLI only.

Every joint is a real drive, built part by part in its own frame (axis z,
output face at z = 0, the housing below it):

  housing (tube, two bearing webs, crossed-roller seat, PCB standoffs,
  tapped holes) and its end cap; a frameless motor: a 12-slot stator with
  pole shoes, 12 concentrated copper coils, a rotor (hollow shaft and
  yoke) with 14 magnets under a retaining sleeve; two deep-groove ball
  bearings (races grooved, balls in a cage); a strain-wave gear: an
  oval wave-generator cam, its thin bearing, a cup flexspline with 160
  external teeth and a circular spline with 162 internal teeth (80:1);
  a crossed-roller output bearing (V-grooved rings, 36 rollers crossed at
  +/-45 deg in a cage); a brake (notched disc on the motor shaft, solenoid
  and a pin on a slider); a motor encoder (slotted disc, readhead on the
  drive PCB) and an output encoder (magnet ring and head); the output
  flange; and the screws holding it together, in counterbores and tapped
  holes.

The assembly places three sizes of joint (base and shoulder, elbow,
wrists) on links like UR's: a shoulder cradle, the upper arm and forearm
tubes with cuffs round the next housing, two wrist brackets and an
ISO 9409-1-50-4-M6 tool flange. Every moving part turns on a mate: each
output flange, rotor and rolling-element cage on a revolute about its
joint's axis, the brake pin on a slider, everything else fastened. The six
output angles are the assembly's parameters j1..j6.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, "/workspace/work/ryucad/crates/ryucad/tests/corpus")
from model import main  # noqa: E402

Z = (0, 0, 1)
X = (1, 0, 0)
Y = (0, 1, 0)

# Joint sizes: scale of the reference (base) drive, and screw lengths.
SIZES = {"l": 1.0, "m": 0.85, "s": 0.72}
OUT_SCREW = {"l": 12, "m": 10, "s": 8}

STEEL, DARK = "#6d7178", "#2a2c30"


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


# ------------------------------------------------------- joint internals
def housing(p, s, k):
    h = p.part(f"housing-{s}")
    prof = [(-128*k, 50*k), (-128*k, 55*k), (-2*k, 55*k), (-2*k, 50*k), (-18*k, 50*k),
            (-18*k, 44*k), (-21*k, 44*k), (-21*k, 50*k), (-54*k, 50*k), (-54*k, 26*k),
            (-60*k, 26*k), (-60*k, 50*k), (-102*k, 50*k), (-102*k, 26*k), (-108*k, 26*k),
            (-108*k, 50*k)]
    rev(p, h, "body", prof)
    for i, a in enumerate((60, 180, 300)):
        cyl(p, h, f"standoff-{i+1}", 2.5*k, -125*k, -107.5*k, at=polar(45*k, a),
            operation="join")
    # tapped holes for the end cap's screws, and clearance for the circular spline's
    cyl(p, h, "cap-tap", 1.5, -128*k, -131*k + 10.5, at=polar(52.5*k, 30), operation="cut")
    circ(p, h, "cap-taps", ["cap-tap"], 6)
    cyl(p, h, "cs-hole", 1.7, -60*k, -54*k, at=polar(40*k, 15), operation="cut")
    circ(p, h, "cs-holes", ["cs-hole"], 12)
    colour(p, h, "#c9ccd1")


def end_cap(p, s, k):
    c = p.part(f"end-cap-{s}")
    rev(p, c, "body", ring_prof(10*k, 55*k, -131*k, -128*k))
    cyl(p, c, "hole", 1.7, -131*k, -128*k, at=polar(52.5*k, 30), operation="cut")
    circ(p, c, "holes", ["hole"], 6)
    colour(p, c, "#5a9bd4")


def stator(p, s, k):
    c = p.part(f"stator-{s}")
    rev(p, c, "back-iron", ring_prof(42*k, 50*k, -98*k, -68*k))
    p.block(c, "tooth", (12.8*k, 5*k, 30*k), (36.6*k, 0, -83*k), Z, X, operation="join")
    p.block(c, "shoe", (1.5*k, 9*k, 30*k), (30.75*k, 0, -83*k), Z, X, operation="join")
    circ(p, c, "teeth", ["tooth", "shoe"], 12)
    colour(p, c, "#5b5f66")


def windings(p, s, k):
    c = p.part(f"windings-{s}")
    for i in range(12):
        a = math.radians(30 * i)
        d = (math.cos(a), math.sin(a), 0)
        cx = 36.5 * k
        centre = (cx * d[0], cx * d[1], -83 * k)
        coil = f"coil-{i+1}"
        p.block(c, coil, (9.8*k, 13*k, 36*k), centre, Z, d)
        p.block(c, f"{coil}-eye", (11*k, 5.1*k, 30.2*k), centre, Z, d, operation="cut",
                target=coil)
    colour(p, c, "#b87333")


def rotor(p, s, k):
    c = p.part(f"rotor-{s}")
    rev(p, c, "body", [(-118*k, 14*k), (-118*k, 17*k), (-98*k, 17*k), (-98*k, 28*k),
                       (-68*k, 28*k), (-68*k, 17*k), (-40*k, 17*k), (-40*k, 14*k)])
    colour(p, c, "#8b9098")


def magnets(p, s, k):
    c = p.part(f"magnets-{s}")
    rev(p, c, "sleeve", ring_prof(29.5*k, 29.8*k, -98*k, -68*k))
    p.block(c, "magnet", (1.5*k, 9*k, 30*k), (28.75*k, 0, -83*k), Z, X, operation="join")
    circ(p, c, "poles", ["magnet"], 14)
    colour(p, c, "#a7acb4")


def oval_ops(a, b, r1):
    r2 = ((a - r1) ** 2 + b ** 2 - r1 ** 2) / (2 * (b - r1))
    c1, c3 = (a - r1, 0), (-(a - r1), 0)
    c2, c4 = (0, -(r2 - b)), (0, r2 - b)

    def tangent(cl, cs):
        dx, dy = cs[0] - cl[0], cs[1] - cl[1]
        n = math.hypot(dx, dy)
        return (cl[0] + r2 * dx / n, cl[1] + r2 * dy / n)
    t1, t2 = tangent(c2, c1), tangent(c2, c3)
    t3, t4 = tangent(c4, c3), tangent(c4, c1)
    pt = lambda i, q: {"op": "add", "type": "point", "id": i,
                       "at": [f"{q[0]:.6f} mm", f"{q[1]:.6f} mm"]}
    ops = [pt("c1", c1), pt("c2", c2), pt("c3", c3), pt("c4", c4),
           pt("t1", t1), pt("t2", t2), pt("t3", t3), pt("t4", t4)]
    for aid, cen, st, en in (("a1", "c1", "t4", "t1"), ("a2", "c2", "t1", "t2"),
                             ("a3", "c3", "t2", "t3"), ("a4", "c4", "t3", "t4")):
        ops.append({"op": "add", "type": "arc", "id": aid, "center": cen, "start": st,
                    "end": en})
    return ops


def wave_generator(p, s, k):
    c = p.part(f"wave-gen-{s}")
    sk = p.sketch(c, oval_ops(21*k, 20.4*k, 19*k), fid="cam-profile",
                  place=((0, 0, -50*k), Z, X))
    p.add(c, "extrude", "cam", sketch=sk, length=f"{10*k:.6f} mm")
    cyl(p, c, "bore", 17*k, -50*k, -40*k, operation="cut")
    cyl(p, c, "lighten", 3*k, -50*k, -40*k, at=polar(19.2*k, 45), operation="cut")
    circ(p, c, "lightening", ["lighten"], 4)
    colour(p, c, "#7f858c")


def bearing(p, name, k, r_in, r_out, pitch, br, n, z0, z1, ball_colour="#d8dade"):
    zc = (z0 + z1) / 2
    gi, go = pitch - 0.55 * br, pitch + 0.55 * br
    i = p.part(f"{name}-in")
    rev(p, i, "race", ring_prof(r_in, gi, z0, z1))
    p.add(i, "torus", "groove", {"major_radius": f"{pitch:.6f}",
                                 "minor_radius": f"{br*1.04:.6f}"},
          ((0, 0, zc), Z, X), operation="cut")
    o = p.part(f"{name}-out")
    rev(p, o, "race", ring_prof(go, r_out, z0, z1))
    p.add(o, "torus", "groove", {"major_radius": f"{pitch:.6f}",
                                 "minor_radius": f"{br*1.04:.6f}"},
          ((0, 0, zc), Z, X), operation="cut")
    b = p.part(f"{name}-balls")
    rev(p, b, "cage", ring_prof(pitch - 0.35*br, pitch + 0.35*br, zc - 0.3*br, zc + 0.3*br))
    p.add(b, "sphere", "ball", {"radius": f"{br:.6f}"}, ((pitch, 0, zc), Z, X),
          operation="join")
    circ(p, b, "balls", ["ball"], n)
    for part, c in ((i, "#b9bdc3"), (o, "#b9bdc3"), (b, ball_colour)):
        colour(p, part, c)


def crossed_roller(p, s, k):
    pr, zc, h = 38*k, -13*k, 3.0*k
    groove = [(zc - h, pr), (zc, pr - h), (zc + h, pr), (zc, pr + h)]
    i = p.part(f"crb-in-{s}")
    rev(p, i, "ring", ring_prof(28*k, 36*k, -18*k, -8*k))
    rev(p, i, "groove", groove, operation="cut")
    cyl(p, i, "tap", 2.0, -18*k, -8*k, at=polar(32*k, 0), operation="cut")
    circ(p, i, "taps", ["tap"], 8)
    o = p.part(f"crb-out-{s}")
    rev(p, o, "ring", ring_prof(40*k, 50*k, -18*k, -8*k))
    rev(p, o, "groove", groove, operation="cut")
    r = p.part(f"crb-rollers-{s}")
    rev(p, r, "cage", ring_prof(pr - 0.4*k, pr + 0.4*k, zc - 0.5*k, zc + 0.5*k))
    rr, L = 2*k, 4*k
    q = math.sqrt(0.5)
    for fid, phi, up in (("roller-a", 0.0, 1), ("roller-b", 10.0, -1)):
        a = math.radians(phi)
        radial = (math.cos(a), math.sin(a), 0)
        ax = (q * radial[0], q * radial[1], up * q)
        perp = (-up * q * radial[0], -up * q * radial[1], q)
        centre = (pr * radial[0], pr * radial[1], zc)
        origin = tuple(c - ax[j] * L / 2 for j, c in enumerate(centre))
        p.add(r, "cylinder", fid, {"radius": f"{rr:.6f}", "height": f"{L:.6f}"},
              (origin, ax, perp), operation="join")
    circ(p, r, "rollers", ["roller-a", "roller-b"], 18)
    colour(p, i, "#aeb3b9")
    colour(p, o, "#aeb3b9")
    colour(p, r, "#e3e4e6")


def teeth_ops(r_a, r_b, w_a, w_b):
    return pts_lines([(r_a, -w_a), (r_b, -w_b), (r_b, w_b), (r_a, w_a)])


def flexspline(p, s, k):
    c = p.part(f"flexspline-{s}")
    rev(p, c, "cup", [(-50*k, 24.5*k), (-50*k, 26*k), (-17*k, 26*k), (-17*k, 20*k),
                      (-8*k, 20*k), (-8*k, 12*k), (-20*k, 12*k), (-20*k, 24.5*k)])
    rev(p, c, "band", ring_prof(25.5*k, 27.6*k, -50*k, -38*k), operation="join")
    n = 160
    gap = 2 * math.pi * 26.85 * k / n
    sk = p.sketch(c, teeth_ops(26.1*k, 27.9*k, 0.28*gap, 0.42*gap), fid="gap-profile",
                  place=((0, 0, -50*k), Z, X))
    p.add(c, "extrude", "gap", sketch=sk, operation="cut", length=f"{12*k:.6f} mm")
    circ(p, c, "teeth", ["gap"], n)
    colour(p, c, "#9da3aa")


def circular_spline(p, s, k):
    c = p.part(f"circular-spline-{s}")
    rev(p, c, "ring", ring_prof(27.75*k, 50*k, -54*k, -38*k))
    n = 162
    gap = 2 * math.pi * 28.5 * k / n
    sk = p.sketch(c, teeth_ops(27.4*k, 29.25*k, 0.42*gap, 0.28*gap), fid="gap-profile",
                  place=((0, 0, -54*k), Z, X))
    p.add(c, "extrude", "gap", sketch=sk, operation="cut", length=f"{16*k:.6f} mm")
    circ(p, c, "teeth", ["gap"], n)
    cyl(p, c, "tap", 1.5, -54*k, -60*k + 10.5, at=polar(40*k, 15), operation="cut")
    circ(p, c, "taps", ["tap"], 12)
    colour(p, c, "#7b8189")


def output_flange(p, s, k):
    c = p.part(f"output-{s}")
    rev(p, c, "flange", ring_prof(12*k, 38*k, -8*k, 0))
    cyl(p, c, "cbore", 3.6, -4.6, 0, at=polar(32*k, 0), operation="cut")
    cyl(p, c, "hole", 2.2, -8*k, 0, at=polar(32*k, 0), operation="cut")
    circ(p, c, "screw-holes", ["cbore", "hole"], 8)
    colour(p, c, "#c3c7cc")


def brake(p, s, k):
    d = p.part(f"brake-disk-{s}")
    rev(p, d, "disk", ring_prof(17*k, 36*k, -113*k, -111*k))
    p.block(d, "notch", (4.5*k, 3.6*k, 2*k), (34.75*k, 0, -112*k), Z, X, operation="cut")
    circ(p, d, "notches", ["notch"], 8)
    sol = p.part(f"brake-solenoid-{s}")
    cyl(p, sol, "body", 4*k, -125*k, -116*k, at=(34*k, 0))
    cyl(p, sol, "bore", 1.6*k, -125*k, -116*k, at=(34*k, 0), operation="cut")
    pin = p.part(f"brake-pin-{s}")
    cyl(p, pin, "pin", 1.5*k, -124*k, -114*k, at=(34*k, 0))
    colour(p, d, "#4b4f55")
    colour(p, sol, "#2f3237")
    colour(p, pin, "#d0d3d7")


def encoders(p, s, k):
    d = p.part(f"enc-disc-{s}")
    rev(p, d, "disc", ring_prof(17*k, 29*k, -118*k, -117.4*k))
    p.block(d, "slit", (2*k, 0.6*k, 0.6*k), (27*k, 0, -117.7*k), Z, X, operation="cut")
    circ(p, d, "slits", ["slit"], 64)
    r = p.part(f"readhead-{s}")
    p.block(r, "head", (5*k, 6*k, 6.4*k), (26*k, 0, -121.8*k), Z, X)
    pcb = p.part(f"pcb-{s}")
    rev(p, pcb, "board", ring_prof(16*k, 49*k, -127*k, -125*k))
    for i, (x, y, w, l) in enumerate([(-30, 0, 10, 10), (0, -30, 8, 6), (0, 30, 8, 6),
                                      (21, 21, 6, 5), (-21, 21, 6, 5), (-21, -21, 6, 5),
                                      (21, -21, 6, 5), (-38, 14, 5, 4), (-38, -14, 5, 4)]):
        p.block(pcb, f"chip-{i+1}", (w*k, l*k, 0.9*k), (x*k, y*k, -127.45*k), Z, X,
                operation="join")
    ring = p.part(f"out-enc-ring-{s}")
    rev(p, ring, "ring", ring_prof(38*k, 41*k, -7*k, -3*k))
    head = p.part(f"out-enc-head-{s}")
    p.block(head, "head", (4*k, 8*k, 5*k), (46*k, 0, -5.5*k), Z, X)
    for part, c in ((d, "#86a9c9"), (r, DARK), (pcb, "#1d6b3a"), (ring, "#3f4349"),
                    (head, DARK)):
        colour(p, part, c)


def screw(p, name, head_r, head_h, r, length, socket):
    c = p.part(name)
    cyl(p, c, "shank", r, -length, 0)
    cyl(p, c, "head", head_r, 0, head_h, operation="join")
    hexagon = [(socket * math.cos(math.radians(60 * i)),
                socket * math.sin(math.radians(60 * i))) for i in range(6)]
    sk = p.sketch(c, pts_lines(hexagon), fid="socket-profile",
                  place=((0, 0, head_h * 0.45), Z, X))
    p.add(c, "extrude", "socket", sketch=sk, operation="cut",
          length=f"{head_h*0.6:.6f} mm")
    colour(p, c, "#1b1c1f")


def joint_parts(p, s, k):
    housing(p, s, k)
    end_cap(p, s, k)
    stator(p, s, k)
    windings(p, s, k)
    rotor(p, s, k)
    magnets(p, s, k)
    wave_generator(p, s, k)
    bearing(p, f"brg-a-{s}", k, 17*k, 26*k, 21.5*k, 2.0*k, 14, -60*k, -54*k)
    bearing(p, f"brg-b-{s}", k, 17*k, 26*k, 21.5*k, 2.0*k, 14, -108*k, -102*k)
    bearing(p, f"wg-brg-{s}", k, 21.05*k, 24.4*k, 22.55*k, 0.8*k, 50, -49*k, -41*k)
    crossed_roller(p, s, k)
    flexspline(p, s, k)
    circular_spline(p, s, k)
    output_flange(p, s, k)
    brake(p, s, k)
    encoders(p, s, k)
    screw(p, f"m4x{OUT_SCREW[s]}", 3.4, 4.0, 2.0, OUT_SCREW[s], 1.15)


# ------------------------------------------------------------ the frames
class Frame:
    def __init__(self, o, z, x):
        self.o, self.z, self.x = o, z, x
        self.y = cross(z, x)

    def local(self, w):
        d = [w[i] - self.o[i] for i in range(3)]
        return (dot(d, self.x), dot(d, self.y), dot(d, self.z))

    def ldir(self, w):
        return (dot(w, self.x), dot(w, self.y), dot(w, self.z))

    def world(self, q):
        return tuple(self.o[i] + q[0]*self.x[i] + q[1]*self.y[i] + q[2]*self.z[i]
                     for i in range(3))

    def wdir(self, q):
        return tuple(q[0]*self.x[i] + q[1]*self.y[i] + q[2]*self.z[i] for i in range(3))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0])


J = {
    1: ("l", Frame((0, 0, 141), (0, 0, 1), X)),
    2: ("l", Frame((0, -70, 206), (0, -1, 0), X)),
    3: ("m", Frame((425, -30, 206), (0, 1, 0), X)),
    4: ("s", Frame((817, -40, 206), (0, -1, 0), X)),
    5: ("s", Frame((817, -90, 260), (0, 0, 1), X)),
    6: ("s", Frame((817, -125, 310), (0, -1, 0), X)),
}


def R(j):
    return 55 * SIZES[J[j][0]]


# ----------------------------------------------------------------- links
def wcyl(p, part, F, fid, r, a, b, x_hint=None, **flags):
    """A cylinder of radius r from world point a to world point b, in frame F."""
    la, lb = F.local(a), F.local(b)
    d = tuple(lb[i] - la[i] for i in range(3))
    L = math.sqrt(dot(d, d))
    z = tuple(c / L for c in d)
    x = x_hint or ((1, 0, 0) if abs(z[0]) < 0.9 else (0, 1, 0))
    x = F.ldir(x) if x_hint else x
    xd = dot(x, z)
    x = tuple(x[i] - xd * z[i] for i in range(3))
    n = math.sqrt(dot(x, x))
    x = tuple(c / n for c in x)
    p.add(part, "cylinder", fid, {"radius": f"{r:.6f}", "height": f"{L:.6f}"},
          (la, z, x), **flags)
    return la, z, x


def wbox(p, part, F, fid, size, centre, wz, wx, **flags):
    p.block(part, fid, size, F.local(centre), F.ldir(wz), F.ldir(wx), **flags)


def along(F, t):
    return F.world((0, 0, t))


SEATS = {}   # link -> (cut feature, local origin, z, x) of the seat it holds the next housing in


def seat(p, part, F, nxt, fid, length_from, length_to):
    """Cut the next housing's cylinder out of a link, from local z of the next
    joint length_from to length_to: the seat the next housing sits in."""
    Fn = J[nxt][1]
    a, b = along(Fn, length_from), along(Fn, length_to)
    la, z, x = wcyl(p, part, F, fid, R(nxt), a, b, x_hint=Fn.x, operation="cut")
    SEATS[part] = (fid, la, z, x, nxt)


def links(p):
    # L1, the shoulder cradle on J1's output (frame J1)
    F1, F2 = J[1][1], J[2][1]
    c = p.part("shoulder-cradle")
    rev(p, c, "plate", ring_prof(0, 55, 0, 10))
    cyl(p, c, "cable", 10, 0, 10, operation="cut", target="plate")
    wbox(p, c, F1, "pedestal", (90, 60, 58), (0, 10, 180), Z, X, operation="join",
         target="plate")
    wcyl(p, c, F1, "cuff", 61, (0, -20, 206), (0, 40, 206), x_hint=X, operation="join",
         target="plate")
    seat(p, c, F1, 2, "seat", -135, -45)

    # L2, the upper arm (frame J2): a boss on J2's output, a tube, a cuff round J3
    F3 = J[3][1]
    c = p.part("upper-arm")
    wcyl(p, c, F2, "boss", 52, (0, -70, 206), (0, -140, 206), x_hint=X)
    wcyl(p, c, F2, "tube", 34, (0, -105, 206), (425, -105, 206), x_hint=Y,
         operation="join", target="boss")
    wcyl(p, c, F2, "cuff", R(3) + 5.5, (425, -140, 206), (425, -70, 206), x_hint=X,
         operation="join", target="boss")
    wcyl(p, c, F2, "bore", 31.5, (60, -105, 206), (370, -105, 206), x_hint=Y,
         operation="cut", target="boss")
    seat(p, c, F2, 3, "seat", -120, -30)

    # L3, the forearm (frame J3)
    F4 = J[4][1]
    c = p.part("forearm")
    wcyl(p, c, F3, "boss", R(3), (425, -30, 206), (425, 30, 206), x_hint=X)
    wcyl(p, c, F3, "tube", 29, (425, 0, 206), (817, 0, 206), x_hint=Y, operation="join",
         target="boss")
    wcyl(p, c, F3, "cuff", R(4) + 4.4, (817, -30, 206), (817, 30, 206), x_hint=X,
         operation="join", target="boss")
    wcyl(p, c, F3, "bore", 26.5, (480, 0, 206), (770, 0, 206), x_hint=Y, operation="cut",
         target="boss")
    seat(p, c, F3, 4, "seat", -100, 5)

    # L4, wrist 1 to wrist 2 (frame J4)
    F5 = J[5][1]
    c = p.part("wrist-1-bracket")
    wcyl(p, c, F4, "plate", R(4), (817, -40, 206), (817, -46, 206), x_hint=X)
    wbox(p, c, F4, "bridge", (60, 16, 50), (817, -52, 206), Z, X, operation="join",
         target="plate")
    wcyl(p, c, F4, "cuff", R(5) + 4.4, (817, -90, 181), (817, -90, 231), x_hint=X,
         operation="join", target="plate")
    seat(p, c, F4, 5, "seat", -85, -20)

    # L5, wrist 2 to wrist 3 (frame J5)
    F6 = J[6][1]
    c = p.part("wrist-2-bracket")
    wcyl(p, c, F5, "plate", R(5), (817, -90, 260), (817, -90, 266), x_hint=X)
    wbox(p, c, F5, "bridge", (60, 50, 14), (817, -90, 271), Z, X, operation="join",
         target="plate")
    wcyl(p, c, F5, "cuff", R(6) + 4.4, (817, -115, 310), (817, -65, 310), x_hint=X,
         operation="join", target="plate")
    seat(p, c, F5, 6, "seat", -85, -5)

    # the tool flange, ISO 9409-1-50-4-M6 (frame J6)
    c = p.part("tool-flange")
    rev(p, c, "flange", ring_prof(0, 31.5, 0, 6))
    cyl(p, c, "centre", 15.5, 0, 6, operation="cut")
    cyl(p, c, "m6", 3.3, 0, 6, at=polar(25, 0), operation="cut")
    circ(p, c, "m6-holes", ["m6"], 4)
    cyl(p, c, "pin", 3.0, 0, 6, at=polar(25, 45), operation="cut")

    # the base: a mounting flange J1's housing stands on
    c = p.part("base")
    rev(p, c, "plate", ring_prof(10, 75, 0, 10))
    cyl(p, c, "pocket", 3.6, 6.5, 10, at=polar(52.5, 30), operation="cut")
    circ(p, c, "pockets", ["pocket"], 6)
    cyl(p, c, "mount", 4.5, 0, 10, at=polar(66, 45), operation="cut")
    circ(p, c, "mounts", ["mount"], 4)

    for part in ("shoulder-cradle", "upper-arm", "forearm", "wrist-1-bracket",
                 "wrist-2-bracket"):
        colour(p, part, "#d7dade")
    colour(p, "tool-flange", "#b9bdc2")
    colour(p, "base", "#c9ccd1")


# ------------------------------------------------------------- assembly
INTERNALS = [  # instance, part, fastened or turning on what
    ("housing", "housing", None),
    ("end-cap", "end-cap", ("fastened", "housing")),
    ("stator", "stator", ("fastened", "housing")),
    ("windings", "windings", ("fastened", "housing")),
    ("brg-a-out", "brg-a-{s}-out", ("fastened", "housing")),
    ("brg-b-out", "brg-b-{s}-out", ("fastened", "housing")),
    ("crb-out", "crb-out", ("fastened", "housing")),
    ("circular-spline", "circular-spline", ("fastened", "housing")),
    ("pcb", "pcb", ("fastened", "housing")),
    ("readhead", "readhead", ("fastened", "pcb")),
    ("brake-solenoid", "brake-solenoid", ("fastened", "pcb")),
    ("brake-pin", "brake-pin", ("slider", "brake-solenoid")),
    ("out-enc-head", "out-enc-head", ("fastened", "housing")),
    ("rotor", "rotor", ("revolute", "housing")),
    ("magnets", "magnets", ("fastened", "rotor")),
    ("wave-gen", "wave-gen", ("fastened", "rotor")),
    ("brake-disk", "brake-disk", ("fastened", "rotor")),
    ("enc-disc", "enc-disc", ("fastened", "rotor")),
    ("brg-a-in", "brg-a-{s}-in", ("fastened", "rotor")),
    ("brg-b-in", "brg-b-{s}-in", ("fastened", "rotor")),
    ("wg-brg-in", "wg-brg-{s}-in", ("fastened", "rotor")),
    ("brg-a-balls", "brg-a-{s}-balls", ("revolute", "housing")),
    ("brg-b-balls", "brg-b-{s}-balls", ("revolute", "housing")),
    ("wg-brg-balls", "wg-brg-{s}-balls", ("revolute", "rotor")),
    ("output", "output", ("revolute", "housing")),
    ("crb-in", "crb-in", ("fastened", "output")),
    ("crb-rollers", "crb-rollers", ("revolute", "housing")),
    ("flexspline", "flexspline", ("fastened", "output")),
    ("wg-brg-out", "wg-brg-{s}-out", ("fastened", "output")),
    ("out-enc-ring", "out-enc-ring", ("fastened", "output")),
]


def pose_flags(F, local=(0, 0, 0), lz=(0, 0, 1), lx=(1, 0, 0)):
    o = F.world(local)
    return dict(origin=",".join(f"{c:.6f}mm" for c in o),
                z=",".join(f"{c:.6f}" for c in F.wdir(lz)),
                x=",".join(f"{c:.6f}" for c in F.wdir(lx)))


def joint_instances(p, a, j):
    s, F = J[j]
    k = SIZES[s]
    pre = f"j{j}"
    for inst, part, how in INTERNALS:
        part = part.format(s=s) if "{s}" in part else f"{part}-{s}"
        p.add(a, "instance", f"{pre}-{inst}", of=part, **pose_flags(F))
    for inst, part, how in INTERNALS:
        if how is None:
            continue
        form, to = how
        flags = dict(form=form, a=f"arm/{pre}-{to}", b=f"arm/{pre}-{inst}",
                     a_offset="{}", b_offset="{}")
        if inst == "output":
            flags["angle"] = f"j{j}"
        if form == "slider":
            flags["distance"] = "brake"   # the pin's travel: 0 mm engaged, as modelled
        p.add(a, "mate", f"{pre}-{inst}-{form}", **flags)
    # screws: the output flange's, the end cap's and the circular spline's
    for name, part, on, r, ang, z0, flip, n in (
            ("out-screw", f"m4x{OUT_SCREW[s]}", "output", 32 * k, 0, -4.6, False, 8),
            ("cap-screw", "m3x10", "end-cap", 52.5 * k, 30, -131 * k, True, 6),
            ("cs-screw", "m3x10", "circular-spline", 40 * k, 15, -60 * k, True, 12)):
        x, y = polar(r, ang)
        lz = (0, 0, -1) if flip else (0, 0, 1)
        iid = f"{pre}-{name}"
        p.add(a, "instance", iid, of=part, **pose_flags(F, (x, y, z0), lz, (1, 0, 0)))
        off = {"origin": [f"{x:.6f} mm", f"{y:.6f} mm", f"{z0:.6f} mm"]}
        if flip:
            off["flip"] = True
        p.add(a, "mate", f"{iid}-fastened", form="fastened", a=f"arm/{pre}-{on}",
              a_offset=json_(off), b=f"arm/{iid}", b_offset="{}")
        p.add(a, "instance_pattern", f"{iid}s", instance=iid, form="circular", axis=f"arm/{pre}-housing",
              count=str(n), angle="360deg")


def json_(v):
    import json
    return json.dumps(v)


def mat_offset(Fa_o, Fa_z, Fa_x, Fb):
    """The offset (in a's own axes: origin, then a turn about z, then a flip
    about x) taking frame a (world) onto frame Fb (world)."""
    Fa = Frame(Fa_o, Fa_z, Fa_x)
    o = Fa.local(Fb.o)
    bz, bx = Fa.ldir(Fb.z), Fa.ldir(Fb.x)
    flip = bz[2] < 0
    if flip:  # undo the flip about x: x stays, y and z reverse
        bx = (bx[0], bx[1], bx[2])
    theta = math.degrees(math.atan2(bx[1], bx[0]))
    off = {"origin": [f"{c:.6f} mm" for c in o], "rotate": f"{theta:.6f} deg"}
    if flip:
        off["flip"] = True
    return off


def arm(p):
    a = p.part("arm", assembly=True)
    p.run("param", "set", "arm", *[f"j{j}=0 deg" for j in range(1, 7)], "brake=0 mm")
    p.add(a, "instance", "base", of="base", fixed=True)
    for j in range(1, 7):
        joint_instances(p, a, j)
    # the base under J1, each link on its joint's output, each housing in its seat
    F1 = J[1][1]
    p.add(a, "mate", "j1-on-base", form="fastened", a="arm/base",
          a_offset=json_({"origin": ["0 mm", "0 mm", "141 mm"]}), b="arm/j1-housing",
          b_offset="{}")
    chain = [(1, "shoulder-cradle"), (2, "upper-arm"), (3, "forearm"), (4, "wrist-1-bracket"),
             (5, "wrist-2-bracket"), (6, "tool-flange")]
    for j, link in chain:
        F = J[j][1]
        p.add(a, "instance", link, of=link, **pose_flags(F))
        p.add(a, "mate", f"{link}-on-j{j}", form="fastened", a=f"arm/j{j}-output",
              a_offset="{}", b=f"arm/{link}", b_offset="{}")
    return chain


def seat_mates(p, chain, face_of):
    """Each next housing fastened in its link's seat: connector a on the seat's
    cylindrical face, its frame moved onto the next joint's frame."""
    for j, link in chain:
        if link not in SEATS:
            continue
        fid, la, z, x, nxt = SEATS[link]
        F = J[j][1]
        Fn = J[nxt][1]
        face, frame = face_of(link, fid)
        # frame: (origin, z, x) in the link's coordinates (mm), as the connector has it
        o_w = F.world(frame[0])
        off = mat_offset(o_w, F.wdir(frame[1]), F.wdir(frame[2]), Fn)
        p.add("arm", "mate", f"j{nxt}-in-{link}", form="fastened", a=f"arm/{link}/{face}",
              a_offset=json_(off), b=f"arm/j{nxt}-housing", b_offset="{}")


def build(p):
    p.run("init", "--unit", "mm")
    for s, k in SIZES.items():
        joint_parts(p, s, k)
    screw(p, "m3x10", 2.75, 3.0, 1.5, 10, 1.25)
    links(p)
    chain = arm(p)

    def face_of(link, fid):
        # the seat's cylindrical face, and its connector frame by design 72's table:
        # origin the part origin projected onto the axis, z the surface's axis, x its x
        _, _, sz, _, nxt = SEATS[link]
        for b in p.bodies(link):
            for f in b["faces"]:
                s = f["surface"]
                if s["type"] == "cylinder" and abs(s["radius"] * 1000 - R(nxt)) < 1e-6 \
                        and abs(dot(s["frame"]["z"], sz)) > 0.999:
                    fr = s["frame"]
                    ax = fr["z"]
                    o = [c * 1000 for c in fr["origin"]]
                    t = -dot(o, ax)
                    foot = tuple(o[i] + t * ax[i] for i in range(3))
                    return f"{b['solid']}/{f['name']}", (foot, tuple(ax), tuple(fr["x"]))
        raise RuntimeError(f"no seat face on {link}")
    seat_mates(p, chain, face_of)


main(build)
