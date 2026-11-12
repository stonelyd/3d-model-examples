"""A lead-screw linear actuator stage (200 mm travel) as a ryucad assembly,
built through the CLI only.

    python3 -I tools/linear-stage.py $(which ryucad) <empty folder>

Every part is modelled in the stage frame: z along the lead screw's axis
(the axis itself is the z axis), x up, y to the side. The assembly places
every instance with that frame turned so the screw runs along world X and
the stage's "up" is world Z (instance z = world X, instance x = world Z), so
mates written with plain part-origin connectors keep the frames aligned.

  base plate        10 mm aluminium plate, 120 x 370 mm, tapped for all the
                    hardware, four counterbored M5 mounting holes
  motor             NEMA 17 (42.3 mm square, 40 mm body): front cap with
                    Ø22 pilot and M3 tapped holes, stator stack, rear cap,
                    connector housing; Ø5 shaft
  motor bracket     6 mm L bracket, M3 x 10 into the motor, M4 x 12 into the base
  coupling          Ø20 x 25 aluminium beam-style coupling, 5 mm to 8 mm bores
                    (the helical beam drawn as three ring slots)
  lead screw        T8 (Ø8, lead 8 mm = 4 starts x 2 mm pitch); thread drawn
                    as a revolved trapezoid of 2 mm pitch (rings, not a helix)
  fixed end         bearing block with a back-to-back pair of 608 bearings
                    (8 x 22 x 7, races grooved, 7 balls in a cage), clamped
                    between two shaft collars
  floating end      bearing block with one 608 bearing, free to float axially
  guide             two Ø8 hardened rods in four rod clamps (slit, M3 clamp
                    screw, two M4 counterbored mounting screws each)
  carriage          aluminium block 96 x 56 x 28 with four LM8UU linear
                    ball bushings, a pocket for the nut, M4 tapped top holes
  nut               anti-backlash brass T8 flange nut (flange Ø26, 4 x M2.5),
                    preload spring and follower nut, sunk into the carriage
  limits            two slotted optical end-stops on small PCBs, two vanes on
                    the carriage that sit in the slots at each end of travel
  end stops         four rubber bumpers on the bearing blocks, 2 mm off the
                    carriage at 0 and 200 mm

Motion: the carriage rides on a slider mate driven by the assembly
parameter `travel` (clamped to 0..200 mm). The lead screw (with coupling,
motor shaft, collars and bearing inner rings) turns on a revolute whose
angle is -45 deg per mm of travel: the 8 mm lead of the right-hand screw,
so the screw's turn and the carriage's position stay consistent. Each
bearing's ball cage turns at 0.37 of the screw (the epicyclic cage speed
for a fixed outer ring, 0.5 (1 - d/Dpw)). The nut's thread is not modelled
as engaging the screw: the coupling is through the shared parameter only.
"""
import json
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import main  # noqa: E402

A = "linear-stage"
Z, X, Y = (0, 0, 1), (1, 0, 0), (0, 1, 0)

TRAVEL = 200.0
C0 = 30.0          # carriage front face at travel 0
CL = 56.0          # carriage length
LEAD = 8.0

ALU, ALU_D, BLACK = "#c9ccd1", "#a9b0b8", "#1b1c1f"


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


def cyl(p, part, fid, r, z0, z1, at=(0, 0), **flags):
    """A cylinder along stage z from z0 to z1 at (x, y) = at."""
    return p.add(part, "cylinder", fid, {"radius": f"{r:.6f}", "height": f"{z1-z0:.6f}"},
                 ((at[0], at[1], z0), Z, X), **flags)


def cyl_x(p, part, fid, r, x0, x1, y, z, **flags):
    """A cylinder along stage x (vertical) from x0 up to x1 at (y, z)."""
    return p.add(part, "cylinder", fid, {"radius": f"{r:.6f}", "height": f"{x1-x0:.6f}"},
                 ((x0, y, z), X, Y), **flags)


def cyl_y(p, part, fid, r, y0, y1, x, z, **flags):
    """A cylinder along stage y from y0 to y1 at (x, z)."""
    return p.add(part, "cylinder", fid, {"radius": f"{r:.6f}", "height": f"{y1-y0:.6f}"},
                 ((x, y0, z), Y, Z), **flags)


def box(p, part, fid, x0, x1, y0, y1, z0, z1, **flags):
    return p.block(part, fid, (x1 - x0, y1 - y0, z1 - z0),
                   ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), Z, X, **flags)


def polar(r, deg):
    a = math.radians(deg)
    return (r * math.cos(a), r * math.sin(a))


def circ(p, part, fid, seeds, n, **flags):
    return p.add(part, "pattern", fid, seed=seeds, form="circular", axis="z", count=str(n),
                 angle="360", **flags)


def colour(p, part, c):
    p.run("colour", part, "--colour", c)


# ------------------------------------------------------------ standard parts
def shcs(p, name, d, size, length):
    """ISO 4762 socket head cap screw: head at the origin, shank along d."""
    dims = {"m2-5": (1.25, 2.25, 2.5, 1.0), "m3": (1.5, 2.75, 3.0, 1.25),
            "m4": (2.0, 3.5, 4.0, 1.5)}
    r, hr, hh, sock = dims[size]
    xr = X if abs(d[0]) < 0.9 else Y
    c = p.part(name)
    p.add(c, "cylinder", "shank", {"radius": f"{r}", "height": f"{length + 0.5}"},
          (tuple(-0.5 * k for k in d), d, xr))
    p.add(c, "cylinder", "head", {"radius": f"{hr}", "height": f"{hh}"},
          (tuple(-hh * k for k in d), d, xr), operation="join")
    # the shank starts 0.5 mm inside the head, so they join through a volume
    hexagon = [(sock * math.cos(math.radians(60 * i)), sock * math.sin(math.radians(60 * i)))
               for i in range(6)]
    sk = p.sketch(c, pts_lines(hexagon), fid="socket-profile",
                  place=(tuple(-(hh + 0.5) * k for k in d), d, xr))
    p.add(c, "extrude", "socket", sketch=sk, operation="cut", length=f"{0.5 + 0.6*hh:.6f} mm")
    colour(p, c, BLACK)


def bearing_608(p):
    """608 deep-groove ball bearing, 8 x 22 x 7, centred at the origin."""
    i = p.part("608-inner-ring")
    rev(p, i, "ring", [(-3.5, 4.0), (3.5, 4.0), (3.5, 6.8), (1.75, 6.8), (1.75, 5.75),
                       (-1.75, 5.75), (-1.75, 6.8), (-3.5, 6.8)])
    o = p.part("608-outer-ring")
    rev(p, o, "ring", [(-3.5, 8.7), (-1.75, 8.7), (-1.75, 9.75), (1.75, 9.75), (1.75, 8.7),
                       (3.5, 8.7), (3.5, 11.0), (-3.5, 11.0)])
    b = p.part("608-balls-and-cage")
    rev(p, b, "cage", ring(7.4, 8.1, -0.5, 0.5))
    p.add(b, "sphere", "ball", {"radius": "1.9"}, ((7.75, 0, 0), Z, X), operation="join")
    circ(p, b, "balls", ["ball"], 7)
    colour(p, i, "#b9bdc3")
    colour(p, o, "#b9bdc3")
    colour(p, b, "#e0e2e5")


def lm8uu(p):
    c = p.part("lm8uu-bushing")
    g0, g1 = 8.75 - 1.1, 8.75
    rev(p, c, "body", [(-12, 4.05), (12, 4.05), (12, 7.5), (g1, 7.5), (g1, 7.15),
                       (g0, 7.15), (g0, 7.5), (-g0, 7.5), (-g0, 7.15), (-g1, 7.15),
                       (-g1, 7.5), (-12, 7.5)])
    colour(p, c, "#c0c4ca")


def guide_rod(p):
    c = p.part("guide-rod-8x306")
    rev(p, c, "rod", [(0, 0), (0, 3.5), (0.5, 4.0), (305.5, 4.0), (306, 3.5), (306, 0)])
    colour(p, c, "#dfe2e6")


def rod_clamp(p):
    """SK8-style clamp, rod axis at the origin, 14 mm along z, seated on the base."""
    c = p.part("rod-clamp")
    box(p, c, "body", -28, 9, -14, 14, -7, 7)
    cyl(p, c, "bore", 4.0, -8, 8, operation="cut")
    box(p, c, "slit", 1.0, 10, -0.5, 0.5, -8, 8, operation="cut")
    for s, y in (("a", 10.0), ("b", -10.0)):
        cyl_x(p, c, f"cbore-{s}", 3.6, -4, 10, y, 0, operation="cut")
        cyl_x(p, c, f"hole-{s}", 2.2, -29, -3.5, y, 0, operation="cut")
    cyl_y(p, c, "clamp-clear", 1.7, 0, 15, 6.5, 0, operation="cut")
    cyl_y(p, c, "clamp-tap", 1.55, -9, 0.5, 6.5, 0, operation="cut")
    colour(p, c, "#b7bcc3")


def bumper(p):
    c = p.part("rubber-bumper")
    cyl(p, c, "pad", 3.5, 0, 6)
    cyl(p, c, "stud", 1.5, -5, 0.5, operation="join")
    colour(p, c, "#232427")


def shaft_collar(p):
    c = p.part("shaft-collar-8")
    rev(p, c, "collar", ring(4.0, 6.5, -2, 2))
    cyl_x(p, c, "set-screw", 1.0, 3.5, 7, 0, 0, operation="cut")
    colour(p, c, "#3a3c40")


def optical_endstop(p):
    """Slotted optical switch (TCST2103 size) on its PCB, slot along z, centred at the origin."""
    c = p.part("optical-endstop")
    box(p, c, "body", -26.4, -15.4, -6.05, 6.05, -3.15, 3.15)
    box(p, c, "slot", -22.4, -14.4, -1.55, 1.55, -4, 4, operation="cut")
    colour(p, c, "#151618")
    b = p.part("endstop-pcb")
    box(p, b, "board", -28, -26.4, -8, 8, -10, 10)
    for s, z in (("a", -7.0), ("b", 7.0)):
        cyl_x(p, b, f"hole-{s}", 1.7, -29, -25, 0, z, operation="cut")
    box(p, b, "header", -26.6, -24.0, 6.3, 7.9, -6.0, 2.0, operation="join")
    colour(p, b, "#1d6b3a")


def endstop_flag(p):
    """Vane and its mounting tab, the tab against the carriage's -y side (y = -48)."""
    c = p.part("endstop-flag")
    box(p, c, "tab", -8, 4, -50.75, -48, 0, 10)
    box(p, c, "vane", -21.4, -7.5, -50.75, -49.25, 0, 10, operation="join")
    cyl_y(p, c, "hole", 1.7, -52, -47, -2, 5, operation="cut")
    colour(p, c, "#e07a2e")


# ---------------------------------------------------------------- the stage
def base(p):
    c = p.part("base-plate")
    box(p, c, "plate", -38, -28, -60, 60, -52, 318)
    taps = [("foot", 2.05, 18, -35), ("foot", 2.05, -18, -35),
            ("blk", 2.05, 14, 7), ("blk", 2.05, -14, 7),
            ("blk", 2.05, 14, 303), ("blk", 2.05, -14, 303)]
    for y in (25, 45, -25, -45):
        for z in (7, 301):
            taps.append(("clamp", 2.05, y, z))
    for z in (26, 40, 276, 290):
        taps.append(("pcb", 1.55, -50, z))
    for i, (kind, r, y, z) in enumerate(taps):
        cyl_x(p, c, f"tap-{kind}-{i+1}", r, -39, -27, y, z, operation="cut")
    for i, (y, z) in enumerate(((52, -44), (-52, -44), (52, 310), (-52, 310))):
        cyl_x(p, c, f"mount-cbore-{i+1}", 4.6, -33, -27, y, z, operation="cut")
        cyl_x(p, c, f"mount-hole-{i+1}", 2.75, -39, -32.5, y, z, operation="cut")
    colour(p, c, ALU)


def motor(p):
    oct_pts = [(21.15, -16.15), (21.15, 16.15), (16.15, 21.15), (-16.15, 21.15),
               (-21.15, 16.15), (-21.15, -16.15), (-16.15, -21.15), (16.15, -21.15)]
    small = [(a * 41.6 / 42.3, b * 41.6 / 42.3) for a, b in oct_pts]

    def slab(part, fid, pts, z0, z1, **flags):
        sk = p.sketch(part, pts_lines(pts), fid=f"{fid}-profile", place=((0, 0, z0), Z, X))
        return p.add(part, "extrude", fid, sketch=sk, length=f"{z1-z0:.6f} mm", **flags)

    f = p.part("nema17-front-cap")
    slab(f, "cap", oct_pts, -56, -48)
    cyl(p, f, "pilot", 11.0, -48.5, -46, operation="join")
    cyl(p, f, "shaft-clear", 2.6, -57, -45, operation="cut")
    for i, (x, y) in enumerate(((15.5, 15.5), (-15.5, 15.5), (-15.5, -15.5), (15.5, -15.5))):
        cyl(p, f, f"tap-{i+1}", 1.55, -53, -47, at=(x, y), operation="cut")
    colour(p, f, "#bfc3c8")

    s = p.part("nema17-stator")
    slab(s, "stack", small, -80, -56)
    colour(p, s, "#26282b")

    r = p.part("nema17-rear-cap")
    slab(r, "cap", oct_pts, -88, -80)
    colour(p, r, "#bfc3c8")

    k = p.part("nema17-connector")
    box(p, k, "housing", 21.15, 26.5, -8, 8, -87, -81)
    box(p, k, "socket", 23, 27, -6.5, 6.5, -86, -82, operation="cut")
    colour(p, k, "#ece9df")

    sh = p.part("motor-shaft")
    rev(p, sh, "shaft", [(-55, 0), (-55, 2.5), (-25.5, 2.5), (-25, 2.0), (-25, 0)])
    box(p, sh, "flat", 2.0, 3, -3, 3, -38, -27, operation="cut")
    colour(p, sh, "#a8adb3")


def motor_bracket(p):
    c = p.part("motor-bracket")
    box(p, c, "plate", -28, 24, -26, 26, -48, -42)
    box(p, c, "foot", -28, -22, -26, 26, -43, -28, operation="join")
    cyl(p, c, "pilot-bore", 11.25, -49, -41, operation="cut")
    for i, (x, y) in enumerate(((15.5, 15.5), (-15.5, 15.5), (-15.5, -15.5), (15.5, -15.5))):
        cyl(p, c, f"hole-{i+1}", 1.7, -49, -41, at=(x, y), operation="cut")
    for i, y in enumerate((18, -18)):
        cyl_x(p, c, f"foot-hole-{i+1}", 2.2, -29, -21, y, -35, operation="cut")
    colour(p, c, ALU_D)


def coupling(p):
    """Beam-style shaft coupling, 5 mm to 8 mm, Ø20 x 25: two hubs with an M3
    set screw each, the helical beam drawn as three ring slots."""
    c = p.part("beam-coupling-5x8")
    prof = [(-38, 2.55), (-25, 2.55), (-25, 4.05), (-13, 4.05), (-13, 10.0),
            (-21.0, 10.0), (-21.0, 5.4), (-22.0, 5.4), (-22.0, 10.0),
            (-23.5, 10.0), (-23.5, 5.4), (-24.5, 5.4), (-24.5, 10.0),
            (-26.0, 10.0), (-26.0, 5.4), (-27.0, 5.4), (-27.0, 10.0),
            (-38, 10.0)]
    rev(p, c, "body", prof)
    cyl_x(p, c, "set-screw-a", 1.4, 2.0, 11, 0, -33, operation="cut")
    cyl_x(p, c, "set-screw-b", 1.4, 3.5, 11, 0, -17, operation="cut")
    colour(p, c, "#9fb4c8")


def lead_screw(p):
    c = p.part("lead-screw-t8")
    prof = [(-23, 0), (-23, 3.5), (-22.5, 4.0), (12, 4.0)]
    z = 12.0
    while z + 2.0 <= 290.0 + 1e-9:
        prof += [(z, 3.95), (z + 0.6, 3.95), (z + 1.0, 3.1), (z + 1.6, 3.1)]
        z += 2.0
    prof += [(z, 3.95), (z, 4.0), (313.5, 4.0), (314, 3.5), (314, 0)]
    # the first point after (12, 4.0) is (12, 3.95): drop the duplicate z step
    clean = [prof[0]]
    for q in prof[1:]:
        if q != clean[-1]:
            clean.append(q)
    rev(p, c, "screw", clean)
    colour(p, c, "#a8adb3")
    return z


def bearing_blocks(p):
    a = p.part("fixed-bearing-block")
    box(p, a, "block", -28, 22, -20, 20, -8, 22)
    cyl(p, a, "pocket", 11.0, -9, 6, operation="cut")
    cyl(p, a, "bore", 7.0, 5, 23, operation="cut")
    for s, y in (("a", 14), ("b", -14)):
        cyl_x(p, a, f"cbore-{s}", 4.0, 16, 23, y, 7, operation="cut")
        cyl_x(p, a, f"hole-{s}", 2.2, -29, 16.5, y, 7, operation="cut")
        cyl(p, a, f"stud-{s}", 1.55, 16, 22.5, at=(10, y), operation="cut")
    colour(p, a, "#b0b5bc")

    b = p.part("floating-bearing-block")
    box(p, b, "block", -28, 22, -20, 20, 294, 312)
    cyl(p, b, "pocket", 11.0, 305, 313, operation="cut")
    cyl(p, b, "bore", 7.0, 293, 305.5, operation="cut")
    for s, y in (("a", 14), ("b", -14)):
        cyl_x(p, b, f"cbore-{s}", 4.0, 16, 23, y, 303, operation="cut")
        cyl_x(p, b, f"hole-{s}", 2.2, -29, 16.5, y, 303, operation="cut")
        cyl(p, b, f"stud-{s}", 1.55, 293.5, 300, at=(10, y), operation="cut")
    colour(p, b, "#b0b5bc")


def carriage(p):
    """Carriage in its own frame: front face (towards the motor) at z = 0."""
    c = p.part("carriage")
    box(p, c, "block", -12, 16, -48, 48, 0, CL)
    for s, y in (("a", 35), ("b", -35)):
        cyl(p, c, f"bushing-bore-{s}", 7.5, -1, CL + 1, at=(0, y), operation="cut")
    cyl(p, c, "nut-pocket", 7.6, -1, 31, operation="cut")
    cyl(p, c, "screw-bore", 5.0, 30, CL + 1, operation="cut")
    cyl(p, c, "nut-tap", 1.3, -1, 6, at=polar(10, 45), operation="cut")
    circ(p, c, "nut-taps", ["nut-tap"], 4)
    for i, (y, z) in enumerate(((20, 10), (-20, 10), (20, 46), (-20, 46))):
        cyl_x(p, c, f"top-tap-{i+1}", 1.65, 8, 17, y, z, operation="cut")
    for s, z in (("a", 5), ("b", CL - 5)):
        cyl_y(p, c, f"flag-tap-{s}", 1.55, -49, -44.5, -2, z, operation="cut")
    colour(p, c, "#3d6fb6")


def nut(p):
    """Anti-backlash T8 flange nut in the carriage's frame (flange on the front face)."""
    n = p.part("t8-flange-nut")
    rev(p, n, "nut", [(-3.5, 4.1), (12, 4.1), (12, 5.1), (0, 5.1), (0, 13.0), (-3.5, 13.0)])
    cyl(p, n, "hole", 1.4, -4.5, 0.5, at=polar(10, 45), operation="cut")
    circ(p, n, "holes", ["hole"], 4)
    colour(p, n, "#c9a227")

    s = p.part("anti-backlash-spring")
    outer = []
    zz = 12.5
    while zz < 19.5 - 1e-9:
        outer += [(zz, 7.2), (zz + 0.7, 7.2), (zz + 0.7, 6.2), (zz + 1.4, 6.2)]
        zz += 1.4
    prof = [(12.5, 5.6), (19.5, 5.6)] + list(reversed(outer))
    rev(p, s, "spring", prof)
    colour(p, s, "#8e959d")

    f = p.part("anti-backlash-follower")
    rev(p, f, "follower", [(20, 4.1), (30, 4.1), (30, 6.0), (28, 6.0), (28, 7.0), (20, 7.0)])
    colour(p, f, "#c9a227")


# --------------------------------------------------------------- assembly
def W(s):
    """Stage coordinates to world: stage z -> X, stage x -> Z, stage y -> -Y."""
    return (s[2], -s[1], s[0])


def build_assembly(p, thread_end):
    a = p.part(A, assembly=True)
    p.run("param", "set", A, "travel=30 mm")
    trav = f"max(0 mm, min(travel, {TRAVEL:g} mm))"

    POSE = {}

    def inst(iid, part, o=(0, 0, 0), flip=False, fixed=False):
        flags = dict(of=part, origin=",".join(f"{c:.6f}mm" for c in W(o)),
                     z=",".join(f"{c:g}" for c in W((0, 0, -1 if flip else 1))),
                     x=",".join(f"{c:g}" for c in W((1, 0, 0))))
        if fixed:
            flags["fixed"] = True
        p.add(a, "instance", iid, **flags)
        POSE[iid] = (tuple(o), flip)

    def off(o=(0, 0, 0), flip=False):
        if o == (0, 0, 0) and not flip:
            return "{}"
        d = {"origin": [f"{c:.6f} mm" for c in o]}
        if flip:
            d["flip"] = True
        return json.dumps(d)

    def fasten(parent, iid, part, o_abs=(0, 0, 0), parent_o=None, flip=False):
        # o_abs and flip are the child's pose in the stage frame; the offset is
        # worked out from the parent's recorded pose (parent_o is only documentation)
        po, pf = POSE[parent]
        inst(iid, part, o_abs, flip)
        rel = [o_abs[i] - po[i] for i in range(3)]
        if pf:   # the parent's axes: x kept, y and z reversed
            rel = [rel[0], -rel[1], -rel[2]]
        p.add(a, "mate", f"{iid}-fastened", form="fastened", a=f"{A}/{parent}",
              a_offset=off(tuple(rel), flip != pf), b=f"{A}/{iid}", b_offset="{}")

    inst("base-plate", "base-plate", fixed=True)
    # ---- fixed frame
    for iid in ("motor-bracket", "fixed-bearing-block", "floating-bearing-block"):
        fasten("base-plate", iid, iid)
    for iid in ("nema17-front-cap", "nema17-stator", "nema17-rear-cap", "nema17-connector"):
        fasten("motor-bracket" if iid == "nema17-front-cap" else "nema17-front-cap", iid, iid)
    for i, (x, y) in enumerate(((15.5, 15.5), (-15.5, 15.5), (-15.5, -15.5), (15.5, -15.5))):
        fasten("motor-bracket", f"motor-screw-{i+1}", "shcs-m3x10", (x, y, -42))
    for i, y in enumerate((18, -18)):
        fasten("motor-bracket", f"bracket-screw-{i+1}", "shcs-m4x12-v", (-22, y, -35))
    for blk, z in (("fixed-bearing-block", 7), ("floating-bearing-block", 303)):
        for i, y in enumerate((14, -14)):
            fasten(blk, f"{blk.split('-')[0]}-block-screw-{i+1}", "shcs-m4x50-v", (16, y, z))
    for blk, z, flip, tag in (("fixed-bearing-block", 22, False, "home"),
                              ("floating-bearing-block", 294, True, "far")):
        for i, y in enumerate((14, -14)):
            fasten(blk, f"bumper-{tag}-{i+1}", "rubber-bumper", (10, y, z), flip=flip)
    # bearing outer rings in their blocks
    BRG = (("fixed-a", -4.5, "fixed-bearing-block"), ("fixed-b", 2.5, "fixed-bearing-block"),
           ("floating", 308.5, "floating-bearing-block"))
    for tag, zc, blk in BRG:
        fasten(blk, f"608-{tag}-outer", "608-outer-ring", (0, 0, zc))
    # guide rods and clamps
    for side, y in (("left", 35.0), ("right", -35.0)):
        flip = y < 0
        for end, zc in (("home", 7.0), ("far", 301.0)):
            cid = f"rod-clamp-{side}-{end}"
            fasten("base-plate", cid, "rod-clamp", (0, y, zc), flip=flip)
            for i, dy in enumerate((10.0, -10.0)):
                fasten(cid, f"{cid}-screw-{i+1}", "shcs-m4x30-v", (-4, y + dy, zc), (0, y, zc))
            hy = y + 14 if not flip else y - 14
            fasten(cid, f"{cid}-clamp-screw", "shcs-m3x20-yn", (6.5, hy, zc), (0, y, zc),
                   flip=flip)
        fasten(f"rod-clamp-{side}-home", f"guide-rod-{side}", "guide-rod-8x306",
               (0, y, 1.0), (0, y, 7.0))
    # limit switches
    for tag, zc in (("home", C0 + 3.0), ("far", C0 + TRAVEL + CL - 3.0)):
        fasten("base-plate", f"endstop-pcb-{tag}", "endstop-pcb", (0, -50, zc))
        fasten(f"endstop-pcb-{tag}", f"endstop-{tag}", "optical-endstop", (0, -50, zc),
               (0, -50, zc))
        for i, dz in enumerate((-7.0, 7.0)):
            fasten(f"endstop-pcb-{tag}", f"endstop-{tag}-screw-{i+1}", "shcs-m3x8-v",
                   (-26.4, -50, zc + dz), (0, -50, zc))

    # ---- the turning group: the lead screw on a revolute, driven with the travel
    inst("lead-screw", "lead-screw-t8")
    p.add(a, "mate", "lead-screw-revolute", form="revolute", a=f"{A}/base-plate",
          a_offset="{}", b=f"{A}/lead-screw", b_offset="{}",
          angle=f"-360 deg / {LEAD:g} mm * {trav}")
    for iid, part, o in (("motor-shaft", "motor-shaft", (0, 0, 0)),
                         ("coupling", "beam-coupling-5x8", (0, 0, 0)),
                         ("collar-outer", "shaft-collar-8", (0, 0, -10)),
                         ("collar-inner", "shaft-collar-8", (0, 0, 8))):
        fasten("lead-screw", iid, part, o)
    for tag, zc, blk in BRG:
        fasten("lead-screw", f"608-{tag}-inner", "608-inner-ring", (0, 0, zc))
        inst(f"608-{tag}-balls", "608-balls-and-cage", (0, 0, zc))
        p.add(a, "mate", f"608-{tag}-balls-revolute", form="revolute", a=f"{A}/base-plate",
              a_offset=off((0, 0, zc)), b=f"{A}/608-{tag}-balls", b_offset="{}",
              angle=f"-0.37 * 360 deg / {LEAD:g} mm * {trav}")

    # ---- the carriage on its slider, everything on it fastened to it
    co = (0, 0, C0)
    inst("carriage", "carriage", co)
    p.add(a, "mate", "carriage-slider", form="slider", a=f"{A}/base-plate",
          a_offset=off(co), b=f"{A}/carriage", b_offset="{}", distance=trav)
    for side, y in (("left", 35.0), ("right", -35.0)):
        for i, zc in enumerate((15.0, 41.0)):
            fasten("carriage", f"lm8uu-{side}-{i+1}", "lm8uu-bushing", (0, y, C0 + zc), co)
    for iid in ("t8-flange-nut", "anti-backlash-spring", "anti-backlash-follower"):
        fasten("carriage", iid, iid, co, co)
    for i in range(4):
        x, y = polar(10, 45 + 90 * i)
        fasten("t8-flange-nut", f"nut-screw-{i+1}", "shcs-m2-5x8", (x, y, C0 - 3.5), co,
               flip=True)
    for tag, dz in (("home", 0.0), ("far", CL - 10.0)):
        fasten("carriage", f"flag-{tag}", "endstop-flag", (0, 0, C0 + dz), co)
        fasten(f"flag-{tag}", f"flag-{tag}-screw", "shcs-m3x6-y", (-2, -50.75, C0 + dz + 5),
               (0, 0, C0 + dz))


def build(p):
    p.run("init", "--unit", "mm")
    base(p)
    motor(p)
    motor_bracket(p)
    coupling(p)
    thread_end = lead_screw(p)
    bearing_blocks(p)
    bearing_608(p)
    shaft_collar(p)
    guide_rod(p)
    rod_clamp(p)
    bumper(p)
    lm8uu(p)
    carriage(p)
    nut(p)
    optical_endstop(p)
    endstop_flag(p)
    D = (0, 0, -1)
    shcs(p, "shcs-m3x10", D, "m3", 10)
    shcs(p, "shcs-m3x8-v", (-1, 0, 0), "m3", 8)
    shcs(p, "shcs-m4x12-v", (-1, 0, 0), "m4", 12)
    shcs(p, "shcs-m4x30-v", (-1, 0, 0), "m4", 30)
    shcs(p, "shcs-m4x50-v", (-1, 0, 0), "m4", 50)
    shcs(p, "shcs-m3x20-yn", (0, -1, 0), "m3", 20)
    shcs(p, "shcs-m3x6-y", (0, 1, 0), "m3", 6)
    shcs(p, "shcs-m2-5x8", D, "m2-5", 8)
    build_assembly(p, thread_end)


main(build)
