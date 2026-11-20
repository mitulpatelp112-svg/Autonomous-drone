# Custom power distribution board (PDB), v0.1 design

A single board to replace the current two-board power setup (the 150 A 6-port XT60 board feeding the ESCs, plus the
old 25 A board feeding the Kakute). This folder is self-contained: nothing in `frame/`, `feed/` or the top-level docs
depends on it, and it does not change them.

Status: **requirements, sizing and placement plan.** No schematic or PCB yet. The next step is the KiCad project
(see [Next steps](#next-steps)).

Figures marked *(verify)* are from memory or are design estimates. Check them against the datasheet or the real part
before ordering boards.

| File | What it is |
|---|---|
| `params.py` | Every design input, each tagged with where it came from |
| `calc.py` | Sizes copper, shunt, wires and connectors → `out/calc.json`, [`out/CALC.md`](out/CALC.md) |
| `layout.py` | Board outline and placement plan → [`out/layout.svg`](out/layout.svg), `out/outline.dxf` (KiCad Edge.Cuts) |

```bash
cd pdb && python3 calc.py && python3 layout.py
```

No packages needed beyond Python 3.

---

## Requirements

| # | Requirement | Value | Why |
|---|---|---|---|
| R1 | Input | 6S LiPo, 25.2 V max, through an XT60 on a 12 AWG pigtail | Both packs are (or will be) XT60 |
| R2 | Parts on the battery bus | rated ≥ 35 V; capacitors 50 V | ESC switching spikes ride on top of 25.2 V |
| R3 | Continuous current | **60 A** | Full throttle on all four motors is ~50 A (Motor sheet: 12.5 A each) |
| R4 | Peak current | **100 A for 10 s** | Punch-outs, a stalled motor; copper must survive it |
| R5 | ESC outputs | 4 solder pad pairs, 16 AWG, one per arm, on the corners | Arms are on the diagonals; wire grooves are sized for 2 × 16 AWG |
| R6 | Current sensing | Shunt + amplifier into the Kakute's current input, ≥ 1.2 × peak full scale | ArduPilot battery failsafe and mAh used |
| R7 | Kakute link | One JST-SH 8-pin cable carrying VBAT, GND, CURR and M1–M4 | Same as a 4-in-1 ESC: one plug instead of loose wires |
| R8 | ESC signals | 4 signal + ground pad pairs; routed to the 8-pin connector | The OPTO ESCs need only signal and ground |
| R9 | Mounting | 30.5 × 30.5 mm M3 pattern, ≤ 60 mm square | Uses the bay's existing standoffs; leaves 15 mm per side for wires |
| R10 | No onboard 5 V needed now | Kakute has its own 5 V / 2 A and 9 V / 3 A BECs | Keeps the board simple; a phase-2 buck footprint is left unfitted |
| R11 | Protection | TVS across the bus, bulk capacitance, power LED | |

Not in scope for v0.1: an antispark or electronic switch, reverse-polarity protection on the main bus (impractical at
100 A without large MOSFETs; the XT60 is keyed), and the phase-2 companion-computer supply.

## Block diagram

```
                       +----------------- PDB --------------------------------------------+
 XT60 --12 AWG--> BAT+ |--[ 0.5 mΩ shunt ]--+== VBAT bus (L1 + L3) ==+--> ESC1+ .. ESC4+   |
                       |        |  Kelvin   |                        +--> C1, C2 (470 µF 50 V)
                       |   [ INA240A2 ]     +--> TVS (SMDJ28A-class) +--> LED + resistor     |
                       |    gain 50         +--> 3.3 V LDO --> INA240 supply               |
                       |        |                                                         |
                       |        +--> CURR -------------------------------+                |
                       |                                                 |                |
                 BAT-  |== GND bus (L2 + L4) ======================> ESC1- .. ESC4-       |
                       |                                                 |                |
                       |  S1..S4, G1..G4 (ESC signal pads) -----> J1 JST-SH 8 --> Kakute  |
                       |  VBAT, GND ------------------------------> J1                    |
                       +------------------------------------------------------------------+
```

The shunt sits on the **high side** (in the + lead), so the ground plane stays one solid piece and the ESC signal
grounds share it with the Kakute. The INA240 family is specified for high-side use at these voltages
*(verify: TI lists a −4 V to 80 V common-mode range)*.

## Sizing results

Full output: [`out/CALC.md`](out/CALC.md). Headlines:

| Item | Result |
|---|---|
| Stack-up | 4 layers, 2 oz on every layer. L1 VBAT, L2 GND, L3 VBAT, L4 GND |
| Main bus width needed (IPC-2221) | 16 mm at 60 A / +20 °C; **20 mm at 100 A / +45 °C**. Each net gets ~26 mm. |
| Each ESC branch | ≥ 3.5 mm at 20 A |
| Board loss | ~2.8 W at full throttle (1.5 W copper, 1.3 W shunt); ~0.1 W at hover |
| Current sense full scale | **128 A** (0.5 mΩ × gain 50 into a 3.3 V ADC) |
| ArduPilot | `BATT_MONITOR = 4`, `BATT_AMP_PERVLT = 40`, `BATT_AMP_OFFSET = 0` |
| Shunt power | 1.3 W at full throttle, 5 W at the 100 A peak → choose a part rated ≥ 5 W |

IPC-2221 is the older, conservative sizing method. IPC-2152 usually allows narrower copper. Treat these widths as a floor.

**XT60 note.** As I recall, Amass rates the XT60 at 30 A continuous with a 60 A burst *(verify)*. Hover (~9 A) is far
inside that, and full throttle (~50 A) is fine as a short burst, but not held for minutes. If you start flying heavy
payloads at high throttle, move the pigtail to an XT90. The board pads take either.

## Placement plan

![placement plan](out/layout.svg)

- Battery pads on the rear edge, right above the frame's battery lead slot (y = −38 mm).
- All battery current goes through the shunt before it reaches the bus.
- ESC pad pairs on the four chamfered corners, each facing its arm's wire pass. **+ and − swap sides from corner to
  corner** (the pattern is mirrored), so the silkscreen must mark each pad clearly.
- Signal pads S/G on the side strips, close to their ESC corner.
- Copper-free rings (7 mm) round the stack holes, so a metal screw or washer can't short VBAT to GND.
- J1 (to the Kakute) on the front edge, under the Kakute's ESC connector *(verify which edge that connector is on)*.
- The board overhangs the battery-strap bands at x = ±33 mm, but sits 8 mm up on the standoffs, so the straps run under it.

## Parts (first pass)

| Ref | Part | Notes |
|---|---|---|
| R1 | 0.5 mΩ 4-terminal current-sense shunt, ≥ 5 W | e.g. a 2512/3920 metal-strip Kelvin shunt *(verify a real part number and its derating)* |
| U1 | TI INA240A2 (gain 50) | Supply 2.7–5.5 V; run it at 3.3 V so its output can't exceed the Kakute ADC range *(verify)* |
| U2 | 3.3 V LDO, ≥ 40 V input, ~10 mA load | e.g. TI LM2936-3.3 or a TPS7A16-class part *(verify ratings)* |
| D1 | SMDJ28A-class TVS | Off below 28 V, clamps near 45 V *(verify on the datasheet)* |
| C1, C2 | 470 µF 50 V low-ESR electrolytic, 10 × 10 mm SMD | The ESCs have their own caps too |
| D2, R2 | Power LED + resistor | ~2 mA from VBAT |
| J1 | JST-SH 1.0 mm 8-pin, matching the Kakute's ESC cable | Pin order not confirmed (see below) |
| — | 12 AWG pigtail + XT60; 16 AWG to ESCs | |
| U3 (DNP) | 5 V buck footprint for phase 2 | Not fitted. Sized when the companion computer is chosen |

## Things to verify before layout

1. **Kakute H7 v1.5 ESC connector pin order** and which edge it's on. `params.py` has a placeholder order
   (VBAT, GND, CURR, TLM, M1–M4). Copy the real one from Holybro's pinout page.
2. **Kakute current-input scaling**: confirm the CURR pin goes to a 3.3 V ADC and which ArduPilot pin number it uses
   (`BATT_CURR_PIN`).
3. Can the Kakute take its own power through the 8-pin cable's VBAT? It needs ~0.3 A; a JST-SH contact is about
   1 A *(verify)*.
4. Real ratings for the shunt, TVS, LDO and capacitors you pick.
5. Your PCB fab's 4-layer options: some only offer 1 oz inner layers. With 1 oz inside, re-run `calc.py` with
   `OZ_INNER = 1.0`; the bus still fits but the margin shrinks.

## Open decisions (yours)

- **Keep the onboard Kakute BECs only, or add a 5 V / 12 V rail now?** Default: none now, footprint for phase 2.
- **XT60 or XT90 pigtail?** Default: XT60, because both packs use it.
- **Board size.** 60 mm leaves room for the wires. A 50 mm board is possible, but the ESC pads get cramped.
- **Hand-solder or assembled?** Default: the fab assembles the small parts; you solder the wires.

## Bench test plan (once boards arrive)

1. Bare board: check VBAT-to-GND resistance (should read open, not a short) before anything is soldered.
2. Power from a current-limited bench supply at 25 V: LED on, LDO at 3.3 V, CURR output ~0 V.
3. Pass a known current (an electronic load or a resistor bank) and check CURR against a clamp meter;
   tune `BATT_AMP_PERVLT`.
4. Full drone, props off: ArduPilot reads voltage and current.
5. Props on, tethered: run up to full throttle in short bursts and check board hot spots by touch or a thermometer.

## Next steps

1. Answer the open decisions and confirm the Kakute pinout.
2. Create the KiCad project in `pdb/kicad/`: schematic first, then import `out/outline.dxf` as Edge.Cuts.
3. Lay out the board following the placement plan; fill planes per the stack-up; stitch GND pads with via arrays.
4. DRC, then a design review before ordering.
