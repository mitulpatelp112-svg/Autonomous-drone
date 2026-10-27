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
PAD_T = 6.0                     # motor pad thickness (screws pass through this)
PAD_POCKET_D = 38.0             # pocket under the pad: a 5.5 mm screw head fits even at the outer end of a slot
MOTOR_SLOT_R = (7.5, 15.5)      # radial slots cover the 5010's 16 mm / 19 mm patterns (and 16x16 / 25 mm)
MOTOR_CENTER_HOLE_D = 12.0      # shaft / circlip clearance
SCREW_CLEAR_D = 3.4             # M3 clearance hole
INSERT_HOLE_D = 4.2             # hole for M3 heat-set insert (check your insert's datasheet; 4.0-4.3 typical)
INSERT_DEPTH = 6.0              # for M3 x 5.7 mm inserts
ESC_L, ESC_W, ESC_T = 52.0, 26.0, 12.0   # 30 A OPTO ESC body with clearance (from listing photos; verify)
ESC_R = 250.0                   # ESC centre radius (under the prop disc for cooling)
ESC_POCKET_DEPTH = 1.5
ZIP_SLOT = (4.0, 2.4)           # zip-tie slot through the arm (x, z)
WIRE_GROOVE = (12.0, 7.0)       # top wire channel (width, depth) from the ESC back to the root: 2 x 16 AWG + signal
JOINT_BOLTS = ((12.0, 9.5), (30.0, -9.5))  # arm-to-body bolts (x from the arm root, y): beside the wire channel, not through it
LIGHTEN_SPANS = ((48.0, 80.0), (110.0, 132.0), (186.0, 222.0))  # web slots between the body and the ESC, and ESC to motor (from the root)

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

# --- Legs (4x) -----------------------------------------------------------------
LEG_H = 110.0                   # chosen: 110 mm, clears a 52 mm battery
LEG_R = 185.0                   # leg mount radius (under each arm)
# The strut is vertical so a screwdriver reaches both leg bolts straight from below (a splayed strut covered the outer bolt).
LEG_T = 14.0                    # strut thickness in the side profile
LEG_WIDTH = 16.0                # extrusion width (print flat on this face)
LEG_BOLT_SPACING = 30.0         # bolts sit outside the strut (strut top +/-10 mm); inserts fall between the arm's lightening slots
LEG_PAD_L = 46.0                # mount pad length along the arm
LEG_FOOT = (20.0, 32.0)         # foot pad (along the arm, across the arm); narrow along the arm so it doesn't cover the bolts

# --- GPS mast (1 part) ---------------------------------------------------------
MAST_D = 12.0
MAST_L = 100.0                  # 20 mm sits in the socket
MAST_BORE_D = 8.0               # cable bore: a JST-SH 6-pin plug (~7 mm wide) fits through
GPS_PLATE = 30.0                # SEQURE M10-252Q is 25 x 25 mm, 182Q is 18 x 18 mm (SEQURE store)

# --- Tool access (for the clearance check) ---------------------------------------
HEAD_D = 5.5                    # M3 socket-cap head
TOOL_D = 7.0                    # space kept clear around a head for a hex key / screwdriver tip going in
BATTERY = (160.0, 52.0, 52.0)   # HOOVO 6S 6200 mAh, approximate (not on the listing): verify with calipers
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
KV = 360                        # motor listing
VOLTS = 22.2
