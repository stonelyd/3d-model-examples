"""A 4-module (70 mm wide) DIN-rail electronics enclosure for a custom
controller PCB, as a ryucad assembly, built through the CLI only.

Assembly frame (millimetres): x along the rail (module width), z up the
cabinet (enclosure height, the latch slides along z), y out of the cabinet
(depth). The rail's front (flange) faces are at y = 0.

  - 35 x 7.5 top-hat rail section (EN 60715 TS35), 100 mm long, slotted web
  - base housing: 2 mm walls, open front, back-wall ribs (1.2 mm, 60 % of
    wall), four PCB bosses with pilot holes for M2.5 self-tapping screws,
    a fixed rail hook at the top, a T-slot track for the latch at the
    bottom, windows for the cover's snap hooks, terminal-plug windows top
    and bottom, and a USB-C cutout in the bottom wall
  - DIN latch slider (orange) in the T-slot, with a lead-in nose, a
    screwdriver tab and two moulded meander spring legs; it slides on one
    slider mate driven by the assembly parameter `latch` (0 mm closed,
    6 mm pulled open, clamped 0..7 mm)
  - cover: 45 mm front nose (DIN 43880 style), front label recess with a
    label, four light-pipe holes, vent slots in both shoulders, four
    cantilever snap hooks into the base
  - four light pipes with retaining collars over four PCB LEDs
  - 1.6 mm controller PCB on the bosses with four pan-head M2.5 PT screws
  - two pluggable 5.08 mm 4-pole terminal blocks (PCB header with pins,
    screw plug with wire entries and four M3 clamp screws each), top and
    bottom edges
  - USB-C receptacle (shell, tongue) at the bottom edge behind the cutout

Every part with a unique place is modelled in the assembly frame, so its
instance sits at the identity pose; repeated parts are modelled once at
their own origin and placed by mate offsets.
"""
import json
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from model import main  # noqa: E402

X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
ASM = "din-enclosure"
LED_X = (-12.0, -4.0, 4.0, 12.0)
LED_Z = 12.0
PITCH = 5.08
POLES = tuple((i - 1.5) * PITCH for i in range(4))   # -7.62 .. 7.62
BOSSES = [(sx * 28.0, sz * 36.0) for sx in (-1, 1) for sz in (-1, 1)]
HOOKS_Z = (-25.0, 25.0)
USB_X, USB_Y = 20.0, 13.43


def f(v):
    return f"{v:.6f}"


# ---------------------------------------------------------------- helpers
def box(p, part, fid, x0, x1, y0, y1, z0, z1, **flags):
    """An axis-aligned box from its extents."""
    return p.add(part, "box", fid, {"x": f(x1 - x0), "y": f(y1 - y0), "z": f(z1 - z0)},
                 ((x0, y0, z0), Z, X), **flags)


def cyl_y(p, part, fid, r, x, z, y0, y1, **flags):
    return p.add(part, "cylinder", fid, {"radius": f(r), "height": f(y1 - y0)},
                 ((x, y0, z), Y, Z), **flags)


def cyl_z(p, part, fid, r, x, y, z0, z1, **flags):
    return p.add(part, "cylinder", fid, {"radius": f(r), "height": f(z1 - z0)},
                 ((x, y, z0), Z, X), **flags)


def poly_ops(points):
    ops = []
    for i, (a, b) in enumerate(points):
        ops.append({"op": "add", "type": "point", "id": f"p{i+1}",
                    "at": [f"{a:.6f} mm", f"{b:.6f} mm"]})
    n = len(points)
    for i in range(n):
        ops.append({"op": "add", "type": "line", "id": f"l{i+1}",
                    "start": f"p{i+1}", "end": f"p{(i+1) % n + 1}"})
    return ops


def prism_x(p, part, fid, pts_yz, x0, length, **flags):
    """A closed (y, z) polygon extruded along +x from x0."""
    sk = p.sketch(part, poly_ops(pts_yz), fid=f"{fid}-profile", place=((x0, 0, 0), X, Y))
    return p.add(part, "extrude", fid, sketch=sk, length=f"{length:.6f} mm", **flags)


def prism_y(p, part, fid, pts_xz, y0, length, **flags):
    """A closed (x, z) polygon extruded along +y from y0 (sketch u = z, v = x)."""
    pts = [(zz, xx) for xx, zz in pts_xz]
    sk = p.sketch(part, poly_ops(pts), fid=f"{fid}-profile", place=((0, y0, 0), Y, Z))
    return p.add(part, "extrude", fid, sketch=sk, length=f"{length:.6f} mm", **flags)


def stadium_z(p, part, fid, cx, cy, w, h, z0, z1, **flags):
    """A slot (stadium) w x h in x/y, along z: a box and two round ends."""
    r = h / 2
    ends = dict(flags) if flags else {"operation": "join"}
    box(p, part, f"{fid}-mid", cx - w / 2 + r, cx + w / 2 - r, cy - r, cy + r, z0, z1, **flags)
    cyl_z(p, part, f"{fid}-l", r, cx - w / 2 + r, cy, z0, z1, **ends)
    cyl_z(p, part, f"{fid}-r", r, cx + w / 2 - r, cy, z0, z1, **ends)


def colour(p, part, c):
    p.run("colour", part, "--colour", c)


# ------------------------------------------------------------------ parts
def din_rail(p):
    c = p.part("din-rail-ts35")
    prof = [(0, 17.5), (-1, 17.5), (-1, 13.5), (-7.5, 13.5), (-7.5, -13.5), (-1, -13.5),
            (-1, -17.5), (0, -17.5), (0, -12.5), (-6.5, -12.5), (-6.5, 12.5), (0, 12.5)]
    prism_x(p, c, "rail", prof, -50, 100)
    for i, cx in enumerate((-37.5, -12.5, 12.5, 37.5)):
        box(p, c, f"slot{i+1}", cx - 5.0, cx + 5.0, -8.5, -5.5, -2.6, 2.6, operation="cut")
        cyl_y(p, c, f"slot{i+1}-a", 2.6, cx - 5.0, 0, -8.5, -5.5, operation="cut")
        cyl_y(p, c, f"slot{i+1}-b", 2.6, cx + 5.0, 0, -8.5, -5.5, operation="cut")
    colour(p, c, "#b4b9c0")


def base_housing(p):
    c = p.part("base-housing")
    box(p, c, "shell", -35, 35, 0.3, 40.0, -45, 45)
    box(p, c, "hollow", -33, 33, 2.3, 41.0, -43, 43, operation="cut")
    # latch boss, back-wall ribs (1.2 mm = 60 % of wall) and PCB bosses
    box(p, c, "latch-boss", -13, 13, 2.0, 5.3, -44, -14, operation="join")
    for i, xr in enumerate((-15.0, 15.0)):
        box(p, c, f"rib-v{i+1}", xr - 0.6, xr + 0.6, 2.0, 7.3, -43.5, 43.5, operation="join")
    box(p, c, "rib-h", -33.5, 33.5, 2.0, 7.3, -0.6, 0.6, operation="join")
    for i, (bx, bz) in enumerate(BOSSES):
        cyl_y(p, c, f"boss{i+1}", 3.0, bx, bz, 2.0, 9.8, operation="join")
        box(p, c, f"gusset{i+1}", bx - 0.6 if bx < 0 else bx - 0.6, bx + 0.6,
            2.0, 7.3, bz - 5.5 if bz > 0 else bz + 2.5, bz - 2.5 if bz > 0 else bz + 5.5,
            operation="join")
        cyl_y(p, c, f"pilot{i+1}", 1.1, bx, bz, 3.0, 10.5, operation="cut")
    # the fixed rail hook over the top flange, with a lead-in
    prism_x(p, c, "rail-hook", [(0.6, 21.0), (-2.5, 21.0), (-2.5, 15.8), (-1.9, 15.0),
                                (-1.3, 15.0), (-1.3, 18.0), (0.6, 18.0)], -10, 20,
            operation="join")
    # T-slot track for the latch, open at the back and bottom; spring pockets
    box(p, c, "track", -7.2, 7.2, 1.0, 3.0, -46, -16, operation="cut")
    box(p, c, "track-mouth", -5.2, 5.2, -0.5, 1.2, -46, -16, operation="cut")
    box(p, c, "spring-pocket-r", 7.0, 11.6, 1.0, 3.0, -32.5, -17, operation="cut")
    box(p, c, "spring-pocket-l", -11.6, -7.0, 1.0, 3.0, -32.5, -17, operation="cut")
    # windows for the cover's snap hooks
    for i, hz in enumerate(HOOKS_Z):
        box(p, c, f"snap-window-r{i+1}", 32.5, 35.5, 34.0, 37.0, hz - 4.6, hz + 4.6,
            operation="cut")
        box(p, c, f"snap-window-l{i+1}", -35.5, -32.5, 34.0, 37.0, hz - 4.6, hz + 4.6,
            operation="cut")
    # terminal-plug windows (top, bottom) and the USB-C cutout (bottom)
    box(p, c, "plug-window-top", -10.8, 10.8, 12.0, 23.1, 42, 46, operation="cut")
    box(p, c, "plug-window-bot", -10.8, 10.8, 12.0, 23.1, -46, -42, operation="cut")
    stadium_z(p, c, "usb-cutout", USB_X, USB_Y, 9.6, 3.9, -46, -42, operation="cut")
    colour(p, c, "#d5d8dc")


def meander(p, c, side):
    """A moulded meander spring leg beside the latch plate (side +1 or -1):
    five 0.6 mm bars joined alternately at their ends."""
    def xs(a, b):
        return (min(side * a, side * b), max(side * a, side * b))
    bars = [-19.0, -20.6, -22.2, -23.8, -25.4]
    for i, zc in enumerate(bars):
        x0 = 6.6 if i == 0 else 7.6
        box(p, c, f"spring-{'r' if side > 0 else 'l'}-bar{i+1}", *xs(x0, 10.9), 1.3, 2.7, zc - 0.3, zc + 0.3,
            operation="join")
    for i in range(len(bars) - 1):
        xa = (10.3, 10.9) if i % 2 == 0 else (7.6, 8.2)
        box(p, c, f"spring-{'r' if side > 0 else 'l'}-link{i+1}", *xs(*xa), 1.3, 2.7, bars[i + 1] - 0.1,
            bars[i] + 0.1, operation="join")


def latch(p):
    c = p.part("din-latch")
    box(p, c, "plate", -7, 7, 1.2, 2.8, -46, -18)
    prism_x(p, c, "nose", [(1.3, -21.0), (1.3, -18.0), (-1.3, -18.0), (-1.3, -15.0),
                           (-1.9, -15.0), (-2.5, -15.8), (-2.5, -21.0)], -5, 10,
            operation="join")
    box(p, c, "tab", -7, 7, 1.2, 6.0, -49, -45.5, operation="join")
    box(p, c, "driver-slot", -2.5, 2.5, 2.2, 5.0, -49.5, -47.0, operation="cut")
    meander(p, c, 1)
    meander(p, c, -1)
    colour(p, c, "#e8812a")


def cover(p):
    c = p.part("cover")
    box(p, c, "body", -35, 35, 40.2, 55.2, -45, 45)
    box(p, c, "nose", -35, 35, 55.0, 62.2, -22.5, 22.5, operation="join")
    box(p, c, "hollow", -33, 33, 39.7, 53.2, -43, 43, operation="cut")
    box(p, c, "nose-hollow", -33, 33, 53.0, 60.2, -20.5, 20.5, operation="cut")
    for i, hz in enumerate(HOOKS_Z):
        for s, sx in (("r", 1), ("l", -1)):
            def xs(a, b):
                return (min(sx * a, sx * b), max(sx * a, sx * b))
            box(p, c, f"hook-arm-{s}{i+1}", *xs(31.0, 32.6), 34.0, 42.0, hz - 4, hz + 4,
                operation="join")
            box(p, c, f"hook-root-{s}{i+1}", *xs(31.0, 33.6), 40.6, 42.0, hz - 4, hz + 4,
                operation="join")
            box(p, c, f"hook-barb-{s}{i+1}", *xs(32.3, 34.4), 34.5, 36.5, hz - 4, hz + 4,
                operation="join")
    box(p, c, "label-recess", -28, 28, 61.7, 62.7, -19, -3, operation="cut")
    for i, lx in enumerate(LED_X):
        cyl_y(p, c, f"pipe-hole{i+1}", 1.6, lx, LED_Z, 59.5, 63.0, operation="cut")
    for i in range(9):
        vx = -24 + 6 * i
        box(p, c, f"vent-top{i+1}", vx - 1, vx + 1, 52.5, 56.0, 27, 40, operation="cut")
        box(p, c, f"vent-bot{i+1}", vx - 1, vx + 1, 52.5, 56.0, -40, -27, operation="cut")
    colour(p, c, "#3d4249")


def label(p):
    c = p.part("front-label")
    box(p, c, "label", -27.8, 27.8, 61.8, 62.1, -18.8, -3.2)
    colour(p, c, "#f2f2ee")


def light_pipe(p):
    c = p.part("light-pipe")
    cyl_y(p, c, "rod", 1.4, 0, 0, 12.6, 62.4)
    cyl_y(p, c, "collar", 2.4, 0, 0, 58.5, 59.8, operation="join")
    colour(p, c, "#cfe8ff")


def pcb(p):
    c = p.part("controller-pcb")
    box(p, c, "board", -32, 32, 10.0, 11.6, -40, 40)
    parts = [  # name, x0, x1, z0, z1, height
        ("mcu", -6, 6, -14, -2, 1.2), ("crystal", 8, 11, -10, -8, 0.9),
        ("inductor", -26, -18, -30, -22, 4.0), ("buck-ic", -15, -11, -29, -25, 1.0),
        ("cap-bulk", -26, -21, -16, -11, 3.0), ("rs485", 10, 16, -30, -24, 1.4),
        ("flash", -16, -10, -8, -3, 1.0), ("ldo", 18, 23, -14, -10, 1.6),
        ("esd", 14, 17, -34, -32, 0.6), ("tvs", -31, -28, -31, -28.5, 1.0)]
    for name, x0, x1, z0, z1, h in parts:
        box(p, c, name, x0, x1, 11.5, 11.6 + h, z0, z1, operation="join")
    for i, lx in enumerate(LED_X):
        box(p, c, f"led{i+1}", lx - 0.8, lx + 0.8, 11.5, 12.2, LED_Z - 0.6, LED_Z + 0.6,
            operation="join")
    for i, (bx, bz) in enumerate(BOSSES):
        cyl_y(p, c, f"hole{i+1}", 1.4, bx, bz, 9.5, 12.0, operation="cut")
    colour(p, c, "#1f6b3c")


def pt_screw(p):
    """Pan-head M2.5 self-tapping screw for plastic, axis -y, head top at y = 0
    (shank at its 2.0 mm core diameter)."""
    c = p.part("screw-pt-m2_5x8")
    cyl_y(p, c, "shank", 1.0, 0, 0, -9.5, -1.6)
    cyl_y(p, c, "head", 2.2, 0, 0, -1.7, 0, operation="join")
    box(p, c, "recess-a", -1.2, 1.2, -0.8, 0.2, -0.3, 0.3, operation="cut")
    box(p, c, "recess-b", -0.3, 0.3, -0.8, 0.2, -1.2, 1.2, operation="cut")
    colour(p, c, "#8c9096")


def header(p):
    """A 4-pole 5.08 mm PCB header for a pluggable terminal block (top edge,
    plug inserted along -z); the bottom one is the same part turned 180 deg about y."""
    c = p.part("tb-header-5_08x4")
    box(p, c, "body", -10.5, 10.5, 11.8, 23.6, 30.0, 38.0)
    box(p, c, "socket", -9.9, 9.9, 12.9, 23.0, 32.8, 38.5, operation="cut")
    for i, px in enumerate(POLES):
        box(p, c, f"pin{i+1}", px - 0.4, px + 0.4, 17.5, 18.3, 32.5, 36.0, operation="join")
    colour(p, c, "#2e7d46")


def plug(p):
    c = p.part("tb-plug-5_08x4")
    box(p, c, "insert", -9.6, 9.6, 13.2, 22.6, 33.2, 38.6)
    box(p, c, "head", -10.3, 10.3, 12.6, 22.6, 38.4, 50.5, operation="join")
    for i, px in enumerate(POLES):
        box(p, c, f"pin-socket{i+1}", px - 0.8, px + 0.8, 17.1, 18.7, 33.0, 36.6,
            operation="cut")
        box(p, c, f"wire-entry{i+1}", px - 1.6, px + 1.6, 14.0, 18.0, 40.5, 51.0,
            operation="cut")
        cyl_y(p, c, f"screw-bore{i+1}", 1.9, px, 45.5, 19.8, 23.0, operation="cut")
        cyl_y(p, c, f"screw-hole{i+1}", 1.4, px, 45.5, 17.5, 19.9, operation="cut")
    colour(p, c, "#3aa05a")


def tb_screw(p):
    """M3 terminal clamp screw, axis -y, head top at y = 0."""
    c = p.part("screw-m3-clamp")
    cyl_y(p, c, "shank", 1.2, 0, 0, -4.2, -1.9)
    cyl_y(p, c, "head", 1.7, 0, 0, -2.0, 0, operation="join")
    box(p, c, "slot", -0.3, 0.3, -0.7, 0.2, -1.9, 1.9, operation="cut")
    colour(p, c, "#c9ccd0")


def usb_c(p):
    c = p.part("usb-c-receptacle")
    stadium_z(p, c, "shell", USB_X, USB_Y, 8.94, 3.26, -42.5, -35.2)
    stadium_z(p, c, "mouth", USB_X, USB_Y, 8.34, 2.66, -43.0, -36.0, operation="cut")
    box(p, c, "tongue", USB_X - 3.3, USB_X + 3.3, USB_Y - 0.3, USB_Y + 0.3, -42.0, -35.5,
        operation="join")
    colour(p, c, "#aeb2b8")


# --------------------------------------------------------------- assembly
def build(p):
    p.run("init", "--unit", "mm")
    for fn in (din_rail, base_housing, latch, cover, label, light_pipe, pcb, pt_screw,
               header, plug, tb_screw, usb_c):
        fn(p)

    a = p.part(ASM, assembly=True)
    p.run("param", "set", ASM, "latch=0 mm")
    ident = dict(origin="0mm,0mm,0mm", z="0,0,1", x="1,0,0")
    turned = dict(z="0,0,-1", x="-1,0,0")   # 180 deg about y

    def inst(iid, part, at=(0, 0, 0), turn=False, **extra):
        pose = dict(ident)
        pose["origin"] = ",".join(f"{v:.6f}mm" for v in at)
        if turn:
            pose.update(turned)
        p.add(a, "instance", iid, of=part, **pose, **extra)

    def mate(on, iid, form="fastened", origin=None, turn=False, **extra):
        off = {}
        if origin:
            off["origin"] = [f"{v:.6f} mm" for v in origin]
        if turn:
            off["rotate"] = "180 deg"
            off["flip"] = True
        p.add(a, "mate", f"{iid}-{form}", form=form, a=f"{ASM}/{on}", a_offset=json.dumps(off),
              b=f"{ASM}/{iid}", b_offset="{}", **extra)

    inst("rail", "din-rail-ts35", fixed=True)
    inst("base", "base-housing")
    mate("rail", "base")
    inst("latch", "din-latch")
    # slides down (-z) when pulled: 0 mm closed .. 7 mm, clamped
    mate("base", "latch", form="slider", distance="0 mm - max(0 mm, min(latch, 7 mm))")
    inst("cover", "cover")
    mate("base", "cover")
    inst("label", "front-label")
    mate("cover", "label")
    for i, lx in enumerate(LED_X):
        iid = f"light-pipe-{i+1}"
        inst(iid, "light-pipe", at=(lx, 0, LED_Z))
        mate("cover", iid, origin=(lx, 0, LED_Z))
    inst("pcb", "controller-pcb")
    mate("base", "pcb")
    for i, (bx, bz) in enumerate(BOSSES):
        iid = f"pcb-screw-{i+1}"
        inst(iid, "screw-pt-m2_5x8", at=(bx, 13.5, bz))
        mate("pcb", iid, origin=(bx, 13.5, bz))
    inst("usb-c", "usb-c-receptacle")
    mate("pcb", "usb-c")
    for s, turn in (("top", False), ("bottom", True)):
        hid, pid = f"header-{s}", f"plug-{s}"
        inst(hid, "tb-header-5_08x4", turn=turn)
        mate("pcb", hid, turn=turn)
        inst(pid, "tb-plug-5_08x4", turn=turn)
        mate(hid, pid)
        for i, px in enumerate(POLES):
            iid = f"tb-screw-{s}-{i+1}"
            at = (-px, 22.3, -45.5) if turn else (px, 22.3, 45.5)
            inst(iid, "screw-m3-clamp", at=at, turn=turn)
            mate(pid, iid, origin=(px, 22.3, 45.5))


main(build)
