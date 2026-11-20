"""Size the PDB copper, shunt and connectors from params.py.

Writes out/calc.json and out/CALC.md. Run:  python3 calc.py
Trace sizing uses the IPC-2221 chart fit (I = k * dT^0.44 * A^0.725, A in mil^2). It is the old, conservative
method; IPC-2152 usually allows narrower copper. Treat the result as a floor for a first layout, then check
the real board's hot spots with a thermal camera or thermocouple at full throttle on the bench.
"""
import json, math, os
import params as P

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
MIL = 0.0254  # mm


def ipc2221_amps(width_mm, oz, dt, external):
    k = 0.048 if external else 0.024
    area_mil2 = (width_mm / MIL) * (oz * P.OZ_UM / 1000 / MIL)
    return k * dt ** 0.44 * area_mil2 ** 0.725


def width_for(amps, dt, n_ext, n_int):
    """Narrowest copper width that carries `amps` with the given number of outer and inner layers in parallel."""
    lo, hi = 0.01, 500.0
    for _ in range(80):
        w = (lo + hi) / 2
        cap = n_ext * ipc2221_amps(w, P.OZ_OUTER, dt, True) + n_int * ipc2221_amps(w, P.OZ_INNER, dt, False)
        lo, hi = (w, hi) if cap < amps else (lo, w)
    return hi


def copper_r(length_mm, width_mm, n_ext, n_int, temp_c):
    t = (n_ext * P.OZ_OUTER + n_int * P.OZ_INNER) * P.OZ_UM * 1e-6
    rho = P.RHO_CU * (1 + P.ALPHA_CU * (temp_c - 20))
    return rho * (length_mm / 1000) / ((width_mm / 1000) * t)


AWG_MOHM_PER_M = {10: 3.277, 12: 5.211, 14: 8.286, 16: 13.17, 18: 20.95}  # [S] solid-copper resistance at 20 C

r = {}
# Each net (battery + and GND) gets one outer and one inner layer on a 4-layer board.
n_ext, n_int = (1, 1) if P.LAYERS == 4 else (1, 0)

# 1. Current budget
r["current"] = {
    "hover_A": P.I_HOVER,
    "full_throttle_A": round(P.N_ESC * P.I_MOTOR_MAX + P.I_AVIONICS, 1),
    "design_continuous_A": P.I_CONT,
    "design_peak_10s_A": P.I_PEAK,
    "esc_listing_burst_all4_A": P.N_ESC * P.I_ESC_BURST,
}

# 2. Copper widths (main bus and per-ESC branch)
w_bus_cont = width_for(P.I_CONT, P.DT_CONT, n_ext, n_int)
w_bus_peak = width_for(P.I_PEAK, P.DT_PEAK, n_ext, n_int)
w_branch = width_for(P.I_PER_ESC, P.DT_CONT, n_ext, n_int)
w_bus = max(w_bus_cont, w_bus_peak)
r["copper"] = {
    "stackup": f"{P.LAYERS} layers, {P.OZ_OUTER:g} oz outer / {P.OZ_INNER:g} oz inner; each net on {n_ext} outer + {n_int} inner",
    "bus_min_width_mm_cont": round(w_bus_cont, 1),
    "bus_min_width_mm_peak": round(w_bus_peak, 1),
    "bus_min_width_mm": round(w_bus, 1),
    "branch_min_width_mm": round(w_branch, 1),
    "fits_on_board": w_bus <= P.BOARD - 2 * P.STACK_KEEPOUT_D,
}

# 3. Bus resistance and loss. Worst path: battery pads (one edge) to the far ESC pads (~ the board diagonal).
path_mm = P.BOARD * 0.9
w_used = min(P.BOARD / 2 - 4, 26.0)   # each net pours about half the board width after keep-outs
t_hot = P.T_AMBIENT + P.DT_CONT
r_one = copper_r(path_mm, w_used, n_ext, n_int, t_hot)
r_loop = 2 * r_one                      # + and GND
r["bus"] = {
    "path_mm": round(path_mm, 1), "pour_width_mm": w_used,
    "loop_mohm": round(r_loop * 1000, 3),
    "drop_mV_full_throttle": round(r_loop * r["current"]["full_throttle_A"] * 1000, 1),
    "loss_W_full_throttle": round(r_loop * r["current"]["full_throttle_A"] ** 2, 2),
    "loss_W_hover": round(r_loop * P.I_HOVER ** 2, 3),
}

# 4. Shunt and amplifier
i_fs = (P.ADC_VREF - P.CSA_SWING_LOSS) / (P.SHUNT_OHM * P.CSA_GAIN)
r["shunt"] = {
    "ohm": P.SHUNT_OHM, "gain": P.CSA_GAIN,
    "full_scale_A": round(i_fs, 1),
    "headroom_over_peak": round(i_fs / P.I_PEAK, 2),
    "mV_at_hover": round(P.SHUNT_OHM * P.I_HOVER * 1000, 2),
    "mV_at_full": round(P.SHUNT_OHM * r["current"]["full_throttle_A"] * 1000, 1),
    "W_hover": round(P.SHUNT_OHM * P.I_HOVER ** 2, 3),
    "W_full": round(P.SHUNT_OHM * r["current"]["full_throttle_A"] ** 2, 2),
    "W_peak": round(P.SHUNT_OHM * P.I_PEAK ** 2, 2),
    "W_rating_needed_ok": P.SHUNT_OHM * P.I_PEAK ** 2 <= P.SHUNT_W_RATING,
    "ardupilot_BATT_AMP_PERVLT": round(1 / (P.SHUNT_OHM * P.CSA_GAIN), 2),
    "ardupilot_BATT_AMP_OFFSET": 0.0,
    "A_per_ADC_step_12bit": round(P.ADC_VREF / 4096 / (P.SHUNT_OHM * P.CSA_GAIN), 3),
}

# 5. Wires (20 C, solid-copper table; stranded silicone wire is within a few percent)
def wire(awg, length_mm, amps):
    rr = 2 * AWG_MOHM_PER_M[awg] / 1000 * length_mm / 1000
    return {"awg": awg, "length_mm": length_mm, "amps": amps,
            "loop_mohm": round(rr * 1000, 2), "drop_mV": round(rr * amps * 1000, 1), "loss_W": round(rr * amps ** 2, 2)}

r["wires"] = {
    "battery_pigtail": wire(P.BATT_AWG, 120, r["current"]["full_throttle_A"]),
    "esc_lead_each": wire(P.ESC_AWG, 200, P.I_MOTOR_MAX),
}

# 6. Connectors
fta = r["current"]["full_throttle_A"]
r["connectors"] = {
    "xt60_rated_A": P.XT60_A[0], "xt60_burst_A": P.XT60_A[1],
    "xt60_ok_hover": P.I_HOVER <= P.XT60_A[0],
    "xt60_ok_full_throttle_burst": fta <= P.XT60_A[1],
    "xt60_ok_full_throttle_continuous": fta <= P.XT60_A[0],
    "kakute_vbat_pin_A": round(5.0 / P.V_NOM + 0.1, 2),   # ~5 W of avionics through the Kakute's own BECs
    "sh_pin_rating_A": P.SH_PIN_A,
}

# 7. Voltage ratings
r["voltage"] = {"bus_max_V": P.V_MAX, "min_part_rating_V": P.V_RATING_MIN,
                "cap_V": P.CAP_V, "cap_margin": round(P.CAP_V / P.V_MAX, 2), "tvs_standoff_V": P.TVS_STANDOFF,
                "tvs_off_at_full_pack": P.TVS_STANDOFF > P.V_MAX}

# 8. Fit in the frame bay
half_diag = P.BOARD / 2 * math.sqrt(2) - P.CORNER_CHAMFER / math.sqrt(2)
r["fit"] = {"board_mm": P.BOARD, "bay_inner_mm": P.BAY_INNER,
            "side_gap_mm": (P.BAY_INNER - P.BOARD) / 2,
            "corner_reach_mm": round(half_diag, 1),
            "overhangs_strap_band": P.BOARD / 2 > P.STRAP_X - 11,
            "lead_slot_clear": P.BOARD / 2 < abs(P.LEAD_SLOT_Y) - 6}

# 9. Totals
loss_full = r["bus"]["loss_W_full_throttle"] + r["shunt"]["W_full"]
r["total"] = {"board_loss_W_full_throttle": round(loss_full, 2),
              "board_loss_W_hover": round(r["bus"]["loss_W_hover"] + r["shunt"]["W_hover"], 3),
              "efficiency_full_throttle_pct": round(100 * (1 - loss_full / (P.V_NOM * fta)), 2)}

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "calc.json"), "w") as f:
    json.dump(r, f, indent=1)

c, b, s, w, k, v, fit, t = (r[x] for x in ("current", "copper", "bus", "wires", "connectors", "voltage", "fit", "total"))
s = r["shunt"]; bus = r["bus"]
md = f"""# PDB sizing results

Generated by `calc.py` from `params.py`. Do not edit by hand.

## Current budget
| Case | Current |
|---|---|
| Hover, 200 g payload | {c['hover_A']} A |
| Full throttle, all four motors | {c['full_throttle_A']} A |
| Design continuous | **{c['design_continuous_A']} A** |
| Design peak (10 s) | **{c['design_peak_10s_A']} A** |
| ESC listing burst x4 (not reachable with these motors) | {c['esc_listing_burst_all4_A']} A |

## Copper ({b['stackup']})
| Item | Minimum width (IPC-2221) |
|---|---|
| Main bus at {P.I_CONT:g} A, +{P.DT_CONT:g} C | {b['bus_min_width_mm_cont']} mm |
| Main bus at {P.I_PEAK:g} A, +{P.DT_PEAK:g} C | {b['bus_min_width_mm_peak']} mm |
| Each ESC branch at {P.I_PER_ESC:g} A | {b['branch_min_width_mm']} mm |

Fits on a {P.BOARD:g} mm board: **{'yes' if b['fits_on_board'] else 'NO'}**.

Bus loop (+ and GND), {bus['path_mm']} mm path, {bus['pour_width_mm']} mm pours at {P.T_AMBIENT + P.DT_CONT:g} C:
**{bus['loop_mohm']} mOhm**, {bus['drop_mV_full_throttle']} mV and {bus['loss_W_full_throttle']} W at full throttle,
{bus['loss_W_hover']} W at hover.

## Current sensing
| Item | Value |
|---|---|
| Shunt | {s['ohm']*1000:g} mOhm, amplifier gain {s['gain']:g} |
| Full scale at the Kakute ADC | **{s['full_scale_A']} A** ({s['headroom_over_peak']}x the design peak) |
| Shunt voltage, hover / full | {s['mV_at_hover']} mV / {s['mV_at_full']} mV |
| Shunt power, hover / full / peak | {s['W_hover']} W / {s['W_full']} W / {s['W_peak']} W (needs a >= {P.SHUNT_W_RATING:g} W part: {'ok' if s['W_rating_needed_ok'] else 'NOT OK'}) |
| Resolution (12-bit ADC) | {s['A_per_ADC_step_12bit']} A per step |
| ArduPilot | `BATT_MONITOR = 4`, `BATT_AMP_PERVLT = {s['ardupilot_BATT_AMP_PERVLT']}`, `BATT_AMP_OFFSET = 0` (calibrate against a clamp meter) |

## Wires (20 C)
| Wire | Loop resistance | Drop | Loss |
|---|---|---|---|
| Battery pigtail, {w['battery_pigtail']['awg']} AWG, {w['battery_pigtail']['length_mm']} mm, {w['battery_pigtail']['amps']} A | {w['battery_pigtail']['loop_mohm']} mOhm | {w['battery_pigtail']['drop_mV']} mV | {w['battery_pigtail']['loss_W']} W |
| Each ESC lead, {w['esc_lead_each']['awg']} AWG, {w['esc_lead_each']['length_mm']} mm, {w['esc_lead_each']['amps']} A | {w['esc_lead_each']['loop_mohm']} mOhm | {w['esc_lead_each']['drop_mV']} mV | {w['esc_lead_each']['loss_W']} W |

## Connectors and voltage
- XT60 (rated {k['xt60_rated_A']:g} A / burst {k['xt60_burst_A']:g} A, *verify*): hover {'ok' if k['xt60_ok_hover'] else 'NOT OK'};
  full throttle as a burst {'ok' if k['xt60_ok_full_throttle_burst'] else 'NOT OK'};
  full throttle held continuously {'ok' if k['xt60_ok_full_throttle_continuous'] else 'over the rated figure'}.
- Kakute VBAT on the 8-pin cable: about {k['kakute_vbat_pin_A']} A against ~{k['sh_pin_rating_A']:g} A per JST-SH pin (*verify*).
- Bus max {v['bus_max_V']:g} V. Capacitors {v['cap_V']:g} V ({v['cap_margin']}x). TVS stand-off {v['tvs_standoff_V']:g} V:
  {'stays off on a full pack' if v['tvs_off_at_full_pack'] else 'CONDUCTS ON A FULL PACK'}.

## Fit in the frame bay
- {fit['board_mm']:g} mm board in the {fit['bay_inner_mm']:g} mm bay: {fit['side_gap_mm']:g} mm each side for wires.
- Battery lead slot at y = {P.LEAD_SLOT_Y:g} mm is {'clear of' if fit['lead_slot_clear'] else 'UNDER'} the board.
- Board {'overhangs' if fit['overhangs_strap_band'] else 'clears'} the battery-strap bands (x = +/-{P.STRAP_X:g} mm); it sits 8 mm up on the standoffs.

## Totals
Board loss: **{t['board_loss_W_full_throttle']} W** at full throttle, {t['board_loss_W_hover']} W at hover
({t['efficiency_full_throttle_pct']} % efficient at full throttle).
"""
with open(os.path.join(OUT, "CALC.md"), "w") as f:
    f.write(md)
print(md)
