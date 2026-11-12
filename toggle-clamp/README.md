# Horizontal hold-down toggle clamp (ryucad 0.9.0-pre.3)

A horizontal hold-down toggle clamp in the manner of a Destaco 225-U, at the size of the
~200 kg holding-capacity class of horizontal clamps, mounted on a fixture plate over a
sample workpiece. Built entirely through the ryucad CLI by `tools/toggle-clamp.py`.
Proportions only follow that class: **no holding force, mass or stiffness was computed.**

![clamped](../hero.png)

## Mechanism
An over-centre four-bar linkage, every pivot parallel to y:

| link | part | pivots |
|---|---|---|
| ground | stamped base (flange + two uprights) | H (handle) and A (arm), 36.4 mm apart, 32 mm above the mounting face |
| crank | handle (U-channel, grip bar, red vinyl grip) | H, crank pin C at 20.8 mm |
| coupler | 2 connecting links, one each side | C to D, 26.7 mm |
| rocker | clamp arm (U-channel) | A, link pin D at 13.0 mm; M8 spindle 75 mm ahead of A |

Clamped (handle = 0 deg) H, C and D sit **3 deg past collinear** (C above the line HD): an
upward push on the spindle compresses the links and drives C further into the lock instead
of opening the clamp. Lifting the handle first pulls the arm 0.4 deg down through centre
(analytic: -0.42 deg at handle 2 deg; solved: -0.29 deg at 5 deg), then swings it open.

Key dimensions (clamped): overall length 257 mm (grip end to arm nose), base footprint
72 x 52 mm with 4 x 6.6 mm holes on 56 x 38 mm centres, spindle axis 111.4 mm ahead of the
handle pivot, spindle tip 12.1 mm above the mounting face (on a 12 mm workpiece, 0.1 mm gap).

| handle (deg) | 0 | 5 | 10 | 20 | 30 | 40 | 50 | 60 |
|---|---|---|---|---|---|---|---|---|
| arm (deg, solved) | 0.00 | -0.29 | 2.56 | 19.32 | 43.90 | 67.23 | 86.84 | 103.36 |

These are ryucad's solved poses; they match the analytic four-bar solution in the
generator (`python3 tools/toggle-clamp.py --kin`).

## Parts (21 BOM lines, 34 occurrences)
- Base (stamped, flange + uprights), clamp arm, handle, handle grip, 2 connecting links
- Pivot pins: A and H (6 mm, through), C and D (5 mm, one per side, left/right hands), each
  headed with an e-clip groove; 2 x 6 mm and 4 x 5 mm E-style retaining clips; 2 spacer
  tubes on pin H
- Spindle: M8 x 35 hex bolt, head down under a neoprene cap, locked through the arm web by
  two ISO 4032 M8 nuts (threads not modelled)
- Mounting: 4 x ISO 4762 M6 x 16 socket head cap screws with ISO 7089 washers into a
  tapped fixture plate; a sample workpiece block (context only)

## Moving it
The assembly parameter `handle` (deg, + opens) drives the handle's revolute on the base;
the arm and both links follow through the closed loop (arm, links: free revolutes).

    ryucad param set toggle-clamp "handle=10 deg"
    ryucad param set toggle-clamp "handle=20 deg"
    ...
    ryucad param set toggle-clamp "handle=60 deg"   # open, arm at 103.4 deg
    ryucad assembly solve toggle-clamp

Step the handle in **10 deg increments or less** (each `param set` solves from the
previous pose and stores it). A four-bar has two assembly branches for every handle angle;
jumping 0 -> 60 deg in one solve can land on the other branch (arm swung down into the
table). If that happens, set `handle=0 deg`, put the arm and links back with
`ryucad assembly move toggle-clamp clamp-arm --origin 0,0,0 --z 0,-1,0 --x 1,0,0` (links:
origin `0,17.55mm,0` / `0,-17.55mm,0`, same axes), and step again. The project is saved
clamped (`handle = 0 deg`).

## Rebuild
    python3 -I tools/toggle-clamp.py $(which ryucad) <empty folder>

## Verified
- `ryucad check`: 0 errors, 0 warnings
- `ryucad interference toggle-clamp`: clamped 68 pairs, open (handle 60 deg) 91 pairs,
  0 interferences at both (pins run in holes with 0.1 mm radial clearance)
- `ryucad assembly solve toggle-clamp`: converges, 0 DOF, no conflicting mates at handle 0
  and 60 deg (state "over": the second link closes a redundant parallel loop, as expected)
- `ryucad bom`, STEP AP242 export (`../toggle-clamp.step`)

## Not verified / simplifications
- No holding force, handle force, mass or stiffness computed; the "200 kg class" is a size
  reference, not a rating
- Clearance checked at the clamped and open poses only, not swept through the full travel
- No handle stop is modelled: the over-centre lock relies on the geometry alone here
- Threads (spindle, M6 holes) not modelled; the base is one solid, not a bent sheet with
  bend radii; curved outlines are polylines (96 segments per circle)
- The workpiece is touched at 0.1 mm gap; rubber compression is not modelled
