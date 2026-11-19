"""Example: "an on air sign that lights up when you are talking" - a retro studio ON AIR light box that hears your voice and glows red.

fork this file for an on air sign / studio light box (a recording light, a
do-not-disturb or in-a-meeting sign, a busy light, a voice-activated tally
light); change PARAMETERS and the outlines.
ARCHETYPE: on air sign

How it is built (R990):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board LANDSCAPE_FRONT in a rounded box (modules facing the viewer, -Y),
    its top row (ports 6..1, left to right) six lights SEATED behind the
    red panel, its bottom row in the chin: the microphone on (13, 14)
    behind a chrome pin-hole grille that carries its own seal tube to
    0.3 mm off the mic, the FORCE key on 10 (a cap through the chin, its
    plunger to 0.16 mm off the button). USB-C CABLED from port 7 (the
    right end) round the board's edge to the back, standing on edge (face
    -X, twist-free), its mouth 1.25 mm behind the back wall in a bay,
    held by two ribs. Ports 8 and 12 stay empty. The housing: one rounded
    box (front corners CORNER, the front edge rolled) hollowed with a sharp
    core, split FRONT / BACK just behind the board (the back is fixed: it
    carries the board on ledges and standoffs); four M2.5 screws from the
    back - two in the chin corners, two in the side margins beside the
    window - into heat-set inserts in the front. The face: a chrome bezel
    (an insert with a raised lip and a flange behind the wall) round a red
    frosted panel (an insert in the bezel, a flange behind it and a rib
    onto the board's spine: the panel holds the board forward). The desk
    foot: a solid tapered plinth on four rubber feet, two M2.5 screws up
    into inserts in the back's floor (take it off to hang the sign); two
    keyholes in the back for the wall.
  * STAGE B - details: ON AIR as five raised white frosted letters inlaid
    1.2 mm into the panel, the front / back reveal, the ring round the key,
    MIC / FORCE legends, ATECH on the chin, the model plate on the back.
RESTYLE (R425): WIDTH, PANEL_H, DEPTH, CORNER and WALL drive every outline
and cutter below; the board frame (x centred on the box, its bottom
Z0 over the floor) is the hardware's own. PANEL_H sets the window and the
box height; the letters scale with it; DEPTH moves the front (the light's
diffusion gap), the back stays on the USB-C module.
DETAILS (visible, 30): 1 rounded retro box with big front corners; 2 rolled
front edge; 3 rolled back edge; 4 front / back reveal; 5 chrome bezel ring;
6 its raised lip, softened; 7 red frosted panel, recessed 2 mm; 8-12 raised
white letters O, N, A, I, R; 13 chrome mic grille disc; 14 its pin holes;
15 its raised rim; 16 FORCE key cap, domed; 17 raised ring round the key;
18 "MIC" legend; 19 "FORCE" legend; 20 "ATECH" on the chin; 21 brushed desk
foot, tapered; 22 its rolled top edge; 23-26 four rubber feet; 27-28 two
keyholes in the back; 29 USB-C socket in the back; 30 four countersunk
screws in the back; 31 the model plate lettering on the back.
Inside: the panel's flange and spine rib, the bezel flange, the mic seal
tube, board ledges and standoffs, the USB-C bay and holder ribs, insert
sleeves on long screw columns, keyhole pads, foot bosses with inserts.
Materials: graphite housing, chrome bezel, grille and screws, red frosted
panel, warm-white frosted letters, signal-red key, brushed aluminium foot, rubber feet.
Hardware: one screw type, M2.5 countersunk Phillips (ISO 10642): 4 x 10
(back to front, into M2.5 heat-set inserts), 2 x 16 (foot to back, into
inserts). 4 rubber feet 10 mm. Two wall screws (head <= 8 mm) for the
keyholes. On the wall, a right-angle USB-C plug clears the wall.
MEASURED (R990, 2026-11-17): ./check CHECK PASS, run_seconds 18 s, wall 42 s; every RESTYLE end CHECK PASS.
"""
import math
import os
import time
import Part
import FreeCAD as App
import atech_ports as ap
import atech_cad as cad
from FreeCAD import Vector, Placement, Rotation
V = Vector
T0 = time.time()

INTENT = {"board": "upright", "fitted_after": [
    "Front", "Bezel", "Panel", "Letter_O", "Letter_N", "Letter_A", "Letter_I", "Letter_R",
    "Mic_Grille", "Force_Key", "Desk_Foot", "Foot_1", "Foot_2", "Foot_3", "Foot_4",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4", "Screw_Foot_1", "Screw_Foot_2"],
    "covers": {"Force_Key": "button_p10"}}
REVIEW_CLOSEUPS = ["Panel", "Mic_Grille", "Back"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them; test_kit_examples_r280 builds
# this file with each knob at its min and at its max, one at a time.
WIDTH = 200.0      # RESTYLE 170..230 width: the box across (x)
PANEL_H = 42.0     # RESTYLE 35.7..48.3 height: the red window (z); the box grows with it
DEPTH = 50.0       # RESTYLE 42.5..57.5 length: the box, front face to back face (y)
CORNER = 22.0      # RESTYLE 18.7..25.3 radius: the box's corners, seen from the front
WALL = 2.4         # RESTYLE 2.0..2.8 wall
# end RESTYLE
# Box frame: x across (the viewer's right +), y from the viewer (-) to the
# back (+), z up; the rubber feet on z = 0. The board is x-centred, the
# lights 10 mm behind the panel at DEPTH 50.
RUB, FOOT_T = 2.0, 9.0           # rubber feet, the desk foot's thickness
ZB = RUB + FOOT_T                # the box's bottom (on the foot)
Z0 = ZB + WALL + 3.6             # the board's bottom: room for the ledge over the split lip
BX0 = WIDTH / 2 - 55.0           # the board's left end: the mic and the key mirror the centre
EDGE = 3.0                       # the rolled front edge
M_SIDE = WALL + 9.5              # housing rim beside the bezel (screw columns, the bezel flange)
M_TOP = WALL + 2.6               # rim over the bezel
BZW = 4.0                        # the chrome bezel's width
LIP = 2.0                        # the bezel lip proud of the face (the panel's recess)
WZ0 = Z0 + 25.0                  # the window's bottom: the chin under it holds the mic and the key
WZ1 = WZ0 + PANEL_H
ZT = WZ1 + BZW + M_TOP           # the box's top
USB_Y = 15.0                     # the USB-C module's centre behind the board (MEASURED: its ribbon clears the board)
YB = USB_Y + 9.88 + 1.5          # the back face: 1.5 mm behind the module's mouth (fixed by the hardware)
YF = YB - DEPTH                  # the front face
PANEL_BACK = 1.2                 # the panel's flange behind the wall
LETTER_H = 0.6 * PANEL_H         # ON AIR cap height
POCKET, RAISE = 1.2, 1.0         # letters: inlaid depth, proud of the panel
CLOSE_R = 0.9                    # glyph gaps under 1.8 mm filled: no panel sliver between pockets
MIC_R, MIC_GRILLE = 9.6, 15.0    # the chrome grille disc; its pin-hole field (>= 3 % open)
KEY_D = 12.0
SCREW = "M2.5"
INSERT_D = 3.6                   # M2.5 heat-set insert pocket (1.4 d + 0.1)
COLOURS = {"Front": "#2e2f33", "Back": "#2e2f33", "Bezel": "chrome", "Panel": "#e3241b",
           "Letter": "#fff3e0", "Mic_Grille": "chrome", "Force_Key": "signal_red",
           "Desk_Foot": "brushed_alu", "Foot": "rubber", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
LANDSCAPE_FRONT = Rotation(Vector(0, 0, 1), 180).multiply(Rotation(Vector(0, 1, 0), 90))
board = ap.board_object(doc)


def place_board(rot, x0=0.0, y0=None, z0=0.0):
    board.Placement = Placement(Vector(), rot)
    bb = ap.bbox(board)
    board.Placement = Placement(Vector(x0 - bb.XMin, 0 if y0 is None else y0 - bb.YMin,
                                       z0 - bb.ZMin), rot)


place_board(LANDSCAPE_FRONT, BX0, None, Z0)     # x BX0..BX0 + 120, z Z0..Z0 + 60, modules face -Y
BB = ap.bbox(board)
lights = [ap.seat(doc, "light", p) for p in (6, 5, 4, 3, 2, 1)]   # the top row, left to right
mic = ap.seat(doc, "microphone", (13, 14))      # bottom left: hears the room through the chin
key = ap.seat(doc, "button", 10)                # bottom right: FORCE ON
# USB-C: CABLED from port 7 (the right end) round the board's edge to the
# back, standing on edge (face -X: twist-free), its mouth 1.5 mm inside
# the back face
usb, usb_rib = ap.cable(doc, "usbc", 7, ap.module_placement(
    "usbc", (BX0 + 126.0, USB_Y, Z0 + 20.0), face="-X", cable="-Y"))
tick("hardware")


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, -1, 0)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def centre(m):
    b = ap.bbox(m)
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


def yslab(x0, x1, z0, z1, r, y0, y1):
    """A rounded rectangle x0..x1 x z0..z1 (corner r), from y0 to y1."""
    return cad.rounded_box(x1 - x0, abs(y1 - y0), z1 - z0, r, at=(x0, min(y0, y1), z0), edges="y")


def insert(shell, cutter):
    """(shell with the opening, the piece that fills it exactly)."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1:
        piece, rest = shell.common(cutter, 0.01), shell.cut(cutter, 0.01)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, piece


def zprism(x0, x1, y0, y1, z0, z1, r):
    w = cad.rounded_rect_wire(x1 - x0, y1 - y0, r, ((x0 + x1) / 2, (y0 + y1) / 2, z0), "Z")
    return Part.Face(w).extrude(V(0, 0, z1 - z0))


def inside_rr(x, z, x0, z0, x1, z1, r):
    """True when (x, z) lies inside the rounded rectangle."""
    cx, cz = min(max(x, x0 + r), x1 - r), min(max(z, z0 + r), z1 - r)
    return x0 <= x <= x1 and z0 <= z <= z1 and math.hypot(x - cx, z - cz) <= r


# ------------------------------------------------------------ the box
X1 = WIDTH
shell = cad.rounded_box(WIDTH, DEPTH, ZT - ZB, CORNER, at=(0, YF, ZB), edges="y")
shell = cad.fillet_safe(shell, EDGE, edges=[e for e in shell.Edges if e.BoundBox.YMax < YF + 0.01])
shell = cad.fillet_safe(shell, 1.5, edges=[e for e in shell.Edges if e.BoundBox.YMin > YB - 0.01])
# the core keeps SHARP inner edges (a filleted core reads as clip channels)
core = cad.rounded_box(WIDTH - 2 * WALL, DEPTH - 2 * WALL, ZT - ZB - 2 * WALL, CORNER - WALL,
                       at=(WALL, YF + WALL, ZB + WALL), edges="y")
shell = cad.cut(shell, core)
tick("box")
# the split stays behind the modules (their slide paths) and the board's
# back: the back is the fixed half, the front (lip side) is fitted after
SPLIT_Y = BB.YMax - 0.3
front, back = cad.split(shell, "Y", at=SPLIT_Y, lip=1.2)
tick("split")

# ------------------------------------------------------------ the back holds the board
YI = YB - WALL + 0.5                       # into the back wall
add = [box(BX0 + 4, BX0 + 116, 0.6, 12.0, BB.ZMin - 2.3, BB.ZMin - 0.3),         # under the board
       box(BX0 + 4, BX0 + 116, 0.6, YI, BB.ZMax + 0.3, BB.ZMax + 2.3)]           # over it
# the bottom ledge stands on the back's floor (legs behind the split lip)
add += [box(BX0 + x, BX0 + x + 8, 4.5, 12.0, ZB + WALL - 0.5, BB.ZMin - 2.0) for x in (6, 56, 104)]
add += [box(BX0 + x, BX0 + x + 6, BB.YMax + 0.1, YI, Z0 + z, Z0 + z + 6) for x in (10, 55, 88) for z in (12, 44)]
# the USB-C module: a bay in the back wall (1.25 mm left in front of its
# mouth) and a rib either side (0.3 mm off; the ribbon comes in at its front)
UB = ap.bbox(usb)
MOUTH_Y = UB.YMax
add += [box(UB.XMin - 1.9, UB.XMin - 0.3, UB.YMin + 3.0, YI, UB.ZMin + 2.0, UB.ZMax - 2.0),
        box(UB.XMax + 0.3, UB.XMax + 1.9, UB.YMin + 3.0, YI, UB.ZMin + 2.0, UB.ZMax - 2.0)]
# two keyhole pads (the wall screws' heads run in them) and two bosses in
# the floor for the desk foot's screws (heat-set inserts from below)
KEYS = [(WIDTH / 2 - 0.3 * WIDTH, Z0 + 38.0), (WIDTH / 2 + 0.3 * WIDTH, Z0 + 38.0)]
add += [box(kx - 8.0, kx + 8.0, YB - 6.5, YI, kz - 6.0, kz + 14.0) for kx, kz in KEYS]
FOOT_SCREWS = [(BX0 + 8.0, 16.0), (BX0 + 112.0, 16.0)]
add += [cyl(3.0, (fx, fy, ZB + WALL - 0.5), 10.0 - WALL + 0.5, (0, 0, 1)) for fx, fy in FOOT_SCREWS]
back = cad.fuse_one(back, *add)
bay = box(UB.XMin - 0.3, UB.XMax + 0.3, UB.YMin + 3.0, MOUTH_Y + 0.25, UB.ZMin - 0.3, UB.ZMax + 0.3)
# the plug opening: the mouth MEASURED from the module's mesh (its last
# 0.6 mm along +Y) plus 1.5 mm a side (socket_opening assumes the board plane)
MP = [p for p in usb.Mesh.Points if p.y > UB.YMax - 0.6]
MX0, MX1 = min(p.x for p in MP), max(p.x for p in MP)
MZ0, MZ1 = min(p.z for p in MP), max(p.z for p in MP)
plug = Part.Face(cad.rounded_rect_wire(MX1 - MX0 + 3.0, MZ1 - MZ0 + 3.0, 2.0,
                                       ((MX0 + MX1) / 2, MOUTH_Y + 0.05, (MZ0 + MZ1) / 2), "Y"))
back = cad.cut(back, [bay, plug.extrude(V(0, YB - MOUTH_Y + 2.0, 0))])
for fx, fy in FOOT_SCREWS:
    back = cad.cut(back, [cyl(INSERT_D / 2, (fx, fy, ZB - 1.0), 6.0, (0, 0, 1)),
                          cyl(2.1 / 2, (fx, fy, ZB + 4.5), 4.5, (0, 0, 1))])
tick("back")

# ------------------------------------------------------------ screws back -> front
# two in the chin's corners (on the corner's diagonal, 1.5 mm inside the
# rounded inner wall) and two in the side margins beside the window
d_c = (CORNER - WALL - 4.5) / math.sqrt(2.0)
SCREWS = [(CORNER - d_c, ZB + CORNER - d_c), (WIDTH - CORNER + d_c, ZB + CORNER - d_c),
          (WALL + 4.5, (WZ0 + WZ1) / 2), (WIDTH - WALL - 4.5, (WZ0 + WZ1) / 2)]
screws = []
yb = YB - WALL - 0.1
SCREW_L = int(round(WALL + 7.6))
for x, z in SCREWS:
    back, front = cad.screw_through(back, front, (x, YB, z), size=SCREW, ribs=0)
    front = cad.fuse_one(front, cyl(INSERT_D / 2 + 1.2, (x, yb, z), 10.0))
    front = cad.cut(front, cyl(INSERT_D / 2, (x, yb + 0.5, z), 6.0))
    screws.append(cad.screw("csk_phillips", SCREW, SCREW_L, at=(x, YB, z), axis="-Y"))
tick("screws")

# ------------------------------------------------------------ the face
# the chrome bezel: an insert in the front wall, a raised lip, a flange
# behind the wall; its corner radius the largest that keeps the flange
# inside the rounded core
BX_0, BX_1, BZ_0, BZ_1 = M_SIDE, WIDTH - M_SIDE, WZ0 - BZW, ZT - M_TOP
RB = 14.0
while RB > BZW + 2.0:
    c = (BX_0 + RB, BZ_1 - RB)
    pts = [(c[0] - (RB + 1.5) * math.cos(a), c[1] + (RB + 1.5) * math.sin(a))
           for a in [i * math.pi / 16 for i in range(9)]]
    if all(inside_rr(px, pz, WALL + 0.3, ZB + WALL + 0.3, WIDTH - WALL - 0.3, ZT - WALL - 0.3,
                     CORNER - WALL - 0.3) for px, pz in pts):
        break
    RB -= 0.5
RW = RB - BZW                                     # the window's corners
WX0, WX1 = BX_0 + BZW, BX_1 - BZW
front, bezel = insert(front, yslab(BX_0, BX_1, BZ_0, BZ_1, RB, YF - 1, YF + WALL + 1))
bezel = cad.fuse_one(bezel, cad.cut(yslab(BX_0, BX_1, BZ_0, BZ_1, RB, YF - LIP, YF + 0.5),
                                    yslab(WX0, WX1, WZ0, WZ1, RW, YF - LIP - 1, YF + 1)))
_hole = yslab(WX0 - 1.2, WX1 + 1.2, WZ0 - 1.2, WZ1 + 1.2, RW + 1.2, YF + WALL - 1, YF + WALL + 2)
bezel = cad.fuse_one(bezel, cad.cut(yslab(BX_0 - 1.5, BX_1 + 1.5, BZ_0 - 1.5, BZ_1 + 1.5, RB + 1.5,
                                          YF + WALL, YF + WALL + 0.8), _hole),
                     cad.cut(yslab(BX_0 + 0.5, BX_1 - 0.5, BZ_0 + 0.5, BZ_1 - 0.5, RB - 0.5,
                                   YF + WALL - 0.3, YF + WALL + 0.5), _hole))
bezel = cad.soften(bezel, 0.8, [e for e in bezel.Edges if e.BoundBox.YMax < YF - LIP + 0.01])
# the red panel: an insert in the bezel's window, a flange behind it and a
# rib onto the board's spine (0.2 mm off) - frosted, so the rib glows too
bezel, panel = insert(bezel, yslab(WX0, WX1, WZ0, WZ1, RW, YF - LIP - 1, YF + WALL + 1))
panel = cad.fuse_one(panel, yslab(WX0, WX1, WZ0, WZ1, RW, YF + WALL - 0.3, YF + WALL + PANEL_BACK),
                     yslab(WX0 - 1.0, WX1 + 1.0, WZ0 - 1.0, WZ1 + 1.0, RW + 1.0, YF + WALL, YF + WALL + PANEL_BACK),
                     box(BX0 + 55, BX0 + 61, YF + WALL + PANEL_BACK - 0.5, BB.YMin - 0.2, WZ0 + 0.6, WZ0 + 3.0))
tick("bezel + panel")
# the microphone: a chrome grille disc (an insert in the chin), pin holes
# over the mic, a raised rim, a seal tube behind it to 0.3 mm off the mic
mx, _my, mz = centre(mic)
mb = ap.bbox(mic)
front, grille = insert(front, cyl(MIC_R, (mx, YF + WALL + 1, mz), WALL + 2))
grille = cad.fuse_one(grille, cad.cut(cyl(MIC_R, (mx, YF + 0.3, mz), 1.1), cyl(MIC_GRILLE / 2 + 0.5, (mx, YF + 1, mz), 3)),
                      cad.cut(cyl(MIC_R - 0.2, (mx, mb.YMin - 0.3, mz), (mb.YMin - 0.3) - (YF + WALL - 0.5)),
                              cyl(MIC_GRILLE / 2 + 0.3, (mx, mb.YMin, mz), (mb.YMin) - YF + 1)))
grille = cad.speaker_grille(grille, (mx, YF, mz), (0, -1, 0), MIC_GRILLE, ring_pitch=2.6, hole=1.6)
# the FORCE key: a cap through the chin, flange 0.1 mm behind the wall, a
# plunger to 0.16 mm off the button's own cap
kx, _ky, kz = centre(key)
kb = ap.bbox(key)
y_base = YF + WALL + 0.9
cap = cad.button_cap(KEY_D, y_base - (YF - 1.8), dome=0.8, flange=1.5, at=(kx, y_base, kz), axis="-Y")
front = cad.opening_for(front, cap, clearance=0.25, chamfer=0.4, axis="-Y")
cap = cad.fuse_one(cap, cyl(3.0, (kx, kb.YMin - 0.16, kz), (kb.YMin - 0.16) - y_base + 0.5))
tick("mic + key")

# ------------------------------------------------------------ the desk foot
# a solid tapered plinth (weight), wider than the box is deep, two M2.5
# screws up into the back's floor inserts, four rubber feet in recesses
FW = (FOOT_SCREWS[1][0] - FOOT_SCREWS[0][0]) + 26.0
FCX = (FOOT_SCREWS[0][0] + FOOT_SCREWS[1][0]) / 2
FD0, FD1 = DEPTH + 12.0, DEPTH - 2 * EDGE - 3.0
FCY = (YF + YB) / 2
foot = cad.loft([cad.rounded_rect_wire(FW + 10.0, FD0, 12.0, (FCX, FCY, RUB), "Z"),
                 cad.rounded_rect_wire(FW, FD1, 8.0, (FCX, FCY, ZB), "Z")], ruled=True)
foot = cad.soften(foot, 2.0, [e for e in foot.Edges if e.BoundBox.ZMin > ZB - 0.05])
FEET = [(FCX + sx * (FW / 2 - 4.0), FCY + sy * (FD0 / 2 - 8.0)) for sx in (-1, 1) for sy in (-1, 1)]
foot = cad.cut(foot, [cyl(5.1, (x, y, RUB - 1.0), 2.5, (0, 0, 1)) for x, y in FEET])
feet = [cad.foot(10, RUB + 1.5, style="dome", at=(x, y, RUB + 1.5)) for x, y in FEET]
FOOT_L = int(FOOT_T + 7.0)                  # stock 16: the tip 1 mm past the insert, in the pilot
foot_screws = []
for fx, fy in FOOT_SCREWS:
    foot = cad.countersink(foot, (fx, fy, RUB), "+Z", 2.9, 4.9, 90.0)
    foot_screws.append(cad.screw("csk_phillips", SCREW, FOOT_L, at=(fx, fy, RUB), axis="+Z"))
tick("stage A")


# === STAGE B: details ===
# ON AIR: five raised letters (each its own frosted part) inlaid POCKET
# deep into the panel, RAISE proud of it - one font, centred in the window
_fonts = [os.path.join(App.getHomePath(), "fonts", f) for f in ("Ubuntu-B.ttf", "DejaVuSans.ttf")]
_fonts += ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
FONT = next(f for f in _fonts if os.path.isfile(f))
_probe = Part.makeFace(Part.makeWireString("N", FONT, 10.0)[0], "Part::FaceMakerBullseye")
_scale = LETTER_H / _probe.BoundBox.YLength
chars = list(zip([c for c in "ON AIR" if c != " "],
                 [Part.makeFace(w, "Part::FaceMakerBullseye")
                  for w in Part.makeWireString("ON AIR", FONT, 10.0 * _scale) if w]))
_tb = chars[0][1].BoundBox
for _ch, f in chars[1:]:
    _tb.add(f.BoundBox)
PX, PZ = (WX0 + WX1) / 2, (WZ0 + WZ1) / 2
letters = {}
def closed(f, r=CLOSE_R):
    """The glyph with every gap under 2 r filled (offset out, then back):
    the N's acute counters would leave knife-edge panel slivers between
    their pocket walls (MEASURED 0.50 mm at WIDTH 230)."""
    try:
        g = f.makeOffset2D(r, 0).makeOffset2D(-r, 0)
        g = g.Faces[0] if g.Faces else None
        if g is not None:   # re-knot as straight facets: a filled tip's arc reads as a channel
            ws = []
            for w in g.Wires:
                pts = w.discretize(QuasiDeflection=0.03)
                if (pts[0] - pts[-1]).Length > 1e-6:
                    pts.append(pts[0])
                ws.append(Part.makePolygon(pts))
            g = Part.makeFace(ws, "Part::FaceMakerBullseye")
        if g is not None and g.isValid() and f.Area - 0.5 < g.Area < f.Area * 1.06:
            return g
    except Exception as exc:                                  # noqa: BLE001
        print("NOTE glyph closing: %s" % exc)
    return f


for ch, f in chars:
    s = closed(f).extrude(V(0, 0, POCKET + RAISE))
    s.translate(V(-_tb.Center.x, -_tb.Center.y, -POCKET))
    s.rotate(V(0, 0, 0), V(1, 0, 0), 90)                      # local z (toward the reader) -> -Y
    s.translate(V(PX, YF, PZ))
    letters["Letter_" + ch] = s
panel = cad.cut(panel, list(letters.values()))
# the front / back reveal, a raised ring round the key, legends
front = cad.groove_ring(front, "Y", SPLIT_Y - 2.0, w=0.8, depth=0.6)
front = cad.fuse_one(front, cad.cut(cyl(KEY_D / 2 + 3.0, (kx, YF + 0.5, kz), 1.1),
                                    cyl(KEY_D / 2 + 1.6, (kx, YF + 1.0, kz), 2.0)))
front = cad.text(front, "MIC", (mx - MIC_R - 9.0, YF, mz), (0, -1, 0), 4, depth=0.4, mode="deboss")
front = cad.text(front, "FORCE", (kx + KEY_D / 2 + 15.0, YF, kz), (0, -1, 0), 4, depth=0.4, mode="deboss")
front = cad.text(front, "ATECH", (WIDTH / 2, YF, kz), (0, -1, 0), 4.5, depth=0.4, mode="deboss")
# the keyholes in the back: the wall screw's head goes in the round hole,
# the sign drops onto it, the head runs in a pocket in the pad
for kxh, kz0 in KEYS:
    back = cad.cut(back, [cyl(4.2, (kxh, YB + 1, kz0), 5.5),
                          box(kxh - 2.2, kxh + 2.2, YB + 1, YB - 2.0, kz0, kz0 + 9),
                          box(kxh - 4.2, kxh + 4.2, YB - 2.0, YB - 4.5, kz0, kz0 + 9)])
back = cad.text(back, "ATECH ON AIR", (WIDTH / 2, YB, ZB + 0.35 * (ZT - ZB)), (0, 1, 0), 5, depth=0.4,
                mode="deboss")
foot = cad.groove_ring(foot, "Z", RUB + 0.45 * FOOT_T, w=1.0, depth=0.6)
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape, colour=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = cad.color(COLOURS[colour or name])
    return o


for nm, sh in (("Back", back), ("Front", front), ("Bezel", bezel), ("Mic_Grille", grille),
               ("Desk_Foot", foot)):
    part(nm, sh)
part("Force_Key", cap)
o = part("Panel", panel)
o.ViewObject.Transparency = cad.transparency("frosted")
for nm, sh in letters.items():
    o = part(nm, sh, "Letter")
    o.ViewObject.Transparency = cad.transparency("frosted")
for i, sh in enumerate(feet):
    part("Foot_%d" % (i + 1), sh, "Foot")
for i, sh in enumerate(screws):
    part("Screw_%d" % (i + 1), sh, "Screw")
for i, sh in enumerate(foot_screws):
    part("Screw_Foot_%d" % (i + 1), sh, "Screw")
print("SIZE", cad.measure(Part.makeCompound([o.Shape for o in doc.Objects if hasattr(o, "Shape")
                                             and o.TypeId == "Part::Feature"]))["size"])
print("TOTAL %.1f s" % (time.time() - T0))
