"""Example: "a cloud lamp that flashes lightning to music" - a puffy glowing cumulus held up by a yellow lightning bolt.

fork this file for a cloud lamp / thunder cloud / mood light on a stand (a storm
lamp, a music-reactive light sculpture, a cloud night light); change PARAMETERS and the outlines.
ARCHETYPE: cloud lamp

How it is built (R990):
  * STAGE A - hardware, shell, every working-face opening, fasteners:
    the board FLAT in a graphite puck base on the desk (the stable end of
    the lamp). The microphone (13, 14) hears the music through a pin-hole
    grille in the FRONT of the deck - in front of the cloud, because a mic
    under the cloud hears nothing (./check casts its rays straight up and
    the cloud is in the way); the mode key (6) sits under a cap at the
    front left, a status light (5) glows through a little frosted bolt
    window beside it, USB-C (7) is in a pocket in the back wall. The
    cloud's light is CABLED from port 3: its ribbon leaves the board's left
    edge, loops up through the deck and climbs INSIDE the hollow lightning
    bolt (its width runs front to back, so it only ever bends over its flat
    side, with each zig of the bolt; waypoints hug the knee's two inside
    corners) to a cradle on the bolt's top flange, where the LED grid
    faces along the cloud. The bolt is one extruded zigzag outline (two
    strokes leaning right and a knee jog) with its own inset channel, an
    impact-star foot plate screwed into the deck (4 x M2.5 into insert
    pockets under the deck) and a flange screwed up into the cloud's floor
    (4 x M2.5 into insert bosses). The cloud is 13 overlapping spheres
    fused into one body, cut flat underneath, hollowed by the same spheres
    shrunk by WALL (an exact offset: the wall is never thinner than WALL) -
    a frosted diffuser that glows all over. Every dome on the floor reaches
    below it and every bump's centre sits deep in the dome under it, so the
    creases meet at wide angles (a shallow crease left a 0.2 mm sliver).
    The cloud sits mostly BEHIND the bolt (36 mm in front, 104 behind) to
    leave the mic grille open sky. The base is ONE revolved section (rolled
    deck edge, straight side, chamfered step into a recessed plinth), split
    into the fixed Base and the Shell; four M2.5 screws from below into
    insert bosses.
  * STAGE B - details: the mic seal ring and grille ring, the key ring and
    legends, the frosted bolt window, the base lettering, the rubber ring
    foot.
DETAILS (visible, 26): 1 puffy cumulus of 13 overlapping domes (a body,
two shoulders, two bumps and a crown); 2 low end puffs; 3 front puffs over
the bolt and back puffs that give it depth; 4 wide-angle creases between
the domes; 5 flat underside; 6 frosted diffuser shell that glows all over;
7 yellow lightning-bolt stand, two leaning strokes and a knee jog; 8 its
rounded corners; 9 its pillowed front and back rims; 10 an eight-point
impact star where the bolt strikes the base; 11 four countersunk screws in
the star; 12 the bolt's top flange under the cloud with four screws;
13 graphite puck base; 14 rolled deck edge; 15 chamfered step into a
recessed black plinth (the base floats); 16 microphone pin-hole grille
(3.6 % of the mic's face open); 17 a raised ring round the grille; 18 mode
key cap; 19 raised ring round the key; 20 "MODE" legend; 21 frosted mini
bolt window over the status light; 22 "ATECH" debossed on the deck;
23 USB-C pocket with a liner in the back; 24 rubber ring foot; 25 "ATECH
CL-1" under the base; 26 four countersunk screws from below.
Inside: the light's ribbon hidden in the bolt's channel, a light cradle
(two cheeks) on the flange, the mic seal ring, board standoffs and edge
fences, a rib onto the board's spine, insert bosses.
Materials: frosted cloud, toy-yellow bolt and star, graphite shell, black
plinth floor, frosted bolt window, graphite key, rubber ring, chrome screws.
MEASURED (R990, 2026-11-16): ./check CHECK PASS, run_seconds 14 s, wall 26-39 s; every RESTYLE end CHECK PASS.
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
    "Shell", "Bolt", "Cloud", "Mode_Key", "Bolt_Window", "Rubber_Ring",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4", "Screw_5", "Screw_6", "Screw_7",
    "Screw_8", "Screw_9", "Screw_10", "Screw_11", "Screw_12"],
    # the key cap presses the mode button (a declared cover, see ./check)
    "covers": {"Mode_Key": "button_p6"}}
REVIEW_CLOSEUPS = ["Cloud", "Bolt", "Mode_Key"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and cutter in
# the stages is derived from them (the cloud's domes, the bolt's zigzag
# and its channel, the ribbon's waypoints, the cradle, the base section,
# the screws' circle).
CLOUD_W = 240.0    # RESTYLE 204..276 width: the cloud end to end (every dome scales with it)
BOLT_H = 100.0     # RESTYLE 85..115 height: the bolt, deck to the cloud's underside
BOLT_W = 70.0      # RESTYLE 59..81 width: the bolt's zigzag across
BASE_R = 90.0      # RESTYLE 76..104 radius: the puck base (76: 6.5 mm round the board)
WALL = 2.0         # RESTYLE 1.7..2.3 wall: the cloud's diffuser wall
# end RESTYLE
# every outline below is driven from these numbers - a fork changes the
# silhouette here, never in the stages.
FOOT0 = 2.0                # base underside (the rubber ring keeps it off the desk)
FLOOR_T = 2.5              # base floor
L = 14.0                   # PCB top
DECK = 29.0                # deck top (the mic tops out at L + 10.84)
DECK_T = 2.5               # deck and side wall
R_ROLL = 6.0               # rolled deck edge
PL_Z, PL_IN = 8.0, 5.0     # plinth step height, how far it is set in
SPLIT = 6.5                # base / shell seam, inside the plinth ring
BOLT_D = 22.0              # bolt depth (front to back): the 14 mm ribbon + 2 x (2 + wall)
BOLT_T = 2.2               # bolt wall
FL_T = 4.0                 # the bolt's top flange (under the cloud) thickness
STAR = (21.0, 30.0, 3.0)   # impact star inner / outer radius, thickness
FOOT_X = -2.0              # the bolt foot's centre (x): the ribbon climbs here
LIGHT_UP = 45.0            # the cloud light's centre above the cloud's underside
CLOUD_FT = 2.5             # cloud floor
SCREW = "M2.5"
# the cloud: (x, y, z above the underside, r) at CLOUD_W 246, about the
# bolt's top (the flange). Every dome on the floor reaches below it (cut
# flat: no undercut crevice), the bumps on top have their centres deep in
# the dome under them, so every crease meets at a wide angle (R990: a
# shallow crease between two domes left a 0.2 mm sliver). The cloud
# reaches only ~36 mm in front of the bolt (the deck's mic grille in front
# of it must see the sky) and ~104 mm behind it.
DOMES = [(0, 30, 40, 66), (-62, 30, 22, 48), (64, 28, 26, 48),       # the body and its shoulders
         (-100, 30, 8, 22), (102, 28, 10, 22),                       # low end puffs
         (-35, 30, 70, 36), (38, 26, 64, 38), (5, 34, 92, 30),       # the bumps on top, the crown
         (-30, 0, 28, 34), (34, 2, 28, 34), (0, -4, 14, 30),         # front puffs (the bolt's)
         (-30, 70, 34, 34), (34, 66, 38, 34)]                        # back puffs
# the bolt outline (x, z) on a 62 x 100 design grid: top edge, left knee,
# knee jog, foot, right knee, back up to the top (two strokes leaning
# right, a knee jog between them)
BOLT_PTS = [(26, 100), (8, 42), (40, 42), (14, 0), (34, 0), (70, 58), (37, 58), (50, 100)]
COLOURS = {"Base": "matte_black", "Shell": "graphite", "Bolt": "toy_yellow", "Cloud": "frosted",
           "Mode_Key": "graphite", "Bolt_Window": "frosted", "Rubber_Ring": "rubber",
           "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
FLAT = Rotation(Vector(1, 0, 0), 90)
board = ap.board_object(doc)
board.Placement = Placement(Vector(0, 0, L), FLAT)     # x 0..60, y -120..0
BB = ap.bbox(board)
CX, CY = (BB.XMin + BB.XMax) / 2, (BB.YMin + BB.YMax) / 2   # the base's axis
mic = ap.seat(doc, "microphone", (13, 14))            # front right: in front of the cloud
key = ap.seat(doc, "button", 6)                        # front left
usb = ap.seat(doc, "usbc", 7)                          # back, mouth +Y
status = ap.seat(doc, "light", 5)                      # under the frosted mini bolt
PCB0 = L - 2.5
CLOUD_Z = DECK + BOLT_H                                # the cloud's flat underside

# the bolt, in world x / z (its mid-plane at port 3's row, y = YB)
YB = -49.95
SX = BOLT_W / 62.0
SZ = (CLOUD_Z - FL_T + 0.5 - DECK) / 100.0
BX0 = FOOT_X - SX * 24.0


def bolt_xz(p):
    return (BX0 + SX * p[0], DECK + SZ * p[1])


BOLT = [bolt_xz(p) for p in BOLT_PTS]
XT = (BOLT[0][0] + BOLT[7][0]) / 2                     # the top edge's middle


def offset_poly(pts, t):
    """The polygon pts (x, z) moved IN by t (mitred corners)."""
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    s = 1.0 if area > 0 else -1.0                       # inward = left of a CCW edge
    lines = []
    for i in range(n):
        (x0, z0), (x1, z1) = pts[i], pts[(i + 1) % n]
        dx, dz = x1 - x0, z1 - z0
        ln = math.hypot(dx, dz)
        nx, nz = -dz / ln * s, dx / ln * s
        lines.append(((x0 + nx * t, z0 + nz * t), (dx, dz)))
    out = []
    for i in range(n):
        (p, d), (q, e) = lines[i - 1], lines[i]
        den = d[0] * e[1] - d[1] * e[0]
        k = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
        out.append((p[0] + d[0] * k, p[1] + d[1] * k))
    return out


def prism_xz(pts, y0, y1):
    w = Part.makePolygon([V(x, y0, z) for x, z in pts] + [V(pts[0][0], y0, pts[0][1])])
    return Part.Face(w).extrude(V(0, y1 - y0, 0))


INNER = offset_poly(BOLT, BOLT_T)


def at_z(edge_a, edge_b, z):
    """x on the segment edge_a-edge_b at height z."""
    (x0, z0), (x1, z1) = edge_a, edge_b
    return x0 + (x1 - x0) * (z - z0) / (z1 - z0)


# the ribbon's path: up the lower stroke hugging its left side, across the
# knee, up the upper stroke into the cradle (all from the inset outline)
zr = lambda f: DECK + SZ * f                            # noqa: E731
lo_l = lambda z: at_z(INNER[3], INNER[2], z)            # noqa: E731  lower stroke, left
lo_r = lambda z: at_z(INNER[4], INNER[5], z)            # noqa: E731  lower stroke, right
up_l = lambda z: at_z(INNER[1], INNER[0], z)            # noqa: E731  upper stroke, left
up_r = lambda z: at_z(INNER[6], INNER[7], z)            # noqa: E731  upper stroke, right
LIGHT_C = (XT, YB, CLOUD_Z + LIGHT_UP)
VIA = [(FOOT_X - 6.0, YB, DECK - 7.0),
       ((lo_l(zr(8)) + lo_r(zr(8))) / 2, YB, zr(8)),
       ((lo_l(zr(30)) + lo_r(zr(30))) / 2, YB, zr(30)),
       (INNER[2][0] + 3.5, YB, INNER[2][1] - 1.0),          # round the knee's two
       ((INNER[2][0] + INNER[6][0]) / 2, YB, (INNER[2][1] + INNER[6][1]) / 2),   # inside corners
       (INNER[6][0] - 3.5, YB, INNER[6][1] + 1.0),
       ((up_l(zr(84)) + up_r(zr(84))) / 2, YB, zr(84)),
       (XT, YB, CLOUD_Z + 2.0)]
light, light_rib = ap.cable(doc, "light", 3, ap.module_placement(
    "light", LIGHT_C, face="+X", cable="-Z"), via=VIA, smooth=True)
tick("hardware")


def centre(m):
    b = ap.bbox(m)
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def annulus(r0, r1, z0, z1, c=None):
    c = c or (CX, CY)
    return cad.cut(cyl(r1, (c[0], c[1], z0), z1 - z0), cyl(r0, (c[0], c[1], z0 - 1), z1 - z0 + 2))


def arc(c, r, a0, a1):
    """('arc', mid, end) of the circle (c, r) from angle a0 to a1 (deg)."""
    am, a1 = math.radians((a0 + a1) / 2), math.radians(a1)
    return ("arc", (c[0] + r * math.cos(am), c[1] + r * math.sin(am)),
            (c[0] + r * math.cos(a1), c[1] + r * math.sin(a1)))


# ---- the base: one closed (radius, height) section, both skins in it
R_PL = BASE_R - PL_IN
section = [
    (0, DECK), (BASE_R - R_ROLL, DECK), arc((BASE_R - R_ROLL, DECK - R_ROLL), R_ROLL, 90, 0),
    (BASE_R, PL_Z + 1.5), (BASE_R - 1.5, PL_Z), (R_PL, PL_Z),                 # side, chamfered step
    (R_PL, FOOT0 + 1.5), arc((R_PL - 1.5, FOOT0 + 1.5), 1.5, 0, -90), (0, FOOT0),
    (0, FOOT0 + FLOOR_T), (R_PL - DECK_T, FOOT0 + FLOOR_T),                   # floor, plinth inside
    (R_PL - DECK_T, PL_Z + 1.0), (BASE_R - DECK_T, PL_Z + 1.0),
    (BASE_R - DECK_T, DECK - R_ROLL), arc((BASE_R - R_ROLL, DECK - R_ROLL), R_ROLL - DECK_T, 0, 90),
    (0, DECK - DECK_T),
]
body = cad.revolve_profile(section, at=(CX, CY, 0))
base, shell = cad.split(body, "Z", at=SPLIT, lip=1.2)
tick("base body")

# the fixed base holds the board: standoffs under it (0.1 mm below), fences
# 0.3 mm off its long edges below the slide paths, clear of port 3's ribbon
FL1 = FOOT0 + FLOOR_T
holders = [box(x - 3, x + 3, y - 3, y + 3, FL1 - 0.5, PCB0 - 0.1)
           for x in (BB.XMin + 12, BB.XMax - 12) for y in (BB.YMax - 12, BB.YMin + 12)]
holders += [box(x0, x1, y - 4, y + 4, FL1 - 0.5, L - 1.0)
            for x0, x1, ys in ((BB.XMin - 1.8, BB.XMin - 0.3, (-20, -100)),
                               (BB.XMax + 0.3, BB.XMax + 1.8, (-30, -110))) for y in ys]
base = cad.fuse_one(base, *holders)
# board hold-down: a rib from the deck onto the board's spine (0.2 mm off)
shell = cad.fuse_one(shell, box(CX - 1, CX + 1, CY - 22, CY + 22, L + 4.5 + 0.2, DECK - DECK_T + 0.5))
# four M2.5 up through the floor into columns hanging from the deck, each
# with a heat-set insert pocket (1.4 d + 0.1) and the thread-forming pilot
INSERT_D = {"M2": 3.2, "M2.5": 3.6, "M3": 4.3}[SCREW]
PILOT_D = {"M2": 1.7, "M2.5": 2.1, "M3": 2.5}[SCREW]
D_SCREW = float(SCREW[1:])
SCREW_R = BASE_R - 16.0
screws, cols, bores, csks = [], [], [], []
for a in (45, 135, 225, 315):
    x, y = CX + SCREW_R * math.cos(math.radians(a)), CY + SCREW_R * math.sin(math.radians(a))
    cols.append(cyl(INSERT_D / 2 + 1.2, (x, y, FL1 + 0.1), (DECK - DECK_T + 0.5) - (FL1 + 0.1)))
    bores.append(cyl(INSERT_D / 2, (x, y, FL1), 9.0))
    bores.append(cyl(PILOT_D / 2, (x, y, FL1 + 8.0), 2.5 * D_SCREW + 2.0))
    csks.append(Part.makeCone(5.6 / 2, 2.9 / 2, (5.6 - 2.9) / 2, V(x, y, FOOT0 - 0.01), V(0, 0, 1)))
    csks.append(cyl(2.9 / 2, (x, y, FOOT0 - 0.5), FLOOR_T + 1.0))
    screws.append(cad.screw("csk_phillips", SCREW, 10, at=(x, y, FOOT0), axis="+Z"))
shell = cad.cut(cad.fuse_one(shell, *cols), bores)
base = cad.cut(base, csks)
tick("base + screws")

# ---- the lightning bolt: the outline extruded front to back, its inset
# channel open at both ends (the ribbon runs through it)
YB0, YB1 = YB - BOLT_D / 2, YB + BOLT_D / 2
bolt = prism_xz(BOLT, YB0, YB1)
# round the CONVEX corners only (a concave fillet reads as a clip channel)
n_b = len(BOLT)
convex = []
for i in range(n_b):
    (ax, az), (bx_, bz), (cx_, cz) = BOLT[i - 1], BOLT[i], BOLT[(i + 1) % n_b]
    cr = (bx_ - ax) * (cz - bz) - (bz - az) * (cx_ - bx_)
    convex.append(cr)
sgn = 1.0 if sum(BOLT[i][0] * BOLT[(i + 1) % n_b][1] - BOLT[(i + 1) % n_b][0] * BOLT[i][1]
                 for i in range(n_b)) > 0 else -1.0
CONVEX = [BOLT[i] for i in range(n_b) if convex[i] * sgn > 0]
bolt = cad.soften(bolt, 2.0, [e for e in bolt.Edges
                              if abs(e.BoundBox.YMax - e.BoundBox.YMin) > BOLT_D - 0.1
                              and any(abs(e.BoundBox.XMin - x) < 0.01 and abs(e.BoundBox.ZMin - z) < 0.01
                                      for x, z in CONVEX)])
# and the front and back faces' rims (a pillowed bolt, not a cut-out)
bolt = cad.soften(bolt, 1.5, [e for e in bolt.Edges
                              if abs(e.BoundBox.YMax - e.BoundBox.YMin) < 0.01
                              and (abs(e.BoundBox.YMin - YB0) < 0.01 or abs(e.BoundBox.YMin - YB1) < 0.01)])
tick("bolt outline")
# the top flange (under the cloud) and the impact star (on the deck)
# the flange's four screws clear the bolt's top edge (x) and the cradle (y)
F_SCREWS = [(XT - 12 * SX - 5.5, YB), (XT + 12 * SX + 5.5, YB), (XT, YB - 19.0), (XT, YB + 19.0)]
FHX, FHY = 12 * SX + 11.5, 25.0
flange = cad.rounded_box(2 * FHX, 2 * FHY, FL_T, 10, at=(XT - FHX, YB - FHY, CLOUD_Z - FL_T))
star_pts = []
for i in range(16):
    r = STAR[1] if i % 2 == 0 else STAR[0]
    a = math.radians(90 + 22.5 * i)
    star_pts.append(V(FOOT_X + r * math.cos(a), YB + r * math.sin(a), DECK))
star = Part.Face(Part.makePolygon(star_pts + [star_pts[0]])).extrude(V(0, 0, STAR[2]))
# the light cradle: two cheeks 0.2 mm off the light's sides (its face, +X,
# and its ribbon, -Z, clear), standing on the flange
lb = ap.bbox(light)
cheeks = [box(lb.XMin + 1.0, lb.XMax - 1.0, y0, y1, CLOUD_Z - 0.5, lb.ZMax - 3.0)
          for y0, y1 in ((lb.YMin - 2.0, lb.YMin - 0.2), (lb.YMax + 0.2, lb.YMax + 2.0))]
bolt = cad.fuse_one(bolt, flange, star, *cheeks)
channel = prism_xz(INNER, YB0 + BOLT_T, YB1 - BOLT_T)
# the channel's ends: through the star (and the deck under it) and out of
# the flange's top into the cloud
ch_lo = box(min(p[0] for p in INNER) - 5, max(p[0] for p in INNER) + 5, YB0 + BOLT_T, YB1 - BOLT_T,
            DECK - 5, DECK + STAR[2] + 0.5).common(prism_xz(
                [(lo_l(DECK - 10), DECK - 10), (lo_r(DECK - 10), DECK - 10),
                 (lo_r(DECK + 6), DECK + 6), (lo_l(DECK + 6), DECK + 6)], YB0 + BOLT_T, YB1 - BOLT_T))
ch_hi = box(up_l(CLOUD_Z - 6), up_r(CLOUD_Z - 6) + 0.0, YB0 + BOLT_T, YB1 - BOLT_T, CLOUD_Z - 6,
            CLOUD_Z + 0.5)
bolt = cad.cut(bolt, [channel, ch_lo, ch_hi])
shell = cad.cut(shell, ch_lo)
# four M2.5 down through the star into columns under the deck (insert
# pockets), four up through the flange into bosses on the cloud's floor
for dx in (-11.0, 11.0):
    for dy in (-15.0, 15.0):
        x, y = FOOT_X + dx, YB + dy
        top = DECK + STAR[2]
        bolt = cad.cut(bolt, [Part.makeCone(5.6 / 2, 2.9 / 2, (5.6 - 2.9) / 2, V(x, y, top + 0.01),
                                            V(0, 0, -1)), cyl(2.9 / 2, (x, y, DECK - 0.5), STAR[2] + 1.0)])
        shell = cad.fuse_one(shell, cyl(INSERT_D / 2 + 1.2, (x, y, DECK - 9.0), 7.0))
        shell = cad.cut(shell, [cyl(INSERT_D / 2, (x, y, DECK - 4.5), 4.6),
                                cyl(PILOT_D / 2, (x, y, DECK - 8.0), 4.0)])
        screws.append(cad.screw("csk_phillips", SCREW, 8, at=(x, y, top), axis="-Z"))
tick("bolt")

# ---- the cloud: domes fused, cut flat, hollowed by the same domes shrunk
S = CLOUD_W / 246.0
CXC, CYC = XT, YB                                      # the domes are placed about the flange
domes = [(CXC + S * x, CYC + S * y, CLOUD_Z + S * z, S * r) for x, y, z, r in DOMES]
outer = cad.fuse_one(*[Part.makeSphere(r, V(x, y, z)) for x, y, z, r in domes])
outer = cad.cut(outer, box(CXC - 400, CXC + 400, CYC - 400, CYC + 400, CLOUD_Z - 300, CLOUD_Z))
core = cad.fuse_one(*[Part.makeSphere(r - WALL, V(x, y, z)) for x, y, z, r in domes])
core = cad.cut(core, box(CXC - 400, CXC + 400, CYC - 400, CYC + 400, CLOUD_Z - 300, CLOUD_Z + CLOUD_FT))
cloud = cad.cut(outer, core)
tick("cloud")
# the cradle comes up through a hole in the floor; four bosses round it
hole = cad.rounded_box(lb.XMax - lb.XMin + 4.0, lb.YMax - lb.YMin + 8.0, CLOUD_FT + 2.0, 3.0,
                       at=(lb.XMin - 2.0, lb.YMin - 4.0, CLOUD_Z - 1.0))
fcols, fbores = [], []
for x, y in F_SCREWS:
    fcols.append(cyl(INSERT_D / 2 + 1.2, (x, y, CLOUD_Z + CLOUD_FT - 0.5), 7.0))
    fbores.append(cyl(INSERT_D / 2, (x, y, CLOUD_Z - 0.01), 5.0))
    fbores.append(cyl(PILOT_D / 2, (x, y, CLOUD_Z + 4.5), 4.0))
    bolt = cad.cut(bolt, [Part.makeCone(5.6 / 2, 2.9 / 2, (5.6 - 2.9) / 2,
                                        V(x, y, CLOUD_Z - FL_T - 0.01), V(0, 0, 1)),
                          cyl(2.9 / 2, (x, y, CLOUD_Z - FL_T - 0.5), FL_T + 1.0)])
    screws.append(cad.screw("csk_phillips", SCREW, 10, at=(x, y, CLOUD_Z - FL_T), axis="+Z"))
cloud = cad.cut(cad.fuse_one(cloud, *fcols), [hole] + fbores)
tick("cloud fixings")

# ---- the deck's working faces: mic grille, mode key, USB-C pocket
mx, my = centre(mic)
mtop = ap.bbox(mic).ZMax
shell = cad.speaker_grille(shell, (mx, my, DECK), (0, 0, 1), 15, ring_pitch=2.5, hole=1.6)
kx, ky = centre(key)
kz = ap.bbox(key).ZMax
key_z = DECK - DECK_T - 0.9
cap = cad.button_cap(11.5, (DECK + 1.6) - key_z, dome=0.6, flange=1.5, at=(kx, ky, key_z), axis="+Z")
shell = cad.opening_for(shell, cap, clearance=0.25, chamfer=0.4, axis="+Z")
cap = cad.fuse_one(cap, cyl(3.0, (kx, ky, kz + 0.16), key_z - (kz + 0.16) + 0.5))
ub = ap.bbox(usb)
uz = L + 5.9
pocket = cad.rounded_box(18, BASE_R, 10, 3, at=(CX - 9, ub.YMax + 1.3, uz - 5), edges="y")
liner = cad.cut(cad.rounded_box(22, BASE_R, 14, 4, at=(CX - 11, ub.YMax + 0.25, uz - 7), edges="y")
                .common(cyl(BASE_R - DECK_T + 1.0, (CX, CY, 0), DECK)), pocket)
shell = cad.fuse_one(cad.cut(shell, pocket), liner)
shell = cad.socket_opening(shell, usb, margin=1.5)
tick("stage A")


# === STAGE B: details ===
# the mic seal ring from the deck onto the mic (0.3 mm off its face)
shell = cad.fuse_one(shell, annulus(8.4, 9.6, mtop + 0.3, DECK - DECK_T + 0.5, (mx, my)),
                     annulus(9.0, 10.6, DECK - 0.5, DECK + 0.6, (mx, my)))     # a raised ring round the grille
# a raised ring round the key, its legend, the wordmark
shell = cad.fuse_one(shell, annulus(6.6, 8.0, DECK - 0.5, DECK + 0.5, (kx, ky)))
shell = cad.text(shell, "MODE", (kx, ky - 12.5, DECK), (0, 0, 1), 3.5, depth=0.4, mode="deboss",
                 up=(0, 1, 0))
shell = cad.text(shell, "ATECH", (CX, CY - BASE_R + 17, DECK), (0, 0, 1), 5, depth=0.4,
                 mode="deboss", up=(0, 1, 0))
# the status light glows through a small frosted bolt window
sx, sy = centre(status)
mini = [(sx + 0.25 * (p[0] - 39), sy + 0.18 * (p[1] - 50)) for p in BOLT_PTS]
mini_w = Part.makePolygon([V(x, y, DECK) for x, y in mini] + [V(mini[0][0], mini[0][1], DECK)])
shell, window = cad.inlay(shell, mini_w, flange=1.0)
# lettering under the base, the rubber ring foot in a groove
base = cad.text(base, "ATECH CL-1", (CX, CY + 30, FOOT0), (0, 0, -1), 6, depth=0.4, mode="deboss",
                up=(0, -1, 0))
RUB = (R_PL - 6.0, R_PL - 3.0)
base = cad.cut(base, annulus(RUB[0], RUB[1], FOOT0 - 0.1, FOOT0 + 1.0))
rubber = annulus(RUB[0] + 0.1, RUB[1] - 0.1, 0.0, FOOT0 + 1.0)
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    return o


o = part("Base", base)
o.ViewObject.ShapeColor = cad.color(COLOURS["Base"])
o = part("Shell", shell)
o.ViewObject.ShapeColor = cad.color(COLOURS["Shell"])
o = part("Bolt", bolt)
o.ViewObject.ShapeColor = cad.color(COLOURS["Bolt"])
o = part("Cloud", cloud)
o.ViewObject.ShapeColor = cad.color(COLOURS["Cloud"])
o.ViewObject.Transparency = cad.transparency(COLOURS["Cloud"])
o = part("Mode_Key", cap)
o.ViewObject.ShapeColor = cad.color(COLOURS["Mode_Key"])
o = part("Bolt_Window", window)
o.ViewObject.ShapeColor = cad.color(COLOURS["Bolt_Window"])
o.ViewObject.Transparency = cad.transparency(COLOURS["Bolt_Window"])
o = part("Rubber_Ring", rubber)
o.ViewObject.ShapeColor = cad.color(COLOURS["Rubber_Ring"])
for i, sh in enumerate(screws):
    o = part("Screw_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Screw"])
print("SIZE %s" % (cad.measure(Part.makeCompound([base, shell, bolt, cloud, rubber]))["size"],))
print("SIZE model build %.1f s" % (time.time() - T0))
