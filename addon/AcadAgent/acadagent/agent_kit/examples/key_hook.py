"""Example: "a key hook by the door that knows who's home" - an oak key board whose glowing name tags show who is in.

fork this file for a key hook / key rack / entryway organiser (a smart key
board, a who's-home board, a hallway key holder with a shelf); change PARAMETERS and the outlines.
ARCHETYPE: key hook

How it is built (R1030):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board LANDSCAPE_UP in a white slab (x 0..120, modules facing the hall,
    -Y; the wall behind, +Y). Three hooks sit 40 mm apart UNDER the board,
    each centred between a pair of bottom-row ports: one port carries the
    hook's light (SEATED on 2 / 4 / 6), glowing through a frosted name tag
    over the hook; the other carries the hook's distance sensor, CABLED
    straight down (1 / 3 / 5: face -Y, pins up, a flat ribbon, no twist)
    to just under the hook, where it looks out through an open slot in a
    black sensor strip at the keys hanging from the hook's saddle 40 mm
    out. The top row holds the screen (10, 11: weather, "everyone is
    home") behind a smoked lens and the PIR (13) behind an OPEN round
    window, both in one black display band; the PIR wakes the screen when
    someone walks by. USB-C is cabled straight out of the left end (7) to
    the slab's left flank (pocket + liner), the cable runs down a channel
    in the oak plate and leaves at the bottom. Ports 8, 9, 12 and 14 stay
    empty (8 and 12: reserved by the firmware). The slab: one rounded box,
    hollowed with a sharp core, split FRONT / BACK just behind the board
    (the back is fixed: board ledges and standoffs, holder ribs round each
    sensor); four M3 screws from the wall side, through the oak plate and
    the back, into insert bosses in the front. Each hook is a thick printed
    J with a top rib, held by two M3 screws driven from inside the front
    into its flange: the load goes front -> screws -> back -> plate -> wall.
    The oak plate stands proud all round, carries the tray on top and hangs
    on two keyhole slots.
  * STAGE B - details: the front / back reveal, the names on the tags,
    a welcome legend, the tray's rolled lip and drain slots, the cable
    channel, keyholes, wordmark.
RESTYLE (R425): TAG_W, HOOK_REACH, TRAY_H, CORNER and WALL drive every
outline and every cutter below; the front's inner face stays 2.6 mm in
front of the modules whatever the wall (YF), the screws follow the corners
(screw_at). The hardware frame (the board at x 0..120, BZ above the slab's
floor) is the board's own: never move it with a knob.
DETAILS (visible, 33): 1 white slab with soft corners; 2 rolled front edge;
3 front / back reveal; 4 oak wall plate, proud all round; 5 its rolled
front edge; 6 oak tray on top; 7 its front lip; 8 its rounded front
corners; 9 two drain slots in its floor; 10 the backsplash above it;
11-13 three terracotta J hooks with a saddle and a raised tip; 14-16 a top
rib on each; 17-19 three frosted name tags, raised, glowing; 20-22 the
names debossed in them; 23 black display band; 24 smoked screen lens;
25 the PIR's open round window; 26 its flared mouth; 27 black sensor strip
with three open slots; 28 "WELCOME HOME" legend; 29 USB-C pocket with liner
in the left flank; 30 the cable channel down the plate; 31 "ATECH" on the
plate's chin; 32-33 two key bunches on the lit hooks (a ring resting on
the saddle, a brass key, a leather fob - props, not printed).
Inside: two keyhole slots and four countersunk screws in the plate's back,
six M3 hook screws driven from inside the front, a rib onto the board's
spine, board ledges and standoffs, sensor holder ribs, USB-C holder
plates, insert bosses, the front / back lip.
Materials: warm white slab, light oak plate and tray, terracotta hooks,
frosted name tags (two lit warm: those two are home), matte black display
band and sensor strip, smoked screen lens, chrome screws; props: brass
keys, teal and tan leather fobs.
MEASURED (R1030, 2026-11-20): ./check CHECK PASS, run_seconds 9 s, wall 34 s; every RESTYLE end CHECK PASS.
"""
import math
import time
import Part
import atech_ports as ap
import atech_cad as cad
import FreeCAD as App
from FreeCAD import Vector, Placement, Rotation
V = Vector
T0 = time.time()

INTENT = {"board": "upright", "fitted_after": [
    "Front", "Display_Bezel", "Screen_Lens", "Sensor_Strip", "Name_Tag_1", "Name_Tag_2",
    "Name_Tag_3", "Hook_1", "Hook_2", "Hook_3", "Wall_Plate",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4", "Screw_5", "Screw_6", "Screw_7", "Screw_8",
    "Screw_9", "Screw_10", "Keys_1", "Keys_2", "Fob_1", "Fob_2"]}
REVIEW_CLOSEUPS = ["Hook_1", "Name_Tag_1", "Display_Bezel"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them; the sweep builds this file
# with each knob at its min and at its max, one at a time.
TAG_W = 30.0       # RESTYLE 25.5..34.5 width: each glowing name tag across (x)
HOOK_REACH = 38.0  # RESTYLE 32..44 length: how far each hook's arm stands out of the face
TRAY_H = 18.0      # RESTYLE 15.3..20.7 height: the tray's lip above its floor
CORNER = 32.0      # RESTYLE 27..37 radius: the slab's corners, seen from the front
WALL = 2.5         # RESTYLE 2.1..2.9 wall
# end RESTYLE
# Frame: x across (the viewer's right +), y from the hall (-) to the wall
# (+), z up; the plate's chin on z = 0. The board is centred: x 0..120.
CX = 60.0                        # the centre line (the middle hook)
WIDTH, DEPTH = 190.0, 30.0       # the slab across and from the front to the wall
X0, X1 = CX - WIDTH / 2, CX + WIDTH / 2
PB = 10.0                        # the slab's bottom (the plate's chin below it)
TZ = PB + 14.5                   # the distance sensors' centre line
BZ = TZ + 36.0                   # the board's bottom: the hooks between the sensors and the board
ZT = BZ + 68.0                   # the slab's top
YF = -12.1 - WALL                # the front: its inner face 2.6 mm in front of the modules
YB = YF + DEPTH                  # the back (on the wall plate)
EDGE = 5.0                       # the rolled front edge
HOOKS = (20.0, 60.0, 100.0)      # each hook between its light and its sensor column
TAG_H = 17.0
HOOK_W, FLANGE = 13.0, (22.0, 7.0, 24.0)   # the arm's width; the flange w, thickness, height
PLATE_T, PLATE_OUT = 8.0, 22.0   # the oak plate's thickness, how far it stands out round the slab
TRAY_D, FLOOR_T = 44.0, 3.0      # the tray's depth from the plate, its floor
SPLASH = 12.0                    # the plate above the tray's lip
NAMES = ("ELSA", "OLLE", "IDA")
SCREW = "M3"                     # the one screw size: housing, plate and hooks
COLOURS = {"Front": "#f3efe7", "Back": "#e6e0d5", "Wall_Plate": "#d9b98c", "Hook": "#c4643c",
           "Name_Tag_1": "#ffd9a0", "Name_Tag_2": "#ffd9a0", "Name_Tag_3": "frosted",
           "Display_Bezel": "matte_black", "Screen_Lens": "smoked", "Sensor_Strip": "matte_black",
           "Screw": "chrome",
           "Keys": "brass", "Fob_1": "#2f6f73", "Fob_2": "#8a5a3b"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
LANDSCAPE_UP = Rotation(Vector(0, 0, 1), 180).multiply(Rotation(Vector(0, 1, 0), -90))
board = ap.board_object(doc)
board.Placement = Placement(Vector(), LANDSCAPE_UP)
_b = ap.bbox(board)
board.Placement = Placement(Vector(-_b.XMin, 0, BZ - _b.ZMin), LANDSCAPE_UP)   # x 0..120, z BZ..BZ+60
BB = ap.bbox(board)
# each hook: its light SEATED in the bottom row, its sensor CABLED straight
# down under it (face -Y, pins up: the ribbon stays flat)
lights = [ap.seat(doc, "light", p) for p in (2, 4, 6)]
tofs = []
for p, x in ((1, 10.0), (3, 50.0), (5, 90.0)):
    t, _rb = ap.cable(doc, "distance_sensor", p, ap.module_placement(
        "distance_sensor", (x, -4.77, TZ), face="-Y", cable="+Z"))
    tofs.append(t)
scr = ap.seat(doc, "screen", (10, 11))           # top row, x 20..60
pir = ap.seat(doc, "pir", 13)                    # top row, x 80..100
XI0 = X0 + WALL
usb, _urb = ap.cable(doc, "usbc", 7, ap.module_placement(
    "usbc", (XI0 + 1.0 + 19.75 / 2, -5.1, BZ + 30.0), face="-Y", cable="+X"))   # mouth -X
tick("hardware")


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, -1, 0)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def centre(m):
    b = ap.bbox(m)
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


def yslab(w, h, r, cx, cz, y0, y1):
    """A rounded rectangle w x h (x, z), corner r, from y0 to y1."""
    return cad.rounded_box(w, abs(y1 - y0), h, r, at=(cx - w / 2, min(y0, y1), cz - h / 2), edges="y")


def xprism(y0, y1, z0, z1, x0, x1, r):
    w = cad.rounded_rect_wire(y1 - y0, z1 - z0, r, (x0, (y0 + y1) / 2, (z0 + z1) / 2), "X")
    return Part.Face(w).extrude(V(x1 - x0, 0, 0))


def insert(shell, cutter):
    """(shell with the opening, the piece that fills it exactly)."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1:
        piece, rest = shell.common(cutter, 0.01), shell.cut(cutter, 0.01)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, piece


# ------------------------------------------------------------ the slab
slab = cad.rounded_box(WIDTH, DEPTH, ZT - PB, CORNER, at=(X0, YF, PB), edges="y")
slab = cad.fillet_safe(slab, EDGE, edges=[e for e in slab.Edges if e.BoundBox.YMax < YF + 0.01])
slab = cad.fillet_safe(slab, 1.0, edges=[e for e in slab.Edges if e.BoundBox.YMin > YB - 0.01])
# the core keeps SHARP inner edges (a filleted core reads as clip channels)
core = cad.rounded_box(WIDTH - 2 * WALL, DEPTH - 2 * WALL, ZT - PB - 2 * WALL, CORNER - WALL,
                       at=(X0 + WALL, YF + WALL, PB + WALL), edges="y")
shell = cad.cut(slab, core)
tick("slab")
SPLIT_Y = BB.YMax - 0.3
front, back = cad.split(shell, "Y", at=SPLIT_Y, lip=1.2)
tick("split")

# ------------------------------------------------------------ the back holds the board
YI = YB - WALL + 0.5                       # into the back wall
ledges = [box(4, 116, 0.6, YI, BB.ZMin - 2.3, BB.ZMin - 0.3), box(4, 116, 0.6, YI, BB.ZMax + 0.3, BB.ZMax + 2.3)]
ledges += [box(x, x + 6, BB.YMax + 0.1, YI, BZ + z, BZ + z + 6) for x in (8, 57, 106) for z in (8, 46)]
# holder ribs either side of each cabled sensor (0.25 mm off), behind its
# face, below the lights' slide paths
for t in tofs:
    tb = ap.bbox(t)
    for xa, xb in ((tb.XMin - 1.8, tb.XMin - 0.25), (tb.XMax + 0.25, tb.XMax + 1.8)):
        ledges.append(box(xa, xb, tb.YMin + 0.6, YI, tb.ZMin + 2.0, tb.ZMax - 2.0))
back = cad.fuse_one(back, *ledges)
# the oak wall plate: the slab's outline, proud all round, rising behind the tray
PTOP = ZT + FLOOR_T + TRAY_H + SPLASH
plate = cad.rounded_box(WIDTH + 2 * PLATE_OUT, PLATE_T, PTOP, CORNER + PLATE_OUT,
                        at=(X0 - PLATE_OUT, YB, 0.0), edges="y")
plate = cad.fillet_safe(plate, 2.0, edges=[e for e in plate.Edges if e.BoundBox.YMax < YB + 0.01])


def screw_at(sx, sz):
    """A screw on the corner's diagonal, its sleeve 1.5 mm inside the
    rounded inner wall (it follows CORNER and WALL)."""
    cx = (X0 + CORNER) if sx < 0 else (X1 - CORNER)
    cz = (PB + CORNER) if sz < 0 else (ZT - CORNER)
    d = (CORNER - WALL - 5.0) / math.sqrt(2.0)
    return cx + sx * d, cz + sz * d


# four M3 screws from the wall side: through the plate and the back into
# insert bosses in the front, clear of every module
SCREWS = [screw_at(-1, -1), screw_at(1, -1), screw_at(-1, 1), screw_at(1, 1)]
INSERT_D = {"M2": 3.2, "M2.5": 3.6, "M3": 4.3}[SCREW]
screws = []
for x, z in SCREWS:
    back, front = cad.screw_through(back, front, (x, YB, z), size=SCREW, ribs=0)
    yb = YB - WALL - 0.1
    front = cad.fuse_one(front, cyl(INSERT_D / 2 + 1.2, (x, yb, z), 10.0))
    front = cad.cut(front, cyl(INSERT_D / 2, (x, yb + 0.5, z), 9.5))
    plate = cad.countersink(plate, (x, YB + PLATE_T, z), "-Y", 3.4, 6.2, 90.0)
    screws.append(cad.screw("csk_phillips", SCREW, round(PLATE_T + 10.0), at=(x, YB + PLATE_T, z), axis="-Y"))
# board retention: a rib from the front wall onto the spine (0.2 mm off)
front = cad.fuse_one(front, box(58, 62, YF + WALL - 0.5, BB.YMin - 0.2, BZ + 24, BZ + 36))
tick("back + screws")

# ------------------------------------------------------------ the tray (part of the plate)
# the tray's ends stay 4 mm inside the plate's rounded top corners at the lip
PR = CORNER + PLATE_OUT
_dz = max(0.0, ZT + FLOOR_T + TRAY_H - (PTOP - PR))
_in = PR - math.sqrt(max(PR ** 2 - _dz ** 2, 0.0)) + 4.0
TX0, TX1 = X0 - PLATE_OUT + _in, X1 + PLATE_OUT - _in
TY0 = YB - TRAY_D
# only its front corners rounded: the back ones run on into the plate
tray = cad.rounded_box(TX1 - TX0, TRAY_D + 12.0, FLOOR_T + TRAY_H, 10.0, at=(TX0, TY0, ZT), edges="z")
tray = tray.common(box(TX0 - 1, TX1 + 1, TY0 - 1, YB + 0.5 * PLATE_T, ZT - 1, ZT + FLOOR_T + TRAY_H + 1))
tray = cad.cut(tray, cad.rounded_box(TX1 - TX0 - 6.0, TRAY_D - 3.0, TRAY_H + 2.0, 7.0,
                                     at=(TX0 + 3.0, TY0 + 3.0, ZT + FLOOR_T), edges="z"))
LIP = ZT + FLOOR_T + TRAY_H                      # the lip's top: rolled
tray = cad.soften(tray, 1.2, edges=[e for e in tray.Edges if e.BoundBox.ZMin > LIP - 0.01
                                         and e.BoundBox.YMax < TY0 + 12.0])
plate = cad.fuse_one(plate, tray)

# ------------------------------------------------------------ the face
# the name tags: a frosted insert over each hook, raised 1 mm, a light pipe
# from its back to 0.4 mm off the part of the LED grid it covers
tags = []
for i, (hx, m) in enumerate(zip(HOOKS, lights)):
    mb = ap.bbox(m)
    tz = (mb.ZMin + mb.ZMax) / 2
    front, tag = insert(front, yslab(TAG_W, TAG_H, 4.0, hx, tz, YF - 1, YF + WALL + 1))
    tag = cad.fuse_one(tag, yslab(TAG_W, TAG_H, 4.0, hx, tz, YF - 1.0, YF + 0.5))
    px0, px1 = max(hx - TAG_W / 2 + 2.5, mb.XMin + 1.2), min(hx + TAG_W / 2 - 2.5, mb.XMax - 1.2)
    tag = cad.fuse_one(tag, box(px0, px1, mb.YMin - 0.4, YF + WALL - 0.5, tz - TAG_H / 2 + 2.5, tz + TAG_H / 2 - 2.5))
    tags.append(tag)
# the display band: one black insert over the top row, the smoked lens over
# the screen in it, an OPEN round window over the PIR's dome
sb, pb_ = ap.bbox(scr), ap.bbox(pir)
DZ = (sb.ZMin + sb.ZMax) / 2
DX0, DX1 = sb.XMin - 6.0, pb_.XMax + 6.0
front, band = insert(front, yslab(DX1 - DX0, 26.0, 8.0, (DX0 + DX1) / 2, DZ, YF - 1, YF + WALL + 1))
band = cad.fuse_one(band, yslab(DX1 - DX0, 26.0, 8.0, (DX0 + DX1) / 2, DZ, YF - 1.0, YF + 0.5))
sx = (sb.XMin + sb.XMax) / 2
band, lens = insert(band, yslab(31.0, 17.0, 2.5, sx, DZ, YF - 2, YF + WALL + 1))
px, _py, pz = centre(pir)
band = cad.cut(band, cyl(5.75, (px, YF + WALL + 1, pz), WALL + 4))
# the sensor strip: one black insert under the hooks, an OPEN slot in
# front of each distance sensor (no glass over a ToF)
SX0, SX1 = HOOKS[0] - 16.0, HOOKS[-1] + 16.0
front, strip = insert(front, yslab(SX1 - SX0, 18.0, 6.0, CX, TZ, YF - 1, YF + WALL + 1))
strip = cad.fuse_one(strip, yslab(SX1 - SX0, 18.0, 6.0, CX, TZ, YF - 0.8, YF + 0.5))
strip = cad.cut(strip, [yslab(14.0, 10.0, 2.0, centre(t)[0], TZ, YF - 2, YF + WALL + 2) for t in tofs])
# USB-C on the left flank: a pocket brings the wall to 0.25 mm off the
# socket mouth, then the measured opening; holder plates over and under it
ub = ap.bbox(usb)
uy, uz = -5.9, (ub.ZMin + ub.ZMax) / 2
pocket = xprism(uy - 4.5, uy + 4.5, uz - 6.5, uz + 6.5, X0 - 5, ub.XMin - 1.3, 3)
liner = cad.cut(xprism(YF + WALL - 0.4, uy + 6.5, uz - 8.0, uz + 8.0, ub.XMin - 0.25, XI0 - 0.5, 3.0), pocket)
usb_hold = [box(XI0 - 0.5, ub.XMax - 4.0, ub.YMin + 0.8, ub.YMax - 0.8, z0, z1)
            for z0, z1 in ((ub.ZMax + 0.3, ub.ZMax + 2.0), (ub.ZMin - 2.0, ub.ZMin - 0.3))]
front = cad.fuse_one(cad.cut(front, pocket), liner, *usb_hold)
front = cad.socket_opening(front, usb, margin=1.5)
tick("face")

# ------------------------------------------------------------ the hooks
# a thick printed J: a flange on the face, an arm sloping down to a saddle
# behind a raised tip (the key ring settles there, in the sensor's view),
# a rib on top; two M3 screws from inside the front into the flange
FZ0 = TZ + 12.0                         # the flange's bottom, clear above the sensor strip
AZ0 = FZ0 + 1.5                         # the arm's underside at the flange
YT = YF - FLANGE[1] - HOOK_REACH        # the tip's front
hooks, hook_screws = [], []
for hx in HOOKS:
    fl = cad.rounded_box(FLANGE[0], FLANGE[1], FLANGE[2], 5.0, at=(hx - FLANGE[0] / 2, YF - FLANGE[1], FZ0),
                         edges="y")
    side = [(YF - FLANGE[1] + 0.5, AZ0), (YT + 8.0, AZ0 - 2.0), (YT, AZ0 - 1.0), (YT, AZ0 + 17.0),
            (YT + 7.0, AZ0 + 17.0), (YT + 8.5, AZ0 + 8.0), (YF - FLANGE[1] + 0.5, AZ0 + 12.0)]
    arm = Part.Face(Part.makePolygon([V(hx - HOOK_W / 2, y, z) for y, z in side + side[:1]])).extrude(
        V(HOOK_W, 0, 0))
    rib = Part.Face(Part.makePolygon([V(hx - 2.0, y, z) for y, z in (
        (YF - FLANGE[1] + 0.5, AZ0 + 11.0), (YF - FLANGE[1] - HOOK_REACH * 0.45, AZ0 + 9.0),
        (YF - FLANGE[1] + 0.5, FZ0 + FLANGE[2] - 3.0), (YF - FLANGE[1] + 0.5, AZ0 + 11.0))])).extrude(V(4.0, 0, 0))
    arm = cad.soften(cad.fuse_one(arm, rib), 2.0)
    hook = cad.fuse_one(fl, arm)
    for z in (AZ0 + 6.0, FZ0 + FLANGE[2] - 6.0):
        front = cad.countersink(front, (hx, YF + WALL, z), "-Y", 3.4, 6.2, 90.0, through="wall")
        hook = cad.hole(hook, (hx, YF, z), "-Y", 2.5, depth=7.0)
        hook_screws.append(cad.screw("csk_phillips", SCREW, 8, at=(hx, YF + WALL, z), axis="-Y"))
    hooks.append(hook)
tick("stage A")


# === STAGE B: details ===
# (a fork may stop after STAGE A, run ./check, then add these one by one)
# the PIR window's mouth flared (a wider field of view)
band = cad.cut(band, Part.makeCone(7.0, 5.75, 1.0, V(px, YF - 1.0, pz), V(0, 1, 0)))
# the front / back reveal and the legend between the tags and the band
front = cad.groove_ring(front, "Y", SPLIT_Y - 2.0, w=0.8, depth=0.6)
front = cad.text(front, "WELCOME HOME", (CX, YF, BZ + 30.0), (0, -1, 0), 4.0, depth=0.4, mode="deboss")
# the names debossed in the tags
for i, nm in enumerate(NAMES):
    tb = tags[i].BoundBox
    tags[i] = cad.text(tags[i], " ".join(nm), (HOOKS[i], YF - 1.0, (tb.ZMin + tb.ZMax) / 2), (0, -1, 0), 5.0,
                       depth=0.5, mode="deboss")
# the tray: two drain slots in its floor; the cable channel down the plate's
# left wing, from the USB-C socket to the plate's bottom edge
plate = cad.cut(plate, [box(x - 20.0, x + 20.0, TY0 + 12.0, TY0 + 15.0, ZT - 1, ZT + FLOOR_T + 1)
                        for x in (CX - 0.25 * WIDTH, CX + 0.25 * WIDTH)])
plate = cad.cut(plate, box(X0 - 7.0, X0 - 1.5, YB - 1.0, YB + 3.0, -1.0, uz))
plate = cad.text(plate, "ATECH", (CX, YB, PB / 2), (0, -1, 0), 4.0, depth=0.4, mode="deboss")
# two keyholes in the plate's back (blind: the wall screw's head goes in
# the round hole, the plate drops onto it; the head runs in a pocket)
KZ = PTOP - 22.0
for kxh in (CX - 0.3 * WIDTH, CX + 0.3 * WIDTH):
    plate = cad.cut(plate, [cyl(4.2, (kxh, YB + PLATE_T + 1, KZ), 5.5),
                            box(kxh - 2.2, kxh + 2.2, YB + PLATE_T + 1, YB + PLATE_T - 2.5, KZ, KZ + 10),
                            box(kxh - 4.2, kxh + 4.2, YB + PLATE_T - 2.5, YB + PLATE_T - 4.5, KZ, KZ + 10)])
# the keys of the two who are home (the lit tags): a split ring resting on
# each hook's saddle, a brass key and a leather fob on it - the key ring
# hangs in the sensor's view, 33 mm out from the face
RING_R, RING_T = 11.0, 1.1


def settle(shape, support, step):
    """Move `shape` along `step` until it rests on `support` (under 0.008
    mm apart, never into it): each move is 0.9 x the measured gap."""
    moved = 0.0
    for _ in range(40):
        d = shape.distToShape(support)[0]
        if d < 0.008:
            break
        shape.translate(V(*step) * (0.9 * d))
        moved += 0.9 * d
    return shape, moved


def plate_in(outline_face, n, u, at, t):
    """A flat part from a face drawn in (u, w) = (x, z) local coords: turned
    so x runs along `u`, z stays up, thickness t along `n`, origin at `at`."""
    s = outline_face.extrude(V(0, t, 0))
    s.translate(V(0, -t / 2, 0))
    m = App.Matrix(u[0], n[0], 0, at[0], u[1], n[1], 0, at[1], 0, 0, 1, at[2], 0, 0, 0, 1)
    s.transformShape(m)
    return s


def key_face():
    bow = Part.Face(Part.Wire(Part.makeCircle(6.5, V(0, 0, -2.5), V(0, 1, 0))))
    blade = Part.Face(Part.makePolygon([V(-2.8, 0, -7.0), V(2.8, 0, -7.0), V(2.8, 0, -13.0), V(1.6, 0, -14.0),
                                        V(2.8, 0, -15.0), V(2.8, 0, -17.0), V(1.4, 0, -18.2), V(2.8, 0, -19.4),
                                        V(2.8, 0, -21.0), V(0.6, 0, -23.5), V(-2.8, 0, -23.5), V(-2.8, 0, -7.0)]))
    f = bow.fuse(blade).removeSplitter()
    return f.cut(Part.Face(Part.Wire(Part.makeCircle(2.4, V(0, 0, 0), V(0, 1, 0))))).Faces[0]


def fob_face():
    w = cad.rounded_rect_wire(12.0, 20.0, 5.0, (0, 0, -6.0), "Y")
    f = Part.Face(w)
    return f.cut(Part.Face(Part.Wire(Part.makeCircle(2.4, V(0, 0, 0), V(0, 1, 0))))).Faces[0]


KEY_F, FOB_F = key_face(), fob_face()
keys, fobs = [], []
for hx, hook in zip(HOOKS[:2], hooks[:2]):
    yr = YT + 12.0
    zt = hook.common(box(hx - 0.5, hx + 0.5, yr - 1.2, yr + 1.2, AZ0 - 5, AZ0 + 25)).BoundBox.ZMax
    zc = zt - (RING_R - RING_T) + 2.0                  # the ring's centre, 2 mm high
    ring, dz = settle(Part.makeTorus(RING_R, RING_T, V(hx, yr, zc), V(0, 1, 0)), hook, (0, 0, -1))
    zc -= dz
    for dx, ang, face, store in ((-2.0, 15.0, KEY_F, keys), (4.0, 15.0, FOB_F, fobs)):
        a = math.radians(ang)
        n, u = (-math.cos(a), -math.sin(a)), (-math.sin(a), math.cos(a))
        tz = zc - math.sqrt(RING_R ** 2 - dx ** 2)     # the ring's tube under this point
        if store is keys:                              # the key's eye bites 0.4 mm into the ring: one body
            ring = cad.fuse_one(ring, plate_in(face, n, u, (hx + dx, yr, tz - 1.7), 2.0))
        else:                                          # the fob drops until it hangs on it
            fob = plate_in(face, n, u, (hx + dx, yr, tz), 3.0)     # the ring through its eye
            store.append(settle(fob, ring, (0, 0, -1))[0])
    keys.append(ring)
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape, colour=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = cad.color(COLOURS[colour or name])
    return o


for nm, sh in (("Back", back), ("Front", front), ("Wall_Plate", plate), ("Display_Bezel", band),
               ("Sensor_Strip", strip)):
    part(nm, sh)
for i, sh in enumerate(hooks):
    part("Hook_%d" % (i + 1), sh, "Hook")
for i, sh in enumerate(tags):
    o = part("Name_Tag_%d" % (i + 1), sh)
    o.ViewObject.Transparency = cad.transparency("frosted")
o = part("Screen_Lens", lens)
o.ViewObject.Transparency = cad.transparency("smoked")
for i, sh in enumerate(keys):
    part("Keys_%d" % (i + 1), sh, "Keys")
for i, sh in enumerate(fobs):
    part("Fob_%d" % (i + 1), sh)
for i, sh in enumerate(screws + hook_screws):
    part("Screw_%d" % (i + 1), sh, "Screw")
print("TOTAL %.1f s" % (time.time() - T0))
