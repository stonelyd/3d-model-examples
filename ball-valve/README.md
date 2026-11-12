# 1" two-piece full-port ball valve (ryucad 0.9.0-pre.3)

A DN25 quarter-turn ball valve in the common two-piece form: a body with a hex
end and stem neck, and an end piece (insert) screwed into it that traps the ball
between two PTFE seats. Both ends are female 1" NPT-style ports. Built entirely
through the ryucad CLI by `tools/ball-valve.py`.

16 occurrences, 14 BOM lines. `ryucad check`: 0 errors, 0 warnings.
`ryucad interference ball-valve`: 32 pairs, 0 interferences, open and closed.

## Key dimensions (as modelled)
- Full port: 25.0 mm bore through ends, seats and ball
- Face to face 92 mm; body and end-piece hexes 46 mm across flats; barrel Ø62 mm
- Female ends: drawn at the 1" NPT minor diameter (Ø30.4 mm) with six stacked
  grooves at 2.209 mm pitch (11.5 TPI) and a thread relief, 17 mm deep.
  Not helical and not tapered.
- Ball Ø42 mm with a 4.4 mm stem slot; seats are PTFE rings with a conical lip,
  ID 27 mm, OD 40 mm. Modelled 0.16 mm off the ball (real seats are preloaded)
- Stem Ø10 mm, 7 mm double-D flats for the handle, Ø16 mm blow-out-proof
  shoulder inside the body with a PTFE thrust washer under the neck
- Stem seal: two PTFE packing rings, a gland follower, and a hex packing nut
  (26 mm AF) on the neck
- Lever 125 mm from the stem axis, with a vinyl grip, two stop tabs and a
  14 mm AF handle nut. A stop pin pressed into a lug on the body limits travel to 90°

## Parts
body, end-piece, body-seal, seat ×2, ball, stem, thrust-washer, packing-ring ×2,
gland, packing-nut, handle, grip, handle-nut, stop-pin.

The frame: flow along x, stem along z, ball centre at the origin. The body is
fixed. The stem turns on a revolute mate about z. Ball, handle, grip and handle
nut are fastened to the stem, and everything else is fastened to the body.

## Moving it
The assembly parameter `valve` drives the stem revolute: 0 deg is open (bore
along the flow) and 90 deg is closed.

    ryucad param set ball-valve "valve=90 deg"
    ryucad assembly solve ball-valve

At each end of travel, one handle tab sits 0.19 mm from the stop pin (measured
with `ryucad clearance ball-valve --instance stop-pin`). The mate itself does not
enforce the stop: angles beyond 0 to 90 deg solve and make the tab run through
the pin.

## Rebuild from scratch
    python3 -I tools/ball-valve.py $(which ryucad) <empty folder>

## Verified
- `ryucad check`: 0 errors, 0 warnings
- `ryucad interference ball-valve`: 32 pairs, 0 interferences at valve = 0 deg and 90 deg
- `ryucad assembly solve ball-valve`: converged, state well, 0 dof at 0 deg and 90 deg
- `ryucad bom ball-valve`: 14 lines (seat and packing-ring qty 2)
- STEP AP242 export of the assembly

## Not verified / simplifications
- No pressure, temperature, flow coefficient (Cv), torque or mass was computed
  or is claimed. No materials file, so there is no mass.
- Threads are grooves, not helices or NPT taper. The body and insert joint is a
  plain bore and spigot with 0.15 mm radial clearance.
- Seat preload and seal compression are not modelled (all seals have small gaps).
- The handle stop is geometric only and is not a mate limit.
