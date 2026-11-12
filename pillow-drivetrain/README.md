# Pillow-block drive line (ryucad 0.9.0-pre.3)

A small industrial power-transmission line: a foot-mounted motor drives a 25 mm line shaft
through a jaw coupling; the shaft runs in two UCP205-style pillow blocks and carries a
single-groove SPA V-belt pulley on its output end. Everything sits on a fabricated steel base.
Built entirely through the ryucad CLI by `tools/pillow-drivetrain.py`.

63 occurrences, 30 BOM lines. `ryucad check`: 0 errors, 0 warnings.
`ryucad interference drive`: 0 interferences at shaft = 0 deg (143 pairs), 35 deg (163 pairs) and 120 deg (165 pairs).

## Key specs (as modelled)
- Shaft centre height 80 mm above the base top (IEC 80 frame shaft height; pillow blocks on 44 mm riser pads).
- Motor: IEC 80 B3-style, simplified. Foot holes A = 125 mm across, B = 100 mm along, 9 mm; finned
  frame Ø150 mm, end shields, fan + cowl, terminal box with cable gland; shaft extension Ø19 x 40 mm, key 6 x 6.
- Jaw coupling, L-100 style: Ø64 mm hubs, bores 19 mm (6 mm keyway) and 25 mm (8 mm keyway), one M6 set screw each;
  three jaws per hub, six-leg elastomer spider.
- Line shaft Ø25 x 360 mm, keyways 8 x 4 at the coupling and pulley ends, keys 8 x 7.
- Pillow blocks UCP205-style: centre height 36.5 mm, overall height 71 mm, base 140 x 38 mm,
  bolt slots 13 x 19 mm at 105 mm centres, grease nipple; spacing 180 mm.
- UC205-style insert: Ø52 mm spherical outer ring, extended inner ring (bore 25 mm, width 34.1 mm) with two M6
  set screws at 120 deg, nine Ø7.94 mm (5/16 in) balls in a cage on a Ø39.5 mm pitch circle, two seals.
- Two Ø42 x 16 mm set-screw shaft collars between the bearings.
- Pulley SPA, 1 groove: Ø140 mm pitch, Ø145.5 mm outside, 38 deg groove, five-hole web, Ø50 x 40 mm hub, keyed + set screw.
- Fasteners: 4 x M8x40 hex bolts, 8 M8 washers, 4 M8 nuts (motor, through slotted base); 4 x M12x40 hex bolts with
  M12 washers into tapped riser holes (pillow blocks).

## Parts list summary
base · motor-frame, motor-de-shield, motor-nde-shield, fan-cowl, terminal-box, cable-gland, motor-rotor ·
jaw-hub-a, jaw-hub-b, jaw-spider · line-shaft, key-6x6x28, key-8x7x26, key-8x7x30, shaft-collar-25 (2) ·
ucp205-housing (2), uc205-outer-ring (2), uc205-inner-ring (2), uc205-balls (2), uc205-seals (2), grease-nipple-m6 (2) ·
pulley-spa-140 · set-screw-m6x8 (5), set-screw-m6x5 (4), hex-bolt-m12x40 (4), washer-m12 (4), hex-bolt-m8x40 (4),
washer-m8 (8), hex-nut-m8 (4). Full list: `ryucad bom drive --flat`.

## Moving it
The assembly `drive` has one parameter, `shaft`, the drive-line angle. The motor rotor and the line shaft each
turn on a revolute driven by `shaft`; hubs, spider, keys, collars, inner rings, pulley and their set screws are
fastened to them. Each ball set turns on a revolute driven by `shaft * 0.4` (cage speed (1 - d/Dpw)/2 for this
geometry). The model is saved at shaft = 35 deg.

    ryucad param set drive "shaft=120 deg"
    ryucad assembly solve drive

## Rebuild from scratch
    python3 -I tools/pillow-drivetrain.py $(which ryucad) <empty folder>

(builds at shaft = 0 deg; `tools/model.py` is the corpus helper it imports).

## Verified
- `ryucad check`: 0 errors, 0 warnings.
- `ryucad interference drive`: 0 interferences at 0, 35 and 120 deg.
- `assembly solve` converges, state well, 0 dof, 0 redundant/conflicting mates, at 35 deg and 120 deg.
- STEP AP242 export of the assembly.

## Not verified / simplifications
- No load, speed, torque, power, belt tension, bearing life or mass figures were computed; no material densities are set.
- Motor is an envelope model: no stator windings or internal bearings; the rotor shaft runs through clearance bores in the end shields.
- Threads are not modelled (tapped holes and nuts are plain bores); bolt slots, spider and keys have nominal clearances.
- The spider is fastened to hub A; in reality it floats between the jaws. Ball/cage speed is a kinematic ratio only.
- The insert's spherical OD is a faceted revolve sitting in a cylindrical housing bore (no misalignment freedom modelled);
  raceway grooves are polygonal approximations of an arc.
- Dimensions follow typical catalogue values for IEC 80, L-100, UCP205/UC205 and SPA, but are not taken from one maker's drawing.
