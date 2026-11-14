# Drone artifacts

The live web pages (claude.ai artifacts) for this build, and how each one links back to the notes and files in this
repository. The full knowledge base is [DRONE.md](DRONE.md). Last updated **2026-11-14**.

All artifacts are private to your claude.ai account until you share them from each page's Share menu.

| Artifact | What it's for | Status |
|---|---|---|
| [Drone Build Bench](https://claude.ai/artifact/PZznX76X35aGoRyHUKSt4b) | Live feed of your Excel workbook: parts, wiring, signals, compatibility, goals | Current |
| [Quad Frame Viewer](https://claude.ai/artifact/TL8M7m7gnEmCRBecsM5XjJ) | 3D model of the printed frame with motors and ESCs, dimensions, comments, lift capacity | Current |
| [Drone Parts Receiving Log](https://claude.ai/artifact/5L8wNSVktLjnAgHyzJEHn1) | Tick off parts as shipments arrive | Current |
| [24-inch Quad Build Guide](https://claude.ai/artifact/5QCyr1wzTm2hUdrVKaoa6E) | Earlier bench sheet: wiring, pin table, tools, flight-time calculator | **Out of date** |
| [RotorLab](https://claude.ai/artifact/3z7vcJqs2KDfVCS5LZy5U3) | General multirotor power and efficiency calculator | Related tool |

---

## Drone Build Bench

<https://claude.ai/artifact/PZznX76X35aGoRyHUKSt4b>

Reads your SharePoint workbook and shows:
- the parts you've bought;
- wiring and signal-flow diagrams;
- a connector table, part-to-part compatibility checks and goal checks;
- spend so far and flight-time estimates.

Its **Update from Excel** button runs a Claude Code scheduled task. The task re-downloads the workbook and republishes
the data, so the page follows the sheet without you saving a copy.

| Built from | Path |
|---|---|
| Page source | [feed/index.html](feed/index.html) |
| Workbook sync | [feed/sync_sheet.py](feed/sync_sheet.py) |
| Synced data (published next to the page) | [feed/data.json](feed/data.json) |
| How it works | [feed/README.md](feed/README.md) |

Covered in DRONE.md:
- [Parts list](DRONE.md#parts-list)
- [Decisions and why](DRONE.md#decisions-and-why)
- [Control and telemetry](DRONE.md#control-and-telemetry)
- [Power and wiring](DRONE.md#power-and-wiring)
- [Connectors, part by part](DRONE.md#connectors-part-by-part)
- [Motor and prop data](DRONE.md#motor-and-prop-data)
- [Data sources](DRONE.md#data-sources)

## Quad Frame Viewer

<https://claude.ai/artifact/TL8M7m7gnEmCRBecsM5XjJ>

The 3D frame in your browser. You can:
- click any part (body, arms, spring legs, GPS mast, motors, ESCs, screws, leads, zip ties, battery) to see its
  dimensions and how it mounts;
- explode the assembly;
- pin comments to any spot.

Two side panels show the clearance check and lift capacity; the lift panel has a payload slider.

| Built from | Path |
|---|---|
| Page source | [frame/viewer/index.html](frame/viewer/index.html) |
| 3D mesh + data (published next to the page) | [frame/viewer/model.json](frame/viewer/model.json), written by [frame/export_viewer.py](frame/export_viewer.py) |
| Dimensions and part sizes | [frame/params.py](frame/params.py) |
| Frame geometry | [frame/build_frame.py](frame/build_frame.py) |
| Motor, ESC and wiring models | [frame/hardware.py](frame/hardware.py) |
| Clearance panel | [frame/clearance.py](frame/clearance.py) → [frame/CLEARANCE.md](frame/CLEARANCE.md), `frame/out/clearance.json` |
| Lift panel | [frame/analysis.py](frame/analysis.py) → [frame/ANALYSIS.md](frame/ANALYSIS.md), `frame/out/lift.json` |
| CAD files for Fusion 360 / slicer | `frame/out/*.step`, `frame/out/*.stl` (open `assembly.step` for the whole drone) |
| Images | [frame/out/assembly.png](frame/out/assembly.png), [frame/out/parts.png](frame/out/parts.png), [frame/out/motor_mount.png](frame/out/motor_mount.png) |
| Print, hardware and assembly guide | [frame/README.md](frame/README.md) |

Covered in DRONE.md:
- [3D-printed frame](DRONE.md#3d-printed-frame)
- [Frame analysis results](DRONE.md#frame-analysis-results)
- [Clearance and tool access](DRONE.md#clearance-and-tool-access)
- [Motor and ESC mounting](DRONE.md#motor-and-esc-mounting)
- [Performance and lift capacity](DRONE.md#performance-and-lift-capacity)
- [Assembly order](DRONE.md#assembly-order)

To refresh it after a design change, run the rebuild command at the end of DRONE.md, then republish
`frame/viewer/index.html` with `model.json`.

## Drone Parts Receiving Log

<https://claude.ai/artifact/5L8wNSVktLjnAgHyzJEHn1>

A checklist of every part to receive. It covers the cart items, the frame hardware and the charger, and has a form
for anything new you order. Ticks are saved in the page's database with the date, so they persist and can be read back.

| Built from | Path |
|---|---|
| Page source | [frame/checklist/index.html](frame/checklist/index.html) |
| Part list | Stored in the artifact's own database (collection `parts`), seeded from the cart sheet and [frame/README.md](frame/README.md) hardware |

Covered in DRONE.md:
- [Build status](DRONE.md#build-status) (snapshot of the log)
- [Parts list](DRONE.md#parts-list)
- Hardware to buy, under [3D-printed frame](DRONE.md#3d-printed-frame)
- [Open items](DRONE.md#open-items)

## 24-inch Quad Build Guide (out of date)

<https://claude.ai/artifact/5QCyr1wzTm2hUdrVKaoa6E>

An earlier bench sheet (2026-10-19), from before most of the decisions in [DRONE.md](DRONE.md#decisions-and-why).
It still assumes:
- the Kakute H7 **v2**;
- the Nomad module plus a separate ELRS receiver;
- a SiK telemetry radio;
- a 5000 mAh battery as the main pack.

Its checklists save only in your browser. Its wiring schematic, tools list and ArduPilot starter parameters are still
useful references, but check each against [Control and telemetry](DRONE.md#control-and-telemetry),
[Power and wiring](DRONE.md#power-and-wiring) and [Before first flight](DRONE.md#before-first-flight) first.

Not built from files in this repository.

## RotorLab

<https://claude.ai/artifact/3z7vcJqs2KDfVCS5LZy5U3>

A general multirotor estimator: momentum theory plus an empirical prop model, with presets and build comparison.
It isn't tied to this build. To use it here, enter the numbers from
[Performance and lift capacity](DRONE.md#performance-and-lift-capacity) and
[Motor and prop data](DRONE.md#motor-and-prop-data). Your Motor sheet's measured thrust data is more reliable than
its estimates.

Not built from files in this repository.

---

## All linked files

| File | Linked from |
|---|---|
| [DRONE.md](DRONE.md) | Every artifact above |
| [feed/README.md](feed/README.md), [feed/index.html](feed/index.html), [feed/sync_sheet.py](feed/sync_sheet.py), [feed/data.json](feed/data.json) | Drone Build Bench |
| [frame/README.md](frame/README.md) | Quad Frame Viewer, Parts Receiving Log |
| [frame/params.py](frame/params.py), [frame/build_frame.py](frame/build_frame.py), [frame/hardware.py](frame/hardware.py), [frame/export_viewer.py](frame/export_viewer.py), [frame/viewer/index.html](frame/viewer/index.html), [frame/viewer/model.json](frame/viewer/model.json) | Quad Frame Viewer |
| [frame/analysis.py](frame/analysis.py), [frame/ANALYSIS.md](frame/ANALYSIS.md) | Quad Frame Viewer (lift panel) |
| [frame/clearance.py](frame/clearance.py), [frame/CLEARANCE.md](frame/CLEARANCE.md) | Quad Frame Viewer (clearance panel) |
| [frame/render.py](frame/render.py), [frame/out/motor_mount.png](frame/out/motor_mount.png) | Quad Frame Viewer, DRONE.md |
| [frame/checklist/index.html](frame/checklist/index.html) | Parts Receiving Log |
