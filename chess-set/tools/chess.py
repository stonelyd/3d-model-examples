"""A Staunton-style chess set, built through ryucad's CLI only.

Six piece types as revolved lathe profiles (sketch in the zx plane,
revolved about the axis segment), plus block/cone/sphere work for the
rook's battlements, the bishop's mitre cut, the queen's coronet, the
king's cross and the knight's head. The board is one part of 65
solids (base + 64 separate square solids, coloured per solid); the
pieces are coloured per assembly occurrence, ivory against ebony.
"""

import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from model import main, polar  # noqa: E402

Z = (0, 0, 1)
X = (1, 0, 0)
Y = (0, 1, 0)
SQ = 42.0  # square size, mm


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


def revolve(p, part, profile):
    """profile: [(h, r), ...] from (0, 0) up the outside to (H, 0)."""
    sk = p.sketch(part, polygon(profile), fid="profile", plane="zx")
    p.add(part, "revolve", "body", sketch=sk,
          axis=f"l{len(profile)}", angle="full")


def pawn(p):
    g = p.part("pawn")
    revolve(p, g, [(0, 0), (0, 11), (1.5, 11), (3, 10.6), (4.5, 8.8),
                   (6, 8.2), (7.5, 8.6), (9, 7.2), (12, 6.2), (16, 5.8),
                   (19, 6.0), (20.5, 7.8), (22, 8.6), (23.5, 8.2),
                   (24.5, 6.4), (26, 6.8), (28, 7.3), (30, 6.2),
                   (31.2, 4.2), (32, 0)])


def rook(p):
    g = p.part("rook")
    revolve(p, g, [(0, 0), (0, 12.5), (1.5, 12.5), (3, 12), (4.5, 10),
                   (6, 9.3), (7.5, 9.8), (9, 8.2), (13, 7.2), (18, 6.8),
                   (22, 7.0), (23.5, 9.2), (25, 10), (26.5, 9.4),
                   (27.5, 10.8), (29, 11.8), (38, 11.8), (38, 0)])
    # Battlements: two crossed slots leave four merlons.
    p.block(g, "slot-a", (27, 6.5, 10), (0, 0, 36), Z, X, operation="cut")
    p.block(g, "slot-b", (27, 6.5, 10), (0, 0, 36), Z, Y, operation="cut")


def knight(p):
    g = p.part("knight")
    revolve(p, g, [(0, 0), (0, 12.5), (1.5, 12.5), (3, 12), (4.5, 10),
                   (6, 9.3), (7.5, 9.8), (9, 8.4), (12, 7.6), (16, 7.2),
                   (19, 7.6), (20.5, 9.6), (22, 10.2), (23.5, 9.8),
                   (23.5, 0)])
    # The head is a horse-head silhouette (y forward, z up) drawn in a
    # yz sketch and extruded across x: muzzle, face, ears, mane curve.
    silhouette = [(6, 20), (10, 30), (13, 33), (11.5, 37), (8.5, 42),
                  (6, 47), (4.5, 51.5), (2.5, 47.5), (0.5, 51), (-1.5, 46.5),
                  (-5, 42), (-6.5, 36), (-7, 29), (-6.5, 22), (-6, 19)]
    sk = p.sketch(g, polygon(silhouette), fid="bust",
                  place=((-5.5, 0, 0), X, Y))
    p.add(g, "extrude", "head", sketch=sk, length="11 mm", operation="join")
    # Eyes: one through-hole reads as an eye on both cheeks.
    p.add(g, "cylinder", "eyes", {"radius": 1.1, "height": 13},
          ((-6.5, 5.5, 41), X, Z), operation="cut")


def bishop(p):
    g = p.part("bishop")
    revolve(p, g, [(0, 0), (0, 13), (1.5, 13), (3, 12.5), (4.5, 10.4),
                   (6, 9.6), (7.5, 10.1), (9, 8.4), (14, 7.2), (20, 6.6),
                   (26, 6.4), (29, 6.8), (30.5, 9.4), (32, 10.2),
                   (33.5, 9.2), (34.5, 7.6), (36, 8.8), (38.5, 9.6),
                   (41, 9.2), (43.5, 7.6), (45.5, 5.2), (46.8, 3.4),
                   (47.6, 3.9), (48.6, 2.4), (49.5, 0)])
    # The mitre: a diagonal slot across the bulb, offset forward so
    # the tip stays attached at the back.
    p.block(g, "mitre", (26, 5, 17), (0, 3, 42), (0, 0.574, 0.819), X,
            operation="cut")


def queen(p):
    g = p.part("queen")
    revolve(p, g, [(0, 0), (0, 14), (1.5, 14), (3, 13.4), (4.5, 11.2),
                   (6, 10.3), (7.5, 10.9), (9, 9.0), (15, 7.6), (22, 7.0),
                   (29, 6.8), (33, 7.2), (34.5, 10.0), (36, 10.8),
                   (37.5, 9.6), (39, 8.2), (42, 8.6), (45, 10.4),
                   (47, 11.2), (48.5, 10.6), (49.5, 9.2), (50, 0)])
    for k in range(8):
        p.add(g, "cone", f"point-{k + 1}", {"radius": 1.8, "height": 5.5},
              (polar(7.2, 45 * k, 49.5), Z, X), operation="join")
    p.add(g, "sphere", "finial", {"radius": 3.6}, ((0, 0, 52), Z, X),
          operation="join")


def king(p):
    g = p.part("king")
    revolve(p, g, [(0, 0), (0, 15), (1.5, 15), (3, 14.4), (4.5, 12),
                   (6, 11), (7.5, 11.7), (9, 9.6), (16, 8.2), (24, 7.5),
                   (31, 7.3), (36, 7.8), (37.5, 10.6), (39, 11.4),
                   (40.5, 10.2), (42, 8.8), (45, 9.2), (48, 10.8),
                   (50.5, 11.6), (52, 10.8), (53, 9.4), (54, 0)])
    p.block(g, "cross-v", (3.6, 3.6, 11), (0, 0, 58.5), Z, X,
            operation="join")
    p.block(g, "cross-h", (10.5, 3.6, 3.6), (0, 0, 60), Z, X,
            operation="join")


def board(p):
    b = p.part("board")
    p.block(b, "base", (392, 392, 16), (0, 0, -8), Z, X)
    for f in range(8):
        for r in range(8):
            p.block(b, f"sq-{chr(97 + f)}{r + 1}", (SQ, SQ, 3),
                    ((f - 3.5) * SQ, (r - 3.5) * SQ, 1.5), Z, X)
    return b


FILES = "abcdefgh"
BACK = ["rook", "knight", "bishop", "queen", "king",
        "bishop", "knight", "rook"]


def assembly(p):
    a = p.part("chess-set", assembly=True)
    p.add(a, "instance", "board", of="board", fixed=True)
    placed = []
    for side, home, pawn_rank in (("white", 0, 1), ("black", 7, 6)):
        for f in range(8):
            x = (f - 3.5) * SQ
            for piece, rank in ((BACK[f], home), ("pawn", pawn_rank)):
                sq = f"{FILES[f]}{rank + 1}"
                iid = f"{side}-{piece}-{sq}"
                kw = {}
                if piece == "knight":
                    # Knights face the other army.
                    kw = {"z": "0,0,1",
                          "x": "1,0,0" if side == "white" else "-1,0,0"}
                p.add(a, "instance", iid, of=piece,
                      origin=f"{x:.1f}mm,{(rank - 3.5) * SQ:.1f}mm,3mm",
                      fixed=True, **kw)
                placed.append((iid, side))
    return a, placed


def finish(p, placed):
    p.run("materials", "set", "boxwood", "--density", "670 kg/m^3",
          "--colour", "#e9dcbc", "--default")
    p.run("materials", "set", "walnut", "--density", "640 kg/m^3",
          "--colour", "#6e452a")
    for part in ["pawn", "rook", "knight", "bishop", "queen", "king"]:
        p.run("props", "set", part, "material=boxwood")
    p.run("props", "set", "board", "material=walnut")
    # Board colours per solid: base mahogany, squares maple/walnut.
    p.run("colour", "board/base", "--colour", "#4a2c1a")
    for f in range(8):
        for r in range(8):
            c = "#e8d5b5" if (f + r) % 2 else "#7a4a2b"
            p.run("colour", f"board/sq-{FILES[f]}{r + 1}", "--colour", c)
    # Pieces coloured per occurrence: ivory against ebony.
    for iid, side in placed:
        p.run("colour", f"chess-set/{iid}", "--colour",
              "#f2ead8" if side == "white" else "#26221f")
    steps = []
    for rank_z, side in ((70, "white"), (150, "black")):
        ids = [i for i, s in placed if s == side]
        steps.append('{"instances": [%s], "translate": [0, 0, "%d mm"]}'
                     % (", ".join(f'"{i}"' for i in ids), rank_z))
    p.run("explode", "save", "chess-set", "lift",
          "--steps", "[" + ", ".join(steps) + "]")


def build(p):
    p.run("init", "--unit", "mm")
    pawn(p)
    rook(p)
    knight(p)
    bishop(p)
    queen(p)
    king(p)
    board(p)
    _, placed = assembly(p)
    finish(p, placed)


main(build)
