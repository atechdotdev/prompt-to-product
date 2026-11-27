# Starter (R820): "Two-wheel base" - the Atech board lying flat on a printed
# chassis, two DC motors seated on ports 1 and 9 driving a wheel each, a
# domed skid under the far end (three points on the ground) and a rounded
# cover over the board and motors, held by four screws up through the
# chassis. Adapt it: add sensors and lights, reshape the cover into a body.
import Part
import atech_ports as ap
import atech_cad as cad
from FreeCAD import Vector, Placement, Rotation
V = Vector

FLAT = Rotation(Vector(1, 0, 0), 90)   # the board lying flat, components up
R = 24.0                               # wheel radius (sets the board height)
WHEEL_W = 14.0
WALL = 2.0                             # chassis floor, cover walls and top
CLEAR = 0.3                            # clearance round the board and motors
MARGIN = 6.0                           # room past the board's ends for the screws
RIM = 1.2                              # chassis rim up the board's edge (low:
                                       # the motors still slide in from the side)
TOP_AIR = 1.0                          # air over the motors
SKID_R = 6.0                           # the skid's dome
SLOT = 4.0                             # the shaft slots' width (shaft: 3 mm)
COLOURS = {"Chassis": "graphite", "Cover": "toy_yellow", "Tyre": "rubber",
           "Rim": "matte_white", "Screw": "chrome"}

# The wheel, measured first: the tread blocks stand proud of R, so the axle
# height comes from the tread's bottom, not from R.
WHEEL = dict(spokes=5, tread="block", tread_n=22)
AXLE = -cad.wheel(2 * R, WHEEL_W, axis="-X", **WHEEL)["tyre"].BoundBox.ZMin
board = ap.board_object(doc)
L = AXLE - 10.14                       # PCB top: shaft centre 10.14 above it
board.Placement = Placement(Vector(0, 0, L), FLAT)
mot_l = ap.seat(doc, "dc_motor", 1)
mot_r = ap.seat(doc, "dc_motor", 9)
pcb = cad.bound_of(board)
mb = ap.bbox(mot_l)
SHAFT_Y = (mb.YMin + mb.YMax) / 2      # the axle, measured
MID_X = (pcb.XMin + pcb.XMax) / 2      # the board's centre line
tip = mb.XMin                          # the left shaft's tip (x)
GEAR_X = tip + 8.8                     # the left gearbox's face: the shaft
                                       # stands 8.8 mm proud of it (measured)

# The outline both parts share: the board plus the screw margin along Y,
# the gearboxes plus the clearance and a wall along X.
X0 = GEAR_X - CLEAR - WALL
X1 = 2 * MID_X - X0
Y0, Y1 = pcb.YMin - CLEAR - MARGIN, pcb.YMax + CLEAR + MARGIN
FLOOR = pcb.ZMin - WALL
DECK = pcb.ZMin + RIM                  # the chassis top: the cover stands on it
TOP = mb.ZMax + TOP_AIR + WALL



def wheel_on(motor):
    """A wheel pushed straight onto a motor's D-shaft, as (tyre, rim): the
    hub's keyed D-bore is the size that printed and fitted (3.4 / 2.9; a
    round bore would not drive) and takes the shaft's OWN flat, measured
    from the module, so bore and shaft line up. The wheel's centre is 1.33 mm
    past the shaft's tip (as the toy car's): 4.5 mm of the shaft in the hub."""
    s = cad.motor_shaft(motor)
    w = cad.wheel(2 * R, WHEEL_W, flat=s["flat"], axis=s["axis"],
                  at=s["tip"] + s["axis"] * 1.33, **WHEEL)
    cap = w["cap"].copy()
    cap.translate(s["axis"] * -0.6)    # pressed into the hub pocket, fused
    return w["tyre"], cad.fuse_one(w["rim"], cap)


tyre_l, rim_l = wheel_on(mot_l)
tyre_r, rim_r = wheel_on(mot_r)

# Chassis: a plate with the skid under the far end, then the pocket the
# board drops into (0.3 mm clear all round) - cut last, so the skid's dome
# never pokes up into it.
chassis = cad.rounded_box(X1 - X0, Y1 - Y0, DECK - FLOOR, 4.0, at=(X0, Y0, FLOOR))
skid_y = pcb.YMin + 12.0
skid_z = SKID_R                        # the dome's centre: its bottom on the desk
skid = Part.makeSphere(SKID_R, V(MID_X, skid_y, skid_z)).fuse(
    Part.makeCylinder(SKID_R, FLOOR + 0.5 - skid_z, V(MID_X, skid_y, skid_z)))
chassis = cad.fuse_one(chassis, skid)
chassis = cad.cut(chassis, cad.rounded_box(pcb.XLength + 2 * CLEAR, pcb.YLength + 2 * CLEAR,
                                           RIM + 1, 1.0,
                                           at=(pcb.XMin - CLEAR, pcb.YMin - CLEAR, pcb.ZMin)))

# Cover: a rounded shell standing on the chassis, open at the bottom, with a
# slot up each side wall for the shaft - open at the bottom, so the cover
# lowers on over the shafts.
cover = cad.rounded_box(X1 - X0, Y1 - Y0, TOP - DECK, 4.0, at=(X0, Y0, DECK))
cover = cad.shell(cover, WALL, cad.faces_at(cover, "-Z"))
slots = [Part.makeBox(WALL + 2, SLOT, AXLE - DECK + 0.5, V(x, SHAFT_Y - SLOT / 2, DECK - 0.5))
         for x in (X0 - 1, X1 - WALL - 1)]
slots += [Part.makeCylinder(SLOT / 2, WALL + 2, V(x, SHAFT_Y, AXLE), V(1, 0, 0))
          for x in (X0 - 1, X1 - WALL - 1)]
cover = cad.cut(cover, slots)

# Four M2 screws up through the chassis into bosses in the cover's corners.
screws = []
for x in (X0 + MARGIN / 2 + 0.5, X1 - MARGIN / 2 - 0.5):
    for y in (Y0 + MARGIN / 2 + 0.5, Y1 - MARGIN / 2 - 0.5):
        chassis, cover = cad.screw_through(chassis, cover, (x, y, FLOOR),
                                           size="M2", ribs=0)
        # the length screw_through prints for this boss
        screws.append(cad.screw("csk_phillips", "M2", 11, at=(x, y, FLOOR), axis="+Z"))

parts = {"Chassis": chassis, "Cover": cover, "Tyre_L": tyre_l, "Rim_L": rim_l,
         "Tyre_R": tyre_r, "Rim_R": rim_r}
parts.update({"Screw_%d" % (i + 1): s for i, s in enumerate(screws)})
for name, shape in parts.items():
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = cad.color(COLOURS[name.split("_")[0]])

# intent.json for this example (write it before model.py): the cover, its
# screws and the wheels go on after the motors, so ./check tests the
# motors' slide paths without them.
INTENT = {"board": "flat", "fitted_after": [
    "Cover", "Screw_1", "Screw_2", "Screw_3", "Screw_4",
    "Tyre_L", "Rim_L", "Tyre_R", "Rim_R"]}
