"""Example: "a piggy bank that counts your coins" - a chunky glossy-pink pig that sees every coin drop, shows the total saved and oinks.

fork this file for a piggy bank / coin bank / money box (a counting savings
jar, a coin pig, any character box that swallows things); change PARAMETERS and the outlines.
ARCHETYPE: piggy bank

How it is built (R990):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board UPRIGHT along the pig's left half (its plane x = -27, long side
    along the body, modules facing +X toward the middle; port 7 at the
    tail, ports 8 and 12 empty for the firmware). A PARTITION standing on
    the Base (a long wall beside the board's modules plus a cross wall
    each end) walls the COIN CHAMBER off from the electronics: the coins
    live in the right two thirds, the board, the screen and their ribbons
    in the left third, the speaker in the head. The ToF distance sensor
    SEATED on 3 looks across the chamber, through an open aperture in the
    partition, 18 mm under the coin slot on the back: each coin falls
    through its beam (its rays leave through the clear coin window in the
    right flank, so you also see your savings). The screen is CABLED from
    (10, 11) under the board and out to the left flank, behind a curved
    smoked visor in a raised rose bezel (the bezel's ribs hold it); the speaker
    is CABLED from (4, 5) over the board's top edge into the head, firing
    down the hollow snout through the nostrils and a ring of pores (it
    oinks through its nose). USB-C SEATED on 7 behind a pocket + liner in
    the rump under the tail. The body is a capsule on a level axis (two
    exact spheres and a cylinder: fast booleans, a fair surface, the inside
    the same capsule WALL smaller) cut flat under the belly, the snout
    fused on and rounded, then cut 6 mm over the flat (where the wall is
    steep enough for a square seam: no knife edge) into the fixed
    Base (floor, legs, lip ring, partition, board posts and pads) and the
    Body; five M2.5 screws come up through the floor into heat-set insert
    lugs on the walls. The coins come out through a twist-lock floor plug
    (two bayonet lugs over the floor, in notches of its hole).
  * STAGE B - details: ears pinned on the head, eyes with glints on pegs,
    rosy cheek inlays, a smile, a corkscrew tail pinned in the rump, hooves
    with a cleft pinned under the legs, lettering.
RESTYLE (R425): SNOUT_L, SNOUT_R, EAR_H, LEG_H and WALL drive the snout
(its length, radius, the nostrils and the pore ring), the ears, the legs
(the whole pig rides on them: every height is ZC-relative) and every wall,
core and cutter. R and H (the body's radius and barrel) are set by the
board: its corners need the 58 mm radius and 29 mm barrel (sized below).
DETAILS (visible, 30): 1 capsule body cut flat under the belly; 2 snout
fused on with a rounded junction; 3 rounded snout rim; 4 the darker snout
disc; 5-6 two oval nostrils (the speaker's sound holes); 7 a ring of 18
pores round them; 8-9 two pointed ears pinned on, tipped forward; 10-11
black domed eyes on pegs; 12-13 a white glint in each; 14-15 rosy cheek
inlays; 16 a smile groove under the snout; 17 the gold coin-slot plate
standing proud; 18 the coin slot; 19 the curved smoked visor over the
screen; 20 its raised rose frame; 21 the clear coin window in the right flank;
22 its gold ring; 23 a corkscrew tail pinned in the rump; 24 USB-C pocket
with liner under it; 25-28 four stubby legs flowing out of the belly with
dark hooves, each with a cleft; 29 the twist-lock coin plug with a grip
bar under the belly; 30 "ATECH" and "OINK" lettering, five countersunk
screws under the belly.
Inside: the partition with the ToF aperture, the board posts with fences
and spine pads, the bezel's screen ribs, speaker ribs from the head wall,
insert lugs and sleeves, the base's lip ring, the plug's bayonet lugs.
Materials: glossy pink body, rose base and legs, deep rose snout disc and
hooves, pink ears, black eyes with white glints, coral cheeks, gold slot
plate and window ring, smoked visor in a deep rose bezel, clear coin window,
rose plug, chrome screws.
MEASURED (R990, 2026-11-17): ./check CHECK PASS, run_seconds 13 s, wall 36 s; every RESTYLE end CHECK PASS.
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
    "Body", "Snout_Disc", "Bezel", "Visor", "Slot_Plate", "Coin_Window", "Window_Ring",
    "Ear_L", "Ear_R", "Eye_L", "Eye_R", "Glint_L", "Glint_R", "Cheek_L", "Cheek_R", "Tail",
    "Coin_Plug", "Hoof_1", "Hoof_2", "Hoof_3", "Hoof_4",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4", "Screw_5"]}
REVIEW_CLOSEUPS = ["Snout_Disc", "Visor", "Slot_Plate", "Coin_Plug"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them. (The body's radius R and
# barrel H are set by the board inside: they are below.)
SNOUT_L = 10.0     # RESTYLE 8.5..11.5 length: how far the snout stands out of the face (-y)
SNOUT_R = 22.0     # RESTYLE 18.5..25.5 radius: the snout disc
EAR_H = 24.0       # RESTYLE 20..28 height: the ears, root to tip
LEG_H = 16.0       # RESTYLE 13.5..18.5 height: the legs under the flat belly (the whole pig rides on them)
WALL = 2.4         # RESTYLE 2.0..2.8 wall
# end RESTYLE
# Frame: the pig's axis runs along y at x = 0, z = ZC, the head at -Y
# (FreeCAD's front), its left flank at -X (the hero view's side). The board
# stands upright at x -29.8..-22.8 (PCB top, the modules' seat, at XB).
R = 58.0                         # the body's radius (the board's corners need 55.6 inside)
H = 29.0                         # half the straight barrel (sphere centres at y = -+H)
FLAT = 48.0                      # the belly is cut flat this far under the axis
ZFLAT = LEG_H                    # the belly's underside (the legs stand it up)
ZC = ZFLAT + FLAT                # the body's axis height
XB = -27.3                       # the board's module face (its back at XB - 2.5)
YB1 = 62.0                       # the board's tail end (port 7, the USB-C)
CORNER = 7.0                     # the round where the snout meets the face
ZS = ZC - 8.0                    # the snout's (and the speaker's) axis height
CHUTE = 18.0                     # the coin's path: this far from the partition, under the slot
SLOT = (31.0, 3.6)               # the coin slot (y, x): every coin up to 30.6 mm, 3.2 thick
PLUG = (10.0, 18.0, 15.0)        # the coin plug: centre x, y, hole radius
EYE = (28.0, 22.0)               # the eyes: azimuth from the nose, elevation (deg)
EAR = (40.0, 50.0)               # the ears' roots: azimuth, elevation (deg)
LEGS = [(-27.0, -44.0), (27.0, -44.0), (-27.0, 44.0), (27.0, 44.0)]
LEG_R = 13.0
SCREW = "M2.5"
SCREWS = [(-24.0, -15.0, "-X"), (-12.0, 50.0, "-X"), (24.0, -16.0, "+X"), (0.0, -54.0, "-Y"), (12.0, -36.0, "+X")]
COLOURS = {"Body": "#f6a5bd", "Base": "#e98aa7", "Snout_Disc": "#d9637f", "Ear": "#f294b0",
           "Eye": "matte_black", "Glint": "matte_white", "Cheek": "#ff7f8e", "Slot_Plate": "brass",
           "Bezel": "#d9637f", "Visor": "smoked", "Coin_Window": "glass", "Window_Ring": "brass",
           "Tail": "#f6a5bd", "Coin_Plug": "#d9637f", "Hoof": "#b54a68", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
R_IN = R - WALL
# the board upright: local x -> world -Z (ports 1-6 along the top edge),
# local y (the module side) -> +X, local z -> -Y (port 7 at the tail)
UPRIGHT_SIDE = Rotation(App.Matrix(0, 1, 0, 0, 0, 0, -1, 0, -1, 0, 0, 0, 0, 0, 0, 1))
board = ap.board_object(doc)
board.Placement = Placement(Vector(XB, YB1, ZC + 30.0), UPRIGHT_SIDE)   # x -29.8..-22.8, y -58..62, z ZC-30..ZC+30
BB = ap.bbox(board)
sen = ap.seat(doc, "distance_sensor", 3)      # top edge, faces +X across the chamber
usb = ap.seat(doc, "usbc", 7)                 # the tail end, mouth +Y
SEN, UB = ap.bbox(sen), ap.bbox(usb)
PA0 = SEN.XMax + 0.4                          # the partition (its electronics face)
PA1 = PA0 + WALL                              # ... and its coin face
YA = -5.0                                     # the chamber's front wall (behind the speaker's ribbons)
YB = UB.YMin - 0.5                            # the chamber's back wall (in front of the USB-C)
SEN_Y, SEN_Z = (SEN.YMin + SEN.YMax) / 2, (SEN.ZMin + SEN.ZMax) / 2


def r_in(y, d=0.0):
    """The body's inside radius at y (its surface moved d out)."""
    c = min(max(y, -H), H)
    return math.sqrt(max(0.0, (R_IN + d) ** 2 - (y - c) ** 2))


# the speaker in the head, facing -Y down the snout, pins up: its ribbons
# rise over the board's top edge from (4, 5), run forward at the top of the
# head and drop into its top (4 runs wide behind the board, left of 5's riser:
# they never cross)
SPK_DZ = max(abs(ZS - 20 - ZC), abs(ZS + 20 - ZC))
SPK_FACE_Y = next(-H - 0.1 * i for i in range(800) if r_in(-H - 0.1 * i) < math.hypot(20.0, SPK_DZ) + 1.0) + 0.1
spk_pl = ap.module_placement("speaker", (0.0, SPK_FACE_Y + 20.2 / 2, ZS), face="-Y", cable="+Z")
SPK_PIN_Y, SPK_TOP = SPK_FACE_Y + 20.2 - 1.4, ZS + 20.0
spk, spk_rib = ap.cable(doc, "speaker", (4, 5), spk_pl, via={
    4: [(XB + 0.5, -8.2, ZC + 35.0), (-31.0, -16.0, ZC + 36.0), (-34.0, -28.0, ZC + 36.0), (-32.0, -40.0, ZC + 36.5),
        (-24.0, -48.0, ZC + 37.0), (-10.0, SPK_PIN_Y, SPK_TOP + 22.25), (-10.0, SPK_PIN_Y, SPK_TOP + 18.25)],
    5: [(XB + 0.5, -28.1, ZC + 34.5), (-14.0, -34.0, ZC + 35.5), (2.0, -44.0, ZC + 36.0),
        (10.0, SPK_PIN_Y, SPK_TOP + 22.25), (10.0, SPK_PIN_Y, SPK_TOP + 18.25)]}, smooth=True)
SB = ap.bbox(spk)
# the screen on the left flank, facing -X, pins down: its ribbons leave
# the bottom edge (10, 11), loop under and rise into its foot
SCR_Y, SCR_Z = 22.0, ZC                       # between ports 10 and 11: straight loops
BZ_BACK = -51.2                               # the bezel's back (the screen 0.3 mm behind it)
SCR_FACE_X = BZ_BACK + 0.3
scr_pl = ap.module_placement("screen", (SCR_FACE_X + 9.64 / 2, SCR_Y, SCR_Z), face="-X", cable="-Z")
SCR_PIN_X, SCR_FOOT = SCR_FACE_X + 9.64 - 1.4, SCR_Z - 9.75
scr, scr_rib = ap.cable(doc, "screen", (10, 11), scr_pl, via={
    p: [(XB + 1.2, y, ZC - 34.5), (XB - 8.0, y, ZC - 36.0),
        (SCR_PIN_X + 0.8, y, SCR_FOOT - 22.25), (SCR_PIN_X, y, SCR_FOOT - 18.25)]
    for p, y in ((10, 32.0), (11, 12.0))}, smooth=True)
SC = ap.bbox(scr)
tick("hardware")


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, d, h):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def egg_solid(d=0.0):
    """The capsule (its surface moved d out) as one solid."""
    return cad.fuse_one(Part.makeSphere(R + d, V(0, -H, ZC)).fuse([
        Part.makeCylinder(R + d, 2 * H, V(0, -H, ZC), V(0, 1, 0)),
        Part.makeSphere(R + d, V(0, H, ZC))]).removeSplitter())


def snout_solid(d=0.0, y1=None):
    """The snout cylinder (radius moved d) from inside the head to its face."""
    y0 = -H - R * 0.55
    y1 = YSN if y1 is None else y1
    return cyl(SNOUT_R + d, (0, y0, ZS), (0, -1, 0), y0 - y1)


def hit(shape, p, d, reach=400.0):
    """The first point where the ray from p along d enters `shape`."""
    p, d = V(*p), V(*d)
    d.normalize()
    sec = shape.section(Part.makeLine(p, p + d * reach))
    pts = sorted((v.Point for v in sec.Vertexes), key=lambda q: (q - p).Length)
    if not pts:
        raise cad.CadError("hit: the ray from %s along %s misses" % (p, d))
    return pts[0]


def on_sphere(c, az, el, r):
    """A point on the sphere (c, r): azimuth from -Y toward +X, elevation (deg)."""
    a, e = math.radians(az), math.radians(el)
    d = V(math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))
    return c + d * r, d


# ------------------------------------------------------------ the hull
HEADC = V(0, -H, ZC)
YSN = -H - math.sqrt(R ** 2 - (ZS - ZC) ** 2) - SNOUT_L      # the snout's face
SKY = box(-200, 200, -300, 300, ZFLAT, 400)
egg = egg_solid().common(SKY)
snout = snout_solid()
snout = cad.soften(snout, 4.0, [e for e in snout.Edges if abs(e.BoundBox.YMax - YSN) < 0.01])
outer = cad.fuse_one(egg, snout)
outer = cad.soften(outer, CORNER, cad.new_edges(outer, Part.makeCompound([egg, snout])))
core = cad.fuse_one(egg_solid(-WALL).common(box(-200, 200, -300, 300, ZFLAT + WALL, 400)),
                    snout_solid(-WALL, YSN + WALL))
INNER = egg_solid(-WALL - 0.3)               # the base's parts stop 0.3 mm inside the body
skin = cad.fuse_one(egg_solid(-0.6), snout_solid(-0.6))   # ribs and lugs stop inside the skin
hull = cad.cut(outer, core)
tick("hull")

# insert lugs on the walls just above the floor
SPLIT_Z = ZC - 42.0                  # where the wall is steep enough (> 40 deg) for a square seam
FLOOR_TOP = ZFLAT + WALL
INSERT_D = {"M2": 3.2, "M2.5": 3.6, "M3": 4.3}[SCREW]
LUG_Z0, LUG_Z1 = SPLIT_Z + 2.8, SPLIT_Z + 11.0      # over the base's lip, under the speaker
lugs = []
for x, y, way in SCREWS:
    a = INSERT_D / 2 + 1.4
    far = {"-X": (x + a, -100, y - a, y + a), "+X": (x - a, 100, y - a, y + a),
           "-Y": (x - a, x + a, y + a, -200), "+Y": (x - a, x + a, y - a, 200)}[way]
    lugs.append(box(far[0], far[1], far[2], far[3], LUG_Z0, LUG_Z1))
hull = cad.fuse_one(hull, *[g.common(skin) for g in lugs])
tick("lugs")

# split just above the floor: the fixed Base (floor, lip ring) and the Body
base = hull.common(box(-200, 200, -300, 300, -10, SPLIT_Z))
body = hull.common(box(-200, 200, -300, 300, SPLIT_Z, 400))
lip = cad.cut(egg_solid(-WALL - 0.15), egg_solid(-WALL - 1.55)).common(
    box(-200, 200, -300, 300, FLOOR_TOP - 0.2, SPLIT_Z + 2.5))
base = cad.fuse_one(base, lip)
tick("split")

# the partition: a long wall beside the modules and a cross wall at each
# end - the coins stay on the +X side; an open aperture for the ToF
walls = [box(PA0, PA1, YA - WALL, YB, FLOOR_TOP - 0.5, 300),
         box(PA0, 100, YA - WALL, YA, FLOOR_TOP - 0.5, 300),
         box(PA0, 100, YB - WALL, YB, FLOOR_TOP - 0.5, 300)]
part_wall = cad.fuse_one(*[w.common(INNER) for w in walls])
part_wall = cad.cut(part_wall, box(PA0 - 1, PA1 + 1, SEN_Y - 6.0, SEN_Y + 6.0, SEN_Z - 4.0, SEN_Z + 4.0))
# the board: posts under its bottom edge between the port housings, each
# with a fence behind the PCB, and pads from the partition onto its spine
holders = []
for y in (42.0, 2.0, -38.0):
    holders.append(box(XB - 4.3, XB, y - 1.5, y + 1.5, FLOOR_TOP - 0.5, BB.ZMin - 0.1))
    holders.append(box(XB - 4.3, BB.XMin - 0.3, y - 1.5, y + 1.5, BB.ZMin - 0.5, BB.ZMin + 4.0))
for y in (6.0, 24.0, 36.0):
    holders.append(box(BB.XMax + 0.2, PA0 + 0.5, y - 2.0, y + 2.0, ZC - 4.0, ZC + 4.0))
base = cad.fuse_one(base, part_wall, *[h.common(INNER) for h in holders])
tick("partition")

# screws: up through the floor into heat-set insert pockets in the lugs; a
# short sleeve under each lug stands 0.1 mm over the floor
screws = []
body = cad.fuse_one(body, *[cyl(INSERT_D / 2 + 1.4, (x, y, FLOOR_TOP + 0.1), (0, 0, 1), LUG_Z0 + 1.5 - FLOOR_TOP)
                            for x, y, _w in SCREWS])
body = cad.cut(body, [cyl(INSERT_D / 2, (x, y, FLOOR_TOP), (0, 0, 1), 9.0) for x, y, _w in SCREWS])
for x, y, _w in SCREWS:
    base = cad.countersink(base, (x, y, ZFLAT), "+Z", 2.9, 5.6, 90.0)
    screws.append(cad.screw("csk_phillips", SCREW, 10, at=(x, y, ZFLAT), axis="+Z"))
tick("screws")

# ------------------------------------------------------------ the legs
# stubby legs flowing out of the belly: each a short cylinder up into the
# base, clipped 0.2 mm off the Body's skin and out of the cavity
up_body = egg_solid(0.2).common(box(-200, 200, -300, 300, SPLIT_Z, 400))
legs = []
for x, y in LEGS:
    lg = cyl(LEG_R, (x, y, 3.0), (0, 0, 1), SPLIT_Z + 14.0 - 3.0)
    legs.append(cad.cut(lg, [up_body, core]))
base = cad.fuse_one(base, *legs)
# a bore up each leg for its hoof's peg
base = cad.cut(base, [cyl(2.65, (x, y, 2.0), (0, 0, 1), 6.0) for x, y in LEGS])
tick("legs")

# ------------------------------------------------------------ the coin plug
# a round hole in the floor under the chamber, a flush seat for the plug's
# flange under it and two notches its bayonet lugs pass through
PX, PY, PR = PLUG
SEAT_R, SEAT_D = PR + 3.5, 1.2
notches = [box(-2.6, 2.6, -PR - 3.2, PR + 3.2, ZFLAT - 1, FLOOR_TOP + 1).rotated(V(0, 0, 0), V(0, 0, 1), 0)
           .translated(V(PX, PY, 0))]
base = cad.cut(base, [cyl(PR + 0.15, (PX, PY, ZFLAT - 1), (0, 0, 1), WALL + 2),
                      cyl(SEAT_R + 0.15, (PX, PY, ZFLAT - 1), (0, 0, 1), SEAT_D + 1)] + notches)
flange = cyl(SEAT_R, (PX, PY, ZFLAT), (0, 0, 1), SEAT_D)
spigot = cyl(PR, (PX, PY, ZFLAT), (0, 0, 1), WALL + 1.8)
blugs = [box(PR - 1.0, PR + 3.0, -2.4, 2.4, FLOOR_TOP + 0.2, FLOOR_TOP + 1.8).rotated(V(0, 0, 0), V(0, 0, 1), a)
         .translated(V(PX, PY, 0)) for a in (0, 180)]
grip = cad.soften(box(PX - 13, PX + 13, PY - 2.5, PY + 2.5, ZFLAT - 3.0, ZFLAT + 0.5), 1.2)
plug = cad.fuse_one(flange, spigot, *blugs, grip)
tick("plug")

# ------------------------------------------------------------ holders
# the speaker between two ribs off its sides, run forward to the head wall
holders = [box(x0, x1, -200, SB.YMax - 1.0, SB.ZMin + 1.0, SB.ZMax - 1.0)
           for x0, x1 in ((SB.XMin - 1.6, SB.XMin - 0.3), (SB.XMax + 0.3, SB.XMax + 1.6))]
body = cad.fuse_one(body, *[h.common(skin).cut(snout_solid(-WALL + 0.01)) for h in holders])
tick("holders")

# ------------------------------------------------------------ the snout disc (the speaker's grille)
# the flat of the snout as its own darker disc: two oval nostrils and a
# ring of pores - the oink comes out of the nose
DISC_R = SNOUT_R - 4.5
dcut = cyl(DISC_R, (0, YSN - 1.0, ZS), (0, 1, 0), WALL + 1.5)
disc = body.common(dcut)
body = cad.cut(body, dcut)
NOSTRIL = (0.22 * SNOUT_R, 0.40 * SNOUT_R)    # half width, half height
nostrils = []
for sd in (-1, 1):
    c = V(sd * 0.30 * SNOUT_R, YSN - 1.0, ZS + 0.5)
    el = Part.Ellipse(c + V(0, 0, NOSTRIL[1]), c + V(NOSTRIL[0], 0, 0), c)
    f = Part.Face(Part.Wire([el.toShape()]))
    nostrils.append(f.extrude(V(0, WALL + 2.0, 0)))
PORE_R = 0.86 * DISC_R
pores = [cyl(0.8, (PORE_R * math.cos(2 * math.pi * i / 18), YSN - 1.0, ZS + PORE_R * math.sin(2 * math.pi * i / 18)),
             (0, 1, 0), WALL + 2.0) for i in range(18)]
disc = cad.cut(disc, nostrils + pores)
tick("snout")

# ------------------------------------------------------------ the screen window (left flank)
# a curved smoked visor in a black bezel that fills its opening; the
# bezel's back is flat 0.3 mm off the screen and two ribs off the bezel
# hold the screen's ends


def xprism(y0, y1, z0, z1, r, x0, x1):
    """A rounded rectangle in (y, z) extruded along X from x0 to x1."""
    w = cad.rounded_rect_wire(y1 - y0, z1 - z0, r, (x0, (y0 + y1) / 2, (z0 + z1) / 2), "X")
    s_ = Part.Face(w).extrude(V(x1 - x0, 0, 0))
    if s_.Volume < 0:
        s_.reverse()
    return s_


def yprism(x0, x1, z0, z1, r, y0, y1):
    w = cad.rounded_rect_wire(x1 - x0, z1 - z0, r, ((x0 + x1) / 2, y0, (z0 + z1) / 2), "Y")
    s_ = Part.Face(w).extrude(V(0, y1 - y0, 0))
    if s_.Volume < 0:
        s_.reverse()
    return s_


OPEN_W, OPEN_H = 48.0, 30.0                    # the opening in the flank (y, z)
VIS_W, VIS_H = 38.0, 22.0                      # the visor (the screen's active area is 25.6 x 13.5)
op = xprism(SCR_Y - OPEN_W / 2, SCR_Y + OPEN_W / 2, SCR_Z - OPEN_H / 2, SCR_Z + OPEN_H / 2, 7.0, -90, -30)
body = cad.cut(body, op)
bezel = egg_solid(0.8).common(op).common(box(-90, BZ_BACK, -300, 300, -10, 400))     # a frame 0.8 mm proud
vp = xprism(SCR_Y - VIS_W / 2, SCR_Y + VIS_W / 2, SCR_Z - VIS_H / 2, SCR_Z + VIS_H / 2, 5.0, -90, -30)
visor = cad.cut(egg_solid(-0.4), egg_solid(-2.2)).common(vp)
bezel = cad.cut(bezel, [cad.cut(egg_solid(2.0), egg_solid(-2.2)).common(vp),
                        xprism(SCR_Y - 14.5, SCR_Y + 14.5, SCR_Z - 8.5, SCR_Z + 8.5, 1.5, -90, -30)])
bezel = cad.fuse_one(bezel, *[box(BZ_BACK - 0.5, SC.XMax - 1.0, y0, y1, SC.ZMin + 1.0, SC.ZMax - 1.0)
                              for y0, y1 in ((SC.YMin - 1.6, SC.YMin - 0.3), (SC.YMax + 0.3, SC.YMax + 1.6))])
tick("screen window")

# ------------------------------------------------------------ the coin slot (on the back, over the ToF's beam)
SLOT_Y = SEN_Y
SLOT_X = PA1 + CHUTE                             # the coin falls this far in front of the sensor


def zstadium(cx, cy, ly, wx, z0, z1):
    """A stadium (long along y) extruded along Z."""
    r_ = wx / 2
    f = Part.Face(Part.Wire([
        Part.LineSegment(V(cx - r_, cy - ly / 2 + r_, z0), V(cx - r_, cy + ly / 2 - r_, z0)).toShape(),
        Part.Arc(V(cx - r_, cy + ly / 2 - r_, z0), V(cx, cy + ly / 2, z0), V(cx + r_, cy + ly / 2 - r_, z0)).toShape(),
        Part.LineSegment(V(cx + r_, cy + ly / 2 - r_, z0), V(cx + r_, cy - ly / 2 + r_, z0)).toShape(),
        Part.Arc(V(cx + r_, cy - ly / 2 + r_, z0), V(cx, cy - ly / 2, z0), V(cx - r_, cy - ly / 2 + r_, z0)).toShape()]))
    return f.extrude(V(0, 0, z1 - z0))


pcut = zstadium(SLOT_X, SLOT_Y, SLOT[0] + 12.0, 14.0, ZC + 30, ZC + 80)
body = cad.cut(body, pcut)
slot_plate = cad.cut(egg_solid(1.2), egg_solid(-WALL)).common(pcut)
slot_plate = cad.cut(slot_plate, zstadium(SLOT_X, SLOT_Y, SLOT[0], SLOT[1], ZC + 30, ZC + 80))
tick("slot")

# ------------------------------------------------------------ the coin window (right flank, on the ToF's axis)
WIN_R = 15.0
WIN_RING = 4.0
wcut = cyl(WIN_R, (0, SEN_Y, SEN_Z), (1, 0, 0), 100)
def ring_at(r0):
    return cad.cut(cyl(WIN_R + WIN_RING, (0, SEN_Y, SEN_Z), (1, 0, 0), 100), cyl(r0, (-1, SEN_Y, SEN_Z), (1, 0, 0), 102))


window = cad.cut(egg_solid(-0.4), egg_solid(-WALL)).common(wcut)
body = cad.cut(body, [wcut, cad.cut(egg_solid(2.0), egg_solid(-1.0)).common(ring_at(WIN_R - 0.01))])
wring = cad.cut(egg_solid(0.8), egg_solid(-1.0)).common(ring_at(WIN_R + 0.1))
tick("coin window")

# ------------------------------------------------------------ USB-C in the rump
ux, uz = XB + 5.9, (UB.ZMin + UB.ZMax) / 2
pocket = yprism(ux - 5.0, ux + 5.0, uz - 6.5, uz + 6.5, 2.5, UB.YMax + 1.3, 200)     # the socket stands on its side
liner = cad.cut(yprism(ux - 7.0, ux + 7.0, uz - 8.5, uz + 8.5, 4.5, UB.YMax + 0.25, 200).common(skin), pocket)
body = cad.fuse_one(cad.cut(body, pocket), liner)
body = cad.socket_opening(body, usb, margin=1.5)
tick("stage A")


# === STAGE B: details ===
# (a fork may stop after STAGE A, run ./check, then add these one by one)
# ------------------------------------------------------------ eyes with glints
EYE_R = 7.2
eyes, glints = {}, {}
for nm, sd in (("L", -1), ("R", 1)):
    p, d = on_sphere(HEADC, sd * EYE[0], EYE[1], R)
    c = p + d * (0.05 * EYE_R)
    eye = Part.makeSphere(EYE_R, c).cut(outer)
    eye = cad.fuse_one(eye, Part.makeCylinder(2.0, WALL + 1.3, p + d * 0.5, d * -1))
    body = cad.cut(body, Part.makeCylinder(2.15, WALL + 3.0, p + d * 1.0, d * -1))
    gd = d + V(-0.25 * sd, -0.1, 0.6)
    gd.normalize()
    g_ball = Part.makeSphere(0.32 * EYE_R, c + gd * EYE_R)
    glints[nm] = g_ball.common(eye)
    eyes[nm] = cad.cut(eye, g_ball)
tick("eyes")

# ------------------------------------------------------------ rosy cheeks (inlays below the eyes)
cheeks = {}
for nm, sd in (("L", -1), ("R", 1)):
    p, d = on_sphere(HEADC, sd * (EYE[0] + 16.0), EYE[1] - 22.0, R)
    cc = Part.makeCylinder(7.5, 30, p + d * 10.0, d * -1)
    cheeks[nm] = cad.cut(egg_solid(0.4), egg_solid(-1.0)).common(cc)
    body = cad.cut(body, cad.cut(egg_solid(2.0), egg_solid(-1.0)).common(cc))
tick("cheeks")

# ------------------------------------------------------------ the smile under the snout
SM_Z = ZS - SNOUT_R - 5.0
smile_pts = []
for i in range(7):
    x = -11.0 + 22.0 * i / 6
    z = SM_Z + 0.035 * x * x
    y = -H - math.sqrt(R ** 2 - x ** 2 - (z - ZC) ** 2)
    smile_pts.append((x, y, z))
body = cad.cut(body, cad.pipe(smile_pts, r=0.9), optional=True)

# ------------------------------------------------------------ ears, pinned on the head
ears = {}
for nm, sd in (("L", -1), ("R", 1)):
    p, d = on_sphere(HEADC, sd * EAR[0], EAR[1], R)
    zt = V(sd * 0.30, -0.40, 1.0)              # up, tipped forward and a little out
    zt.normalize()
    yt = V(0, -1, 0) - zt * (V(0, -1, 0).dot(zt))
    yt.normalize()
    xt = yt.cross(zt)
    m_ = App.Matrix(xt.x, yt.x, zt.x, 0, xt.y, yt.y, zt.y, 0, xt.z, yt.z, zt.z, 0, 0, 0, 0, 1)
    cone = Part.makeCone(16.0, 3.0, EAR_H + 6.0)
    sq = App.Matrix()
    sq.scale(1.0, 0.32, 1.0)
    cone = cone.transformGeometry(sq)
    cone = cad.soften(cone, 1.2)
    cone.transformShape(m_)
    cone.translate(p - zt * 6.0)
    ear = cone.cut(outer)
    peg_at = p + d * 0.5
    ear = cad.fuse_one(ear, Part.makeCylinder(2.0, WALL + 1.3, peg_at, d * -1))
    body = cad.cut(body, Part.makeCylinder(2.15, WALL + 3.0, p + d * 1.0, d * -1))
    ears[nm] = ear
tick("ears")

# ------------------------------------------------------------ the corkscrew tail, pinned in the rump
tp, td = on_sphere(V(0, H, ZC), 180.0, 38.0, R)      # az 180: the back of the rump
TAIL_C = tp + td * 3.0
ex = V(1, 0, 0)
ey = td.cross(ex)
pts = [tp - td * 1.0, tp + td * 2.5]
for i in range(1, 15):
    a = 2 * math.pi * 1.25 * i / 14
    q = TAIL_C + td * (2.0 + 0.55 * i) + ex * (4.5 * math.sin(a)) + ey * (4.5 * (1 - math.cos(a)))
    pts.append(q)
tail = cad.pipe(pts, r=2.4).cut(outer)
tail = cad.fuse_one(tail, Part.makeCylinder(2.0, WALL + 1.3, tp + td * 0.5, td * -1))
body = cad.cut(body, Part.makeCylinder(2.15, WALL + 3.0, tp + td * 1.0, td * -1))
tick("tail")

# ------------------------------------------------------------ hooves with a cleft, pinned under the legs
hooves = []
for x, y in LEGS:
    hv = cyl(LEG_R, (x, y, 0.0), (0, 0, 1), 3.0)
    hv = cad.soften(hv, 1.0, [e for e in hv.Edges if e.BoundBox.ZMax < 0.1])
    hv = cad.cut(hv, box(x - 0.8, x + 0.8, y - LEG_R - 1, y - LEG_R + 5.0, -1, 4))   # the cleft at the front
    hv = cad.fuse_one(hv, cyl(2.5, (x, y, 2.5), (0, 0, 1), 3.4))
    hooves.append(hv)

# ------------------------------------------------------------ lettering
base = cad.text(base, "ATECH", (-18.0, 20.0, ZFLAT), (0, 0, -1), 6, depth=0.4, mode="deboss", up=(-1, 0, 0))
_tag = hit(body, (0, 60.0, 300), (0, 0, -1))
body = cad.text(body, "OINK", _tag, (0, 0, 1), 7.0, depth=0.5, mode="deboss", up=(0, 1, 0))
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    return o


o = part("Base", base)
o.ViewObject.ShapeColor = cad.color(COLOURS["Base"])
o = part("Body", body)
o.ViewObject.ShapeColor = cad.color(COLOURS["Body"])
o = part("Snout_Disc", disc)
o.ViewObject.ShapeColor = cad.color(COLOURS["Snout_Disc"])
o = part("Bezel", bezel)
o.ViewObject.ShapeColor = cad.color(COLOURS["Bezel"])
o = part("Visor", visor)
o.ViewObject.ShapeColor = cad.color("smoked")
o.ViewObject.Transparency = cad.transparency("smoked")
o = part("Slot_Plate", slot_plate)
o.ViewObject.ShapeColor = cad.color(COLOURS["Slot_Plate"])
o = part("Coin_Window", window)
o.ViewObject.ShapeColor = cad.color("glass")
o.ViewObject.Transparency = cad.transparency("glass")
o = part("Window_Ring", wring)
o.ViewObject.ShapeColor = cad.color(COLOURS["Window_Ring"])
o = part("Coin_Plug", plug)
o.ViewObject.ShapeColor = cad.color(COLOURS["Coin_Plug"])
for nm in ("L", "R"):
    o = part("Ear_" + nm, ears[nm])
    o.ViewObject.ShapeColor = cad.color(COLOURS["Ear"])
    o = part("Eye_" + nm, eyes[nm])
    o.ViewObject.ShapeColor = cad.color(COLOURS["Eye"])
    o = part("Glint_" + nm, glints[nm])
    o.ViewObject.ShapeColor = cad.color(COLOURS["Glint"])
    o = part("Cheek_" + nm, cheeks[nm])
    o.ViewObject.ShapeColor = cad.color(COLOURS["Cheek"])
o = part("Tail", tail)
o.ViewObject.ShapeColor = cad.color(COLOURS["Tail"])
for i, sh in enumerate(hooves):
    o = part("Hoof_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Hoof"])
for i, sh in enumerate(screws):
    o = part("Screw_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Screw"])
print("SIZE %s" % (cad.measure(Part.makeCompound([base, body, disc, ears["L"], ears["R"], tail] + hooves))["size"],))
print("TOTAL %.1f s" % (time.time() - T0))
