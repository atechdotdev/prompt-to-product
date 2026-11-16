"""Example: "a live follower counter" - a creator's desk trophy: big live digits behind a smoked window on a brushed plaque, a heart that pulses on every new follower.

fork this file for a follower counter / desk trophy display (a live
subscriber counter, a creator award plaque, a donation counter); change PARAMETERS and the outlines.
Any plaque with one big readout and an emblem on a weighted base forks it too.
ARCHETYPE: trophy plaque

How it is built (R940):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board UPRIGHT_FRONT in the plaque and its stem (portrait, modules
    facing the front, -Y). The big_screen SEATED on the left column pair
    (13, 14): it overhangs the board 40 mm to the left, landscape (59.7 x
    39.5, MEASURED), behind a smoked lens (a wide front band in a pocket,
    a step through the screen's window) in a recessed, bevelled window.
    The heart light CABLED from port 6 and the cycle button CABLED from
    port 4, both straight out to the right (twist-free) into the plaque's
    right column, which mirrors the window about the board's centre line:
    the light behind a frosted heart badge (its pipe 0.45 mm off the LED
    grid), the button under a red key cap. USB-C CABLED from port 7
    straight down out of the stem into the base: the ribbon turns back
    under the stem to a bay in the base (walls 0.3 mm off the module), the
    mouth at the base's back wall (1.25 mm thick in front of it, the plug
    opening measured from the module's mesh). The plaque: a brushed front
    plate (bevelled front edge) on a graphite back shell set in INSET, its
    outline a T (the plaque over a 72 mm stem, concave fillets behind),
    the stem's front wall set back STEM_SET under the plate; four M2.5
    screws from behind through columns into pilots in the plate.
    Everything above the base is built UPRIGHT and TILTED back TILT
    degrees about the plate's front-bottom line (one Placement); the
    stem's bottom is then cut flat on the base's slot floor. The base (a
    tapered black plinth) takes the stem in a slot; two M2.5 screws from
    the base's cavity up into bosses in the board's bottom ledges hold it;
    a steel weight plate closes the cavity from below on four M2.5
    screws, standing on four rubber feet.
  * STAGE B - details: the engraved FOLLOWERS legend, hex vents in the
    stem's back behind the board, a reveal line round the plinth, ATECH on
    its front.
RESTYLE (R425): WIDTH, BASE_H, CORNER and WALL drive every outline and
cutter below; the plaque's centre line (CX, the board's), the window and
the right column are fixed by the hardware (the screen's overhang, the
cabled modules' reach), so WIDTH moves the plaque's edges, its corner
screws (a top-left one that would meet the window moves over it) and the
plinth's width. Swept 2026-11-10: each knob at its min and max CHECK PASS.
DETAILS (visible, 24 of 34): 1 brushed plaque, 2 its 45 deg bevelled front
edge, 3 the window's 45 deg recess bevel, 4 the wide smoked lens over the
digits, 5 its stepped core through the screen window, 6 frosted red heart
badge (34 mm), 7 red cycle key, 8 engraved "FOLLOWERS" legend, 9 graphite
back shell set in INSET (a shadow line round the plate), 10 graphite stem,
set back under the plate, 11 concave fillets plaque / stem on the back,
12 hex vents in the stem's back, 13-16 four countersunk screws on the
back, 17 tapered black plinth, 18 its rolled top edge, 19 reveal line round
it, 20 "ATECH" on its front, 21 USB-C socket in its back, 22 steel weight
plate underneath, 23-26 four rubber feet in recesses. Inside: 27 board
ledges and standoffs, 28 a rib from the plate onto the board's spine, 29
ledges above / below the screen's overhang and standoffs behind it, 30
ribs and a pad round the heart light, 31 ribs and a pad round the button,
32 screw columns, 33 the stem's bosses in the board ledges, 34 the USB-C
bay and the ribbon slots through the stem floor and the slot floor.
Materials: brushed aluminium plate, graphite back shell and stem, matte
black plinth, smoked lens, frosted red heart, red key, satin steel weight,
rubber feet, chrome screws.
Hardware: one screw type, M2.5 countersunk Phillips (ISO 10642): 4 x 20
(plate to back shell, heads in 2 mm counterbores), 2 x 8 (stem to
plinth), 4 x 10 (weight plate). Steel weight plate 150 x 70 x 5 (~410 g);
4 rubber feet 10 mm, 3.5 mm tall.
MEASURED (R940, 2026-11-10): ./check CHECK PASS, model build 6.8 s, ./check
wall 25 s (run_example).
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
    "Plate", "Back", "Base", "Screen_Lens", "Heart_Badge", "Cycle_Key", "Weight",
    "Foot_1", "Foot_2", "Foot_3", "Foot_4",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4", "Screw_Neck_1", "Screw_Neck_2",
    "Screw_Weight_1", "Screw_Weight_2", "Screw_Weight_3", "Screw_Weight_4"],
    # the key cap presses the cabled button through its opening; the smoked
    # lens sits 2 mm in front of the big screen's face (see-through: the
    # face-open probe lists "screen", not "big_screen", as optical)
    "covers": {"Cycle_Key": "button_4", "Screen_Lens": "big_screen_p13_14"}}
REVIEW_CLOSEUPS = ["Screen_Lens", "Heart_Badge", "Base"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them; test_kit_examples_r280 builds
# this file with each knob at its min and at its max, one at a time.
WIDTH = 200.0      # RESTYLE 170..230 width: the plaque across (x)
BASE_H = 44.0      # RESTYLE 37..51 height: the plinth's top over the desk (z)
CORNER = 14.0      # RESTYLE 11.5..16.5 radius: the plaque's corners (the back shell's INSET less)
WALL = 2.2         # RESTYLE 1.85..2.55 wall
# end RESTYLE
# Built UPRIGHT in a local frame (front = -Y, x across, z up), then tilted
# back TILT degrees as one piece about the plate's front-bottom edge, which
# lands on the base's slot floor at world z = ZF. The board, the screen and
# the right column are fixed by the hardware: never move them with a knob.
TILT = 10.0
Z0 = 11.0                        # the board's bottom edge (local z): room for the stem's screw bosses under it
WIN_M = 1.0                      # window margin round the screen's face (each side)
LEDGE, BEV = 6.0, 1.5            # the smoked lens's band round the window, the recess's 45 deg bevel
LENS_STEP = 2.0                  # the lens's wide front part: its pocket's depth in the plate
HEART_W = 34.0                   # the heart badge across
KEY_D = 11.0
PT = 5.0                         # the plate's thickness
YF = -16.5                       # the plate's face (local y)
YR = YF + PT                     # its back = the back shell's front
YBI = 5.0                        # the back shell's inner face (2.5 behind the board)
YB = YBI + WALL
INSET = 2.0                      # the back shell set in from the plate
FR = 6.0                         # the concave fillets plaque / stem (on the back shell)
NECK_HALF = 36.0                 # the stem's half width: the board + 1.8 mm a side inside
STEM_SET = 2.8                   # the stem's front, set back from the plate's face
NZ0 = -12.0                      # the neck's bottom before the flat cut (below the desk plane)
FOOT_H, WT = 2.0, 5.0            # rubber feet, the steel weight plate
COLOURS = {"Plate": "brushed_alu", "Back": "graphite", "Base": "matte_black", "Screen_Lens": "smoked",
           "Heart_Badge": "#ff4d6d", "Cycle_Key": "signal_red", "Weight": "satin_grey",
           "Foot": "rubber", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
UPRIGHT_FRONT = Rotation(Vector(0, 0, 1), 180)
UZ = FOOT_H + WT + 0.5 + 3.1 + 10.21 / 2        # the USB-C module's centre: its socket 0.5 mm over the weight
ZF = UZ + 9.0                                   # the slot floor (the plate's front-bottom edge): a gentle drop
TILT_PL = Placement(V(0, 0, ZF), Rotation(V(1, 0, 0), -TILT), V(0, YF, 0))
TILT_M = TILT_PL.toMatrix()
INV_M = TILT_PL.inverse().toMatrix()
board = ap.board_object(doc)
board.Placement = Placement(V(), UPRIGHT_FRONT)
_b = ap.bbox(board)
board.Placement = TILT_PL.multiply(Placement(V(-_b.XMin, 0, Z0 - _b.ZMin), UPRIGHT_FRONT))
scr = ap.seat(doc, "big_screen", (13, 14))      # left column, overhangs 40 mm left: landscape digits
_g = scr.Mesh.copy()
_g.Placement = TILT_PL.inverse().multiply(_g.Placement)
SB = _g.BoundBox                                # the screen, local frame
BB = board.Mesh.copy()
BB.Placement = TILT_PL.inverse().multiply(BB.Placement)
BB = BB.BoundBox
CX = (BB.XMin + BB.XMax) / 2                    # the plaque's centre line: the board's (the stem's)
WX, WZ = (SB.XMin + SB.XMax) / 2, (SB.ZMin + SB.ZMax) / 2   # the window's centre = the screen's
WW, WH = (SB.XMax - SB.XMin) + 2 * WIN_M, (SB.ZMax - SB.ZMin) + 2 * WIN_M
WIN_L = WX - WW / 2 - LEDGE - BEV               # the window's outer edge (left)
HX = 2 * CX - WIN_L - HEART_W / 2               # the right column (heart, key) mirrors the window
# the heart light and the cycle key: CABLED straight out of the right
# column (6 and 4) to the right, facing the front: the ribbon stays flat
PORT6_Z, PORT4_Z = Z0 + 109.99, Z0 + 70.19      # MEASURED: the seated cells' centres
heart, heart_rib = ap.cable(doc, "light", 6, TILT_PL.multiply(ap.module_placement(
    "light", (HX, -4.77, PORT6_Z), face="-Y", cable="-X")))
btn, btn_rib = ap.cable(doc, "button", 4, TILT_PL.multiply(ap.module_placement(
    "button", (HX, -5.02, PORT4_Z), face="-Y", cable="-X")))
# USB-C: CABLED from port 7 straight down out of the neck and back under
# the plaque into a bay in the base, its mouth at the base's back (+Y)
USB_Y = 30.0
usb, usb_rib = ap.cable(doc, "usbc", 7, ap.module_placement(
    "usbc", (30.0, USB_Y, UZ), face="+Z", cable="-Y"))
tick("hardware")


def W_(s):
    """Local frame -> world (tilted back, standing on the slot floor)."""
    s = s.copy()
    s.transformShape(TILT_M)
    return s


def L_(s):
    """World -> local frame."""
    s = s.copy()
    s.transformShape(INV_M)
    return s


def lbox(obj):
    """An Atech object's box in the LOCAL (untilted) frame."""
    g = (obj.Mesh if hasattr(obj, "Mesh") else obj.Shape).copy()
    g.Placement = TILT_PL.inverse().multiply(g.Placement)
    return g.BoundBox


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, d, h):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def yprism(x0, x1, z0, z1, r, y0, y1):
    """A rounded rectangle in (x, z) extruded along Y from y0 to y1."""
    w = cad.rounded_rect_wire(x1 - x0, z1 - z0, r, ((x0 + x1) / 2, y0, (z0 + z1) / 2), "Y")
    s = Part.Face(w).extrude(V(0, y1 - y0, 0))
    if s.Volume < 0:
        s.reverse()
    return s


def frustum(w0, h0, w1, h1, r0, r1, y0, y1, cx, cz):
    """A rounded-rectangle frustum along Y: w0 x h0 at y0 to w1 x h1 at y1."""
    a = cad.rounded_rect_wire(w0, h0, r0, (cx, y0, cz), "Y")
    b = cad.rounded_rect_wire(w1, h1, r1, (cx, y1, cz), "Y")
    return cad.loft([a, b], ruled=True)


def centre(b):
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


HB, KB = lbox(heart), lbox(btn)
HRB, KRB = lbox(heart_rib[0]), lbox(btn_rib[0])
UB = ap.bbox(usb)                               # world (the base is not tilted)
print("LOCAL board x %.1f..%.1f z %.1f..%.1f; screen x %.1f..%.1f z %.1f..%.1f; heart x %.1f..%.1f "
      "z %.1f..%.1f; key x %.1f..%.1f z %.1f..%.1f; WORLD usb x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (
          BB.XMin, BB.XMax, BB.ZMin, BB.ZMax, SB.XMin, SB.XMax, SB.ZMin, SB.ZMax, HB.XMin, HB.XMax,
          HB.ZMin, HB.ZMax, KB.XMin, KB.XMax, KB.ZMin, KB.ZMax, UB.XMin, UB.XMax, UB.YMin, UB.YMax,
          UB.ZMin, UB.ZMax))

# ------------------------------------------------------------ the layout
WX0, WX1 = CX - WIDTH / 2, CX + WIDTH / 2
LEG_Z = WZ - WH / 2 - LEDGE - BEV - 5.5         # the legend under the window
PZ0 = min(KB.ZMin - INSET - WALL - 1.0, LEG_Z - 10.0)   # the plaque's bottom: under the key and the legend
PZ1 = WZ + WH / 2 + LEDGE + BEV + 11.0          # its top: 11 mm over the window
NX0, NX1 = CX - NECK_HALF, CX + NECK_HALF
YN = YF + STEM_SET                              # the stem's front
KX, KZ = centre(KB)[0], centre(KB)[2]
HZ = centre(HB)[2]


def t_body(ins, y0, y1, z_bot=NZ0):
    """The T outline (plaque over a neck, concave fillets) set in `ins`,
    extruded along Y from y0 to y1; the neck runs down to z_bot."""
    r = max(1.0, CORNER - ins)
    px0, px1, pz0, pz1 = WX0 + ins, WX1 - ins, PZ0 + ins, PZ1 - ins
    nx0, nx1, fr = NX0 + ins, NX1 - ins, FR + ins
    plaque = yprism(px0, px1, pz0, pz1, r, y0, y1)
    neck = box(nx0, nx1, y0, y1, z_bot, pz0 + r)
    fl = cad.cut(box(nx0 - fr, nx0 + 0.5, y0, y1, pz0 - fr, pz0 + 0.5), cyl(fr, (nx0 - fr, y0 - 1, pz0 - fr), (0, 1, 0), y1 - y0 + 2))
    fr_ = cad.cut(box(nx1 - 0.5, nx1 + fr, y0, y1, pz0 - fr, pz0 + 0.5), cyl(fr, (nx1 + fr, y0 - 1, pz0 - fr), (0, 1, 0), y1 - y0 + 2))
    return cad.fuse_one(plaque, neck, fl, fr_)


ABOVE_F = L_(box(-400, 400, -400, 400, ZF, 600))                 # world z >= the slot floor
ABOVE_W = L_(box(-400, 400, -400, 400, ZF + WALL, 600))          # the neck's floor, flat on it

# ------------------------------------------------------------ the plate
plate = yprism(WX0, WX1, PZ0, PZ1, CORNER, YF, YR)
_flat = plate
try:
    plate = plate.makeChamfer(1.2, [e for e in plate.Edges if e.BoundBox.YMax < YF + 0.01])
    plate = plate if plate.isValid() else _flat
except Exception as exc:                                         # noqa: BLE001
    plate = _flat
    print("NOTE chamfer: %s" % exc)
# the window: a 45 deg bevel down to the smoked lens's wide front (in a
# pocket LENS_STEP deep), then the screen's window straight through
LW, LH = WW + 2 * LEDGE, WH + 2 * LEDGE
plate = cad.cut(plate, [frustum(LW + 2 * (BEV + 0.5), LH + 2 * (BEV + 0.5), LW, LH, 5.0 + BEV + 0.5, 5.0,
                                YF - 0.5, YF + BEV, WX, WZ),
                        yprism(WX - LW / 2, WX + LW / 2, WZ - LH / 2, WZ + LH / 2, 5.0, YF + BEV - 0.2,
                               YF + BEV + LENS_STEP),
                        yprism(WX - WW / 2, WX + WW / 2, WZ - WH / 2, WZ + WH / 2, 3.0, YF + BEV + LENS_STEP - 0.2,
                               YR + 1.0)])
lens = cad.fuse_one(yprism(WX - LW / 2, WX + LW / 2, WZ - LH / 2, WZ + LH / 2, 5.0, YF + BEV, YF + BEV + LENS_STEP),
                    yprism(WX - WW / 2, WX + WW / 2, WZ - WH / 2, WZ + WH / 2, 3.0, YF + BEV + LENS_STEP - 0.5, YR))
tick("plate")

# ------------------------------------------------------------ the back shell
back = t_body(INSET, YR, YB)
back = cad.cut(back, t_body(INSET + WALL, YR - 1.0, YBI).common(ABOVE_W))
# the stem's front wall: under the plate, set back STEM_SET from its face
back = cad.fuse_one(back, box(NX0 + INSET, NX1 - INSET, YN, YR + 0.5, NZ0, PZ0))
back = back.common(ABOVE_F)
tick("back shell")
add = []
# the board: ledges under (notched for the USB-C ribbon) and over it,
# standoffs 0.1 mm behind it
URB = L_(usb_rib[0].Shape).BoundBox
add += [box(BB.XMin + 2, URB.XMin - 1.5, -4.0, YBI + 0.5, BB.ZMin - 6.0, BB.ZMin - 0.3),
        box(URB.XMax + 1.5, BB.XMax - 2, -4.0, YBI + 0.5, BB.ZMin - 6.0, BB.ZMin - 0.3),
        box(BB.XMin + 2, BB.XMax - 2, 0.6, YBI + 0.5, BB.ZMax + 0.3, BB.ZMax + 2.3)]
add += [box(BB.XMin + x, BB.XMin + x + 6, BB.YMax + 0.1, YBI + 0.5, BB.ZMin + z, BB.ZMin + z + 6)
        for x in (24, 48) for z in (12, 50, 100)]
# the screen's overhang: a ledge under it, one over it, standoffs behind
add += [box(SB.XMin + 3, BB.XMin - 1, -7.0, YBI + 0.5, SB.ZMin - 2.3, SB.ZMin - 0.3),
        box(SB.XMin + 3, BB.XMin - 1, -7.0, YBI + 0.5, SB.ZMax + 0.3, SB.ZMax + 2.3)]
add += [box(SB.XMin + x, SB.XMin + x + 6, SB.YMax + 0.1, YBI + 0.5, SB.ZMin + 6, SB.ZMin + 12) for x in (4, 24)]
add += [box(SB.XMin + x, SB.XMin + x + 6, SB.YMax + 0.1, YBI + 0.5, SB.ZMax - 12, SB.ZMax - 6) for x in (4, 24)]
# the heart light and the key: ribs above and below (0.3 mm off; their
# ribbons leave the -X side), a pad behind the key
for MB in (HB, KB):
    add += [box(MB.XMin + 4.0, MB.XMax - 1.0, MB.YMin + 1.0, YBI + 0.5, MB.ZMin - 1.6, MB.ZMin - 0.3),
            box(MB.XMin + 4.0, MB.XMax - 1.0, MB.YMin + 1.0, YBI + 0.5, MB.ZMax + 0.3, MB.ZMax + 1.6)]
add += [box(KB.XMin + 4, KB.XMax - 3, KB.YMax + 0.2, YBI + 0.5, KB.ZMin + 4, KB.ZMax - 4),
        box(HB.XMin + 4, HB.XMax - 3, HB.YMax + 0.2, YBI + 0.5, HB.ZMin + 4, HB.ZMax - 4)]


# four M2.5 screws from the back, through columns into pilots in the
# plate: the plaque's corners (a top-left one that would meet the window's
# bevel moves over the window)
def screw_at():
    xi0, xi1 = WX0 + INSET + WALL + 5.0, WX1 - INSET - WALL - 5.0
    zi0, zi1 = PZ0 + INSET + WALL + 5.0, PZ1 - INSET - WALL - 5.0
    tl = (xi0, zi1) if xi0 < WIN_L - 4.0 else (WX - WW / 4, PZ1 - INSET - WALL - 3.2)
    return [(xi0, zi0), (xi1, zi0), (xi1, zi1), tl]


SCREWS = screw_at()
add += [cyl(3.0, (x, YBI + 0.5, z), (0, -1, 0), YBI + 0.5 - YR) for x, z in SCREWS]
back = cad.fuse_one(back, *add).common(ABOVE_F)     # the ledges trimmed to the slot floor too
PILOT = PT - 1.2
# a stock length (ISO 10642 M2.5: ... 16, 20, 25): the heads sink in a
# counterbore so the tip still ends PILOT - 0.3 into the plate
SCREW_L = max(n for n in (12, 16, 20, 25) if n <= YB - YR + PILOT - 0.3)
SINK = YB - YR + PILOT - 0.3 - SCREW_L           # the counterbore's depth
screws = []
for x, z in SCREWS:
    if SINK > 0.05:
        back = cad.cut(back, cyl(2.75, (x, YB + 0.5, z), (0, -1, 0), SINK + 0.5))
    back = cad.countersink(back, (x, YB - SINK, z), "-Y", 2.9, 4.9, 90.0)
    plate = cad.hole(plate, (x, YR, z), "-Y", 2.1, depth=PILOT)
    screws.append(cad.screw("csk_phillips", "M2.5", SCREW_L, at=(x, YB - SINK, z), axis="-Y"))
tick("board + screws")

# ------------------------------------------------------------ openings
# a rib from the plate onto the board's spine (0.2 mm off), under the plaque's middle
plate = cad.fuse_one(plate, box(BB.XMin + 27, BB.XMin + 33, YR - 0.5, BB.YMin - 0.2, PZ0 + 3.0, PZ0 + 13.0))
# the heart: a frosted insert filling a heart-shaped hole through the
# plate (0.6 mm under its face), its pipe on to 0.45 mm off the LED grid
# (the classic heart curve, its tip cut to a 3 mm flat and its notch eased:
# no knife edge in the insert or the plate)
s = HEART_W / 32.0
pts = []
for i in range(1, 48):
    t = 2 * math.pi * i / 48
    z = s * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
    if z < -15.2 * s:
        continue
    pts.append(V(HX + s * 16 * math.sin(t) ** 3, 0, HZ + z + 1.5 * s))
pts.append(pts[0])
heart_face = Part.Face(Part.makePolygon(pts))
plate = cad.cut(plate, heart_face.extrude(V(0, PT + 2, 0)).translated(V(0, YF - 1, 0)))
badge = heart_face.extrude(V(0, (HB.YMin - 0.45) - (YF + 0.6), 0)).translated(V(0, YF + 0.6, 0))
# the key: a cap through the plate, flange 0.1 mm behind it, a plunger to
# 0.16 mm off the button
y_base = YR + 0.9
cap = cad.button_cap(KEY_D, y_base - (YF - 1.2), dome=0.6, flange=1.5, at=(KX, y_base, KZ), axis="-Y")
plate = cad.opening_for(plate, cap, clearance=0.25, chamfer=0.4, axis="-Y")
cap = cad.fuse_one(cap, cyl(2.5, (KX, KB.YMin - 0.16, KZ), (0, -1, 0), (KB.YMin - 0.16) - y_base + 0.5))
tick("openings")

# ------------------------------------------------------------ neck -> base
# two bosses in the board's bottom ledges (world-vertical, their tops
# 0.2 mm under the ledge's), pilots up into them; the screws come up
# through the slot floor from the base's cavity
YBOSS = -2.0                                     # the ledge's front half (local y): the floor drops behind
BASE_SCREWS = []
for bx in (BB.XMin + 8.0, BB.XMax - 8.0):
    p = TILT_PL.multVec(V(bx, YBOSS, 0.0))
    top = TILT_PL.multVec(V(bx, YBOSS + 4.5, BB.ZMin - 0.5)).z
    BASE_SCREWS.append((bx, p.y, top))
back = cad.fuse_one(back, *[L_(cyl(3.0, (x, y, ZF + 0.5), (0, 0, 1), t - ZF - 0.5)) for x, y, t in BASE_SCREWS])
UPW = INV_M.multVec(V(0, 0, 1)) - INV_M.multVec(V(0, 0, 0))   # world +Z in the local frame
NECK_PILOT = min(t for _x, _y, t in BASE_SCREWS) - ZF - 0.6
for x, y, _t in BASE_SCREWS:
    back = cad.hole(back, L_(Part.Vertex(V(x, y, ZF))).Point, (UPW.x, UPW.y, UPW.z), 2.1, depth=NECK_PILOT)
# the USB-C ribbon's way down: a slot through the neck's floor
RIB_PTS = usb_rib[0].Shape.tessellate(0.2)[0]
RIB_PTS_Z = [p for p in RIB_PTS if ZF - 3.5 < p.z < ZF + WALL + 1.0]
RIB_ZMIN = min(p.z for p in RIB_PTS)
print("USB ribbon: lowest z %.2f (weight top %.2f); through the floors y %.1f..%.1f" % (
    RIB_ZMIN, FOOT_H + WT, min(p.y for p in RIB_PTS_Z), max(p.y for p in RIB_PTS_Z)))
rib_cut = box(min(p.x for p in RIB_PTS_Z) - 0.8, max(p.x for p in RIB_PTS_Z) + 0.8,
              min(p.y for p in RIB_PTS_Z) - 0.8, max(p.y for p in RIB_PTS_Z) + 0.8, ZF - 3.0, ZF + WALL + 0.8)
back = cad.cut(back, L_(rib_cut))
tick("neck")

# ------------------------------------------------------------ the base
BW = 0.8 * WIDTH
BY0 = TILT_PL.multVec(V(0, YN, 0)).y - 24.0                 # the plinth's front: 24 mm before the stem
MOUTH_Y = UB.YMax                                           # the USB-C mouth (world)
BY1 = MOUTH_Y + 1.5                                         # its back: 1.25 mm in front of the mouth
BX0, BX1 = CX - BW / 2, CX + BW / 2
# a tapered plinth: its sides lean in TAPER over its height, the top edge rolled
TAPER = 4.0
BCY = (BY0 + BY1) / 2
base = cad.loft([cad.rounded_rect_wire(BW, BY1 - BY0, 16.0, (CX, BCY, FOOT_H), "Z"),
                 cad.rounded_rect_wire(BW - 2 * TAPER, BY1 - BY0 - TAPER, 16.0 - TAPER, (CX, BCY + TAPER / 2, BASE_H),
                                       "Z")], ruled=True)
base = cad.soften(base, 5.0, [e for e in base.Edges if e.BoundBox.ZMin > BASE_H - 0.05])
# the slot: the stem (0.25 mm clear), its floor flat at ZF
slot = W_(box(NX0 + INSET - 0.25, NX1 - INSET + 0.25, YN - 0.25, YB + 0.25, -30, 200)).common(
    box(-400, 400, -400, 400, ZF, 600))
# the cavity under the slot floor (the neck screws' heads, the ribbon), the
# USB-C bay (0.3 mm round the module), the weight's pocket underneath
FLOOR_T = 2.0
cav = box(min(b[0] for b in BASE_SCREWS) - 5.0, max(b[0] for b in BASE_SCREWS) + 5.0,
          min(b[1] for b in BASE_SCREWS) - 5.0, UB.YMin + 2.0, FOOT_H + WT - 0.5, ZF - FLOOR_T)
# the ribbon's way from the cavity up into the slot (it bends under the neck)
cav_up = box(min(p.x for p in RIB_PTS_Z) - 0.8, max(p.x for p in RIB_PTS_Z) + 0.8, min(p.y for p in RIB_PTS_Z) - 0.8,
             UB.YMin + 2.0, FOOT_H + WT - 0.5, ZF + 0.5)
bay = box(UB.XMin - 0.3, UB.XMax + 0.3, UB.YMin - 2.0, MOUTH_Y + 0.25, FOOT_H + WT - 0.5, UB.ZMax + 0.3)
pocket = box(BX0 + 5.0, BX1 - 5.0, BY0 + 5.0, BY1 - 5.0, FOOT_H - 1.0, FOOT_H + WT)
base = cad.cut(base, [slot, cav, cav_up, bay, pocket, rib_cut])
# the plug opening (cad.socket_opening measures a module lying on the
# board; this one stands across it): the mouth MEASURED from the module's
# mesh - the points in its last 0.6 mm along +Y - plus 1.5 mm a side
MP = [p for p in usb.Mesh.Points if p.y > UB.YMax - 0.6]
MX0, MX1 = min(p.x for p in MP), max(p.x for p in MP)
MZ0, MZ1 = min(p.z for p in MP), max(p.z for p in MP)
print("USB-C mouth x %.2f..%.2f z %.2f..%.2f at y %.2f" % (MX0, MX1, MZ0, MZ1, UB.YMax))
plug_cut = Part.Face(cad.rounded_rect_wire(MX1 - MX0 + 3.0, MZ1 - MZ0 + 3.0, 2.0, ((MX0 + MX1) / 2, MOUTH_Y + 0.05,
                                                                                 (MZ0 + MZ1) / 2), "Y"))
base = cad.cut(base, plug_cut.extrude(V(0, BY1 - MOUTH_Y + 2.0, 0)))
base_screws = []
NECK_L = int(FLOOR_T + NECK_PILOT - 0.3)
for x, y, _t in BASE_SCREWS:
    base = cad.countersink(base, (x, y, ZF - FLOOR_T), "+Z", 2.9, 4.9, 90.0)
    base_screws.append(cad.screw("csk_phillips", "M2.5", NECK_L, at=(x, y, ZF - FLOOR_T), axis="+Z"))
# the steel weight plate closes the cavity from below: four M2.5 screws
# into pilots in the plinth, four rubber feet in shallow recesses
weight = box(BX0 + 5.2, BX1 - 5.2, BY0 + 5.2, BY1 - 5.2, FOOT_H, FOOT_H + WT)
WS = [(x, y) for x in (BX0 + 14.0, BX1 - 14.0) for y in (BY0 + 14.0, BY1 - 14.0)]
FEET = [(x, y) for x in (BX0 + 15.0, BX1 - 15.0) for y in (BY0 + 26.0, BY1 - 26.0)]
weight_screws, feet = [], []
for x, y in WS:
    weight = cad.countersink(weight, (x, y, FOOT_H), "+Z", 2.9, 4.9, 90.0)
    base = cad.hole(base, (x, y, FOOT_H + WT), "+Z", 2.1, depth=6.0)
    weight_screws.append(cad.screw("csk_phillips", "M2.5", 10, at=(x, y, FOOT_H), axis="+Z"))
weight = cad.cut(weight, [cyl(5.1, (x, y, FOOT_H - 1.0), (0, 0, 1), 2.5) for x, y in FEET])
feet = [cad.foot(10, FOOT_H + 1.5, style="dome", at=(x, y, FOOT_H + 1.5)) for x, y in FEET]
tick("stage A")


# === STAGE B: details ===
# the engraved legend under the window
plate = cad.text(plate, "FOLLOWERS", (WX, YF, LEG_Z), (0, -1, 0), 6.0, depth=0.8, mode="deboss")
# hex vents in the neck's back, behind the board (between its standoffs)
back = cad.grille(back, ((BB.XMin + BB.XMax) / 2, YB, BB.ZMin + 34.0), (0, 1, 0), (44.0, 16.0), kind="hex",
                  hole=3.0, pitch=4.5)
# a reveal line round the plinth, ATECH on its front
base = cad.groove_ring(base, "Z", FOOT_H + 0.4 * (BASE_H - FOOT_H), w=1.2, depth=0.8)
_f = 0.72
_a = math.atan2(TAPER, BASE_H - FOOT_H)        # the plinth's front leans back this much
base = cad.text(base, "ATECH", (CX, BY0 + TAPER * _f, FOOT_H + _f * (BASE_H - FOOT_H)),
                (0, -math.cos(_a), math.sin(_a)), 5.0, depth=0.4, mode="deboss", up=(0, math.sin(_a), math.cos(_a)))
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape, colour):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = cad.color(COLOURS[colour])
    return o


part("Plate", W_(plate), "Plate")
part("Back", W_(back), "Back")
part("Base", base, "Base")
o = part("Screen_Lens", W_(lens), "Screen_Lens")
o.ViewObject.Transparency = cad.transparency("smoked")
o = part("Heart_Badge", W_(badge), "Heart_Badge")
o.ViewObject.Transparency = cad.transparency("frosted")
part("Cycle_Key", W_(cap), "Cycle_Key")
part("Weight", weight, "Weight")
for i, sh in enumerate(feet):
    part("Foot_%d" % (i + 1), sh, "Foot")
for i, sh in enumerate(screws):
    part("Screw_%d" % (i + 1), W_(sh), "Screw")
for i, sh in enumerate(base_screws):
    part("Screw_Neck_%d" % (i + 1), sh, "Screw")
for i, sh in enumerate(weight_screws):
    part("Screw_Weight_%d" % (i + 1), sh, "Screw")
print("SIZE", cad.measure(Part.makeCompound([o.Shape for o in doc.Objects if hasattr(o, "Shape")
                                             and o.TypeId == "Part::Feature"]))["size"])
print("SCREWS M2.5 csk: plate %d mm, neck %d mm, weight 10 mm" % (SCREW_L, NECK_L))
print("TOTAL %.1f s" % (time.time() - T0))
