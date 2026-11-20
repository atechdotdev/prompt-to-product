"""Example: "a filament dry box that shows the humidity and how much filament is left" - a sealed spool chamber on an instrument plinth that reads the chamber's humidity and the spool's wound diameter.

fork this file for a filament dry box (a spool dryer, a dry cabinet, a
desiccant box for one 1 kg spool); change PARAMETERS and the outlines.
ARCHETYPE: filament dry box

How it is built (R1030):
  * STAGE A - hardware, shell, every working-face opening, fasteners: ONE
    1 kg spool (200 x 70) stands on four 608 bearings in a 225 x 84 x 220
    chamber. Under the chamber, a plinth holds the board LANDSCAPE_UP
    behind its front wall (modules face the front, the PCB 10 mm back so
    the USB-C clears the front corner): the screen (10, 11) behind a
    smoked lens in a black bezel with a tunnel back to the screen
    (humidity, temperature and filament left), the status light (13)
    behind a frosted light pipe, USB-C (7) in a pocket with a liner in the
    left side. Both sensors are CABLED straight up from the two ends of
    the top row (twist-free) and lie face-up under the chamber floor
    between ribs: the ToF distance sensor (14) under the spool's axis
    looks up through a stepped glass window between the rollers at the
    underside of the wound filament - the spool rides on its flange rims,
    so its axis never moves and the distance gives the wound radius (the
    filament left); the temp / humidity sensor (9) at the far left, under
    a slot vent in the chamber's corner, where the chamber air rises past
    the spool's rim (it reads the chamber, not the room). The spool is
    drawn see-through (a clear spool, translucent filament): ./check's
    rays from the ToF must leave the product, and the filament they meet
    is the target. The chamber is a sleeve (four walls) screwed down onto
    the plinth's top - the chamber floor - through four tabs; the plinth
    shell is screwed onto the fixed base plate that carries the board;
    the desiccant drawer slides out of the plinth's right half under a
    slotted floor, behind a partition. Each pair of bearings turns on ONE
    8 mm pin through a rail on the floor (a head at the front, an e-clip
    at the back). The lid rests on the sleeve's rim on a silicone cord in
    a groove, keyed by a lip, and snaps on with four hooks through windows
    in the side walls (cad.snap_fit_pair); the filament leaves through a
    PTFE push-fit coupler (PC4-M10) on a boss in the lid, over a funnel.
  * STAGE B - details: the white filament gauge inlaid in the glass (a ring
    where the wound filament leaves 10 / 25 / 50 / 75 % - those inside
    the window - the empty core ring, a scale bar with the numbers, a
    centre label), the orange carry handle, the curved PTFE tube,
    lettering, the drawer's grip, rubber feet.
DETAILS (visible, 26): 1 tall graphite chamber with soft corners; 2 a
reveal groove at the plinth joint; 3 a big round window over the spool;
4 the orange bezel ring that retains the glass; 5 white gauge rings
inlaid in the glass; 6 the scale bar with "10" / "25" / "50" in it; 7 the
white centre label with "%"; 8 the lid with a rolled top edge; 9 the
orange carry handle on the lid; 10 the PTFE coupler on a boss, with an
orange collet; 11 the white PTFE tube curving away to the printer;
12 "ATECH" on the lid; 13 four snap hooks in their windows in the side
walls; 14 the orange instrument plinth; 15 the smoked screen lens;
16 the black bezel round it; 17 the frosted status light in a black
halo; 18 "FILAMENT DRY BOX" over the readout; 19 the graphite desiccant
drawer; 20 its grip slot; 21 "SILICA" on it; 22 the USB-C pocket with a
liner in the left side; 23 the black base plate; 24 four rubber feet;
25 "ATECH FD-1" under the base; 26 ten countersunk M3 screws (four in the
chamber floor, four under the base, two in the lid under the handle).
Inside: 27 four 608 bearings on two 8 mm pins through rails on the
floor, e-clips; 28 the spool (clear, 88 mm of wound filament); 29 the
stepped glass ToF window between the rails; 30 the humidity slot vent in
the chamber's corner; 31 the slotted floor over the drawer; 32 the
drawer's silica beads; 33 the lid's locating lip and cord gasket; 34 the
glass's flange behind the wall; 35 the filament funnel under the coupler;
36 the partition between the electronics and the drawer bay; 37 board
posts, fences, the spine rib and the top tabs; 38 sensor ribs; 39 heat-set
insert columns.
Materials: graphite chamber, lid and drawer, an orange plinth, bezel,
handle and collet, a black base plate and bezels, clear glass window and
ToF window, a white gauge, smoked lens, frosted light, chrome bearings,
pins and coupler, a white PTFE tube and silicone cord, rubber feet, a
clear spool with orange filament.
Screws: ONE type, 10 x M3 x 10 countersunk + 10 M3 heat-set inserts;
bought: 4 x 608 bearings, 2 x 8 mm headed pins with e-clips, a PC4-M10
coupler, a 2 m silicone cord (1.5 mm), about 150 g of silica beads.
MEASURED (R1030, 2026-11-20): ./check CHECK PASS, run_seconds 15 s, wall 45 s (37-60 s; 195 s once on a saturated machine); every RESTYLE end CHECK PASS.
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
    "Base_Shell", "Chamber", "Lid", "Gasket", "Window", "Bezel_Ring", "Screen_Bezel", "Screen_Lens",
    "Status_Lens", "Halo_Ring", "Drawer", "Silica", "Sensor_Window", "Spool", "Bearing_1", "Bearing_2",
    "Bearing_3", "Bearing_4", "Roller_Pin_1", "Roller_Pin_2", "Clip_1", "Clip_2",
    "PTFE_Coupler", "Collet", "PTFE_Tube", "Gauge", "Handle", "Foot_1", "Foot_2", "Foot_3", "Foot_4",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4", "Screw_5", "Screw_6", "Screw_7", "Screw_8", "Screw_9", "Screw_10"]}
REVIEW_CLOSEUPS = ["Window", "Screen_Bezel", "Drawer"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them and the measured hardware.
WALL = 3.0         # RESTYLE 2.55..3.45 wall
LID_H = 10.0       # RESTYLE 8.5..11.5 height: the lid's thickness
CORNER = 10.0      # RESTYLE 8.5..11.5 radius: the box's plan corners
WIN_R = 85.0       # RESTYLE 72..98 radius: the window over the spool
BEZEL_W = 7.0      # RESTYLE 5.95..8.05 width: the orange bezel ring round the window
# end RESTYLE
# the spool (a standard 1 kg spool) and the chamber round it
SPOOL_R, SPOOL_W, FLANGE_T = 100.0, 70.0, 3.0
HUB_R, CORE_R = 28.0, 50.0                  # the bore, the core (a solid hub)
FILL_R = 88.0                               # the wound filament (a part-used spool)
IN_X, IN_D = 112.5, 84.0                    # the chamber inside: half width, depth
CH_H = 220.0                                # floor to lid underside
FLOOR_T = 3.0                               # the chamber floor (the plinth's top)
# the rollers: 608 bearings (22 x 8 x 7) on headed 8 mm pins in floor posts
BRG_R, BRG_RI, BRG_W = 11.0, 4.1, 7.0
PIN_R, ROLL_X, ROLL_LIFT = 4.0, 55.0, 2.0
# the hardware frame (fixed: the board decides it)
PZ0, PZ1 = 2.0, 5.0                         # the base plate
ZB = 8.0                                    # the board's bottom edge
BY = 10.0                                   # the PCB's front face (modules face -Y from here)
YFI = -10.64                                # the front wall's inner face
DX0 = 12.0                                  # the partition (electronics | drawer bay)
SZ = 3.2                                    # the sensors over the board's top edge
WIN_GLASS = 14.0                            # the ToF window in the chamber floor
SCREEN_WIN = (28.0, 16.0)
GAUGE = (10, 25, 50, 75)                    # % of the filament left (rings on the glass, those that fit)
EXIT_X = -55.0                              # the filament exit in the lid
SCREW = "M3"
COLOURS = {"Base_Plate": "matte_black", "Base_Shell": "#ff6b1a", "Chamber": "#3a3d42",
           "Lid": "#3a3d42", "Gasket": "matte_white", "Window": "glass", "Gauge": "matte_white", "Bezel_Ring": "#ff6b1a",
           "Screen_Bezel": "matte_black", "Screen_Lens": "smoked", "Status_Lens": "frosted",
           "Halo_Ring": "matte_black", "Drawer": "#3a3d42", "Silica": "#f2a33a", "Sensor_Window": "glass",
           "Spool": "#ff7a1f", "Bearing": "chrome", "Roller_Pin": "chrome", "Clip": "matte_black", "PTFE_Coupler": "chrome",
           "Collet": "#ff6b1a", "Handle": "#ff6b1a", "PTFE_Tube": "matte_white", "Foot": "rubber", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
LANDSCAPE_UP = Rotation(Vector(0, 0, 1), 180).multiply(Rotation(Vector(0, 1, 0), -90))
board = ap.board_object(doc)
board.Placement = Placement(V(), LANDSCAPE_UP)
_b = ap.bbox(board)
board.Placement = Placement(V(-110.0 - _b.XMin, BY, ZB - _b.ZMin), LANDSCAPE_UP)   # x -110..10, z 8..68
BB = ap.bbox(board)
scr = ap.seat(doc, "screen", (10, 11))        # top row, left: the readout
led = ap.seat(doc, "light", 13)               # top row: the status light
usb = ap.seat(doc, "usbc", 7)                 # left end, mouth -X
# the sensors: straight up out of the top row's two ends, face up under
# the chamber floor (twist-free: face +Z x cable -Y runs along the row)
SY = BY + 24.0
SZC = BB.ZMax + SZ + 9.54 / 2
th, th_rib = ap.cable(doc, "temp_humidity", 9, ap.module_placement(
    "temp_humidity", (-100.0, SY, SZC), face="+Z", cable="-Y"))
tof, tof_rib = ap.cable(doc, "distance_sensor", 14, ap.module_placement(
    "distance_sensor", (0.0, SY, SZC), face="+Z", cable="-Y"))
tick("hardware")

SB, LB, UB, HB, TB = [ap.bbox(o) for o in (scr, led, usb, th, tof)]
for nm, b in (("board", BB), ("screen", SB), ("light", LB), ("usb", UB), ("th", HB), ("tof", TB)):
    print("BOX %-6s x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (nm, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def centre(b):
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


def facet_rect(x0, x1, y0, y1, r, n=3):
    """A rectangle's points in plan with each corner cut by n straight
    facets (an inside corner that never reads as a clip channel)."""
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90.0 * i / n)
            pts.append(V(cx + r * math.cos(a), cy + r * math.sin(a), 0))
    return pts


def prism(pts, z0, z1):
    w = Part.makePolygon([V(p.x, p.y, z0) for p in pts] + [V(pts[0].x, pts[0].y, z0)])
    return Part.Face(w).extrude(V(0, 0, z1 - z0))


def ring_prism(o0, o1, inset0, inset1, r, z0, z1):
    """The ring between the outline inset by inset0 and by inset1 (faceted)."""
    (x0, x1), (y0, y1) = o0, o1
    a = prism(facet_rect(x0 + inset0, x1 - inset0, y0 + inset0, y1 - inset0, max(r - inset0, 0.6)), z0, z1)
    b = prism(facet_rect(x0 + inset1, x1 - inset1, y0 + inset1, y1 - inset1, max(r - inset1, 0.6)), z0 - 1, z1 + 1)
    return a.cut(b)


def insert(shell, cutter):
    """(shell with the opening, the piece that fills it exactly)."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, piece


def ycyl(r, x, z, y0, y1):
    return cyl(r, (x, y0, z), y1 - y0, (0, 1, 0))


# ------------------------------------------------------------ the frame
X1 = IN_X + WALL                          # outer half width
YF = YFI - WALL                           # the front face
YBI = YFI + IN_D                          # the back wall's inner face
YB = YBI + WALL                           # the back face
ZF = HB.ZMax + 0.5 + FLOOR_T              # the chamber floor's top (0.5 over the sensors' faces)
ZT = ZF + CH_H                            # the sleeve's rim
SC_Y = YFI + IN_D / 2                     # the spool's mid-plane
Z_R = ZF + ROLL_LIFT + BRG_R              # the bearings' axis
ZA = Z_R + math.sqrt((SPOOL_R + BRG_R + 0.2) ** 2 - ROLL_X ** 2)   # the spool's axis (0.2 over the bearings)
CR_IN = max(CORNER - WALL, 1.0)
OUT = ((-X1, X1), (YF, YB))
print("FRAME floor z %.2f, rim z %.2f, spool axis z %.2f, outside %.0f x %.0f x %.0f" % (
    ZF, ZT, ZA, 2 * X1, YB - YF, ZT + LID_H))


def outer(z0, z1):
    return cad.rounded_box(2 * X1, YB - YF, z1 - z0, CORNER, at=(-X1, YF, z0))


def inner(z0, z1, grow=0.0):
    return prism(facet_rect(-IN_X - grow, IN_X + grow, YFI - grow, YBI + grow, max(CR_IN + grow, 0.6)), z0, z1)


# ------------------------------------------------------------ the base plate (fixed: holds the board)
plate = outer(PZ0, PZ1)
plate = cad.soften(plate, 1.0, [e for e in plate.Edges if e.BoundBox.ZMax < PZ0 + 1e-3])
UNDER = ZB - 0.1
holders = [box(x - 3, x + 3, BY + 0.2, BY + 2.3, PZ1 - 0.5, UNDER) for x in (-95.0, -60.0, -25.0, 0.0)]
holders += [box(x - 1.0, x + 1.0, BY - 1.5, BY - 0.25, PZ1 - 0.5, ZB + 4.0) for x in (-90.0, -30.0)]
holders += [box(x - 3, x + 3, BY + 2.75, BY + 4.25, PZ1 - 0.5, ZB + 6.0) for x in (-95.0, -60.0, -25.0, 0.0)]
plate = cad.fuse_one(plate, *holders)

# ------------------------------------------------------------ the plinth shell (top = the chamber floor)
base = outer(PZ1, ZF)
base = cad.soften(base, 1.2, [e for e in base.Edges if e.BoundBox.ZMin > ZF - 1e-3])
base = cad.cut(base, inner(PZ1 - 1, ZF - FLOOR_T))
FL0 = ZF - FLOOR_T                        # the floor's underside
# the partition walls off the desiccant bay on the right
base = cad.fuse_one(base, box(DX0, DX0 + WALL, YFI - 0.5, YBI + 0.5, PZ1, FL0 + 0.5))
# the board: a spine rib from the front wall, a tab over the top edge
# and one behind it
base = cad.fuse_one(base, box(-62, -58, YFI - 0.5, BY - 4.5 - 0.2, 33.0, 43.0),
                    box(-42, -38, BY + 0.3, BY + 2.3, BB.ZMax + 0.2, FL0 + 0.5),
                    box(-42, -38, BY + 2.75, BY + 4.25, BB.ZMax - 8.0, FL0 + 0.5))
# the cabled sensors lie between ribs hanging from the floor (0.25 mm off)
ribs = []
for b in (HB, TB):
    ribs += [box(b.XMin - 1.75, b.XMin - 0.25, b.YMin + 1, b.YMax - 1, b.ZMin + 1.0, FL0 + 0.5),
             box(b.XMax + 0.25, b.XMax + 1.75, b.YMin + 1, b.YMax - 1, b.ZMin + 1.0, FL0 + 0.5)]
ribs[0] = box(-IN_X - 0.5, HB.XMin - 0.25, HB.YMin + 1, HB.YMax - 1, HB.ZMin + 1.0, FL0 + 0.5)
base = cad.fuse_one(base, *ribs)
tick("plinth")

# ------------------------------------------------------------ the chamber sleeve
sleeve = outer(ZF, ZT)
sleeve = cad.soften(sleeve, 1.2, [e for e in sleeve.Edges if e.BoundBox.ZMax < ZF + 1e-3])
sleeve = cad.cut(sleeve, inner(ZF - 1, ZT + 1))
# screw tabs inside the front and back walls (clear of the spool)
TAB_X, TAB_H = 80.0, 9.0
TABS = [(sx * TAB_X, y) for sx in (-1, 1) for y in (YFI + 5.0, YBI - 5.0)]
sleeve = cad.fuse_one(sleeve, *[box(x - 6, x + 6, YFI - 0.5, YFI + 10.0, ZF, ZF + TAB_H) for x in (-TAB_X, TAB_X)],
                      *[box(x - 6, x + 6, YBI - 10.0, YBI + 0.5, ZF, ZF + TAB_H) for x in (-TAB_X, TAB_X)])
tick("sleeve")

# ------------------------------------------------------------ the lid
lid = outer(ZT, ZT + LID_H)
EDGE = 0.45 * LID_H
lid = cad.soften(lid, EDGE, [e for e in lid.Edges if e.BoundBox.ZMin > ZT + LID_H - 1e-3])
LIP = 5.0
lid = cad.fuse_one(lid, ring_prism(*OUT, WALL + 0.25, WALL + 1.85, CORNER, ZT - LIP, ZT + 0.5))
# the gasket: a silicone cord in a groove over the middle of the wall
G_IN0, G_IN1 = 0.95, WALL - 0.7               # 0.95 mm outside it, 0.95 to the lip
groove = ring_prism(*OUT, G_IN0, G_IN1, CORNER, ZT - 0.01, ZT + 1.5)
lid = cad.cut(lid, groove)
gasket = ring_prism(*OUT, G_IN0 + 0.1, G_IN1 - 0.1, CORNER, ZT, ZT + 1.5 - 0.01)
sleeve, lid = cad.snap_fit_pair(sleeve, lid, count=4, walls="x")
tick("lid + snaps")

# ------------------------------------------------------------ fasteners (one type: M3 countersunk)
INSERT_D, PILOT_D, D_SCREW = 4.3, 2.5, 3.0
CSK = (6.4, 3.4)
screws = []
# the chamber onto the plinth: down through the tabs into inserts in
# columns under the floor
cols, bores, csks = [], [], []
for x, y in TABS:
    cols.append(cyl(INSERT_D / 2 + 1.5, (x, y, FL0 - 7.0), 7.5))
    bores.append(cyl(INSERT_D / 2, (x, y, ZF - 6.0), 6.5))
    bores.append(cyl(PILOT_D / 2, (x, y, ZF - 9.0), 3.5))
    csks.append(Part.makeCone(CSK[1] / 2, CSK[0] / 2, (CSK[0] - CSK[1]) / 2, V(x, y, ZF + TAB_H - (CSK[0] - CSK[1]) / 2 + 0.01),
                              V(0, 0, 1)))
    csks.append(cyl(CSK[1] / 2, (x, y, ZF - 0.5), TAB_H + 1.0))
    screws.append(cad.screw("csk_phillips", SCREW, 10, at=(x, y, ZF + TAB_H), axis="-Z"))
base = cad.cut(cad.fuse_one(base, *cols), bores)
sleeve = cad.cut(sleeve, csks)
# the plinth onto the base plate: up through the plate into corner columns
# each column on its corner's diagonal, 1 mm into the faceted corner wall
CD = CR_IN - (CR_IN - (INSERT_D / 2 + 1.5) + 1.0) / math.sqrt(2.0)   # its inset from both walls
PS = [(sx * (IN_X - CD), y) for sx in (-1, 1) for y in (YFI + CD, YBI - CD)]
cols, bores, csks = [], [], []
for x, y in PS:
    cols.append(cyl(INSERT_D / 2 + 1.5, (x, y, PZ1 + 0.1), 13.0))
    bores.append(cyl(INSERT_D / 2, (x, y, PZ1), 6.0))
    bores.append(cyl(PILOT_D / 2, (x, y, PZ1 + 5.5), 5.0))
    csks.append(Part.makeCone(CSK[0] / 2, CSK[1] / 2, (CSK[0] - CSK[1]) / 2, V(x, y, PZ0 - 0.01), V(0, 0, 1)))
    csks.append(cyl(CSK[1] / 2, (x, y, PZ0 - 0.5), PZ1 - PZ0 + 1.0))
    screws.append(cad.screw("csk_phillips", SCREW, 10, at=(x, y, PZ0), axis="+Z"))
base = cad.cut(cad.fuse_one(base, *cols), bores)
plate = cad.cut(plate, csks)
tick("screws")

# ------------------------------------------------------------ working-face openings
# the ToF looks up through a stepped glass window in the floor
tx, ty, _tz = centre(TB)
base, swin = insert(base, cad.fuse_one(cyl(WIN_GLASS / 2, (tx, ty, ZF - FLOOR_T - 1), FLOOR_T + 2),
                                       cyl(WIN_GLASS / 2 + 2.0, (tx, ty, FL0 - 1.0), 2.0)))
# the humidity sensor breathes the chamber through a slot vent in the
# floor's left corner, where the air rises past the spool's rim
hx, hy, _hz = centre(HB)
base = cad.grille(base, ((-IN_X + HB.XMax) / 2, hy, ZF), (0, 0, 1), (HB.XMax + IN_X - 1.0, HB.YMax - HB.YMin - 2.0),
                  kind="slot", hole=2.0, pitch=3.2, margin=0.5)
# the screen: a black bezel insert in the front wall with a tunnel back
# to 0.5 mm off the screen, a smoked lens in its window
sx, _sy, sz = centre(SB)
BZ = (SCREEN_WIN[0] + 12.0, SCREEN_WIN[1] + 10.0)


def yprism(cx, cz, w, h, r, y0, y1):
    return Part.Face(cad.rounded_rect_wire(w, h, r, (cx, y0, cz), "Y")).extrude(V(0, y1 - y0, 0))


base, bezel = insert(base, yprism(sx, sz, BZ[0], BZ[1], 3.0, YF - 1.0, YFI + 1.0))
bezel = cad.fuse_one(bezel, cad.cut(box(sx - SCREEN_WIN[0] / 2 - 2, sx + SCREEN_WIN[0] / 2 + 2, YFI - 0.5,
                                        SB.YMin - 0.5, sz - SCREEN_WIN[1] / 2 - 2, sz + SCREEN_WIN[1] / 2 + 2),
                                    box(sx - SCREEN_WIN[0] / 2, sx + SCREEN_WIN[0] / 2, YFI - 1, SB.YMin,
                                        sz - SCREEN_WIN[1] / 2, sz + SCREEN_WIN[1] / 2)))
bezel = bezel.cut(yprism(sx, sz, BZ[0] - 4.0, BZ[1] - 4.0, 2.0, YF - 2, YF + 1.0))
bezel, lens = insert(bezel, box(sx - SCREEN_WIN[0] / 2, sx + SCREEN_WIN[0] / 2, YF - 1, YF + WALL,
                                sz - SCREEN_WIN[1] / 2, sz + SCREEN_WIN[1] / 2))
# the status light: a frosted pipe through the wall to 0.5 mm off the LEDs
lx, _ly, lz = centre(LB)
base, slens = insert(base, ycyl(5.0, lx, lz, YF - 1.0, YFI + 1.0))
slens = cad.fuse_one(slens, ycyl(4.5, lx, lz, YFI - 0.5, LB.YMin - 0.5))
# USB-C in the left side: a pocket brings the wall to 0.25 mm off the mouth
uy, uz = (UB.YMin + UB.YMax) / 2, (UB.ZMin + UB.ZMax) / 2


def xprism(y0, y1, z0, z1, x0, x1, r):
    w = cad.rounded_rect_wire(y1 - y0, z1 - z0, r, (x0, (y0 + y1) / 2, (z0 + z1) / 2), "X")
    return Part.Face(w).extrude(V(x1 - x0, 0, 0))


skin = outer(PZ1 + 0.5, ZF - 0.5)
pocket = xprism(uy - 6.0, uy + 6.0, uz - 9.0, uz + 9.0, -X1 - 5, UB.XMin - 1.3, 3)
liner = cad.cut(xprism(uy - 8.0, uy + 8.0, uz - 11.0, uz + 11.0, -X1 - 2, UB.XMin - 0.25, 4), pocket)
base = cad.fuse_one(cad.cut(base, pocket), liner.common(skin))
base = cad.socket_opening(base, usb, margin=1.5)
tick("openings")

# ------------------------------------------------------------ the desiccant drawer
OX0, OX1 = DX0 + WALL + 2.0, X1 - CORNER - 1.5      # the opening, in the front wall's flat
DZT = FL0 - 8.5                                    # the drawer's top (under the screw columns)
base = cad.cut(base, box(OX0, OX1, YF - 1, YFI + 1, PZ1 - 1, DZT + 0.3))
D0, D1 = OX0 + 0.3, OX1 - 0.3
drawer = box(D0, D1, YF, YBI - 1.0, PZ1 + 0.3, DZT)
drawer = cad.cut(drawer, box(D0 + 2.0, D1 - 2.0, YFI + 0.3, YBI - 3.0, PZ1 + 2.3, DZT + 1))
# the floor over the bay: slots let the beads breathe the chamber air
base = cad.grille(base, ((D0 + D1) / 2, (YFI + YBI) / 2, ZF), (0, 0, 1), (D1 - D0 - 14.0, IN_D - 30.0),
                  kind="slot", hole=2.5, pitch=6.0, margin=1.0)
silica = box(D0 + 2.1, D1 - 2.1, YFI + 2.1, YBI - 3.1, PZ1 + 2.3, PZ1 + 2.3 + 0.55 * (DZT - PZ1 - 2.3))
tick("drawer")

# ------------------------------------------------------------ the rollers and the spool
rails, pins, clips, brgs = [], [], [], []
B0 = SC_Y - SPOOL_W / 2 + 1.0                     # the front bearing's front face (under the flange)
B3 = SC_Y + SPOOL_W / 2 - 1.0                     # the back bearing's back face
for sx_ in (-1, 1):
    x = sx_ * ROLL_X
    # a rail on the floor between the two bearings, ONE pin through it and
    # both bearings: a head at the front, an e-clip in a groove at the back
    r0, r1 = B0 + BRG_W + 0.2, B3 - BRG_W - 0.2
    rails.append(cad.cut(box(x - 6.0, x + 6.0, r0, r1, ZF - 0.5, Z_R + 6.0), ycyl(PIN_R + 0.1, x, Z_R, r0 - 1, r1 + 1)))
    pins.append(cad.fuse_one(ycyl(PIN_R, x, Z_R, B0 - 0.2, B3 + 1.8), ycyl(6.0, x, Z_R, B0 - 1.7, B0 - 0.2)))
    clips.append(cad.cut(ycyl(6.5, x, Z_R, B3 + 0.3, B3 + 1.1), ycyl(PIN_R + 0.1, x, Z_R, B3, B3 + 2)))
    for y0 in (B0, B3 - BRG_W):
        y1 = y0 + BRG_W
        ring = [(BRG_RI, y0 + 0.5), (BRG_RI + 0.5, y0), (BRG_R - 0.5, y0), (BRG_R, y0 + 0.5), (BRG_R, y1 - 0.5),
                (BRG_R - 0.5, y1), (BRG_RI + 0.5, y1), (BRG_RI, y1 - 0.5)]
        brgs.append(cad.revolve_profile(ring, axis="Y", at=(x, 0, Z_R)))
base = cad.fuse_one(base, *rails)
# the spool: flanges, the core tube and the wound filament as one bought part
S0, S1 = SC_Y - SPOOL_W / 2, SC_Y + SPOOL_W / 2
spool = cad.revolve_profile([(HUB_R, S0), (SPOOL_R, S0), (SPOOL_R, S0 + FLANGE_T), (FILL_R, S0 + FLANGE_T),
                             (FILL_R, S1 - FLANGE_T), (SPOOL_R, S1 - FLANGE_T), (SPOOL_R, S1), (HUB_R, S1)], axis="Y", at=(0, 0, ZA))
tick("spool")

# ------------------------------------------------------------ the window and the filament exit
# the glass: a disc in the window 0.05 mm clear all round, a flange
# behind the wall (sealed with a bead of silicone), the bezel in front
YG = YF + 0.05                                    # the glass's front face
sleeve = cad.cut(sleeve, ycyl(WIN_R, 0.0, ZA, YF - 1.0, YFI + 1.0))
glass = cad.fuse_one(ycyl(WIN_R - 0.05, 0.0, ZA, YG, YFI + 1.0), ycyl(WIN_R + 3.0, 0.0, ZA, YFI + 0.05, YFI + 1.55))
# the orange bezel ring: keyed 1 mm into a pocket round the window, its
# lip 1.5 mm over the glass's edge holds it in from the front
BR0, BR1 = WIN_R - 1.5, WIN_R + BEZEL_W
key = cad.cut(ycyl(BR1, 0.0, ZA, YF - 1.0, YF + 1.0), ycyl(WIN_R, 0.0, ZA, YF - 2, YF + 2))
sleeve, kpiece = insert(sleeve, key)
bring = cad.fuse_one(kpiece, cad.cut(ycyl(BR1, 0.0, ZA, YF - 1.5, YF + 0.5), ycyl(WIN_R + 0.5, 0.0, ZA, YF - 2, YF + 2)),
                     cad.cut(ycyl(WIN_R + 0.6, 0.0, ZA, YF - 1.5, YF - 0.05), ycyl(BR0, 0.0, ZA, YF - 2, YF + 2)))
# the PTFE exit: a boss on the lid, an M10 hole, a funnel under it
ex, ey = EXIT_X, SC_Y
LT = ZT + LID_H
lid = cad.fuse_one(lid, cyl(9.0, (ex, ey, LT - 1.0), 5.0),
                   Part.makeCone(6.0, 10.0, 6.0, V(ex, ey, ZT - 6.0 + 0.01), V(0, 0, 1)))
lid = cad.cut(lid, [cyl(5.0, (ex, ey, ZT - 7.0), LID_H + 12.0),
                    Part.makeCone(8.0, 5.0, 4.0, V(ex, ey, ZT - 6.0 - 0.01), V(0, 0, 1))])
BT = LT + 4.0                                     # the boss's top
HEX = [V(ex + 8.08 * math.cos(math.radians(60 * i)), ey + 8.08 * math.sin(math.radians(60 * i)), BT) for i in range(7)]
coupler = cad.fuse_one(cyl(4.9, (ex, ey, ZT - 2.0), BT - ZT + 2.5), Part.Face(Part.makePolygon(HEX)).extrude(V(0, 0, 7.0)))
coupler = cad.cut(coupler, cyl(2.05, (ex, ey, ZT - 3.0), BT - ZT + 20.0))
collet = cad.cut(cyl(4.5, (ex, ey, BT + 7.0 - 1.0), 3.5), cyl(2.1, (ex, ey, BT), 12.0))
coupler = cad.cut(coupler, cyl(4.6, (ex, ey, BT + 7.0 - 1.0), 2.0))
# the PTFE tube (4 x 2): in the coupler, then away to the printer (the
# curve drawn 0.05 mm thinner: two coincident skins make the fuse fail)
tube = cad.fuse_one(cyl(2.0, (ex, ey, ZT - 2.0), BT - ZT + 16.0),
                    cad.pipe([(ex, ey, BT + 12.0), (ex, ey, BT + 30.0), (ex + 14.0, ey + 8.0, BT + 50.0),
                              (ex + 40.0, ey + 20.0, BT + 58.0)], r=1.95))
# a carry handle on the lid, two M3 screws up through the lid into
# heat-set inserts in its legs
HX0, HX1, HW, HH = 0.0, 80.0, 16.0, 22.0
handle = cad.rounded_box(HX1 - HX0, HW, HH, 7.0, at=(HX0, ey - HW / 2, LT), edges="y")
handle = cad.cut(handle, box(HX0 + 13.0, HX1 - 13.0, ey - HW, ey + HW, LT - 1, LT + HH - 8.0))
handle = cad.soften(handle, 2.0, [e for e in handle.Edges if abs(e.tangentAt(e.FirstParameter).x) > 0.99
                                  and e.BoundBox.ZMin > LT + HH - 1e-3])
HS = [(HX0 + 6.5, ey), (HX1 - 6.5, ey)]
LB_Z = ZT + 6.0                                   # the screw heads, sunk 6 mm into the lid's underside
for hx_, hy_ in HS:
    handle = cad.cut(handle, [cyl(INSERT_D / 2, (hx_, hy_, LT - 0.5), 6.5), cyl(PILOT_D / 2, (hx_, hy_, LT + 5.5), 4.0)])
    lid = cad.cut(lid, [cyl(CSK[0] / 2 + 0.2, (hx_, hy_, ZT - LIP - 1.0), LB_Z - ZT + LIP + 1.0),
                        Part.makeCone(CSK[0] / 2, CSK[1] / 2, (CSK[0] - CSK[1]) / 2, V(hx_, hy_, LB_Z - 0.01), V(0, 0, 1)),
                        cyl(CSK[1] / 2, (hx_, hy_, LB_Z), LT - LB_Z + 1.0)])
    screws.append(cad.screw("csk_phillips", SCREW, 10, at=(hx_, hy_, LB_Z), axis="+Z"))
tick("stage A")


# === STAGE B: details ===
# the gauge on the glass: a white ring inlaid where the wound filament
# leaves 10 / 25 / 50 / 75 % of the spool (those inside the window), the
# empty core ring and a scale bar across them with the numbers in it
GA = math.radians(40.0)                           # the scale bar's angle (upper right)
gauge = [(0, CORE_R + 1.0)]
for pct in GAUGE:
    r = math.sqrt(CORE_R ** 2 + pct / 100.0 * ((SPOOL_R - 2.0) ** 2 - CORE_R ** 2))
    if r < WIN_R - 3.0:
        gauge.append((pct, r))
GR = gauge[-1][1]
marks = [cad.cut(ycyl(r + 0.8, 0.0, ZA, YG - 0.5, YG + 0.8), ycyl(r - 0.8, 0.0, ZA, YG - 1, YG + 1)) for _p, r in gauge]
bar = box(CORE_R - 8.0, GR + 0.5, YG - 0.5, YG + 0.8, -5.0, 5.0)
bar.rotate(V(0, 0, 0), V(0, 1, 0), -math.degrees(GA))
bar.translate(V(0, 0, ZA))
CAP_R = CORE_R - 6.0                              # a white centre label over the hub
gmark = cad.fuse_one(bar, ycyl(CAP_R, 0.0, ZA, YG - 0.5, YG + 0.8), *marks)
gmark = cad.text(gmark, "%", (0.0, YG - 0.5, ZA), (0, -1, 0), 24.0, depth=0.35, mode="deboss")
for (p0, r0), (p1, r1) in zip(gauge[:-1], gauge[1:]):
    rm = (r0 + r1) / 2
    gmark = cad.text(gmark, "%d" % p1, (rm * math.cos(GA), YG - 0.5, ZA + rm * math.sin(GA)), (0, -1, 0), 3.2,
                     depth=0.35, mode="deboss", up=(math.cos(GA), 0, math.sin(GA)))
glass = cad.cut(glass, gmark)
lid = cad.text(lid, "ATECH", (40.0, YF + 13.0, LT), (0, 0, 1), 7.0, depth=0.6, mode="deboss", up=(0, 1, 0))
base = cad.text(base, "FILAMENT DRY BOX", (-45.0, YF, (SB.ZMax + ZF) / 2 + 1.5), (0, -1, 0), 4.0, depth=0.4,
                mode="deboss")
drawer = cad.cut(drawer, box((D0 + D1) / 2 - 22, (D0 + D1) / 2 + 22, YF - 1, YF + 1.5, DZT - 12, DZT - 5))
drawer = cad.text(drawer, "SILICA", ((D0 + D1) / 2, YF, (PZ1 + DZT) / 2 - 4), (0, -1, 0), 6.0, depth=0.5,
                  mode="deboss")
plate = cad.text(plate, "ATECH FD-1", (0.0, (YF + YB) / 2, PZ0), (0, 0, -1), 8.0, depth=0.4, mode="deboss",
                 up=(0, -1, 0))
# the orange halo round the status light, keyed 1 mm into the wall
halo = cad.cut(ycyl(9.0, lx, lz, YF - 0.8, YF + 1.0), ycyl(5.0, lx, lz, YF - 2, YF + 2))
base = cad.cut(base, cad.cut(ycyl(9.1, lx, lz, YF - 1, YF + 1.0), ycyl(5.0, lx, lz, YF - 2, YF + 2)))
# rubber feet in pockets under the plate
FEET = [(sx_ * (X1 - 18.0), y) for sx_ in (-1, 1) for y in (YF + 14.0, YB - 14.0)]
plate = cad.cut(plate, [cyl(6.1, (x, y, PZ0 - 1), 2.0) for x, y in FEET])
feet = [cad.foot(12.0, 3.0, style="dome", at=(x, y, PZ0 + 1.0)) for x, y in FEET]
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    return o


o = part("Base_Plate", plate)
o.ViewObject.ShapeColor = cad.color(COLOURS["Base_Plate"])
o = part("Base_Shell", base)
o.ViewObject.ShapeColor = cad.color(COLOURS["Base_Shell"])
o = part("Chamber", sleeve)
o.ViewObject.ShapeColor = cad.color(COLOURS["Chamber"])
o = part("Lid", lid)
o.ViewObject.ShapeColor = cad.color(COLOURS["Lid"])
o = part("Drawer", drawer)
o.ViewObject.ShapeColor = cad.color(COLOURS["Drawer"])
o = part("Spool", spool)
o.ViewObject.ShapeColor = cad.color(COLOURS["Spool"])
o.ViewObject.Transparency = cad.transparency("frosted")
o = part("Window", glass)
o.ViewObject.ShapeColor = cad.color(COLOURS["Window"])
o.ViewObject.Transparency = cad.transparency("glass")
o = part("Bezel_Ring", bring)
o.ViewObject.ShapeColor = cad.color(COLOURS["Bezel_Ring"])
o = part("Gasket", gasket)
o.ViewObject.ShapeColor = cad.color(COLOURS["Gasket"])
o = part("Screen_Bezel", bezel)
o.ViewObject.ShapeColor = cad.color(COLOURS["Screen_Bezel"])
o = part("Screen_Lens", lens)
o.ViewObject.ShapeColor = cad.color(COLOURS["Screen_Lens"])
o.ViewObject.Transparency = cad.transparency("smoked")
o = part("Status_Lens", slens)
o.ViewObject.ShapeColor = cad.color(COLOURS["Status_Lens"])
o.ViewObject.Transparency = cad.transparency("frosted")
o = part("Halo_Ring", halo)
o.ViewObject.ShapeColor = cad.color(COLOURS["Halo_Ring"])
o = part("Sensor_Window", swin)
o.ViewObject.ShapeColor = cad.color(COLOURS["Sensor_Window"])
o.ViewObject.Transparency = cad.transparency("glass")
o = part("Silica", silica)
o.ViewObject.ShapeColor = cad.color(COLOURS["Silica"])
for i, sh in enumerate(brgs):
    o = part("Bearing_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Bearing"])
for i, sh in enumerate(pins):
    o = part("Roller_Pin_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Roller_Pin"])
for i, sh in enumerate(clips):
    o = part("Clip_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Clip"])
o = part("Handle", handle)
o.ViewObject.ShapeColor = cad.color(COLOURS["Handle"])
o = part("PTFE_Coupler", coupler)
o.ViewObject.ShapeColor = cad.color(COLOURS["PTFE_Coupler"])
o = part("Collet", collet)
o.ViewObject.ShapeColor = cad.color(COLOURS["Collet"])
o = part("Gauge", gmark)
o.ViewObject.ShapeColor = cad.color(COLOURS["Gauge"])
o = part("PTFE_Tube", tube)
o.ViewObject.ShapeColor = cad.color(COLOURS["PTFE_Tube"])
for i, sh in enumerate(feet):
    o = part("Foot_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Foot"])
for i, sh in enumerate(screws):
    o = part("Screw_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Screw"])
print("SIZE %s" % (cad.measure(Part.makeCompound([plate, base, sleeve, lid]))["size"],))
print("SIZE model build %.1f s" % (time.time() - T0))
