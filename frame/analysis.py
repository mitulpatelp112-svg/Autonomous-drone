"""Forces, moments and stresses for the 680 mm PETG frame. Writes frame/ANALYSIS.md.

Run after build_frame.py (it reads the part masses from out/report.json).
Printed-part model: 4 walls (1.8 mm) of solid PETG around 25% gyroid infill,
which carries ~20% of solid stiffness. Stresses are compared with PETG strength
divided by the safety factor in params.py.
"""
import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import Point, Polygon, box
from shapely import contains_xy, distance

from params import *  # noqa: F403

G = 9.81
HERE = Path(__file__).parent
rep = json.loads((HERE / "out" / "report.json").read_text())
frame_g = sum(p["est_mass_g"] * p["count"] for p in rep["parts"].values())

# --- Masses (g). Sources: product pages / your sheets; "est" = my estimate -------
COMPONENTS = {
    "Frame (printed, from CAD volume)": frame_g,
    "4 x 5010 360KV motor (listing: 80 g)": 4 * 80,
    "4 x 30 A ESC (est. 25 g)": 4 * 25,
    "4 x 16-inch carbon prop (est. 22 g)": 4 * 22,
    "Kakute H7 v1.5 (8 g, Holybro)": 8,
    "Power board with XT60 (11 g, listing)": 11,
    "RP3 receiver (4.6 g, RadioMaster)": 4.6,
    "SEQURE M10 GPS (12 g, SEQURE)": 12,
    "Finder buzzer (est. 4 g)": 4,
    "Wiring, inserts, bolts, straps (est.)": 90,
    "HOOVO 6S 6200 mAh (837 g, listing)": 837,
    "Payload (mission: 200 g)": 200,
}
AUW_G = sum(COMPONENTS.values())
W_N = AUW_G / 1000 * G
T_MAX = THRUST_MAX_G / 1000 * G
T_HOVER = W_N / 4

ARM_LEN = MOTOR_R - ARM_R0
SUPPORT_X = SOCKET_TIP_R - ARM_R0          # where the arm leaves the body tunnel
h_at = lambda x: ARM_H_ROOT + (ARM_H_TIP - ARM_H_ROOT) * x / ARM_LEN
ESC_X = ESC_R - ARM_R0
GROOVE_END = ESC_X - ESC_L / 2 + 2
WALLS, INFILL_STIFF = 1.8, 0.2


def section(x):
    """Arm cross-section (y, z) at distance x from the root, as built in build_frame.arm()."""
    h = h_at(x)
    s = box(-ARM_W / 2, 0, ARM_W / 2, h)
    if x < GROOVE_END:
        s = s.difference(box(-WIRE_GROOVE[0] / 2, h - WIRE_GROOVE[1], WIRE_GROOVE[0] / 2, h + 1))
    if abs(x - ESC_X) < ESC_L / 2:
        s = s.difference(box(-ESC_W / 2, h - ESC_POCKET_DEPTH, ESC_W / 2, h + 1))
    for x0, x1 in LIGHTEN_SPANS:
        n = max(1, int((x1 - x0) // 28)); pitch = (x1 - x0) / n
        for k in range(n):
            cx = x0 + pitch * (k + 0.5)
            L, H = pitch - 8, h_at(cx) * 0.38
            r = H / 2
            dx = abs(x - cx)
            if dx <= L / 2 - r:
                half = r
            elif dx < L / 2:
                half = math.sqrt(max(r * r - (dx - (L / 2 - r)) ** 2, 0))
            else:
                continue
            zc = h_at(cx) * 0.45
            s = s.difference(box(-ARM_W, zc - half, ARM_W, zc + half))
    return s


def props(poly, step=0.15):
    """Area, centroid and effective bending stiffness I (mm^4) with shell + infill weighting."""
    minx, miny, maxx, maxy = poly.bounds
    ys, zs = np.meshgrid(np.arange(minx, maxx, step) + step / 2, np.arange(miny, maxy, step) + step / 2)
    ys, zs = ys.ravel(), zs.ravel()
    inside = contains_xy(poly, ys, zs)
    ys, zs = ys[inside], zs[inside]
    d = distance(poly.boundary, [Point(a, b) for a, b in zip(ys, zs)])
    w = np.where(d <= WALLS, 1.0, INFILL_STIFF) * step * step
    zc = (w * zs).sum() / w.sum()
    I = (w * (zs - zc) ** 2).sum()
    c = max(zs.max() - zc, zc - zs.min())
    return {"area_eff": w.sum(), "zc": zc, "I": I, "c": c}


# --- Arm bending under full thrust ---------------------------------------------
xs = np.arange(SUPPORT_X, ARM_LEN - PAD_D / 2 + 0.1, 2.0)
rows = []
for x in xs:
    p = props(section(x))
    M = T_MAX * (ARM_LEN - x)                    # N*mm
    rows.append((x, p["I"], M, M * p["c"] / p["I"]))
rows = np.array(rows)
crit = rows[rows[:, 3].argmax()]
allow_xy = PETG_UTS_XY / SAFETY_FACTOR

# Tip deflection by integrating curvature twice (cantilever from the tunnel exit).
E = PETG_E
def tip_deflection(F):
    x = rows[:, 0]; I = rows[:, 1]
    kappa = F * (ARM_LEN - x) / (E * I)
    slope = np.concatenate([[0], np.cumsum((kappa[1:] + kappa[:-1]) / 2 * np.diff(x))])
    defl = np.concatenate([[0], np.cumsum((slope[1:] + slope[:-1]) / 2 * np.diff(x))])
    # pad region beyond the last station: rigid extension
    return defl[-1] + slope[-1] * (ARM_LEN - x[-1]), x, defl
d_max, _, shape = tip_deflection(T_MAX)
d_hover, _, _ = tip_deflection(T_HOVER)

# First bending frequency (Rayleigh): tip mass + ESC + distributed arm mass.
tip_m = (80 + 22 + 8) / 1000                     # motor, prop, pad region (kg)
esc_m = 25 / 1000
arm_m = rep["parts"]["arm"]["est_mass_g"] / 1000
d1, x1, shape1 = tip_deflection(1.0)              # shape under 1 N at the tip (mm)
y_tip = d1
y_esc = np.interp(ESC_X, x1, shape1)
k_tip = 1.0 / (d1 / 1000)                         # N/m
# Simple equivalent: effective mass at the tip.
m_eff = tip_m + esc_m * (y_esc / y_tip) ** 2 + 0.24 * arm_m
f1 = math.sqrt(k_tip / m_eff) / (2 * math.pi)

rpm_max = KV * VOLTS * 0.85
rpm_hover = rpm_max * math.sqrt(T_HOVER / T_MAX)

# --- Motor torque reaction (arm torsion) ----------------------------------------
P_mech = POWER_MAX_W * 0.8
Q = P_mech / (rpm_max * 2 * math.pi / 60) * 1000          # N*mm
h_s = h_at(SUPPORT_X)
Am = (ARM_W - WALLS) * (h_s - WALLS)
tau_torsion = Q / (2 * Am * WALLS)

# --- Arm-to-body joint ----------------------------------------------------------
F_edge = T_MAX * ARM_LEN / SUPPORT_X                       # arm pushes up on the tunnel roof lip
F_root = F_edge - T_MAX                                    # root end pushes down on the floor
bearing = F_edge / (ARM_W * 3.0)                           # over a 3 mm contact strip
roof_span = ARM_W + 2 * FIT
roof_M = F_edge * roof_span / 8                            # fixed-fixed plate strip
roof_Z = 15 * ROOF**2 / 6                                  # ~15 mm effective strip
roof_sigma = roof_M / roof_Z
wall_area = 2 * ((BOSS_W - ARM_W - 2 * FIT) / 2) * 30      # side walls above the lip, across layers
wall_sigma_z = F_edge / wall_area
allow_z = PETG_UTS_Z / SAFETY_FACTOR

# --- Landing on the legs --------------------------------------------------------
LAND_G = 4.0                                               # hard landing, all weight on 2 legs
F_leg = W_N * LAND_G / 2
F_lat = 0.3 * F_leg                                        # sideways skid at touchdown (friction 0.3)
M_leg = F_lat * LEG_H                                      # straight strut: only the skid bends it
Z_leg = min(LEG_WIDTH * LEG_T**2, LEG_T * LEG_WIDTH**2) / 6   # weaker of the two directions
sigma_leg = M_leg / Z_leg + F_leg / (LEG_T * LEG_WIDTH)
# Skid along the arm: pad tips about its edge, far bolt takes it. Skid across the arm: pad tips
# about its 16 mm side edge, both bolts share it at 8 mm leverage.
bolt_T_along = M_leg * (LEG_PAD_L / 2 + LEG_BOLT_SPACING / 2) / ((LEG_PAD_L / 2 + LEG_BOLT_SPACING / 2) ** 2 + (LEG_PAD_L / 2 - LEG_BOLT_SPACING / 2) ** 2)
bolt_T_across = M_leg / (2 * LEG_WIDTH / 2)
bolt_T = max(bolt_T_along, bolt_T_across)
INSERT_PULLOUT = 500.0                                     # N, M3 insert in PETG (rough; varies with insert and print)

# --- Centre of gravity vs thrust line --------------------------------------------
cg_items = [  # (mass g, z mm)
    (frame_g, 18), (4 * 80, ARM_H_TIP + FLOOR + 15), (4 * 25, 30), (4 * 22, ARM_H_TIP + FLOOR + 45),
    (40, 25), (837, -26), (200, -60), (90, 15)]
cg_z = sum(m * z for m, z in cg_items) / sum(m for m, _ in cg_items)
prop_z = ARM_H_TIP + FLOOR + 45

f = lambda v, d=1: f"{v:,.{d}f}"
ok = lambda s, a: "OK" if s <= a else "TOO HIGH"
lines = f"""# Frame loads and stresses

Generated by `frame/analysis.py` from the CAD and your Excel motor data. Re-run after
changing `params.py`. Estimates, not a substitute for testing a printed arm.

## Inputs

| Item | Value |
|---|---|
| All-up weight (HOOVO pack + 200 g payload) | **{f(AUW_G, 0)} g** ({f(W_N)} N) |
| Printed frame (from CAD, {int(PRINT_FILL*100)}% fill) | {f(frame_g, 0)} g |
| Hover thrust per motor | {f(T_HOVER)} N ({f(T_HOVER/G*1000,0)} g) |
| Max thrust per motor (Motor sheet, 22.2 V, CF16x5.5) | {f(T_MAX)} N ({f(THRUST_MAX_G,0)} g) |
| Thrust-to-weight | {f(4*T_MAX/W_N, 2)} : 1 |
| Material | PETG, E = {PETG_E:.0f} MPa, strength {PETG_UTS_XY:.0f} MPa along lines / {PETG_UTS_Z:.0f} MPa across layers, safety factor {SAFETY_FACTOR:.0f} |

Mass breakdown:

| Part | g |
|---|---|
""" + "\n".join(f"| {k} | {f(v, 0)} |" for k, v in COMPONENTS.items()) + f"""

## Arms (cantilever from the body tunnel exit, r = {SOCKET_TIP_R:.0f} mm, to the motor, r = {MOTOR_R:.0f} mm)

| Check | Value | Allowed | Result |
|---|---|---|---|
| Bending moment at the tunnel exit, full thrust | {f(T_MAX * (ARM_LEN - SUPPORT_X) / 1000, 2)} N·m | | |
| Peak bending stress (at {f(crit[0] + ARM_R0, 0)} mm from centre) | {f(crit[3], 2)} MPa | {f(allow_xy, 1)} MPa | {ok(crit[3], allow_xy)} |
| Tip deflection at hover | {f(d_hover, 2)} mm | < 2 mm | {ok(d_hover, 2)} |
| Tip deflection at full thrust | {f(d_max, 2)} mm | < 4 mm | {ok(d_max, 4)} |
| Motor torque reaction | {f(Q / 1000, 2)} N·m | | |
| Torsion shear in the arm walls | {f(tau_torsion, 2)} MPa | {f(PETG_SHEAR / SAFETY_FACTOR, 1)} MPa | {ok(tau_torsion, PETG_SHEAR / SAFETY_FACTOR)} |
| First bending frequency of an arm | {f(f1, 0)} Hz | | |
| Motor speed at hover / full thrust (est.) | {f(rpm_hover / 60, 0)} / {f(rpm_max / 60, 0)} Hz | | |
| Blade-pass at hover (2 blades) | {f(2 * rpm_hover / 60, 0)} Hz | | |

The arm's first bending frequency (~{f(f1, 0)} Hz, a rough estimate) sits {f(100 * (1 - f1 / (rpm_hover / 60)), 0)}% below the hover rotor speed.
The rotors only pass through it briefly at low throttle (descents), which is normal for printed frames. Do not make the arms
moderately stiffer: that would move the frequency onto hover speed. Instead: balance the props, soft-mount the flight
controller on its grommets, and turn on ArduPilot's throttle-based harmonic notch (the ESCs have no RPM telemetry).
After the first hover, check the FFT in the flight log; if a peak shows up near hover speed, tell me and I will retune the arm.

## Arm-to-body joint (arm in the tunnel, held by 2 x M3)

Under thrust the arm presses **up** on the tunnel roof lip and **down** on the floor at its root,
so the bolts are not loaded in normal flight; they hold the arm in and take crash loads.

| Check | Value | Allowed | Result |
|---|---|---|---|
| Force on the roof lip | {f(F_edge)} N | | |
| Force on the floor at the root | {f(F_root)} N | | |
| Bearing stress on the lip (3 mm strip) | {f(bearing, 2)} MPa | {f(allow_xy, 1)} MPa | {ok(bearing, allow_xy)} |
| Roof bending (7 mm roof, {roof_span:.1f} mm span) | {f(roof_sigma, 2)} MPa | {f(allow_xy, 1)} MPa | {ok(roof_sigma, allow_xy)} |
| Side walls pulled across layers | {f(wall_sigma_z, 2)} MPa | {f(allow_z, 1)} MPa | {ok(wall_sigma_z, allow_z)} |

## Legs (hard landing: {LAND_G:.0f} g on two legs)

| Check | Value | Allowed | Result |
|---|---|---|---|
| Force per leg | {f(F_leg)} N | | |
| Moment at the top of the strut (skid at 0.3 x the landing force) | {f(M_leg / 1000, 2)} N·m | | |
| Strut bending stress (printed on its side) | {f(sigma_leg, 1)} MPa | {f(allow_xy, 1)} MPa | {ok(sigma_leg, allow_xy)} |
| Worst pull on a leg bolt / insert (sideways skid) | {f(bolt_T, 0)} N | ~{INSERT_PULLOUT/SAFETY_FACTOR:.0f} N (insert pull-out {INSERT_PULLOUT:.0f} N / {SAFETY_FACTOR:.0f}) | {ok(bolt_T, INSERT_PULLOUT/SAFETY_FACTOR)} |

## Balance

| Item | Value |
|---|---|
| Centre of gravity height (z = 0 is the body underside) | {f(cg_z)} mm |
| Prop plane height (est.) | {f(prop_z)} mm |
| CG below the props by | {f(prop_z - cg_z)} mm |

A CG below the prop plane (battery underneath) is stable and easy to tune. Keep the battery
centred front-to-back: a 10 mm shift moves the CG {f(837 * 10 / AUW_G, 1)} mm.

## Prop clearances

| Check | Value |
|---|---|
| Gap between neighbouring prop tips | {rep['prop_tip_gap_mm']} mm |
| Prop disc inner edge vs body tip (radius) | {rep['prop_inner_radius_mm']} mm vs {rep['body_tip_radius_mm']} mm |

## Assumptions to check

- PETG strengths are typical datasheet values; printed parts vary. Weigh and bend-test one arm.
- Insert pull-out (~{INSERT_PULLOUT:.0f} N for an M3 insert in PETG) is a rough figure; it depends on the insert and print settings.
- Motor speed is estimated from KV x volts x 0.85; your Motor sheet has no rpm at 22.2 V.
- ESC and prop weights are estimates (not on their listings).
"""
(HERE / "ANALYSIS.md").write_text(lines)
print(lines)
