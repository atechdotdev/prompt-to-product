"""Example: "a sourdough jar lid that tracks how much your starter rises" - a smart lid that measures the rise from above.

fork this file for a jar lid (a smart lid, a fermentation or kombucha
monitor, a canister or crock lid with sensors looking into the jar); change PARAMETERS and the outlines.
ARCHETYPE: jar lid

How it is built (R990):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board FLAT and turned ACROSS (long side left to right, modules up) in
    a 146 x 102 pod over the jar's mouth, ports 9-14 along the front: the
    screen (10, 11) under a smoked window in a cream bezel (rise % and
    peak time), the FEED key (13, a key cap: press it when you feed the
    starter), the PEAK light (9) under a frosted dot, USB-C (7) in a
    pocket with a liner in the right end. Both sensors face DOWN, CABLED
    from the back row round the board's back edge onto the floor under
    the board: the ToF distance sensor (3) on the jar's axis side over a
    stepped glass window in the floor (it reads the height of the
    starter's surface); the temp/humidity sensor (6) out at the left end
    against the end wall, in a walled chamber over a round-hole vent in
    the underside of the overhang, OUTSIDE the jar: it samples the
    kitchen's air (a starter's pace follows the room's temperature; the
    jar's headspace sits near 100 % RH anyway). The pod is a rounded plan
    extruded, hollowed with its own core and split low into the fixed
    Lid_Base (floor, the bayonet skirt that grips the jar's neck, board
    posts and end fences, the sensor cradle) and the Lid_Top; four M2.5
    screws from below into heat-set insert columns hanging from the deck;
    ribs from the deck onto the board's spine. The jar: ONE revolved
    section with both glass skins (rolled base, body, shoulder, neck,
    rim), three bayonet lugs on its neck; the skirt's three lugs bear up
    under them (a quarter turn locks the lid, pulling the food-safe
    silicone gasket down onto the rim).
  * STAGE B - details: the grip flutes round the skirt, the neck's bead,
    graduation ticks moulded on the glass, the rise-marker band, the
    lettering moulded in the glass, the starter itself, the gasket's
    breather notch, the parting-line reveal, legends, the model mark.
DETAILS (visible, 25 of 34): 1 rounded wooden pod 146 x 102 with 26 mm
corners; 2 rolled top edge (r 8); 3 small round on the bottom edge; 4 sage
lid base under it (the room-air vent in the left overhang's underside); 5 parting-line reveal between wood and sage; 6 cream
bezel plaque round the screen; 7 smoked screen window; 8 sage FEED key
cap; 9 "FEED" legend; 10 frosted PEAK dot; 11 "PEAK" legend; 12 "RISE"
legend over the window; 13 USB-C pocket with liner in the right end;
14 sage bayonet skirt round the neck; 15 40 grip flutes round the skirt;
16 clear glass jar with a rolled base; 17 its round shoulder (the inside
concentric) and neck; 18 the neck's bead under the skirt; 19 moulded
graduation ticks every 10 mm (long every 20); 20 "STARTER" moulded in the
glass; 21 the terracotta rise-marker band with its pointer tab; 22 the
cream starter with a domed top; 23 "ATECH" on the base's front; 24 "ATECH
SJ-1" under the pod; 25 four countersunk screws under the overhangs.
Inside: 26 the stepped glass ToF window in the floor; 27 the round-hole
humidity vent (room air); 28 the humidity chamber walls (the end wall and ribs; ribs
either side of the ToF); 29 the silicone gasket on the rim; 30 its breather
notch (the starter's CO2 escapes between the lugs); 31 three bayonet lugs
on the neck and three in the skirt; 32 board posts and end fences; 33
ribs onto the spine; 34 insert columns with M2.5 heat-set pockets, and
the key's plunger.
Materials: oak top, sage-green base and skirt and key, cream bezel,
smoked window, frosted dot, clear glass jar and ToF window, cream
starter, terracotta silicone band, white food-safe silicone gasket,
brass screws.
Screws: ONE type, 4 x M2.5 x 10 countersunk + 4 M2.5 heat-set inserts.
MEASURED (R990, 2026-11-17): ./check CHECK PASS, run_seconds 18.3 s, wall 40 s (a busy machine); every RESTYLE end CHECK PASS.
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
    "Lid_Top", "Bezel", "Screen_Window", "Peak_Dot", "Key", "Screw_1", "Screw_2", "Screw_3", "Screw_4"],
    # the key presses its button through its opening (a declared cover)
    "covers": {"Key": "button_p13"}}
REVIEW_CLOSEUPS = ["Bezel", "Lid_Base", "Glass_Jar"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them and the measured hardware.
JAR_H = 140.0      # RESTYLE 119..161 height: the jar, desk to rim
JAR_R = 52.0       # RESTYLE 44..60 radius: the jar's body
CORNER = 26.0      # RESTYLE 22..30 radius: the pod's plan corners
SKIRT_H = 14.0     # RESTYLE 11.5..16.5 height: the bayonet skirt below the rim
WALL = 2.5         # RESTYLE 2.1..2.9 wall
SIDE = 13.0        # RESTYLE 11..15 length: the pod past the board's ends (x; 146 long at 13)
# end RESTYLE
DEPTH = 102.0      # the pod front to back (y)
EDGE_R, FOOT_R = 8.0, 1.5
AIR = 1.2          # the deck's inner face over the tallest module (usbc 10.21)
GASKET_T = 1.5     # the silicone gasket between the rim and the pod's floor
GLASS = 3.0        # the jar's wall
RN, RNI = 43.0, 39.5   # the neck: outside (the lugs stand on it) and the mouth
SK_RI = 45.6       # the skirt's bore (0.6 mm round the jar's lugs)
LUG_T, LUG_W = 3.5, 30.0   # bayonet lug height and width (deg)
WIN_D = 14.0       # the ToF window in the floor
WINDOW, BEZEL, RECESS = (36.0, 16.0), 5.0, 1.0
KEY_D, DOT_D = 13.0, 7.0
SCREW = "M2.5"
START = 0.42       # the starter's level (share of the jar height) at feeding
COLOURS = {"Lid_Top": "#94704f", "Lid_Base": "#8da58a", "Bezel": "cream", "Screen_Window": "smoked",
           "Peak_Dot": "frosted", "Key": "#8da58a", "Sensor_Window": "glass", "Gasket": "#ece9e0",
           "Glass_Jar": "#a9d2d9", "Starter": "#efe0bd", "Marker_Band": "#c4523b", "Screw": "brass"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
FLAT = Rotation(Vector(1, 0, 0), 90)
ACROSS = Rotation(Vector(0, 0, 1), -90).multiply(FLAT)    # long side along X, ports 9-14 at the front (-Y)
ZR = JAR_H                                 # the jar's rim
ZF0 = ZR + GASKET_T                        # the pod's underside (on the gasket)
ZF1 = ZF0 + WALL                           # the floor's top
FACE = ZF1 + 0.5                           # the sensors' faces, looking down
Z_PCB = FACE + 9.54 + 0.6 + 2.5            # the PCB top: the sensors lie under the board
board = ap.board_object(doc)
board.Placement = Placement(V(), ACROSS)
_b = ap.bbox(board)
board.Placement = Placement(V(-(_b.XMin + _b.XMax) / 2, -(_b.YMin + _b.YMax) / 2, Z_PCB - 2.5 - _b.ZMin), ACROSS)
BB = ap.bbox(board)
scr = ap.seat(doc, "screen", (10, 11))        # front, right of centre (12 is reserved in the SDK)
key = ap.seat(doc, "button", 13)              # front left: FEED
led = ap.seat(doc, "light", 9)                # front right: PEAK
usb = ap.seat(doc, "usbc", 7)                 # right end, mouth +X
# the sensors: cabled from the back row round the back edge, face down
# on the floor under the board (the ribbons loop 8 mm past the edge)
SZ = Z_PCB - 2.5 - 0.6 - 9.54 / 2
SY = BB.YMax - 18.25                          # the socket run (14.5) ends past the board edge
tof, tof_rib = ap.cable(doc, "distance_sensor", 3, ap.module_placement(
    "distance_sensor", (11.25, SY, SZ), face="-Z", cable="+Y"), via=[(11.25, BB.YMax + 8.0, Z_PCB - 5.0)])
# the temp / humidity sensor samples the KITCHEN's air (a starter's pace
# follows the room's temperature; the jar's headspace sits near 100 % RH):
# out at the left end, its outer side 0.3 mm off the end wall, over a
# vent in the underside of the overhang, outside the jar
HX = -(BB.XMax + SIDE - WALL - 0.3 - 9.75)
th, th_rib = ap.cable(doc, "temp_humidity", 6, ap.module_placement(
    "temp_humidity", (HX, SY, SZ), face="-Z", cable="+Y"), via=[(HX + 4.0, BB.YMax + 7.0, Z_PCB - 4.0)], smooth=True)
tick("hardware")

SB, KB, LB, UB, TB, HB = [ap.bbox(o) for o in (scr, key, led, usb, tof, th)]
for nm, b in (("board", BB), ("screen", SB), ("key", KB), ("light", LB), ("usb", UB), ("tof", TB), ("th", HB)):
    print("BOX %-7s x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (nm, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))
for r in tof_rib + th_rib:
    rb = r.Shape.BoundBox
    print("RIBBON %s y %.1f..%.1f z %.1f..%.1f" % (r.Label, rb.YMin, rb.YMax, rb.ZMin, rb.ZMax))


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def annulus(r0, r1, z0, z1):
    return cad.cut(cyl(r1, (0, 0, z0), z1 - z0), cyl(r0, (0, 0, z0 - 1), z1 - z0 + 2))


def centre(b):
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


def zbox(w, d, r, cx, cy, z0, z1):
    return cad.rounded_box(w, d, z1 - z0, r, at=(cx - w / 2, cy - d / 2, z0))


def sector(r0, r1, a_mid, half, z0, z1, n=6):
    """An annular sector (straight facets) from z0 to z1, centred on the axis."""
    pts = [V(r1 * math.cos(math.radians(a_mid - half + 2 * half * i / n)),
             r1 * math.sin(math.radians(a_mid - half + 2 * half * i / n)), z0) for i in range(n + 1)]
    pts += [V(r0 * math.cos(math.radians(a_mid + half - 2 * half * i / n)),
              r0 * math.sin(math.radians(a_mid + half - 2 * half * i / n)), z0) for i in range(n + 1)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, z1 - z0))


def insert(shell, cutter):
    """(shell with the opening, the piece that fills it exactly)."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, piece


def arc(c, r, a0, a1):
    """('arc', mid, end) of the circle (c, r) from angle a0 to a1 (deg)."""
    am, a1 = math.radians((a0 + a1) / 2), math.radians(a1)
    return ("arc", (c[0] + r * math.cos(am), c[1] + r * math.sin(am)),
            (c[0] + r * math.cos(a1), c[1] + r * math.sin(a1)))


X1 = BB.XMax + SIDE
WIDTH = 2 * X1
Z_TOP = max(b.ZMax for b in (SB, KB, LB, UB)) + AIR + WALL
print("POD %.0f x %.0f, underside z %.2f, deck z %.2f" % (WIDTH, DEPTH, ZF0, Z_TOP))


# ------------------------------------------------------------ the pod
def slab(t):
    w = cad.rounded_rect_wire(WIDTH - 2 * t, DEPTH - 2 * t, max(CORNER - t, 0.6), (0, 0, ZF0 + t), "Z")
    return Part.Face(w).extrude(V(0, 0, Z_TOP - ZF0 - 2 * t))


def rolled(t):
    """slab(0) with its top edges rolled EDGE_R and its foot rounded; the
    core slab(t) CHAMFERED under the roll (EDGE_R - t): the deck's edge keeps
    the full wall, and no concave round inside reads as a clip channel."""
    s = slab(t)
    top_edges = [e for e in s.Edges if e.BoundBox.ZMin > Z_TOP - t - 1e-3]
    if t > 0:
        return cad.chamfer_safe(s, max(EDGE_R - t, 0.6), top_edges)
    s = cad.soften(s, EDGE_R, top_edges)
    return cad.soften(s, FOOT_R, [e for e in s.Edges if e.BoundBox.ZMax < ZF0 + 1e-3])


outer = rolled(0.0)
body = cad.hollow(outer, WALL, core=rolled)
skin = slab(0.5)
tick("pod")
SPLIT = Z_PCB - 2.5                          # its lip stays 0.3 mm over the humidity sensor at the end wall
base, top = cad.split(body, "Z", at=SPLIT, lip=1.2)
tick("split")

# the floor: the ToF looks through a stepped glass window (it cannot fall
# out downward), the humidity sensor breathes through a round-hole vent
tx, ty, _tz = centre(TB)
hx, hy, _hz = centre(HB)
base, win = insert(base, cad.fuse_one(cyl(WIN_D / 2, (tx, ty, ZF0 - 1), WALL + 2),
                                      cyl(WIN_D / 2 + 2.0, (tx, ty, ZF1 - 1.0), 2.0)))
# the vent: only where the floor is past the jar (and its marker band),
# so it opens to the room at every JAR_R
VX0, VX1 = HB.XMin + 0.8, min(HB.XMax - 0.8, -(JAR_R + 3.0))
base = cad.grille(base, ((VX0 + VX1) / 2, hy, ZF0), (0, 0, -1), (VX1 - VX0, 16), kind="round", hole=1.8,
                  pitch=3.0, margin=0.5)

# the bayonet skirt round the neck, three lugs inside it that bear up
# under the jar's lugs (a quarter turn locks it)
SK_RO = SK_RI + WALL
Z_SK = ZR - SKIRT_H
LUG_Z = Z_SK + 1.0                            # the skirt lugs' underside
LUG_ANG = (90.0, 210.0, 330.0)
skirt = annulus(SK_RI, SK_RO, Z_SK, ZF0 + 0.5)
skirt = cad.fuse_one(skirt, *[sector(RN + 0.6, SK_RI + 0.5, a, LUG_W / 2, LUG_Z, LUG_Z + LUG_T) for a in LUG_ANG])
base = cad.fuse_one(base, skirt)
# the fixed base holds the board: posts 0.1 mm under it (clear of the
# sensors and their ribbons), fences off its ends below the PCB top
UNDER = BB.ZMin - 0.1
posts = [box(x - 3, x + 3, y - 3, y + 3, ZF1 - 0.5, UNDER) for x, y in ((-45.0, -18.0), (45.0, -18.0), (45.0, 18.0),
                                                                          (-38.0, 18.0))]
posts += [box(x - 3, x + 3, -21.0, -15.0, ZF1 - 0.5, UNDER) for x in (-22.0, 22.0)]
fences = [box(x0, x0 + 1.5, y0, y0 + 5, ZF1 - 0.5, Z_PCB - 0.8)
          for x0, y0 in ((BB.XMin - 1.8, -15.0), (BB.XMax + 0.3, -15.0), (BB.XMax + 0.3, 10.0))]
# the sensor cradle: ribs 0.25 mm off both sensors' sides (the end wall
# is the humidity sensor's outer one), a front wall closing its chamber
RIB_Z1 = FACE + 6.0
cradle = [box(TB.XMax + 0.25, TB.XMax + 1.75, TB.YMin + 1, TB.YMax - 1, ZF1 - 0.5, RIB_Z1),
          box(TB.XMin - 1.75, TB.XMin - 0.25, TB.YMin + 1, TB.YMax - 1, ZF1 - 0.5, RIB_Z1),
          box(HB.XMax + 0.25, HB.XMax + 1.75, HB.YMin + 1, HB.YMax - 1, ZF1 - 0.5, RIB_Z1),
          box(HB.XMin - 0.5, HB.XMax + 1.75, HB.YMin - 1.75, HB.YMin - 0.25, ZF1 - 0.5, RIB_Z1)]
base = cad.fuse_one(base, *[p.common(skin) for p in posts + fences] + cradle)
# board retention: ribs from the deck down onto the spine (0.2 mm off it)
SPINE_Z = BB.ZMax
top = cad.fuse_one(top, *[box(x - 2, x + 2, -6, 6, SPINE_Z + 0.2, Z_TOP - WALL + 0.5) for x in (-10.0, 30.0)])
tick("base")

# four M2.5 screws from below, under the overhangs past the jar: columns
# hang from the deck with a heat-set insert pocket at their foot
INSERT_D = {"M2": 3.2, "M2.5": 3.6, "M3": 4.3}[SCREW]
PILOT_D = {"M2": 1.7, "M2.5": 2.1, "M3": 2.5}[SCREW]
CSK = {"M2": (3.8, 2.4), "M2.5": (5.6, 2.9), "M3": (6.4, 3.4)}[SCREW]
SX = max(BB.XMax + 3.4, X1 - WALL - 4.5)      # past the board's end, 0.5 mm clear of the base's lip
# front pair under the overhangs, back pair in the strip behind the board
# (the humidity sensor and its ribbon have the left end's back corner)
SCREWS = [(-SX, -20.0), (SX, -20.0), (-38.0, DEPTH / 2 - WALL - 6.5), (38.0, DEPTH / 2 - WALL - 6.5)]
cols, bores, csks, screws = [], [], [], []
for x, y in SCREWS:
    cols.append(cyl(INSERT_D / 2 + 1.2, (x, y, ZF1 + 0.1), (Z_TOP - WALL + 0.5) - (ZF1 + 0.1)))
    bores.append(cyl(INSERT_D / 2, (x, y, ZF1), 7.0))
    bores.append(cyl(PILOT_D / 2, (x, y, ZF1 + 6.5), 5.0))
    csks.append(Part.makeCone(CSK[0] / 2, CSK[1] / 2, (CSK[0] - CSK[1]) / 2, V(x, y, ZF0 - 0.01), V(0, 0, 1)))
    csks.append(cyl(CSK[1] / 2, (x, y, ZF0 - 0.5), WALL + 1.0))
    screws.append(cad.screw("csk_phillips", SCREW, 10, at=(x, y, ZF0), axis="+Z"))
top = cad.cut(cad.fuse_one(top, *cols), bores)
base = cad.cut(base, csks)
tick("screws")

# ------------------------------------------------------------ the top's controls
base_z = Z_TOP - WALL - 0.9
kx, ky, _kz = centre(KB)
cap = cad.button_cap(KEY_D, (Z_TOP + 1.6) - base_z, dome=0.5, flange=0.8, at=(kx, ky, base_z), axis="+Z")
top = cad.opening_for(top, cap, clearance=0.25, chamfer=0.4, axis="+Z")
keycap = cad.fuse_one(cap, cyl(3.0, (kx, ky, KB.ZMax + 0.16), base_z - (KB.ZMax + 0.16) + 0.5))
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
tick("controls")

# ------------------------------------------------------------ the jar
# ONE revolved section with both glass skins: a rolled base, the body,
# the shoulder, the neck and a rounded rim
R, T = JAR_R, GLASS
Z_NECK = Z_SK - 5.0                           # where the neck rises from the shoulder
Z_SH = Z_NECK - min(18.0, max(4.0, (R - RN) * 1.6))   # the body's top
FLOOR_J = 6.0
# the shoulder: an arc tangent to the body, the inside CONCENTRIC with it
# (the glass keeps its thickness round the curve)
SH_D, SH_H = R - RN, Z_NECK - Z_SH
RHO = (SH_D ** 2 + SH_H ** 2) / (2 * SH_D)
SC = (R - RHO, Z_SH)                          # the shoulder arc's centre
TH_O = math.degrees(math.atan2(SH_H, RN - SC[0]))
ci = (RNI - SC[0]) / (RHO - T)
TH_I = math.degrees(math.acos(ci)) if -1 < ci < 1 else 90.0
Z_IN = Z_SH + (RHO - T) * math.sin(math.radians(TH_I))
inner_top = [(RNI, Z_IN)] + ([(SC[0], Z_IN)] if TH_I == 90.0 else [])
jar_sec = [
    (0, 0), (R - 6.0, 0), arc((R - 6.0, 6.0), 6.0, -90, 0),            # rolled base
    (R, Z_SH), arc(SC, RHO, 0, TH_O),                                    # body, shoulder
    (RN, ZR - 1.0), arc((RN - 1.0, ZR - 1.0), 1.0, 0, 90),               # neck, rim
    (RNI + 1.0, ZR), arc((RNI + 1.0, ZR - 1.0), 1.0, 90, 180),
] + inner_top + [                                                         # inside: neck, shoulder
    arc(SC, RHO - T, TH_I, 0),
    (R - T, FLOOR_J + 4.0), arc((R - T - 4.0, FLOOR_J + 4.0), 4.0, 0, -90), (0, FLOOR_J),
]
jar = cad.revolve_profile(jar_sec)
# three bayonet lugs on the neck: their undersides rest on the skirt's lugs
JLUG = LUG_Z + LUG_T
jar = cad.fuse_one(jar, *[sector(RN - 0.5, SK_RI - 0.6, a, LUG_W / 2, JLUG, JLUG + LUG_T) for a in LUG_ANG])
# the silicone gasket under the floor, inside the skirt, on the rim
gasket = annulus(RNI - 1.0, SK_RI - 0.1, ZR, ZF0)
# a breather notch across its underside: a rising starter's CO2 escapes
# past the rim and out between the lugs instead of pressing on the lid
notch = box(RNI - 2.0, SK_RI + 1.0, -1.5, 1.5, ZR - 1.0, ZR + 0.6)
notch.rotate(V(0, 0, 0), V(0, 0, 1), 30.0)
gasket = cad.cut(gasket, notch)
tick("stage A")


# === STAGE B: details ===
# grip flutes round the skirt (one cut)
flutes = []
for i in range(40):
    f = box(SK_RO - 0.8, SK_RO + 2.0, -0.7, 0.7, Z_SK + 1.5, ZF0 - 1.0)
    f.rotate(V(0, 0, 0), V(0, 0, 1), 360.0 * i / 40 + 4.5)
    flutes.append(f)
base = cad.cut(base, flutes)
# the neck's bead under the skirt, moulded graduation ticks on the glass
# (front left, toward the viewer), a long tick every 20 mm
Z_START = START * ZR
bead = annulus(RN - 0.5, RN + 2.0, Z_NECK + 1.0, Z_NECK + 2.5)
ticks = []
zt, i = FLOOR_J + 14.0, 0
while zt < Z_SH - 4.0:
    half = 9.0 if i % 2 == 0 else 4.5
    if not Z_START - 8.5 < zt < Z_START + 1.0:          # none under the marker band
        ticks.append(sector(R - 0.5, R + 0.6, -138.0, half, zt, zt + 1.0, n=4))
    zt, i = zt + 10.0, i + 1
jar = cad.fuse_one(jar, bead, *ticks)
# moulded lettering on the glass's front, over the band
ga = math.radians(-100.0)
jar = cad.text(jar, "STARTER", (R * math.cos(ga), R * math.sin(ga), (Z_START + Z_SH) / 2 + 4.0),
               (math.cos(ga), math.sin(ga), 0), 7.0, depth=0.6, mode="emboss")
# the rise marker: a silicone band stretched round the glass at the
# starter's level at feeding, a pointer tab up at the front
mz0 = Z_START - 7.0
band = annulus(R, R + 2.0, mz0, Z_START)
tab = Part.Face(Part.makePolygon([V(R - 0.5, -6.0, Z_START - 1.0), V(R - 0.5, 6.0, Z_START - 1.0),
                                  V(R - 0.5, 0.0, Z_START + 7.0), V(R - 0.5, -6.0, Z_START - 1.0)])).extrude(V(2.5, 0, 0))
tab.rotate(V(0, 0, 0), V(0, 0, 1), -100.0)
band = cad.fuse_one(band, tab.cut(cyl(R, (0, 0, mz0 - 1), 20)))
# the starter: the jar's inner skin up to its level, a dome on top
SR = R - T
starter = cad.revolve_profile([(0, FLOOR_J), (SR - 4.0, FLOOR_J), arc((SR - 4.0, FLOOR_J + 4.0), 4.0, -90, 0),
                               (SR, Z_START), arc((0, Z_START - 200.0), math.hypot(SR, 200.0), math.degrees(math.atan2(200.0, SR)), 90)])
# the parting-line reveal, legends, the model mark under the pod
top = cad.groove_ring(top, "Z", SPLIT + 2.2, w=0.8, depth=0.6)
top = cad.text(top, "FEED", (kx, KB.YMin - 2.7, Z_TOP), (0, 0, 1), 3.5, depth=0.4, mode="deboss", up=(0, 1, 0))
top = cad.text(top, "PEAK", (lx, KB.YMin - 2.7, Z_TOP), (0, 0, 1), 3.5, depth=0.4, mode="deboss", up=(0, 1, 0))
top = cad.text(top, "RISE", (sx, sy + WINDOW[1] / 2 + BEZEL + 4.0, Z_TOP), (0, 0, 1), 4.0, depth=0.4, mode="deboss",
               up=(0, 1, 0))
base = cad.text(base, "ATECH", (0.0, -DEPTH / 2, (ZF0 + SPLIT) / 2), (0, -1, 0), 4.0, depth=0.4, mode="deboss")
base = cad.text(base, "ATECH SJ-1", ((X1 + SK_RO) / 2, 0.0, ZF0), (0, 0, -1), 3.5, depth=0.4, mode="deboss",
                up=(1, 0, 0))
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    return o


o = part("Lid_Base", base)
o.ViewObject.ShapeColor = cad.color(COLOURS["Lid_Base"])
o = part("Lid_Top", top)
o.ViewObject.ShapeColor = cad.color(COLOURS["Lid_Top"])
o = part("Bezel", bezel)
o.ViewObject.ShapeColor = cad.color(COLOURS["Bezel"])
o = part("Screen_Window", window)
o.ViewObject.ShapeColor = cad.color(COLOURS["Screen_Window"])
o.ViewObject.Transparency = cad.transparency("smoked")
o = part("Peak_Dot", dot)
o.ViewObject.ShapeColor = cad.color(COLOURS["Peak_Dot"])
o.ViewObject.Transparency = cad.transparency("frosted")
o = part("Key", keycap)
o.ViewObject.ShapeColor = cad.color(COLOURS["Key"])
o = part("Sensor_Window", win)
o.ViewObject.ShapeColor = cad.color(COLOURS["Sensor_Window"])
o.ViewObject.Transparency = cad.transparency("glass")
o = part("Gasket", gasket)
o.ViewObject.ShapeColor = cad.color(COLOURS["Gasket"])
o = part("Glass_Jar", jar)
o.ViewObject.ShapeColor = cad.color(COLOURS["Glass_Jar"])
o.ViewObject.Transparency = cad.transparency("glass")
o = part("Starter", starter)
o.ViewObject.ShapeColor = cad.color(COLOURS["Starter"])
o.ViewObject.Transparency = cad.transparency("frosted")
o = part("Marker_Band", band)
o.ViewObject.ShapeColor = cad.color(COLOURS["Marker_Band"])
for i, sh in enumerate(screws):
    o = part("Screw_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Screw"])
print("SIZE", cad.measure(Part.makeCompound([base, top, jar, band]))["size"])
print("TOTAL %.1f s" % (time.time() - T0))
