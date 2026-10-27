"""Clearance and tool-access check for the assembled frame. Writes frame/CLEARANCE.md.

Every fastener gets a straight "tool corridor": a cylinder from the screw head out
along the direction you would put the screw in, wide enough for the head plus a hex
key or screwdriver tip. Every cable or strap gets a box along its path. Each one is
intersected with every part of the assembled drone (printed parts plus the battery,
ESCs, motors and prop discs); the overlap must be 0 mm^3.

Run after build_frame.py:  python3 clearance.py
"""
import math
from pathlib import Path

import cadquery as cq

import build_frame as bf
from params import *  # noqa: F403

HERE = Path(__file__).parent
REACH = 150.0                                   # corridor length: a full screwdriver


def rot(s, ang):
    return s.rotate((0, 0, 0), (0, 0, 1), ang)


def cyl(d, length, at, axis=(0, 0, 1)):
    """Cylinder of diameter d from point `at` along `axis` (unit, any direction) for `length`."""
    return cq.Workplane(cq.Plane(origin=at, xDir=_perp(axis), normal=axis)).circle(d / 2).extrude(length)


def _perp(axis):
    x, y, z = axis
    return (1, 0, 0) if abs(x) < 0.9 else (0, 1, 0)


def world():
    """Every solid in the assembled drone, by name."""
    parts = {"body": bf.body(), "arm": bf.arm(), "leg": bf.leg(), "mast": bf.mast()}
    w = {"body": parts["body"], "mast": bf.place_mast(parts["mast"])}
    bx, by, bz = BATTERY
    w["battery"] = cq.Workplane("XY").box(bx, by, bz, centered=(True, True, False)).translate((0, 0, -bz))
    pad_top = FLOOR + FIT + ARM_H_TIP
    h_esc = ARM_H_ROOT + (ARM_H_TIP - ARM_H_ROOT) * (ESC_R - ARM_R0) / (MOTOR_R - ARM_R0)
    for i, ang in enumerate(bf.ARM_ANGLES, 1):
        w[f"arm {i}"] = bf.place_arm(parts["arm"], ang)
        w[f"leg {i}"] = bf.place_leg(parts["leg"], ang)
        w[f"ESC {i}"] = rot(cq.Workplane("XY").box(ESC_L - 1, ESC_W - 1, ESC_T, centered=(True, True, False))
                            .translate((ESC_R, 0, FLOOR + FIT + h_esc - ESC_POCKET_DEPTH)), ang)
        # 5010 motor: ~58 mm bell, ~32 mm tall above the pad (estimate); prop disc above it.
        w[f"motor {i}"] = rot(cyl(58, 32, (MOTOR_R, 0, pad_top)), ang)
        w[f"prop {i}"] = rot(cyl(PROP_D, 8, (MOTOR_R, 0, pad_top + 36)), ang)
    return parts, w


def overlap(a, b):
    ba, bb = a.val().BoundingBox(), b.val().BoundingBox()
    if ba.xmax < bb.xmin or bb.xmax < ba.xmin or ba.ymax < bb.ymin or bb.ymax < ba.ymin or ba.zmax < bb.zmin or bb.zmax < ba.zmin:
        return 0.0
    return a.val().intersect(b.val()).Volume()


def corridors():
    """(group, what it checks, solid, names of solids it must not touch; None = everything)."""
    out = []
    h = BODY_H
    gw, gd = WIRE_GROOVE
    for i, ang in enumerate(bf.ARM_ANGLES, 1):
        tag = f"arm {i}"
        # Arm-to-body bolts: M3 x 40 up from under the body, through floor + arm, into the roof insert.
        for x, y in JOINT_BOLTS:
            p = (ARM_R0 + x, y, 0)
            out.append(("Arm-to-body bolts (M3 x 40, from below)", f"{tag}: bolt line through floor, arm and roof",
                        rot(cyl(3.0, h, p), ang), ["body", tag]))
            out.append(("Arm-to-body bolts (M3 x 40, from below)", f"{tag}: head + driver from below",
                        rot(cyl(TOOL_D, REACH, p, (0, 0, -1)), ang), None))
            out.append(("Heat-set inserts (soldering iron from above)", f"{tag}: roof insert",
                        rot(cyl(10, 100, (ARM_R0 + x, y, h)), ang), None))
        # Leg bolts: M3 x 8 up through the leg pad into the arm-underside inserts.
        for dx in (-LEG_BOLT_SPACING / 2, LEG_BOLT_SPACING / 2):
            z_cb = FLOOR + FIT - 3                          # top of the counterbore (head seat)
            p = (LEG_R + dx, 0, z_cb)
            out.append(("Leg bolts (M3 x 8, from below)", f"{tag}: bolt line through leg pad into insert",
                        rot(cyl(3.0, 3 + 5.5, p), ang), [f"leg {i}", tag]))
            out.append(("Leg bolts (M3 x 8, from below)", f"{tag}: head into its counterbore",
                        rot(cyl(HEAD_D, 3, p, (0, 0, -1)), ang), None))
            out.append(("Leg bolts (M3 x 8, from below)", f"{tag}: driver from below the leg pad",
                        rot(cyl(TOOL_D, REACH, (p[0], 0, z_cb - 3), (0, 0, -1)), ang), None))
            out.append(("Heat-set inserts (soldering iron from below)", f"{tag}: leg insert in arm underside",
                        rot(cyl(10, 60, (LEG_R + dx, 0, FLOOR + FIT), (0, 0, -1)), ang), [tag, "body", "battery"]))
        # Motor screws: up through the pad from inside the pocket. Worst case = outer end of each slot.
        pad_bottom = FLOOR + FIT + ARM_H_TIP - PAD_T
        for k in range(0, 360, 45):
            for r in (MOTOR_SLOT_R[0], MOTOR_SLOT_R[1]):
                p = (MOTOR_R + r * math.cos(math.radians(k)), r * math.sin(math.radians(k)), pad_bottom)
                out.append(("Motor screws (M3, from under the pad)", f"{tag}: slot {k} deg, r = {r} mm",
                            rot(cyl(HEAD_D, REACH, p, (0, 0, -1)), ang), None))
        # ESC wires: along the top channel, under the roof, through the bulkhead opening, down into the bay.
        floor0 = FLOOR + FIT + ARM_H_ROOT - gd + 0.3     # channel floor at the root (world z)
        bundle_h = 5.5                                   # 2 x 16 AWG silicone (~2.9 mm) + signal lead
        out.append(("ESC wire path (10 x 5.5 mm bundle)", f"{tag}: along the channel under the body roof",
                    rot(cq.Workplane("XY").box(SOCKET_TIP_R - ARM_R0, 10, bundle_h, centered=(False, True, False))
                        .translate((ARM_R0, 0, floor0)), ang), ["body", tag]))
        out.append(("ESC wire path (10 x 5.5 mm bundle)", f"{tag}: out of the arm through the bulkhead opening",
                    rot(cq.Workplane("XY").box(12, 10, bundle_h, centered=(False, True, False))
                        .translate((ARM_R0 - 12, 0, floor0)), ang), ["body", tag]))
        out.append(("ESC wire path (10 x 5.5 mm bundle)", f"{tag}: down the pocket to the bay floor",
                    rot(cq.Workplane("XY").box(10, 10, floor0 + bundle_h - FLOOR - 1, centered=(False, True, False))
                        .translate((CORE / 2 - WALL - 4, 0, FLOOR + 1)), ang), ["body", tag]))

    # Flight-controller stack bolts: M3 x 20 down from above.
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append(("Stack bolts (M3, from above)", f"({sx * STACK / 2:+.2f}, {sy * STACK / 2:+.2f})",
                        cyl(TOOL_D, REACH, (sx * STACK / 2, sy * STACK / 2, STACK_TOP)), None))
            out.append(("Heat-set inserts (soldering iron from above)", "stack standoff",
                        cyl(10, 100, (sx * STACK / 2, sy * STACK / 2, FLOOR + 8.0)), None))
    # GPS mast lock screw, from the rear.
    rear = MAST_X - MAST_BOSS_D / 2
    out.append(("GPS mast", "lock screw: head + driver from the rear", cyl(TOOL_D, REACH, (rear, 0, h - 10), (-1, 0, 0)), None))
    out.append(("GPS mast", "lock screw line through the insert to the mast flat",
                cyl(3.0, MAST_BOSS_D / 2 - MAST_D / 2 + 0.6, (rear, 0, h - 10), (1, 0, 0)), ["body"]))
    out.append(("GPS mast", "GPS cable down the mast bore (6.5 mm plug)",
                cyl(6.5, MAST_L + 3, (MAST_X, 0, h - MAST_SOCKET_DEPTH + 0.5)), ["mast", "body"]))
    out.append(("GPS mast", "GPS cable from under the mast into the bay (6.5 x 5 mm)",
                cq.Workplane("XY").box(-(CORE / 2 - WALL) + 4 - MAST_X, 6.5, 5, centered=(False, True, False))
                .translate((MAST_X, 0, h - MAST_SOCKET_DEPTH + 0.5)), ["body"]))
    # Battery strap: 20 mm Velcro (22 x 1.5 band) across the bay floor and down through both slots.
    for sx in (-STRAP_X, STRAP_X):
        side = "rear" if sx < 0 else "front"
        out.append(("Battery straps (20 mm)", f"{side} strap across the bay floor",
                    cq.Workplane("XY").box(STRAP[0] - 1, 72 + STRAP[1] - 1, 1.5, centered=(True, True, False))
                    .translate((sx, 0, FLOOR + 0.1)), ["body", "mast"]))
        for sy in (-36, 36):
            out.append(("Battery straps (20 mm)", f"{side} strap through the floor slot at y = {sy}",
                        cq.Workplane("XY").box(STRAP[0] - 1, 1.5, FLOOR + 2).translate((sx, sy, FLOOR / 2)), ["body"]))
    # Connectors through the body.
    out.append(("Connectors", "battery lead: XT60 plug (16 x 8.5) down through the floor slot",
                cq.Workplane("XY").box(16, 8.5, FLOOR + 10).translate((0, -38, FLOOR / 2)), ["body"]))
    out.append(("Connectors", "USB-C plug (12.5 x 7) through the side window",
                cq.Workplane("XY").box(12.5, WALL * 4, 7).translate((0, -CORE / 2 + WALL / 2, FLOOR + STANDOFF_H + 14)), ["body"]))
    return out


def walls():
    """Thinnest plastic left between neighbouring holes (arithmetic, from params)."""
    gw = WIRE_GROOVE[0]
    rows = []
    jy = min(abs(y) for _, y in JOINT_BOLTS)
    rows.append(("Joint bolt hole to wire channel (arm)", jy - SCREW_CLEAR_D / 2 - gw / 2))
    rows.append(("Joint bolt hole to arm side (before the 2 mm edge fillet)", ARM_W / 2 - jy - SCREW_CLEAR_D / 2))
    # Leg inserts vs lightening slots along the arm (slot ends are 4 mm inside each span).
    gaps = []
    for dx in (-LEG_BOLT_SPACING / 2, LEG_BOLT_SPACING / 2):
        xi = LEG_R - ARM_R0 + dx
        for x0, x1 in LIGHTEN_SPANS:
            gaps.append(max(x0 + 4 - xi, xi - (x1 - 4)) - INSERT_HOLE_D / 2)
    rows.append(("Leg insert hole to nearest lightening slot (along the arm)", min(gaps)))
    rows.append(("Mast lock insert (5.7 mm) to mast socket", MAST_BOSS_D / 2 - MAST_SOCKET_D / 2 - 5.7))
    rows.append(("Motor screw head (outer slot end) to pad pocket wall", PAD_POCKET_D / 2 - MOTOR_SLOT_R[1] - HEAD_D / 2))
    rows.append(("Leg bolt head to strut gusset", LEG_BOLT_SPACING / 2 - HEAD_D / 2 - (LEG_T / 2 + 3)))
    rows.append(("Leg bolt head to foot", LEG_BOLT_SPACING / 2 - HEAD_D / 2 - LEG_FOOT[0] / 2))
    rows.append(("Strap slot to bay wall", (CORE / 2 - WALL) - (STRAP_X + STRAP[0] / 2)))
    return rows


def run():
    parts, w = world()
    results = []
    for group, what, solid, only in corridors():
        names = only if only is not None else list(w)
        hits = {n: overlap(solid, w[n]) for n in names}
        bad = {n: round(v, 1) for n, v in hits.items() if v > 0.05}
        results.append((group, what, bad))
    # Part-to-part: printed parts and hardware must not touch except where they are meant to sit.
    pairs = [("mast", "battery"), ("mast", "prop 2"), ("mast", "prop 3"), ("body", "battery")]
    for i in range(1, 5):
        pairs += [(f"leg {i}", "battery"), (f"prop {i}", "body"), (f"prop {i}", f"ESC {i}"), (f"arm {i}", "battery")]
        pairs += [(f"prop {i}", f"prop {j}") for j in range(i + 1, 5)]
    for a, b in pairs:
        v = overlap(w[a], w[b])
        results.append(("Part to part", f"{a} vs {b}", {b: round(v, 1)} if v > 0.05 else {}))
    for i, ang in enumerate(bf.ARM_ANGLES, 1):
        v = overlap(w["body"], w[f"arm {i}"])
        results.append(("Part to part", f"arm {i} in its body tunnel", {"body": round(v, 1)} if v > 0.05 else {}))

    batt_bottom = -BATTERY[2]
    foot_bottom = FLOOR + FIT - LEG_H
    groups = {}
    for g, what, bad in results:
        groups.setdefault(g, []).append((what, bad))
    lines = ["# Clearance and tool-access check", "",
             "Generated by `frame/clearance.py` from the CAD. Each tool path is a straight cylinder from the screw head",
             f"outward ({REACH:.0f} mm, a full screwdriver), {TOOL_D:.0f} mm wide for an M3 head ({HEAD_D} mm) plus the driver tip.",
             "Cable and strap paths are boxes the size of the bundle. Each is intersected with every printed part, the battery",
             f"({BATTERY[0]:.0f} x {BATTERY[1]:.0f} x {BATTERY[2]:.0f} mm, estimated), the ESCs, the motors and the prop discs. Pass = 0 mm³ overlap.", "",
             "| Check | Paths | Result |", "|---|---|---|"]
    fails = 0
    for g, items in groups.items():
        nbad = sum(1 for _, b in items if b)
        fails += nbad
        lines.append(f"| {g} | {len(items)} | {'all clear' if not nbad else f'**{nbad} blocked**'} |")
    lines += ["", "## Blocked paths", ""]
    blocked = [(g, what, bad) for g, what, bad in results if bad]
    lines += [f"- {g}: {what} hits " + ", ".join(f"{n} ({v} mm³)" for n, v in bad.items()) for g, what, bad in blocked] or ["None."]
    lines += ["", "## Thinnest walls between holes", "", "| Between | mm |", "|---|---|"]
    lines += [f"| {k} | {v:.1f} |" for k, v in walls()]
    lines += ["", "## Other clearances", "", "| Item | mm |", "|---|---|",
              f"| Ground clearance under the battery (legs {LEG_H:.0f} mm) | {batt_bottom - foot_bottom:.1f} |",
              f"| Gap between neighbouring prop tips | {WHEELBASE / math.sqrt(2) - PROP_D:.1f} |",
              f"| Prop disc inner edge to body tip (radius) | {MOTOR_R - PROP_D / 2 - SOCKET_TIP_R:.1f} |",
              f"| Prop disc inner edge to GPS mast | {math.hypot(MOTOR_R * math.cos(math.radians(135)) - MAST_X, MOTOR_R * math.sin(math.radians(135))) - PROP_D / 2 - GPS_PLATE / math.sqrt(2):.1f} |",
              "", "## Order of assembly (so every screw stays reachable)", "",
              "1. Inserts first: all heat-set inserts go in before anything is attached.",
              "2. Motors onto the arms (screws from under the pad), then ESCs and zip ties.",
              "3. Arms into the body; joint bolts from underneath, with the battery off.",
              "4. Power board and Kakute from above; stack bolts from above.",
              "5. Legs: drone upside down, bolts straight up into the arm undersides.",
              "6. GPS mast into its socket at the back; lock screw from the rear.",
              "7. Battery last, strapped underneath."]
    (HERE / "CLEARANCE.md").write_text("\n".join(lines) + "\n")
    import json
    (HERE / "out" / "clearance.json").write_text(json.dumps({
        "groups": [{"name": g, "paths": len(items), "blocked": sum(1 for _, b in items if b)} for g, items in groups.items()],
        "walls": [[k, round(v, 1)] for k, v in walls()],
        "ground_mm": round(batt_bottom - foot_bottom, 1)}))
    return results, fails


if __name__ == "__main__":
    results, fails = run()
    for g, what, bad in results:
        if bad:
            print("BLOCKED", g, "|", what, "|", bad)
    print(f"{len(results)} checks, {fails} blocked")
