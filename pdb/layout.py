"""Board outline and placement plan for the PDB.

Writes out/layout.svg (placement plan, top view) and out/outline.dxf (board edge + mounting holes, mm,
for KiCad: File > Import > Graphics, layer Edge.Cuts). Run:  python3 layout.py

Coordinates match the frame body: origin at the stack centre, +y toward the front, the battery lead slot at
y = -38 (rear). Arms are on the diagonals, so each ESC's pads sit on a chamfered corner facing its arm.
"""
import math, os
import params as P

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
H = P.BOARD / 2
C = P.CORNER_CHAMFER

# Board edge: square with 45-degree chamfered corners (counter-clockwise from the rear-right corner).
outline = [(H - C, -H), (H, -H + C), (H, H - C), (H - C, H), (-H + C, H), (-H, H - C), (-H, -H + C), (-H + C, -H)]
holes = [(sx * P.STACK / 2, sy * P.STACK / 2) for sx in (-1, 1) for sy in (-1, 1)]

# Placement plan: (label, centre x, centre y, w, h, rotation deg, kind)
blocks = []
# Battery pads on the rear edge, beside the lead slot. + on the left, - on the right (mark on silkscreen).
blocks += [("BAT+", -9, -H + 6, *P.BATT_PAD, 0, "pos"), ("BAT-", 9, -H + 6, *P.BATT_PAD, 0, "neg")]
# Shunt right inside the + pad, so all battery current passes it first; amplifier, 3.3 V LDO and TVS beside it.
# Everything stays out of the copper-free rings round the stack holes.
blocks += [("SHUNT", -4, -17, 10, 5, 0, "part"), ("CSA", 5, -11.5, 5, 4, 0, "part"),
           ("LDO", -7, -11.5, 4, 3, 0, "part"), ("PMON", -1.5, -11.5, 3, 3, 0, "part"),
           ("TVS", 7, -17, 5, 4, 0, "part"), ("LED", -16, -21, 2, 1.2, 0, "part")]
# Bulk capacitors: 4 x low-ESR 470 uF / 50 V, 10 x 10 mm SMD, on the side strips outside the Kakute footprint.
for sx in (-1, 1):
    for sy in (-1, 1):
        blocks.append((f"C{'12'[sx > 0]}{'ab'[sy > 0]}", sx * (H - 7), sy * 5.5, 10, 10, 0, "cap"))
# ESC pads: one + / - pair per corner, long side pointing out along the arm, side by side along the chamfer.
reach = H * math.sqrt(2) - C / math.sqrt(2)
for i, ang in enumerate(P.ARM_ANGLES):
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)          # outward along the arm
    tx, ty = -uy, ux                           # along the chamfer
    r_pad = reach - P.ESC_PAD[0] / 2 - 0.8
    off = P.ESC_PAD[1] / 2 + 0.7
    for s, lbl, kind in ((-1, "+", "pos"), (1, "-", "neg")):
        blocks.append((f"ESC{i+1}{lbl}", r_pad * ux + s * off * tx, r_pad * uy + s * off * ty, P.ESC_PAD[0], P.ESC_PAD[1], ang, kind))
    sx, sy = (1 if ux > 0 else -1), (1 if uy > 0 else -1)
    blocks.append((f"S{i+1}", sx * (H - 3.5), sy * 16.5, *P.SIG_PAD, 0, "sig"))
    blocks.append((f"G{i+1}", sx * (H - 3.5), sy * 13.0, *P.SIG_PAD, 0, "sig"))
# The two buck converters in the clear cross between the stack holes. They sit under the Kakute:
# the spacer between the boards must clear the tallest inductor.
blocks.append(("BEC1 5V FC", 0, 12, 22, 13, 0, "bec"))
blocks.append(("BEC2 12/5V AUX", 0, -2.5, 22, 11, 0, "bec"))
# Rail output pads and the power LED, between the converters and the front connectors.
blocks += [("5V", -11, 21.5, 3, 2, 0, "rail"), ("G", -7, 21.5, 3, 2, 0, "rail"), ("J3 GH-4 I2C", 0, 21.5, 7, 4.25, 0, "part"),
           ("AUX", 7, 21.5, 3, 2, 0, "rail"), ("G", 11, 21.5, 3, 2, 0, "rail")]
# Front edge: J1 to the Kakute (JST-SH 8), J2 Pixhawk-style power port (JST-GH 6).
blocks.append(("J1 SH-8 Kakute", -8, H - 5, 12, 4.5, 0, "part"))
blocks.append(("J2 GH-6 FC PWR", 8, H - 5, 10, 4.5, 0, "part"))


def rect_pts(cx, cy, w, h, rot):
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in ((-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2))]


# ---- SVG ----
S, M = 8.0, 14.0          # px per mm, margin (mm)
W = P.BAY_INNER + 2 * M
def tx_(x): return (x + W / 2) * S
def ty_(y): return (W / 2 - y) * S
colors = {"pos": "#d9534f", "neg": "#333", "sig": "#2a7ab0", "part": "#8a6d3b", "cap": "#5b8a3a", "dnp": "#999", "bec": "#7a4fb0", "rail": "#c07a00"}
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*S:.0f}" height="{W*S:.0f}" viewBox="0 0 {W*S:.0f} {W*S:.0f}" font-family="sans-serif">',
       f'<rect width="100%" height="100%" fill="#fff"/>']
b = P.BAY_INNER / 2
svg.append(f'<rect x="{tx_(-b)}" y="{ty_(b)}" width="{2*b*S}" height="{2*b*S}" fill="none" stroke="#bbb" stroke-dasharray="6 4"/>')
svg.append(f'<text x="{tx_(-b)+4}" y="{ty_(b)-6}" font-size="13" fill="#888">frame bay, {P.BAY_INNER:g} mm inside</text>')
for sx in (-1, 1):   # strap bands
    x0 = sx * P.STRAP_X - 11
    svg.append(f'<rect x="{tx_(x0)}" y="{ty_(b)}" width="{22*S}" height="{2*b*S}" fill="#f0e6ff" opacity="0.5"/>')
svg.append(f'<rect x="{tx_(-12)}" y="{ty_(P.LEAD_SLOT_Y+6)}" width="{24*S}" height="{12*S}" fill="#eee" stroke="#aaa"/>')
svg.append(f'<text x="{tx_(0)}" y="{ty_(P.LEAD_SLOT_Y)+5}" font-size="12" text-anchor="middle" fill="#666">battery lead slot</text>')
for ang in P.ARM_ANGLES:
    a = math.radians(ang)
    svg.append(f'<line x1="{tx_(H*1.25*math.cos(a))}" y1="{ty_(H*1.25*math.sin(a))}" x2="{tx_(b*1.35*math.cos(a))}" y2="{ty_(b*1.35*math.sin(a))}" stroke="#ccc" stroke-width="10" stroke-linecap="round"/>')
pts = " ".join(f"{tx_(x):.1f},{ty_(y):.1f}" for x, y in outline)
svg.append(f'<polygon points="{pts}" fill="#2e6b3a" fill-opacity="0.12" stroke="#2e6b3a" stroke-width="2"/>')
for x, y in holes:
    svg.append(f'<circle cx="{tx_(x)}" cy="{ty_(y)}" r="{P.STACK_KEEPOUT_D/2*S}" fill="#fff" stroke="#999" stroke-dasharray="3 2"/>')
    svg.append(f'<circle cx="{tx_(x)}" cy="{ty_(y)}" r="{P.STACK_HOLE_D/2*S}" fill="#fff" stroke="#000"/>')
for lbl, cx, cy, w, h, rot, kind in blocks:
    p = " ".join(f"{tx_(x):.1f},{ty_(y):.1f}" for x, y in rect_pts(cx, cy, w, h, rot))
    dash = ' stroke-dasharray="4 3"' if kind == "dnp" else ""
    fill = colors[kind] if kind in ("pos", "neg") else "none"
    svg.append(f'<polygon points="{p}" fill="{fill}" fill-opacity="0.85" stroke="{colors[kind]}" stroke-width="1.5"{dash}/>')
    fs = 9 if kind == "sig" else 11
    yoff = -(h / 2 + 1.2) * S if kind in ("part", "dnp", "cap", "rail") and h < 6 else 4
    fc = "#fff" if kind in ("pos", "neg") else colors[kind]
    svg.append(f'<text x="{tx_(cx)}" y="{ty_(cy)+ (yoff if yoff != 4 else 4)}" font-size="{fs}" text-anchor="middle" fill="{fc}">{lbl}</text>')
svg.append(f'<text x="{tx_(0)}" y="{ty_(-b)+32}" font-size="13" text-anchor="middle" fill="#333">PDB v0.2 placement plan, top view, {P.BOARD:g} x {P.BOARD:g} mm, 30.5 mm stack (rear at bottom)</text>')
svg.append('</svg>')
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "layout.svg"), "w") as f:
    f.write("\n".join(svg))

# ---- DXF (R12, mm): board edge + mounting holes only ----
dxf = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "9", "$INSUNITS", "70", "4", "0", "ENDSEC",
       "0", "SECTION", "2", "ENTITIES"]
for (x1, y1), (x2, y2) in zip(outline, outline[1:] + outline[:1]):
    dxf += ["0", "LINE", "8", "Edge.Cuts", "10", f"{x1:.4f}", "20", f"{y1:.4f}", "11", f"{x2:.4f}", "21", f"{y2:.4f}"]
for x, y in holes:
    dxf += ["0", "CIRCLE", "8", "Edge.Cuts", "10", f"{x:.4f}", "20", f"{y:.4f}", "40", f"{P.STACK_HOLE_D/2:.4f}"]
dxf += ["0", "ENDSEC", "0", "EOF"]
with open(os.path.join(OUT, "outline.dxf"), "w") as f:
    f.write("\n".join(dxf) + "\n")
print("wrote out/layout.svg and out/outline.dxf")
