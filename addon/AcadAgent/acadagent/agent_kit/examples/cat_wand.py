"""Example: "a cat toy that waves a feather wand when the cat walks by" - a cat-eared turret on a low pebble that swings a feather wand when its PIR eye sees the cat.

fork this file for a cat toy / pet teaser / interactive wand toy (a feather
teaser, a laser-free cat entertainer, a motion-triggered pet toy - a geared
turret on a low round base); change PARAMETERS and the outlines.
ARCHETYPE: cat toy

How it is built (R990):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board FLAT on the floor of a low round pebble, port 7 at the back
    (USB-C SEATED there, its mouth facing the back wall: a pocket and a
    liner bring the wall to 0.25 mm off it). The board is centred on the
    base's y and sits 6 mm left of the head's axis, so the dc_motor (N20)
    CABLED from port 13 stands upright beside it, shaft up, exactly one
    gear centre distance (44.05 mm, measured off the shaft) from the axis.
    Unlike a turntable the whole drive is INSIDE the base: a 12 tooth
    pinion (cad.spur_gear, module 1) on the shaft meshes a 76 tooth drive
    gear hanging under a closed deck, ratio 6.33 : 1 - no gear a paw can
    reach. The head is ONE part with a round spigot (the pin: 0.1 mm clear
    in a bearing sleeve through the deck) and a hex end; the drive gear is
    pressed onto the hex from below (a declared intended overlap) and stops
    the head lifting off, the head's hub rests on the sleeve's thrust ring
    (intent "motion": the head swings -90 .. 90 deg, swept clear). The PIR
    (14) and the pause key (6) are CABLED to a flat arched facet at the
    front, each between ribs and a back stop: the PIR looks out through an
    OPEN window in a black eye bezel (infrared does not pass plastic). The
    motor hangs in a frame of ribs from the deck, under the gears. The base
    is ONE revolved (radius, z) outline (a recessed plinth, a chamfered
    step, a drum with a reveal groove, a quarter-round shoulder rolling
    onto the flat deck) hollowed by the same outline WALL in; the facet is
    cut flat through both skins; split low into the fixed Base (standoffs
    and fences under the board) and the Shell (deck, sleeve, motor frame,
    key and PIR ribs); four M2.5 screws from below into insert sleeves on
    columns that carry the deck.
  * STAGE B - details: cat ears with pink inner ears, eyes and a nose
    inlaid in the dome, whisker grooves, a red collar with a brass bell,
    the wand socket on the head with the wand stub and its feather tuft,
    paw prints raised on the shoulder, the PIR window's flare, a raised
    ring round the key with a pause mark, the rubber foot ring, lettering.
RESTYLE (R425): R_HEAD, HEAD_H, EAR_H, WAND_L and WALL drive every outline
and cutter below (the dome's sphere, the ears, eyes, nose, whiskers,
collar, bell and the wand socket follow the head; the wand's path and the
tuft follow WAND_L; the base and head skins and every opening follow
WALL). The board, the motor and the gear centre distance are the
hardware's own: never move them with a knob.
DETAILS (visible, 32): 1 revolved pebble base; 2 recessed dark plinth (it
floats); 3 chamfered step over it; 4 reveal groove round the drum;
5 quarter-round shoulder onto the deck; 6 flat arched front facet;
7 black PIR eye bezel, proud of the facet; 8 its OPEN flared window;
9 coral pause key with a flange; 10 its debossed pause mark; 11 raised
ring round the key; 12 "ATECH" on the facet; 13-16 four raised paw
prints round the shoulder; 17 the domed cream head over a 0.6 mm shadow
gap; 18-19 two cat ears tilted out; 20-21 pink inner ears inlaid;
22-23 black eyes inlaid; 24 pink nose inlaid; 25 six whisker grooves;
26 red collar inlaid round the skirt; 27 brass bell with its slot and
band, pegged into the collar; 28 the wand socket boss on the back left
of the head; 29 the navy wand stub arching over; 30 the ferrule and bead
at its tip; 31 seven fanned feathers; 32 the flat deck ring round the
head. Underneath: the rubber foot ring in a groove, four countersunk
screws, USB-C pocket with a liner at the back.
Inside: the 12 tooth pinion on the motor shaft; the 76 tooth drive gear
pressed on the head's hex end, six lightening holes; the bearing sleeve
and thrust ring; the motor frame hung from the deck; ribs and back stops
round the key and the PIR; standoffs and fences; insert sleeves on
columns; the lip keying the shell to the base.
Materials: sage shell, matte black plinth, cream head, pink inner ears
and nose, black eyes and PIR bezel, red collar, brass bell, coral key,
navy wand, pink feathers, orange gears, rubber foot ring, chrome screws.
MEASURED (R990, 2026-11-17): ./check CHECK PASS, run_seconds 22 s, wall 66 s; every RESTYLE end CHECK PASS.
"""
import math
import time
import Part
import atech_ports as ap
import atech_cad as cad
from FreeCAD import Vector, Placement, Rotation, Matrix
V = Vector
T0 = time.time()

INTENT = {"board": "flat", "fitted_after": [
    "Shell", "Head", "Drive_Gear", "Pinion", "Key_Pause", "PIR_Bezel", "Ear_Inner_L", "Ear_Inner_R",
    "Eye_L", "Eye_R", "Nose", "Collar", "Bell", "Wand", "Feather_Tuft", "Rubber_Ring",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4"],
    "covers": {"Key_Pause": "button_6"},
    "motion": [{"part": "Head", "axis": [[0, 0, 0], [0, 0, 1]], "range_deg": [-90, 90]}]}
# the drive gear is pressed onto the head's hex spigot; the inlays ride in
# the head and the wand sits in its socket - they all turn with the head
INTENDED_OVERLAPS = [("Head", "Drive_Gear"), ("Head", "Ear_Inner_L"), ("Head", "Ear_Inner_R"),
                     ("Head", "Eye_L"), ("Head", "Eye_R"), ("Head", "Nose"), ("Head", "Wand")]
REVIEW_CLOSEUPS = ["Head", "PIR_Bezel", "Drive_Gear", "Feather_Tuft"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them; each knob at its min and its
# max gives CHECK PASS.
R_HEAD = 44.0          # RESTYLE 37..51 radius: the head's skirt (the dome, ears, face and socket follow it)
HEAD_H = 40.0          # RESTYLE 34..46 height: the head, skirt bottom to crown
EAR_H = 20.0           # RESTYLE 17..23 height: the cat ears above the dome
WAND_L = 100.0         # RESTYLE 85..115 length: the wand stub out of its socket
WALL = 2.5             # RESTYLE 2.1..2.9 wall
# end RESTYLE
# Frame: the head's axis on z, the front (the PIR) at -Y, the desk at z = 0.
R_BASE = 88.0          # the pebble's radius (176 mm across): the board corners sit at r 70
R_DECK = 52.0          # the flat deck the head turns on: covers the pinion (r 51)
FACET_W = 80.0         # the flat front facet across (x) at its foot
FACET = math.sqrt(R_BASE ** 2 - (FACET_W / 2) ** 2)   # the facet's distance from the axis
FOOT = 1.5             # the rubber foot ring under the base
FLOOR = FOOT + 3.0     # the floor's top (the foot ring's groove leaves 1.6)
SPLIT = FLOOR + 0.5    # base / shell seam, under every slide path (USB from z 8.5)
PLINTH = 5.0           # the plinth's recess (radius) and the step up over it
L = 6.0                # board underside (PCB top L + 2.5)
AXIS_OFF = (5.9, 22.0)  # the head's axis from the board's right-back reference (see the board below)
MOTOR_Z0 = 17.0        # the motor's lowest point: its socket and ribbon clear the floor
M, Z_PIN, Z_GEAR = 1.0, 12, 76          # gear module and teeth
BACKLASH = 0.1         # off each tooth (FDM)
CD = M * (Z_PIN + Z_GEAR) / 2.0 + 0.05  # centre distance + 0.05 backlash
GEAR_T = 5.5           # face width of both gears
SPIGOT_R = 3.8         # the head's round spigot through the sleeve (bore 0.1 mm clear): the pin
HEX_R = 3.7            # its hex end in the drive gear (circumradius: it passes the bore)
SKIRT = 12.0           # the head's straight skirt under the dome
HEAD_WALL = WALL + 0.9 # the head's skin (the inlays sink 1.2 mm into it)
INLAY = 1.2            # depth of the eyes, nose and inner ears (>= 1 mm: they key into the head)
WAND_R = 3.0           # the wand rod (a 6 mm fibreglass rod)
SOCKET_PHI = 40.0      # the socket's polar angle on the dome, from the crown
WAND_AZ = 120.0        # ...and its azimuth: back left (90 = straight back, +Y)
WAND_BEND = 80.0       # how far the wand arches over from the socket's axis to its tip (deg)
PIR_DEPTH = 14.2       # the PIR module's height over its pins (MEASURED: its dome tip)
SCREWS = [(-60.0, -30.0), (-60.0, 30.0), (56.0, 34.0), (60.0, -4.0)]   # columns clear of the board, motor and ribbons
SCREW = "M2.5"
RUBBER = (R_BASE - PLINTH - 12.0, R_BASE - PLINTH - 6.5, FOOT)   # the foot ring's radii and its height under the base
COLOURS = {"Base": "matte_black", "Shell": "#8DB9A6", "Head": "#F4E6CC", "Drive_Gear": "orange",
           "Pinion": "orange", "Ear_Inner": "#F2A0B4", "Eye": "matte_black", "Nose": "#E9798F",
           "Key_Pause": "coral", "PIR_Bezel": "matte_black", "Wand": "#2F3656",
           "Feather_Tuft": "#FF5C9D", "Rubber_Ring": "rubber", "Screw": "chrome",
           "Collar": "#D9433B", "Bell": "brass"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
FLAT = Rotation(Vector(1, 0, 0), 90)
board = ap.board_object(doc)
board.Placement = Placement(Vector(), FLAT)
_b = ap.bbox(board)
# x -35.9..24.1, y -60..60: centred on y, the motor's port (13) 22 mm in front of the axis
board.Placement = Placement(Vector(-30.0 - _b.XMin - AXIS_OFF[0], 82.0 - _b.YMax - AXIS_OFF[1], L - _b.ZMin), FLAT)
BB = ap.bbox(board)
PT = L + 2.5                                           # the PCB top
usb = ap.seat(doc, "usbc", 7)                          # back centre, mouth +Y
# the motor: CABLED from port 13 (right column), upright beside the board,
# pins down / shaft up; the shaft one centre distance off the axis, 22 mm
# in front of it (the shaft sits 0.57 / 0.25 mm off the module's box centre)
SY_T = -AXIS_OFF[1]
SX_T = math.sqrt(CD ** 2 - SY_T ** 2)
SHAFT_OFF = (0.57, 0.25)                # the shaft off the module's box centre (MEASURED)
motor, motor_rib = ap.cable(doc, "dc_motor", 13, ap.module_placement(
    "dc_motor", (SX_T - SHAFT_OFF[0], SY_T - SHAFT_OFF[1], MOTOR_Z0 + 24.15), face="+X", cable="-Z"))
# the pause key (6) and the PIR (14): CABLED to the front facet, facing
# -Y, pins outboard (toward their own plug's side)
FY_OUT, FY_IN = -FACET, -(FACET - WALL)
MOD_Z = 28.0
KEY_X, PIR_X = BB.XMin + 10.0, BB.XMax - 10.0        # in front of their own ports' columns
key, key_rib = ap.cable(doc, "button", 6, ap.module_placement(
    "button", (KEY_X, FY_IN + 7.0, MOD_Z), face="-Y", cable="-X"))
pir, pir_rib = ap.cable(doc, "pir", 14, ap.module_placement(
    "pir", (PIR_X, FY_IN + 0.5 + PIR_DEPTH / 2, MOD_Z), face="-Y", cable="+X"))
MB = ap.bbox(motor)
# the shaft, measured: the mesh points in its top 6 mm
_sp = [p for p in motor.Mesh.Points if p.z > MB.ZMax - 6.0]
SX = (min(p.x for p in _sp) + max(p.x for p in _sp)) / 2.0
SY = (min(p.y for p in _sp) + max(p.y for p in _sp)) / 2.0
SHAFT_TIP = MB.ZMax
BODY_TOP = SHAFT_TIP - 8.8
print("SHAFT at (%.3f, %.3f), tip z %.2f; centre distance %.3f (m (z1 + z2) / 2 = %.2f)" % (
    SX, SY, SHAFT_TIP, math.hypot(SX, SY), M * (Z_PIN + Z_GEAR) / 2.0))
# the heights all follow the motor: the gears under a closed deck
G0 = BODY_TOP + 1.0                     # gears' underside
G1 = G0 + GEAR_T                        # drive gear top
SLEEVE_Z0 = G1 + 0.3                    # the bearing sleeve's foot, 0.3 mm over the gear
DECK_IN = max(SHAFT_TIP + 0.5, SLEEVE_Z0 + 1.5)   # deck underside: clear of the shaft tip
TOP = DECK_IN + WALL                    # deck top
THRUST = TOP + 1.0                      # the thrust ring's top: the head's hub rests on it
H0 = TOP + 0.6                          # the head's skirt bottom: a 0.6 mm shadow gap over the deck
HS = H0 + SKIRT                         # the skirt top / dome foot
HT = H0 + HEAD_H                        # the crown
_D = HT - HS
ZC = HS + (_D ** 2 - R_HEAD ** 2) / (2.0 * _D)   # the dome's sphere: centre on the axis
RHO = HT - ZC
RQ = R_BASE - R_DECK                    # the base's quarter-round shoulder
ZS = TOP - RQ                           # the drum's top / the shoulder's foot
tick("hardware")


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def annulus(r0, r1, z0, z1, c=(0, 0)):
    return cad.cut(cyl(r1, (c[0], c[1], z0), z1 - z0), cyl(r0, (c[0], c[1], z0 - 1), z1 - z0 + 2))


def ycyl(r, x, z, y0, y1):
    return Part.makeCylinder(r, abs(y1 - y0), V(x, min(y0, y1), z), V(0, 1, 0))


def hexagon(r, z0, z1):
    pts = [V(r * math.cos(math.radians(60 * k)), r * math.sin(math.radians(60 * k)), z0) for k in range(6)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, z1 - z0))


def centre(m):
    b = ap.bbox(m)
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


def insert(shell, cutter):
    """(shell with the opening, the piece that fills it exactly)."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1:
        piece, rest = shell.common(cutter, 0.01), shell.cut(cutter, 0.01)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, piece


def yprism(x0, x1, z0, z1, y0, y1, r):
    """A rounded-rectangle prism along Y; its corners are 3 straight facets
    each (an arc corner reads as an open clip channel, R7)."""
    pts = []
    for cx, cz, a0 in ((x1 - r, z0 + r, -90), (x1 - r, z1 - r, 0), (x0 + r, z1 - r, 90), (x0 + r, z0 + r, 180)):
        pts += [V(cx + r * math.cos(math.radians(a0 + 30 * i)), y0, cz + r * math.sin(math.radians(a0 + 30 * i)))
                for i in range(4)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, y1 - y0, 0))


def arc45(cr, cz, rad):
    """The 45 deg point of a quarter round centred (cr, cz)."""
    return (cr + rad * math.sqrt(0.5), cz + rad * math.sqrt(0.5))


def dome_pt(phi_deg, rad=None, az_deg=90.0):
    """A point on the head's sphere (radius rad), polar angle phi from the
    crown, azimuth az (90 = toward +Y, the back; -90 = the face)."""
    rad = RHO if rad is None else rad
    p, a = math.radians(phi_deg), math.radians(az_deg)
    return V(rad * math.sin(p) * math.cos(a), rad * math.sin(p) * math.sin(a), ZC + rad * math.cos(p))


# ------------------------------------------------------------ the base
# ONE revolved outline: a recessed plinth, a 45 deg step out over it, the
# drum with a reveal groove, a quarter-round shoulder onto the flat deck;
# the core is the same outline WALL in (concentric shoulder arcs)
R0, R1 = R_BASE - PLINTH, R_BASE
ZG = SPLIT + 0.5 + PLINTH + 0.45 * (ZS - SPLIT - 0.5 - PLINTH)   # the reveal groove, in the section
outer = cad.revolve_profile([(0, FOOT), (R0, FOOT), (R0, SPLIT + 0.5), (R1, SPLIT + 0.5 + PLINTH),
                             (R1, ZG - 0.5), (R1 - 0.7, ZG - 0.5), (R1 - 0.7, ZG + 0.5), (R1, ZG + 0.5),
                             (R1, ZS), ("arc", arc45(R_DECK, ZS, RQ), (R_DECK, TOP)), (0, TOP)])
k = WALL * (math.sqrt(2) - 1)           # a 45 deg line offset WALL meets a vertical one this far along
core = cad.revolve_profile([(0, FLOOR), (R0 - WALL, FLOOR), (R0 - WALL, SPLIT + 0.5 + WALL - k),
                            (R1 - WALL, SPLIT + 0.5 + PLINTH + WALL - k), (R1 - WALL, ZS),
                            ("arc", arc45(R_DECK, ZS, RQ - WALL), (R_DECK, DECK_IN)), (0, DECK_IN)])
# the flat front facet through both skins: an arch where it meets the shoulder
far = 3 * R_BASE
outer = cad.cut(outer, box(-far, far, -far, FY_OUT, -1, TOP + 1))
core = cad.cut(core, box(-far, far, -far, FY_IN, -1, TOP + 1))
shell = cad.cut(outer, core)
tick("base body")
base, shell = cad.split(shell, "Z", at=SPLIT, lip=1.2)
tick("split")

# the fixed base holds the board: standoffs 0.1 mm under it, fences 0.3 mm
# off its long edges (clear of the motor's ribbon at port 13)
holders = [box(x - 3, x + 3, y - 3, y + 3, FLOOR - 0.5, BB.ZMin - 0.1)
           for x in (BB.XMin + 12, BB.XMax - 12) for y in (BB.YMin + 14, BB.YMin + 68, BB.YMax - 14)]
holders += [box(BB.XMin - 1.8, BB.XMin - 0.3, BB.YMin + y - 5, BB.YMin + y + 5, FLOOR - 0.5, PT - 1.5)
            for y in (26.0, 78.0, 110.0)]
holders += [box(BB.XMax + 0.3, BB.XMax + 1.8, BB.YMin + y - 5, BB.YMin + y + 5, FLOOR - 0.5, PT - 1.5)
            for y in (78.0, 110.0)]
base = cad.fuse_one(base, *holders)

# the shell: the bearing sleeve through the deck, its bore 0.2 mm round the
# hex spigot, a thrust ring on top the head's hub rests on
shell = cad.fuse_one(shell, cyl(7.0, (0, 0, SLEEVE_Z0), THRUST - SLEEVE_Z0), cyl(9.0, (0, 0, TOP - 0.5), THRUST - TOP + 0.5))
shell = cad.cut(shell, cyl(SPIGOT_R + 0.1, (0, 0, SLEEVE_Z0 - 1), THRUST - SLEEVE_Z0 + 2))
# the motor's frame: a rib down from the deck on its outer side (outside the
# drive gear) and a ring of arms round the body under the gears
mcy = (MB.YMin + MB.YMax) / 2
RZ0 = MB.ZMax - 30.0
ARM_TOP = G0 - 0.6
ribs = [box(MB.XMax + 0.3, MB.XMax + 2.3, MB.YMin - 2.3, MB.YMax + 2.3, RZ0, DECK_IN + 0.5),
        box(MB.XMin - 2.3, MB.XMax + 2.3, MB.YMax + 0.3, MB.YMax + 2.3, RZ0, ARM_TOP),
        box(MB.XMin - 2.3, MB.XMax + 2.3, MB.YMin - 2.3, MB.YMin - 0.3, RZ0, ARM_TOP),
        box(MB.XMin - 2.3, MB.XMin - 0.3, MB.YMin - 2.3, MB.YMax + 2.3, RZ0, ARM_TOP)]
# the key and the PIR: ribs over and under each, from the front wall back,
# and a back stop behind (the key is pressed against it)
for m in (key, pir):
    b = ap.bbox(m)
    cx = (b.XMin + b.XMax) / 2
    ribs += [box(b.XMin + 2, b.XMax - 2, FY_IN - 0.5, b.YMax + 2.3, b.ZMax + 0.3, b.ZMax + 2.3),
             box(b.XMin + 2, b.XMax - 2, FY_IN - 0.5, b.YMax - 3.0, b.ZMin - 2.3, b.ZMin - 0.3),
             box(cx - 4, cx + 4, b.YMax + 0.3, b.YMax + 2.3, b.ZMin + 3.0, b.ZMax + 2.3)]
shell = cad.fuse_one(shell, *ribs)
tick("sleeve + ribs")

# four M2.5 up through the base into insert sleeves on columns up to the
# shoulder (they carry the deck too)
INSERT_D = {"M2": 3.2, "M2.5": 3.6, "M3": 4.3}[SCREW]
screws = []
for x, y in SCREWS:
    shell = cad.screw_boss(shell, (x, y, FLOOR + 0.1), axis="+Z", size=SCREW, ribs=0)
    base = cad.countersink(base, (x, y, FOOT), "+Z", 2.9, 5.6, 90.0)
    screws.append(cad.screw("csk_phillips", SCREW, 10, at=(x, y, FOOT), axis="+Z"))
shell = cad.fuse_one(shell, *[cyl(INSERT_D / 2 + 1.2, (x, y, FLOOR + 0.1), 10.0) for x, y in SCREWS])
shell = cad.cut(shell, [cyl(INSERT_D / 2, (x, y, FLOOR), 9.5) for x, y in SCREWS])
tick("screws")

# ------------------------------------------------------------ front openings
# the pause key: a cap through the facet, flange 0.1 mm behind it, a
# plunger to 0.16 mm off the module's own cap
kx, _ky, kz = centre(key)
k_face = ap.bbox(key).YMin
cap_base = FY_IN + 0.9
cap = cad.button_cap(13.0, cap_base - (FY_OUT - 1.6), dome=0.8, flange=1.5, at=(kx, cap_base, kz), axis="-Y")
shell = cad.opening_for(shell, cap, clearance=0.25, chamfer=0.4, axis="-Y")
cap = cad.fuse_one(cap, ycyl(3.0, kx, kz, cap_base - 0.5, k_face - 0.16))
# the PIR eye: a black bezel (an insert through the facet, proud of it)
# with an OPEN round window over the dome - infrared does not pass plastic
EYE_R, WINDOW_D = 9.8, 11.5     # the bezel clears the ribs over and under the PIR
ex, _ey, ez = centre(pir)
shell, bezel = insert(shell, ycyl(EYE_R, ex, ez, FY_OUT - 1.0, FY_IN + 1.0))
bezel = cad.fuse_one(bezel, ycyl(EYE_R, ex, ez, FY_OUT - 1.7, FY_OUT + 0.5))
bezel = cad.cut(bezel, ycyl(WINDOW_D / 2, ex, ez, FY_OUT - 3.0, FY_IN + 2.0))
# USB-C at the back: a pocket brings the wall to 0.25 mm off the mouth
ub = ap.bbox(usb)
ux, uz = (ub.XMin + ub.XMax) / 2, PT + 5.9
pocket = yprism(ux - 6.5, ux + 6.5, uz - 5.0, uz + 5.0, ub.YMax + 1.3, R_BASE + 5, 3)
liner = cad.cut(yprism(ux - 8.5, ux + 8.5, max(uz - 7.0, SPLIT + 1.6), uz + 7.0, ub.YMax + 0.25,
                       math.sqrt((R_BASE - WALL) ** 2 - (abs(ux) + 8.5) ** 2) + 1.0, 3.5), pocket)
shell = cad.fuse_one(cad.cut(shell, pocket), liner)
shell = cad.socket_opening(shell, usb, margin=1.5)
tick("openings")

# ------------------------------------------------------------ the drive
# the pinion on the shaft (bore 3.3 round the 3.0 shaft), the drive gear on
# the head's hex spigot; each phased so a tooth of one points into a space
pinion = cad.spur_gear(M, Z_PIN, GEAR_T - 0.3, bore=3.3, backlash=BACKLASH)
pinion.translate(V(SX, SY, G0))
pinion = cad.mesh_phase(pinion, (SX, SY, G0), "+Z", (-SX, -SY, 0), tooth=True)
gear = cad.spur_gear(M, Z_GEAR, GEAR_T, backlash=BACKLASH)
gear = cad.cut(gear, [cyl(6.0, (22.0 * math.cos(math.radians(a)), 22.0 * math.sin(math.radians(a)), -1), GEAR_T + 2)
                      for a in range(30, 360, 60)])
gear = cad.cut(gear, hexagon(HEX_R - 0.05, -1, GEAR_T + 1))     # pressed on: 0.05 mm interference
gear.translate(V(0, 0, G0))
gear = cad.mesh_phase(gear, (0, 0, G0), "+Z", (SX, SY, 0))

# the head: ONE revolved section with both skins - the straight skirt and
# a dome on a sphere centred on the axis; the hub down to the thrust ring
# and the hex spigot through the sleeve into the drive gear
RI = RHO - HEAD_WALL
ZI = ZC + math.sqrt(RI ** 2 - (R_HEAD - HEAD_WALL) ** 2)       # inner sphere meets the inner skirt
p_out = (RHO * math.sin(math.asin(R_HEAD / RHO) / 2), ZC + RHO * math.cos(math.asin(R_HEAD / RHO) / 2))
_ai = math.asin((R_HEAD - HEAD_WALL) / RI) / 2
p_in = (RI * math.sin(_ai), ZC + RI * math.cos(_ai))
head = cad.revolve_profile([(R_HEAD - HEAD_WALL, H0), (R_HEAD, H0), (R_HEAD, HS), ("arc", p_out, (0, HT)),
                            (0, HT - HEAD_WALL), ("arc", p_in, (R_HEAD - HEAD_WALL, ZI))])
head = cad.soften(head, 1.0, [e for e in head.Edges if e.BoundBox.ZMax < H0 + 0.01])
head = cad.fuse_one(head, cyl(7.5, (0, 0, THRUST), HT - HEAD_WALL + 0.5 - THRUST),
                    cyl(SPIGOT_R, (0, 0, G1 + 0.1), THRUST + 0.5 - G1 - 0.1), hexagon(HEX_R, G0, G1 + 0.6))
# the dome's solids for inlays and grooves: the outer sphere and one INLAY in
dome_out = Part.makeSphere(RHO, V(0, 0, ZC)).common(cyl(R_HEAD + 1, (0, 0, HS), HT - HS + 1))
dome_in = Part.makeSphere(RHO - INLAY, V(0, 0, ZC))
layer = dome_out.cut(dome_in)
tick("stage A")


# === STAGE B: details ===
# (a fork may stop after STAGE A, run ./check, then add these one by one)
# the cat ears: two fins on the dome, tilted out, cut by the dome's cavity
EAR_W, EAR_T = 0.62 * R_HEAD, 0.22 * R_HEAD
EAR_PHI = math.degrees(math.asin(0.5 * R_HEAD / RHO))   # the ear's root half way out
ears, inner_ears = [], []
for s in (-1, 1):
    root = dome_pt(EAR_PHI, az_deg=0.0 if s > 0 else 180.0)
    # a fin with a flat front face (top_at keeps it vertical), tapering back
    fin = cad.wedge(EAR_W, EAR_T, EAR_H + 7.0, top_x=0, top_y=EAR_T * 0.45,
                    at=(-EAR_W / 2, -EAR_T / 2, -7.0), top_at=(EAR_W / 2, 0.0))
    fin = cad.soften(fin, 1.6)
    fin.rotate(V(0, 0, 0), V(0, 1, 0), s * 16.0)
    fin.translate(V(root.x, 0, root.z))
    # the pink inner ear: a triangle inlaid INLAY deep into the ear's front
    tri = cad.wedge(EAR_W * 0.5, 4.0, (EAR_H + 7.0) * 0.55, top_x=0, at=(-EAR_W * 0.25, 0.0, 0.0))
    tri.translate(V(0, -EAR_T / 2 - 4.0 + INLAY, -4.0))
    tri.rotate(V(0, 0, 0), V(0, 1, 0), s * 16.0)
    tri.translate(V(root.x, 0, root.z))
    tri = tri.cut(dome_out)
    ears.append(fin)
    inner_ears.append(tri)
cavity = cad.revolve_profile([(0, H0 - 1), (R_HEAD - HEAD_WALL, H0 - 1), (R_HEAD - HEAD_WALL, ZI),
                              ("arc", p_in, (0, HT - HEAD_WALL))])
head = cad.fuse_one(head, *[cad.cut(e, cavity) for e in ears])
ear_l, ear_r = [None, None]
head, ear_l = insert(head, inner_ears[0])
head, ear_r = insert(head, inner_ears[1])
# the face on the front of the dome: eyes and a nose inlaid INLAY deep,
# three whisker grooves each side
EYE_PHI, EYE_AZ = 40.0, 22.0
eyes = []
for s in (-1, 1):
    p = dome_pt(EYE_PHI, az_deg=-90.0 + s * EYE_AZ)
    n = p - V(0, 0, ZC)                             # along the dome's normal there
    n.normalize()
    c = Part.makeCylinder(0.13 * R_HEAD, 10.0, p - n * 5.0, n)
    head, eye = insert(head, c.common(layer))
    eyes.append(eye)
pn = dome_pt(EYE_PHI + 12.0, az_deg=-90.0)
nn = pn - V(0, 0, ZC)
nn.normalize()
up = V(0, 0, 1) - nn * nn.z
up.normalize()
_q = [pn - nn * 5.0 + V(-4.2, 0, 0) + up * 2.4, pn - nn * 5.0 + V(4.2, 0, 0) + up * 2.4, pn - nn * 5.0 - up * 2.6]
nose_t = Part.Face(Part.makePolygon(_q + [_q[0]])).extrude(nn * 10.0)
head, nose = insert(head, nose_t.common(layer))
wh_layer = dome_out.cut(Part.makeSphere(RHO - 0.6, V(0, 0, ZC)))
whiskers = []
for s in (-1, 1):
    for dz, tilt in ((-2.0, 8.0), (-4.5, 0.0), (-7.0, -8.0)):
        w = box(0, 0.34 * R_HEAD, -R_HEAD - 10, 0, -0.45, 0.45)
        w.rotate(V(0, 0, 0), V(0, 1, 0), -tilt)
        w.translate(V(0.2 * R_HEAD, 0, pn.z + dz))
        if s < 0:
            w = w.mirror(V(0, 0, 0), V(1, 0, 0))
        whiskers.append(w.common(wh_layer))
head = cad.cut(head, whiskers, optional=True)
# a red collar round the skirt (an inlay 1.2 mm deep, 1.2 proud) and a
# brass bell on a peg in it, under the chin
CZ0, CZ1 = H0 + 0.38 * SKIRT, H0 + 0.88 * SKIRT
head = cad.cut(head, annulus(R_HEAD - INLAY, R_HEAD + 2.0, CZ0, CZ1))
collar = annulus(R_HEAD - INLAY, R_HEAD + 1.2, CZ0, CZ1)
collar = cad.soften(collar, 0.5, [e for e in collar.Edges if e.BoundBox.XMax > R_HEAD + 1.0])
BELL_R = 5.0
bc = V(0, -(R_HEAD + 1.2 + 0.2 + BELL_R), (CZ0 + CZ1) / 2)
collar = cad.cut(collar, Part.makeCylinder(1.1, 1.6, V(0, -(R_HEAD + 1.2), bc.z), V(0, 1, 0)))
bell = cad.fuse_one(Part.makeSphere(BELL_R, bc),
                    Part.makeCylinder(1.0, BELL_R + 0.2 + 1.4, bc, V(0, 1, 0)))
bell = cad.cut(bell, [box(-BELL_R - 1, BELL_R + 1, bc.y - 0.4, bc.y + 0.4, bc.z - BELL_R - 1, bc.z - 1.2),
                      annulus(BELL_R - 0.3, BELL_R + 1, bc.z + 0.6, bc.z + 1.1, (0, bc.y))], optional=True)
# the wand socket: a boss on the back of the dome along its normal, a
# blind bore 0.1 mm round the rod (it is pushed in: a pin in a bore)
sn = dome_pt(SOCKET_PHI, az_deg=WAND_AZ) - V(0, 0, ZC)
sn.normalize()
sp = dome_pt(SOCKET_PHI, az_deg=WAND_AZ)
SOCK_L = 0.36 * R_HEAD
head = cad.fuse_one(head, Part.makeCylinder(WAND_R + 3.5, SOCK_L + 2.0, sp - sn * 2.0, sn))
head = cad.cut(head, Part.makeCylinder(WAND_R + 0.1, SOCK_L + 1.0, sp + sn * 1.0, sn))
head = cad.soften(head, 0.8, [e for e in head.Edges if (e.BoundBox.Center - (sp + sn * SOCK_L)).Length < WAND_R + 4.0
                              and e.BoundBox.DiagonalLength > 12.0])
# the wand: a rod out of the socket that arches over as it rises (its end
# 0.2 mm off the bore's floor), the feather tuft on a ferrule at its tip
d = math.radians(SOCKET_PHI)
hz = V(math.cos(math.radians(WAND_AZ)), math.sin(math.radians(WAND_AZ)), 0)   # the wand's plane
p = sp + sn * (SOCK_L + 2.0 + 6.0)                  # straight through the socket and 6 mm out
pts = [sp + sn * (1.2 + WAND_R), sp + sn * (SOCK_L / 2 + 2.0), sp + sn * (SOCK_L + 1.0 + WAND_R), p]
N = 7
for i in range(1, N + 1):
    seg = (WAND_L - 3.0) / N
    a = d + math.radians(WAND_BEND) * (i / float(N)) ** 1.4
    p = p + hz * (math.sin(a) * seg) + V(0, 0, math.cos(a) * seg)
    pts.append(p)
td = pts[-1] - pts[-2]
td.normalize()
pts.append(pts[-1] + td * 6.0)                      # a straight end for the ferrule
# the rod's end in the socket is a true cylinder (a pin in the bore); the
# bent rest is a pipe starting inside it
ROD0 = sp + sn * 1.2
wand = cad.fuse_one(Part.makeCylinder(WAND_R, SOCK_L + 4.0, ROD0, sn),
                    cad.pipe([(q.x, q.y, q.z) for q in pts[2:]], r=WAND_R - 0.05))
tip = pts[-1]
td = pts[-1] - pts[-2]
td.normalize()
FER_L = 13.0                                       # the ferrule: tip - 8 .. tip + 5 along the rod
fer0 = tip - td * 8.0
tuft = Part.makeCylinder(WAND_R + 1.6, FER_L, fer0, td)
bead = tip + td * (WAND_R + 3.5)
tuft = cad.fuse_one(tuft, Part.makeSphere(WAND_R + 2.6, bead))
# the bore over the rod's end, 0.35 mm round it and 0.2 mm past its cap
tuft = cad.cut(tuft, Part.makeCylinder(WAND_R + 0.35, 8.0 + WAND_R + 1.2, fer0 - td * 1.0, td))
# the tuft hangs off the tip: its axis D the tip's direction turned 35 deg
# further down; five long feathers fanned 90 deg in the plane that faces
# the front-left (the 3/4 view), two short ones behind them
el = math.atan2(td.z, math.hypot(td.x, td.y)) - math.radians(35.0)
D = hz * math.cos(el) + V(0, 0, math.sin(el))
fw = V(-1.0, -1.0, 0.8).cross(D)
fw.normalize()
fn = D.cross(fw)
BASIS = Matrix(D.x, fw.x, fn.x, 0, D.y, fw.y, fn.y, 0, D.z, fw.z, fn.z, 0, 0, 0, 0, 1)
FAN = [(-45, 0.78, 0.0), (-22, 0.92, 0.0), (0, 1.0, 0.0), (22, 0.92, 0.0), (45, 0.78, 0.0),
       (-11, 0.62, -2.4), (11, 0.62, -2.4)]          # (fan angle, length share, offset behind)
feathers = []
for ang, ln, off in FAN:
    fl = 0.28 * WAND_L * ln
    f = Part.makeSphere(1.0).transformGeometry(Matrix(fl, 0, 0, 0, 0, 0.24 * fl, 0, 0, 0, 0, 1.8, 0, 0, 0, 0, 1))
    f.translate(V(fl - 1.5, 0, off))               # its root in the bead, clear of the bore
    f.rotate(V(0, 0, 0), V(0, 0, 1), ang)
    f.transformShape(BASIS)                        # a rigid turn: local x -> D
    f.translate(bead)
    feathers.append(f)
tuft = cad.fuse_one(tuft, *feathers)
tick("head + wand")

# paw prints raised 0.8 mm on the shoulder (sunk 0.4 to fuse), four round the sides
paw_layer = cad.revolve_profile([(R1 + 0.8, ZS), ("arc", arc45(R_DECK, ZS, RQ + 0.8), (R_DECK, TOP + 0.8)),
                                 (R_DECK, TOP - 0.4), ("arc", arc45(R_DECK, ZS, RQ - 0.4), (R1 - 0.4, ZS))])
PSI = 42.0                                         # the paw's place up the shoulder (deg)
pr, pz = R_DECK + RQ * math.cos(math.radians(PSI)), ZS + RQ * math.sin(math.radians(PSI))
nr, nz = math.cos(math.radians(PSI)), math.sin(math.radians(PSI))
paws = []
for az in (35.0, 145.0, 215.0, 325.0):
    a = math.radians(az)
    u = V(math.cos(a) * nr, math.sin(a) * nr, nz)             # the shoulder's normal there
    t = V(-math.sin(a), math.cos(a), 0)                       # along the shoulder
    b = u.cross(t)
    c = V(math.cos(a) * pr, math.sin(a) * pr, pz)
    pad = [(0.0, -2.0, 6.2)] + [(dx, 5.8 + dy, 2.6) for dx, dy in ((-6.6, -0.8), (-2.3, 1.8), (2.3, 1.8), (6.6, -0.8))]
    for dx, dy, r in pad:
        q = c + t * dx + b * dy
        paws.append(Part.makeCylinder(r, 10.0, q - u * 5.0, u).common(paw_layer))
shell = cad.fuse_one(shell, *paws)
# the PIR window's mouth flared (a wider field of view)
bezel = cad.cut(bezel, Part.makeCone(WINDOW_D / 2, WINDOW_D / 2 + 1.6, 1.25, V(ex, FY_OUT - 0.5, ez), V(0, -1, 0)))
# a raised ring round the key with a pause mark in the cap, lettering
shell = cad.fuse_one(shell, cad.cut(ycyl(9.8, kx, kz, FY_OUT - 0.6, FY_OUT + 0.5),
                                    ycyl(8.3, kx, kz, FY_OUT - 1.0, FY_OUT + 1.0)))
cap = cad.cut(cap, [box(kx + dx - 0.7, kx + dx + 0.7, FY_OUT - 3.0, FY_OUT - 1.1, kz - 2.8, kz + 2.8)
                    for dx in (-1.6, 1.6)], optional=True)
shell = cad.text(shell, "ATECH", ((KEY_X + PIR_X) / 2, FY_OUT, 13.0), (0, -1, 0), 5, depth=0.5, mode="deboss")
# the rubber foot ring in a groove under the base
base = cad.cut(base, annulus(RUBBER[0], RUBBER[1], FOOT - 0.1, FOOT + 1.4))
rubber = annulus(RUBBER[0] + 0.1, RUBBER[1] - 0.1, FOOT - RUBBER[2], FOOT + 1.3)
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape, colour):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = cad.color(COLOURS[colour])
    return o


part("Base", base, "Base")
part("Shell", shell, "Shell")
part("Head", head, "Head")
part("Drive_Gear", gear, "Drive_Gear")
part("Pinion", pinion, "Pinion")
part("Key_Pause", cap, "Key_Pause")
part("PIR_Bezel", bezel, "PIR_Bezel")
part("Ear_Inner_L", ear_l, "Ear_Inner")
part("Ear_Inner_R", ear_r, "Ear_Inner")
part("Eye_L", eyes[0], "Eye")
part("Eye_R", eyes[1], "Eye")
part("Nose", nose, "Nose")
part("Collar", collar, "Collar")
part("Bell", bell, "Bell")
part("Wand", wand, "Wand")
part("Feather_Tuft", tuft, "Feather_Tuft")
part("Rubber_Ring", rubber, "Rubber_Ring")
for i, sh in enumerate(screws):
    part("Screw_%d" % (i + 1), sh, "Screw")
print("SIZE %s" % (cad.measure(Part.makeCompound([o.Shape for o in doc.Objects
                                                   if o.TypeId == "Part::Feature" and o.Label[0].isupper()
                                                   and hasattr(o, "Shape")]))["size"],))
print("TOTAL %.1f s" % (time.time() - T0))
