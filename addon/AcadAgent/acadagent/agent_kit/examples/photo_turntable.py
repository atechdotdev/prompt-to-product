"""Example: "a 360 photo turntable" - a motorised turntable that spins a product on a 188 mm platter for 360 videos.

fork this file for a photo turntable / display turntable / lazy susan
(a rotating stand, a 360 product spinner, a jewellery or cake display
turntable - a geared platter on a low round base); change PARAMETERS and the outlines.
ARCHETYPE: turntable

How it is built (R940):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board FLAT on the floor of a low round base, port 7 at the back (USB-C
    SEATED there, its mouth facing the back wall: a pocket and a liner
    bring the wall to 0.25 mm off it). The dc_motor (N20) is CABLED from
    port 13 and stands upright beside the board, shaft up (+Z): its ribbon
    leaves the plug outboard and turns up into the socket under it. A 12
    tooth pinion (cad.spur_gear, module 1, real involute teeth) on the
    shaft meshes a 76 tooth drive gear under the platter - centre distance
    m (z1 + z2) / 2 = 44 mm, measured off the shaft and printed; ratio
    6.33 : 1. The drive gear is pegged to the platter, the pair turns on a
    chrome axle in a boss hanging from the deck (intent "motion": the
    platter turns 360 deg, swept clear at 73 positions). A rim rising
    from the deck hides the gears 0.6 mm under the platter's overhang.
    The status light (14) and the speed key (6) are CABLED to a flat front
    facet, each between ribs and a back stop on the shell. The base is ONE
    revolved (radius, z) outline (a recessed dark plinth, a chamfered step,
    a straight drum with a reveal groove, a 45 deg top chamfer) hollowed
    by its own inset outline, the front facet cut flat through
    both, split low into the fixed Base (standoffs and fences under the
    board) and the Shell (deck, axle boss, motor ribs, spine rib); four M2.5
    screws from below into insert sleeves on tall columns that also carry
    the deck.
  * STAGE B - details: the rubber ring set into the platter, 72 tick marks
    round its edge (every 45 deg long), two centring rings, the coral index
    mark under the platter's edge, a raised ring round the key, lettering,
    rubber feet.
RESTYLE (R425): R_PLATTER, PLATTER_T, FACET_W and WALL drive every
outline and cutter below (the rubber ring, ticks and rim follow the
platter; the facet's distance, the key and the light follow FACET_W);
the heights follow the measured motor (its shaft sets the deck, the
gears and the platter). The board, the motor
and the gear centre distance are the hardware's own: never move them
with a knob.
DETAILS (visible, 25): 1 revolved drum base; 2 recessed dark plinth (it
floats); 3 chamfered step over the plinth; 4 45 deg top chamfer; 5 flat
front facet; 6 coral speed key with a flange; 7 raised ring round it;
8 frosted status lens; 9 "ATECH" on the facet; 10 coral index mark;
11 9 mm platter overhanging the deck's rim; 12 its top chamfer;
13 rubber ring set into the top; 14-15 two centring rings; 16 72 tick
marks round the edge; 17 eight long ticks every 45 deg; 18 the rim and
its shadow gap under the platter; 19 the reveal groove round the drum;
20 USB-C pocket with liner at the back; 21-24 four rubber feet; 25 four
countersunk screws under the base.
Inside: 26 the 12 tooth pinion on the motor shaft; 27 the 76 tooth drive
gear, three pegs into the platter, six lightening holes; 28 the chrome
axle in the hanging boss; 29 four motor ribs and the deck over the
motor; 30 ribs and back stops round the key and the light; 31 rib onto
the board's spine; 32 standoffs and fences; 33 the lip keying the shell
to the base.
Materials: graphite shell, matte black plinth, matte white platter,
rubber ring and feet, coral key and index, frosted lens, orange gears,
chrome axle and screws.
MEASURED (R940, 2026-11-10): ./check CHECK PASS, model 6.8 s, ./check run
9.7 s (50 s wall with the review sheets; every RESTYLE end CHECK PASS); GEAR Drive_Gear x Pinion 76:12, centre 44.05 mm
(needs 44.00), turns clear; MOTION Platter 0 .. 360 deg clear (73 positions).
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
    "Shell", "Platter", "Drive_Gear", "Pinion", "Axle", "Rubber_Ring", "Index_Mark", "Key_Speed",
    "Status_Lens", "Rubber_1", "Rubber_2", "Rubber_3", "Rubber_4",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4"],
    "covers": {"Key_Speed": "button_6"},
    "motion": [{"part": "Platter", "axis": [[0, 0, 0], [0, 0, 1]], "range_deg": [0, 360]}]}
# the platter and its drive gear are pegged together and turn as one
INTENDED_OVERLAPS = [("Platter", "Drive_Gear")]
REVIEW_CLOSEUPS = ["Key_Speed", "Platter", "Drive_Gear", "Pinion"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them; test_kit_examples_r280 builds
# this file with each knob at its min and at its max, one at a time.
R_PLATTER = 94.0       # RESTYLE 79..108.5 radius: the platter (the rubber ring, ticks and rim follow it)
PLATTER_T = 9.0        # RESTYLE 7.5..10.5 height: the platter's thickness
FACET_W = 88.0         # RESTYLE 74..102 width: the flat front facet across (x)
WALL = 2.5             # RESTYLE 2.1..2.9 wall
# end RESTYLE
# Frame: the platter's axis on z, the front at -Y, the desk at z = 0.
R_BASE = 98.0          # the drum's radius: the board's back corners and the screws need it
CHAMFER = 7.0          # the top chamfer (45 deg)
FACET = math.sqrt(R_BASE ** 2 - (FACET_W / 2) ** 2)   # the facet's distance from the axis
FOOT = 1.5             # rubber feet under the base
FLOOR = FOOT + 2.0     # the floor's top
SPLIT = FLOOR + 0.5    # base / shell seam, under every slide path (USB from z 8.5)
PLINTH = 5.0           # the plinth's recess (radius) and the step up over it
L = 6.0                # board underside (PCB top L + 2.5)
BOARD_BACK = 82.0     # the board's back edge: its back corners 4 mm inside the plinth wall
MOTOR_Z0 = 17.0        # the motor's lowest point: its socket and ribbon clear the floor
M, Z_PIN, Z_GEAR = 1.0, 12, 76          # gear module and teeth
BACKLASH = 0.1         # off each tooth (FDM)
CD = M * (Z_PIN + Z_GEAR) / 2.0 + 0.05  # centre distance + 0.05 backlash (atech_gears: -0.02..+0.15 m)
GEAR_T = 5.5           # face width of both gears
AXLE_R = 4.0           # the chrome axle (bores 0.1 mm clear)
RING = (0.62 * R_PLATTER, 0.894 * R_PLATTER)   # the rubber ring's radii on the platter
TICKS = 72             # tick marks round the platter (every 5 deg)
SCREWS = [(-72.0, -42.0), (72.0, -42.0), (-58.0, 58.0), (58.0, 58.0)]   # sleeves inside the lip
SCREW = "M2.5"
COLOURS = {"Base": "matte_black", "Shell": "graphite", "Platter": "matte_white", "Drive_Gear": "orange",
           "Pinion": "orange", "Axle": "chrome", "Rubber_Ring": "rubber", "Index_Mark": "coral",
           "Key_Speed": "coral", "Status_Lens": "frosted", "Rubber": "rubber", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
FLAT = Rotation(Vector(1, 0, 0), 90)
board = ap.board_object(doc)
board.Placement = Placement(Vector(), FLAT)
_b = ap.bbox(board)
board.Placement = Placement(Vector(-30.0 - _b.XMin, BOARD_BACK - _b.YMax, L - _b.ZMin), FLAT)   # x -30..30, y -38..82
BB = ap.bbox(board)
PT = L + 2.5                                           # the PCB top
usb = ap.seat(doc, "usbc", 7)                          # back centre, mouth +Y
# the motor: CABLED from port 13 (right column, y ~0), upright beside the
# board, pins down / shaft up; its shaft sits 0.57 mm along `face` off the
# module's centre, so the centre goes CD - 0.57 out along +X
motor, motor_rib = ap.cable(doc, "dc_motor", 13, ap.module_placement(
    "dc_motor", (CD - 0.57, 0.0, MOTOR_Z0 + 24.15), face="+X", cable="-Z"))
# the speed key (6) and the status light (14): CABLED to the front facet,
# facing -Y, pins outboard (toward their own plug's side)
MOD_Y, MOD_Z = -(FACET - WALL) + 7.0, 28.0
key, key_rib = ap.cable(doc, "button", 6, ap.module_placement(
    "button", (-20.0, MOD_Y, MOD_Z), face="-Y", cable="-X"))
glow, glow_rib = ap.cable(doc, "light", 14, ap.module_placement(
    "light", (20.0, MOD_Y, MOD_Z), face="-Y", cable="+X"))
MB = ap.bbox(motor)
# the shaft, measured: the mesh points in its top 6 mm
_sp = [p for p in motor.Mesh.Points if p.z > MB.ZMax - 6.0]
SX = (min(p.x for p in _sp) + max(p.x for p in _sp)) / 2.0
SY = 0.0
SHAFT_TIP = MB.ZMax
BODY_TOP = SHAFT_TIP - 8.8
print("SHAFT at (%.3f, %.3f), tip z %.2f; centre distance %.3f (m (z1 + z2) / 2 = %.2f)" % (
    SX, SY, SHAFT_TIP, math.hypot(SX, SY), M * (Z_PIN + Z_GEAR) / 2.0))
# the heights all follow the motor
TOP = BODY_TOP + 3.2                    # deck top: fixed over the motor so the gears stay on the shaft
DECK_IN = TOP - WALL                    # deck underside: >= 0.3 mm over the motor body at any WALL
G0 = TOP + 0.5                          # gears' underside (the drive gear rests on the boss)
G1 = G0 + GEAR_T                        # drive gear top = platter underside
P0, P1 = G1, G1 + PLATTER_T                   # platter underside / top
_rim = min(R_BASE - CHAMFER - 1.5, R_PLATTER - 4.0)      # under the platter's overhang
RIM = (_rim - 3.5, _rim)              # the deck's rim round the gears (inner, outer)
RIM_TOP = P0 - 0.6                      # 0.6 mm under the platter: the shadow gap
tick("hardware")


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def annulus(r0, r1, z0, z1, c=(0, 0)):
    return cad.cut(cyl(r1, (c[0], c[1], z0), z1 - z0), cyl(r0, (c[0], c[1], z0 - 1), z1 - z0 + 2))


def ycyl(r, x, z, y0, y1):
    return Part.makeCylinder(r, abs(y1 - y0), V(x, min(y0, y1), z), V(0, 1, 0))


def centre(m):
    b = ap.bbox(m)
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


def insert(shell, cutter):
    """(shell with the opening, the piece that fills it exactly)."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1:
        piece, rest = shell.common(cutter, 0.01), shell.cut(cutter, 0.01)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, piece


def yprism(x0, x1, z0, z1, y0, y1, r):
    w = cad.rounded_rect_wire(x1 - x0, z1 - z0, r, ((x0 + x1) / 2, y0, (z0 + z1) / 2), "Y")
    return Part.Face(w).extrude(V(0, y1 - y0, 0))


# ------------------------------------------------------------ the base
# ONE revolved outline: a recessed plinth, a 45 deg step out over it, the
# straight drum, a 45 deg top chamfer; the core is the same outline WALL in
R0, R1 = R_BASE - PLINTH, R_BASE
ZG = SPLIT + 0.5 + PLINTH + 0.3 * (TOP - CHAMFER - SPLIT - 0.5 - PLINTH)   # a reveal groove, in the section
outer = cad.revolve_profile([(0, FOOT), (R0, FOOT), (R0, SPLIT + 0.5), (R1, SPLIT + 0.5 + PLINTH),
                             (R1, ZG - 0.5), (R1 - 0.7, ZG - 0.5), (R1 - 0.7, ZG + 0.5), (R1, ZG + 0.5),
                             (R1, TOP - CHAMFER), (R1 - CHAMFER, TOP), (0, TOP)])
k = WALL * (math.sqrt(2) - 1)           # a 45 deg line offset WALL meets a vertical one this far along
core = cad.revolve_profile([(0, FLOOR), (R0 - WALL, FLOOR), (R0 - WALL, SPLIT + 0.5 + WALL - k + 0.0),
                            (R1 - WALL, SPLIT + 0.5 + PLINTH + WALL - k),
                            (R1 - WALL, TOP - CHAMFER - WALL + k), (R1 - CHAMFER - WALL + k, DECK_IN),
                            (0, DECK_IN)])
# the flat front facet through both skins
far = 3 * R_BASE
outer = cad.cut(outer, box(-far, far, -far, -FACET, -1, TOP + 1))
core = cad.cut(core, box(-far, far, -far, -(FACET - WALL), -1, TOP + 1))
shell = cad.cut(outer, core)
tick("base body")
base, shell = cad.split(shell, "Z", at=SPLIT, lip=1.2)
tick("split")

# the fixed base holds the board: standoffs 0.1 mm under it, fences 0.3 mm
# off its long edges (clear of the motor's ribbon round y 0 on the right)
holders = [box(x - 3, x + 3, y - 3, y + 3, FLOOR - 0.5, BB.ZMin - 0.1)
           for x in (BB.XMin + 12, BB.XMax - 12) for y in (BB.YMin + 14, 30.0, BB.YMax - 14)]
holders += [box(BB.XMin - 1.8, BB.XMin - 0.3, y - 5, y + 5, FLOOR - 0.5, PT - 1.5) for y in (-12.0, 40.0, 72.0)]
holders += [box(BB.XMax + 0.3, BB.XMax + 1.8, y - 5, y + 5, FLOOR - 0.5, PT - 1.5) for y in (40.0, 72.0)]
base = cad.fuse_one(base, *holders)

# the shell: the axle boss hanging from the deck, raised 0.5 mm over it
# (the drive gear rests on it), its blind bore 0.1 mm round the axle
BOSS_Z0 = TOP - 15.0
shell = cad.fuse_one(shell, cyl(7.5, (0, 0, BOSS_Z0), TOP - 0.5 - BOSS_Z0), cyl(9.0, (0, 0, TOP - 0.5), 1.0))
shell = cad.cut(shell, cyl(AXLE_R + 0.1, (0, 0, BOSS_Z0 + 1.5), G0 + 1 - BOSS_Z0 - 1.5))
# the rim: a ring up from the deck round the gears, 0.6 mm under the
# platter's overhang - it hides the drive and reads as a shadow gap
shell = cad.fuse_one(shell, annulus(RIM[0], RIM[1], TOP - 0.5, RIM_TOP))
# the shaft's way up through the deck
shell = cad.hole(shell, at=(SX, SY, TOP), axis="-Z", d=6.0, through="wall")
# the motor's holder: four ribs down from the deck to 0.3 mm off its body
RZ0 = MB.ZMax - 30.0
mcy = (MB.YMin + MB.YMax) / 2
ribs = [box(SX - 4, SX + 4, MB.YMax + 0.3, MB.YMax + 2.3, RZ0, DECK_IN + 0.5),
        box(SX - 4, SX + 4, MB.YMin - 2.3, MB.YMin - 0.3, RZ0, DECK_IN + 0.5),
        box(MB.XMax + 0.3, MB.XMax + 2.3, mcy - 4, mcy + 4, RZ0, DECK_IN + 0.5),
        box(MB.XMin - 2.3, MB.XMin - 0.3, mcy - 4, mcy + 4, RZ0, DECK_IN + 0.5)]
# board retention: a rib down from the deck onto the spine (0.2 mm off it)
ribs.append(box(-1.0, 1.0, 14.0, 50.0, BB.ZMax + 0.2, DECK_IN + 0.5))
# the key and the light: ribs over and under each, from the front wall
# back, and a back stop behind (the key is pressed against it)
for m in (key, glow):
    b = ap.bbox(m)
    cx = (b.XMin + b.XMax) / 2
    ribs += [box(b.XMin + 2, b.XMax - 2, -(FACET - WALL) - 0.5, b.YMax + 2.3, b.ZMax + 0.3, b.ZMax + 2.3),
             box(b.XMin + 2, b.XMax - 2, -(FACET - WALL) - 0.5, b.YMax - 3.0, b.ZMin - 2.3, b.ZMin - 0.3),
             box(cx - 4, cx + 4, b.YMax + 0.3, b.YMax + 2.3, b.ZMin + 3.0, b.ZMax + 2.3)]
shell = cad.fuse_one(shell, *ribs)
tick("boss + ribs")

# four M2.5 up through the base into insert sleeves on columns that hang
# from the deck (they carry it too)
INSERT_D = {"M2": 3.2, "M2.5": 3.6, "M3": 4.3}[SCREW]
screws = []
for x, y in SCREWS:
    shell = cad.screw_boss(shell, (x, y, FLOOR + 0.1), axis="+Z", size=SCREW, ribs=0)
    base = cad.countersink(base, (x, y, FOOT), "+Z", 2.9, 5.6, 90.0)
    screws.append(cad.screw("csk_phillips", SCREW, 10, at=(x, y, FOOT), axis="+Z"))
shell = cad.fuse_one(shell, *[cyl(INSERT_D / 2 + 1.2, (x, y, FLOOR + 0.1), 10.0) for x, y in SCREWS])
shell = cad.cut(shell, [cyl(INSERT_D / 2, (x, y, FLOOR), 9.5) for x, y in SCREWS])
tick("screws")

# ------------------------------------------------------------ front openings
FY_OUT, FY_IN = -FACET, -(FACET - WALL)
# the speed key: a cap through the facet, flange 0.1 mm behind it, a
# plunger to 0.16 mm off the module's own cap
kx, _ky, kz = centre(key)
k_face = ap.bbox(key).YMin
cap_base = FY_IN + 0.9
cap = cad.button_cap(13.0, cap_base - (FY_OUT - 1.6), dome=0.8, flange=1.5, at=(kx, cap_base, kz), axis="-Y")
shell = cad.opening_for(shell, cap, clearance=0.25, chamfer=0.4, axis="-Y")
cap = cad.fuse_one(cap, ycyl(3.0, kx, kz, cap_base - 0.5, k_face - 0.16))
# the status light: a frosted light pipe from 0.4 mm off the LEDs to 1.2 mm
# proud, a flange behind the facet
gx, _gy, gz = centre(glow)
g_face = ap.bbox(glow).YMin
lens = cad.lens(17.6, (g_face - 0.4) - (FY_OUT - 1.2), dome=1.0, at=(gx, g_face - 0.4, gz), axis="-Y")
shell = cad.opening_for(shell, lens, clearance=0.2, chamfer=0.0, axis="-Y")
lens = cad.fuse_one(lens, ycyl(9.6, gx, gz, FY_IN + 0.1, FY_IN + 0.9))
# USB-C at the back: a pocket brings the wall to 0.25 mm off the mouth
ub = ap.bbox(usb)
ux, uz = (ub.XMin + ub.XMax) / 2, PT + 5.9
pocket = yprism(ux - 6.5, ux + 6.5, uz - 5.0, uz + 5.0, ub.YMax + 1.3, R_BASE + 5, 3)
liner = cad.cut(yprism(ux - 8.5, ux + 8.5, max(uz - 7.0, SPLIT + 1.6), uz + 7.0, ub.YMax + 0.25,
                       R_BASE - WALL + 1.0, 3.5), pocket)
shell = cad.fuse_one(cad.cut(shell, pocket), liner)
shell = cad.socket_opening(shell, usb, margin=1.5)
tick("openings")

# ------------------------------------------------------------ the drive
# the pinion on the shaft (bore 3.3 round the 3.0 shaft), the drive gear
# on the axle; each phased so a tooth of one points into a space of the other
pinion = cad.spur_gear(M, Z_PIN, GEAR_T - 0.3, bore=3.3, backlash=BACKLASH)
pinion.translate(V(SX, SY, G0))
pinion = cad.mesh_phase(pinion, (SX, SY, G0), "+Z", (-SX, -SY, 0), tooth=True)
gear = cad.spur_gear(M, Z_GEAR, GEAR_T, backlash=BACKLASH)
gear = cad.cut(gear, [cyl(6.0, (22.0 * math.cos(math.radians(a)), 22.0 * math.sin(math.radians(a)), -1), GEAR_T + 2)
                      for a in range(30, 360, 60)])
gear = cad.hole(gear, at=(0, 0, 0), axis="+Z", d=2 * (AXLE_R + 0.1), through=True)
gear.translate(V(0, 0, G0))
# three pegs up into the platter (0.15 mm clear in their holes)
PEGS = [(30.0 * math.cos(math.radians(a)), 30.0 * math.sin(math.radians(a))) for a in (0, 120, 240)]
gear = cad.mesh_phase(gear, (0, 0, G0), "+Z", (SX, SY, 0))
gear = cad.fuse_one(gear, *[cyl(1.5, (x, y, G1 - 0.5), 3.5) for x, y in PEGS])
# the platter: ONE revolved outline - the disc with a chamfered top edge
# and an eased underside, overhanging the deck's rim; a blind bore for the axle
platter = cad.revolve_profile([(AXLE_R + 0.1, P0), (R_PLATTER - 1.0, P0), (R_PLATTER, P0 + 1.0),
                               (R_PLATTER, P1 - 1.5), (R_PLATTER - 1.5, P1), (0, P1),
                               (0, P0 + 4.0), (AXLE_R + 0.1, P0 + 4.0)])
platter = cad.cut(platter, [cyl(1.65, (x, y, P0 - 1), 4.0) for x, y in PEGS])
axle = cyl(AXLE_R, (0, 0, BOSS_Z0 + 2.0), P0 + 3.5 - (BOSS_Z0 + 2.0))
axle = cad.soften(axle, 0.5)
tick("stage A")


# === STAGE B: details ===
# (a fork may stop after STAGE A, run ./check, then add these one by one)
# the rubber ring: set into a 1 mm groove in the platter top, 0.8 mm proud
platter = cad.cut(platter, annulus(RING[0], RING[1], P1 - 1.0, P1 + 1.0))
# 0.15 mm clear in its groove; chamfered in its section (a revolve: cheap
# for the platter's motion sweep, where a filleted ring cost 3 x)
r0, r1 = RING[0] + 0.15, RING[1] - 0.15
rubber = cad.revolve_profile([(r0, P1 - 0.9), (r1, P1 - 0.9), (r1, P1 + 0.3), (r1 - 0.5, P1 + 0.8),
                              (r0 + 0.5, P1 + 0.8), (r0, P1 + 0.3)])
# two centring rings and 72 tick marks round the edge (every 45 deg long)
grooves = [annulus(r - 0.4, r + 0.4, P1 - 0.5, P1 + 1.0) for r in (0.213 * R_PLATTER, 0.426 * R_PLATTER)]
for i in range(TICKS):
    a = 360.0 * i / TICKS
    ln = 6.0 if i % 9 == 0 else (4.0 if i % 3 == 0 else 2.5)
    t = box(R_PLATTER - 3.0 - ln, R_PLATTER + 1.0, -0.4, 0.4, P1 - 0.6, P1 + 1.0)
    t.rotate(V(0, 0, 0), V(0, 0, 1), a - 90.0)            # tick 0 at the front (-Y)
    grooves.append(t)
platter = cad.cut(platter, grooves)
# the coral index mark under the platter's front edge (an insert through the facet)
tri = Part.Face(Part.makePolygon([V(-4.0, 0, TOP - 3.5), V(4.0, 0, TOP - 3.5), V(0, 0, TOP - 9.5),
                                  V(-4.0, 0, TOP - 3.5)])).extrude(V(0, WALL + 2.0, 0))
tri.translate(V(0, FY_OUT - 1.0, 0))
shell, index = insert(shell, tri)
# a raised ring round the key, lettering on the facet
shell = cad.fuse_one(shell, cad.cut(ycyl(9.8, kx, kz, FY_OUT - 0.6, FY_OUT + 0.5),
                                    ycyl(8.3, kx, kz, FY_OUT - 1.0, FY_OUT + 1.0)))
shell = cad.text(shell, "ATECH", (0, FY_OUT, 14.0), (0, -1, 0), 5, depth=0.5, mode="deboss")
# rubber feet in recesses under the base
feet = []
for a in (45, 135, 225, 315):
    x, y = 66.0 * math.cos(math.radians(a)), 66.0 * math.sin(math.radians(a))
    base = cad.cut(base, cyl(4.6, (x, y, FOOT - 1), 2.2))
    feet.append(cad.foot(9, FOOT + 1.2, style="dome", at=(x, y, FOOT + 1.2)))
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape, colour):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = cad.color(COLOURS[colour])
    return o


part("Base", base, "Base")
part("Shell", shell, "Shell")
part("Platter", platter, "Platter")
part("Drive_Gear", gear, "Drive_Gear")
part("Pinion", pinion, "Pinion")
part("Axle", axle, "Axle")
part("Rubber_Ring", rubber, "Rubber_Ring")
part("Index_Mark", index, "Index_Mark")
part("Key_Speed", cap, "Key_Speed")
o = part("Status_Lens", lens, "Status_Lens")
o.ViewObject.Transparency = cad.transparency("frosted")
for i, sh in enumerate(feet):
    part("Rubber_%d" % (i + 1), sh, "Rubber")
for i, sh in enumerate(screws):
    part("Screw_%d" % (i + 1), sh, "Screw")
print("SIZE %s" % (cad.measure(Part.makeCompound([o.Shape for o in doc.Objects
                                                   if o.TypeId == "Part::Feature" and o.Label[0].isupper()
                                                   and hasattr(o, "Shape")]))["size"],))
print("TOTAL %.1f s" % (time.time() - T0))
