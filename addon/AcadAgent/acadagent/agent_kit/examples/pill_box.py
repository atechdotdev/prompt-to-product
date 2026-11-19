"""Example: "a weekly pill box that reminds you to take your pills" - seven pastel sliding day lids in front of a raised console with a screen, a glow light and a TAKEN key.

fork this file for a pill box / pill organiser / medication reminder (a
weekly tray of lidded compartments with a small console behind it); change PARAMETERS and the outlines.
ARCHETYPE: pill box

How it is built (R990):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board FLAT and turned ACROSS (long side left to right, modules up)
    in the console behind the tray, ports 9-14 along its FRONT, all of
    them under ONE black control strip set 1 mm into the deck: the
    screen (13, 14) at the left under a clear tinted window (the next dose
    time), the TAKEN key (11) under a big pill-shaped coral cap with a
    plunger, the reminder lights (9, 10) under ONE frosted capsule with a
    light pipe; on the back row the chime speaker (1, 2), overhanging the
    board's back edge, under a round grille in the raised back hump, and
    USB-C (4) in a pocket with a liner in the back wall. The body is ONE
    side section along X (the flat tray top, a raked step, the hump) cut
    by the rounded plan, hollowed as ONE core: the whole console, and a
    thin cavity under the cups - the tray block itself stays SOLID, so
    every compartment is a cup with its own floor and the electronics are
    sealed off from the pills by the wall behind the cups. Split low into
    the fixed Base (pads and fences under the board, a pad under the
    speaker's overhang) and the Shell; six M2.5 screws from below (four
    into bosses under the console's deck, two through base columns into
    the tray's end rims). Seven cups with scooped floors; each lid slides
    out to the FRONT in T-slots cut into the dividers (its tongues ride
    on the slot floors under a 1.6 mm lip, so a lid cannot lift off) and
    stops on the slot's back end; a finger notch under its front edge.
  * STAGE B - details: the day letters and grip ridges on the lids, a
    raised tick on the key, ATECH on the raked step, a coral pill badge in
    the hump, the parting-line reveal, a
    model mark under the base, rubber feet.
RESTYLE (R425): LENGTH (the tray and the console, x), POCKET_L (each cup
front to back), PZ (the tray height; the board and the hump follow it),
CORNER, WALL; also RIM_S / RIM_F / DIV, LID_T, SCOOP, EDGE_R.
DETAILS (visible, 26 of 37): 1 a 222 x 138 counter footprint with 16 mm
plan corners; 2 the flat tray top; 3 a raked step up to 4 the raised back
hump; 5 rolled top edges; 6 seven sliding lids flush with the tray; 7 one
soft pastel per day; 8 the day letters M T W T F S S raised on the lids;
9 three grip ridges on each lid; 10 the lids' rolled front edges; 11 a
finger notch under each lid's front edge; 12 the 0.2 mm reveal round
every lid; 13 scooped cup floors (lid open); 14 the black control strip,
recessed 1 mm; 15 clear blue-grey tinted screen window; 16 pill-shaped coral TAKEN key;
17 a raised tick on it; 18 frosted capsule glow window; 19 round chime
grille on the hump; 20 "ATECH" on the raked step and a coral pill badge in the hump; 21 USB-C pocket
with liner in the back; 22 parting-line reveal round the body; 23 pale
grey base; 24 "ATECH PR-1" mark under it; 25 six countersunk screws from
below; 26 four rubber feet. Inside: 27 the T-slots and lips in every
divider and end rim; 28 the sealed wall between the cups and the console;
29 the thin cavity under the cups; 30 board pads; 31 end fences; 32 ribs
onto the board's spine; 33 a pad under the speaker's overhang; 34 four
screw bosses; 35 two base columns under the rims; 36 the key plunger;
37 a light pipe under the capsule.
Materials: warm-white shell, pale grey base, seven pastel lids (rose,
peach, butter, mint, sky, lavender, lilac), coral key and pill badge, black strip, tinted
window, frosted capsule, chrome screws, rubber feet.
Screws: ONE type, M2.5 countersunk thread-forming (4 x M2.5 x 13 console,
2 x M2.5 x 15 tray rims), no inserts.
MEASURED (R990, 2026-11-17): ./check CHECK PASS, run_seconds 12.7 s, wall 30 s; every RESTYLE end CHECK PASS.
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
    "Shell", "Bezel", "Screen_Window", "Glow_Window", "Key_Taken", "Pill_Badge",
    "Lid_1", "Lid_2", "Lid_3", "Lid_4", "Lid_5", "Lid_6", "Lid_7",
    "Rubber_1", "Rubber_2", "Rubber_3", "Rubber_4",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4", "Screw_5", "Screw_6"],
    # the TAKEN cap presses its button through its opening (a declared cover)
    "covers": {"Key_Taken": "button_p11"}}
REVIEW_CLOSEUPS = ["Key_Taken", "Lid_1", "Glow_Window"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them and the measured hardware.
LENGTH = 222.0     # RESTYLE 188..256 length: the tray and the console, left to right (x)
POCKET_L = 46.0    # RESTYLE 39..53 length: each compartment front to back (y)
PZ = 28.0          # RESTYLE 23.8..32.2 height: the tray top (the board and the hump follow it)
CORNER = 16.0      # RESTYLE 13.6..18.4 radius: the footprint's plan corners
WALL = 2.4         # RESTYLE 2.0..2.8 wall
# end RESTYLE
DAYS = ("M", "T", "W", "T", "F", "S", "S")
RIM_S, RIM_F = 9.0, 5.0    # the tray's end rims (screws go up through them) / front rim
DIV = 5.0                  # a divider: two 1.7 mm T-slots and a 1.6 mm core
LID_T = 3.4                # the lid (flush with the tray top)
TONGUE, SLOT_CL = 1.5, 0.2 # the lid's tongue into each slot / clearance all round it
LIP = 1.6                  # the lip over each tongue
SCOOP = 5.0                # the cups' scooped floor radius
CAV_T = 2.6                # the cavity under the cups (the split is in it)
RUB = 1.5                  # rubber feet
AIR = 1.4                  # the deck's inner face over the front row (button 10.04)
STEP = 16.0                # the raked step's run (y), knee to crest
EDGE_R, FOOT_R = 3.0, 1.2
WINDOW, BEZEL, RECESS = (34.0, 15.0), 2.0, 1.0
KEY = (26.0, 17.0)         # the pill-shaped TAKEN key
GLOW = (30.0, 12.0)        # the frosted capsule over lights 9 + 10
GRILLE_D = 32.0
SCREW = "M2.5"
COLOURS = {"Shell": "#f3efe8", "Base": "#cfd3d4", "Key": "coral",
           # one soft pastel per day, Monday to Sunday
           "Lid_1": "#f6b8b3", "Lid_2": "#f8d2a6", "Lid_3": "#f3e49c", "Lid_4": "#bfe3bf",
           "Lid_5": "#b4d9ee", "Lid_6": "#c8c1ec", "Lid_7": "#e8bddf",
           "Screen_Window": "#7f97a6", "Bezel": "matte_black", "Glow_Window": "frosted",
           "Rubber": "rubber", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
FLAT = Rotation(Vector(1, 0, 0), 90)
ACROSS = Rotation(Vector(0, 0, 1), -90).multiply(FLAT)    # long side along X, ports 9-14 at the front (-Y)
Z_PCB = PZ - WALL - AIR - 10.04                            # the PCB top: the front row 1.4 under the deck
board = ap.board_object(doc)
board.Placement = Placement(V(), ACROSS)
_b = ap.bbox(board)
board.Placement = Placement(V(-(_b.XMin + _b.XMax) / 2, -(_b.YMin + _b.YMax) / 2, Z_PCB - 2.5 - _b.ZMin), ACROSS)
scr = ap.seat(doc, "screen", (13, 14))        # front left (12 is reserved in the SDK)
key = ap.seat(doc, "button", 11)              # front, right of the screen: TAKEN
led_a = ap.seat(doc, "light", 10)             # front right: the two reminder lights
led_b = ap.seat(doc, "light", 9)              #   under one capsule
spk = ap.seat(doc, "speaker", (1, 2))         # back right: the chime, overhanging the back edge
usb = ap.seat(doc, "usbc", 4)                 # back, mouth +Y
tick("hardware")

BB, SB, KB, LA, LB, PB, UB = [ap.bbox(o) for o in (board, scr, key, led_a, led_b, spk, usb)]
for nm, b in (("board", BB), ("screen", SB), ("key", KB), ("light10", LA), ("light9", LB), ("speaker", PB),
              ("usb", UB)):
    print("BOX %-7s x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (nm, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def centre(b):
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


def zbox(w, d, r, cx, cy, z0, z1):
    return cad.rounded_box(w, d, z1 - z0, r, at=(cx - w / 2, cy - d / 2, z0))


def yprism(x0, x1, z0, z1, r, y0, y1):
    """A rounded rectangle in (x, z) extruded along Y from y0 to y1."""
    w = cad.rounded_rect_wire(x1 - x0, z1 - z0, r, ((x0 + x1) / 2, y0, (z0 + z1) / 2), "Y")
    s = Part.Face(w).extrude(V(0, y1 - y0, 0))
    if s.Volume < 0:
        s.reverse()
    return s


def insert(shell, cutter):
    """(shell with the opening, the piece that fills it exactly)."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, piece


def section_x(pts, x0, x1):
    """A (y, z) polygon extruded along X from x0 to x1 (lines only)."""
    f = Part.Face(Part.makePolygon([V(x0, y, z) for y, z in pts + pts[:1]]))
    s = f.extrude(V(x1 - x0, 0, 0))
    if s.Volume < 0:
        s.reverse()
    return s


def inset(pts, t):
    """The (y, z) polygon (counter-clockwise) moved t inward: every edge
    offset along its inner normal, neighbours intersected (lines only)."""
    n = len(pts)
    lines = []
    for i in range(n):
        (y0, z0), (y1, z1) = pts[i], pts[(i + 1) % n]
        dy, dz = y1 - y0, z1 - z0
        L = math.hypot(dy, dz)
        lines.append(((y0 - dz / L * t, z0 + dy / L * t), (dy, dz)))
    out = []
    for i in range(n):
        (p, d), (q, e) = lines[i - 1], lines[i]
        det = d[0] * (-e[1]) + e[0] * d[1]
        s = ((q[0] - p[0]) * (-e[1]) + e[0] * (q[1] - p[1])) / det
        out.append((p[0] + s * d[0], p[1] + s * d[1]))
    return out


# ------------------------------------------------------------ the frame
FR_Y0, FR_Y1 = min(SB.YMin, KB.YMin, LA.YMin), max(SB.YMax, KB.YMax, LA.YMax)   # the front row
YCAV = FR_Y0 - 0.6                       # the console cavity's front face
YPK1 = YCAV - WALL                       # the cups' back face: the sealed wall between
YP0 = YPK1 - POCKET_L                    # the cups' front face
YF = YP0 - RIM_F                         # the front edge
YB = PB.YMax + 0.5 + WALL                # the back edge, behind the speaker's overhang
YK = FR_Y1 + 2.5                         # the knee: the flat deck ends behind the front row
YH = YK + STEP                           # the crest of the raked step
HB = PB.ZMax + 1.2 + WALL                # the hump over the speaker
FLOOR = RUB + WALL                       # the base's inner floor
Z_PB = FLOOR + CAV_T + WALL              # the cups' floor
X1 = LENGTH / 2
SEC = [(YF, RUB), (YB, RUB), (YB, HB), (YH, HB), (YK, PZ), (YF, PZ)]
print("BODY %.0f x %.0f, tray %.1f, hump %.1f, PCB top %.2f, cups %.1f deep" % (
    LENGTH, YB - YF, PZ, HB, Z_PCB, PZ - LID_T - Z_PB))


def footprint(t, z0, z1):
    w = cad.rounded_rect_wire(LENGTH - 2 * t, YB - YF - 2 * t, CORNER - t, (0, (YF + YB) / 2, z0), "Z")
    return Part.Face(w).extrude(V(0, 0, z1 - z0))


outer = section_x(SEC, -X1 - 1, X1 + 1).common(footprint(0, RUB - 1, HB + 1))
outer = cad.soften(outer, EDGE_R, [e for e in outer.Edges if e.BoundBox.ZMin > PZ - 1e-3])
outer = cad.soften(outer, FOOT_R, [e for e in outer.Edges if e.BoundBox.ZMax < RUB + 1e-3])
skin = section_x(inset(SEC, 0.5), -X1, X1).common(footprint(0.5, RUB, HB))
# ONE core: the console, and a thin cavity under the cups (the tray block
# above it stays solid - the cups are cut into it, each with a floor)
core = section_x(inset(SEC, WALL), -X1, X1).common(footprint(WALL, RUB, HB))
core = cad.cut(core, box(-X1 - 5, X1 + 5, YF - 5, YCAV, Z_PB - WALL, HB + 5))
body = cad.cut(outer, core)
tick("body")
SPLIT = FLOOR + 0.6
base, shell = cad.split(body, "Z", at=SPLIT, lip=1.2)
tick("split")

# the fixed base holds the board: pads 0.1 mm under it, fences off its
# ends, a pad 0.1 mm under the speaker's overhang (all below the modules'
# slide corridors)
UNDER = BB.ZMin - 0.1
pads = [box(x - 4, x + 4, y - 4, y + 4, FLOOR - 0.5, UNDER)
        for x in (BB.XMin + 10, 0.0, BB.XMax - 10) for y in (-22.0, 22.0)]
pads += [box(BB.XMin - 1.8, BB.XMin - 0.3, y0, y0 + 6, FLOOR - 0.5, Z_PCB - 0.8) for y0 in (-17.0, 11.0)]
pads += [box(BB.XMax + 0.3, BB.XMax + 1.8, y0, y0 + 6, FLOOR - 0.5, Z_PCB - 0.8) for y0 in (-17.0, 11.0)]
pads.append(box(PB.XMin + 5, PB.XMax - 5, BB.YMax + 3, PB.YMax - 5, FLOOR - 0.5, PB.ZMin - 0.1))
base = cad.fuse_one(base, *pads)
# board retention: ribs from the raked step down onto the spine (0.2 mm off)
top_solid = section_x(SEC, -X1, X1)
shell = cad.fuse_one(shell, *[box(x - 2, x + 2, -6, 6, BB.ZMax + 0.2, HB).common(top_solid) for x in (-30.0, 10.0)])


def first_above(shape, x, y, z0):
    """The first surface of `shape` straight above (x, y, z0)."""
    s = shape.section(Part.makeLine(V(x, y, z0), V(x, y, z0 + 300)))
    return min(v.Point.z for v in s.Vertexes)


# six M2.5 screws from below: four into bosses hanging from the console's
# deck (cad.screw_through), two up into the tray's end rims - the cavity
# under the cups is too thin for a boss there, so a short column stands on
# the base (up to 0.1 mm under the rim) and the thread-forming pilot is
# drilled up into the rim's solid
SX_C = X1 - 14.0
SCREWS = [(-SX_C, -18.0), (SX_C, -18.0), (-(X1 - 26.0), YB - 11.0), (X1 - 26.0, YB - 11.0)]
screws = []
D_S = float(SCREW[1:])
for x, y in SCREWS:
    reach = first_above(shell, x, y, FLOOR + 0.1) - (FLOOR + 0.1)
    base, shell = cad.screw_through(base, shell, (x, y, RUB), size=SCREW, ribs=0)
    L = int(min(WALL + 0.85 * reach, WALL + 0.1 + min(reach, 4 * D_S + 1.0) - 0.3))
    screws.append(cad.screw("csk_phillips", SCREW, L, at=(x, y, RUB), axis="+Z"))
SX_T = X1 - WALL - 3.3
for x in (-SX_T, SX_T):
    y = YF + CORNER + 1.0                     # behind the plan corner, where the lip runs straight
    base = cad.fuse_one(base, cyl(1.1 * D_S, (x, y, FLOOR - 0.5), (Z_PB - WALL - 0.1) - (FLOOR - 0.5)))
    base = cad.countersink(base, (x, y, RUB), "+Z", 2.9, 4.9, through=True)
    shell = cad.hole(shell, (x, y, Z_PB - WALL), "+Z", 2.1, depth=4 * D_S + 1.0)
    screws.append(cad.screw("csk_phillips", SCREW, int(Z_PB - WALL + 4 * D_S + 1.0 - 0.3 - RUB), at=(x, y, RUB),
                            axis="+Z"))
tick("base + screws")

# ------------------------------------------------------------ the tray: cups, T-slots, lids
PW = (LENGTH - 2 * RIM_S - 6 * DIV) / 7.0          # each cup's width
CUPS = [-X1 + RIM_S + PW / 2 + k * (PW + DIV) for k in range(7)]
Z_LID = PZ - LID_T                                  # the lids' underside = the slot floors
cutters = []
for cx in CUPS:
    a, b = cx - PW / 2, cx + PW / 2
    cup = zbox(PW, POCKET_L, 3.0, cx, (YP0 + YPK1) / 2, Z_PB, Z_LID + 0.5)
    cup = cad.soften(cup, min(SCOOP, PW / 2 - 1.0, Z_LID - Z_PB - 1.0),
                     [e for e in cup.Edges if e.BoundBox.ZMax < Z_PB + 1e-3 and e.BoundBox.XLength > PW - 7])
    cutters.append(cup)
    cutters.append(box(a - SLOT_CL, b + SLOT_CL, YF - 3, YPK1, Z_LID, PZ + 2))       # the lid's well
    cutters.append(box(a - TONGUE - SLOT_CL, b + TONGUE + SLOT_CL, YF - 3, YPK1, Z_LID, PZ - LIP))  # T-slots
    # a finger notch in the front rim under the lid's front edge (flat facets)
    nf = Part.Face(Part.makePolygon([V(cx - 7.0, YF - 2, Z_LID + 0.5), V(cx + 7.0, YF - 2, Z_LID + 0.5),
                                     V(cx + 3.5, YF - 2, Z_LID - 4.0), V(cx - 3.5, YF - 2, Z_LID - 4.0),
                                     V(cx - 7.0, YF - 2, Z_LID + 0.5)]))
    cutters.append(nf.extrude(V(0, 4.5, 0)))
shell = cad.cut(shell, cutters)
tick("cups")

lids = []
for k, cx in enumerate(CUPS):
    a, b = cx - PW / 2, cx + PW / 2
    y1 = YPK1 - SLOT_CL
    lid = cad.fuse_one(box(a, b, YF, y1, Z_LID, PZ),
                       box(a - TONGUE, a + 0.5, YF, y1, Z_LID, PZ - LIP - SLOT_CL),
                       box(b - 0.5, b + TONGUE, YF, y1, Z_LID, PZ - LIP - SLOT_CL))
    lid = cad.soften(lid, EDGE_R, [e for e in lid.Edges if e.BoundBox.YMax < YF + 1e-3 and e.BoundBox.ZMin > PZ - 1e-3])
    lid = cad.soften(lid, 0.6, [e for e in lid.Edges if e.BoundBox.ZMin > PZ - 1e-3 and e.BoundBox.YLength > 5])
    lids.append(lid)

# ------------------------------------------------------------ the console face
# ONE black control strip set RECESS into the deck over the whole front
# row (an insert that fills its opening exactly); the screen window, the
# key and the glow are cut through IT
sx, sy, _sz = centre(SB)
SX0, SX1 = SB.XMin - 2.5, LB.XMax + 2.5
SY0, SY1 = YCAV + 0.4, FR_Y1 + 0.6
shell, panel = insert(shell, zbox(SX1 - SX0, SY1 - SY0, 4.0, (SX0 + SX1) / 2, (SY0 + SY1) / 2, PZ - WALL - 1, PZ + 1))
panel = panel.cut(box(-300, 300, -300, 300, PZ - RECESS, PZ + 2))
# the TAKEN key: a pill-shaped cap through the strip, its flange 0.9 mm
# under the deck, a plunger to 0.16 mm off the button
kx, ky, _kz = centre(KB)
base_z = PZ - WALL - 0.9
KT = PZ + 1.8                                   # the key's flat top
KH = KT - base_z
cap = cad.rounded_box(KEY[0], KEY[1], KH, KEY[1] / 2, at=(kx - KEY[0] / 2, ky - KEY[1] / 2, base_z))
cap = cad.soften(cap, 0.8, [e for e in cap.Edges if e.BoundBox.ZMin > KT - 1e-3])
fl = cad.rounded_box(KEY[0] + 1.6, KEY[1] + 1.6, 0.8, KEY[1] / 2 + 0.8,
                     at=(kx - KEY[0] / 2 - 0.8, ky - KEY[1] / 2 - 0.8, base_z))
panel = cad.opening_for(panel, cap, clearance=0.25, chamfer=0.4, axis="+Z")
cap = cad.fuse_one(cap, fl, cyl(3.0, (kx, ky, KB.ZMax + 0.16), base_z - (KB.ZMax + 0.16) + 0.5))
# the screen: a clear, lightly tinted window in the strip (it shows the screen from the hero view)
panel, window = insert(panel, zbox(WINDOW[0], WINDOW[1], 3.0, sx, sy, PZ - WALL - 2, PZ + 2))
# the reminder glow: a frosted capsule through the strip over both
# lights, its light pipe down to 0.5 mm off them
gx = (LA.XMin + LB.XMax) / 2
gy = (LA.YMin + LA.YMax) / 2
panel, glow = insert(panel, zbox(GLOW[0], GLOW[1], GLOW[1] / 2 - 0.01, gx, gy, PZ - WALL - 1, PZ + 1))
glow = cad.fuse_one(glow, zbox(GLOW[0] - 1.0, GLOW[1] - 1.0, GLOW[1] / 2 - 0.51, gx, gy,
                               max(LA.ZMax, LB.ZMax) + 0.5, PZ - WALL + 0.5))
# the chime: a round grille in the hump over the speaker
px, py, _pz = centre(PB)
shell = cad.speaker_grille(shell, (px, py, HB), (0, 0, 1), GRILLE_D, ring_pitch=2.6, hole=1.6)
# USB-C in the back wall: a pocket brings the wall to 1.3 mm off the
# mouth, a liner round it, then the measured opening
ux, uz = (UB.XMin + UB.XMax) / 2, Z_PCB + 5.9
pocket = yprism(ux - 6.5, ux + 6.5, uz - 5.0, uz + 5.0, 3, UB.YMax + 1.3, YB + 5)
liner = cad.cut(yprism(ux - 8.5, ux + 8.5, max(uz - 7.5, SPLIT + 1.6), uz + 7.5, 4, UB.YMax + 0.25, YB + 2), pocket)
shell = cad.fuse_one(cad.cut(shell, pocket), liner.common(skin))
shell = cad.socket_opening(shell, usb, margin=1.5)
tick("stage A")


# === STAGE B: details ===
# the day letters and grip ridges on the lids
LETTER = min(12.0, 0.45 * PW)
for k, (lid, d) in enumerate(zip(lids, DAYS)):
    cx = CUPS[k]
    lid = cad.fuse_one(lid, *[box(cx - 0.3 * PW, cx + 0.3 * PW, YF + 5 + 2.2 * i, YF + 5.8 + 2.2 * i, PZ - 0.3, PZ + 0.6)
                              for i in range(3)])
    lids[k] = cad.text(lid, d, (cx, (YP0 + YPK1) / 2 + 3.0, PZ), (0, 0, 1), LETTER, depth=0.5, mode="emboss",
                       up=(0, 1, 0))
# a tick on the key, ATECH on the raked step

def stroke(p, q, w, z0, z1):
    """A round-ended bar from p to q (x, y), w wide, z0..z1."""
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    s = cad.rounded_box(L + w, w, z1 - z0, w / 2 - 0.01, at=(-w / 2, -w / 2, z0))
    s.rotate(V(0, 0, 0), V(0, 0, 1), math.degrees(math.atan2(q[1] - p[1], q[0] - p[0])))
    s.translate(V(p[0], p[1], 0))
    return s


# a raised tick on the key (2.2 mm strokes print clean; letters this
# small leave sub-0.8 mm walls)
s_ = 0.32 * KEY[1]
tick_a, tick_b, tick_c = (kx - 1.2 * s_, ky + 0.1 * s_), (kx - 0.35 * s_, ky - 0.75 * s_), (kx + 1.2 * s_, ky + 0.8 * s_)
cap = cad.fuse_one(cap, stroke(tick_a, tick_b, 2.2, KT - 0.3, KT + 0.6), stroke(tick_b, tick_c, 2.2, KT - 0.3, KT + 0.6))
_n = V(0, -(HB - PZ), STEP)
_n.normalize()
shell = cad.text(shell, "ATECH", (-40.0, (YK + YH) / 2, (PZ + HB) / 2), (_n.x, _n.y, _n.z), 5.0, depth=0.5,
                 mode="deboss", up=(0, STEP, HB - PZ))
# a coral pill badge on the hump, the grille's mirror image: a capsule
# through the wall (an insert that fills its opening), 0.5 mm proud, its
# two halves split by a groove


def capsule(z0, z1):
    c = cad.rounded_box(34.0, 13.0, z1 - z0, 6.49, at=(-17.0, -6.5, z0))
    c.rotate(V(0, 0, 0), V(0, 0, 1), 30.0)
    c.translate(V(-px, py, 0))
    return c


shell, badge = insert(shell, capsule(HB - WALL - 1, HB + 1))
badge = cad.fuse_one(badge, capsule(HB - 0.3, HB + 0.5))
_g = box(-0.5, 0.5, -10, 10, HB + 0.1, HB + 1)
_g.rotate(V(0, 0, 0), V(0, 0, 1), 30.0)
_g.translate(V(-px, py, 0))
badge = cad.cut(badge, _g)
# the parting-line reveal, a model mark under the base, rubber feet
shell = cad.groove_ring(shell, "Z", SPLIT + 2.0, w=0.8, depth=0.6)
base = cad.text(base, "ATECH PR-1  WEEKLY PILL REMINDER", (0.0, (YF + YB) / 2, RUB), (0, 0, -1), 4.0, depth=0.4,
                mode="deboss", up=(0, -1, 0))
FEET = [(x, y) for x in (-(X1 - 18.0), X1 - 18.0) for y in (YF + 18.0, YB - 18.0)]
base = cad.fuse_one(base, *[cyl(6.0, (x, y, FLOOR - 0.5), 1.5) for x, y in FEET])
rubbers = []
for x, y in FEET:
    base = cad.cut(base, cyl(5.1, (x, y, RUB - 1), 2.2))
    rubbers.append(cad.foot(10, RUB + 1.2, style="dome", at=(x, y, RUB + 1.2)))
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    return o


o = part("Shell", shell)
o.ViewObject.ShapeColor = cad.color(COLOURS["Shell"])
o = part("Base", base)
o.ViewObject.ShapeColor = cad.color(COLOURS["Base"])
o = part("Key_Taken", cap)
o.ViewObject.ShapeColor = cad.color(COLOURS["Key"])
o = part("Bezel", panel)
o.ViewObject.ShapeColor = cad.color(COLOURS["Bezel"])
o = part("Screen_Window", window)
o.ViewObject.ShapeColor = cad.color(COLOURS["Screen_Window"])
o.ViewObject.Transparency = cad.transparency("glass")
o = part("Pill_Badge", badge)
o.ViewObject.ShapeColor = cad.color(COLOURS["Key"])
o = part("Glow_Window", glow)
o.ViewObject.ShapeColor = cad.color(COLOURS["Glow_Window"])
o.ViewObject.Transparency = cad.transparency("frosted")
o = part("Lid_1", lids[0])
o.ViewObject.ShapeColor = cad.color(COLOURS["Lid_1"])
o = part("Lid_2", lids[1])
o.ViewObject.ShapeColor = cad.color(COLOURS["Lid_2"])
o = part("Lid_3", lids[2])
o.ViewObject.ShapeColor = cad.color(COLOURS["Lid_3"])
o = part("Lid_4", lids[3])
o.ViewObject.ShapeColor = cad.color(COLOURS["Lid_4"])
o = part("Lid_5", lids[4])
o.ViewObject.ShapeColor = cad.color(COLOURS["Lid_5"])
o = part("Lid_6", lids[5])
o.ViewObject.ShapeColor = cad.color(COLOURS["Lid_6"])
o = part("Lid_7", lids[6])
o.ViewObject.ShapeColor = cad.color(COLOURS["Lid_7"])
for i, sh in enumerate(rubbers):
    o = part("Rubber_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Rubber"])
for i, sh in enumerate(screws):
    o = part("Screw_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Screw"])
print("SIZE", cad.measure(Part.makeCompound([shell, base] + lids + rubbers))["size"])
print("TOTAL %.1f s" % (time.time() - T0))
