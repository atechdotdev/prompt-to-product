"""Example: "a finger drum pad that plays real drum sounds" - a tabletop finger-drum controller: four big rubber pads, a glowing grid, a chrome dial, a speaker.

fork this file for a drum pad / finger drum / beat pad (a sampler pad, an
MPC-style pad controller, a sound board with big hit pads); change PARAMETERS and the outlines.
ARCHETYPE: drum pad

How it is built (R990):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board FLAT under a low pad deck (port 7 at the back, its USB-C mouth
    out of the back wall). Four buttons in two rows 40 mm apart - 3 + 11
    (back) and 6 + 14 (front) - sit under the four 46 mm pads of a 2 x 2
    grid; each pad is a soft-cornered block over a skirt through its own
    opening in the deck, two snap barbs under the deck keep it in, a
    plunger presses its button and its 3 mm overhang lands on the deck
    after 0.8 mm (the stop). A frosted LATTICE (the frame round the grid
    and the cross between the pads) is inlaid in the deck over a rib; two
    lights glow up through it - 13 under the cross's right arm (between
    the two right pads), 10 under the back bar (behind the back-right pad)
    - each through a light pipe kept inside its light's footprint. Both
    sit on the right column (the left ports carry the speaker, the knob
    and two pads' buttons), so the left half of the lattice only glows by
    light carried along the frosted part. Light 9 is the KIT status lens
    in the back margin. The speaker (4, 5) and the encoder knob (1, 2) are
    CABLED straight out of the left edge into a raised control column on
    the left (ribbons in their own plane, no twist): the speaker at the
    board's height under a round grille, the knob lowered so only its cap
    rises through a dial crown, a chrome cap on its shaft. Everything is
    built in a LOCAL frame (the deck flat) and tilted back ALPHA as one
    Placement - the pads lean toward the player and the foot stands flat.
    The body is a rounded plan extruded twice (deck, column), cut by the
    leaning foot plane, hollowed with its own core, split into the fixed
    Base (board pads, end fences, cradles for the speaker and the knob) and
    the Top with a lip; five M2 screws from below into heat-set insert
    bosses; a rib from the deck onto the board's spine.
  * STAGE B - details: the chrome dial bezel with 12 ticks, the knurled cap
    with its pointer, legends, the parting-line reveal, a grip groove along
    the wrist edge, vents and a model mark under the base, rubber feet.
DETAILS (visible, 32): 1 low wedge deck leaning 4.4 deg toward the player;
2 rolled top edges; 3 soft plan corners; 4 a raised control column on the
left with a crisp step riser; 5 four 46 mm rubber pads in four colours;
6 soft-rolled pad tops; 7 pad numbers 1-4; 8 a frosted lattice (frame and
cross) glowing between the pads; 9 each pad's overhang standing 0.8 mm over
the deck (its travel to the stop); 10 a dial crown rising out of the column;
11 a chrome bezel on its rim with 12 ticks; 12 a knurled chrome dial cap
with a pointer; 13 a frosted LED ring in the dial well; 14 a brushed round
speaker grille (133 holes); 15 "KIT / VOL" legend; 16 "ATECH" on the column;
17 the KIT status lens with its legend; 18 "FINGER DRUM" on the back margin;
19 USB-C pocket with a liner in the back; 20 parting-line reveal; 21 grip
groove along the wrist edge; 22 slot vents under the base; 23 "ATECH DP-4"
under the base; 24 five countersunk screws from below; 25 four rubber feet.
Inside: 26 two snap barbs on each pad's skirt; 27 a plunger to each button;
28 the lattice's rib under the deck and two light pipes; 29 board pads and
end fences; 30 cradle ribs and pads under the speaker and the knob; 31 a rib
onto the board's spine; 32 five bosses with heat-set insert sleeves.
Materials: charcoal soft-touch top, black base, red / amber / blue / green
rubber pads, frosted lattice, dial ring and status lens, chrome dial cap
and bezel, brushed speaker grille, chrome screws, rubber feet.
MEASURED (R990, 2026-11-17): ./check CHECK PASS, run_seconds 15 s, wall 54 s; every RESTYLE end CHECK PASS.
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
    "Top", "Light_Grid", "Status_Lens", "Grille", "Dial_Ring", "Dial_Bezel", "Dial_Cap",
    "Pad_1", "Pad_2", "Pad_3", "Pad_4",
    "Rubber_1", "Rubber_2", "Rubber_3", "Rubber_4",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4", "Screw_5"],
    # each pad presses its own button through its opening (a declared cover)
    "covers": {"Pad_1": "button_p3", "Pad_2": "button_p11", "Pad_3": "button_p6", "Pad_4": "button_p14"}}
REVIEW_CLOSEUPS = ["Pad_1", "Dial_Cap", "Light_Grid"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them and the measured hardware.
WRIST = 14.0       # RESTYLE 11.9..16.1 length: the wrist rest in front of the pad grid (y)
SIDE = 12.0        # RESTYLE 10.2..13.8 width: the deck past the grid on the right (x)
RISE = 12.0        # RESTYLE 10.2..13.8 height: how much higher the back stands than the front
CORNER = 12.0      # RESTYLE 10.2..13.8 radius: the plan's corners
WALL = 2.0         # RESTYLE 1.7..2.3 wall
# end RESTYLE
# the product is built in a LOCAL frame - the deck flat, x across, y away
# from the player, z up from the front-bottom edge - and tilted back ALPHA
# as one piece (the foot plane leans the other way, so it lands flat).
Z_PCB = WALL + 4.0               # the PCB top over the front edge's foot
TRAVEL = 0.8                     # each pad's travel to its stop (the overhang on the deck)
ZI = Z_PCB + 10.04 + 0.66 + TRAVEL + 1.2   # the deck's inner face: a pressed skirt stays 0.66 over the buttons
EDGE_R, FOOT_R = 1.5 * WALL, 1.2  # the rolled top edges (a sharp core keeps >= t/2 in their corners), the foot
PAD, GUT, BAR = 46.0, 5.0, 4.0   # pad size, the cross between the pads, the frame round them
OVER, PAD_T, PAD_R = 3.0, 4.0, 5.0   # the pad's overhang (the stop), thickness, corner radius
GX, GY = 30.0, -82.0             # the grid's centre: the cross over light 13's LEDs, the back bar over light 10's
LAT_T = 1.6                      # the frosted lattice's thickness (a rib under the deck keeps WALL under it)
XK = -50.0                       # the control column's axis: knob and speaker cabled out to it
CROWN_H = 10.0                   # the dial crown over the column top
CAP_R, DISH_R, RIM_R, FOOT_RC = 11.0, 17.5, 19.5, 21.5   # dial cap, well, crown rim, crown foot
RING_R = (8.05, 13.5)            # the frosted ring round the dial shaft
GRILLE_D = 34.0                  # the speaker grille
RUB = 1.5                        # the rubber feet's height
COLOURS = {"Top": "#2b2d31", "Base": "matte_black", "Light_Grid": "frosted", "Status_Lens": "frosted",
           "Grille": "brushed_alu", "Dial_Ring": "frosted", "Dial_Bezel": "chrome", "Dial_Cap": "chrome",
           "Pad_1": "#e0383e", "Pad_2": "#f39c1e", "Pad_3": "#2d7fe0", "Pad_4": "#2fb36a",
           "Rubber": "rubber", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
FLAT = Rotation(Vector(1, 0, 0), 90)            # modules face +Z; board x 0..60, y -120..0
HALF = GUT / 2 + PAD                            # grid centre to the pads' outer edge
X_RISER = GX - HALF - BAR - 1.5                 # the control column's step, 1.5 mm off the lattice
X0 = XK - 28.0                                  # the column's outer side (the knob 6 mm inside its wall)
X1 = GX + HALF + BAR + SIDE
Y0 = GY - HALF - BAR - WRIST                    # the wrist edge
Y1 = 7.0                                        # the back: the USB-C mouth 6 mm inside it
Z_TOP = ZI + WALL                               # the pad deck
Z_COL = Z_PCB + 20.2 + 1.0 + WALL               # the column top: 1 mm air over the speaker
Z_RIM = Z_COL + CROWN_H
ALPHA = math.degrees(math.atan2(RISE, Y1 - Y0))
TAN_A = math.tan(math.radians(ALPHA))
TILT = Placement(V(0, 0, RUB), Rotation(V(1, 0, 0), ALPHA), V(0, Y0, 0))
TILT_M = TILT.toMatrix()
board = ap.board_object(doc)
board.Placement = TILT.multiply(Placement(V(0, 0, Z_PCB), FLAT))
pad_btn = [ap.seat(doc, "button", n) for n in (3, 11, 6, 14)]   # back-left, back-right, front-left, front-right
l_back = ap.seat(doc, "light", 10)              # under the lattice's back bar
l_mid = ap.seat(doc, "light", 13)               # under the cross
l_kit = ap.seat(doc, "light", 9)                # the KIT status lens
usb = ap.seat(doc, "usbc", 7)                   # back, mouth +Y
# the speaker at the board's height and the knob lowered (its cap's top
# 2.2 mm under the crown's rim), both straight out of the left edge, pins
# toward the board (face x cable = +Y: the plug's width, no twist)
SPK_C = (XK, -80.0, Z_PCB + 10.1)
KNOB_TOP = Z_RIM - 2.2
KNOB_C = (XK, -20.0, KNOB_TOP - 19.07)
spk, spk_rb = ap.cable(doc, "speaker", (4, 5), TILT.multiply(ap.module_placement("speaker", SPK_C, face="+Z", cable="+X")))
knob, knob_rb = ap.cable(doc, "knob", (1, 2), TILT.multiply(ap.module_placement("knob", KNOB_C, face="+Z", cable="+X")))
tick("hardware")


def lbox(obj):
    """An Atech object's box in the LOCAL (untilted) frame."""
    g = (obj.Mesh if hasattr(obj, "Mesh") else obj.Shape).copy()
    g.Placement = TILT.inverse().multiply(g.Placement)
    return g.BoundBox


def W_(s):
    """Local frame -> world (tilted back, standing on its feet)."""
    s = s.copy()
    s.transformShape(TILT_M)
    return s


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


BB = lbox(board)
PB = [lbox(m) for m in pad_btn]
LBK, LMD, LKT, UB, SB, KB = [lbox(m) for m in (l_back, l_mid, l_kit, usb, spk, knob)]
print("DECK %.0f x %.0f, front %.1f / back %.1f mm, column %.1f, leaning %.1f deg" % (
    X1 - X0, Y1 - Y0, Z_TOP, Z_TOP + RISE, Z_COL, ALPHA))


# ------------------------------------------------------------ the body
def foot_cut(t):
    """Everything above the leaning foot plane, raised t along its normal."""
    k = box(-400, 400, -400, 400, 0, 400)
    k.rotate(V(0, Y0, 0), V(1, 0, 0), -ALPHA)
    k.translate(V(0, t * math.sin(math.radians(ALPHA)), t * math.cos(math.radians(ALPHA))))
    return k


def slab(t):
    """The body inset t: the rounded plan extruded to the deck, and again
    to the column top left of the step, cut by the foot plane (planes and
    cylinders only - robust booleans)."""
    w = cad.rounded_rect_wire((X1 - X0) - 2 * t, (Y1 - Y0) - 2 * t, max(CORNER - t, 0.6),
                              ((X0 + X1) / 2, (Y0 + Y1) / 2, -80), "Z")
    f = Part.Face(w)
    deck = f.extrude(V(0, 0, 80 + Z_TOP - t))
    col = f.extrude(V(0, 0, 80 + Z_COL - t)).common(box(X0 - 5, X_RISER - t, Y0 - 5, Y1 + 5, -90, 100))
    return cad.fuse_one(deck, col).removeSplitter().common(foot_cut(t))


def on_foot(e):
    return all(abs(v.Point.z + (v.Point.y - Y0) * TAN_A) < 1e-3 for v in e.Vertexes)


outer = slab(0.0)
outer = cad.soften(outer, EDGE_R, [e for e in outer.Edges if e.BoundBox.ZMin > Z_TOP - 1e-3])
outer = cad.soften(outer, FOOT_R, [e for e in outer.Edges if on_foot(e)])
# the core keeps SHARP inner edges (a filleted core leaves concave rounds
# ./check reads as clip channels)
body = cad.hollow(outer, WALL, core=lambda t: slab(t))
skin = slab(0.5)                              # clips ribs and liners 0.5 mm under the outer skin
tick("body")
SPLIT = Z_PCB - 2.0                           # in the cavity: the lip's top stays under the PCB
base, top = cad.split(body, "Z", at=SPLIT, lip=1.2)
tick("split")


def floor_z(x, y):
    """The base's inner floor height at (x, y) (the foot plane leans)."""
    return -(y - Y0) * TAN_A + WALL / math.cos(math.radians(ALPHA))


# the fixed base holds the board: pads 0.1 mm under it (0.5 mm into the
# floor), fences off its front and back ends (clear of port 7's slide
# path), cradles 0.25 mm off the cabled speaker and knob with a pad under each
UNDER = BB.ZMin - 0.1
pads = [box(x - 4, x + 4, y - 4, y + 4, floor_z(x, y + 4) - 0.5, UNDER)
        for x in (BB.XMin + 10, (BB.XMin + BB.XMax) / 2, BB.XMax - 10) for y in (BB.YMax - 18, BB.YMin + 18)]
fences = [box(x0, x0 + 10, BB.YMin - 1.8, BB.YMin - 0.3, floor_z(0, BB.YMin - 0.3) - 0.5, Z_PCB - 0.8)
          for x0 in (BB.XMin + 5, BB.XMax - 15)]
fences += [box(x0, x0 + 10, BB.YMax + 0.3, BB.YMax + 1.8, floor_z(0, BB.YMax + 1.8) - 0.5, Z_PCB - 0.8)
           for x0 in (BB.XMin + 3, BB.XMax - 13)]
cradles = []
for mb, hi in ((SB, 12.0), (KB, 8.0)):
    for y0, y1 in ((mb.YMin - 1.85, mb.YMin - 0.25), (mb.YMax + 0.25, mb.YMax + 1.85)):
        cradles.append(box(mb.XMin + 4, mb.XMax - 10, y0, y1, floor_z(0, y1) - 0.5, mb.ZMin + hi))
    cx_, cy_, _ = centre(mb)
    cradles.append(box(cx_ - 10, cx_ + 6, cy_ - 10, cy_ + 10, floor_z(0, cy_ + 10) - 0.5, mb.ZMin - 0.2))
base = cad.fuse_one(base, *[p.common(skin) for p in pads + fences + cradles])
# board retention: a rib from the deck down onto the spine (0.2 mm off
# it), under the lattice's cross
SPINE_Z = BB.ZMax                              # the spine's top (PCB top + 4.5)
top = cad.fuse_one(top, box(GX - 2, GX + 2, BB.YMin + 25, BB.YMax - 45, SPINE_Z + 0.2, ZI + 0.5))
# five M2 screws from below into insert bosses in the top: in the margins,
# off the board, every module and every slide corridor
SCREWS = [(X0 + 10, Y0 + 12), (X1 - 10, Y0 + 10), (X1 - 9, Y1 - 12), (X0 + 10, (SB.YMax + KB.YMin) / 2),
          (GX, Y0 + 7)]
screws = []
for x, y in SCREWS:
    zb = -(y - Y0) * TAN_A                     # the foot's outer face under the screw
    base, top = cad.screw_through(base, top, (x, y, zb), size="M2", ribs=0)
    ring_ = [(0.0, 0.0)] + [(rr * math.cos(math.radians(a_)), rr * math.sin(math.radians(a_)))
                            for rr in (1.5, 3.0) for a_ in range(0, 360, 45)]
    z0 = max(floor_z(x + ex, y + ey) for ex, ey in ring_) + 0.1
    zt = (Z_COL if x < X_RISER else Z_TOP) - WALL + 0.5
    top = cad.fuse_one(top, cyl(2.8, (x, y, z0), zt - z0))
    top = cad.cut(top, cyl(1.6, (x, y, z0 - 0.1), 6.5))
    screws.append(cad.screw("csk_phillips", "M2", 8, at=(x, y, zb), axis="+Z"))
# a 1 mm boss inside the floor over each rubber foot (its 1.2 mm recess
# leaves the floor whole at any WALL)
FEET = [(x, y) for x in (X0 + 20.0, X1 - 20.0) for y in (Y0 + 14.0, Y1 - 14.0)]
base = cad.fuse_one(base, *[cyl(6.0, (x, y, floor_z(x, y + 6) - 0.5),
                                (floor_z(x, y - 6) + 1.0) - (floor_z(x, y + 6) - 0.5))
                            for x, y in FEET])
tick("base + screws")


def insert(shell, cutter):
    """(shell with the opening, the piece that fills it exactly)."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, piece


# ------------------------------------------------------------ the pad deck
# the pads: a soft block over a skirt through its own opening, two snap
# barbs 0.1 mm under the deck, a plunger to 0.16 mm over its button; the
# block's overhang stands TRAVEL over the deck (that is the stop)
PC = [(GX + sx * (GUT / 2 + PAD / 2), GY + sy * (GUT / 2 + PAD / 2)) for sx, sy in ((-1, 1), (1, 1), (-1, -1), (1, -1))]
SKIRT = PAD - 2 * OVER
Z_SB = ZI - 1.2                                # the skirt's foot
pad_parts = []
openings = []
for (cx, cy), bb in zip(PC, PB):
    blk = zbox(PAD, PAD, PAD_R, cx, cy, Z_TOP + TRAVEL, Z_TOP + TRAVEL + PAD_T)
    blk = cad.soften(blk, 1.5, [e for e in blk.Edges if e.BoundBox.ZMin > Z_TOP + TRAVEL + PAD_T - 1e-3])
    skirt = zbox(SKIRT, SKIRT, PAD_R - OVER, cx, cy, Z_SB, Z_TOP + TRAVEL + 0.5)
    barbs = [box(cx + s * (SKIRT / 2 - 0.5), cx + s * (SKIRT / 2 + 0.9), cy - 8, cy + 8, Z_SB + 0.1, ZI - 0.1)
             if s > 0 else box(cx - SKIRT / 2 - 0.9, cx - SKIRT / 2 + 0.5, cy - 8, cy + 8, Z_SB + 0.1, ZI - 0.1)
             for s in (1, -1)]
    bx, by, _bz = centre(bb)
    plunger = cyl(3.0, (bx, by, bb.ZMax + 0.16), Z_SB + 0.5 - (bb.ZMax + 0.16))
    pad_parts.append(cad.fuse_one(blk, skirt, plunger, *barbs))
    openings.append(zbox(SKIRT + 0.5, SKIRT + 0.5, PAD_R - OVER + 0.25, cx, cy, ZI - 1, Z_TOP + 1))
top = cad.cut(top, openings)


def lattice(z0, z1):
    """The frame round the grid and the cross between the pads, z0..z1."""
    fr = zbox(2 * (HALF + BAR), 2 * (HALF + BAR), PAD_R + BAR, GX, GY, z0, z1)
    return cad.cut(fr, [zbox(PAD, PAD, PAD_R, cx, cy, z0 - 1, z1 + 1) for cx, cy in PC])


# the frosted lattice: inlaid LAT_T deep in the deck over a rib that keeps
# WALL under it, a tab through the deck and the rib over each lit light,
# a light pipe under each tab kept inside its light's footprint
top = cad.fuse_one(top, lattice(ZI - LAT_T, ZI + 0.5))
foot_boxes = [box(lb.XMin, lb.XMax, lb.YMin, lb.YMax, ZI - LAT_T - 1.0, Z_TOP - LAT_T + 0.5) for lb in (LBK, LMD)]
LAT = lattice(ZI - LAT_T - 1.0, Z_TOP + 1)
cutters = [lattice(Z_TOP - LAT_T, Z_TOP + 1)] + [LAT.common(fb) for fb in foot_boxes]
grid = cad.fuse_one(*[top.common(c) for c in cutters])
top = cad.cut(top, cutters)
pipes = [LAT.common(box(lb.XMin + 0.3, lb.XMax - 0.3, lb.YMin + 0.3, lb.YMax - 0.3, lb.ZMax + 0.5, ZI - LAT_T + 0.5))
         for lb in (LBK, LMD)]
grid = cad.fuse_one(grid, *pipes)
# the KIT status lens over light 9: an insert through the deck, a pipe
# down to 0.5 mm over the light, a low dome on top
kx9, ky9, _ = centre(LKT)
top, lens = insert(top, cyl(4.0, (kx9, ky9, ZI - 1), WALL + 2))
lens = cad.fuse_one(lens, cyl(3.4, (kx9, ky9, LKT.ZMax + 0.5), ZI + 0.5 - (LKT.ZMax + 0.5)),
                    Part.makeSphere(4.0, V(kx9, ky9, Z_TOP - 3.3)).common(cyl(4.0, (kx9, ky9, Z_TOP - 0.2), 2.0)))

# ------------------------------------------------------------ the control column
# the dial crown: a cone rising out of the column round the knob, the
# well floor the column top; a frosted ring in it over the knob's LED
# ring with its pipe down to 0.5 mm over the knob's plate
kx, ky, _kz = centre(KB)
K_PLATE = KB.ZMin + 10.1                          # the knob's LED plate
crown = Part.makeCone(FOOT_RC, RIM_R, Z_RIM - (Z_COL - 1.0), V(kx, ky, Z_COL - 1.0))
top = cad.cut(cad.fuse_one(top, crown), cyl(DISH_R, (kx, ky, Z_COL - 0.01), 60))
ring_cut = ring(RING_R[0], RING_R[1], (kx, ky), Z_COL - WALL - 1, Z_COL + 1)
dial_ring = top.common(ring_cut)
top = cad.cut(top, cyl(RING_R[1], (kx, ky, Z_COL - WALL - 1), WALL + 2))
dial_ring = cad.fuse_one(dial_ring, ring(RING_R[0], RING_R[1] - 1.0, (kx, ky), K_PLATE + 0.5, Z_COL - WALL + 0.5))
# the chrome bezel: a ring in a rebate round the crown's rim (it fills it)
reb = ring(DISH_R - 0.5, RIM_R + 1.0, (kx, ky), Z_RIM - 2.2, Z_RIM + 2.5)
dial_bezel = top.common(reb)
top = cad.cut(top, reb)
# the chrome cap: pushed on the knob's shaft (bore 0.45 mm round its 12 mm
# cap), a plug 2 mm into the ring's bore keeps it on its axis
CAP_TOP = KB.ZMax + 2.6
z_cb = Z_COL + 0.6
dial_cap = cad.fuse_one(cyl(CAP_R, (kx, ky, z_cb), CAP_TOP - z_cb),
                        ring(6.45, RING_R[0] - 0.2, (kx, ky), Z_COL - 2.0, z_cb + 0.5))
dial_cap = cad.fillet_safe(dial_cap, 1.5, edges=[e for e in dial_cap.Edges if e.BoundBox.ZMin > CAP_TOP - 0.01])
dial_cap = cad.cut(dial_cap, cyl(6.45, (kx, ky, Z_COL - 3.0), (KB.ZMax + 0.4) - (Z_COL - 3.0)))
# the speaker grille: a brushed disc filling its opening in the column top
gx, gy, _gz = centre(SB)
top, grille = insert(top, cyl(GRILLE_D / 2 + 2.0, (gx, gy, Z_COL - WALL - 1), WALL + 2))
grille = cad.speaker_grille(grille, (gx, gy, Z_COL), (0, 0, 1), GRILLE_D, ring_pitch=2.6, hole=1.6)
# USB-C in the back wall: a pocket brings the wall to 0.25 mm off the mouth
ux, uz = (UB.XMin + UB.XMax) / 2, Z_PCB + 5.9


def yprism(x0, x1, z0, z1, y0, y1, r):
    w = cad.rounded_rect_wire(x1 - x0, z1 - z0, r, ((x0 + x1) / 2, y0, (z0 + z1) / 2), "Y")
    return Part.Face(w).extrude(V(0, y1 - y0, 0))


pocket = yprism(ux - 6.5, ux + 6.5, uz - 5.0, uz + 5.0, UB.YMax + 1.3, Y1 + 5, 3)
liner = cad.cut(yprism(ux - 8.5, ux + 8.5, max(uz - 7.5, SPLIT + 1.6), uz + 7.5, UB.YMax + 0.25, Y1 + 2, 4), pocket)
top = cad.fuse_one(cad.cut(top, pocket), liner.common(skin))
tick("stage A")


# === STAGE B: details ===
# twelve ticks on the dial's chrome bezel
ticks = []
for i in range(12):
    t = box(RIM_R - 2.6, RIM_R + 1.5, -0.45, 0.45, Z_RIM - 0.5, Z_RIM + 1.0)
    t.rotate(V(0, 0, 0), V(0, 0, 1), 30 * i)
    t.translate(V(kx, ky, 0))
    ticks.append(t)
dial_bezel = cad.cut(dial_bezel, ticks, optional=True)
# the cap: a straight knurl round its side, a pointer groove on its face
dial_cap = cad.knurl(dial_cap, "+Z", (kx, ky, z_cb), CAP_R, 1.0, CAP_TOP - z_cb - 2.4, n=40, depth=0.35)
dial_cap = cad.cut(dial_cap, box(kx - 0.6, kx + 0.6, ky + 3.0, ky + CAP_R - 1.6, CAP_TOP - 0.6, CAP_TOP + 0.6))
# legends, the parting-line reveal, a grip groove along the wrist edge
top = cad.text(top, "KIT / VOL", (kx, (ky - FOOT_RC + gy + GRILLE_D / 2 + 2.0) / 2, Z_COL), (0, 0, 1), 3.5,
               depth=0.4, mode="deboss", up=(0, 1, 0))
top = cad.text(top, "ATECH", (gx, (gy - GRILLE_D / 2 - 2.0 + Y0 + EDGE_R) / 2, Z_COL), (0, 0, 1), 5.0,
               depth=0.4, mode="deboss", up=(0, 1, 0))
top = cad.text(top, "KIT", (kx9 - 9.0, ky9, Z_TOP), (0, 0, 1), 3.2, depth=0.4, mode="deboss", up=(0, 1, 0))
top = cad.text(top, "FINGER DRUM", (GX - 22.0, (GY + HALF + BAR + Y1 - EDGE_R) / 2, Z_TOP), (0, 0, 1), 3.2,
               depth=0.4, mode="deboss", up=(0, 1, 0))
top = cad.groove_ring(top, "Z", SPLIT + 2.2, w=0.8, depth=0.6)
Y_GRIP = Y0 + EDGE_R + 2.0
top = cad.cut(top, box(X_RISER + 6, X1 - 2 * CORNER, Y_GRIP - 0.6, Y_GRIP + 0.6, Z_TOP - 0.6, Z_TOP + 1))
pad_parts = [cad.text(p, str(i + 1), (cx - PAD / 2 + 6.0, cy + PAD / 2 - 6.0, Z_TOP + TRAVEL + PAD_T), (0, 0, 1), 4.0,
                      depth=0.4, mode="deboss", up=(0, 1, 0)) for i, (p, (cx, cy)) in enumerate(zip(pad_parts, PC))]
tick("stage B")


# ------------------------------------------------------------ tilt + feet
parts = {"Top": top, "Base": base}
for i, p in enumerate(pad_parts):
    parts["Pad_%d" % (i + 1)] = p
parts.update({"Dial_Cap": dial_cap, "Light_Grid": grid, "Dial_Ring": dial_ring, "Dial_Bezel": dial_bezel,
              "Grille": grille, "Status_Lens": lens})
parts = {k: W_(v) for k, v in parts.items()}
# the USB-C opening is MEASURED from the module, so it is cut after the tilt
parts["Top"] = cad.socket_opening(parts["Top"], usb, margin=1.5)
screws = [W_(s) for s in screws]
# under the base (flat on the desk now): vents, a model mark, rubber feet
B = parts["Base"]
foot_pts = [TILT.multVec(V(x, y, -(y - Y0) * TAN_A)) for x, y in FEET]
mid = TILT.multVec(V(GX, GY + 10.0, -(GY + 10.0 - Y0) * TAN_A))
B = cad.grille(B, (mid.x - 24.0, mid.y, RUB), (0, 0, -1), (34, 22), kind="slot", hole=2.0, pitch=4.5)
B = cad.text(B, "ATECH DP-4", (mid.x + 26.0, mid.y, RUB), (0, 0, -1), 4.5, depth=0.4, mode="deboss",
             up=(0, -1, 0))
rubbers = []
for p in foot_pts:
    B = cad.cut(B, cyl(4.6, (p.x, p.y, RUB - 1), 2.2))
    rubbers.append(cad.foot(9, RUB + 1.2, style="dome", at=(p.x, p.y, RUB + 1.2)))
parts["Base"] = B
tick("tilt + feet")


# ------------------------------------------------------------ parts
def part(name, shape):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    return o


for nm, sh in parts.items():
    o = part(nm, sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS[nm])
    if nm in ("Light_Grid", "Status_Lens", "Dial_Ring"):
        o.ViewObject.Transparency = cad.transparency(COLOURS[nm])
for i, sh in enumerate(rubbers):
    o = part("Rubber_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Rubber"])
for i, sh in enumerate(screws):
    o = part("Screw_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Screw"])
print("SIZE %s" % (cad.measure(Part.makeCompound(list(parts.values())))["size"],))
print("TOTAL %.1f s" % (time.time() - T0))
