"""A 7-cylinder air-cooled radial aircraft engine, built through ryucad's CLI only.

Cylinders lie in the XY plane, crank axis = Z, propeller at the front (+Z).
Each cylinder is one part modelled along its local +Y (base at the case,
barrel y 38..92) and instanced 7 times rotated about Z. The crankcase and
the exhaust collector ring are revolved profiles (zx-plane sketches,
axis = last line for the case; a dedicated axis line for the torus).
No mates: every instance is fixed at a computed frame.
"""

import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.expanduser(
    "~/workspace/ryucad-test/crates/ryucad/tests/corpus"))
from model import main  # noqa: E402

Z = (0, 0, 1)
X = (1, 0, 0)
Y = (0, 1, 0)


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


def revolve_profile(p, part, profile, fid="body"):
    """profile: [(z, r), ...] from (z0, 0) round the outside to (z1, 0);
    the closing line (last point back to the first) is the axis."""
    sk = p.sketch(part, polygon(profile), fid="profile", plane="zx")
    p.add(part, "revolve", fid, sketch=sk,
          axis=f"l{len(profile)}", angle="full")


def crankcase(p):
    g = p.part("crankcase")
    # z from -22 (rear flange) to +18 (front cover), max radius 58.
    # The rear neck (z -20.9..-10) stays under r 44, and the flange
    # step moved back to z -20.9 so the exhaust collector ring (tube
    # centre r 46 at z -16, rear reach -20.2) clears the flange face
    # by 0.7 instead of sinking its rear arc into the flange disc.
    revolve_profile(p, g, [
        (-22, 0), (-22, 58), (-20.9, 58), (-20.9, 39),
        (-14, 37), (-10, 44), (-4, 53), (3, 58), (10, 54),
        (14, 44), (17, 32), (18, 20), (18, 0)])
    # Cylinder sockets: a stepped counterbore for each of the 7
    # cylinders, cut along that cylinder's radial direction (the same
    # frame the assembly instance uses: local +Y -> (-sin a, cos a)).
    # Tier 1 r 15.5, radial 60..44, swallows the base ring (r 13,
    # radial 50..59), the first fin (radial 56..58.2, r 14.5) and the
    # pushrod roots (their axes sit 13.4 off the cylinder axis, r 1.6,
    # reaching 15.0 < 15.5). Tier 2 r 11.9, radial 46..36, seats the
    # barrel (r 11.5, root at radial 38) with 0.4 radial clearance.
    # The cylinders used to be rooted ~7,200 mm^3 apiece in solid case.
    for k in range(7):
        a = math.radians(k * 360.0 / 7.0)
        d = (-math.sin(a), math.cos(a), 0)
        inward = (-d[0], -d[1], 0)
        p.add(g, "cylinder", f"socket-{k + 1}",
              {"radius": 15.5, "height": 16},
              ((60 * d[0], 60 * d[1], 0), inward, Z), operation="cut")
        p.add(g, "cylinder", f"socket-deep-{k + 1}",
              {"radius": 11.9, "height": 10},
              ((46 * d[0], 46 * d[1], 0), inward, Z), operation="cut")
    # Front bore for the crankshaft: r 7.3 over the r 7 shaft (0.3
    # clearance), and a counterweight cavity r 19.5, z 10.4..17.6,
    # for the r 19 disc at z 11..17 (0.5 radial / 0.6 axial clear),
    # kept 0.4 behind the front face so the cavity stays internal.
    p.add(g, "cylinder", "shaft-bore", {"radius": 7.3, "height": 14},
          ((0, 0, 22), (0, 0, -1), X), operation="cut")
    p.add(g, "cylinder", "cw-cavity", {"radius": 19.5, "height": 7.2},
          ((0, 0, 17.6), (0, 0, -1), X), operation="cut")
    return g


def cylinder(p):
    g = p.part("cylinder")
    # Barrel along local +Y, y 38..92 (root buried in the case, r 58).
    p.add(g, "cylinder", "barrel", {"radius": 11.5, "height": 54},
          ((0, 38, 0), Y, X))
    # Base flange ring, radial 50..59, r 13. As first built (r 14 at
    # radial 46..55) its rear rim swept straight through the exhaust
    # collector ring: the tube (centre r 46 at z -16, r 4.2) passes
    # within 2 mm of the disc's rear-inner corner. At radial 50..59
    # the closest disc point (50, z -14) misses the tube by 0.27 mm,
    # and the ring sits in the case socket (r 15.5) like a flanged
    # mounting.
    p.add(g, "cylinder", "base-ring", {"radius": 13, "height": 9},
          ((0, 50, 0), Y, X), operation="join")
    # Four cooling fins above y 48.
    for i, y0 in enumerate((56, 65, 74, 83)):
        p.add(g, "cylinder", f"fin-{i + 1}", {"radius": 14.5, "height": 2.2},
              ((0, y0, 0), Y, X), operation="join")
    # Head block: 26 (X, tangential) x 18 (Y, radial) x 24 (Z, axial),
    # y 92..110. Block frame: z = radial Y, x = tangential X, so the
    # block's own y (z cross x) is -Z and size is (26, 24, 18).
    p.block(g, "head", (26, 24, 18), (0, 101, 0), Y, X, operation="join")
    # Rocker box on top of the head: 18 x 10 x 16, y 110..120.
    p.block(g, "rocker", (18, 16, 10), (0, 115, 0), Y, X, operation="join")
    # Two pushrod tubes on the front face, running into the head and
    # through the fins (which is what joins them to the barrel).
    for i, sx in enumerate((-6, 6)):
        p.add(g, "cylinder", f"pushrod-{i + 1}",
              {"radius": 1.6, "height": 56},
              ((sx, 44, 12), Y, X), operation="join")
    # Exhaust stub out of the head's side.
    p.add(g, "cylinder", "exhaust-stub", {"radius": 3.5, "height": 11},
          ((11, 100, 0), X, Y), operation="join")
    return g


def crankshaft(p):
    g = p.part("crankshaft")
    p.add(g, "cylinder", "shaft", {"radius": 7, "height": 24},
          ((0, 0, 10), Z, X))
    # Counterweight disc inside the case, on the shaft: z 11..17,
    # centred in its case cavity (z 10.4..17.6).
    p.add(g, "cylinder", "counterweight", {"radius": 19, "height": 6},
          ((0, 0, 11), Z, X), operation="join")
    return g


def propeller(p):
    g = p.part("propeller")
    # Hub r 13, z 30..42, bored r 7.3 (z 28..36) over the r 7 shaft,
    # which ends at z 34: 0.3 radial / 2 axial clearance instead of
    # the solid hub swallowing the shaft's last 4 mm.
    p.add(g, "cylinder", "hub", {"radius": 13, "height": 12},
          ((0, 0, 30), Z, X))
    p.add(g, "cylinder", "hub-bore", {"radius": 7.3, "height": 8},
          ((0, 0, 28), Z, X), operation="cut")
    # Blades pitched 22 deg about their long (X) axis: frame z is the
    # thickness direction, tilted from +Z towards -Y.
    s, c = math.sin(math.radians(22)), math.cos(math.radians(22))
    pitch_z = (0, -s, c)
    for fid, cx in (("blade-r", 38), ("blade-l", -38)):
        p.block(g, fid, (64, 13, 4), (cx, 0, 38), pitch_z, X,
                operation="join")
    # Yellow tips: separate solids (no join), overlapping the blade ends.
    for fid, cx in (("tip-r", 66), ("tip-l", -66)):
        p.block(g, fid, (14, 13.2, 4.2), (cx, 0, 38), pitch_z, X)
    print("propeller bodies:", [(b["solid"], b.get("feature"))
                                 for b in p.bodies(g)])
    return g


def spinner(p):
    g = p.part("spinner")
    # Cone: base r 13 at z 42.3, apex at z 62.3. The 0.3 mm standoff
    # from the hub face (z 42) replaces a coincident-face contact the
    # mesh interference estimate read as 1.4 mm^3 of overlap.
    p.add(g, "cone", "cone", {"radius": 13, "height": 20},
          ((0, 0, 42.3), Z, X))
    return g


def exhaust_ring(p):
    g = p.part("exhaust-ring")
    # Torus: circle of r 4.2 centred at radius 46, in the z = -16 plane,
    # revolved about the Z axis (the line at radius 0 in the zx sketch).
    # At r 4.5 the tube was exactly tangent to every barrel (axis
    # distance 16 = 11.5 + 4.5) and the mesh estimate read the
    # tangency as ~66 mm^3 a barrel; 4.2 leaves an honest 0.3 gap.
    ops = [
        {"op": "add", "type": "point", "id": "a1", "at": ["-30 mm", "0 mm"]},
        {"op": "add", "type": "point", "id": "a2", "at": ["0 mm", "0 mm"]},
        {"op": "add", "type": "line", "id": "axis", "start": "a1", "end": "a2"},
        {"op": "add", "type": "point", "id": "pc", "at": ["-16 mm", "46 mm"]},
        {"op": "add", "type": "circle", "id": "c1", "center": "pc",
         "r": "4.2 mm"},
    ]
    sk = p.sketch(g, ops, fid="torus-profile", plane="zx")
    p.add(g, "revolve", "ring", sketch=sk, axis="axis", angle="full")
    return g


def assembly(p):
    a = p.part("radial-engine", assembly=True)
    p.add(a, "instance", "crankcase", of="crankcase", fixed=True)
    # Local +Y of a cylinder maps to (-sin a, cos a, 0) under the frame
    # z = (0,0,1), x = (cos a, sin a, 0); a = 0 points straight up (+Y).
    for k in range(7):
        ang = math.radians(k * 360.0 / 7.0)
        cx, sx = math.cos(ang), math.sin(ang)
        p.add(a, "instance", f"cyl-{k + 1}", of="cylinder",
              origin="0mm,0mm,0mm", z="0,0,1",
              x=f"{cx:.6f},{sx:.6f},0", fixed=True)
    p.add(a, "instance", "crankshaft", of="crankshaft", fixed=True)
    p.add(a, "instance", "propeller", of="propeller", fixed=True)
    p.add(a, "instance", "spinner", of="spinner", fixed=True)
    p.add(a, "instance", "exhaust-ring", of="exhaust-ring", fixed=True)
    return a


def finish(p):
    p.run("materials", "set", "aluminium", "--density", "2700 kg/m^3",
          "--colour", "#454b51", "--default")
    p.run("materials", "set", "cast-iron", "--density", "7200 kg/m^3",
          "--colour", "#26262a")
    p.run("materials", "set", "steel", "--density", "7850 kg/m^3",
          "--colour", "#333333")
    p.run("materials", "set", "brass", "--density", "8500 kg/m^3",
          "--colour", "#b08d3f")
    p.run("materials", "set", "walnut", "--density", "640 kg/m^3",
          "--colour", "#7b4b2a")
    for part, mat in [("crankcase", "aluminium"), ("cylinder", "cast-iron"),
                      ("crankshaft", "steel"), ("propeller", "walnut"),
                      ("spinner", "brass"), ("exhaust-ring", "steel")]:
        p.run("props", "set", part, f"material={mat}")
        p.run("colour", part, "--material")
    p.run("colour", "crankcase", "--colour", "#454b51")
    p.run("colour", "cylinder", "--colour", "#26262a")
    p.run("colour", "exhaust-ring", "--colour", "#333333")
    p.run("colour", "spinner", "--colour", "#b08d3f")
    p.run("colour", "propeller", "--colour", "#7b4b2a")
    # Yellow tips are their own solids in the propeller part.
    for solid in ("tip-r", "tip-l"):
        try:
            p.run("colour", f"propeller/{solid}", "--colour", "#e8c33a")
        except Exception as e:  # noqa: BLE001 - reported, retried by hand
            print(f"tip colour failed for {solid}: {e}")


def build(p):
    p.run("init", "--unit", "mm")
    crankcase(p)
    cylinder(p)
    crankshaft(p)
    propeller(p)
    spinner(p)
    exhaust_ring(p)
    assembly(p)
    finish(p)


main(build)
