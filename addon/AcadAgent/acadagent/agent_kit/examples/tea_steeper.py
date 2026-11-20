"""Example: "a tea timer that lifts the tea bag out of the cup when it's ready" - a counter-top steeping tower whose arm dips the bag and lifts it out on time.

fork this file for a tea steeper (a tea timer with a lifting arm, an auto
tea-bag dipper, any tower with a stepper-driven arm over a cup); change PARAMETERS and the outlines.
ARCHETYPE: tea steeper

How it is built (R1030):
  * STAGE A - hardware, shell, every working-face opening, fasteners: a
    counter-top tower (about 99 x 75 x 169) that stands beside the cup on
    a wide weighted foot. The board UPRIGHT_FRONT inside it, modules facing
    the front (-Y): the chime speaker (9, 10) bottom left and the minutes
    dial knob (13, 14) top left, both hanging 20 mm out past the board's
    left edge; on the right column the TMC2209 stepper driver (1, 2), the
    ready light (3) and the portrait screen (4, 5) - countdown and tea.
    The arm's motor is an off-board NEMA 17 (am.load_module) BEHIND the
    board's top, its shaft forward over the board's top edge, its face on
    a bulkhead across the tower (22.5 pilot bore, two M3 into the flange's
    top holes; the lower pair sits behind the board) and its body on a
    cradle shelf. USB-C is CABLED from port 11 round the board's left edge
    to the back wall, standing on edge between two ribs, its mouth 1.25 mm
    inside the back face. The tower is one plan (flat face, round front
    corners = the top's roll, big back corners) extruded, rolled on top,
    hollowed by its own core (top edges chamfered inside) and split just
    behind the PCB face into the white Shell (all the openings, fitted
    after the modules) and the sage Back (bulkhead, pads 0.1 mm behind the
    board and both overhangs, edge fences, stands behind the floor's lip,
    the motor cradle, the USB-C bay); two M3 from the back into insert
    sleeves on long Shell columns. THE ARM: one part - a hub, a tapered
    beam 30 deg up and a round tip - turning on the shaft (intent
    "motion": 0 .. 60 deg down, swept clear); its spigot is the pin in a
    bearing sleeve on the face's inner side, a D-bore on the shaft's flat.
    The arm's length sets where the hook hangs and the cup stands, so the
    hook is over the cup at both ends of the swing and the arm never
    reaches the rim. The foot is the hull of the tower's footprint and
    the coaster's circle; the tower stands in a socket in it, and four M3
    from under a steel weight plate go up through the foot into heat-set
    inserts in the tower's floor.
  * STAGE B - details: twelve minute ticks on the dial crown, a knurled
    cork cap with a pointer, STEEP / ATECH lettering, a vein on the glowing
    leaf, a brass cap on the arm's hub, the hook's ball tip, the drip
    groove round the coaster, vent slots over the motor at the back, the
    model mark; props (not printed): a glass tea cup with tea, the tea bag
    lifted out on the hook.
DETAILS (visible, 28): 1 two-tone tower, white Shell over a sage Back;
2 rolled top edge; 3 round front corners matching it; 4 big rounded back
corners; 5 the parting seam between white and sage; 6 sage foot (the
hull of tower and coaster) with a rolled edge; 7 the socket the tower
stands in; 8 cork coaster inlaid 0.5 mm proud; 9 drip groove round it;
10 the sage arm, tapered, with a round tip; 11 brass hub cap; 12 brass
J-hook with a ball tip; 13 dial crown standing out of the face; 14 twelve
minute ticks, the quarters wider; 15 frosted ring over the knob's LEDs;
16 knurled cork dial cap; 17 its pointer groove; 18 "STEEP" over the
dial; 19 sage screen bezel standing proud; 20 smoked lens set 0.6 mm
back in it; 21 frosted amber leaf over the ready light; 22 the leaf's
vein; 23 round chime grille insert (ring of holes); 24 its twin, the
driver's vent; 25 "ATECH" between them; 26 vent slots over the motor at
the back; 27 "ATECH TS-1" on the back; 28 the USB-C bay at the back.
Underneath: seven rubber feet in recesses, the steel weight plate, four
countersunk screws. Inside: the bulkhead with the pilot bore, the
ribbon window and the motor-wire pass; pads, fences, stands; the motor
cradle; the bearing sleeve; a rib onto the board's spine; the USB-C ribs;
the long insert columns.
Materials: ceramic-white Shell, sage Back, foot, arm and bezel, cork dial
cap and coaster, tan grille and vent, brass hub cap and hook, smoked
lens, frosted ring, frosted amber leaf, satin steel weight, rubber feet,
chrome screws; props: glass cup, tea, paper tea bag.
Screws: ONE type, M3 countersunk (2 x M3 x 8 back, 2 x M3 x 6 motor,
4 x M3 x 10 under the foot) + 6 M3 heat-set inserts.
Honest limits: the NEMA 17 wants a 12-24 V motor supply on the driver
(./check's WIRING note); at USB-C 5 V it holds a tea bag but the user
must be asked what supply they have. The cup, the tea and the bag are
props.
MEASURED (R1030, 2026-11-20): ./check CHECK PASS, run_seconds 14 s, wall 47 s; every RESTYLE end CHECK PASS.
"""
import math
import time
import Part
import atech_ports as ap
import atech_cad as cad
import atech_modules as am
from FreeCAD import Vector, Placement, Rotation
V = Vector
T0 = time.time()

INTENT = {"board": "upright", "fitted_after": [
    "Shell", "Arm", "Hook", "Hub_Cap", "Bezel", "Lens", "Glow_Lens", "Grille", "Vent", "Dial_Ring", "Dial_Cap",
    "Screw_1", "Screw_2", "Screw_3", "Screw_4", "Screw_5", "Screw_6", "Screw_7", "Screw_8"],
    # the frosted leaf carries the ready light, the dial cap sits on the knob
    "covers": {"Glow_Lens": "light_p3"},
    # the arm turns on the stepper's shaft: up (as built, +30 deg) to 30 deg down
    "motion": [{"part": "Arm", "axis": [[38.826, 0, 144.075], [0, 1, 0]], "range_deg": [0, 60]}]}
# the hook rides in the arm; the props: the mug stands in the cork, the
# tea fills it, the bag hangs on the hook (and goes down with the arm)
INTENDED_OVERLAPS = [("Arm", "Hook"), ("Glass_Cup", "Coaster"), ("Glass_Cup", "Tea"), ("Tea_Bag", "Hook"), ("Arm", "Tea_Bag")]
REVIEW_CLOSEUPS = ["Arm", "Dial_Cap", "Lens"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them and the measured hardware.
ARM_L = 95.0       # RESTYLE 80..110 length: the arm, shaft to hook (the cup and the foot follow it)
FOOT_H = 9.0       # RESTYLE 7.5..10.5 height: the weighted foot under the tower and the cup
CORNER = 14.0      # RESTYLE 11.5..16.5 radius: the tower's back corners (plan)
TOP_R = 8.0        # RESTYLE 6.5..9.5 radius: the tower's rolled top edge
WALL = 2.5         # RESTYLE 2.1..2.9 wall
# end RESTYLE
# Frame: x across (the cup on the right, +X), y from the face (-Y) to the
# back, z up; the desk at z = 0. The board, the modules and the motor are
# the hardware's own: never move them with a knob.
RUB = 1.5                      # rubber feet under the foot
SEAT = 7.0                     # the foot under the tower (the tower sits in a socket FOOT_H - SEAT deep)
FLOOR_T = 5.0                  # the tower's floor (an M3 insert from below leaves 1 mm)
RF = TOP_R                     # the tower's front corners (plan) = the top's roll: round corners
WIN, BZW = (16.0, 28.0), 4.0   # the screen window (active area 13.5 x 25.6), its bezel
ARM_ANG = 30.0                 # the arm as built: 30 deg up (the bag lifted out); it turns 60 deg down
ARM_T = 7.0                    # the arm's thickness (y)
HUB_R = 11.0                   # the arm's hub
SPIGOT_R = 4.0                 # the hub's spigot in the bearing sleeve (bore 0.1 mm clear): the pin
GAP = 0.6                      # hub to face
PLATE_T = 2.4                  # the motor bulkhead
CUP = (40.0, 85.0)             # the cup the arm serves: radius, height (MEASURED mug: 80 x 85)
COASTER_R = 44.0               # the cork coaster under the cup
SCREW = "M3"                   # ONE screw type: M3 countersunk (+ M3 heat-set inserts)
INSERT_D = 4.3
COLOURS = {"Shell": "#F3F0EA", "Back": "#8FB5A0", "Foot": "#8FB5A0", "Arm": "#8FB5A0", "Hook": "brass",
           "Bezel": "#8FB5A0", "Lens": "smoked", "Glow_Lens": "#F6C76B", "Grille": "#C9A27A",
           "Dial_Ring": "frosted", "Dial_Cap": "#B8875A", "Coaster": "#B8875A", "Weight": "satin_grey",
           "Rubber": "rubber", "Screw": "chrome", "Glass_Cup": "glass", "Tea": "#7A3E16", "Tea_Bag": "#E9DDBF"}


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
ZT0 = RUB + SEAT                                 # the tower's bottom, in the foot's socket
ZFT = RUB + FOOT_H                               # the foot's top (the coaster)
ZF = ZT0 + FLOOR_T                               # the tower's floor (inner face)
ZB = ZF + 1.6                                    # the board's bottom edge (clear of the split lip on the floor)
UPRIGHT_FRONT = Rotation(Vector(0, 0, 1), 180)   # portrait, modules face -Y, 1-6 on the right
board = ap.board_object(doc)
board.Placement = Placement(Vector(), UPRIGHT_FRONT)
_b = ap.bbox(board)
board.Placement = Placement(Vector(-_b.XMin, -_b.YMin, ZB - _b.ZMin), UPRIGHT_FRONT)   # x 0..60, y 0..7
BB = ap.bbox(board)
spk = ap.seat(doc, "speaker", (9, 10))           # bottom left, hangs 20 mm out to the left: the chime
knob = ap.seat(doc, "knob", (13, 14))            # top left, hangs out to the left: the minutes dial
scr = ap.seat(doc, "screen", (4, 5))             # right, portrait: the countdown and the tea
glow = ap.seat(doc, "light", 3)                  # right, under the screen: glows when it is ready
drv = ap.seat(doc, "stepper_motor", (1, 2))      # bottom right: the TMC2209 driving the arm's motor
SPB, KB, SB, LB, DB = [ap.bbox(m) for m in (spk, knob, scr, glow, drv)]
# the arm's motor: a NEMA 17 behind the board's top, shaft forward (-Y)
# over the board's top edge, its face on a bulkhead behind the board
PLATE_Y0 = BB.YMax + 1.6                         # the bulkhead's front (clear of the split lip)
PLATE_Y1 = PLATE_Y0 + PLATE_T                    # the motor's face
MOT_X = BB.XMax - 21.15                          # the motor flush with the board's right edge
MOT_Z = BB.ZMax + 9.0                            # the shaft over the board's top edge
motor, _rep = am.load_module(doc, "nema17_stepper", placement=Placement(V(MOT_X, PLATE_Y1, MOT_Z),
                                                                          Rotation(V(0, 0, 1), 180)))
MB = motor.Mesh.BoundBox
_sp = [p for p in motor.Mesh.Points if p.y < MB.YMin + 3.0]
SX = (min(p.x for p in _sp) + max(p.x for p in _sp)) / 2.0 - 0.25   # (the D-flat trims the -X side by 0.5)
SZ = (min(p.z for p in _sp) + max(p.z for p in _sp)) / 2.0
SHAFT_TIP = MB.YMin
print("SHAFT at x %.2f z %.2f, tip y %.2f; motor y %.1f..%.1f" % (SX, SZ, SHAFT_TIP, MB.YMin, MB.YMax))
# the tower, measured from the hardware
_ri = RF - WALL                                  # the front corners' inner radius: the speaker's corner must clear it
_dy = 0.8                                        # (the speaker 0.8 mm behind the face's inner side)
_dx = max(3.0, _ri - math.sqrt(max((_ri - 0.6) ** 2 - (_ri - _dy) ** 2, 0.0)) + 0.3) if _ri > _dy else 3.0
XL = min(SPB.XMin, KB.XMin) - _dx - WALL         # left face
XR = max(max(BB.XMax, MB.XMax, SB.XMax, DB.XMax) + 3.8 + WALL,   # right face: the face flat past the bezel
         (SB.XMin + SB.XMax) / 2 + WIN[0] / 2 + BZW + 1.0 + RF)
YF = SPB.YMin - 0.8 - WALL                       # the face: 0.8 mm air in front of the speaker
Y_IN = YF + WALL
ri = CORNER - WALL                               # the back corners' inner radius: the motor's corner must clear it
dx = (XR - WALL) - MB.XMax
need = 3.0
if ri - dx > 0:
    need = max(need, ri - math.sqrt(max((ri - 1.0) ** 2 - (ri - dx) ** 2, 0.0)))
YBK = MB.YMax + need + WALL                      # the back
ZTOP = MB.ZMax + 1.5 + WALL                      # the top
SPLIT_Y = BB.YMax - 2.2                          # Shell / Back: just behind the modules' slide paths (PCB face 4.5)
usb, usb_rib = ap.cable(doc, "usbc", 11, ap.module_placement(
    "usbc", (BB.XMin - 8.0, YBK - 1.25 - 9.875, ZB + 50.0), face="+X", cable="-Y"))
UB = ap.bbox(usb)
print("TOWER x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (XL, XR, YF, YBK, ZT0, ZTOP))
# the cup: the hook over its centre at both ends of the swing
PIVOT = V(SX, YF - GAP - ARM_T / 2, SZ)
HOOK_X = SX + ARM_L * math.cos(math.radians(ARM_ANG))
CX = max(HOOK_X, XR + COASTER_R + 4.5)            # (a short arm: the coaster and its groove stay clear of the tower, the hook inside the rim)
CY = PIVOT.y
tick("hardware")


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, h, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def ycyl(r, x, z, y0, y1):
    (y0, y1) = sorted((y0, y1))
    return Part.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0))


def yprism(x0, x1, z0, z1, r, y0, y1):
    """A rounded rectangle in (x, z) extruded along Y from y0 to y1."""
    (y0, y1) = sorted((y0, y1))
    w = cad.rounded_rect_wire(x1 - x0, z1 - z0, r, ((x0 + x1) / 2, y0, (z0 + z1) / 2), "Y")
    s = Part.Face(w).extrude(V(0, y1 - y0, 0))
    if s.Volume < 0:
        s.reverse()
    return s


def yrect(cx, cz, w, h, r, y0, y1):
    return yprism(cx - w / 2, cx + w / 2, cz - h / 2, cz + h / 2, r, y0, y1)


def ring_y(c, r0, r1, y0, y1):
    (y0, y1) = sorted((y0, y1))
    return cad.cut(ycyl(r1, c[0], c[1], y0, y1), ycyl(r0, c[0], c[1], y0 - 1, y1 + 1))


def centre(b):
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


def insert(shell, cutter):
    """(shell with the opening, the piece that fills it exactly)."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1:
        piece, rest = shell.common(cutter, 0.01), shell.cut(cutter, 0.01)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, piece


def plan_wire(t, z):
    """The tower's plan moved t in: flat face, small front corners RF, big
    back corners CORNER (arcs)."""
    x0, x1, y0, y1 = XL + t, XR - t, YF + t, YBK - t
    rf, rb = max(RF - t, 0.6), max(CORNER - t, 0.6)
    s = math.sqrt(0.5)

    def arc(cx, cy, r, a0):
        a1, am_ = math.radians(a0 + 90), math.radians(a0 + 45)
        a0 = math.radians(a0)
        return Part.Arc(V(cx + r * math.cos(a0), cy + r * math.sin(a0), z), V(cx + r * math.cos(am_), cy + r * math.sin(am_), z),
                        V(cx + r * math.cos(a1), cy + r * math.sin(a1), z)).toShape()
    e = [Part.makeLine(V(x0 + rf, y0, z), V(x1 - rf, y0, z)), arc(x1 - rf, y0 + rf, rf, -90),
         Part.makeLine(V(x1, y0 + rf, z), V(x1, y1 - rb, z)), arc(x1 - rb, y1 - rb, rb, 0),
         Part.makeLine(V(x1 - rb, y1, z), V(x0 + rb, y1, z)), arc(x0 + rb, y1 - rb, rb, 90),
         Part.makeLine(V(x0, y1 - rb, z), V(x0, y0 + rf, z)), arc(x0 + rf, y0 + rf, rf, 180)]
    del s
    return Part.Wire(e)


def slab(t, z0, z1):
    s = Part.Face(plan_wire(t, z0)).extrude(V(0, 0, z1 - z0))
    if s.Volume < 0:
        s.reverse()
    return s


# ------------------------------------------------------------ the tower
outer = slab(0.0, ZT0, ZTOP)
outer = cad.fillet_safe(outer, TOP_R, edges=[e for e in outer.Edges if e.BoundBox.ZMin > ZTOP - 0.01])
core = slab(WALL, ZF, ZTOP - WALL)
# (its top edges chamfered: a round inside corner reads as an open clip channel, R19)
# (the chamfer stays under the inner front corners' radius: equal to it, OCCT gives up)
_v0 = core.Volume
for _c in (TOP_R - WALL - 0.6, TOP_R - WALL - 1.2, TOP_R - WALL - 1.8):
    _ch = cad.chamfer_safe(core, _c, [e for e in core.Edges if e.BoundBox.ZMin > ZTOP - WALL - 0.01])
    if _ch.Volume < _v0 - 1.0:
        break
core = _ch
tower = cad.cut(outer, core)
skin = slab(0.5, ZT0 + 0.5, ZTOP - 0.5)
tick("tower")
shell, back = cad.split(tower, "Y", at=SPLIT_Y, lip=1.2)
tick("split")

# ------------------------------------------------------------ the Back holds the board and the motor
# a bulkhead across the tower behind the board: the motor's face on its
# back (pilot boss in a 22.5 bore, two M3 into the flange's top holes),
# a window for the USB-C ribbon, a pass for the motor's wires; pads from it
# 0.1 mm behind the board and the overhangs, fences 0.3 mm off the board's
# edges (behind every module's slide path: those end at the PCB's face)
UR = usb_rib[0].Shape.BoundBox
YK = PLATE_Y0
bulk = box(XL, XR, YK, PLATE_Y1, ZT0, ZTOP).common(core)
bulk = cad.cut(bulk, [box(XL, UR.XMax + 2.0, YK - 1, PLATE_Y1 + 1, UR.ZMin - 2.0, UR.ZMax + 2.0),        # the ribbon
                      yrect((DB.XMin + DB.XMax) / 2, DB.ZMin + 8.0, 14.0, 6.0, 2.0, YK - 1, PLATE_Y1 + 1),  # motor wires
                      ycyl(11.25, SX, SZ, YK - 1, PLATE_Y1 + 1)])                                       # pilot boss
YP = BB.YMax + 0.1
pads = [box(x, x + 6, YP, YK + 0.5, BB.ZMin + z, BB.ZMin + z + 6) for x in (8, 46) for z in (8, 102)]
pads += [box(m.XMin + 5, m.XMin + 13, m.YMax + 0.3, YK + 0.5, (m.ZMin + m.ZMax) / 2 - 5, (m.ZMin + m.ZMax) / 2 + 5)
         for m in (SPB, KB)]
YQ = SPLIT_Y + 0.1
fences = [box(BB.XMin - 1.8, BB.XMin - 0.3, YQ, YK + 0.5, BB.ZMin + z, BB.ZMin + z + 14) for z in (20, 92)]
fences += [box(BB.XMax + 0.3, BB.XMax + 1.8, YQ, YK + 0.5, BB.ZMin + z, BB.ZMin + z + 14) for z in (20, 92)]
fences += [box(BB.XMin + 22, BB.XMax - 22, YQ, YK + 0.5, BB.ZMax + 0.3, BB.ZMax + 2.3)]
stands = [box(x, x + 6, SPLIT_Y + 1.4, YK + 0.5, ZF - 0.5, BB.ZMin - 0.1) for x in (6, 48)]   # behind the floor's lip
# the motor's cradle: a shelf from the back wall under its body
cradle = box(MB.XMin + 4.0, MB.XMax - 4.0, PLATE_Y1 + 0.5, YBK - WALL + 0.5, MB.ZMin - 2.5, MB.ZMin - 0.3)
# the USB-C module: a rib either side (0.3 mm off; the ribbon comes in at its front)
YI = YBK - WALL + 0.5
usb_ribs = [box(UB.XMin - 1.9, UB.XMin - 0.3, UB.YMin + 3.0, YI, UB.ZMin + 2.0, UB.ZMax - 2.0),
            box(UB.XMax + 0.3, UB.XMax + 1.9, UB.YMin + 3.0, YI, UB.ZMin + 2.0, UB.ZMax - 2.0)]
back = cad.fuse_one(back, bulk, cradle, *[p.common(skin) for p in pads + fences + stands + usb_ribs])
# the plug opening: the mouth MEASURED from the module's mesh (its last
# 0.6 mm along +Y) plus 1.5 mm a side, in a bay 1.25 mm deep
MOUTH_Y = UB.YMax
MP = [p for p in usb.Mesh.Points if p.y > UB.YMax - 0.6]
MX0, MX1 = min(p.x for p in MP), max(p.x for p in MP)
MZ0, MZ1 = min(p.z for p in MP), max(p.z for p in MP)
bay = box(UB.XMin - 0.3, UB.XMax + 0.3, UB.YMin + 3.0, MOUTH_Y + 0.25, UB.ZMin - 0.3, UB.ZMax + 0.3)
plug = Part.Face(cad.rounded_rect_wire(MX1 - MX0 + 3.0, MZ1 - MZ0 + 3.0, 2.0,
                                       ((MX0 + MX1) / 2, MOUTH_Y + 0.05, (MZ0 + MZ1) / 2), "Y"))
back = cad.cut(back, [bay, plug.extrude(V(0, YBK - MOUTH_Y + 2.0, 0))])
tick("back")

# ------------------------------------------------------------ the Shell: bearing, rib
# the bearing sleeve for the arm's spigot on the face's inner side, a
# raised ring outside it; a rib from the face onto the board's spine
SLEEVE_Y1 = SHAFT_TIP + 1.5
shell = cad.fuse_one(shell, ycyl(7.5, SX, SZ, Y_IN - 0.5, SLEEVE_Y1),
                     box(25, 35, Y_IN - 0.5, BB.YMin - 0.2, BB.ZMin + 50, BB.ZMin + 62))
shell = cad.cut(shell, ycyl(SPIGOT_R + 0.1, SX, SZ, YF - 2, SLEEVE_Y1 + 1))
tick("shell")

# ------------------------------------------------------------ fasteners (ONE type: M3 countersunk)
# two from the back into insert sleeves on long columns of the Shell (on
# the left, clear of the overhangs and the USB-C), four from under the
# foot into inserts in the tower's floor
screws = []
BACK_SCREWS = [(XL + CORNER + 2.0, (UB.ZMax + KB.ZMin) / 2 + 3.0), (XL + CORNER + 2.0, (KB.ZMax + ZTOP - WALL) / 2)]
for x, z in BACK_SCREWS:
    back, shell = cad.screw_through(back, shell, (x, YBK, z), size=SCREW, ribs=0)
    yb = YBK - WALL - 0.1
    shell = cad.fuse_one(shell, cyl(INSERT_D / 2 + 1.2, (x, yb, z), 10.0, (0, -1, 0)))
    shell = cad.cut(shell, cyl(INSERT_D / 2, (x, yb + 0.5, z), 6.0, (0, -1, 0)))
    screws.append(cad.screw("csk_phillips", SCREW, 8, at=(x, YBK, z), axis="-Y"))
    back = cad.cut(back, ycyl(INSERT_D / 2 + 1.6, x, z, YK - 1, PLATE_Y1 + 1))   # through the bulkhead
FLOOR_SCREWS = [(XL + WALL + 7.0, Y_IN + 7.0), (XR - WALL - 7.0, Y_IN + 7.0),
                (XL + CORNER + 2.0, YBK - WALL - 7.0), (XR - CORNER - 2.0, YBK - WALL - 7.0)]
WT = 3.0                       # the steel weight plate under the tower (the floor screws clamp it)
FLOOR_L = 2 * int((SEAT + 3.5) / 2)
# the motor: two M3 through the bulkhead into its flange's top holes (the
# lower pair sits behind the board), heads countersunk in the bulkhead
for dx_ in (-15.5, 15.5):
    back = cad.countersink(back, (SX + dx_, PLATE_Y0, SZ + 15.5), "+Y", 3.4, 6.5, 90.0, through="wall")
    screws.append(cad.screw("csk_phillips", SCREW, 6, at=(SX + dx_, PLATE_Y0, SZ + 15.5), axis="+Y"))
tick("screws")

# ------------------------------------------------------------ the face: chime grille, driver vents
spx, _spy, spz = centre(SPB)
shell, grille = insert(shell, ycyl(18.0, spx, spz, YF - 1, Y_IN + 1))
grille = cad.fuse_one(grille, ycyl(18.0, spx, spz, YF - 0.8, YF + 0.5))
grille = cad.speaker_grille(grille, (spx, YF - 0.8, spz), (0, -1, 0), 32.0, ring_pitch=2.6, hole=1.5)
dvx, _dvy, dvz = centre(DB)
# the driver runs warm: a round vent insert in front of it (the chime's twin)
VENT_R = min(13.0, XR - RF - dvx - 1.0)
shell, vent = insert(shell, ycyl(VENT_R, dvx, dvz, YF - 1, Y_IN + 1))
vent = cad.fuse_one(vent, ycyl(VENT_R, dvx, dvz, YF - 0.8, YF + 0.5))
vent = cad.speaker_grille(vent, (dvx, YF - 0.8, dvz), (0, -1, 0), 2 * VENT_R - 3.0, ring_pitch=3.0, hole=1.8)
# ------------------------------------------------------------ the face: screen
sx, _sy, sz = centre(SB)
shell, bezel = insert(shell, yrect(sx, sz, WIN[0] + 2 * BZW, WIN[1] + 2 * BZW, 4.0, YF - 1, Y_IN + 1))
bezel = cad.fuse_one(bezel, yrect(sx, sz, WIN[0] + 2 * BZW, WIN[1] + 2 * BZW, 4.0, YF - 1.2, YF + 0.5))
bezel, lens = insert(bezel, yrect(sx, sz, WIN[0], WIN[1], 2.0, YF - 3, Y_IN + 1))
lens = cad.cut(lens, box(sx - 20, sx + 20, YF - 3, YF - 0.6, sz - 30, sz + 30))     # set 0.6 mm back in the bezel
lens = cad.fuse_one(lens, yrect(sx, sz, WIN[0] - 1.0, WIN[1] - 1.0, 1.5, Y_IN - 0.5, SB.YMin - 0.4))
# ------------------------------------------------------------ the face: ready light
lx, _ly, lz = centre(LB)


def leaf(z0, z1, s=1.0):
    """A tea leaf (point up), straight facets only, along Y."""
    pts = []
    for i in range(17):
        a = math.radians(-90 + 180 * i / 16.0)
        pts.append((lx + s * 6.5 * math.cos(a), lz + s * 9.0 * math.sin(a) - s * 1.5 * math.cos(a) ** 2))
    pts += [(lx - s * 6.5 * math.cos(math.radians(-90 + 180 * i / 16.0)),
             lz + s * 9.0 * math.sin(math.radians(-90 + 180 * i / 16.0)) - s * 1.5 * math.cos(math.radians(-90 + 180 * i / 16.0)) ** 2)
            for i in range(15, 0, -1)]
    pp = [V(x, z0, z) for x, z in pts]
    return Part.Face(Part.makePolygon(pp + [pp[0]])).extrude(V(0, z1 - z0, 0))


shell, glow_lens = insert(shell, leaf(YF - 1, Y_IN + 1))
glow_lens = cad.fuse_one(glow_lens, leaf(YF - 0.8, YF + 0.5), leaf(Y_IN - 0.5, LB.YMin - 0.5, 0.8))
tick("screen + light")
# ------------------------------------------------------------ the face: the dial (tiny_tv.py)
CAP_R, DISH_R, RIM_R, FOOT_R = 11.0, 17.5, 20.5, 22.5
RING_R = (8.05, 13.5)
kx, _ky, kz = centre(KB)
K_PLATE = KB.YMax - 10.1
CAP_TOP = KB.YMin - 2.0
Y_RIM = CAP_TOP - 0.4
crown = Part.makeCone(FOOT_R, RIM_R, (YF + 1.0) - Y_RIM, V(kx, YF + 1.0, kz), V(0, -1, 0))
shell = cad.cut(cad.fuse_one(shell, crown), cyl(DISH_R, (kx, YF - 0.01, kz), 60, (0, -1, 0)))
ring_cut = ring_y((kx, kz), RING_R[0], RING_R[1], YF - 1, Y_IN + 1)
dial_ring = shell.common(ring_cut)
shell = cad.cut(shell, cyl(RING_R[1], (kx, YF - 1, kz), WALL + 2, (0, 1, 0)))
dial_ring = cad.fuse_one(dial_ring, ring_y((kx, kz), RING_R[0], RING_R[1] - 1.0, Y_IN - 0.5, K_PLATE - 0.5))
y_cb = YF - 0.6
dial_cap = cad.fuse_one(cyl(CAP_R, (kx, y_cb, kz), y_cb - CAP_TOP, (0, -1, 0)),
                        ring_y((kx, kz), 6.45, RING_R[0] - 0.2, y_cb - 0.5, YF + 2.0))
dial_cap = cad.fillet_safe(dial_cap, 1.5, edges=[e for e in dial_cap.Edges if e.BoundBox.YMax < CAP_TOP + 0.01])
dial_cap = cad.cut(dial_cap, cyl(6.45, (kx, YF + 3.0, kz), (YF + 3.0) - (KB.YMin - 0.4), (0, -1, 0)))
tick("dial")

# ------------------------------------------------------------ the arm
# ONE part: the hub on the face, a tapered beam 30 deg up to a round tip;
# the spigot (the pin) back through the bearing sleeve, a D-bore 0.05 mm
# round the motor's 5 mm shaft (its flat faces -X as the mesh is built)
u = V(math.cos(math.radians(ARM_ANG)), 0, math.sin(math.radians(ARM_ANG)))
w = V(-u.z, 0, u.x)
AY0, AY1 = YF - GAP - ARM_T, YF - GAP
TIP_R = 6.0
P = V(SX, AY0, SZ)
T = P + u * ARM_L
pts = [P + w * 7.5, T + w * (TIP_R - 0.5), T - w * (TIP_R - 0.5), P - w * 7.5]
beam = Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, ARM_T, 0))
arm = cad.fuse_one(ycyl(HUB_R, SX, SZ, AY0, AY1), beam, ycyl(TIP_R, T.x, T.z, AY0, AY1))
arm = cad.soften(arm, 2.0, [e for e in arm.Edges if e.BoundBox.YMin < AY0 + 0.01 or e.BoundBox.YMax > AY1 - 0.01])
arm = cad.fuse_one(arm, ycyl(SPIGOT_R, SX, SZ, AY1 - 0.5, SHAFT_TIP + 9.0))
dbore = cad.cut(ycyl(2.55, SX, SZ, SHAFT_TIP - 0.5, SHAFT_TIP + 10.0),
                box(SX - 3, SX - 2.05, SHAFT_TIP - 1, SHAFT_TIP + 11, SZ - 3, SZ + 3))
arm = cad.cut(arm, dbore)
# the hook: a brass pin in a bore up into the tip (pushed in), hanging down
# and curling into a J that opens away from the tower
HOOK_R = 1.5
hb = T + V(0, ARM_T / 2, 0)
arm = cad.cut(arm, cyl(HOOK_R + 0.1, (hb.x, hb.y, hb.z - TIP_R - 1), TIP_R + 1 + 2.0))
hook = cyl(HOOK_R, (hb.x, hb.y, hb.z - TIP_R - 14.0), TIP_R + 14.0 + 1.8)
j0 = V(hb.x, hb.y, hb.z - TIP_R - 14.0)
jp = [(j0.x, j0.y, j0.z + 0.5), (j0.x, j0.y, j0.z - 3.0), (j0.x + 2.5, j0.y, j0.z - 6.0),
      (j0.x + 6.0, j0.y, j0.z - 5.0), (j0.x + 7.5, j0.y, j0.z - 1.5)]
hook = cad.fuse_one(hook, cad.pipe(jp, r=HOOK_R - 0.05))
tick("arm")

# ------------------------------------------------------------ the foot
# one plan: the tower's footprint grown 6 mm and the coaster's circle,
# joined by their hull (straight facets); a rolled top edge
_pts = []
for t_ in range(0, 360, 6):
    a = math.radians(t_)
    _pts.append((CX + (COASTER_R + 5.0) * math.cos(a), CY + (COASTER_R + 5.0) * math.sin(a)))
for cx_, cy_, r_ in ((XL + 6.0, YF + 6.0, 12.0), (XR - 6.0, YF + 6.0, 12.0),
                     (XR - CORNER, YBK - CORNER, CORNER + 6.0), (XL + CORNER, YBK - CORNER, CORNER + 6.0)):
    for t_ in range(0, 360, 10):
        a = math.radians(t_)
        _pts.append((cx_ + r_ * math.cos(a), cy_ + r_ * math.sin(a)))


def hull(points):
    pts_ = sorted(set((round(x, 4), round(y, 4)) for x, y in points))
    lo, hi = [], []
    for p_ in pts_:
        while len(lo) >= 2 and (lo[-1][0] - lo[-2][0]) * (p_[1] - lo[-2][1]) - (lo[-1][1] - lo[-2][1]) * (p_[0] - lo[-2][0]) <= 0:
            lo.pop()
        lo.append(p_)
    for p_ in reversed(pts_):
        while len(hi) >= 2 and (hi[-1][0] - hi[-2][0]) * (p_[1] - hi[-2][1]) - (hi[-1][1] - hi[-2][1]) * (p_[0] - hi[-2][0]) <= 0:
            hi.pop()
        hi.append(p_)
    return lo[:-1] + hi[:-1]


FOOT_PLAN = hull(_pts)
fp = [V(x, y, RUB) for x, y in FOOT_PLAN]
foot = Part.Face(Part.makePolygon(fp + [fp[0]])).extrude(V(0, 0, FOOT_H))
foot = cad.soften(foot, min(3.0, FOOT_H / 3), [e for e in foot.Edges if e.BoundBox.ZMin > ZFT - 0.01])
# the socket the tower sits in (0.2 mm round it)
foot = cad.cut(foot, slab(-0.2, ZT0, ZFT + 1.0))
# the cork coaster inlaid 2 mm, 0.5 mm proud; four M3 up into the tower
foot = cad.cut(foot, cyl(COASTER_R, (CX, CY, ZFT - 2.0), 3.0))
coaster = cyl(COASTER_R - 0.2, (CX, CY, ZFT - 2.0), 2.5)
# the steel weight: a plate in a pocket under the tower; the four floor
# screws go up through it and the foot into inserts in the tower's floor
foot = cad.cut(foot, slab(5.0, RUB - 1.0, RUB + WT))
weight = slab(5.2, RUB, RUB + WT)
for x, y in FLOOR_SCREWS:
    weight = cad.countersink(weight, (x, y, RUB), "+Z", 3.4, 6.5, 90.0)
    foot = cad.cut(foot, cyl(1.7, (x, y, RUB + WT - 0.5), ZT0 - RUB - WT + 1.0))
    tgt = shell if y < SPLIT_Y else back
    tgt = cad.cut(tgt, cyl(INSERT_D / 2, (x, y, ZT0 - 0.5), 4.5))
    if y < SPLIT_Y:
        shell = tgt
    else:
        back = tgt
    screws.append(cad.screw("csk_phillips", SCREW, FLOOR_L, at=(x, y, RUB), axis="+Z"))
# rubber feet in shallow recesses: one at each tower corner (outside the
# weight) and three round the cup's end
FEET = [(XL + 0.5, YF + 0.5), (XR - 0.5, YF + 0.5)]
FEET += [(cx_ + s_ * (CORNER + 1.5) / math.sqrt(2), YBK - CORNER + (CORNER + 1.5) / math.sqrt(2))
         for cx_, s_ in ((XR - CORNER, 1), (XL + CORNER, -1))]
FEET += [(CX + (COASTER_R - 2.0) * math.cos(math.radians(a)), CY + (COASTER_R - 2.0) * math.sin(math.radians(a)))
         for a in (-70, 0, 70)]
foot = cad.cut(foot, [cyl(3.6, (x, y, RUB - 1.0), 2.5) for x, y in FEET])
rubbers = [cad.foot(7.0, RUB + 1.5, style="dome", at=(x, y, RUB + 1.5)) for x, y in FEET]
tick("stage A")


# === STAGE B: details ===
# (a fork may stop after STAGE A, run ./check, then add these one by one)
# twelve minute ticks on the dial's crown rim, the four quarter ticks wider
ticks = []
for i in range(12):
    tw = 1.6 if i % 3 == 0 else 0.8
    t_ = box(-tw / 2, tw / 2, Y_RIM - 1.0, Y_RIM + 0.5, DISH_R + 0.6, RIM_R - 0.5)
    t_.rotate(V(0, 0, 0), V(0, 1, 0), 30 * i)
    t_.translate(V(kx, 0, kz))
    ticks.append(t_)
shell = cad.cut(shell, ticks, optional=True)
# the cork cap: a straight knurl round its side, a pointer groove on its face
dial_cap = cad.knurl(dial_cap, "-Y", (kx, y_cb, kz), CAP_R, 1.0, y_cb - CAP_TOP - 2.4, n=36, depth=0.35)
dial_cap = cad.cut(dial_cap, box(kx - 0.6, kx + 0.6, CAP_TOP - 1, CAP_TOP + 0.6, kz + 3.0, kz + CAP_R - 1.6))
# lettering: STEEP over the dial, MIN under it, ATECH low between the grilles
shell = cad.text(shell, "STEEP", (kx, YF, (KB.ZMax + ZTOP - TOP_R) / 2 + 1.0), (0, -1, 0), 4.5, depth=0.5, mode="deboss")
shell = cad.text(shell, "ATECH", ((spx + dvx) / 2 + 2.0, YF, ZT0 + 2.0 + (ZB - ZT0) + 6.0), (0, -1, 0), 4.0, depth=0.5,
                 mode="deboss")
# a vein down the leaf
glow_lens = cad.cut(glow_lens, box(lx - 0.35, lx + 0.35, YF - 1.0, YF - 0.4, lz - 6.0, lz + 6.5), optional=True)
# the arm: a brass cap on the hub (a pin in a bore in the hub's face)
arm = cad.cut(arm, ycyl(2.1, SX, SZ, AY0 - 1, AY0 + 3.0))
hub_cap = cad.fuse_one(ycyl(6.5, SX, SZ, AY0 - 1.2, AY0 - 0.2), ycyl(2.0, SX, SZ, AY0 - 0.5, AY0 + 2.8))
hub_cap = cad.soften(hub_cap, 0.5, [e for e in hub_cap.Edges if e.BoundBox.YMin < AY0 - 1.19])
# the hook's ball tip
hook = cad.fuse_one(hook, Part.makeSphere(HOOK_R + 0.4, V(*jp[-1])))
# the foot: a drip groove round the coaster
foot = cad.cut(foot, cad.cut(cyl(COASTER_R + 3.0, (CX, CY, ZFT - 0.8), 2.0), cyl(COASTER_R + 1.8, (CX, CY, ZFT - 1.0), 3.0)))
# the back: vent slots over the motor, a model mark
back = cad.grille(back, ((XL + XR) / 2, YBK, MB.ZMin + 21.0), (0, 1, 0), (40.0, 22.0), kind="slot", hole=2.5, pitch=5.5,
                  margin=1.0)
back = cad.text(back, "ATECH TS-1", ((XL + XR) / 2, YBK, (UB.ZMin + UB.ZMax) / 2 + 26.0), (0, 1, 0), 4.0, depth=0.4,
                mode="deboss", up=(0, 0, 1))
tick("details")

# ------------------------------------------------------------ the cup and the bag (props, not printed)
# a double-wall glass tea cup (the 80 x 85 mug the arm is sized for), standing on the coaster (sunk 0.3 mm into
# the cork), tea in it, the tea bag on the hook - lifted out
MZ0 = ZFT + 0.2
mug = cad.revolve_profile([(0, MZ0), (CUP[0] - 2.0, MZ0), (CUP[0], MZ0 + 2.0), (CUP[0], MZ0 + CUP[1] - 1.0),
                           (CUP[0] - 1.0, MZ0 + CUP[1]), (CUP[0] - 2.5, MZ0 + CUP[1]), (CUP[0] - 3.5, MZ0 + CUP[1] - 1.0),
                           (CUP[0] - 3.5, MZ0 + 7.0), (0, MZ0 + 7.0)], at=(CX, CY, 0))
hp = [(CX - 0.6 * CUP[0], CY - 0.8 * CUP[0] + 0.8, MZ0 + 0.78 * CUP[1]),
      (CX - 0.75 * CUP[0], CY - 0.8 * CUP[0] - 14.0, MZ0 + 0.72 * CUP[1]),
      (CX - 0.75 * CUP[0], CY - 0.8 * CUP[0] - 16.0, MZ0 + 0.45 * CUP[1]),
      (CX - 0.6 * CUP[0], CY - 0.8 * CUP[0] + 0.8, MZ0 + 0.32 * CUP[1])]
mug = cad.fuse_one(mug, cad.pipe(hp, r=4.5))
tea = cyl(CUP[0] - 3.4, (CX, CY, MZ0 + 7.0), 0.62 * CUP[1])
s0 = V(jp[1][0], jp[1][1], jp[1][2] - 2.0)              # the string over the J's bottom
BAG = (36.0, 5.0, 40.0)
bag_top = s0.z - 6.0                            # lifted out: the bag hangs over the rim
tea_bag = cad.fuse_one(cyl(0.6, (s0.x, s0.y, bag_top - 1.0), s0.z + 1.6 - bag_top),
                       cad.rounded_box(BAG[0], BAG[1], BAG[2], 2.4, at=(s0.x - BAG[0] / 2, s0.y - BAG[1] / 2, bag_top - BAG[2]),
                                       edges="y"))
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape, colour=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    c = COLOURS[colour or name]
    o.ViewObject.ShapeColor = cad.color(c)
    if c in ("smoked", "frosted", "glass"):
        o.ViewObject.Transparency = cad.transparency(c)
    return o


part("Back", back)
part("Shell", shell)
part("Arm", arm)
part("Hook", hook)
part("Foot", foot)
part("Coaster", coaster)
part("Weight", weight)
for i, sh in enumerate(rubbers):
    part("Rubber_%d" % (i + 1), sh, "Rubber")
part("Bezel", bezel)
part("Lens", lens)
o = part("Glow_Lens", glow_lens)
o.ViewObject.Transparency = cad.transparency("frosted")
part("Grille", grille)
part("Vent", vent, "Grille")
part("Hub_Cap", hub_cap, "Hook")
part("Glass_Cup", mug)
part("Tea", tea)
part("Tea_Bag", tea_bag)
part("Dial_Ring", dial_ring)
part("Dial_Cap", dial_cap)
for i, sh in enumerate(screws):
    part("Screw_%d" % (i + 1), sh, "Screw")
print("SIZE %s" % (cad.measure(Part.makeCompound([o.Shape for o in doc.Objects if o.TypeId == "Part::Feature"
                                                   and o.Label[0].isupper()]))["size"],))
print("TOTAL %.1f s" % (time.time() - T0))
