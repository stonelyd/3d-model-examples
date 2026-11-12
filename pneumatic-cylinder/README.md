# ISO 15552-style tie-rod pneumatic cylinder, 32 bore x 100 stroke (ryucad 0.9.0-pre.3)

A double-acting, cushioned, tie-rod pneumatic cylinder in the ISO 15552 32 mm envelope, with a rear double-clevis mount and an ISO 8140-style rod-end clevis. Built through the ryucad CLI only, by `tools/pneumatic-cylinder.py`.

35 occurrences, 21 BOM lines. `ryucad check`: 0 errors, 0 warnings. `ryucad interference pneumatic-cylinder`: 85 pairs at stroke 10, 90 and 100 mm (88 at 0 mm), 0 interferences, 0 touching, 0 unchecked.

## Key dimensions (as modelled)
- Bore 32 mm (barrel 32 ID x 38 OD), stroke 100 mm, piston rod 12 mm
- Body length (rear cap face to front cap face) 94 mm + stroke = 194 mm; 3 mm x 30 mm centring boss on the front cap
- End caps 45 mm square; four M6 tie rods on a 32.5 mm square
- Ports: G1/8 on the +x face of each cap, shown as 8.8 mm tap-drill bores (threads not modelled) with 4 mm feed passages into the cushion bores
- Rod thread M10x1.25, 22 mm long; rod shoulder 26 mm beyond the front cap face when retracted
- Rear clevis: 26 mm slot, 10 mm pin 24 mm behind the rear cap face. Rod clevis: 10 mm slot, 10 mm pin 40 mm from the clevis's thread end
- Computed areas: piston 804.2 mm², annulus (rod side) 691.2 mm². No force, pressure rating, mass or flow is claimed.

## Parts (21 lines)
- Body: barrel, rear-cap, front-cap (each cap: cushion bore, port bore and passage, cushion-needle bore), 4 x tie-rod, 4 x nut-m6, 2 x cushion-screw (slotted needle screws)
- Rod gland (in the front cap): rod-seal (U-cup), rod-bushing (bronze), rod-wiper
- Piston group: piston (aluminium, with rear cushion spear), 2 x piston-seal (U-cups, back to back), wear-band, magnet-ring
- Rod: piston-rod (M8 spigot into the piston, front cushion collar, M10x1.25 end), nut-m10x1-25 (jam nut), rod-clevis, pin-10x25, 2 x circlip-10
- Rear mount: rear-clevis-mount, 4 x screw-m6x14 (socket head, in counterbores), pin-10x45, 2 x circlip-10

## Moving it
The rod slides on one slider mate (`stroke-slider`, barrel to rod) whose distance is the assembly parameter `stroke`, clamped to 0..100 mm by the expression `max(0 mm, min(stroke, 100 mm))`. Everything on the rod (piston, seals, wear band, magnet, jam nut, clevis, pin, clips) is fastened to it.

    ryucad param set pneumatic-cylinder "stroke=90 mm"
    ryucad assembly solve pneumatic-cylinder

`param set` writes the solved poses back. The project is saved at stroke = 10 mm.

## Rebuild from scratch
    python3 -I tools/pneumatic-cylinder.py $(which ryucad) <empty folder>

(`tools/model.py` is ryucad's corpus helper, copied beside it.)

## Verified
- `ryucad check`: passed, 0 errors, 0 warnings
- `ryucad interference`: 0 interferences at stroke 0, 10, 90 and 100 mm
- `ryucad assembly solve`: converged, 0 dof, all 25 mates `well`, at stroke 10 and 90 mm (and 0, 100, and 150 mm, which the clamp holds at 100)
- `ryucad bom`: 21 lines, 35 parts placed
- STEP AP242 export of the assembly

## Not verified / simplified
- Threads (ports, tie rods, rod end, screws, piston on rod) are not modelled; threaded features are plain bores and shanks at nominal or minor diameter
- Seals are rigid U-cup sections drawn just short of contact (0.02 to 0.05 mm), not compressed, and have no squeeze or sealing analysis
- Cushioning is geometric only (spear and collar in their bores, needle screws); no air flow, cushioning, force or pressure calculation
- Clevis pins and the rod clevis are fastened, not free to rotate; the rod does not turn about its axis
- No masses or materials assigned; no tolerances or fits checked beyond interference
- The tie rods screw into the rear cap and the mount screws into the same holes from behind, 1 mm apart (simplified from real ISO practice)
