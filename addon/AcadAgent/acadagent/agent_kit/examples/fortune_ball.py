"""Example: "a fortune ball that answers your question when you shake it" - a midnight-blue crystal ball with a gold porthole; shake it and the answer rises in the glass.

fork this file for a fortune ball (a shake-to-answer ball, a decision ball, a crystal ball, an oracle orb); change PARAMETERS and the outlines.
ARCHETYPE: fortune ball

How it is built (R990):
  * STAGE A - hardware, shell, every working-face opening, fasteners: a
    150 mm sphere (the 60 x 120 board needs R >= 67.2 inside: no smaller
    ball holds it) that sits loose in a gold seat ring on a black stand.
    The board stands UPRIGHT_FRONT on the ball's centre (modules facing
    the front, -Y), port 7 at the bottom: the USB-C mouth looks straight
    down into a well at the bottom pole, under the stand (the cable leaves
    through an arch in the stand's foot). The SCREEN is CABLED from (4, 5)
    to the front, centred on the ball's vertical mid-plane and turned up
    EL deg so its face looks out along a radius (the window axis): both
    ribbons leave the right edge, run left behind the screen in their own
    planes and U-turn into its left edge (pins -X: from +X the two
    ribbons cross, MEASURED). The window is ONE axis: a deep crystal lens
    plug with a flange under the shell, a barrel round it with two end
    tabs that cradle the screen, a gold bezel ring in a groove round it.
    The speaker (10, 11) seats on the left, low, firing through a chamber
    tube to a round whisper grille; the IMU (3) seats square on the board.
    The shell is two skins of one sphere with its poles turned to the
    sides (left / right, away from every cut), a parting reveal, split
    FRONT / BACK just behind the board with a lip: the back holds the board
    on a bulkhead with pads and edge fences, the front clamps its corners
    with four tabs; four M2.5 pan screws from deep wells in the back into
    heat-set insert columns in the front. The stand is one revolved
    section (foot, waist, a seat 0.2 mm off the ball); its top is the
    gold Stand_Ring, keyed 2.5 mm into it.
  * STAGE B - details: gold inlays, each cut from the front's outer
    0.8 mm and standing 0.5 mm proud (it fills its own pocket): a crescent
    moon, a constellation of five stars joined by fine lines (one solid),
    a ring round the grille, and a big "?" (hook and dot) debossed and
    filled gold; small debossed stars round the sides.
    (cad.text's deboss removed nothing on the back hemisphere, MEASURED;
    the back carries no lettering.)
DETAILS (visible, 24): 1 a 150 mm sphere, glossy midnight blue; 2 the
crystal window looking out 20 deg above the horizon; 3 the deep indigo
lens plug, flush with the skin; 4 the gold bezel ring, 1.4 mm proud with
a rolled crown; 5 the whisper grille, 95 holes on 5 rings; 6 its gold
ring; 7 the gold crescent moon; 8 the gold constellation, five stars and
four lines; 9 the gold "?" (hook and dot); 10-14 five small debossed
stars round the sides; 15 the parting reveal round the seam; 16 the gold
seat ring the ball rests in; 17 the black waisted stand, flared foot;
18 the cable arch in the foot at the back; 19 the USB-C well at the
bottom pole (pocket + liner); 20 four pan screws in wells on the back.
Inside: 21 the lens flange under the shell and the barrel with two tabs
holding the screen's ends; 22 the speaker's chamber tube; 23 the board
bulkhead with pads and fences, four corner tabs from the front; 24 four
insert columns and the lip keying front into back.
Materials: midnight-blue shell (front and back), indigo glass lens,
brass bezel, inlays and seat ring, matte-black stand, chrome screws.
Off the board: four M2.5 x 18 pan-head screws + four M2.5 heat-set inserts
(the only fasteners). Use a right-angle USB-C cable: the well is 14 mm
deep and the plug leaves 24 mm under the ball (STAND_H).
MEASURED (R990, 2026-11-17): ./check CHECK PASS, run_seconds 42 s, wall 72 s; every RESTYLE end CHECK PASS.
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
    "Front", "Lens", "Bezel", "Moon", "Constellation", "Grille_Ring", "Question_Mark", "Question_Dot", "Screw_1", "Screw_2", "Screw_3", "Screw_4"]}
REVIEW_CLOSEUPS = ["Bezel", "Lens"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and cutter in
# the stages is derived from them (the window, its lens, barrel, tabs and
# bezel; the stand's seat, waist and foot; every wall and boss). The
# ball's radius is not a knob: the board sets it.
WALL = 2.4         # RESTYLE 2.0..2.8 wall: the ball's shell
WINDOW_R = 21.0    # RESTYLE 17.5..24.5 radius: the crystal window
BEZEL_W = 4.5      # RESTYLE 3.8..5.2 width: the gold bezel ring round the window
STAND_H = 24.0     # RESTYLE 20..28 height: desk to the ball's bottom (room for the USB-C plug)
STAND_R = 52.0     # RESTYLE 44..60 radius: the stand's foot
# end RESTYLE
R_OUT = 75.0                   # the ball (150 mm): the board's corners sit at r 67.1
R_IN = R_OUT - WALL
ZO = STAND_H + R_OUT           # the ball's centre over the desk
H_SCR = 58.0                   # the screen's centre, out from the ball's centre along the window axis
Z_PAIR = 20.1                  # ports 4 + 5 centre over the board's centre (MEASURED): the screen's height
EL = math.degrees(math.asin(Z_PAIR / H_SCR))   # the window axis: up from horizontal
SCR_HALF = (9.75, 19.75, 4.82)  # screen module half sizes: across, along, thick (MEASURED)
BEZEL_UP = 1.4                 # the bezel stands proud of the ball
SEAT_R = (34.0, 44.0)          # the gold seat ring touches the ball between these radii
SPLIT_Y = 2.8                  # front / back seam: 0.3 behind the board's back
SCREW = "M2.5"
SCREW_RHO, SCREW_ANG = 66.0, (45, 135, 225, 315)
COLOURS = {"Front": "#1d2858", "Back": "#1d2858", "Lens": "#2f3c9e", "Bezel": "brass",
           "Stand": "matte_black", "Stand_Ring": "brass", "Moon": "brass",
           "Constellation": "brass", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
UPRIGHT_FRONT = Rotation(Vector(0, 0, 1), 180)
board = ap.board_object(doc)
board.Placement = Placement(V(), UPRIGHT_FRONT)
_b = ap.bbox(board)
board.Placement = Placement(V(-(_b.XMin + _b.XMax) / 2, 0, ZO - (_b.ZMin + _b.ZMax) / 2), UPRIGHT_FRONT)
BB = ap.bbox(board)                     # x -30..30, z ZO -60..ZO +60, PCB y 0..2.5
spk = ap.seat(doc, "speaker", (10, 11))  # left, low, hangs past the left edge: the whisper
imu = ap.seat(doc, "orientation", 3)     # seated square: it feels the shake
usb = ap.seat(doc, "usbc", 7)            # bottom centre, mouth straight down
# the window axis D (unit) and the screen on it, turned up EL about X
ER = math.radians(EL)
D = V(0, -math.cos(ER), math.sin(ER))
O = V(0, 0, ZO)
S = O + D * H_SCR
TILT = Placement(V(), Rotation(V(1, 0, 0), -EL), S)


def screen_route(zp):
    """Waypoints for a ribbon from a right-column plug at height zp: out of
    the right edge, forward, left behind the screen, a U-turn round its
    left end into its socket (all in the plane z = zp: no twist)."""
    yb = S.y + 8.0
    return [(36.0, -9.0, zp), (22.0, -24.0, zp), (-20.0, -27.0, zp), (-33.0, -36.0, zp), (-33.0, yb, zp)]


scr, scr_ribs = ap.cable(doc, "screen", (4, 5), TILT.multiply(ap.module_placement(
    "screen", (S.x, S.y, S.z), face="-Y", cable="-X")),
    via={4: screen_route(ZO + Z_PAIR - 9.9), 5: screen_route(ZO + Z_PAIR + 9.9)}, smooth=True)
for r_ in scr_ribs:
    if r_.Shape.Volume <= 0:
        raise cad.CadError("%s came out inside-out: change its waypoints" % r_.Label)
SB, UB, IB = [ap.bbox(m) for m in (spk, usb, imu)]
print("HW window EL %.1f deg; screen centre (%.1f, %.1f, %.1f); ribbons r <= %.1f" % (
    EL, S.x, S.y, S.z - ZO, max(max((p - O).Length for p in r_.Shape.tessellate(0.5)[0]) for r_ in scr_ribs)))
tick("hardware")


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def ball(r):
    """A solid sphere on the ball's centre, its poles to the sides (+-X),
    far from every window, grille and inlay."""
    return Part.makeSphere(r, O, V(1, 0, 0))


def to_window(s):
    """A shape built about +Z through the origin (the window frame: +Z is
    the window axis, +Y up the screen, +X across) moved onto the window
    axis D through the ball's centre."""
    s = s.copy()
    s.rotate(V(0, 0, 0), V(1, 0, 0), 90.0 - EL)
    s.translate(O)
    return s


def zc(r, h, z0):
    """A disc of radius r on the window axis from z0 to z0 + h (window frame)."""
    return Part.makeCylinder(r, h, V(0, 0, z0), V(0, 0, 1))


def wtube(r0, r1, z0, z1):
    return zc(r1, z1 - z0, z0).cut(zc(r0, z1 - z0 + 2, z0 - 1))


def arc(c, r, a0, a1):
    """('arc', mid, end) of the circle (c, r) from angle a0 to a1 (deg)."""
    am, a1 = math.radians((a0 + a1) / 2), math.radians(a1)
    return ("arc", (c[0] + r * math.cos(am), c[1] + r * math.sin(am)),
            (c[0] + r * math.cos(a1), c[1] + r * math.sin(a1)))


# ------------------------------------------------------------ the shell
hull = cad.cut(ball(R_OUT), ball(R_IN))
# the parting reveal goes in BEFORE the split (it needs a closed ring)
# (one ring cutter about Y: groove_ring on the sphere left a sliver solid)
YG = SPLIT_Y - 1.6
RG = math.sqrt(R_OUT ** 2 - YG ** 2)
hull = cad.cut(hull, cad.cut(cyl(RG + 2, (0, YG - 0.4, ZO), 0.8, (0, 1, 0)),
                             cyl(RG - 0.6, (0, YG - 1, ZO), 2, (0, 1, 0))))
front, back = cad.split(hull, "Y", at=SPLIT_Y, lip=1.2)
tick("shell")

# ------------------------------------------------------------ back: holds the board
# a bulkhead across the back half behind the lip, pads 0.1 mm off the
# board's back, fences 0.3 mm off its edges (behind the module layer)
YK = SPLIT_Y + 3.0
inside = ball(R_IN + 0.6)
bulk = cyl(R_OUT, (0, YK, ZO), 3.0, (0, 1, 0)).common(inside)
pads = [box(x - 4, x + 4, BB.YMax + 0.1, YK + 0.5, ZO + z - 4, ZO + z + 4)
        for x in (-18, 18) for z in (-44, 0, 44)]
fences = [box(sx * (BB.XMax + 0.3), sx * (BB.XMax + 2.3), 0.6, YK + 0.5, ZO + z0, ZO + z1)
          for sx in (-1, 1) for z0, z1 in ((-36, -16), (16, 36))]
fences += [box(x0, x1, 0.6, YK + 0.5, ZO + sz * (BB.ZMax - ZO + 0.3), ZO + sz * (BB.ZMax - ZO + 2.3))
           for sz in (-1, 1) for x0, x1 in ((-26, -14), (14, 26))]
back = cad.fuse_one(back, bulk, *pads, *fences)
# front: four tabs from the wall over the board's corners (ports 1, 6, 9
# and 14 stay empty there), 0.4 mm off the port housings
tabs = [box(sx * 25.0, sx * 40.0, -2.8, -6.5, ZO + sz * 55.0, ZO + sz * 70.0).common(inside)
        for sx in (-1, 1) for sz in (-1, 1)]
front = cad.fuse_one(front, *tabs)
# fasteners: four M2.5 pan screws from wells in the back into heat-set
# insert columns in the front (1.4 d + 0.1 pockets, a thread-forming
# pilot past them), all in ONE fuse and ONE cut per half
INSERT_D, PILOT_D, CLEAR_D, HEAD_D = 3.6, 2.1, 2.9, 6.0
Y_HEAD = SPLIT_Y + 11.0           # the head's seat at the foot of its well
SCREW_L = 18
SPOT_R = HEAD_D / 2 + 2.0
Y_SPOT = math.sqrt(R_OUT ** 2 - (SCREW_RHO + SPOT_R + 0.3) ** 2)   # the spot face's floor
screws, b_cols, b_cuts, f_cols, f_cuts = [], [], [], [], []
for a in SCREW_ANG:
    x, z = SCREW_RHO * math.cos(math.radians(a)), ZO + SCREW_RHO * math.sin(math.radians(a))
    # the column: slim past the lip, then wide round a flat spot face
    # whose floor meets the skin at the well's outboard edge (a well
    # drilled straight out through the sloping skin left a knife edge,
    # MEASURED 0.31 mm at WALL 2.8)
    b_cols.append(cyl(HEAD_D / 2 + 1.6, (x, SPLIT_Y + 0.1, z), 4.5, (0, 1, 0)))
    b_cols.append(cyl(SPOT_R + 1.6, (x, SPLIT_Y + 4.0, z), 60, (0, 1, 0)).common(inside))
    b_cuts.append(cyl(HEAD_D / 2, (x, Y_HEAD, z), Y_SPOT - Y_HEAD + 1.0, (0, 1, 0)))
    b_cuts.append(cyl(SPOT_R, (x, Y_SPOT, z), 80, (0, 1, 0)))
    b_cuts.append(cyl(CLEAR_D / 2, (x, SPLIT_Y - 1, z), Y_HEAD - SPLIT_Y + 2, (0, 1, 0)))
    f_cols.append(cyl(INSERT_D / 2 + 1.6, (x, SPLIT_Y - 0.1, z), 40, (0, -1, 0)).common(inside))
    f_cuts.append(cyl(INSERT_D / 2, (x, SPLIT_Y + 1.0, z), 6.0, (0, -1, 0)))
    f_cuts.append(cyl(PILOT_D / 2, (x, SPLIT_Y - 4.5, z), 7.0, (0, -1, 0)))
    screws.append(cad.screw("pan_phillips", SCREW, SCREW_L, at=(x, Y_HEAD, z), axis="-Y"))
back = cad.cut(cad.fuse_one(back, *b_cols), b_cuts)
front = cad.cut(cad.fuse_one(front, *f_cols), f_cuts)
tick("back + screws")

# ------------------------------------------------------------ the window (one axis)
# in the window frame: the screen's face at FACE, a crystal plug from
# 0.4 mm over it out to the ball's skin, a flange under the shell; a
# barrel round it from 3 mm over the face's level up into the wall, two
# tabs from the barrel hold the screen's ends (0.25 mm off); the gold
# bezel ring sits in a 1 mm groove round the window, BEZEL_UP proud
FACE = H_SCR + SCR_HALF[2]
FL_R = WINDOW_R + 1.8
FL_TOP = math.sqrt(R_IN ** 2 - FL_R ** 2) - 0.4
BAR_IN = max(WINDOW_R + 2.0, math.hypot(SCR_HALF[0], SCR_HALF[1]) + 0.4)   # clear of the screen's corners
BAR = (BAR_IN, BAR_IN + 2.0)
BAR0 = FACE - 3.0
lens = zc(WINDOW_R, R_OUT + 5 - (FACE + 0.4), FACE + 0.4)
lens = cad.fuse_one(lens.common(Part.makeSphere(R_OUT)), zc(FL_R, FL_TOP - (FACE + 0.4), FACE + 0.4))
barrel = wtube(BAR[0], BAR[1], BAR0, R_OUT).common(Part.makeSphere(R_IN + 0.6))
TAB_Y = (SCR_HALF[1] + 0.25, max(BAR[0] + 0.8, SCR_HALF[1] + 2.5))
ctabs = [box(-6, 6, sy * TAB_Y[0], sy * TAB_Y[1], H_SCR - SCR_HALF[2] + 1.5, BAR0 + 0.6) for sy in (-1, 1)]
barrel = cad.fuse_one(barrel, *ctabs)


def skin(rho):
    return math.sqrt(R_OUT ** 2 - rho ** 2)


B0, B1 = WINDOW_R, WINDOW_R + BEZEL_W
bezel_sec = [(B0, skin(B0) - 1.0), (B0, skin(B0) + BEZEL_UP - 0.6), arc((B0 + 0.6, skin(B0) + BEZEL_UP - 0.6), 0.6, 180, 90),
             (B1 - 1.2, skin(B1) + BEZEL_UP * 0.5), arc((B1 - 1.2, skin(B1) + BEZEL_UP * 0.5 - 1.2), 1.2, 90, 0),
             (B1, skin(B1) - 1.0)]
bezel = cad.revolve_profile(bezel_sec)
lens, barrel, bezel = to_window(lens), to_window(barrel), to_window(bezel)
front = cad.cut(front, [to_window(zc(WINDOW_R, 20, R_OUT - 10)), bezel])
front = cad.fuse_one(front, barrel)
tick("window")

# ------------------------------------------------------------ the whisper grille
# the speaker fires forward: a chamber tube from 0.5 mm off its face to
# the shell, a round grille where the tube meets the skin
kx, kz = (SB.XMin + SB.XMax) / 2, (SB.ZMin + SB.ZMax) / 2
GRILLE_D = 30.0
tube = cad.cut(cyl(16.6, (kx, SB.YMin - 0.5, kz), 80, (0, -1, 0)),
               cyl(15.0, (kx, SB.YMin + 1, kz), 90, (0, -1, 0))).common(inside)
front = cad.fuse_one(front, tube)
tick("tube")
ky = -math.sqrt(R_OUT ** 2 - kx ** 2 - (kz - ZO) ** 2)
# the holes laid out in rings (2.6 mm pitch, 1.6 mm holes) and drilled
# along the speaker's axis through the wall only, in ONE cut
# (cad.speaker_grille measures every hole on the sphere: 80 s MEASURED)
holes = []
for k in range(int((GRILLE_D / 2 - 0.8) / 2.6) + 1):
    n = max(1, int(round(2 * math.pi * k * 2.6 / 2.6)))
    for i in range(n):
        a = 2 * math.pi * (i + 0.5 * (k % 2)) / n
        x, z = kx + k * 2.6 * math.cos(a), kz + k * 2.6 * math.sin(a)
        y0 = -math.sqrt(R_OUT ** 2 - x ** 2 - (z - ZO) ** 2) - 1.0
        y1 = -math.sqrt(R_IN ** 2 - x ** 2 - (z - ZO) ** 2) + 1.0
        holes.append(cyl(0.8, (x, y0, z), y1 - y0, (0, 1, 0)))
print("GRILLE %d holes, open %.0f%% of d %g" % (len(holes), 100 * len(holes) * 0.64 / (GRILLE_D / 2) ** 2, GRILLE_D))
front = cad.cut(front, holes)

# ------------------------------------------------------------ USB-C at the bottom pole
# a pocket from below brings the wall to 0.25 mm under the mouth (a liner
# round it), then the measured opening; the plug comes up through the stand
ux, uy = (UB.XMin + UB.XMax) / 2, -5.9
UZ = UB.ZMin                           # the mouth
Z_BOT = ZO - R_OUT - 2.0
pocket = cad.rounded_box(18, 10, (UZ - 1.3) - Z_BOT, 3, at=(ux - 9, uy - 5, Z_BOT))
liner = cad.cut(cad.rounded_box(22, 14, (UZ - 0.25) - Z_BOT, 4, at=(ux - 11, uy - 7, Z_BOT))
                .common(ball(R_IN + 1.0)), pocket)
tick("grille")
front = cad.fuse_one(cad.cut(front, pocket), liner)
tick("pocket")
front = cad.socket_opening(front, usb, margin=1.5)
tick("grille + usb")

# ------------------------------------------------------------ the stand
# one revolved section: a foot ring, a waisted neck, the seat bowl that
# follows the ball 0.2 mm off; its top is the gold Stand_Ring (an insert
# keyed into the black stand); an arch in the foot lets the cable out
RS = R_OUT + 0.2


def seat_z(r):
    return ZO - math.sqrt(RS ** 2 - r ** 2)


Z_RIM = seat_z(SEAT_R[1])
RIM_R = SEAT_R[1] + 3.5
WAIST_R = max(0.76 * STAND_R, SEAT_R[0] + 5.0)   # a narrow foot keeps the neck round the key
Z_W = 0.45 * Z_RIM
ST_T = 3.0
stand_sec = [(STAND_R - 1.5, 0), (STAND_R, 1.5), (STAND_R, 4.0),
             ("arc", (WAIST_R + 0.30 * (STAND_R - WAIST_R), 0.55 * Z_W + 1.8), (WAIST_R, Z_W)),
             ("arc", (WAIST_R + 0.35 * (RIM_R - WAIST_R), 0.5 * (Z_W + Z_RIM - 2.0)), (RIM_R, Z_RIM - 2.0)),
             (RIM_R, Z_RIM - 0.8), arc((RIM_R - 0.8, Z_RIM - 0.8), 0.8, 0, 90),
             (SEAT_R[1], Z_RIM)]
# the seat: the ball's own sphere (0.2 mm off), from the rim down to the bore
TH = [math.asin(r / RS) for r in SEAT_R]
TM = 0.5 * (TH[0] + TH[1])
stand_sec += [("arc", (RS * math.sin(TM), ZO - RS * math.cos(TM)), (SEAT_R[0], seat_z(SEAT_R[0]))),
              (SEAT_R[0], seat_z(SEAT_R[0]) - 2.5), (WAIST_R - ST_T, Z_W),
              ("arc", (WAIST_R + 0.30 * (STAND_R - WAIST_R) - ST_T, 0.55 * Z_W + 1.8), (STAND_R - ST_T, 4.0)),
              (STAND_R - ST_T, 0)]
stand = cad.revolve_profile(stand_sec, at=(0, 0, 0))
# the gold seat ring: the whole seat and rim, keyed 2.5 mm down into the
# black stand (an insert: it fills its own groove exactly)
Z_CUT = seat_z(SEAT_R[0]) - 1.5
ring_cut = cad.cut(cyl(RIM_R + 2, (0, 0, Z_CUT), 20), cyl(SEAT_R[0] - 1, (0, 0, Z_CUT - 1), 22))
KEY = (SEAT_R[0] + 2.5, SEAT_R[0] + 5.5)   # away from the outer flare (a short stand thins it there)
ring_cut = cad.fuse_one(ring_cut, cad.cut(cyl(KEY[1], (0, 0, Z_CUT - 2.5), 3.0), cyl(KEY[0], (0, 0, Z_CUT - 3), 4)))
stand_ring = stand.common(ring_cut)
stand = cad.cut(stand, ring_cut)
# the cable arch at the back of the foot
# (straight facets, not a half-round: a round top reads as a clip channel)
arch = Part.Face(Part.makePolygon([V(x, 20, z) for x, z in (
    (-6.5, -1), (6.5, -1), (6.5, 6.0), (3.5, 9.0), (-3.5, 9.0), (-6.5, 6.0), (-6.5, -1))])).extrude(V(0, STAND_R + 5, 0))
stand = cad.cut(stand, arch)
tick("stage A")


# === STAGE B: details ===
# gold inlays: each piece is the shell's outer 0.8 mm (and 0.5 mm proud)
# under a prism in the tangent plane, cut from the Front - it fills its
# own pocket exactly
INLAY = (R_OUT - 0.8, R_OUT + 0.5)
layer = cad.cut(Part.makeSphere(INLAY[1], O), Part.makeSphere(INLAY[0], O))


def unit(az, el):
    """The outward direction at azimuth az (deg, 0 = front, + = right) and
    elevation el (deg)."""
    a, e = math.radians(az), math.radians(el)
    return V(math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))


def frame(u):
    right = V(0, 0, 1).cross(u)
    right.normalize()
    return right, u.cross(right)


def prism(u, pts2d):
    """A prism of the outline pts2d (mm, in u's tangent plane: x right, y
    up) through the inlay layer at direction u."""
    rt, up = frame(u)
    c = O + u * (R_OUT + 1.5)
    f = Part.Face(Part.makePolygon([c + rt * x + up * y for x, y in pts2d] + [c + rt * pts2d[0][0] + up * pts2d[0][1]]))
    return f.extrude(u * -5.0)


def star_pts(r, rot=0.0):
    return [((r if i % 2 == 0 else 0.42 * r) * math.cos(math.radians(90 + rot + 36 * i)),
             (r if i % 2 == 0 else 0.42 * r) * math.sin(math.radians(90 + rot + 36 * i))) for i in range(10)]


# the crescent moon, upper left, horns to the right
MOON = (-42.0, 40.0, 11.0)          # azimuth, elevation, radius
# (a polygon, its horn tips 1.4 mm wide: two circles subtracted leave
# knife-edge tips, MEASURED 0.06 mm)
cres = []
for i in range(25):
    t = -1 + 2 * i / 24.0
    th = math.radians(180 + 135 * t)
    cres.append((MOON[2] * math.cos(th), MOON[2] * math.sin(th)))
for i in range(25):
    t = 1 - 2 * i / 24.0
    th = math.radians(180 + 128 * t)
    rr = MOON[2] - (1.4 + 0.42 * MOON[2] * (1 - t * t))
    cres.append((rr * math.cos(th) + 0.18 * MOON[2] * (1 - t * t), rr * math.sin(th)))
moon = prism(unit(MOON[0], MOON[1]), cres).common(layer)
# a constellation: five stars over the top, joined by fine gold lines (one inlay)
STARS = [(-20.0, 58.0, 4.5), (2.0, 66.0, 3.2), (28.0, 60.0, 4.0), (46.0, 47.0, 3.0), (34.0, 33.0, 3.6)]
LINE_W = 1.2
pieces = [prism(unit(a, e), star_pts(r, 8 * i)) for i, (a, e, r) in enumerate(STARS)]
for (a0, e0, _r0), (a1, e1, _r1) in zip(STARS, STARS[1:]):
    ua, ub = unit(a0, e0), unit(a1, e1)
    nrm = ua.cross(ub)
    nrm.normalize()
    pts = [O + (ua * (1 - t) + ub * t).normalize() * (R_OUT + 1.5) for t in (0, 0.25, 0.5, 0.75, 1)]
    pts += [O + (ua * (1 - t) + ub * t).normalize() * (R_OUT - 3.0) for t in (1, 0.75, 0.5, 0.25, 0)]
    f = Part.Face(Part.makePolygon(pts + [pts[0]]))
    f.translate(nrm * (-LINE_W / 2))
    pieces.append(f.extrude(nrm * LINE_W))
constellation = cad.fuse_one(*pieces).common(layer)
# a gold ring round the whisper grille
grille_ring = cad.cut(cyl(GRILLE_D / 2 + 3.4, (kx, 0, kz), 90, (0, -1, 0)),
                      cyl(GRILLE_D / 2 + 1.4, (kx, 1, kz), 92, (0, -1, 0))).common(layer)
front = cad.cut(front, [moon, constellation, grille_ring])
tick("moon + stars")
# the question mark: debossed under the window, filled gold (hook and dot)
QU = unit(-52.0, 2.0)
q_at = O + QU * R_OUT
deb = cad.text(front, "?", q_at, QU, 20.0, depth=1.0, mode="deboss", up=frame(QU)[1])
q = front.cut(deb)
front = deb
q_parts = sorted(q.Solids, key=lambda s: -s.Volume)
# small debossed stars scattered round the back and the sides
for a, e, r in ((-70, 10, 3.0), (-60, -25, 2.4), (70, 20, 2.6), (60, -12, 3.0), (-28, -42, 2.2)):
    tool = prism(unit(a, e), star_pts(r)).common(cad.cut(Part.makeSphere(R_OUT + 1, O), Part.makeSphere(R_OUT - 0.6, O)))
    front = cad.cut(front, tool, optional=True)
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape, colour=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = cad.color(COLOURS[colour or name])
    return o


part("Back", back)
part("Front", front)
o = part("Lens", lens)
o.ViewObject.Transparency = cad.transparency("glass")
part("Bezel", bezel)
part("Stand", stand)
part("Stand_Ring", stand_ring)
part("Moon", moon)
part("Constellation", constellation)
part("Grille_Ring", grille_ring, "Moon")
for i, sh in enumerate(q_parts):
    part(("Question_Mark", "Question_Dot")[i], sh, "Moon")
for i, sh in enumerate(screws):
    part("Screw_%d" % (i + 1), sh, "Screw")
print("SIZE %s" % (cad.measure(Part.makeCompound([front, back, stand]))["size"],))
print("TOTAL %.1f s" % (time.time() - T0))
