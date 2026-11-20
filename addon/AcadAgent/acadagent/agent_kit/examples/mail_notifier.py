"""Example: "a mailbox sensor that tells my phone when the post arrives" - a weatherproof flag box that sees letters land and pops up a red flag.

fork this file for a mailbox notifier (a mailbox sensor, a letterbox
alert, a post-arrived flag, a parcel box sensor); change PARAMETERS and the outlines.
ARCHETYPE: mailbox notifier

How it is built (R1030):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board FLAT and FACE DOWN (modules look at the ground, -Z), the box
    bolted on the mailbox's roof over a 25 mm hole. The distance sensor on
    3 looks STRAIGHT DOWN through an OPEN flared window in the base, into
    the mailbox (no glass over a ToF), and sees the floor come up when a
    letter lands. The stepper driver sits on (13, 14); its motor (a NEMA 17
    stand-in) is screwed to the inside of the left wall by its four face
    screws, its shaft out through the wall into the red flag's hub: the
    firmware turns the flag up when post arrives. The status light is
    CABLED from 7 straight up in front of the board to a frosted lens in
    the front wall; the reset key is cabled from 9 up the right wall (both
    twist-free, each held by two ribs). USB-C on 8, its mouth in a pocket
    low in the back wall under a hood (the cable drops away behind). The
    BASE plate is the fixed part: it carries the board on a spine rib, edge
    posts and front stops, and runs out as a screw-mount flange with four
    keyholes. The BODY (four walls with rounded corners under an arched
    tunnel roof, one part, fitted after) keys a tongue into the gasket
    groove of the base and is held by four M3 screws from below into
    corner columns.
  * STAGE B - details: drip edges along both eaves and barge lips across
    both ends of the roof, roof seams, a hood over every opening (lens,
    key, shaft, USB-C), the cream envelope badge inlaid in the front
    gable, the lens's chrome bezel, the flag's reflective stripe,
    lettering on the flag and the walls, keyholes, a drain hole.
RESTYLE (R1030): RISE, CORNER, WALL, EAVE and FLAG_ARM drive every outline
and every cutter below; the box's plan follows the hardware (the front
wall 0.5 mm in front of the light, the back from the USB-C mouth, the
right wall from the reset key), the eave height is solved so the ceiling
clears the motor at every RISE.
DETAILS (visible, 34): 1 arched tunnel roof; 2 eaves overhanging the
walls; 3-4 drip edges under both eaves; 5-6 barge lips across the front
and back; 7 three roof seams; 8 rounded upright corners; 9 a drip skirt
round the walls' foot over the base joint; 10 the red classic flag on an
arm, mid-side; 11 its hub on the motor shaft; 12 "MAIL" raised on the
flag; 13 a white reflective stripe inlaid through the flag; 14 the hood
over the shaft; 15 the bearing boss round the shaft; 16 the frosted
green status lens, domed; 17 its chrome bezel; 18 the lens hood with a
drip lip; 19 the reset key cap on the right wall; 20 its hood; 21
"RESET" under it; 22 the cream envelope badge in the front gable; 23 its
debossed flap; 24 "ATECH" on the front; 25 the USB-C recess low in the
back wall (1.2 mm in front of the mouth); 26 its hood and cheeks (a
sheltered pocket, open downward); 27 the charcoal base flange; 28-31
four keyhole slots; 32 drain hole; 33 the OPEN flared sensor window
underneath; 34 four countersunk M3 face screws on the left wall (four
more from below into the body: 8 x M3 countersunk, one screw type).
Inside: the gasket groove and the tongue in it, four corner columns with
pilots, the spine rib, edge posts and front stops, a hold-down rib from
the roof, holder ribs either side of the light and the key, the motor
pad with its pilot recess, back stops on the back wall.
Materials: postal-green body, charcoal (graphite) base, signal-red flag,
frosted green status lens in a chrome bezel, white flag stripe, cream
envelope and key, chrome screws.
Placeholders: the motor is the library's NEMA 17 (Atech's driver is said
to drive a NEMA 20: measure the real motor); the stepper driver needs its
own 12-24 V motor supply, which USB-C alone does not give.
MEASURED (R1030, 2026-11-20): ./check CHECK PASS, run_seconds 7-13 s, wall 17-28 s; every RESTYLE end CHECK PASS.
"""
import math
import time
import Part
import atech_ports as ap
import atech_modules as am
import atech_cad as cad
from FreeCAD import Vector, Placement, Rotation
V = Vector
T0 = time.time()

INTENT = {"board": "flat", "fitted_after": [
    "Body", "Lens", "Lens_Bezel", "Reset_Key", "Envelope_Badge", "Flag", "Flag_Stripe",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4", "Screw_5", "Screw_6", "Screw_7", "Screw_8"],
    "covers": {"Reset_Key": "button_9"},
    # the flag turns on the motor shaft (x axis), raised (0) to lowered
    # forward along the side (90)
    "motion": [{"part": "Flag", "axis": [[-20.0, 62.0, 44.65], [1, 0, 0]], "range_deg": [0, 90]}]}
# the reflective stripe rides in the flag and turns with it
INTENDED_OVERLAPS = [("Flag", "Flag_Stripe")]
REVIEW_CLOSEUPS = ["Flag", "Lens_Bezel", "Base"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them (the eave height is solved
# from RISE so the ceiling clears the motor: see ZE below).
RISE = 28.0        # RESTYLE 23.8..32.2 height: the arched roof, eave to crown
CORNER = 6.0       # RESTYLE 5.1..6.9 radius: the body's four upright corners
WALL = 3.0         # RESTYLE 2.55..3.45 wall
EAVE = 5.0         # RESTYLE 4.25..5.75 length: the roof's overhang past the walls
FLAG_ARM = 78.0    # RESTYLE 66..90 length: the flag's arm, shaft to the flag's top
# end RESTYLE
BASE_T = 4.0                     # the base plate (floor and flange)
FT = BASE_T                      # the floor's top face
BZ = FT + 11.0                   # the board's box bottom: the stepper driver 0.5 mm over the floor
ROOF_T = 3.0                     # the roof shell
FLANGE = 12.0                    # the screw-mount flange past the walls (left, right, front)
PAD = 2.0                        # the motor pad inside the left wall
YM, ZM = 62.0, 44.65             # the motor shaft (y, z): mid-length, over the board (the flag mid-side)
MOTOR_HALF = 21.15               # the NEMA 17 body's half size (measured)
FLAG_W, FLAG_H, FLAG_T = 44.0, 40.0, 4.0   # the flag plate (along y when raised, along z), thickness
HUB_R, HUB_L = 7.0, 17.0         # the flag hub on the shaft
SCREW = "M3"                     # ONE screw type: M3 countersunk (12 mm into the body, 8 mm into the motor)
COLOURS = {"Body": "#21684a", "Base": "graphite", "Flag": "signal_red", "Lens": "#9be8b4",
           "Reset_Key": "cream", "Envelope_Badge": "cream", "Lens_Bezel": "chrome",
           "Flag_Stripe": "matte_white", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
FACE_DOWN = Rotation(Vector(1, 0, 0), -90)    # modules face -Z; board x 0..60, y 0..120
board = ap.board_object(doc)


def place_board(rot, x0=0.0, y0=0.0, z0=0.0):
    board.Placement = Placement(Vector(), rot)
    bb = ap.bbox(board)
    board.Placement = Placement(Vector(x0 - bb.XMin, y0 - bb.YMin, z0 - bb.ZMin), rot)


place_board(FACE_DOWN, 0, 0, BZ)              # ports 1-6 at x 0..20, 9-14 at x 40..60, 7 front, 8 back
BB = ap.bbox(board)
PCB = BB.ZMin + 4.5                           # the PCB face (the modules hang under it)
tof = ap.seat(doc, "distance_sensor", 3)      # left, middle: looks down into the mailbox
drv = ap.seat(doc, "stepper_motor", (13, 14))  # the flag motor's driver, back right
usb = ap.seat(doc, "usbc", 8)                 # the back end, mouth +Y
# the status light: straight up in front of port 7, facing the front
light, light_rb = ap.cable(doc, "light", 7, ap.module_placement(
    "light", (30.0, -12.0, PCB + 24.0), "-Y", "-Z"))
# the reset key: straight up beside port 9, facing the right wall
key, key_rb = ap.cable(doc, "button", 9, ap.module_placement(
    "button", (BB.XMax + 7.0, 10.0, PCB + 24.0), "+X", "-Z"))
tick("hardware")
TB, UB, LB, KB = ap.bbox(tof), ap.bbox(usb), ap.bbox(light), ap.bbox(key)
YF = LB.YMin - 0.5 - WALL        # the front wall's outer face (inner face 0.5 mm off the light)
YB = UB.YMax + 0.25 + WALL       # the back wall's outer face (inner face 0.25 mm off the USB-C mouth)
X1 = KB.XMax + 2.5 + WALL        # the right wall (room for the key's flange and plunger)
X0 = -4.0 - WALL                 # the left wall (3.5 mm clear of the left column)
XC, HW = (X0 + X1) / 2, (X1 - X0) / 2
XMF = X0 + WALL + PAD            # the motor's face (on the pad)
MTOP = ZM + MOTOR_HALF           # the motor's top
# the motor: the library's NEMA 17, face on the pad, shaft out through the left wall (-X)
motor, _rep = am.load_module(doc, "nema17_stepper", label="Motor",
                             placement=Placement(V(XMF, YM, ZM), Rotation(V(0, 0, 1), 90)))


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def prism_xz(pts, y0, y1):
    """A prism of an (x, z) outline from y0 to y1."""
    w = Part.makePolygon([V(x, y0, z) for x, z in pts] + [V(pts[0][0], y0, pts[0][1])])
    return Part.Face(w).extrude(V(0, y1 - y0, 0))


def prism_yz(pts, x0, x1):
    w = Part.makePolygon([V(x0, y, z) for y, z in pts] + [V(x0, pts[0][0], pts[0][1])])
    return Part.Face(w).extrude(V(x1 - x0, 0, 0))


def zplate(pts, z0, z1):
    w = Part.makePolygon([V(x, y, z0) for x, y in pts] + [V(pts[0][0], pts[0][1], z0)])
    return Part.Face(w).extrude(V(0, 0, z1 - z0))


def soft_rect(x0, x1, y0, y1, r):
    """A rectangle's (u, v) outline, each corner 3 straight facets (an arc
    corner reads as a clip channel, R7)."""
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for k in range(4):
            a = math.radians(a0 + 30 * k)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def ngon(cx, cy, r, n=12):
    return [(cx + r * math.cos(2 * math.pi * (k + 0.5) / n), cy + r * math.sin(2 * math.pi * (k + 0.5) / n))
            for k in range(n)]


def insert(shell, cutter):
    """(shell with the opening, the piece that fills it exactly)."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1:
        piece, rest = shell.common(cutter, 0.01), shell.cut(cutter, 0.01)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, piece


# ------------------------------------------------------------ the arched roof
# one circle through both eaves and the crown; the eave height ZE is
# solved so the ceiling (ROOF_T under it) meets the side walls 1 mm over
# the motor's top: the whole motor face (its screws, the shaft hood) sits
# on the open wall under the eave
E = HW + EAVE
RO = (E * E + RISE * RISE) / (2 * RISE)
RI = RO - ROOF_T
ZE = MTOP + 1.0 - RISE + RO - math.sqrt(RI * RI - HW * HW)
ZC0 = ZE + RISE - RO             # the circle's centre height
ZCROWN = ZE + RISE


def z_in(u):
    return ZC0 + math.sqrt(RI * RI - u * u)


def z_out(u):
    return ZC0 + math.sqrt(RO * RO - u * u)


def band(r_out, r_in, a0, a1, y0, y1, n=40):
    """An arched band (both skins concentric about the roof's axis) from
    angle a0 to a1 (rad, from +x), y0..y1 - each skin n straight facets (a
    true arc reads as an open clip channel, R7)."""
    def p(r, a):
        return (XC + r * math.cos(a), ZC0 + r * math.sin(a))
    ang = [a0 + (a1 - a0) * k / n for k in range(n + 1)]
    return prism_xz([p(r_out, a) for a in ang] + [p(r_in, a) for a in ang[::-1]], y0, y1)


AR = math.atan2(ZE - ZC0, E)     # the right eave's angle; the left one is pi - AR
AL = math.pi - AR
YR0, YR1 = YF - EAVE, YB + EAVE
slab = band(RO, RI, AR, AL, YR0, YR1)
# the walls: one block under the roof (its top 0.6 mm into the slab), its
# four upright corners rounded, hollowed by a sharp-cornered cavity whose
# top follows the ceiling
NS = 24
top_pts = [(X0 + 2 * HW * k / NS, z_in(X0 + 2 * HW * k / NS - XC) + 0.6) for k in range(NS + 1)]
block = prism_xz([(X0, FT), (X1, FT)] + top_pts[::-1], YF, YB)
block = cad.fillet_safe(block, CORNER, edges=[e for e in block.Edges if e.BoundBox.ZLength > 20
                                              and e.BoundBox.XLength < 0.01 and e.BoundBox.YLength < 0.01])
xi0, xi1 = X0 + WALL, X1 - WALL
cav_pts = [(xi0 + (xi1 - xi0) * k / NS, z_in(xi0 + (xi1 - xi0) * k / NS - XC) - 0.05) for k in range(NS + 1)]
cavity = prism_xz([(xi0, FT - 1), (xi1, FT - 1)] + cav_pts[::-1], YF + WALL, YB - WALL)
body = cad.cut(cad.fuse_one(slab, block), cavity)
tick("roof + walls")

# ------------------------------------------------------------ inside the body
YFI, YBI = YF + WALL, YB - WALL  # the inner faces
# corner columns for the base screws (short at the back left: the board is over it)
CP = 8.0
CORNERS = [(xi0 + CP / 2, YFI + CP / 2), (xi1 - CP / 2, YFI + CP / 2),
           (xi0 + CP / 2, YBI - CP / 2), (xi1 - CP / 2, YBI - CP / 2)]
cols = [box(x - CP / 2 - 0.5, x + CP / 2 + 0.5, y - CP / 2 - 0.5, y + CP / 2 + 0.5, FT, FT + 10.5)
        for x, y in CORNERS]
# the motor pad on the left wall (it runs up into the ceiling), back stops
# 0.3 mm off the board's back edge, a hold-down rib from the ceiling onto
# the board's top (0.2 mm off), holder ribs either side of the light and the key
pad = box(xi0 - 0.5, XMF, YM - MOTOR_HALF - 2, YM + MOTOR_HALF + 2, ZM - MOTOR_HALF - 2, MTOP)
stops = [box(x, x + 6, BB.YMax + 0.3, YBI + 0.5, BB.ZMin, BB.ZMax - 1) for x in (3.0, 51.0)]
hold = box(48.0, 52.0, 30.0, 60.0, BB.ZMax + 0.2, z_in(50.0 - XC) + 0.5)
lribs = [box(LB.XMin - 2.0, LB.XMin - 0.4, YFI - 0.5, LB.YMax - 1.5, LB.ZMin + 2, LB.ZMax - 2),
         box(LB.XMax + 0.4, LB.XMax + 2.0, YFI - 0.5, LB.YMax - 1.5, LB.ZMin + 2, LB.ZMax - 2)]
kribs = [box(KB.XMin + 1.5, xi1 + 0.5, KB.YMin - 2.0, KB.YMin - 0.25, KB.ZMin + 2, KB.ZMax - 2),
         box(KB.XMin + 1.5, xi1 + 0.5, KB.YMax + 0.25, KB.YMax + 2.0, KB.ZMin + 2, KB.ZMax - 2)]
# the tongue under the walls, into the base's gasket groove
M = WALL / 2


def ring(inset_out, inset_in, z0, z1):
    ro = cad.rounded_box(X1 - X0 - 2 * inset_out, YB - YF - 2 * inset_out, z1 - z0, CORNER - inset_out,
                         at=(X0 + inset_out, YF + inset_out, z0))
    ri = cad.rounded_box(X1 - X0 - 2 * inset_in, YB - YF - 2 * inset_in, z1 - z0 + 2, CORNER - inset_in,
                         at=(X0 + inset_in, YF + inset_in, z0 - 1))
    return cad.cut(ro, ri)


tongue = ring(M - 0.5, M + 0.5, FT - 1.2, FT + 0.5)
# a drip skirt round the walls' foot, 1.2 mm proud: rain runs off it past
# the joint onto the flange
skirt = ring(-1.2, 0.5, FT, FT + 7.0)
body = cad.fuse_one(body, pad, hold, tongue, skirt, *(cols + stops + lribs + kribs))
tick("body inside")

# ------------------------------------------------------------ the base (fixed)
base = cad.rounded_box(X1 - X0 + 2 * FLANGE, YB + 3.0 - YF + FLANGE, BASE_T, CORNER + FLANGE * 0.5,
                       at=(X0 - FLANGE, YF - FLANGE, 0))      # 3 mm past the back wall: the groove's outer wall
groove = ring(M - 0.8, M + 0.8, FT - 1.5, FT + 1.0)
base = cad.cut(base, groove)
# the board rides on a rib under its spine, between edge posts and front
# stops (0.3 mm clear), all clear of the module corridors
sup = [box(29.0, 31.0, 40.0, 80.0, FT - 0.5, BB.ZMin - 0.2)]
sup += [box(BB.XMin - 2.3, BB.XMin - 0.3, y, y + 6, FT - 0.5, BB.ZMax - 2) for y in (66.0, 100.0)]
sup += [box(BB.XMax + 0.3, BB.XMax + 2.3, y, y + 6, FT - 0.5, BB.ZMax - 2) for y in (30.0, 56.0)]
sup += [box(x, x + 6, BB.YMin - 2.3, BB.YMin - 0.3, FT - 0.5, BB.ZMax - 2) for x in (3.0, 51.0)]
base = cad.fuse_one(base, *sup)
# the sensor's window: OPEN, flared toward the mailbox (no glass over a ToF)
TC = ((TB.XMin + TB.XMax) / 2, (TB.YMin + TB.YMax) / 2)
base = cad.cut(base, Part.makeCone(10.0, 7.0, BASE_T + 2, V(TC[0], TC[1], -1), V(0, 0, 1)))
tick("base")

# ------------------------------------------------------------ joints and openings
screws = []
for x, y in CORNERS:
    base = cad.countersink(base, (x, y, 0), "+Z", 3.4, 6.2, 90.0, through="wall")
    body = cad.hole(body, (x, y, FT), "+Z", 2.55, depth=9)       # the M3 thread-forming pilot (1.5 mm under the column top)
    screws.append(cad.screw("csk_phillips", SCREW, 12, at=(x, y, 0), axis="+Z"))
tick("base screws")
# the motor: pilot recess in the pad, the shaft through the wall, four M3
# face screws from outside (31 mm square)
body = cad.cut(body, [cyl(11.25, (XMF + 0.01, YM, ZM), 2.1, (-1, 0, 0)),
                      cyl(3.5, (XMF + 0.5, YM, ZM), WALL + PAD + 2, (-1, 0, 0))])
for dy in (-15.5, 15.5):
    for dz in (-15.5, 15.5):
        body = cad.countersink(body, (X0, YM + dy, ZM + dz), "+X", 3.4, 6.2, 90.0, through="wall")
        screws.append(cad.screw("csk_phillips", SCREW, 8, at=(X0, YM + dy, ZM + dz), axis="+X"))
tick("motor screws")
# the status light: a frosted lens filling a round opening, 0.5 mm off the LEDs
LX, LZ = (LB.XMin + LB.XMax) / 2, (LB.ZMin + LB.ZMax) / 2
# (the lens fills a chrome bezel, the bezel fills its opening in the wall;
# the holder ribs stay 0.15 mm outside the bezel's opening)
LENS_R, BEZ_R = 8.5, 10.0
body, lens = insert(body, cyl(BEZ_R, (LX, YFI + 1, LZ), WALL + 2, (0, -1, 0)))
bezel = cad.cut(lens, cyl(LENS_R, (LX, YFI + 2, LZ), WALL + 4, (0, -1, 0)))
lens = lens.common(cyl(LENS_R, (LX, YFI + 2, LZ), WALL + 4, (0, -1, 0)))
LRS = (LENS_R ** 2 + 1.2 ** 2) / (2 * 1.2)        # its dome: 1.2 mm proud of the face
lens = cad.fuse_one(lens, Part.makeSphere(LRS, V(LX, YF - 1.2 + LRS, LZ)).common(
    cyl(LENS_R, (LX, YF + 0.5, LZ), 1.7, (0, -1, 0))))
bezel = cad.fuse_one(bezel, cad.cut(cyl(BEZ_R + 2.5, (LX, YF, LZ), 1.5, (0, -1, 0)),
                                    cyl(LENS_R + 0.1, (LX, YF + 1, LZ), 3.0, (0, -1, 0))),
                     cad.cut(cyl(BEZ_R - 0.1, (LX, YF + 1.0, LZ), 1.5, (0, -1, 0)),
                             cyl(LENS_R + 0.1, (LX, YF + 1.5, LZ), 3.0, (0, -1, 0))))
tick("lens + bezel")
# the reset key: a cap through the right wall, its flange 0.1 mm inside,
# a plunger to 0.16 mm off the button
KY, KZ = (KB.YMin + KB.YMax) / 2, (KB.ZMin + KB.ZMax) / 2
x_base = xi1 - 0.9
cap = cad.button_cap(10.0, (X1 + 1.6) - x_base, dome=0.8, flange=1.5, at=(x_base, KY, KZ), axis="+X")
body = cad.opening_for(body, cap, clearance=0.25, chamfer=0.4, axis="+X")
cap = cad.fuse_one(cap, cyl(3.0, (KB.XMax + 0.16, KY, KZ), x_base - (KB.XMax + 0.16) + 0.5, (1, 0, 0)))
tick("reset key")
# USB-C low in the back wall: a recess outside brings the wall to 1.2 mm
ux = (UB.XMin + UB.XMax) / 2
uz = PCB - 5.9                   # the receptacle: 5.9 mm under the PCB face
body = cad.cut(body, prism_xz(soft_rect(ux - 9, ux + 9, uz - 5.5, uz + 5.5, 2.5), YB - (WALL - 1.2), YB + 3))
body = cad.socket_opening(body, usb, margin=1.5)
tick("stage A")


# === STAGE B: details ===
# drip edges under both eaves, barge lips across both ends
sl = (z_out(E - 1.6) - ZE)
lips = [prism_xz([(XC + s * E, ZE - 4.0), (XC + s * E, ZE), (XC + s * (E - 1.6), ZE + sl * 0.9),
                  (XC + s * (E - 1.6), ZE - 4.0)], YR0, YR1) for s in (-1, 1)]
lips += [band(RI + 0.5, RI - 3.0, AR + 0.03, AL - 0.03, y0, y0 + 1.6) for y0 in (YR0, YR1 - 1.6)]
body = cad.fuse_one(body, *lips)
# roof seams: three shallow grooves over the arch
seams = [band(RO + 1.0, RO - 0.6, AR + 0.02, AL - 0.02, y - 0.5, y + 0.5)
         for y in [YR0 + (YR1 - YR0) * k / 4 for k in (1, 2, 3)]]
body = cad.cut(body, seams)
tick("roof details")
# hoods: over the lens, the key, the shaft and the USB-C pocket
hoods = [box(LX - 13, LX + 13, YF - 7, YF + 0.5, LZ + 13, LZ + 15),
         box(LX - 13, LX + 13, YF - 7, YF - 5.5, LZ + 11, LZ + 13.5),
         box(X1 - 0.5, X1 + 7, KY - 11, KY + 11, KZ + 10, KZ + 12),
         box(X1 + 5.5, X1 + 7, KY - 11, KY + 11, KZ + 8, KZ + 10.5),
         box(ux - 12, ux + 12, YB - 0.5, YB + 8, uz + 7, uz + 9),
         box(ux - 12, ux - 10, YB - 0.5, YB + 8, uz - 4, uz + 7.5),
         box(ux + 10, ux + 12, YB - 0.5, YB + 8, uz - 4, uz + 7.5)]
# (a half ring of straight facets over the shaft: a round one reads as a channel)
hood_a = [math.radians(15 + 150 * k / 10) for k in range(11)]
shaft_hood = prism_yz([(YM + 12.0 * math.cos(a), ZM + 12.0 * math.sin(a)) for a in hood_a]
                      + [(YM + 10.0 * math.cos(a), ZM + 10.0 * math.sin(a)) for a in hood_a[::-1]], X0 - 4.0, X0 + 0.5)
boss = cad.cut(cyl(6.5, (X0 + 0.5, YM, ZM), 1.3, (-1, 0, 0)), cyl(3.5, (X0 + 1, YM, ZM), 3, (-1, 0, 0)))
body = cad.fuse_one(body, shaft_hood, boss, *hoods)
# the envelope badge: a cream insert through the front gable, its flap debossed
EZ = (LZ + 15 + ZE + RISE - ROOF_T) / 2 + 1.0
EW, EH = 24.0, 15.0
body, badge = insert(body, prism_xz(soft_rect(XC - EW / 2, XC + EW / 2, EZ - EH / 2, EZ + EH / 2, 1.5),
                                    YF - 1, YFI + 1))
flap = []
for s in (-1, 1):
    x0_, z0_ = XC + s * (EW / 2 - 1.5), EZ + EH / 2 - 1.2
    x1_, z1_ = XC, EZ - 1.0
    nx, nz = (z1_ - z0_), -(x1_ - x0_)
    ln = math.hypot(nx, nz)
    nx, nz = 0.45 * nx / ln, 0.45 * nz / ln
    flap.append(prism_xz([(x0_ - nx, z0_ - nz), (x0_ + nx, z0_ + nz), (x1_ + nx, z1_ + nz), (x1_ - nx, z1_ - nz)],
                         YF - 1, YF + 0.5))
badge = cad.cut(badge, flap)
# lettering
body = cad.text(body, "ATECH", (LX, YF, FT + 16.0), (0, -1, 0), 5.0, depth=0.4, mode="deboss")
body = cad.text(body, "RESET", (X1, KY, KZ - 9.5), (1, 0, 0), 3.5, depth=0.4, mode="deboss")
# a drain hole in the floor (front right), keyholes in the flange
base = cad.cut(base, cyl(1.5, (xi1 - 14.0, YFI + 3.0, -1), BASE_T + 2))
kh = []
for x in (X0 - FLANGE / 2, X1 + FLANGE / 2):
    for y in (YF + 0.22 * (YB - YF), YB - 0.22 * (YB - YF)):
        kh.append(zplate(ngon(x, y, 3.6), -1, BASE_T + 1))
        kh.append(box(x - 1.7, x + 1.7, y, y + 9.0, -1, BASE_T + 1))
base = cad.cut(base, kh)
tick("hoods + badge")

# ------------------------------------------------------------ the flag
# modelled RAISED (post arrived): a hub on the shaft (bore 0.15 mm clear),
# an arm straight up, the plate at its top reaching forward
XH0, XH1 = X0 - 1.5 - HUB_L, X0 - 1.5
hub = cyl(HUB_R, (XH0, YM, ZM), HUB_L, (1, 0, 0))
ztop = ZM + FLAG_ARM
arm = box(XH0, XH0 + FLAG_T, YM - 4.5, YM + 4.5, ZM, ztop - 2)
plate = Part.Face(Part.makePolygon([V(XH0, y, z) for y, z in soft_rect(YM + 4.5 - FLAG_W, YM + 4.5, ztop - FLAG_H, ztop, 4)]
                                   + [V(XH0, *soft_rect(YM + 4.5 - FLAG_W, YM + 4.5, ztop - FLAG_H, ztop, 4)[0])])
                  ).extrude(V(FLAG_T, 0, 0))
flag = cad.fuse_one(hub, arm, plate)
flag = cad.cut(flag, cyl(2.65, (XH0 - 1, YM, ZM), HUB_L + 2, (1, 0, 0)))
# a white reflective stripe through the plate's lower part (an insert: it
# fills its own opening), "MAIL" raised above it
flag, stripe = insert(flag, box(XH0 - 1, XH0 + FLAG_T + 1, YM + 4.5 - FLAG_W + 4.5, YM + 0.5,
                                ztop - FLAG_H + 5.0, ztop - FLAG_H + 12.0))
flag = cad.text(flag, "MAIL", (XH0, YM + 4.5 - FLAG_W / 2, ztop - FLAG_H / 2 + 4.0), (-1, 0, 0), 10.0,
                depth=0.8, mode="emboss")
tick("flag")


# ------------------------------------------------------------ parts
def part(name, shape, colour=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = cad.color(COLOURS[colour or name])
    return o


for nm, sh in (("Base", base), ("Body", body), ("Flag", flag), ("Envelope_Badge", badge),
               ("Lens_Bezel", bezel), ("Flag_Stripe", stripe)):
    part(nm, sh)
part("Reset_Key", cap)
o = part("Lens", lens)
o.ViewObject.Transparency = cad.transparency("frosted")
for i, sh in enumerate(screws):
    part("Screw_%d" % (i + 1), sh, "Screw")
print("SIZE", cad.measure(Part.makeCompound([base, body, flag]))["size"], "ZE %.1f crown %.1f" % (ZE, ZCROWN))
print("TOTAL %.1f s" % (time.time() - T0))
