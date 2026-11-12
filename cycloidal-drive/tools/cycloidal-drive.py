"""A compact cycloidal reducer for robot joints, 11:1, about 90 mm across,
as a ryucad assembly built through the CLI only.

Axis z, input side at z = 0 (end cover underneath), output flange on top.

  housing (pin cavity, output-bearing bore and shoulder, tapped holes),
  end cover (input-bearing bore, ring-pin sockets, counterbored screws);
  12 ring pins (dia 4) on a 70 mm pin circle, each with a roller (dia 6.5);
  two 11-lobe cycloidal discs, 180 deg out of phase: an epitrochoid,
  offset for the roller radius plus 0.15 mm backlash clearance, as a
  264-segment polyline; a central bore for the eccentric bearing and six
  output-pin holes (roller dia + 2e + 0.6 mm);
  an input shaft with two eccentric cams (e = 1.2 mm, 180 deg apart) and
  a flat on its input stub;
  6802 (15x24x5) eccentric bearings, 6800 (10x19x5) input bearings in the
  cover and in the output carrier, two 6808 (40x52x7) main output bearings
  in the housing; every bearing as inner ring, outer ring (grooves cut by
  revolved polygons) and balls in a cage;
  the output carrier (plate and hub), the input-side carrier ring, six
  output pins (dia 5) with rollers (dia 7), an output flange with an
  M4 bolt circle; M3 socket screws throughout.

Mates: the shaft turns on a revolute (parameter `input`), the carrier on a
revolute (parameter `output`), each disc on a revolute about its cam's
eccentric axis (parameter `disc`). `output` = -input/11 and
`disc` = -input*12/11 are parameter expressions: ryucad has no gear-ratio
mate, so the 11:1 reduction is carried by the geometry and those
expressions, not enforced by the solver. Rollers and ball cages turn on
free revolutes.
"""
import json
import math
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from model import main  # noqa: E402

Z = (0, 0, 1)
X = (1, 0, 0)
ASM = "cycloidal-drive"

# reducer geometry (mm)
N, R_PIN, R_ROLL, ECC, CLEAR = 12, 35.0, 3.25, 1.2, 0.15
LOBES = N - 1
RW, OUT_PIN_R, OUT_ROLL_R, N_OUT = 21.0, 2.5, 3.5, 6
HOLE_R = OUT_ROLL_R + ECC + 0.3
D1, D2 = (14.0, 20.0), (21.0, 27.0)       # disc z ranges


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


def cycloid(n_per_lobe=24):
    """The disc's outline, centred on its own axis, for the eccentric along
    +x at input angle 0: the epitrochoid of N pins of radius R_PIN offset by
    the roller radius plus CLEAR (checked by tools/prof.py)."""
    rr = R_ROLL + CLEAR
    pts = []
    m = LOBES * n_per_lobe
    for i in range(m):
        t = 2 * math.pi * i / m
        psi = math.atan2(math.sin((1 - N) * t), R_PIN / (ECC * N) - math.cos((1 - N) * t))
        x = R_PIN * math.cos(t) - rr * math.cos(t + psi) - ECC * math.cos(N * t)
        y = -R_PIN * math.sin(t) + rr * math.sin(t + psi) + ECC * math.sin(N * t)
        pts.append((x, y))
    return pts


# ----------------------------------------------------------------- parts
def bearing(p, name, r_in, r_out, w, br, n, ball_colour="#d8dade"):
    """A deep-groove ball bearing, z 0..w: rings with polygon grooves."""
    pitch, zc = (r_in + r_out) / 2, w / 2
    gi, go = pitch - 0.55 * br, pitch + 0.55 * br
    groove = [(zc + 1.06 * br * math.cos(math.radians(30 * i + 15)),
               pitch + 1.06 * br * math.sin(math.radians(30 * i + 15))) for i in range(12)]
    i = p.part(f"{name}-inner")
    rev(p, i, "race", ring_prof(r_in, gi, 0, w))
    rev(p, i, "groove", groove, operation="cut")
    o = p.part(f"{name}-outer")
    rev(p, o, "race", ring_prof(go, r_out, 0, w))
    rev(p, o, "groove", groove, operation="cut")
    b = p.part(f"{name}-balls")
    rev(p, b, "cage", ring_prof(pitch - 0.35 * br, pitch + 0.35 * br, zc - 0.3 * br,
                                zc + 0.3 * br))
    p.add(b, "sphere", "ball", {"radius": f"{br:.6f}"}, ((pitch, 0, zc), Z, X),
          operation="join")
    circ(p, b, "balls", ["ball"], n)
    colour(p, i, "#b9bdc3")
    colour(p, o, "#b9bdc3")
    colour(p, b, ball_colour)


def screw(p, name, head_r, head_h, r, length, socket):
    """A socket head cap screw: head z 0..head_h, shank down to -length."""
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


def housing(p):
    h = p.part("housing")
    rev(p, h, "body", [(8, 39), (32, 39), (32, 23), (33, 23), (33, 26.05), (48, 26.05),
                       (48, 45), (8, 45)])
    # ring-pin sockets (output side), cover-screw taps, mounting taps on top
    cyl(p, h, "pin-socket", 2.05, 31, 35, at=polar(R_PIN, 0), operation="cut")
    circ(p, h, "pin-sockets", ["pin-socket"], N)
    cyl(p, h, "cover-tap", 1.55, 7, 16, at=polar(41, 15), operation="cut")
    circ(p, h, "cover-taps", ["cover-tap"], 6)
    cyl(p, h, "mount-tap", 1.7, 40, 49, at=polar(38.5, 45), operation="cut")
    circ(p, h, "mount-taps", ["mount-tap"], 6)
    colour(p, h, "#3d5a80")


def end_cover(p):
    c = p.part("end-cover")
    rev(p, c, "body", ring_prof(9.55, 45, 0, 8))
    cyl(p, c, "pin-socket", 2.05, 3, 9, at=polar(R_PIN, 0), operation="cut")
    circ(p, c, "pin-sockets", ["pin-socket"], N)
    cyl(p, c, "hole", 1.7, -1, 9, at=polar(41, 15), operation="cut")
    cyl(p, c, "cbore", 3.0, -1, 3.5, at=polar(41, 15), operation="cut")
    circ(p, c, "screw-holes", ["hole", "cbore"], 6)
    colour(p, c, "#4f6d94")


def ring_pin(p):
    c = p.part("ring-pin")
    cyl(p, c, "pin", 2.0, 0, 31.8)          # placed at z 3.1 .. 34.9
    colour(p, c, "#c8ccd2")
    r = p.part("ring-roller")
    rev(p, r, "sleeve", ring_prof(2.1, R_ROLL, 0, 14))   # z 13.5 .. 27.5
    colour(p, r, "#e0b44c")


def input_shaft(p):
    s = p.part("input-shaft")
    cyl(p, s, "shaft", 4.95, -16, 33.3)
    cyl(p, s, "cam-1", 7.45, D1[0], D1[1], at=(ECC, 0), operation="join")
    cyl(p, s, "cam-2", 7.45, D2[0], D2[1], at=(-ECC, 0), operation="join")
    p.block(s, "flat", (4, 12, 13), (6.2, 0, -10.5), Z, X, operation="cut")
    colour(p, s, "#9aa0a8")


def disc(p):
    d = p.part("cycloid-disc")
    sk = p.sketch(d, pts_lines(cycloid()), fid="lobe-profile", place=((0, 0, 0), Z, X))
    p.add(d, "extrude", "disc", sketch=sk, length="6 mm")
    cyl(p, d, "bore", 12.05, -1, 7, operation="cut")
    cyl(p, d, "pin-hole", HOLE_R, -1, 7, at=polar(RW, 0), operation="cut")
    circ(p, d, "pin-holes", ["pin-hole"], N_OUT)
    colour(p, d, "#d9822b")


def output_parts(p):
    c = p.part("output-carrier")
    rev(p, c, "body", [(27.5, 9.55), (27.5, 30), (31.5, 30), (31.5, 19.95), (48.4, 19.95),
                       (48.4, 0), (34, 0), (34, 9.55)])
    cyl(p, c, "pin-bore", OUT_PIN_R + 0.05, 27, 30.5, at=polar(RW, 0), operation="cut")
    circ(p, c, "pin-bores", ["pin-bore"], N_OUT)
    cyl(p, c, "flange-tap", 1.55, 40, 49, at=polar(14, 30), operation="cut")
    circ(p, c, "flange-taps", ["flange-tap"], 6)
    colour(p, c, "#aeb4bb")

    r = p.part("carrier-ring")
    rev(p, r, "ring", ring_prof(10, 27, 11.5, 13.5))
    cyl(p, r, "hole", 1.7, 11, 14, at=polar(RW, 0), operation="cut")
    circ(p, r, "holes", ["hole"], N_OUT)
    colour(p, r, "#aeb4bb")

    op = p.part("output-pin")
    cyl(p, op, "pin", OUT_PIN_R, 0, 16.9)      # placed at z 13.55 .. 30.45
    cyl(p, op, "tap", 1.55, -1, 6, operation="cut")
    colour(p, op, "#c8ccd2")
    orl = p.part("output-roller")
    rev(p, orl, "sleeve", ring_prof(2.6, OUT_ROLL_R, 0, 13.4))   # z 13.8 .. 27.2
    colour(p, orl, "#e0b44c")

    f = p.part("output-flange")
    rev(p, f, "body", ring_prof(0, 30, 48.5, 54.5))
    cyl(p, f, "pilot", 8, 53, 55, operation="cut")
    cyl(p, f, "hole", 1.7, 48, 52, at=polar(14, 30), operation="cut")
    cyl(p, f, "cbore", 3.0, 51, 55, at=polar(14, 30), operation="cut")
    circ(p, f, "screw-holes", ["hole", "cbore"], 6)
    cyl(p, f, "m4", 2.05, 50.5, 55, at=polar(24, 0), operation="cut")
    circ(p, f, "m4-holes", ["m4"], 6)
    colour(p, f, "#c3c7cc")


# -------------------------------------------------------------- assembly
def off(origin=(0, 0, 0), rotate=None, flip=False):
    o = {"origin": [f"{c:.6f} mm" for c in origin]}
    if rotate is not None:
        o["rotate"] = f"{rotate:.6f} deg"
    if flip:
        o["flip"] = True
    return json.dumps(o)


def place(p, iid, part, origin=(0, 0, 0), z=Z, x=X):
    p.add(ASM, "instance", iid, of=part,
          origin=",".join(f"{c:.6f}mm" for c in origin),
          z=",".join(f"{c:.6f}" for c in z), x=",".join(f"{c:.6f}" for c in x))


def mate(p, mid, form, a, b, a_off="{}", b_off="{}", **flags):
    p.add(ASM, "mate", mid, form=form, a=f"{ASM}/{a}", b=f"{ASM}/{b}", a_offset=a_off,
          b_offset=b_off, **flags)


def fasten(p, iid, part, on, origin, rotate=0.0, flip=False, world=None):
    """An instance fastened to `on` at a pose in on's frame (placed first at
    `world`, else at that pose taken as the assembly's)."""
    a = math.radians(rotate)
    zz = (0, 0, -1) if flip else Z
    xx = (math.cos(a), math.sin(a), 0)
    place(p, iid, part, world or origin, zz, xx)
    mate(p, f"{iid}-fastened", "fastened", on, iid, off(origin, rotate, flip))


def bearing_set(p, iid, name, outer_on, inner_on, origin, inner_origin=None):
    """Outer ring fastened to outer_on, inner to inner_on, balls free on the outer."""
    fasten(p, f"{iid}-outer", f"{name}-outer", outer_on, origin)
    fasten(p, f"{iid}-inner", f"{name}-inner", inner_on, inner_origin or origin)
    place(p, f"{iid}-balls", f"{name}-balls", origin)
    mate(p, f"{iid}-balls-revolute", "revolute", f"{iid}-outer", f"{iid}-balls")


def assembly(p):
    a = p.part(ASM, assembly=True)
    p.run("param", "set", ASM, "input=75 deg", "output=-input / 11",
          "disc=-input * 12 / 11")
    p.add(a, "instance", "housing", of="housing", fixed=True)
    fasten(p, "end-cover", "end-cover", "housing", (0, 0, 0))

    # input shaft and the discs on its cams
    place(p, "input-shaft", "input-shaft")
    mate(p, "input-revolute", "revolute", "housing", "input-shaft", angle="input")
    place(p, "disc-1", "cycloid-disc", (ECC, 0, D1[0]))
    mate(p, "disc-1-revolute", "revolute", "input-shaft", "disc-1",
         off((ECC, 0, D1[0])), angle="disc")
    place(p, "disc-2", "cycloid-disc", (-ECC, 0, D2[0]), Z, (-1, 0, 0))
    mate(p, "disc-2-revolute", "revolute", "input-shaft", "disc-2",
         off((-ECC, 0, D2[0]), 180), angle="disc")

    # output carrier and what turns with it
    place(p, "output-carrier", "output-carrier")
    mate(p, "output-revolute", "revolute", "housing", "output-carrier", angle="output")
    fasten(p, "carrier-ring", "carrier-ring", "output-carrier", (0, 0, 0))
    fasten(p, "output-flange", "output-flange", "output-carrier", (0, 0, 0))

    # ring pins and rollers
    for k in range(N):
        x, y = polar(R_PIN, 360 * k / N)
        fasten(p, f"ring-pin-{k+1}", "ring-pin", "housing", (x, y, 3.1))
        place(p, f"ring-roller-{k+1}", "ring-roller", (x, y, 13.5))
        mate(p, f"ring-roller-{k+1}-revolute", "revolute", f"ring-pin-{k+1}",
             f"ring-roller-{k+1}", off((0, 0, 10.4)))
    # output pins, rollers, and the carrier ring's screws into the pins
    for k in range(N_OUT):
        ang = 360 * k / N_OUT
        x, y = polar(RW, ang)
        fasten(p, f"output-pin-{k+1}", "output-pin", "output-carrier", (x, y, 13.55), ang)
        place(p, f"output-roller-{k+1}", "output-roller", (x, y, 13.8))
        mate(p, f"output-roller-{k+1}-revolute", "revolute", f"output-pin-{k+1}",
             f"output-roller-{k+1}", off((0, 0, 0.25)))
        fasten(p, f"ring-screw-{k+1}", "m3x8", "output-carrier", (x, y, 11.4), ang,
               flip=True)
    # cover screws (heads under the cover) and output-flange screws
    for k in range(6):
        ang = 15 + 60 * k
        x, y = polar(41, ang)
        fasten(p, f"cover-screw-{k+1}", "m3x10", "housing", (x, y, 3.45), ang, flip=True)
        ang = 30 + 60 * k
        x, y = polar(14, ang)
        fasten(p, f"flange-screw-{k+1}", "m3x10", "output-carrier", (x, y, 51.05), ang)

    # bearings
    bearing_set(p, "input-bearing-a", "6800", "end-cover", "input-shaft", (0, 0, 1.5))
    bearing_set(p, "input-bearing-b", "6800", "output-carrier", "input-shaft", (0, 0, 28.5))
    bearing_set(p, "main-bearing-1", "6808", "housing", "output-carrier", (0, 0, 33.1))
    bearing_set(p, "main-bearing-2", "6808", "housing", "output-carrier", (0, 0, 40.2))
    for i, d in ((1, "disc-1"), (2, "disc-2")):
        iid = f"ecc-bearing-{i}"
        sx = ECC if i == 1 else -ECC
        z0 = (D1 if i == 1 else D2)[0] + 0.5
        fasten(p, f"{iid}-outer", "6802-outer", d, (0, 0, 0.5), world=(sx, 0, z0))
        place(p, f"{iid}-inner", "6802-inner", (sx, 0, z0))
        mate(p, f"{iid}-inner-fastened", "fastened", "input-shaft", f"{iid}-inner",
             off((sx, 0, z0)))
        place(p, f"{iid}-balls", "6802-balls", (sx, 0, z0))
        mate(p, f"{iid}-balls-revolute", "revolute", f"{iid}-outer", f"{iid}-balls")
    # the two discs told apart in renders
    p.run("colour", f"{ASM}/disc-1", "--colour", "#b8452e")


def build(p):
    p.run("init", "--unit", "mm")
    housing(p)
    end_cover(p)
    ring_pin(p)
    input_shaft(p)
    disc(p)
    output_parts(p)
    bearing(p, "6800", 5.0, 9.5, 5.0, 1.25, 10)
    bearing(p, "6802", 7.5, 12.0, 5.0, 1.25, 13)
    bearing(p, "6808", 20.0, 26.0, 7.0, 1.7, 26)
    screw(p, "m3x10", 2.75, 3.0, 1.5, 10, 1.25)
    screw(p, "m3x8", 2.75, 3.0, 1.5, 8, 1.25)
    assembly(p)


main(build)
