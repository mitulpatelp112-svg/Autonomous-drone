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

# --- Landing on the curved spring legs ---------------------------------------------
# Curved-beam model of the leaf centreline (pad and foot rigid): bending energy U = sum M^2 ds / 2EI,
# with M from the foot force (vertical P plus a sideways skid of SKID x P either way).
from build_frame import leaf_arc
_cx, _zm, _r, _th = leaf_arc()
_t = np.linspace(_th, -_th, 600)
_lx, _lz = _cx + _r * np.cos(_t), _zm + _r * np.sin(_t)
_ds = _r * abs(_t[1] - _t[0])
_free = _lz < -6.0
_xb, _zb = _lx[-1], _lz[-1]
I_leaf = LEG_WIDTH * LEAF_T ** 3 / 12


def leaf_moments(Fx, Fz):
    return ((_xb - _lx) * Fz - (_zb - _lz) * Fx)[_free]


k_leg = 1 / (2 * (leaf_moments(0, 1.0) ** 2).sum() * _ds / (2 * PETG_E * I_leaf))     # N/mm
peak_M = lambda P: max(np.abs(leaf_moments(f * P, P)).max() for f in (-SKID, 0, SKID))
leaf_sigma = lambda P: peak_M(P) * (LEAF_T / 2) / I_leaf
P_unit_sigma = leaf_sigma(1.0)                                     # MPa per N (linear)
leaf_len = _free.sum() * _ds
ground0 = BATTERY[2] * 0 + (LEG_H - FLOOR - FIT) - BATTERY[2]     # battery-to-ground gap, unloaded
sag = (W_N / 4) / k_leg


def landing(v, legs):
    """Peak force per leg, travel, stress and g for a vertical touchdown at v (m/s) on `legs` legs."""
    U = 0.5 * (AUW_G / 1000) * v ** 2 / legs * 1000                # mJ = N*mm per leg
    P = math.sqrt(2 * U * k_leg)
    return {"v": v, "legs": legs, "U": U, "P": P, "d": P / k_leg, "sigma": leaf_sigma(P),
            "g": (legs * P) / W_N, "gap": ground0 - sag - P / k_leg}


cases = [landing(LAND_V_NORMAL, 4), landing(1.0, 4), landing(LAND_V_HARD, 4), landing(LAND_V_HARD, 2)]
P_break = LEAF_STRESS_BREAK / P_unit_sigma
U_break = P_break ** 2 / (2 * k_leg)
v_break4 = math.sqrt(2 * 4 * U_break / 1000 / (AUW_G / 1000))
v_break2 = math.sqrt(2 * 2 * U_break / 1000 / (AUW_G / 1000))
d_break = P_break / k_leg

# Leg pad bolts at the break load: only the skid can open the joint (the vertical push closes it).
_pivot = LEG_PAD[1]
_h = -_zb
_d = [_pivot - x for x in (-LEG_BOLT_SPACING / 2, LEG_BOLT_SPACING / 2)]
M_open_along = max(0.0, SKID * P_break * _h - P_break * abs(_xb - _pivot))
bolt_T_along = M_open_along * max(_d) / sum(x * x for x in _d)
M_open_across = max(0.0, SKID * P_break * _h - P_break * LEG_WIDTH / 2)
bolt_T_across = M_open_across / (2 * LEG_WIDTH / 2)
bolt_T = max(bolt_T_along, bolt_T_across)
INSERT_PULLOUT = 500.0                                     # N, M3 insert in PETG (rough; varies with insert and print)
# Arm bending from the leg push at the break load (arm cantilevered from the tunnel exit).
M_arm_leg = P_break * (LEG_R + _xb - SOCKET_TIP_R)
sigma_arm_leg = crit[3] * M_arm_leg / (T_MAX * (ARM_LEN - crit[0]))
# Sideways skid bends the 28 mm-wide leaf the stiff way.
sigma_leaf_side = SKID * P_break * _h / (LEAF_T * LEG_WIDTH ** 2 / 6)

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

## Curved spring legs

Each leg is a C-shaped PETG leaf ({LEG_WIDTH:.0f} mm wide, {LEAF_T} mm thick, {f(leaf_len, 0)} mm long, bowing {LEAF_BULGE:.0f} mm outward).
On touchdown the C closes up and stores the landing energy in bending. Modelled as a curved beam
(linear, small deflections) with a sideways skid of {SKID:.1f} x the vertical force either way.

| Property | Value |
|---|---|
| Spring rate per leg | {f(k_leg, 2)} N/mm |
| Sag when sitting on the ground | {f(sag)} mm |
| Battery-to-ground gap, unloaded / resting | {f(ground0)} / {f(ground0 - sag)} mm |

| Touchdown | Energy per leg | Peak force per leg | Leg compresses | Peak deceleration | Leaf stress (limit {LEAF_STRESS_MAX:.0f}) | Battery gap left |
|---|---|---|---|---|---|---|
""" + "\n".join(f"| {c['v']} m/s on {c['legs']} legs | {f(c['U'] / 1000, 2)} J | {f(c['P'])} N | {f(c['d'])} mm | {f(c['g'], 1)} g | {f(c['sigma'])} MPa {ok(c['sigma'], LEAF_STRESS_MAX) if c['legs'] == 4 else ''} | {f(c['gap'])} mm |" for c in cases) + f"""

The {LAND_V_NORMAL} m/s case is a normal ArduPilot landing: the leaf sees about {f(cases[0]['sigma'], 0)} MPa, low enough for
thousands of landings. The {LAND_V_HARD} m/s case is the design hard landing. Tipping onto two legs at {LAND_V_HARD} m/s
reaches {f(cases[3]['sigma'], 0)} MPa, {"past" if cases[3]['sigma'] > LEAF_STRESS_BREAK else "close to"} the ~{LEAF_STRESS_BREAK:.0f} MPa where the leaf is expected to bend for good:
those legs may need replacing after a hard tip-over (print a spare pair).

**Where it gives up.** The leaf is expected to bend permanently or crack at about {LEAF_STRESS_BREAK:.0f} MPa: {f(P_break)} N per leg,
after {f(d_break)} mm of travel. That is a {f(v_break4, 1)} m/s touchdown on 4 legs or {f(v_break2, 1)} m/s on 2. The legs are
the weak link on purpose: they are cheap bolt-on parts, and everything behind them stays well inside its limits at that load:

| At the leg's break load ({f(P_break)} N) | Value | Allowed | Result |
|---|---|---|---|
| Battery-to-ground gap left | {f(ground0 - sag - d_break)} mm | > 0 | {"OK" if ground0 - sag - d_break > 0 else "TOUCHES"} |
| Worst pull on a leg bolt / insert | {f(bolt_T, 0)} N | ~{INSERT_PULLOUT/SAFETY_FACTOR:.0f} N (insert pull-out {INSERT_PULLOUT:.0f} N / {SAFETY_FACTOR:.0f}) | {ok(bolt_T, INSERT_PULLOUT/SAFETY_FACTOR)} |
| Arm bending stress from the leg push | {f(sigma_arm_leg, 1)} MPa | {f(allow_xy, 1)} MPa | {ok(sigma_arm_leg, allow_xy)} |
| Leaf stress from a sideways skid (stiff direction) | {f(sigma_leaf_side, 1)} MPa | {f(allow_xy, 1)} MPa | {ok(sigma_leaf_side, allow_xy)} |

**Printing the legs:** on their side (the C lies flat on the bed), so the printed lines run along the curve and the leaf bends
along its lines, not across layers. Print them solid (100% infill or 6+ walls); a leaf with sparse infill is much
softer and weaker than this model. Each leg is about {f(rep['parts']['leg']['est_mass_g'], 0)} g printed solid.

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
