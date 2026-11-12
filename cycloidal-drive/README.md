# Cycloidal drive, 11:1, 90 mm

A compact single-stage cycloidal reducer for a robot joint, modelled in ryucad
through its CLI only (`tools/cycloidal-drive.py` writes the whole project).

## Key specs (as modelled)
- Reduction **11:1**, output turns opposite to input: 12 ring pins, two 11-lobe discs.
- Envelope: housing Ø90 mm; 54.5 mm from the end cover's face to the output
  flange's face, plus a 16 mm long Ø9.9 input stub with a flat.
- Ring pins Ø4 on a Ø70 pin circle, rollers Ø6.5.
- Eccentricity e = 1.2 mm; discs 6 mm thick, 180° out of phase on two cams.
- Disc profile: epitrochoid offset by roller radius + 0.15 mm backlash clearance,
  as a 264-segment polyline (11 lobes x 24); disc tip/root radius 32.8 / 30.4 mm.
- Six output pins Ø5 on a Ø42 circle with Ø7 rollers; disc holes Ø10
  (roller Ø + 2e + 0.6 mm).
- Bearings: 2x 6800 (10x19x5) input, 2x 6802 (15x24x5) eccentric,
  2x 6808 (40x52x7) main output. Each is inner ring, outer ring and caged balls.
- Output flange Ø60 with 6x M4 bolt circle Ø48 and a Ø16 pilot.

## Parts (22 BOM lines, 80 occurrences)
housing, end cover, input shaft (two cams), cycloid disc x2, output carrier
(plate + hub), carrier ring, output flange, ring pin x12 + roller x12,
output pin x6 + roller x6, 6800/6802/6808 bearings x2 each (inner, outer,
balls), M3x10 x12 (cover, flange), M3x8 x6 (carrier ring into output pins).

## Motion
Assembly `cycloidal-drive` parameters:
- `input` – input shaft angle (revolute housing → shaft).
- `output = -input / 11` – output carrier angle (revolute housing → carrier).
- `disc = -input * 12 / 11` – each disc's turn on its cam's eccentric axis
  (revolute shaft → disc), so its absolute turn equals the output's.

ryucad has no gear-ratio mate: the 11:1 relation lives in these parameter
expressions and the geometry; the solver does not enforce it. Rollers and
ball cages sit on free revolutes.

```
ryucad param set cycloidal-drive "input=132 deg"
ryucad assembly solve cycloidal-drive
ryucad interference cycloidal-drive
```

## Rebuild
```
python3 -I tools/cycloidal-drive.py $(which ryucad) <empty folder>
python3 tools/prof.py   # checks the polyline disc against the pins at several input angles
```
(ryucad v0.9.0-pre.3; `model.py` is ryucad's corpus helper.)

## Verified
- `ryucad check`: 0 errors, 0 warnings; `check-format` clean.
- `ryucad interference`: 0 interferences, 0 touching, at input 0° (304 pairs),
  75° (337 pairs) and 132° (353 pairs).
- `assembly solve` converges at input 0°, 75° and 132° (output 0°, -6.82°, -12°).
- `tools/prof.py`: polyline disc-to-roller clearance 0.13–0.16 mm at input 0°, 37°, 132°, 200°.
- STEP AP242 export.

## Not verified
- Torque, stiffness, efficiency, lost motion, mass, bearing life: not computed.
- The reduction is not solver-enforced (parameter expressions only).
- Tolerances/fits are nominal CAD gaps (0.05–0.5 mm), not a fit analysis.
- Threads are plain holes; no seals, retaining rings or lubrication.
- Assembly sequence is plausible but not simulated.
