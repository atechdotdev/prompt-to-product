"""Example: "a stand for my record sleeve that shows what's playing" - a walnut now-playing ledge that hears the song and shows it.

fork this file for a record stand / now playing stand (a vinyl sleeve
ledge, an album display shelf, a picture-ledge with a display); change PARAMETERS and the outlines.
ARCHETYPE: record stand

How it is built (R1030):
  * STAGE A - hardware, shell, every working-face opening, fasteners: a
    long walnut ledge, square-ended like real record ledges: ONE side
    profile (a low deck, a steep ramp up to a back rail) extruded across
    the width, hollowed with its own inset core, split LOW into the black
    plinth (Base, fixed: it carries the board on pads between fences) and
    the walnut Body (fitted after). The sleeve stands in a slot through the
    rail, leaning back LEAN deg, walled off from the cavity by a solid
    slot block. The board lies FLAT under the deck, turned so its long
    side runs across (ports 9-14 at the front): five lights (14, 13, 11,
    10, 9) under one frosted level-meter strip, the screen (5, 4) behind a smoked
    window, the microphone (2, 1) under a little turntable platter whose
    rings of pin holes are its grille (with a seal tube to 0.3 mm off the
    mic), the SKIP key on 6, USB-C on 3 with its mouth to the BACK through
    a pocket + liner under the slot block (ports 8 and 12 stay empty). All
    of it sits in a brushed brass panel inlaid in the deck (a flange under
    the deck holds it, a rib onto the board's spine holds the board down).
    A steel bar in the plinth's floor keeps the centre of mass over the
    feet with a sleeve in the slot (STABILITY line). Six M2.5 screws from
    below into heat-set inserts.
  * STAGE B - details: the tonearm (parked beside the platter, off the
    mic's holes), the strip as a green / amber / red level meter in 18
    segments, the skip glyph, lettering, the brass trim line, the plinth
    reveal, felt strips gripping the sleeve in the slot, the record sleeve itself (an album with a vinyl disc, a label and stripes
    inlaid in its art), rubber feet.
RESTYLE (R425): WIDTH, HEIGHT, SLOT_D, EDGE and WALL drive every outline
and every cutter below. The board rides at HEIGHT - its stack (the deck
0.8 mm over the mic), the USB-C pocket follows the board, the slot's bottom
sits a wall over the pocket and the rail rises SLOT_D over that; the
hardware frame in x / y (the board centred) is the board's own.
DETAILS (visible, 30): 1 walnut ledge with square ends; 2 rolled deck
front edge; 3 coved ramp up to the back rail; 4 rolled rail edges; 5 the
sleeve slot through the rail, leaning back, its mouth eased; 6 black
plinth; 7 plinth reveal groove; 8 brass trim line inlaid along the front;
9 brushed brass control panel inlaid in the deck; 10 frosted level-meter
strip over five lights in green, amber and red; 11 its 18 segments; 12 smoked screen window; 13 its
black bezel, recessed 1 mm; 14 black turntable platter (the mic grille);
15 its rings of pin holes; 16 chrome tonearm on a pegged pivot; 17 its
headshell parked on an arm rest; 18 its counterweight; 19 black SKIP key;
20 its skip glyph; 21 raised brass ring round the key; 22 "NOW PLAYING"
on the deck; 23 "ATECH" on the deck; 24 USB-C socket in the back;
25 "ATECH NP-1" under the plinth; 26-29 four rubber feet; 30 six
countersunk screws from below. The sleeve: 31 orange album sleeve;
32 black vinyl disc inlaid in its art; 33 groove rings; 34 mustard label
with its hole; 35-36 teal and cream stripes; 37 the album title; 38-39 two felt strips in the slot walls
(0.8 mm proud: they grip the sleeve front and back).
Inside: board pads, end and side fences, the panel's flange and spine rib,
light pipes, the mic seal tube, the slot block, the USB-C liner, insert
sleeves, the steel weight bar between two stops, a plunger on the key.
Materials: walnut body, black plinth, brushed brass panel and trim, smoked
window, black bezel, platter and key, frosted green / amber / red strip, black felt, chrome tonearm and
screws, satin steel weight, rubber feet; the sleeve in print colours.
Hardware: one screw type, M2.5 countersunk Phillips (ISO 10642) x 8, six
of them, into M2.5 heat-set inserts; a steel flat bar 30 x 6 mm cut to
length (WEIGHT line); four 10 mm rubber feet. USB-C cable with an
overmould up to 12 x 9 mm (the pocket is 12 x 9, 24 mm deep).
MEASURED (R1030, 2026-11-20): ./check CHECK PASS, run_seconds 12 s, wall 31 s; every RESTYLE end CHECK PASS.
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
    "Body", "Panel", "Light_Strip_Green", "Light_Strip_Amber", "Light_Strip_Red", "Screen_Bezel", "Screen_Window", "Platter", "Tonearm", "Skip_Key",
    "Trim", "Felt_Clip_Front", "Felt_Clip_Back", "Record_Sleeve", "Vinyl", "Label", "Stripe_Teal", "Stripe_Cream",
    "Foot_1", "Foot_2", "Foot_3", "Foot_4",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4", "Screw_5", "Screw_6"],
    "covers": {"Skip_Key": "button_p6"}}
REVIEW_CLOSEUPS = ["Panel", "Tonearm", "Body"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them and the measured hardware.
WIDTH = 320.0      # RESTYLE 272..368 width: the ledge across (x); the sleeve is 315
HEIGHT = 28.0      # RESTYLE 23.8..32.2 height: the deck over the desk (z)
SLOT_D = 16.0      # RESTYLE 13.6..18.4 height: how deep the sleeve stands in the slot
EDGE = 3.5         # RESTYLE 2.9..4.1 radius: the deck's rolled front edge
WALL = 2.5         # RESTYLE 2.1..2.9 wall
# end RESTYLE
# Frame: x across, y front (-) to back (+), z up; the rubber feet on z = 0.
Z_BOT = 1.5                       # the plinth's underside (the rubber feet stand 1.5 proud)
FRONT = 7.0                       # the deck in front of the light row (y)
STACK = 2.5 + 10.84               # board underside -> the microphone's top (the tallest module)
BZ = HEIGHT - WALL - 0.8 - STACK  # the board's underside: the deck 0.8 mm over the mic
SPLIT = BZ - 2.0                  # plinth / body seam, under every module's slide path
RAMP = 4.5                        # the ramp from the deck up to the rail (y)
RF, SLOT_W, BACK = 3.0, 6.0, 7.0  # the slot's front wall, the slot (a 3-5 mm sleeve), the rail behind it
LEAN = 4.0                        # the sleeve leans back (deg)
RAIL_R = 2.0                      # the rail's rolled top edges
COVE = 2.5                        # the cove where the deck meets the ramp
SLEEVE = (315.0, 4.0)             # a 12-inch sleeve with its record: side, thickness
SLEEVE_G = 230.0                  # its mass (g): a 180 g LP in a card sleeve
STRIP_W = 9.0                     # the frosted light strip (y)
WIN = (28.0, 16.0)                # the screen window (the active area 25.6 x 13.5)
BEZEL, RECESS = 2.0, 1.0
PLATTER_R, GRILLE_D = 10.5, 17.0  # the platter over the mic; its pin-hole field (>= 3 % open)
KEY_D = 12.0
PIVOT = (60.0, 26.0)              # the tonearm's pivot on the panel
SCREW = "M2.5"
INSERT_D = 3.6                    # M2.5 heat-set insert pocket (1.4 d + 0.1)
COLOURS = {"Base": "matte_black", "Body": "#6b4226", "Panel": "brass", "Trim": "brass",
           "Light_Strip_Green": "#62d67e", "Light_Strip_Amber": "#ffb547", "Light_Strip_Red": "#ff5a4e", "Screen_Bezel": "matte_black", "Screen_Window": "smoked",
           "Platter": "#17171a", "Tonearm": "chrome", "Skip_Key": "#17171a", "Weight": "satin_grey",
           "Record_Sleeve": "#de5a2c", "Vinyl": "#141418", "Label": "#f2c94c", "Stripe_Teal": "#1f6c72",
           "Stripe_Cream": "#f1e6cc", "Felt": "#2a2a2e", "Foot": "rubber", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
FLAT = Rotation(Vector(1, 0, 0), 90)
ROT = Rotation(Vector(0, 0, 1), -90).multiply(FLAT)    # long side across, ports 9-14 at the front
board = ap.board_object(doc)
board.Placement = Placement(Vector(), ROT)
_b = ap.bbox(board)
board.Placement = Placement(Vector(-60.0 - _b.XMin, 30.0 - _b.YMax, BZ - _b.ZMin), ROT)  # x -60..60, y -30..30
BB = ap.bbox(board)
PT = BB.ZMin + 2.5                                     # the PCB top: every module's seat
lights = [ap.seat(doc, "light", p) for p in (14, 13, 11, 10, 9)]   # the front row, left to right
key = ap.seat(doc, "button", 6)                        # back row, left: SKIP / LIKE
scr = ap.seat(doc, "screen", (5, 4))                   # back row, left of centre
usb = ap.seat(doc, "usbc", 3)                          # back row, mouth +Y (to the back)
mic = ap.seat(doc, "microphone", (2, 1))               # back row, right: under the platter
tick("hardware")


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def annulus(r0, r1, c, z0, z1):
    return cad.cut(cyl(r1, (c[0], c[1], z0), z1 - z0), cyl(r0, (c[0], c[1], z0 - 1), z1 - z0 + 2))


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


def zbox(w, d, r, cx, cy, z0, z1):
    return cad.rounded_box(w, d, z1 - z0, r, at=(cx - w / 2, cy - d / 2, z0))


def yprism(x0, x1, z0, z1, y0, y1, r):
    w = cad.rounded_rect_wire(x1 - x0, z1 - z0, r, ((x0 + x1) / 2, y0, (z0 + z1) / 2), "Y")
    return Part.Face(w).extrude(V(0, y1 - y0, 0))


def lean(s):
    """The slot's frame (x, u across the slot, w up it) -> world: leaning
    back LEAN about the slot's front-bottom edge."""
    s = s.copy()
    s.rotate(V(0, 0, 0), V(1, 0, 0), -LEAN)
    s.translate(V(0, YS0, SLOT_BOT))
    return s


# ------------------------------------------------------------ the plan from the hardware
X1 = WIDTH / 2
LB = [ap.bbox(m) for m in lights]
SB, KB, UB, MB = ap.bbox(scr), ap.bbox(key), ap.bbox(usb), ap.bbox(mic)
Y0 = min(b.YMin for b in LB) - FRONT                  # the front face
TOP_IN = HEIGHT - WALL                                # the deck's inner face
PX0, PX1 = BB.XMin - 6.0, BB.XMax + 6.0               # the brass panel across
PY0 = Y0 + max(EDGE + 0.6, WALL + 1.6)                # its front edge: behind the roll, its flange inside the wall
sx, sy, _ = centre(scr)
mx, my, _ = centre(mic)
PY1 = max(sy + WIN[1] / 2 + BEZEL, my + PLATTER_R) + 1.6   # its back edge
DECK_Y1 = PY1 + 1.5                                   # the deck's back edge, where the ramp starts
YR0 = DECK_Y1 + RAMP                                  # the rail's front face
YS0 = YR0 + RF                                        # the slot's front face (at its bottom)
YS1 = YS0 + SLOT_W
Y1 = YS1 + BACK                                       # the back face
UX, UZ = (UB.XMin + UB.XMax) / 2, PT + 5.9            # the USB-C socket's centre
POCKET = (12.0, 9.0)                                  # the plug's pocket, w x h
SLOT_BOT = UZ + POCKET[1] / 2 + WALL                  # the slot's bottom: a wall over the plug pocket
RAIL_Z = SLOT_BOT + SLOT_D                            # the rail's top
print("LEDGE %.0f x %.1f, deck %.1f, rail %.1f, slot bottom %.1f (%.1f deep)" % (
    WIDTH, Y1 - Y0, HEIGHT, RAIL_Z, SLOT_BOT, SLOT_D))


# ------------------------------------------------------------ the ledge
def profile(t):
    """The side profile (y, z), inset t, extruded across x (inset t)."""
    pts = [(Y0, Z_BOT), (Y0, HEIGHT), (DECK_Y1, HEIGHT), (YR0, RAIL_Z), (Y1, RAIL_Z), (Y1, Z_BOT)]
    face = Part.Face(Part.makePolygon([V(-X1 - 1, y, z) for y, z in pts + pts[:1]]))
    if t > 0:
        face = face.makeOffset2D(-t, join=2)
        face = face.Faces[0] if face.Faces else face
    s = face.extrude(V(2 * X1 + 2, 0, 0))
    return s.common(box(-X1 + t, X1 - t, Y0 - 1, Y1 + 1, Z_BOT - 1, RAIL_Z + 1))


def xedges(shape, y, z, tol=0.05):
    return [e for e in shape.Edges if e.BoundBox.XLength > X1 and abs(e.BoundBox.YMin - y) < tol
            and abs(e.BoundBox.YMax - y) < tol and abs(e.BoundBox.ZMin - z) < tol and abs(e.BoundBox.ZMax - z) < tol]


outer = profile(0.0)
outer = cad.fillet_safe(outer, EDGE, edges=xedges(outer, Y0, HEIGHT))
outer = cad.fillet_safe(outer, COVE, edges=xedges(outer, DECK_Y1, HEIGHT))
outer = cad.fillet_safe(outer, RAIL_R, edges=xedges(outer, YR0, RAIL_Z) + xedges(outer, Y1, RAIL_Z))
outer = cad.fillet_safe(outer, 1.0, edges=xedges(outer, Y0, Z_BOT) + xedges(outer, Y1, Z_BOT))
# the slot block: solid round the slot (it walls the slot off from the
# cavity), from a wall under the slot up through the rail, its front kept
# behind the panel
slot = lean(box(-X1 - 5, X1 + 5, 0.0, SLOT_W, 0.0, RAIL_Z - SLOT_BOT + 20.0))
block = lean(box(-X1 - 5, X1 + 5, (PY1 + 0.6) - YS0, SLOT_W + WALL, -WALL, RAIL_Z - SLOT_BOT + 20.0))
core = cad.cut(profile(WALL), block)
shell = cad.cut(outer, core)
tick("ledge")
base, body = cad.split(shell, "Z", at=SPLIT, lip=1.2)
tick("split")

# ------------------------------------------------------------ the plinth holds the board
# pads 0.1 mm under the board, fences off its ends and long sides - all
# under the modules' seat plane (PT), so every slide path stays clear; the
# steel bar lies on the floor between the pad rows, two stops at its ends
FLOOR = Z_BOT + WALL
WT = min(6.0, BZ - 0.6 - FLOOR)                       # the steel bar's thickness (under the board)
WX = X1 - WALL - 12.0                                 # its half length
pads = [box(x - 4, x + 4, y - 4, y + 4, FLOOR - 0.5, BB.ZMin - 0.1) for x in (-48, 48) for y in (-20, 20)]
fences = [box(sx_ * 60.3, sx_ * 61.8, y0, y0 + 8, FLOOR - 0.5, PT - 1.5) for sx_ in (-1, 1) for y0 in (-25, 17)]
fences += [box(x - 6, x + 6, sy_ * 30.3, sy_ * 31.8, FLOOR - 0.5, PT - 1.5) for x in (-30, 30) for sy_ in (-1, 1)]
stops = [box(s_ * (WX + 0.2), s_ * (WX + 1.8), -10, 10, FLOOR - 0.5, FLOOR + min(3.0, WT)) for s_ in (-1, 1)]
# two pegs on the floor through holes in the bar locate it (the board's
# pads and the body clamp it down)
PEGS = [(-(WX - 20.0), 0.0), (WX - 20.0, 0.0)]
base = cad.fuse_one(base, *pads, *fences, *stops, *[cyl(2.0, (x, y, FLOOR - 0.5), WT) for x, y in PEGS])
weight = cad.cut(box(-WX, WX, -15.0, 15.0, FLOOR, FLOOR + WT), [cyl(2.2, (x, y, FLOOR - 1), WT + 2) for x, y in PEGS])
# six M2.5 screws up through the plinth into insert bosses in the body:
# four along the front (clear of the board and the panel's flange), two at
# the back under the slot block
SCREWS = [(x, Y0 + WALL + 4.0) for x in (-(X1 - 12.0), -85.0, 85.0, X1 - 12.0)]
SCREWS += [(x, YS0 + SLOT_W / 2) for x in (-(X1 - 12.0), X1 - 12.0)]
screws = []
for x, y in SCREWS:
    base, body = cad.screw_through(base, body, (x, y, Z_BOT), size=SCREW, ribs=0)
    zf = FLOOR + 0.1
    body = cad.fuse_one(body, cyl(INSERT_D / 2 + 1.2, (x, y, zf), 10.0))
    body = cad.cut(body, cyl(INSERT_D / 2, (x, y, zf - 0.5), 9.5))
    screws.append(cad.screw("csk_phillips", SCREW, 8, at=(x, y, Z_BOT), axis="+Z"))
tick("plinth + screws")

# ------------------------------------------------------------ the brass panel and its openings
# the panel: an insert in the deck, a flange under the deck at its front
# and ends (it drops in from below), a rib onto the board's spine (0.2 mm off)
body, panel = insert(body, zbox(PX1 - PX0, PY1 - PY0, 4.0, (PX0 + PX1) / 2, (PY0 + PY1) / 2, TOP_IN - 1, HEIGHT + 1))
FL = 1.2
flange = cad.cut(box(PX0 - FL, PX1 + FL, PY0 - FL, PY1 - 6.0, TOP_IN - 1.0, TOP_IN),
                 box(PX0 + 1.0, PX1 - 1.0, PY0 + 1.0, PY1, TOP_IN - 2.0, TOP_IN + 1.0))
panel = cad.fuse_one(panel, flange, box(8.0, 12.0, -3.0, 3.0, BB.ZMax + 0.2, TOP_IN + 0.5))
# the light strip: a frosted bar through the panel over the five lights,
# a pipe under it to 0.5 mm off each light's LEDs
LY = (LB[0].YMin + LB[0].YMax) / 2
SX0, SX1 = LB[0].XMin + 1.5, LB[-1].XMax - 1.5
panel, strip = insert(panel, zbox(SX1 - SX0, STRIP_W, STRIP_W / 2 - 0.01, (SX0 + SX1) / 2, LY, TOP_IN - 1, HEIGHT + 1))
_clip = zbox(SX1 - SX0 - 0.6, STRIP_W - 0.6, (STRIP_W - 0.6) / 2 - 0.01, (SX0 + SX1) / 2, LY, TOP_IN - 20, TOP_IN + 1)
strip = cad.fuse_one(strip, *[zbox(17.0, STRIP_W - 1.0, 2.0, (b.XMin + b.XMax) / 2, LY, b.ZMax + 0.5, TOP_IN + 0.5)
                              .common(_clip) for b in LB])
# the screen: a black bezel set RECESS down in its opening, a smoked window in it
panel, bezel = insert(panel, zbox(WIN[0] + 2 * BEZEL, WIN[1] + 2 * BEZEL, 3.0 + BEZEL, sx, sy, TOP_IN - 1,
                                  HEIGHT + 1))
bezel = bezel.cut(box(PX0, PX1, PY0, PY1, HEIGHT - RECESS, HEIGHT + 2))
bezel, window = insert(bezel, zbox(WIN[0], WIN[1], 3.0, sx, sy, TOP_IN - 2, HEIGHT + 2))
# the microphone: a black platter (an insert in the panel) standing 1 mm
# proud, rings of pin holes over the mic, a seal tube to 0.3 mm off it
panel, platter = insert(panel, cyl(PLATTER_R, (mx, my, TOP_IN - 1), WALL + 2))
platter = cad.fuse_one(platter, cyl(PLATTER_R, (mx, my, HEIGHT - 0.5), 1.5),
                       annulus(GRILLE_D / 2 + 0.3, GRILLE_D / 2 + 1.8, (mx, my), MB.ZMax + 0.3, TOP_IN + 0.5))
platter = cad.speaker_grille(platter, (mx, my, HEIGHT + 1.0), (0, 0, 1), GRILLE_D, ring_pitch=2.8, hole=1.8)
# the SKIP key: a black cap through the panel, flange 0.1 mm under it, a
# plunger to 0.16 mm over the button's own cap
kx, ky, _ = centre(key)
base_z = TOP_IN - 0.9
cap = cad.button_cap(KEY_D, (HEIGHT + 1.8) - base_z, dome=0.8, flange=1.5, at=(kx, ky, base_z), axis="+Z")
panel = cad.opening_for(panel, cap, clearance=0.25, chamfer=0.4, axis="+Z")
cap = cad.fuse_one(cap, cyl(3.0, (kx, ky, KB.ZMax + 0.16), base_z - (KB.ZMax + 0.16) + 0.5))
# USB-C to the back: a pocket from the back face to 1.3 mm off the mouth
# under the slot block, a liner round it (its back wall 0.25 mm off the
# mouth, its top under the panel)
pocket = yprism(UX - POCKET[0] / 2, UX + POCKET[0] / 2, UZ - POCKET[1] / 2, UZ + POCKET[1] / 2, UB.YMax + 1.3,
                Y1 + 5, 3.0)
liner = yprism(UX - POCKET[0] / 2 - 2.0, UX + POCKET[0] / 2 + 2.0, UZ - POCKET[1] / 2 - 2.0, SLOT_BOT,
               UB.YMax + 0.25, Y1 - 1.0, 2.0)
liner = cad.cut(liner, [pocket, box(PX0 - FL - 0.2, PX1 + FL + 0.2, PY0 - FL - 0.2, PY1 + 0.2, TOP_IN, RAIL_Z)])
body = cad.fuse_one(cad.cut(body, pocket), liner)
body = cad.socket_opening(body, usb, margin=1.5)
# the slot through the rail, its mouth eased; a felt strip inlaid in each
# of its walls, 0.8 mm proud (4.4 mm between them: a 5 mm gatefold presses
# the felt), so the sleeve stands gripped front and back
FELT = (0.5, 0.8)                                     # inlaid, proud
FW0, FW1 = 1.5, SLOT_D - 3.5                          # the felt's band up the slot
felts = [lean(box(-X1 + 1.0, X1 - 1.0, -FELT[0], FELT[1], FW0, FW1)),
         lean(box(-X1 + 1.0, X1 - 1.0, SLOT_W - FELT[1], SLOT_W + FELT[0], FW0, FW1))]
cut_ = cad.cut(body, [slot] + [lean(box(-X1 + 1.0, X1 - 1.0, -FELT[0], 0.5, FW0, FW1)),
                               lean(box(-X1 + 1.0, X1 - 1.0, SLOT_W - 0.5, SLOT_W + FELT[0], FW0, FW1))])
body = cad.soften(cut_, 0.8, [e for e in cad.new_edges(cut_, body) if e.BoundBox.ZMin > RAIL_Z - 1.5
                               and e.BoundBox.XLength > X1])
tick("stage A")


# === STAGE B: details ===
# (a fork may stop after STAGE A, run ./check, then add these one by one)
# the tonearm, parked beside the platter (it keeps off the mic's holes):
# a chrome pivot pegged into a blind hole in the panel, the arm 2.2 mm
# over the panel, its headshell on an arm rest, a counterweight behind
px, py = PIVOT
panel = cad.cut(panel, cyl(1.6, (px, py, HEIGHT - 1.5), 2.0))
hx, hy = mx + PLATTER_R + 3.5, my - 8.5               # the headshell, parked on its rest
L_ARM = math.hypot(hx - px, hy - py)
ang = math.degrees(math.atan2(hy - py, hx - px))
arm = box(0.0, L_ARM, -0.8, 0.8, HEIGHT + 2.2, HEIGHT + 3.2)
arm = cad.fuse_one(arm, box(L_ARM - 3.0, L_ARM + 1.5, -2.0, 2.0, HEIGHT + 2.0, HEIGHT + 3.0),
                   cyl(2.0, (-4.5, 0, HEIGHT + 1.4), 2.4, (0, 0, 1)), box(-4.5, 0.5, -0.8, 0.8, HEIGHT + 2.2,
                                                                       HEIGHT + 3.2),
                   cyl(1.2, (L_ARM - 1.0, 0, HEIGHT), 2.4, (0, 0, 1)))     # the arm rest under the headshell
arm.rotate(V(0, 0, 0), V(0, 0, 1), ang)
arm.translate(V(px, py, 0))
tonearm = cad.fuse_one(cyl(2.6, (px, py, HEIGHT), 3.4), cyl(1.45, (px, py, HEIGHT - 1.5), 1.6), arm)
# VU segments across the light strip, the skip glyph on the key, a raised
# ring round it, lettering on the walnut deck either side of the panel
# (18 segments of 20 / 3 mm, a light under every three); the strip in
# three frosted parts - green, amber, red - split on the segment lines
# between the lights, so it reads as a level meter
SEG = 20.0 / 3.0
GX = [BB.XMin + k * SEG for k in range(1, 18) if SX0 + 1.0 < BB.XMin + k * SEG < SX1 - 1.0]
strip = cad.cut(strip, [box(g - 0.3, g + 0.3, LY - STRIP_W, LY + STRIP_W, HEIGHT - 0.4, HEIGHT + 1) for g in GX])
XA, XR = BB.XMin + 12 * SEG, BB.XMin + 15 * SEG    # amber from the 4th light, red over the 5th
vu = {"Light_Strip_Green": strip.common(box(SX0 - 5, XA, LY - 20, LY + 20, 0, 80)),
      "Light_Strip_Amber": strip.common(box(XA, XR, LY - 20, LY + 20, 0, 80)),
      "Light_Strip_Red": strip.common(box(XR, SX1 + 5, LY - 20, LY + 20, 0, 80))}
KT = HEIGHT + 1.8
glyph = []
for dx in (-2.6, 0.4):
    tri = Part.Face(Part.makePolygon([V(kx + dx, ky - 2.4, KT - 1.2), V(kx + dx + 2.8, ky, KT - 1.2),
                                      V(kx + dx, ky + 2.4, KT - 1.2), V(kx + dx, ky - 2.4, KT - 1.2)]))
    glyph.append(tri.extrude(V(0, 0, 1.5)))
glyph.append(box(kx + 3.3, kx + 4.4, ky - 2.4, ky + 2.4, KT - 1.2, KT + 0.3))
cap = cad.fuse_one(cap, *glyph)
panel = cad.fuse_one(panel, annulus(KEY_D / 2 + 1.6, KEY_D / 2 + 3.0, (kx, ky), HEIGHT - 0.5, HEIGHT + 0.6))
DY = (PY0 + PY1) / 2
body = cad.text(body, "NOW PLAYING", (-(X1 + PX1) / 2, DY, HEIGHT), (0, 0, 1), 6, depth=0.5, mode="deboss",
                up=(0, 1, 0))
body = cad.text(body, "ATECH", ((X1 + PX1) / 2, DY, HEIGHT), (0, 0, 1), 6, depth=0.5, mode="deboss", up=(0, 1, 0))
# the plinth reveal, the brass trim line inlaid along the front face
REVEAL = SPLIT + 3.0                                  # above the lip's groove inside
body = cad.groove_ring(body, "Z", REVEAL, w=0.8, depth=0.6)
ZT = (REVEAL + HEIGHT - EDGE) / 2
body, trim = insert(body, box(-X1 + 6.0, X1 - 6.0, Y0 - 1.0, Y0 + 1.2, ZT - 1.0, ZT + 1.0))
# under the plinth: lettering, four rubber feet in recesses
base = cad.text(base, "ATECH NP-1", (0, (Y0 + Y1) / 2, Z_BOT), (0, 0, -1), 6, depth=0.4, mode="deboss",
                up=(0, -1, 0))
FEET = [(x, y) for x in (-(X1 - 32.0), X1 - 32.0) for y in (Y0 + 11.0, Y1 - 10.0)]
feet = []
for x, y in FEET:
    base = cad.cut(base, cyl(5.1, (x, y, Z_BOT - 1), 2.0))
    feet.append(cad.foot(10, Z_BOT + 1.0, style="dome", at=(x, y, Z_BOT + 1.0)))
# the record sleeve in the slot (it rests on the slot's bottom, 1 mm clear
# each side): an album whose art is inlaid parts - a vinyl disc with groove
# rings and a label, two stripes, the title
U0 = (SLOT_W - SLEEVE[1]) / 2
S2 = SLEEVE[0] / 2
sleeve = box(-S2, S2, U0, U0 + SLEEVE[1], 0.0, SLEEVE[0])
ART = 1.2
VC, VR = (38.0, 175.0), 112.0                          # the vinyl disc on the art


def ucyl(r, c, u0, u1):
    return Part.makeCylinder(r, u1 - u0, V(c[0], u0, c[1]), V(0, 1, 0))


sleeve, vinyl = insert(sleeve, ucyl(VR, VC, U0 - 1, U0 + ART))
vinyl, label = insert(vinyl, ucyl(36.0, VC, U0 - 2, U0 + ART + 0.5))
label = cad.cut(label, ucyl(3.6, VC, U0 - 1, U0 + ART + 1))
vinyl = cad.cut(vinyl, [cad.cut(ucyl(r + 0.4, VC, U0 - 1, U0 + 0.4), ucyl(r - 0.4, VC, U0 - 2, U0 + 1))
                        for r in (52.0, 68.0, 84.0, 100.0)])
sleeve, teal = insert(sleeve, box(-S2 + 14.0, -S2 + 34.0, U0 - 1, U0 + ART, 24.0, SLEEVE[0] + 1))
sleeve, cream = insert(sleeve, box(-S2 + 40.0, -S2 + 48.0, U0 - 1, U0 + ART, 24.0, SLEEVE[0] + 1))
sleeve = cad.text(sleeve, "ATECH SESSIONS", (-S2 + 120.0, U0, SLEEVE[0] - 18.0), (0, -1, 0), 11, depth=0.8,
                  mode="deboss")
sleeve, vinyl, label, teal, cream = [lean(s) for s in (sleeve, vinyl, label, teal, cream)]
tick("stage B")


# ------------------------------------------------------------ stability (a sleeve in the slot)
PLA, STEEL = 1.24e-3, 7.85e-3                          # g / mm3
def com(s):
    return sum((sol.CenterOfMass * sol.Volume for sol in s.Solids), V()) * (1.0 / s.Volume)


masses = [(s.Volume * PLA, com(s)) for s in (base, body, panel, strip, bezel, window, platter, cap, trim)]
masses += [(weight.Volume * STEEL, com(weight)), (70.0, V(0, 0, PT)),   # the board and modules ~70 g
           (SLEEVE_G, sleeve.BoundBox.Center)]
M = sum(m for m, _c in masses)
CY_ = sum(m * c.y for m, c in masses) / M
CZ_ = sum(m * c.z for m, c in masses) / M
YF1 = max(y for _x, y in FEET)
print("WEIGHT steel bar %.0f x 30 x %.1f mm, %.0f g" % (2 * WX, WT, weight.Volume * STEEL))
print("STABILITY %.0f g with a %.0f g sleeve: centre of mass y %.1f z %.1f, the back feet at y %.1f - "
      "%.1f mm inside them, it tips back only past %.0f deg (the sleeve's own centre y %.1f)" % (
          M, SLEEVE_G, CY_, CZ_, YF1, YF1 - CY_, math.degrees(math.atan2(YF1 - CY_, CZ_)),
          sleeve.BoundBox.Center.y))


# ------------------------------------------------------------ parts
def part(name, shape, colour=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = cad.color(COLOURS[colour or name])
    return o


part("Base", base)
part("Body", body)
part("Panel", panel)
for nm, sh in vu.items():
    o = part(nm, sh)
    o.ViewObject.Transparency = cad.transparency("frosted")
part("Screen_Bezel", bezel)
o = part("Screen_Window", window)
o.ViewObject.Transparency = cad.transparency("smoked")
part("Platter", platter)
part("Tonearm", tonearm)
part("Skip_Key", cap)
part("Trim", trim)
part("Weight", weight)
part("Record_Sleeve", sleeve)
part("Vinyl", vinyl)
part("Label", label)
part("Stripe_Teal", teal)
part("Stripe_Cream", cream)
part("Felt_Clip_Front", felts[0], "Felt")
part("Felt_Clip_Back", felts[1], "Felt")
for i, sh in enumerate(feet):
    part("Foot_%d" % (i + 1), sh, "Foot")
for i, sh in enumerate(screws):
    part("Screw_%d" % (i + 1), sh, "Screw")
print("SIZE", cad.measure(Part.makeCompound([base, body, sleeve]))["size"])
print("TOTAL %.1f s" % (time.time() - T0))
