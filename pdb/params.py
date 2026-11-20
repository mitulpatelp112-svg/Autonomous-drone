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
I_CONT = 100.0                   # [E] continuous design rating: 2x today's full throttle (~50 A), room for bigger motors
I_PEAK = 150.0                   # [E] 10 s peak - copper must survive it
I_PER_ESC = 30.0                 # [E] each ESC branch: 100 A / 4 = 25 A, rounded up to the 30 A ESC rating
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
BOARD = 66.0                     # [E] square board edge (66 mm makes room for two buck converters); bay is 90 mm inside [D]
CORNER_CHAMFER = 9.0             # [E] corners cut at 45 deg so the ESC pads face the arm wire passes
STACK = 30.5                     # [D] Kakute H7 v1.5 pattern; board sits on the bay's existing standoffs
STACK_HOLE_D = 3.4               # [S] M3 clearance
STACK_KEEPOUT_D = 7.0            # [E] copper-free ring round each stack hole (nylon spacer + washer)
# Each net has whole layers to itself, so the narrowest cross-section of its copper is the board width
# less the two stack-hole keep-outs on that line, less ~6 mm for pad islands of the other net.
BUS_WIDTH = BOARD - 2 * STACK_KEEPOUT_D - 6.0
BAY_INNER = 90.0                 # [D] CORE - 2 * WALL
STRAP_X = 33.0                   # [D] battery strap bands run under the board at x = +/-33 (22 mm wide)
LEAD_SLOT_Y = -38.0              # [D] battery lead comes up through the floor at y = -38
ARM_ANGLES = (45, 135, 225, 315) # [D] arms on the diagonals

# --- Pads and connectors ---------------------------------------------------------------
BATT_AWG = 8                     # [E] battery pigtail: 8 AWG silicone (10 AWG runs hot at 100 A continuous)
ESC_AWG = 14                     # [E] 25-30 A per branch. Frame groove (12 x 7 mm) was sized for 16 AWG; 2 x 14 AWG should fit (verify)
BATT_PAD = (14.0, 9.0)             # [E] battery +/- solder pads, sized for 8 AWG (~4.5-5 mm over the insulation, verify)
ESC_PAD = (9.0, 5.5)             # [E] per-ESC +/- solder pads (14 AWG)
SIG_PAD = (2.0, 3.0)             # [E] ESC signal + signal-ground pads per arm
# Battery connector candidates: (rated continuous A, burst A). All [V]: my recollection of Amass figures; hobby
# sellers often quote higher. Check the maker's datasheet for the exact part.
CONNECTORS = {"XT60": (30.0, 60.0), "XT90": (45.0, 90.0), "AS150": (150.0, 300.0)}
CONNECTOR = "XT90"               # [E] your choice. Fine for today's flying; check its datasheet rating against 100 A held

# --- Current sensing (shunt + current-sense amplifier -> Kakute CURR input) ----------
SHUNT_OHM = 0.00025              # [E] 0.25 mOhm, 4-terminal (Kelvin) shunt (0.5 mOhm would burn 5 W at 100 A)
SHUNT_W_RATING = 6.0             # [E] pick a part rated >= this; check its derating curve at T_AMBIENT
CSA_GAIN = 50.0                  # [E] e.g. TI INA240A2 (gain 50). INA240 family: -4..80 V common mode (verify on datasheet)
ADC_VREF = 3.3                   # [V] STM32H7 ADCs are 3.3 V; Holybro doesn't state the CUR pin's range. Running the amplifier from 3.3 V means it can't overdrive the pin either way
CSA_SWING_LOSS = 0.1             # [E] output can't reach the rail exactly

# --- Digital power monitor (for logging) -----------------------------------------------------
# A TI INA228 on the same Kelvin shunt: 20-bit, reads bus voltage, current, power, energy, charge and its own
# temperature over I2C (verify on the datasheet: I recall 0-85 V bus range and +/-163.84 mV / +/-40.96 mV shunt ranges).
# J3 (JST-GH 4-pin: 5V, SCL, SDA, GND) goes to the flight controller's I2C bus or a companion computer.
PMON_SHUNT_FS_MV = 163.84        # [V] widest shunt range (ADCRANGE = 0)
PMON_ADC_BITS = 20               # [V]
PMON_I2C_ADDR = 0x40             # [V] with A0 = A1 = GND; 16 addresses are selectable
I2C_PINS = ("5V", "SCL", "SDA", "GND")   # [V] common drone I2C/GPS-port order; check against your FC

# --- Battery voltage sense --------------------------------------------------------------
# The Kakute measures VBAT through its own input divider (it gets raw VBAT on J1).
# J2 (Pixhawk-style power port) gets a scaled voltage from this divider.
VDIV = (100e3, 10e3)             # [E] top, bottom: 11:1, so 25.2 V reads 2.29 V and full scale is ~36 V

# --- On-board supplies (BECs) ---------------------------------------------------------------
# Both are the same 60 V-input synchronous/asynchronous buck (e.g. a TI TPS54560-class part, 5 A switch: verify).
# BEC1 is fixed 5 V for a flight controller. BEC2 is set to 12 V or 5 V by a solder jumper on its feedback divider.
BEC_VIN_MAX = 60.0               # [V] converter input rating; must clear V_MAX plus spikes
BECS = {                         # name: (output volts, continuous amps, what it's for)
    "BEC1 FC": (5.0, 3.0, "flight controller: J2 Pixhawk-style power port, or the Kakute's peripherals"),
    "BEC2 AUX": (12.0, 3.0, "other equipment: VTX, cameras, LEDs (jumper to 5 V for USB-type loads)"),
}
BEC_EFF = 0.90                   # [E] typical for a buck at these voltages; check the chosen part's efficiency curve
BEC_SWITCH_A = 5.0               # [V] converter switch current rating

# --- Bulk capacitance and protection ----------------------------------------------------
CAP_BULK_UF = 470.0              # [E] per capacitor; 4 fitted at 100 A (the ESCs carry their own too)
CAP_V = 50.0                     # [E] 50 V parts on a 25.2 V bus
TVS_STANDOFF = 28.0              # [E] e.g. an SMDJ28A-class TVS: off below 28 V, clamps a spike near 45 V (verify part)

# --- Kakute link --------------------------------------------------------------------
# One JST-SH 8-pin cable to the Kakute's "ESC Port 1", like a 4-in-1 ESC would use.
# Pin order from Holybro's Kakute H7 pinout table (docs.holybro.com, kakute-h7-v1/pinout) and the labels on
# ArduPilot's Kakute H7 pinout image, where the B+ end of the connector is marked. Holybro's version chart lists
# no ESC-connector change from V1.2 to V1.5, but the drawings are of V1.2/V1.3: check pin 1 on your board.
#   B+  : battery voltage in (powers the Kakute; its own divider measures it on BATT_VOLT_PIN 10)
#   R7  : UART7 RX, ESC telemetry. The OPTO ESCs have none, so the PDB leaves it unconnected.
#   CUR : current-sense input (BATT_CURR_PIN 11). Voltage range not stated by Holybro or ArduPilot.
KAKUTE_ESC_PINS = ("B+", "R7", "GND", "CUR", "M1", "M2", "M3", "M4")   # [D] pin 1 = B+
KAKUTE_5V_MAX_A = 1.5            # [L] Holybro pinout: "5v output (1.5A max)" (the spec list says 5 V BEC 2 A)
KAKUTE_I2C = "SDA/SCL solder pads, no connector"   # [L] shared with the GPS compass
# J2: Pixhawk-style 6-pin power port (JST-GH). Pin order as I recall the Pixhawk standard; verify against your FC's docs.
PIXHAWK_POWER_PINS = ("5V", "5V", "CURR", "VOLT", "GND", "GND")   # [V]
SH_PIN_A = 1.0                   # [V] JST-SH contact rating as I recall it (about 1 A per pin)
