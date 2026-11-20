"""Example: "a desk game where you bop light-up moles before they hide" - a grassy tabletop reaction game: four glowing moles to bop, a scoreboard sign, a mallet.

fork this file for a reaction game / bop-the-mole / tap-the-light game (a
hit-the-target toy, a reflex trainer, a light-up button game); change PARAMETERS and the outlines.
ARCHETYPE: reaction game

How it is built (R1030):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board FLAT and turned ACROSS (ports 1-6 along the front row, 9-14
    along the back row, 7 at the left end). PORT PLAN (ports 8 and 12 are
    reserved by the SDK and stay empty): four moles in a 2 x 2 grid 40 mm
    apart - buttons 1 + 3 (front) and 9 + 11 (back) - and only TWO lights,
    2 and 10, each seated BETWEEN its row's two moles: a light is a 3 x 3
    NeoPixel grid, so its left column lights the left mole and its right
    column the right one (setColumn). Each mole is a frosted cap whose
    skirt drops through a hole in its burrow ring, with a light fin hanging
    over its own LED column, two snap barbs under the deck, a plunger to
    its button and a 0.8 mm travel to the stop on the ring. Button 6 is
    the START key; USB-C 7 sits in a pocket + liner in the left flank. The
    speaker (4, 5) is CABLED straight out of the front edge to the
    front-right (face up, ribbons flat in their own plane) under a round
    grille; the screen (13, 14) is CABLED straight out of the back edge -
    a flat run back, a quarter turn up, a straight rise up a hollow neck -
    into the yellow scoreboard sign (no twist, no crossing). The mound is
    the convex hull of circles round the moles, the neck's foot, the
    holster, the START key and the grille, drafted 16 deg (planes and
    cones only - a lofted draft and split()'s own lip came back with
    volumes that did not add up, so every hole check failed), hollowed
    with its own core, split into the fixed Base (board pads, end fences,
    speaker cradle, a lip built from the same outlines) and the Top; five
    M2 screws from below into heat-set insert bosses; a rib from the deck
    onto the board's spine. The neck is part of the Top; the yellow sign
    sits on it on two pins, the smoked glass in a black bezel through its
    front. ONE mole is built (its face's pockets cut) and copied.
  * STAGE B - details: the mole faces (pink noses, black bead eyes in the
    pockets), the red MOLE BOP logo inlaid in the sign, the
    mallet pegged into its holster, grass tufts, legends, the parting-line
    reveal, vents and a model mark under the base, rubber feet.
DETAILS (visible, 34): 1 a grassy green mound with a 16 deg draft; 2 soft
rolled top edge; 3 a plan that hugs its contents (hull of circles); 4 four
cute frosted mole heads that glow; 5 pink noses; 6 black bead eyes; 7 dark
soil burrow rings raised round each mole; 8 each mole standing 0.8 mm over
its ring (its travel to the stop); 9 the yellow scoreboard sign on a
hollow neck; 10 rounded sign corners; 11 smoked score window in a raised
black bezel; 12 the raised red MOLE BOP logo on its underline swoosh; 13 the round
speaker grille (yellow, 133 holes) for the boing; 14 a red START key with
"GO"; 15 a soft red mallet with a wooden handle; 16 its holster boss;
17 eight grass tufts; 18 "ATECH" and "BOP!" legends on the deck; 19 USB-C pocket
with a liner in the left flank; 20 parting-line reveal; 21 slot vents
under the base; 22 "ATECH MB-4" under the base; 23 five countersunk screws
from below; 24 five rubber feet. Inside: 25 two snap barbs on each mole's
skirt; 26 a plunger to each button; 27 a light fin on each mole over its
LED column; 28 board pads and end fences; 29 speaker cradle ribs and a pad;
30 a rib onto the board's spine; 31 screen ribs in the sign and two pins
keying it to the neck; 32 the screen ribbons' flat run and rise up the
neck; 33 five bosses with heat-set insert sleeves; 34 the base / top lip.
Materials: grass-green top, forest-green base, dark soil burrow rings,
frosted cocoa moles with pink noses and black eyes, toy-yellow sign with
a red logo, smoked window in a black bezel, yellow grille, red START key,
red mallet head on a wood handle, chrome screws, rubber feet.
MEASURED (R1030, 2026-11-20): ./check CHECK PASS, run_seconds 15 s, wall 56 s; every RESTYLE end CHECK PASS.
"""
import math
import os
import time
import FreeCAD as App
import Part
import atech_ports as ap
import atech_cad as cad
from FreeCAD import Vector, Placement, Rotation
V = Vector
T0 = time.time()

INTENT = {"board": "flat", "fitted_after": [
    "Top", "Burrow_1", "Burrow_2", "Burrow_3", "Burrow_4", "Mole_1", "Mole_2", "Mole_3", "Mole_4",
    "Start_Key", "Grille", "Sign", "Bezel", "Glass",
    "Nose_1", "Nose_2", "Nose_3", "Nose_4", "Eye_1L", "Eye_1R", "Eye_2L", "Eye_2R",
    "Eye_3L", "Eye_3R", "Eye_4L", "Eye_4R",
    "Title",
    "Mallet_Handle", "Mallet_Head",
    "Rubber_1", "Rubber_2", "Rubber_3", "Rubber_4", "Rubber_5",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4", "Screw_5"],
    # each mole presses its own button through its burrow (a declared cover);
    # the moles are frosted, so the lights between them shine through
    "covers": {"Mole_1": "button_p1", "Mole_2": "button_p3", "Mole_3": "button_p9", "Mole_4": "button_p11",
               "Start_Key": "button_p6"}}
REVIEW_CLOSEUPS = ["Mole_1", "Bezel", "Mallet_Head"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them and the measured hardware.
SIDE = 12.0        # RESTYLE 10.2..13.8 width: the mound past the moles' burrows (x, left and back)
FRONT = 12.0       # RESTYLE 10.2..13.8 length: the mound in front of the speaker grille (y)
MOLE_H = 18.0      # RESTYLE 15.3..20.7 height: each mole's head above its stop
SIGN_H = 32.0      # RESTYLE 27.2..36.8 height: the sign's bottom edge above the deck
CORNER = 18.0      # RESTYLE 15.3..20.7 radius: the sign's foot and the right-hand plan circles
WALL = 2.0         # RESTYLE 1.7..2.3 wall
# end RESTYLE
RUB = 1.5                        # the rubber feet: the body's underside over the desk
TAPER = 16.0                     # the mound's draft (deg): its sides lean in
Z_PCB = RUB + WALL + 4.0         # the PCB top (pads 1.5 mm under the board)
ZI = Z_PCB + 20.2 + 1.0          # the deck's inner face: 1 mm air over the cabled speaker
Z_TOP = ZI + WALL                # the deck
EDGE_R, FOOT_R = 2.0 * WALL, 1.2  # the rolled top edge (a sharp core keeps >= t/2 there), the foot
HOLE_R, BUR_R, RIM_H = 15.5, 18.6, 2.5    # each burrow's bore, outer radius, rim over the deck
SK_R, HEAD_R = 15.2, 17.0        # each mole's skirt (through the bore) and head
TRAVEL = 0.8                     # each mole's travel to its stop (the gap over its rim)
DOME_R, KNUCKLE, HEAD_T = 19.0, 9.0, 2.2   # the mole's crown, its rolled shoulder, its shell
SCR_FACE = 56.0                  # the screen's face (y): the sign stands behind the back moles
SIGN_W, SIGN_HT, SIGN_R = 104.0, 56.0, 8.0
R1 = 5.0                         # the screen ribbons' quarter turn up
GRILLE_D = 34.0
START_D = 20.0
MALLET = {"at": (-60.0, 48.0), "boss_r": 8.0, "boss_h": 6.0, "peg_r": 3.9, "bore_r": 4.05,
          "handle_r": 6.0, "handle_l": 78.0, "head_r": 15.0, "head_l": 52.0}
COLOURS = {"Top": "#58b947", "Base": "#2f6d33", "Burrow": "#5a3920", "Mole": "#a0704a",
           "Nose": "#ff8fa6", "Eye": "matte_black", "Start_Key": "signal_red", "Grille": "toy_yellow",
           "Sign": "toy_yellow", "Bezel": "matte_black", "Glass": "smoked", "Title": "#d8262c",
           "Mallet_Head": "signal_red", "Mallet_Handle": "wood", "Rubber": "rubber", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
FLAT = Rotation(Vector(1, 0, 0), 90)
ACROSS = Rotation(Vector(0, 0, 1), 90).multiply(FLAT)      # long side along X, port 1 front-left
board = ap.board_object(doc)
board.Placement = Placement(V(), ACROSS)
_b = ap.bbox(board)
board.Placement = Placement(V(-(_b.XMin + _b.XMax) / 2, -(_b.YMin + _b.YMax) / 2, Z_PCB - 2.5 - _b.ZMin), ACROSS)
BB = ap.bbox(board)
mole_btn = [ap.seat(doc, "button", n) for n in (1, 3, 9, 11)]   # front-left, front-right, back-left, back-right
lights = [ap.seat(doc, "light", n) for n in (2, 10)]             # each between its row's two moles
start = ap.seat(doc, "button", 6)                                # the START key, front right
usb = ap.seat(doc, "usbc", 7)                                    # left end, mouth -X
# the speaker straight out of the front edge, pins toward the board (face x
# cable = -X: the front row's plug width, no twist), at the board's height
SPK_C = (BB.XMin + 80.0, BB.YMin - 50.0, Z_PCB + 10.1)
spk, spk_ribs = ap.cable(doc, "speaker", (4, 5), ap.module_placement("speaker", SPK_C, face="+Z", cable="+Y"))
# the screen in the sign: a flat run back out of the back edge, a quarter
# turn up, a straight rise to its socket (face x cable = +X: no twist)
PLUG_Y, PLUG_Z = BB.YMax + 3.25, BB.ZMin + 3.77          # each back-edge plug's lead end: MEASURED (mini_arcade)
SCR_C = (BB.XMin + 100.0, SCR_FACE + 4.82, Z_TOP + SIGN_H + 21.0)
SCR_LEAD = [(SCR_C[0] + dx, SCR_C[1] + 3.55, SCR_C[2] - 12.89) for dx in (-10, 10)]   # MEASURED (mini_arcade)
RUN = SCR_LEAD[0][1] - R1 - PLUG_Y


def screen_route(xp, lead):
    pts = [(xp, PLUG_Y + RUN * i / 4.0, PLUG_Z) for i in range(1, 5)]
    for i in range(1, 7):
        a = math.radians(-90 + 90 * i / 6.0)
        pts.append((xp, PLUG_Y + RUN + R1 * math.cos(a), PLUG_Z + R1 + R1 * math.sin(a)))
    z0, z1 = PLUG_Z + R1, lead[2] - 0.15
    n = max(3, int((z1 - z0) / 6.0))
    pts += [(xp, lead[1], z0 + (z1 - z0) * i / n) for i in range(1, n + 1)]
    return pts


scr, scr_ribs = ap.cable(doc, "screen", (13, 14), ap.module_placement("screen", SCR_C, face="-Y", cable="-Z"),
                         via={13: screen_route(BB.XMin + 90.0, SCR_LEAD[0]),
                              14: screen_route(BB.XMin + 110.0, SCR_LEAD[1])})
tick("hardware")


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def ring(r0, r1, c, z0, z1):
    return cad.cut(cyl(r1, (c[0], c[1], z0), z1 - z0), cyl(r0, (c[0], c[1], z0 - 1), z1 - z0 + 2))


def centre(b):
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


def zbox(w, d, r, cx, cy, z0, z1):
    return cad.rounded_box(w, d, z1 - z0, r, at=(cx - w / 2, cy - d / 2, z0))


MB = [ap.bbox(m) for m in mole_btn]
LB = [ap.bbox(m) for m in lights]
STB, UB, SB, SCB = ap.bbox(start), ap.bbox(usb), ap.bbox(spk), ap.bbox(scr)
MC = [centre(b)[:2] for b in MB]                 # the moles' axes = their buttons'
GX, GY = centre(SB)[:2]                          # the speaker grille's centre
SX = centre(SCB)[0]                              # the sign's centre line = the screen's

# the sign's neck (its foot sets the plan's back)
Y_SF = SCR_FACE - 0.4 - WALL                  # the sign's and the neck's front face
Y_SI = SCR_FACE + 10.5                        # their inner back face (behind the rise)
Y_SB = Y_SI + WALL
NI, NW, FLS = 22.0, 5.0, 4.0                  # the neck's inner half width (the screen is 39.5
                                              # long), its side walls, the sign's floor

# ------------------------------------------------------------ the plan
# the mound's top outline: the convex hull of circles round what it carries
# (every edge a line or an arc - the draft offsets them into planes and cones)
CIRCLES = [
    (MC[0][0], MC[0][1], BUR_R + SIDE),                   # front-left mole
    (GX, GY, GRILLE_D / 2 + FRONT + 4.0),                  # the grille, front right (its circle holds
                                                           # the speaker's corners, 28.3 mm out)
    (centre(STB)[0] + 22.0, centre(STB)[1] - 4.0, CORNER + 6.0),   # right of the START key
    (SX + NI + NW - 6.5, Y_SB - 6.5, CORNER),             # the neck's foot, right
    (SX - NI - NW + 6.5, Y_SB - 6.5, CORNER),             # the neck's foot, left
    (MALLET["at"][0], MALLET["at"][1], MALLET["boss_r"] + SIDE - 2.0),   # the mallet's holster
    (MC[2][0], MC[2][1], BUR_R + SIDE),                   # back-left mole
]


def hull_wire(circles, grow, z):
    """The convex hull of the circles (centre x, y, radius + grow) at z as
    one closed wire of tangent lines and arcs; circles listed CCW."""
    cs = [(x, y, r + grow) for x, y, r in circles]
    n = len(cs)
    tang = []
    for i in range(n):
        x1, y1, r1 = cs[i]
        x2, y2, r2 = cs[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        c = (r1 - r2) / L
        s = math.sqrt(1 - c * c)
        nx, ny = c * ux + s * uy, c * uy - s * ux          # the outward normal (right of the travel)
        tang.append(((x1 + r1 * nx, y1 + r1 * ny), (x2 + r2 * nx, y2 + r2 * ny)))
    edges = []
    for i in range(n):
        a, b = tang[i]
        edges.append(Part.LineSegment(V(a[0], a[1], z), V(b[0], b[1], z)).toShape())
        x, y, r = cs[(i + 1) % n]
        p0, p1 = tang[i][1], tang[(i + 1) % n][0]
        a0 = math.atan2(p0[1] - y, p0[0] - x)
        a1 = math.atan2(p1[1] - y, p1[0] - x)
        while a1 < a0:
            a1 += 2 * math.pi
        if a1 - a0 > 1e-4:
            am = (a0 + a1) / 2
            edges.append(Part.Arc(V(p0[0], p0[1], z), V(x + r * math.cos(am), y + r * math.sin(am), z),
                                  V(p1[0], p1[1], z)).toShape())
    return Part.Wire(Part.__sortEdges__(edges))


TAN_T = math.tan(math.radians(TAPER))


def slab(t):
    """The mound inset t: the hull at its foot, drafted up to the deck
    (the core keeps sharp edges: no concave rounds inside)."""
    z0, z1 = RUB + t, Z_TOP - t
    grow = (Z_TOP - z0) * TAN_T - (t / math.cos(math.radians(TAPER)) if t else 0.0)
    w = hull_wire(CIRCLES, grow, z0)
    return cad.extrude_profile(Part.Face(w), z1 - z0, taper_deg=TAPER)


def inside(x, y, z=None, t=0.0):
    """True when (x, y) lies at least t inside the top outline."""
    f = Part.Face(hull_wire(CIRCLES, -t, 0))
    return f.isInside(V(x, y, 0), 1e-6, True)


outer = slab(0.0)
outer = cad.soften(outer, EDGE_R, [e for e in outer.Edges if e.BoundBox.ZMin > Z_TOP - 1e-3])
outer = cad.soften(outer, FOOT_R, [e for e in outer.Edges if e.BoundBox.ZMax < RUB + 1e-3])
body = cad.hollow(outer, WALL, core=lambda t: slab(t))
skin = slab(0.5)                              # clips ribs and liners 0.5 mm under the outer skin
tick("body")
SPLIT = Z_PCB - 2.0                           # in the cavity: the lip's top stays under the PCB
base, top = cad.split(body, "Z", at=SPLIT)
# the lip: the inner 40 % of the wall (and 0.6 mm into the cavity, so lip
# and skin both stay >= 0.8 mm at WALL 1.7) standing LIP over the split on
# the base, keyed into a groove 0.2 mm larger in the top - built from the same
# drafted outlines (planes and cones: split's own lip came back as swept
# surfaces whose volumes would not add up)
LIP = 1.5


def band(z0, z1):
    return box(-400, 400, -400, 400, z0, z1)


lip = cad.cut(slab(0.6 * WALL).common(band(SPLIT - 0.5, SPLIT + LIP)), slab(WALL + 0.6))
top = cad.cut(top, slab(0.6 * WALL - 0.2).common(band(SPLIT - 1.0, SPLIT + LIP + 0.2)))
base = cad.fuse_one(base, lip)
tick("split")
FLOOR = RUB + WALL                            # the base's inner floor

# the fixed base holds the board: pads 0.1 mm under it, fences off its
# ends (under port 7's slide path), a cradle round the cabled speaker (ribs
# 0.25 mm off its left and right sides, a pad under it)
UNDER = BB.ZMin - 0.1
pads = [box(x - 4, x + 4, y - 4, y + 4, FLOOR - 0.5, UNDER)
        for x in (BB.XMin + 10, 0.0, BB.XMax - 10) for y in (-22.0, 22.0)]
fences = [box(x0, x1, y0, y0 + 6, FLOOR - 0.5, Z_PCB - 0.8)
          for x0, x1 in ((BB.XMin - 1.8, BB.XMin - 0.3), (BB.XMax + 0.3, BB.XMax + 1.8)) for y0 in (-17.0, 11.0)]
cradles = [box(x0, x1, SB.YMin + 4, SB.YMax - 12, FLOOR - 0.5, SB.ZMin + 12.0)
           for x0, x1 in ((SB.XMin - 1.85, SB.XMin - 0.25), (SB.XMax + 0.25, SB.XMax + 1.85))]
cradles.append(box(GX - 10, GX + 10, GY - 10, GY + 6, FLOOR - 0.5, SB.ZMin - 0.2))
base = cad.fuse_one(base, *[p.common(skin) for p in pads + fences + cradles])
# board retention: a rib from the deck down onto the spine (0.2 mm off
# it), right of the moles
SPINE_Z = BB.ZMax
top = cad.fuse_one(top, box(14.0, 34.0, -2.0, 2.0, SPINE_Z + 0.2, ZI + 0.5))
# five M2 screws from below into insert bosses in the top: off the board,
# every module, ribbon, burrow and slide corridor
SCREWS = [(MC[0][0] + 5.0, MC[0][1] - 29.4), (MC[2][0] - 18.0, MC[2][1] + 17.4), (MC[3][0] + 10.0, MC[3][1] + 24.4),
          (SX + 30.0, SCR_FACE - 11.0), (centre(STB)[0] + 10.0, centre(STB)[1] - 29.4)]
for x, y in SCREWS:
    if not inside(x, y, t=WALL + 4.0):
        print("NOTE screw at (%.1f, %.1f) is near the mound's edge" % (x, y))
screws, cols, bores, csks = [], [], [], []
for x, y in SCREWS:
    # one column from 0.1 mm over the floor up into the deck, a heat-set
    # insert pocket (1.4 d + 0.1) at its foot and the thread-forming pilot
    # above it; a 90 deg countersink through the floor - every boss in ONE
    # fuse and ONE cut (hype_button.py)
    cols.append(cyl(2.8, (x, y, FLOOR + 0.1), ZI + 0.5 - (FLOOR + 0.1)))
    bores.append(cyl(1.6, (x, y, FLOOR), 7.0))
    bores.append(cyl(0.85, (x, y, FLOOR + 6.5), 7.0))
    csks.append(Part.makeCone(4.0 / 2, 2.4 / 2, (4.0 - 2.4) / 2, V(x, y, RUB - 0.01), V(0, 0, 1)))
    csks.append(cyl(2.4 / 2, (x, y, RUB - 0.5), WALL + 1.0))
    screws.append(cad.screw("csk_phillips", "M2", 8, at=(x, y, RUB), axis="+Z"))
top = cad.cut(cad.fuse_one(top, *cols), bores)
base = cad.cut(base, csks)
# a 1 mm boss inside the floor over each rubber foot (its recess leaves the
# floor whole at any WALL)
FEET = [(MC[0][0] - 12.0, MC[0][1] - 21.4), (MC[2][0] - 8.0, MC[2][1] + 29.4), (GX + 10.0, GY - 20.0),
        (centre(STB)[0] + 30.0, centre(STB)[1] - 9.4), (SX, SCR_FACE + 12.0)]
base = cad.fuse_one(base, *[cyl(6.0, (x, y, FLOOR - 0.5), 1.5) for x, y in FEET])
tick("base + screws")


def insert(shell, cutter):
    """(shell with the opening, the piece that fills it exactly)."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, piece


# ------------------------------------------------------------ the moles
# each burrow: a dark soil ring filling its opening in the deck, its rim
# RIM_H proud; each mole: a frosted head (a crown on a rolled shoulder,
# hollow) TRAVEL over the rim, a skirt down the bore, two snap barbs 0.1 mm
# under the deck, a plunger to 0.16 mm over its button and a light fin
# hanging over its own column of the light beside it
Z_RIM = Z_TOP + RIM_H
Z_HB = Z_RIM + TRAVEL                         # the head's underside
Z_SB = ZI - 1.2                               # the skirt's foot
top = cad.cut(top, [cyl(BUR_R, (x, y, ZI - 1), WALL + 2) for x, y in MC])
burrows = []
for x, y in MC:
    b = ring(HOLE_R, BUR_R, (x, y), ZI, Z_RIM)
    b = cad.soften(b, 1.0, [e for e in b.Edges if e.BoundBox.ZMin > Z_RIM - 1e-3])
    burrows.append(b)
CC = (0.0, MOLE_H - DOME_R)
KC = (HEAD_R - KNUCKLE, CC[1] + math.sqrt((DOME_R - KNUCKLE) ** 2 - (HEAD_R - KNUCKLE) ** 2))
PHI = math.degrees(math.atan2(KC[1] - CC[1], KC[0]))
RI = SK_R - 1.6


def arc(c, r, a0, a1):
    am, a1 = math.radians((a0 + a1) / 2), math.radians(a1)
    return ("arc", (c[0] + r * math.cos(am), c[1] + r * math.sin(am)),
            (c[0] + r * math.cos(a1), c[1] + r * math.sin(a1)))


SKIRT = Z_HB - Z_SB                           # the skirt's length under the head
mole_sec = [
    (0, MOLE_H), arc(CC, DOME_R, 90, PHI), arc(KC, KNUCKLE, PHI, 0), (HEAD_R, 0.0),
    (SK_R, 0.0), (SK_R, -SKIRT), (RI, -SKIRT), (RI, KC[1]), (KC[0] + KNUCKLE - HEAD_T, KC[1]),
    arc(KC, KNUCKLE - HEAD_T, 0, PHI), arc(CC, DOME_R - HEAD_T, PHI, 90),
]
# ONE mole is built (and its face's pockets cut) on the origin's axis and
# copied to each burrow: a pink nose on the shoulder, two bead eyes on the
# crown, looking at the player (-Y); each face piece fills its own pocket
KT = KC[1] + KNUCKLE * math.sin(math.radians(PHI))   # the shoulder's top (local height)
H_NOSE = KC[1] + 0.5 * (KT - KC[1])
H_EYE = KT + 0.3 * (MOLE_H - KT)
NOSE_R, EYE_R, EYE_X = 3.4, 1.8, 5.8
rr = KC[0] + math.sqrt(KNUCKLE ** 2 - (H_NOSE - KC[1]) ** 2)       # the shoulder's radius there
nz = (H_NOSE - KC[1]) / KNUCKLE
face0 = [Part.makeSphere(NOSE_R, V(0, -rr, Z_HB + H_NOSE) + V(0, -math.sqrt(1 - nz * nz), nz) * 1.6)]
for k in (-1, 1):
    dz = H_EYE - CC[1]
    dy = math.sqrt(DOME_R ** 2 - dz ** 2 - EYE_X ** 2)
    n = V(k * EYE_X, -dy, dz)
    n.normalize()
    face0.append(Part.makeSphere(EYE_R, V(k * EYE_X, -dy, Z_HB + H_EYE) + n * 0.6))
mole0 = cad.cut(cad.revolve_profile(mole_sec, at=(0, 0, Z_HB)), face0)
moles, faces = [], []
for i, (x, y) in enumerate(MC):
    m = mole0.copy()
    m.translate(V(x, y, 0))
    fc = [f.copy() for f in face0]
    for f in fc:
        f.translate(V(x, y, 0))
    faces.append(fc)
    bt = MB[i].ZMax
    z_in = Z_HB + MOLE_H - HEAD_T
    lb = LB[0] if i < 2 else LB[1]
    lx = centre(lb)[0]
    s = 1.0 if lx > x else -1.0
    fin = box(x + s * 11.0 if s > 0 else x - 15.4, x + 15.4 if s > 0 else x - 11.0, y - 5.0, y + 5.0,
              lb.ZMax + TRAVEL + 0.5, Z_SB + 0.5).common(cyl(14.9, (x, y, 0), 100))
    barbs = [box(x - 6, x + 6, y + sy * (SK_R - 0.5) if sy > 0 else y - SK_R - 0.9,
                 y + SK_R + 0.9 if sy > 0 else y - (SK_R - 0.5), Z_SB + 0.1, ZI - 0.1) for sy in (1, -1)]
    m = cad.fuse_one(m, fin, cyl(3.0, (x, y, bt + 0.16), z_in + 0.6 - (bt + 0.16)),
                     cyl(4.5, (x, y, z_in - 4.0), 4.6), *barbs)
    moles.append(m)
tick("moles")

# the START key: a round cap through the deck, its flange 0.1 mm under it
sx_, sy_, _ = centre(STB)
k_base = ZI - 0.9
start_key = cad.button_cap(START_D, (Z_TOP + 4.0) - k_base, dome=0.8, flange=1.2, at=(sx_, sy_, k_base), axis="+Z")
top = cad.opening_for(top, start_key, clearance=0.25, chamfer=0.4, axis="+Z")
start_key = cad.fuse_one(start_key, cyl(3.0, (sx_, sy_, STB.ZMax + 0.16), k_base - (STB.ZMax + 0.16) + 0.5))
# the speaker grille: a disc filling its opening in the deck
top, grille = insert(top, cyl(GRILLE_D / 2 + 2.0, (GX, GY, ZI - 1), WALL + 2))
grille = cad.speaker_grille(grille, (GX, GY, Z_TOP), (0, 0, 1), GRILLE_D, ring_pitch=2.6, hole=1.6)

# ------------------------------------------------------------ the sign
# a hollow neck rises from the deck; the yellow sign sits on it, keyed by
# two pins in the neck's thick side walls. The screen rides up the neck
# (fitted with the top, the sign after it) and stands in the sign 0.4 mm
# behind the glass between two ribs.
ZS = Z_TOP + SIGN_H                           # the sign's bottom edge = the neck's top
top = cad.fuse_one(top, box(SX - NI - NW, SX + NI + NW, Y_SF, Y_SB, ZI - 0.5, ZS))
top = cad.cut(top, box(SX - NI, SX + NI, Y_SF + WALL, Y_SI, ZI - 1, ZS + 1))
PINS = [(SX + k * (NI + NW / 2), (Y_SF + Y_SB) / 2) for k in (-1, 1)]
top = cad.fuse_one(top, *[cyl(1.5, (px, py, ZS - 0.5), 3.0) for px, py in PINS])
sign = cad.rounded_box(SIGN_W, Y_SB - Y_SF, SIGN_HT, SIGN_R, at=(SX - SIGN_W / 2, Y_SF, ZS), edges="y")
sign = cad.soften(sign, 1.2, [e for e in sign.Edges if abs(e.BoundBox.YMin - Y_SF) < 1e-6
                              and abs(e.BoundBox.YMax - Y_SF) < 1e-6])
C6 = 6.0                                      # the inside's chamfered corners (no concave rounds)
a_, b_ = SIGN_W / 2 - WALL, SIGN_HT - WALL
poly = [(-a_ + C6, FLS), (a_ - C6, FLS), (a_, FLS + C6), (a_, b_ - C6), (a_ - C6, b_), (-a_ + C6, b_),
        (-a_, b_ - C6), (-a_, FLS + C6)]
pw = Part.makePolygon([V(SX + px, Y_SF + WALL, ZS + pz) for px, pz in poly + poly[:1]])
cavity = Part.Face(pw).extrude(V(0, Y_SI - (Y_SF + WALL), 0))
sign = cad.cut(sign, [cavity, box(SX - NI, SX + NI, Y_SF + WALL, Y_SI, ZS - 1, ZS + FLS + 1)]
               + [cyl(1.65, (px, py, ZS - 0.1), 2.8) for px, py in PINS])
# ribs either side of the screen, 0.3 mm off its ends, from the front wall
# to the back wall
scz = centre(SCB)[2]
sign = cad.fuse_one(sign, *[box(x0, x1, Y_SF + WALL - 0.5, Y_SI + 0.5, scz - 8.0, scz + 8.0)
                            for x0, x1 in ((SCB.XMin - 1.8, SCB.XMin - 0.3), (SCB.XMax + 0.3, SCB.XMax + 1.8))])


def yprism(x0, x1, z0, z1, y0, y1, r):
    w = cad.rounded_rect_wire(x1 - x0, z1 - z0, r, ((x0 + x1) / 2, y0, (z0 + z1) / 2), "Y")
    return Part.Face(w).extrude(V(0, y1 - y0, 0))


# the black bezel through the front wall round the window (a raised lip
# proud of the sign), the smoked glass in it over the active area
WIN = (31.0, 18.0)
BZ = 4.0


def win_box(m, y0, y1, r):
    return yprism(SX - WIN[0] / 2 - m, SX + WIN[0] / 2 + m, scz - WIN[1] / 2 - m, scz + WIN[1] / 2 + m, y0, y1, r)


sign, bezel = insert(sign, win_box(BZ, Y_SF - 1, Y_SF + WALL + 0.5, 4.0))
bezel = cad.fuse_one(bezel, cad.cut(win_box(BZ, Y_SF - 1.2, Y_SF + 0.3, 4.0), win_box(1.0, Y_SF - 2, Y_SF + 1, 1.5)))
bezel, glass = insert(bezel, win_box(0.0, Y_SF - 0.6, Y_SF + WALL + 1, 1.5))

# ------------------------------------------------------------ the holster
mx, my = MALLET["at"]
HB_TOP = Z_TOP + MALLET["boss_h"]
top = cad.fuse_one(top, cyl(MALLET["boss_r"], (mx, my, Z_TOP - 0.5), HB_TOP - Z_TOP + 0.5),
                   cyl(MALLET["peg_r"] + 2.5, (mx, my, ZI - 7.0), 7.5))
top = cad.cut(top, cyl(MALLET["bore_r"], (mx, my, HB_TOP - 12.0), 13.0))
top = cad.soften(top, 1.0, [e for e in top.Edges if abs(e.BoundBox.ZMin - HB_TOP) < 1e-3
                            and e.BoundBox.XLength > 2 * MALLET["boss_r"] - 0.1])

# USB-C in the left flank: a pocket brings the wall to 0.25 mm off the mouth
uy, uz = (UB.YMin + UB.YMax) / 2, Z_PCB + 5.9


def xprism(y0, y1, z0, z1, x0, x1, r):
    w = cad.rounded_rect_wire(y1 - y0, z1 - z0, r, (x0, (y0 + y1) / 2, (z0 + z1) / 2), "X")
    return Part.Face(w).extrude(V(x1 - x0, 0, 0))


pocket = xprism(uy - 6.5, uy + 6.5, uz - 4.0, uz + 5.0, -200.0, UB.XMin - 1.3, 3)
liner = cad.cut(xprism(uy - 8.5, uy + 8.5, max(uz - 7.5, SPLIT + LIP + 0.6), uz + 7.5, UB.XMin - 0.25, -200.0, 4), pocket)
top = cad.fuse_one(cad.cut(top, pocket), liner.common(skin))
top = cad.socket_opening(top, usb, margin=1.5)
tick("stage A")


# === STAGE B: details ===
# the mole faces: the nose and eye pieces fill the pockets cut in STAGE A
noses = [fc[0] for fc in faces]
eyes = [e for fc in faces for e in fc[1:]]
# MOLE BOP: raised red letters on an underline swoosh (one part) inlaid
# POCKET deep into the sign above the window, RAISE proud of it
POCKET, RAISE, LETTER_H, CLOSE_R = 1.0, 1.4, 9.0, 0.9
_fonts = [os.path.join(App.getHomePath(), "fonts", f) for f in ("Ubuntu-B.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf")]
_fonts += ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
FONT = next(f for f in _fonts if os.path.isfile(f))
_probe = Part.makeFace(Part.makeWireString("M", FONT, 10.0)[0], "Part::FaceMakerBullseye")
_scale = LETTER_H / _probe.BoundBox.YLength
TITLE = "MOLE BOP"
chars = [Part.makeFace(w, "Part::FaceMakerBullseye") for w in Part.makeWireString(TITLE, FONT, 10.0 * _scale) if w]
_tb = chars[0].BoundBox
for f in chars[1:]:
    _tb.add(f.BoundBox)


def closed(f, r=CLOSE_R):
    """The glyph with every gap under 2 r filled (offset out, then back),
    re-knotted as straight facets (no knife-edge slivers, no arc channels)."""
    try:
        g = f.makeOffset2D(r, 0).makeOffset2D(-r, 0)
        g = g.Faces[0] if g.Faces else None
        if g is not None:
            ws = []
            for w in g.Wires:
                pts = w.discretize(QuasiDeflection=0.03)
                if (pts[0] - pts[-1]).Length > 1e-6:
                    pts.append(pts[0])
                ws.append(Part.makePolygon(pts))
            g = Part.makeFace(ws, "Part::FaceMakerBullseye")
        if g is not None and g.isValid() and f.Area - 0.5 < g.Area < f.Area * 1.12:
            return g
    except Exception as exc:                                  # noqa: BLE001
        print("NOTE glyph closing: %s" % exc)
    return f


Z_TITLE = (scz + WIN[1] / 2 + BZ + ZS + SIGN_HT) / 2
# the letters stand on an underline swoosh (each overlaps it): ONE part
BASE_L = max(f.BoundBox.YMin for f in chars)
bar = cad.rounded_rect_wire(_tb.XLength + 4.0, 3.0, 1.45, (_tb.Center.x, BASE_L - 0.8, 0), "Z")
glyphs = [closed(f) for f in chars] + [Part.Face(bar)]
_gb = glyphs[0].BoundBox
for f in glyphs[1:]:
    _gb.add(f.BoundBox)
title = cad.fuse_one(*[f.extrude(V(0, 0, POCKET + RAISE)) for f in glyphs])
title.translate(V(-_gb.Center.x, -_gb.Center.y, -POCKET))
title.rotate(V(0, 0, 0), V(1, 0, 0), 90)                      # local z (toward the reader) -> -Y
title.translate(V(SX, Y_SF, Z_TITLE))
tick("faces")
# a pad behind the logo inside the sign keeps WALL behind its pocket
tb = title.BoundBox
sign = cad.fuse_one(sign, box(tb.XMin - 2.0, tb.XMax + 2.0, Y_SF + WALL - 0.5, Y_SF + WALL + POCKET,
                              tb.ZMin - 2.0, tb.ZMax + 2.0))
sign = cad.cut(sign, title)
tick("letters")
# the mallet: a wooden handle pegged into the holster, a soft red head on
# its tenon (the tenon's end carries it on the bore's floor)
hp = MALLET
z_sh = HB_TOP + hp["handle_l"]                 # the shaft's top
zc = z_sh + 1.0 + hp["head_r"]                 # the head's axis
TEN = 10.0
handle = cad.fuse_one(cyl(hp["peg_r"], (mx, my, HB_TOP - 11.5), 12.0), cyl(hp["handle_r"], (mx, my, HB_TOP), hp["handle_l"]),
                      cyl(hp["peg_r"], (mx, my, z_sh - 0.5), 1.5 + TEN))
handle = cad.cut(handle, [ring(hp["handle_r"] - 0.5, hp["handle_r"] + 1, (mx, my), HB_TOP + 8.0 + 6.0 * k,
                               HB_TOP + 9.0 + 6.0 * k) for k in range(4)])
head = cyl(hp["head_r"], (mx - hp["head_l"] / 2, my, zc), hp["head_l"], (1, 0, 0))
head = cad.soften(head, 5.0)
head = cad.cut(head, cyl(hp["bore_r"], (mx, my, zc - hp["head_r"] - 1.0), 1.0 + (z_sh + 1.0 + TEN) - (zc - hp["head_r"])))
tick("mallet")
# grass tufts on the deck: three leaning blades each, sunk 0.5 mm into it
TUFTS = [((MC[0][0] + MC[1][0]) / 2, (MC[0][1] + MC[2][1]) / 2), (MC[0][0] - 12.0, MC[0][1] - 24.0),
         (MC[0][0] - 20.0, 2.0), (centre(STB)[0] + 22.0, centre(STB)[1] + 16.0), (GX + 34.0, GY + 22.0),
         (MC[3][0], MC[3][1] + 26.0), (MC[2][0] + 4.0, MC[2][1] + 36.0), (GX - 28.0, GY - 10.0)]
blades = []
for tx, ty in TUFTS:
    if not inside(tx, ty, t=EDGE_R + 4.0):
        continue
    for a, h in ((90, 10.0), (210, 8.0), (330, 9.0)):
        c = Part.makeCone(2.0, 0.4, h, V(0, 0, 0), V(0, 0, 1))
        c.rotate(V(0, 0, 0), V(0, 1, 0), 18)
        c.rotate(V(0, 0, 0), V(0, 0, 1), a)
        c.translate(V(tx + 1.4 * math.cos(math.radians(a)), ty + 1.4 * math.sin(math.radians(a)), Z_TOP - 0.5))
        blades.append(c)
top = cad.fuse_one(top, *blades)
tick("tufts")
# legends, the START key's GO, the parting-line reveal
top = cad.text(top, "BOP!", (MC[0][0] + 26.0, MC[0][1] - 40.0, Z_TOP), (0, 0, 1), 8.0, depth=0.6, mode="emboss",
               up=(0, 1, 0))
top = cad.text(top, "ATECH", (GX, GY + GRILLE_D / 2 + 7.0, Z_TOP), (0, 0, 1), 4.0, depth=0.4, mode="deboss",
               up=(0, 1, 0))
tick("texts")
start_key = cad.text(start_key, "GO", (sx_, sy_, Z_TOP + 4.0), (0, 0, 1), 5.0, depth=0.4, mode="deboss", up=(0, 1, 0))
top = cad.groove_ring(top, "Z", SPLIT + LIP + 2.0, w=0.8, depth=0.6)
tick("stage B")


# ------------------------------------------------------------ feet
B = base
B = cad.grille(B, ((MC[0][0] + MC[1][0]) / 2 + 10.0, MC[0][1] - 44.0, RUB), (0, 0, -1), (30, 16), kind="slot",
               hole=2.0, pitch=4.5)
B = cad.text(B, "ATECH MB-4", (0.0, -45.0, RUB), (0, 0, -1), 5.0, depth=0.4, mode="deboss", up=(0, -1, 0))
rubbers = []
for x, y in FEET:
    B = cad.cut(B, cyl(4.6, (x, y, RUB - 1), 2.2))
    rubbers.append(cad.foot(9, RUB + 1.2, style="dome", at=(x, y, RUB + 1.2)))
base = B


# ------------------------------------------------------------ parts
def part(name, shape):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    return o


parts = {"Top": top, "Base": base}
for i in range(4):
    parts["Burrow_%d" % (i + 1)] = burrows[i]
for i in range(4):
    parts["Mole_%d" % (i + 1)] = moles[i]
parts.update({"Start_Key": start_key, "Grille": grille, "Sign": sign, "Bezel": bezel, "Glass": glass})
for nm, sh in parts.items():
    o = part(nm, sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS[nm.split("_")[0] if nm.split("_")[0] in ("Burrow", "Mole") else nm])
    if nm.startswith("Mole"):
        o.ViewObject.Transparency = cad.transparency("frosted")
    if nm == "Glass":
        o.ViewObject.Transparency = cad.transparency("smoked")
for i, sh in enumerate(noses):
    o = part("Nose_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Nose"])
for i, sh in enumerate(eyes):
    o = part("Eye_%d%s" % (i // 2 + 1, "LR"[i % 2]), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Eye"])
o = part("Title", title)
o.ViewObject.ShapeColor = cad.color(COLOURS["Title"])
o = part("Mallet_Handle", handle)
o.ViewObject.ShapeColor = cad.color(COLOURS["Mallet_Handle"])
o = part("Mallet_Head", head)
o.ViewObject.ShapeColor = cad.color(COLOURS["Mallet_Head"])
for i, sh in enumerate(rubbers):
    o = part("Rubber_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Rubber"])
for i, sh in enumerate(screws):
    o = part("Screw_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Screw"])
print("SIZE %s" % (cad.measure(Part.makeCompound(list(parts.values())))["size"],))
print("TOTAL %.1f s" % (time.time() - T0))
