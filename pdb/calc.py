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


AWG_MOHM_PER_M = {8: 2.061, 10: 3.277, 12: 5.211, 14: 8.286, 16: 13.17, 18: 20.95}  # [S] solid-copper resistance at 20 C

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
    "available_width_mm": P.BUS_WIDTH,
    "fits_on_board": w_bus <= P.BUS_WIDTH,
    "margin_pct": round(100 * (P.BUS_WIDTH / w_bus - 1), 0),
}

# Stack-up options, for when the fab's choices are known: (outer oz, inner oz, outer layers per net, inner layers per net)
r["stackups"] = {}
for name, (oo, oi, ne, ni) in {"4 layers, 2 oz / 2 oz": (2, 2, 1, 1), "4 layers, 2 oz / 1 oz": (2, 1, 1, 1),
                               "4 layers, 3 oz / 2 oz": (3, 2, 1, 1), "6 layers, 2 oz / 2 oz": (2, 2, 1, 2)}.items():
    save = (P.OZ_OUTER, P.OZ_INNER); P.OZ_OUTER, P.OZ_INNER = oo, oi
    need = max(width_for(P.I_CONT, P.DT_CONT, ne, ni), width_for(P.I_PEAK, P.DT_PEAK, ne, ni))
    loss = 2 * copper_r(P.BOARD * 0.9, P.BUS_WIDTH, ne, ni, P.T_AMBIENT + P.DT_CONT) * P.I_CONT ** 2
    r["stackups"][name] = {"need_mm": round(need, 1), "fits": need <= P.BUS_WIDTH, "loss_W_design": round(loss, 2)}
    P.OZ_OUTER, P.OZ_INNER = save

# 3. Bus resistance and loss. Worst path: battery pads (one edge) to the far ESC pads (~ the board diagonal).
path_mm = P.BOARD * 0.9
w_used = P.BUS_WIDTH
t_hot = P.T_AMBIENT + P.DT_CONT
r_one = copper_r(path_mm, w_used, n_ext, n_int, t_hot)
r_loop = 2 * r_one                      # + and GND
r["bus"] = {
    "path_mm": round(path_mm, 1), "pour_width_mm": w_used,
    "loop_mohm": round(r_loop * 1000, 3),
    "drop_mV_full_throttle": round(r_loop * r["current"]["full_throttle_A"] * 1000, 1),
    "loss_W_full_throttle": round(r_loop * r["current"]["full_throttle_A"] ** 2, 2),
    "loss_W_hover": round(r_loop * P.I_HOVER ** 2, 3),
    "drop_mV_design": round(r_loop * P.I_CONT * 1000, 1),
    "loss_W_design": round(r_loop * P.I_CONT ** 2, 2),
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
    "W_design": round(P.SHUNT_OHM * P.I_CONT ** 2, 2),
    "W_peak": round(P.SHUNT_OHM * P.I_PEAK ** 2, 2),
    "W_rating_needed_ok": P.SHUNT_OHM * P.I_PEAK ** 2 <= P.SHUNT_W_RATING,
    "mV_at_design": round(P.SHUNT_OHM * P.I_CONT * 1000, 1),
    "ardupilot_BATT_AMP_PERVLT": round(1 / (P.SHUNT_OHM * P.CSA_GAIN), 2),
    "ardupilot_BATT_AMP_OFFSET": 0.0,
    "A_per_ADC_step_12bit": round(P.ADC_VREF / 4096 / (P.SHUNT_OHM * P.CSA_GAIN), 3),
}

# 4b. Digital power monitor
i_fs_pmon = P.PMON_SHUNT_FS_MV / 1000 / P.SHUNT_OHM
r["pmon"] = {"full_scale_A": round(i_fs_pmon, 1), "headroom_over_peak": round(i_fs_pmon / P.I_PEAK, 2),
             "current_lsb_mA": round(i_fs_pmon / 2 ** (P.PMON_ADC_BITS - 1) * 1000, 3),
             "i2c_addr": hex(P.PMON_I2C_ADDR)}

# 5. Wires (20 C, solid-copper table; stranded silicone wire is within a few percent)
def wire(awg, length_mm, amps):
    rr = 2 * AWG_MOHM_PER_M[awg] / 1000 * length_mm / 1000
    return {"awg": awg, "length_mm": length_mm, "amps": amps,
            "loop_mohm": round(rr * 1000, 2), "drop_mV": round(rr * amps * 1000, 1), "loss_W": round(rr * amps ** 2, 2)}

r["wires"] = {
    "battery_pigtail": wire(P.BATT_AWG, 120, P.I_CONT),
    "esc_lead_each": wire(P.ESC_AWG, 200, P.I_CONT / P.N_ESC),
}

# 6. Connectors
fta = r["current"]["full_throttle_A"]
r["connectors"] = {"choice": P.CONNECTOR, "table": {}}
for name, (cont, burst) in P.CONNECTORS.items():
    r["connectors"]["table"][name] = {"rated_A": cont, "burst_A": burst,
        "ok_full_throttle_today": fta <= cont, "ok_design_cont": P.I_CONT <= cont, "ok_design_peak": P.I_PEAK <= burst}
r["connectors"]["kakute_vbat_pin_A"] = round(5.0 / P.V_NOM + 0.1, 2)   # ~5 W of avionics through the Kakute's own BECs
r["connectors"]["sh_pin_rating_A"] = P.SH_PIN_A

# 6b. On-board supplies
r["becs"] = {}
for name, (vout, iout, use) in P.BECS.items():
    pout = vout * iout
    pin = pout / P.BEC_EFF
    r["becs"][name] = {"vout": vout, "iout": iout, "use": use, "pout_W": pout,
                       "heat_W": round(pin - pout, 2), "battery_A_at_min_V": round(pin / (P.CELLS * 3.3), 2),
                       "switch_margin": round(P.BEC_SWITCH_A / iout, 2)}
r["becs_ok_vin"] = P.BEC_VIN_MAX >= P.V_RATING_MIN
vtop, vbot = P.VDIV
r["volt_sense"] = {"ratio": round((vtop + vbot) / vbot, 2), "V_at_full_pack": round(P.V_MAX * vbot / (vtop + vbot), 2),
                   "full_scale_V": round(P.ADC_VREF * (vtop + vbot) / vbot, 1),
                   "ardupilot_BATT_VOLT_MULT": round((vtop + vbot) / vbot, 2)}

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
            "lead_slot_overlap_mm": max(0.0, P.BOARD / 2 - (abs(P.LEAD_SLOT_Y) - 6))}

# 9. Totals
bec_heat = sum(b["heat_W"] for b in r["becs"].values())
loss_full = r["bus"]["loss_W_full_throttle"] + r["shunt"]["W_full"]
loss_design = r["bus"]["loss_W_design"] + r["shunt"]["W_design"]
r["total"] = {"bec_heat_W_full_load": round(bec_heat, 2),
              "board_loss_W_full_throttle": round(loss_full, 2),
              "board_loss_W_design": round(loss_design, 2),
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

Each net has its own layers, so its narrowest cross-section is about {b['available_width_mm']:g} mm on a {P.BOARD:g} mm board.
Fits: **{'yes' if b['fits_on_board'] else 'NO'}** ({b['margin_pct']:+g} % margin).

| Stack-up option | Width needed | Fits in {P.BUS_WIDTH:g} mm | Copper loss at {P.I_CONT:g} A |
|---|---|---|---|
""" + "".join(f"| {n} | {d['need_mm']} mm | {'yes' if d['fits'] else 'no'} | {d['loss_W_design']} W |\n" for n, d in r['stackups'].items()) + f"""

Bus loop (+ and GND), {bus['path_mm']} mm path, {bus['pour_width_mm']:g} mm wide at {P.T_AMBIENT + P.DT_CONT:g} C:
**{bus['loop_mohm']} mOhm**, {bus['drop_mV_full_throttle']} mV and {bus['loss_W_full_throttle']} W at full throttle,
{bus['loss_W_hover']} W at hover; {bus['drop_mV_design']} mV and **{bus['loss_W_design']} W at {P.I_CONT:g} A**.

## Current sensing
| Item | Value |
|---|---|
| Shunt | {s['ohm']*1000:g} mOhm, amplifier gain {s['gain']:g} |
| Full scale at the Kakute ADC | **{s['full_scale_A']} A** ({s['headroom_over_peak']}x the design peak) |
| Shunt voltage, hover / full throttle / {P.I_CONT:g} A | {s['mV_at_hover']} mV / {s['mV_at_full']} mV / {s['mV_at_design']} mV |
| Shunt power, hover / full throttle / {P.I_CONT:g} A / {P.I_PEAK:g} A peak | {s['W_hover']} W / {s['W_full']} W / {s['W_design']} W / {s['W_peak']} W (a {P.SHUNT_W_RATING:g} W part covers the peak: {'ok' if s['W_rating_needed_ok'] else 'NOT OK'}) |
| Resolution (12-bit ADC) | {s['A_per_ADC_step_12bit']} A per step |
| ArduPilot | `BATT_MONITOR = 4`, `BATT_AMP_PERVLT = {s['ardupilot_BATT_AMP_PERVLT']}`, `BATT_AMP_OFFSET = 0` (calibrate against a clamp meter) |

## Data logging
| Source | What it reports | Where it goes |
|---|---|---|
| Analog: amplifier + divider on J1 / J2 | Current, voltage | Flight controller ADC; ArduPilot logs them (BAT messages) and sends them over telemetry |
| Digital: INA228 on J3 (I2C, address {r['pmon']['i2c_addr']}) | Voltage, current, power, energy, charge, temperature | Flight controller I2C (second battery monitor) or a companion computer |

INA228 on the {P.SHUNT_OHM*1000:g} mOhm shunt: full scale **{r['pmon']['full_scale_A']} A** ({r['pmon']['headroom_over_peak']}x the design peak),
{r['pmon']['current_lsb_mA']} mA per step.

## On-board supplies (both at full load, {P.BEC_EFF:.0%} efficiency assumed)
| Rail | Output | Use | Heat | Battery current (empty pack) | Switch margin |
|---|---|---|---|---|---|
""" + "".join(f"| {n} | {d['vout']:g} V / {d['iout']:g} A ({d['pout_W']:g} W) | {d['use']} | {d['heat_W']} W | {d['battery_A_at_min_V']} A | {d['switch_margin']}x |\n" for n, d in r['becs'].items()) + f"""
Converter input rating {P.BEC_VIN_MAX:g} V against a {P.V_MAX:g} V bus: {'ok' if r['becs_ok_vin'] else 'NOT OK'}.

Voltage sense on J2: divider {r['volt_sense']['ratio']}:1, full pack reads {r['volt_sense']['V_at_full_pack']} V,
full scale {r['volt_sense']['full_scale_V']} V. ArduPilot `BATT_VOLT_MULT = {r['volt_sense']['ardupilot_BATT_VOLT_MULT']}` (calibrate with a meter).

## Wires (20 C)
| Wire | Loop resistance | Drop | Loss |
|---|---|---|---|
| Battery pigtail, {w['battery_pigtail']['awg']} AWG, {w['battery_pigtail']['length_mm']} mm, {w['battery_pigtail']['amps']} A | {w['battery_pigtail']['loop_mohm']} mOhm | {w['battery_pigtail']['drop_mV']} mV | {w['battery_pigtail']['loss_W']} W |
| Each ESC lead, {w['esc_lead_each']['awg']} AWG, {w['esc_lead_each']['length_mm']} mm, {w['esc_lead_each']['amps']} A | {w['esc_lead_each']['loop_mohm']} mOhm | {w['esc_lead_each']['drop_mV']} mV | {w['esc_lead_each']['loss_W']} W |

## Connectors and voltage
Battery connector (ratings are my recollection, *verify*); chosen: **{k['choice']}**
| Connector | Rated / burst | Today's full throttle held ({fta} A) | {P.I_CONT:g} A continuous | {P.I_PEAK:g} A peak |
|---|---|---|---|---|
""" + "".join(f"| {n} | {d['rated_A']:g} / {d['burst_A']:g} A | {'ok' if d['ok_full_throttle_today'] else 'over'} | {'ok' if d['ok_design_cont'] else 'over'} | {'ok' if d['ok_design_peak'] else 'over'} |\n" for n, d in k['table'].items()) + f"""
- Kakute VBAT on the 8-pin cable: about {k['kakute_vbat_pin_A']} A against ~{k['sh_pin_rating_A']:g} A per JST-SH pin (*verify*).
- Bus max {v['bus_max_V']:g} V. Capacitors {v['cap_V']:g} V ({v['cap_margin']}x). TVS stand-off {v['tvs_standoff_V']:g} V:
  {'stays off on a full pack' if v['tvs_off_at_full_pack'] else 'CONDUCTS ON A FULL PACK'}.

## Fit in the frame bay
- {fit['board_mm']:g} mm board in the {fit['bay_inner_mm']:g} mm bay: {fit['side_gap_mm']:g} mm each side for wires.
- Battery lead slot (y = {P.LEAD_SLOT_Y:g} mm, 12 mm long): the board edge covers {fit['lead_slot_overlap_mm']:g} mm of it, 8 mm higher up; the lead still comes straight up beside the rear edge.
- Board {'overhangs' if fit['overhangs_strap_band'] else 'clears'} the battery-strap bands (x = +/-{P.STRAP_X:g} mm); it sits 8 mm up on the standoffs.

## Totals
Converter heat with both rails fully loaded: **{t['bec_heat_W_full_load']} W** (on top of the figures below).
Power-path loss: **{t['board_loss_W_design']} W at {P.I_CONT:g} A**, {t['board_loss_W_full_throttle']} W at today's full throttle, {t['board_loss_W_hover']} W at hover
({t['efficiency_full_throttle_pct']} % efficient at full throttle).
"""
with open(os.path.join(OUT, "CALC.md"), "w") as f:
    f.write(md)
print(md)
