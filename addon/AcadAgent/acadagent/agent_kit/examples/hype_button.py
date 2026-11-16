"""Example: "a giant sound button" - the big red do-not-press button that fires airhorns and meme sounds.

fork this file for a giant sound button / big red button / hype button (a
desk buzzer, a game-show button, a panic button); change PARAMETERS and the outlines.
ARCHETYPE: giant button

How it is built (R940):
  * STAGE A - hardware, shell, every working-face opening, fasteners:
    the board FLAT on the pedestal's axis (it centres in a 150 mm drum:
    its corners sit at r 67). TWO buttons (3, 11) sit 41 mm apart under
    the one big cap, so a slap anywhere on the dome closes at least one
    switch; the cap is guided in a collar (a flange under the collar's lip,
    1.0 mm travel to a stop ring) with a plunger down to each button. The
    four corner lights (1, 6, 9, 14) sit at r 54 under a frosted ring
    round the cap. The speaker cannot sit under the cap and look out, so
    it is CABLED from (4, 5) round the left edge and hangs UNDER the board,
    firing down through a grille in the floor into the gap the rubber base
    ring keeps under the pedestal (notches in the ring let the sound out
    all round). USB-C (7) in a pocket in the back wall. The body is ONE
    closed (radius, height) section with both skins in it - collar, lip,
    stop ring, flat deck, rolled edge, a drum that flares to the floor, a
    flange and a recessed plinth - revolved hollow, split into the fixed
    Base and the Shell at the band's foot; four M2.5 screws from below into
    heat-set insert bosses hanging from the deck.
  * STAGE B - details: the yellow hazard band (a ring slid up the drum
    from below, slanted slots through it showing the black drum behind),
    the chrome collar ring, the "PRESS" legend on the dome, lettering,
    the speaker gasket, the rubber base ring with its sound notches.
DETAILS (visible, 26): 1 domed signal-red cap with a rolled knuckle;
2 embossed "PRESS" on the dome; 3 chrome collar ring round the cap;
4 the collar's lip retaining the cap flange; 5 frosted light ring round the
collar (four lit sectors); 6 flat black deck; 7 rolled deck edge; 8 drum
flaring out toward the floor; 9 yellow hazard band with 30 slanted black
stripes; 10 band rails top and bottom; 11 graphite flange under the band;
12 chamfered step into a recessed plinth (the pedestal floats); 13 rubber
base ring with six sound notches; 14 round floor speaker grille (36 mm, 2.1 mm holes);
15 USB-C pocket with a liner in the back; 16 "ATECH" debossed on the deck;
17 "ATECH HB-1" under the base; 18 four countersunk screws from below.
Inside: 19 two plungers; 20 a stop ring under the cap flange (1.0 mm
travel); 21 a bridge from the stop ring onto the board's spine; 22 board
standoffs and edge fences; 23 speaker cradle ribs; 24 a rubber gasket
round the driver on the floor; 25 four bosses with heat-set insert
sleeves; 26 a light pipe sector under the ring over each light.
Materials: signal-red cap, black shell, yellow hazard band, chrome collar
and screws, frosted light ring, graphite base, rubber base ring and gasket.
MEASURED (R940, 2026-11-10): ./check CHECK PASS, run_seconds 11 s, wall 42 s; every RESTYLE end CHECK PASS.
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
    "Shell", "Hazard_Band", "Collar_Ring", "Light_Ring", "Cap", "Gasket", "Rubber_Ring",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4"],
    # the one big cap presses both buttons (a declared cover, see ./check)
    "covers": {"Cap": ["button_p3", "button_p11"]}}
REVIEW_CLOSEUPS = ["Cap", "Hazard_Band", "Light_Ring"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and cutter in
# the stages is derived from them (the cap's dome, the collar's lip and
# stop ring, the bridge under the cap, the deck's roll, the band's slots).
DOME_RISE = 20.0   # RESTYLE 17..23 height: the red dome, collar top to cap top
COLLAR_H = 9.0     # RESTYLE 7.6..10.4 height: the chrome collar above the deck
R_ROLL = 6.0       # RESTYLE 5.1..6.9 radius: the deck's rolled edge
STRIPE_W = 7.0     # RESTYLE 5.9..8.1 width: each black hazard stripe
DECK_T = 2.5       # RESTYLE 2.1..2.9 wall: the deck under the cap and the ring
# end RESTYLE
# every outline below is driven from these numbers - a fork changes the
# silhouette here, never in the stages.
FLOOR0 = 3.0               # base underside (the rubber ring keeps it off the desk)
FLOOR_T = 2.5              # floor thickness
L = 30.5                   # PCB top: the speaker hangs between the floor and the board
DECK = 45.0                # deck top (lights / buttons / USB-C top out at L + 10.2)
COLLAR = (43.6, 45.3, 48.3)    # lip inner radius, tube inner radius, outer radius
CAP_R = 43.2               # cap cylinder radius (0.4 inside the lip)
FLANGE_R, FLANGE_H = 45.0, 3.1
TRAVEL = 1.0               # cap travel down to the stop ring
DOME_R, KNUCKLE = 70.0, 6.0   # dome sphere radius, knuckle radius
CAP_TOP = DECK + COLLAR_H + DOME_RISE
CAP_T = 2.5
R_SHOULDER = 72.0          # drum radius under the roll
R_FLARE = 75.5             # drum radius at the band's foot (the widest point)
WALL_SIDE = 4.3
BAND = (14.0, 30.0, 1.8)   # hazard band z0, z1, thickness
STRIPES, RAIL = 30, 1.5
R_PLINTH = 71.5            # recessed plinth radius
RING = (48.6, 61.0)        # light ring radii (the corner lights sit at r 54)
SCREW = "M2.5"
SCREW_R, SCREW_ANG = 60.0, (35, 145, 215, 325)
RUBBER = (64.5, 68.5, 3.0)  # base ring radii, height under the floor
COLOURS = {"Base": "graphite", "Shell": "matte_black", "Hazard_Band": "toy_yellow",
           "Collar_Ring": "chrome", "Light_Ring": "frosted", "Cap": "signal_red",
           "Gasket": "rubber", "Rubber_Ring": "rubber", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
FLAT = Rotation(Vector(1, 0, 0), 90)
board = ap.board_object(doc)
board.Placement = Placement(Vector(0, 0, L), FLAT)     # x 0..60, y -120..0
BB = ap.bbox(board)
CX, CY = (BB.XMin + BB.XMax) / 2, (BB.YMin + BB.YMax) / 2   # the pedestal's axis
btn_l = ap.seat(doc, "button", 3)
btn_r = ap.seat(doc, "button", 11)
usb = ap.seat(doc, "usbc", 7)                          # back, mouth +Y
lights = [ap.seat(doc, "light", n) for n in (1, 6, 9, 14)]
# the speaker under the board, firing down: centred on its ports' row so
# both ribbons run straight out of the left edge and loop back under
PCB0 = L - 2.5
SPK_C = (CX, -80.0, PCB0 - 0.6 - 10.1)
spk, spk_ribs = ap.cable(doc, "speaker", (4, 5), ap.module_placement(
    "speaker", SPK_C, face="-Z", cable="-X"), via={4: [(-9, -70, L - 6)], 5: [(-9, -90, L - 6)]})
SB = ap.bbox(spk)
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


def r_out(z):
    """The drum's outside radius at height z (a straight flare)."""
    return R_SHOULDER + (DECK - R_ROLL - z) * (R_FLARE - R_SHOULDER) / (DECK - R_ROLL - BAND[0])


def r_in(z):
    return r_out(z) - WALL_SIDE


CT = DECK + COLLAR_H                   # collar top
LIP0 = CT - 2.5                        # lip underside
STOP = LIP0 - 0.1 - FLANGE_H - TRAVEL  # stop ring top
Z_ROLL = DECK - R_ROLL
section = [
    (COLLAR[0], CT), (COLLAR[2] - 1.0, CT), arc((COLLAR[2] - 1.0, CT - 1.0), 1.0, 90, 0),   # collar top
    (COLLAR[2], DECK), (R_SHOULDER - R_ROLL, DECK), arc((R_SHOULDER - R_ROLL, Z_ROLL), R_ROLL, 90, 0),
    (r_out(BAND[0]), BAND[0]), (r_out(BAND[0]), BAND[0] - 1.7),            # drum flare, flange
    (r_out(BAND[0]) - 1.5, BAND[0] - 3.2), (R_PLINTH, BAND[0] - 3.2),       # chamfered step
    (R_PLINTH, FLOOR0 + 1.8), arc((R_PLINTH - 1.8, FLOOR0 + 1.8), 1.8, 0, -90), (0, FLOOR0),
    (0, FLOOR0 + FLOOR_T), (R_PLINTH - 2.5, FLOOR0 + FLOOR_T),              # floor, plinth inside
    (R_PLINTH - 2.5, BAND[0] - 1.5), (r_in(BAND[0] - 1.5), BAND[0] - 1.5),
    (r_in(Z_ROLL), Z_ROLL), (r_in(Z_ROLL), DECK - DECK_T - 0.8),          # drum inside (it rises
    (R_SHOULDER - R_ROLL - 2.0, DECK - DECK_T),                            # clear of the corner lights)
    (COLLAR[0] + 0.3, DECK - DECK_T), (COLLAR[0] + 0.3, STOP), (COLLAR[1], STOP),   # stop ring
    (COLLAR[1], LIP0), (COLLAR[0], LIP0),                                   # collar tube, lip
]
body = cad.revolve_profile(section, at=(CX, CY, 0))
# the hazard band: a ring slid up the flare from below onto its seat (it
# stops at the shoulder; the base's flange holds it), 30 slanted slots
# through it show the black drum behind
bseat = cad.revolve_profile([(r_out(BAND[1]) - BAND[2], BAND[1]), (r_out(BAND[1]) + 1.0, BAND[1]),
                             (r_out(BAND[0]) + 1.0, BAND[0]), (r_out(BAND[0]) - BAND[2], BAND[0])],
                            at=(CX, CY, 0))
band = body.common(bseat)
body = cad.cut(body, bseat)
H = BAND[1] - BAND[0] - 2 * RAIL
slots = []
for i in range(STRIPES):
    a = 360.0 * i / STRIPES
    z0 = BAND[0] + RAIL
    r0 = r_in(BAND[0]) - 1.0
    f = Part.Face(Part.makePolygon([V(r0, -STRIPE_W / 2 - H / 2, z0), V(r0, STRIPE_W / 2 - H / 2, z0),
                                    V(r0, STRIPE_W / 2 + H / 2, z0 + H), V(r0, -STRIPE_W / 2 + H / 2, z0 + H),
                                    V(r0, -STRIPE_W / 2 - H / 2, z0)]))
    s = f.extrude(V(R_FLARE + 3 - r0, 0, 0))
    s.rotate(V(0, 0, 0), V(0, 0, 1), a)
    s.translate(V(CX, CY, 0))
    slots.append(s)
band = cad.cut(band, slots)
tick("body")
base, shell = cad.split(body, "Z", at=BAND[0], lip=1.2)
tick("split")

# the fixed base holds the board: standoffs under it (0.1 mm below), fences
# 0.3 mm off its long edges clear of the speaker ribbons - all below the
# modules' slide paths; ribs 0.25 mm off the speaker's front and back
FL1 = FLOOR0 + FLOOR_T
holders = [box(x - 3, x + 3, y - 3, y + 3, FL1 - 0.5, PCB0 - 0.1)
           for x in (BB.XMin + 12, BB.XMax - 12) for y in (BB.YMax - 12, BB.YMin + 12)]
holders += [box(x0, x1, y - 4, y + 4, FL1 - 0.5, L - 1.0)
            for x0, x1, ys in ((BB.XMin - 1.8, BB.XMin - 0.3, (-30, -110)),
                               (BB.XMax + 0.3, BB.XMax + 1.8, (-30, -90))) for y in ys]
holders += [box(SB.XMin + 12, SB.XMax - 8, y0, y1, FL1 - 0.5, SB.ZMin + 12)
            for y0, y1 in ((SB.YMin - 1.45, SB.YMin - 0.25), (SB.YMax + 0.25, SB.YMax + 1.45))]
base = cad.fuse_one(base, *holders)
# board hold-down: a bridge across the stop ring, under the cap's travel,
# with a post onto the board's spine (0.2 mm off)
BR_Z0 = STOP - 2.5
shell = cad.fuse_one(shell, box(CX - 2, CX + 2, CY - COLLAR[0] - 0.8, CY + COLLAR[0] + 0.8, BR_Z0, STOP - 0.5),
                     box(CX - 2, CX + 2, CY - 12, CY + 12, L + 4.5 + 0.2, BR_Z0 + 0.5))
# fasteners: four M2.5 up through the floor into bosses hanging from the
# deck, each with a heat-set insert pocket (1.4 d + 0.1) in a sleeve
INSERT_D = {"M2": 3.2, "M2.5": 3.6, "M3": 4.3}[SCREW]
PILOT_D = {"M2": 1.7, "M2.5": 2.1, "M3": 2.5}[SCREW]
D_SCREW = float(SCREW[1:])
screws, cols, bores, csks = [], [], [], []
for a in SCREW_ANG:
    x, y = CX + SCREW_R * math.cos(math.radians(a)), CY + SCREW_R * math.sin(math.radians(a))
    # one column from 0.1 mm over the floor up into the deck, a heat-set
    # insert pocket at its foot and the thread-forming pilot above it -
    # every boss in ONE fuse and ONE cut (R940: four screw_boss calls on
    # the revolved shell cost most of this stage)
    cols.append(cyl(INSERT_D / 2 + 1.2, (x, y, FL1 + 0.1), (DECK - DECK_T + 0.5) - (FL1 + 0.1)))
    bores.append(cyl(INSERT_D / 2, (x, y, FL1), 9.0))
    bores.append(cyl(PILOT_D / 2, (x, y, FL1 + 8.0), 2.5 * D_SCREW + 2.0))
    # a 90 deg countersink through the floor (cone + clearance hole)
    csks.append(Part.makeCone(5.6 / 2, 2.9 / 2, (5.6 - 2.9) / 2, V(x, y, FLOOR0 - 0.01), V(0, 0, 1)))
    csks.append(cyl(2.9 / 2, (x, y, FLOOR0 - 0.5), FLOOR_T + 1.0))
    screws.append(cad.screw("csk_phillips", SCREW, 10, at=(x, y, FLOOR0), axis="+Z"))
shell = cad.cut(cad.fuse_one(shell, *cols), bores)
base = cad.cut(base, csks)
tick("base + screws")

# the light ring: a frosted annulus in a recess in the deck, with a sector
# tab down through the deck over each light - the deck stays one piece
RECESS = 1.2


def sector(r0, r1, a_mid, half, z0, z1):
    n = 6
    pts = [V(CX + r1 * math.cos(math.radians(a_mid - half + 2 * half * i / n)),
             CY + r1 * math.sin(math.radians(a_mid - half + 2 * half * i / n)), z0) for i in range(n + 1)]
    pts += [V(CX + r0 * math.cos(math.radians(a_mid + half - 2 * half * i / n)),
              CY + r0 * math.sin(math.radians(a_mid + half - 2 * half * i / n)), z0) for i in range(n + 1)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, z1 - z0))


LIGHT_ANG = [math.degrees(math.atan2(y - CY, x - CX)) for x, y in map(centre, lights)]
cutters = [annulus(RING[0], RING[1], DECK - RECESS, DECK + 1)]
cutters += [sector(RING[0], RING[1], a, 12, DECK - DECK_T - 1, DECK - RECESS + 0.5) for a in LIGHT_ANG]
ring = cad.fuse_one(*[shell.common(c) for c in cutters])
shell = cad.cut(shell, cutters)
LT = max(ap.bbox(m).ZMax for m in lights)
# a light pipe under each tab, kept inside its light's footprint (port 7's
# USB-C stands right beside the back pair)
pipes = []
for m, a in zip(lights, LIGHT_ANG):
    lb = ap.bbox(m)
    pipes.append(sector(RING[0] + 0.1, RING[1] - 0.1, a, 11.5, LT + 0.5, DECK - DECK_T + 0.5)
                 .common(box(lb.XMin, lb.XMax, lb.YMin, lb.YMax, LT, DECK)))
ring = cad.fuse_one(ring, *pipes)
# USB-C at the back: a pocket brings the wall to 0.25 mm off the mouth
ub = ap.bbox(usb)
uz = L + 5.9
pocket = cad.rounded_box(18, 40, 10, 3, at=(CX - 9, ub.YMax + 1.3, uz - 5), edges="y")
liner = cad.cut(cad.rounded_box(22, 30, 14, 4, at=(CX - 11, ub.YMax + 0.25, uz - 7), edges="y")
                .common(cyl(r_in(uz) + 1.0, (CX, CY, 0), DECK)), pocket)
shell = cad.fuse_one(cad.cut(shell, pocket), liner)
shell = cad.socket_opening(shell, usb, margin=1.5)
# the speaker fires down: a round grille in the floor under the driver
# (grilled on a plain floor disc, then the holes cut from the base in ONE
# cut - R940: grilling the whole base measured every hole on it, 56 s)
plate = cyl(21.0, (SPK_C[0], SPK_C[1], FLOOR0), FLOOR_T)
holes = plate.cut(cad.speaker_grille(plate, (SPK_C[0], SPK_C[1], FLOOR0), (0, 0, -1), 36, ring_pitch=2.6, hole=2.1))
base = cad.cut(base, holes)

# the cap: ONE revolved section - a dome on a rolled knuckle, the cylinder
# through the collar's lip, a flange under the lip (0.1 mm) and 1.0 mm
# above the stop ring; hollow, a plunger to 0.16 mm over each button
CC = (0, CAP_TOP - DOME_R)                                # dome centre (r, z)
KC = (CAP_R - KNUCKLE, CC[1] + math.sqrt((DOME_R - KNUCKLE) ** 2 - (CAP_R - KNUCKLE) ** 2))
PHI = math.degrees(math.atan2(KC[1] - CC[1], KC[0]))
FL0 = LIP0 - 0.1 - FLANGE_H
RI = CAP_R - CAP_T
cap_sec = [
    (0, CAP_TOP), arc(CC, DOME_R, 90, PHI), arc(KC, KNUCKLE, PHI, 0),
    (CAP_R, LIP0 - 0.1), (FLANGE_R, LIP0 - 0.1), (FLANGE_R, FL0), (RI, FL0),
    (RI, KC[1]), arc(KC, KNUCKLE - CAP_T, 0, PHI), arc(CC, DOME_R - CAP_T, PHI, 90),
]
cap = cad.revolve_profile(cap_sec, at=(CX, CY, 0))
plungers = []
for m in (btn_l, btn_r):
    x, y = centre(m)
    mz = ap.bbox(m).ZMax
    rr = math.hypot(x - CX, y - CY)
    z_in = CC[1] + math.sqrt((DOME_R - CAP_T) ** 2 - rr ** 2)
    plungers.append(cyl(3.0, (x, y, mz + 0.16), z_in + 0.6 - (mz + 0.16)))
    plungers.append(cyl(4.5, (x, y, z_in - 4.0), 4.6))                    # a root boss
cap = cad.fuse_one(cap, *plungers)
tick("stage A")


# === STAGE B: details ===
# the chrome collar: the collar's outer skin and top as its own ring,
# keyed 1 mm into the deck
ccut = annulus(COLLAR[1] + 1.2, COLLAR[2] + 1.0, DECK - 1.0, CT + 1.0)
collar = shell.common(ccut)
shell = cad.cut(shell, ccut)
# "PRESS" on the dome, read from the front
cap = cad.text(cap, "PRESS", (CX, CY, CAP_TOP), (0, 0, 1), 13, depth=1.2, mode="emboss", up=(0, 1, 0))
# lettering on the deck's front and under the base
RT = (RING[1] + R_SHOULDER - R_ROLL) / 2
shell = cad.text(shell, "ATECH", (CX, CY - RT, DECK), (0, 0, 1), 3.2, depth=0.4, mode="deboss", up=(0, 1, 0))
base = cad.text(base, "ATECH HB-1", (CX, CY + 30, FLOOR0), (0, 0, -1), 6, depth=0.4, mode="deboss",
                up=(0, -1, 0))
# a rubber gasket round the driver, in a groove in the floor, 0.2 mm under it
sx, sy = SPK_C[0], SPK_C[1]
groove = annulus(19.2, 20.2, FL1 - 0.6, FL1 + 0.1, (sx, sy))
base = cad.cut(base, groove)
gasket = annulus(19.3, 20.1, FL1 - 0.6, SB.ZMin - 0.2, (sx, sy))
# the rubber base ring in a groove under the floor, six notches in its
# tread let the down-firing speaker breathe out all round
base = cad.cut(base, annulus(RUBBER[0], RUBBER[1], FLOOR0 - 0.1, FLOOR0 + 1.0))
rubber = annulus(RUBBER[0] + 0.1, RUBBER[1] - 0.1, FLOOR0 - RUBBER[2], FLOOR0 + 1.0)
rubber = cad.cut(rubber, [box(-6, 6, -80, 80, FLOOR0 - RUBBER[2] - 1, FLOOR0 - RUBBER[2] + 1.2)
                          .rotated(V(0, 0, 0), V(0, 0, 1), a).translated(V(CX, CY, 0)) for a in (0, 60, 120)])
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
o = part("Hazard_Band", band)
o.ViewObject.ShapeColor = cad.color(COLOURS["Hazard_Band"])
o = part("Collar_Ring", collar)
o.ViewObject.ShapeColor = cad.color(COLOURS["Collar_Ring"])
o = part("Light_Ring", ring)
o.ViewObject.ShapeColor = cad.color(COLOURS["Light_Ring"])
o.ViewObject.Transparency = cad.transparency(COLOURS["Light_Ring"])
o = part("Cap", cap)
o.ViewObject.ShapeColor = cad.color(COLOURS["Cap"])
o = part("Gasket", gasket)
o.ViewObject.ShapeColor = cad.color(COLOURS["Gasket"])
o = part("Rubber_Ring", rubber)
o.ViewObject.ShapeColor = cad.color(COLOURS["Rubber_Ring"])
for i, sh in enumerate(screws):
    o = part("Screw_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Screw"])
print("SIZE %s" % (cad.measure(Part.makeCompound([base, shell, cap, rubber]))["size"],))
print("SIZE model build %.1f s" % (time.time() - T0))
