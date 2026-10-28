"""Shared dimensions for the 680 mm PETG quad frame (millimetres, grams, newtons).

Every number that came from a product page or your sheets says where it came from.
Change a value here and re-run build_frame.py and analysis.py.
"""

# --- Overall layout ------------------------------------------------------------
WHEELBASE = 680.0               # motor-to-motor diagonal (chosen: 680 mm for 16" props)
MOTOR_R = WHEELBASE / 2         # motor centre distance from frame centre
PROP_D = 16 * 25.4              # 16 x 5.5 props (Efficiency sheet "my choice")
BED = 220.0                     # every part must fit a 220 x 220 mm bed
BED_MARGIN = 5.0                # keep this far from the bed edges

# --- Arms (4x, identical) ------------------------------------------------------
ARM_R0 = 90.0                   # arm root (inner end) radius from frame centre
ARM_W = 28.0                    # arm width (fits the 25 mm wide ESC on top)
ARM_H_ROOT = 28.0               # arm height at the root
ARM_H_TIP = 20.0                # arm height under the motor
PAD_D = 46.0                    # motor pad diameter
PAD_T = 5.0                     # motor pad thickness: M3 x 8 screws then reach ~3 mm into the motor base
PAD_POCKET_D = 38.0             # pocket under the pad: a 5.5 mm screw head fits even at the outer end of a slot
MOTOR_SLOT_R = (6.0, 15.5)      # 4 radial slots (a cross) take any 4-hole pattern from 12 to 31 mm, incl. the listed 16 / 19 mm
MOTOR_SLOT_ANGLES = (0, 90, 180, 270)
MOTOR_VENTS = (15.0, 7.0)       # 4 cooling holes on the diagonals (radius, dia): air comes up through the pocket into the motor base
MOTOR_CENTER_HOLE_D = 9.0       # 4 mm shaft end + circlip poke out under the motor base
SCREW_CLEAR_D = 3.4             # M3 clearance hole
INSERT_HOLE_D = 4.2             # hole for M3 heat-set insert (check your insert's datasheet; 4.0-4.3 typical)
INSERT_DEPTH = 6.0              # for M3 x 5.7 mm inserts
ESC_SEAT = (71.0, 1.0)          # flat seat for the ESC across the full arm width (length, depth); zip ties locate it
ESC_R = 250.0                   # ESC centre radius (under the prop disc for cooling)
ZIP_SLOT = (4.0, 2.4)           # zip-tie slot through the arm (x, z)
WIRE_GROOVE = (12.0, 7.0)       # top wire channel (width, depth) from the ESC back to the root: 2 x 16 AWG + signal
JOINT_BOLTS = ((12.0, 9.5), (30.0, -9.5))  # arm-to-body bolts (x from the arm root, y): beside the wire channel, not through it
LIGHTEN_SPANS = ((48.0, 80.0), (110.0, 132.0), (192.0, 222.0))  # web slots between the body and the ESC, and ESC to motor (from the root)

# --- Central body (1 part) -----------------------------------------------------
FLOOR = 5.0                     # base thickness (also the tunnel floor)
ROOF = 7.0                      # tunnel roof thickness (holds the 5.7 mm joint inserts with 1 mm to spare)
FIT = 0.25                      # clearance per side between arm and tunnel
BODY_H = FLOOR + ARM_H_ROOT + 2 * FIT + ROOF
CORE = 96.0                     # electronics bay outer size (square)
WALL = 3.0                      # bay wall thickness
BOSS_W = 36.0                   # width of each arm socket boss
SOCKET_TIP_R = 133.0            # how far the socket bosses reach from centre
STACK = 30.5                    # Kakute H7 v1.5 / power board mounting pattern (both listings: 30.5 x 30.5 mm)
STANDOFF_H = 8.0                # printed standoffs under the power board
STRAP = (22.0, 3.5)             # battery strap slot (20 mm Velcro)
STRAP_X = 33.0                  # straps at x = +/-33 mm (slot stays 1 mm inside the bay wall)
LEAD_SLOT = (24.0, 12.0)        # battery lead pass-through (an XT60 is ~16 x 8 mm; room for the EC5 adapter too)
WIRE_PASS = (18.0, 25.0)        # opening from each arm's wire channel into the bay (width, bottom height above z = 0)
MAST_SOCKET_D = 12.3            # GPS mast socket bore
MAST_BOSS_D = 26.0              # boss on the OUTSIDE of the rear wall, so the battery strap crosses the bay freely
MAST_X = -(CORE / 2 + MAST_BOSS_D / 2 - 1)   # mast axis (behind the rear wall)
MAST_SOCKET_DEPTH = 28.0        # mast sits 20 mm deep; 8 mm below it for the cable to turn into the bay
MAST_LOCK_GAP = 7.5             # height of the cable passage from under the mast into the bay (9 mm wide)

# --- Legs (4x): curved PETG spring legs ------------------------------------------
# A C-shaped leaf hangs from a mount pad and bows outward. On touchdown the C closes up and
# stores the landing energy in bending, like a leaf spring. analysis.py sizes it.
LEG_H = 110.0                   # pad top to ground (unloaded); clears a 52 mm battery
LEG_R = 185.0                   # leg mount radius (under each arm)
LEG_WIDTH = 28.0                # leaf width = print height (printed on its side); matches the arm
LEAF_T = 4.8                    # leaf thickness (print solid: 100% infill or enough walls)
LEAF_X = 26.0                   # leaf hangs from here (leg frame, x outward along the arm): outboard of both bolts
LEAF_BULGE = 50.0               # how far the C bows outward at mid-height (50 = almost a semicircle)
LEG_BOLT_SPACING = 30.0         # both bolts sit inboard of the leaf, so a driver goes straight up to them
LEG_PAD = (-22.0, 32.0)         # mount pad extent along the arm (leg frame)
LEG_FOOT = (21.0, 45.0)         # foot pad extent along the arm; stays outboard of the bolts
# Landing cases for the spring sizing
LAND_V_NORMAL = 0.5             # m/s, ArduPilot's final landing speed (LAND_SPEED default 50 cm/s; verify in your params)
LAND_V_HARD = 1.2               # m/s, design hard landing on all 4 legs
SKID = 0.3                      # sideways friction at the foot, as a fraction of the vertical force
LEAF_STRESS_MAX = 30.0          # MPa at the hard landing (printed PETG yields ~40-45 MPa along the lines)
LEAF_STRESS_BREAK = 40.0        # MPa, where the leaf is expected to bend permanently or crack (estimate)

# --- GPS mast (1 part) ---------------------------------------------------------
MAST_D = 12.0
MAST_L = 100.0                  # 20 mm sits in the socket
MAST_BORE_D = 8.0               # cable bore: a JST-SH 6-pin plug (~7 mm wide) fits through
GPS_PLATE = 30.0                # SEQURE M10-252Q is 25 x 25 mm, 182Q is 18 x 18 mm (SEQURE store)

# --- Bought parts: real sizes ------------------------------------------------------
# Source tags: [L] product listing in your sheet (5010 motor + 30 A ESC set, AliExpress 3256808405937047)
#              [R] retailer listing for the same ESC model   [P] measured from the listing photos   [E] estimate
MOTOR_STATOR = (50.0, 10.0)     # [L] "Motor size: 50*10mm" (stator), "5010-14 360KV"
MOTOR_SHAFT_D = 4.0             # [L] "Shaft size: 4mm"
MOTOR_MOUNT = (16.0, 19.0)      # [L] "rear threaded mounting holes with both 16 mm and 19mm hole spacings" (a cross)
MOTOR_MASS = 80.0               # [L] "Weight: 80g"
MOTOR_BELL_D = 58.0             # [P] ~58 mm (photos scaled from the 4 mm shaft); a 50 mm stator needs ~57 mm or more
MOTOR_BODY_H = 18.0             # [P] can side ~13-15 mm in the photos plus the base plate; measure yours
ADAPTER_COLLAR = (20.0, 5.0)    # [P] bullet prop adapter: collar diameter x height
ADAPTER_BULLET = (16.0, 35.0)   # [P] bullet nut diameter x height above the collar (tip ~40 mm above the motor top)
PROP_HUB_T = 10.0               # [E] prop hub thickness; the prop sits on the collar
ESC_L, ESC_W, ESC_T = 68.0, 25.0, 8.7   # [R] ReadytoSky 30A 2-6S OPTO: "68x25x8.7mm (approx.)"; label in your listing photo: "Brushless 30A 2-6S LIPO OPTO"
ESC_MASS = 30.0                 # [R] 30 g
BULLET = (3.5, 15.0)            # [L] 3.5 mm bullet connectors (ESC end: female, ~15 mm long)
MOTOR_SCREW_L = 8.0             # M3 x 8: pad 5 mm + ~3 mm into the motor (thread size not on the listing: check it is M3)

# --- Tool access (for the clearance check) ---------------------------------------
HEAD_D = 5.5                    # M3 socket-cap head
TOOL_D = 7.0                    # space kept clear around a head for a hex key / screwdriver tip going in
BATTERY = (152.0, 48.5, 48.0)   # HOOVO 6S 6200 mAh: 152 x 48.5 x 48 mm (listing)
STACK_TOP = FLOOR + 8.0 + 22.0  # top of the power board + Kakute stack (estimate)

# --- Material: PETG (typical datasheet values; printed parts are weaker) --------
PETG_DENSITY = 1.27             # g/cm^3
PETG_E = 2000.0                 # MPa, Young's modulus (bulk ~2.0-2.1 GPa)
PETG_UTS_XY = 45.0              # MPa, along printed lines (bulk ~50)
PETG_UTS_Z = 25.0               # MPa, across layers (layer adhesion)
PETG_SHEAR = 20.0               # MPa, interlayer shear (estimate)
PRINT_FILL = 0.5                # mass fraction with 4 walls + 25-30% gyroid (estimate; weigh a printed arm)
SAFETY_FACTOR = 3.0             # for fatigue, vibration, heat and print variation

# --- Loads from your Excel "Motor" and "Efficiency" sheets ---------------------
THRUST_MAX_G = 1740.0           # 22.2 V, CF16x5.5, highest test point
CURRENT_MAX_A = 12.5
POWER_MAX_W = 277.5
# Thrust curve, CF16x5.5 at 22.2 V, from your Motor sheet: (grams of thrust, amps per motor). 0 g = no-load current.
MOTOR_CURVE = ((0.0, 0.4), (600.0, 2.3), (1200.0, 6.7), (1740.0, 12.5))
# Power and lift limits
PDB_AMPS = (25.0, 30.0)         # XT60 power board: continuous / burst, from its listing (all 4 ESCs are powered through it)
BATT_MAH = 6200.0               # HOOVO 6S
BATT_USABLE = 0.80              # land at ~20% left
AVIONICS_W = 5.0                # flight controller, receiver, GPS, buzzer (estimate)
MISSION_PAYLOAD = 200.0         # g, from your mission goal
TW_GOOD = 2.0                   # thrust-to-weight for normal, responsive flying (rule of thumb)
TW_MIN = 1.6                    # below about this, control in wind and climb-out get marginal (rule of thumb)
KV = 360                        # motor listing
VOLTS = 22.2
