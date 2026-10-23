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
PAD_POCKET_D = 36.0             # pocket under the pad so motor screws can be reached
MOTOR_SLOT_R = (7.5, 15.5)      # radial slots cover the 5010's 16 mm / 19 mm patterns (and 16x16 / 25 mm)
MOTOR_CENTER_HOLE_D = 12.0      # shaft / circlip clearance
SCREW_CLEAR_D = 3.4             # M3 clearance hole
INSERT_HOLE_D = 4.2             # hole for M3 heat-set insert (check your insert's datasheet; 4.0-4.3 typical)
INSERT_DEPTH = 6.0              # for M3 x 5.7 mm inserts
ESC_L, ESC_W, ESC_T = 52.0, 26.0, 12.0   # 30 A OPTO ESC body with clearance (from listing photos; verify)
ESC_R = 250.0                   # ESC centre radius (under the prop disc for cooling)
ESC_POCKET_DEPTH = 1.5
ZIP_SLOT = (4.0, 2.4)           # zip-tie slot through the arm (x, z)
WIRE_GROOVE = (10.0, 6.0)       # top wire channel (width, depth) from ESC back to the root
JOINT_BOLT_X = (12.0, 30.0)     # arm-to-body bolt positions, measured from the arm root
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
STRAP_X = 36.0                  # straps at x = +/-36 mm
LEAD_SLOT = (16.0, 10.0)        # battery lead pass-through
MAST_SOCKET_D = 12.3            # GPS mast socket bore
MAST_BOSS_D = 20.0

# --- Legs (4x) -----------------------------------------------------------------
LEG_H = 110.0                   # chosen: 110 mm, clears a 52 mm battery
LEG_R = 185.0                   # leg mount radius (under each arm)
LEG_SPLAY_DEG = 12.0            # feet splay outward
LEG_T = 14.0                    # strut thickness in the side profile
LEG_WIDTH = 16.0                # extrusion width (print flat on this face)
LEG_BOLT_SPACING = 24.0

# --- GPS mast (1 part) ---------------------------------------------------------
MAST_D = 12.0
MAST_L = 100.0                  # 20 mm sits in the socket
GPS_PLATE = 30.0                # SEQURE M10-252Q is 25 x 25 mm, 182Q is 18 x 18 mm (SEQURE store)

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
