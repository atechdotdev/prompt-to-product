"""Example: "a little robot that drives around on paper and draws with a pen" - a domed turtle robot with a real marker through its middle.

fork this file for a drawing robot (a turtle robot, a pen plotter on wheels, a
floor drawing bot, a logo turtle, a sketch bot); change PARAMETERS and the outlines.
ARCHETYPE: drawing robot

How it is built (R1030):
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    pen's axis is the middle of the axle, so the robot turns on the spot
    about its pen tip. Two NEMA 17 steppers (am.load_module) sit back to
    back on one axle, each screwed by four M3 to a bracket on the chassis
    plate, the pen guide tube between their backs; the 60 mm wheels sit on
    the 5 mm shafts in hub sleeves (M3 grub screw) inside wheel wells. The
    board stands UPRIGHT behind the axle, long side across (ports 1-6
    along the top edge, 9-14 the bottom), modules facing back: the two
    TMC2209 stepper drivers SEATED on (9, 10) and (13, 14) - they slide out
    down through slots in the chassis that the belly plate closes - and
    the tail light SEATED on 3 behind a red light pipe out of the back.
    Everything else is CABLED: the screen (1, 2) tilted 40 deg behind the
    face visor on the shoulder, the GO key's button (4) under the crown,
    USB-C (5) low in the back (pocket + liner, the opening measured from
    the module's mouth) and the pen-lift N20 (6) in front of the tube, its
    shaft +Y carrying an eccentric cam under the pen carrier's tab (lift
    5 mm; pen down the marker rests on the paper by its own weight). The
    shell is ONE revolved section with both skins (vertical skirt, a
    shoulder arc, a crown arc tangent to it, the pen tower and its bore),
    four M3 screws from under the chassis into heat-set insert bosses; the
    belly plate (four M3) holds the 5/8" caster ball and closes the slots.
    Ports 7, 8, 11 and 12 stay empty (8 and 12 are reserved).
  * STAGE B - details: the rubber bumper band (two halves between the
    arches), the smile, the chrome tower ring, driver vents, the GO
    key ring, lettering, the pen collar's grooves and thumb screw, the
    marker cap's clip.
DETAILS (visible, 28): 1 a domed toy-yellow shell, 160 across; 2 rolled
shoulder; 3 the pen tower on the crown; 4 chrome tower ring; 5 the marker
standing through it (a real 11.5 mm felt-tip); 6 its posted blue cap
with a clip; 7 orange pen collar with two grooves; 8 its chrome thumb
screw that clamps the marker; 9 black visor on the shoulder; 10 smoked
screen window (the eyes); 11 the coral GO key; 12 its raised ring; 13-14
two wheel arches; 15-16 wheel wells closing them; 17-18 block-tread
tyres (rib tread); 19-20 white five-window rims; 21-22 chrome caps; 23 rubber bumper
band round the skirt; 24 a smile grooved under the face; 25 "ATECH" on the back;
26 red tail light in the back; 27 USB-C pocket in the back; 28 slot vents
over each driver; plus the graphite chassis plate with its chamfer, the
belly plate with the caster ring and "ATECH DRAW-1", countersunk screws.
Inside: NEMA brackets with gussets, the guide tube and its tab slot, the
pen carrier and tab, the eccentric cam, the N20 cradle and cheeks, the
board's fences, post and ledge, the screen's light tunnel and end ribs
on the visor, the key's L-ribs and plunger, USB-C ribs, insert bosses,
the caster socket.
Materials: toy-yellow shell, graphite chassis and belly plate, black
visor, smoked window, coral key, orange collar and cam, white marker with
a blue cap, rubber tyres and bumper, white rims, chrome caps, ring and
screws, a red tail light, a steel ball.
Power: USB-C gives 5 V. The SDK's stepper driver expects its own 12-24 V
motor supply (./check NOTE WIRING); a TMC2209 runs from 4.75 V, so 5 V
moves the steppers slowly with little torque - fine for drawing, or feed
a USB-C PD trigger at 12 V to the drivers' VM.
Fasteners: M3 throughout - 8 x M3x6 pan (motors), 8 x M3x10 countersunk
(shell, belly plate) into 8 M3 heat-set inserts, 1 x M3x6 button (the
pen clamp), 2 x M3 grub screws (hubs, not modelled).
MEASURED (R1030, 2026-11-20): ./check CHECK PASS, run_seconds 13 s, wall 48 s; every RESTYLE end CHECK PASS.
"""
import math
import time
import Part
import atech_ports as ap
import atech_modules as am
import atech_cad as cad
from FreeCAD import Vector, Placement, Rotation
V = Vector
T0 = time.time()

INTENT = {"board": "upright", "fitted_after": [
    "Shell", "Visor", "Screen_Lens", "Tail_Lens", "Go_Key", "Belly_Plate", "Bumper_F", "Bumper_B", "Tower_Ring",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4", "Screw_5", "Screw_6", "Screw_7", "Screw_8"],
    "covers": {"Go_Key": "button_4", "Tail_Lens": "light_p3"}}
REVIEW_CLOSEUPS = ["Visor", "Pen_Carrier", "Tyre_R"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and cutter in
# the stages is derived from them (the crown and its inner skin, the
# tower and its bore, the visor and the screen behind it, the key, the
# pockets, the bosses).
DOME_H = 48.0      # RESTYLE 40.8..55.2 height: the dome's rise from the skirt's shoulder line to the crown
TOWER_R = 16.0     # RESTYLE 13.6..18.4 radius: the pen tower round the guide tube
VISOR_W = 58.0     # RESTYLE 49..67 width: the black face visor across the front
WALL = 2.4         # RESTYLE 2.0..2.8 wall
# end RESTYLE
# World frame: the pen's axis is x = y = 0 (the middle of the axle: the
# robot turns on the spot about its pen), z up, the paper at z = 0; the
# robot drives toward -Y (its face), the board stands upright behind the
# axle. Every number below is the hardware's own or derived from the knobs.
R_O = 80.0                 # the shell's outside radius (160 mm across)
SKIRT_Z = 50.0             # the vertical skirt's top: the shoulder starts here
ROLL_R = 32.0              # the shoulder's radius (the crown is tangent to it)
Z_SH0 = 8.5                # the shell's foot = the chassis plate's top
CH_Z0 = 4.0                # the chassis plate's underside (4 mm over the paper)
WHEEL_R, WHEEL_W = 30.0, 12.0
AXLE_Z = WHEEL_R           # the steppers' shafts
MOT_FACE = 52.0            # each NEMA 17's mounting face (x); its back at 12.0, 0.6 off the tube
WHEEL_X = 72.5             # tyre centre (x): its outer face 2 mm inside the arch
BRACKET_T = 3.0
TUBE_R = (9.4, 11.4)       # the pen guide tube (inside, outside): 0.9 mm round the carrier
CARRIER_R = (6.05, 8.5)    # the pen carrier sleeve (bore 12.1 for a 11.5 mm marker)
MARKER_R = 5.75
LIFT = 5.0                 # pen lift (the cam's eccentricity x 2)
ZCAM = 36.0                # the pen-lift cam's shaft
TOWER_H = 6.0              # the tower over the crown
BOARD_Y, ZB = 24.0, 10.0   # the board's front face (y) and bottom edge (z)
PHI_V = 40.0               # the visor's centre on the shoulder (deg above level)
VISOR_H = 30.0
SCREEN_WIN = (30.0, 17.0)  # smoked window over the screen (active 25.6 x 13.5)
KEY_D = 14.0
BALL_D = 15.875            # a 5/8" steel ball caster
BALL_Y = 48.0
SCREW = "M3"
SCREW_ANG = (30, 150, 225, 315)
COLOURS = {"Chassis": "graphite", "Shell": "toy_yellow", "Visor": "matte_black",
           "Screen_Lens": "smoked", "Tail_Lens": "led_red", "Go_Key": "coral",
           "Pen_Carrier": "orange", "Cam": "orange", "Bumper": "rubber", "Tower_Ring": "chrome", "Marker": "matte_white", "Marker_Cap": "toy_blue",
           "Tyre": "rubber", "Rim": "matte_white", "Wheel_Cap": "chrome",
           "Belly_Plate": "graphite", "Caster_Ball": "chrome", "Screw": "chrome"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def annulus(r0, r1, z0, z1, c=(0.0, 0.0)):
    return cad.cut(cyl(r1, (c[0], c[1], z0), z1 - z0), cyl(r0, (c[0], c[1], z0 - 1), z1 - z0 + 2))


def arc(c, r, a0, a1):
    """('arc', mid, end) of the circle (c, r) from angle a0 to a1 (deg)."""
    am_, a1_ = math.radians((a0 + a1) / 2), math.radians(a1)
    return ("arc", (c[0] + r * math.cos(am_), c[1] + r * math.sin(am_)),
            (c[0] + r * math.cos(a1_), c[1] + r * math.sin(a1_)))


# the dome: a vertical skirt, a shoulder arc (ROLL_R) and a crown arc
# tangent to it reaching SKIRT_Z + DOME_H on the axis; the inner skin is the
# same two arcs WALL smaller (one wall thickness everywhere)
D_SH = R_O - ROLL_R                                      # the shoulder arc's centre radius
TH = math.pi / 2 - 2 * math.atan((DOME_H - ROLL_R) / D_SH)   # the tangent angle
C_R = ROLL_R + D_SH / math.cos(TH)                       # the crown's radius
ZC = SKIRT_Z - (C_R - ROLL_R) * math.sin(TH)             # the crown's centre (z)
TOP = ZC + C_R
T_TOP = TOP + TOWER_H


def dome_z(r, off=0.0):
    """The skin's height at radius r: off = 0 the outside, WALL the inside."""
    rt = D_SH + (ROLL_R - off) * math.cos(TH)
    if r <= rt:
        return ZC + math.sqrt((C_R - off) ** 2 - r * r)
    if r <= R_O - off:
        return SKIRT_Z + math.sqrt(max((ROLL_R - off) ** 2 - (r - D_SH) ** 2, 0.0))
    return None


def dome_section(off_out, off_in, z0, bore=None, inner_axis=True):
    """A closed (r, z) section between the skins offset off_out and
    off_in (0 = outside, WALL = inside), from z0 up."""
    thd = math.degrees(TH)
    ro, ri = R_O - off_out, R_O - off_in
    pts = [(0, ZC + C_R - off_out), arc((0, ZC), C_R - off_out, 90, thd)[1:],
           arc((D_SH, SKIRT_Z), ROLL_R - off_out, thd, 0), (ro, z0), (ri, z0), (ri, SKIRT_Z),
           arc((D_SH, SKIRT_Z), ROLL_R - off_in, 0, thd), arc((0, ZC), C_R - off_in, thd, 90)]
    return pts


TB = TUBE_R[1] + 0.3                     # the tower's bore round the guide tube
T_RND = min(2.5, 0.5 * (TOWER_R - TB))     # the tower's rolled top edge
thd = math.degrees(TH)
a_tw = math.degrees(math.acos(TOWER_R / C_R))
a_sl = math.degrees(math.acos((TB + 1.8) / (C_R - WALL)))
Z_SLEEVE = dome_z(TB + 1.8, WALL) - 5.0
section = [
    (TB, T_TOP), (TOWER_R - T_RND, T_TOP), arc((TOWER_R - T_RND, T_TOP - T_RND), T_RND, 90, 0),
    (TOWER_R, dome_z(TOWER_R)), arc((0, ZC), C_R, a_tw, thd), arc((D_SH, SKIRT_Z), ROLL_R, thd, 0),
    (R_O, Z_SH0), (R_O - WALL, Z_SH0), (R_O - WALL, SKIRT_Z),
    arc((D_SH, SKIRT_Z), ROLL_R - WALL, 0, thd), arc((0, ZC), C_R - WALL, thd, a_sl),
    (TB + 1.8, Z_SLEEVE), (TB, Z_SLEEVE)]
# the cavity, 0.8 mm into the wall: inner parts are clipped to it so a rib
# or a boss joins the wall without ever reaching its outside
cav_sec = [(0, Z_SH0 - 1), (R_O - WALL + 0.8, Z_SH0 - 1), (R_O - WALL + 0.8, SKIRT_Z),
           arc((D_SH, SKIRT_Z), ROLL_R - WALL + 0.8, 0, thd), arc((0, ZC), C_R - WALL + 0.8, thd, 90)]
CAVITY = cad.revolve_profile(cav_sec)
print("DOME crown r %.1f centre z %.1f, tangent %.1f deg, top %.1f, tower top %.1f" % (C_R, ZC, thd, TOP, T_TOP))

# ------------------------------------------------------------ hardware
LANDSCAPE = Rotation(Vector(0, 1, 0), 90)       # ports 1-6 along the top edge, 9-14 the bottom, modules face +Y
board = ap.board_object(doc)
board.Placement = Placement(Vector(), LANDSCAPE)
_bb = ap.bbox(board)
board.Placement = Placement(Vector(-(_bb.XMin + _bb.XMax) / 2, BOARD_Y - _bb.YMin, ZB - _bb.ZMin), LANDSCAPE)
BB = ap.bbox(board)
print("BOARD x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f; inner skin over its top corner %.1f" % (
    BB.XMin, BB.XMax, BB.YMin, BB.YMax, BB.ZMin, BB.ZMax, dome_z(math.hypot(60.0, BB.YMax), WALL)))
drv_l = ap.seat(doc, "stepper_motor", (9, 10))   # bottom left: the left wheel's TMC2209
drv_r = ap.seat(doc, "stepper_motor", (13, 14))  # bottom right
tail = ap.seat(doc, "light", 3)                  # top row, facing back: the tail light
# the two NEMA 17s back to back on one axle, the guide tube between them
motors = {"R": am.load_module(doc, "nema17_stepper", label="Motor_R",
                              placement=Placement(V(MOT_FACE, 0, AXLE_Z), Rotation(V(0, 0, 1), -90)))[0],
          "L": am.load_module(doc, "nema17_stepper", label="Motor_L",
                              placement=Placement(V(-MOT_FACE, 0, AXLE_Z), Rotation(V(0, 0, 1), 90)))[0]}
# the pen-lift: an N20 in front of the tube, its shaft +Y; the cam on the
# shaft tip lifts the carrier's tab
N20_TIP = -(TUBE_R[1] + 1.3 + 0.3)              # shaft tip (y)
cam_m, cam_rib = ap.cable(doc, "dc_motor", 6, ap.module_placement(
    "dc_motor", (0.0, N20_TIP - 24.15, ZCAM - 0.57), face="+Z", cable="-Y"),
    via=[(46.0, 18.0, 74.0), (36.0, -10.0, 75.0), (34.0, -48.0, 44.0), (0.0, -73.0, ZCAM)], smooth=True)
NB = ap.bbox(cam_m)
SH = [p for p in cam_m.Mesh.Points if p.y > NB.YMax - 3.0]
SHX = (min(p.x for p in SH) + max(p.x for p in SH)) / 2
SHZ = (min(p.z for p in SH) + max(p.z for p in SH)) / 2
print("N20 x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f shaft (%.2f, %.2f) tip y %.2f" % (
    NB.XMin, NB.XMax, NB.YMin, NB.YMax, NB.ZMin, NB.ZMax, SHX, SHZ, NB.YMax))
# the screen behind the visor, tilted to the shoulder's normal
NV = (math.cos(math.radians(PHI_V)), math.sin(math.radians(PHI_V)))       # (r, z) outward normal
S_FACE = ROLL_R - WALL - 4.0                    # its face 4 mm inside the inner skin (the wall curves in plan)
SC = (D_SH + (S_FACE - 4.82) * NV[0], SKIRT_Z + (S_FACE - 4.82) * NV[1])
TILT = Placement(V(0, -SC[0], SC[1]), Rotation(V(1, 0, 0), -PHI_V))
scr, scr_rib = ap.cable(doc, "screen", (1, 2), TILT.multiply(ap.module_placement(
    "screen", (0, 0, 0), face="-Y", cable="+Z")),
    via={1: [(-46.0, 18.0, 74.0), (-40.0, -8.0, 76.0), (-10.0, -42.0, 74.0)],
         2: [(-28.0, 18.0, 75.0), (-22.0, -8.0, 77.0), (10.0, -42.0, 74.0)]}, smooth=True)
# the GO key on the crown behind the tower, cabled from 4 (up and back)
BX, BY = 10.0, 46.0
R_KF = math.hypot(BX, BY) + KEY_D / 2 + 1.5     # the key flange's far edge (the lowest inner skin)
KEY_BASE = dome_z(R_KF, WALL) - 1.1
BTN_TOP = 64.0                                  # the button's top: fixed (its ribbon is short); the plunger takes up the dome
key_m, key_rib = ap.cable(doc, "button", 4, ap.module_placement(
    "button", (BX, BY, BTN_TOP - 5.02), face="+Z", cable="-Y"),
    via=[(BX, BOARD_Y + 4.5, BB.ZMax + 5.0), (BX, BOARD_Y + 10.0, BB.ZMax - 2.0)], smooth=True)
# USB-C at the back, low, mouth +Y 1 mm inside the inner skin
USB_Y1 = R_O - WALL - 1.0
usb, usb_rib = ap.cable(doc, "usbc", 5, ap.module_placement(
    "usbc", (0.0, USB_Y1 - 19.75 / 2, 24.0), face="+Z", cable="-Y"),
    via=[(30.0, 40.0, 75.0), (30.0, 50.0, 45.0), (0.0, 48.0, 24.0)], smooth=True)
tick("hardware")


def insert(shell, cutter):
    """(shell with the opening, the piece that fills it exactly)."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, cad.fuse_one(*piece.Solids) if len(piece.Solids) > 1 else piece.Solids[0]


def tilted_slab(w, h, r, y0, y1, pl):
    """A rounded rectangle w x h (local x, z), corner r, from local y0 to
    y1, placed by pl (the visor's frame: local -Y points out of the wall)."""
    s = cad.rounded_box(w, y1 - y0, h, r, at=(-w / 2, y0, -h / 2), edges="y")
    s.Placement = pl.multiply(s.Placement)
    return s


# ------------------------------------------------------------ the shell
shell = cad.revolve_profile(section)
tick("shell")
# wheel arches through the skirt and shoulder over each tyre
arches = [cyl(WHEEL_R + 3.0, (s_ * 57.5, 0, AXLE_Z), 30.0, (s_, 0, 0)) for s_ in (-1, 1)]
# four M3 insert bosses hugging the skirt, screwed from under the chassis
INSERT_D = {"M2": 3.2, "M2.5": 3.6, "M3": 4.3}[SCREW]
R_BOSS = R_O - WALL - INSERT_D / 2 - 1.2 + 0.8
SCREWS = [(R_BOSS * math.cos(math.radians(a)), R_BOSS * math.sin(math.radians(a))) for a in SCREW_ANG]
cols = [cyl(INSERT_D / 2 + 1.2, (x, y, Z_SH0 + 0.1), 18.0).common(CAVITY) for x, y in SCREWS]
shell = cad.fuse_one(shell, *cols)
bores = [cyl(INSERT_D / 2, (x, y, Z_SH0), 6.1) for x, y in SCREWS]
bores += [cyl(1.25, (x, y, Z_SH0 + 6.0), 4.0) for x, y in SCREWS]
shell = cad.cut(shell, arches + bores)
# wheel wells: a tube round each arch and an end wall 1.5 mm past the
# board's end close the body from inside; a U-slot (open downward) lets
# the shell down over the wheel's hub sleeve
WELL_X = 60.5
wells = []
for s_ in (-1, 1):
    tube = cad.cut(cyl(WHEEL_R + 3.0 + WALL, (s_ * WELL_X, 0, AXLE_Z), R_O - WELL_X, (s_, 0, 0)),
                   cyl(WHEEL_R + 3.0, (s_ * (WELL_X + 2.0), 0, AXLE_Z), R_O, (s_, 0, 0)))
    tube = cad.cut(tube, [cyl(7.6, (s_ * (WELL_X - 1.0), 0, AXLE_Z), 4.0, (s_, 0, 0)),
                          box(s_ * (WELL_X - 1.0), s_ * (WELL_X + 3.0), -7.6, 7.6, 0, AXLE_Z)])
    wells.append(tube.common(CAVITY).common(box(-90, 90, -90, 90, Z_SH0 + 0.3, 120)))
shell = cad.fuse_one(shell, *wells)
tick("arches + bosses")

# the face: a black visor (an insert in the shoulder) with the smoked
# screen window, a light tunnel back to 1 mm off the screen and two ribs
# holding the screen's ends
VP = (D_SH + ROLL_R * NV[0], SKIRT_Z + ROLL_R * NV[1])             # the visor's centre on the outside
VPL = Placement(V(0, -VP[0], VP[1]), Rotation(V(1, 0, 0), -PHI_V))  # local -Y = out
shell, visor = insert(shell, tilted_slab(VISOR_W, VISOR_H, 12.0, -6.0, 8.0, VPL))
visor, screen_lens = insert(visor, tilted_slab(SCREEN_WIN[0], SCREEN_WIN[1], 2.0, -6.0, 8.0, VPL))
D_IN = WALL + 4.0 - 1.0                                            # the tunnel ends 1 mm off the screen
tunnel = cad.cut(tilted_slab(SCREEN_WIN[0] + 3.0, SCREEN_WIN[1] + 3.0, 3.0, WALL - 0.6, D_IN, VPL),
                 tilted_slab(SCREEN_WIN[0], SCREEN_WIN[1], 2.0, WALL - 1.0, D_IN + 1.0, VPL))
ribs = []
for s_ in (-1, 1):
    rb = box(s_ * 20.05, s_ * 21.8, -4.82 - 8.0, 3.5, -7.0, 7.0)
    rb.Placement = TILT.multiply(rb.Placement)
    ribs.append(rb.common(CAVITY).common(tilted_slab(VISOR_W - 2.0, VISOR_H - 2.0, 10.0, -6.0, 40.0, VPL)))
visor = cad.fuse_one(visor, tunnel, *ribs)
tick("visor")

# the tail light: a red pipe from 0.4 mm off the LEDs out through the back
lb = ap.bbox(tail)
lx, lz = (lb.XMin + lb.XMax) / 2, (lb.ZMin + lb.ZMax) / 2
shell, tail_lens = insert(shell, box(lx - 8.0, lx + 8.0, 60.0, R_O + 5.0, lz - 8.0, lz + 8.0))
tail_lens = cad.fuse_one(tail_lens, box(lx - 8.0, lx + 8.0, lb.YMax + 0.4, 72.0, lz - 8.0, lz + 8.0).common(CAVITY))

# the GO key through the crown: a cap on a plunger to 0.16 mm over the
# button, two L-ribs either side of the module (0.3 mm off) hung from the crown
KB = ap.bbox(key_m)
r_near = math.hypot(BX, BY) - KEY_D / 2
cap = cad.button_cap(KEY_D, dome_z(r_near) + 2.0 - KEY_BASE, dome=1.0, flange=1.5, at=(BX, BY, KEY_BASE), axis="+Z")
shell = cad.opening_for(shell, cap, clearance=0.25, chamfer=0.4, axis="+Z")
cap = cad.fuse_one(cap, cyl(3.0, (BX, BY, KB.ZMax + 0.16), KEY_BASE + 0.5 - KB.ZMax - 0.16))
krib = []
for s_ in (-1, 1):
    x0 = BX + s_ * (KB.XLength / 2 + 0.3)
    krib.append(box(x0, x0 + s_ * 1.6, BY - 7.0, BY + 7.0, KB.ZMin - 1.8, KEY_BASE + 6.0).common(CAVITY))
    krib.append(box(x0 + s_ * 1.6, x0 - s_ * 3.0, BY - 7.0, BY + 7.0, KB.ZMin - 1.8, KB.ZMin - 0.3))
shell = cad.fuse_one(shell, *krib)
tick("key + tail")

# USB-C at the back: a pocket brings the skirt to 0.25 mm off the mouth
# (a liner), the plug opening MEASURED from the module's mouth
UB = ap.bbox(usb)
uz = (UB.ZMin + UB.ZMax) / 2
pocket = cad.rounded_box(18.0, 12.0, 10.0, 3.0, at=(-9.0, UB.YMax + 1.3, uz - 5.0), edges="y")
liner = cad.cut(cad.rounded_box(22.0, 8.0, 14.0, 4.0, at=(-11.0, UB.YMax + 0.25, uz - 7.0), edges="y")
                .common(CAVITY), pocket)
MP = [p for p in usb.Mesh.Points if p.y > UB.YMax - 0.6]
MX0, MX1 = min(p.x for p in MP), max(p.x for p in MP)
MZ0, MZ1 = min(p.z for p in MP), max(p.z for p in MP)
plug = Part.Face(cad.rounded_rect_wire(MX1 - MX0 + 3.0, MZ1 - MZ0 + 3.0, 2.0,
                                       ((MX0 + MX1) / 2, UB.YMax + 0.05, (MZ0 + MZ1) / 2), "Y")).extrude(V(0, 12.0, 0))
shell = cad.cut(cad.fuse_one(cad.cut(shell, pocket), liner), plug)
tick("usb")

# ------------------------------------------------------------ the chassis
# a graphite plate under the shell: NEMA brackets, the pen guide tube, the
# board's fences, the N20 cradle, the USB-C ribs, the caster socket
plate = cyl(R_O, (0, 0, CH_Z0), Z_SH0 - CH_Z0)
plate = cad.chamfer_safe(plate, 1.0, [e for e in plate.Edges if e.BoundBox.ZMax < CH_Z0 + 0.01])
Z_IN = Z_SH0 - 0.5                     # every add starts 0.5 mm into the plate
adds = []
for s_ in (-1, 1):
    x0, x1 = s_ * MOT_FACE, s_ * (MOT_FACE + BRACKET_T)
    adds.append(box(x0, x1, -21.15, 21.15, Z_IN, AXLE_Z + 21.15))
    for yy in (-21.15, 18.4):
        g = Part.Face(Part.makePolygon([V(x1 - s_ * 0.5, yy, Z_IN), V(x1 + s_ * 3.0, yy, Z_IN),
                                        V(x1 - s_ * 0.5, yy, Z_SH0 + 16.0), V(x1 - s_ * 0.5, yy, Z_IN)]))
        adds.append(g.extrude(V(0, 2.75, 0)))
adds.append(annulus(TUBE_R[0], TUBE_R[1], Z_IN, T_TOP - 1.0))
for s_ in (-1, 1):                     # fences in front of the board, a post behind it, a ledge under it
    adds.append(box(s_ * 24.0, s_ * 48.0, BB.YMin - 2.0, BB.YMin - 0.3, Z_IN, ZB + 14.0))
adds.append(box(-1.5, 1.5, BOARD_Y + 2.8, BOARD_Y + 6.5, Z_IN, ZB + 12.0))
adds.append(box(-18.0, 18.0, BB.YMin + 0.2, BB.YMin + 2.3, Z_IN, ZB - 0.3))
# the N20's cradle: a block under it and cheeks 0.3 mm off its sides
adds.append(box(-7.0, 7.0, NB.YMin + 3.0, NB.YMax - 12.0, Z_IN, NB.ZMin - 0.3))
for s_ in (-1, 1):
    adds.append(box(s_ * (NB.XLength / 2 + 0.3), s_ * (NB.XLength / 2 + 1.9), NB.YMin + 3.0, NB.YMax - 12.0,
                    Z_IN, NB.ZMin + 12.0))
# the USB-C module's ribs (0.3 mm off its sides)
for s_ in (-1, 1):
    adds.append(box(s_ * (UB.XLength / 2 + 0.3), s_ * (UB.XLength / 2 + 1.9), UB.YMin + 3.0, UB.YMax - 1.0,
                    Z_IN, UB.ZMax - 2.0))
# the caster socket and four insert bosses for the belly plate
BR = BALL_D / 2
adds.append(cyl(11.0, (0, BALL_Y, Z_IN), BALL_D + 0.9 - Z_IN))
CUP_SCREWS = [(-15.0, BALL_Y), (15.0, BALL_Y), (-42.0, BALL_Y - 1.0), (42.0, BALL_Y - 1.0)]
adds += [cyl(INSERT_D / 2 + 1.2, (x, y, Z_IN), 16.5 - Z_IN) for x, y in CUP_SCREWS]
chassis = cad.fuse_one(plate, *adds)
tick("chassis adds")
holes = [cyl(7.5, (0, 0, CH_Z0 - 1), Z_SH0 - CH_Z0 + 2)]                  # the pen
holes += [box(s_ * 62.0, s_ * (R_O + 1.0), -22.5, 22.5, CH_Z0 - 1, Z_SH0 + 0.4) for s_ in (-1, 1)]
for d in (drv_l, drv_r):              # the drivers slide out down through these, the belly plate off
    db = ap.bbox(d)
    holes.append(box(db.XMin - 0.8, db.XMax + 0.8, db.YMin - 0.8, db.YMax + 0.8, CH_Z0 - 1, Z_SH0 + 0.4))
# the belly plate's recess under the back half (it closes the driver slots
# and holds the caster ball)
BELLY = (61.5, BOARD_Y + 0.9, BALL_Y + 11.0, 2.0)            # half width, y0, y1, depth
holes.append(cad.rounded_box(2 * BELLY[0], BELLY[2] - BELLY[1], BELLY[3] + 1.0, 6.0,
                             at=(-BELLY[0], BELLY[1], CH_Z0 - 1.0)))


def xsquare(a, rc, x0, y, z, h):
    """A soft-square hole 2a across (corners rc) along X: the two brackets'
    holes share the axle line, and a soft square is not read as one round
    bore through both."""
    return Part.Face(cad.rounded_rect_wire(2 * a, 2 * a, rc, (x0, y, z), "X")).extrude(V(h, 0, 0))


for s_ in (-1, 1):                    # NEMA pilot (22.5) and its four M3 clearances (3.4) on the 31 square
    xa = s_ * (MOT_FACE - 1.0)
    holes.append(xsquare(11.25, 9.0, xa, 0, AXLE_Z, s_ * (BRACKET_T + 2.0)))
    holes += [xsquare(1.7, 1.2, xa, yy, AXLE_Z + zz, s_ * (BRACKET_T + 2.0))
              for yy in (-15.5, 15.5) for zz in (-15.5, 15.5)]
holes.append(Part.makeSphere(BR + 0.25, V(0, BALL_Y, BR)))
holes.append(cyl(BR + 0.25, (0, BALL_Y, CH_Z0 - 1), BR + 1))
for x, y in CUP_SCREWS:
    holes.append(cyl(1.7, (x, y, CH_Z0 - 1), Z_SH0 - CH_Z0 + 1.5))
    holes.append(cyl(INSERT_D / 2, (x, y, Z_SH0), 5.6))
    holes.append(cyl(1.25, (x, y, Z_SH0 + 5.5), 2.5))
for x, y in SCREWS:                   # countersinks for the shell screws
    holes.append(Part.makeCone(6.2 / 2, 3.4 / 2, (6.2 - 3.4) / 2, V(x, y, CH_Z0 - 0.01), V(0, 0, 1)))
    holes.append(cyl(1.7, (x, y, CH_Z0 - 1), Z_SH0 - CH_Z0 + 2))
# the cam tab's slot in the tube's front
TAB_Z = SHZ - LIFT / 2 + 6.5 + 0.8                  # the tab's underside, 0.8 mm over the cam's low top
holes.append(box(SHX - 3.5, SHX + 3.5, -TUBE_R[1] - 1.0, -TUBE_R[0] + 0.5, TAB_Z - 2.0, TAB_Z + 3.0 + LIFT + 2.0))
chassis = cad.cut(chassis, holes)
tick("chassis")

# ------------------------------------------------------------ wheels
w = cad.wheel(2 * WHEEL_R, WHEEL_W, hub_d=14.0, spokes=5, tread="rib", bore=5.2, axis="+X",
              at=(WHEEL_X, 0, AXLE_Z))
X_IN = WHEEL_X - 0.84 * WHEEL_W / 2                 # the rim's inner face
sleeve = cyl(6.5, (MOT_FACE + BRACKET_T + 0.6, 0, AXLE_Z), X_IN + 0.5 - (MOT_FACE + BRACKET_T + 0.6), (1, 0, 0))
rim = cad.cut(cad.fuse_one(w["rim"], sleeve), [cyl(2.6, (MOT_FACE, 0, AXLE_Z), WHEEL_X - MOT_FACE, (1, 0, 0)),
                                                cyl(1.25, (MOT_FACE + BRACKET_T + 3.5, 0, AXLE_Z + 7.0), 5.0, (0, 0, -1))])
wheels = {"Tyre_R": w["tyre"], "Rim_R": rim, "Wheel_Cap_R": w["cap"]}
for k in list(wheels):
    wheels[k[:-1] + "L"] = cad.mirror(wheels[k], "YZ", (0, 0, 0))
tick("wheels")

# ------------------------------------------------------------ the pen
# the carrier slides in the guide tube; its tab rests 1 mm over the cam
# (pen down, the marker's own weight on the paper); the cam's lobe lifts it
CAR_Z0 = 13.0
COLLAR = (T_TOP + 1.0, T_TOP + 9.0, 12.5)
carrier = cad.fuse_one(annulus(CARRIER_R[0], CARRIER_R[1], CAR_Z0, COLLAR[0] + 0.5),
                       annulus(CARRIER_R[0], COLLAR[2], COLLAR[0], COLLAR[1]),
                       box(SHX - 2.5, SHX + 2.5, -CARRIER_R[1] - 0.5 + 1.0, N20_TIP - 3.4, TAB_Z, TAB_Z + 3.0)
                       .cut(cyl(CARRIER_R[0], (0, 0, TAB_Z - 1), 5.0)))
CAM_Y0, CAM_Y1 = N20_TIP + 0.3, N20_TIP - 3.7
cam = cad.fuse_one(cyl(6.5, (SHX, CAM_Y0, SHZ - LIFT / 2), CAM_Y0 - CAM_Y1, (0, -1, 0)),
                   cyl(3.5, (SHX, CAM_Y1 + 0.5, SHZ), 5.0, (0, -1, 0)))
cam = cad.cut(cam, cyl(1.65, (SHX, CAM_Y0 + 1.0, SHZ), 12.0, (0, -1, 0)))
M_TOP = COLLAR[1] + 30.0
marker = cad.fuse_one(cyl(1.5, (0, 0, 0), 4.5), Part.makeCone(3.0, MARKER_R, 8.0, V(0, 0, 4.0)),
                      cyl(MARKER_R, (0, 0, 11.9), M_TOP - 11.9))
mcap = cad.fuse_one(annulus(MARKER_R + 0.1, MARKER_R + 1.1, M_TOP - 6.0, M_TOP + 20.0),
                    Part.makeSphere(MARKER_R + 1.1, V(0, 0, M_TOP + 20.0)).common(
                        cyl(MARKER_R + 1.1, (0, 0, M_TOP + 19.5), 3.0)))
tick("pen")

# ------------------------------------------------------------ the caster
# the belly plate: flush in its recess, a ring under the ball (2 mm
# proud) whose 7.2 mm lip keeps the 5/8" ball in its socket
ball = Part.makeSphere(BR, V(0, BALL_Y, BR))
RING_Z = 2.0
belly = cad.fuse_one(cad.rounded_box(2 * BELLY[0] - 0.4, BELLY[2] - BELLY[1] - 0.4, BELLY[3], 5.8,
                                     at=(-BELLY[0] + 0.2, BELLY[1] + 0.2, CH_Z0)),
                     cyl(11.0, (0, BALL_Y, RING_Z), CH_Z0 - RING_Z + 0.5))
belly = cad.cut(belly, [cyl(7.2, (0, BALL_Y, RING_Z - 1.0), CH_Z0 - RING_Z + 1.0),
                        cyl(BR + 0.3, (0, BALL_Y, CH_Z0), BELLY[3] + 1.0)]
                + [Part.makeCone(6.2 / 2, 3.4 / 2, 1.4, V(x, y, CH_Z0 - 0.01), V(0, 0, 1)) for x, y in CUP_SCREWS]
                + [cyl(1.7, (x, y, CH_Z0 - 1.0), BELLY[3] + 2.0) for x, y in CUP_SCREWS])
screws = [cad.screw("csk_phillips", SCREW, 10, at=(x, y, CH_Z0), axis="+Z") for x, y in SCREWS + CUP_SCREWS]
for s_ in (-1, 1):
    xa = s_ * (MOT_FACE + BRACKET_T)
    screws += [cad.screw("pan_phillips", SCREW, 6, at=(xa, yy, AXLE_Z + zz), axis=(-s_, 0, 0))
               for yy in (-15.5, 15.5) for zz in (-15.5, 15.5)]
tick("stage A")


# === STAGE B: details ===
# (a fork may stop after STAGE A, run ./check, then add these one by one)
# a rubber bumper band round the skirt in its own seat (cut by the arches)
BUMP = (12.0, 21.0)
bseat = cad.cut(annulus(R_O - 0.8, R_O + 1.5, BUMP[0], BUMP[1]),
                [cyl(WHEEL_R + 4.5, (s_ * 50.0, 0, AXLE_Z), 40.0, (s_, 0, 0)) for s_ in (-1, 1)])
bumper = cad.soften(bseat, 0.6, [e for e in bseat.Edges if e.BoundBox.XMax > -R_O - 0.5 and
                                 math.hypot(e.BoundBox.XMax, e.BoundBox.YMax) > R_O + 1.0])
shell = cad.cut(shell, bseat)
# the chrome ring on the tower
tring = annulus(TB, TOWER_R + 1.0, T_TOP - 3.0, T_TOP + 1.0)
tower_ring = shell.common(tring)
shell = cad.cut(shell, tring)
# vents over the two drivers in the back of the skirt
for s_ in (-1, 1):
    a = math.radians(90 - s_ * 32)
    shell = cad.grille(shell, (R_O * math.cos(a), R_O * math.sin(a), 31.0), (math.cos(a), math.sin(a), 0),
                       (26.0, 9.0), kind="slot", hole=2.2, pitch=4.4)
# lettering: ATECH under the face, USB-C over the socket, DRAW-1 under the belly
shell = cad.text(shell, "ATECH", (0, R_O, 36.0), (0, 1, 0), 6.0, depth=0.5, mode="deboss")
# a smile under the face: a round groove 1 mm deep along the skirt
SMILE = [(x, -math.sqrt(R_O ** 2 - x * x), 42.0 - 5.0 * (1 - (x / 15.0) ** 2)) for x in (-15, -9, -3, 3, 9, 15)]
shell = cad.cut(shell, cad.pipe(SMILE, r=1.1))
belly = cad.text(belly, "ATECH DRAW-1", (0, BALL_Y - 17.0, CH_Z0), (0, 0, -1), 4.5, depth=0.4,
                 mode="deboss", up=(0, -1, 0))
# a raised ring round the GO key and its legend on the cap
rk = math.hypot(BX, BY)
shell = cad.fuse_one(shell, cad.cut(cyl(KEY_D / 2 + 3.2, (BX, BY, dome_z(rk + KEY_D / 2 + 3.2) - 1.0), 2.4),
                                    cyl(KEY_D / 2 + 1.6, (BX, BY, KEY_BASE), 20.0)))
# the pen collar: knurled, with a thumb screw that clamps the marker
carrier = cad.groove_ring(carrier, "Z", COLLAR[0] + 1.6, w=0.8, depth=0.5)
carrier = cad.groove_ring(carrier, "Z", COLLAR[1] - 1.6, w=0.8, depth=0.5)
TS_Z = (COLLAR[0] + COLLAR[1]) / 2
carrier = cad.cut(carrier, Part.makeCylinder(1.25, 9.0, V(COLLAR[2] + 1.0, 0, TS_Z), V(-1, 0, 0)))
screws.append(cad.screw("button", SCREW, 6, at=(COLLAR[2] + 0.05, 0, TS_Z), axis="-X"))
# the marker cap's clip
mcap = cad.fuse_one(mcap, box(-1.6, 1.6, MARKER_R + 0.8, MARKER_R + 2.4, M_TOP - 2.0, M_TOP + 18.0),
                    box(-1.6, 1.6, MARKER_R + 0.8, MARKER_R + 3.2, M_TOP - 2.0, M_TOP + 0.5))
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape, colour=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = cad.color(COLOURS[colour or name])
    return o


part("Chassis", chassis)
part("Shell", shell)
part("Visor", visor)
o = part("Screen_Lens", screen_lens)
o.ViewObject.Transparency = cad.transparency("smoked")
o = part("Tail_Lens", tail_lens)
o.ViewObject.Transparency = cad.transparency("led_red")
part("Go_Key", cap)
part("Pen_Carrier", carrier)
bumpers = sorted(bumper.Solids, key=lambda q: q.BoundBox.Center.y)
part("Bumper_F", bumpers[0], "Bumper")
part("Bumper_B", bumpers[1], "Bumper")
part("Tower_Ring", tower_ring)
part("Cam", cam)
part("Marker", marker)
part("Marker_Cap", mcap)
for nm, sh in wheels.items():
    part(nm, sh, nm[:-2])
part("Belly_Plate", belly)
part("Caster_Ball", ball)
for i, sh in enumerate(screws):
    part("Screw_%d" % (i + 1), sh, "Screw")
print("SIZE %s" % (cad.measure(Part.makeCompound([chassis, shell, marker, mcap]))["size"],))
print("SIZE model build %.1f s" % (time.time() - T0))
