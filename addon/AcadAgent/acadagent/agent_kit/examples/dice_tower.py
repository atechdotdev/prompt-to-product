"""Example: "a dice tower that counts and announces your rolls" - a castle keep that counts every die and plays a fanfare.

fork this file for a dice tower (a castle dice tower, a dice roller, a
rolling tower with a tray, a gaming keep); change PARAMETERS and the outlines.
ARCHETYPE: dice tower

How it is built (R990):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board stands UPRIGHT on its long edge in a duct along the keep's right
    wall, modules facing out (+X), its front column (9-14) toward the tray.
    The speaker on (10, 11) hangs forward off the board and fires through a
    rose-window grille in the right wall. The screen is CABLED from (13, 14):
    both ribbons leave the board's front edge, turn flat through a quarter
    circle and run along the inside of the front wall into the screen,
    portrait behind the gold shield over the gate (the ribbons stay
    flat - no twist, no crossing). The distance sensor is CABLED from 9
    straight forward into a pocket in the gate's right jamb and looks
    ACROSS the exit through an open window: every die that rolls out of
    the keep breaks its beam. USB-C on port 1 at the back, in a recess.
    The keep is ONE part: stone walls on a talus, corner pilasters, a
    corbelled parapet with merlons, a flat deck round the open chute, and
    inside it the duct partition, the screen bay, the jamb block, a left
    guide wedge, two 45 deg baffles and the exit ramp (the dice drop in at
    the top, tumble off both baffles and roll out under the portcullis).
    The Base (fixed: it carries the board on pads) is the floor of the keep
    and of the walled tray; four M2.5 screws come up through it into the
    pilasters.
  * STAGE B - details: stone coursing with staggered joints, voussoirs and
    a keystone round the gate, a wooden portcullis in jamb grooves, the
    red banner with a swallowtail, the gold shield with a raised rim round
    the smoked window, cross-shaped arrow loops, the rose window's frame,
    corner turrets on the tray wall, a wood cap rail, a felt floor, a
    pennant on the deck, two dice, lettering, rubber feet.
RESTYLE (R990): TOWER_H, ARCH_W, TRAY_L, WALL and TURRET_R drive every outline and
cutter below (the parapet, deck, baffles and banner follow TOWER_H; the
keep's width follows the gate, centred on it; the tray follows TRAY_L;
the cap rail, felt and wall courses stop at the turrets).
The hardware frame (the board's plane P, its front edge Y0, its foot ZB)
is the board's own: never move it with a knob.
DETAILS (visible, 35): 1 square keep on a sloped talus; 2 four corner
pilasters with quoin joints; 3 stone courses with staggered joints on
every face; 4 a corbel table under 5 the overhanging parapet; 6 merlons
and crenels all round; 7 round-headed gate; 8 voussoir ring; 9 keystone
and impost blocks; 10 wooden portcullis with spikes in jamb grooves;
11 the open sensor window in the gate's right jamb (12 its light-gate
slot out through the left wall); 13 the red banner hanging under the
corbels; 14 its swallowtail and rolled hem; 15 the gold shield; 16 its
raised rim; 17 the bezel round 18 the smoked screen window; 19 the iron
rose-window speaker grille; 20 its stone frame ring; 21-26 six
cross-shaped arrow loops (left, back, front); 27 the red pennant on its
brass pole; 28 the walled tray; 29-30 two round corner turrets with
merlons; 31 the wood cap rail; 32 the green felt floor; 33 USB-C recess
in the back; 34 "ATECH" on the tray front; 35 a red d6 and a blue d20 in
the tray. Under the base: four countersunk M2.5 screws, rubber feet.
Inside: the duct partition with board standoffs, the spine rib, the
screen bay with its holder rib, the jamb block with the sensor pocket,
the guide wedge, two 45 deg baffles, the exit ramp, the open chute, board
pads, the pennant's socket boss.
Materials: grey stone keep, darker stone base and tray, wood portcullis
and cap rail, red banner and pennant, gold shield, smoked window, iron
grille, green felt, red and blue dice, rubber feet, chrome screws.
Placeholders: the dice are props resting in the felt (INTENDED_OVERLAPS);
one screw type throughout (M2.5 x 12 countersunk, four).
MEASURED (R990, 2026-11-17): ./check CHECK PASS, run_seconds 16-26 s, wall 38-76 s; every RESTYLE end CHECK PASS (42-69 s).
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
    "Tower", "Banner", "Shield", "Screen_Lens", "Portcullis", "Flag_Pole", "Pennant", "Rose_Grille",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4"]}
# the dice rest in the felt (it gives under them)
INTENDED_OVERLAPS = [("Die_D6", "Felt"), ("Die_D20", "Felt")]
REVIEW_CLOSEUPS = ["Shield", "Tower"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them.
TOWER_H = 200.0    # RESTYLE 170..230 height: the keep, desk to the merlon tops
ARCH_W = 36.0      # RESTYLE 30.5..41.5 width: the gate (the keep is centred on it)
TRAY_L = 86.0      # RESTYLE 73..99 length: the tray in front of the keep (y)
WALL = 5.0         # RESTYLE 4.25..5.75 wall: the keep's and the tray's stone walls
TURRET_R = 10.0    # RESTYLE 8.5..11.5 radius: the tray's round corner turrets
# end RESTYLE
# Frame: x across (the viewer's right +), y from the player (-) to the
# back, z up. The hardware frame (fixed, the board's own):
P = 77.0                         # the PCB's module face (x); modules face +X
Y0 = 30.1                        # the board's front edge (the speaker hangs 20.6 in front of it)
ZB = 6.5                         # the board's bottom edge
FOOT_H = 1.5                     # rubber feet under the base
FLOOR = 6.0                      # the base's top face: the tray floor and the keep's floor
F_IN = 7.0                       # the front wall's inner face (0.4 mm in front of the screen)
R_IN = 98.0                      # the right wall's inner face (0.8 mm off the speaker)
B_IN = 91.0                      # the back wall's inner face (0.3 mm off the USB-C mouth)
JAMB_X = P - 8.5                 # the gate's right jamb (the sensor window in it)
PIL = (12.0, 3.0)                # corner pilasters: size, how far they stand out
TALUS = (6.0, 20.0)              # the sloped foot: how far out, how high
PARAPET = 24.0                   # the parapet over the deck
CORBEL = 3.0                     # the parapet stands out this far on corbels
MERLON = (12.0, 9.0)             # merlon width (crenel the same), crenel depth
ARCH_SPRING = 24.0               # the gate's straight jambs above the floor
COURSE = 11.0                    # stone course height
TRAY_WALL_H = 22.0               # tray walls above the floor
TRAY_OUT = 10.0                  # the tray wider than the keep, each side
SCREW = "M2.5"                   # ONE screw type: M2.5 x 12 countersunk
COLOURS = {"Base": "#6c675f", "Tower": "#9d978b", "Banner": "#a3181d", "Shield": "#d6a62c",
           "Screen_Lens": "smoked", "Portcullis": "#6b4425", "Tray_Rim": "#7b5130", "Felt": "#2d5a3d",
           "Flag_Pole": "brass", "Pennant": "#a3181d", "Foot": "rubber", "Screw": "chrome",
           "Rose_Grille": "#3a3b3f", "Die_D6": "#c8202a", "Die_D20": "#2f5fb8"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
SIDE = Rotation(Vector(0, 0, 1), 90).multiply(Rotation(Vector(0, 0, 1), 180))   # face +X, 9-14 at the front
board = ap.board_object(doc)
board.Placement = Placement(V(P, Y0 + 60.0, ZB), SIDE)   # x P-2.5..P+4.5, y Y0..Y0+60, z ZB..ZB+120
BB = ap.bbox(board)
usb = ap.seat(doc, "usbc", 1)                            # back column, bottom: mouth +Y
spk = ap.seat(doc, "speaker", (10, 11))                  # front column: hangs 20.6 forward, fires +X
SB, UB = ap.bbox(spk), ap.bbox(usb)
# (the plug lead ends, MEASURED: 1.27 mm off the PCB face, 3.23 past the edge)
PLUG_X, PLUG_Y = P + 1.27, Y0 - 3.23
Z9, Z13, Z14 = ZB + 10.0, ZB + 90.0, ZB + 110.0          # the port centres up the front column
SZ = (Z13 + Z14) / 2                                     # the screen's centre height
# the keep's centre line: the gate's (the gate's right jamb is the sensor's)
CX = JAMB_X - ARCH_W / 2
# the distance sensor: cabled from 9 straight forward into the jamb, face
# -X across the exit, its socket lead 1 mm short of the plug's (MEASURED
# socket lead = centre + (3.5, 12.89) along (back, cable))
TOF_C = (PLUG_X - 3.5, PLUG_Y - 1.0 - 12.89, Z9)
tof, tof_rib = ap.cable(doc, "distance_sensor", 9, ap.module_placement(
    "distance_sensor", TOF_C, face="-X", cable="+Y"))
# the screen: portrait behind the front wall, centred on the keep, its pins
# toward +X; each ribbon turns flat (width along z) through a quarter
# circle from the plug into the socket (MEASURED socket lead = centre +
# (12.89, 3.55) along (cable, back))
SCR_C = (CX, F_IN + 0.4 + 4.82, SZ)
LEAD = (SCR_C[0] + 12.89, SCR_C[1] + 3.55)
RT = PLUG_Y - LEAD[1]                                    # the turn radius


def screen_route(z):
    c = (PLUG_X - RT, PLUG_Y)
    pts = [(c[0] + RT * math.cos(math.radians(a)), c[1] - RT * math.sin(math.radians(a)), z)
           for a in (15, 30, 45, 60, 75, 90)]
    return pts + [((pts[-1][0] + LEAD[0]) / 2 + 0.1, LEAD[1], z)]


scr, scr_rib = ap.cable(doc, "screen", (13, 14), ap.module_placement("screen", SCR_C, face="-Y", cable="+X"),
                        via={13: screen_route(Z13), 14: screen_route(Z14)}, smooth=True)
TB, CB = ap.bbox(tof), ap.bbox(scr)
tick("hardware")


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def prism_yz(pts, x0, x1):
    """A prism of a (y, z) outline from x0 to x1."""
    w = Part.makePolygon([V(x0, y, z) for y, z in pts] + [V(x0, pts[0][0], pts[0][1])])
    return Part.Face(w).extrude(V(x1 - x0, 0, 0))


def prism_xz(pts, y0, y1):
    """A prism of an (x, z) outline from y0 to y1."""
    w = Part.makePolygon([V(x, y0, z) for x, z in pts] + [V(pts[0][0], y0, pts[0][1])])
    return Part.Face(w).extrude(V(0, y1 - y0, 0))


def prism_xy(pts, z0, z1):
    w = Part.makePolygon([V(x, y, z0) for x, y in pts] + [V(pts[0][0], pts[0][1], z0)])
    return Part.Face(w).extrude(V(0, 0, z1 - z0))


def arch_pts(x0, x1, z0, zs, n=12, inset=0.0):
    """An (x, z) round-headed arch outline: jambs x0..x1 from z0 up to the
    springing zs, a half circle over them (n facets)."""
    r = (x1 - x0) / 2 - inset
    c = (x0 + x1) / 2
    pts = [(c - r, z0), (c + r, z0)]
    pts += [(c + r * math.cos(math.pi * i / n), zs + r * math.sin(math.pi * i / n)) for i in range(n + 1)]
    return pts


def insert(shell, cutter):
    """(shell with the opening, the piece that fills it exactly)."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1:
        piece, rest = shell.common(cutter, 0.01), shell.cut(cutter, 0.01)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, piece


# ------------------------------------------------------------ the keep's frame
F0 = F_IN - WALL                 # the front face
R1 = R_IN + WALL                 # the right face
B1 = B_IN + WALL                 # the back face
L0 = 2 * CX - R1                 # the left face (the keep centred on the gate)
L_IN = L0 + WALL
AL = JAMB_X - ARCH_W             # the gate's left jamb
H = TOWER_H
DECK = H - PARAPET               # the deck (walkway) round the chute's mouth
XP = P - 6.0                     # the duct partition (x XP..XP+3, 0.5 mm off the board's back)
BAY_Z = SZ - 24.5                # the screen bay's floor (top face)
print("FRAME keep x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f; gate x %.1f..%.1f; chute x %.1f..%.1f y %.1f..%.1f; "
      "screen %s sensor %s" % (L0, R1, F0, B1, FLOOR, H, AL, JAMB_X, L_IN, XP, Y0, B_IN,
                               [round(v, 1) for v in (CB.XMin, CB.XMax, CB.ZMin, CB.ZMax)],
                               [round(v, 1) for v in (TB.XMin, TB.XMax, TB.YMin, TB.YMax, TB.ZMin, TB.ZMax)]))

# ------------------------------------------------------------ the keep
outer = box(L0, R1, F0, B1, FLOOR, DECK)
# the corner pilasters (they stand out PIL[1] on both faces)
pil = [box(x - PIL[1] if sx < 0 else x - PIL[0] + PIL[1], x + PIL[0] - PIL[1] if sx < 0 else x + PIL[1],
           y - PIL[1] if sy < 0 else y - PIL[0] + PIL[1], y + PIL[0] - PIL[1] if sy < 0 else y + PIL[1],
           FLOOR, DECK - 6.0)
       for x, sx in ((L0, -1), (R1, 1)) for y, sy in ((F0, -1), (B1, 1))]
# the talus: the walls' foot slopes out TALUS[0] over TALUS[1]
tal = cad.loft([cad.rounded_rect_wire(R1 - L0 + 2 * TALUS[0], B1 - F0 + 2 * TALUS[0], 0.5,
                                      ((L0 + R1) / 2, (F0 + B1) / 2, FLOOR), "Z"),
                cad.rounded_rect_wire(R1 - L0 + 0.2, B1 - F0 + 0.2, 0.5,
                                      ((L0 + R1) / 2, (F0 + B1) / 2, FLOOR + TALUS[1]), "Z")], ruled=True)
# the parapet: out CORBEL on every face, from the corbel table to the top
par = box(L0 - CORBEL, R1 + CORBEL, F0 - CORBEL, B1 + CORBEL, DECK - 6.0, H)
keep = cad.fuse_one(outer, tal, par, *pil)
# one cavity: the interior up to the deck's underside, and the walk inside
# the parapet above it
keep = cad.cut(keep, [box(L_IN, R_IN, F_IN, B_IN, FLOOR - 1, DECK - 2.0),
                      box(L0 + 2.0, R1 - 2.0, F0 + 2.0, B1 - 2.0, DECK, H + 1)])
tick("keep shell")

# ------------------------------------------------------------ inside the keep
DUCT_TOP = DECK - 2.0
inner = []
# the duct partition behind the board (and its standoffs, 0.1 mm off the
# board's flat back), up to the deck
inner.append(box(XP, XP + 3.0, Y0 - 2.0, B_IN + 0.5, FLOOR, DUCT_TOP + 0.5))
inner += [box(XP + 2.5, BB.XMin - 0.1, y, y + 6, z, z + 6) for y in (Y0 + 8, Y0 + 46) for z in (ZB + 30, ZB + 100)]
# the jamb block: the gate's right side, from the front wall back to the
# board's front edge, up to the screen bay's floor (the sensor's pocket in it)
inner.append(box(JAMB_X, P - 0.5, F_IN - 0.5, Y0, FLOOR, BAY_Z))
# the screen bay: a floor over the exit, a back wall to the deck, a holder
# rib 0.25 mm behind the screen
inner.append(box(L_IN - 0.5, P - 0.5, F_IN - 0.5, Y0, BAY_Z - 2.0, BAY_Z))
inner.append(box(L_IN - 0.5, XP + 0.5, Y0 - 2.0, Y0, BAY_Z - 0.5, DUCT_TOP + 0.5))
inner.append(box(CX - 9.0, CX + 5.0, CB.YMax + 0.25, CB.YMax + 2.25, BAY_Z - 0.5, SZ + 18.0))
# the deck round the chute's mouth (the chute stays open: x L_IN..XP, y Y0..B_IN)
deck = box(L_IN - 0.5, R_IN + 0.5, F_IN - 0.5, B_IN + 0.5, DECK - 2.0, DECK)
inner.append(cad.cut(deck, box(L_IN, XP, Y0, B_IN, DECK - 3, DECK + 1)))
# the spine rib from the right wall onto the board's spine (0.2 mm off)
inner.append(box(BB.XMax + 0.2, R_IN + 0.5, Y0 + 27.0, Y0 + 33.0, ZB + 64.0, ZB + 94.0))
# the left guide wedge: steers the dice from the full chute into the gate
inner.append(prism_xy([(L_IN - 0.5, F_IN - 0.5), (AL, F_IN - 0.5), (L_IN - 0.5, F_IN + (AL - L_IN) * 0.8)],
                      FLOOR, BAY_Z - 1.0))
# the exit ramp: from the back wall down to the gate's sill
RAMP0 = 40.0
inner.append(prism_yz([(F_IN - 0.5, FLOOR), (B_IN + 0.5, FLOOR), (B_IN + 0.5, RAMP0), (F_IN - 0.5, FLOOR + 0.8)],
                      L_IN - 0.5, XP + 0.5))
# two 45 deg baffles across the chute: off the back wall down toward the
# front, off the bay wall down toward the back (each opening >= 28 mm)
ZB1 = DECK - 10.0
B1_END = 58.0
ZB2 = ZB1 - (B_IN - B1_END) - 12.0
B2_END = 62.0
inner.append(prism_yz([(B_IN + 0.5, ZB1), (B1_END, ZB1 - (B_IN + 0.5 - B1_END)),
                       (B1_END, ZB1 - (B_IN + 0.5 - B1_END) - 3.0), (B_IN + 0.5, ZB1 - 3.0)], L_IN - 0.5, XP + 0.5))
inner.append(prism_yz([(Y0 - 0.5, ZB2), (B2_END, ZB2 - (B2_END - Y0 + 0.5)),
                       (B2_END, ZB2 - (B2_END - Y0 + 0.5) - 3.0), (Y0 - 0.5, ZB2 - 3.0)], L_IN - 0.5, XP + 0.5))
keep = cad.fuse_one(keep, *inner)
tick("inside")

# ------------------------------------------------------------ openings
cuts = []
# the gate: a round-headed arch through the front wall and the talus
ARCH_TOP = FLOOR + ARCH_SPRING + ARCH_W / 2
cuts.append(prism_xz(arch_pts(AL, JAMB_X, FLOOR - 1, FLOOR + ARCH_SPRING), F0 - TALUS[0] - 1, F_IN + 0.2))
# the sensor: a pocket 0.3 mm round it in the jamb block, an OPEN window
# (14 x 8, along its emitter / receiver) through to the gate
cuts.append(box(TB.XMin, TB.XMax + 0.3, TB.YMin - 0.3, TB.YMax + 0.3, FLOOR - 1.0, TB.ZMax + 0.3))
tc = ((TB.YMin + TB.YMax) / 2, (TB.ZMin + TB.ZMax) / 2)
cuts.append(box(JAMB_X - 1, TB.XMin + 0.5, tc[0] - 5.7, tc[0] + 5.7, tc[1] - 5, tc[1] + 5))
# ...and its beam crosses the exit and leaves through a slot in the guide
# wedge and the left wall (a ToF needs an open line of sight: the light gate)
cuts.append(box(L0 - TALUS[0] - 1, AL, tc[0] - 5.7, tc[0] + 5.7, tc[1] - 5, tc[1] + 5))
# the sensor's ribbon runs forward out of the duct into the pocket
cuts.append(box(PLUG_X - 1.5, PLUG_X + 1.5, TB.YMax, Y0 + 0.5, tc[1] - 8, tc[1] + 8))
# the screen's window through the front wall (the lens fills the shield's)
WIN = (16.0, 28.0)
cuts.append(box(CX - WIN[0] / 2 - 0.5, CX + WIN[0] / 2 + 0.5, F0 - 1, F_IN + 0.1, SZ - WIN[1] / 2 - 0.5, SZ + WIN[1] / 2 + 0.5))
# USB-C at the back: a recess brings the wall to 1.2 mm in front of the mouth
ux, uz = P + 5.9, (UB.ZMin + UB.ZMax) / 2
cuts.append(box(ux - 9, ux + 9, B_IN + 1.2, B1 + TALUS[0] + 1, uz - 7, uz + 7))
keep = cad.cut(keep, cuts)
keep = cad.socket_opening(keep, usb, margin=1.5)
# the speaker: a round grille through the right wall (grilled on a plain
# plate, then the holes cut once - a grille on the whole keep measures
# every hole on it)
SPC = ((SB.YMin + SB.YMax) / 2, (SB.ZMin + SB.ZMax) / 2)
# (an iron grille insert filling a round hole: 133 holes in the keep's own
# wall made every point query on it slow - R990 MEASURED)
keep, grille = insert(keep, cyl(18.0, (R_IN - 0.5, SPC[0], SPC[1]), WALL + 1.0, (1, 0, 0)))
grille = cad.speaker_grille(grille, (R1, SPC[0], SPC[1]), (1, 0, 0), 34, ring_pitch=2.6, hole=1.6)
tick("openings")

# ------------------------------------------------------------ the base and tray
TX0, TX1 = L0 - TRAY_OUT, R1 + TRAY_OUT
TY0 = F0 - TALUS[0] - TRAY_L
base = cad.fuse_one(box(TX0, TX1, TY0, F0 - TALUS[0] + 0.5, FOOT_H, FLOOR),
                    box(L0 - TALUS[0] - 1, R1 + TALUS[0] + 1, F0 - TALUS[0], B1 + TALUS[0] + 1, FOOT_H, FLOOR))
# the tray walls: front and sides, and a return wall to the keep each side
TW = [box(TX0, TX1, TY0, TY0 + WALL, FLOOR - 0.5, FLOOR + TRAY_WALL_H),
      box(TX0, TX0 + WALL, TY0, F0 - TALUS[0], FLOOR - 0.5, FLOOR + TRAY_WALL_H),
      box(TX1 - WALL, TX1, TY0, F0 - TALUS[0], FLOOR - 0.5, FLOOR + TRAY_WALL_H)]
# the board stands on pads (0.1 mm under it), between fences 0.3 mm off its back
pads = [box(BB.XMin + 0.1, P - 0.2, y, y + 8, FLOOR - 0.5, BB.ZMin - 0.1) for y in (Y0 + 4, Y0 + 30)]
base = cad.fuse_one(base, *(TW + pads))
# four M2.5 screws up through the base into the pilasters
INSERT_D, PILOT_D = 3.6, 2.1
SCREWS = [(L0 + PIL[1], F0 + PIL[1]), (R1 - PIL[1], F0 + PIL[1]), (L0 + PIL[1], B1 - PIL[1]), (R1 - PIL[1], B1 - PIL[1])]
screws = []
for x, y in SCREWS:
    base = cad.countersink(base, (x, y, FOOT_H), "+Z", 2.9, 5.6, 90.0)
    keep = cad.hole(keep, (x, y, FLOOR), "+Z", PILOT_D, depth=8.5)
    screws.append(cad.screw("csk_phillips", SCREW, 12, at=(x, y, FOOT_H), axis="+Z"))
tick("base + screws")

# ------------------------------------------------------------ the face: banner, shield, lens
BAN_W = 50.0
BAN_TOP, BAN_BOT = DECK - 13.5, SZ - 44.0
BT = 1.6                          # the banner's thickness
banner = prism_xz([(CX - BAN_W / 2, BAN_TOP), (CX + BAN_W / 2, BAN_TOP), (CX + BAN_W / 2, BAN_BOT),
                   (CX, BAN_BOT + 12.0), (CX - BAN_W / 2, BAN_BOT)], F0 - BT, F0)
# the shield: a flat top, straight sides, a curved point under the window
SH_W, SH_T = 44.0, 2.4
sh_top, sh_mid, sh_pt = SZ + 21.0, SZ - 8.0, SZ - 36.0
sh = [(CX - SH_W / 2, sh_top), (CX + SH_W / 2, sh_top), (CX + SH_W / 2, sh_mid)]
sh += [(CX + SH_W / 2 * math.cos(math.radians(a)), sh_mid - (sh_mid - sh_pt) * math.sin(math.radians(a)))
       for a in (20, 40, 60, 80)]
sh += [(CX, sh_pt)]
sh += [(CX - SH_W / 2 * math.cos(math.radians(a)), sh_mid - (sh_mid - sh_pt) * math.sin(math.radians(a)))
       for a in (80, 60, 40, 20)]
sh += [(CX - SH_W / 2, sh_mid)]
shield = prism_xz(sh, F0 - BT - SH_T, F0 - BT)
# the smoked lens: fills the shield's and the banner's window, stops 0.4 mm
# short of the screen
lens_cut = box(CX - WIN[0] / 2, CX + WIN[0] / 2, F0 - BT - SH_T - 1, F0 + 0.01, SZ - WIN[1] / 2, SZ + WIN[1] / 2)
shield = cad.cut(shield, lens_cut)
banner = cad.cut(banner, lens_cut)
lens = box(CX - WIN[0] / 2, CX + WIN[0] / 2, F0 - BT - SH_T + 0.4, CB.YMin - 0.4, SZ - WIN[1] / 2, SZ + WIN[1] / 2)
# pegs: the banner's two into the wall, the shield's two through the banner
for px, pz in ((CX - 18, BAN_TOP - 8), (CX + 18, BAN_TOP - 8)):
    banner = cad.fuse_one(banner, cyl(1.5, (px, F0 - 0.5, pz), 3.5, (0, 1, 0)))
    keep = cad.cut(keep, cyl(1.65, (px, F0 - 0.5, pz), 4.2, (0, 1, 0)))
for px, pz in ((CX - 14, sh_top - 6), (CX + 14, sh_top - 6)):
    shield = cad.fuse_one(shield, cyl(1.5, (px, F0 - BT - 0.5, pz), BT + 3.5, (0, 1, 0)))
    banner = cad.cut(banner, cyl(1.65, (px, F0 - BT - 1, pz), BT + 2, (0, 1, 0)))
    keep = cad.cut(keep, cyl(1.65, (px, F0 - 0.5, pz), 4.2, (0, 1, 0)))
tick("stage A")


# === STAGE B: details ===
# ------------------------------------------------------------ the keep's stonework
# mortar courses and staggered joints on every face between the pilasters
# (one cut; none over the USB-C recess, where the wall is 1.2 mm)
GD = 0.8                                   # mortar groove: width and depth
mortar = []
zs = [FLOOR + TALUS[1] + COURSE * k for k in range(int((DECK - 8 - FLOOR - TALUS[1]) / COURSE) + 1)]
faces = [("y", F0, L0 + PIL[0] - PIL[1], R1 - PIL[0] + PIL[1], -1), ("y", B1, L0 + PIL[0] - PIL[1], R1 - PIL[0] + PIL[1], 1),
         ("x", L0, F0 + PIL[0] - PIL[1], B1 - PIL[0] + PIL[1], -1), ("x", R1, F0 + PIL[0] - PIL[1], B1 - PIL[0] + PIL[1], 1)]
for ax, w, a0, a1, sg in faces:
    o0, o1 = (w - 1.0, w + GD) if sg < 0 else (w - GD, w + 1.0)
    for k, z in enumerate(zs):
        segs = [(a0 + 1.0, a1 - 1.0)]
        if ax == "y" and sg > 0 and abs(z - uz) < 10:        # the USB-C recess
            segs = [(a0 + 1.0, ux - 10), (ux + 10, a1 - 1.0)]
        for s0, s1 in segs:
            mortar.append(box(s0, s1, o0, o1, z - GD / 2, z + GD / 2) if ax == "y"
                          else box(o0, o1, s0, s1, z - GD / 2, z + GD / 2))
        if k + 1 < len(zs):
            a = a0 + (8.0 if k % 2 else 20.0)
            while a < a1 - 6:
                if not (ax == "y" and sg > 0 and abs(a - ux) < 11 and abs(z - uz) < 14):
                    mortar.append(box(a - GD / 2, a + GD / 2, o0, o1, z, zs[k + 1]) if ax == "y"
                                  else box(o0, o1, a - GD / 2, a + GD / 2, z, zs[k + 1]))
                a += 24.0
# quoins: a joint round each corner pilaster at every course
for x, sx in ((L0, -1), (R1, 1)):
    for y, sy in ((F0, -1), (B1, 1)):
        xo = x + sx * PIL[1]
        yo = y + sy * PIL[1]
        xi, yi = x - sx * (PIL[0] - PIL[1]), y - sy * (PIL[0] - PIL[1])
        for z in zs:
            mortar.append(box(xi, xo + sx * 1.0, yo - sy * GD, yo + sy * 1.0, z - GD / 2, z + GD / 2))
            mortar.append(box(xo - sx * GD, xo + sx * 1.0, yi, yo + sy * 1.0, z - GD / 2, z + GD / 2))
keep = cad.cut(keep, mortar)
tick("stonework")
# the corbel table under the parapet: a block every 12 mm on every face
corbels = []
for ax, w, a0, a1, sg in faces:
    a = a0 - PIL[1] + 4.0
    while a < a1 + PIL[1] - 4.0:
        lo, hi = (w - CORBEL, w + 0.5) if sg < 0 else (w - 0.5, w + CORBEL)
        corbels.append(box(a - 2.0, a + 2.0, lo, hi, DECK - 12.0, DECK - 5.5) if ax == "y"
                       else box(lo, hi, a - 2.0, a + 2.0, DECK - 12.0, DECK - 5.5))
        a += 12.0
keep = cad.fuse_one(keep, *corbels)
# merlons and crenels round the parapet (a merlon on every corner)
cren = []
for ax, lo_, hi_ in (("x", L0 - CORBEL, R1 + CORBEL), ("y", F0 - CORBEL, B1 + CORBEL)):
    span = hi_ - lo_
    n = max(2, int(round((span - MERLON[0]) / (2 * MERLON[0]))))
    pitch = (span - MERLON[0]) / n
    for i_ in range(n):
        c = lo_ + MERLON[0] + pitch * i_ + (pitch - MERLON[0]) / 2
        w_ = pitch - MERLON[0]
        if ax == "x":
            cren.append(box(c - w_ / 2 + MERLON[0] / 2 - MERLON[0] / 2, c + w_ / 2, F0 - CORBEL - 1, B1 + CORBEL + 1,
                            H - MERLON[1], H + 1))
        else:
            cren.append(box(L0 - CORBEL - 1, R1 + CORBEL + 1, c - w_ / 2, c + w_ / 2, H - MERLON[1], H + 1))
keep = cad.cut(keep, cren)
tick("parapet")
# cross-shaped arrow loops: two on the left face, two on the back, two on
# the front beside the banner (each through one wall only)
loops = []


def loop(ax, w, a, z, sg):
    o0, o1 = (w - 1.0, w + WALL + 0.5) if sg < 0 else (w - WALL - 0.5, w + 1.0)
    if ax == "x":
        return [box(o0, o1, a - 1.6, a + 1.6, z - 12, z + 12), box(o0, o1, a - 5.5, a + 5.5, z + 2.5, z + 5.5)]
    return [box(a - 1.6, a + 1.6, o0, o1, z - 12, z + 12), box(a - 5.5, a + 5.5, o0, o1, z + 2.5, z + 5.5)]


LOOP_Z = (DECK - 40.0, DECK - 85.0)
for z in LOOP_Z:
    loops += loop("x", L0, (Y0 + B_IN) / 2, z, -1)
    loops += loop("y", B1, CX - 22.0, z, 1)
loops += loop("y", F0, (L0 + PIL[0] + CX - BAN_W / 2) / 2, DECK - 40.0, -1)
loops += loop("y", F0, (R1 - PIL[0] + CX + BAN_W / 2) / 2, DECK - 40.0, -1)
keep = cad.cut(keep, loops)
# the gate: a voussoir ring 1.4 mm proud with radial joints, a keystone,
# and impost blocks at the springing
RA = ARCH_W / 2
ring = prism_xz(arch_pts(AL - 6.0, JAMB_X + 6.0, FLOOR + ARCH_SPRING, FLOOR + ARCH_SPRING), F0 - 1.4, F0 + 0.5)
ring = cad.cut(ring, prism_xz(arch_pts(AL, JAMB_X, FLOOR + ARCH_SPRING - 1, FLOOR + ARCH_SPRING), F0 - 2, F0 + 1))
ring = cad.cut(ring, [prism_xz([(CX + (RA - 0.5) * math.cos(math.radians(a - 0.8)), FLOOR + ARCH_SPRING + (RA - 0.5) * math.sin(math.radians(a - 0.8))),
                                (CX + (RA + 7) * math.cos(math.radians(a - 0.8)), FLOOR + ARCH_SPRING + (RA + 7) * math.sin(math.radians(a - 0.8))),
                                (CX + (RA + 7) * math.cos(math.radians(a + 0.8)), FLOOR + ARCH_SPRING + (RA + 7) * math.sin(math.radians(a + 0.8))),
                                (CX + (RA - 0.5) * math.cos(math.radians(a + 0.8)), FLOOR + ARCH_SPRING + (RA - 0.5) * math.sin(math.radians(a + 0.8)))],
                               F0 - 2, F0 - 0.6) for a in (22.5, 45, 67.5, 112.5, 135, 157.5)])
key_ = prism_xz([(CX - 3.5, ARCH_TOP - 1), (CX + 3.5, ARCH_TOP - 1), (CX + 5.0, ARCH_TOP + 9), (CX - 5.0, ARCH_TOP + 9)],
                F0 - 2.4, F0 + 0.5)
imposts = [box(x0, x1, F0 - 1.8, F0 + 0.5, FLOOR + ARCH_SPRING - 3.0, FLOOR + ARCH_SPRING)
           for x0, x1 in ((AL - 7.5, AL), (JAMB_X, JAMB_X + 7.5))]
keep = cad.fuse_one(keep, ring, key_, *imposts)
# the portcullis grooves in the gate's jambs and head (2.0 mm, the
# portcullis bears on the head's top face)
PY = (F0 + 1.2, F0 + 3.2)
PZ0 = FLOOR + ARCH_SPRING                  # the spikes' tips (the dice pass under)
PTOP = ARCH_TOP + 12.0                     # the portcullis's top, in a slot over the gate's head
groove = cad.fuse_one(prism_xz(arch_pts(AL - 2.0, JAMB_X + 2.0, FLOOR - 1.0, FLOOR + ARCH_SPRING), PY[0], PY[1]),
                      box(AL - 2.0, JAMB_X + 2.0, PY[0], PY[1], FLOOR + ARCH_SPRING, PTOP))
keep = cad.cut(keep, groove)
# the rose window round the speaker grille: a stone frame ring, 1.5 proud
rose = cad.cut(cyl(22.5, (R1 - 0.5, SPC[0], SPC[1]), 2.0, (1, 0, 0)), cyl(18.6, (R1 - 1, SPC[0], SPC[1]), 3.0, (1, 0, 0)))
keep = cad.fuse_one(keep, rose)
# the pennant's socket: a boss under the deck at the front-left corner
FPX, FPY = L_IN + 8.0, F_IN + 9.0
keep = cad.fuse_one(keep, cyl(4.0, (FPX, FPY, DECK - 10.0), 8.5))
keep = cad.cut(keep, cyl(1.5, (FPX, FPY, DECK - 8.0), 9.0))
tick("keep details")

# ------------------------------------------------------------ the portcullis (wood)
grid = box(AL - 1.9, JAMB_X + 1.9, PY[0] + 0.1, PY[1] - 0.1, PZ0 + 4.0, PTOP)
open_ = []
nb = int(round((ARCH_W + 3.8) / 6.0))
pb = (ARCH_W + 3.8) / nb
for i_ in range(nb):                                          # between the vertical bars
    x0 = AL - 1.9 + pb * i_ + 1.2
    open_.append(box(x0, x0 + pb - 2.4, PY[0] - 1, PY[1] + 1, PZ0 + 4.0 + 2.4, ARCH_TOP - 1.0))
grid = cad.cut(grid, open_)
# horizontal rails across the openings (fused back), and a spike under each bar
rails = [box(AL - 1.9, JAMB_X + 1.9, PY[0] + 0.1, PY[1] - 0.1, z, z + 2.2)
         for z in (PZ0 + 4.0 + 5.5, PZ0 + 4.0 + 11.0)]
spikes = []
for i_ in range(nb + 1):
    x = AL - 1.9 + pb * i_ + (1.2 if i_ < nb else -1.2)
    if AL + 1.0 < x < JAMB_X - 1.0:
        spikes.append(prism_xz([(x - 1.2, PZ0 + 4.5), (x + 1.2, PZ0 + 4.5), (x + 0.6, PZ0), (x - 0.6, PZ0)],
                               PY[0] + 0.1, PY[1] - 0.1))
portcullis = cad.fuse_one(grid, *(rails + spikes))
tick("portcullis")

# ------------------------------------------------------------ the banner and the shield's rim
banner = cad.fuse_one(banner, cyl(1.8, (CX - BAN_W / 2 - 2.0, F0 - 1.9, BAN_TOP - 0.6), BAN_W + 4.0, (1, 0, 0)))
try:
    inner_w = Part.Face(Part.makePolygon([V(x, F0 - BT - SH_T, z) for x, z in sh + sh[:1]])).makeOffset2D(-1.6)
    rim = cad.cut(prism_xz(sh, F0 - BT - SH_T - 0.9, F0 - BT - SH_T + 0.5),
                  inner_w.extrude(V(0, -3, 0)).translated(V(0, 1.5, 0)))
    shield = cad.fuse_one(shield, rim)
except Exception as exc:                                # noqa: BLE001
    print("NOTE shield rim skipped: %s" % exc)
bez = cad.cut(box(CX - WIN[0] / 2 - 2.0, CX + WIN[0] / 2 + 2.0, F0 - BT - SH_T - 0.9, F0 - BT - SH_T + 0.5,
                  SZ - WIN[1] / 2 - 2.0, SZ + WIN[1] / 2 + 2.0),
              box(CX - WIN[0] / 2, CX + WIN[0] / 2, F0 - BT - SH_T - 2, F0 - BT, SZ - WIN[1] / 2, SZ + WIN[1] / 2))
shield = cad.fuse_one(shield, bez)
tick("banner + shield")

# ------------------------------------------------------------ the tray
TOPZ = FLOOR + TRAY_WALL_H
# round corner turrets at the tray's front corners, crenellated
TUR_R = TURRET_R
TTOP = TOPZ + 14.0
turrets = []
for tx in (TX0 + WALL / 2, TX1 - WALL / 2):
    t_ = cyl(TUR_R, (tx, TY0 + WALL / 2, FOOT_H), TTOP - FOOT_H)
    t_ = cad.fuse_one(t_, cyl(TUR_R + 1.5, (tx, TY0 + WALL / 2, TTOP - 7.0), 7.0))
    t_ = cad.cut(t_, [cyl(TUR_R - 2.5, (tx, TY0 + WALL / 2, TTOP - 4.0), 5.0)] +
                 [box(tx - 2.5, tx + 2.5, TY0 + WALL / 2, TY0 + WALL / 2 + TUR_R + 3, TTOP - 4.0, TTOP + 1)
                  .rotated(V(tx, TY0 + WALL / 2, 0), V(0, 0, 1), a) for a in (0, 90, 180, 270)])
    turrets.append(t_)
base = cad.fuse_one(base, *turrets)
# the felt floor: a pad in a 1 mm recess
FELT = (TX0 + WALL + 0.3, TX1 - WALL - 0.3, TY0 + WALL + 0.3, F0 - TALUS[0] - 1.0)
# (its front corners curve round the turrets, 0.3 mm off them)
tcl = [cyl(TUR_R + 0.3, (tx, TY0 + WALL / 2, FLOOR - 2.0), 4.0) for tx in (TX0 + WALL / 2, TX1 - WALL / 2)]
base = cad.cut(base, cad.cut(box(FELT[0], FELT[1], FELT[2], FELT[3], FLOOR - 1.0, FLOOR + 1), tcl))
felt = cad.cut(box(FELT[0], FELT[1], FELT[2], FELT[3], FLOOR - 1.0, FLOOR), tcl)
# stone courses on the tray walls' outer faces
tm = [box(TX0 + TUR_R + 1, TX1 - TUR_R - 1, TY0 - 1, TY0 + GD, z - GD / 2, z + GD / 2) for z in (FLOOR + 7.5, FLOOR + 15.0)]
tm += [box(o0, o1, TY0 + TUR_R + 1, F0 - TALUS[0] - 1, z - GD / 2, z + GD / 2)
       for o0, o1 in ((TX0 - 1, TX0 + GD), (TX1 - GD, TX1 + 1)) for z in (FLOOR + 7.5, FLOOR + 15.0)]
base = cad.cut(base, tm)
base = cad.text(base, "ATECH", ((TX0 + TX1) / 2, TY0, FLOOR + 11.25), (0, -1, 0), 5.0, depth=0.5, mode="deboss")
# the wood cap rail on the tray walls (three pegs into the wall top)
RAIL_H = 3.0
rails_ = [box(TX0 + TUR_R - 1, TX1 - TUR_R + 1, TY0 - 0.8, TY0 + WALL + 0.8, TOPZ, TOPZ + RAIL_H)]
rails_ += [box(x0 - 0.8, x0 + WALL + 0.8, TY0 + TUR_R - 1, F0 - TALUS[0], TOPZ, TOPZ + RAIL_H) for x0 in (TX0, TX1 - WALL)]
pegs = [((TX0 + TX1) / 2, TY0 + WALL / 2), (TX0 + WALL / 2, (TY0 + F0) / 2), (TX1 - WALL / 2, (TY0 + F0) / 2)]
for k, (px, py) in enumerate(pegs):
    r_ = cad.fuse_one(cad.cut(rails_[k], turrets), cyl(1.0, (px, py, TOPZ - 3.0), 3.5))
    base = cad.cut(base, cyl(1.12, (px, py, TOPZ - 3.5), 4.0))
    rails_[k] = cad.soften(r_, 1.0, [e for e in r_.Edges if e.BoundBox.ZMin > TOPZ + RAIL_H - 0.01])
# rubber feet in shallow pockets under the base
FEET = [(TX0 + 14, TY0 + 14), (TX1 - 14, TY0 + 14), (L0 + 10, B1 - 10), (R1 - 10, B1 - 10)]
base = cad.cut(base, [cyl(5.1, (x, y, FOOT_H - 1.0), 2.5) for x, y in FEET])
feet = [cad.foot(10, FOOT_H + 1.5, style="dome", at=(x, y, FOOT_H + 1.5)) for x, y in FEET]
tick("tray")

# ------------------------------------------------------------ the pennant
FLAG_T = H + 42.0
pole = cyl(1.5, (FPX, FPY, DECK - 8.0), FLAG_T - (DECK - 8.0))
pole = cad.fuse_one(pole, Part.makeSphere(2.6, V(FPX, FPY, FLAG_T)))
flag = prism_yz([(FPY, FLAG_T - 3.0), (FPY - 40.0, FLAG_T - 13.0), (FPY - 34.0, FLAG_T - 15.5), (FPY - 40.0, FLAG_T - 18.0),
                 (FPY, FLAG_T - 26.0)], FPX - 0.7, FPX + 0.7)
flag = cad.cut(cad.fuse_one(flag, cyl(2.7, (FPX, FPY, FLAG_T - 26.0), 23.0)), cyl(1.5, (FPX, FPY, FLAG_T - 27.0), 25.0))

# ------------------------------------------------------------ two dice on the felt (sunk 0.3 mm in it)
D6 = 16.0
d6 = cad.rounded_box(D6, D6, D6, 2.4, at=(-D6 / 2, -D6 / 2, 0), edges="vertical")
d6 = cad.soften(d6, 2.0, [e for e in d6.Edges if abs(e.BoundBox.ZLength) < 0.01])
PIPS = {(0, 0, 1): [(0, 0)], (0, -1, 0): [(-4, -4), (4, 4)], (1, 0, 0): [(-4, -4), (0, 0), (4, 4)],
        (-1, 0, 0): [(-4, -4), (4, -4), (-4, 4), (4, 4)], (0, 1, 0): [(-4, -4), (4, -4), (0, 0), (-4, 4), (4, 4)],
        (0, 0, -1): [(-4, -4), (4, -4), (-4, 0), (4, 0), (-4, 4), (4, 4)]}
pips = []
for (nx, ny, nz), uv in PIPS.items():
    for u, v_ in uv:
        if nz:
            c = (u, v_, D6 / 2 + nz * (D6 / 2 + 0.9))
        elif nx:
            c = (nx * (D6 / 2 + 0.9), u, D6 / 2 + v_)
        else:
            c = (u, ny * (D6 / 2 + 0.9), D6 / 2 + v_)
        pips.append(Part.makeSphere(1.7, V(*c)))
d6 = cad.cut(d6, pips)
d6.rotate(V(0, 0, 0), V(0, 0, 1), 24.0)
d6.translate(V(CX - 24.0, TY0 + WALL + 52.0, FLOOR - 0.3))
# a d20: an icosahedron turned onto one face
PHI = (1 + 5 ** 0.5) / 2
IV = [V(0, a, b * PHI) for a in (-1, 1) for b in (-1, 1)] + [V(a, b * PHI, 0) for a in (-1, 1) for b in (-1, 1)] + \
     [V(a * PHI, 0, b) for a in (-1, 1) for b in (-1, 1)]
EDGE2 = 4.0 + 1e-6
tri = [(i, j, k) for i in range(12) for j in range(i + 1, 12) for k in range(j + 1, 12)
       if all((IV[a] - IV[b]).Length ** 2 < EDGE2 for a, b in ((i, j), (j, k), (i, k)))]
d20 = Part.Solid(Part.Shell([Part.Face(Part.makePolygon([IV[a], IV[b], IV[c], IV[a]])) for a, b, c in tri]))
d20.scale(11.0 / 2.0)                         # 22 mm edge to edge... edge 11 mm
fa = tri[0]
n = (IV[fa[0]] + IV[fa[1]] + IV[fa[2]])
n.normalize()
ax = n.cross(V(0, 0, -1))
d20.rotate(V(0, 0, 0), ax, math.degrees(math.acos(max(-1.0, min(1.0, n.dot(V(0, 0, -1)))))))
d20.translate(V(CX + 20.0, TY0 + WALL + 40.0, FLOOR - 0.3 - d20.BoundBox.ZMin))
tick("stage B")
# ------------------------------------------------------------ parts
def part(name, shape, colour=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = cad.color(COLOURS[colour or name])
    return o


for nm, sh_ in (("Base", base), ("Tower", keep), ("Banner", banner), ("Shield", shield),
               ("Portcullis", portcullis), ("Rim_Front", rails_[0]), ("Rim_Left", rails_[1]),
               ("Rim_Right", rails_[2]), ("Felt", felt), ("Flag_Pole", pole),
               ("Pennant", flag), ("Rose_Grille", grille), ("Die_D6", d6), ("Die_D20", d20)):
    part(nm, sh_, "Tray_Rim" if nm.startswith("Rim_") else None)
for i, f in enumerate(feet):
    part("Foot_%d" % (i + 1), f, "Foot")
o = part("Screen_Lens", lens)
o.ViewObject.Transparency = cad.transparency("smoked")
for i, s in enumerate(screws):
    part("Screw_%d" % (i + 1), s, "Screw")
print("SIZE", cad.measure(Part.makeCompound([base, keep]))["size"])
print("TOTAL %.1f s" % (time.time() - T0))
