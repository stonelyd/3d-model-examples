"""An ISO 15552-style tie-rod pneumatic cylinder, 32 mm bore, 100 mm stroke,
as a ryucad assembly built through the CLI only.

    python3 -I tools/pneumatic-cylinder.py <ryucad> <empty folder>

Every part is modelled in place in the cylinder's own frame: the axis is z,
z = 0 the rear face of the rear end cap, the rod pointing to +z, the ports
on the +x face and the cushion screws on the +y face. Moving parts are drawn
at stroke 0 (retracted) and slide on one slider mate driven by the
assembly parameter `stroke` (clamped to 0..100 mm).

Parts:
  barrel tube (32 bore x 38 OD), rear and front end caps (45 square, G1/8
  port bores with feed passages, cushion bores, cushion needle screws),
  four M6 tie rods with front nuts, piston (rear cushion spear, two U-cup
  seals, wear band, magnet ring), 12 mm piston rod (M8 piston spigot,
  front cushion collar, M10x1.25 thread) with jam nut, rod seal, bronze
  rod bushing and wiper in the front cap, an ISO 15552 rear double-clevis
  mount on four M6 socket screws with its 10 mm pin and two circlips, and
  an ISO 8140-style rod-end clevis with its 10 mm pin and two circlips.
Threads are drawn at their nominal or minor diameter, not modelled.
"""
import json
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import main  # noqa: E402

A = "pneumatic-cylinder"
Z = (0, 0, 1)
X = (1, 0, 0)
Y = (0, 1, 0)
TG = 32.5 / 2          # tie-rod / mounting-screw square, half pitch
SQ = 45.0              # end cap square


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


def rev_y(p, part, fid, prof, zc=0.0, **flags):
    """Revolve a closed (y, r) profile about a line along y at x = 0, z = zc."""
    ys = [a for a, _ in prof]
    pts = [(r, y) for y, r in prof]
    ops = pts_lines(pts)
    ops += [{"op": "add", "type": "point", "id": "ax1", "at": ["0 mm", f"{min(ys)-1:.6f} mm"]},
            {"op": "add", "type": "point", "id": "ax2", "at": ["0 mm", f"{max(ys)+1:.6f} mm"]},
            {"op": "add", "type": "line", "id": "axis", "start": "ax1", "end": "ax2"}]
    sk = p.sketch(part, ops, fid=f"{fid}-profile", place=((0, 0, zc), Z, X))
    return p.add(part, "revolve", fid, sketch=sk, axis="axis", angle="full", **flags)


def ring(r0, r1, z0, z1):
    return [(z0, r0), (z1, r0), (z1, r1), (z0, r1)]


def ucup(z_heel, z_lip, r_in, r_out):
    """A U-cup seal section, lips toward z_lip."""
    h = r_out - r_in
    zm = z_lip + 0.45 * (z_heel - z_lip)
    return [(z_heel, r_in), (z_heel, r_out), (z_lip, r_out), (z_lip, r_out - 0.3 * h),
            (zm, (r_in + r_out) / 2), (z_lip, r_in + 0.3 * h), (z_lip, r_in)]


def cyl(p, part, fid, r, z0, z1, at=(0, 0), **flags):
    return p.add(part, "cylinder", fid, {"radius": f"{r:.6f}", "height": f"{z1-z0:.6f}"},
                 ((at[0], at[1], z0), Z, X), **flags)


def cyl_dir(p, part, fid, r, origin, d, length, **flags):
    """A cylinder of radius r from `origin` along unit direction d."""
    x = Z if abs(d[2]) < 0.9 else X
    return p.add(part, "cylinder", fid, {"radius": f"{r:.6f}", "height": f"{length:.6f}"},
                 (origin, d, x), **flags)


def hexagon(af):
    rc = af / math.sqrt(3)
    return [(rc * math.cos(math.radians(60 * i + 30)), rc * math.sin(math.radians(60 * i + 30)))
            for i in range(6)]


def hex_prism(p, part, fid, af, z0, z1, at=(0, 0), **flags):
    pts = [(at[0] + u, at[1] + v) for u, v in hexagon(af)]
    sk = p.sketch(part, pts_lines(pts), fid=f"{fid}-profile", place=((0, 0, z0), Z, X))
    return p.add(part, "extrude", fid, sketch=sk, length=f"{z1-z0:.6f} mm", **flags)


def colour(p, part, c):
    p.run("colour", part, "--colour", c)


ALU, ALU_DARK, STEEL, CHROME = "#c9cdd3", "#8d96a1", "#9ea3aa", "#e4e7eb"
RUBBER, BLACK, BRONZE = "#25272b", "#1b1c1f", "#b48a4a"


# ----------------------------------------------------------------- parts
def tie_rod_corners():
    return [(TG, TG), (-TG, TG), (-TG, -TG), (TG, -TG)]


def end_cap_common(p, c, z0, z1, port_z, cush_z, port_into):
    """Square cap body z0..z1, four tie-rod holes, a G1/8 port on +x and a
    cushion-screw bore on +y."""
    p.block(c, "body", (SQ, SQ, z1 - z0), (0, 0, (z0 + z1) / 2), Z, X)
    for i, (x, y) in enumerate(tie_rod_corners()):
        cyl(p, c, f"tie-hole-{i+1}", 3.0 if z0 < 1 else 3.2, z0 - 1, z1 + 1, at=(x, y),
            operation="cut", target="body")
    # G1/8 port: tap-drill bore 8.8 mm, 11 mm deep, then a 4 mm feed passage
    cyl_dir(p, c, "port", 4.4, (12.0, 0, port_z), X, SQ / 2 + 1 - 12.0, operation="cut",
            target="body")
    cyl_dir(p, c, "port-feed", 2.0, (port_into, 0, port_z), X, 12.5 - port_into,
            operation="cut", target="body")
    # cushion needle bore: counterbore for the head, then the needle bore
    cyl_dir(p, c, "cushion-cbore", 3.6, (0, SQ / 2 + 1, cush_z), (0, -1, 0), 4.0,
            operation="cut", target="body")
    return c


def rear_cap(p):
    c = p.part("rear-cap")
    end_cap_common(p, c, 0, 24, 14, 20, 0)
    cyl(p, c, "spigot", 15.9, 23.5, 29, operation="join", target="body")
    rev(p, c, "cushion-bore", [(8, 0), (8, 7.2), (30, 7.2), (30, 0)], operation="cut",
        target="body")
    cyl_dir(p, c, "cushion-needle-bore", 2.55, (0, 20, 20), (0, -1, 0), 13.5,
            operation="cut", target="body")
    colour(p, c, ALU)


def front_cap(p):
    c = p.part("front-cap")
    end_cap_common(p, c, 162, 194, 168, 168, 6)
    cyl(p, c, "spigot", 15.9, 157, 162.5, operation="join", target="body")
    cyl(p, c, "boss", 15.0, 193.5, 197, operation="join", target="body")
    rev(p, c, "bore", [(156, 0), (156, 8.2), (174, 8.2), (174, 6.5), (175, 6.5), (175, 10),
                       (179, 10), (179, 9), (189, 9), (189, 6.5), (190, 6.5), (190, 10.5),
                       (198, 10.5), (198, 0)], operation="cut", target="body")
    cyl_dir(p, c, "cushion-needle-bore", 2.55, (0, 20, 168), (0, -1, 0), 12.5,
            operation="cut", target="body")
    colour(p, c, ALU)


def barrel(p):
    c = p.part("barrel")
    rev(p, c, "tube", ring(16.0, 19.0, 24, 162))
    colour(p, c, "#b9c3cf")


def tie_rod(p):
    c = p.part("tie-rod")
    cyl(p, c, "rod", 2.9, 6, 201, at=(TG, TG))
    colour(p, c, STEEL)


def tie_nut(p):
    c = p.part("nut-m6")
    hex_prism(p, c, "hex", 10, 194, 199, at=(TG, TG))
    cyl(p, c, "bore", 3.0, 193, 200, at=(TG, TG), operation="cut", target="hex")
    colour(p, c, "#b0b5bb")


def cushion_screw(p):
    c = p.part("cushion-screw")
    rev_y(p, c, "screw", [(8.0, 0), (8.0, 2.0), (8.5, 2.5), (19.7, 2.5), (19.7, 3.4),
                          (22.2, 3.4), (22.2, 0)], zc=20)
    p.block(c, "slot", (8, 2.4, 0.8), (0, 22.2, 20), Z, X, operation="cut", target="screw")
    colour(p, c, "#3a3d42")


def piston(p):
    c = p.part("piston")
    rev(p, c, "body", [(21, 4.05), (21, 6.0), (21.5, 6.5), (30, 6.5), (30, 15.6), (32, 15.6),
                       (32, 11.5), (37, 11.5), (37, 15.6), (39, 15.6), (39, 12.5), (42, 12.5),
                       (42, 14.5), (48, 14.5), (48, 15.6), (49, 15.6), (49, 11.5), (54, 11.5),
                       (54, 15.6), (56, 15.6), (56, 4.05)])
    colour(p, c, ALU_DARK)


def piston_seal(p):
    c = p.part("piston-seal")
    rev(p, c, "seal", ucup(36.95, 32.05, 11.55, 15.95))
    colour(p, c, RUBBER)


def wear_band(p):
    c = p.part("wear-band")
    rev(p, c, "band", ring(14.55, 15.95, 42.05, 47.95))
    colour(p, c, "#e9e3cf")


def magnet(p):
    c = p.part("magnet-ring")
    rev(p, c, "ring", ring(12.55, 14.9, 39.05, 41.95))
    colour(p, c, "#5d6670")


def rod(p):
    c = p.part("piston-rod")
    rev(p, c, "rod", [(22, 0), (22, 3.5), (22.5, 4.0), (56, 4.0), (56, 7.6), (65.5, 7.6),
                      (66, 6.0), (220, 6.0), (220, 5.0), (241.5, 5.0), (242, 4.5), (242, 0)])
    colour(p, c, CHROME)


def rod_seal(p):
    c = p.part("rod-seal")
    rev(p, c, "seal", ucup(178.95, 175.05, 6.05, 9.95))
    colour(p, c, RUBBER)


def bushing(p):
    c = p.part("rod-bushing")
    rev(p, c, "bush", ring(6.05, 8.98, 179.05, 188.95))
    colour(p, c, BRONZE)


def wiper(p):
    c = p.part("rod-wiper")
    rev(p, c, "wiper", [(190.5, 7.2), (190.5, 10.45), (196.8, 10.45), (196.8, 8.4),
                        (195.6, 8.0), (196.8, 6.02), (195.4, 6.02), (193.0, 7.2)])
    colour(p, c, RUBBER)


def rod_nut(p):
    c = p.part("nut-m10x1-25")
    hex_prism(p, c, "hex", 17, 223, 229)
    cyl(p, c, "bore", 5.05, 222, 230, operation="cut", target="hex")
    colour(p, c, "#b0b5bb")


def eye_profile(z_start, z_pin, r_end, half_w):
    """A fork or lug outline in (x, -z) sketch coordinates: a rectangle from
    z_start to the pin and a half-circle (polyline) round the pin."""
    pts = [(half_w, -z_start), (half_w, -z_pin)]
    n = 12
    sign = 1 if z_pin > z_start else -1
    for i in range(1, n):
        a = math.pi * i / n
        x = half_w * math.cos(a)
        z = z_pin + sign * r_end * math.sin(a)
        pts.append((x, -z))
    pts += [(-half_w, -z_pin), (-half_w, -z_start)]
    return pts


def rod_clevis(p):
    c = p.part("rod-clevis")
    cyl(p, c, "shank", 9.0, 230, 252)
    sk = p.sketch(c, pts_lines(eye_profile(251, 270, 10, 10)), fid="fork-profile",
                  place=((0, -10, 0), Y, X))
    p.add(c, "extrude", "fork", sketch=sk, length="20 mm", operation="join", target="shank")
    p.block(c, "slot", (24, 10.5, 30), (0, 0, 271), Z, X, operation="cut", target="shank")
    cyl_dir(p, c, "pin-hole", 5.1, (0, -11, 270), Y, 22, operation="cut", target="shank")
    cyl(p, c, "thread-bore", 5.05, 228, 246, operation="cut", target="shank")
    colour(p, c, "#aab0b7")


def rear_mount(p):
    c = p.part("rear-clevis-mount")
    p.block(c, "plate", (SQ, SQ, 10), (0, 0, -5), Z, X)
    for i, y0 in enumerate((13, -19)):
        sk = p.sketch(c, pts_lines(eye_profile(-9.5, -24, 10, 10)), fid=f"lug-{i+1}-profile",
                      place=((0, y0, 0), Y, X))
        p.add(c, "extrude", f"lug-{i+1}", sketch=sk, length="6 mm", operation="join",
              target="plate")
    cyl_dir(p, c, "pin-hole", 5.1, (0, -20, -24), Y, 40, operation="cut", target="plate")
    for i, (x, y) in enumerate(tie_rod_corners()):
        cyl(p, c, f"screw-hole-{i+1}", 3.2, -11, 1, at=(x, y), operation="cut", target="plate")
        cyl(p, c, f"screw-cbore-{i+1}", 5.5, -11, -4, at=(x, y), operation="cut", target="plate")
    colour(p, c, "#9aa1aa")


def mount_screw(p):
    c = p.part("screw-m6x14")
    rev(p, c, "screw", [(5.0, 0), (5.0, 2.4), (4.6, 2.9), (-4.0, 2.9), (-4.0, 5.0),
                        (-10.0, 5.0), (-10.0, 0)])
    # hexagon socket, 5 mm across flats, from the head's end
    pts = hexagon(5.0)
    sk = p.sketch(c, pts_lines(pts), fid="socket-profile", place=((0, 0, -10.5), Z, X))
    p.add(c, "extrude", "socket", sketch=sk, length="4 mm", operation="cut", target="screw")
    colour(p, c, BLACK)


def pin(p, name, half, clip_y):
    c = p.part(name)
    g0, g1 = clip_y - 0.6, clip_y + 0.6    # clip groove
    prof = [(-half, 0), (-half, 4.6), (-half + 0.4, 5.0), (-g1, 5.0), (-g1, 4.3), (-g0, 4.3),
            (-g0, 5.0), (g0, 5.0), (g0, 4.3), (g1, 4.3), (g1, 5.0), (half - 0.4, 5.0),
            (half, 4.6), (half, 0)]
    rev_y(p, c, "pin", prof)
    colour(p, c, "#c7ccd2")


def clip(p):
    c = p.part("circlip-10")
    rev_y(p, c, "ring", [(-0.5, 4.35), (0.5, 4.35), (0.5, 7.6), (-0.5, 7.6)])
    p.block(c, "gap", (5, 2, 3), (6.0, 0, 0), Z, X, operation="cut", target="ring")
    colour(p, c, "#2f3338")


# -------------------------------------------------------------- assembly
def j(v):
    return json.dumps(v)


def off(x=0.0, y=0.0, z=0.0, flip=False):
    o = {"origin": [f"{x:.6f} mm", f"{y:.6f} mm", f"{z:.6f} mm"]}
    if flip:
        o["flip"] = True
    return o


def assembly(p):
    a = p.part(A, assembly=True)
    p.run("param", "set", A, "stroke=10 mm")

    def inst(iid, part, at=(0, 0, 0), z=Z, x=X, **kw):
        p.add(a, "instance", iid, of=part,
              origin=",".join(f"{c:.6f}mm" for c in at),
              z=",".join(f"{c:.6f}" for c in z), x=",".join(f"{c:.6f}" for c in x), **kw)

    def fasten(to, iid, offset=None):
        p.add(a, "mate", f"{iid}-fastened", form="fastened", a=f"{A}/{to}",
              a_offset=j(offset) if offset else "{}", b=f"{A}/{iid}", b_offset="{}")

    inst("barrel", "barrel", fixed=True)
    # the static body
    for iid, part in (("rear-cap", "rear-cap"), ("front-cap", "front-cap"),
                      ("rear-clevis-mount", "rear-clevis-mount"), ("rod-seal", "rod-seal"),
                      ("rod-bushing", "rod-bushing"), ("rod-wiper", "rod-wiper")):
        inst(iid, part)
        fasten("barrel" if "cap" in iid else
               ("rear-cap" if iid == "rear-clevis-mount" else "front-cap"), iid)
    inst("cushion-screw-rear", "cushion-screw")
    fasten("rear-cap", "cushion-screw-rear")
    inst("cushion-screw-front", "cushion-screw", at=(0, 0, 148))
    fasten("front-cap", "cushion-screw-front", off(z=148))
    for iid, part, to in (("tie-rod", "tie-rod", "rear-cap"), ("tie-nut", "nut-m6", "front-cap"),
                          ("mount-screw", "screw-m6x14", "rear-clevis-mount")):
        if iid == "mount-screw":
            inst(iid, part, at=(TG, TG, 0))
            fasten(to, iid, off(TG, TG, 0))
        else:
            inst(iid, part)
            fasten(to, iid)
        p.add(a, "instance_pattern", f"{iid}s", instance=iid, form="circular",
              axis=f"{A}/barrel", count="4", angle="360deg")
    inst("rear-pin", "pin-10x45", at=(0, 0, -24))
    fasten("rear-clevis-mount", "rear-pin", off(z=-24))
    for s, y in (("a", 20.0), ("b", -20.0)):
        inst(f"rear-clip-{s}", "circlip-10", at=(0, y, -24))
        fasten("rear-pin", f"rear-clip-{s}", off(y=y))

    # the moving group: the rod slides; everything on it is fastened to it
    inst("piston-rod", "piston-rod")
    p.add(a, "mate", "stroke-slider", form="slider", a=f"{A}/barrel", a_offset="{}",
          b=f"{A}/piston-rod", b_offset="{}", distance="max(0 mm, min(stroke, 100 mm))")
    for iid, part in (("piston", "piston"), ("piston-seal-rear", "piston-seal"),
                      ("wear-band", "wear-band"), ("magnet-ring", "magnet-ring"),
                      ("rod-nut", "nut-m10x1-25"), ("rod-clevis", "rod-clevis")):
        inst(iid, part)
        fasten("piston" if iid.startswith(("piston-seal", "wear", "magnet")) else "piston-rod",
               iid)
    inst("piston-seal-front", "piston-seal", at=(0, 0, 86), z=(0, 0, -1), x=X)
    fasten("piston", "piston-seal-front", off(z=86, flip=True))
    inst("rod-pin", "pin-10x25", at=(0, 0, 270))
    fasten("rod-clevis", "rod-pin", off(z=270))
    for s, y in (("a", 11.0), ("b", -11.0)):
        inst(f"rod-clip-{s}", "circlip-10", at=(0, y, 270))
        fasten("rod-pin", f"rod-clip-{s}", off(y=y))


def build(p):
    p.run("init", "--unit", "mm")
    barrel(p)
    rear_cap(p)
    front_cap(p)
    tie_rod(p)
    tie_nut(p)
    cushion_screw(p)
    piston(p)
    piston_seal(p)
    wear_band(p)
    magnet(p)
    rod(p)
    rod_seal(p)
    bushing(p)
    wiper(p)
    rod_nut(p)
    rod_clevis(p)
    rear_mount(p)
    mount_screw(p)
    pin(p, "pin-10x45", 22.5, 20.0)
    pin(p, "pin-10x25", 12.5, 11.0)
    clip(p)
    assembly(p)


main(build)
