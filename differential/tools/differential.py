import os, sys, math
sys.path.insert(0, os.path.expanduser("~/workspace/ryucad-test/crates/ryucad/tests/corpus"))
from model import main, polar

Z = (0, 0, 1); X = (1, 0, 0); Y = (0, 1, 0)

STEEL = ("#b9bec4", "steel"); DARKSTEEL = ("#4a4e55", "steel")
PINIONC = ("#6f757d", "steel"); RED = ("#7a1f1f", "steel")
CAST = ("#34373d", "cast-iron"); WOOD = ("#8a6844", None)

def polygon(points, prefix=""):
    ops = []
    for i, (x, y) in enumerate(points):
        ops.append({"op": "add", "type": "point", "id": f"{prefix}p{i+1}",
                    "at": [f"{x} mm", f"{y} mm"]})
    n = len(points)
    for i in range(n):
        ops.append({"op": "add", "type": "line", "id": f"{prefix}l{i+1}",
                    "start": f"{prefix}p{i+1}", "end": f"{prefix}p{(i+1)%n+1}"})
    return ops

def spur(p, name, teeth, pitch_r, thick, colour, mat, bore_r=None, hub=None):
    tip = pitch_r + 0.25 * (2 * math.pi * pitch_r / teeth)
    root = pitch_r - 0.315 * (2 * math.pi * pitch_r / teeth)
    g = p.part(name)
    blank = p.sketch(g, [{"op": "add", "type": "point", "id": "c", "at": ["0", "0"]},
                         {"op": "add", "type": "circle", "id": "rim", "center": "c",
                          "r": f"{tip} mm"}], fid="blank", place=((0, 0, -thick / 2), Z, X))
    p.add(g, "extrude", "disc", sketch=blank, length=f"{thick} mm")
    if hub:
        hr, hz0, hz1 = hub
        p.add(g, "cylinder", "hub", {"radius": hr, "height": hz1 - hz0},
              ((0, 0, hz0), Z, X), operation="join")
    hp = math.pi * pitch_r / teeth
    pts = [(root, -0.60 * hp), (tip + 1.5, -0.74 * hp), (tip + 1.5, 0.74 * hp), (root, 0.60 * hp)]
    gaps = p.sketch(g, polygon(pts), fid="gap-profile", place=((0, 0, 0), Z, X))
    p.add(g, "extrude", "gap", sketch=gaps, operation="cut", extent="through_all", both=True)
    p.add(g, "pattern", "teeth", seed="gap", form="circular", axis="z",
          count=str(teeth), angle="360")
    if bore_r:
        p.add(g, "cylinder", "bore", {"radius": bore_r, "height": thick + 26},
              ((0, 0, -thick / 2 - 13), Z, X), operation="cut")
    return g

def bevel(p, name, teeth, blank_prof, bore_r, bore_span, gap, colour):
    """Bevel gear: revolve blank at TIP cone, bore cut, then prismatic
    sector gap cuts (XY sketch, blind z-range over the tooth band),
    patterned. Tooth thickness tapers with radius (correct bevel look);
    gap floors sit below the root cone (no bottoming)."""
    g = p.part(name)
    sk = p.sketch(g, polygon(blank_prof), fid="blank-profile", plane="zx")
    p.add(g, "revolve", "blank", sketch=sk, axis=f"l{len(blank_prof)}", angle="full")
    z0, h = bore_span
    p.add(g, "cylinder", "bore", {"radius": bore_r, "height": h},
          ((0, 0, z0), Z, X), operation="cut")
    root, tip, hw_r, hw_t, gz, glen = gap
    pts = [(root, -hw_r), (tip, -hw_t), (tip, hw_t), (root, hw_r)]
    gaps = p.sketch(g, polygon(pts), fid="gap-profile", place=((0, 0, gz), Z, X))
    p.add(g, "extrude", "gap", sketch=gaps, length=f"{glen} mm", operation="cut")
    p.add(g, "pattern", "teeth", seed="gap", form="circular", axis="z",
          count=str(teeth), angle="360")
    return g

def build(p):
    p.run("init", "--unit", "mm")

    # ---- gears ------------------------------------------------------------
    # side gears 16T: blank at tip cone (profile in (z, r), apex at origin)
    side_prof = [(7.5, 0), (7.5, 12.5), (10.2, 18.1), (15.2, 26.75),
                 (17.5, 26.75), (17.5, 11), (36, 11), (36, 0)]
    # gap: root r, tip r, half-widths root/tip, z start, length
    # (gap cuts run out through the heel/back band, as real bevel teeth do,
    # so the mating tooth heels clear the blank's back cylinder)
    side_gap = (12.8, 28.0, 2.44, 3.01, 9.8, 8.2)
    sg_r = bevel(p, "side-gear-right", 16, side_prof, 6, (-2, 40), side_gap, STEEL[0])
    sg_l = bevel(p, "side-gear-left", 16, side_prof, 6, (-2, 40), side_gap, STEEL[0])
    # pinions 10T
    pin_prof = [(14.5, 0), (14.5, 6.5), (16.4, 12.0), (23.8, 17.25),
                (25.5, 17.25), (25.5, 6.5), (31, 6.5), (31, 0)]
    pin_gap = (6.8, 18.6, 2.51, 3.08, 15.9, 9.8)
    pin_parts = []
    for nm in ("pinion-1", "pinion-2", "pinion-3", "pinion-4"):
        pin_parts.append(bevel(p, nm, 10, pin_prof, 4.7, (12, 21), pin_gap, PINIONC[0]))

    # ring gear 40T pitch r40 (spur idiom) + input pinion 13T pitch r13;
    # ring centre bore r12 clears the left side-gear hub (r11)
    ring = spur(p, "ring-gear", 40, 40.0, 8, STEEL[0], STEEL[1], bore_r=12,
                hub=None)
    # bolts joined into the ring disc (tips end inside the cheek holes);
    # place origin is (x, y, z): bolt circle in local XY, axial start z=-4
    for k in range(6):
        a = math.radians(60 * k + 30)
        p.add(ring, "cylinder", f"bolt{k+1}", {"radius": 2.5, "height": 12.5},
              ((31 * math.cos(a), 31 * math.sin(a), -4), Z, X), operation="join")
    inp = spur(p, "input-pinion", 13, 13.0, 9, PINIONC[0], PINIONC[1], bore_r=4.2)

    # ---- carrier -----------------------------------------------------------
    car = p.part("carrier")
    p.add(car, "cylinder", "shell", {"radius": 36, "height": 56},
          ((-28, 0, 0), X, Z))
    p.add(car, "cylinder", "shell-bore", {"radius": 33, "height": 58},
          ((-29, 0, 0), X, Z), operation="cut")
    for sgn, nm in ((1, "cheek-r"), (-1, "cheek-l")):
        x0 = 28 if sgn > 0 else -34          # cheek disc spans x0..x0+6
        xb = 26 if sgn > 0 else -38          # bore cut spans the cheek
        p.add(car, "cylinder", nm, {"radius": 36, "height": 6},
              ((x0, 0, 0), X, Z), operation="join")
        p.add(car, "cylinder", f"{nm}-bore", {"radius": 11.4, "height": 12},
              ((xb, 0, 0), X, Z), operation="cut")
        # NOTE: no separate r6 axle cut in the cheek — the axle passes
        # through the side-gear hub, which journals in this r11.4 bore.
        # (An empty boolean here silently killed later features in 0.9.0.)
    for k in range(6):
        a = math.radians(60 * k + 30)
        p.add(car, "cylinder", f"bolthole{k+1}", {"radius": 3, "height": 12},
              ((-36, 31 * math.cos(a), 31 * math.sin(a)), X, Z), operation="cut")
    for k in range(4):
        a = math.radians(90 * k + 45)
        cx, cy = 30 * math.cos(a), 30 * math.sin(a)
        p.block(car, f"window{k+1}", (24, 26, 26), (0, cx, cy), Z, X, operation="cut")
    p.add(car, "cylinder", "pin-z", {"radius": 4.5, "height": 66},
          ((0, 0, -33), Z, X), operation="join")
    p.add(car, "cylinder", "pin-y", {"radius": 4.5, "height": 66},
          ((0, -33, 0), Y, X), operation="join")

    # ---- axles + hand wheels (part axis = local Z, like the gears) -----------
    def axle(name):
        g = p.part(name)
        p.add(g, "cylinder", "shaft", {"radius": 5.6, "height": 90}, ((0, 0, 8), Z, X))
        p.add(g, "cylinder", "wheel", {"radius": 16, "height": 8}, ((0, 0, 90), Z, X),
              operation="join")
        p.add(g, "cylinder", "grip", {"radius": 3.5, "height": 14},
              ((12, 0, 97), Z, X), operation="join")
        return g
    ax_r = axle("axle-right"); ax_l = axle("axle-left")

    # ---- layshaft (crank at the +X end, clear of the left pedestal) ---------
    lay = p.part("layshaft")
    p.add(lay, "cylinder", "shaft", {"radius": 4, "height": 116}, ((-72, 0, -53), X, Z))
    p.block(lay, "crank-arm", (5, 8, 26), (38, 0, -43), Z, X, operation="join")
    grip = p.part("crank-grip")
    p.add(grip, "cylinder", "grip", {"radius": 4.5, "height": 11},
          ((40.5, 0, -32), X, Z))

    # ---- base -----------------------------------------------------------------
    base = p.part("base")
    p.block(base, "plate", (190, 110, 8), (0, 0, -78), Z, X)
    for sgn in (1, -1):
        p.block(base, f"pedestal{sgn}", (16, 34, 86), (sgn * 80, 0, -31), Z, X,
                operation="join")
        p.add(base, "cylinder", f"bearing{sgn}", {"radius": 6, "height": 20},
              ((sgn * 80 - 10, 0, 0), X, Z), operation="cut")
    for cx in (-55, -15):
        p.block(base, f"layped{cx}", (14, 26, 25), (cx, 0, -61.5), Z, X, operation="join")
        p.add(base, "cylinder", f"laybore{cx}", {"radius": 4.4, "height": 18},
              ((cx - 9, 0, -53), X, Z), operation="cut")

    # ---- materials & colours (0.9.0 idiom) -----------------------------------
    p.run("materials", "set", "steel", "--density", "7850 kg/m^3",
          "--colour", "#b9bec4", "--default")
    p.run("materials", "set", "cast-iron", "--density", "7200 kg/m^3",
          "--colour", "#34373d")
    p.run("materials", "set", "wood", "--density", "700 kg/m^3",
          "--colour", "#8a6844")
    for part, mat, col in (
            ("side-gear-right", "steel", None), ("side-gear-left", "steel", None),
            ("ring-gear", "steel", None),
            ("pinion-1", "steel", "#6f757d"), ("pinion-2", "steel", "#6f757d"),
            ("pinion-3", "steel", "#6f757d"), ("pinion-4", "steel", "#6f757d"),
            ("input-pinion", "steel", "#6f757d"),
            ("carrier", "steel", "#7a1f1f"),
            ("axle-right", "steel", "#4a4e55"), ("axle-left", "steel", "#4a4e55"),
            ("layshaft", "steel", "#4a4e55"),
            ("crank-grip", "wood", None),
            ("base", "cast-iron", None)):
        p.run("props", "set", part, f"material={mat}")
        if col:
            p.run("colour", part, "--colour", col)
        else:
            p.run("colour", part, "--material")

    # ---- assembly --------------------------------------------------------------
    asm = p.part("differential", assembly=True)
    ID = {"z": "0,0,1", "x": "1,0,0"}
    p.add(asm, "instance", "base", of="base", origin="0mm,0mm,0mm",
          fixed=True, **ID)
    cos11 = "0.9807852804032304"; sin11 = "0.19509032201612825"
    p.add(asm, "instance", "side-gear-right", of="side-gear-right",
          origin="0mm,0mm,0mm", z="1,0,0", x=f"0,{cos11},-{sin11}", fixed=True)
    p.add(asm, "instance", "side-gear-left", of="side-gear-left",
          origin="0mm,0mm,0mm", z="-1,0,0", x=f"0,{cos11},{sin11}", fixed=True)
    p.add(asm, "instance", "pinion-z-top", of="pinion-1",
          origin="0mm,0mm,0mm", z="0,0,1", x="1,0,0", fixed=True)
    p.add(asm, "instance", "pinion-z-bottom", of="pinion-2",
          origin="0mm,0mm,0mm", z="0,0,-1", x="1,0,0", fixed=True)
    p.add(asm, "instance", "pinion-y-front", of="pinion-3",
          origin="0mm,0mm,0mm", z="0,1,0", x="1,0,0", fixed=True)
    p.add(asm, "instance", "pinion-y-back", of="pinion-4",
          origin="0mm,0mm,0mm", z="0,-1,0", x="1,0,0", fixed=True)
    p.add(asm, "instance", "carrier", of="carrier", origin="0mm,0mm,0mm",
          fixed=True, **ID)
    p.add(asm, "instance", "ring-gear", of="ring-gear",
          origin="-38.5mm,0mm,0mm", z="1,0,0", x="0,1,0", fixed=True)
    p.add(asm, "instance", "axle-right", of="axle-right",
          origin="0mm,0mm,0mm", z="1,0,0", x="0,1,0", fixed=True)
    p.add(asm, "instance", "axle-left", of="axle-left",
          origin="0mm,0mm,0mm", z="-1,0,0", x="0,1,0", fixed=True)
    dlt = -6.923; cd, sd = math.cos(math.radians(dlt)), math.sin(math.radians(dlt))
    p.add(asm, "instance", "input-pinion", of="input-pinion",
          origin="-38mm,0mm,-53mm", z="1,0,0", x=f"0,{cd:.6f},{sd:.6f}",
          fixed=True)
    p.add(asm, "instance", "layshaft", of="layshaft", origin="0mm,0mm,0mm",
          fixed=True, **ID)
    p.add(asm, "instance", "crank-grip", of="crank-grip", origin="0mm,0mm,0mm",
          fixed=True, **ID)
    p.run("explode", "save", "differential", "apart", "--steps",
          '[{"instances": ["ring-gear"], "translate": ["-70 mm", 0, 0]},'
          ' {"instances": ["side-gear-left"], "translate": ["-60 mm", 0, 0]},'
          ' {"instances": ["side-gear-right"], "translate": ["60 mm", 0, 0]},'
          ' {"instances": ["axle-left"], "translate": ["-140 mm", 0, 0]},'
          ' {"instances": ["axle-right"], "translate": ["140 mm", 0, 0]},'
          ' {"instances": ["pinion-z-top"], "translate": [0, 0, "55 mm"]},'
          ' {"instances": ["pinion-z-bottom"], "translate": [0, 0, "-55 mm"]},'
          ' {"instances": ["pinion-y-front"], "translate": [0, "55 mm", 0]},'
          ' {"instances": ["pinion-y-back"], "translate": [0, "-55 mm", 0]},'
          ' {"instances": ["input-pinion", "layshaft", "crank-grip"],'
          '  "translate": [0, 0, "-45 mm"]}]')
    bom = p.run("bom", "differential")
    print("BOM lines:", len(bom["tree"]["children"]))
    chk = p.run("check", "differential")
    print("CHECK passed:", chk["passed"], "errors:", chk["errors"],
          "warnings:", chk["warnings"])
    for f in chk["findings"]:
        print("  FINDING:", f["a"], "<->", f["b"],
              f"{f['volume_m3'] * 1e9:.1f} mm3")
    intf = p.run("interference", "differential")
    print("INTERFERENCE pairs:", intf["pairs"], "clear:", intf["clear"],
          "interfering:", len(intf["interferences"]),
          "touching:", len(intf.get("touching", [])))

main(build)
