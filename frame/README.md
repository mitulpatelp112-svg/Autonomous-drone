# 680 mm printed quad frame

A PETG frame for the parts in your build sheet: 5010 360KV motors with 16 × 5.5 props,
four 30 A ESCs on the arms, Kakute H7 v1.5 + XT60 power board stack, RP3 receiver,
SEQURE M10 GPS on a mast, finder buzzer, and a 6S pack strapped underneath.

| File | What it is |
|---|---|
| `params.py` | Every dimension, with where each number came from. Edit here. |
| `build_frame.py` | Builds the parts and the assembly, checks bed fit and arm/body interference. |
| `analysis.py` | Forces, moments, stresses, deflection and vibration. Writes `ANALYSIS.md`. |
| `render.py` | Preview images. |
| `out/*.step` | Open in Fusion 360 (File → Open). `assembly.step` opens with every part placed. |
| `out/*.stl` | Ready for the slicer. |

Rebuild after changing a number:

```
pip install cadquery shapely
cd frame
python3 build_frame.py && python3 analysis.py && python3 render.py
```

## Parts to print (all fit a 220 × 220 mm bed)

| Part | Qty | Est. mass each | Orientation on the bed |
|---|---|---|---|
| Body | 1 | ~152 g | Floor down, as modelled. The arm tunnels' roofs bridge 28.5 mm, so no supports. |
| Arm | 4 | ~93 g | Flat side down (as modelled), diagonally across the bed. Longest part: 210 mm footprint. |
| Leg | 4 | ~22 g | On its side (the 16 mm face). |
| GPS mast | 1 | ~6 g | Upside down: GPS plate on the bed, tube standing up. |

Frame total about 620 g (estimated with 4 walls + 25–30% infill; weigh your first arm).

**PETG settings:** 0.4 mm nozzle, 0.2 mm layers, **4 walls**, 5 top / 5 bottom layers,
25–30% gyroid infill, no supports (enable bridging). Arms rely mostly on their walls, so
don't drop below 4 walls.

## Hardware

| Item | Qty | Where |
|---|---|---|
| M3 heat-set insert, 5.7 mm long, OD ~4.6–5 mm | 21 | 8 body roof (arm joints), 4 stack standoffs, 8 arm undersides (legs), 1 mast lock |
| M3 × 40 bolt | 8 | Arm joints: from under the body, through floor + arm, into the roof inserts |
| M3 × 8 bolt | 8 | Legs: through the leg pad into the arm inserts |
| M3 × 8 bolt or grub screw | 1 | Mast lock, from the side |
| M3 × 20 bolt + nylon spacers | 4 | Power board + Kakute stack into the standoff inserts (check stack height) |
| Motor screws (M3) | 16 | From under each pad into the motor. Must not reach the windings: pad is 6 mm, so use 8–10 mm screws (check the motor's thread depth) |
| Zip ties, ≤ 3.6 mm wide | 8 | Two per ESC, through the slots in the arm |
| 20 mm Velcro battery straps | 2 | Through the slots in the body floor |

The insert holes are 4.2 mm (`INSERT_HOLE_D`). If your inserts call for a different hole, change it in `params.py` and rebuild.

## Assembly

1. **Inserts.** Melt them in with a soldering iron at about 220–240 °C, flush with the surface:
   8 into the top of the body (the holes above each tunnel), 4 into the stack standoffs, 2 into
   the underside of each arm (leg mount), 1 into the side of the mast boss.
2. **Motors.** Bolt each motor onto its arm pad from underneath. The pad has radial slots, so
   it takes the motor's 16 mm and 19 mm screw patterns. Point the motor wires toward the body.
3. **ESCs.** Each ESC sits in the recess on top of its arm and is held by two zip ties through the slots.
   Solder the motor bullets; run the ESC power and signal wires back along the top channel to the root.
4. **Arms into the body.** Slide each arm root into its tunnel (wires go through the hole at the end of the
   tunnel into the electronics bay). Bolt with 2 × M3 × 40 from underneath. The tunnel carries the
   flight loads; the bolts just hold the arm in.
5. **Power board + Kakute.** Power board on the standoffs (XT60 lead down through the slot in the floor
   to the battery), Kakute above it on its grommets. Solder the ESC power leads to the board and the
   ESC signals to the Kakute's M1–M4 via the cut 8-pin cable.
6. **Receiver, buzzer.** RP3 on the bay wall with double-sided tape; its two antennas out through the
   holes in the front wall. Buzzer in the bay.
7. **GPS mast.** Push the mast into the socket at the rear of the bay, lock it with the side screw,
   stick the GPS on the plate (arrow forward). Run the cable down the inside of the mast.
8. **Legs.** Bolt each leg under its arm with 2 × M3 × 8. The feet splay outward.
9. **Battery.** Two Velcro straps through the floor slots, battery underneath, centred.
   Note: the HOOVO pack has an EC5 plug and the power board has XT60 (see the connector check).

Front is +X (between the two front arms). The receiver antennas point forward and the GPS mast is at the back.

## Opening in Fusion 360

File → Open → `out/assembly.step`. Fusion imports every part as a body inside its own component,
already positioned. The imported bodies have no feature history; to change a size parametrically,
edit `params.py` and rebuild, or edit the bodies directly in Fusion.

See `ANALYSIS.md` for loads, stresses, deflection, vibration and balance.
