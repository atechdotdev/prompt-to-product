"""Example: "a flip focus timer" - a soft tomato-red cube you roll onto 5 / 15 / 25 / 50; the face that is up starts the countdown.

fork this file for a flip timer / pomodoro cube (a time-tracking die, a mood cube); change PARAMETERS and the outlines.
Any block whose UP face picks a mode and whose front shows it forks it too.
ARCHETYPE: flip timer

How it is built (R940):
  * STAGE A - hardware, shell, every working-face opening, fasteners: a
    rounded-square prism (WIDTH x WIDTH across the front, DEPTH deep) that
    ROLLS about its front-to-back axis: its four long faces carry the four
    durations, the front always faces you. The board LANDSCAPE_UP behind
    the front (modules facing -Y), only SDK pairs (ports 8 and 12 are
    reserved, so nothing is centred on the board): the screen (4, 5)
    behind a smoked lens in a black bezel tray, inside a frosted HALO ring
    (38 mm radius) lit from behind through two light pipes by the lights
    (3, 6) 30 mm either side of the screen - it glows when time is up; the
    chime speaker (10, 11) hanging above the board's left half behind a
    round grille with a chamber tube - halo low right, grille high left,
    balanced about the square's centre; the orientation module (1) seated
    square on the board (it reads which face is up); USB-C (7) in a pocket
    with a liner in the left face. One rounded box, rolled front and back
    edges, hollowed with its own core, a parting reveal, split FRONT /
    BACK just behind the board with a lip: the back holds the board on
    ledges and standoffs, four M2.5 screws from the back into heat-set
    insert columns on the front, one in each rolling corner.
  * STAGE B - details: leaf-green rubber rails on every labelled face (two
    each, in pockets), the big debossed numerals 5 / 15 / 25 / 50 with MIN,
    a 12-tick dial round the halo, FOCUS on the face, lettering on the back.
RESTYLE (R425): DEPTH, CORNER, EDGE, PAD_OUT and WALL drive every outline,
cutter, rail, screw and numeral below (WIDTH is fixed by the hardware);
the board sits at the square's centre across and ZC - 26.5 up, the front's inner face stays 1.5 mm in
front of the speaker whatever the wall. The hardware frame (board x
0..120) is the board's own: never move it with a knob.
DETAILS (visible, 24): 1 rounded-square prism, 22 mm rolling corners;
2 rolled front edge; 3 rolled back edge; 4 two-tone: cream front, tomato
back; 5 parting reveal; 6 frosted halo ring, 0.5 mm proud; 7 smoked lens
set 1 mm back; 8 black bezel between halo and lens; 9 black mask with the
screen window; 10 12-tick dial round the halo, the four face ticks wider;
11 round chime grille; 12 FOCUS on the face; 13-16 debossed 25 / 50 / 5 /
15 on the four faces (25 up as built); 17 MIN beside each; 18 two rubber
rails per labelled face (8), 1.2 mm proud, rounded treads; 19 USB-C pocket
with liner; 20 four countersunk screws in the back; 21 "ATECH" on the
back; 22 "FLIP TO START" on the back; 23 the rails sunk in pockets;
24 the halo's two light pipes (seen through the frost).
Inside: speaker chamber tube, rib onto the board's spine, board ledges
and standoffs, insert columns, the lip.
Materials: cream front, tomato-red back, smoked lens, black bezel,
frosted band, leaf-green rubber rails, chrome screws.
MEASURED (R940, 2026-11-10): ./check CHECK PASS, model 13.5 s (39 s wall with the review sheets).
"""
import math
import time
import Part
import atech_ports as ap
import atech_cad as cad
from FreeCAD import Vector, Placement, Rotation
V = Vector
T0 = time.time()

INTENT = {"board": "upright", "fitted_after": [
    "Front", "Halo", "Bezel", "Lens",
    "Pad_1", "Pad_2", "Pad_3", "Pad_4", "Pad_5", "Pad_6", "Pad_7", "Pad_8",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4"]}
REVIEW_CLOSEUPS = ["Halo", "Pad_1"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline, cutter, rail,
# screw and numeral in the stages is derived from them (WIDTH below is not
# a knob: the board's 120 mm and the halo set it).
DEPTH = 80.0       # RESTYLE 66..94 length: front face to back (y)
CORNER = 22.0      # RESTYLE 18.5..25.5 radius: the rolling corners seen from the front
EDGE = 6.0         # RESTYLE 5..7 radius: the rolled front and back edges
PAD_OUT = 1.2      # RESTYLE 1.0..1.4 height: the rubber rails, proud of each labelled face
WALL = 2.5         # RESTYLE 2.1..2.9 wall
# end RESTYLE
WIDTH = 140.0                        # the square, side to side AND bottom to top (x, z); 136..156 fits the hardware
PAD_IN = 1.0                         # the rails sunk in their pockets
PAD_L, PAD_W = 0.53 * WIDTH, 5.5     # rail length along the face, width
Z0 = PAD_OUT                         # the body's bottom (the rails stand on the desk)
XC, ZC = 60.0, Z0 + WIDTH / 2        # the square's centre (the board's centre across)
X0, X1 = XC - WIDTH / 2, XC + WIDTH / 2
ZT = Z0 + WIDTH
ZB = ZC - 26.5                       # board bottom: the halo (low) and the grille (high) balance on ZC
SPK_FACE = -20.2                     # the speaker's face in front of the PCB (catalogue)
YF = SPK_FACE - 1.5 - WALL           # the front face
Y_IN = YF + WALL                     # its inner face
YB = YF + DEPTH                      # the back
RO, RI = 38.0, 22.0                  # the frosted halo ring: outer / inner radius (lights at 30 mm)
BEZEL, RECESS, HALO_UP = 2.0, 1.0, 0.5   # black bezel inside the halo, the lens set back, the halo proud
SCREEN_WIN = (28.0, 16.0)            # mask window over the screen (active area 25.6 x 13.5)
GRILLE_D = 32.0
SCREW = "M2.5"
NUMERALS = {"+Z": "25", "+X": "50", "-Z": "5", "-X": "15"}    # the face up = the minutes
COLOURS = {"Front": "cream", "Back": "#d9483b", "Bezel": "matte_black", "Lens": "smoked",
           "Halo": "frosted", "Pad": "#5e8f4e", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
# (SDK pairs only: ports 8 and 12 are reserved, so no pair is centred on
# the board - the screen sits 20 mm right of centre, the halo with it)
LANDSCAPE_UP = Rotation(Vector(0, 0, 1), 180).multiply(Rotation(Vector(0, 1, 0), -90))
board = ap.board_object(doc)
board.Placement = Placement(V(), LANDSCAPE_UP)
_b = ap.bbox(board)
board.Placement = Placement(V(-_b.XMin, 0, ZB - _b.ZMin), LANDSCAPE_UP)    # x 0..120
BB = ap.bbox(board)
scr = ap.seat(doc, "screen", (4, 5))            # bottom row, right of centre: the countdown
glow_l = ap.seat(doc, "light", 3)               # either side of the screen, 30 mm off its centre:
glow_r = ap.seat(doc, "light", 6)               # they light the halo ring when time is up
spk = ap.seat(doc, "speaker", (10, 11))         # top row, left of centre, hangs above the board: the chime
imu = ap.seat(doc, "orientation", 1)            # seated square: which face is up
usb = ap.seat(doc, "usbc", 7)                   # left end, mouth -X
SB, SC, L3, L6, UB = [ap.bbox(m) for m in (spk, scr, glow_l, glow_r, usb)]
print("HW board x %.1f..%.1f z %.1f..%.1f; speaker x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (
    BB.XMin, BB.XMax, BB.ZMin, BB.ZMax, SB.XMin, SB.XMax, SB.YMin, SB.YMax, SB.ZMin, SB.ZMax))
tick("hardware")


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, -1, 0)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def ycyl(r, x, z, y0, y1):
    """A round disc in (x, z) from y0 to y1 (y0 < y1)."""
    return Part.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0))


def centre(b):
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


def yprism(x0, x1, z0, z1, r, y0, y1):
    """A rounded rectangle in (x, z) extruded along Y from y0 to y1."""
    w = cad.rounded_rect_wire(x1 - x0, z1 - z0, r, ((x0 + x1) / 2, y0, (z0 + z1) / 2), "Y")
    s = Part.Face(w).extrude(V(0, y1 - y0, 0))
    if s.Volume < 0:
        s.reverse()
    return s


def xprism(y0, y1, z0, z1, x0, x1, r):
    w = cad.rounded_rect_wire(y1 - y0, z1 - z0, r, (x0, (y0 + y1) / 2, (z0 + z1) / 2), "X")
    return Part.Face(w).extrude(V(x1 - x0, 0, 0))


# ------------------------------------------------------------ the body
# a rounded square (CORNER: the rolling corners) extruded front to back,
# its front and back edges rolled EDGE
outer = cad.rounded_box(WIDTH, DEPTH, WIDTH, CORNER, at=(X0, YF, Z0), edges="y")
outer = cad.fillet_safe(outer, EDGE, edges=[e for e in outer.Edges if e.BoundBox.YMax < YF + 0.01])
outer = cad.fillet_safe(outer, EDGE, edges=[e for e in outer.Edges if e.BoundBox.YMin > YB - 0.01])


def slab(t):
    """The body moved t in all round, sharp edges (the core, the skin)."""
    return cad.rounded_box(WIDTH - 2 * t, DEPTH - 2 * t, WIDTH - 2 * t, CORNER - t, at=(X0 + t, YF + t, Z0 + t),
                           edges="y")


# the core's front and back edges rounded concentric with the body's
# (EDGE - WALL): a sharp core corner would leave a 1 mm wall in the roll
core, skin = slab(WALL), slab(0.5)
core = cad.fillet_safe(core, EDGE - WALL, edges=[e for e in core.Edges if e.BoundBox.YMin > YB - WALL - 0.01])
core = cad.fillet_safe(core, EDGE - WALL, edges=[e for e in core.Edges if e.BoundBox.YMax < YF + WALL + 0.01])
hull = cad.cut(outer, core)
# the parting reveal goes in BEFORE the split (it needs a closed ring)
SPLIT_Y = BB.YMax + 0.3
hull = cad.groove_ring(hull, "Y", SPLIT_Y - 2.0, w=0.8, depth=0.6)
front, back = cad.split(hull, "Y", at=SPLIT_Y, lip=1.2)
tick("body")

# ------------------------------------------------------------ back: holds the board
YI = YB - WALL + 0.5                            # into the back wall
ledges = [box(4, 116, 0.6, YI, BB.ZMin - 2.3, BB.ZMin - 0.3)]
ledges += [box(a, b, 0.6, YI, BB.ZMax + 0.3, BB.ZMax + 2.3) for a, b in ((4, SB.XMin - 1.0), (SB.XMax + 1.0, 116))]
ledges += [box(x, x + 6, BB.YMax + 0.1, YI, BB.ZMin + z, BB.ZMin + z + 6) for x in (8, 57, 106) for z in (7, 47)]
back = cad.fuse_one(back, *[lg.common(skin) for lg in ledges])
# four M2.5 screws from the back into insert columns on the front, one in
# each rolling corner, clear of every module and of the halo
INSERT_D = {"M2": 3.2, "M2.5": 3.6, "M3": 4.3}[SCREW]
SCREW_IN = min(CORNER, 22.0)          # (a bigger corner would bring the low right screw into the halo)
SCREWS = [(x, z) for x in (X0 + SCREW_IN, X1 - SCREW_IN) for z in (Z0 + SCREW_IN, ZT - SCREW_IN)]
screws = []
for x, z in SCREWS:
    back, front = cad.screw_through(back, front, (x, YB, z), size=SCREW, ribs=0)
    yb = YB - WALL - 0.1
    front = cad.fuse_one(front, cyl(INSERT_D / 2 + 1.2, (x, yb, z), 10.0))
    front = cad.cut(front, cyl(INSERT_D / 2, (x, yb + 0.5, z), 9.5))
    screws.append(cad.screw("csk_phillips", SCREW, round(WALL + 8.0), at=(x, YB, z), axis="-Y"))
# board retention: a rib from the front wall onto the spine (0.2 mm off),
# left of the halo, under the speaker
front = cad.fuse_one(front, box(26, 32, Y_IN - 0.5, BB.YMin - 0.2, BB.ZMin + 24.0, BB.ZMin + 34.0))
tick("back + screws")

# ------------------------------------------------------------ the face
# the countdown: ONE round opening (RO) on the screen's centre holds three
# nested inserts - a frosted HALO ring (RI..RO, HALO_UP proud) lit from
# behind by both lights through two light pipes; inside it a black bezel
# tray set RECESS back, its back the mask with the screen window; in the
# tray the smoked lens
sx, _sy, sz = centre(SC)
front = cad.cut(front, ycyl(RO, sx, sz, YF - 6, Y_IN + 0.5))
halo = cad.cut(ycyl(RO, sx, sz, YF - HALO_UP, Y_IN), ycyl(RI, sx, sz, YF - 7, Y_IN + 1))
y_led = min(L3.YMin, L6.YMin) - 0.4
ann = cad.cut(ycyl(RO - 0.4, sx, sz, Y_IN - 0.5, y_led), ycyl(RI + 0.4, sx, sz, Y_IN - 1, y_led + 1))
pipes = [ann.common(yprism(L.XMin + 1.0, L.XMax - 1.0, L.ZMin + 1.0, L.ZMax - 1.0, 1.5, Y_IN - 1, y_led + 1))
         for L in (L3, L6)]
halo = cad.fuse_one(halo, *pipes)
yt0, yt1 = YF + RECESS, Y_IN + 2.0
tray = cad.cut(ycyl(RI, sx, sz, yt0, yt1), ycyl(RI - BEZEL, sx, sz, yt0 - 1, Y_IN + 1.0))
lens = ycyl(RI - BEZEL, sx, sz, yt0 + 0.6, Y_IN + 0.7)                    # 0.3 mm air before the mask
tray = cad.cut(tray, cad.rounded_box(SCREEN_WIN[0], 10, SCREEN_WIN[1], 1.5,
                                     at=(sx - SCREEN_WIN[0] / 2, yt1 - 5, sz - SCREEN_WIN[1] / 2), edges="y"))
# the chime: a round grille over the speaker's surround, a chamber tube to
# 0.5 mm off the driver (the sound goes out, not into the case)
kx, _ky, kz = centre(SB)
front = cad.speaker_grille(front, (kx, YF, kz), (0, -1, 0), GRILLE_D, ring_pitch=2.6, hole=1.5)
front = cad.fuse_one(front, cad.cut(cyl(17.6, (kx, SB.YMin - 0.5, kz), (SB.YMin - 0.5) - (YF + 1.0)),
                                    cyl(16.6, (kx, SB.YMin, kz), 40)))
# USB-C in the left face: a pocket brings the wall to 0.25 mm off the
# socket mouth, then the measured opening
uy, uz = -5.9, (UB.ZMin + UB.ZMax) / 2
pocket = xprism(uy - 4.5, uy + 4.5, uz - 6.5, uz + 6.5, X0 - 5, UB.XMin - 1.3, 3)
liner = cad.cut(xprism(Y_IN - 0.4, min(uy + 6.5, SPLIT_Y - 0.6), uz - 8.0, uz + 8.0, UB.XMin - 0.25,
                       X0 + WALL - 0.5, 3.0), pocket)
front = cad.fuse_one(cad.cut(front, pocket), liner)
front = cad.cut(front, xprism(uy - 3.25, uy + 3.25, uz - 6.5, uz + 6.5, UB.XMin - 2.0, UB.XMin - 0.1, 1.5))
tick("stage A")


# === STAGE B: details ===
# (a fork may stop after STAGE A, run ./check, then add these one by one)
# rubber rails: two per labelled face (one on each half), each filling a
# PAD_IN pocket and standing PAD_OUT proud - the cube rests on them
PAD_Y = [(YF + EDGE + 0.6, YF + EDGE + 0.6 + PAD_W), (YB - EDGE - 0.6 - PAD_W, YB - EDGE - 0.6)]


def rail(face, y0, y1):
    h, r = PAD_IN + PAD_OUT, PAD_W / 2 - 0.3
    if face in ("+Z", "-Z"):
        z = ZT - PAD_IN if face == "+Z" else Z0 - PAD_OUT
        return cad.rounded_box(PAD_L, y1 - y0, h, r, at=(XC - PAD_L / 2, y0, z))
    x = X1 - PAD_IN if face == "+X" else X0 - PAD_OUT
    return cad.rounded_box(h, y1 - y0, PAD_L, r, at=(x, y0, ZC - PAD_L / 2), edges="x")


pads = []
for face in ("+Z", "+X", "-Z", "-X"):
    for y0, y1 in PAD_Y:
        pd = rail(face, y0, y1)
        if y1 < SPLIT_Y:
            front = cad.cut(front, pd)
        else:
            back = cad.cut(back, pd)
        pads.append(pd)
NORMALS = {"+Z": (0, 0, 1), "-Z": (0, 0, -1), "+X": (1, 0, 0), "-X": (-1, 0, 0)}


def round_top(pd, n):
    """Soften the rail's tread (the edges farthest out along n)."""
    top = max(V(*n).dot(v.Point) for v in pd.Vertexes)
    return cad.soften(pd, 0.8, [e for e in pd.Edges if min(V(*n).dot(v.Point) for v in e.Vertexes) > top - 0.01])


pads = [round_top(pd, NORMALS[f]) for pd, f in zip(pads, [f for f in ("+Z", "+X", "-Z", "-X") for _ in PAD_Y])]
# the numerals: big debossed minutes on the back half of each face, read
# from the front when that face is UP (their top toward the back), MIN
# beside each
NUM_SIZE = min(0.19 * WIDTH, PAD_Y[1][0] - SPLIT_Y - 5.0)    # (a shallow cube: smaller numerals)
NUM_Y = (SPLIT_Y + 3.0 + PAD_Y[1][0] - 1.0) / 2
FACE_AT = {"+Z": (XC, NUM_Y, ZT), "-Z": (XC, NUM_Y, Z0), "+X": (X1, NUM_Y, ZC), "-X": (X0, NUM_Y, ZC)}
UPV = V(0, 1, 0)
for face, num in NUMERALS.items():
    n = V(*NORMALS[face])
    at = V(*FACE_AT[face])
    back = cad.text(back, num, at, n, NUM_SIZE, depth=1.0, mode="deboss", up=UPV)
    right = (-n).cross(UPV)
    w = 0.62 * NUM_SIZE * len(num)
    m_at = at + right * (w / 2 + 3.0) - UPV * (0.5 * NUM_SIZE - 2.6)
    back = cad.text(back, "MIN", m_at, n, 4.2, depth=0.5, mode="deboss", up=UPV, halign="left")
# a dial round the halo: 12 debossed ticks, the four that point at the
# labelled faces wider (one cut)
ticks = []
for i in range(12):
    a = math.radians(30 * i)
    tw = 2.0 if i % 3 == 0 else 1.0
    tk = box(RO + 2.5, RO + 5.5, YF - 1, YF + 0.5, -tw / 2, tw / 2)
    tk.rotate(V(0, 0, 0), V(0, 1, 0), 30 * i)
    tk.translate(V(sx, 0, sz))
    ticks.append(tk)
front = cad.cut(front, ticks)
# the face: FOCUS in the open corner the halo and the grille leave
front = cad.text(front, "FOCUS", (X0 + 0.25 * WIDTH, YF, Z0 + 0.2 * WIDTH), (0, -1, 0), 5.0, depth=0.5,
                 mode="deboss", up=(0, 0, 1))
# the back: ATECH and how to use it
back = cad.text(back, "ATECH", (XC, YB, ZC + 9.0), (0, 1, 0), 8.0, depth=0.6, mode="deboss", up=(0, 0, 1))
back = cad.text(back, "FLIP TO START", (XC, YB, ZC - 6.0), (0, 1, 0), 4.5, depth=0.5, mode="deboss", up=(0, 0, 1))
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape, colour=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    c = COLOURS[colour or name]
    o.ViewObject.ShapeColor = cad.color(c)
    if c in ("smoked", "frosted", "glass"):
        o.ViewObject.Transparency = cad.transparency(c)
    return o


for nm, sh in (("Back", back), ("Front", front), ("Halo", halo), ("Bezel", tray), ("Lens", lens)):
    part(nm, sh)
for i, sh in enumerate(pads):
    part("Pad_%d" % (i + 1), sh, "Pad")
for i, sh in enumerate(screws):
    part("Screw_%d" % (i + 1), sh, "Screw")
print("TOTAL %.1f s" % (time.time() - T0))
