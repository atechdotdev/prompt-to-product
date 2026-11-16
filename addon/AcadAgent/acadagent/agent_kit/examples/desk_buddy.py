# Example: "a little desk buddy" - a small printed character, 88 mm tall,
# made to test a printer: eight parts, every one prints without supports
# (the sideways sockets are teardrops: their roofs rise at 45 deg).
#
#   Body      a soft block, flat bottom; a neck socket on top, an arm socket
#             each side, a round belly badge pressed 1 mm into the front
#   Head      sits on the body on a separate Neck_Pin; two eye sockets and
#             an engraved smile in the front, an antenna socket on top
#   Eye_L/R   discs pressed into the sockets (stand 1 mm proud)
#   Arm_L/R   mitten plates on a pin; they print outer face down, pin up
#   Antenna   a stalk with a flat cap; it prints cap down
#
# Fits (FDM, 0.4 mm nozzle): pins and pegs 0.2 mm under their holes on the
# diameter, eyes 0.2 mm under (a drop of glue if they are loose).
import Part
import atech_cad as cad
from FreeCAD import Vector
V = Vector

# === PARAMETERS ===
BW, BD, BH = 50.0, 38.0, 44.0     # body width (x), depth (y), height (z)
HW, HD, HH = 46.0, 36.0, 34.0     # head
CLEAR = 0.2                       # hole minus pin, on the diameter
NECK_D, NECK_L = 8.0, 19.0        # peg; 10 mm sockets in body and head
ARM_PIN_D, ARM_Z = 6.0, 30.0
EYE_D, EYE_T, EYE_X, EYE_Z = 8.8, 4.0, 10.0, 18.0
ANT_D = 4.0
FOOT_CHAMFER = 0.8                # bottom edges: under 45 deg, no supports


def cyl(r, at, axis, h):
    return Part.makeCylinder(r, h, V(*at), V(*axis))


def teardrop(d, at, axis, depth):
    """A sideways blind hole's cutter, pointed on top: its roof rises at
    45 deg, so it prints without supports and a round pin still fits.
    axis "+X" / "-X" / "+Y" / "-Y" points INTO the part from `at`."""
    import math
    r = d / 2.0
    k = r * math.sqrt(0.5)
    u = V(1, 0, 0) if axis in ("+Y", "-Y") else V(0, 1, 0)     # across, level
    n = {"+X": V(1, 0, 0), "-X": V(-1, 0, 0), "+Y": V(0, 1, 0), "-Y": V(0, -1, 0)}[axis]
    c = V(*at) - n * 0.5                                       # start 0.5 outside
    pts = [c + u * k + V(0, 0, k), c + V(0, 0, r * math.sqrt(2.0)),
           c - u * k + V(0, 0, k)]
    tip = Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(n * (depth + 0.5))
    return cyl(r, c, n, depth + 0.5).fuse(tip).removeSplitter()


def soft_block(w, d, h, z0, r, top_r):
    s = cad.rounded_box(w, d, h, r, at=(-w / 2, -d / 2, z0))
    s = cad.fillet_safe(s, top_r, lambda e: e.BoundBox.ZMin > z0 + h - 0.1,
                        why="soft top edges")
    return cad.chamfer_safe(s, FOOT_CHAMFER, lambda e: e.BoundBox.ZMax < z0 + 0.1,
                            why="bottom edge, prints on the bed")


# ------------------------------------------------------------ body
body = soft_block(BW, BD, BH, 0.0, 12.0, 6.0)
body = cad.hole(body, at=(0, 0, BH), axis="-Z", d=NECK_D + CLEAR, depth=NECK_L / 2 + 0.5)
body = cad.cut(body, *[teardrop(ARM_PIN_D + CLEAR, (sx * BW / 2, 0, ARM_Z),
                                "-X" if sx > 0 else "+X", 7.0) for sx in (1, -1)])
# belly badge: a 1 mm round recess with a raised ring inside it
badge = cyl(12.0, (0, -BD / 2 - 1, 20.0), (0, 1, 0), 2.0)
body = cad.cut(body, badge)
body = cad.fuse_one(body, cyl(8.0, (0, -BD / 2 + 1.5, 20.0), (0, -1, 0), 1.1).cut(
    cyl(6.5, (0, -BD / 2 + 2.0, 20.0), (0, -1, 0), 3.0)))

# ------------------------------------------------------------ head
Z0 = BH
head = soft_block(HW, HD, HH, Z0, 10.0, 8.0)
# the neck socket from below ends in a 90 deg cone (a drill point), not a
# flat roof that would need bridging or supports
r_neck = (NECK_D + CLEAR) / 2
head = cad.cut(head, cyl(r_neck, (0, 0, Z0 - 0.5), (0, 0, 1), NECK_L / 2 + 1.0).fuse(
    Part.makeCone(r_neck, 0.0, r_neck, V(0, 0, Z0 + NECK_L / 2 + 0.5))))
head = cad.cut(head, *[teardrop(EYE_D + CLEAR, (sx * EYE_X, -HD / 2, Z0 + EYE_Z), "+Y", 3.0)
                       for sx in (1, -1)])
head = cad.hole(head, at=(0, 0, Z0 + HH), axis="-Z", d=ANT_D + CLEAR, depth=5.0)
# smile: the lower half of a thin ring, 1 mm into the face
ring = Part.makeTorus(7.0, 1.0, V(0, -HD / 2, Z0 + 13.0), V(0, 1, 0))
lower = Part.makeBox(20.0, 6.0, 9.0, V(-10.0, -HD / 2 - 3.0, Z0 + 13.0 - 1.5 - 9.0 + 1.5))
head = cad.cut(head, ring.common(lower))

# ------------------------------------------------------------ small parts
neck = cyl(NECK_D / 2, (0, 0, BH - NECK_L / 2), (0, 0, 1), NECK_L)
neck = cad.chamfer_safe(neck, 0.6, why="peg ends, lead-in")
eyes = [cyl(EYE_D / 2, (sx * EYE_X, -HD / 2 + 3.0, Z0 + EYE_Z), (0, -1, 0), EYE_T)
        for sx in (1, -1)]
eyes = [cad.chamfer_safe(e, 0.4, lambda ed: ed.BoundBox.YMax < -HD / 2 - 0.5,
                         why="soft front edge") for e in eyes]
antenna = cad.fuse_one(cyl(ANT_D / 2, (0, 0, Z0 + HH - 4.5), (0, 0, 1), 12.0),
                       cyl(5.0, (0, 0, Z0 + HH + 7.5), (0, 0, 1), 3.0))
arms = []
for sx in (1, -1):
    x_out = sx * (BW / 2 + 6.0)
    plate = cad.rounded_box(6.0, 14.0, 24.0, 6.5, at=(min(sx * BW / 2, x_out), -7.0, 12.0),
                            edges="x")
    pin = cyl(ARM_PIN_D / 2, (sx * BW / 2, 0, ARM_Z), (-sx, 0, 0), 6.5)
    arms.append(cad.fuse_one(plate, cad.chamfer_safe(pin, 0.5, lambda e: abs(
        e.BoundBox.XMin - (sx * BW / 2 - sx * 6.5)) < 0.1, why="pin tip")))


# ------------------------------------------------------------ parts
def part(name, shape, colour):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = cad.color(colour)
    return o


part("Body", body, "cream")
part("Head", head, "sky")
part("Neck_Pin", neck, "graphite")
part("Eye_L", eyes[1], "matte_black")
part("Eye_R", eyes[0], "matte_black")
part("Antenna", antenna, "coral")
part("Arm_L", arms[1], "coral")
part("Arm_R", arms[0], "coral")
