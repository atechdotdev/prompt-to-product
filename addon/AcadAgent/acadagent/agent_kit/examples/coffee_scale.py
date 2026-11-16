"""Example: "a pour-over coffee scale" - a slim matte-black slab with a floating heat-pad platform on a bar load cell.

fork this file for a kitchen / coffee / barista / parcel scale (a flat slab,
a platform on a load cell, a display and keys); change PARAMETERS and the outlines.
ARCHETYPE: coffee scale

How it is built (R940):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board FLAT and turned ACROSS (long side left to right, modules up)
    with ports 9-14 along the FRONT (left to right 14..9): the screen
    (13, 14) at the left under a smoked window in a recessed black bezel
    (11 + 12 would centre it, but the SDK reserves port 12), a copper
    coffee-drop badge over the empty port 12, the TARE key (11), the status
    light (10) under a frosted dot, the TIMER key (9); the load-cell
    amplifier (load_cell, 1) at the back right, USB-C (7) in a pocket with
    a liner in the right side. The slab
    is a rounded plan extruded (planes and cylinders only), hollowed with
    its own core and split low into the fixed Base (pads and fences under
    the board) and the Top; six M4 screws from below into heat-set insert
    pockets in bosses hanging from the deck; ribs from the deck onto the
    board's spine. THE LOAD PATH: a single-point bar load cell (80 x 12.7
    x 12.7 aluminium, the strain gauges over its binocular hole) lies
    behind the board, its FIXED end screwed from below (2 x M4) onto a
    pedestal on the base floor, its FREE end 1.5 mm over the floor; the
    platform's post drops through a clearance hole in the deck onto the
    free end (2 x M4 from above, under the pad). The platform floats
    1.5 mm over the deck: it touches nothing but the bar, and the deck is
    its overload stop. The bar's fixed end ends 1 mm from the amplifier:
    its 4-wire lead (not modelled) is a few mm long.
  * STAGE B - details: the drip groove round the platform, a centring
    ring in the pad, the copper coffee-drop badge (an insert, embossed), TARE / TIMER legends,
    the chamfered platform rim, the parting-line reveal, a model mark
    under the base, rubber feet.
RESTYLE (R425): SIDE / DEPTH (the slab's plan), PT (the platform plate),
CORNER, WALL; also STRIP, P_IN, GAP, PAD_D / PAD_UP, EDGE_R.
DETAILS (visible, 22 of 32): 1 slim slab 150 x 150 with 14 mm corners; 2
rolled top edge; 3 small foot round; 4 the floating platform, a shadow gap
under it; 5 chamfered platform rim; 6 silicone heat pad flush in a 4 mm
rim; 7 a centring ring in the pad for the dripper; 8 drip groove in the
deck round the platform; 9 smoked display window; 10 recessed black bezel;
11 TARE key; 12 TIMER key; 13 "TARE" / "TIMER" legends; 14 frosted status
dot; 15 copper coffee-drop badge, embossed 0.5 mm; 16 USB-C pocket with liner in the right
side; 17 parting-line reveal round the slab; 18 graphite base; 19 "ATECH
CS-1" mark under it; 20 six countersunk screws from below; 21 two more
holding the load cell; 22 four rubber feet. Inside: 23 the bar load cell
with its binocular hole; 24 its pedestal; 25 the platform post; 26 the
post's clearance hole (overload stop); 27 board pads; 28 end fences; 29
ribs onto the spine; 30 screw bosses with M4 insert pockets; 31 key
plungers; 32 a light pipe under the dot.
Materials: matte-black top, graphite base, brushed-aluminium platform, dark
silicone pad, copper keys and drop badge, smoked window, black bezel, frosted dot,
aluminium load cell, chrome screws, rubber feet.
Screws: ONE type, M4 countersunk (6 x M4 x 10 case, 2 x M4 x 16 platform,
2 x M4 x 12 load cell) + 6 M4 heat-set inserts.
MEASURED (R940, 2026-11-10): ./check CHECK PASS, model build 12.8 s (./check wall 45 s); RESTYLE sweep 10/10 ends CHECK PASS.
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
    "Top", "Bezel", "Screen_Window", "Status_Dot", "Drop_Badge", "Key_Tare", "Key_Timer", "Load_Cell_Bar",
    "Platform", "Heat_Pad", "Rubber_1", "Rubber_2", "Rubber_3", "Rubber_4",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4", "Screw_5", "Screw_6",
    "Screw_7", "Screw_8", "Screw_9", "Screw_10"],
    # each key presses its button through its opening (a declared cover)
    "covers": {"Key_Tare": "button_p11", "Key_Timer": "button_p9"}}
REVIEW_CLOSEUPS = ["Key_Tare", "Screen_Window", "Heat_Pad"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them and the measured hardware.
SIDE = 15.0        # RESTYLE 12.75..17.25 width: the slab past the board's ends (x; 150.8 overall at 15)
DEPTH = 150.0      # RESTYLE 127..173 length: the slab front to back (y)
PT = 5.0           # RESTYLE 4.2..5.8 height: the platform plate under the pad
CORNER = 14.0      # RESTYLE 11.5..16.5 radius: the slab's plan corners
WALL = 2.5         # RESTYLE 2.1..2.9 wall
# end RESTYLE
STRIP = 10.0       # the slab in front of the front-row modules
P_IN = 7.5         # the platform's inset from the slab's sides and back
GAP = 1.5          # the platform's float over the deck (its overload stop)
PAD_D, PAD_UP = 2.0, 1.0   # the pad's recess in the plate / how far it stands proud
PRIM = 4.0         # the aluminium rim round the pad
EDGE_R, FOOT_R = 3.5, 1.2
AIR = 1.2          # the deck's inner face over the tallest module (usbc 10.21)
RUB = 1.5          # rubber feet
BAR = (80.0, 12.7, 12.7)   # the single-point bar load cell (5 kg class), l x w x h
BAR_GAP = 1.5      # the free end over the floor
POST_L = 25.0      # the platform post / pedestal along the bar's ends
WINDOW, BEZEL, RECESS = (36.0, 16.0), 2.0, 1.0
KEY_D = 13.0
DOT_D = 8.0
COLOURS = {"Top": "matte_black", "Base": "graphite", "Platform": "brushed_alu", "Heat_Pad": "#2b2b2d",
           "Key": "copper", "Screen_Window": "smoked", "Bezel": "matte_black", "Status_Dot": "frosted",
           "Load_Cell_Bar": "brushed_alu", "Rubber": "rubber", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
FLAT = Rotation(Vector(1, 0, 0), 90)
ACROSS = Rotation(Vector(0, 0, 1), -90).multiply(FLAT)    # long side along X, ports 9-14 at the front (-Y)
Z_PCB = RUB + WALL + 4.0                                   # the PCB top
board = ap.board_object(doc)
board.Placement = Placement(V(), ACROSS)
_b = ap.bbox(board)
board.Placement = Placement(V(-(_b.XMin + _b.XMax) / 2, -(_b.YMin + _b.YMax) / 2, Z_PCB - 2.5 - _b.ZMin), ACROSS)
scr = ap.seat(doc, "screen", (13, 14))        # front left (12 is reserved in the SDK)
tare = ap.seat(doc, "button", 11)             # front, right of the screen
timer = ap.seat(doc, "button", 9)             # front right
led = ap.seat(doc, "light", 10)               # between the keys: status dot
cell = ap.seat(doc, "load_cell", 1)           # back right: the amplifier, next to the bar's fixed end
usb = ap.seat(doc, "usbc", 7)                 # right end, mouth +X
tick("hardware")

BB, SB, KT, KM, LB, CB, UB = [ap.bbox(o) for o in (board, scr, tare, timer, led, cell, usb)]
for nm, b in (("board", BB), ("screen", SB), ("tare", KT), ("timer", KM), ("light", LB), ("cell", CB), ("usb", UB)):
    print("BOX %-7s x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (nm, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def centre(b):
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


def zbox(w, d, r, cx, cy, z0, z1):
    return cad.rounded_box(w, d, z1 - z0, r, at=(cx - w / 2, cy - d / 2, z0))


def insert(shell, cutter):
    """(shell with the opening, the piece that fills it exactly)."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, piece


X1 = BB.XMax + SIDE
WIDTH = 2 * X1
Y0 = min(SB.YMin, KT.YMin, LB.YMin) - STRIP     # the front edge
Y1 = Y0 + DEPTH                                 # the back edge
Z_TOP = max(b.ZMax for b in (SB, KT, KM, LB, CB, UB)) + AIR + WALL
FLOOR = RUB + WALL                              # the base's inner floor
print("SLAB %.0f x %.0f, deck at z %.2f" % (WIDTH, DEPTH, Z_TOP))


# ------------------------------------------------------------ the slab
def slab(t):
    w = cad.rounded_rect_wire(WIDTH - 2 * t, DEPTH - 2 * t, max(CORNER - t, 0.6), (0, (Y0 + Y1) / 2, RUB + t), "Z")
    return Part.Face(w).extrude(V(0, 0, Z_TOP - RUB - 2 * t))


outer = slab(0.0)
outer = cad.soften(outer, EDGE_R, [e for e in outer.Edges if e.BoundBox.ZMin > Z_TOP - 1e-3])
outer = cad.soften(outer, FOOT_R, [e for e in outer.Edges if e.BoundBox.ZMax < RUB + 1e-3])
body = cad.hollow(outer, WALL, core=lambda t: slab(t))
skin = slab(0.5)
tick("body")
SPLIT = Z_PCB - 2.0
base, top = cad.split(body, "Z", at=SPLIT, lip=1.2)
tick("split")

# the fixed base holds the board: pads 0.1 mm under it, fences off its ends
UNDER = BB.ZMin - 0.1
pads = [box(x - 4, x + 4, y - 4, y + 4, FLOOR - 0.5, UNDER)
        for x in (BB.XMin + 10, 0.0, BB.XMax - 10) for y in (-22.0, 22.0)]
fences = [box(BB.XMin - 1.8, BB.XMin - 0.3, y0, y0 + 6, FLOOR - 0.5, Z_PCB - 0.8) for y0 in (-17.0, 11.0)]
fences += [box(BB.XMax + 0.3, BB.XMax + 1.8, y0, y0 + 6, FLOOR - 0.5, Z_PCB - 0.8) for y0 in (-17.0, 11.0)]
# the load cell: behind the board, the platform's centre over its middle,
# its fixed end (right, beside the amplifier) on a pedestal on the floor
PX, PY0, PY1 = X1 - P_IN, -4.0, Y1 - P_IN       # the platform's plan
PY0 = max(PY0, SB.YMax + BEZEL + 4.0)
BY = max((PY0 + PY1) / 2, CB.YMax + 19.5 + BAR[1] / 2 + 0.5)   # clear of the amplifier's slide corridor
BX0 = min(-BAR[0] / 2, CB.XMin - 1.0 - BAR[0])                 # the bar's left (free) end
BX1 = BX0 + BAR[0]
BZ0 = FLOOR + BAR_GAP
BZ1 = BZ0 + BAR[2]
print("BAR x %.1f..%.1f y %.1f z %.1f..%.1f (deck inner %.2f)" % (BX0, BX1, BY, BZ0, BZ1, Z_TOP - WALL))
pedestal = box(BX1 - POST_L, BX1, BY - BAR[1] / 2, BY + BAR[1] / 2, FLOOR - 0.5, BZ0)
base = cad.fuse_one(base, *[p.common(skin) for p in pads + fences] + [pedestal])
# board retention: ribs from the deck down onto the spine (0.2 mm off it)
SPINE_Z = BB.ZMax
top = cad.fuse_one(top, *[box(x - 2, x + 2, -6, 6, SPINE_Z + 0.2, Z_TOP - WALL + 0.5) for x in (-30.0, 10.0)])

# six M4 screws from below into insert pockets in bosses hanging from the deck
SX = BB.XMax + 0.6 + 4.4                       # the M4 boss (r 4.4) 0.6 mm off the board's ends
SPAD = RUB + 3.2                               # a floor pad under each screw: an M4 countersink at any WALL
SXB = X1 - WALL - 6.2                          # behind the board: the boss 0.2 mm off the base's lip
YB = BB.YMax + 4.4 + 3.0
SCREWS = [(-SX, -16.0), (-SXB, YB), (SX, -16.0), (SXB, YB), (-45.0, Y1 - WALL - 12.0), (45.0, Y1 - WALL - 12.0)]
base = cad.fuse_one(base, *[cyl(5.5, (x, y, FLOOR - 0.5), SPAD - FLOOR + 0.5) for x, y in SCREWS])
screws = []
for x, y in SCREWS:
    base, top = cad.screw_through(base, top, (x, y, RUB), size="M4", ribs=0)
    top = cad.cut(top, cyl(2.85, (x, y, SPAD + 0.05), 8.5))       # the heat-set insert pocket, open below
    screws.append(cad.screw("csk_phillips", "M4", 10, at=(x, y, RUB), axis="+Z"))
FEET = [(x, y) for x in (-(X1 - 15.0), X1 - 15.0) for y in (Y0 + 13.0, Y1 - 15.0)]
base = cad.fuse_one(base, *[cyl(6.0, (x, y, FLOOR - 0.5), 1.5) for x, y in FEET])
tick("base + screws")

# ------------------------------------------------------------ the load cell bar
bar = box(BX0, BX1, BY - BAR[1] / 2, BY + BAR[1] / 2, BZ0, BZ1)
bm, zm = (BX0 + BX1) / 2, (BZ0 + BZ1) / 2
bino = cad.fuse_one(cyl(4.0, (bm - 5.5, BY - 10, zm), 20, (0, 1, 0)), cyl(4.0, (bm + 5.5, BY - 10, zm), 20, (0, 1, 0)),
                    box(bm - 5.5, bm + 5.5, BY - 10, BY + 10, zm - 1.5, zm + 1.5))
bar = cad.cut(bar, bino)
FREE = [BX0 + 5.0, BX0 + 20.0]                 # the free end's tapped holes (platform screws)
FIXED = [BX1 - 5.0, BX1 - 20.0]                # the fixed end's (base screws)
for x in FREE:
    bar = cad.hole(bar, (x, BY, BZ1), "-Z", 3.4, depth=10)
for x in FIXED:
    bar = cad.hole(bar, (x, BY, BZ0), "+Z", 3.4, depth=10)
cell_screws = []
for x in FIXED:
    base = cad.countersink(base, (x, BY, RUB), "+Z", 4.5, 8.2, through=True)
    cell_screws.append(cad.screw("csk_phillips", "M4", int(BZ0 + 8.0 - RUB), at=(x, BY, RUB), axis="+Z"))

# ------------------------------------------------------------ the platform
PZ0 = Z_TOP + GAP
PZ1 = PZ0 + PT
PCORNER = CORNER - P_IN + 3.0
pw, pd, pcy = 2 * PX, PY1 - PY0, (PY0 + PY1) / 2
plate = zbox(pw, pd, PCORNER, 0.0, pcy, PZ0, PZ1)
post = box(BX0, BX0 + POST_L, BY - BAR[1] / 2, BY + BAR[1] / 2, BZ1, PZ0 + 0.5)
plate = cad.fuse_one(plate, post)
RZ = PZ1 - PAD_D
plate = cad.cut(plate, zbox(pw - 2 * PRIM, pd - 2 * PRIM, PCORNER - PRIM, 0.0, pcy, RZ, PZ1 + 1))
pad = zbox(pw - 2 * PRIM, pd - 2 * PRIM, PCORNER - PRIM, 0.0, pcy, RZ, PZ1 + PAD_UP)
plat_screws = []
for x in FREE:
    plate = cad.countersink(plate, (x, BY, RZ), "-Z", 4.5, 8.2, through=True)
    plat_screws.append(cad.screw("csk_phillips", "M4", int(RZ - (BZ1 - 8.0)), at=(x, BY, RZ), axis="-Z"))
# the deck: a clearance hole round the post (the platform never touches the slab)
top = cad.cut(top, zbox(POST_L + 4.0, BAR[1] + 4.0, 3.0, BX0 + POST_L / 2, BY, Z_TOP - WALL - 1, Z_TOP + 1))
tick("load path")

# ------------------------------------------------------------ the control strip
base_z = Z_TOP - WALL - 0.9
keys = {}
for nm, kb in (("Key_Tare", KT), ("Key_Timer", KM)):
    kx, ky, _kz = centre(kb)
    cap = cad.button_cap(KEY_D, (Z_TOP + 1.6) - base_z, dome=0.5, flange=0.8, at=(kx, ky, base_z), axis="+Z")
    top = cad.opening_for(top, cap, clearance=0.25, chamfer=0.4, axis="+Z")
    keys[nm] = cad.fuse_one(cap, cyl(3.0, (kx, ky, kb.ZMax + 0.16), base_z - (kb.ZMax + 0.16) + 0.5))
sx, sy, _sz = centre(SB)
top, bezel = insert(top, zbox(WINDOW[0] + 2 * BEZEL, WINDOW[1] + 2 * BEZEL, 3.0 + BEZEL, sx, sy, Z_TOP - WALL - 1,
                              Z_TOP + 1))
bezel = bezel.cut(box(-300, 300, -300, 300, Z_TOP - RECESS, Z_TOP + 2))
bezel, window = insert(bezel, zbox(WINDOW[0], WINDOW[1], 3.0, sx, sy, Z_TOP - WALL - 2, Z_TOP + 2))
lx, ly, _lz = centre(LB)
top, dot = insert(top, cyl(DOT_D / 2, (lx, ly, Z_TOP - WALL - 1), WALL + 2))
dot = cad.fuse_one(dot, cyl(DOT_D / 2 - 0.5, (lx, ly, LB.ZMax + 0.5), (Z_TOP - WALL + 0.5) - (LB.ZMax + 0.5)))
# USB-C in the right end: a pocket brings the wall to 0.25 mm off the mouth
uy, uz = (UB.YMin + UB.YMax) / 2, Z_PCB + 5.9


def xprism(y0, y1, z0, z1, x0, x1, r):
    w = cad.rounded_rect_wire(y1 - y0, z1 - z0, r, (x0, (y0 + y1) / 2, (z0 + z1) / 2), "X")
    return Part.Face(w).extrude(V(x1 - x0, 0, 0))


pocket = xprism(uy - 6.5, uy + 6.5, uz - 5.0, uz + 5.0, UB.XMax + 1.3, X1 + 5, 3)
liner = cad.cut(xprism(uy - 8.5, uy + 8.5, max(uz - 7.5, SPLIT + 1.6), uz + 7.5, UB.XMax + 0.25, X1 + 2, 4), pocket)
top = cad.fuse_one(cad.cut(top, pocket), liner.common(skin))
top = cad.socket_opening(top, usb, margin=1.5)
tick("stage A")


# === STAGE B: details ===
# the drip groove in the deck round the platform's foot
ring = cad.cut(zbox(pw + 6.2, pd + 6.2, PCORNER + 3.1, 0.0, pcy, Z_TOP - 1.0, Z_TOP + 1),
               zbox(pw + 3.8, pd + 3.8, PCORNER + 1.9, 0.0, pcy, Z_TOP - 2.0, Z_TOP + 2))
top = cad.cut(top, ring)
# the chamfered platform rim, a soft pad edge, the centring ring in the pad
plate = cad.chamfer_safe(plate, 0.8, [e for e in plate.Edges if e.BoundBox.ZMin > PZ1 - 1e-3
                                      and (e.BoundBox.XLength > pw - 1 or e.BoundBox.YLength > pd - 1
                                           or e.BoundBox.XLength < PCORNER + 0.1 and e.BoundBox.XMin < -PX + PCORNER
                                           or e.BoundBox.XMax > PX - PCORNER)])
pad = cad.soften(pad, 0.8, [e for e in pad.Edges if e.BoundBox.ZMin > PZ1 + PAD_UP - 1e-3])
pad = cad.cut(pad, cad.cut(cyl(41.0, (0.0, pcy, PZ1 + PAD_UP - 0.5), 2), cyl(40.0, (0.0, pcy, PZ1), 3)))
# the parting-line reveal, legends, the coffee-drop icon
top = cad.groove_ring(top, "Z", SPLIT + 2.2, w=0.8, depth=0.6)
for kb, t in ((KT, "TARE"), (KM, "TIMER")):
    kx_, ky_, _ = centre(kb)
    top = cad.text(top, t, (kx_, kb.YMin - 2.7, Z_TOP), (0, 0, 1), 3.5, depth=0.4, mode="deboss", up=(0, 1, 0))
r_ = 3.6
dx, dy = (SB.XMax + KT.XMin) / 2, ly - 1.2      # the icon between the window and TARE (port 12 stays empty)


def drop_prism(z0, z1):
    """A coffee drop (point to the back), straight facets only."""
    pts = [V(dx, dy + 2 * r_, z0)] + [V(dx + r_ * math.cos(math.radians(a)), dy + r_ * math.sin(math.radians(a)), z0)
                                      for a in range(150, 391, 15)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, z1 - z0))


# a copper badge through the deck (an insert), embossed 0.5 mm proud
top, badge = insert(top, drop_prism(Z_TOP - WALL - 1, Z_TOP + 1))
badge = cad.fuse_one(badge, drop_prism(Z_TOP - 0.3, Z_TOP + 0.5))
# under the base: a model mark, rubber feet
base = cad.text(base, "ATECH CS-1  2 kg / 0.1 g", (0.0, 20.0, RUB), (0, 0, -1), 4.0, depth=0.4, mode="deboss",
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
o = part("Platform", plate)
o.ViewObject.ShapeColor = cad.color(COLOURS["Platform"])
o = part("Heat_Pad", pad)
o.ViewObject.ShapeColor = cad.color(COLOURS["Heat_Pad"])
o = part("Load_Cell_Bar", bar)
o.ViewObject.ShapeColor = cad.color(COLOURS["Load_Cell_Bar"])
o = part("Bezel", bezel)
o.ViewObject.ShapeColor = cad.color(COLOURS["Bezel"])
o = part("Screen_Window", window)
o.ViewObject.ShapeColor = cad.color(COLOURS["Screen_Window"])
o.ViewObject.Transparency = cad.transparency("smoked")
o = part("Status_Dot", dot)
o.ViewObject.ShapeColor = cad.color(COLOURS["Status_Dot"])
o.ViewObject.Transparency = cad.transparency("frosted")
o = part("Drop_Badge", badge)
o.ViewObject.ShapeColor = cad.color(COLOURS["Key"])
o = part("Key_Tare", keys["Key_Tare"])
o.ViewObject.ShapeColor = cad.color(COLOURS["Key"])
o = part("Key_Timer", keys["Key_Timer"])
o.ViewObject.ShapeColor = cad.color(COLOURS["Key"])
for i, sh in enumerate(rubbers):
    o = part("Rubber_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Rubber"])
for i, sh in enumerate(screws):
    o = part("Screw_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Screw"])
for i, sh in enumerate(cell_screws):
    o = part("Screw_%d" % (len(screws) + i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Screw"])
for i, sh in enumerate(plat_screws):
    o = part("Screw_%d" % (len(screws) + len(cell_screws) + i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Screw"])
print("SIZE", cad.measure(Part.makeCompound([top, base, plate, pad] + rubbers))["size"])
print("TOTAL %.1f s" % (time.time() - T0))
