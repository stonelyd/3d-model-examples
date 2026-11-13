"""An 0-6-0 saddle-tank steam locomotive (shunter), built through
ryucad's CLI only.

Forward is +X, wheels turn about Y, rail top is z=0. All static
parts are modelled in place in world coordinates and placed at the
origin in the assembly; the one wheel part is modelled about its own
centre and instanced six times (three per side, crank pins out, all
pins at the same phase: pin forward of the axle at axle height, so
the coupling rods line up on the pin span).

The saddle tank is a full cylinder cut flat at its centreline so it
saddles over the boiler. The wheel tyre is a ring (centre bored out
before the spokes are added) so the spokes actually show.
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

GREEN = "#1f5c38"
GREEN_DARK = "#17452b"
SMOKEBOX = "#26262a"
BLACK = "#17181a"
ROOF_BLACK = "#1a1a1c"
BRASS = "#b08d57"
RED = "#8e2323"
BUFFER_RED = "#a52a21"
TYRE = "#2a2a2e"
STEEL = "#8a8f98"
STEEL_BRIGHT = "#9aa0a8"
DARK_STEEL = "#33373d"
BOARD = "#24272b"
RAIL = "#6f757d"
SLEEPER = "#3a2e24"
COAL = "#17181c"
GLASS = "#101014"
PISTON = "#33363b"


def track(p):
    t = p.part("track")
    for side, s in (("l", 33), ("r", -33)):
        p.block(t, f"rail-{side}", (700, 8, 10), (0, s, -5), Z, X)
    for i, x in enumerate((-320, -240, -160, -80, 0, 80, 160, 240, 320)):
        p.block(t, f"sleeper-{i + 1}", (28, 110, 8), (x, 0, -14), Z, X)
    return t


def frames(p):
    f = p.part("frames")
    # Plates inboard at y +-26 (outer face +-28): clear of the wheel
    # hubs (inner face +-29) and tyres (+-30).
    for side, s in (("l", 26), ("r", -26)):
        p.block(f, f"plate-{side}", (300, 4, 26), (2, s, 27), Z, X)
    p.block(f, "buffer-beam", (10, 76, 20), (158, 0, 42), Z, X)
    p.block(f, "running-board", (320, 84, 4), (2, 0, 52), Z, X)
    # Cutouts in the running board: a channel the boiler sits in
    # (barrel half-width at board level is <= 13.4 mm; channel +-28)
    # and an arch over each driving wheel (wheel needs |x-wx| <= 10
    # at board underside; arches are +-13). Cuts overcut z by 1 mm
    # each way to avoid coincident-face booleans.
    p.block(f, "board-boiler-slot", (220, 56, 6), (15, 0, 52), Z, X,
            operation="cut", target="running-board")
    for i, wx in enumerate((65, -15, -95)):
        p.block(f, f"board-arch-{i + 1}", (26, 84, 6), (wx, 0, 52), Z, X,
                operation="cut", target="running-board")
    for side, s in (("l", 24), ("r", -24)):
        p.add(f, "cylinder", f"buffer-{side}", {"radius": 6, "height": 12},
              ((163, s, 42), X, Z))
    for i, wx in enumerate((65, -15, -95)):
        p.add(f, "cylinder", f"axle-{i + 1}", {"radius": 5, "height": 76},
              ((wx, -38, 26), Y, X))
    return f


def boiler(p):
    b = p.part("boiler")
    p.add(b, "cylinder", "barrel", {"radius": 27, "height": 190},
          ((-85, 0, 78), X, Z))
    p.add(b, "cylinder", "smokebox", {"radius": 27.5, "height": 30},
          ((90, 0, 78), X, Z))
    p.add(b, "cylinder", "door", {"radius": 20, "height": 4},
          ((120, 0, 78), X, Z))
    p.add(b, "cylinder", "dart", {"radius": 2.5, "height": 14},
          ((124, 0, 78), X, Z))
    p.block(b, "dart-bar", (3, 18, 3), (136, 0, 78), Z, X)
    # Chimney at x=108, mid-smokebox: at x=95 its cap (r 13) clipped
    # the saddle tank's front face (tank ends at x=92.5).
    p.add(b, "cylinder", "chimney", {"radius": 8, "height": 20},
          ((108, 0, 100), Z, X))
    p.add(b, "cone", "chimney-cap",
          {"radius": 8, "height": 8, "top_radius": 13},
          ((108, 0, 120), Z, X))
    # No steam dome: as dimensioned (r 13 at x=35) it lay entirely
    # inside the saddle tank and the barrel -- an invisible solid
    # intersecting both. The brass safety valve behind the tank is
    # the visible fitting.
    p.add(b, "cylinder", "safety", {"radius": 4, "height": 14},
          ((-40, 0, 100), Z, X))
    p.add(b, "sphere", "safety-cap", {"radius": 5}, ((-40, 0, 114), Z, X))
    return b


def tank(p):
    t = p.part("tank")
    p.add(t, "cylinder", "tank", {"radius": 33, "height": 115},
          ((-22.5, 0, 103), X, Z))
    # Saddle cut matched to the boiler: a cylinder of r 28 about the
    # boiler axis (barrel r 27 -> 1.0 mm gap; smokebox r 27.5, which
    # runs under the tank's front 2.5 mm, -> 0.5 mm gap). The old
    # flat box cut at the centreline let the boiler top (z 105) poke
    # 2 mm into the tank's flat underside.
    p.add(t, "cylinder", "saddle-cut", {"radius": 28, "height": 125},
          ((-25, 0, 78), X, Z), operation="cut")
    p.add(t, "cylinder", "filler", {"radius": 6, "height": 8},
          ((35, 0, 133), Z, X))
    return t


def cab(p):
    c = p.part("cab")
    p.block(c, "floor", (60, 84, 4), (-115, 0, 56), Z, X)
    for side, s in (("l", 40), ("r", -40)):
        p.block(c, f"side-{side}", (60, 4, 96), (-115, s, 102), Z, X)
    p.block(c, "front", (4, 84, 96), (-87, 0, 102), Z, X)
    p.block(c, "rear", (4, 84, 96), (-143, 0, 102), Z, X)
    p.block(c, "roof", (76, 92, 5), (-115, 0, 150), Z, X)
    for side, s in (("l", 18), ("r", -18)):
        p.add(c, "cylinder", f"spectacle-{side}",
              {"radius": 7, "height": 3}, ((-85, s, 118), X, Z))
    p.block(c, "bunker", (16, 72, 62), (-152, 0, 85), Z, X)
    coal = [(-156, -14, 110, 10), (-156, 14, 110, 10), (-150, 0, 112, 11),
            (-159, 2, 108, 9), (-149, -20, 108, 9)]
    for i, (x, y, z, r) in enumerate(coal):
        p.add(c, "sphere", f"coal-{i + 1}", {"radius": r}, ((x, y, z), Z, X))
    return c


def wheel(p):
    w = p.part("wheel")
    p.add(w, "cylinder", "tyre", {"radius": 26, "height": 8},
          ((0, -4, 0), Y, X))
    # Bore the tyre into a ring BEFORE the spokes exist, so the cut
    # (targeted at the tyre solid only) leaves the spokes alone.
    p.add(w, "cylinder", "bore", {"radius": 20, "height": 12},
          ((0, -6, 0), Y, X), operation="cut", target="tyre")
    # Hub 10 thick (world y +-29..39 once placed): its outer face is
    # the motion plane's inner limit. Bored r 5.4 for the r 5 axle
    # (0.4 mm clearance instead of a solid intersection).
    p.add(w, "cylinder", "hub", {"radius": 7, "height": 10},
          ((0, -5, 0), Y, X))
    p.add(w, "cylinder", "hub-bore", {"radius": 5.4, "height": 14},
          ((0, -7, 0), Y, X), operation="cut", target="hub")
    for k in range(6):
        a = math.radians(60 * k)
        radial = (math.cos(a), 0, math.sin(a))
        centre = (14.5 * radial[0], 0, 14.5 * radial[2])
        # Spokes span radially 6..23: clear of the r 5 axle by 1 mm
        # (they used to start at 3, inside the axle), still lapping
        # the hub (r 7) and the tyre ring (inner r 20).
        # block frame: z = wheel axis, x = radial; size is
        # (radial 17, tangential 4, axial 5).
        p.block(w, f"spoke-{k + 1}", (17, 4, 5), centre, Y, radial)
    p.add(w, "cylinder", "pin", {"radius": 4, "height": 8},
          ((14, 4, 0), Y, X))
    return w


def motion(p):
    m = p.part("motion")
    for side, s in (("l", 1), ("r", -1)):
        # All motion now runs in the plane y = s*43, outboard of the
        # wheel outer faces (tyre +-38, hub +-39): cylinders, crosshead
        # and rods used to run at y 34..40, in the wheel plane.
        # Coupling rod centred on the pin span: pins sit 14 mm ahead
        # of the axles at -95/-15/65, i.e. at -81/-1/79, centre -1.
        # The rod rides on the pins (which span y 38..46) through
        # bored eyes r 4.4 over the r 4 pins: 0.4 mm clearance.
        p.block(m, f"rod-{side}", (174, 5, 10), (-1, s * 43, 26), Z, X)
        for i, wx in enumerate((65, -15, -95)):
            p.add(m, "cylinder", f"rod-eye-{side}-{i + 1}",
                  {"radius": 4.4, "height": 9},
                  ((wx + 14, s * 38.5, 26), (0, s, 0), X),
                  operation="cut", target=f"rod-{side}")
        p.add(m, "cylinder", f"piston-{side}",
              {"radius": 11, "height": 44}, ((96, s * 43, 26), X, Z))
        # Crosshead centred x=95 (spans 84..106): at x=84 it straddled
        # the third crank pin (x 75..83) in plan; now it starts 1 mm
        # ahead of the pin and merges into the cylinder's rear.
        p.block(m, f"crosshead-{side}", (22, 8, 16), (95, s * 43, 26), Z, X)
        p.add(m, "cylinder", f"prod-{side}", {"radius": 2, "height": 16},
              ((84, s * 43, 26), X, Z))
        # Connecting-rod link from the crosshead back to the third
        # crank pin (x=79), with a bored eye r 4.4 on the pin. (The
        # old plain cylinder along X ran straight through the pin.)
        p.block(m, f"link-{side}", (24, 8, 14), (76, s * 43, 26), Z, X)
        p.add(m, "cylinder", f"link-eye-{side}", {"radius": 4.4,
              "height": 9}, ((79, s * 38.5, 26), (0, s, 0), X),
              operation="cut", target=f"link-{side}")
    return m


def assembly(p):
    a = p.part("steam-locomotive", assembly=True)
    for part in ("track", "frames", "boiler", "tank", "cab", "motion"):
        p.add(a, "instance", part, of=part, fixed=True)
    # Wheels: +Y side keeps the part frame (pin on +Y, outwards);
    # -Y side flips z so local +Y maps to world -Y (pin still out,
    # pin offset stays +X: same phase both sides).
    for i, wx in enumerate((65, -15, -95)):
        p.add(a, "instance", f"wheel-{i + 1}-l", of="wheel",
              origin=f"{wx}mm,34mm,26mm", fixed=True)
        p.add(a, "instance", f"wheel-{i + 1}-r", of="wheel",
              origin=f"{wx}mm,-34mm,26mm", z="0,0,-1", x="1,0,0",
              fixed=True)
    return a


COLOURS = {
    "track": {"rail-l": RAIL, "rail-r": RAIL,
              **{f"sleeper-{i}": SLEEPER for i in range(1, 10)}},
    "frames": {"plate-l": DARK_STEEL, "plate-r": DARK_STEEL,
               "buffer-beam": BUFFER_RED, "running-board": BOARD,
               "buffer-l": TYRE, "buffer-r": TYRE,
               "axle-1": DARK_STEEL, "axle-2": DARK_STEEL,
               "axle-3": DARK_STEEL},
    "boiler": {"barrel": GREEN, "smokebox": SMOKEBOX, "door": SMOKEBOX,
               "dart": STEEL, "dart-bar": STEEL, "chimney": BLACK,
               "chimney-cap": BLACK, "safety": BRASS,
               "safety-cap": BRASS},
    "tank": {"tank": GREEN, "filler": SMOKEBOX},
    "cab": {"floor": BOARD, "side-l": GREEN, "side-r": GREEN,
            "front": GREEN, "rear": GREEN, "roof": ROOF_BLACK,
            "spectacle-l": GLASS, "spectacle-r": GLASS,
            "bunker": GREEN_DARK,
            **{f"coal-{i}": COAL for i in range(1, 6)}},
    "wheel": {"tyre": TYRE, "hub": RED,
              **{f"spoke-{i}": RED for i in range(1, 7)},
              "pin": STEEL},
    "motion": {"rod-l": STEEL_BRIGHT, "rod-r": STEEL_BRIGHT,
               "piston-l": PISTON, "piston-r": PISTON,
               "crosshead-l": STEEL, "crosshead-r": STEEL,
               "prod-l": STEEL_BRIGHT, "prod-r": STEEL_BRIGHT,
               "link-l": STEEL_BRIGHT, "link-r": STEEL_BRIGHT},
}

MATERIALS = {
    "track": "steel",
    "frames": "steel",
    "boiler": "steel",
    "tank": "steel",
    "cab": "steel",
    "wheel": "cast-iron",
    "motion": "steel",
}


def finish(p):
    p.run("materials", "set", "steel", "--density", "7850 kg/m^3",
          "--colour", STEEL, "--default")
    p.run("materials", "set", "cast-iron", "--density", "7200 kg/m^3",
          "--colour", "#43464c")
    p.run("materials", "set", "brass", "--density", "8500 kg/m^3",
          "--colour", BRASS)
    p.run("materials", "set", "coal", "--density", "1300 kg/m^3",
          "--colour", COAL)
    p.run("materials", "set", "timber", "--density", "600 kg/m^3",
          "--colour", SLEEPER)
    for part, mat in MATERIALS.items():
        p.run("props", "set", part, f"material={mat}")
    for part, solids in COLOURS.items():
        have = {b["solid"] for b in p.bodies(part)}
        for solid, hexcode in solids.items():
            if solid not in have:
                print(f"WARNING: {part}/{solid} not a solid: {sorted(have)}")
                continue
            p.run("colour", f"{part}/{solid}", "--colour", hexcode)


def build(p):
    p.run("init", "--unit", "mm")
    track(p)
    frames(p)
    boiler(p)
    tank(p)
    cab(p)
    wheel(p)
    motion(p)
    assembly(p)
    finish(p)


main(build)
