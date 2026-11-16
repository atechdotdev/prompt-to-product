"""Example: "a rubber duck debugger" - a big desk duck that listens to your bug, quacks back and glows its beak.

fork this file for a rubber duck debugger / talking desk character; change PARAMETERS and the outlines.
(a listening mascot, a quacking timer, any desk pet with a voice.)
ARCHETYPE: character speaker

How it is built:
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board FLAT on the base, the duck facing -Y (the port-8 end; ports 8
    and 12 stay empty for the firmware). Everything the duck does is
    CABLED to where a duck does it: the microphone (13, 14) behind a
    pin-hole grille in the chest, the speaker (10, 11) behind a grille in
    the right wing, the light (6) up the neck into the head behind the
    frosted orange beak (its stem is the light pipe), the button (7)
    straight up out of the tail end and forward under the key on the back.
    USB-C SEATED on 3 behind a pocket in the left flank. The body is a
    capsule on a level axis (a chest hemisphere, a straight barrel, a rump
    hemisphere: exact spheres and a cylinder, the inside the same capsule
    WALL smaller), cut flat on the desk; the neck, the head sphere (sunk
    onto the body) and the upturned tail loft are fused on, the junctions
    rounded, and the hull hollowed by the union of the cores, then cut just
    above the floor into the fixed Base (the floor, a lip ring and the
    board cradle) and the Body. Each cabled module sits between two holder
    ribs (the key's button in a hung cradle); five M2.5 screws come up
    through the base into heat-set insert lugs on the walls.
  * STAGE B - details: eyes with glints on pegs, the beak line, feather
    grooves, the "</>" engraving, a raised ring round the key, lettering,
    the rubber foot ring.
RESTYLE (R425): HEAD_R, NECK_H, BEAK_W, BEAK_L and WALL drive the head,
the neck, the bill, the eyes, the light's place and every cutter on them.
The body's LENGTH / WIDTH are below the block, not knobs: the board and
the cabled modules set them (the board's corners need the 140 mm barrel).
DETAILS (visible, 28): 1 capsule body; 2 flat desk underside; 3 upturned
tail flick; 4 head sphere sunk on a thick neck; 5 rounded neck
junctions; 6 flat duck bill; 7 frosted orange beak that glows (the
light's lens); 8 the beak line (mouth groove); 9-10 black eyes, domed,
on pegs; 11-12 a white glint in each eye; 13-14 wing reliefs on both
flanks; 15-18 two feather grooves on each wing; 19 the orange speaker
grille insert in the right wing; 20 the mic pin-hole grille on the
chest; 21 the orange key cap on the back; 22 a raised ring round it;
23 "</>" engraved behind the key; 24 USB-C pocket with liner in the left
flank; 25 the graphite base under a parting line; 26 "ATECH" under the
base; 27 the rubber foot ring in its recess; 28 five countersunk screws.
Inside: the board cradle, a rib onto the board's spine, a sound tube on
the speaker, a seal ring on the mic, holder ribs round every cabled
module, insert lugs and sleeves, the base's lip ring.
Materials: toy-yellow body, frosted orange beak, black eyes with white
glints, orange key and grille, graphite base, rubber foot ring, chrome
screws.
MEASURED (2026-11-10): ./check CHECK PASS, model build 26 s (run_seconds), ./check 59 s wall;
every RESTYLE knob at its min and max CHECK PASS (29-33 s each).
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
    "Body", "Grille", "Beak", "Key", "Eye_L", "Eye_R", "Glint_L", "Glint_R", "Foot_Ring",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4", "Screw_5"],
    "covers": {"Key": "button_7"}}
REVIEW_CLOSEUPS = ["Beak", "Key", "Eye_L"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them. (The body's length and width
# are set by the board and the cabled modules inside: they are below.)
HEAD_R = 46.0      # RESTYLE 39..53 radius: the head sphere
NECK_H = 4.0       # RESTYLE 3.2..4.8 height: the neck that shows between the body and the head
BEAK_W = 52.0      # RESTYLE 44..60 width: the bill across (x)
BEAK_L = 36.0      # RESTYLE 30..42 length: the bill's reach past the head (-y)
WALL = 2.2         # RESTYLE 1.8..2.6 wall
# end RESTYLE
# Frame: the board FLAT at x 0..60, y -120..0 (port 8 at the front, -Y),
# z up from the desk. The body's axis runs along y at x = 30, z = ZC.
LENGTH = 230.0                   # the body, chest to rump (the board's 120 + room for the chest mic)
WIDTH = 140.0                    # the body's diameter (the board's corners need 120 inside)
CORNER = 12.0                    # the rounds where the neck meets the body and the head
FOOT = 1.5                       # the rubber foot ring under the base
L = 10.0                         # PCB top (the cradle stands it 2.5 mm over the floor)
ZC = 54.0                        # the body's axis height
YM = -65.0                       # the body's middle
YF, YR = YM - LENGTH / 2, YM + LENGTH / 2
NECK_Y = -128.0                  # the neck's axis (over the board's front end)
NECK_R = 0.8 * HEAD_R            # a thick neck: the head sits on the body
_YFC = YF + WIDTH / 2            # the chest hemisphere's centre
HEAD_Z = ZC + math.sqrt((WIDTH / 2) ** 2 - (NECK_Y - _YFC) ** 2) + NECK_H + HEAD_R - 14.0   # sunk: it sits on the body
LIGHT_Y = NECK_Y - HEAD_R * 0.45  # the beak light's centre (its pipe reaches the beak)
LIGHT_Z = HEAD_Z - 9.0           # the beak sits just under the head's middle
BEAK = (BEAK_W, BEAK_L, 15.0)    # the bill: width, reach past the head, thickness
MIC_Z = ZC + 16.0                # the chest microphone's centre (off the egg's pole)
SPK_Z = ZC - 2.0                 # the wing speaker's centre height
KEY_Y = -23.0                    # the key on the back (the button under it)
SCREW = "M2.5"
SCREWS = [(12.0, 7.0), (48.0, 7.0), (-9.0, -80.0), (67.0, -76.0), (5.0, -140.0)]   # insert lugs on the walls, off every ribbon
COLOURS = {"Base": "graphite", "Body": "toy_yellow", "Beak": "orange", "Eye": "matte_black",
           "Glint": "matte_white", "Grille": "orange", "Key": "orange", "Foot_Ring": "rubber", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
FLAT = Rotation(Vector(1, 0, 0), 90)
board = ap.board_object(doc)
board.Placement = Placement(Vector(0, 0, L), FLAT)     # x 0..60, y -120..0
BB = ap.bbox(board)
usb = ap.seat(doc, "usbc", 3)                          # left flank, mouth -X


# The body: a capsule on a level axis - a chest hemisphere, a straight
# barrel (a duck's back is level) and a rump hemisphere under the tail.
# Exact spheres and a cylinder: fast booleans, a fair surface, and the
# inside is the same capsule WALL smaller (an exact offset). MEASURED: a
# revolved spline egg took 145 s for the wing grille, a revolved torus
# rump measured a loose box (z -16) after every boolean.
W2 = WIDTH / 2
YF_C, Y3 = YF + W2, YR - W2                      # the hemisphere centres (y)


def egg_r(y, d=0.0):
    """The body's radius at y, its surface moved d out (d < 0: the inside)."""
    c = min(max(y, YF_C), Y3)
    return math.sqrt(max(0.0, (W2 + d) ** 2 - (y - c) ** 2))


def egg_solid(d=0.0):
    """The body (its surface moved d out) as one solid."""
    return cad.fuse_one(Part.makeSphere(W2 + d, V(30, YF_C, ZC)).fuse([
        Part.makeCylinder(W2 + d, Y3 - YF_C, V(30, YF_C, ZC), V(0, 1, 0)),
        Part.makeSphere(W2 + d, V(30, Y3, ZC))]).removeSplitter())


def r_in(y):
    """The inside radius at y."""
    return egg_r(y, -WALL)


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, d, h):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def ring(r_out, r_in_, p, d, h):
    return cad.cut(cyl(r_out, p, d, h), cyl(r_in_, tuple(a - 0.5 * b for a, b in zip(p, d)), d, h + 1.0))


def centre(m):
    b = ap.bbox(m)
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


# ------------------------------------------------------------ cabled modules
# the beak light: up the neck into the head, facing the beak
LIGHT_C = (30.0, LIGHT_Y, LIGHT_Z)
light_pl = ap.module_placement("light", LIGHT_C, face="-Y", cable="-Z")
light, light_rib = ap.cable(doc, "light", 6, light_pl, via=[
    (-9, -112, L + 16), (-8, -118, L + 50), (6, -126, L + 92), (26, LIGHT_Y + 8, LIGHT_Z - 38),
    (30, LIGHT_Y + 6.2, LIGHT_Z - 9.75 - 22.25), (30, LIGHT_Y + 3.4, LIGHT_Z - 9.75 - 18.25)], smooth=True)
# the chest microphone: face -Y just behind the chest's inner tip
MIC_R = math.hypot(39.5 / 2, abs(MIC_Z - ZC) + 19.5 / 2)    # its farthest corner from the axis
MIC_FACE_Y = next(YF + 0.1 * i for i in range(600) if r_in(YF + 0.1 * i) >= MIC_R + 0.6)   # just behind the chest
mic_pl = ap.module_placement("microphone", (30, MIC_FACE_Y + 10.84 / 2, MIC_Z), face="-Y", cable="-Z")
mic, mic_rib = ap.cable(doc, "microphone", (13, 14), mic_pl, via={
    13: [(70, -92, L + 14), (60, -110, L + 24), (40, -130, L + 28), (22, -148, L + 26),
         (20, MIC_FACE_Y + 10.84 - 0.6, MIC_Z - 9.75 - 22.25), (20, MIC_FACE_Y + 9.44, MIC_Z - 9.75 - 18.25)],
    14: [(70, -112, L + 4), (60, -132, L + 8), (46, -150, L + 14),
         (40, MIC_FACE_Y + 10.84 - 0.6, MIC_Z - 9.75 - 22.25), (40, MIC_FACE_Y + 9.44, MIC_Z - 9.75 - 18.25)]},
    smooth=True)
# the wing speaker: face +X inside the right flank, pins UP - its two
# ribbons rise behind it and hairpin down into its top (face +X with pins
# down would cross the two ribbons: the connector order flips)
SPK_Y = -40.0                                           # between ports 10 and 11
SPK_DZ = max(abs(SPK_Z - 20 - ZC), abs(SPK_Z + 20 - ZC))
SPK_FACE_X = 30 + math.sqrt((min(r_in(SPK_Y - 20), r_in(SPK_Y + 20)) - 1.0) ** 2 - SPK_DZ ** 2)
spk_pl = ap.module_placement("speaker", (SPK_FACE_X - 20.2 / 2, SPK_Y, SPK_Z), face="+X", cable="+Z")
SPK_PIN_X, SPK_TOP = SPK_FACE_X - 20.2 + 1.4, SPK_Z + 20.0
SPK_RISE_X = SPK_FACE_X - 20.2 - 2.7                    # the risers, 2.7 behind the speaker
spk, spk_rib = ap.cable(doc, "speaker", (10, 11), spk_pl, via={
    p: [(SPK_RISE_X, y, L + 20), (SPK_RISE_X, y, SPK_TOP + 10), (SPK_RISE_X + 1.5, y, SPK_TOP + 21.5),
        (SPK_PIN_X - 0.8, y, SPK_TOP + 22.25), (SPK_PIN_X, y, SPK_TOP + 18.25)]
    for p, y in ((10, SPK_Y + 10), (11, SPK_Y - 10))}, smooth=True)
# the key on the back: the button straight up out of port 7 and forward
KEY_TOP = ZC + r_in(KEY_Y)                              # the inner skin over the key
BTN_Z = KEY_TOP - 3.6 - 10.04 / 2                       # its cover 3.6 mm under the skin
btn_pl = ap.module_placement("button", (30, KEY_Y, BTN_Z), face="+Z", cable="+Y")
btn, btn_rib = ap.cable(doc, "button", 7, btn_pl, via=[
    (30, 11, L + 30), (30, 11, BTN_Z - 16),
    (30, KEY_Y + 9.75 + 22.25, BTN_Z - 5.0 + 0.6), (30, KEY_Y + 9.75 + 18.25, BTN_Z - 5.0 + 1.4)], smooth=True)
tick("hardware")


def hit(shape, p, d, reach=400.0):
    """The first point where the ray from p along d enters `shape`."""
    p, d = V(*p), V(*d)
    d.normalize()
    sec = shape.section(Part.makeLine(p, p + d * reach))
    pts = sorted((v.Point for v in sec.Vertexes), key=lambda q: (q - p).Length)
    if not pts:
        raise cad.CadError("hit: the ray from %s along %s misses" % (p, d))
    return pts[0]


# ------------------------------------------------------------ the hull
# the egg cut flat on the desk, the neck, the head sphere, the tail flick
HEAD = V(30, NECK_Y, HEAD_Z)
SKY = box(-200, 260, -400, 300, FOOT, 400)


def tail_solid(t=0.0):
    """The upturned tail: a loft from inside the rump up and back to a tip."""
    y0, y2 = YR - 46.0, YR + 14.0
    secs = [cad.rounded_rect_wire(WIDTH * 0.46 - 2 * t, 46 - 2 * t, 18 - t, (30, y0, ZC + 26), "Y"),
            cad.rounded_rect_wire(WIDTH * 0.30 - 2 * t, 26 - 2 * t, 10 - t, (30, YR - 14, ZC + 44), "Y")]
    if t == 0.0:
        secs.append(cad.rounded_rect_wire(10, 6, 2.9, (30, y2, ZC + 68), "Y"))
    return cad.loft(secs)


egg = egg_solid().common(SKY)
neck = cyl(NECK_R, (30, NECK_Y, ZC), (0, 0, 1), HEAD_Z - ZC)
head = Part.makeSphere(HEAD_R, HEAD)
tail = tail_solid()
outer = cad.fuse_one(egg, neck, head, tail)
outer = cad.soften(outer, CORNER, cad.new_edges(outer, Part.makeCompound([egg, neck, head, tail])))
core = cad.fuse_one(egg_solid(-WALL).common(box(-200, 260, -400, 300, FOOT + WALL, 400)),
                    cyl(NECK_R - WALL, (30, NECK_Y, ZC), (0, 0, 1), HEAD_Z - ZC),
                    Part.makeSphere(HEAD_R - WALL, HEAD), tail_solid(WALL))
skin = cad.fuse_one(egg_solid(-0.6), Part.makeSphere(HEAD_R - 0.6, HEAD),
                    cyl(NECK_R - 0.6, (30, NECK_Y, ZC), (0, 0, 1), HEAD_Z - ZC))   # ribs stop inside the skin
hull = cad.cut(outer, core)
tick("hull")

# insert lugs for the screws, on the flank walls just above the floor
SPLIT_Z = FOOT + WALL + 0.6
INSERT_D = {"M2": 3.2, "M2.5": 3.6, "M3": 4.3}[SCREW]
LUG_Z0, LUG_Z1 = SPLIT_Z + 2.8, SPLIT_Z + 14.0     # over the base's lip
lugs = []
for x, y in SCREWS:
    a = INSERT_D / 2 + 1.4
    if x < 0 or (x < 30 and y < -130):
        lugs.append(box(x + a, -60, y - a, y + a, LUG_Z0, LUG_Z1))
    elif x > 60:
        lugs.append(box(x - a, 120, y - a, y + a, LUG_Z0, LUG_Z1))
    else:                               # the rear pair: back to the tail wall
        lugs.append(box(x - a, x + a, y - a, 80, LUG_Z0, LUG_Z1))
hull = cad.fuse_one(hull, *[g.common(skin) for g in lugs])
tick("lugs")

# the wings: a 1.6 mm relief on each flank (the right one carries the
# speaker grille - the duck quacks through its wing)
WING = [(-112, 56), (-100, 74), (-70, 82), (-35, 82), (-5, 86), (16, 98), (8, 80),
        (-14, 54), (-40, 30), (-76, 29), (-104, 40)]


def wing_prism(side):
    ys = [YM + (y + 65.0) * LENGTH / 230.0 for y, _z in WING]     # follows LENGTH
    pts = [V(30, y, ZC + (z - 54.0) * WIDTH / 140.0) for y, (_y, z) in zip(ys, WING)]
    sp = Part.BSplineCurve()
    sp.interpolate(pts, PeriodicFlag=True)
    f = Part.Face(Part.Wire([sp.toShape()]))
    pr = f.extrude(V(side * WIDTH, 0, 0))
    if pr.Volume < 0:
        pr.reverse()
    return pr


relief = cad.cut(egg_solid(1.6).common(SKY), egg_solid(-0.6))     # 0.6 into the wall: it fuses
wings = {k: relief.common(wing_prism(sd)) for k, sd in (("R", 1), ("L", -1))}
hull = cad.fuse_one(hull, wings["R"], wings["L"])
tick("wings")

# split just above the floor: the fixed Base (floor + cradle) and the Body
# (cad.split here returned an upper part with untrimmed sphere faces -
# MEASURED z -16 - so the seam is cut by hand: two slabs and a lip ring
# 0.15 mm inside the wall, standing 2.5 mm up into the Body)
base = hull.common(box(-200, 260, -400, 300, -10, SPLIT_Z))
body = hull.common(box(-200, 260, -400, 300, SPLIT_Z, 400))
lip = cad.cut(egg_solid(-WALL - 0.15), egg_solid(-WALL - 1.55)).common(
    box(-200, 260, -400, 300, FOOT + WALL - 0.2, SPLIT_Z + 2.5))
base = cad.fuse_one(base, lip)
PCB0 = L - 2.5
cradle = cad.cut(box(BB.XMin - 2.3, BB.XMax + 2.3, BB.YMin - 2.3, BB.YMax + 2.3, FOOT + WALL - 0.5, PCB0 + 1.4),
                 [box(BB.XMin - 0.3, BB.XMax + 0.3, BB.YMin - 0.3, BB.YMax + 0.3, PCB0 - 0.1, 60),
                  box(BB.XMin + 6, BB.XMax - 6, BB.YMin + 6, BB.YMax - 6, 0, 60)])
base = cad.fuse_one(base, cradle)
# board retention: a rib from the back down onto the spine (0.2 mm above it)
body = cad.fuse_one(body, box(29, 31, -78, -62, L + 4.5 + 0.2, 200).common(skin))
tick("split + cradle")

# screws: up through the base into heat-set insert pockets in the lugs; a
# short sleeve under each lug stands 0.1 mm over the floor
screws = []
FLOOR_TOP = FOOT + WALL
body = cad.fuse_one(body, *[cyl(INSERT_D / 2 + 1.4, (x, y, FLOOR_TOP + 0.1), (0, 0, 1), LUG_Z0 + 1.5 - FLOOR_TOP)
                            for x, y in SCREWS])
body = cad.cut(body, [cyl(INSERT_D / 2, (x, y, FLOOR_TOP), (0, 0, 1), 9.0) for x, y in SCREWS])
for x, y in SCREWS:
    base = cad.countersink(base, (x, y, FOOT), "+Z", 2.9, 5.6, 90.0)
    screws.append(cad.screw("csk_phillips", SCREW, 10, at=(x, y, FOOT), axis="+Z"))
tick("screws")

# ------------------------------------------------------------ holders
# every cabled module sits between two ribs 0.3 mm off its sides, each
# rib run out to the wall it hangs from (and stopped inside the skin)
holders = []
b = ap.bbox(mic)                        # chest: ribs either side (x), back from the chest wall
holders += [box(x0, x1, YF - 5, b.YMax - 1.0, b.ZMin + 1.0, b.ZMax - 1.0)
            for x0, x1 in ((b.XMin - 1.6, b.XMin - 0.3), (b.XMax + 0.3, b.XMax + 1.6))]
b = ap.bbox(spk)                        # wing: ribs fore and aft (y), out from the flank
holders += [box(b.XMin + 1.0, 130, y0, y1, b.ZMin + 1.0, b.ZMax - 1.0)
            for y0, y1 in ((b.YMin - 1.6, b.YMin - 0.3), (b.YMax + 0.3, b.YMax + 1.6))]
b = ap.bbox(light)                      # head: ribs either side (x), back from the face
holders += [box(x0, x1, NECK_Y - HEAD_R - 5, b.YMax - 1.0, b.ZMin + 1.0, b.ZMax - 1.0)
            for x0, x1 in ((b.XMin - 1.6, b.XMin - 0.3), (b.XMax + 0.3, b.XMax + 1.6))]
b = ap.bbox(btn)                        # back: a cradle hung from the top - two cheeks and a pad under it
BTN_BB = b
holders += [box(x0, x1, b.YMin + 1.0, b.YMax - 1.5, b.ZMin - 2.2, 200)
            for x0, x1 in ((b.XMin - 1.6, b.XMin - 0.3), (b.XMax + 0.3, b.XMax + 1.6))]
holders.append(box(b.XMin - 1.6, b.XMax + 1.6, b.YMin + 1.0, b.YMax - 1.5, b.ZMin - 2.2, b.ZMin - 0.2))
body = cad.fuse_one(body, *[h.common(skin) for h in holders])
tick("holders")

# ------------------------------------------------------------ the chest microphone
mb = ap.bbox(mic)
MX, MZ = (mb.XMin + mb.XMax) / 2, (mb.ZMin + mb.ZMax) / 2
mic_at = hit(body, (MX, YF - 30, MZ), (0, 1, 0))
body = cad.speaker_grille(body, mic_at, (0, -1, 0), 15, ring_pitch=2.5, hole=1.6)
# a seal ring from the chest wall to 0.3 mm off the mic face
body = cad.fuse_one(body, ring(9.6, 8.4, (MX, mb.YMin - 0.3, MZ), (0, -1, 0), 12.0).common(skin))
# ------------------------------------------------------------ the wing speaker
sb = ap.bbox(spk)
SY, SZ = (sb.YMin + sb.YMax) / 2, (sb.ZMin + sb.ZMax) / 2
spk_at = hit(body, (SPK_FACE_X + 60, SY, SZ), (-1, 0, 0))
# the grille is its own insert (a round piece of the wing, orange): drilled
# on its own it costs ~1 s, on the whole hull ~145 s (MEASURED)
GRILLE_R = 18.5
g_cut = cyl(GRILLE_R, (sb.XMax + 1.0, SY, SZ), (1, 0, 0), 40.0)
grille = body.common(g_cut)
body = cad.cut(body, g_cut)
grille = cad.speaker_grille(grille, spk_at, (1, 0, 0), 32, ring_pitch=2.6, hole=1.5)
# a sound tube from the wing wall down to 0.3 mm off the driver's face
body = cad.fuse_one(body, ring(GRILLE_R + 2.3, GRILLE_R + 0.3, (sb.XMax + 0.3, SY, SZ), (1, 0, 0), 20.0).common(skin))
tick("mic + speaker")

# ------------------------------------------------------------ the beak (the light's lens)
# a flat bill: an ellipse in plan, its root on the head sphere; its stem
# runs back through the head wall to 0.4 mm off the light (a light pipe)
lb = ap.bbox(light)
LX, LZ = (lb.XMin + lb.XMax) / 2, (lb.ZMin + lb.ZMax) / 2
HEAD_FRONT = hit(head, (LX, NECK_Y - HEAD_R - 20, LZ), (0, 1, 0)).y
TIP_Y = HEAD_FRONT - BEAK[1]
BEAK_B = 0.5 * BEAK[1] + 6.0                 # the bill's half reach: its root 12 mm inside the head
_c = V(LX, TIP_Y + BEAK_B, LZ - BEAK[2] / 2)
_ax = (V(BEAK[0] / 2, 0, 0), V(0, BEAK_B, 0)) if BEAK[0] / 2 >= BEAK_B else (V(0, BEAK_B, 0), V(BEAK[0] / 2, 0, 0))
bill = Part.Face(Part.Wire([Part.Ellipse(_c + _ax[0], _c + _ax[1], _c).toShape()]))
bill = bill.extrude(V(0, 0, BEAK[2]))
bill = cad.soften(bill, 3.5)
beak = bill.cut(outer)
STEM_H = min(9.0, BEAK[2] / 2 - 1.0)              # the pipe stays inside the bill
stem = box(LX - 9, LX + 9, lb.YMin - 0.4, HEAD_FRONT - 4.0, LZ - STEM_H, LZ + STEM_H)
body = cad.cut(body, stem)
beak = cad.fuse_one(beak, stem)
tick("beak")

# ------------------------------------------------------------ the key on the back
bx, by = (BTN_BB.XMin + BTN_BB.XMax) / 2, (BTN_BB.YMin + BTN_BB.YMax) / 2
KEY_D = 18.0
key_out = hit(body, (bx, by, 300), (0, 0, -1)).z
key_in = min(hit(core, (bx + dx, by + dy, 300), (0, 0, -1)).z
             for dx, dy in ((0, 0), (KEY_D / 2 + 1.6, 0), (-KEY_D / 2 - 1.6, 0), (0, KEY_D / 2 + 1.6), (0, -KEY_D / 2 - 1.6)))
k_base = key_in - 0.15 - 0.8                 # the flange 0.15 under the skin's lowest point over it
key = cad.button_cap(KEY_D, key_out + 2.0 - k_base, dome=1.0, flange=0.75, at=(bx, by, k_base), axis="+Z")
body = cad.opening_for(body, key, clearance=0.25, chamfer=0.4, axis="+Z")
key = cad.fuse_one(key, cyl(3.0, (bx, by, BTN_BB.ZMax + 0.16), (0, 0, 1), k_base - BTN_BB.ZMax - 0.16 + 0.5))
tick("key")

# ------------------------------------------------------------ USB-C in the left flank
ub = ap.bbox(usb)
uy, uz = (ub.YMin + ub.YMax) / 2, L + 5.9


def xprism(y0, y1, z0, z1, x0, x1, r):
    w = cad.rounded_rect_wire(y1 - y0, z1 - z0, r, (x0, (y0 + y1) / 2, (z0 + z1) / 2), "X")
    s_ = Part.Face(w).extrude(V(x1 - x0, 0, 0))
    if s_.Volume < 0:
        s_.reverse()
    return s_


pocket = xprism(uy - 6.5, uy + 6.5, uz - 5.0, uz + 5.0, -80, ub.XMin - 1.3, 2.5)
liner = cad.cut(xprism(uy - 8.5, uy + 8.5, max(uz - 7.0, SPLIT_Z + 2.0), uz + 7.0, ub.XMin - 0.25, -80, 3.5)
                .common(skin), pocket)
body = cad.fuse_one(cad.cut(body, pocket), liner)
body = cad.socket_opening(body, usb, margin=1.5)
tick("stage A")


# === STAGE B: details ===
# (a fork may stop after STAGE A, run ./check, then add these one by one)
# ------------------------------------------------------------ eyes with glints
# black domes on the head, each pinned by a peg into a hole through the
# head wall (0.15 mm clear); a white glint fills its own pocket in the eye
EYE_R = 0.16 * HEAD_R
eyes, glints = {}, {}
for nm, sd in (("L", -1), ("R", 1)):
    az, el = math.radians(36.0), math.radians(18.0)
    d = V(sd * math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))
    c = HEAD + d * (HEAD_R + 0.05 * EYE_R)       # a bulging ball: no knife edge where it meets the head
    eye = Part.makeSphere(EYE_R, c).cut(outer)
    peg_at = HEAD + d * (HEAD_R + 0.5)
    eye = cad.fuse_one(eye, Part.makeCylinder(2.0, WALL + 1.3, peg_at, d * -1))
    body = cad.cut(body, Part.makeCylinder(2.15, WALL + 3.0, HEAD + d * (HEAD_R + 1.0), d * -1))
    gd = d + V(0, -0.25, 0.55)
    gd.normalize()
    g_ball = Part.makeSphere(0.3 * EYE_R, c + gd * EYE_R)     # centred ON the eye: steep edges
    glints[nm] = g_ball.common(eye)
    eyes[nm] = cad.cut(eye, g_ball)
tick("eyes")

# ------------------------------------------------------------ the beak line
# a mouth groove round the bill's front at mid thickness
_g = Part.Face(Part.Wire([Part.Ellipse(_c + _ax[0] * ((_ax[0].Length + 2) / _ax[0].Length),
                                       _c + _ax[1] * ((_ax[1].Length + 2) / _ax[1].Length), _c).toShape()]))
_gi = Part.Face(Part.Wire([Part.Ellipse(_c + _ax[0] * ((_ax[0].Length - 1.0) / _ax[0].Length),
                                        _c + _ax[1] * ((_ax[1].Length - 1.0) / _ax[1].Length), _c).toShape()]))
mouth = cad.cut(_g.extrude(V(0, 0, 1)), _gi.extrude(V(0, 0, 1)))
mouth.translate(V(0, 0, BEAK[2] / 2 - 1.5))
mouth = mouth.common(box(-200, 260, -400, HEAD_FRONT - 6.0, -10, 400))
beak = cad.cut(beak, mouth, optional=True)

# ------------------------------------------------------------ feather grooves on each wing
def on_wing(y, z, sd):
    yy = YM + (y + 65.0) * LENGTH / 230.0
    zz = ZC + (z - 54.0) * WIDTH / 140.0
    return (30 + sd * math.sqrt(egg_r(yy, 1.6) ** 2 - (zz - ZC) ** 2), yy, zz)


FEATHERS = [[(-14, 74), (-4, 80), (6, 88), (12, 94)], [(-16, 64), (-6, 70), (2, 78), (7, 84)]]
grooves = [cad.pipe([on_wing(y, z, sd) for y, z in f], r=0.8) for sd in (1, -1) for f in FEATHERS]
body = cad.cut(body, grooves, optional=True)
tick("feathers")

# ------------------------------------------------------------ "</>" behind the key, a raised ring round it
_tag = hit(body, (30, by + KEY_D + 8.0, 300), (0, 0, -1))      # "</>" engraved on the back behind the key
body = cad.text(body, "</>", _tag, (0, 0, 1), 9.0, depth=0.6, mode="deboss", up=(0, 1, 0))
body = cad.fuse_one(body, cad.cut(cyl(KEY_D / 2 + 2.4, (bx, by, key_out - 1.3), (0, 0, 1), 1.9),
                                  cyl(KEY_D / 2 + 0.9, (bx, by, key_out - 2.0), (0, 0, 1), 4.0)))

# ------------------------------------------------------------ underside: lettering, the rubber foot ring
def stadium(inset, z0, h):
    """The base's flat outline (the capsule cut at z = FOOT) moved inset in."""
    rr = math.sqrt(W2 ** 2 - (ZC - FOOT) ** 2) - inset
    return cad.fuse_one(cyl(rr, (30, YF_C, z0), (0, 0, 1), h), cyl(rr, (30, Y3, z0), (0, 0, 1), h),
                        box(30 - rr, 30 + rr, YF_C, Y3, z0, z0 + h))


base = cad.text(base, "ATECH", (30, -60, FOOT), (0, 0, -1), 8, depth=0.4, mode="deboss", up=(0, -1, 0))
base = cad.cut(base, cad.cut(stadium(1.6, FOOT - 1, 2.0), stadium(4.6, FOOT - 2, 4.0)))
foot_ring = cad.cut(stadium(1.75, 0.0, FOOT + 1.0), stadium(4.45, -1.0, FOOT + 3.0))
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape, colour=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    return o


o = part("Base", base)
o.ViewObject.ShapeColor = cad.color(COLOURS["Base"])
o = part("Body", body)
o.ViewObject.ShapeColor = cad.color(COLOURS["Body"])
o = part("Grille", grille)
o.ViewObject.ShapeColor = cad.color(COLOURS["Grille"])
o = part("Beak", beak)
o.ViewObject.ShapeColor = cad.color(COLOURS["Beak"])
o.ViewObject.Transparency = cad.transparency("frosted")
o = part("Key", key)
o.ViewObject.ShapeColor = cad.color(COLOURS["Key"])
for nm in ("L", "R"):
    o = part("Eye_" + nm, eyes[nm])
    o.ViewObject.ShapeColor = cad.color(COLOURS["Eye"])
    o = part("Glint_" + nm, glints[nm])
    o.ViewObject.ShapeColor = cad.color(COLOURS["Glint"])
o = part("Foot_Ring", foot_ring)
o.ViewObject.ShapeColor = cad.color(COLOURS["Foot_Ring"])
for i, sh in enumerate(screws):
    o = part("Screw_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Screw"])
print("TOTAL %.1f s" % (time.time() - T0))
