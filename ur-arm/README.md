# UR-style 6-axis arm (ryucad 0.9.0-pre.3)

UR5e-class layout: about 850 mm reach (425 mm upper arm, 392 mm forearm), 5 kg-class.
343 occurrences, 101 BOM lines. `ryucad check`: 0 errors, 0 warnings. `ryucad interference arm`: 1,703 pairs, 0 interferences.

## Joints (sizes l: J1-J2, m: J3, s: J4-J6)
Each joint is a full drive stack, every part its own solid and mated:
- frameless BLDC: 12-slot stator with tooth shoes, 12 windings, rotor, 14-pole magnet ring
- two deep-groove rotor bearings (races, balls, cages)
- strain-wave gear 80:1: oval wave generator + thin bearing, 160-tooth flexspline, 162-tooth circular spline
- crossed-roller output bearing (36 rollers), output flange
- brake: slotted disk, solenoid, locking pin (slider mate, parameter `brake`)
- encoders: motor-side slotted disc + readhead on PCB; output-side magnet ring + head
- M3/M4 socket-head screws as circular instance patterns

## Moving it
Joint angles are assembly parameters `j1`..`j6` driving the output revolute mates:

    ryucad param set arm "j2=50 deg" "j3=-95 deg"
    ryucad assembly solve arm

Rotors, ball sets and roller sets are free revolutes (ryucad has no gear-ratio mate yet), so the 80:1 coupling is geometric, not solved.

## Rebuild from scratch
    python3 -I tools/arm.py $(which ryucad) <empty folder>
