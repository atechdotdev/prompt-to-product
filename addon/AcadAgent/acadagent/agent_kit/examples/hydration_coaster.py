"""Example: "a coaster for my water bottle that glows when I forget to drink" - a white puck that weighs your bottle and pulses an aqua halo when you have not drunk for a while.

fork this file for a drink coaster / smart coaster / bottle base / cup warmer pad (a low round puck,
a floating seat on a load cell, a glowing ring, a small display); change PARAMETERS and the outlines.
ARCHETYPE: drink coaster

How it is built (R1030):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board FLAT and turned ACROSS (long side left to right, modules up),
    11 mm behind the puck's centre so the front keeps a wide chin; the
    seat, its halo and the deck are centred on the BOARD, the outer circle
    on the puck. THE LOAD PATH: an 80 x 12.7 x 12.7 single-point bar load
    cell lies along the board's raised spine (0.8 mm over it, between the
    front and back module rows); its FIXED end (right) is screwed (2 x M4
    from above) to a spacer under the deck, its FREE end (left) carries the
    seat's post, which drops through a clearance hole in the deck (2 x M4
    from the seat, under the mat). The seat floats 1.2 mm over the deck:
    it touches nothing but the bar, and the deck is its overload stop. The
    amplifier (load_cell, 2) sits in the back row beside the fixed end.
    The four corner lights (1, 6, 9, 14) sit at r 54 from the seat's axis
    under the frosted halo ring round the seat (a ring rib thickens the
    deck under its recess; a tab through the deck and a light pipe over
    each light). The screen (cabled from 10 + 11) and the snooze button
    (cabled from 13) lie flat 22 mm in front of the board under the sloped
    chin, their ribbons straight out of the front edge (no twist), each
    between two holder ribs; a smoked window block over the screen, a
    press cap over the button. USB-C (4) in the back row, mouth +Y, at the
    end of a pocket with a liner through the back wall. The body: a
    cylinder under an oblique ruled cone (the outer circle to the deck
    circle round the seat), hollowed with its own core and split low into
    the fixed Base (pads and fences under the board, holder ribs) and the
    Top; four M4 screws from below into heat-set insert pockets in bosses
    hanging from the deck; ribs from the deck onto the spine beside the bar.
  * STAGE B - details: the seat's drip lip and its silicone mat with two
    drip grooves and a raised bottle ring, the "SIP" legend under the key,
    an aqua drop badge inlaid in the chin between the key and the window,
    a model mark under the base, rubber feet.
DETAILS (visible, 22): 1 a 155 mm round puck; 2 rolled edge between the side
and the rim; 3 the rim sloping down from the seat to the edge (an oblique
cone, steeper at the back); 4 the wide front chin; 5 the floating seat, a
glowing shadow gap under it; 6 the seat's raised drip lip; 7 rounded lip
edge; 8 aqua silicone mat in the dish; 9 two drip grooves in the mat; 10 a
raised bottle ring on the mat; 11 frosted aqua halo ring standing 1.5 mm
proud round the seat; 12 smoked screen window on the sloped chin; 13 its
aqua bezel; 14 the aqua snooze cap, its top following the slope; 15 "SIP"
legend under it; 16 an aqua water-drop badge inlaid in the chin, 0.5 mm
proud; 17 the parting line between the white shell and the base; 18 the
aqua-grey base band; 19 USB-C pocket with a
liner in the back; 20 "ATECH WR-1" under the base; 21 four countersunk
screws from below; 22 four rubber feet. Inside: 23 the bar load cell with
its binocular hole; 24 the fixed-end spacer under the deck; 25 the seat's
post; 26 the post's clearance hole (overload stop); 27 the halo's ring rib,
tabs and four light pipes; 28 board pads and end fences; 29 ribs onto the
spine; 30 holder ribs either side of the screen and the button; 31 the
key's plunger; 32 screw bosses with M4 insert pockets.
Materials: matte-white top and seat, aqua-grey base, frosted aqua halo,
aqua mat, key, bezel and drop badge, smoked window, aluminium load cell, chrome screws,
rubber feet.
Screws: ONE type, M4 countersunk (4 x M4 x 10 case, 2 x M4 x 12 load cell
fixed end, 2 x M4 x 16 seat) + 4 M4 heat-set inserts.
Left out: the speaker (a 40 x 40 x 20 module): beside the board it does
not fit a puck this size, under the board it doubles the height. The halo
pulse is the reminder.
MEASURED (R1030, 2026-11-20): ./check CHECK PASS, run_seconds 11 s, wall 39 s (26 s / 89 s on a loaded machine); every RESTYLE end CHECK PASS.
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
    "Top", "Halo_Ring", "Bezel", "Screen_Window", "Snooze_Key", "Drop_Badge", "Load_Cell_Bar", "Seat", "Seat_Mat",
    "Rubber_1", "Rubber_2", "Rubber_3", "Rubber_4",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4", "Screw_5", "Screw_6", "Screw_7", "Screw_8"],
    # the snooze cap presses its button through its opening (a declared cover)
    "covers": {"Snooze_Key": "button_13"}}
# the library's straight lead out of a cabled screen's socket runs through the
# screen mesh's own feet (2-12 mm3 by the mesh's parity test, 0 for the same
# lead in other orientations; the button's identical lead measures 0): a
# library limit, declared, not a design overlap
INTENDED_OVERLAPS = [("screen_10_11_cable_p10", "screen_10_11"), ("screen_10_11_cable_p11", "screen_10_11")]
REVIEW_CLOSEUPS = ["Halo_Ring", "Screen_Window", "Snooze_Key"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them and the measured hardware.
RIM_DROP = 7.0     # RESTYLE 5.9..8.1 height: the rim's fall from the deck to the rolled edge
EDGE_R = 4.0       # RESTYLE 3.4..4.6 radius: the rolled edge between the side and the rim
HALO_W = 8.0       # RESTYLE 6.8..9.2 width: the frosted halo ring round the seat
LIP_H = 1.6        # RESTYLE 1.35..1.85 height: the seat's drip lip over its dish
WALL = 2.5         # RESTYLE 2.1..2.9 wall
# end RESTYLE
R_OUT = 77.5       # the puck's radius (the board's corners sit at r 72 inside it)
Y_BOARD = 11.0     # the board's centre behind the puck's centre: the front chin
RUB = 1.5          # rubber feet under the base
PADS = 1.0         # board pads over the floor
SPINE_GAP = 0.8    # the bar over the board's spine
BAR = (80.0, 12.7, 12.7)   # the single-point bar load cell (5 kg class), l x w x h
BAR_GAP = 1.2      # the free end under the deck
BAR_X = 4.0        # the bar's shift toward its fixed end (its free end nearer the seat's axis)
POST_L = 24.0      # the seat's post along the bar's free end
GAP = 1.2          # the seat's float over the deck (its overload stop)
SEAT_R = 40.0      # the seat (dish) radius: an 80 mm seat
PT = 4.0           # the seat plate under the dish
PRIM = 4.0         # the lip's width round the dish
HALO_GAP = 1.5     # seat edge to the halo
HALO_UP = 1.5      # the halo's rise over the deck
RECESS = 1.2       # the halo's recess in the deck
FLAT_M = 1.0       # flat deck outside the halo before the rim falls
FOOT_R = 1.2
YGAP = 22.0        # the board's front edge to the cabled screen / button
WINDOW = (27.0, 15.0)
BEZEL = 1.5
KEY_D = 14.0
COLOURS = {"Top": "matte_white", "Base": "#9cc9c6", "Seat": "matte_white", "Seat_Mat": "#2ea59f",
           "Halo_Ring": "#8ff0e8", "Key": "#3cb7b0", "Bezel": "#3cb7b0", "Screen_Window": "smoked",
           "Load_Cell_Bar": "brushed_alu", "Rubber": "rubber", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
FLAT = Rotation(Vector(1, 0, 0), 90)
ACROSS = Rotation(Vector(0, 0, 1), -90).multiply(FLAT)    # long side along X, ports 9-14 at the front (-Y)
FLOOR = RUB + WALL                                         # the base's inner floor
Z_PCB = FLOOR + PADS + 2.5                                 # the PCB top
board = ap.board_object(doc)
board.Placement = Placement(V(), ACROSS)
_b = ap.bbox(board)
board.Placement = Placement(V(-(_b.XMin + _b.XMax) / 2, Y_BOARD - (_b.YMin + _b.YMax) / 2, Z_PCB - 2.5 - _b.ZMin),
                            ACROSS)
BB = ap.bbox(board)
CX, CY = 0.0, (BB.YMin + BB.YMax) / 2                      # the seat's axis: the board's centre
lights = [ap.seat(doc, "light", n) for n in (1, 6, 9, 14)]   # the four corners, under the halo
cell = ap.seat(doc, "load_cell", 2)                        # back row, beside the bar's fixed end
usb = ap.seat(doc, "usbc", 4)                              # back row, mouth +Y (the back)
# the screen and the snooze button lie flat YGAP in front of the board,
# their sockets pointing back at their plugs: straight, untwisted ribbons
Z_MOD = Z_PCB + 4.8
FRONT = BB.YMin - YGAP                                     # their back edges
scr, scr_ribs = ap.cable(doc, "screen", (10, 11), ap.module_placement(
    "screen", (CX + 20.0, FRONT - 9.75, Z_MOD), face="+Z", cable="+Y"))     # in line with ports 10 + 11
key_m, key_ribs = ap.cable(doc, "button", 13, ap.module_placement(
    "button", (CX - 30.0, FRONT - 9.75, Z_MOD), face="+Z", cable="+Y"))     # in line with port 13
tick("hardware")

SB, KB, UB, CB = [ap.bbox(o) for o in (scr, key_m, usb, cell)]
for nm, b in (("board", BB), ("screen", SB), ("key", KB), ("usb", UB), ("cell", CB)):
    print("BOX %-7s x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (nm, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def centre(b):
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


def zbox(w, d, r, cx, cy, z0, z1):
    return cad.rounded_box(w, d, z1 - z0, r, at=(cx - w / 2, cy - d / 2, z0))


def annulus(r0, r1, z0, z1, c=(CX, CY)):
    return cad.cut(cyl(r1, (c[0], c[1], z0), z1 - z0), cyl(r0, (c[0], c[1], z0 - 1), z1 - z0 + 2))


def insert(shell, cutter):
    """(shell with the opening, the piece that fills it exactly)."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, piece


# ------------------------------------------------------------ heights
SPINE_Z = BB.ZMax                                  # the spine's top
BZ0 = SPINE_Z + SPINE_GAP
BZ1 = BZ0 + BAR[2]
Z_D = BZ1 + BAR_GAP + WALL                         # the deck top round the seat
Z_EDGE = Z_D - RIM_DROP                            # the rim's foot (top of the side)
HALO_IN = SEAT_R + HALO_GAP
HALO_OUT = HALO_IN + HALO_W
R_FLAT = HALO_OUT + FLAT_M                         # the deck circle (round the seat's axis)
print("DECK z %.2f, edge z %.2f, bar z %.2f..%.2f" % (Z_D, Z_EDGE, BZ0, BZ1))


# ------------------------------------------------------------ the puck
def puck(t):
    """The side cylinder under an oblique ruled cone: the outer circle (the
    puck's axis) to the deck circle (the seat's axis), inset by t."""
    side = cyl(R_OUT - t, (0, 0, RUB + t), Z_EDGE - t - (RUB + t))
    w0 = Part.Wire(Part.makeCircle(R_OUT - t, V(0, 0, Z_EDGE - t)))      # dropped t: the slope's wall stays t
    w1 = Part.Wire(Part.makeCircle(R_FLAT - 0.3 * t, V(CX, CY, Z_D - t)))
    cone = Part.makeLoft([w0, w1], True, True)
    return cad.fuse_one(side, cone)


outer = puck(0.0)
outer = cad.soften(outer, EDGE_R, [e for e in outer.Edges if abs(e.BoundBox.ZMin - Z_EDGE) < 1e-3
                                   and abs(e.BoundBox.ZMax - Z_EDGE) < 1e-3])
outer = cad.soften(outer, 2.0, [e for e in outer.Edges if e.BoundBox.ZMin > Z_D - 1e-3])
outer = cad.soften(outer, FOOT_R, [e for e in outer.Edges if e.BoundBox.ZMax < RUB + 1e-3])
body = cad.hollow(outer, WALL, core=lambda t: puck(t))
skin = puck(0.5)
tick("body")
SPLIT = Z_PCB - 2.0
base, top = cad.split(body, "Z", at=SPLIT, lip=1.2)
tick("split")

# the fixed base holds the board: pads 0.1 mm under it, fences off its ends
UNDER = BB.ZMin - 0.1
pads = [box(x - 4, x + 4, y - 4, y + 4, FLOOR - 0.5, UNDER)
        for x in (BB.XMin + 10, 0.0, BB.XMax - 10) for y in (CY - 20.0, CY + 20.0)]
fences = [box(BB.XMin - 1.8, BB.XMin - 0.3, y0, y0 + 6, FLOOR - 0.5, Z_PCB - 0.8) for y0 in (CY - 24.0, CY + 18.0)]
fences += [box(BB.XMax + 0.3, BB.XMax + 1.8, y0, y0 + 6, FLOOR - 0.5, Z_PCB - 0.8) for y0 in (CY - 24.0, CY + 18.0)]
# holder ribs 0.25 mm off the left and right sides of the cabled screen and key
holders = []
for mb in (SB, KB):
    for x0, x1 in ((mb.XMin - 1.75, mb.XMin - 0.25), (mb.XMax + 0.25, mb.XMax + 1.75)):
        holders.append(box(x0, x1, mb.YMin + 2.0, mb.YMax - 2.0, FLOOR - 0.5, (mb.ZMin + mb.ZMax) / 2))
base = cad.fuse_one(base, *[p.common(skin) for p in pads + fences + holders])
# board retention: ribs from the deck down onto the spine, beside the bar
BY = CY
DECK_IN = Z_D - WALL
spine_ribs = [box(x - 2, x + 2, y0, y0 + 2.0, SPINE_Z + 0.2, DECK_IN + 0.5)
              for x in (-25.0, 25.0) for y0 in (BY - BAR[1] / 2 - 2.9, BY + BAR[1] / 2 + 0.9)]
top = cad.fuse_one(top, *spine_ribs)

# four M4 screws from below into insert pockets in columns hanging from the
# deck: every column in ONE fuse, every bore in ONE cut (R940: four
# screw_through calls on this lofted shell cost 13 s)
SPAD = RUB + 3.2                               # a floor pad under each screw: an M4 countersink at any WALL
XS = BB.XMax + 6.0                             # beyond the board's ends
FX = SB.XMax + 6.5                             # the front corners, beside the screen and the key
SCREWS = [(-XS, CY), (XS, CY), (-FX, FRONT - 1.0), (FX, FRONT - 1.0)]
INSERT_D, PILOT_D = 5.7, 3.4                   # M4 heat-set insert pocket (1.4 d + 0.1), thread-forming pilot
base = cad.fuse_one(base, *[cyl(5.5, (x, y, FLOOR - 0.5), SPAD - FLOOR + 0.5) for x, y in SCREWS])
cols, bores, csks, screws = [], [], [], []
for x, y in SCREWS:
    cols.append(cyl(INSERT_D / 2 + 1.2, (x, y, SPAD + 0.1), Z_D - SPAD).common(skin))
    bores.append(cyl(INSERT_D / 2, (x, y, SPAD), 8.6))
    bores.append(cyl(PILOT_D / 2, (x, y, SPAD + 8.0), 6.0))
    csks.append(Part.makeCone(8.2 / 2, 4.5 / 2, (8.2 - 4.5) / 2, V(x, y, RUB - 0.01), V(0, 0, 1)))
    csks.append(cyl(4.5 / 2, (x, y, RUB - 0.5), SPAD - RUB + 1.0))
    screws.append(cad.screw("csk_phillips", "M4", 10, at=(x, y, RUB), axis="+Z"))
top = cad.cut(cad.fuse_one(top, *cols), bores)
base = cad.cut(base, csks)
FEET = [(58.0 * math.cos(math.radians(a)), 58.0 * math.sin(math.radians(a))) for a in (60, 120, 240, 300)]
base = cad.fuse_one(base, *[cyl(6.0, (x, y, FLOOR - 0.5), 1.5) for x, y in FEET])
tick("base + screws")

# ------------------------------------------------------------ the load cell bar
BX0 = CX - BAR[0] / 2 + BAR_X                  # the free end (left)
BX1 = BX0 + BAR[0]                             # the fixed end (right)
bar = box(BX0, BX1, BY - BAR[1] / 2, BY + BAR[1] / 2, BZ0, BZ1)
bm, zm = (BX0 + BX1) / 2, (BZ0 + BZ1) / 2
bino = cad.fuse_one(cyl(4.0, (bm - 5.5, BY - 10, zm), 20, (0, 1, 0)), cyl(4.0, (bm + 5.5, BY - 10, zm), 20, (0, 1, 0)),
                    box(bm - 5.5, bm + 5.5, BY - 10, BY + 10, zm - 1.5, zm + 1.5))
bar = cad.cut(bar, bino)
FREE = [BX0 + 5.0, BX0 + 20.0]                 # the free end's tapped holes (seat screws)
FIXED = [BX1 - 10.0, BX1 - 22.0]               # the fixed end's (deck screws, heads inside the seat's shadow)
for x in FREE + FIXED:
    bar = cad.hole(bar, (x, BY, BZ1), "-Z", 3.4, depth=10)
# the fixed end: a spacer under the deck, two M4 from above
top = cad.fuse_one(top, box(BX1 - 25.0, BX1, BY - BAR[1] / 2, BY + BAR[1] / 2, BZ1, DECK_IN + 0.5))
fixed_screws = []
for x in FIXED:
    top = cad.countersink(top, (x, BY, Z_D), "-Z", 4.5, 8.2, through=True)
    fixed_screws.append(cad.screw("csk_phillips", "M4", 12, at=(x, BY, Z_D), axis="-Z"))

# ------------------------------------------------------------ the seat
PZ0 = Z_D + GAP
PZ1 = PZ0 + PT
seat = cyl(SEAT_R, (CX, CY, PZ0), PT + LIP_H)
post = box(BX0 + 0.5, BX0 + POST_L, BY - 4.5, BY + 4.5, BZ1, PZ0 + 0.5)
seat = cad.fuse_one(seat, post)
DISH_R = SEAT_R - PRIM
seat = cad.cut(seat, cyl(DISH_R, (CX, CY, PZ1), LIP_H + 1))
seat_screws = []
for x in FREE:
    seat = cad.countersink(seat, (x, BY, PZ1), "-Z", 4.5, 8.2, through=True)
    seat_screws.append(cad.screw("csk_phillips", "M4", 16, at=(x, BY, PZ1), axis="-Z"))
# the deck: a clearance hole round the post (the seat never touches the shell)
top = cad.cut(top, zbox(POST_L + 2.5, 9.0 + 3.0, 2.5, BX0 + 0.5 + POST_L / 2, BY, DECK_IN - 1, Z_D + 1))
tick("load path")

# ------------------------------------------------------------ the halo
# a ring rib under the halo keeps the deck thick under its recess; a tab
# through the deck over each light, a light pipe down to it
top = cad.fuse_one(top, annulus(HALO_IN - 1.5, HALO_OUT + 1.5, DECK_IN - 1.0, DECK_IN + 0.5).common(puck(WALL - 0.5)))


def sector(r0, r1, a_mid, half, z0, z1):
    n = 6
    pts = [V(CX + r1 * math.cos(math.radians(a_mid - half + 2 * half * i / n)),
             CY + r1 * math.sin(math.radians(a_mid - half + 2 * half * i / n)), z0) for i in range(n + 1)]
    pts += [V(CX + r0 * math.cos(math.radians(a_mid + half - 2 * half * i / n)),
              CY + r0 * math.sin(math.radians(a_mid + half - 2 * half * i / n)), z0) for i in range(n + 1)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, z1 - z0))


LIGHT_ANG = [math.degrees(math.atan2(c[1] - CY, c[0] - CX)) for c in (centre(ap.bbox(m)) for m in lights)]
cutters = [annulus(HALO_IN, HALO_OUT, Z_D - RECESS, Z_D + 1)]
cutters += [sector(HALO_IN, HALO_OUT, a, 10, DECK_IN - 2.0, Z_D - RECESS + 0.5) for a in LIGHT_ANG]
halo = cad.fuse_one(*[top.common(c) for c in cutters])
top = cad.cut(top, cutters)
halo = cad.fuse_one(halo, annulus(HALO_IN, HALO_OUT, Z_D - 0.5, Z_D + HALO_UP))
LT = max(ap.bbox(m).ZMax for m in lights)
pipes = []
for m, a in zip(lights, LIGHT_ANG):
    lb = ap.bbox(m)
    pipes.append(sector(HALO_IN + 0.1, HALO_OUT - 0.1, a, 9.5, LT + 0.5, DECK_IN - 0.5)
                 .common(box(lb.XMin, lb.XMax, lb.YMin, lb.YMax, LT, Z_D)))
halo = cad.fuse_one(halo, *pipes)
tick("halo")

# ------------------------------------------------------------ the chin: screen window and snooze key


def surface_z(x, y):
    """The top's outer surface over (x, y), measured with a ray."""
    return cad.measure(top.common(cyl(0.05, (x, y, Z_EDGE - 15.0), 40.0)))["bbox_max"][2]


def surface_n(x, y, h=2.0):
    """The outer surface's normal over (x, y), from four rays."""
    gx = (surface_z(x + h, y) - surface_z(x - h, y)) / (2 * h)
    gy = (surface_z(x, y + h) - surface_z(x, y - h)) / (2 * h)
    m = math.sqrt(gx * gx + gy * gy + 1.0)
    return (-gx / m, -gy / m, 1.0 / m)


sx, sy, _sz = centre(SB)
top, bezel = insert(top, zbox(WINDOW[0] + 2 * BEZEL, WINDOW[1] + 2 * BEZEL, 2.0 + BEZEL, sx, sy, SB.ZMax + 1.0,
                              Z_D + 1))
# the window: a smoked block from 0.5 mm over the screen up to the chin's surface
wcut = zbox(WINDOW[0], WINDOW[1], 2.0, sx, sy, SB.ZMax + 0.5, Z_D + 2)
bezel = cad.cut(bezel, wcut)
window = wcut.common(puck(0.0))
kx, ky, _kz = centre(KB)
kz_top = surface_z(kx, ky + KEY_D / 2) + 1.2                  # the cap's high (back) edge
kz_low = surface_z(kx, ky - KEY_D / 2) + 1.2                  # its low (front) edge
base_z = surface_z(kx, ky - KEY_D / 2 - 1.0) - WALL - 2.4      # under the low edge of the wall
cap = cad.button_cap(KEY_D, kz_top + 1.0 - base_z, dome=0.0, flange=0.8, at=(kx, ky, base_z), axis="+Z")
# the cap's top follows the slope of the chin, 1.2 mm proud
slope = (kz_top - kz_low) / KEY_D
plane = Part.Face(Part.makePolygon([V(kx - 20, ky - 20, kz_low + slope * (-20 + KEY_D / 2)),
                                    V(kx + 20, ky - 20, kz_low + slope * (-20 + KEY_D / 2)),
                                    V(kx + 20, ky + 20, kz_low + slope * (20 + KEY_D / 2)),
                                    V(kx - 20, ky + 20, kz_low + slope * (20 + KEY_D / 2)),
                                    V(kx - 20, ky - 20, kz_low + slope * (-20 + KEY_D / 2))]))
cap = cad.cut(cap, plane.extrude(V(0, 0, 20)))
top = cad.opening_for(top, cap, clearance=0.25, chamfer=0.4, axis="+Z")
key = cad.fuse_one(cap, cyl(3.0, (kx, ky, KB.ZMax + 0.16), base_z - (KB.ZMax + 0.16) + 0.5))
# USB-C in the back: a pocket brings the wall to 0.25 mm off the mouth
ux, uz = (UB.XMin + UB.XMax) / 2, Z_PCB + 5.9


def yprism(x0, x1, z0, z1, y0, y1, r):
    w = cad.rounded_rect_wire(x1 - x0, z1 - z0, r, ((x0 + x1) / 2, y0, (z0 + z1) / 2), "Y")
    return Part.Face(w).extrude(V(0, y1 - y0, 0))


pocket = yprism(ux - 6.5, ux + 6.5, uz - 5.0, uz + 5.0, UB.YMax + 1.3, R_OUT + 5, 3)
liner = yprism(ux - 8.5, ux + 8.5, max(uz - 7.5, SPLIT + 1.6), uz + 7.5, UB.YMax + 0.25, R_OUT + 2, 4).common(skin)
top = cad.cut(cad.fuse_one(top, liner), pocket)
top = cad.socket_opening(top, usb, margin=1.5)
tick("stage A")


# === STAGE B: details ===
# the seat: a rounded lip, the silicone mat with drip grooves and a bottle ring
seat = cad.soften(seat, 1.0, [e for e in seat.Edges if e.BoundBox.ZMin > PZ1 + LIP_H - 1e-3])
seat = cad.soften(seat, 0.8, [e for e in seat.Edges if abs(e.BoundBox.ZMin - PZ0) < 1e-3
                              and e.BoundBox.XLength > 2 * SEAT_R - 1])
MAT_T = LIP_H - 0.1
mat = cyl(DISH_R, (CX, CY, PZ1), MAT_T)
mat = cad.cut(mat, [annulus(r, r + 1.0, PZ1 + MAT_T - 0.4, PZ1 + MAT_T + 1) for r in (DISH_R - 6.0, 14.0)])
mat = cad.fuse_one(mat, annulus(26.0, 29.0, PZ1 + MAT_T - 0.3, PZ1 + MAT_T + 0.8))
# the key legend, a drop icon on the chin
ly = ky - KEY_D / 2 - 4.5
top = cad.text(top, "SIP", (kx, ly, surface_z(kx, ly)), surface_n(kx, ly), 3.5,
               depth=0.4, mode="deboss", up=(0, 1, 0))
r_ = 4.0
dx, dy = (KB.XMax + sx - WINDOW[0] / 2 - BEZEL) / 2, sy - 1.5   # between the key and the window


def drop_prism(z0, z1):
    """A water drop (point to the back), straight facets only."""
    pts = [V(dx, dy + 2 * r_, z0)] + [V(dx + r_ * math.cos(math.radians(a)), dy + r_ * math.sin(math.radians(a)), z0)
                                      for a in range(150, 391, 15)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, z1 - z0))


# an aqua drop badge through the chin (an insert), embossed 0.5 mm proud
dz = surface_z(dx, dy)
top, badge = insert(top, drop_prism(dz - WALL - 3.0, dz + 3.0))
badge = cad.fuse_one(badge, drop_prism(dz - 1.0, dz + 3.0).common(puck(-0.5)))
# under the base: a model mark, rubber feet
base = cad.text(base, "ATECH WR-1  5 kg", (0.0, -20.0, RUB), (0, 0, -1), 4.0, depth=0.4, mode="deboss",
                up=(0, -1, 0))
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


o = part("Top", top)
o.ViewObject.ShapeColor = cad.color(COLOURS["Top"])
o = part("Base", base)
o.ViewObject.ShapeColor = cad.color(COLOURS["Base"])
o = part("Seat", seat)
o.ViewObject.ShapeColor = cad.color(COLOURS["Seat"])
o = part("Seat_Mat", mat)
o.ViewObject.ShapeColor = cad.color(COLOURS["Seat_Mat"])
o = part("Load_Cell_Bar", bar)
o.ViewObject.ShapeColor = cad.color(COLOURS["Load_Cell_Bar"])
o = part("Halo_Ring", halo)
o.ViewObject.ShapeColor = cad.color(COLOURS["Halo_Ring"])
o.ViewObject.Transparency = cad.transparency("frosted")
o = part("Bezel", bezel)
o.ViewObject.ShapeColor = cad.color(COLOURS["Bezel"])
o = part("Screen_Window", window)
o.ViewObject.ShapeColor = cad.color(COLOURS["Screen_Window"])
o.ViewObject.Transparency = cad.transparency("smoked")
o = part("Drop_Badge", badge)
o.ViewObject.ShapeColor = cad.color(COLOURS["Key"])
o = part("Snooze_Key", key)
o.ViewObject.ShapeColor = cad.color(COLOURS["Key"])
for i, sh in enumerate(rubbers):
    o = part("Rubber_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Rubber"])
for i, sh in enumerate(screws + fixed_screws + seat_screws):
    o = part("Screw_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Screw"])
print("SIZE", cad.measure(Part.makeCompound([top, base, seat, mat] + rubbers))["size"])
print("TOTAL %.1f s" % (time.time() - T0))

