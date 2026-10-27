# 680 mm printed quad frame

A PETG frame for the parts in your build sheet: 5010 360KV motors with 16 × 5.5 props,
four 30 A ESCs on the arms, Kakute H7 v1.5 + XT60 power board stack, RP3 receiver,
SEQURE M10 GPS on a mast, finder buzzer, and a 6S pack strapped underneath.

| File | What it is |
|---|---|
| `params.py` | Every dimension, with where each number came from. Edit here. |
| `build_frame.py` | Builds the parts and the assembly, checks bed fit and arm/body interference. |
| `analysis.py` | Forces, moments, stresses, deflection and vibration. Writes `ANALYSIS.md`. |
| `clearance.py` | Tool-access and clearance check for every screw, insert, cable and strap. Writes `CLEARANCE.md`. |
| `render.py` | Preview images. |
| `out/*.step` | Open in Fusion 360 (File → Open). `assembly.step` opens with every part placed. |
| `out/*.stl` | Ready for the slicer. |

Rebuild after changing a number:

```
pip install cadquery shapely
cd frame
python3 build_frame.py && python3 clearance.py && python3 analysis.py && python3 render.py
```

## Parts to print (all fit a 220 × 220 mm bed)

| Part | Qty | Est. mass each | Orientation on the bed |
|---|---|---|---|
| Body | 1 | ~157 g | Floor down, as modelled. The arm tunnels' roofs bridge 28.5 mm, so no supports. |
| Arm | 4 | ~90 g | Flat side down (as modelled), diagonally across the bed. Longest part: 210 mm footprint. |
| Leg (curved spring) | 4 | ~40 g (solid) | On its side, C flat on the bed. **100% infill** (or 6+ walls): the leaf is a spring. |
| GPS mast | 1 | ~6 g | Upside down: GPS plate on the bed, tube standing up. |

Frame total about 678 g (estimated with 4 walls + 25–30% infill; weigh your first arm).

**PETG settings:** 0.4 mm nozzle, 0.2 mm layers, **4 walls**, 5 top / 5 bottom layers,
25–30% gyroid infill, no supports (enable bridging). Arms rely mostly on their walls, so
don't drop below 4 walls.

## Hardware

| Item | Qty | Where |
|---|---|---|
| M3 heat-set insert, 5.7 mm long, OD ~4.6–5 mm | 21 | 8 body roof (arm joints), 4 stack standoffs, 8 arm undersides (legs), 1 mast lock (back of the mast boss) |
| M3 × 40 bolt | 8 | Arm joints: from under the body, through floor + arm, into the roof inserts |
| M3 × 8 bolt | 8 | Legs: through the leg pad into the arm inserts |
| M3 × 10 bolt or grub screw | 1 | Mast lock, from the back of the mast boss |
| M3 × 20 bolt + nylon spacers | 4 | Power board + Kakute stack into the standoff inserts (check stack height) |
| Motor screws (M3) | 16 | From under each pad into the motor. Must not reach the windings: pad is 6 mm, so use 8–10 mm screws (check the motor's thread depth) |
| Zip ties, ≤ 3.6 mm wide | 8 | Two per ESC, through the slots in the arm |
| 20 mm Velcro battery straps | 2 | Through the slots in the body floor |

The insert holes are 4.2 mm (`INSERT_HOLE_D`). If your inserts call for a different hole, change it in `params.py` and rebuild.

## Assembly

1. **Inserts.** Melt them in with a soldering iron at about 220–240 °C, flush with the surface:
   8 into the top of the body (the holes above each tunnel), 4 into the stack standoffs, 2 into
   the underside of each arm (leg mount), 1 into the back of the mast boss.
2. **Motors.** Bolt each motor onto its arm pad from underneath. The pad has radial slots, so
   it takes the motor's 16 mm and 19 mm screw patterns. Point the motor wires toward the body.
3. **ESCs.** Each ESC sits in the recess on top of its arm and is held by two zip ties through the slots.
   Solder the motor bullets; run the ESC power and signal wires back along the top channel (12 × 7 mm) to the root.
   The two arm bolts sit either side of the channel, so the wires never have to go round a bolt.
4. **Arms into the body.** Slide each arm root into its tunnel. The wires come out of the channel through the
   18 mm opening at the end of the tunnel (open at the top, so you can lay them in) and drop into the bay. Bolt with 2 × M3 × 40 from underneath. The tunnel carries the
   flight loads; the bolts just hold the arm in.
5. **Power board + Kakute.** Power board on the standoffs (XT60 lead down through the slot in the floor
   to the battery), Kakute above it on its grommets. Solder the ESC power leads to the board and the
   ESC signals to the Kakute's M1–M4 via the cut 8-pin cable.
6. **Receiver, buzzer.** RP3 on the bay wall with double-sided tape; its two antennas out through the
   holes in the front wall. Buzzer in the bay.
7. **GPS mast.** The socket is on the outside of the rear wall, so the bay floor is clear for the battery strap.
   Thread the GPS cable down the mast (8 mm bore), push the mast in, and feed the plug through the passage under
   the mast into the bay. Lock the mast with the screw from the back. GPS on the plate, arrow forward.
8. **Legs.** Drone upside down. Bolt each leg under its arm with 2 × M3 × 8, with the C bowing outward (away from the
   body). Both bolts sit inboard of the leaf and the foot, so a straight screwdriver reaches them. The legs are
   curved PETG springs that compress about 7 mm on a normal landing and 18 mm on a 1.2 m/s hard one; they are
   meant to be the part that gives in a crash, so print a spare pair.
9. **Battery.** Two Velcro straps through the floor slots, battery underneath, centred.
   Note: the HOOVO pack has an EC5 plug and the power board has XT60 (see the connector check).

Front is +X (between the two front arms). The receiver antennas point forward and the GPS mast is at the back.

## Opening in Fusion 360

File → Open → `out/assembly.step`. Fusion imports every part as a body inside its own component,
already positioned. The imported bodies have no feature history; to change a size parametrically,
edit `params.py` and rebuild, or edit the bodies directly in Fusion.

See `ANALYSIS.md` for loads, stresses, deflection, vibration and balance, and `CLEARANCE.md` for the
tool-access and clearance check (every screw, insert, cable and strap path; all clear).
