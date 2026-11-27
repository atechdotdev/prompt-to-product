"""R1230: the fit coupon (cad.fit_coupon) - runs INSIDE freecadcmd.

    <freecadcmd> fc_cadwf_r1230.py        (tests/test_cadwf_r1230.py does this)

Five pucks whose D-bores measure what their labels say, a module gauge with
three windows, and the whole thing against Gustav's testfit.py: his
out/testfit.stl is 85.99 x 14.0 x 10.0 mm and 7.167 cm3 (measured from the
cad-workflow repository, 2026-11-27).

Prints PASS/FAIL per check and ends with ATECH_CADWF_R1230=<failures>.
ATECH_CADWF_SABOTAGE=same makes every puck's bore 3.4 (the suite must notice).
"""
import math
import os
import sys
import traceback

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "acadagent", "agent_kit")))

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402

import atech_cad as cad  # noqa: E402
import atech_detail as det  # noqa: E402
import atech_print  # noqa: E402

V = App.Vector
FAIL = []
if os.environ.get("ATECH_CADWF_SABOTAGE") == "same":
    det.COUPON_BORES = (3.4, 3.4, 3.4, 3.4, 3.4)

# Gustav's testfit.stl, measured with trimesh from cad-workflow/builds/wheels/out
REF_SIZE = (85.99, 14.0, 10.0)
REF_CM3 = 7.167


def check(name, ok, detail=""):
    print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAIL.append(name)


def t_shaft_pucks():
    got = cad.fit_coupon()
    check("five pucks", sorted(got) == ["Fit_D32", "Fit_D33", "Fit_D34", "Fit_D35", "Fit_D36"],
          repr(sorted(got)))
    for i, bd in enumerate((3.2, 3.3, 3.4, 3.5, 3.6)):
        puck = got.get("Fit_D%d" % round(bd * 10))
        if puck is None:
            continue
        cx = i * 18.0
        air = Part.makeBox(8, 8, 0.02, V(cx - 4, -4, 5.0)).cut(puck)
        bb = air.BoundBox
        check("puck %g: round %g" % (bd, bd), abs(bb.YLength - bd) < 0.01, "%.3f" % bb.YLength)
        check("puck %g: across the flat %g" % (bd, bd - 0.5),
              abs(bb.XLength - (bd - 0.5)) < 0.01, "%.3f" % bb.XLength)
        check("puck %g: bore goes through" % bd,
              not puck.isInside(V(cx, 0, 0.2), 1e-6, True)
              and not puck.isInside(V(cx, 0, 9.8), 1e-6, True))
        check("puck %g: one valid solid" % bd, puck.isValid() and len(puck.Solids) == 1)
        row = atech_print.shape_report(puck, "p")
        check("puck %g: prints as it stands, no supports" % bd,
              row["turned_deg"] == 0.0 and not row["supports"] and not row["flags"],
              repr(row.get("flags")))
    whole = Part.makeCompound(list(got.values()))
    bb = whole.BoundBox
    size = (bb.XLength, bb.YLength, bb.ZLength)
    check("the row is the size of Gustav's (86 x 14 x 10)",
          all(abs(a - b) < 0.05 for a, b in zip(size, REF_SIZE)),
          "%.2f x %.2f x %.2f" % size)
    cm3 = sum(s.Volume for s in got.values()) / 1000.0
    check("its volume is within 2 %% of his %.3f cm3" % REF_CM3,
          abs(cm3 - REF_CM3) < 0.02 * REF_CM3, "%.3f" % cm3)


def t_labels_differ():
    got = cad.fit_coupon()
    vols = [round(got[k].Volume, 2) for k in sorted(got)]
    # a larger bore and another number: no two pucks have the same volume
    check("every puck is its own", len(set(vols)) == 5, repr(vols))
    check("bigger bore, less plastic (within the dots)", vols[0] > vols[-1], repr(vols))
    # R1295: the labels are round dots in the top face, one per tenth:
    # 2 on the 3.2 puck ... 6 on the 3.6 puck, 2 / 3 / 4 on the plate
    def dots(shape, z, d):
        return [f for f in shape.Faces
                if type(f.Surface).__name__ == "Plane" and abs(f.Area - math.pi * d * d / 4) < 0.01
                and abs(f.CenterOfMass.z - (z - det.COUPON_DOT_DEPTH)) < 1e-6]
    for bd in (3.2, 3.3, 3.4, 3.5, 3.6):
        n = len(dots(got["Fit_D%d" % round(bd * 10)], 10.0, det.COUPON_DOT_D))
        check("puck %g carries %d dots" % (bd, round(bd * 10) % 10),
              n == round(bd * 10) % 10, "%d" % n)
    plate = cad.fit_coupon("module")["Fit_slide"]
    n = len(dots(plate, 3.0, det.COUPON_PLATE_DOT_D))
    check("the plate carries 2 + 3 + 4 dots", n == 9, "%d" % n)
    # no letters: nothing in the coupon is a spline or a glyph's cusp
    kinds = {type(f.Surface).__name__ for s in got.values() for f in s.Faces}
    check("only planes, cylinders and cones", kinds <= {"Plane", "Cylinder", "Cone"},
          repr(sorted(kinds)))


def t_module_gauge():
    got = cad.fit_coupon("module")
    check("one plate", list(got) == ["Fit_slide"])
    plate = got["Fit_slide"]
    x = 4.0
    for g in (0.2, 0.3, 0.4):
        w = 19.5 + 2 * g
        air = Part.makeBox(w + 2, 30, 0.02, V(x - 1, 2, 1.5)).cut(plate)
        win = [s for s in air.Solids if s.isInside(V(x + w / 2, 4 + w / 2, 1.51), 1e-6, True)]
        bb = win[0].BoundBox if win else None
        check("window for %.1f a side is %.1f square" % (g, w),
              bb is not None and abs(bb.XLength - w) < 0.01 and abs(bb.YLength - w) < 0.01,
              "%s" % (bb,))
        x += w + 4.0
    check("plate valid", plate.isValid() and len(plate.Solids) == 1)
    row = atech_print.shape_report(plate, "plate")
    check("the plate lies flat, no supports", row["turned_deg"] in (0.0, 180.0)
          and not row["supports"], repr(row.get("flags")))


def t_all_and_refusals():
    got = cad.fit_coupon("all")
    check("all: six parts", len(got) == 6)
    for a in got:
        for b in got:
            if a < b and got[a].common(got[b]).Volume > 1e-6:
                check("%s and %s do not overlap" % (a, b), False)
    check("all: nothing overlaps", True)
    try:
        cad.fit_coupon("bolt")
        check("unknown kind refused", False)
    except cad.CadError:
        check("unknown kind refused", True)


for fn in (t_shaft_pucks, t_labels_differ, t_module_gauge, t_all_and_refusals):
    try:
        fn()
    except Exception:                                   # noqa: BLE001
        traceback.print_exc()
        check(fn.__name__, False, "raised")

print("ATECH_CADWF_R1230=%d" % len(FAIL))
if FAIL:
    print("FAILED: " + ", ".join(FAIL))
