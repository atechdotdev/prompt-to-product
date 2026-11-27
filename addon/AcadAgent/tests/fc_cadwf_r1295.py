"""R1295 under freecadcmd: the print check on a solid made from a mesh.

Run by test_cadwf_r1295.py. A ball with a small flat base, sewn from its
mesh (about 2000 planar faces): the second review found that reading such
a part from its mesh lost the base ("no flat side to rest on") and named
another side than Export.
"""
import math
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(os.path.dirname(HERE), "acadagent", "agent_kit")
sys.path.insert(0, KIT)
sys.path.insert(0, os.path.dirname(HERE))

import FreeCAD as App  # noqa: E402
import Mesh  # noqa: E402
import Part  # noqa: E402

import atech_print  # noqa: E402

V = App.Vector
FAIL = []


def check(name, ok, detail=""):
    print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAIL.append(name)


def sewn_ball(turn=None):
    """A ball of radius 15 with a flat base of about 36 mm2, as a solid
    whose faces are the facets of its mesh."""
    r = 15.0
    cap = math.sqrt(36.0 / math.pi)                     # the base's radius
    ball = Part.makeSphere(r).cut(Part.makeBox(40, 40, 40, V(-20, -20, -40 - math.sqrt(
        r * r - cap * cap))))
    if turn is not None:
        ball.rotate(V(0, 0, 0), V(*turn), 90)
    mesh = Mesh.Mesh()
    pts, tris = ball.tessellate(0.5)
    for a, b, c in tris:
        mesh.addFacet(pts[a], pts[b], pts[c])
    shape = Part.Shape()
    shape.makeShapeFromMesh(mesh.Topology, 0.01)
    return Part.makeSolid(shape), ball


def t_a_small_base_on_a_many_faced_part():
    solid, ball = sewn_ball()
    n = len(solid.Faces)
    check("the sewn ball has many planar faces", n > 500, "%d" % n)
    t0 = time.time()
    row = atech_print.shape_report(solid, "Ball", deadline=time.time() + 6.0)
    took = time.time() - t0
    check("judged within the budget", "skipped" not in row and took < 6.0,
          "%.2f s %r" % (took, row.get("skipped")))
    want = atech_print.shape_report(ball, "Ball")["flat_face_mm2"]
    check("its base is found: the same flat side as the drawn ball",
          abs((row.get("flat_face_mm2") or 0) - want) < 0.05 * want,
          "%s vs %s" % (row.get("flat_face_mm2"), want))
    check("no 'no flat side' flag", not any("no flat side" in f[1] for f in row.get("flags", [])),
          repr(row.get("flags")))
    check("base down: not turned", row.get("turned_deg") == 0.0, repr(row.get("turned_deg")))


def t_the_base_to_the_side_is_turned_down():
    solid, _ball = sewn_ball(turn=(1, 0, 0))
    row = atech_print.shape_report(solid, "Ball", deadline=time.time() + 6.0)
    check("base to the side: turned 90 degrees onto it, as Export does",
          "skipped" not in row and abs((row.get("turned_deg") or 0) - 90.0) < 0.5,
          repr((row.get("turned_deg"), row.get("skipped"))))
    try:
        from acadagent import export_tools as et
        _shape, info = et.orient_for_print(solid)
        check("Export agrees on the side", abs(info["flat_face_mm2"] - row["flat_face_mm2"]) < 1.0,
              "%s vs %s" % (info.get("flat_face_mm2"), row.get("flat_face_mm2")))
    except Exception as exc:                             # noqa: BLE001
        check("Export could be asked", False, repr(exc))


def t_past_the_deadline_it_is_skipped():
    solid, _ball = sewn_ball()
    row = atech_print.shape_report(solid, "Ball", deadline=time.time() - 1.0)
    check("a deadline already past: not judged", row.get("skipped") == "time budget", repr(row))
    keep = atech_print.MAX_BREP_FACES
    atech_print.MAX_BREP_FACES = 100
    try:
        row = atech_print.shape_report(solid, "Ball")
    finally:
        atech_print.MAX_BREP_FACES = keep
    check("over the face limit: not judged, and it says how many",
          str(row.get("skipped", "")).endswith(" faces") and not row.get("flags"), repr(row))


for fn in (t_a_small_base_on_a_many_faced_part, t_the_base_to_the_side_is_turned_down,
           t_past_the_deadline_it_is_skipped):
    try:
        fn()
    except Exception:                                   # noqa: BLE001
        traceback.print_exc()
        check(fn.__name__, False, "raised")

print("ATECH_CADWF_R1295=%d" % len(FAIL))
if FAIL:
    print("FAILED: " + ", ".join(FAIL))
