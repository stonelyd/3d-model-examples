"""A Staunton-style chess set as a ryucad assembly, through the CLI only:
six pieces turned from lathe profiles (revolves) with their details
joined and cut, a knight's head extruded from a side silhouette, a board
of 64 square solids, and an assembly placing all 32 pieces, coloured
ivory and ebony by occurrence."""
import math, os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, "/workspace/work/ryucad/crates/ryucad/tests/corpus")
from model import main

Z = (0, 0, 1); X = (1, 0, 0); Y = (0, 1, 0)
SQ = 50.0                       # square size, mm
IVORY, EBONY = "#efe4cc", "#2b2522"
LIGHT, DARK = "#d9b98c", "#7a4e2d"


def polygon(points):
    ops = []
    for i, (a, b) in enumerate(points):
        ops.append({"op": "add", "type": "point", "id": f"p{i+1}", "at": [f"{a} mm", f"{b} mm"]})
    n = len(points)
    for i in range(n):
        ops.append({"op": "add", "type": "line", "id": f"l{i+1}", "start": f"p{i+1}",
                    "end": f"p{(i+1) % n + 1}"})
    return ops


def turned(p, part, profile):
    """Revolve a (height, radius) profile about z; its last line is the axis."""
    pts = [(0, 0)] + profile + [(profile[-1][0], 0)]
    sk = p.sketch(part, polygon(pts), fid="profile", plane="zx")
    p.add(part, "revolve", "body", sketch=sk, axis=f"l{len(pts)}", angle="full")


BASE = [(0, 17), (3, 17), (4.5, 15.5), (6.5, 15.5), (8, 13)]


def pawn(p):
    c = p.part("pawn")
    turned(p, c, BASE + [(10, 11), (24, 6), (26, 9.5), (28, 9.5), (29, 5.5), (33, 5.5)])
    p.add(c, "sphere", "head", {"radius": 9}, ((0, 0, 40), Z, X), operation="join")


def rook(p):
    c = p.part("rook")
    turned(p, c, BASE + [(10, 12), (36, 10), (38, 13), (50, 13)])
    p.add(c, "cylinder", "well", {"radius": 8, "height": 6}, ((0, 0, 46), Z, X), operation="cut")
    for k in range(4):
        a = k * 45
        d = (math.cos(math.radians(a)), math.sin(math.radians(a)), 0)
        p.block(c, f"crenel-{k+1}", (30, 4.5, 5), (0, 0, 48), Z, d, operation="cut")


def knight(p):
    c = p.part("knight")
    turned(p, c, BASE + [(10, 12), (14, 11.5), (15, 9)])
    # side silhouette of the head, (z, x) in the zx plane; nose toward +x
    head = [(14, -11), (14, 9), (22, 11), (30, 15), (40, 19), (46, 18), (49, 12),
            (47, 8), (50, 5), (56, 2), (58, -2), (55, -6), (50, -9), (40, -11),
            (28, -12), (20, -12)]
    sk = p.sketch(c, polygon(head), fid="head-profile", plane="zx")
    p.add(c, "extrude", "head", sketch=sk, length="16 mm", extent="symmetric",
          operation="join")
    p.add(c, "cylinder", "eye-l", {"radius": 1.6, "height": 30}, ((3, -15, 48), Y, X),
          operation="cut")


def bishop(p):
    c = p.part("bishop")
    turned(p, c, BASE + [(10, 11.5), (32, 6), (34, 10), (36, 10), (37, 6), (40, 6),
                         (44, 9), (50, 8.5), (55, 5.5), (59, 2)])
    p.add(c, "sphere", "finial", {"radius": 3}, ((0, 0, 60.5), Z, X), operation="join")
    # the mitre's slit
    p.block(c, "slit", (14, 2.2, 9), (6, 0, 51), (0.6, 0, 0.8), (0.8, 0, -0.6),
            operation="cut")


def queen(p):
    c = p.part("queen")
    turned(p, c, BASE + [(10, 13), (40, 7), (42, 11), (44, 11), (45, 7.5), (49, 7.5),
                         (60, 12), (64, 12)])
    p.add(c, "cylinder", "cup", {"radius": 9, "height": 6}, ((0, 0, 60), Z, X), operation="cut")
    for k in range(8):
        a = math.radians(k * 45)
        p.add(c, "sphere", f"notch-{k+1}", {"radius": 3.6},
              ((12.5 * math.cos(a), 12.5 * math.sin(a), 64), Z, X), operation="cut")
    p.add(c, "sphere", "orb", {"radius": 5}, ((0, 0, 63), Z, X), operation="join")


def king(p):
    c = p.part("king")
    turned(p, c, BASE + [(10, 13.5), (44, 7.5), (46, 11.5), (48, 11.5), (49, 8),
                         (53, 8), (64, 11), (66, 11), (68, 6)])
    p.block(c, "cross-v", (4.5, 4.5, 16), (0, 0, 75), Z, X, operation="join")
    p.block(c, "cross-h", (13, 4.5, 4.5), (0, 0, 77), Z, X, operation="join")


def board(p):
    c = p.part("board")
    p.block(c, "frame", (8 * SQ + 40, 8 * SQ + 40, 10), (0, 0, -9), Z, X)
    for f in range(8):
        for r in range(8):
            fid = f"sq-{'abcdefgh'[f]}{r+1}"
            p.block(c, fid, (SQ, SQ, 4), (centre(f), centre(r), -2), Z, X)


def centre(i):
    return (i - 3.5) * SQ


def colour_board(p):
    p.run("colour", "board/frame", "--colour", "#4a2f1c")
    light = [f"board/sq-{'abcdefgh'[f]}{r+1}" for f in range(8) for r in range(8) if (f + r) % 2]
    dark = [f"board/sq-{'abcdefgh'[f]}{r+1}" for f in range(8) for r in range(8) if not (f + r) % 2]
    p.run("colour", *light, "--colour", LIGHT)
    p.run("colour", *dark, "--colour", DARK)


BACK = ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]


def chess(p):
    a = p.part("chess", assembly=True)
    p.add(a, "instance", "board", of="board", fixed=True)
    white, black = [], []
    for side, rank_back, rank_pawn, face, out in (
            ("w", 0, 1, (0, 1, 0), white), ("b", 7, 6, (0, -1, 0), black)):
        for f, kind in enumerate(BACK):
            iid = f"{side}-{kind}-{'abcdefgh'[f]}"
            p.add(a, "instance", iid, of=kind, fixed=True,
                  origin=f"{centre(f)}mm,{centre(rank_back)}mm,0mm",
                  z="0,0,1", x=",".join(str(v) for v in face))
            out.append(f"chess/{iid}")
        for f in range(8):
            iid = f"{side}-pawn-{'abcdefgh'[f]}"
            p.add(a, "instance", iid, of="pawn", fixed=True,
                  origin=f"{centre(f)}mm,{centre(rank_pawn)}mm,0mm")
            out.append(f"chess/{iid}")
    p.run("colour", *white, "--colour", IVORY)
    p.run("colour", *black, "--colour", EBONY)


def build(p):
    p.run("init", "--unit", "mm")
    for make in (pawn, rook, knight, bishop, queen, king, board):
        make(p)
    colour_board(p)
    chess(p)


if __name__ == "__main__":
    main(build)
