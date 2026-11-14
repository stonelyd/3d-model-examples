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

    # ---- assembly (parametric: mates driven by crank/slip) ---------------------
    asm = p.part("differential", assembly=True)
    ID = {"z": "0,0,1", "x": "1,0,0"}
    # two inputs, four derived couplings. carrier follows the crank through
    # the 13:40 final drive; the axles split around the carrier by the slip;
    # each spider pinion spins about its own outward axis at slip * 16/10.
    p.run("param", "set", asm, "crank=0 deg", "slip=0 deg")
    p.run("param", "set", asm, "carrier=crank * 13 / 40")
    p.run("param", "set", asm, "left=carrier + slip", "right=carrier - slip")
    p.run("param", "set", asm, "spider=slip * 16 / 10")
    p.add(asm, "instance", "base", of="base", origin="0mm,0mm,0mm",
          fixed=True, **ID)
    cos11 = "0.9807852804032304"; sin11 = "0.19509032201612825"
    p.add(asm, "instance", "side-gear-right", of="side-gear-right",
          origin="0mm,0mm,0mm", z="1,0,0", x=f"0,{cos11},-{sin11}")
    p.add(asm, "instance", "side-gear-left", of="side-gear-left",
          origin="0mm,0mm,0mm", z="-1,0,0", x=f"0,{cos11},{sin11}")
    p.add(asm, "instance", "pinion-z-top", of="pinion-1",
          origin="0mm,0mm,0mm", z="0,0,1", x="1,0,0")
    p.add(asm, "instance", "pinion-z-bottom", of="pinion-2",
          origin="0mm,0mm,0mm", z="0,0,-1", x="1,0,0")
    p.add(asm, "instance", "pinion-y-front", of="pinion-3",
          origin="0mm,0mm,0mm", z="0,1,0", x="1,0,0")
    p.add(asm, "instance", "pinion-y-back", of="pinion-4",
          origin="0mm,0mm,0mm", z="0,-1,0", x="1,0,0")
    p.add(asm, "instance", "carrier", of="carrier", origin="0mm,0mm,0mm", **ID)
    p.add(asm, "instance", "ring-gear", of="ring-gear",
          origin="-38.5mm,0mm,0mm", z="1,0,0", x="0,1,0")
    p.add(asm, "instance", "axle-right", of="axle-right",
          origin="0mm,0mm,0mm", z="1,0,0", x="0,1,0")
    p.add(asm, "instance", "axle-left", of="axle-left",
          origin="0mm,0mm,0mm", z="-1,0,0", x="0,1,0")
    dlt = -6.923; cd, sd = math.cos(math.radians(dlt)), math.sin(math.radians(dlt))
    p.add(asm, "instance", "input-pinion", of="input-pinion",
          origin="-38mm,0mm,-53mm", z="1,0,0", x=f"0,{cd:.6f},{sd:.6f}")
    p.add(asm, "instance", "layshaft", of="layshaft", origin="0mm,0mm,0mm",
          **ID)
    p.add(asm, "instance", "crank-grip", of="crank-grip", origin="0mm,0mm,0mm",
          **ID)

    # ---- mates -----------------------------------------------------------------
    # ryumate connector semantics (measured on 0.9.0 with a probe rig and
    # against the corpus gearbox): a mate connector's origin is the owning
    # instance's origin, with the referenced face's frame origin substituted
    # only in the plane perpendicular to the face axis (the axial station
    # stays at the instance origin); the face supplies the connector axes.
    # The offset document then shifts the origin in connector axes, turns
    # about z and flips about x. Each offset below makes B's connector
    # coincide with A's at the placed pose, so angle 0 is the shipped
    # static pose and a positive angle turns B right-handed about the
    # connector z. All main-axis and layshaft connectors end with z = +X
    # (their axis lines through (0,0,0) and (0,0,-53) respectively, from
    # the anchor faces' perpendicular components); the pinions' connectors
    # sit on the carrier origin with z along their pin.
    import json as _json

    def cyl_face(part, solid, radius_mm, origin_pred):
        refs = p.faces(part, solid, lambda f: f["surface"]["type"] == "cylinder"
                       and abs(f["surface"]["radius"] * 1000 - radius_mm) < 0.01
                       and origin_pred([v * 1000 for v in f["surface"]["frame"]["origin"]]))
        assert refs, (part, solid, radius_mm)
        return refs[0].split("/", 1)[1]  # "<solid>/<hash>"

    def off(Ob, xb, yb, zb, Oa, xa):
        """Offset taking B's connector (instance origin Ob, axes xb/yb/zb)
        onto A's connector (origin Oa, x xa): origin in B's axes plus the
        turn about z that aligns B's x onto A's x."""
        d = [Oa[i] - Ob[i] for i in range(3)]
        dot = lambda a, b: a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
        o = {"origin": [f"{dot(d, ax):.6f} mm" for ax in (xb, yb, zb)]}
        theta = math.degrees(math.atan2(dot(xa, yb), dot(xa, xb)))
        if abs(theta) > 1e-9:
            o["rotate"] = f"{theta:.6f} deg"
        return o

    def J(o):
        return _json.dumps(o)

    # Anchor faces: base bearings (main axis) and laybores (layshaft axis)
    # all have frame x=(0,0,1), z=+X; the carrier cheek bore face matches.
    XA = (0, 0, 1)
    brg_p = cyl_face("base", "plate", 6.0, lambda o: o[0] > 0)      # (70,0,0)
    brg_m = cyl_face("base", "plate", 6.0, lambda o: o[0] < 0)      # (-90,0,0)
    lay_55 = cyl_face("base", "plate", 4.4, lambda o: o[0] < -40)   # (-64,0,-53)
    lay_15 = cyl_face("base", "plate", 4.4, lambda o: o[0] > -40)   # (-24,0,-53)
    cheek_r = cyl_face("carrier", "shell", 11.4, lambda o: o[0] > 0)  # (26,0,0)
    pin_y = cyl_face("carrier", "shell", 4.5,
                     lambda o: abs(o[1] + 33) < 1 and abs(o[0]) < 1)  # pin-y face
    lay_shaft_f = cyl_face("layshaft", "shaft", 4.0, lambda o: True)  # (-72,0,-53)

    def rev(mid, a_ref, b_ref, a_off, b_off, angle):
        flags = dict(form="revolute", a=a_ref, b=b_ref,
                     a_offset=J(a_off) if a_off else "{}",
                     b_offset=J(b_off) if b_off else "{}")
        if angle:
            flags["angle"] = angle
        p.add(asm, "mate", mid, **flags)

    Z3 = (0.0, 0.0, 0.0)
    # Input group: layshaft (via its shaft face; connector already on the
    # layshaft axis at (0,0,-53)) and input pinion turn with the crank.
    # The ring gear is an external mesh, so the pinion turns -crank about
    # +X when the carrier turns +crank*13/40 (rolling at the pitch point).
    rev("turn-layshaft", f"{asm}/base/{lay_55}",
        f"{asm}/layshaft/{lay_shaft_f}", None, None, "-crank")
    ip_x = (0, cd, sd); ip_y = (0, -sd, cd)
    rev("turn-input-pinion", f"{asm}/base/{lay_15}", f"{asm}/input-pinion", None,
        off((-38, 0, -53), ip_x, ip_y, (1, 0, 0), (0, 0, -53), XA), "-crank")
    p.add(asm, "mate", "grip-on-layshaft", form="fastened",
          a=f"{asm}/layshaft", a_offset="{}", b=f"{asm}/crank-grip",
          b_offset="{}")
    # Carrier group: drum (via its cheek bore face; connector already on
    # the main axis at the origin) and ring gear, both at angle=carrier.
    rev("turn-carrier", f"{asm}/base/{brg_p}", f"{asm}/carrier/{cheek_r}",
        None, None, "carrier")
    rev("turn-ring-gear", f"{asm}/base/{brg_m}", f"{asm}/ring-gear", None,
        off((-38.5, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0), Z3, XA), "carrier")
    # Right group: axle + side gear at angle=right about +X.
    rev("turn-axle-right", f"{asm}/base/{brg_p}", f"{asm}/axle-right", None,
        off(Z3, (0, 1, 0), (0, 0, 1), (1, 0, 0), Z3, XA), "right")
    c11, s11 = 0.9807852804032304, 0.19509032201612825
    rev("turn-gear-right", f"{asm}/base/{brg_p}", f"{asm}/side-gear-right", None,
        off(Z3, (0, c11, -s11), (0, s11, c11), (1, 0, 0), Z3, XA), "right")
    # Left group: frames point -X, so their connectors flip onto +X and
    # the same angle expression turns them +left about +X.
    o = off(Z3, (0, 1, 0), (0, 0, -1), (-1, 0, 0), Z3, XA); o["flip"] = True
    rev("turn-axle-left", f"{asm}/base/{brg_m}", f"{asm}/axle-left", None, o,
        "left")
    o = off(Z3, (0, c11, s11), (0, s11, -c11), (-1, 0, 0), Z3, XA)
    o["flip"] = True
    rev("turn-gear-left", f"{asm}/base/{brg_m}", f"{asm}/side-gear-left", None,
        o, "left")
    # Spider pinions, chained on the carrier: the z pair mates on the
    # carrier's own frame (its z is the pin axis), the y pair on the
    # carrier's pin-y face. Connectors already coincide at the carrier
    # origin, so only the flipped pinions carry an offset; they take
    # -spider so every pinion spins +spider about its own outward axis,
    # as the mesh kinematics require (rolling at both pitch points).
    rev("spin-z-top", f"{asm}/carrier", f"{asm}/pinion-z-top", None, None,
        "spider")
    rev("spin-z-bottom", f"{asm}/carrier", f"{asm}/pinion-z-bottom", None,
        {"flip": True}, "-spider")
    rev("spin-y-front", f"{asm}/carrier/{pin_y}", f"{asm}/pinion-y-front",
        None, None, "spider")
    rev("spin-y-back", f"{asm}/carrier/{pin_y}", f"{asm}/pinion-y-back", None,
        {"flip": True}, "-spider")
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
    eq = p.run("equations", "differential")
    for row in eq["rows"]:
        if row["what"] == "parameter":
            print("PARAM", row["name"], "=", row["text"], "->",
                  f"{row['value'].get('rad', 0):.6f} rad")

main(build)
