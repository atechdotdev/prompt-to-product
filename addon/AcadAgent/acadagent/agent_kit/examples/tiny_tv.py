"""Example: "a tiny retro TV" - a 1960s mini CRT television that plays GIFs and clips on its big screen.

fork this file for a retro TV / mini television / desktop CRT (a tiny TV
that loops GIFs, a retro monitor, a vintage radio-TV - any cabinet with a
big screen in a chrome frame, a tuner dial and a speaker grille, on
legs); change PARAMETERS and the outlines.
ARCHETYPE: retro tv

How it is built (R940):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board UPRIGHT_FRONT at the back of the front box (modules face the
    viewer, -Y); the BIG SCREEN SEATS on the top of the left column (13,
    14) and hangs 40 mm out past the board's left edge, landscape, facing
    front; the speaker on (9, 10) under it; on the right column the KNOB
    (4, 5) - the channel dial, hanging 20 mm past the right edge - the
    pilot light (3) and the power button (1). USB-C SEATS on port 7, its
    mouth down through a pocket in the floor (a measured socket mouth must
    lie in the board's plane, so an upright board cannot point it
    straight back): the plug goes in between the legs. The
    cabinet is a rounded front box (CORNER radius on the four edges along
    the depth, the front edge rolled) and a CRT "hump" lofted to a smaller
    back with a flat bottom, hollowed with its own inset core and split
    behind the board into the Shell (fitted after: the modules' slide
    paths run through its walls) and the fixed Back (a bulkhead across
    the hump, pads behind the board and the overhangs, edge fences).
    Four M2.5 screws from the back shoulder into bosses on the Shell's
    walls.
  * STAGE B - details: the chrome CRT bezel standing proud, a black mask
    tunnel to the screen holding a domed acrylic block, a chrome slot grille, a dial
    crown with a chrome rim, ticks, a frosted ring and a knurled cap, a
    red jewel pilot light and the power key on a chrome control plate,
    the brand badge, a reveal line round the front box, rabbit-ear
    antenna, back vents, four splayed peg legs with brass ferrules.
RESTYLE (R425): WIDTH, HEIGHT, DEPTH, CORNER and WALL drive the box, the
hump and every cutter; the hardware (the board, the screen hanging left,
the dial hanging right) sets a floor the cabinet never shrinks below
(printed as FLOOR). The hardware frame is the board's own: never move it
with a knob.
DETAILS (visible, 30): 1 rounded front box; 2 rolled front edge; 3 CRT
hump tapering to the back; 4 chrome CRT bezel 2.5 mm proud; 5 black mask
tunnel; 6 domed acrylic "CRT" block on the screen; 7 rounded screen window; 8 chrome
speaker grille plate 1 mm proud; 9 its vertical slots; 10 brand badge;
11 "ATECH" on it; 12 dial crown; 13 chrome dial rim; 14-25 twelve
channel ticks on the rim; 26 knurled cream dial cap with a pointer;
27 frosted ring round the dial; 28 red jewel pilot light and 29 the power
key on a chrome control plate hugging the dial (ON / TV legends);
30 rabbit-ear antenna (hub, two telescoping rods, ball tips).
More: a reveal line round the front box, back vent slots, USB-C pocket
in the floor, four splayed peg legs with brass ferrules, four screws in
the back shoulder.
Inside: bulkhead, board pads and fences, pads behind the screen and the
speaker overhangs, a rib onto the board's spine, the USB-C liner, screw
bosses, leg bosses, the Shell / Back lip.
Materials: walnut wood Shell, dark-walnut Back and legs, chrome bezel,
grille, badge, dial rim, antenna and screws, black mask, glass, cream dial
cap and power key, frosted ring, red jewel, brass ferrules.
MEASURED (R940, 2026-11-10): ./check CHECK PASS, model 7 s, ./check wall 27 s.
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
    "Shell", "Bezel", "Mask", "Glass", "Grille", "Badge", "Control_Plate", "Dial_Bezel", "Dial_Ring", "Dial_Cap", "Jewel",
    "Power_Key", "Antenna_Hub", "Antenna_L", "Antenna_R",
    "Leg_1", "Leg_2", "Leg_3", "Leg_4", "Ferrule_1", "Ferrule_2", "Ferrule_3", "Ferrule_4",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4"],
    # the key presses the power button, the jewel carries the pilot light,
    # the acrylic block sits on the display
    "covers": {"Power_Key": "button_p1", "Jewel": "light_p3", "Glass": "big_screen_p13_14"}}
REVIEW_CLOSEUPS = ["Glass", "Dial_Cap", "Grille"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them. The hardware sets a floor
# under WIDTH and HEIGHT (printed as FLOOR).
WIDTH = 144.0      # RESTYLE 122..166 width: the cabinet across (x)
HEIGHT = 146.0     # RESTYLE 124..168 height: the cabinet's bottom to its top (z)
DEPTH = 82.0       # RESTYLE 68..96 length: the front face to the back of the hump (y)
CORNER = 18.0      # RESTYLE 15..21 radius: the front box's corners
WALL = 2.5         # RESTYLE 2.1..2.9 wall
# end RESTYLE
# Cabinet frame: x across (the viewer's right = +X), y from the screen
# (-Y) to the back, z up; the desk at z = 0 under the legs.
LEG_H = 30.0                   # the cabinet's underside over the desk
SPLAY = 11.0                   # each leg leans out this much (deg)
UNDER = 4.0                    # the floor's inner face under the board (the USB-C pocket's liner)
BOX_D = 35.0                   # the front box's depth (the hump behind it)
INSET = 12.0                   # the hump starts this far in from the box's sides and top
EDGE = 4.0                     # the front edge's roll
BZ = (77.0, 57.0, 10.0)        # chrome bezel w, h, corner r
MASK = (69.0, 49.0, 7.0)       # the mask tunnel's outside (the bezel's opening)
WIN = (63.0, 43.0, 5.0)        # the screen window (the display is 59.7 x 39.5)
BZ_PROUD = 2.5                 # the bezel stands this proud of the face
DOME = 2.0                     # the glass bulges this much
CAP_R, DISH_R, RIM_R, FOOT_R = 11.0, 17.5, 20.5, 22.5   # dial cap, well, crown rim, crown foot
RING_R = (8.05, 13.5)          # the frosted ring round the dial shaft
KEY_D = 12.0
SCREW = "M2.5"
COLOURS = {"Shell": "wood", "Back": "#4a2f1c", "Chrome": "chrome", "Mask": "#0b0c0e", "Glass": "glass",
           "Cap": "cream", "Ring": "frosted", "Jewel": "led_red", "Leg": "#4a2f1c", "Ferrule": "brass"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
ZBOT = LEG_H                                     # the cabinet's underside
ZB = ZBOT + WALL + UNDER                         # the board's bottom edge
UPRIGHT_FRONT = Rotation(Vector(0, 0, 1), 180)   # portrait, modules face -Y, 1-6 on the right
board = ap.board_object(doc)
board.Placement = Placement(Vector(), UPRIGHT_FRONT)
_b = ap.bbox(board)
board.Placement = Placement(Vector(-_b.XMin, -_b.YMin, ZB - _b.ZMin), UPRIGHT_FRONT)   # x 0..60, y 0..7
BB = ap.bbox(board)
scr = ap.seat(doc, "big_screen", (13, 14))       # top left, hangs 40 mm out to the left
spk = ap.seat(doc, "speaker", (9, 10))           # under the screen
knob = ap.seat(doc, "knob", (4, 5))              # the channel dial, hangs 20 mm out to the right
lamp = ap.seat(doc, "light", 3)                  # the pilot light
btn = ap.seat(doc, "button", 1)                  # power
SB, SPB, KB, LB, NB = [ap.bbox(m) for m in (scr, spk, knob, lamp, btn)]
# the cabinet, measured from the hardware: the front 0.8 mm off the speaker
YF = SPB.YMin - 0.8 - WALL                       # the front face
YS = YF + BOX_D                                  # the box's back (the shoulder)
YH = YF + max(DEPTH, 64.0)                       # the hump's back
SCX, SCZ = (SB.XMin + SB.XMax) / 2, (SB.ZMin + SB.ZMax) / 2
XL = SCX - BZ[0] / 2 - 7.0                       # the hardware floor: the bezel 7 mm in from the left
XR = KB.XMax + 5.0 + WALL                        # the dial 5 mm in from the right
W = max(WIDTH, XR - XL)
XC = (XL + XR) / 2
X0, X1 = XC - W / 2, XC + W / 2
ZTOP = max(ZBOT + HEIGHT, SCZ + BZ[1] / 2 + 6.5, BB.ZMax + 4.0 + WALL)
H = ZTOP - ZBOT
print("FLOOR cabinet %.1f x %.1f x %.1f (knobs %.1f x %.1f x %.1f)" % (W, YH - YF, H, WIDTH, DEPTH, HEIGHT))
usb = ap.seat(doc, "usbc", 7)                    # bottom centre, mouth -Z: under the cabinet
UB = ap.bbox(usb)
tick("hardware")


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, d, h):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def yprism(x0, x1, z0, z1, r, y0, y1):
    """A rounded rectangle in (x, z) extruded along Y from y0 to y1."""
    w = cad.rounded_rect_wire(x1 - x0, z1 - z0, r, ((x0 + x1) / 2, y0, (z0 + z1) / 2), "Y")
    s = Part.Face(w).extrude(V(0, y1 - y0, 0))
    if s.Volume < 0:
        s.reverse()
    return s


def yrect(cx, cz, w, h, r, y0, y1):
    return yprism(cx - w / 2, cx + w / 2, cz - h / 2, cz + h / 2, r, y0, y1)


def ring_y(c, r0, r1, y0, y1):
    """An annulus on the Y axis through c = (x, z), from y0 to y1."""
    (y0, y1) = sorted((y0, y1))
    return cad.cut(cyl(r1, (c[0], y0, c[1]), (0, 1, 0), y1 - y0), cyl(r0, (c[0], y0 - 1, c[1]), (0, 1, 0), y1 - y0 + 2))


def centre(b):
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


def insert(shell, cutter):
    """(shell with the opening, the piece that fills it exactly)."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1:
        piece, rest = shell.common(cutter, 0.01), shell.cut(cutter, 0.01)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, piece


def section(x0, x1, z0, z1, r, y):
    return cad.rounded_rect_wire(x1 - x0, z1 - z0, r, ((x0 + x1) / 2, y, (z0 + z1) / 2), "Y")


# ------------------------------------------------------------ the cabinet
# the front box (rounded on the four edges along the depth, front edge
# rolled) and the CRT hump lofted from the box's back to a smaller back
# panel - its bottom stays flat on the box's bottom plane
front_box = yprism(X0, X1, ZBOT, ZTOP, CORNER, YF, YS)
front_box = cad.fillet_safe(front_box, EDGE, edges=[e for e in front_box.Edges if e.BoundBox.YMax < YF + 0.01])
front_box = cad.fillet_safe(front_box, 1.0, edges=[e for e in front_box.Edges if e.BoundBox.YMin > YS - 0.01])
BW, BH = 0.68 * W, 0.70 * H                       # the back panel
HR0, HR1 = CORNER - 6.0, max(4.0, CORNER - 9.0)   # the hump's corner radii, front and back
HF = (X0 + INSET, X1 - INSET, ZBOT, ZTOP - INSET)
HB = (XC - BW / 2, XC + BW / 2, ZBOT, ZBOT + BH)
hump = Part.makeLoft([section(*HF, HR0, YS - 1.0), section(*HB, HR1, YH)], True, True)
outer = cad.fuse_one(front_box, hump)
core = cad.fuse_one(
    yprism(X0 + WALL, X1 - WALL, ZBOT + WALL, ZTOP - WALL, CORNER - WALL, YF + WALL, YS - WALL),
    Part.makeLoft([section(HF[0] + WALL, HF[1] - WALL, ZBOT + WALL, HF[3] - WALL, HR0 - WALL, YS - WALL - 0.5),
                   section(HB[0] + WALL, HB[1] - WALL, ZBOT + WALL, HB[3] - WALL, HR1 - WALL, YH - WALL)],
                  True, True))
cabinet = cad.cut(outer, core)
tick("cabinet")
SPLIT_Y = BB.YMax + 4.0                           # behind the board, in the box's cavity
shell, back = cad.split(cabinet, "Y", at=SPLIT_Y, lip=1.2)
tick("split")

# ------------------------------------------------------------ the Back holds the board
# a bulkhead across the hump (notched for the USB-C ribbon), pads 0.1 mm
# behind the board and behind the screen's and the speaker's overhangs,
# fences 0.3 mm off the board's edges (behind every module's slide path:
# those end at the PCB's face, y <= 4.5)
YK = YS + 0.5                                     # the bulkhead's front face
bulk = box(X0, X1, YK, YK + 2.0, ZBOT - 1, ZTOP + 1).common(hump)
YP = BB.YMin + 4.8                                # the pads' front: off the PCB's face
pads = [box(x, x + 6, BB.YMax + 0.1, YK + 0.5, BB.ZMin + z, BB.ZMin + z + 6)
        for x in (8, 46) for z in (8, 106)]
pads += [box(SB.XMin + 10, SB.XMin + 16, SB.YMax + 0.3, YK + 0.5, SCZ - 6, SCZ + 6),
         box(SPB.XMin + 6, SPB.XMin + 12, SPB.YMax + 0.3, YK + 0.5, (SPB.ZMin + SPB.ZMax) / 2 - 6,
             (SPB.ZMin + SPB.ZMax) / 2 + 6)]
fences = [box(BB.XMin - 1.8, BB.XMin - 0.3, YP, YK + 0.5, BB.ZMin + 44, BB.ZMin + 76),
          box(BB.XMax + 0.3, BB.XMax + 1.8, YP, YK + 0.5, BB.ZMin + 22, BB.ZMin + 38),
          box(BB.XMax + 0.3, BB.XMax + 1.8, YP, YK + 0.5, BB.ZMin + 102, BB.ZMin + 118),
          box(BB.XMin + 4, BB.XMin + 18, YP, YK + 0.5, BB.ZMin - 2.3, BB.ZMin - 0.3),
          box(BB.XMax - 18, BB.XMax - 4, YP, YK + 0.5, BB.ZMin - 2.3, BB.ZMin - 0.3),
          box(BB.XMin + 22, BB.XMax - 22, YP, YK + 0.5, BB.ZMax + 0.3, BB.ZMax + 2.3)]
back = cad.fuse_one(back, bulk, *pads, *fences)
# board retention from the front: a rib from the face onto the spine
shell = cad.fuse_one(shell, box(25, 35, YF + WALL - 0.5, BB.YMin - 0.2, BB.ZMin + 45, BB.ZMin + 58))
tick("back")

# ------------------------------------------------------------ fasteners
# four M2.5 screws from the back shoulder (y = YS) into bosses that merge
# with the Shell's walls; each boss stops 2 mm short of the split (clear
# of the lip and the Back), so the screw spans that gap into its pilot
SCREWS = [(X0 + WALL + 1.0, BB.ZMin + 40.0), (X1 - WALL - 1.0, BB.ZMin + 40.0),
          (X0 + INSET + 22.0, ZTOP - WALL - 1.0), (X1 - INSET - 22.0, ZTOP - WALL - 1.0)]
screws = []
Y_BOSS = SPLIT_Y - 2.0                            # each boss's top
for x, z in SCREWS:
    shell = cad.screw_boss(shell, (x, Y_BOSS, z), "-Y", size=SCREW, ribs=0)
    back = cad.countersink(back, (x, YS, z), "-Y", 2.9, 4.7 + 0.2, through="wall")
    # head flush at the shoulder, the shank across the gap 5 mm into the pilot
    screws.append(cad.screw("csk_phillips", SCREW, int(round(YS - Y_BOSS + 5.0)), at=(x, YS, z), axis="-Y"))
tick("screws")

# ------------------------------------------------------------ the face: screen
# the chrome bezel fills its opening and stands proud; the black mask
# tunnel fills the bezel's opening and runs back to 0.4 mm off the screen;
# the glass fills the mask's window, domed
shell, bezel = insert(shell, yrect(SCX, SCZ, BZ[0], BZ[1], BZ[2], YF - 1, YF + WALL + 1))
bezel = cad.fuse_one(bezel, yrect(SCX, SCZ, BZ[0], BZ[1], BZ[2], YF - BZ_PROUD, YF + 0.5))
bezel = cad.cut(bezel, yrect(SCX, SCZ, MASK[0], MASK[1], MASK[2], YF - BZ_PROUD - 1, YF + WALL + 1))
Y_MF = YF - BZ_PROUD + 0.8                        # the mask's front, set back in the bezel
mask = cad.cut(yrect(SCX, SCZ, MASK[0], MASK[1], MASK[2], Y_MF, SB.YMin - 0.4),
               yrect(SCX, SCZ, WIN[0], WIN[1], WIN[2], Y_MF - 1, SB.YMin + 1))
# (the glass is a solid acrylic block - the CRT's bulge - from the mask's
# front to 0.4 mm off the display: a declared cover, so the picture shows)
Y_GF = Y_MF                                       # the glass's corners: flush with the mask's front
glass = yrect(SCX, SCZ, WIN[0], WIN[1], WIN[2], Y_GF, SB.YMin - 0.4)
half_diag = math.hypot(WIN[0] / 2, WIN[1] / 2)
RS = (half_diag ** 2 + DOME ** 2) / (2 * DOME)
dome = Part.makeSphere(RS, V(SCX, Y_GF - DOME + RS, SCZ)).common(
    yrect(SCX, SCZ, WIN[0], WIN[1], WIN[2], Y_GF - DOME - 1, Y_GF + 0.5))
glass = cad.fuse_one(glass, dome)
tick("screen")

# ------------------------------------------------------------ the face: speaker
# a chrome grille plate under the screen fills its opening, 1 mm proud;
# slots through it in front of the speaker (0.8 mm air behind the wall)
GZ0, GZ1 = BB.ZMin + 4.0, SCZ - BZ[1] / 2 - 12.0
shell, grille = insert(shell, yrect(SCX, (GZ0 + GZ1) / 2, BZ[0], GZ1 - GZ0, 4.0, YF - 1, YF + WALL + 1))
grille = cad.fuse_one(grille, yrect(SCX, (GZ0 + GZ1) / 2, BZ[0], GZ1 - GZ0, 4.0, YF - 1.0, YF + 0.5))
tick("grille plate")

# ------------------------------------------------------------ the face: the dial
# a crown rises round the knob, its rim 0.4 mm over the cap's top (only
# the working face looks out), the face is the well's floor; a frosted
# ring in it over the LED ring, its pipe to 0.5 mm off the knob's plate
kx, _ky, kz = centre(KB)
K_PLATE = KB.YMax - 10.1                          # the knob's LED plate (10.1 mm over the PCB)
CAP_TOP = KB.YMin - 2.0
Y_RIM = CAP_TOP - 0.4
crown = Part.makeCone(FOOT_R, RIM_R, (YF + 1.0) - Y_RIM, V(kx, YF + 1.0, kz), V(0, -1, 0))
shell = cad.cut(cad.fuse_one(shell, crown), cyl(DISH_R, (kx, YF - 0.01, kz), (0, -1, 0), 60))
ring_cut = ring_y((kx, kz), RING_R[0], RING_R[1], YF - 1, YF + WALL + 1)
dial_ring = shell.common(ring_cut)
shell = cad.cut(shell, cyl(RING_R[1], (kx, YF - 1, kz), (0, 1, 0), WALL + 2))
dial_ring = cad.fuse_one(dial_ring, ring_y((kx, kz), RING_R[0], RING_R[1] - 1.0, YF + WALL - 0.5, K_PLATE - 0.5))
# the chrome rim: a ring in a rebate round the crown's rim (it fills it)
reb = ring_y((kx, kz), RIM_R - 1.6, RIM_R + 1.0, Y_RIM - 1.0, Y_RIM + 2.5)
dial_bezel = shell.common(reb)
shell = cad.cut(shell, reb)
# the cap: pushed on the knob's shaft (bore 0.35 mm round its 12.2 mm
# cap), a plug 2 mm into the ring's bore keeps it on its axis
y_cb = YF - 0.6
dial_cap = cad.fuse_one(cyl(CAP_R, (kx, y_cb, kz), (0, -1, 0), y_cb - CAP_TOP),
                        ring_y((kx, kz), 6.45, RING_R[0] - 0.2, y_cb - 0.5, YF + 2.0))
dial_cap = cad.fillet_safe(dial_cap, 1.5, edges=[e for e in dial_cap.Edges if e.BoundBox.YMax < CAP_TOP + 0.01])
dial_cap = cad.cut(dial_cap, cyl(6.45, (kx, YF + 3.0, kz), (0, -1, 0), (YF + 3.0) - (KB.YMin - 0.4)))
tick("dial")

# ------------------------------------------------------------ the face: pilot light, power key
# a chrome control plate under the dial fills its opening, 0.8 mm proud;
# the jewel and the key come through it
lx, _ly, lz = centre(LB)
bx, _by, bz = centre(NB)
PX0, PX1 = BB.XMax - 18.5, BB.XMax + 16.0
PZ0, PZ1 = NB.ZMin + 2.0, lz + 8.0
PL_F = YF - 0.8                                   # the plate's face
# (its top hugs the dial crown: an arc 2 mm off the crown's foot)
hug = cyl(FOOT_R + 2.0, (kx, YF - 5, kz), (0, 1, 0), WALL + 10)
shell, plate = insert(shell, cad.cut(yprism(PX0, PX1, PZ0, PZ1, 5.0, YF - 1, YF + WALL + 1), hug))
plate = cad.fuse_one(plate, cad.cut(yprism(PX0, PX1, PZ0, PZ1, 5.0, PL_F, YF + 0.5), hug))
l0 = LB.YMin - 0.4
jewel = cad.lens(9.0, l0 - (PL_F - 1.4), dome=1.0, at=(lx, l0, lz), axis="-Y")
plate = cad.opening_for(plate, jewel, clearance=0.2, chamfer=0.4, axis="-Y")
base_y = YF + WALL + 0.9
key = cad.button_cap(KEY_D, base_y - (PL_F - 1.6), dome=0.8, flange=1.5, at=(bx, base_y, bz), axis="-Y")
plate = cad.opening_for(plate, key, clearance=0.25, chamfer=0.4, axis="-Y")
key = cad.fuse_one(key, cyl(3.0, (bx, NB.YMin - 0.16, bz), (0, -1, 0), (NB.YMin - 0.16) - base_y + 0.5))
tick("lamp + key")

# ------------------------------------------------------------ the floor: USB-C
# a pocket from below brings the floor to 1.3 mm off the mouth, a liner
# round it, then the measured opening (the plug goes in from under the
# cabinet, between the legs; the cable leaves to the back)
ux, uy = (UB.XMin + UB.XMax) / 2, BB.YMin + 4.5 - 5.9   # the receptacle: 5.9 mm off the PCB's face


def zrect(cx, cy, w, d, r, z0, z1):
    w_ = cad.rounded_rect_wire(w, d, r, (cx, cy, z0), "Z")
    s_ = Part.Face(w_).extrude(V(0, 0, z1 - z0))
    if s_.Volume < 0:
        s_.reverse()
    return s_


pocket = zrect(ux, uy, 15.0, 8.0, 3.0, ZBOT - 5, UB.ZMin - 1.3)
liner = cad.cut(zrect(ux, uy, 19.0, 12.0, 4.0, ZBOT + 1.0, UB.ZMin - 0.25), pocket)
shell = cad.fuse_one(cad.cut(shell, pocket), liner)
shell = cad.socket_opening(shell, usb, margin=1.5)
tick("stage A")


# === STAGE B: details ===
# (a fork may stop after STAGE A, run ./check, then add these one by one)
# the grille's vertical slots, the brand badge over it
grille = cad.grille(grille, (SCX, YF - 1.0, (GZ0 + GZ1) / 2), (0, -1, 0), (BZ[0] - 4, GZ1 - GZ0 - 4), kind="slot",
                    hole=2.0, pitch=4.0, margin=2.0, through="wall")
BADGE_Z = (GZ1 + SCZ - BZ[1] / 2) / 2
shell, badge = insert(shell, yrect(SCX, BADGE_Z, 34.0, 8.0, 2.0, YF - 1, YF + WALL + 1))
badge = cad.fuse_one(badge, yrect(SCX, BADGE_Z, 34.0, 8.0, 2.0, YF - 0.8, YF + 0.5))
badge = cad.text(badge, "ATECH", (SCX, YF - 0.8, BADGE_Z), (0, -1, 0), 4.0, depth=0.4, mode="deboss")
# twelve channel ticks on the dial's chrome rim
ticks = []
for i in range(12):
    a = math.radians(30 * i)
    t = box(-0.45, 0.45, Y_RIM - 1.0, Y_RIM + 0.5, RIM_R - 2.6, RIM_R + 1.5)
    t.rotate(V(0, 0, 0), V(0, 1, 0), 30 * i)
    t.translate(V(kx, 0, kz))
    ticks.append(t)
dial_bezel = cad.cut(dial_bezel, ticks, optional=True)
# legends on the control plate, a reveal line round the front box
plate = cad.text(plate, "ON", ((bx + PX1) / 2 + 2.0, PL_F, bz), (0, -1, 0), 4.0, depth=0.4, mode="deboss")
plate = cad.text(plate, "TV", ((lx + PX1) / 2 + 2.0, PL_F, lz), (0, -1, 0), 4.0, depth=0.4, mode="deboss")
shell = cad.groove_ring(shell, "Y", YF + EDGE + 3.0, w=0.8, depth=0.6)
# the cap: a straight knurl round its side, a pointer groove on its face
dial_cap = cad.knurl(dial_cap, "-Y", (kx, y_cb, kz), CAP_R, 1.0, y_cb - CAP_TOP - 2.4, n=40, depth=0.35)
dial_cap = cad.cut(dial_cap, box(kx - 0.6, kx + 0.6, CAP_TOP - 1, CAP_TOP + 0.6, kz + 3.0, kz + CAP_R - 1.6))
# back vents: slots over the USB-C, in the back panel
back = cad.grille(back, (XC, YH, ZBOT + 0.62 * BH), (0, 1, 0), (0.55 * BW, 0.30 * BH), kind="slot", hole=2.5,
                  pitch=5.5, margin=2.0)
tick("details")

# rabbit-ear antenna: a chrome hub pegged into the top, two telescoping
# rods in bores in its dome, leaning out and back, ball tips
HUB_R = 9.0
ax_, ay_ = XC, (YF + SPLIT_Y) / 2
hub = cad.fuse_one(cyl(HUB_R, (ax_, ay_, ZTOP + 0.1), (0, 0, 1), 3.0),
                   Part.makeSphere(HUB_R, V(ax_, ay_, ZTOP + 3.0)).common(
                       cyl(HUB_R, (ax_, ay_, ZTOP + 2.5), (0, 0, 1), HUB_R + 1)),
                   cyl(3.0, (ax_, ay_, ZTOP - WALL + 0.1), (0, 0, 1), WALL + 0.5))
shell = cad.cut(shell, cyl(3.15, (ax_, ay_, ZTOP - WALL - 1), (0, 0, 1), WALL + 2))
hc = V(ax_, ay_, ZTOP + 3.0)
rods, bores = [], []
for sx in (-1, 1):
    u = V(sx * 0.57, 0.25, 0.82)
    u.normalize()
    bores.append(Part.makeCylinder(1.45, HUB_R + 2.0, hc + u * 2.5, u))
    r1 = Part.makeCylinder(1.25, 48.0, hc + u * 3.0, u)
    r2 = Part.makeCylinder(0.9, 48.0, hc + u * 50.0, u)
    tip = Part.makeSphere(2.2, hc + u * 98.0)
    rods.append(cad.fuse_one(r1, r2, tip))
hub = cad.cut(hub, bores)
tick("antenna")

# four splayed peg legs, each pegged into a boss on the floor, a brass
# ferrule round its foot; the soles are cut flat on the desk
legs, ferrules, boss_tools, peg_holes = [], [], [], []
for lx_, ly_, sx, sy in ((X0 + 20.0, YF + 14.0, -1, -1), (X1 - 20.0, YF + 14.0, 1, -1),
                         (HB[0] + 12.0, YH - 14.0, -1, 1), (HB[1] - 12.0, YH - 14.0, 1, 1)):
    t = math.tan(math.radians(SPLAY))
    d = V(sx * t * 0.7, sy * t * 0.7, -1.0)
    d.normalize()
    top = V(lx_, ly_, ZBOT - 0.1)
    L = (ZBOT + 3.0) / -d.z + 3.0
    leg = Part.makeCone(5.2, 3.4, L, top - d * 3.0, d).common(box(lx_ - 40, lx_ + 40, ly_ - 40, ly_ + 40, 0,
                                                                  ZBOT - 0.1))
    leg = cad.fuse_one(leg, cyl(2.0, (lx_, ly_, ZBOT - 0.6), (0, 0, 1), 5.5))
    spigot = V(lx_, ly_, ZBOT) + d * ((ZBOT - 1.5) / -d.z)      # on the axis, 1.5 mm over the desk
    ferrule = leg.common(box(lx_ - 40, lx_ + 40, ly_ - 40, ly_ + 40, -1, 7.0))
    ferrule = cad.cut(ferrule, Part.makeCylinder(2.2, 12.0, spigot, d * -1.0))
    leg = cad.cut(leg, ferrule)
    legs.append(leg)
    ferrules.append(ferrule)
    boss_tools.append(cyl(5.5, (lx_, ly_, ZBOT + WALL - 0.5), (0, 0, 1), 7.0))
    peg_holes.append(cyl(2.15, (lx_, ly_, ZBOT - 1.0), (0, 0, 1), 7.5))
shell = cad.cut(cad.fuse_one(shell, *boss_tools[:2]), peg_holes[:2])
back = cad.cut(cad.fuse_one(back, *boss_tools[2:]), peg_holes[2:])
tick("legs")


# ------------------------------------------------------------ parts
def part(name, shape, colour):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = cad.color(COLOURS[colour])
    return o


part("Back", back, "Back")
part("Shell", shell, "Shell")
part("Bezel", bezel, "Chrome")
part("Mask", mask, "Mask")
o = part("Glass", glass, "Glass")
o.ViewObject.Transparency = cad.transparency("glass")
part("Grille", grille, "Chrome")
part("Badge", badge, "Chrome")
part("Control_Plate", plate, "Chrome")
part("Dial_Bezel", dial_bezel, "Chrome")
o = part("Dial_Ring", dial_ring, "Ring")
o.ViewObject.Transparency = cad.transparency("frosted")
part("Dial_Cap", dial_cap, "Cap")
o = part("Jewel", jewel, "Jewel")
o.ViewObject.Transparency = cad.transparency("led_red")
part("Power_Key", key, "Cap")
part("Antenna_Hub", hub, "Chrome")
part("Antenna_L", rods[0], "Chrome")
part("Antenna_R", rods[1], "Chrome")
for i, sh in enumerate(legs):
    part("Leg_%d" % (i + 1), sh, "Leg")
for i, sh in enumerate(ferrules):
    part("Ferrule_%d" % (i + 1), sh, "Ferrule")
for i, sh in enumerate(screws):
    part("Screw_%d" % (i + 1), sh, "Chrome")
print("TOTAL %.1f s" % (time.time() - T0))
