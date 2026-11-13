"""A planetary gearbox desk model, built through ryucad's CLI only.

Sun (18T) drives three planets (12T) on a carrier inside a fixed ring
gear (42T): 18 + 2*12 = 42, so the geometry closes. Every gear is a
sketched disc with one tooth gap cut and patterned round it. Phasing
is tooth-into-gap at every mesh: the sun's gaps sit at 0/120/240 and
the ring's gaps too, and each planet is phased so a TOOTH points at
the sun (into its gap) and, 180 degrees on, another tooth points out
into the ring's gap. (Gap-into-gap was tried first and is wrong: the
neighbouring teeth cross flanks, 159 mm^3 a mesh by `check`.)

Parts are modelled in place about the gear axis (z) and placed at the
origin in the assembly, like the corpus radial engine. Mates are
attempted and tolerated: a refused mate is logged, not fatal.
"""

import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from model import main, polar, Failed  # noqa: E402

Z = (0, 0, 1)
X = (1, 0, 0)

MATES_OK = []
MATES_FAILED = []


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


def rot(points, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [(x * c - y * s, x * s + y * c) for x, y in points]


def gear(p, name, teeth, rp, width, bore, z0=0.0, phase=0.0):
    """An external gear: disc, one trapezoid gap cut, patterned, bored."""
    g = p.part(name)
    blank = p.sketch(g, [{"op": "add", "type": "point", "id": "c",
                          "at": ["0", "0"]},
                         {"op": "add", "type": "circle", "id": "rim",
                          "center": "c", "r": f"{rp + 2.5} mm"}],
                     fid="blank", place=((0, 0, z0), Z, X))
    p.add(g, "extrude", "disc", sketch=blank, length=f"{width} mm")
    gap = math.pi * rp / teeth
    root, tip = rp - 3.5, rp + 3.5
    # Gap half-widths 0.60 of the half-pitch at the root, 0.74 at the
    # tip: verified clash-free against the mating gears with a 2D
    # polygon model of these trapezoids before building.
    pts = rot([(root, -0.60 * gap), (tip, -0.74 * gap),
               (tip, 0.74 * gap), (root, 0.60 * gap)], phase)
    gaps = p.sketch(g, polygon(pts), fid="gap-profile",
                    place=((0, 0, z0), Z, X))
    p.add(g, "extrude", "gap", sketch=gaps, operation="cut",
          extent="through_all", both=True)
    p.add(g, "pattern", "teeth", seed="gap", form="circular", axis="z",
          count=str(teeth), angle="360")
    hub = p.sketch(g, [{"op": "add", "type": "point", "id": "o",
                        "at": ["0", "0"]}],
                   fid="axis", place=((0, 0, z0 + width), Z, X))
    p.add(g, "hole", "bore", sketch=hub, point="o",
          diameter=f"{2 * bore} mm", depth="through_all")
    p.add(g, "chamfer", "edges", d="0.4 mm", edge=p.edges(
        g, "disc", lambda e: e["curve"]["type"] == "circle"
        and abs(e["curve"]["radius"] - bore / 1000) < 1e-9))
    return g


def ring_gear(p):
    """The fixed ring: teeth point inwards (blank bore at the tip
    radius, gaps cut outwards to the root), six bolt holes in teeth."""
    g = p.part("ring")
    blank = p.sketch(g, [{"op": "add", "type": "point", "id": "c",
                          "at": ["0", "0"]},
                         {"op": "add", "type": "circle", "id": "rim",
                          "center": "c", "r": "52 mm"}], fid="blank")
    p.add(g, "extrude", "disc", sketch=blank, length="14 mm")
    p.add(g, "cylinder", "bore", {"radius": 39, "height": 22},
          ((0, 0, -4), Z, X), operation="cut")
    gap = math.pi * 42 / 42
    pts = [(38, -0.60 * gap), (47, -0.74 * gap),
           (47, 0.74 * gap), (38, 0.60 * gap)]
    gaps = p.sketch(g, polygon(pts), fid="gap-profile")
    p.add(g, "extrude", "gap", sketch=gaps, operation="cut",
          extent="through_all", both=True)
    p.add(g, "pattern", "teeth", seed="gap", form="circular", axis="z",
          count="42", angle="360")
    for k in range(6):
        p.add(g, "cylinder", f"bolt-{k + 1}", {"radius": 2, "height": 22},
              (polar(49, 30 + 60 * k, -4), Z, X), operation="cut")
    return g


def carrier(p):
    c = p.part("carrier")
    # Plate radius 35, not 34: a pin at centre distance 30 with radius 4
    # reaches exactly 34, and that tangency with the rim is what made
    # pin-1's boolean "uncertain" in the first build.
    p.add(c, "cylinder", "plate", {"radius": 35, "height": 6},
          ((0, 0, -8), Z, X))
    p.add(c, "cylinder", "hub", {"radius": 10, "height": 4},
          ((0, 0, -12), Z, X), operation="join")
    for k in range(3):
        p.add(c, "cylinder", f"pin-{k + 1}", {"radius": 4, "height": 20},
              (polar(30, 120 * k, -8), Z, X), operation="join")
    p.add(c, "cylinder", "bore", {"radius": 5.5, "height": 16},
          ((0, 0, -13), Z, X), operation="cut")
    for k in range(3):
        p.add(c, "cylinder", f"light-{k + 1}", {"radius": 7, "height": 10},
              (polar(19, 60 + 120 * k, -10), Z, X), operation="cut")
    return c


def input_shaft(p):
    s = p.part("input")
    p.add(s, "cylinder", "shaft", {"radius": 5, "height": 50},
          ((0, 0, -26), Z, X))
    p.add(s, "cylinder", "collar", {"radius": 9, "height": 5},
          ((0, 0, 16), Z, X), operation="join")
    p.block(s, "crank-arm", (30, 8, 6), (11, 0, -27), Z, X,
            operation="join")
    p.add(s, "cylinder", "handle", {"radius": 4, "height": 14},
          ((22, 0, -42), Z, X), operation="join")
    p.add(s, "cylinder", "grip", {"radius": 5.5, "height": 12},
          ((22, 0, -44), Z, X), operation="join")
    return s


def stand(p):
    s = p.part("stand")
    p.add(s, "cylinder", "plate", {"radius": 58, "height": 8},
          ((0, 0, -20), Z, X))
    p.add(s, "cylinder", "bore", {"radius": 6, "height": 12},
          ((0, 0, -22), Z, X), operation="cut")
    for k in range(6):
        p.add(s, "cylinder", f"bolt-{k + 1}", {"radius": 2.5, "height": 14},
              (polar(50, 60 * k, -22), Z, X), operation="cut")
    p.block(s, "column", (24, 40, 14), (0, -52, -16), Z, X,
            operation="join")
    p.block(s, "base", (150, 10, 84), (0, -75, 0), Z, X, operation="join")
    for sx in (-60, 60):
        for sz in (-30, 30):
            p.add(s, "cylinder", f"foot-{sx}-{sz}",
                  {"radius": 3, "height": 14},
                  ((sx, -82, sz), (0, 1, 0), X), operation="cut")
    return s


def first_solid(p, part):
    return p.bodies(part)[0]["solid"]


def try_mate(p, asm, mid, **kw):
    try:
        p.add(asm, "mate", mid, **kw)
        MATES_OK.append(mid)
    except Failed as e:
        MATES_FAILED.append(f"{mid}: {e}")


def assembly(p):
    a = p.part("planetary", assembly=True)
    for part in ["stand", "ring", "carrier", "sun", "input"]:
        p.add(a, "instance", part, of=part, fixed=True)
    # The planets are modelled about their own centres, so their
    # instances carry the centre offset (the first build left them at
    # the origin, stacked inside the sun).
    for k in range(3):
        cx, cy, _ = polar(30, 120 * k)
        # fixed=True matters: unfixed, the revolute mate solver flipped
        # each planet about its bore face (bore frames point -z), which
        # put the discs at z -13..-1 behind the carrier while their XY
        # (and every plan-view render) still looked right.
        p.add(a, "instance", f"planet-{k + 1}", of=f"planet-{k + 1}",
              origin=f"{cx:.4f}mm,{cy:.4f}mm,0mm", z="0,0,1", x="1,0,0",
              fixed=True)

    def face_ref(part, solid, keep):
        found = p.faces(part, solid, keep)
        return found[0].split("/", 1)[1] if found else None

    cyl = lambda r: (lambda f: f["surface"]["type"] == "cylinder"
                     and abs(f["surface"]["radius"] - r / 1000) < 1e-9)
    # Sun fastened to the input shaft; ring fastened to the stand.
    try_mate(p, a, "sun-key", form="fastened", a="planetary/input",
             a_offset="{}", b="planetary/sun", b_offset="{}")
    try_mate(p, a, "ring-key", form="fastened", a="planetary/stand",
             a_offset="{}", b="planetary/ring", b_offset="{}")
    # Input shaft turns in the stand's bore.
    bore = face_ref("stand", first_solid(p, "stand"), cyl(6))
    shaft = face_ref("input", first_solid(p, "input"), cyl(5))
    if bore and shaft:
        try_mate(p, a, "input-turn", form="revolute",
                 a=f"planetary/stand/{bore}", b=f"planetary/input/{shaft}",
                 a_offset="{}", b_offset="{}")
    # Each planet turns on its OWN carrier pin. Faces carry their
    # origin feature, so pin-k's face is selectable exactly. (The
    # second build gave all three mates pin-1's face -- the first r4
    # face found -- and the solver stacked planets 2 and 3 onto pin-1.)
    csolid = first_solid(p, "carrier")
    for k in range(1, 4):
        pin = face_ref("carrier", csolid,
                       lambda f, k=k: f["surface"]["type"] == "cylinder"
                       and abs(f["surface"]["radius"] - 0.004) < 1e-9
                       and f.get("origin", {}).get("feature") == f"pin-{k}")
        pbore = face_ref(f"planet-{k}", "disc", cyl(4))
        if pin and pbore:
            try_mate(p, a, f"planet-turn-{k}", form="revolute",
                     a=f"planetary/carrier/{pin}",
                     b=f"planetary/planet-{k}/{pbore}",
                     a_offset="{}", b_offset="{}")
    return a


def finish(p):
    p.run("materials", "set", "steel", "--density", "7850 kg/m^3",
          "--colour", "#8a8f98", "--default")
    p.run("materials", "set", "bronze", "--density", "8800 kg/m^3",
          "--colour", "#b08d57")
    p.run("materials", "set", "aluminium", "--density", "2700 kg/m^3",
          "--colour", "#c9ccd4")
    p.run("materials", "set", "cast-iron", "--density", "7200 kg/m^3",
          "--colour", "#43464c")
    for part, mat in [("sun", "steel"), ("input", "steel"),
                      ("planet-1", "bronze"), ("planet-2", "bronze"),
                      ("planet-3", "bronze"), ("carrier", "aluminium"),
                      ("ring", "cast-iron"), ("stand", "cast-iron")]:
        p.run("props", "set", part, f"material={mat}")
        p.run("colour", part, "--material")
    p.run("colour", "stand", "--colour", "#2e3138")
    p.run("explode", "save", "planetary", "apart", "--steps",
          '[{"instances": ["carrier"], "translate": [0, 0, "-45 mm"]},'
          ' {"instances": ["input"], "translate": [0, 0, "-95 mm"]},'
          ' {"instances": ["ring"], "translate": [0, 0, "50 mm"]},'
          ' {"instances": ["planet-1", "planet-2", "planet-3"],'
          '  "translate": [0, 0, "100 mm"]},'
          ' {"instances": ["sun"], "translate": [0, 0, "150 mm"]}]')


def build(p):
    p.run("init", "--unit", "mm")
    gear(p, "sun", 18, 18, 14, 5)
    for k in range(3):
        theta = 120 * k
        # Gap seed at theta-15 puts planet teeth at theta and
        # theta+180: tooth into the ring's gap, tooth into the sun's.
        gear(p, f"planet-{k + 1}", 12, 12, 12, 4, z0=1.0,
             phase=theta - 15)
    ring_gear(p)
    carrier(p)
    input_shaft(p)
    stand(p)
    assembly(p)
    finish(p)
    print(f"mates ok: {MATES_OK}")
    for f in MATES_FAILED:
        print(f"mate FAILED: {f}")


main(build)
