"""Example: "a mini ball launcher that plays fetch with my dog" - a chunky orange drum that fires a 40 mm ball out of its glowing mouth when the dog drops it in the hopper.

fork this file for a ball launcher (a fetch machine, a ball thrower, a pitching
machine - two flywheels under a hopper); change PARAMETERS and the outlines.
ARCHETYPE: ball launcher

How it is built (R1030):
  * STAGE A - hardware, shell, every working-face opening, fasteners:
    the board FLAT on standoffs in the base, shifted so the distance
    sensor SEATED on port 4 sits right under the throat: it looks straight
    up the ball path (an open window in the elbow, the throat, the hopper)
    and sees each ball drop; USB-C SEATED on 7, its mouth in a pocket with a
    liner in the back wall. The ball path is ONE part, the Chute: a 45 mm
    throat from the hopper's collar (a sleeve 0.2 mm round it), a round
    elbow, a launch tube falling 6 deg to a nozzle 18 mm out of the drum.
    Two dc_motor (N20) CABLED from 6 and 14 stand upright either side of
    the tube, shaft up, in rib frames under two closed guard cans; a
    flywheel with a stretched-on rubber tyre on each shaft bites 1.45 mm
    into the ball through a slot in the tube (only the tyre reaches the
    bore: no finger reaches a wheel from the hopper, 150 mm up the throat).
    Three legs pin the Chute into bosses on the floor. The start key's
    button (9) and the screen (1 + 2) are CABLED up behind the throat (the
    screen's pins down, both ribbons straight risers) - the key under the
    deck behind the hopper, the screen in the back wall facing the owner;
    the speaker (10 + 11) CABLED to the right wall, pins up, firing through
    a grille insert; two lights (5, 13) CABLED over the guard cans into a
    frosted ring round the mouth, carried by ribs and light pipes on the
    ring itself. The drum is ONE revolved outline (recessed plinth, 45 deg
    step, reveal groove, rolled deck) hollowed by the same outline WALL in,
    split low into the fixed Base and the Shell; five M2.5 screws from
    below into heat-set inserts in columns webbed to the wall. The Hopper
    is an oblique cone (a loft) from a 100 mm opening to the outlet on the
    axis, a drafted crown with a fat rolled rim over the deck, pinned
    through its flange.
  * STAGE B - details: rubber feet pinned into the floor, the charcoal
    bumper band, FETCH lettering, the paw on the start key, the ball.
RESTYLE (R425): HOPPER_H sets the deck height (the screen, the key and
their ribbons follow it), R_ROLL the deck's rolled edge, NOZZLE_L the
nozzle, WALL the drum, deck, band groove and hopper skin. The board, the
motors, the ball path and the ring are the hardware's own.
DETAILS (visible, 26): 1 revolved orange drum; 2 recessed graphite plinth
(the drum floats); 3 45 deg step over it; 4 reveal groove under the roll;
5 rolled deck edge; 6 charcoal rubber bumper band in a groove; 7 embossed
FETCH; 8 the charcoal hopper crown with its fat rolled rim; 9 the hopper's
flange on the deck; 10 the oblique funnel inside it; 11 the ball resting in
it; 12 the big white start key with 13 a paw print pressed in; 14 the cyan
frosted light ring round the mouth (116 mm); 15 the black rubber bezel,
proud of the drum; 16 the grey nozzle with 17 its lip; 18 the smoked screen
window in the back wall; 19 the speaker grille insert in the right side
(93 holes); 20 USB-C pocket with a liner at the back; 21 four rubber feet;
22 "ATECH FETCH-1" under the base; 23 five countersunk screws from below.
Inside: 24 two flywheels (six lightening holes, tyre flanges) in closed
guard cans; 25 motor rib frames and three pinned legs; 26 the ToF window
under the elbow; standoffs and fences; insert columns; the screen, key,
speaker and light holders; the sleeve round the hopper's collar.
Materials: orange shell, graphite base, charcoal hopper and band, satin
grey chute, graphite flywheels with rubber tyres, cyan frosted ring, black
rubber bezel and feet, smoked lens, white key, chrome screws, a yellow ball.
Safety (honest): a finger can still reach the tyres 30 mm inside the
mouth - the firmware spins the wheels only for the second after the ToF
sees a ball drop, and a real product would add a flap or interlock.
MEASURED (R1030, 2026-11-20): ./check CHECK PASS, run_seconds 15 s, wall 77 s; every RESTYLE end CHECK PASS.
"""
import math
import time
import Part
import atech_ports as ap
import atech_cad as cad
from FreeCAD import Vector, Placement, Rotation
V = Vector
T0 = time.time()

INTENT = {"board": "flat", "fitted_after": [
    "Shell", "Hopper", "Chute", "Flywheel_L", "Flywheel_R", "Tyre_L", "Tyre_R", "Light_Ring",
    "Bezel", "Grille", "Screen_Lens", "Start_Key", "Ball", "Band",
    "Foot_1", "Foot_2", "Foot_3", "Foot_4", "Screw_1", "Screw_2", "Screw_3", "Screw_4", "Screw_5"],
    # the big start key presses the button module under the deck
    "covers": {"Start_Key": "button_9"}}
# the tyres are stretched onto their hubs; the ball is a prop resting in the hopper
INTENDED_OVERLAPS = [("Flywheel_L", "Tyre_L"), ("Flywheel_R", "Tyre_R"), ("Hopper", "Ball")]
REVIEW_CLOSEUPS = ["Light_Ring", "Hopper", "Start_Key"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them; each knob at its min and its
# max gives CHECK PASS.
HOPPER_H = 75.0        # RESTYLE 63..87 height: the hopper, its outlet to the deck (sets the deck height)
R_ROLL = 12.0          # RESTYLE 10..14 radius: the deck's rolled edge
NOZZLE_L = 18.0        # RESTYLE 15..21 length: the nozzle out of the drum's front
WALL = 3.0             # RESTYLE 2.5..3.5 wall: drum, deck and hopper skin
# end RESTYLE
# Frame: the drum's axis on z (x = y = 0), the mouth at -Y, the floor at z = 0.
R_BODY = 102.0         # the drum's radius (204 across): the speaker's corners sit at r 97
PLINTH = 5.0           # the dark plinth's recess under the drum
FOOT = 4.0             # rubber feet under the base
FLOOR_T = 2.5
FL1 = FOOT + FLOOR_T   # floor top
SPLIT = 15.5           # base / shell seam, in the plinth wall, under every slide path (PCB top 17.5)
Z_STEP = 16.0          # the plinth's top; a 45 deg step out to the drum
L = 15.0               # board underside
BALL_D = 40.0          # a mini tennis ball
RB = BALL_D / 2 + 2.5  # the ball path's bore radius (45 mm)
TUBE_T = 2.5           # chute wall
RN = RB + TUBE_T
SLOPE = 6.0            # the launch tube falls this much toward the mouth (deg): the ball rolls in
MOTOR_LIFT = 18.5      # the motors' lowest point over the PCB top (their ribbons clear the floor)
WHEEL_R, WHEEL_H = 20.0, 14.0   # flywheel radius (rubber tyre included) and tread height
SQUEEZE = 1.45         # each flywheel bites this far into the ball
Y_W = -59.75           # the flywheels' shafts (y): 9 mm in front of the board
Z_OUT = 163.0          # the hopper's outlet (its collar hangs under it)
COLLAR_H = 10.0
R_FUN = 50.0           # the hopper's top opening radius (100 mm across)
FUN_BACK = 23.0        # the hopper's back edge (y): the deck behind it carries the screen and key
FLANGE_W, FLANGE_T = 5.0, 2.5   # the hopper's flange on the deck
CROWN = 14.0           # the hopper's collar over the deck
RING_IN, RING_OUT = 29.0, 56.5  # the frosted light ring round the mouth
LIGHT_OFF = (24.0, 36.0)        # each light from the mouth centre (x, up)
KEY_D = 30.0           # the big start key
SCREEN_X, SCREEN_DZ = -20.0, 44.0   # the screen in the back wall: its centre x, and its depth under the deck
KEY_XY = (0.0, 62.0)            # start key centre (port 9), on the deck behind the hopper
SPK_C = (85.0, 0.0, 62.0)       # the speaker, firing out of the right side
SCREW = "M2.5"
SCREW_R, SCREW_ANG = 89.0, (0, 100, 170, 235, 305)
COLOURS = {"Base": "graphite", "Shell": "orange", "Hopper": "#3b3f45", "Chute": "satin_grey",
           "Flywheel": "graphite", "Tyre": "rubber", "Light_Ring": "#7fdcff", "Band": "#3b3f45", "Bezel": "rubber",
           "Grille": "graphite", "Screen_Lens": "smoked", "Start_Key": "matte_white",
           "Ball": "#cfe23a", "Foot": "rubber", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
FLAT = Rotation(Vector(1, 0, 0), 90)
board = ap.board_object(doc)
board.Placement = Placement(Vector(), FLAT)
_b = ap.bbox(board)
# x -9.35..50.65, y -50..70: port 4 (the ToF) lands right under the throat
board.Placement = Placement(Vector(-9.35 - _b.XMin, 70.0 - _b.YMax, L - _b.ZMin), FLAT)
BB = ap.bbox(board)
PT = L + 2.5
H_TOP = Z_OUT + HOPPER_H               # deck top
DECK_U = H_TOP - WALL                  # deck underside
tof = ap.seat(doc, "distance_sensor", 4)   # looks straight up the throat
usb = ap.seat(doc, "usbc", 7)               # back centre, mouth +Y
# the flywheel motors: CABLED from 6 and 14, upright, shaft up, one each
# side of the launch tube (the shaft sits 0.57 / 0.25 off the box centre)
SHAFT_OFF = (0.57, 0.25)
SX = BALL_D / 2 - SQUEEZE + WHEEL_R    # shaft x: the tyre bites SQUEEZE into the ball
MZ = PT + MOTOR_LIFT + 24.15
mot_l, mot_l_rib = ap.cable(doc, "dc_motor", 6, ap.module_placement(
    "dc_motor", (-SX - SHAFT_OFF[0], Y_W - SHAFT_OFF[1], MZ), face="+X", cable="-Z"))
mot_r, mot_r_rib = ap.cable(doc, "dc_motor", 14, ap.module_placement(
    "dc_motor", (SX - SHAFT_OFF[0], Y_W - SHAFT_OFF[1], MZ), face="+X", cable="-Z"))
MB = ap.bbox(mot_r)
SHAFT_TIP = MB.ZMax
BODY_TOP = SHAFT_TIP - 8.8
W0 = BODY_TOP + 2.3                    # flywheel underside (6.5 mm of shaft in its hub)
W1 = W0 + WHEEL_H
Z_W = (W0 + W1) / 2                    # the ball's centre between the wheels
Z_E = Z_W + abs(Y_W) * math.tan(math.radians(SLOPE))   # ... and in the elbow under the throat
DIR = V(0, -math.cos(math.radians(SLOPE)), -math.sin(math.radians(SLOPE)))
E = V(0, 0, Z_E)
Z_M = Z_E - R_BODY * math.tan(math.radians(SLOPE))     # the mouth's centre at the drum's face
# the screen: CABLED from 1 + 2 into the back wall, facing out the back
# (the owner reads the throw count from behind), pins down: both ribbons
# rise straight up behind the board and the throat
SCR_Z = H_TOP - SCREEN_DZ
_sy = math.sqrt((R_BODY - WALL) ** 2 - (abs(SCREEN_X) + 19.75) ** 2) - 0.5 - 4.82
scr, scr_rib = ap.cable(doc, "screen", (1, 2), ap.module_placement(
    "screen", (SCREEN_X, _sy, SCR_Z), face="+Y", cable="-Z"),
    via={1: [(-22, 62, 40), (SCREEN_X - 10, _sy - 9, 95), (SCREEN_X - 10, _sy - 3.55, SCR_Z - 40)],
         2: [(-15, 42, 36), (SCREEN_X + 10, _sy - 9, 110), (SCREEN_X + 10, _sy - 3.55, SCR_Z - 40)]},
    smooth=True)
# the start key: CABLED from 9 up under the deck behind the hopper
KEY_FB = DECK_U - 0.1 - 0.8            # the key's flange underside (flange 0.8, 0.1 under the deck)
KEY_MT = KEY_FB - 1.2                  # the button module's top: 1 mm of travel
key, key_rib = ap.cable(doc, "button", 9, ap.module_placement(
    "button", (KEY_XY[0], KEY_XY[1], KEY_MT - 5.02), face="+Z", cable="+X"),
    via=[(58, 59, 40), (52, 60, 110), (KEY_XY[0] + 36, KEY_XY[1], H_TOP - 38)], smooth=True)
# the speaker: CABLED from 10 + 11, firing out of the right side, pins down
spk, spk_rib = ap.cable(doc, "speaker", (10, 11), ap.module_placement(
    "speaker", SPK_C, face="+X", cable="+Z"), via={10: [(60, 40, 40), (70, 12, SPK_C[2] + 38)],
                                                    11: [(60, 20, 40), (70, -8, SPK_C[2] + 38)]}, smooth=True)
# two lights behind the frosted ring over the mouth: CABLED from 5 and 13,
# each riser outside the launch tube, over the flywheel guards, down into the light
LZ = Z_M + LIGHT_OFF[1]
_xo = LIGHT_OFF[0] + 9.75
LY = -math.sqrt((R_BODY - WALL) ** 2 - _xo ** 2) + 0.5 + 4.77     # 0.5 mm behind the wall
LTOP = LZ + 9.75 + 14.5 + 22.0
light_l, light_l_rib = ap.cable(doc, "light", 5, ap.module_placement(
    "light", (-LIGHT_OFF[0], LY, LZ), face="-Y", cable="+Z"),
    via=[(-28, -20, 30), (-34, -21, 80), (-33, -24, LTOP - 18), (-27, -60, LTOP), (-LIGHT_OFF[0], LY + 5, LTOP)],
    smooth=True)
light_r, light_r_rib = ap.cable(doc, "light", 13, ap.module_placement(
    "light", (LIGHT_OFF[0], LY, LZ), face="-Y", cable="+Z"),
    via=[(58, -21, 40), (57, -22, 80), (50, -26, LTOP - 18), (30, -60, LTOP), (LIGHT_OFF[0], LY + 5, LTOP)],
    smooth=True)
tick("hardware")


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def annulus(r0, r1, z0, z1, c=(0, 0)):
    return cad.cut(cyl(r1, (c[0], c[1], z0), z1 - z0), cyl(r0, (c[0], c[1], z0 - 1), z1 - z0 + 2))


def along(r, s0, s1):
    """A cylinder of radius r on the launch axis, s0..s1 mm from the elbow."""
    return Part.makeCylinder(r, s1 - s0, E + DIR * s0, DIR)


def along_ring(r0, r1, s0, s1):
    return cad.cut(along(r1, s0, s1), along(r0, s0 - 1, s1 + 1))


def s_at(y):
    """The distance along the launch axis where it crosses y."""
    return -y / math.cos(math.radians(SLOPE))


def centre(m):
    b = ap.bbox(m)
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


def arc(c, r, a0, a1):
    am, a1 = math.radians((a0 + a1) / 2), math.radians(a1)
    return ("arc", (c[0] + r * math.cos(am), c[1] + r * math.sin(am)),
            (c[0] + r * math.cos(a1), c[1] + r * math.sin(a1)))


def rot(s, a):
    s = s.copy()
    s.rotate(V(0, 0, 0), V(0, 0, 1), a)
    return s


def hop_circle(z, grow):
    """The hopper's (centre y, radius) at height z, grown by `grow`: an
    oblique cone from the outlet (on the axis) to the top opening."""
    t = (z - Z_OUT) / (H_TOP - Z_OUT)
    return (FUN_BACK - R_FUN) * t, RB + (R_FUN - RB) * t + grow


def hop_cone(z0, z1, grow):
    ws = []
    for z in (z0, z1):
        yc, r = hop_circle(z, grow)
        ws.append(Part.Wire(Part.makeCircle(r, V(0, yc, z), V(0, 0, 1))))
    return Part.makeLoft(ws, True, True)


# ------------------------------------------------------------ the drum
# ONE revolved outline: a recessed plinth, a 45 deg step out to the drum,
# a reveal groove under the rolled edge, the roll onto the flat deck; the
# core is the same outline WALL in (concentric roll)
RP = R_BODY - PLINTH
ZR = H_TOP - R_ROLL
ZG = ZR - 6.0                          # the reveal groove under the roll
outer_pts = [(0, FOOT), (RP, FOOT), (RP, Z_STEP), (R_BODY, Z_STEP + PLINTH),
             (R_BODY, ZG - 1.0), (R_BODY - 0.8, ZG - 0.4), (R_BODY - 0.8, ZG + 0.4), (R_BODY, ZG + 1.0),
             (R_BODY, ZR), arc((R_BODY - R_ROLL, ZR), R_ROLL, 0, 90), (0, H_TOP)]
drum = cad.revolve_profile(outer_pts)
k = WALL * (math.sqrt(2) - 1)
core = cad.revolve_profile([(0, FL1), (RP - WALL, FL1), (RP - WALL, Z_STEP + k),
                            (R_BODY - WALL, Z_STEP + PLINTH + k), (R_BODY - WALL, ZR),
                            arc((R_BODY - R_ROLL, ZR), R_ROLL - WALL, 0, 90), (0, DECK_U)])
body = cad.cut(drum, core)
# the hopper's hole through the deck, 0.2 mm round its skin
GROW = WALL * 1.25                     # the cone's skin, measured across its slope ~ WALL
body = cad.cut(body, hop_cone(Z_OUT - 0.5, H_TOP + 2.0, GROW + 0.2))
tick("drum")
base, shell = cad.split(body, "Z", at=SPLIT, lip=1.2)
tick("split")

# the fixed base holds the board: standoffs 0.1 mm under it, fences 0.3 mm
# off its edges where no plug comes out
holders = [box(x - 3, x + 3, y - 3, y + 3, FL1 - 0.5, L - 0.1)
           for x in (BB.XMin + 12, BB.XMax - 12) for y in (BB.YMin + 12, BB.YMin + 60, BB.YMax - 12)]
holders += [box(BB.XMin - 1.8, BB.XMin - 0.3, BB.YMax - 56, BB.YMax - 44, FL1 - 0.5, PT - 1.5),
            box(BB.XMax + 0.3, BB.XMax + 1.8, BB.YMax - 76, BB.YMax - 64, FL1 - 0.5, PT - 1.5),
            box(BB.XMin + 18, BB.XMin + 26, BB.YMin - 1.8, BB.YMin - 0.3, FL1 - 0.5, PT - 1.5)]
base = cad.fuse_one(base, *holders)

# ------------------------------------------------------------ the hopper
# an oblique cone from a 100 mm opening down to the 45 mm outlet on the
# axis, a collar under it, a rolled flange resting on the deck, pinned
HC_Y = FUN_BACK - R_FUN
# the crown: the opening rises CROWN over the deck in a straight collar
# with a fat rolled rim (the dog's target, easy to see)
def crown(r0, r1, z0, z1):
    """The collar over the deck: a 3 deg draft, on the opening's centre."""
    return Part.makeLoft([Part.Wire(Part.makeCircle(r0, V(0, HC_Y, z0), V(0, 0, 1))),
                          Part.Wire(Part.makeCircle(r1, V(0, HC_Y, z1), V(0, 0, 1)))], True, True)


DRAFT = math.tan(math.radians(3.0))
hop_in = cad.fuse_one(hop_cone(Z_OUT - 0.01, H_TOP, 0.0),
                      crown(R_FUN, R_FUN + (CROWN + 5.0) * DRAFT, H_TOP, H_TOP + CROWN + 5.0),
                      cyl(RB, (0, 0, Z_OUT - COLLAR_H - 1), COLLAR_H + 1.5))
RIM_R = GROW / 2 + 1.0
hopper = cad.fuse_one(hop_cone(Z_OUT, H_TOP + 1.0, GROW),
                      crown(R_FUN + GROW, R_FUN + GROW + CROWN * DRAFT, H_TOP + 0.5, H_TOP + CROWN),
                      Part.makeTorus(R_FUN + GROW / 2 + CROWN * DRAFT, RIM_R, V(0, HC_Y, H_TOP + CROWN), V(0, 0, 1)),
                      cyl(RB + WALL, (0, 0, Z_OUT - COLLAR_H), COLLAR_H + 0.5),
                      cyl(R_FUN + GROW + FLANGE_W, (0, HC_Y, H_TOP), FLANGE_T))
hopper = cad.cut(hopper, hop_in)
hopper = cad.soften(hopper, 1.0, [e for e in hopper.Edges if abs(e.BoundBox.ZMin - (H_TOP + FLANGE_T)) < 0.01])
PIN_R = R_FUN + GROW + FLANGE_W / 2
pins, pin_bores = [], []
for a in (90.0, 210.0, 330.0):
    px, py = PIN_R * math.cos(math.radians(a)), HC_Y + PIN_R * math.sin(math.radians(a))
    pins.append(cyl(1.5, (px, py, H_TOP - WALL + 0.6), WALL - 0.6 + 0.5))
    pin_bores.append(cyl(1.65, (px, py, H_TOP - WALL + 0.4), WALL))
hopper = cad.fuse_one(hopper, *pins)
shell = cad.cut(shell, pin_bores)
tick("hopper")

# ------------------------------------------------------------ the chute
# the ball's path: the throat straight down from the hopper's collar, a
# round elbow, the launch tube falling SLOPE deg to the nozzle; a guard can
# round each flywheel (only its tyre reaches into the bore), a frame of
# ribs round each motor, three legs pinned into the floor
S_END = s_at(-(R_BODY + NOZZLE_L))
TOP_T = Z_OUT - COLLAR_H - 0.2         # the throat's top, 0.2 under the collar
SLV = RB + WALL + 0.2                  # the sleeve's bore round the collar
CAN_Z0, CAN_Z1 = BODY_TOP + 0.3, W1 + 0.3 + 2.0
RC = WHEEL_R + 1.5                     # the guard can's cavity
shafts = []
for m in (mot_l, mot_r):
    sp_ = [p for p in m.Mesh.Points if p.z > ap.bbox(m).ZMax - 6.0]
    shafts.append(((min(p.x for p in sp_) + max(p.x for p in sp_)) / 2, (min(p.y for p in sp_) + max(p.y for p in sp_)) / 2))
print("SHAFTS %s, tip z %.2f, wheels z %.2f..%.2f, elbow z %.2f, mouth z %.2f" % (shafts, SHAFT_TIP, W0, W1, Z_E, Z_M))
chute = cad.fuse_one(cyl(RN, (0, 0, Z_E), TOP_T - Z_E), Part.makeSphere(RN, E), along(RN, 0, S_END),
                     cyl(SLV + 2.0, (0, 0, TOP_T - 1.8), Z_OUT - 0.6 - TOP_T + 1.8),
                     along_ring(RN - 0.5, RN + 2.0, S_END - 4.0, S_END),          # the nozzle's lip
                     *[cyl(RC + 2.0, (x, y, CAN_Z0), CAN_Z1 - CAN_Z0) for x, y in shafts])
# the motors' frames: four ribs round each body, 0.3 mm off, up into the can floor
frames = []
for m in (mot_l, mot_r):
    b = ap.bbox(m)
    z0 = BODY_TOP - 30.0
    frames += [box(b.XMax + 0.3, b.XMax + 2.3, b.YMin - 2.3, b.YMax + 2.3, z0, CAN_Z0 + 0.5),
               box(b.XMin - 2.3, b.XMin - 0.3, b.YMin - 2.3, b.YMax + 2.3, z0, CAN_Z0 + 0.5),
               box(b.XMin - 2.3, b.XMax + 2.3, b.YMax + 0.3, b.YMax + 2.3, z0, CAN_Z0 + 0.5),
               box(b.XMin - 2.3, b.XMax + 2.3, b.YMin - 2.3, b.YMin - 0.3, z0, CAN_Z0 + 0.5)]
# three legs: one outboard of each can, one under the nozzle; each ends in
# a pin in a boss on the floor
BOSS_H = 4.0
LEGS = [(-(SX + RC + 4.5), Y_W), (SX + RC + 4.5, Y_W), (0.0, -(R_BODY - WALL - PLINTH - 6.0))]
legs, leg_pins, bosses, boss_bores = [], [], [], []
for i, (x, y) in enumerate(LEGS):
    top = CAN_Z0 + 8.0 if i < 2 else (Z_E - s_at(y) * math.sin(math.radians(SLOPE)) - RN + 1.5)
    legs.append(cyl(4.0, (x, y, FL1 + BOSS_H), top - FL1 - BOSS_H))
    leg_pins.append(cyl(2.0, (x, y, FL1 + BOSS_H - 3.3), 3.5))
    bosses.append(cyl(6.0, (x, y, FL1 - 0.5), BOSS_H + 0.5))
    boss_bores.append(cyl(2.1, (x, y, FL1 + BOSS_H - 3.5), 4.0))
chute = cad.fuse_one(chute, *frames, *legs, *leg_pins)
# the bore: throat, elbow, launch tube; the sleeve's bore round the collar;
# the cans' cavities (they open into the bore: the tyres bite the ball);
# soft-square shaft holes; the ToF's open window under the elbow
bore = [cyl(RB, (0, 0, Z_E), TOP_T - Z_E + 0.01), Part.makeSphere(RB, E), along(RB, 0, S_END + 1.0),
        cyl(SLV, (0, 0, TOP_T), Z_OUT), cyl(RB, (0, 0, TOP_T - 2.5), 3.0)]
bore += [cyl(RC, (x, y, CAN_Z0 + 1.7), CAN_Z1 - 2.0 - CAN_Z0 - 1.7) for x, y in shafts]
bore += [cad.rounded_box(5.4, 5.4, 3.0, 1.5, at=(x - 2.7, y - 2.7, CAN_Z0 - 0.5)) for x, y in shafts]
tc = centre(tof)
bore.append(cad.rounded_box(12.0, 9.0, 8.0, 2.0, at=(tc[0] - 6.0, tc[1] - 4.5, Z_E - RN - 2.0)))
chute = cad.cut(chute, bore)
base = cad.cut(cad.fuse_one(base, *bosses), boss_bores)
tick("chute")

# the flywheels: a hub on each shaft (bore 3.3 round the 3.0 shaft, blind),
# flanges either side of a stretched-on rubber tyre
TYRE_T = 3.0
wheels, tyres = [], []
for x, y in shafts:
    hub = cad.fuse_one(cyl(WHEEL_R - TYRE_T, (x, y, W0), WHEEL_H),
                       cyl(WHEEL_R - 1.4, (x, y, W0), 1.0), cyl(WHEEL_R - 1.4, (x, y, W1 - 1.0), 1.0))
    hub = cad.cut(hub, [cyl(1.65, (x, y, W0 - 1), SHAFT_TIP + 0.2 - W0 + 1)] +
                  [cyl(3.5, (x + 9.0 * math.cos(math.radians(a)), y + 9.0 * math.sin(math.radians(a)), W0 + 2.0), WHEEL_H - 4.0)
                   for a in range(0, 360, 60)])
    wheels.append(hub)
    tyres.append(annulus(WHEEL_R - TYRE_T - 0.2, WHEEL_R, W0 + 1.0, W1 - 1.0, (x, y)))
tick("flywheels")

# ------------------------------------------------------------ the front: mouth, bezel, light ring
# a hole round the nozzle, a rubber bezel in it (proud lip), the frosted
# ring round that, its light pipes and holder ribs reaching back to the lights
S_IN, S_OUT = s_at(-(R_BODY - 30.0)), s_at(-(R_BODY + 12.0))   # past the skin at the ring's foot too
shell = cad.cut(shell, along(RN + 0.3, S_IN, S_OUT))
bz = along_ring(RN + 0.3, RING_IN, S_IN, S_OUT)
bezel = shell.common(bz)
shell = cad.cut(shell, bz)
bezel = cad.fuse_one(bezel, cad.cut(along_ring(RN + 0.3, RING_IN + 1.0, s_at(-(R_BODY - 8.0)), s_at(-(R_BODY + 15.0))), drum)
                     .common(box(-R_BODY, R_BODY, -(R_BODY + 2.5), 0, 0, H_TOP)))   # a flat face, square to y
rg = along_ring(RING_IN, RING_OUT, S_IN, S_OUT)
ring = shell.common(rg)
shell = cad.cut(shell, rg)
inside = cyl(R_BODY - 0.4 * WALL, (0, 0, 0), H_TOP)     # ribs and pipes stay inside the drum's skin
lpieces = []
for m in (light_l, light_r):
    b = ap.bbox(m)
    pipe_ = box(b.XMin, b.XMax, b.YMin - 0.4, -R_BODY, b.ZMin, b.ZMax)
    ribs = [box(b.XMin - 2.3, b.XMin - 0.3, -R_BODY, b.YMax + 2.3, b.ZMin + 2.0, b.ZMax - 2.0),
            box(b.XMax + 0.3, b.XMax + 2.3, -R_BODY, b.YMax + 2.3, b.ZMin + 2.0, b.ZMax - 2.0),
            box(b.XMin - 2.3, b.XMax + 2.3, b.YMax + 0.3, b.YMax + 2.3, (b.ZMin + b.ZMax) / 2 - 3, (b.ZMin + b.ZMax) / 2 + 3)]
    for p in [pipe_] + ribs:
        lpieces.append(p.common(inside).common(along_ring(RING_IN + 0.3, RING_OUT - 0.3, s_at(-60.0), S_OUT)))
ring = cad.fuse_one(ring, *lpieces)
tick("front")

# ------------------------------------------------------------ the deck: screen window, start key
sx, sy, sz = centre(scr)
win = cad.rounded_box(28.0, R_BODY, 16.0, 2.0, at=(sx - 14.0, sy, sz - 8.0), edges="y")
lens = shell.common(win)
shell = cad.cut(shell, win)
sb = ap.bbox(scr)
kx, ky, kz = centre(key)
kb = ap.bbox(key)
cap = cad.button_cap(KEY_D, H_TOP + 4.0 - KEY_FB, dome=1.6, flange=1.5, at=(kx, ky, KEY_FB), axis="+Z")
shell = cad.opening_for(shell, cap, clearance=0.3, chamfer=0.5, axis="+Z")
cap = cad.fuse_one(cap, cyl(3.0, (kx, ky, kb.ZMax + 0.16), KEY_FB + 0.5 - kb.ZMax - 0.16))
# holders hung from the deck: the screen in a cradle (side ribs and a shelf
# under it); the key module the same, its ribs stopping under the cap's
# flange and hung from posts outside it
KR = KEY_D / 2 + 1.5 + 1.0
dh = [box(x0, x1, sb.YMin - 2.3, R_BODY, sb.ZMin + 8.0, sb.ZMax + 2.3).common(inside)
      for x0, x1 in ((sb.XMin - 2.3, sb.XMin - 0.3), (sb.XMax + 0.3, sb.XMax + 2.3))]
dh += [box(sb.XMin - 2.3, sb.XMax + 2.3, sb.YMin - 2.3, R_BODY, sb.ZMax + 0.3, sb.ZMax + 2.3).common(inside),
       box(sb.XMin - 2.3, sb.XMax + 2.3, sb.YMin - 2.3, sb.YMin - 0.3, sb.ZMax - 5.0, sb.ZMax + 2.3)]
for s in (-1, 1):
    y_in = ky + s * (9.75 + 0.3)
    y_rib = ky + s * (9.75 + 2.3)
    y_post = ky + s * (KR + 2.0)
    dh += [box(kb.XMin, kb.XMax - 5.0, y_in, y_rib, kb.ZMin - 2.3, kb.ZMax - 0.3),
           box(kb.XMin, kb.XMax - 5.0, y_in, y_post, kb.ZMin - 2.3, kb.ZMin + 1.0),
           box(kb.XMin, kb.XMax - 5.0, ky + s * KR, y_post, kb.ZMin - 2.3, DECK_U + 0.5)]
dh.append(box(kb.XMin, kb.XMax - 5.0, kb.YMin - 2.3, kb.YMax + 2.3, kb.ZMin - 2.3, kb.ZMin - 0.3))
shell = cad.fuse_one(shell, *dh)
tick("deck")

# ------------------------------------------------------------ the right side: speaker grille, USB-C
# the grille is its own insert in the wall (holes in a small part are fast
# to check, R15); the speaker sits between two ribs from the wall and a stop
gc = (R_BODY, SPK_C[1], SPK_C[2])
gcut = Part.makeCylinder(19.0, 2 * WALL + 4, V(R_BODY - 2 * WALL - 2, gc[1], gc[2]), V(1, 0, 0))
grille = shell.common(gcut)
shell = cad.cut(shell, gcut)
# one cut of 1.6 mm holes on rings 2.6 mm apart (speaker_grille measured every
# hole on the curved piece: 17 s)
gh = [Part.makeCylinder(0.8, 3 * WALL + 6, V(R_BODY - 2 * WALL - 3, gc[1], gc[2]), V(1, 0, 0))]
for i in range(1, 6):
    rr = 2.6 * i
    n = int(2 * math.pi * rr / 2.6)
    for j in range(n):
        a = 2 * math.pi * (j + 0.5 * (i % 2)) / n
        gh.append(Part.makeCylinder(0.8, 3 * WALL + 6, V(R_BODY - 2 * WALL - 3, gc[1] + rr * math.cos(a),
                                                            gc[2] + rr * math.sin(a)), V(1, 0, 0)))
grille = cad.cut(grille, gh)
pb = ap.bbox(spk)
shell = cad.fuse_one(shell, *[box(pb.XMin - 2.3, R_BODY - 0.5 * WALL, y0, y1, pb.ZMin + 4.0, pb.ZMax - 2.0)
                              .common(inside) for y0, y1 in ((pb.YMin - 2.3, pb.YMin - 0.3), (pb.YMax + 0.3, pb.YMax + 2.3))],
                     box(pb.XMin - 2.3, pb.XMin - 0.3, pb.YMin - 2.3, pb.YMax + 2.3, pb.ZMax - 12.0, pb.ZMax - 2.0))
# USB-C at the back: a pocket brings the wall to 0.25 mm off the mouth
ub = ap.bbox(usb)
ux, uz = (ub.XMin + ub.XMax) / 2, PT + 5.9
pocket = cad.rounded_box(18, R_BODY, 10, 3, at=(ux - 9, ub.YMax + 1.3, uz - 5), edges="y")
liner = cad.cut(cad.rounded_box(22, R_BODY, 14, 4, at=(ux - 11, ub.YMax + 0.25, max(uz - 7, SPLIT + 1.6)), edges="y")
                .common(cyl(R_BODY - WALL + 1.0, (0, 0, 0), H_TOP)), pocket)
shell = cad.fuse_one(cad.cut(shell, pocket), liner)
shell = cad.socket_opening(shell, usb, margin=1.5)
tick("side + usb")

# ------------------------------------------------------------ fasteners: base to shell
# five M2.5 up through the base into heat-set inserts in columns webbed
# to the drum wall (all in ONE fuse and ONE cut)
INSERT_D = {"M2": 3.2, "M2.5": 3.6, "M3": 4.3}[SCREW]
PILOT_D = {"M2": 1.7, "M2.5": 2.1, "M3": 2.5}[SCREW]
CLEAR_D = {"M2": 2.4, "M2.5": 2.9, "M3": 3.4}[SCREW]
screws, cols, bores, bbosses, bholes = [], [], [], [], []
for a in SCREW_ANG:
    x, y = SCREW_R * math.cos(math.radians(a)), SCREW_R * math.sin(math.radians(a))
    cols.append(cyl(INSERT_D / 2 + 1.2, (x, y, SPLIT + 0.1), 12.0))
    cols.append(rot(box(SCREW_R, R_BODY - WALL + 0.6, -1.0, 1.0, SPLIT + 3.0, SPLIT + 12.0), a))
    bores.append(cyl(INSERT_D / 2, (x, y, SPLIT), 6.5))
    bores.append(cyl(PILOT_D / 2, (x, y, SPLIT + 6.0), 5.5))
    bbosses.append(cyl(3.5, (x, y, FL1 - 0.5), SPLIT - 0.1 - FL1 + 0.5))
    bholes.append(cyl(CLEAR_D / 2, (x, y, FOOT - 1), SPLIT + 1))
    bholes.append(Part.makeCone(4.7 / 2 + 0.3, CLEAR_D / 2, (4.7 + 0.6 - CLEAR_D) / 2, V(x, y, FOOT - 0.01), V(0, 0, 1)))
    screws.append(cad.screw("csk_phillips", SCREW, 16, at=(x, y, FOOT), axis="+Z"))
shell = cad.cut(cad.fuse_one(shell, *cols), bores)
base = cad.cut(cad.fuse_one(base, *bbosses), bholes)
tick("stage A")


# === STAGE B: details ===
# (a fork may stop after STAGE A, run ./check, then add these one by one)
# rubber feet: a pad with a stem pinned into the floor
feet = []
foot_bores = []
for a in (45, 135, 225, 315):
    x, y = 74.0 * math.cos(math.radians(a)), 74.0 * math.sin(math.radians(a))
    f = cad.fuse_one(cad.soften(cyl(10.0, (x, y, 0), FOOT), 1.2, None), cyl(3.0, (x, y, FOOT - 0.5), 1.9))
    feet.append(f)
    foot_bores.append(cyl(3.1, (x, y, FOOT - 0.5), 2.0))
base = cad.cut(base, foot_bores)
# lettering: FETCH across the front above the ring, ATECH under the base
# a paw print pressed into the start key
paw = [(0.0, -3.0, 3.2)] + [(dx, dy, 1.4) for dx, dy in ((-6.0, 3.2), (-2.0, 4.6), (2.0, 4.6), (6.0, 3.2))]   # >= 1.2 mm between pockets
DOME_H = 1.6


def dome_z(rr):
    """The key's dome surface height at rr from its axis (a 1.6 mm dome)."""
    return H_TOP + 4.0 - DOME_H * min(1.0, (rr / (KEY_D / 2)) ** 2)


# each pocket 0.6 mm under the dome at its outer edge (no feather edge)
cap = cad.cut(cap, [cyl(r_, (kx + dx, ky - dy, dome_z(math.hypot(dx, dy) + r_) - 0.6), 3.0)
                    for dx, dy, r_ in paw], optional=True)
# a charcoal rubber bumper band stretched into a groove round the drum
# over the ring (it keeps the dog's teeth off the paint)
BAND_Z0 = Z_M + RING_OUT + 6.0
BAND_Z1 = BAND_Z0 + 12.0
GD = WALL - 1.6                                   # the groove leaves 1.6 mm of wall
shell = cad.cut(shell, annulus(R_BODY - GD, R_BODY + 2.0, BAND_Z0, BAND_Z1))
band = annulus(R_BODY - GD, R_BODY + 1.5, BAND_Z0, BAND_Z1)
band = cad.soften(band, 0.6, [e for e in band.Edges if e.BoundBox.XMax > R_BODY + 1.0])
shell = cad.text(shell, "FETCH", (0, -R_BODY, (BAND_Z1 + ZG) / 2), (0, -1, 0), 22,
                 depth=1.0, mode="emboss")
base = cad.text(base, "ATECH FETCH-1", (0, 30, FOOT), (0, 0, -1), 6, depth=0.4, mode="deboss", up=(0, -1, 0))
# the ball: a prop resting on the hopper's front slope (sunk 0.3 mm)
t = 0.8
zb = Z_OUT + t * HOPPER_H
yc, r = hop_circle(zb, 0.0)
p_front = V(0, yc - r, zb)                         # the front generatrix at that height
ga = math.atan2(HOPPER_H, -(FUN_BACK - R_FUN) + (R_FUN - RB))   # its slope from horizontal
nrm = V(0, math.sin(ga), math.cos(ga))             # into the hopper, up the slope's normal
ball = Part.makeSphere(BALL_D / 2, p_front + nrm * (BALL_D / 2 - 0.3))
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape, colour):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = cad.color(COLOURS[colour])
    return o


part("Base", base, "Base")
part("Shell", shell, "Shell")
part("Hopper", hopper, "Hopper")
part("Chute", chute, "Chute")
part("Flywheel_L", wheels[0], "Flywheel")
part("Flywheel_R", wheels[1], "Flywheel")
part("Tyre_L", tyres[0], "Tyre")
part("Tyre_R", tyres[1], "Tyre")
o = part("Light_Ring", ring, "Light_Ring")
o.ViewObject.Transparency = cad.transparency("frosted")   # glows cyan when ready
part("Bezel", bezel, "Bezel")
part("Grille", grille, "Grille")
o = part("Screen_Lens", lens, "Screen_Lens")
o.ViewObject.Transparency = cad.transparency("smoked")
part("Start_Key", cap, "Start_Key")
part("Ball", ball, "Ball")
part("Band", band, "Band")
for i, sh in enumerate(feet):
    part("Foot_%d" % (i + 1), sh, "Foot")
for i, sh in enumerate(screws):
    part("Screw_%d" % (i + 1), sh, "Screw")
print("SIZE %s" % (cad.measure(Part.makeCompound([base, shell, hopper, chute] + feet))["size"],))
print("TOTAL %.1f s" % (time.time() - T0))
