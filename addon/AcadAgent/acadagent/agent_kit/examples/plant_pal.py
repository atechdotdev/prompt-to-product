"""Example: "a plant pot with a face" - a living planter whose screen eyes look happy or thirsty, blushing cheeks, two leaf ears and a soil probe.

fork this file for a character planter (a pot with a face, a virtual pet
for a plant, a plant buddy); change PARAMETERS and the outlines.
ARCHETYPE: planter

How it is built (R940):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board LANDSCAPE_UP in a shallow bay behind the flat face (modules
    facing the front, -Y). The face is centred on the SCREEN, not on the
    board: the screen sits on (10, 11) (the firmware's 2-port pairs leave
    no pair on the board's centre, and 12 is reserved), so the pot is
    centred on x = 40 and the board runs 80 mm to its right. Screen (10,
    11) behind a smoked stadium visor in a recessed black bezel = the
    eyes; lights 1 and 4 (the bottom row, 30 mm either side of the eyes'
    centre line) behind frosted pink domes = the blush cheeks. Three
    CABLED modules, each held by ribs on two opposite sides: the soil
    probe from 13 goes straight up out of the bay into the RIGHT leaf ear
    and down behind the partition - its head hangs dry in the ear, its 49
    mm prongs stand in the soil of the inner pot; the PAT button from 9
    rises (shifting 15 mm sideways in one gentle S) into the LEFT leaf ear
    under a key cap in the ear's dome; USB-C from 7 runs straight out to
    the left side wall in a pocket + liner (a seated USB-C would sit 46
    mm inside the wall). The body is ONE plan outline (a flat face, soft
    front corners, big round back corners) and one side outline with a
    round belly drawing in TAPER at the foot (cad.profile_body, the base
    edge filleted) hollowed with its own sharp core, a partition closing
    the bay from the soil cavity, the cavity opened at the top; split low
    into the fixed Base (posts under the board, a plate behind it) and
    the Shell; four M2.5 screws from below into insert bosses bridged to
    the belly wall. The two ears are their own parts, pinned into the
    bay's roof. Behind the partition: a Drip_Tray on the Base floor, the
    Pot_Liner on four feet in it (drainage holes), the Soil with a slot
    round the prongs.
  * STAGE B - details: a rolled rim bead all round the top (it covers the
    body's sharp top edge), the smile (a round-ended arc band with a dark
    inlay), leaf veins on the ears, a sprout pinned on the right ear, the
    parting-line reveal, the liner's rolled rim, the tray's finger notch,
    lettering, feet.
RESTYLE (R425): the knobs DEPTH, EAR_H, CORNER, TAPER and WALL drive every
outline and every cutter below (each swept to both ends of its range,
CHECK PASS); the tray and pot step in by TAPER, the visor and rim bead
shrink to fit. WIDTH (the board needs 2 x 88 round the eyes' centre line)
and HEIGHT (the pat button's ribbon needs a 25 mm rise to its ear) are set
by the hardware: change them only with the cable routes. The face
elements follow the measured modules (centre(...)), the ears follow
EAR_SPREAD round the screen's centre line. The hardware frame (the board
at x 0..120, z ZB..ZB+60, the modules' faces 0.4 mm behind the front
wall) is the board's own: never move it with a knob. The probe's height
follows HEIGHT (its head 15 mm under the rim, 3 mm over the soil).
DETAILS (visible, 28 of 36): 1 flat face with soft corners; 2 big round
back; 3 round belly drawing in at the foot; 4 soft fillet round the base;
5 smoked stadium visor over the screen eyes; 6 recessed black bezel round
it; 7 the mask window over the screen's active area; 8-9 frosted pink
blush cheeks, domed; 10 the smile with its dark inlay; 11-12 two
dome-topped leaf ears; 13 a leaf vein down each ear; 14 the pat key in
the left ear's dome; 15 a two-leaf sprout on the right ear; 16 rolled rim
bead all round; 17 parting-line reveal over the base; 18 forest-green
base; 19 open soil cavity; 20 terracotta inner pot; 21 its rolled rim;
22 the soil; 23 drip tray under the pot; 24 the tray's finger notch;
25 "PLANT PAL" on the back; 26 USB-C pocket with liner in the left side;
27-28 four countersunk screws and four round feet under the base.
Inside: 29 partition between bay and soil; 30 insert bosses with heat-set
pockets on base pillars; 31 board posts and a plate with pads behind it;
32 a rib onto the board's spine; 33 probe holder ribs in the right ear;
34 button ribs and a pad in the left ear; 35 USB-C holder plates;
36 drainage holes in the pot floor and the pot's four feet.
Materials: mint shell, leaf-green ears and sprout, forest-green base and
tray, smoked visor, black bezel, frosted pink cheeks, dark smile inlay,
sunny-yellow pat key, terracotta pot, soil, rubber feet, chrome screws.
MEASURED (R940, 2026-11-10): ./check CHECK PASS, model 38.4 s (./check wall 124 s, machine loaded by parallel runs; 16 s unloaded before the R280 knobs).
"""
import math
import time
import Part
import FreeCAD as App
import atech_ports as ap
import atech_cad as cad
from FreeCAD import Vector, Placement, Rotation
V = Vector
T0 = time.time()

INTENT = {"board": "upright", "fitted_after": [
    "Shell", "Bezel", "Visor", "Cheek_L", "Cheek_R", "Leaf_Ear_L", "Leaf_Ear_R", "Pat_Key", "Smile", "Sprout",
    "Drip_Tray", "Pot_Liner", "Soil", "Foot_1", "Foot_2", "Foot_3", "Foot_4",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4"],
    "covers": {"Pat_Key": "button_9"}}
REVIEW_CLOSEUPS = ["Visor", "Leaf_Ear_R", "Cheek_L"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and cutter in
# the stages is derived from them (the hardware frame below is the board's).
DEPTH = 140.0      # RESTYLE 118..162 length: face to back (y)
EAR_H = 24.0       # RESTYLE 20..28 height: the leaf ears over the rim (>= 20: the probe's ribbon loops at rim + 14.5)
CORNER = 52.0      # RESTYLE 44..60 radius: the back plan corners (a round back)
TAPER = 14.0       # RESTYLE 11..17 width: how far the belly draws the sides in at the foot (front view)
WALL = 2.4         # RESTYLE 2.0..2.8 wall
# end RESTYLE
WIDTH = 180.0                        # across the face (x), centred on the eyes: the board needs 2 x 88 + the belly
R_FRONT = 8.0                        # the face's plan corners (the USB-C liner needs the side flat behind them)
Z_BELLY = 50.0                       # where the belly meets the straight sides (under the USB-C)
EAR_SPREAD = 45.0                    # the ears' centres either side of the eyes (the cables shift to them)
EAR_W = 28.0                         # a leaf ear's width (the probe and the button need 23 inside)
HEIGHT = 120.0                       # desk to rim: >= 120 gives the pat button's ribbon the 25 mm rise its S-shift needs
EAR_R = 13.9                         # the ears' top corners, front view (13.9 = a round dome; the pat key sits in it)
EAR_FRONT_R, EAR_BACK_R = 8.0, 8.0    # the ears' top corners, side view (the pat key's flange must clear the back one)
# Frame: x across, y front (-) to back, z up; the desk at z = 0.
# The hardware frame (fixed: the board decides it):
ZB = 32.0                            # board bottom (the cheeks' slide corridors under it: z 12.5..32)
Y_IN = -13.0                         # the front wall's inner face (0.4 mm in front of the modules' faces)
FOOT = 3.0                           # round feet under the base
EDGE = 5.0                           # the soft fillet round the base (the rim bead covers the top edge)
SPLIT = FOOT + WALL + 3.6            # base / shell seam (lip top under the cheeks' corridors at z 12.5)
CX = 40.0                            # the face's centre line: the screen on (10, 11)
X0, X1 = CX - WIDTH / 2, CX + WIDTH / 2
YF = Y_IN - WALL                     # the face
YB = YF + DEPTH                      # the back
ZT = HEIGHT                          # the rim
RECESS, BEZEL, LENS_R = 1.0, 3.0, 12.0
VISOR_W, VISOR_H_MAX = 52.0, 28.0        # smoked visor over the screen eyes (a stadium)
SCREEN_WIN = (28.0, 16.0)            # mask window over the screen (active area 25.6 x 13.5)
CHEEK_D = 18.0                       # blush cheek domes over the 17 x 17 LED grids
TRAY_H, TRAY_GAP, TRAY_T = 16.0, 2.0, 1.6    # drip tray height, gap to the walls, wall
POT_FEET, POT_WALL = 5.0, 1.8        # the pot stands 5 mm over the tray floor (a reservoir)
POT_DOWN = 6.0                       # the pot's rim under the shell's rim (the ears' skirts pass over it)
SOIL_DOWN = 18.0                     # soil level under the rim
PROBE_HEAD = 15.0                    # the probe head's bottom under the rim (3 mm over the soil)
SCREW = "M2.5"
COLOURS = {"Base": "#3f6b4f", "Shell": "#cfe8d3", "Bezel": "matte_black", "Visor": "smoked",
           "Cheek": "#ff8fa3", "Ear": "#5fae52", "Pat_Key": "#ffd25e", "Sprout": "#8fd16a", "Smile": "#3b2a20",
           "Drip_Tray": "#3f6b4f", "Pot_Liner": "#c46a43", "Soil": "#4a3426", "Foot": "rubber", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
LANDSCAPE_UP = Rotation(Vector(0, 0, 1), 180).multiply(Rotation(Vector(0, 1, 0), -90))
board = ap.board_object(doc)
board.Placement = Placement(Vector(), LANDSCAPE_UP)
_b = ap.bbox(board)
board.Placement = Placement(Vector(-_b.XMin, 0, ZB - _b.ZMin), LANDSCAPE_UP)   # x 0..120, z 32..92
BB = ap.bbox(board)
scr = ap.seat(doc, "screen", (10, 11))         # top row, x 20..60: the eyes
cheek_l = ap.seat(doc, "light", 1)             # bottom row, x 0..20
cheek_r = ap.seat(doc, "light", 4)             # bottom row, x 60..80
XI0, XI1 = X0 + WALL, X1 - WALL                # the inner side walls
PLATE_Y = BB.YMax + 0.1
PART_Y0 = PLATE_Y + 5.5                        # the partition between bay and soil
PART_Y1 = PART_Y0 + WALL
EAR_X = (CX - EAR_SPREAD, CX + EAR_SPREAD)     # left ear (pat key), right ear (soil probe)
EAR_YB = 39.7                                  # the ears' back face (the button module ends at y 36.75)
# USB-C cabled straight out of the left end to the left wall (mouth -X)
usb, usb_rib = ap.cable(doc, "usbc", 7, ap.module_placement(
    "usbc", (XI0 + 1.0 + 19.75 / 2, -5.1, ZB + 30.0), face="-Y", cable="+X"))
# the soil probe: pins up, prongs down, its head PROBE_HEAD under the rim
# in the right ear, behind the partition over the pot (a straight rise
# from 13 and one loop back over the partition)
probe, probe_rib = ap.cable(doc, "soil_sensor", 13, ap.module_placement(
    "soil_sensor", (EAR_X[1], 24.0, ZT - PROBE_HEAD - 49.0 + 34.25), face="-Y", cable="+Z"),
    via=[(90.0, -1.2, ZT - 6), (EAR_X[1], -1.2, ZT + 2)], smooth=True)
# the pat button: face up under the left ear's top, pins toward the face;
# its ribbon rises from 9 and shifts to the ear's centre on the way up
KEY_Z = ZT + 7.0                               # the button module's centre (its top 3 mm over the probe's head)
key, key_rib = ap.cable(doc, "button", 9, ap.module_placement(
    "button", (EAR_X[0], 25.0, KEY_Z), face="+Z", cable="-Y"),
    via=[(8, -1.2, ZB + 66), (EAR_X[0] + 3, -1.2, ZT - 6), (EAR_X[0], -1.2, ZT - 2)], smooth=True)
tick("hardware")


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def centre(m):
    b = ap.bbox(m)
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


def corner(c, r, a0, a1, n=6):
    """A plan corner as n straight facets (the profile fillet rounds them)."""
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def plan_pts(x0, x1, y0, y1, rf, rb):
    """A plan outline: front corners rf, back corners rb (facets)."""
    return (corner((x0 + rf, y0 + rf), rf, 180, 270, 3) + corner((x1 - rf, y0 + rf), rf, 270, 360, 3)
            + corner((x1 - rb, y1 - rb), rb, 0, 90) + corner((x0 + rb, y1 - rb), rb, 90, 180))


def plan_face(pts, z=0.0):
    return Part.Face(Part.makePolygon([V(x, y, z) for x, y in pts + pts[:1]]))


def zprism(pts, z0, z1):
    return plan_face(pts, z0).extrude(V(0, 0, z1 - z0))


def yprism(x0, x1, z0, z1, r, y0, y1):
    """A rounded rectangle in (x, z) extruded along Y from y0 to y1."""
    w = cad.rounded_rect_wire(x1 - x0, z1 - z0, r, ((x0 + x1) / 2, y0, (z0 + z1) / 2), "Y")
    s = Part.Face(w).extrude(V(0, y1 - y0, 0))
    if s.Volume < 0:
        s.reverse()
    return s


def xprism(y0, y1, z0, z1, x0, x1, r):
    w = cad.rounded_rect_wire(y1 - y0, z1 - z0, r, (x0, (y0 + y1) / 2, (z0 + z1) / 2), "X")
    return Part.Face(w).extrude(V(x1 - x0, 0, 0))


def tub(pts, z0, z1, t, floor):
    """An open-top vessel: the plan prism hollowed to wall t, floor `floor`."""
    outer = zprism(pts, z0, z1)
    inner = plan_face(pts, z0).makeOffset2D(-t, join=0)
    inner.translate(V(0, 0, floor))
    return cad.cut(outer, inner.extrude(V(0, 0, z1 - z0)))


# ------------------------------------------------------------ the body
PLAN = plan_pts(X0, X1, YF, YB, R_FRONT, CORNER)
BELLY = [(TAPER * (1 - t) ** 2, FOOT + t * (Z_BELLY - FOOT)) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
SIDE = ([(X1 - d, z) for d, z in BELLY] + [(X1, ZT), (X0, ZT)] + [(X0 + d, z) for d, z in BELLY[::-1]])
body = cad.profile_body(SIDE, PLAN, spline=False, fillet=(0, EDGE))     # the rim bead covers the (sharp) top edge
# the core keeps SHARP inner edges (a filleted core's concave rounds read
# to ./check as open clip channels)
core = cad.profile_body(SIDE, PLAN, spline=False, fillet=None, inset=WALL)
hull = cad.cut(body, core)
hull = cad.groove_ring(hull, "Z", SPLIT + 2.5, w=0.8, depth=0.6)     # the parting-line reveal (closed ring)
tick("body")
base, shell = cad.split(hull, "Z", at=SPLIT, lip=1.2)
tick("split")
YI1 = YB - WALL
FLOOR = FOOT + WALL

# the fixed base holds the board: posts under its bottom edge (under the
# free ports 2 and 6, clear of the cheeks' corridors), a plate behind it
# with pads 0.1 mm off its back
# (under the free ports 2 and 5; the right-hand screw bosses stand at x 110)
posts = [box(x, x + 6, 0.3, PLATE_Y + 1.5, FLOOR - 0.5, BB.ZMin - 0.1) for x in (27.0, 87.0)]
plate = box(10, 102, PLATE_Y + 1.0, PLATE_Y + 5.0, FLOOR - 0.5, BB.ZMax - 4)
pads = [box(x, x + 6, PLATE_Y, PLATE_Y + 1.5, z, z + 8) for x in (14, 57, 94) for z in (ZB + 10, ZB + 42)]
base = cad.fuse_one(base, plate, *pads, *posts)
# the partition: the bay in front, the soil behind
shell = cad.fuse_one(shell, box(XI0 - 0.5, XI1 + 0.5, PART_Y0, PART_Y1, SPLIT + 2.0, ZT - WALL + 0.5).common(
    body))                                           # clipped to the belly
# open the soil cavity behind the partition, up through the top wall
lift = core.copy()
lift.translate(V(0, 0, WALL + 2.0))
shell = cad.cut(shell, lift.common(box(X0 - 5, X1 + 5, PART_Y1, YB + 5, ZT - WALL - 1.0, ZT + 5)))
# board retention: a rib from the front wall onto the spine (0.2 mm off),
# between the eyes and the right cheek
shell = cad.fuse_one(shell, box(64, 68, Y_IN - 0.5, BB.YMin - 0.2, ZB + 22, ZB + 34))
tick("base + partition")

# four M2.5 screws from below, in the bay's two ends: a pillar on the base
# floor up to 0.1 mm under an insert boss hung on the side wall
INSERT_D = {"M2": 3.2, "M2.5": 3.6, "M3": 4.3}[SCREW]
BOSS_Z0 = SPLIT + 2.0
XS0, XS1 = X0 + TAPER + WALL + 3.6, X1 - TAPER - WALL - 3.6     # inside the belly
SCREWS = [(XS0, -4.0), (XS0, 4.5), (XS1, -4.0), (XS1, 4.5)]
screws, sleeves, bridges, pockets, pillars = [], [], [], [], []
for x, y in SCREWS:
    wall_x = X0 - 1 if x < CX else X1 + 1
    sleeves.append(cyl(INSERT_D / 2 + 1.2, (x, y, BOSS_Z0), 12.0))
    bridges.append(box(wall_x, x, y - 3.0, y + 3.0, BOSS_Z0, BOSS_Z0 + 12.0).common(body))   # to the belly wall
    pockets.append(cyl(INSERT_D / 2, (x, y, BOSS_Z0 - 1.0), 10.5))
    pillars.append(cyl(INSERT_D / 2 + 1.2, (x, y, FLOOR - 0.5), BOSS_Z0 - 0.1 - (FLOOR - 0.5)))
    screws.append(cad.screw("csk_phillips", SCREW, int(BOSS_Z0 + 6.0 - FOOT), at=(x, y, FOOT), axis="+Z"))
shell = cad.cut(cad.fuse_one(shell, *sleeves, *bridges), pockets)
base = cad.fuse_one(base, *pillars)
for x, y in SCREWS:
    base = cad.countersink(base, (x, y, FOOT), "+Z", 2.9, 5.6, 90.0)
tick("screws")

# ------------------------------------------------------------ the face
# the eyes: a black bezel tray set RECESS back in its opening, holding the
# smoked stadium visor, its back the mask with the screen window (0.36 mm
# off the screen)
sx, _sy, sz = centre(scr)
# the visor shrinks under a low rim: its bezel stays 2 mm under the roof
VISOR_H = min(VISOR_H_MAX, 2 * (ZT - WALL - 2.0 - BEZEL - sz))
LENS_R = min(LENS_R, VISOR_H / 2 - 0.5)
lx0, lx1, lz0, lz1 = sx - VISOR_W / 2, sx + VISOR_W / 2, sz - VISOR_H / 2, sz + VISOR_H / 2
shell = cad.cut(shell, yprism(lx0 - BEZEL, lx1 + BEZEL, lz0 - BEZEL, lz1 + BEZEL, LENS_R + BEZEL, YF - 6, Y_IN + 1))
yt0, yt1 = YF + RECESS, Y_IN + 3.0
tray = cad.fuse_one(yprism(lx0 - BEZEL, lx1 + BEZEL, lz0 - BEZEL, lz1 + BEZEL, LENS_R + BEZEL, yt0, Y_IN + 1),
                    yprism(lx0 - 2, lx1 + 2, lz0 - 2, lz1 + 2, LENS_R + 2, Y_IN + 0.5, yt1))
y_lens1 = Y_IN + 1.7
tray = cad.cut(tray, yprism(lx0, lx1, lz0, lz1, LENS_R, yt0 - 1, y_lens1))
visor = yprism(lx0, lx1, lz0, lz1, LENS_R, yt0 + 0.6, y_lens1 - 0.3)          # 0.3 mm air before the mask
tray = cad.cut(tray, cad.rounded_box(SCREEN_WIN[0], 10, SCREEN_WIN[1], 1.5,
                                     at=(sx - SCREEN_WIN[0] / 2, yt1 - 5, sz - SCREEN_WIN[1] / 2), edges="y"))
# the cheeks: frosted pink domes from 0.4 mm off the LEDs to 0.8 mm proud,
# a flange behind the wall
cheeks = []
for m in (cheek_l, cheek_r):
    gx, _gy, gz = centre(m)
    gb = ap.bbox(m)
    c = cad.lens(CHEEK_D, (gb.YMin - 0.4) - (YF - 0.8), dome=0.8, at=(gx, gb.YMin - 0.4, gz), axis="-Y")
    shell = cad.opening_for(shell, c, clearance=0.2, chamfer=0.0, axis="-Y")
    cheeks.append(cad.fuse_one(c, cyl(CHEEK_D / 2 + 1.5, (gx, Y_IN + 0.9, gz), 0.8, (0, -1, 0))))
# USB-C on the left side: a pocket brings the wall to 0.25 mm off the
# socket mouth, then the measured opening; holder plates over and under
# the module from the side wall (0.3 mm off)
ub = ap.bbox(usb)
uy, uz = -5.9, (ub.ZMin + ub.ZMax) / 2
pocket = xprism(uy - 4.5, uy + 4.5, uz - 6.5, uz + 6.5, X0 - 5, ub.XMin - 1.3, 3)
liner = cad.cut(xprism(Y_IN - 0.4, uy + 6.5, uz - 8.0, uz + 8.0, ub.XMin - 0.25, XI0 - 0.5, 3.0).common(body), pocket)
usb_hold = [box(XI0 - 0.5, ub.XMax - 4.0, ub.YMin + 0.8, ub.YMax - 0.8, z0, z1)
            for z0, z1 in ((ub.ZMax + 0.3, ub.ZMax + 2.0), (ub.ZMin - 2.0, ub.ZMin - 0.3))]
shell = cad.fuse_one(cad.cut(shell, pocket), liner, *usb_hold)
shell = cad.socket_opening(shell, usb, margin=1.5)
tick("face")

# ------------------------------------------------------------ the leaf ears
# each ear: a round-topped hood flush with the face, standing on the bay's
# roof in front of the partition and hanging a skirt over the pot behind
# it; the bay's roof is opened under it for the ribbon; two pegs into the
# roof hold it


def ear_side(y0, y1, top, rf, rb, x0, x1):
    """The ear's side view (y, z): a vertical front, round top corners rf / rb, extruded x0..x1."""
    pts = ([(y0, ZT - 41)] + corner((y0 + rf, top - rf), rf, 180, 90, 4)
           + corner((y1 - rb, top - rb), rb, 90, 0, 5) + [(y1, ZT - 41)])
    f = Part.Face(Part.makePolygon([V(x0, y, z) for y, z in pts + pts[:1]]))
    s_ = f.extrude(V(x1 - x0, 0, 0))
    if s_.Volume < 0:
        s_.reverse()
    return s_


def ear_inner(xc):
    x0, x1 = xc - EAR_W / 2 + WALL, xc + EAR_W / 2 - WALL
    return yprism(x0, x1, ZT - 41, ZT + EAR_H - WALL, EAR_R - WALL, Y_IN, EAR_YB - WALL).common(
        ear_side(Y_IN, EAR_YB - WALL, ZT + EAR_H - WALL, EAR_FRONT_R - WALL, EAR_BACK_R - WALL, x0 - 1, x1 + 1))


ears, roof_cuts, peg_holes = [], [], []
for xc in EAR_X:
    ex0, ex1 = xc - EAR_W / 2, xc + EAR_W / 2
    outer = yprism(ex0, ex1, ZT - 40, ZT + EAR_H, EAR_R, YF, EAR_YB).common(
        ear_side(YF, EAR_YB, ZT + EAR_H, EAR_FRONT_R, EAR_BACK_R, ex0 - 1, ex1 + 1)).common(
        box(ex0 - 1, ex1 + 1, YF - 1, EAR_YB + 1, ZT - POT_DOWN + 0.5, ZT + EAR_H + 1))
    outer = cad.soften(outer, 1.5, [e for e in outer.Edges if e.BoundBox.ZMin > ZT + 1])
    e = cad.cut(outer, [ear_inner(xc), box(ex0 - 1, ex1 + 1, YF - 1, PART_Y1 + 0.3, ZT - POT_DOWN, ZT)])
    pegs = [cyl(0.9, (px, (Y_IN + PART_Y0) / 2, ZT - (WALL - 0.8)), WALL - 0.3) for px in (ex0 + WALL / 2, ex1 - WALL / 2)]
    ears.append(cad.fuse_one(e, *pegs))
    peg_holes += [cyl(1.05, (px, (Y_IN + PART_Y0) / 2, ZT - (WALL - 0.6)), WALL - 0.4) for px in (ex0 + WALL / 2, ex1 - WALL / 2)]
    roof_cuts.append(ear_inner(xc).common(box(ex0, ex1, Y_IN + 0.5, PART_Y1 + 2.0, ZT - WALL - 1.0, ZT + 1.0)))
shell = cad.cut(shell, roof_cuts + peg_holes)
ear_l, ear_r = ears
# the probe's holder: ribs from the right ear's side walls onto the probe
# head's sides (0.3 mm off), over the pot's rim
pb = ap.bbox(probe)
z_head1 = pb.ZMax
ear_r = cad.fuse_one(ear_r, *[box(x0, x1, pb.YMin + 1.0, pb.YMax - 1.0, ZT - POT_DOWN + 1.0, z_head1 - 0.5)
                              for x0, x1 in ((EAR_X[1] - EAR_W / 2 + WALL - 0.5, pb.XMin - 0.3),
                                             (pb.XMax + 0.3, EAR_X[1] + EAR_W / 2 - WALL + 0.5))])
# the pat button's holder: ribs on its sides and a pad under its back
# half (behind the ribbon's socket), from the left ear's walls
kb = ap.bbox(key)
ear_l = cad.fuse_one(ear_l, *[box(x0, x1, kb.YMin + 1.0, kb.YMax - 1.0, kb.ZMin + 1.0, kb.ZMax - 1.0)
                              for x0, x1 in ((EAR_X[0] - EAR_W / 2 + WALL - 0.5, kb.XMin - 0.3),
                                             (kb.XMax + 0.3, EAR_X[0] + EAR_W / 2 - WALL + 0.5))],
                     box(kb.XMin + 1.0, kb.XMax - 1.0, kb.YMax - 6.0, EAR_YB - WALL + 0.5, kb.ZMin - 6.0, kb.ZMin - 0.3))
# the pat key through the left ear's flat top, a plunger onto the button
kx, ky, _kz = centre(key)
FLANGE = 1.2
r_in = EAR_R - WALL                            # the dome's inner radius: the flange clears it at its edge
z_base = ZT + EAR_H - WALL - 0.9 - (r_in - math.sqrt(r_in ** 2 - (11.5 / 2 + FLANGE + 0.3) ** 2))
cap = cad.button_cap(11.5, ZT + EAR_H + 1.6 - z_base, dome=0.8, flange=FLANGE, at=(kx, ky, z_base), axis="+Z")
ear_l = cad.opening_for(ear_l, cap, clearance=0.25, chamfer=0.3, axis="+Z")
cap = cad.fuse_one(cap, cyl(3.0, (kx, ky, kb.ZMax + 0.16), z_base - kb.ZMax - 0.16 + 0.5))
tick("ears")

# ------------------------------------------------------------ tray, pot, soil
cav = (XI0 + TAPER, XI1 - TAPER, PART_Y1, YI1)      # inside the belly at the tray's foot
tp = plan_pts(cav[0] + TRAY_GAP, cav[1] - TRAY_GAP, cav[2] + TRAY_GAP, cav[3] - TRAY_GAP, 3.0,
              CORNER - WALL - TRAY_GAP)
drip = tub(tp, FLOOR, FLOOR + TRAY_H, TRAY_T, TRAY_T)
# two locating pegs under the tray drop into holes through the base floor
tcx, tcy = (XI0 + XI1) / 2, (PART_Y1 + YI1) / 2
PEGS = [(tcx - 0.3 * (XI1 - XI0), tcy), (tcx + 0.3 * (XI1 - XI0), tcy)]
drip = cad.fuse_one(drip, *[cyl(2.5, (x, y, FLOOR - 1.5), 2.0) for x, y in PEGS])
base = cad.cut(base, [cyl(2.65, (x, y, FOOT - 1), WALL + 2) for x, y in PEGS])
g = TRAY_GAP + TRAY_T + 1.0
pp = plan_pts(cav[0] + g, cav[1] - g, cav[2] + g, cav[3] - g, 2.0, CORNER - WALL - g)
POT_Z0 = FLOOR + TRAY_T + POT_FEET
pot = tub(pp, POT_Z0, ZT - POT_DOWN, POT_WALL, 2.0)
pcx, pcy = (cav[0] + cav[1]) / 2, (cav[2] + cav[3]) / 2
pw, pd = (cav[1] - cav[0]) - 2 * g, (cav[3] - cav[2]) - 2 * g
pot_feet = [cyl(4.0, (pcx + sx_ * 0.3 * pw, pcy + sy_ * 0.3 * pd, FLOOR + TRAY_T), POT_FEET + 1.0)
            for sx_ in (-1, 1) for sy_ in (-1, 1)]
pot = cad.fuse_one(pot, *pot_feet)
sp = plan_face(pp).makeOffset2D(-POT_WALL, join=0)
sp.translate(V(0, 0, POT_Z0 + 2.0))
soil = sp.extrude(V(0, 0, (ZT - SOIL_DOWN) - (POT_Z0 + 2.0)))
# a slot in the soil round the probe's prongs (0.3 mm clear)
soil = cad.cut(soil, box(pb.XMin - 0.3, pb.XMax + 0.3, pb.YMin - 0.3, pb.YMax + 0.3, POT_Z0, ZT))
tick("stage A")


# === STAGE B: details ===
# (a fork may stop after STAGE A, run ./check, then add these one by one)
# a rolled rim bead all round the top (into the wall 1.2, out 2.5)
BEAD_OUT = 3.5
BEAD_H = min(11.0, ZT - (lz1 + BEZEL) - 1.0)      # over the visor's bezel under a low rim
bead = cad.cut(zprism(plan_pts(X0 - BEAD_OUT, X1 + BEAD_OUT, YF - BEAD_OUT, YB + BEAD_OUT, R_FRONT + BEAD_OUT,
                               CORNER + BEAD_OUT), ZT - BEAD_H, ZT),
               zprism(plan_pts(X0 + 1.2, X1 - 1.2, YF + 1.2, YB - 1.2, R_FRONT - 1.2, CORNER - 1.2), ZT - BEAD_H - 1, ZT + 1))
shell = cad.fuse_one(shell, cad.soften(bead, min(2.5, BEAD_H / 2 - 0.3), [e for e in bead.Edges
                                                    if e.BoundBox.ZMin > ZT - BEAD_H - 0.5 and e.BoundBox.ZMax < ZT - BEAD_H + 0.5
                                                    or e.BoundBox.ZMin > ZT - 0.5]))
# the smile: a round-ended arc band 2.4 wide, 1.4 deep, between the
# cheeks under the visor, filled by a dark inlay
SMILE_R, SMILE_W, SMILE_DEEP = 7.3, 2.4, min(1.4, WALL - 0.8)
smile_z = lz0 - BEZEL - 2.4 - 1.2 + 2.0          # the arc's centre: its ends 2.4 under the bezel
yy0, yy1 = YF - 1.0, YF + SMILE_DEEP
smile = cad.cut(cyl(SMILE_R + SMILE_W / 2, (sx, yy0, smile_z), yy1 - yy0, (0, 1, 0)),
                cyl(SMILE_R - SMILE_W / 2, (sx, yy0 - 1, smile_z), yy1 - yy0 + 2, (0, 1, 0)))
smile = smile.common(box(sx - 12, sx + 12, yy0, yy1, smile_z - 12, smile_z - 2.0))
ex_ = math.sqrt(SMILE_R ** 2 - 2.0 ** 2)
# round ends as 8 facets (an arc end reads to ./check as a clip channel)
ends = [Part.Face(Part.makePolygon([V(sx + k * ex_ + SMILE_W / 2 * math.cos(math.radians(22.5 + 45 * i)), yy0,
                                         smile_z - 2.0 + SMILE_W / 2 * math.sin(math.radians(22.5 + 45 * i)))
                                       for i in range(9)])).extrude(V(0, yy1 - yy0, 0)) for k in (-1, 1)]
smile = cad.fuse_one(smile, *ends)
smile_inlay = shell.common(smile)                 # a dark inlay fills it (an insert)
shell = cad.cut(shell, smile)
# leaf veins: a groove down each ear's face
ear_l = cad.cut(ear_l, box(EAR_X[0] - 0.5, EAR_X[0] + 0.5, YF - 1, YF + 0.7, ZT + 3, ZT + EAR_H - 6))
ear_r = cad.cut(ear_r, box(EAR_X[1] - 0.5, EAR_X[1] + 0.5, YF - 1, YF + 0.7, ZT + 3, ZT + EAR_H - 6))
# a sprout on the right ear's dome: a stem pinned through the top wall
# (0.15 mm clear) and two leaves (flattened ellipsoids, tilted up)
SPROUT_Y, STEM_R, STEM_H = 16.0, 1.5, 9.0
st_top = ZT + EAR_H + STEM_H
stem = cyl(STEM_R, (EAR_X[1], SPROUT_Y, ZT + EAR_H - WALL), WALL + STEM_H + 0.8)
leaves = []
for k in (-1, 1):
    m_ = App.Matrix()
    m_.scale(6.5, 3.2, 1.3)
    lf = Part.makeSphere(1.0).transformGeometry(m_)
    lf.rotate(V(0, 0, 0), V(0, 1, 0), -28.0 * k)
    lf.translate(V(EAR_X[1] + k * 5.6, SPROUT_Y, st_top + 1.6))
    leaves.append(lf)
sprout = cad.fuse_one(stem, *leaves)
ear_r = cad.cut(ear_r, cyl(STEM_R + 0.15, (EAR_X[1], SPROUT_Y, ZT + EAR_H - WALL - 1.0), WALL + 3.0))
# the pot: a rolled rim band round its top, drainage holes in its floor
rim = cad.cut(zprism(plan_pts(cav[0] + g - 1.5, cav[1] - g + 1.5, cav[2] + g - 1.5, cav[3] - g + 1.5, 3.5,
                              CORNER - WALL - g + 1.5), ZT - POT_DOWN - 6.0, ZT - POT_DOWN),
              zprism(pp, ZT - POT_DOWN - 7.0, ZT - POT_DOWN + 1.0))
pot = cad.fuse_one(pot, cad.soften(rim, 0.6))
pot = cad.grille(pot, (pcx, pcy, POT_Z0), (0, 0, -1), (pw - 40, pd - 40), kind="round", hole=4.0, pitch=14.0)
# the tray: a finger notch in its back rim
drip = cad.cut(drip, cad.rounded_box(24, 8, 8, 3.5, at=(pcx - 12, cav[3] - TRAY_GAP - 5, FLOOR + TRAY_H - 6),
                                     edges="y"))
# lettering on the back
shell = cad.text(shell, "PLANT PAL", (CX, YB, ZT * 0.45), (0, 1, 0), 7, depth=0.5, mode="deboss")
# round feet in recesses under the base
feet = []
for x, y in ((X0 + TAPER + 20, YF + 26), (X1 - TAPER - 20, YF + 26), (X0 + 36, YB - 36), (X1 - 36, YB - 36)):
    base = cad.cut(base, cyl(7.15, (x, y, FOOT - 1), 2.2))
    feet.append(cad.foot(14, FOOT + 1.2, style="dome", at=(x, y, FOOT + 1.2)))
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape, colour=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    return o


o = part("Base", base)
o.ViewObject.ShapeColor = cad.color(COLOURS["Base"])
o = part("Shell", shell)
o.ViewObject.ShapeColor = cad.color(COLOURS["Shell"])
o = part("Bezel", tray)
o.ViewObject.ShapeColor = cad.color(COLOURS["Bezel"])
o = part("Visor", visor)
o.ViewObject.ShapeColor = cad.color("smoked")
o.ViewObject.Transparency = cad.transparency("smoked")
o = part("Cheek_L", cheeks[0])
o.ViewObject.ShapeColor = cad.color(COLOURS["Cheek"])
o.ViewObject.Transparency = cad.transparency("frosted")
o = part("Cheek_R", cheeks[1])
o.ViewObject.ShapeColor = cad.color(COLOURS["Cheek"])
o.ViewObject.Transparency = cad.transparency("frosted")
o = part("Leaf_Ear_L", ear_l)
o.ViewObject.ShapeColor = cad.color(COLOURS["Ear"])
o = part("Leaf_Ear_R", ear_r)
o.ViewObject.ShapeColor = cad.color(COLOURS["Ear"])
o = part("Sprout", sprout)
o.ViewObject.ShapeColor = cad.color(COLOURS["Sprout"])
o = part("Smile", smile_inlay)
o.ViewObject.ShapeColor = cad.color(COLOURS["Smile"])
o = part("Pat_Key", cap)
o.ViewObject.ShapeColor = cad.color(COLOURS["Pat_Key"])
o = part("Drip_Tray", drip)
o.ViewObject.ShapeColor = cad.color(COLOURS["Drip_Tray"])
o = part("Pot_Liner", pot)
o.ViewObject.ShapeColor = cad.color(COLOURS["Pot_Liner"])
o = part("Soil", soil)
o.ViewObject.ShapeColor = cad.color(COLOURS["Soil"])
for i, sh in enumerate(feet):
    o = part("Foot_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color("rubber")
for i, sh in enumerate(screws):
    o = part("Screw_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color("chrome")
print("SIZE", cad.measure(Part.makeCompound([base, shell, ear_l, ear_r, cap] + feet))["size"])
print("TOTAL %.1f s" % (time.time() - T0))
