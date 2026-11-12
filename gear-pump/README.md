# External spur-gear hydraulic pump, Group-1 size (ryucad 0.9.0-pre.3)

A two-gear external pump of the common "Group 1" class: a pair of 12-tooth
spur gears in a figure-8 cavity, a split body with front (mounting) and
rear covers, sleeve-bushed shafts, a keyed drive shaft with a lip seal.
Built entirely through the ryucad CLI by `tools/gear-pump.py`.

30 occurrences, 17 BOM lines. `ryucad check`: 0 errors, 0 warnings.
`ryucad interference gear-pump`: 84 pairs at theta = 0 deg and 82 pairs at
theta = 10 deg, 0 interferences, 0 unchecked.

## Key specs (as modelled)
- Gears: module 2, 12 teeth, 20 deg pressure angle, 24 mm pitch diameter,
  27.6 mm tip diameter (addendum shortened), 18.8 mm root diameter, 18 mm
  face width, 24 mm centre distance, 0.25 mm design backlash. Involute
  flanks are polylines (6 points per flank from the base circle) with a
  radial flank below the base circle, because the connector takes no splines.
- Geometric displacement, textbook estimate 2*pi*m^2*z*b: about 5.4 cm^3/rev.
  (A geometric estimate only; no flow, pressure or efficiency is claimed.)
- Cavity: two 28 mm bores (0.2 mm radial tip clearance), 0.1 mm end float
  each side between the gears and the covers.
- Ports: inlet 13 mm bore on +x, outlet 10 mm bore on -x, with straight
  port adapters and bonded seals (threads not modelled). With this porting
  the drive turns clockwise seen from the shaft end (theta increasing).
- Shafts 14 mm in four 14x16x10 sleeve bushings (PAP 1410 type), two per
  cover; drive shaft 14 mm with a 5x5x20 parallel key; 14x24x7 lip seal in
  the front cover's 32 mm pilot.
- Covers located by four 5x12 dowel pins, sealed by two O-rings
  (about 56 x 3, modelled squeezed in face grooves), clamped by four M8x45
  socket head cap screws with washers from the rear cover into tapped holes
  in the front cover. Front cover: 104 x 92 mm 4-hole mounting flange,
  9 mm holes.
- Envelope: body 64 x 80 x 18.2 mm; about 97 mm from shaft end to screw
  heads.

## Parts (BOM summary)
Made: body, front cover, rear cover, drive gear with integral shaft, idler
gear, idler shaft. Bought: 4 bushings, lip seal, 2 O-rings, key, 4 dowel
pins, 4 M8 washers, 4 M8x45 SHCS, 2 port adapters, 2 bonded seals.
`ryucad bom gear-pump` gives the full list with descriptions.

## Moving it
The assembly parameter `theta` drives the drive gear's revolute mate. The
idler's revolute is driven by the expression `15 deg - theta` (equal gears
turning opposite ways, half a tooth out of phase), so the pair stays in
mesh for any theta:

    ryucad param set gear-pump "theta=10 deg"
    ryucad assembly solve gear-pump

ryucad has no gear-ratio mate: the coupling is geometric (two driven
revolutes sharing one parameter), not a solved gear constraint. The
project is saved at theta = 10 deg; a fresh build from the script is at
theta = 0 deg.

## Rebuilding
    python3 -I tools/gear-pump.py $(which ryucad) <empty folder outside any Git repo>

`tools/model.py` is the corpus helper the script drives the CLI through.
`tools/mesh_check.py` (optional, needs `shapely`) checks the 2D gear
outlines over one tooth pitch: no overlap, smallest gap 0.117 mm.

## Verified
- `ryucad check`: 0 errors, 0 warnings; `check-format` clean.
- `ryucad interference gear-pump` at theta = 0 deg (84 pairs) and 10 deg
  (82 pairs): 0 interferences, 0 unchecked.
- `ryucad assembly solve gear-pump` converges ("well", 0 dof) at both poses.
- 2D mesh clearance of the gear outlines over a full tooth pitch (script above).
- STEP AP242 export of the assembly.

## Not verified / simplified
- No flow, pressure rating, volumetric efficiency, torque or mass computed
  (no materials assigned).
- Tooth profile is a polyline approximation, not true involute; the root
  below the base circle is a straight radial flank, not a generated undercut
  trochoid; no profile shift.
- No trapped-volume relief grooves, no pressure-balanced bushing blocks.
- Threads (ports, tapped holes, screws) not modelled; tapped holes are at
  the screw's major diameter; bonded seals and adapters are simplified.
- The lip seal is a simple lip section without garter spring; O-rings are
  modelled already squeezed.
- Interference was checked at two poses, not swept through a full turn in 3D
  (the full-pitch sweep is the 2D check only).
