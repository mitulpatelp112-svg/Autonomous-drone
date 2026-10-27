"""Parametric 680 mm quad frame: 1 body + 4 arms (+ 4 bolt-on legs and a GPS mast).

Run:  python3 frame/build_frame.py
Writes STEP (for Fusion 360) and STL (for the slicer) to frame/out/, plus
frame/out/report.json with part masses and build-plate fit checks.

Coordinates: frame centre at the origin, +X is forward, +Z is up, z = 0 is the
underside of the body. Arms sit on the diagonals (45, 135, 225, 315 degrees).
"""
import json
import math
from pathlib import Path

import cadquery as cq

from params import *  # noqa: F403  (one flat namespace of dimensions)

OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)
ARM_ANGLES = (45, 135, 225, 315)
ARM_LEN = MOTOR_R - ARM_R0      # root to motor centre


def arm():
    """One arm, built along +X with the root at x = 0 and the motor at x = ARM_LEN."""
    # Side profile tapers from the root height to the tip height.
    side = (cq.Workplane("XZ")
            .polyline([(0, 0), (ARM_LEN, 0), (ARM_LEN, ARM_H_TIP), (0, ARM_H_ROOT)]).close()
            .extrude(ARM_W / 2, both=True))
    pad = cq.Workplane("XY").center(ARM_LEN, 0).circle(PAD_D / 2).extrude(ARM_H_TIP)
    a = side.union(pad)

    # Hollow under the motor pad so the motor screws can be reached from below.
    a = a.cut(cq.Workplane("XY").center(ARM_LEN, 0).circle(PAD_POCKET_D / 2).extrude(ARM_H_TIP - PAD_T))
    a = a.cut(cq.Workplane("XY").center(ARM_LEN, 0).circle(MOTOR_CENTER_HOLE_D / 2).extrude(ARM_H_TIP + 1))
    # Radial slots for the motor screws (8 directions covers cross and square patterns).
    r1, r2 = MOTOR_SLOT_R
    for ang in range(0, 360, 45):
        slot = (cq.Workplane("XY").slot2D(r2 - r1 + SCREW_CLEAR_D, SCREW_CLEAR_D)
                .extrude(ARM_H_TIP + 1)
                .translate(((r1 + r2) / 2, 0, 0))
                .rotate((0, 0, 0), (0, 0, 1), ang)
                .translate((ARM_LEN, 0, 0)))
        a = a.cut(slot)

    # ESC recess on top, plus two zip-tie slots straight through the arm.
    esc_x = ESC_R - ARM_R0
    h_at = lambda x: ARM_H_ROOT + (ARM_H_TIP - ARM_H_ROOT) * x / ARM_LEN
    top = h_at(esc_x)
    a = a.cut(cq.Workplane("XY").box(ESC_L, ESC_W, ESC_POCKET_DEPTH * 2)
              .translate((esc_x, 0, top)))
    for dx in (-ESC_L / 2 + 8, ESC_L / 2 - 8):
        z = h_at(esc_x + dx) - ESC_POCKET_DEPTH - ZIP_SLOT[1] / 2 - 2.5
        a = a.cut(cq.Workplane("XY").box(ZIP_SLOT[0], ARM_W + 2, ZIP_SLOT[1]).translate((esc_x + dx, 0, z)))

    # Wire channel along the top, from the back of the ESC to the root (runs under the body roof).
    gw, gd = WIRE_GROOVE
    groove_end = esc_x - ESC_L / 2 + 2
    groove = (cq.Workplane("XZ")
              .polyline([(-1, ARM_H_ROOT - gd), (groove_end, h_at(groove_end) - gd),
                         (groove_end, ARM_H_ROOT + 5), (-1, ARM_H_ROOT + 5)]).close()
              .extrude(gw / 2, both=True))
    a = a.cut(groove)

    # Lightening slots through the web, near the neutral axis where they cost the least stiffness.
    for x0, x1 in LIGHTEN_SPANS:
        n = max(1, int((x1 - x0) // 28))
        pitch = (x1 - x0) / n
        for k in range(n):
            cx = x0 + pitch * (k + 0.5)
            hz = h_at(cx)
            a = a.cut(cq.Workplane("XZ").center(cx, hz * 0.45).slot2D(pitch - 8, hz * 0.38).extrude(ARM_W / 2 + 1, both=True))

    # Arm-to-body bolts (clearance; the inserts are in the body roof), either side of the wire channel.
    for x, y in JOINT_BOLTS:
        a = a.cut(cq.Workplane("XY").center(x, y).circle(SCREW_CLEAR_D / 2).extrude(ARM_H_ROOT + 2).translate((0, 0, -1)))
    # Leg inserts in the arm underside.
    for dx in (-LEG_BOLT_SPACING / 2, LEG_BOLT_SPACING / 2):
        a = a.cut(cq.Workplane("XY").center(LEG_R - ARM_R0 + dx, 0).circle(INSERT_HOLE_D / 2).extrude(INSERT_DEPTH))
    # Soften the outer edges a little (also saves plastic).
    try:
        a = a.edges("|X").fillet(2.0)
    except Exception:
        pass
    return a


def body():
    h = BODY_H
    core = cq.Workplane("XY").box(CORE, CORE, h, centered=(True, True, False))
    b = core
    for ang in ARM_ANGLES:
        boss_len = SOCKET_TIP_R - BOSS_W / 2 - 30
        boss = (cq.Workplane("XY").box(boss_len, BOSS_W, h, centered=(False, True, False)).translate((30, 0, 0))
                .union(cq.Workplane("XY").center(SOCKET_TIP_R - BOSS_W / 2, 0).circle(BOSS_W / 2).extrude(h)))
        b = b.union(boss.rotate((0, 0, 0), (0, 0, 1), ang))

    # Electronics bay (open top).
    inner = CORE - 2 * WALL
    b = b.cut(cq.Workplane("XY").box(inner, inner, h, centered=(True, True, False)).translate((0, 0, FLOOR)))

    for ang in ARM_ANGLES:
        rot = lambda s: s.rotate((0, 0, 0), (0, 0, 1), ang)
        # Tunnel the arm slides into (bridged roof prints fine at this width).
        tunnel = cq.Workplane("XY").box(SOCKET_TIP_R + 10 - ARM_R0, ARM_W + 2 * FIT, ARM_H_ROOT + 2 * FIT,
                                        centered=(False, True, False)).translate((ARM_R0, 0, FLOOR))
        b = b.cut(rot(tunnel))
        # Hollow the boss between the bay and the tunnel (open top), leaving a bulkhead at the tunnel end.
        pocket = cq.Workplane("XY").box(ARM_R0 - 4 - (CORE / 2 - WALL), BOSS_W - 2 * WALL, h,
                                        centered=(False, True, False)).translate((CORE / 2 - WALL, 0, FLOOR))
        b = b.cut(rot(pocket))
        # Wire opening in the bulkhead, level with the arm's top channel and open at the top, so the
        # ESC leads drop straight from the channel into the pocket and on to the bay (and can be laid in from above).
        wire = (cq.Workplane("XY").box(ARM_R0 - (CORE / 2 - WALL), WIRE_PASS[0], h, centered=(False, True, False))
                .translate((CORE / 2 - WALL, 0, WIRE_PASS[1])))
        b = b.cut(rot(wire))
        # Joint bolts: clearance through the floor, insert in the roof.
        for x, y in JOINT_BOLTS:
            bx = ARM_R0 + x
            b = b.cut(rot(cq.Workplane("XY").center(bx, y).circle(SCREW_CLEAR_D / 2).extrude(FLOOR + 1).translate((0, 0, -0.5))))
            b = b.cut(rot(cq.Workplane("XY").center(bx, y).circle(INSERT_HOLE_D / 2).extrude(INSERT_DEPTH + 1).translate((0, 0, h - INSERT_DEPTH))))
            b = b.cut(rot(cq.Workplane("XY").center(bx, y).circle(SCREW_CLEAR_D / 2).extrude(ROOF + 1).translate((0, 0, h - ROOF - 0.5))))

    # Stack standoffs (power board + Kakute H7 v1.5 on 30.5 mm) with M3 inserts.
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = (sx * STACK / 2, sy * STACK / 2)
            b = b.union(cq.Workplane("XY").center(*p).circle(4.5).extrude(STANDOFF_H).translate((0, 0, FLOOR)))
            b = b.cut(cq.Workplane("XY").center(*p).circle(INSERT_HOLE_D / 2).extrude(INSERT_DEPTH).translate((0, 0, FLOOR + STANDOFF_H - INSERT_DEPTH)))

    # Battery strap slots (2 straps across the body) and the battery lead hole.
    for sx in (-STRAP_X, STRAP_X):
        for sy in (-36, 36):
            b = b.cut(cq.Workplane("XY").box(STRAP[0], STRAP[1], FLOOR * 3).translate((sx, sy, 0)))
    b = b.cut(cq.Workplane("XY").box(LEAD_SLOT[0], LEAD_SLOT[1], FLOOR * 3).translate((0, -38, 0)))

    # GPS mast socket on the OUTSIDE of the rear wall (keeps the bay floor clear for the battery strap).
    # Lock screw goes in from the back; the GPS cable turns under the mast and enters the bay through the wall.
    b = b.union(cq.Workplane("XY").center(MAST_X, 0).circle(MAST_BOSS_D / 2).extrude(h))
    b = b.cut(cq.Workplane("XY").center(MAST_X, 0).circle(MAST_SOCKET_D / 2).extrude(MAST_SOCKET_DEPTH)
              .translate((0, 0, h - MAST_SOCKET_DEPTH)))
    rear = MAST_X - MAST_BOSS_D / 2
    b = b.cut(cq.Workplane("YZ").circle(INSERT_HOLE_D / 2).extrude(INSERT_DEPTH).translate((rear, 0, h - 10)))
    b = b.cut(cq.Workplane("YZ").circle(SCREW_CLEAR_D / 2).extrude(MAST_BOSS_D / 2).translate((rear, 0, h - 10)))
    cable_z0 = h - MAST_SOCKET_DEPTH
    b = b.cut(cq.Workplane("XY").box(-(CORE / 2 - WALL) + 1 - MAST_X, 9, MAST_LOCK_GAP, centered=(False, True, False))
              .translate((MAST_X, 0, cable_z0)))

    # Receiver antenna holes in the front wall, and USB access on the side.
    for y in (-15, 15):
        b = b.cut(cq.Workplane("YZ").center(y, h - 8).circle(2.2).extrude(WALL * 3).translate((CORE / 2 - WALL * 2, 0, 0)))
    b = b.cut(cq.Workplane("XY").box(16, WALL * 3, 10).translate((0, -CORE / 2 + WALL / 2, FLOOR + STANDOFF_H + 14)))
    return b


def leg():
    """Bolt-on leg in its own frame: mount face at z = 0, +X points outward along the arm.
    Vertical strut with a gusset under the pad; both bolts sit outside the strut and foot so a
    driver goes straight up to them."""
    t, p = LEG_T, LEG_PAD_L / 2
    prof = [(-p, 0), (p, 0), (p, -6), (t / 2 + 3, -6), (t / 2, -26), (t / 2, -LEG_H + 4),
            (-t / 2, -LEG_H + 4), (-t / 2, -26), (-t / 2 - 3, -6), (-p, -6)]
    l = cq.Workplane("XZ").polyline(prof).close().extrude(LEG_WIDTH / 2, both=True)
    l = l.union(cq.Workplane("XY").box(LEG_FOOT[0], LEG_FOOT[1], 4, centered=(True, True, False)).translate((0, 0, -LEG_H)))
    for dx in (-LEG_BOLT_SPACING / 2, LEG_BOLT_SPACING / 2):
        l = l.cut(cq.Workplane("XY").center(dx, 0).circle(SCREW_CLEAR_D / 2).extrude(-7))
        l = l.cut(cq.Workplane("XY").center(dx, 0).circle(3.2).extrude(-3).translate((0, 0, -6 + 3)))
    return l


def mast():
    m = cq.Workplane("XY").circle(MAST_D / 2).extrude(MAST_L)
    m = m.union(cq.Workplane("XY").box(GPS_PLATE, GPS_PLATE, 3, centered=(True, True, False)).translate((0, 0, MAST_L)))
    m = m.cut(cq.Workplane("XY").circle(MAST_BORE_D / 2).extrude(MAST_L + 5))      # cable bore (SH1.0 plug passes)
    m = m.cut(cq.Workplane("XY").box(8, 30, 6).translate((0, 0, MAST_L - 8)))      # cable exit window
    m = m.cut(cq.Workplane("XY").box(2, 20, 20).translate((-(MAST_D / 2 + 0.2), 0, 10)))  # flat for the lock screw (faces the rear)
    return m


def place_arm(a, ang):
    return a.translate((ARM_R0, 0, FLOOR + FIT)).rotate((0, 0, 0), (0, 0, 1), ang)


def place_leg(l, ang):
    return l.translate((LEG_R, 0, FLOOR + FIT)).rotate((0, 0, 0), (0, 0, 1), ang)


def place_mast(m):
    return m.translate((MAST_X, 0, BODY_H - 20))


def fit_on_bed(shape):
    """Smallest axis-aligned footprint over all rotations about Z (1 degree steps)."""
    best = None
    for deg in range(0, 180):
        bb = shape.rotate((0, 0, 0), (0, 0, 1), deg).val().BoundingBox()
        side = max(bb.xlen, bb.ylen)
        if best is None or side < best[1]:
            best = (deg, side, bb.xlen, bb.ylen, bb.zlen)
    return best


def best_lay(shape, name):
    """Pick a flat face to print on: arms and body print as modelled; legs print on their side."""
    if name == "leg":
        return shape.rotate((0, 0, 0), (1, 0, 0), 90)
    if name == "mast":
        return shape.rotate((0, 0, 0), (1, 0, 0), 180)   # GPS plate on the bed, tube standing up
    return shape


if __name__ == "__main__":
    parts = {"body": body(), "arm": arm(), "leg": leg(), "mast": mast()}
    report = {"parts": {}}
    for name, shp in parts.items():
        cq.exporters.export(shp, str(OUT / f"{name}.step"))
        cq.exporters.export(shp, str(OUT / f"{name}.stl"), tolerance=0.05, angularTolerance=0.1)
        vol_cm3 = shp.val().Volume() / 1000
        deg, side, xl, yl, zl = fit_on_bed(best_lay(shp, name))
        report["parts"][name] = {
            "count": {"body": 1, "arm": 4, "leg": 4, "mast": 1}[name],
            "solid_volume_cm3": round(vol_cm3, 1),
            "est_mass_g": round(vol_cm3 * PETG_DENSITY * PRINT_FILL, 1),
            "print_rotation_deg": deg, "footprint_mm": [round(xl, 1), round(yl, 1)], "height_mm": round(zl, 1),
            "fits_bed": side <= BED - 2 * BED_MARGIN,
        }

    asm = cq.Assembly(name="quad_frame_680")
    asm.add(parts["body"], name="body", color=cq.Color(0.20, 0.22, 0.25))
    for i, ang in enumerate(ARM_ANGLES):
        asm.add(place_arm(parts["arm"], ang), name=f"arm_{i + 1}", color=cq.Color(0.05, 0.42, 0.48))
        asm.add(place_leg(parts["leg"], ang), name=f"leg_{i + 1}", color=cq.Color(0.55, 0.57, 0.6))
    asm.add(place_mast(parts["mast"]), name="gps_mast", color=cq.Color(0.55, 0.57, 0.6))
    asm.save(str(OUT / "assembly.step"))

    # Interference check: arms must not touch the body except through the clearance.
    clash = {}
    b = parts["body"].val()
    for ang in ARM_ANGLES:
        inter = b.intersect(place_arm(parts["arm"], ang).val())
        clash[f"arm_{ang}"] = round(inter.Volume(), 3)
    report["interference_mm3"] = clash
    report["prop_tip_gap_mm"] = round(WHEELBASE / math.sqrt(2) - PROP_D, 1)
    report["prop_inner_radius_mm"] = round(MOTOR_R - PROP_D / 2, 1)
    report["body_tip_radius_mm"] = SOCKET_TIP_R
    (OUT / "report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
