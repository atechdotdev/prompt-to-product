"""Example: "a theremin you play by waving your hand over it" - a walnut-and-brass desk theremin: hand height over the sensor sets the pitch.

fork this file for a theremin / air instrument / gesture synth (a hand-wave
music box, a distance-played noise maker, a touchless instrument); change PARAMETERS and the outlines.
ARCHETYPE: theremin

How it is built (R990):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board FLAT in the cabinet, turned so its long side runs across (ROT)
    and its front column (9-14) faces the player: the speaker SEATS on
    (13, 14) front left and the knob on (9, 10) front right, both
    overhanging the board's front edge 20 mm; the distance sensor on 1 at
    the back right looks STRAIGHT UP through an open brass ring (the hand
    hovers over it, beside the pitch mast); four lights on 2 / 3 / 5 / 6
    along the back row under ONE frosted note strip; USB-C on 4 in the
    middle of the back wall (pocket + liner). Ports 7, 8, 11, 12 stay
    empty (8 and 12 are reserved). The cabinet is a WEDGE: one (y, z)
    section - a low front, a raked top rising RISE to the back - extruded
    across and cut to a rounded plan, its top perimeter rolled, hollowed
    with a sharp core (chamfered under the roll so the wall keeps its
    thickness), split LOW into the fixed Base (a black plinth: pads, end
    and side fences hold the board, all under the modules' slide paths)
    and the walnut Body (fitted after). The raked top carries a black
    Panel inset between walnut end cheeks (the right one wider: the mast
    stands in it), resting on a ledge under each end and pegged into it
    (two pegs each end); the grille, the knob ring, the note strip and the
    sensor ring are inserts in it. The front grows to whatever the speaker
    under the rake needs (HF is solved, not set). Four M2.5 screws from
    below into insert bosses in the cheeks.
  * STAGE B - details: the chrome pitch mast in a brass collar pegged
    into a bored column in the right cheek, the chrome volume loop pinned
    through the left end, a brass pinstripe along the front, lettering,
    the knob's knurl and pointer, scale dots round the knob, the strip's
    seven note cells and letters, four splayed peg legs with brass ferrules.
DETAILS (visible, 29): 1 walnut wedge cabinet with a raked top; 2 rolled
top perimeter; 3 black control panel inset between walnut cheeks; 4 big
50 mm brass speaker grille disc; 5 its rings of holes; 6 a raised brass
bezel round the grille; 7 chrome knob cap, knurled; 8 its pointer groove;
9 frosted LED ring round the knob; 10 eleven scale dots round the knob;
11 frosted note strip over four lights; 12 six dividers making seven
note cells; 13 note letters C D E F G A B under the strip; 14 raised brass
sensor ring over the open aperture; 15 an engraved arc round it; 16 the
aperture's chimney down to the sensor; 17 chrome pitch mast, two
telescoping sections; 18 a ferrule between them; 19 ball tip; 20 brass
mast collar on the rake; 21 chrome volume loop out of the left end;
22 its two flanges on the end wall; 23 brass pinstripe inlaid along the
front; 24 "ATECH THEREMIN" and 25 "PITCH" on the front; 26 black plinth
under the walnut; 27 USB-C pocket with a liner in the back; 28 four
splayed walnut peg legs with brass ferrules; 29 four countersunk screws
from below.
Inside: board pads, end and side fences, light pipes down to 0.5 mm off
the LEDs, the knob ring's pipe, insert sleeves in the screw bosses, the
panel's ledges and pegs, the mast's bored column, leg bosses, the lip
keying Body to Base.
Materials: walnut body and legs, black plinth and panel, brass grille,
bezel, sensor ring, mast collar, ferrules and pinstripe, chrome mast,
loop, knob cap and screws, frosted knob ring and note strip.
MEASURED (R990, 2026-11-17): ./check CHECK PASS, run_seconds 17 s, wall 51 s; every RESTYLE end CHECK PASS.
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
    "Body", "Panel", "Grille", "Bezel", "Knob_Ring", "Knob_Cap", "Note_Strip", "Sensor_Ring",
    "Mast_Collar", "Mast", "Loop", "Pinstripe", "Leg_1", "Leg_2", "Leg_3", "Leg_4", "Ferrule_1", "Ferrule_2", "Ferrule_3", "Ferrule_4",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4"]}
REVIEW_CLOSEUPS = ["Sensor_Ring", "Grille", "Knob_Cap", "Note_Strip"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them (the rake, the panel, the
# inserts on it, the screws, the mast and the loop).
LENGTH = 220.0     # RESTYLE 187..253 length: the cabinet across (x); it grows to the left
RISE = 32.0        # RESTYLE 27..37 height: the rake's rise from the front edge to the back
MAST_H = 130.0     # RESTYLE 110..150 height: the pitch mast over its collar
EDGE_R = 5.0       # RESTYLE 4.2..5.8 radius: the rolled top perimeter
WALL = 2.5         # RESTYLE 2.1..2.9 wall
# end RESTYLE
# Cabinet frame: x across (the mast at +X), y front (-) to back (+), z up;
# the desk at z = 0. The board's own frame (x -60..60, y -30..30) is fixed.
Z_BOT = 28.0                      # the plinth's underside: the peg legs' height
SPLAY = 8.0                       # the legs lean out this much
RIGHT_M = 36.0                    # the right cheek past the board's end (the mast stands in it)
FRONT_GAP, BACK_GAP = 12.0, 10.0    # air in front of the speaker / behind the back row
CORNER = 14.0                     # plan corners
CHEEK = (16.0, 26.0)              # the walnut cheeks, left / right (the mast stands in the right one)
GRILLE_D = 50.0                   # the brass grille disc over the speaker
RING_R = (8.6, 17.0)              # the frosted ring round the knob shaft (inner, outer)
CAP_R = 11.0                      # the chrome knob cap
STRIP_W = 11.0                    # the frosted note strip's width
EYE_R = (7.0, 11.5)               # the sensor ring: open aperture radius, ring outer radius
LOOP = (54.0, 30.0, 2.4)          # the volume loop: reach out of the end, bend radius, tube radius
SCREW = "M2.5"
COLOURS = {"Base": "#1b1a1a", "Body": "#8a5a35", "Panel": "#1d1d1f", "Grille": "brass", "Bezel": "brass",
           "Knob_Ring": "frosted", "Knob_Cap": "chrome", "Note_Strip": "frosted", "Sensor_Ring": "brass",
           "Mast_Collar": "brass", "Mast": "chrome", "Loop": "chrome", "Pinstripe": "brass",
           "Leg": "#8a5a35", "Ferrule": "brass", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
FLAT = Rotation(Vector(1, 0, 0), 90)
ROT = Rotation(Vector(0, 0, 1), -90).multiply(FLAT)    # long side across, ports 9-14 at the front
FLOOR = Z_BOT + WALL
BZ = FLOOR + 3.0                                       # the board's underside, on pads
board = ap.board_object(doc)
board.Placement = Placement(Vector(), ROT)
_b = ap.bbox(board)
board.Placement = Placement(Vector(-60.0 - _b.XMin, 30.0 - _b.YMax, BZ - _b.ZMin), ROT)  # x -60..60, y -30..30
BB = ap.bbox(board)
PT = BB.ZMin + 2.5                                     # the PCB top: every module's seat
spk = ap.seat(doc, "speaker", (13, 14))                # front left, overhangs to y -50.4
knob = ap.seat(doc, "knob", (9, 10))                   # front right, overhangs to y -50.5
eye = ap.seat(doc, "distance_sensor", 1)               # back right, looking up at the hand
lights = [ap.seat(doc, "light", n) for n in (6, 5, 3, 2)]   # the note row, left to right
usb = ap.seat(doc, "usbc", 4)                          # back, mouth +Y
tick("hardware")
SB, KB, EB = ap.bbox(spk), ap.bbox(knob), ap.bbox(eye)
SPLIT = BZ - 2.0                                       # plinth / body seam, under every slide path
X1 = BB.XMax + RIGHT_M
X0 = X1 - LENGTH
Y0 = min(SB.YMin, KB.YMin) - FRONT_GAP - WALL
Y1 = max(ap.bbox(m).YMax for m in lights + [eye, usb]) + BACK_GAP + WALL
DEPTH = Y1 - Y0
K = RISE / DEPTH                                       # the rake's slope (dz / dy)
SEC = math.sqrt(1.0 + K * K)                           # vertical wall thickness = WALL * SEC
# the front height: the rake's inner face 1.2 mm over the speaker's front edge
HF = SB.ZMax + 1.2 + WALL * SEC - (SB.YMin - Y0) * K
HB = HF + RISE
NRM = V(0, -K, 1) / SEC                                # the rake's outward normal
UPS = V(0, 1, K) / SEC                                 # up the rake


def top_out(y):
    return HF + (y - Y0) * K


def top_in(y):
    return top_out(y) - WALL * SEC


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


def section(y0, y1, zb, zf, x0, x1):
    """The wedge: the (y, z) section - flat bottom zb, front zf at y0, the
    rake at slope K - extruded from x0 to x1."""
    pts = [V(x0, y0, zb), V(x0, y1, zb), V(x0, y1, zf + (y1 - y0) * K), V(x0, y0, zf), V(x0, y0, zb)]
    return Part.Face(Part.makePolygon(pts)).extrude(V(x1 - x0, 0, 0))


def rake_faces(shape):
    return [f for f in shape.Faces if f.Surface.__class__.__name__ == "Plane"
            and abs(f.normalAt(0, 0).z - 1.0 / SEC) < 1e-3 and abs(f.normalAt(0, 0).y + K / SEC) < 1e-3]


def plan_cut(x0, x1, y0, y1, r, z0, z1):
    return cad.rounded_box(x1 - x0, y1 - y0, z1 - z0, r, at=(x0, y0, z0))


# ------------------------------------------------------------ the cabinet
OUTER = section(Y0, Y1, Z_BOT, HF, X0, X1).common(plan_cut(X0, X1, Y0, Y1, CORNER, Z_BOT - 1, HB + 5))
OUTER = cad.fillet_safe(OUTER, EDGE_R, edges=rake_faces(OUTER)[0].Edges)
OUTER = cad.fillet_safe(OUTER, 1.0, edges=[e for e in OUTER.Edges if e.BoundBox.ZMax < Z_BOT + 0.01])
# the core keeps SHARP inner edges, chamfered under the roll so the wall
# keeps its thickness round the rolled perimeter
core = section(Y0 + WALL, Y1 - WALL, Z_BOT + WALL, HF + WALL * K - WALL * SEC, X0 + WALL, X1 - WALL).common(
    plan_cut(X0 + WALL, X1 - WALL, Y0 + WALL, Y1 - WALL, CORNER - WALL, Z_BOT, HB + 5))
CH = 0.75 * (EDGE_R - WALL) + 0.3
if CH > 0.4:
    core = cad.chamfer_safe(core, CH, edges=rake_faces(core)[0].Edges)
shell = cad.cut(OUTER, core)
tick("cabinet")
base, body = cad.split(shell, "Z", at=SPLIT, lip=1.2)
tick("split")

# ------------------------------------------------------------ the plinth holds the board
# pads 0.1 mm under the board, fences off its ends and long sides - all
# under the modules' seat plane (PT), so every slide path stays clear
pads = [box(x - 4, x + 4, y - 4, y + 4, FLOOR - 0.5, BB.ZMin - 0.1) for x in (-48, 48) for y in (-20, 20)]
fences = [box(sx * 60.3, sx * 61.8, -8, 8, FLOOR - 0.5, PT - 1.5) for sx in (-1, 1)]
fences += [box(x - 6, x + 6, sy * 30.3, sy * 31.8, FLOOR - 0.5, PT - 1.5) for x in (-30, 30) for sy in (-1, 1)]
base = cad.fuse_one(base, *pads, *fences)

# ------------------------------------------------------------ the cream panel between the cheeks
PX0, PX1 = X0 + CHEEK[0], X1 - CHEEK[1]
PY0, PY1 = Y0 + EDGE_R + 2.5, Y1 - EDGE_R + 0.5 - 2.5
body, panel = insert(body, plan_cut(PX0, PX1, PY0, PY1, 4.0, SPLIT + 3.0, HB + 5))
# it rests on a ledge under each end (flush with its inner face, hung from
# the cheek's top wall) and is pegged into it: two pegs each end
ledges, pegs, peg_bores = [], [], []
for xe, s in ((PX0, 1), (PX1, -1)):
    ya, yb = PY0 + 6.0, PY1 - 6.0
    lo = top_in(ya) - 8.0
    ledges.append(box(xe - s * 4.0, xe, ya, yb, lo, HB).common(core.translated(V(0, 0, 0.5))))
    ledges.append(box(xe, xe + s * 5.0, ya, yb, lo, HB).common(core.translated(V(0, 0, -0.05))))
    for y in (ya + 5.0, yb - 5.0):
        px = xe + s * 2.5
        pegs.append(cyl(1.5, (px, y, top_in(y) - 4.5), 4.5 + 0.8))
        peg_bores.append(cyl(1.65, (px, y, top_in(y) - 5.5), 6.5))
body = cad.cut(cad.fuse_one(body, *ledges), peg_bores)
panel = cad.fuse_one(panel, *pegs)
tick("panel")

# ------------------------------------------------------------ four screws up into the cheeks
SCREWS = [(x, y) for x in (X0 + CHEEK[0] / 2 + 1.0, X1 - 9.0) for y in (Y0 + 12.0, Y1 - 12.0)]
INSERT_D = {"M2": 3.2, "M2.5": 3.6, "M3": 4.3}[SCREW]
screws = []
for x, y in SCREWS:
    base, body = cad.screw_through(base, body, (x, y, Z_BOT), size=SCREW, ribs=0)
    zf = FLOOR + 0.1
    body = cad.fuse_one(body, cyl(INSERT_D / 2 + 1.2, (x, y, zf), 10.0))
    body = cad.cut(body, cyl(INSERT_D / 2, (x, y, zf - 0.5), 9.5))
    screws.append(cad.screw("csk_phillips", SCREW, 8, at=(x, y, Z_BOT), axis="+Z"))
tick("screws")

# ------------------------------------------------------------ the panel's openings
# the speaker: a brass grille disc on the rake (its axis on the rake's
# normal) fills its own opening; the holes run straight down at the driver
scx, scy, _ = centre(spk)
GC = V(scx, scy, top_out(scy))
panel, grille = insert(panel, Part.makeCylinder(GRILLE_D / 2, WALL * SEC + 4, GC - NRM * (WALL * SEC + 2), NRM))
grille = cad.speaker_grille(grille, GC, (0, 0, 1), GRILLE_D - 6, ring_pitch=2.6, hole=1.6)
# the knob: its shaft up through a frosted ring over its LED ring, the
# ring's pipe down to 0.5 mm off the knob's plate (clipped to the cabinet)
kx, ky, _ = centre(knob)
ZLO, ZHI = top_in(ky + RING_R[1]) - 1.0 - (2 * RING_R[1]) * K, top_out(ky + RING_R[1]) + 1.0
panel = cad.cut(panel, cyl(RING_R[0], (kx, ky, ZLO), ZHI - ZLO))
panel, ring = insert(panel, annulus(RING_R[0] - 0.5, RING_R[1], (kx, ky), ZLO, ZHI))
ring = cad.fuse_one(ring, annulus(RING_R[0], RING_R[1] - 1.0, (kx, ky), PT + 10.6, ZHI).common(OUTER))
# a chrome cap pushed on the knob's own 12.2 mm cap (0.35 mm round it),
# its underside 0.6 mm over the rake, a plug 2 mm down the ring's bore
KT = KB.ZMax + 6.0
cap = cyl(CAP_R, (kx, ky, ZLO), KT - ZLO)
cap = cad.cut(cap, OUTER.translated(V(0, 0, 0.6)))
cap = cad.fillet_safe(cap, 1.5, edges=[e for e in cap.Edges if e.BoundBox.ZMin > KT - 0.01])
plug = annulus(6.45, RING_R[0] - 0.2, (kx, ky), top_out(ky - RING_R[0]) - 2.0, top_out(ky + RING_R[0]) + 1.5)
cap = cad.fuse_one(cap, plug.cut(OUTER.translated(V(0, 0, -2.0))))
cap = cad.cut(cap, cyl(6.45, (kx, ky, ZLO - 1), KB.ZMax + 0.4 - (ZLO - 1)))
print("KNOB shaft %.1f mm over the rake, the cap's top %.1f" % (KB.ZMax - top_out(ky), KT - top_out(ky)))
# the note strip: one frosted stadium over the four back-row lights, a
# light pipe from each down to 0.5 mm off its LEDs (inside its footprint)
LB = [ap.bbox(m) for m in lights]
LY = sum((b.YMin + b.YMax) / 2 for b in LB) / len(LB)
SX0, SX1 = LB[0].XMin + 1.0, LB[-1].XMax - 1.5
sz0, sz1 = top_in(LY - STRIP_W / 2) - 1.0, top_out(LY + STRIP_W) + 1.0
strip_cut = cad.rounded_box(SX1 - SX0, STRIP_W, sz1 - sz0, STRIP_W / 2 - 0.01, at=(SX0, LY - STRIP_W / 2, sz0))
panel, strip = insert(panel, strip_cut)
strip_core = cad.rounded_box(SX1 - SX0 - 1.2, STRIP_W - 1.2, HB, STRIP_W / 2 - 0.61,
                             at=(SX0 + 0.6, LY - STRIP_W / 2 + 0.6, 0)).common(OUTER)
pipes = [box(b.XMin + 1.5, b.XMax - 1.5, LY - STRIP_W / 2, LY + STRIP_W / 2, b.ZMax + 0.5, HB + 2)
         .common(strip_core) for b in LB]
strip = cad.fuse_one(strip, *pipes)
# the hand sensor: an OPEN aperture (no glass) straight up over the ToF,
# a brass ring round it, a chimney from the ring to 0.8 mm off the sensor
ex, ey, _ = centre(eye)
ez0, ez1 = top_in(ey + EYE_R[1]) - 1.0 - 2 * EYE_R[1] * K, top_out(ey + EYE_R[1]) + 1.0
panel = cad.cut(panel, cyl(EYE_R[0], (ex, ey, ez0), ez1 - ez0))
panel, eye_ring = insert(panel, annulus(EYE_R[0] - 0.5, EYE_R[1], (ex, ey), ez0, ez1))
eye_ring = cad.fuse_one(eye_ring, annulus(EYE_R[0], EYE_R[0] + 1.6, (ex, ey), EB.ZMax + 0.8, ez1).common(OUTER))
# USB-C at the back: a pocket brings the wall to 0.25 mm off the mouth
ub = ap.bbox(usb)
ux, uz = (ub.XMin + ub.XMax) / 2, PT + 5.9


def yprism(x0, x1, z0, z1, y0, y1, r):
    w = cad.rounded_rect_wire(x1 - x0, z1 - z0, r, ((x0 + x1) / 2, y0, (z0 + z1) / 2), "Y")
    return Part.Face(w).extrude(V(0, y1 - y0, 0))


pocket = yprism(ux - 6.0, ux + 6.0, uz - 5.0, uz + 5.0, ub.YMax + 1.3, Y1 + 5, 3)
liner = cad.cut(yprism(ux - 8.0, ux + 8.0, uz - 7.0, uz + 7.0, ub.YMax + 0.25, Y1 - 1.0, 4), pocket)
body = cad.fuse_one(cad.cut(body, pocket), liner)
body = cad.socket_opening(body, usb, margin=1.5)
tick("stage A")


# === STAGE B: details ===
# a raised brass bezel round the grille (on the rake, keyed 0.8 mm into it)
bez = Part.makeCylinder(GRILLE_D / 2 + 2.2, 2.0, GC - NRM * 0.8, NRM).cut(
    Part.makeCylinder(GRILLE_D / 2, 4.0, GC - NRM * 1.5, NRM))
panel = cad.cut(panel, bez)
body = cad.cut(body, bez, optional=True)
# the raised sensor ring: the ring stands 1.5 mm proud, parallel to the rake
eye_ring = cad.fuse_one(eye_ring, annulus(EYE_R[0], EYE_R[1], (ex, ey), ez0, ez1 + 2.0)
                        .common(OUTER.translated(V(0, 0, 1.5 * SEC))).cut(OUTER))
# a groove ring round the sensor (engraved parallel to the rake, 0.4 deep)
def engrave(cutter, depth=0.4):
    return cutter.common(OUTER).cut(OUTER.translated(V(0, 0, -depth * SEC)))


# (an arc: it stops 2.5 mm short of the note strip's end)
panel = cad.cut(panel, engrave(annulus(EYE_R[1] + 2.0, EYE_R[1] + 2.7, (ex, ey), ez0 - 5, ez1 + 5)
                               .cut(box(SX1 - 50, SX1 + 2.5, ey - 30, ey + 30, ez0 - 6, ez1 + 6))))
# scale dots round the knob ring, the knob's knurl and pointer
dots = []
for i in range(11):
    a = math.radians(225 - 27 * i)
    px, py = kx + (RING_R[1] + 2.6) * math.cos(a), ky + (RING_R[1] + 2.6) * math.sin(a)
    dots.append(cyl(0.7, (px, py, top_out(py) - 0.5), 2.0))
panel = cad.cut(panel, dots)
KZ0 = top_out(ky + CAP_R) + 0.6
cap = cad.knurl(cap, "+Z", (kx, ky, KZ0), CAP_R, 0.5, KT - KZ0 - 1.8, n=40, depth=0.35)
cap = cad.cut(cap, box(kx - 0.5, kx + 0.5, ky - CAP_R + 1.5, ky - 4.0, KT - 0.6, KT + 1))
# the strip's seven note cells: six engraved dividers across it
cells = [engrave(box(SX0 + (SX1 - SX0) * i / 7.0 - 0.4, SX0 + (SX1 - SX0) * i / 7.0 + 0.4,
                     LY - STRIP_W, LY + STRIP_W, sz0 - 5, sz1 + 5), 0.5) for i in range(1, 7)]
strip = cad.cut(strip, cells)
# note letters under the strip
NOTES = "C D E F G A B"
ly = LY - STRIP_W / 2 - 4.5
panel = cad.text(panel, NOTES, ((SX0 + SX1) / 2, ly, top_out(ly)), (NRM.x, NRM.y, NRM.z), 3.5, depth=0.4,
                 mode="deboss", up=(UPS.x, UPS.y, UPS.z))
tick("panel details")

# the pitch mast: a brass collar on the rake in the right cheek, its spigot
# in a bored column hanging from the top; the chrome rod in the collar's
# bore, a ferrule, a thinner top section and a ball tip
mx, my = X1 - CHEEK[1] / 2, (Y0 + Y1) / 2 + 6.0
mz = top_out(my)
body = cad.fuse_one(body, cyl(7.0, (mx, my, SPLIT + 4.0), mz - SPLIT - 4.0).common(OUTER.translated(V(0, 0, -0.6))))
body = cad.cut(body, cyl(4.15, (mx, my, mz - 14.0), 20.0))
COL_H = 10.0
collar = Part.makeCone(8.5, 5.6, COL_H + 4.0, V(mx, my, mz - 4.0), V(0, 0, 1)).cut(OUTER)
collar = cad.fuse_one(collar, cyl(4.0, (mx, my, mz - 12.0), 12.5))
collar = cad.cut(collar, cyl(3.65, (mx, my, mz + COL_H - 7.0), 8.0))
MZ = mz + COL_H
mast = cad.fuse_one(cyl(3.5, (mx, my, MZ - 6.8), 6.8 + 0.55 * MAST_H),
                    cyl(4.3, (mx, my, MZ + 0.55 * MAST_H - 1.5), 3.5),
                    cyl(2.5, (mx, my, MZ + 0.55 * MAST_H), 0.45 * MAST_H),
                    Part.makeSphere(4.8, V(mx, my, MZ + MAST_H)))
# the volume loop: a chrome U out of the left end, its legs pinned through
# the end wall (bores 0.15 mm round them, a flange on each)
lyc = (Y0 + Y1) / 2 - 4.0
lz = (SPLIT + top_out(lyc - LOOP[1]) - EDGE_R) / 2 + 1.0
lx = X0 - LOOP[0] + LOOP[1]
legs = [cyl(LOOP[2], (X0 + WALL + 0.8, lyc + s * LOOP[1], lz), (X0 + WALL + 0.8) - lx, (-1, 0, 0))
        for s in (-1, 1)]
bend = Part.makeTorus(LOOP[1], LOOP[2], V(0, 0, 0), V(0, 0, 1), -180, 180, 180)
bend.rotate(V(0, 0, 0), V(0, 0, 1), 90)
bend.translate(V(lx, lyc, lz))
flanges = [cyl(LOOP[2] + 2.0, (X0, lyc + s * LOOP[1], lz), 2.0, (-1, 0, 0)) for s in (-1, 1)]
loop = cad.fuse_one(bend, *legs, *flanges)
body = cad.cut(body, [cyl(LOOP[2] + 0.15, (X0 - 1.0, lyc + s * LOOP[1], lz), WALL + 2.0, (1, 0, 0))
                      for s in (-1, 1)])
tick("mast + loop")
# a brass pinstripe inlaid along the front, lettering on the front band
PZ = SPLIT + 4.0
body, stripe = insert(body, box(X0 + CORNER, X1 - CORNER, Y0 - 1.0, Y0 + 1.0, PZ, PZ + 1.6))
body = cad.text(body, "ATECH  THEREMIN", ((X0 + X1) / 2 - 20.0, Y0, (PZ + 1.6 + HF - EDGE_R) / 2),
                (0, -1, 0), 5.0, depth=0.5, mode="deboss")
body = cad.text(body, "PITCH", (mx, Y0, (PZ + 1.6 + HF - EDGE_R) / 2), (0, -1, 0), 3.5, depth=0.4,
                mode="deboss")
base = cad.text(base, "ATECH AT-1", ((X0 + X1) / 2, (Y0 + Y1) / 2, Z_BOT), (0, 0, -1), 6, depth=0.4,
                mode="deboss", up=(0, -1, 0))
# four splayed walnut peg legs (mid-century), each pegged into a boss on
# the plinth's floor, a brass ferrule round its foot, soles cut flat
legs, ferrules, boss_tools, peg_holes = [], [], [], []
t = math.tan(math.radians(SPLAY))
for lx_, ly_, sx, sy in ((X0 + 22.0, Y0 + 17.0, -1, -1), (X1 - 22.0, Y0 + 17.0, 1, -1),
                         (X0 + 22.0, Y1 - 17.0, -1, 1), (X1 - 22.0, Y1 - 17.0, 1, 1)):
    d = V(sx * t * 0.7, sy * t * 0.7, -1.0)
    d.normalize()
    top = V(lx_, ly_, Z_BOT - 0.1)
    L = (Z_BOT + 3.0) / -d.z + 3.0
    leg = Part.makeCone(5.6, 3.6, L, top - d * 3.0, d).common(box(lx_ - 40, lx_ + 40, ly_ - 40, ly_ + 40, 0,
                                                                  Z_BOT - 0.1))
    leg = cad.fuse_one(leg, cyl(2.0, (lx_, ly_, Z_BOT - 0.6), 5.5))
    spigot = V(lx_, ly_, Z_BOT) + d * ((Z_BOT - 1.5) / -d.z)      # on the axis, 1.5 mm over the desk
    ferrule = leg.common(box(lx_ - 40, lx_ + 40, ly_ - 40, ly_ + 40, -1, 6.0))
    ferrule = cad.cut(ferrule, Part.makeCylinder(2.2, 12.0, spigot, d * -1.0))
    leg = cad.cut(leg, ferrule)
    legs.append(leg)
    ferrules.append(ferrule)
    boss_tools.append(cyl(5.5, (lx_, ly_, FLOOR - 0.5), 6.0))
    peg_holes.append(cyl(2.15, (lx_, ly_, Z_BOT - 1.0), 7.0))
base = cad.cut(cad.fuse_one(base, *boss_tools), peg_holes)
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape, colour):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = cad.color(COLOURS[colour])
    return o


part("Base", base, "Base")
part("Body", body, "Body")
part("Panel", panel, "Panel")
part("Grille", grille, "Grille")
part("Bezel", bez, "Bezel")
o = part("Knob_Ring", ring, "Knob_Ring")
o.ViewObject.Transparency = cad.transparency("frosted")
part("Knob_Cap", cap, "Knob_Cap")
o = part("Note_Strip", strip, "Note_Strip")
o.ViewObject.Transparency = cad.transparency("frosted")
part("Sensor_Ring", eye_ring, "Sensor_Ring")
part("Mast_Collar", collar, "Mast_Collar")
part("Mast", mast, "Mast")
part("Loop", loop, "Loop")
part("Pinstripe", stripe, "Pinstripe")
for i, sh in enumerate(legs):
    part("Leg_%d" % (i + 1), sh, "Leg")
for i, sh in enumerate(ferrules):
    part("Ferrule_%d" % (i + 1), sh, "Ferrule")
for i, sh in enumerate(screws):
    part("Screw_%d" % (i + 1), sh, "Screw")
print("SIZE %s" % (cad.measure(Part.makeCompound([base, body, mast, loop]))["size"],))
print("TOTAL %.1f s" % (time.time() - T0))
