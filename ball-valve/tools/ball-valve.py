"""A 1" (DN25) two-piece full-port ball valve with female NPT-style ends,
as a ryucad assembly, through the CLI only.

Frame: flow along x, stem along z, ball centre at the origin. Every part
is built in this frame and placed at the identity (the left seat and the
second packing ring are turned or lifted copies), so mates hold as written.

Parts: the body (hex end, barrel, stem neck with its stop lug), the end
piece screwed into the body, a body seal, a stainless ball with a 25 mm
full bore and a stem slot, two PTFE seats, a blow-out-proof stem (tang,
shoulder inside the body, double-D flats), a PTFE thrust washer, two
packing rings, a gland follower, the packing nut, the lever handle with
two stop tabs, its vinyl grip, the handle nut and the stop pin.

Female ends are drawn as their minor-diameter bore with six stacked grooves
(11.5 TPI pitch) and a thread relief, not as helical threads.

The stem turns on one revolute about z driven by the parameter `valve`:
0 deg open (bore along x), 90 deg closed (bore across the flow). Ball,
handle and handle nut are fastened to the stem.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import main  # noqa: E402

Z = (0, 0, 1)
X = (1, 0, 0)
Y = (0, 1, 0)
ASM = "ball-valve"

# ---- key dimensions (mm)
BORE = 12.5          # flow bore radius: 25 mm full port
BALL = 21.0          # ball radius
CAV = 22.2           # cavity radius round the ball
POCKET = 20.2        # seat pocket radius
SEAT_IN, SEAT_OUT = 13.5, 20.0
THREAD_MINOR = 15.2  # 1" NPT female, drawn at minor radius
THREAD_GROOVE = 16.3
PITCH = 25.4 / 11.5
HEX_AF = 46.0
STEM_R = 5.0
PIN_R, PIN_AT, PIN_ANG = 2.0, 18.5, 135.0
TAB_OFF = 11.5       # stop tabs' angular offset from the pin, deg


# ------------------------------------------------------------- helpers
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


def rev_x(p, part, fid, prof, **flags):
    """Revolve a closed (x, r) profile about the x axis (sketch u = x, v = z)."""
    xs = [a for a, _ in prof]
    ops = pts_lines(prof)
    ops += [{"op": "add", "type": "point", "id": "ax1", "at": [f"{min(xs)-1:.6f} mm", "0 mm"]},
            {"op": "add", "type": "point", "id": "ax2", "at": [f"{max(xs)+1:.6f} mm", "0 mm"]},
            {"op": "add", "type": "line", "id": "axis", "start": "ax1", "end": "ax2"}]
    sk = p.sketch(part, ops, fid=f"{fid}-profile", place=((0, 0, 0), (0, -1, 0), X))
    return p.add(part, "revolve", fid, sketch=sk, axis="axis", angle="full", **flags)


def zcyl(p, part, fid, r, z0, z1, at=(0, 0), **flags):
    return p.add(part, "cylinder", fid, {"radius": f"{r:.6f}", "height": f"{z1-z0:.6f}"},
                 ((at[0], at[1], z0), Z, X), **flags)


def xcyl(p, part, fid, r, x0, x1, **flags):
    return p.add(part, "cylinder", fid, {"radius": f"{r:.6f}", "height": f"{x1-x0:.6f}"},
                 ((x0, 0, 0), X, Y), **flags)


def hexagon(af):
    rc = af / math.sqrt(3)
    return [(rc * math.cos(math.radians(60 * i)), rc * math.sin(math.radians(60 * i)))
            for i in range(6)]


def hex_x(p, part, fid, af, x0, x1, **flags):
    """A hex prism along x (flats top and bottom)."""
    sk = p.sketch(part, pts_lines(hexagon(af)), fid=f"{fid}-profile",
                  place=((x0, 0, 0), X, Y))
    return p.add(part, "extrude", fid, sketch=sk, length=f"{x1-x0:.6f} mm", **flags)


def hex_z(p, part, fid, af, z0, z1, **flags):
    sk = p.sketch(part, pts_lines(hexagon(af)), fid=f"{fid}-profile",
                  place=((0, 0, z0), Z, X))
    return p.add(part, "extrude", fid, sketch=sk, length=f"{z1-z0:.6f} mm", **flags)


def colour(p, part, c):
    p.run("colour", part, "--colour", c)


def thread_run(x_face, inward):
    """(x, r) points of a female end, from the face inwards: chamfer, minor bore with
    six stacked grooves, thread relief, ending at the flow bore. `inward` = +1 for the
    left end (face at -46), -1 for the right end (face at +46)."""
    s = inward
    pts = [(x_face - s * 1.0, THREAD_MINOR + 1.4), (x_face + s * 1.5, THREAD_MINOR)]
    start = x_face + s * 2.0
    for k in range(6):
        a = start + s * k * PITCH
        b = a + s * 1.1
        pts += [(a, THREAD_MINOR), (a, THREAD_GROOVE), (b, THREAD_GROOVE), (b, THREAD_MINOR)]
    pts += [(x_face + s * 15.0, THREAD_MINOR), (x_face + s * 15.0, 16.8),
            (x_face + s * 17.0, 16.8), (x_face + s * 17.0, BORE)]
    return pts


# --------------------------------------------------------------- parts
def body(p):
    b = p.part("body")
    rev_x(p, b, "barrel", [(-28, 0), (-28, 31), (18, 31), (18, 0)])
    hex_x(p, b, "hex-end", HEX_AF, -46, -27, operation="join", target="barrel")
    zcyl(p, b, "neck", 13, 15, 38, operation="join", target="barrel")
    zcyl(p, b, "neck-thread", 11, 37.5, 44, operation="join", target="barrel")
    a = math.radians(PIN_ANG)
    d = (math.cos(a), math.sin(a), 0)
    p.block(b, "stop-lug", (14, 10, 13.5), (19 * d[0], 19 * d[1], 30.75), Z, d,
            operation="join", target="barrel")
    # flow passage: left female end, bore, seat pocket, cavity, end-piece thread bore
    inner = [(-47, 0)] + thread_run(-46, +1) + [
        (-19.1, BORE), (-19.1, POCKET), (-13.0, POCKET), (-13.0, CAV),
        (9.0, CAV), (9.0, 26.5), (18.5, 26.5), (18.5, 0)]
    rev_x(p, b, "passage", inner, operation="cut", target="barrel")
    # stem bore: shoulder pocket (blow-out-proof), stem bore, packing counterbore
    zcyl(p, b, "shoulder-pocket", 8.2, 15, 25.3, operation="cut", target="barrel")
    zcyl(p, b, "stem-bore", 5.1, 25.0, 44.5, operation="cut", target="barrel")
    zcyl(p, b, "packing-bore", 8.1, 34.0, 44.5, operation="cut", target="barrel")
    px, py = PIN_AT * d[0], PIN_AT * d[1]
    zcyl(p, b, "pin-hole", PIN_R + 0.05, 31.0, 38.0, at=(px, py), operation="cut",
         target="barrel")
    colour(p, b, "#b4b9bf")


def end_piece(p):
    e = p.part("end-piece")
    rev_x(p, e, "spigot", [(10.1, 0), (10.1, 26.35), (18.7, 26.35), (18.7, 0)])
    hex_x(p, e, "hex", HEX_AF, 18.2, 46, operation="join", target="spigot")
    inner = [(9.5, 0), (9.5, CAV), (12.9, CAV), (12.9, POCKET), (19.1, POCKET),
             (19.1, BORE)] + list(reversed(thread_run(46, -1))) + [(47, 0)]
    rev_x(p, e, "passage", inner, operation="cut", target="spigot")
    colour(p, e, "#a9aeb5")


def body_seal(p):
    s = p.part("body-seal")
    rev_x(p, s, "ring", [(9.1, 22.4), (10.0, 22.4), (10.0, 26.3), (9.1, 26.3)])
    colour(p, s, "#efece4")


def seat(p):
    s = p.part("seat")
    rev_x(p, s, "ring", [(16.3, SEAT_IN), (13.0, 17.5), (13.0, SEAT_OUT), (19.0, SEAT_OUT),
                         (19.0, SEAT_IN)])
    colour(p, s, "#f4f2ec")


def ball(p):
    b = p.part("ball")
    p.add(b, "sphere", "sphere", {"radius": f"{BALL:.6f}"}, ((0, 0, 0), Z, X))
    xcyl(p, b, "bore", BORE, -23, 23, operation="cut", target="sphere")
    p.block(b, "stem-slot", (24, 4.4, 6), (0, 0, 20.5), Z, X, operation="cut",
            target="sphere")
    colour(p, b, "#e4e7ea")


def stem(p):
    s = p.part("stem")
    zcyl(p, s, "shoulder", 8.0, 21.3, 24.3)
    p.block(s, "tang", (14, 4, 3.9), (0, 0, 19.75), Z, X, operation="join", target="shoulder")
    zcyl(p, s, "shaft", STEM_R, 24.0, 60.0, operation="join", target="shoulder")
    for side in (1, -1):
        p.block(s, f"flat-{'a' if side > 0 else 'b'}", (14, 3, 12),
                (0, side * 5.0, 55.0), Z, X, operation="cut", target="shoulder")
    colour(p, s, "#c7cbd0")


def thrust_washer(p):
    w = p.part("thrust-washer")
    zcyl(p, w, "ring", 7.9, 24.4, 25.2)
    zcyl(p, w, "hole", 5.2, 24.4, 25.2, operation="cut", target="ring")
    colour(p, w, "#efece4")


def packing(p):
    k = p.part("packing-ring")
    zcyl(p, k, "ring", 8.0, 34.1, 37.0)
    zcyl(p, k, "hole", 5.1, 34.1, 37.0, operation="cut", target="ring")
    colour(p, k, "#e9e5da")


def gland(p):
    g = p.part("gland")
    zcyl(p, g, "sleeve", 8.0, 40.1, 44.7)
    zcyl(p, g, "collar", 10.5, 44.5, 46.2, operation="join", target="sleeve")
    zcyl(p, g, "hole", 5.2, 40.1, 46.2, operation="cut", target="sleeve")
    colour(p, g, "#9ea4ab")


def packing_nut(p):
    n = p.part("packing-nut")
    hex_z(p, n, "hex", 26, 38.5, 49.0)
    zcyl(p, n, "thread", 11.1, 38.5, 46.4, operation="cut", target="hex")
    zcyl(p, n, "stem-hole", 5.4, 46.4, 49.0, operation="cut", target="hex")
    colour(p, n, "#8f959c")


def handle(p):
    h = p.part("handle")
    zcyl(p, h, "hub", 20, 50.5, 53.5)
    p.block(h, "lever", (125, 18, 3), (62.5, 0, 52.0), Z, X, operation="join", target="hub")
    zcyl(p, h, "stem-hole", 5.15, 50.5, 53.5, operation="cut", target="hub")
    for side in (1, -1):   # the double-D: segments outside the stem's flats put back
        p.block(h, f"d-{'a' if side > 0 else 'b'}", (11, 2.5, 3), (0, side * 4.9, 52.0),
                Z, X, operation="join", target="hub")
    # stop tabs hanging from the hub: one meets the pin open, the other closed
    for name, ang in (("stop-open", PIN_ANG + TAB_OFF), ("stop-closed", PIN_ANG - 90 - TAB_OFF)):
        a = math.radians(ang)
        d = (math.cos(a), math.sin(a), 0)
        p.block(h, name, (2.5, 3, 5.3), (PIN_AT * d[0], PIN_AT * d[1], 48.15), Z, d,
                operation="join", target="hub")
    colour(p, h, "#b9bdc3")


def grip(p):
    g = p.part("grip")
    p.block(g, "sleeve", (62.5, 23, 7), (97.25, 0, 52.0), Z, X)
    p.block(g, "slot", (60.4, 18.6, 3.4), (95.2, 0, 52.0), Z, X, operation="cut",
            target="sleeve")
    colour(p, g, "#c8202f")


def handle_nut(p):
    n = p.part("handle-nut")
    hex_z(p, n, "hex", 14, 53.6, 59.6)
    zcyl(p, n, "hole", STEM_R + 0.05, 53.6, 59.6, operation="cut", target="hex")
    colour(p, n, "#7d838a")


def stop_pin(p):
    s = p.part("stop-pin")
    a = math.radians(PIN_ANG)
    zcyl(p, s, "pin", PIN_R, 31.5, 49.0, at=(PIN_AT * math.cos(a), PIN_AT * math.sin(a)))
    colour(p, s, "#d0d3d7")


# ------------------------------------------------------------ assembly
def json_(v):
    import json
    return json.dumps(v)


def build(p):
    p.run("init", "--unit", "mm")
    for f in (body, end_piece, body_seal, seat, ball, stem, thrust_washer, packing, gland,
              packing_nut, handle, grip, handle_nut, stop_pin):
        f(p)

    a = p.part(ASM, assembly=True)
    p.run("param", "set", ASM, "valve=0 deg")
    p.add(a, "instance", "body", of="body", fixed=True)
    ident = dict(origin="0mm,0mm,0mm", z="0,0,1", x="1,0,0")

    def place(inst, part, on, form="fastened", pose=None, off=None, **extra):
        p.add(a, "instance", inst, of=part, **(pose or ident))
        p.add(a, "mate", f"{inst}-{form}", form=form, a=f"{ASM}/{on}",
              a_offset=json_(off or {}), b=f"{ASM}/{inst}", b_offset="{}", **extra)

    place("end-piece", "end-piece", "body")
    place("body-seal", "body-seal", "body")
    place("seat-outlet", "seat", "body")
    place("seat-inlet", "seat", "body", pose=dict(origin="0mm,0mm,0mm", z="0,0,1", x="-1,0,0"),
          off={"rotate": "180 deg"})
    place("stem", "stem", "body", form="revolute", angle="valve")
    place("ball", "ball", "stem")
    place("thrust-washer", "thrust-washer", "body")
    place("packing-1", "packing-ring", "body")
    place("packing-2", "packing-ring", "body", pose=dict(origin="0mm,0mm,3mm", z="0,0,1", x="1,0,0"),
          off={"origin": ["0 mm", "0 mm", "3 mm"]})
    place("gland", "gland", "body")
    place("packing-nut", "packing-nut", "body")
    place("stop-pin", "stop-pin", "body")
    place("handle", "handle", "stem")
    place("grip", "grip", "handle")
    place("handle-nut", "handle-nut", "stem")


main(build)
