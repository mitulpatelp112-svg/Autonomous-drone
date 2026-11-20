"""Design inputs for the custom power distribution board (PDB). Units: mm, A, V, ohm, degC.

Source tags:  [D] DRONE.md / frame/params.py (this repo)   [L] product listing   [S] standard / datasheet value
              [E] estimate or design choice   [V] not confirmed: check before ordering boards
Change a value here, then re-run calc.py and layout.py.
"""

# --- Electrical system -------------------------------------------------------------
CELLS = 6                        # [D] 6S LiPo (HOOVO 6200 mAh main, OVONIC 5000 mAh backup)
V_CELL_MAX = 4.20                # [S] LiPo full charge
V_CELL_NOM = 3.70
V_MAX = CELLS * V_CELL_MAX       # 25.2 V on a full pack
V_NOM = CELLS * V_CELL_NOM       # 22.2 V
V_RATING_MIN = 35.0              # [E] every part on the battery bus is rated at least this (ESC switching spikes)

N_ESC = 4
I_MOTOR_MAX = 12.5               # [D] Motor sheet: 1740 g at 12.5 A per motor, CF16x5.5, 22.2 V
I_ESC_BURST = 40.0               # [D] ESC listing: 40 A for 10 s (an ESC limit, not what these motors draw)
I_HOVER = 9.3                    # [D] battery current at hover with the 200 g payload
I_AVIONICS = 0.5                 # [E] Kakute + its BEC loads, taken off the battery bus

# Design targets for the board
I_CONT = 60.0                    # [E] continuous: full throttle on all four (~50 A) + 20 %
I_PEAK = 100.0                   # [E] 10 s peak (punch-outs, a stuck motor) - copper must survive it
I_PER_ESC = 20.0                 # [E] each ESC branch: 12.5 A max draw with margin
DT_CONT = 20.0                   # [E] allowed copper temperature rise at I_CONT
DT_PEAK = 45.0                   # [E] allowed temperature rise if I_PEAK were steady (conservative for 10 s)
T_AMBIENT = 40.0                 # [E] inside the bay on a warm day

# --- Board stack-up ----------------------------------------------------------------
LAYERS = 4                       # [E] 4 layers: battery + and GND each get an outer and an inner layer
OZ_OUTER = 2.0                   # [E] 2 oz outer copper (common, cheap at most fabs)
OZ_INNER = 2.0                   # [E] 2 oz inner copper (check your fab offers it on 4-layer; some only do 1 oz)
OZ_UM = 34.79                    # [S] 1 oz/ft^2 copper = 34.79 um thick (often rounded to 35)
BOARD_T = 1.6                    # [E] board thickness
RHO_CU = 1.72e-8                 # [S] ohm*m at 20 C
ALPHA_CU = 0.00393               # [S] per degC

# --- Board shape and fit in the frame bay --------------------------------------------
BOARD = 60.0                     # [E] square board edge; the bay is 90 mm inside [D: CORE 96 - 2 x WALL 3]
CORNER_CHAMFER = 9.0             # [E] corners cut at 45 deg so the ESC pads face the arm wire passes
STACK = 30.5                     # [D] Kakute H7 v1.5 pattern; board sits on the bay's existing standoffs
STACK_HOLE_D = 3.4               # [S] M3 clearance
STACK_KEEPOUT_D = 7.0            # [E] copper-free ring round each stack hole (nylon spacer + washer)
BAY_INNER = 90.0                 # [D] CORE - 2 * WALL
STRAP_X = 33.0                   # [D] battery strap bands run under the board at x = +/-33 (22 mm wide)
LEAD_SLOT_Y = -38.0              # [D] battery lead comes up through the floor at y = -38
ARM_ANGLES = (45, 135, 225, 315) # [D] arms on the diagonals

# --- Pads and connectors ---------------------------------------------------------------
BATT_AWG = 12                    # [E] battery pigtail: 12 AWG silicone to an XT60 (or XT90 if you go bigger)
ESC_AWG = 16                     # [D] frame wire groove is sized for 2 x 16 AWG per arm
BATT_PAD = (12.0, 7.0)             # [E] battery +/- solder pads (12 AWG fits with a fillet all round)
ESC_PAD = (8.0, 5.0)             # [E] per-ESC +/- solder pads (16 AWG)
SIG_PAD = (2.0, 3.0)             # [E] ESC signal + signal-ground pads per arm
XT60_A = (30.0, 60.0)            # [V] Amass XT60 rating as I recall it: 30 A rated, 60 A burst. Hobby use often quotes 60 A.
XT90_A = (45.0, 90.0)            # [V] Amass XT90, same caveat

# --- Current sensing (shunt + current-sense amplifier -> Kakute CURR input) ----------
SHUNT_OHM = 0.0005               # [E] 0.5 mOhm, 4-terminal (Kelvin) shunt
SHUNT_W_RATING = 5.0             # [E] pick a part rated >= this; check its derating curve at T_AMBIENT
CSA_GAIN = 50.0                  # [E] e.g. TI INA240A2 (gain 50). INA240 family: -4..80 V common mode (verify on datasheet)
ADC_VREF = 3.3                   # [V] Kakute H7 ADC full scale; run the amplifier from 3.3 V so it can't overdrive the pin
CSA_SWING_LOSS = 0.1             # [E] output can't reach the rail exactly

# --- Battery voltage sense --------------------------------------------------------------
# The Kakute measures VBAT through its own input divider, so the board just passes VBAT + GND to it.

# --- Bulk capacitance and protection ----------------------------------------------------
CAP_BULK_UF = 470.0              # [E] one low-ESR electrolytic per ESC branch (the ESCs carry their own too)
CAP_V = 50.0                     # [E] 50 V parts on a 25.2 V bus
TVS_STANDOFF = 28.0              # [E] e.g. an SMDJ28A-class TVS: off below 28 V, clamps a spike near 45 V (verify part)

# --- Kakute link --------------------------------------------------------------------
# One JST-SH 8-pin cable to the Kakute's ESC connector, like a 4-in-1 ESC would use.
# PIN ORDER IS NOT CONFIRMED. Copy it from Holybro's Kakute H7 v1.5 pinout before layout.
KAKUTE_ESC_PINS = ("VBAT", "GND", "CURR", "TLM", "M1", "M2", "M3", "M4")   # [V] placeholder order
SH_PIN_A = 1.0                   # [V] JST-SH contact rating as I recall it (about 1 A per pin)
