"""Example: "a retro pixel camera" - a chunky two-tone toy camera with a big lens barrel.

fork this file for a camera / camera-faced gadget (a pixel camera, an
instant-camera look-alike, a kids' camera, a webcam body); change PARAMETERS and the outlines.
ARCHETYPE: camera

How it is built:
  * STAGE A - hardware, shell, every working-face opening, fasteners: the
    board LANDSCAPE upright behind the front face (modules facing the
    subject, -Y). The CAMERA module seats on the top-centre pair (11, 12),
    so the lens sits on the body's centre line with no ribbon; the flash
    LIGHT seats on port 14 beside it, behind a frosted flash window in a
    light box; USB-C seats on port 7 at the left end (a pocket and liner
    in the left side). The SHUTTER button is CABLED from port 9 up over the
    board's top edge under the top wall (face +Z, its ribbon an S in the
    plane of its flat side - no twist), held by its key cap above and two
    pads below; the SCREEN is CABLED from the bottom pair (4, 5) round the
    board's bottom edge (smooth waypoints) to face the back (+Y) behind a
    smoked window, held by ribs at its ends. The body is ONE front
    silhouette (a rounded rectangle) x ONE plan (cad.profile_body, rolled
    edges), hollowed with its own core and split near the back into the
    Front (a deep tub, fitted after) and the Back (the fixed tray: ledges
    and pads hold the board, ribs the screen, pads the shutter module);
    four M2.5 screws from the back run into insert bosses in the Front.
    The lens barrel is ONE revolved section whose spigot is the disc the
    front wall gives up (it fills its hole exactly). Its bore is OPEN - no
    glass, nothing between the sensor and the subject: a stepped cone from
    the camera's lens (MEASURED: barrel r 3.55 at y -13.5, tip y -14.35,
    centred on the module) whose every step stays outside an 80 deg view
    cone from the tip (the build raises if one does not).
  * STAGE B - details: the knurled focus ring and the chrome front trim,
    the flash bezel and its Fresnel ribs, the shutter collar, the rainbow
    stripe under the lens, the soft-touch grip, the strap lugs, the
    viewfinder hump with its windows, the screen bezel, the thumb rest,
    lettering, the parting-line reveal.
RESTYLE (R425): WIDTH, HEIGHT, DEPTH, CORNER and WALL drive every outline
and cutter; the hardware (the board, the shutter over its top edge, the
screen behind it) sets a floor the body never shrinks below (printed as
FLOOR). Extra height goes under the board, extra depth behind it.
DETAILS (visible, 30): 1 chunky rounded body with rolled edges; 2 two-tone
shell (cream front, teal back); 3 big black lens barrel; 4 diamond-knurled
focus ring; 5 groove rings on the barrel; 6 chrome front trim ring; 7
stepped open bore to the sensor (no glass); 8 frosted flash window; 9
chrome flash bezel; 10 Fresnel ribs on the flash; 11 light box behind it;
12 red shutter key with a plunger; 13 chrome shutter collar; 14 black
viewfinder hump pinned on top; 15 its front window; 16 its eyepiece
window; 17 rainbow stripe (five bars) under the lens; 18 soft-touch grip
with ribs at the shutter end; 19-20 strap lugs with strap holes; 21 USB-C
pocket with liner in the left side; 22 smoked screen window on the back;
23 black screen bezel; 24 thumb-rest ribs; 25 "PIXEL" under the flash; 26
"ATECH" on the back; 27 four countersunk screws into insert bosses; 28
parting-line reveal; 29 rib onto the board's spine; 30 lip keying the
Front into the Back.
Materials: cream front, teal back, matte-black barrel, hump and bezel,
brushed-aluminium trim, collar and flash bezel, frosted flash, smoked
windows, signal-red shutter, rainbow bars, soft-touch grip, chrome screws.
MEASURED (2026-11-10): ./check CHECK PASS, model run 10.1 s (wall 25.9 s);
every RESTYLE knob at its min and at its max: CHECK PASS.
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
    "Front", "Lens_Barrel", "Lens_Trim", "Flash_Lens", "Flash_Bezel", "Shutter_Cap", "Shutter_Collar",
    "Viewfinder_Hump", "Finder_Window", "Eyepiece_Window", "Grip_Pad", "Stripe_Red", "Stripe_Orange",
    "Stripe_Yellow", "Stripe_Green", "Stripe_Blue", "Screw_1", "Screw_2", "Screw_3", "Screw_4"],
    # the key cap presses the shutter button through its opening (a declared cover)
    "covers": {"Shutter_Cap": "button_9"}}
REVIEW_CLOSEUPS = ["Lens_Barrel", "Shutter_Cap", "Flash_Lens"]


def tick(what, t=[time.time()]):
    print("TIME %-22s %5.1f s" % (what, time.time() - t[0]))
    t[0] = time.time()


# === PARAMETERS (restyle here) ===
# RESTYLE (R425) - the knobs a restyle turns. Every outline and every
# cutter in the stages is derived from them. The board and its modules set
# a floor under WIDTH, HEIGHT and DEPTH (printed as FLOOR).
WIDTH = 146.0      # RESTYLE 124..168 width: across the body (x)
HEIGHT = 92.0      # RESTYLE 78..106 height: desk to the top face, without the hump (z)
DEPTH = 37.0       # RESTYLE 31..43 length: front face to back face, without the lens (y)
CORNER = 10.0      # RESTYLE 8.5..11.5 radius: the body's corners in the front view
WALL = 2.4         # RESTYLE 2.0..2.8 wall
# end RESTYLE
# Device frame: x across, z up, the subject in front (-Y), the user behind
# (+Y). The board's frame is fixed: the hardware decides it.
AX = 60.0                      # the centre line: the camera's lens (pair 11 / 12)
CAM_TIP = -14.35               # the camera's lens tip (MEASURED, PCB top at y 0)
FRONT_IN = CAM_TIP - 0.85      # the front wall's inner face, just over the lens tip
EDGE = 2.0 * WALL              # the rolled edge round the front and the back
LENS_R = 22.0                  # the focus ring's radius (the barrel's base is 1 mm more)
LENS_L = 14.0                  # the barrel stands this far proud of the front
FLASH = (20.0, 15.0)           # the flash window (w, h)
CAP_D = 16.0                   # the shutter key
COLOURS = {"Front": "#efe6d2", "Back": "#2f7f86", "Lens_Barrel": "matte_black",
           "Trim": "brushed_alu", "Flash_Lens": "frosted",
           "Shutter_Cap": "signal_red", "Hump": "matte_black", "Window": "smoked",
           "Grip": "soft_touch", "Screw": "chrome"}
STRIPES = ("signal_red", "orange", "toy_yellow", "toy_green", "toy_blue")


# === STAGE A: hardware, shell, every working-face opening, fasteners ===
# ------------------------------------------------------------ the body's size
# worked out from the knobs and the hardware BEFORE anything is placed
BTN_RISE = 11.0                                   # the shutter module's centre over the board's top edge
BTN_HALF = 5.02                                   # half the button module's height (MEASURED 10.04)
TOP_IN_OVER_BOARD = BTN_RISE + BTN_HALF + 1.6     # the top wall's inner face over the board's top edge
ZB = max(12.0, HEIGHT - (60.0 + TOP_IN_OVER_BOARD + WALL))   # the board's bottom edge over the desk
Z0, Z1 = 0.0, ZB + 60.0 + TOP_IN_OVER_BOARD + WALL
Y_F = FRONT_IN - WALL                             # the front face
Y_BI = max(Y_F + DEPTH - WALL, 17.0)              # the back wall's inner face (17: shutter + split + lip)
Y_B = Y_BI + WALL                                 # the back face
W = max(WIDTH, 2 * (120.0 + 3.3 + 3.0 + WALL + 2.5 - AX))
X0, X1 = AX - W / 2, AX + W / 2
R = min(CORNER, (Z1 - Z0) / 2 - 1.0)
SPLIT_Y = Y_BI - 5.0                              # inside the cavity, in the plain wall ahead of the rolled back edge
print("FLOOR body %.1f x %.1f x %.1f (knobs %.1f x %.1f x %.1f)" % (W, Z1 - Z0, Y_B - Y_F, WIDTH, HEIGHT, DEPTH))

# ------------------------------------------------------------ hardware
LANDSCAPE_UP = Rotation(Vector(0, 0, 1), 180).multiply(Rotation(Vector(0, 1, 0), -90))
board = ap.board_object(doc)


def place_board(rot, x0=0.0, y0=None, z0=0.0):
    board.Placement = Placement(Vector(), rot)
    bb = ap.bbox(board)
    board.Placement = Placement(Vector(x0 - bb.XMin, 0 if y0 is None else y0 - bb.YMin,
                                       z0 - bb.ZMin), rot)


place_board(LANDSCAPE_UP, 0, None, ZB)            # x 0..120, z ZB..ZB + 60, modules face -Y
BB = ap.bbox(board)
cam = ap.seat(doc, "camera", (11, 12))            # top centre: the lens on the centre line
flash = ap.seat(doc, "light", 14)                 # top right: the flash beside the lens
usb = ap.seat(doc, "usbc", 7)                     # left end, mouth -X
# the shutter: from port 9 up over the board's top edge, face up (+Z), its
# pins toward the front (-Y): the ribbon makes an S in the plane of its
# flat side (no twist) into the module's underside
BTN_Y = SPLIT_Y - 12.25                           # the module's centre: the key's collar 1.2 mm ahead of the seam
btn, btn_rib = ap.cable(doc, "button", 9, ap.module_placement(
    "button", (10.0, BTN_Y, BB.ZMax + BTN_RISE), face="+Z", cable="-Y"))
# the screen: from the bottom pair (4, 5) round the board's bottom edge,
# facing the back (+Y), its pins down; 0.8 mm behind the back wall
# (waypoints, smooth: without them this short U-turn came out as
# an inside-out ribbon solid, MEASURED volume -504 mm3)
SCR_Y = Y_BI - 0.8 - 4.82


def u_turn(xc):
    """Waypoints for a ribbon from a bottom-row plug at x = xc: down, a U
    under the board's bottom edge, up into the screen's socket."""
    return [(xc, -1.3, ZB - 5.0), (xc, 2.0, ZB - 7.0), (xc, 6.0, ZB - 6.5), (xc, SCR_Y - 3.5, ZB - 3.0)]


scr, scr_ribs = ap.cable(doc, "screen", (4, 5), ap.module_placement(
    "screen", (80.0, SCR_Y, ZB + 38.0), face="+Y", cable="-Z"), via={4: u_turn(70.0), 5: u_turn(90.0)},
    smooth=True)
CB, FB, UB, KB, SB = [ap.bbox(m) for m in (cam, flash, usb, btn, scr)]
for r_ in btn_rib + scr_ribs:
    if r_.Shape.Volume <= 0:
        raise cad.CadError("%s came out inside-out: change its waypoints" % r_.Label)
print("SHUTTER module y %.2f..%.2f z %.2f..%.2f; SCREEN y %.2f..%.2f; ribbons z >= %.2f" % (
    KB.YMin, KB.YMax, KB.ZMin, KB.ZMax, SB.YMin, SB.YMax, min(r_.Shape.BoundBox.ZMin for r_ in scr_ribs)))
tick("hardware")


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, p, d, h):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def centre(b):
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2


def ray_y(shape, x, z, nth=0, back=False):
    """The surface's y at (x, z), measured with a ray from the front (or the
    back); nth=1 gives the next face in (a wall's inner face)."""
    s = shape.section(Part.makeLine(V(x, -300, z), V(x, 300, z)))
    ys = sorted(v.Point.y for v in s.Vertexes)
    return ys[-1 - nth] if back else ys[nth]


def ray_z(shape, x, y, nth=0):
    """The top surface's z at (x, y) (a ray down); nth=1: the next face down."""
    s = shape.section(Part.makeLine(V(x, y, 300), V(x, y, -300)))
    zs = sorted((v.Point.z for v in s.Vertexes), reverse=True)
    return zs[nth]


def insert(shell, cutter):
    """(shell with the opening, the piece it removed): a part that fills its
    opening exactly. Exact booleans first, fuzzy (0.01 mm) after."""
    piece, rest = shell.common(cutter), shell.cut(cutter)
    if piece.Volume < 1:
        piece, rest = shell.common(cutter, 0.01), shell.cut(cutter, 0.01)
    if piece.Volume < 1 or not rest.isValid() or len(rest.Solids) != len(shell.Solids):
        raise cad.CadError("insert: the cutter does not cleanly cross the wall")
    return rest, piece


def yprism(x0, x1, z0, z1, y0, y1, r):
    """A rounded rectangle (x, z) extruded along Y from y0 to y1."""
    w = cad.rounded_rect_wire(x1 - x0, z1 - z0, r, ((x0 + x1) / 2, y0, (z0 + z1) / 2), "Y")
    return Part.Face(w).extrude(V(0, y1 - y0, 0))


def xprism(y0, y1, z0, z1, x0, x1, r):
    w = cad.rounded_rect_wire(y1 - y0, z1 - z0, r, (x0, (y0 + y1) / 2, (z0 + z1) / 2), "X")
    return Part.Face(w).extrude(V(x1 - x0, 0, 0))


# ------------------------------------------------------------ the body
SIDE = cad.rounded_rect_wire(W, Z1 - Z0, R, (AX, 0, (Z0 + Z1) / 2), "Y")
PLAN = [(X0 - 3, Y_F), (X1 + 3, Y_F), (X1 + 3, Y_B), (X0 - 3, Y_B)]
body = cad.profile_body(SIDE, PLAN, spline=False, fillet=EDGE)
# the core keeps SHARP inner edges (a filleted core reads as open clip
# channels to ./check - handheld_console.py, R270)
shell = cad.hollow(body, WALL, core=lambda t: cad.profile_body(SIDE, PLAN, spline=False, fillet=None,
                                                               inset=t))
tick("body")
front, back = cad.split(shell, "Y", at=SPLIT_Y, lip=1.2)
tick("split")

# ------------------------------------------------------------ the Back: board, screen, shutter
# ledges 0.3 mm under and over the board's long edges (clear of the
# screen's ribbons under ports 4 / 5 and the shutter's ribbon over port 9,
# which runs in FRONT of the board), pads 0.1 mm behind it
YL = BB.YMax - 1.9                                # the ledges' front: behind the modules' slide paths (y <= 0.43)
ledges = [box(x0, x1, YL, Y_BI + 0.5, BB.ZMin - 2.3, BB.ZMin - 0.3) for x0, x1 in ((4, 56), (104, 116))]
ledges += [box(x0, x1, YL, Y_BI + 0.5, BB.ZMax + 0.3, BB.ZMax + 2.3) for x0, x1 in ((22, 56), (64, 116))]
pads = [box(x, x + 7, BB.YMax + 0.1, Y_BI + 0.5, BB.ZMin + z, BB.ZMin + z + 7) for x, z in
        ((6, 6), (6, 46), (42, 6), (42, 46), (107, 6), (107, 46))]
# the screen between two ribs 0.3 mm off its ends (its ribbons run up
# under it, x 62..98), the shutter module on two pads 0.1 mm under it
ribs = [box(x0, x1, SB.YMin + 1.0, Y_BI + 0.5, SB.ZMin + 2.0, SB.ZMax - 2.0)
        for x0, x1 in ((SB.XMin - 1.6, SB.XMin - 0.3), (SB.XMax + 0.3, SB.XMax + 1.6))]
kpads = [box(x0, x0 + 3.0, KB.YMax - 6.0, Y_BI + 0.5, BB.ZMax + 2.0, KB.ZMin - 0.1)
         for x0 in (KB.XMin + 1.0, KB.XMax - 4.0)]
back = cad.fuse_one(back, *ledges, *pads, *ribs, *kpads)
tick("back")

# four M2.5 screws from the back into insert bosses in the Front, inside
# the corners (clear of the board, the shutter, the flash and the USB-C)
SCREW = "M2.5"
SX = (X0 + 8.5, X1 - 8.5)
SZ = (ZB + 2.0, Z1 - 14.0)
SCREWS = [(x, z) for x in SX for z in SZ]
screws = []
for x, z in SCREWS:
    back, front = cad.screw_through(back, front, (x, Y_B, z), size=SCREW, ribs=0)
    yb = Y_BI - 0.1                               # the boss's top, 0.1 mm under the back wall
    front = cad.fuse_one(front, cyl(3.0, (x, yb, z), (0, -1, 0), 10.0))
    front = cad.cut(front, cyl(1.8, (x, yb + 0.5, z), (0, -1, 0), 9.5))
    lid_t = Y_B - yb
    screws.append(cad.screw("csk_phillips", SCREW, int(lid_t + 6.0), at=(x, Y_B, z), axis="-Y"))
tick("screws")

# ------------------------------------------------------------ the Front: openings
cx_, _cy, cz_ = centre(CB)                        # the lens axis
# board retention: a rib from the front wall onto the board's spine (0.2 mm off)
front = cad.fuse_one(front, box(28, 32, FRONT_IN - 0.5, BB.YMin - 0.2, BB.ZMin + 24, BB.ZMin + 36))
# the lens barrel: ONE revolved section along -Y (h = mm in front of the
# front face, r = radius); its spigot is the disc the front wall gives up
# (an insert - it fills its hole exactly), the base ring sits on the face
RB = LENS_R + 1.0
SEC = [(0, -0.5), (RB - 2.0, -0.5), (RB - 2.0, 0.0), (RB, 0.0), (RB, 3.0), (LENS_R - 0.6, 3.0),
       (LENS_R - 0.6, 3.6), (LENS_R, 3.6), (LENS_R, 10.0), (LENS_R - 0.8, 10.0), (LENS_R - 0.8, 10.6),
       (LENS_R, 10.6), (LENS_R, LENS_L - 0.6), (LENS_R - 0.6, LENS_L), (0, LENS_L)]
barrel = cad.revolve_profile(SEC, axis="-Y", at=(cx_, Y_F, cz_))
front, spigot = insert(front, cyl(RB - 2.0, (cx_, Y_F - 1.0, cz_), (0, 1, 0), WALL + 2.0))
barrel = cad.fuse_one(barrel, spigot)
# the open bore (no glass: nothing at all between the sensor and the
# subject): a stepped cone from the lens tip (h = Y_F - CAM_TIP) out
# through the front - every step outside an 80 deg view cone from the tip
h_tip = Y_F - CAM_TIP                             # the lens tip, h (negative: behind the face)
BORE_R = LENS_R - 3.5                             # the bore's mouth
VIEW_HALF = 40.0                                  # half the view cone kept clear (deg): 80 deg across
bore = []
for h0, h1, r in ((-WALL - 1.0, 1.5, 8.0), (1.5, 5.5, 11.5), (5.5, 9.5, 15.0), (9.5, LENS_L + 1.0, BORE_R)):
    if r < 3.55 + (min(h1, LENS_L) - h_tip) * math.tan(math.radians(VIEW_HALF)) - 1e-6:
        raise cad.CadError("lens bore step h %.1f..%.1f is inside the view cone" % (h0, h1))
    bore.append(cyl(r, (cx_, Y_F - h0, cz_), (0, -1, 0), h1 - h0))
barrel = cad.cut(barrel, bore)
# the flash: a frosted window through the front wall over the light, a
# light box from the wall to 0.5 mm off the light's cover
fx_, _fy, fz_ = centre(FB)
front, flash_lens = insert(front, yprism(fx_ - FLASH[0] / 2, fx_ + FLASH[0] / 2, fz_ - FLASH[1] / 2,
                                         fz_ + FLASH[1] / 2, Y_F - 2.0, FRONT_IN + 0.01, 2.0))
lbox = cad.cut(yprism(fx_ - FLASH[0] / 2 - 1.6, fx_ + FLASH[0] / 2 + 1.6, fz_ - FLASH[1] / 2 - 1.6,
                      fz_ + FLASH[1] / 2 + 1.6, FRONT_IN - 0.5, FB.YMin - 0.5, 3.0),
               yprism(fx_ - FLASH[0] / 2, fx_ + FLASH[0] / 2, fz_ - FLASH[1] / 2, fz_ + FLASH[1] / 2,
                      FRONT_IN - 1.0, FB.YMin, 2.0))
front = cad.fuse_one(front, lbox)
# the shutter: a big round key through the top wall, its flange 0.1 mm
# under the wall, a plunger to 0.16 mm over the module's own cap
kx_, ky_, _kz = centre(KB)
top_in = ray_z(front, kx_, ky_, nth=1)
base_z = top_in - 0.9
cap = cad.button_cap(CAP_D, (Z1 + 3.0) - base_z, dome=1.2, flange=1.5, at=(kx_, ky_, base_z), axis="+Z")
front = cad.opening_for(front, cap, clearance=0.25, chamfer=0.5, axis="+Z")
cap = cad.fuse_one(cap, cyl(3.0, (kx_, ky_, KB.ZMax + 0.16), (0, 0, 1), base_z - KB.ZMax + 0.34))
# USB-C on the left: a pocket brings the wall to 0.25 mm off the mouth (a
# real plug reaches it), a liner round the pocket, then the opening
uy, uz = -5.9, (UB.ZMin + UB.ZMax) / 2            # the receptacle: 5.9 mm in front of the PCB
# (the plug's overmould: 15 along the socket's 10 mm side (z), 7.5 across it)
pocket = xprism(uy - 3.75, uy + 3.75, uz - 7.5, uz + 7.5, X0 - 5, UB.XMin - 1.3, 3)
liner = cad.cut(xprism(uy - 5.75, min(uy + 5.75, SPLIT_Y - 0.6), uz - 9.5, uz + 9.5, UB.XMin - 0.25,
                       X0 + 1.0, 4), pocket)
front = cad.fuse_one(cad.cut(front, pocket), liner)
front = cad.socket_opening(front, usb, margin=1.5)
# the screen: a smoked window through the back wall over the screen
sx_, _sy, sz_ = centre(SB)
SCR_WIN = (34.0, 22.0)                            # inside the ribs at the screen's ends
back, scr_win = insert(back, yprism(sx_ - SCR_WIN[0] / 2, sx_ + SCR_WIN[0] / 2, sz_ - SCR_WIN[1] / 2,
                                    sz_ + SCR_WIN[1] / 2, Y_BI - 0.01, Y_B + 2.0, 4.0))
tick("stage A")


# === STAGE B: details ===
# (a fork may stop after STAGE A, run ./check, then add these one by one)
# the barrel: a diamond-knurled focus ring, a chrome trim ring in a recess
# round the bore's mouth (it stands 0.4 mm proud)
barrel = cad.knurl(barrel, "-Y", (cx_, Y_F, cz_), LENS_R, 4.6, 9.0, n=72, kind="diamond", depth=0.4)
TRIM = (BORE_R + 0.9, LENS_R - 1.6)               # the trim ring's radii
trim_recess = cad.cut(cyl(TRIM[1], (cx_, Y_F - LENS_L + 1.0, cz_), (0, -1, 0), 3.0),
                      cyl(TRIM[0], (cx_, Y_F - LENS_L + 2.0, cz_), (0, -1, 0), 5.0))
barrel = cad.cut(barrel, trim_recess)
lens_trim = trim_recess.common(box(-500, 500, Y_F - LENS_L - 0.4, Y_F - LENS_L + 1.0, -500, 500))
# the flash: a chrome bezel in a recess round the window (0.8 mm proud),
# Fresnel ribs across the frosted lens
BZ = 3.0                                          # the bezel's width round the window
bezel_ring = cad.cut(yprism(fx_ - FLASH[0] / 2 - BZ, fx_ + FLASH[0] / 2 + BZ, fz_ - FLASH[1] / 2 - BZ,
                            fz_ + FLASH[1] / 2 + BZ, Y_F - 0.8, Y_F + 0.5 * WALL, 2.0 + BZ),
                     yprism(fx_ - FLASH[0] / 2, fx_ + FLASH[0] / 2, fz_ - FLASH[1] / 2, fz_ + FLASH[1] / 2,
                            Y_F - 5, Y_F + 5, 2.0))       # its inner edge IS the window's edge (no sliver)
front = cad.cut(front, bezel_ring)
flash_bezel = bezel_ring
flash_lens = cad.cut(flash_lens, [box(fx_ - FLASH[0] / 2 - 1, fx_ + FLASH[0] / 2 + 1, Y_F - 1.0, Y_F + 0.4,
                                      fz_ - FLASH[1] / 2 + 2.6 + 2.5 * i, fz_ - FLASH[1] / 2 + 3.4 + 2.5 * i)
                                  for i in range(4)])
# the shutter: a chrome collar ring round the key, in a recess in the top
# wall, 1.5 mm proud; the key runs in its bore
COLLAR = (CAP_D / 2 + 0.25, CAP_D / 2 + 2.6)       # its bore IS the key's opening (no thin web)
collar = cad.cut(cyl(COLLAR[1], (kx_, ky_, Z1 - 0.5 * WALL), (0, 0, 1), 0.5 * WALL + 1.5),
                 cyl(COLLAR[0], (kx_, ky_, Z1 - WALL - 1), (0, 0, 1), WALL + 4))
front = cad.cut(front, collar)
# the rainbow stripe: five bars under the lens to the bottom edge, each in
# its own recess (0.8 mm webs between them), 0.4 mm proud
BAR_W, BAR_WEB = 3.6, 0.8
bar_x0 = AX - (5 * BAR_W + 4 * BAR_WEB) / 2
BAR_Z = (Z0 + EDGE + 2.0, cz_ - RB - 2.5)
bars = [box(bar_x0 + i * (BAR_W + BAR_WEB), bar_x0 + i * (BAR_W + BAR_WEB) + BAR_W, Y_F - 0.4,
            Y_F + 0.5 * WALL, BAR_Z[0], BAR_Z[1]) for i in range(5)]
front = cad.cut(front, bars)
# the grip: a soft-touch pad in a recess at the shutter end, 1.2 mm proud,
# with horizontal ribs
GX = (X0 + EDGE + 2.5, X0 + EDGE + 26.0)
GZ = (Z0 + EDGE + 8.0, Z1 - EDGE - 10.0)
grip_cut = yprism(GX[0], GX[1], GZ[0], GZ[1], Y_F - 1.2, Y_F + 0.5 * WALL, 5.0)
front = cad.cut(front, grip_cut)
grip = cad.cut(grip_cut, [box(GX[0] - 1, GX[1] + 1, Y_F - 1.3, Y_F - 0.6, z, z + 1.0)
                          for z in [GZ[0] + 4.0 + 3.5 * i for i in range(int((GZ[1] - GZ[0] - 7.0) / 3.5) + 1)]])
# strap lugs on both ends, high up behind the front face, a strap hole each
lugs = []
for xe, d in ((X0, -1), (X1, 1)):
    lug = cad.rounded_box(7.0, 9.0, 14.0, 3.0, at=(xe - 6.0 if d < 0 else xe - 1.0, -4.5, cz_ + 2.0), edges="y")
    hx = xe + d * 2.6
    lug = cad.hole(lug, (hx, -4.5, cz_ + 9.0), "+Y", 3.6, through=True)
    lugs.append(lug)
front = cad.fuse_one(front, *lugs)
# the viewfinder hump over the lens: a black block pinned into the top
# wall (two pegs 0.15 mm clear in holes), a smoked window front and back
HW, HD, HH = 44.0, 22.0, 11.0
HY0 = Y_F + EDGE + 0.6
hump = cad.soften(cad.rounded_box(HW, HD, HH, 5.0, at=(AX - HW / 2, HY0, Z1)), 2.5)
PEGS = [(AX - 14.0, HY0 + HD / 2), (AX + 14.0, HY0 + HD / 2)]
for px, py in PEGS:
    front = cad.hole(front, (px, py, Z1), "-Z", 4.3, through="wall")
hump = cad.fuse_one(hump, *[cyl(2.0, (px, py, Z1 - WALL + 0.3), (0, 0, 1), WALL - 0.3 + 0.5) for px, py in PEGS])
hump, finder = insert(hump, box(AX - 9.0, AX + 9.0, HY0 - 1.0, HY0 + 1.5, Z1 + 3.0, Z1 + 8.0))
hump, eyepiece = insert(hump, box(AX - 6.0, AX + 6.0, HY0 + HD - 1.5, HY0 + HD + 1.0, Z1 + 3.0, Z1 + 8.0))
# the back: a black bezel round the screen window (0.6 mm proud), thumb-rest
# ribs at the right-hand end, lettering
SBZ = 7.0
scr_bezel = cad.cut(box(sx_ - SCR_WIN[0] / 2 - SBZ, sx_ + SCR_WIN[0] / 2 + SBZ, Y_B - 0.5 * WALL, Y_B + 0.6,
                        sz_ - SCR_WIN[1] / 2 - SBZ, sz_ + SCR_WIN[1] / 2 + SBZ),
                    box(sx_ - SCR_WIN[0] / 2, sx_ + SCR_WIN[0] / 2, Y_B - 5, Y_B + 5,
                        sz_ - SCR_WIN[1] / 2, sz_ + SCR_WIN[1] / 2))
back = cad.cut(back, scr_bezel)
back = cad.fuse_one(back, *[box(x, x + 1.6, Y_B - 0.5, Y_B + 1.0, sz_ - 16.0, sz_ + 16.0)
                            for x in [X0 + EDGE + 5.0 + 4.0 * i for i in range(5)]])
back = cad.text(back, "ATECH", (sx_, Y_B, sz_ - SCR_WIN[1] / 2 - SBZ - 7.0), (0, 1, 0), 5.0, depth=0.5,
                mode="deboss")
front = cad.text(front, "PIXEL", (fx_, Y_F, fz_ - FLASH[1] / 2 - BZ - 7.0), (0, -1, 0), 5.0, depth=0.5,
                 mode="deboss")
# the parting-line reveal just ahead of the seam
front = cad.groove_ring(front, "Y", SPLIT_Y - 1.4, w=0.8, depth=0.6)
tick("stage B")


# ------------------------------------------------------------ parts
def part(name, shape):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    return o


o = part("Back", back)
o.ViewObject.ShapeColor = cad.color(COLOURS["Back"])
o = part("Front", front)
o.ViewObject.ShapeColor = cad.color(COLOURS["Front"])
o = part("Lens_Barrel", barrel)
o.ViewObject.ShapeColor = cad.color(COLOURS["Lens_Barrel"])
o = part("Lens_Trim", lens_trim)
o.ViewObject.ShapeColor = cad.color(COLOURS["Trim"])
o = part("Flash_Lens", flash_lens)
o.ViewObject.ShapeColor = cad.color(COLOURS["Flash_Lens"])
o.ViewObject.Transparency = cad.transparency(COLOURS["Flash_Lens"])
o = part("Flash_Bezel", flash_bezel)
o.ViewObject.ShapeColor = cad.color(COLOURS["Trim"])
o = part("Shutter_Cap", cap)
o.ViewObject.ShapeColor = cad.color(COLOURS["Shutter_Cap"])
o = part("Shutter_Collar", collar)
o.ViewObject.ShapeColor = cad.color(COLOURS["Trim"])
o = part("Viewfinder_Hump", hump)
o.ViewObject.ShapeColor = cad.color(COLOURS["Hump"])
o = part("Finder_Window", finder)
o.ViewObject.ShapeColor = cad.color(COLOURS["Window"])
o.ViewObject.Transparency = cad.transparency(COLOURS["Window"])
o = part("Eyepiece_Window", eyepiece)
o.ViewObject.ShapeColor = cad.color(COLOURS["Window"])
o.ViewObject.Transparency = cad.transparency(COLOURS["Window"])
o = part("Screen_Window", scr_win)
o.ViewObject.ShapeColor = cad.color(COLOURS["Window"])
o.ViewObject.Transparency = cad.transparency(COLOURS["Window"])
o = part("Screen_Bezel", scr_bezel)
o.ViewObject.ShapeColor = cad.color(COLOURS["Hump"])
o = part("Grip_Pad", grip)
o.ViewObject.ShapeColor = cad.color(COLOURS["Grip"])
o = part("Stripe_Red", bars[0])
o.ViewObject.ShapeColor = cad.color(STRIPES[0])
o = part("Stripe_Orange", bars[1])
o.ViewObject.ShapeColor = cad.color(STRIPES[1])
o = part("Stripe_Yellow", bars[2])
o.ViewObject.ShapeColor = cad.color(STRIPES[2])
o = part("Stripe_Green", bars[3])
o.ViewObject.ShapeColor = cad.color(STRIPES[3])
o = part("Stripe_Blue", bars[4])
o.ViewObject.ShapeColor = cad.color(STRIPES[4])
for i, sh in enumerate(screws):
    o = part("Screw_%d" % (i + 1), sh)
    o.ViewObject.ShapeColor = cad.color(COLOURS["Screw"])
print("TOTAL %.1f s" % (time.time() - T0))
