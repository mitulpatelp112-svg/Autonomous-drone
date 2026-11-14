# Autonomous drone: build notes

Everything known about this build, in one place. Last updated **2026-11-14**.

- Live pages for this build are listed in [ARTIFACTS.md](ARTIFACTS.md).
- Detailed frame docs: [frame/README.md](frame/README.md), [frame/ANALYSIS.md](frame/ANALYSIS.md), [frame/CLEARANCE.md](frame/CLEARANCE.md).
- Excel feed docs: [feed/README.md](feed/README.md).

Figures marked *(verify)* are estimates, photo measurements or claims I could not confirm from a primary source.
Check them against the real part before you rely on them.

## Contents

- [Mission and goals](#mission-and-goals)
- [Build status](#build-status)
- [Parts list](#parts-list)
- [Decisions and why](#decisions-and-why)
- [Control and telemetry](#control-and-telemetry)
- [Power and wiring](#power-and-wiring)
- [Connectors, part by part](#connectors-part-by-part)
- [Motor and prop data](#motor-and-prop-data)
- [Performance and lift capacity](#performance-and-lift-capacity)
- [3D-printed frame](#3d-printed-frame)
- [Frame analysis results](#frame-analysis-results)
- [Clearance and tool access](#clearance-and-tool-access)
- [Motor and ESC mounting](#motor-and-esc-mounting)
- [Assembly order](#assembly-order)
- [Before first flight](#before-first-flight)
- [Open items](#open-items)
- [Things to verify](#things-to-verify)
- [Data sources](#data-sources)
- [Repository map](#repository-map)

---

## Mission and goals

From the build workbook:

- About **30 minutes** of hover endurance.
- **200 g** payload.
- GPS autonomy: waypoint missions with return-to-launch.
- Safe manual flight first; autonomy hardware comes after the drone flies safely.
- Phase 2 (skipped for now): NVIDIA Jetson Orin Nano companion computer (~180 g, ~12 W), Arducam IMX477 CSI camera,
  FPV camera and video transmitter.

## Build status

From the [Parts Receiving Log](https://claude.ai/artifact/5L8wNSVktLjnAgHyzJEHn1) as of 2026-11-14.
The log is the live record; this table is a snapshot.

| Part | Status |
|---|---|
| Holybro Kakute H7 v1.5 flight controller | Received 2026-11-02 |
| XT60 plugs | Received 2026-11-02 |
| HOOVO 6S 6200 mAh LiPo (main battery) | Received 2026-11-02 |
| 5010 360KV motors + 30 A OPTO ESCs | Received 2026-11-11 |
| 16 x 5.5 carbon props | Received 2026-11-11 |
| RadioMaster Boxer radio | Received 2026-11-11 |
| RadioMaster 2S 6200 mAh radio battery | Received 2026-11-11 |
| RadioMaster RP3 ExpressLRS receiver | Received 2026-11-11 |
| XT60 power distribution board | Received 2026-11-12 |
| iFlight finder buzzer | Received 2026-11-12 |
| SEQURE M10 GPS with compass | Received 2026-11-14 |
| OVONIC 6S 5000 mAh LiPo (backup battery) | On the way |
| 6S balance charger (HTRC C150 suggested) | Not ordered |
| Frame hardware (inserts, M3 bolts, zip ties, Velcro straps) | Not ordered |
| PETG filament (~1 kg) | Not ordered |

## Parts list

Final choices. Prices are from the cart sheet (blank where the sheet has none). The cart total was **$558.17** at the last sync.

| System | Part | Key specs | Price | Store |
|---|---|---|---|---|
| Flight controller | Holybro Kakute H7 v1.5 | STM32H7, ICM-42688-P IMU (single), SPA06 baro, 6 UARTs, 7–42 V input, 5 V/2 A and 9 V/3 A BECs, 30.5 mm mount, 8 g | $103.85 | [flyfive33](https://flyfive33.com/products/holybrio-kakute-h7-v1-5-icm-42688-p) |
| Power board | 30.5 mm XT60 PDB | XT60 input, 2–6S, **25 A continuous / 30 A burst**, 5 V/3 A + 12 V/0.5 A BEC, 11 g | $20.74 | [Amazon](https://www.amazon.com/30-5mm-Distribution-PDB-XT60-Quadcopter-QAV210/dp/B0FPQZ2598) |
| Motors + ESCs | 5010-14 360KV ×4 + 30 A OPTO ESC ×4 (one set) | Motor: 50×10 mm stator, 4 mm shaft, 80 g, 2–6S, 16/19 mm threaded holes. ESC: 30 A (40 A for 10 s), 2–6S, no BEC, 3.5 mm bullets, up to 621 Hz signal | $106.06 | [AliExpress](https://www.aliexpress.us/item/3256808405937047.html) |
| Props | Carbon 16 × 5.5 (1655), 2 CW + 2 CCW | Bullet/cone-nut hub *(check hole fit)* | $30.00 | [AliExpress](https://www.aliexpress.us/item/3256808508291370.html) |
| Main battery | HOOVO 6S 6200 mAh 120C | 152 × 48.5 × 48 mm, 837 g, EC5 plug (being swapped to XT60), JST-XH 7-pin balance | – | [Amazon](https://www.amazon.com/HOOVO-Softcase-Quadcopter-Airplane-Helicopter/dp/B0B1D9GQ5M) |
| Backup battery | OVONIC 6S 5000 mAh 130C | XT60, 689 g | – | [Amazon](https://www.amazon.com/OVONIC-Battery-5000mAh-22-2V-Connector/dp/B0DNLWDTDT) |
| Receiver | RadioMaster RP3 V2 | ExpressLRS 2.4 GHz, ESP8285, 2 UFL T-antennas, 4.6 g | $25.52 | [RadioMaster](https://radiomasterrc.com/products/rp3-expresslrs-2-4ghz-nano-receiver) |
| Radio | RadioMaster Boxer | EdgeTX, internal 2.4 GHz ELRS, built-in WiFi Backpack, JR module bay | $196.57 | [RadioMaster](https://radiomasterrc.com/collections/boxer-radio/products/boxer-radio-controller-m2) |
| Radio battery | RadioMaster 2S 6200 mAh | XT30 + JST-XH | $38.28 | [RadioMaster](https://radiomasterrc.com/products/2s-7-4v-6200mah-lipo-battery) |
| GPS | SEQURE M10 with QMC5883 compass | u-blox M10, SH1.0 6-pin (5V, GND, TX, RX, SDA, SCL), 12 g; plate fits M10-252Q (25 × 25) or M10-182Q (18 × 18) | $32.24 | [AliExpress](https://www.aliexpress.com/item/3256810183446273.html) |
| Buzzer | iFlight YR50B_S finder buzzer | Own backup battery + LED, 3-pin cable (5 V, GND, signal), ~4 g | $4.91 | [AliExpress](https://www.aliexpress.us/item/3256809180946860.html) |
| Charger | HTRC C150 (suggested) | 1–6S, 150 W (~6 A on 6S, about an hour for 6200 mAh), banana output with XT60 lead, JST-XH balance board, about $42–58 | – | not ordered |
| Frame | Self-designed, 3D-printed PETG | See [3D-printed frame](#3d-printed-frame) | – | – |
| Compass | Skipped: built into the GPS | – | – | – |
| Phase 2 | FPV camera, perception camera, VTX, companion computer | Skipped until the drone flies safely | – | – |

## Decisions and why

- **Radio: Boxer with its built-in ELRS, no external TX module.** The path was Nomad TX module → Pocket radio → Boxer.
  You own the Boxer. Its internal ExpressLRS talks to the RP3, and its WiFi Backpack links the laptop to Mission Planner,
  so no Nomad or separate telemetry radio is needed.
- **Flight controller: Kakute H7 v1.5**, because the v2 was out of stock. Same 30.5 mm stack. It has a single IMU,
  which is fine for learning; a Pixhawk-class board would add redundancy later.
- **Receiver: RP3** (the cart link). It is ESP8285-based, which ExpressLRS MAVLink mode needs.
  (An earlier plan named the XR3; the cart link is the RP3.)
- **GPS: SEQURE M10 with compass.** The compass row in the sheet is "Skip" because the GPS has one.
- **Batteries: HOOVO 6200 mAh main, OVONIC 5000 mAh backup.** The HOOVO's EC5 plug doesn't fit the XT60 power board
  or the charger, so it gets swapped to XT60 using the XT60 plugs you received.
  Cut and solder one wire at a time so the pack is never shorted.
- **Charger: HTRC C150 recommended** as the cheapest real 6S AC balance charger found.
- **Buzzer:** a finder buzzer with its own battery, so it still beeps after a crash unplugs the main pack.
- **Props: 16 × 5.5.** Your Efficiency sheet marks CF16x5.5 at 22.2 V as "my choice". The sheet's most efficient point
  was CF17x5.5 at 18.5 V, but 17-inch props don't fit a 680 mm wheelbase with a safe tip gap.
- **Frame: self-designed 680 mm PETG.** It has 5 main parts (body + 4 arms), plus bolt-on spring legs and a GPS mast.

## Control and telemetry

```
Boxer radio --(ExpressLRS 2.4 GHz)--> RP3 receiver --(UART, CRSF/MAVLink)--> Kakute H7 v1.5 (ArduPilot)
Laptop (Mission Planner) --(WiFi, UDP 14550)--> Boxer WiFi Backpack --(MAVLink over ELRS)--> drone
Kakute --> ESCs M1–M4 (signal over the 8-pin ESC cable; these ESCs take up to 621 Hz) --> motors
GPS + compass --> Kakute (UART + I²C)
```

- **MAVLink over ELRS** needs ExpressLRS **3.5.0 or newer** on the radio and receiver, and Backpack **1.5.0 or newer**.
  Docs: <https://www.expresslrs.org/software/mavlink/>
- The receiver goes on a flight-controller UART set to MAVLink (`SERIALx_PROTOCOL = 2`), and Mission Planner connects
  over UDP port 14550 through the Boxer's WiFi Backpack. *(verify against the ExpressLRS MAVLink page for your firmware versions)*
- RC control alone works over plain CRSF. MAVLink mode adds the laptop telemetry link.
- **Radio-loss failsafe:** ArduPilot detects lost control input and runs its radio failsafe (`FS_THR_ENABLE`); set it to RTL.

## Power and wiring

```
HOOVO 6S (XT60 after swap) --> XT60 power board --> 4 ESC pad pairs --> 4 ESCs --> 3.5 mm bullets --> 4 motors
                                     |--> Kakute VBAT/GND (flight controller power + voltage sensing)
                                     |--> 5 V / 12 V BEC pads
Kakute 5 V --> RP3, GPS, buzzer
```

- **The power board limits lift.** It is rated 25 A continuous / 30 A burst, and all four ESCs draw through it.
  Full throttle on all four motors is about **50 A**. See [Performance and lift capacity](#performance-and-lift-capacity).
- ESCs are **OPTO**: no BEC, signal and ground only. The flight controller and accessories run off the Kakute and power-board BECs.
- Battery current at hover is about 9 A with the 200 g payload, well inside every rating.

## Connectors, part by part

Checked against each product page linked in the sheet.

| Part | Has | Goes to | Note |
|---|---|---|---|
| HOOVO battery | EC5 power plug, JST-XH 7-pin balance | Power board XT60, charger balance board | **Mismatch: swap EC5 → XT60** (plugs received) |
| OVONIC battery | XT60, JST-XH | Power board, charger | Fits directly |
| Power board | XT60 input lead (solder on), 6 pad pairs, 5 V and 12 V pads | Battery, 4 ESCs, Kakute VBAT | 25 A / 30 A rating |
| ESC power leads ×4 | Bare red/black wires | Power board ESC pads | Solder; keep all four the same length |
| ESC → motor ×4 | 3 female 3.5 mm bullets per ESC | Motor's 3 phase wires (male bullets in the box) | Solder bullets to motor wires; swap any two to reverse a motor |
| ESC signal ×4 | 2-wire servo plug (signal + ground) | Kakute M1–M4 via its JST-SH 8-pin ESC cable | **Cut the servo plugs and solder to the 8-pin cable** |
| Kakute power | VBAT + GND on the 8-pin cable or battery pads | Power board battery pads | 7–42 V input |
| RP3 receiver | Solder pads 5V / GND / TX / RX, CRSF wire included, 2 UFL antennas | A Kakute UART | Antennas out through the body's front holes |
| SEQURE M10 GPS | SH1.0 6-pin socket + pads: 5V, GND, TX, RX, SDA, SCL | Kakute UART + I²C | Cable runs down the GPS mast |
| YR50B_S buzzer | 3-pin 1.0 mm: red 5 V, black GND, yellow signal | Kakute 5 V, GND, buzzer pad | Has its own backup cell |
| Props | Centre hole | Motor's bullet prop adapter | Check the hole fits the adapter |
| Boxer radio | Internal ELRS + WiFi Backpack, USB-C (charging, 2 A max) | RP3 over the air, laptop over WiFi | – |
| Radio battery | XT30 + JST-XH (2S) | Boxer battery bay | – |
| HTRC C150 charger | 4 mm banana output with XT60 lead, JST-XH balance board 2–6S | Flight packs, radio pack | No EC5 lead, so another reason for the XT60 swap |

## Motor and prop data

From the **Motor** sheet: per-motor thrust (g), current (A) and power (W).

| Volts | Prop | Thrust points (g @ A, W) |
|---|---|---|
| 22.2 V (6S) | CF15x5.5 | 500 @ 1.9 A, 42 W · 1000 @ 5.3 A, 118 W · 1640 @ 11.5 A, 255 W |
| 22.2 V (6S) | **CF16x5.5 (chosen)** | **600 @ 2.3 A, 51 W · 1200 @ 6.7 A, 149 W · 1740 @ 12.5 A, 278 W** |
| 22.2 V (6S) | CF17x5.5 | 600 @ 2.2 A, 49 W · 1200 @ 6.3 A, 140 W · 1840 @ 14.4 A, 320 W |
| 18.5 V (5S) | CF16x5.5 | 400 @ 1.6 A · 800 @ 4.2 A · 1370 @ 9.7 A (6660 rpm) |
| 18.5 V (5S) | CF17x5.5 | 500 @ 2.0 A · 1000 @ 5.4 A · 1600 @ 11.8 A (most efficient in the Efficiency sheet) |
| 14.8 V (4S) | CF16x5.5 | 300 @ 1.3 A · 600 @ 3.5 A · 990 @ 7.1 A |
| 11.1 V (3S) | CF16x5.5 | 200 @ 1.0 A · 400 @ 2.4 A · 630 @ 4.7 A |

No-load current is 0.4 A at 22.2 V. The full table, including 18-inch props, is in the workbook.

## Performance and lift capacity

All figures come from the Motor sheet curve (16 × 5.5 at 22.2 V); see [frame/ANALYSIS.md](frame/ANALYSIS.md).

| Item | Value |
|---|---|
| All-up weight (HOOVO + 200 g payload) | **2,367 g** |
| Empty weight (everything but payload) | 2,167 g |
| Hover thrust per motor | 592 g (34% of max) |
| Max thrust, all four motors | **6.96 kg** at ~50 A |
| Max thrust the power board can feed | **~5.08 kg** at 30 A (4.52 kg at 25 A) |
| Thrust-to-weight with the 200 g payload | 2.14 (board-limited) / 2.94 (motors) |
| Hover time, HOOVO 6200 mAh, 80% usable, calm air | **~32 min** |
| Hover time, OVONIC 5000 mAh | ~28 min *(estimate)* |

**Maximum payload** at thrust-to-weight 2.0 (responsive flying):
- **~370 g with the current 25 A power board.**
- **~1,313 g with a 70 A or bigger board**, or with the ESC leads wired straight to the battery lead.

At thrust-to-weight 1.6 (calm air only) those limits are ~1,006 g and ~2,183 g.

| Payload | All-up weight | T/W (board / motors) | Hover current | Hover time | Legs' hard-landing limit |
|---|---|---|---|---|---|
| 0 g | 2,167 g | 2.34 / 3.21 | 8.7 A | 34 min | 1.27 m/s |
| 200 g | 2,367 g | 2.14 / 2.94 | 9.3 A | 32 min | 1.21 m/s |
| 500 g | 2,667 g | 1.90 / 2.61 | 11.4 A | 26 min | 1.14 m/s |
| 1,000 g | 3,167 g | 1.60 / 2.20 | 15.0 A | 20 min | 1.05 m/s |
| 1,313 g | 3,480 g | 1.46 / 2.00 | 17.3 A | 17 min | 1.00 m/s |

Thrust-to-weight 2.0 for responsive flying and 1.6 as the marginal limit are rules of thumb. Real flights with wind and
manoeuvring get less time than these calm-air hover numbers.

## 3D-printed frame

Parametric CadQuery model; all numbers live in [frame/params.py](frame/params.py). It exports STEP for Fusion 360
(`frame/out/assembly.step` opens with every part placed) and STL for the slicer.

| Item | Value |
|---|---|
| Wheelbase (motor to motor, diagonal) | **680 mm** |
| Props | 16 × 5.5; 74 mm gap between neighbouring prop tips |
| Material | PETG; 0.4 mm nozzle, 0.2 mm layers, 4 walls, 25–30% gyroid; legs at 100% infill |
| Printer bed | Every part fits 220 × 220 mm |
| Printed mass | ~672 g |

| Part | Qty | Mass each | Key dimensions | Print orientation |
|---|---|---|---|---|
| Central body | 1 | ~156 g | 198.6 × 198.6 × 40.5 mm; 90 × 90 mm electronics bay; 30.5 mm stack standoffs; 4 arm tunnels 28.5 × 28.5 mm | Floor down; tunnel roofs bridge, no supports |
| Arm | 4 | ~88 g | 250 mm root to motor; 28 mm wide; 28 → 20 mm tall; Ø46 × 5 mm motor pad; 12 × 7 mm wire channel; flat 71 mm ESC seat | Flat side down, diagonally on the bed |
| Curved spring leg | 4 | ~40 g | C-shaped leaf 28 × 4.8 mm, bows 50 mm outward, 110 mm tall; 54 × 28 × 6 mm pad; 24 × 28 mm foot | On its side, C flat on the bed, 100% infill |
| GPS mast | 1 | ~5 g | Ø12 × 100 mm tube, Ø8 cable bore, 30 × 30 mm GPS plate | GPS plate on the bed |

**Design features**
- **Arm joint.** Each arm slides into a tunnel in the body and is held by 2 × M3 × 40 from underneath.
  The tunnel carries flight loads; the bolts sit either side of the wire channel.
- **Wiring.** ESC leads run along each arm's 12 × 7 mm top channel, under the body roof, and out through an 18 mm
  opening (open at the top) into the bay.
- **GPS mast** sits outside the rear wall, so the battery strap crosses the bay floor freely.
  Its lock screw goes in from the back, and its cable passes under the mast into the bay.
- **Battery** hangs underneath on two 20 mm Velcro straps through floor slots at x = ±33 mm.
- **Motor pad.**
  - A level landing under the 58 mm motor base.
  - A cross of slots that takes any 4-hole pattern from 12 to 31 mm, including the listed 16 mm and 19 mm holes.
  - 4 × Ø7 cooling vents, with an open pocket underneath for screwdriver access and airflow.
- **Spring legs.** A C-shaped leaf compresses on touchdown: ~7.5 mm at 0.5 m/s, ~18 mm at a 1.2 m/s hard landing.
  The legs are the designed weak link, so print a spare pair.
- Receiver antennas exit through two Ø4.4 holes in the front wall; there is a 16 × 10 mm USB-C window in the side wall,
  and a 24 × 12 mm battery lead slot in the floor.
- Front is +X, between the two front arms.

**Hardware to buy**

| Item | Qty | Use |
|---|---|---|
| M3 heat-set inserts, 5.7 mm long (Ø4.2 mm holes) | 21 (buy 50) | 8 body roof, 4 stack standoffs, 8 arm undersides (legs), 1 mast lock |
| M3 × 40 socket cap | 8 | Arm-to-body joints, from under the body |
| M3 × 8 socket cap | 24 | 16 motor screws (5 mm pad + ~3 mm into the motor) + 8 leg bolts |
| M3 × 10 bolt or grub screw | 1 | GPS mast lock |
| M3 × 20 + nylon spacers | 4 | Power board + Kakute stack (check the Kakute's own hardware first) |
| Zip ties ≤ 3.6 mm wide | 8 | Two per ESC |
| 20 mm Velcro battery straps | 2 | Battery |
| PETG filament | ~1 kg | All printed parts |

## Frame analysis results

Full report: [frame/ANALYSIS.md](frame/ANALYSIS.md). Material limits: PETG strength 45 MPa along lines and 25 MPa
across layers, divided by a safety factor of 3.

| Check | Value | Limit |
|---|---|---|
| Arm bending at the tunnel exit, full thrust (17.1 N) | 3.53 N·m, **2.24 MPa** | 15 MPa |
| Arm tip deflection, hover / full thrust | 0.49 / 1.44 mm | 2 / 4 mm |
| Arm torsion from motor torque (0.31 N·m) | 0.13 MPa | 6.7 MPa |
| Arm first bending frequency | ~47 Hz (rotor ~66 Hz at hover) | – |
| Tunnel roof lip force / roof bending | 99 N / 2.9 MPa | 15 MPa |
| Spring leg at a 1.2 m/s landing on 4 legs | 18 mm travel, 29.7 MPa | 30 MPa |
| Spring leg gives way | ~63 N per leg (1.6 m/s on 4 legs, 1.1 m/s on 2) | – |
| Leg bolt pull at the leg's break load | 41 N | ~167 N |
| Centre of gravity | about at the body underside, ~53 mm below the prop plane | – |

- **Vibration.** The arm's first bending mode sits below hover rotor speed. Don't make the arms moderately stiffer:
  that would move the mode onto hover speed. Instead:
  - balance the props;
  - soft-mount the flight controller;
  - turn on ArduPilot's throttle-based harmonic notch, since these ESCs have no RPM telemetry;
  - check the FFT in the first hover log.

## Clearance and tool access

Full report: [frame/CLEARANCE.md](frame/CLEARANCE.md); checker: [frame/clearance.py](frame/clearance.py).
**210 of 210 paths are clear.**

The checker gives every screw a straight 7 mm-wide, 150 mm-long tool path from its head, and every insert a
soldering-iron path. Cables, straps and connectors get boxes along their routes. Each path is tested against every
part, the battery, motors, ESCs, wiring and props.

Thinnest walls left between holes:

| Between | Wall |
|---|---|
| Motor screw head (outer slot end) to pad pocket wall | 0.8 mm |
| Strap slot to bay wall | 1.0 mm |
| Mast lock insert to mast socket | 1.1 mm |
| Joint bolt hole to wire channel | 1.8 mm |

Ground clearance under the battery is ~57 mm unloaded and ~54 mm resting.

Problems found and fixed along the way:
- the outer leg bolt was blocked by a slanted strut;
- the arm wires hit a solid wall;
- the GPS mast blocked the battery strap;
- the strap slots cut into the wall;
- the USB window was never cut through;
- the battery lead slot was too small for an XT60;
- the GPS cable had no exit;
- the motor base rested on the sloped arm.

## Motor and ESC mounting

Diagram: [frame/out/motor_mount.png](frame/out/motor_mount.png). Parts are modelled in [frame/hardware.py](frame/hardware.py).

| Size | Value | Source |
|---|---|---|
| Motor stator | 50 × 10 mm (the "5010"), Ø4 shaft, 80 g | Listing |
| Motor mounting holes | Threaded, 16 mm and 19 mm spacing | Listing |
| Motor can | ~Ø58 × 18 mm | Measured from listing photos *(verify)* |
| Prop adapter | Bullet type, ~Ø20 collar, tip ~40 mm above the motor | Photos *(verify)* |
| ESC body | ~68 × 25 × 8.7 mm, ~30 g | Retailer listing of the same ReadytoSky model *(verify)* |
| Screw thread | M3 | Assumed, not on the listing *(verify)* |

- **Motor.** Turn it until its holes sit over the cross of slots, wires toward the body.
  Screw in 4 × M3 × 8 from under the arm, through the pocket.
  First push a toothpick into a motor hole and check it's at least 3.5 mm deep, so the screw can't reach the windings.
- **ESC.** It sits on the flat seat, bullet end toward the motor, held by 2 zip ties through the arm.
  The motor leads plug into its bullets; the power and signal leads go back along the channel into the body.
  The prop sweeps over it, which cools it.
- The prop hub sits ~53 mm above the body underside.

## Assembly order

So every screw stays reachable (details in [frame/README.md](frame/README.md)):

1. All heat-set inserts first.
2. Motors onto the arms (screws from under the pad), then ESCs and zip ties.
3. Lay the ESC leads in the channels; slide the arms into the body; joint bolts from underneath, with the battery off.
4. Power board and Kakute from above; stack bolts from above. Solder ESC power to the board and ESC signals to the
   Kakute's 8-pin cable.
5. Receiver on the bay wall, antennas out the front holes; buzzer in the bay.
6. Thread the GPS cable down the mast, push the mast into its socket, feed the plug into the bay, and lock it from the rear.
7. Legs: drone upside down, bolts straight up into the arm undersides, C bowing outward.
8. Battery last, strapped underneath, centred front to back. A 10 mm shift moves the CG about 3.5 mm.

## Before first flight

- Swap the HOOVO's EC5 to XT60, one wire at a time.
- Check that the motors say **360 KV** (the listing sells 360 and 750 KV). Check that the ESC labels say **2–6S**:
  the listing title says 2–4S but the photo label reads 2–6S. A full 6S pack reaches 25.2 V.
- Flash ArduPilot to the Kakute. *(I'm not certain which ArduPilot target name matches the v1.5 board; check the
  ArduPilot hardware list.)*
- Update the Boxer and RP3 to the same ExpressLRS version (3.5.0+), and the Backpack to 1.5.0+.
- Calibrate the accelerometer, compass and radio. Check the battery voltage reading against a multimeter.
- Run a motor test with props off to confirm order and direction.
- Failsafes: radio loss → RTL, low battery → RTL, critical battery → Land, geofence on. Test them with props off.
- First hovers in an open field; read the vibration and FFT logs; set the harmonic notch; then AutoTune.
- Balance the props.
- **FAA:** at ~2.4 kg this drone needs FAA registration and Remote ID in the US for recreational flying
  *(rules change; check the FAA site before flying)*.
- The older [24-inch Quad Build Guide](https://claude.ai/artifact/5QCyr1wzTm2hUdrVKaoa6E) has ArduPilot starter
  parameters, but they assume SiK telemetry and the Kakute v2. Redo them for this build.

## Open items

- [ ] Order the 6S charger (HTRC C150 or similar). The Charger row in the sheet is still empty.
- [ ] Order the frame hardware and PETG filament.
- [ ] Print the frame. Weigh the first arm to check the mass estimate.
- [ ] Measure the real motor (diameter, height, hole spacing, hole depth) and ESC (length, width) and update `frame/params.py`.
- [ ] Check that the props' centre hole fits the motor's prop adapter.
- [ ] Decide on the power board: the current 25 A board caps payload at ~370 g. A 70 A+ board unlocks ~1.3 kg.
- [ ] Receive the OVONIC backup battery.
- [ ] Reorganize the Excel workbook. This was started and then stopped; the workbook is read-only to the feed.

## Things to verify

- Power board rating (25 A / 30 A): from my earlier read of its listing. Check its label.
- ESC voltage rating (2–6S vs 2–4S) and motor KV (360 vs 750).
- Motor can size, height and prop adapter: measured from photos, roughly ±10–30%.
- ESC size: from one retailer listing of what looks like the same model.
- Motor screw thread (M3) and hole depth.
- Prop weight (22 g each), wiring and hardware mass (~90 g), avionics power (5 W): estimates.
- PETG properties and print strength: typical datasheet values; printed parts vary.
- Spring-leg behaviour: linear curved-beam model. Real legs will be a little softer near full compression.
  The ~40 MPa break point is an estimate. A drop from ~7 cm with the battery on is roughly a 1.2 m/s touchdown,
  a good test.
- ArduPilot landing speed default (believed 50 cm/s, `LAND_SPEED`).

## Data sources

- **Build workbook (SharePoint, read-only):** `Drone_Master_Build_Sheet.xlsx`
  <https://studentuncc-my.sharepoint.com/:x:/g/personal/mpate183_charlotte_edu/IQDsuxazQJ82SpIsXuKB2604AWyWIvZJR2nDEfddNOIa2ec?e=Zj4fVf>
  - **cart:** parts, links, quantities, costs.
  - **Motor:** thrust test data.
  - **Efficiency:** prop/voltage choice. The Master Build Sheet tab was removed in October.
- [feed/sync_sheet.py](feed/sync_sheet.py) downloads it and writes [feed/data.json](feed/data.json).
- **Product pages** linked in the cart (see [Parts list](#parts-list)). Connector facts were read from them on
  2026-10-23. The motor/ESC specs are from the listing text and photos.
- ExpressLRS MAVLink docs: <https://www.expresslrs.org/software/mavlink/>

## Repository map

| Path | What it is |
|---|---|
| [DRONE.md](DRONE.md) | This file |
| [ARTIFACTS.md](ARTIFACTS.md) | Index of the live web pages (artifacts), linked back here |
| [feed/README.md](feed/README.md) | How the Excel feed works |
| [feed/index.html](feed/index.html) | Source of the **Drone Build Bench** page |
| [feed/sync_sheet.py](feed/sync_sheet.py), [feed/data.json](feed/data.json) | Workbook sync and its output |
| [frame/README.md](frame/README.md) | Frame print settings, hardware, assembly, Fusion import |
| [frame/params.py](frame/params.py) | Every frame dimension and part size, with sources |
| [frame/build_frame.py](frame/build_frame.py) | Builds the parts, exports STEP/STL, checks bed fit and interference |
| [frame/hardware.py](frame/hardware.py) | Motor, ESC, wiring and zip ties at real sizes |
| [frame/analysis.py](frame/analysis.py) → [frame/ANALYSIS.md](frame/ANALYSIS.md) | Loads, stresses, vibration, spring legs, lift capacity |
| [frame/clearance.py](frame/clearance.py) → [frame/CLEARANCE.md](frame/CLEARANCE.md) | Tool-access and clearance check |
| [frame/render.py](frame/render.py) | Preview images and the motor-mount diagram |
| [frame/export_viewer.py](frame/export_viewer.py) | Writes `frame/viewer/model.json` for the 3D viewer |
| [frame/viewer/index.html](frame/viewer/index.html) | Source of the **Quad Frame Viewer** page |
| [frame/checklist/index.html](frame/checklist/index.html) | Source of the **Parts Receiving Log** page |
| `frame/out/` | STEP and STL files, `report.json`, `clearance.json`, `lift.json`, images |

Rebuild everything after changing a number in `frame/params.py`:

```
cd frame
python3 build_frame.py && python3 clearance.py && python3 analysis.py && python3 render.py && python3 render.py --mount && python3 export_viewer.py
```
