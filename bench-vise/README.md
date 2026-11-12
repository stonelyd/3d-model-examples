# 100 mm (4") machinist's milling vise — ryucad 0.9.0-pre.3

A screw-driven milling vise of the classic layout: a cast body with a guided
way, a fixed jaw cast in, a moving jaw riding the way on gib strips with a
hold-down plate under the lips, and a lead screw journalled in the body's end
wall between two axial ball thrust bearings, turned by a crank handle. The
nut is bolted under the moving jaw, so the screw turns in place and the jaw
travels. Built entirely through the ryucad CLI by `tools/bench-vise.py`.

## Key specs (as modelled)
- Jaw width 100 mm, jaw plates 100 x 32 x 10 mm (hardened, ground), 2 x M6 SHCS each in counterbores
- Opening 0–100 mm (assembly parameter `opening`, clamped in the mate expressions)
- Lead screw: 20 mm Acme-style, 4 mm lead (thread drawn as stacked trapezoidal rings, 16 mm minor), 16 mm journal
- Thrust: two axial ball thrust bearings 16 x 28 mm (shaft washer, housing washer, 12 x 2.4 mm balls in a cage), one each side of the end wall, plus a locking collar
- Way: 48 mm slot between the lips, 40 mm tongue with a 3.9 mm gib strip each side, hold-down plate 72 mm wide under the lips, bronze nut bolted through it with 4 x M6
- Body 270 x 110 mm (170 mm over the mounting ears), 108 mm to the jaw tops; screw axis 33 mm above the table
- Mounting: 18 mm keyway underneath with two tenon keys (M6 each); four open slots for M12 T-bolts with washers
- Crank handle: 117 mm throw, 22 mm grip

## Parts (25 BOM lines, 42 occurrences)
Make: body, moving-jaw, fixed- and moving-jaw-plate, gib-strip a/b, clamp-plate,
lead-nut, lead-screw, thrust-collar, handle, handle-grip, tenon-key (x2).
Buy: 2 thrust bearings (as 6 parts: washers and ball cages), M6x20 (4), M6x40 (4),
M6x12 (2), M3x40 (4), M12x40 hex bolts (4), M12 washers (4). See `ryucad bom vise --flat`.

## Moving it
    ryucad param set vise "opening=35 mm"
    ryucad assembly solve vise

`opening` drives the nut's slider mate (clamped to 0–100 mm). The lead screw's
revolute is driven from the same parameter at 360° per 4 mm lead (turning the
crank clockwise seen from the handle end closes the jaws), and the thrust-bearing
cages turn at half the screw's angle. The jaw, plate, gibs, clamp plate and their
screws are fastened to the nut; collar, handle, grip and shaft washers to the
screw; everything else to the body (fixed). Screws are fastened through
connectors on their tapped holes' cylindrical faces. The project is saved at
opening = 80 mm; a fresh build from the script is at 20 mm.

## Rebuild
    python3 -I tools/bench-vise.py $(which ryucad) <empty folder>

## Verified (ryucad 0.9.0-pre.3)
- `ryucad check`: 0 errors, 0 warnings
- `ryucad interference vise`: 93 pairs checked, 0 interferences, 0 touching, 0 unchecked — at opening 20 mm and at 80 mm
- `assembly solve`: converges, state well, 0 dof, at 20 mm and 80 mm (also tried 2 mm, i.e. screw at 180°, 37 mm, and 150 mm, which clamps to 100 mm)
- `ryucad bom vise`, STEP AP242 export

## Not verified / simplifications
- The thread is stacked rings, not a helix, and the nut bore is plain (clears the 20 mm major diameter); the screw–nut coupling is by parameter expression, not geometric contact. ryucad has no screw/gear mate.
- Thrust bearings are simplified (flat washers, balls clear of them by 0.1 mm), not catalogue geometry.
- Clearances of 0.1 mm are drawn at the way, gibs and bearings; no fits/tolerances are specified.
- The 117 mm crank sweeps below the table plane (axis 33 mm up): in use the handle is repositioned, or the vise end overhangs the table. Not checked over a full turn for collisions with a table or neighbouring parts.
- No mass, clamping force or screw torque has been computed; no materials are assigned.
- Bolts for the T-slots are plain hex bolts standing in for T-bolts; the table itself is not modelled.
