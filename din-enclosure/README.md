# 4-module DIN-rail controller enclosure (ryucad 0.9.0-pre.3)

A 70 mm wide (4 x 17.5 mm modules) DIN-rail enclosure for a custom controller
PCB, laid out for injection moulding: 2 mm walls, 1.2 mm ribs (60 % of wall),
screw bosses with gussets, cantilever snap hooks, and a separate sprung latch
slider. It is shown clipped onto a 35 x 7.5 mm top-hat rail section. Built
entirely through the ryucad CLI by `tools/din-enclosure.py`.

27 occurrences, 12 BOM lines. `ryucad check`: 0 errors, 0 warnings.
`ryucad interference din-enclosure`: 0 interferences with the latch closed
(54 pairs) and pulled open (53 pairs).

## Frame
x along the rail (module width), z up the cabinet (the latch slides along z),
y out of the cabinet. The rail's flange faces are at y = 0; the housing's back
sits 0.3 mm off them.

## Key dimensions (as modelled)
- Envelope 70 (W) x 90 (H) x 62.2 mm (D from the rail face); front nose 45 mm
  high (DIN 43880 style); base housing depth 40 mm, cover 22 mm
- Walls 2.0 mm; back-wall ribs 1.2 x 5 mm (two vertical, one horizontal)
- Rail: TS35 x 7.5, 1 mm steel, 100 mm section, four 15 x 5.2 mm slots at 25 mm pitch
- Rail clip: fixed hook (lead-in chamfer) behind the top flange; latch nose
  (lead-in chamfer) behind the bottom flange, 0.3 mm off the flange back face
- Latch: 14 x 1.6 mm slider plate in a T-slot track (0.2 mm running clearance),
  screwdriver tab with 5 mm slot, two moulded meander spring legs (0.6 mm bars)
  in pockets in the latch boss. Travel 6 mm opens it: the nose then clears the
  flange by 3.5 mm (ryucad clearance)
- Cover: four cantilever snap hooks (1.6 mm arms, 1.8 mm barbs) into windows
  in the base side walls; 56 x 16 mm label recess 0.5 mm deep with label;
  four Ø3.2 mm light-pipe holes; 2 x 13 mm vent slots, 9 per shoulder
- PCB 64 x 80 x 1.6 mm on four Ø6 mm bosses (Ø2.2 mm pilot holes, gussets),
  Ø2.8 mm board holes, four pan-head M2.5 x 8 self-tapping (PT-style) screws
- Two pluggable 4-pole 5.08 mm terminal blocks, top and bottom PCB edges:
  header with pins + screw plug (wire entries 3.2 x 4 mm, M3 clamp screws in
  front-facing bores), plugs pass through 21.6 x 11.1 mm wall windows
- USB-C receptacle (8.94 x 3.26 mm shell, tongue) at the bottom edge behind a
  9.6 x 3.9 mm slot in the bottom wall
- Four Ø2.8 mm light pipes with retaining collars over four PCB LEDs

## Parts (BOM)
din-rail-ts35, base-housing, din-latch, cover, front-label, light-pipe x4,
controller-pcb, screw-pt-m2_5x8 x4, usb-c-receptacle, tb-header-5_08x4 x2,
tb-plug-5_08x4 x2, screw-m3-clamp x8.

The rail is fixed; the base is fastened to it. The latch slides on one slider
mate against the base. Cover, PCB and everything on the PCB are fastened; the
bottom header and plug are the top ones turned 180 deg about y.

## Moving it
The assembly parameter `latch` drives the slider: 0 mm closed (on the rail),
6 mm pulled open. The mate's distance is `0 mm - max(0 mm, min(latch, 7 mm))`,
so it is clamped to 0..7 mm and moves the latch down (-z).

    ryucad param set din-enclosure "latch=6 mm"
    ryucad assembly solve din-enclosure

## Rebuild from scratch
    python3 -I tools/din-enclosure.py $(which ryucad) <empty folder>

## Verified
- `ryucad check`: 0 errors, 0 warnings
- `ryucad interference din-enclosure`: 0 interferences at latch = 0 mm (54 pairs)
  and 6 mm (53 pairs), nothing touching, nothing unchecked
- `ryucad assembly solve din-enclosure`: converged, state well, 0 dof at both poses
- `ryucad clearance --instance latch`: 0.3 mm to the rail closed, 3.5 mm open;
  0.2 mm to the housing track at both
- `ryucad bom din-enclosure`: 12 lines
- STEP AP242 export of the assembly

## Not verified / simplifications
- No mass, material, latch force, spring rate, snap-fit strain, IP rating or
  thermal performance was computed or is claimed. No materials file.
- The meander spring legs are drawn undeflected; they do not touch the housing
  in either pose, so spring preload/return is not modelled. The slider is
  clamped by the expression, not by a physical stop.
- Snap hooks, screws and parts on the PCB sit with 0.2-0.5 mm gaps rather than
  in contact; self-tapping screw shanks are drawn at the 2.0 mm core diameter
  and have no threads; terminal clamp screws have no threads.
- No draft angles, fillets or gate/ejector features; a "moulding-ready" layout
  (uniform walls, ribs, open-front shells, bosses), not a DFM-checked tool design.
- PCB components are blocks; no copper, pins through the board, or wiring.
- Terminal blocks, USB-C and rail follow common catalogue proportions, not a
  specific manufacturer's drawing.
