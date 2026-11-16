"""Example: "a smart bird feeder camera" - a little porch house that photographs every bird on its perch.

fork this file for a bird feeder camera (a smart bird feeder, a bird
house camera, a squirrel-cam feeder, a wildlife feeder cam, a nest box
camera); change PARAMETERS and the outlines.
ARCHETYPE: bird feeder camera

How it is built (R940):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board FLAT and FACE DOWN (modules look at the ground, -Z) in the attic
    under a front-gable roof, its long side front to back, its front edge
    out over the porch. The camera on (1, 2) and the PIR on 9 sit side by
    side at the board's front end and look STRAIGHT DOWN through OPEN
    apertures in a black eye pod set into the porch soffit (no glass over
    the lens, none over the PIR dome: infrared does not pass plastic) -
    right over the gap between the perch and the seed tray, where a
    feeding bird leans its head in. USB-C on 8 at the board's back end,
    its mouth in the back gable under the roof overhang (a recess brings
    the wall to 1.2 mm in front of the mouth). The ATTIC plate is the
    fixed part: it carries the board on a spine rib and edge posts, closes
    the hopper from above and runs forward as the porch ceiling; the
    ROOF (two slabs, gable walls, side knees) sits on it, fitted after,
    four M2.5 screws up from below. The attic + roof lift off the house
    BODY (four pegs in its corner posts) to fill the hopper: a box of four
    walls with a clear hopper window, a ramp inside sliding the seed out
    of a feed slot into the tray. The BASE plate under it all carries the
    tray (rim, drain holes) and two arms with porch posts (pegged into
    the soffit) that hold the perch dowel; four M2.5 screws up into the
    body's corner posts.
  * STAGE B - details: shingle courses with staggered tab slits, a ridge
    cap, drip edges and barge boards, the hanging loop, a cream bird badge
    inlaid through the front gable, lap siding, a window frame, lettering.
RESTYLE (R940): WIDTH, BODY_H, EAVE, PERCH_GAP, CORNER and WALL drive every
outline and cutter below; the depth and the porch follow the board (the
back gable from the USB-C mouth, the perch and the tray from the PIR's
and the camera's view: their straight-down rays fall between them).
DETAILS (visible, 30): 1 front-gable house roof; 2 eaves overhanging the
walls; 3 drip edges under both eaves; 4 barge boards under the front and
back overhangs; 5 shingle courses on both slopes; 6 staggered tab slits;
7 a ridge cap; 8 the hanging loop on the ridge; 9 a deep porch roof over
the tray; 10 the cream bird badge inlaid in the front gable; 11 its
debossed eye, legs and branch; 12 black eye pod under the porch soffit;
13 its OPEN flared camera aperture; 14 its OPEN flared PIR window;
15 clear hopper window; 16 its raised frame; 17 seed showing in the
hopper; 18 the feed slot under the window; 19 lap siding on the sides and
back; 20 seed tray with a rounded rim; 21 drain holes in the tray;
22 the wood perch dowel; 23-24 two porch posts on arms; 25 "ATECH" on the
tray rim; 26 USB-C recess in the back gable; 27-30 countersunk screws:
four M2.5 x 12 under the base, four M2.5 x 10 in the soffit (one screw type).
Inside: a seed ramp, four corner posts with pegs and pilots, the spine
rib, board posts, front stops, a hold-down rib from the ridge, flat
screw pads under the slopes.
Materials: cream house and soffit, terracotta roof, graphite base, tray
and posts, black eye pod, clear hopper window, wood perch, chrome screws.
Placeholders: the PIR lens is a stand-in shape (measure the real AM312);
the camera has no SDK driver yet (no firmware); the roof + attic lift off
to fill seed, held only by four pegs (no latch).
MEASURED (R940, 2026-11-10): ./check CHECK PASS, model 10-19 s, ./check wall 25-49 s; every RESTYLE knob at its min and max CHECK PASS.
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
    "Roof", "Bird_Badge", "Screw_5", "Screw_6", "Screw_7", "Screw_8"]}
REVIEW_CLOSEUPS = ["Pod_Bezel", "Roof", "Base"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them (the ridge rises by itself when
# a narrow house would bring the roof down onto the board: see ZR below).
WIDTH = 110.0      # RESTYLE 93.5..126.5 width: the house body across (x)
BODY_H = 95.0      # RESTYLE 80..115 height: the body walls (z)
EAVE = 14.0        # RESTYLE 11.9..18 length: the roof's overhang past the side walls
PERCH_GAP = 22.0   # RESTYLE 18..26 length: perch front to tray rim (a bird's reach)
CORNER = 4.0       # RESTYLE 3.4..4.6 radius: the body's four upright corners
WALL = 2.5         # RESTYLE 2.1..2.9 wall
# end RESTYLE
PITCH = 38.0                     # the roof slopes (deg)
BASE_T = 6.0                     # the base plate
SOFF_T = 2.5                     # the attic plate / porch soffit
ROOF_T = 3.0                     # the roof slabs (across the slope)
OV_FRONT, OV_BACK = 6.0, 8.0     # the roof past the front and back gables
XC = 30.0                        # the board's centre line
X0, X1 = XC - WIDTH / 2, XC + WIDTH / 2
ZS = BASE_T + BODY_H + SOFF_T    # the attic plate's top face
BZ = ZS + 10.3                   # the board's box bottom: the lens tip 0.45 mm over the soffit
RIM_H, RIM_T = 10.0, 2.5         # the tray rim
PERCH_D = 7.0
POST = 10.0                      # the porch posts (square; the perch bore through them)
SCREW = "M2.5"                   # ONE screw type: M2.5 countersunk, 12 mm (base) and 10 mm (roof)
SEED_Z = BASE_T + 0.62 * BODY_H     # the seed level shown in the hopper
COLOURS = {"Seed": "#c9a66b", "Bird_Badge": "#f6efe0", "Body": "cream", "Roof": "#b85c3c", "Base": "graphite", "Attic": "cream",
           "Pod_Bezel": "matte_black", "Hopper_Window": "glass", "Perch_Dowel": "wood",
           "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
FACE_DOWN = Rotation(Vector(1, 0, 0), -90)    # modules face -Z; board x 0..60, y 0..120
board = ap.board_object(doc)


def place_board(rot, x0=0.0, y0=0.0, z0=0.0):
    board.Placement = Placement(Vector(), rot)
    bb = ap.bbox(board)
    board.Placement = Placement(Vector(x0 - bb.XMin, y0 - bb.YMin, z0 - bb.ZMin), rot)


place_board(FACE_DOWN, 0, 0, BZ)              # ports 1-6 at x 0..20, 9-14 at x 40..60, 7 front, 8 back
BB = ap.bbox(board)
cam = ap.seat(doc, "camera", (1, 2))          # front left: the lens looks down at the perch
pir = ap.seat(doc, "pir", 9)                  # front right, beside it
usb = ap.seat(doc, "usbc", 8)                 # the back end, mouth +Y
tick("hardware")
CB, PB_, UB = ap.bbox(cam), ap.bbox(pir), ap.bbox(usb)
# measured: the lens tip and the PIR dome are the lowest points at the
# module's middle (probe R940: lens (9.4, 20.0), dome (50.6, 10.1))
CAM_C = ((CB.XMin + CB.XMax) / 2, (CB.YMin + CB.YMax) / 2)
PIR_C = ((PB_.XMin + PB_.XMax) / 2, (PB_.YMin + PB_.YMax) / 2)
YB = UB.YMax + 0.25 + WALL       # the back: the gable's inner face 0.25 mm off the USB-C mouth
YP = BB.YMin - 6.0               # the porch front: the front gable's outer face
YF = YB - 63.35                  # the body's front wall (the hopper behind it)
PERCH_Y = PIR_C[1] - 10.0        # the perch, just in front of the PIR's view
YT = PERCH_Y + PERCH_D / 2 + PERCH_GAP   # the tray rim's front face
PERCH_Z = BASE_T + RIM_H + 6.0


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


def soft_rect(x0, x1, y0, y1, r):
    """A rectangle's (u, v) outline, each corner 3 straight facets (an arc
    corner reads as a clip channel, R7)."""
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for k in range(4):
            a = math.radians(a0 + 30 * k)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def zplate(pts, z0, z1):
    w = Part.makePolygon([V(x, y, z0) for x, y in pts] + [V(pts[0][0], pts[0][1], z0)])
    return Part.Face(w).extrude(V(0, 0, z1 - z0))


def insert(shell, cutter):
    """(shell with the opening, the piece that fills it exactly)."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1:
        piece, rest = shell.common(cutter, 0.01), shell.cut(cutter, 0.01)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, piece


# ------------------------------------------------------------ the roof
K = math.tan(math.radians(PITCH))
TV = ROOF_T / math.cos(math.radians(PITCH))      # the slab's vertical thickness
HW = WIDTH / 2
# the ridge (outer): the slab's underside 1 mm over the plate at the walls,
# or higher when a narrow or flat roof would come down onto the board
# (its ceiling 1.5 mm over the board 2 mm outside its edges)
ZR = max(ZS + 1.0 + TV + HW * K, BB.ZMax + 1.8 + TV + (BB.XMax - XC + 2.0) * K)
E = HW + EAVE


def top(d):
    return ZR - d * K


def under(d):
    return top(d) - TV


slab = prism_xz([(XC - E, top(E)), (XC, ZR), (XC + E, top(E)), (XC + E, under(E)),
                 (XC, ZR - TV), (XC - E, under(E))], YP - OV_FRONT, YB + OV_BACK)
block = prism_xz([(X0, ZS), (X1, ZS), (X1, under(HW) + 0.6), (XC, ZR - TV + 0.6),
                  (X0, under(HW) + 0.6)], YP, YB)
hw_in = HW - WALL
cavity = prism_xz([(X0 + WALL, ZS - 1), (X1 - WALL, ZS - 1), (X1 - WALL, under(hw_in) - 0.3),
                   (XC, ZR - TV - 0.3), (X0 + WALL, under(hw_in) - 0.3)], YP + WALL, YB - WALL)
roof = cad.fuse_one(slab, cad.cut(block, cavity))
# the hold-down rib from the ridge onto the board's back, 0.2 mm off it
roof = cad.fuse_one(roof, box(XC - 1, XC + 1, 45, 75, BB.ZMax + 0.2, ZR - TV + 0.5))
# two stops from the front gable to 0.3 mm off the board's front edge,
# either side of the bird badge (the modules slide in along x behind them)
roof = cad.fuse_one(roof, *[box(x, x + 4, YP + WALL - 0.5, BB.YMin - 0.3, BB.ZMin, BB.ZMax - 1)
                            for x in (BB.XMin + 2, BB.XMax - 6)])
tick("roof")

# ------------------------------------------------------------ the attic plate (fixed)
attic = box(X0, X1, YP, YB, ZS - SOFF_T, ZS)
# the board rides on a rib under its spine and between edge posts (0.3 mm clear)
attic = cad.fuse_one(attic, box(XC - 1, XC + 1, 50, 70, ZS - 0.5, BB.ZMin - 0.2))
posts = [box(BB.XMin - 2.3, BB.XMin - 0.3, y, y + 6, ZS - 0.5, BB.ZMax - 2) for y in (60, 96)]
posts += [box(BB.XMax + 0.3, BB.XMax + 2.3, y, y + 6, ZS - 0.5, BB.ZMax - 2) for y in (46, 90)]
attic = cad.fuse_one(attic, *posts)

# the eye pod: a black insert through the soffit under the camera and the
# PIR, 3 mm proud below it, its two apertures OPEN and flared
PX0, PX1 = CAM_C[0] - 12, PIR_C[0] + 12
PY0, PY1 = min(CAM_C[1], PIR_C[1]) - 12, max(CAM_C[1], PIR_C[1]) + 12
pod_cut = zplate(soft_rect(PX0, PX1, PY0, PY1, 4), ZS - SOFF_T - 1, ZS + 1)
attic, pod = insert(attic, pod_cut)
POD_Z = ZS - SOFF_T - 5.0
lip = zplate(soft_rect(PX0, PX1, PY0, PY1, 4), POD_Z, ZS - SOFF_T + 0.5)
lip = cad.soften(lip, 1.5, [e for e in lip.Edges if e.BoundBox.ZMax < POD_Z + 0.01])
pod = cad.fuse_one(pod, lip)
pod = cad.cut(pod, [Part.makeCone(6.0, 8.5, ZS + 0.5 - POD_Z + 0.5, V(CAM_C[0], CAM_C[1], ZS + 0.5), V(0, 0, -1)),
                    Part.makeCone(6.5, 8.5, ZS + 0.5 - POD_Z + 0.5, V(PIR_C[0], PIR_C[1], ZS + 0.5), V(0, 0, -1))])
tick("attic + pod")

# ------------------------------------------------------------ the body (the hopper)
ZT = ZS - SOFF_T                 # the body's top
outer = cad.rounded_box(WIDTH, YB - YF, ZT - BASE_T, CORNER, at=(X0, YF, BASE_T))
body = cad.cut(outer, box(X0 + WALL, X1 - WALL, YF + WALL, YB - WALL, BASE_T - 1, ZT + 1))
CP = 8.0                         # the corner posts inside
CORNERS = [(X0 + WALL + CP / 2, YF + WALL + CP / 2), (X1 - WALL - CP / 2, YF + WALL + CP / 2),
           (X0 + WALL + CP / 2, YB - WALL - CP / 2), (X1 - WALL - CP / 2, YB - WALL - CP / 2)]
cposts = [box(x - CP / 2 - 0.5, x + CP / 2 + 0.5, y - CP / 2 - 0.5, y + CP / 2 + 0.5, BASE_T, ZT)
          for x, y in CORNERS]
ramp = prism_yz([(YF + WALL - 0.5, BASE_T), (YB - WALL + 0.5, BASE_T), (YB - WALL + 0.5, BASE_T + 28),
                 (YF + WALL - 0.5, BASE_T + 1.5)], X0 + WALL - 0.5, X1 - WALL + 0.5)
body = cad.fuse_one(body, ramp, *cposts)
# the feed slot under the window: the seed slides off the ramp into the tray
body = cad.cut(body, box(XC - 32, XC + 32, YF - 1, YF + WALL + 1, BASE_T - 1, BASE_T + 8))
# the hopper window: a clear insert filling the front wall
WZ0, WZ1 = BASE_T + 22, ZT - 14
body, window = insert(body, prism_xz(soft_rect(XC - 34, XC + 34, WZ0, WZ1, 7), YF - 1, YF + WALL + 1))
# the seed in the hopper, shown 0.8 mm off the ramp, the walls and the posts
# (loose content, not a housing part: it must not "meet" the body)
ramp_up = ramp.copy()
ramp_up.translate(V(0, 0, 0.8))
seed = box(X0 + WALL + 0.8, X1 - WALL - 0.8, YF + WALL + 0.8, YB - WALL - 0.8, BASE_T + 0.8, SEED_Z)
seed = cad.cut(seed, [ramp_up] + [box(x - CP / 2 - 1.3, x + CP / 2 + 1.3, y - CP / 2 - 1.3, y + CP / 2 + 1.3,
                                      BASE_T - 1, SEED_Z + 1) for x, y in CORNERS])
tick("body")

# ------------------------------------------------------------ the base, tray, porch posts
base = cad.rounded_box(WIDTH + 8, YB + 4 - YT, BASE_T, 5.0, at=(X0 - 4, YT, 0))
PX = (X0 + 4 + POST / 2, X1 - 4 - POST / 2)      # the porch posts' centres
arms = [box(x - POST / 2 - 1, x + POST / 2 + 1, PERCH_Y - POST / 2 - 1, YT + 1, 0, BASE_T) for x in PX]
pposts = [box(x - POST / 2, x + POST / 2, PERCH_Y - POST / 2, PERCH_Y + POST / 2, BASE_T - 0.5, ZT) for x in PX]
pposts = [cad.soften(p, 1.5, [e for e in p.Edges if e.BoundBox.ZLength > 10]) for p in pposts]
rim_o = zplate(soft_rect(X0 - 4, X1 + 4, YT, YF + 6, 4), BASE_T - 0.5, BASE_T + RIM_H)
rim_i = zplate(soft_rect(X0 - 4 + RIM_T, X1 + 4 - RIM_T, YT + RIM_T, YF + 12, 2), BASE_T - 1, BASE_T + RIM_H + 1)
rim = cad.cut(rim_o, rim_i)
rim = cad.soften(rim, 0.8, [e for e in rim.Edges if e.BoundBox.ZMin > BASE_T + RIM_H - 0.01])
base = cad.fuse_one(base, rim, *(arms + pposts))
# the perch: a wood dowel through both posts (0.2 mm clear)
# (a soft-square bore: a round one through both posts reads as a hole through 2 walls)
oct_r = (PERCH_D / 2 + 0.2) / math.cos(math.radians(22.5))
base = cad.cut(base, prism_yz([(PERCH_Y + oct_r * math.cos(math.radians(22.5 + 45 * k)),
                                PERCH_Z + oct_r * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)],
                              X0 - 1, X1 + 1))
perch = cyl(PERCH_D / 2, (X0 - 1, PERCH_Y, PERCH_Z), WIDTH + 2, (1, 0, 0))
# drain holes in the tray floor
drains = [cyl(1.3, (x, y, -1), BASE_T + 2) for x in [XC + 12 * i for i in range(-3, 4)]
          for y in (YT + RIM_T + 6, (YT + YF) / 2 + 1, YF - 5)]
base = cad.cut(base, drains)
tick("base")

# ------------------------------------------------------------ joints
# pegs: the attic onto the body's corner posts and onto the porch posts
PEG_D = 3.0
for x, y in CORNERS:
    body = cad.cut(body, cyl((PEG_D + 0.3) / 2, (x, y, ZT - 5), 5.5))
    attic = cad.fuse_one(attic, cyl(PEG_D / 2, (x, y, ZT - 4.5), 5.0))
for x in PX:
    attic = cad.cut(attic, cyl((PEG_D + 0.3) / 2, (x, PERCH_Y, ZT - 0.5), 2.7))
    base = cad.fuse_one(base, cyl(PEG_D / 2, (x, PERCH_Y, ZT - 0.5), 2.5))
# four M2.5 screws up through the base into the body's corner posts
screws = []
for x, y in CORNERS:
    base = cad.countersink(base, (x, y, 0), "+Z", 2.9, 5.6, 90.0, through="wall")
    body = cad.hole(body, (x, y, BASE_T), "+Z", 2.1, depth=10)      # the M2.5 thread-forming pilot
    screws.append(cad.screw("csk_phillips", SCREW, 12, at=(x, y, 0), axis="+Z"))
# four M2.5 screws up through the attic plate into bosses in the roof
# (15 mm in from the side walls, at least 6 mm outside the board's edges;
# the back pair clear of the board posts)
SX = (min(X0 + 15, BB.XMin - 6), max(X1 - 15, BB.XMax + 6))
ROOF_SCREWS = [(SX[0], 46.0), (SX[1], 46.0), (SX[0], YB - 34), (SX[1], YB - 34)]
for x, y in ROOF_SCREWS:
    # a flat pad under the sloped slab first: a boss under a slope only
    # meets it at one edge (a 0.5 mm wall, MEASURED)
    # (its flat bottom under the lowest ceiling over it, the boss below it)
    dd = abs(x - XC)
    zb = under(dd + 3.5) - 0.8
    roof = cad.fuse_one(roof, prism_xz([(x - 3.5, zb), (x + 3.5, zb), (x + 3.5, under(abs(x + 3.5 - XC)) + 0.5),
                                        (x - 3.5, under(abs(x - 3.5 - XC)) + 0.5)], y - 3.5, y + 3.5))
    attic, roof = cad.screw_through(attic, roof, (x, y, ZS - SOFF_T), size=SCREW, ribs=0)
    # 10 mm: the length screw_through prints (the tip 0.3 mm short of the pilot's bottom)
    screws.append(cad.screw("csk_phillips", SCREW, 10, at=(x, y, ZS - SOFF_T), axis="+Z"))
# USB-C in the back gable: a recess outside brings the wall to 1.2 mm
ux = (UB.XMin + UB.XMax) / 2
uz = BB.ZMin + 4.5 - 5.9          # the receptacle: 5.9 mm under the PCB face
roof = cad.cut(roof, prism_xz(soft_rect(ux - 9, ux + 9, uz - 5.5, uz + 5.5, 2.5), YB - 1.3, YB + 1))
roof = cad.socket_opening(roof, usb, margin=1.5)
tick("stage A")


# === STAGE B: details ===
# the roof: shingle courses (grooves along the eaves, staggered tab slits),
# drip edges under both eaves, barge boards under the gable overhangs, a
# ridge cap and the hanging loop
YR0, YR1 = YP - OV_FRONT, YB + OV_BACK
cutters = []
COURSE = 9.0
ds = [E - 2.0 - COURSE * i for i in range(int((E - 8.0) / COURSE) + 1)]
ang = math.radians(PITCH)
for sg in (-1, 1):
    sx, sz = sg * math.cos(ang), -math.sin(ang)        # down the slope
    nx, nz = sg * math.sin(ang), math.cos(ang)         # out of it
    for i, d in enumerate(ds):
        px, pz = XC + sg * d, top(d)
        cutters.append(prism_xz([(px - sx * 0.5 + nx * 0.5, pz - sz * 0.5 + nz * 0.5),
                                 (px + sx * 0.5 + nx * 0.5, pz + sz * 0.5 + nz * 0.5),
                                 (px + sx * 0.5 - nx * 0.8, pz + sz * 0.5 - nz * 0.8),
                                 (px - sx * 0.5 - nx * 0.8, pz - sz * 0.5 - nz * 0.8)], YR0 - 1, YR1 + 1))
        if i + 1 < len(ds):                            # tab slits in the course above this groove
            # (as deep as the grooves and running 0.3 mm into both: no thin step)
            d2 = ds[i + 1] + 0.2
            qx, qz = XC + sg * d2, top(d2)
            quad = [(px - sx * 0.2 + nx * 0.5, pz - sz * 0.2 + nz * 0.5), (qx + nx * 0.5, qz + nz * 0.5),
                    (qx - nx * 0.8, qz - nz * 0.8), (px - sx * 0.2 - nx * 0.8, pz - sz * 0.2 - nz * 0.8)]
            y = YR0 + (6.0 if i % 2 else 14.0)
            while y < YR1 - 4:
                cutters.append(prism_xz(quad, y, y + 0.9))
                y += 16.0
roof = cad.cut(roof, cutters)
tick("shingles")
trims = []
for sg in (-1, 1):
    xo, xi = XC + sg * E, XC + sg * (E - 1.8)
    trims.append(prism_xz([(xi, under(E - 1.8) + 0.4), (xo, under(E) + 0.4), (xo, under(E) - 2.2),
                           (xi, under(E) - 2.2)], YR0, YR1))
for y0 in (YR0, YR1 - 2.5):
    trims.append(prism_xz([(XC - E, under(E) + 0.5), (XC, ZR - TV + 0.5), (XC + E, under(E) + 0.5),
                           (XC + E, under(E) - 2.2), (XC, ZR - TV - 3.0), (XC - E, under(E) - 2.2)], y0, y0 + 2.5))
trims.append(cyl(3.2, (XC, YR0, ZR - 1.2), YR1 - YR0, (0, 1, 0)))
LOOP_Y, LOOP_Z = (YP + YB) / 2 + 8.0, ZR + 9.0
trims.append(cad.cut(cyl(9.0, (XC - 2.0, LOOP_Y, LOOP_Z), 4.0, (1, 0, 0)),
                     cyl(5.5, (XC - 3.0, LOOP_Y, LOOP_Z), 6.0, (1, 0, 0))))
roof = cad.fuse_one(roof, *trims)
# the bird silhouette: a cream badge inlaid through the front gable, on a
# debossed branch
BIRD = [(-15, 5.8), (-12.6, 6.9), (-11.5, 8.4), (-9.5, 9.4), (-7, 9.5), (-4.8, 8.3), (-2, 6.6),
        (2.5, 5.6), (7, 4.4), (11, 3.6), (15, 6.6), (14.6, 4.4), (11.5, 1.4), (8, -0.6), (5, -2.6),
        (1, -4.3), (-3.5, -4.6), (-7.5, -3), (-9.8, -0.6), (-11, 2), (-12.6, 4.6)]
BS, BZC = 1.25, ZS + 16.0
roof, badge = insert(roof, Part.Face(Part.makePolygon([V(XC + u * BS, YP - 1.0, BZC + v * BS)
                                                       for u, v in BIRD + BIRD[:1]])).extrude(V(0, WALL + 2, 0)))
badge = cad.cut(badge, cyl(1.1, (XC - 11.0, YP - 0.5, BZC + 7.8), 1.3, (0, 1, 0)))     # the eye
roof = cad.cut(roof, box(XC - 20, XC + 15, YP - 0.5, YP + 0.8, BZC - 10.2, BZC - 8.6))
# legs: from the belly to the branch
roof = cad.cut(roof, [box(XC - 3.5, XC - 2.3, YP - 0.5, YP + 0.8, BZC - 9.0, BZC - 5.0),
                      box(XC + 0.8, XC + 2.0, YP - 0.5, YP + 0.8, BZC - 9.0, BZC - 3.0)])
tick("roof trim")
# the hopper window's raised frame, the wordmark on the tray rim
frame = cad.cut(prism_xz(soft_rect(XC - 37, XC + 37, WZ0 - 3, WZ1 + 3, 9), YF - 1.2, YF + 0.5),
                prism_xz(soft_rect(XC - 34, XC + 34, WZ0, WZ1, 7), YF - 2, YF + 1))
body = cad.fuse_one(body, frame)
# lap siding on the body's sides and back
sid = []
for z in [BASE_T + 10 + 8.0 * i for i in range(int((ZT - BASE_T - 16) / 8.0) + 1)]:
    sid += [box(X0 - 1, X0 + 0.6, YF + CORNER + 1, YB - CORNER - 1, z, z + 0.8), box(X1 - 0.6, X1 + 1, YF + CORNER + 1, YB - CORNER - 1, z, z + 0.8),
            box(X0 + CORNER + 1, X1 - CORNER - 1, YB - 0.6, YB + 1, z, z + 0.8)]
body = cad.cut(body, sid)
base = cad.text(base, "ATECH", (XC, YT, BASE_T + RIM_H / 2), (0, -1, 0), 5.0, depth=0.4, mode="deboss")
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape, colour=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = cad.color(COLOURS[colour or name])
    return o


for nm, sh in (("Attic", attic), ("Body", body), ("Base", base), ("Roof", roof), ("Pod_Bezel", pod),
               ("Perch_Dowel", perch), ("Seed", seed), ("Bird_Badge", badge)):
    part(nm, sh)
o = part("Hopper_Window", window)
o.ViewObject.Transparency = cad.transparency("glass")
for i, sh in enumerate(screws):
    part("Screw_%d" % (i + 1), sh, "Screw")
print("SIZE", cad.measure(Part.makeCompound([attic, body, base, roof]))["size"])
print("TOTAL %.1f s" % (time.time() - T0))
