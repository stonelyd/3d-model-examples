# Lead-screw linear stage, 200 mm travel (ryucad 0.9.0-pre.3)

A NEMA 17 driven linear actuator stage of the common "two rods + T8 screw" kind:
a stepper on an L bracket turns a T8 lead screw through a beam coupling; the screw
is held axially at the motor end by a back-to-back pair of 608 bearings between
two shaft collars and floats in one 608 at the far end. A carriage rides on two
Ø8 hardened rods in four LM8UU linear ball bushings and is pushed by an
anti-backlash brass flange nut sunk into it. Two slotted optical end-stops and
four rubber bumpers mark the ends of travel. Built entirely through the ryucad
CLI by `tools/linear-stage.py`.

78 occurrences of 34 parts (34 BOM lines). `ryucad check`: 0 errors, 0 warnings.
`ryucad interference linear-stage`: 156 pairs, 0 interferences at travel 30 mm
and 170 mm (also 0 interferences at the 0 mm and 200 mm ends).

## Key dimensions (as modelled)
- Travel 200 mm (carriage front face 30 mm to 230 mm from the motor-end block's
  bearing seat, i.e. X = 30..230 mm in the assembly frame)
- Base: 10 mm aluminium plate 120 x 370 mm, four counterbored M5 mounting holes,
  every other screw in a tapped hole in the plate
- Lead screw: T8, Ø8 mm major, lead 8 mm (4 starts x 2 mm pitch), 337 mm long,
  screw axis 28 mm above the plate. Thread drawn as revolved 2 mm-pitch
  trapezoid rings (crest Ø7.9, root Ø6.2), not a helix
- Motor: NEMA 17, 42.3 mm square, 40 mm body, Ø22 pilot, Ø5 shaft with a flat,
  4 x M3 x 10 into the front cap through a 6 mm L bracket (2 x M4 x 12 into the plate)
- Coupling: beam style Ø20 x 25, 5 mm / 8 mm bores, an M3 set-screw hole per hub;
  the helical beam is drawn as three ring slots
- Bearings: 608 (8 x 22 x 7), grooved races, 7 balls Ø3.8 in a cage. Fixed end:
  two, clamped by shaft collars on both sides; floating end: one
- Guide: two Ø8 x 306 mm rods at ±35 mm, four slit rod clamps (M3 clamp screw,
  2 x M4 x 30 counterbored each)
- Carriage: 96 x 56 x 28 mm aluminium block, four LM8UU (Ø15 x 24, retaining-ring
  grooves), 4 x M4 tapped holes on top
- Nut: T8 brass flange nut (flange Ø26, 4 x M2.5 x 8), preload spring and brass
  follower nut inside a Ø15.2 pocket in the carriage; nut bore 0.15 mm off the
  screw's crests
- End stops: rubber bumpers on both bearing blocks, 2 mm off the carriage at
  travel 0 and 200. Limits: TCST2103-size slotted optical switches on small PCBs;
  carriage vanes sit in the slots (0.8 mm each side) at travel 0 and 200

## Parts
base-plate, motor-bracket, nema17 front cap / stator / rear cap / connector,
motor-shaft, beam-coupling-5x8, lead-screw-t8, shaft-collar-8 x2,
fixed-bearing-block, floating-bearing-block, 608 inner ring / outer ring /
balls-and-cage x3 each, guide-rod-8x306 x2, rod-clamp x4, carriage,
lm8uu-bushing x4, t8-flange-nut, anti-backlash-spring, anti-backlash-follower,
optical-endstop x2, endstop-pcb x2, endstop-flag x2, rubber-bumper x4, and
socket head cap screws: M2.5x8 x4, M3x6 x2, M3x8 x4, M3x10 x4, M3x20 x4,
M4x12 x2, M4x30 x8, M4x50 x4. (Screw parts carry a suffix -v / -y / -yn: the
same screw modelled along another axis, see below.)

## Frames and mates
Every part is modelled in the stage frame (z along the screw axis, x up), and
every instance places that frame with z on world X and x on world Z, so the screw
runs along world X and the plate lies in world XY. Mates use part-origin
connectors with origin/flip offsets; because offsets cannot turn z onto another
axis, screws that point up/down or sideways are separate parts modelled along that
axis.

- base-plate fixed; everything static fastened to it (directly or via the bracket,
  blocks, clamps and PCBs)
- carriage: **slider** on the base, `distance = max(0 mm, min(travel, 200 mm))`;
  bushings, nut, spring, follower, nut screws, flags and their screws fastened to it
- lead-screw: **revolute** on the base, `angle = -360 deg / 8 mm * travel`
  (clamped the same way): the right-hand 8 mm lead, so screw angle and carriage
  position stay consistent. Motor shaft, coupling, collars and the three bearing
  inner rings are fastened to the screw
- each bearing's ball cage: revolute on the base at 0.37 x the screw angle (cage
  speed for a fixed outer ring, ½(1 − d/Dpw))

The screw-to-nut coupling exists only through the shared parameter; ryucad has no
screw/gear-ratio mate and the nut's thread does not engage the screw geometrically.

## Moving it
    ryucad param set linear-stage "travel=170 mm"
    ryucad assembly solve linear-stage

Values outside 0..200 mm are clamped by the mate expressions. Saved at travel = 30 mm.

## Rebuild from scratch
    python3 -I tools/linear-stage.py $(which ryucad) <empty folder>

(`tools/model.py` is the corpus helper the script drives the CLI with.)

## Verified
- `ryucad check`: 0 errors, 0 warnings
- `ryucad interference linear-stage`: 156 pairs, 0 interferences, 0 unchecked at
  travel = 30 mm and 170 mm; 157 / 155 pairs, 0 interferences at 0 mm / 200 mm
- `ryucad assembly solve linear-stage`: converged, state well, 0 dof at 30 mm
  (carriage at X = 60 mm) and 170 mm (carriage at X = 200 mm)
- `ryucad clearance`: bumpers 2 mm from the carriage at travel 0 and 200; vanes
  0.8 mm from the switch slot walls there; screw crests 0.15 mm from the nut bore
- `ryucad bom linear-stage`: 34 lines
- STEP AP242 export of the assembly

## Not verified / simplifications
- No load capacity, thrust, speed, stiffness, accuracy, torque or mass was
  computed or is claimed. No materials file, so there is no mass.
- Lead-screw and nut threads are rings, not helices; the nut bore is plain.
- The coupling's helical beam is drawn as ring slots; set screws are holes only
  (no set screws modelled). Bearing shields, the motor's internals and the
  switches' wiring are not modelled.
- Bearing seats, bearing bores and the bushings' outer diameters are
  line-to-line (contact), not press fits; the bushings run 0.05 mm off the rods
  (no balls modelled inside them). Spring preload is not modelled (the spring sits
  with 0.5 mm gaps).
- End stops and limit switches are geometric only: the slider is limited by the
  clamp in its expression, not by contact.
