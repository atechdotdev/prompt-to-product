"""Example: "a night-sky projector that fills my kid's ceiling with stars" - a navy star ball that slowly turns on a cream base and throws a sky of stars on the ceiling.

fork this file for a star projector (a night-sky lamp, a planetarium night
light, a rotating star ball, a nursery light that plays lullabies); change PARAMETERS and the outlines.
ARCHETYPE: star projector

How it is built (R1030):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board FLAT on the base's axis (x -30..30, y -60..60), the lights on
    ports 2 and 3 SEATED under the ball, shining straight up through two
    frosted lenses in the deck, through the windows of the drive gear and
    out of the pierced ball (a Pleiades cluster is drilled right over each
    light). USB-C (7) in a pocket in the back wall. The dc_motor (N20) is
    CABLED from port 13 and stands upright beside the board, shaft up
    through the deck: a 12 tooth pinion (cad.spur_gear, module 1) meshes
    the 84 tooth hub gear the ball is pegged to (centre distance 48 mm,
    ratio 7 : 1, intent "motion": the ball turns 360 deg). The hub gear
    turns on a chrome axle in a boss hanging from the deck; a gold collar
    round it hides the drive. The speaker (4, 5) is CABLED to the LEFT
    side, face out behind a gold grille, its pins down so both ribbons run
    straight out of the board's left edge and dip under it into the
    sockets (no twist); the brightness dial (knob, 10 + 11) is cabled the
    same way to the RIGHT side, its shaft through a frosted LED ring with a
    knurled gold cap; the big soft on/off/timer key (button, 14) is cabled
    to the front, held by a rib from the deck, a post from the floor and a
    back stop. The base is a rounded box (vertical corners r 22, a rolled
    top edge) hollowed by its own inset core and split low into the fixed
    navy Base (standoffs and fences under the board) and the cream Shell;
    four M2.5 screws from below into heat-set insert columns. The ball is
    ONE sphere outline revolved in two halves, each printed rim down
    (the dome's last ~10 mm round the pole bridge over Polaris): the Shade_Lower band (an inner flange on the hub gear, three
    pegs) and the Shade_Top dome (a spigot into the band, three pins into
    pads); Polaris is the pole hole the sky turns round.
  * STAGE B - details: 150-odd star holes of six sizes (each band of the
    sphere keeps its own face, so no face carries more than ~70 holes),
    three gold constellation inlays (the Big Dipper, Cassiopeia, Orion)
    standing 0.5 mm proud with a hole through every star, a frosted
    crescent moon window, the moon debossed on the key, a raised ring round
    it, lettering, four gold bun feet.
DETAILS (visible, 28): 1 navy star ball; 2 ~150 pierced stars in six sizes;
3 a Pleiades cluster over each light; 4 Polaris, the pole hole the sky turns
round; 5 the gold Big Dipper inlay; 6 the gold Cassiopeia "W"; 7 gold Orion
with his belt; 8 a hole through every gold star; 9 the frosted crescent
moon window; 10 the seam at the equator; 11 the gold collar cup under the
ball; 12 cream rounded-box base; 13 its rolled top edge; 14 the navy plinth
line; 15 four gold bun feet; 16 the big soft yellow key; 17 a crescent
moon debossed on it; 18 a raised ring round the key; 19 the gold speaker
grille on the left side (ring of holes); 20 the brightness dial: a knurled
gold cap; 21 its pointer groove; 22 the frosted LED ring round it; 23
"ATECH" on the front; 24 USB-C pocket with a liner at the back; 25 "ATECH
SP-1" under the base; 26 four countersunk screws under the base.
Inside: 27 the 12 tooth pinion and the 84 tooth hub gear with four light
windows; 28 the chrome axle in its hanging boss; motor ribs; key rib, post
and back stop; speaker and dial ribs and back stops; frosted lenses over the
lights; a rib onto the board's spine; standoffs and fences; insert columns;
the spigot, pads and pins that join the two halves of the ball.
Materials: navy ball, gold inlays, collar, grille, dial cap and feet,
frosted moon, LED ring and lenses, cream shell, navy plinth, soft yellow key,
white gears, chrome axle and screws.
MEASURED (R1030, 2026-11-20): ./check CHECK PASS, run_seconds 22 s, wall 121 s (load 33 on 18 cores; 86-107 s at the SHADE_R ends); every RESTYLE end CHECK PASS.
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
    "Shell", "Drive_Gear", "Pinion", "Axle", "Shade_Lower", "Shade_Top", "Collar", "Key",
    "Dial_Cap", "Dial_Ring", "Grille", "Lens_1", "Lens_2", "Moon", "Big_Dipper", "Cassiopeia",
    "Orion", "Foot_1", "Foot_2", "Foot_3", "Foot_4",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4"],
    # the big key presses the on/off/timer button (a declared cover, see ./check)
    "covers": {"Key": "button_14"},
    "motion": [{"part": "Shade_Lower", "axis": [[0, 0, 0], [0, 0, 1]], "range_deg": [0, 360]}]}
# the ball and its hub gear are pegged together and turn as one; the two
# halves of the ball are pinned together
INTENDED_OVERLAPS = [("Shade_Lower", "Drive_Gear"), ("Shade_Lower", "Shade_Top")]
REVIEW_CLOSEUPS = ["Shade_Top", "Key", "Dial_Cap", "Drive_Gear"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them (the ball's two halves, its
# joint, the star field, the inlays and the moon follow SHADE_R; every
# height follows FOOT_H; the key, its ring and its opening follow BUTTON_D;
# the deck height and the base core follow ROLL and WALL).
SHADE_R = 58.0     # RESTYLE 49..67 radius: the star ball
FOOT_H = 8.0       # RESTYLE 6.8..9.2 height: the gold bun feet (everything stands on them)
BUTTON_D = 28.0    # RESTYLE 23.8..32.2 width: the big soft key across
ROLL = 12.0        # RESTYLE 10.2..13.8 radius: the base's rolled top edge
WALL = 2.4         # RESTYLE 2.0..2.8 wall: the base shell and the ball
# end RESTYLE
# Frame: the ball's axis on z through the board's centre, the front at -Y,
# the desk at z = 0. The base's plan is the hardware's: never move it with a knob.
W2, D2 = 76.0, 80.0        # the base's half width (x) and half depth (y)
CORNER = 22.0              # the base's vertical corners
Z0 = FOOT_H                # the base's underside (the feet below it)
FLOOR_T = 2.5
FL1 = Z0 + FLOOR_T         # the floor's top
SPLIT = FL1 + 0.5          # base / shell seam, under every slide path
L = Z0 + 5.0               # board underside (standoffs 2.5)
PT = L + 2.5               # the PCB top
MZ = FL1 + 21.0            # the side modules' centre height (their ribbons loop over them)
GRILLE_D = 30.0            # the speaker grille
RING_R = (8.05, 14.5)      # the frosted LED ring round the dial's shaft
CAP_R = 11.0               # the dial's cap
KNOB_OUT = 16.0            # the dial's shaft tip beyond the right side
KEY_Z = MZ                 # the key's centre height
KEY_PROUD = 3.0            # the key stands this far out of the front
M, Z_PIN, Z_GEAR = 1.0, 12, 84          # gear module and teeth
BACKLASH = 0.1
CD = M * (Z_PIN + Z_GEAR) / 2.0 + 0.12  # centre distance: + 0.06 measured at the shaft, + backlash
GEAR_T = 5.5
AXLE_R = 4.0
MOTOR_Y = -22.0            # the motor beside the board, 8 mm off its port (13)
COLLAR = (56.0, 58.5)      # the gold collar round the gears (inner, outer)
RB = 46.0                  # the ball's bottom opening (outer radius)
FL_IN, FL_T = 37.5, 3.0    # the ball's inner flange on the hub gear
LIP = 4.0                  # the top's spigot down into the band
SCREW = "M2.5"
SCREWS = [(-56.0, 60.0), (56.0, 60.0), (-52.0, -66.0), (56.0, -66.0)]
FEET = [(-46.0, 50.0), (46.0, 50.0), (-46.0, -50.0), (46.0, -50.0)]
# the deck: over the side modules and high enough that the grille, the
# dial's ring and the key all sit on the flat sides under the roll
# (and over the motor: its socket run starts at the PCB top, its shaft
# reaches 5.6 mm over the deck into the pinion)
D_TOP = max(MZ + 20.0 + 7.0 + 0.5 + WALL, MZ + max(GRILLE_D / 2, RING_R[1]) + ROLL + 1.5,
            KEY_Z + BUTTON_D / 2 + 2.5 + ROLL + 1.0, PT + 14.5 + 48.3 - 5.6 + 0.3)
DECK_IN = D_TOP - WALL
NAVY = "#1f2d5c"
GOLD = "#f0bf4c"
COLOURS = {"Base": NAVY, "Shell": "cream", "Shade_Lower": NAVY, "Shade_Top": NAVY,
           "Drive_Gear": "matte_white", "Pinion": "matte_white", "Axle": "chrome", "Collar": GOLD,
           "Key": "#ffd866", "Dial_Cap": GOLD, "Dial_Ring": "frosted", "Grille": GOLD,
           "Lens": "frosted", "Moon": "#fff4c4", "Inlay": GOLD, "Foot": GOLD, "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
FLAT = Rotation(Vector(1, 0, 0), 90)
board = ap.board_object(doc)
board.Placement = Placement(Vector(), FLAT)
_b = ap.bbox(board)
board.Placement = Placement(Vector(-30.0 - _b.XMin, 60.0 - _b.YMax, L - _b.ZMin), FLAT)   # x -30..30, y -60..60
BB = ap.bbox(board)
usb = ap.seat(doc, "usbc", 7)                          # back centre, mouth +Y
lights = [ap.seat(doc, "light", n) for n in (2, 3)]    # left of the axis, under the ball
# the speaker (4, 5) to the left side, face out (-X), pins UP: both ribbons
# leave the left edge, rise behind the module and loop over into its
# sockets, no twist and no crossing (pins down, the two ribbons cross)
spk, spk_rib = ap.cable(doc, "speaker", (4, 5), ap.module_placement(
    "speaker", (-(W2 - WALL - 1.0) + 10.1, -20.0, MZ), face="-X", cable="+Z"))
# the brightness dial (knob 10 + 11) to the right side the same way
KB = W2 + KNOB_OUT - 38.1                              # the dial module's back (x)
knob, knob_rib = ap.cable(doc, "knob", (10, 11), ap.module_placement(
    "knob", (KB + 19.05, 20.0, MZ - 0.25), face="+X", cable="+Z"))
# the motor: CABLED from port 13, upright beside the board, shaft up; its
# shaft sits 0.57 mm along `face` off the module's centre
SHAFT_TIP = D_TOP + 5.6
motor, motor_rib = ap.cable(doc, "dc_motor", 13, ap.module_placement(
    "dc_motor", (math.sqrt(CD ** 2 - MOTOR_Y ** 2) - 0.57, MOTOR_Y, SHAFT_TIP - 24.15), face="+X", cable="-Z"))
# the big key (14): to the front, facing -Y, pins outboard (+X)
MOD_Y = -(D2 - WALL) + 7.0
key, key_rib = ap.cable(doc, "button", 14, ap.module_placement(
    "button", (20.0, MOD_Y, KEY_Z), face="-Y", cable="+X"))
MB = ap.bbox(motor)
_sp = [p for p in motor.Mesh.Points if p.z > MB.ZMax - 6.0]
SX = (min(p.x for p in _sp) + max(p.x for p in _sp)) / 2.0
SY = (min(p.y for p in _sp) + max(p.y for p in _sp)) / 2.0
print("SHAFT at (%.3f, %.3f), tip z %.2f; centre distance %.3f (m (z1 + z2) / 2 = %.2f)" % (
    SX, SY, MB.ZMax, math.hypot(SX, SY), M * (Z_PIN + Z_GEAR) / 2.0))
G0 = D_TOP + 0.5                       # gears' underside (the hub gear rests on the boss)
G1 = G0 + GEAR_T                       # hub gear top = the ball's flange underside
ZB = G1
ZC = ZB + math.sqrt(SHADE_R ** 2 - RB ** 2)   # the ball's centre (the seam)
RI = SHADE_R - WALL
tick("hardware")


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def annulus(r0, r1, z0, z1, c=(0, 0)):
    return cad.cut(cyl(r1, (c[0], c[1], z0), z1 - z0), cyl(r0, (c[0], c[1], z0 - 1), z1 - z0 + 2))


def xcyl(r, y, z, x0, x1):
    return Part.makeCylinder(r, abs(x1 - x0), V(min(x0, x1), y, z), V(1, 0, 0))


def ycyl(r, x, z, y0, y1):
    return Part.makeCylinder(r, abs(y1 - y0), V(x, min(y0, y1), z), V(0, 1, 0))


def xring(r0, r1, y, z, x0, x1):
    return cad.cut(xcyl(r1, y, z, x0, x1), xcyl(r0, y, z, x0 - 1, x1 + 1))


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


def arc(c, r, a0, a1):
    """('arc', mid, end) of the circle (c, r) from angle a0 to a1 (deg)."""
    am, a1 = math.radians((a0 + a1) / 2), math.radians(a1)
    return ("arc", (c[0] + r * math.cos(am), c[1] + r * math.sin(am)),
            (c[0] + r * math.cos(a1), c[1] + r * math.sin(a1)))


def rbox(w2, d2, r, z0, z1, top_r=None, bottom_r=None):
    """The base's rounded box, its top (and bottom) edges rolled."""
    b = cad.rounded_box(2 * w2, 2 * d2, z1 - z0, r, at=(-w2, -d2, z0))
    if top_r:
        b = cad.fillet_safe(b, top_r, [e for e in b.Edges if e.BoundBox.ZMin > z1 - 1e-6])
    if bottom_r:
        b = cad.fillet_safe(b, bottom_r, [e for e in b.Edges if e.BoundBox.ZMax < z0 + 1e-6])
    return b


# ------------------------------------------------------------ the base
outer = rbox(W2, D2, CORNER, Z0, D_TOP, ROLL, 2.0)
core = rbox(W2 - WALL, D2 - WALL, CORNER - WALL, FL1, DECK_IN, ROLL - WALL)
body = cad.cut(outer, core)
tick("base body")
base, shell = cad.split(body, "Z", at=SPLIT, lip=1.2)
tick("split")
# the fixed base holds the board: standoffs 0.1 mm under it, fences 0.3 mm
# off its long edges below the slide paths, clear of every ribbon's exit
holders = [box(x - 3, x + 3, y - 3, y + 3, FL1 - 0.5, BB.ZMin - 0.1)
           for x in (BB.XMin + 12, BB.XMax - 12) for y in (BB.YMin + 12, 0.0, BB.YMax - 12)]
holders += [box(BB.XMin - 1.8, BB.XMin - 0.3, y - 4, y + 4, FL1 - 0.5, PT - 1.5) for y in (46.0, -48.0)]
holders += [box(BB.XMax + 0.3, BB.XMax + 1.8, y - 4, y + 4, FL1 - 0.5, PT - 1.5) for y in (48.0, -10.0)]
# the key's post up from the floor to 0.3 mm under the button
kb_ = ap.bbox(key)
holders.append(box(kb_.XMin + 3, kb_.XMax - 3, kb_.YMin + 0.5, kb_.YMin + 4.0, FL1 - 0.5, kb_.ZMin - 0.3))
# bosses for the feet's pegs
holders += [cyl(4.5, (x, y, FL1 - 0.5), 3.5) for x, y in FEET]
base = cad.fuse_one(base, *holders)

# the shell: the axle boss hanging from the deck, raised 0.5 mm over it
# (the hub gear rests on it), its blind bore 0.1 mm round the axle
BOSS_Z0 = D_TOP - 15.0
shell = cad.fuse_one(shell, cyl(7.5, (0, 0, BOSS_Z0), D_TOP - 0.5 - BOSS_Z0), cyl(9.0, (0, 0, D_TOP - 0.5), 1.0))
shell = cad.cut(shell, cyl(AXLE_R + 0.1, (0, 0, BOSS_Z0 + 1.5), G0 + 1 - BOSS_Z0 - 1.5))
# the shaft's way up through the deck
shell = cad.hole(shell, at=(SX, SY, D_TOP), axis="-Z", d=6.0, through="wall")
# the motor's holder: four ribs down from the deck to 0.3 mm off its body
RZ0 = MB.ZMax - 30.0
mcy = (MB.YMin + MB.YMax) / 2
mcx = (MB.XMin + MB.XMax) / 2
ribs = [box(mcx - 4, mcx + 4, MB.YMax + 0.3, MB.YMax + 2.3, RZ0, DECK_IN + 0.5),
        box(mcx - 4, mcx + 4, MB.YMin - 2.3, MB.YMin - 0.3, RZ0, DECK_IN + 0.5),
        box(MB.XMax + 0.3, MB.XMax + 2.3, mcy - 4, mcy + 4, RZ0, DECK_IN + 0.5),
        box(MB.XMin - 2.3, MB.XMin - 0.3, mcy - 4, mcy + 4, RZ0, DECK_IN + 0.5)]
# board retention: a rib down from the deck onto the spine (0.2 mm off it)
ribs.append(box(-1.0, 1.0, 14.0, 38.0, BB.ZMax + 0.2, DECK_IN + 0.5))
# the key: a rib from the deck onto its top, a back stop behind it
kcx = (kb_.XMin + kb_.XMax) / 2
ribs += [box(kb_.XMin + 3, kb_.XMax - 3, kb_.YMin + 0.5, kb_.YMax, kb_.ZMax + 0.3, DECK_IN + 0.5),
         box(kcx - 4, kcx + 4, kb_.YMax + 0.3, kb_.YMax + 2.3, kb_.ZMin + 3.0, DECK_IN + 0.5)]
# the speaker and the dial: ribs 0.3 mm off their front and back faces
# from the side wall in (their ribbons loop up behind them)
SB = ap.bbox(spk)
NB = ap.bbox(knob)
for b, xr in ((SB, (-(W2 - WALL) - 0.5, SB.XMax - 3.0)), (NB, (W2 - WALL + 0.5, NB.XMin + 6.0))):
    ribs += [box(xr[0], xr[1], b.YMin - 2.3, b.YMin - 0.3, b.ZMin + 4.0, b.ZMax - 4.0),
             box(xr[0], xr[1], b.YMax + 0.3, b.YMax + 2.3, b.ZMin + 4.0, b.ZMax - 4.0)]
shell = cad.fuse_one(shell, *ribs)
tick("boss + ribs")

# four M2.5 up through the floor into insert columns hanging from the deck
INSERT_D = {"M2": 3.2, "M2.5": 3.6, "M3": 4.3}[SCREW]
PILOT_D = {"M2": 1.7, "M2.5": 2.1, "M3": 2.5}[SCREW]
D_SCREW = float(SCREW[1:])
screws, cols, bores, csks = [], [], [], []
for x, y in SCREWS:
    cols.append(cyl(INSERT_D / 2 + 1.2, (x, y, FL1 + 0.1), DECK_IN + 0.5 - (FL1 + 0.1)))
    bores.append(cyl(INSERT_D / 2, (x, y, FL1), 9.0))
    bores.append(cyl(PILOT_D / 2, (x, y, FL1 + 8.0), 2.5 * D_SCREW + 2.0))
    csks.append(Part.makeCone(5.6 / 2, 2.9 / 2, (5.6 - 2.9) / 2, V(x, y, Z0 - 0.01), V(0, 0, 1)))
    csks.append(cyl(2.9 / 2, (x, y, Z0 - 0.5), FLOOR_T + 1.0))
    screws.append(cad.screw("csk_phillips", SCREW, 10, at=(x, y, Z0), axis="+Z"))
shell = cad.cut(cad.fuse_one(shell, *cols), bores)
base = cad.cut(base, csks)
tick("screws")

# ------------------------------------------------------------ openings
# the lights: a frosted lens through the deck over each
lenses = []
for m in lights:
    lx, ly, _ = centre(m)
    shell, lens = insert(shell, cyl(8.0, (lx, ly, DECK_IN - 1.0), WALL + 2.0))
    lenses.append(lens)
# the gold collar round the gears, keyed 1 mm into the deck
groove = annulus(COLLAR[0], COLLAR[1], D_TOP - 1.0, D_TOP + 1.0)
shell, ckey = insert(shell, groove)
collar = cad.fuse_one(ckey, annulus(COLLAR[0], COLLAR[1], D_TOP - 0.5, G1 + 2.0))
# three pins down from the collar's key through the deck (0.15 mm clear)
CPIN = [((COLLAR[0] + COLLAR[1]) / 2 * math.cos(math.radians(a)),
         (COLLAR[0] + COLLAR[1]) / 2 * math.sin(math.radians(a))) for a in (60, 180, 300)]
collar = cad.fuse_one(collar, *[cyl(0.9, (x, y, DECK_IN - 1.0), WALL + 0.5) for x, y in CPIN])
shell = cad.cut(shell, [cyl(1.05, (x, y, DECK_IN - 2.0), WALL + 1.0) for x, y in CPIN])
# the big key: a soft domed cap through the front, flange 0.1 mm behind it,
# a plunger to 0.16 mm off the module's own cap
FY_OUT, FY_IN = -D2, -(D2 - WALL)
kx, _ky, kz = centre(key)
k_face = kb_.YMin
cap_base = FY_IN + 0.9
cap = cad.button_cap(BUTTON_D, cap_base - (FY_OUT - KEY_PROUD), dome=2.0, flange=1.5,
                     at=(kx, cap_base, kz), axis="-Y")
shell = cad.opening_for(shell, cap, clearance=0.3, chamfer=0.5, axis="-Y")
cap = cad.fuse_one(cap, ycyl(3.0, kx, kz, cap_base - 0.5, k_face - 0.16))
# the speaker: a gold grille disc that fills its own opening in the left
# side (an insert), a ring of holes through it (grilled on the plain disc)
sx, sy, sz = centre(spk)
shell, grille = insert(shell, xcyl(GRILLE_D / 2, sy, sz, -W2 - 1.0, -(W2 - WALL) + 1.0))
grille = cad.fuse_one(grille, xcyl(GRILLE_D / 2 + 1.5, sy, sz, -W2 - 1.0, -W2 + 0.0))
grille = cad.speaker_grille(grille, (-W2 - 1.0, sy, sz), (-1, 0, 0), GRILLE_D - 5, ring_pitch=2.6, hole=1.6)
# the dial: its shaft out through a frosted ring over its LED ring, the
# ring's pipe down to 0.5 mm off the dial's plate; a gold cap on the shaft
nx, ny, nz = centre(knob)
PLATE = NB.XMin + 10.1
shell = cad.cut(shell, xcyl(RING_R[0], ny, nz, W2 - WALL - 1.0, W2 + 1.0))
shell, dring = insert(shell, xring(RING_R[0] - 0.5, RING_R[1], ny, nz, W2 - WALL - 1.0, W2 + 1.0))
dring = cad.fuse_one(dring, xring(RING_R[0], RING_R[1] - 1.0, ny, nz, PLATE + 0.5, W2 - WALL + 0.3))
KT = NB.XMax + 2.0
dcap = cad.fuse_one(xcyl(CAP_R, ny, nz, W2 + 0.6, KT),
                    xring(6.45, RING_R[0] - 0.2, ny, nz, W2 - 2.0, W2 + 1.0))
dcap = cad.fillet_safe(dcap, 1.5, edges=[e for e in dcap.Edges if e.BoundBox.XMin > KT - 0.01])
dcap = cad.cut(dcap, xcyl(6.45, ny, nz, W2 - 3.0, NB.XMax + 0.4))
# USB-C at the back: a pocket brings the wall to 0.25 mm off the mouth
ub = ap.bbox(usb)
ux, uz = (ub.XMin + ub.XMax) / 2, PT + 5.9
pocket = yprism(ux - 6.5, ux + 6.5, uz - 5.0, uz + 5.0, ub.YMax + 1.3, D2 + 5, 3)
liner = cad.cut(yprism(ux - 8.5, ux + 8.5, max(uz - 7.0, SPLIT + 1.6), uz + 7.0, ub.YMax + 0.25,
                       D2 - WALL + 1.0, 3.5), pocket)
shell = cad.fuse_one(cad.cut(shell, pocket), liner)
shell = cad.socket_opening(shell, usb, margin=1.5)
tick("openings")

# ------------------------------------------------------------ the drive
# the pinion on the shaft (bore 3.3 round the 3.0 shaft), the hub gear on
# the axle; each phased so a tooth of one points into a space of the other
pinion = cad.spur_gear(M, Z_PIN, GEAR_T - 0.3, bore=3.3, backlash=BACKLASH)
pinion.translate(V(SX, SY, G0))
pinion = cad.mesh_phase(pinion, (SX, SY, G0), "+Z", (-SX, -SY, 0), tooth=True)
gear = cad.spur_gear(M, Z_GEAR, GEAR_T, backlash=BACKLASH)
gear = cad.hole(gear, at=(0, 0, 0), axis="+Z", d=2 * (AXLE_R + 0.1), through=True)
gear.translate(V(0, 0, G0))
gear = cad.mesh_phase(gear, (0, 0, G0), "+Z", (SX, SY, 0))
# four light windows between four spokes (cut after phasing: the spokes
# stay off the lights), three pegs up into the ball's flange
WIN_R = (12.0, FL_IN - 1.0)
wins = []
for a in (45, 135, 225, 315):
    pts = [V(WIN_R[1] * math.cos(math.radians(a + t)), WIN_R[1] * math.sin(math.radians(a + t)), G0 - 1)
           for t in range(-38, 39, 8)]
    pts += [V(WIN_R[0] * math.cos(math.radians(a + t)), WIN_R[0] * math.sin(math.radians(a + t)), G0 - 1)
            for t in range(28, -29, -14)]
    wins.append(Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, GEAR_T + 2)))
gear = cad.cut(gear, wins)
PEG_R = (FL_IN + M * (Z_GEAR - 2.5) / 2.0) / 2.0   # mid-way across the rim
PEGS = [(PEG_R * math.cos(math.radians(a)), PEG_R * math.sin(math.radians(a))) for a in (30, 150, 270)]
gear = cad.fuse_one(gear, *[cyl(1.2, (x, y, G1 - 0.5), 2.3) for x, y in PEGS])
axle = cad.soften(cyl(AXLE_R, (0, 0, BOSS_Z0 + 2.0), G1 + 1.0 - (BOSS_Z0 + 2.0)), 0.5)
tick("drive")

# ------------------------------------------------------------ the ball
# ONE sphere outline in two halves, both skins in each section. The band:
# an inner flange on the hub gear, the outer skin up to the seam, the
# inner skin back down (arcs split at latitudes: each band its own face)
def sph(r, deg):
    return (r * math.cos(math.radians(deg)), ZC + r * math.sin(math.radians(deg)))


lat_b = math.degrees(math.asin((ZB - ZC) / SHADE_R))          # the bottom rim's latitude
lat_f = math.degrees(math.asin((ZB + FL_T - ZC) / RI))       # the flange's top on the inner skin
lo_sec = [(FL_IN, ZB), sph(SHADE_R, lat_b),
          ("arc", sph(SHADE_R, (lat_b + lat_b / 2) / 2), sph(SHADE_R, lat_b / 2)),
          ("arc", sph(SHADE_R, lat_b / 4), sph(SHADE_R, 0)),
          sph(RI, 0),
          ("arc", sph(RI, lat_f / 4), sph(RI, lat_f / 2)),
          ("arc", sph(RI, (lat_f / 2 + lat_f) / 2), sph(RI, lat_f)),
          (FL_IN, ZB + FL_T)]
lower = cad.revolve_profile(lo_sec)
# the dome: the outer skin from the seam to Polaris (the pole hole), the
# inner skin back, in three latitude bands
POLE = 3.0
lat_p = math.degrees(math.acos(POLE / SHADE_R))
lat_pi = math.degrees(math.acos(POLE / RI))
BANDS = (0.0, 32.0, 60.0)
up_sec = [sph(SHADE_R, 0)]
for a0, a1 in zip(BANDS, BANDS[1:] + (lat_p,)):
    up_sec.append(("arc", sph(SHADE_R, (a0 + a1) / 2), sph(SHADE_R, a1)))
up_sec.append(sph(RI, lat_pi))
for a1, a0 in zip(BANDS[::-1], (lat_pi,) + BANDS[:0:-1]):
    up_sec.append(("arc", sph(RI, (a0 + a1) / 2), sph(RI, a1)))
top = cad.revolve_profile(up_sec)
# the spigot: a ring fused inside the dome's rim, down into the band 0.2 mm
# off its inner skin
R_LOW = math.sqrt(RI ** 2 - LIP ** 2) - 0.2
spigot = cad.revolve_profile([(R_LOW - 2.6, ZC - LIP), (R_LOW, ZC - LIP), (R_LOW, ZC), (RI + 0.5, ZC),
                              (RI + 0.5, ZC + 3.0), (R_LOW - 2.6, ZC + 3.0)])
top = cad.fuse_one(top, spigot)
# three pads on the band's inner skin under the spigot, three pins from
# the spigot down into them (0.15 mm clear in their bores)
PIN_A = (90.0, 210.0, 330.0)
pads, pins, pin_bores = [], [], []
for a in PIN_A:
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    rp = R_LOW - 1.3
    pad = box(R_LOW - 4.0, RI + 0.8, -3.5, 3.5, ZC - LIP - 7.0, ZC - LIP - 0.3)
    pad.rotate(V(0, 0, 0), V(0, 0, 1), a)
    pads.append(pad)
    pins.append(cyl(1.0, (rp * c, rp * s, ZC - LIP - 4.0), 4.5))
    pin_bores.append(cyl(1.15, (rp * c, rp * s, ZC - LIP - 4.5), 5.0))
lower = cad.cut(cad.fuse_one(lower, *pads), pin_bores)
top = cad.fuse_one(top, *pins)
# the flange's peg bores (0.15 mm round the hub gear's pegs)
lower = cad.cut(lower, [cyl(1.35, (x, y, ZB - 1.0), 3.0) for x, y in PEGS])
tick("ball")


# === STAGE B: details ===
def unit(az, el):
    a, e = math.radians(az), math.radians(el)
    return V(math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e))


O = V(0, 0, ZC)


def frame(u):
    rt = V(0, 0, 1).cross(u)
    if rt.Length < 1e-6:
        rt = V(1, 0, 0)
    rt.normalize()
    up = u.cross(rt)
    return rt, up


def prism(u, pts2d, r_from, depth):
    """A prism of the outline pts2d (mm, in u's tangent plane: x right, y up)
    from radius r_from inward `depth` along -u."""
    rt, up = frame(u)
    c = O + u * r_from
    f = Part.Face(Part.makePolygon([c + rt * x + up * y for x, y in pts2d] + [c + rt * pts2d[0][0] + up * pts2d[0][1]]))
    return f.extrude(u * -depth)


def star_pts(r, rot=0.0):
    return [((r if i % 2 == 0 else 0.5 * r) * math.cos(math.radians(90 + rot + 36 * i)),
             (r if i % 2 == 0 else 0.5 * r) * math.sin(math.radians(90 + rot + 36 * i))) for i in range(10)]


def ang(u, w):
    return math.degrees(math.acos(max(-1.0, min(1.0, u.dot(w)))))


def radial_hole(u, d):
    return Part.makeCylinder(d / 2, WALL + 3.0, O + u * (RI - 1.5), u)


S = SHADE_R / 58.0                     # the sky's star sizes follow the ball
# three gold constellations (azimuth, elevation, star radius), each one
# inlay: its stars joined by fine lines, standing 0.5 mm proud
CONST = {
    "Big_Dipper": [(-118, 40, 3.6), (-104, 45, 3.2), (-92, 46, 3.2), (-80, 44, 3.4),
                   (-74, 31, 3.4), (-90, 26, 3.6), (-80, 44, 3.4)],
    "Cassiopeia": [(30, 30, 3.4), (42, 40, 3.0), (54, 32, 3.6), (66, 42, 3.0), (78, 34, 3.4)],
    "Orion": [(-30, 36, 3.6), (-10, 38, 3.4), (-27, 21, 3.2), (-20, 19, 3.2), (-13, 17, 3.2),
              (-33, 4, 3.4), (-7, 6, 3.6)],
}
LINKS = {"Big_Dipper": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 3)],
         "Cassiopeia": [(0, 1), (1, 2), (2, 3), (3, 4)],
         "Orion": [(0, 2), (1, 4), (2, 3), (3, 4), (2, 5), (4, 6)]}
LINE_W = 1.1
layer = cad.cut(Part.makeSphere(SHADE_R + 0.5, O), Part.makeSphere(SHADE_R - 0.8, O))
inlays, star_holes, used = {}, [], []
for name, stars in CONST.items():
    pieces = []
    for i, (a, e, r) in enumerate(stars):
        u = unit(a, e)
        pieces.append(prism(u, star_pts(max(r * S, 3.2), 11 * i), SHADE_R + 1.5, 4.0))
        star_holes.append(radial_hole(u, 1.2 + 0.2 * (r > 3.5)))
        used.append((u, 6.0 * S))
    for i0, i1 in LINKS[name]:
        ua, ub = unit(*stars[i0][:2]), unit(*stars[i1][:2])
        nrm = ua.cross(ub)
        nrm.normalize()
        pts = [O + (ua * (1 - t) + ub * t).normalize() * (SHADE_R + 1.5) for t in (0, 0.25, 0.5, 0.75, 1)]
        pts += [O + (ua * (1 - t) + ub * t).normalize() * (SHADE_R - 2.5) for t in (1, 0.75, 0.5, 0.25, 0)]
        f = Part.Face(Part.makePolygon(pts + [pts[0]]))
        f.translate(nrm * (-LINE_W / 2))
        pieces.append(f.extrude(nrm * LINE_W))
        for t in (0.25, 0.5, 0.75):
            used.append(((ua * (1 - t) + ub * t).normalize(), 4.5 * S))
    inlays[name] = cad.fuse_one(*pieces).common(layer)
# the crescent moon window (a frosted insert through the wall), horns to the right
MOON = (-150.0, 22.0, 11.0 * S)
cres = []
for i in range(25):
    t = -1 + 2 * i / 24.0
    th = math.radians(180 + 135 * t)
    cres.append((MOON[2] * math.cos(th), MOON[2] * math.sin(th)))
for i in range(25):
    t = 1 - 2 * i / 24.0
    th = math.radians(180 + 128 * t)
    rr = MOON[2] - (1.4 + 0.42 * MOON[2] * (1 - t * t))
    cres.append((rr * math.cos(th) + 0.18 * MOON[2] * (1 - t * t), rr * math.sin(th)))
u_moon = unit(MOON[0], MOON[1])
used.append((u_moon, 1.3 * MOON[2] + 4.0))
top, moon = insert(top, prism(u_moon, cres, SHADE_R + 1.5, WALL + 3.5))
for name in inlays:
    top = cad.cut(top, inlays[name].common(layer))
tick("inlays + moon")
# the Pleiades: a cluster drilled straight up over each light (its rays
# leave through them), the brightest star on the light's centre
pleiades = []
for m in lights:
    lx, ly, _ = centre(m)
    for dx, dy, d in ((0, 0, 3.2), (-5.0, 3.5, 2.2), (4.5, 4.0, 2.0), (5.5, -3.0, 2.4),
                      (-4.0, -4.5, 1.8), (1.0, 6.5, 1.6), (-6.5, -0.5, 1.6)):
        x, y = lx + dx, ly + dy
        pleiades.append(cyl(d / 2, (x, y, ZC + math.sqrt(RI ** 2 - x * x - y * y) - 1.5), WALL + 6.0))
        used.append((V(x, y, math.sqrt(SHADE_R ** 2 - x * x - y * y)).normalize(), 3.0))
# the star field: a Fibonacci sphere, jittered, six sizes, kept off the
# inlays, the moon, the seam band and the pole
GOLDEN = math.pi * (3 - math.sqrt(5))
SIZES = (1.1, 1.3, 1.5, 1.8, 2.2, 2.8)
N = 300
seed = [12345]


def rnd():
    seed[0] = (seed[0] * 1103515245 + 12345) % 2147483648
    return seed[0] / 2147483648.0


field_lo, field_hi = [], []
lat_lo_min = lat_b + 9.0
for i in range(N):
    zz = 1 - 2 * (i + 0.5) / N
    el = math.degrees(math.asin(zz)) + (rnd() - 0.5) * 3.0
    az = math.degrees(i * GOLDEN) % 360 + (rnd() - 0.5) * 6.0
    if not (lat_lo_min < el < -9.0 or 7.0 < el < 84.0):
        continue
    u = unit(az, el)
    d = SIZES[int(rnd() * len(SIZES))] * (0.85 + 0.15 * S)
    if any(ang(u, w) < r / SHADE_R * 57.3 + d for w, r in used):
        continue
    if rnd() < 0.18:
        continue
    used.append((u, d + 1.5))
    (field_hi if el > 0 else field_lo).append(radial_hole(u, d))
print("STARS %d on the dome, %d on the band, %d in the inlays, %d in the Pleiades" % (
    len(field_hi), len(field_lo), len(star_holes), len(pleiades)))
top = cad.cut(top, field_hi + star_holes + pleiades)
lower = cad.cut(lower, field_lo)
for name in inlays:
    inlays[name] = cad.cut(inlays[name], star_holes)
print("LOOPS busiest face: dome %d, band %d" % (max(len(f.Wires) for f in top.Faces),
                                                max(len(f.Wires) for f in lower.Faces)))
tick("star field")
# the key: a crescent moon debossed on its dome; a raised ring round it
cap_front = cap.BoundBox.YMin
moon_k = [(0.5 * BUTTON_D / 28.0 * x, 0.5 * BUTTON_D / 28.0 * y) for x, y in cres]
ktool = Part.Face(Part.makePolygon([V(kx + x * 0.9 / S, cap_front - 1.0, kz + y * 0.9 / S) for x, y in moon_k]
                                   + [V(kx + moon_k[0][0] * 0.9 / S, cap_front - 1.0, kz + moon_k[0][1] * 0.9 / S)]))
ktool = ktool.extrude(V(0, 1.6, 0))
cap = cad.cut(cap, ktool, optional=True)
shell = cad.fuse_one(shell, cad.cut(ycyl(BUTTON_D / 2 + 3.2, kx, kz, FY_OUT - 0.6, FY_OUT + 0.5),
                                    ycyl(BUTTON_D / 2 + 1.6, kx, kz, FY_OUT - 1.0, FY_OUT + 1.0)))
# the dial cap: a straight knurl round its side, a pointer groove on top
dcap = cad.knurl(dcap, "+X", (W2 + 0.6, ny, nz), CAP_R, 1.0, KT - W2 - 2.4, n=40, depth=0.35)
dcap = cad.cut(dcap, box(KT - 0.6, KT + 1, ny - 0.5, ny + 0.5, nz + 1.5, nz + CAP_R - 1.5))
# lettering on the front and under the base
shell = cad.text(shell, "ATECH", (-32.0, FY_OUT, KEY_Z), (0, -1, 0), 7, depth=0.5, mode="deboss")
base = cad.text(base, "ATECH SP-1", (0, 20.0, Z0), (0, 0, -1), 6, depth=0.4, mode="deboss", up=(0, -1, 0))
# four gold bun feet, each pegged into a boss in the floor
feet, peg_bores = [], []
for x, y in FEET:
    f = cad.foot(18.0, FOOT_H, style="dome", at=(x, y, Z0))
    feet.append(cad.fuse_one(f, cyl(2.5, (x, y, Z0 - 0.5), 4.5)))
    peg_bores.append(cyl(2.65, (x, y, Z0 - 0.5), 5.0))
base = cad.cut(base, peg_bores)
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape, colour=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = cad.color(COLOURS[colour or name])
    return o


part("Base", base)
part("Shell", shell)
part("Drive_Gear", gear)
part("Pinion", pinion)
part("Axle", axle)
part("Shade_Lower", lower)
part("Shade_Top", top)
part("Collar", collar)
part("Key", cap)
part("Dial_Cap", dcap)
o = part("Dial_Ring", dring)
o.ViewObject.Transparency = cad.transparency("frosted")
part("Grille", grille)
for i, sh in enumerate(lenses):
    o = part("Lens_%d" % (i + 1), sh, "Lens")
    o.ViewObject.Transparency = cad.transparency("frosted")
o = part("Moon", moon)
o.ViewObject.Transparency = cad.transparency("frosted")
for name, sh in inlays.items():
    part(name, sh, "Inlay")
for i, sh in enumerate(feet):
    part("Foot_%d" % (i + 1), sh, "Foot")
for i, sh in enumerate(screws):
    part("Screw_%d" % (i + 1), sh, "Screw")
print("SIZE %s" % (cad.measure(Part.makeCompound([base, shell, lower, top] + feet))["size"],))
print("SIZE model build %.1f s" % (time.time() - T0))
