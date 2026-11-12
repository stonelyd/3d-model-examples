# NEMA 17 planetary gearbox, 5:1 (ryucad 0.9.0-pre.3)

A single-stage planetary reducer that bolts to the face of a NEMA 17 stepper: the motor's
5 mm D-shaft drives a sun gear, three planets on needle bearings roll inside a fixed ring
gear, and the planet carrier carries an 8 mm output shaft on two 608 ball bearings. Built
entirely through the ryucad CLI by `tools/planetary-gearbox.py`.

39 occurrences, 18 BOM lines. `ryucad check`: 0 errors, 0 warnings.
`ryucad interference gearbox`: 0 interferences at both poses (109 pairs checked at out = 0 deg,
123 pairs at out = 36 deg).

## Key specs
- Ratio 5:1 exactly (i = 1 + Z_ring / Z_sun = 1 + 48/12); sun and carrier turn the same way.
- Gearing: module 1, 25 deg pressure angle (a 12-tooth sun with no undercut), sun 12T, planets
  18T x 3 (equally spaced: (12 + 48) / 3 = 20), ring 48T internal, centre distance 15 mm.
- Tooth flanks are true involutes sampled as polylines (8 segments a flank, radial below the
  base circle, flat roots and tips); each flank thinned 0.06 mm at the pitch circle for
  backlash. In a 2D check of the same profiles the closest tooth-to-tooth gap was about
  0.11 mm at carrier angles 0, 7, 13.3, 36 and 90 deg.
- Face width 8 mm (planets), 8.5 mm (sun).
- Housing: 64 mm OD, 40.5 mm from the motor face to the output cover. Output shaft 8 mm with a
  0.5 mm D-flat, 17.5 mm beyond the cover. Overall length with a 40 mm motor: 98 mm.
- Mounting: 32 mm output spigot, 4 x M3 tapped on a 44 mm PCD in the output cover.
- Motor interface: 22 mm pilot recess, 4 x M3 x 6 counterbored on the 31 mm square pattern.

## Parts (summary, see `ryucad bom gearbox`)
- Made: input plate, sun gear (12T, D bore, M3 set-screw hub), planet gear (x3), planet
  carrier with integral output shaft, ring-gear housing (48T), output cover.
- Bought / standard: NEMA 17 stepper (envelope: 42.3 mm square body with chamfered corners,
  22 mm pilot, tapped M3 holes, connector) and its 5 mm D-shaft; 3 x dowel pin 4 x 13;
  3 x drawn-cup needle bearing in the HK0408 envelope (4 x 8 x 8: cup, 11 rollers in a cage);
  3 x thrust washer; 2 x 608 deep-groove ball bearing (inner ring, outer ring, 7 balls with a
  cage, races grooved by a polygon, no torus); 4 x M3 x 6 and 6 x M3 x 25 socket head cap
  screws; 1 x M3 x 3 set screw on the shaft's flat.

## Moving it
The assembly parameter `out` is the output (carrier) angle. ryucad has no gear mate, so the
gear train's kinematics are written as parameter expressions instead of being solved from
tooth contact:

- `sun = out * 5` drives the motor shaft's revolute (the sun is fastened to the shaft),
- `planet = out * -8 / 3` drives each planet's revolute on the carrier (spin relative to the
  carrier: -Z_ring / Z_planet),

so at any `out` the teeth stay in mesh. The needle-roller sets and the 608 ball sets are free
revolutes (5 DOF left, reported as `under` by the solver).

    ryucad param set gearbox "out=36 deg"
    ryucad assembly solve gearbox

The project is saved at out = 36 deg (sun 180 deg, planets -96 deg relative to the carrier).

## Rebuild from scratch
    python3 -I tools/planetary-gearbox.py $(which ryucad) <empty folder>

(`tools/model.py` is ryucad's corpus helper, copied beside the script.)

## Verified
- `ryucad check`: 0 errors, 0 warnings.
- `ryucad interference gearbox`: 0 interferences at out = 0 deg (109 pairs) and at
  out = 36 deg (123 pairs); no touching pairs reported.
- `ryucad assembly solve gearbox` converges at out = 0 deg and out = 36 deg (no redundant or
  conflicting mates); poses checked: carrier 36 deg, sun 180 deg, planets at -60 deg absolute.
- `ryucad bom gearbox`: 18 lines, 39 occurrences.
- STEP AP242 export of the assembly.

## Not verified / simplified
- Gear coupling is imposed by parameter expressions, not a gear mate or contact solve.
- 3D interference was run at two poses only; other angles were checked in 2D on the tooth
  profiles only.
- No tooth strength, torque, efficiency, backlash tolerance stack or mass is computed or claimed.
- Involutes are polylines with no root fillet or tip relief; threads are not modelled (M3
  screws are 2.9 mm cylinders in 3.0 mm tapped holes); the motor is an envelope with no
  internals; bearing internals are simplified.
- The outer 608 has no axial retainer (circlip or seal) and there is no shaft seal; the sun's
  set screw has no access hole once the housing is assembled (it is tightened before the
  ring goes on).
