"""R1250: printability in ./check - agent_kit/atech_print.py
(docs/CAD_WORKFLOW_MERGE.md).

    cd addon/AcadAgent/tests && python3 -m unittest test_cadwf_r1250

Pure numpy on meshes made here by hand. The cases are the print failures
Gustav's cad-workflow recorded: a rim that is a knife edge on the bed, a
shell that would have gone rim-down, a part with no flat side, a part on a
small foot, a flange that hangs over air. Every expected number is a closed
form of the sizes used to build the mesh.

The FreeCAD class runs ./check on a real model.py in the bundled freecadcmd
and reads the PRINT lines; it skips when freecadcmd is missing.
"""
import math
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
KIT = os.path.join(ADDON, "acadagent", "agent_kit")
sys.path.insert(0, KIT)
sys.path.insert(0, ADDON)

try:
    import numpy as np
except ImportError:
    np = None

import atech_print  # noqa: E402

PI = math.pi
N = 96                                   # segments of a lathed mesh
ROUND = N / (2 * PI) * math.sin(2 * PI / N)   # a 96-gon's area over a circle's


def lathe(profile, n=N):
    """A closed mesh: the closed (r, z) polygon `profile` turned round Z."""
    m = len(profile)
    pts = []
    for k in range(n):
        a = 2 * PI * k / n
        pts += [(r * math.cos(a), r * math.sin(a), z) for r, z in profile]
    tris = []
    for k in range(n):
        k2 = (k + 1) % n
        for i in range(m):
            j = (i + 1) % m
            a, b, c, d = k * m + i, k * m + j, k2 * m + j, k2 * m + i
            tris += [(a, b, c), (a, c, d)]
    return pts, tris


def box(w, d, h, at=(0.0, 0.0, 0.0)):
    x, y, z = at
    pts = [(x, y, z), (x + w, y, z), (x + w, y + d, z), (x, y + d, z),
           (x, y, z + h), (x + w, y, z + h), (x + w, y + d, z + h), (x, y + d, z + h)]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    tris = []
    for a, b, c, e in quads:
        tris += [(a, b, c), (a, c, e)]
    return pts, tris


def join(*meshes):
    pts, tris = [], []
    for p, t in meshes:
        off = len(pts)
        pts += p
        tris += [(a + off, b + off, c + off) for a, b, c in t]
    return pts, tris


def flipped(mesh):
    pts, tris = mesh
    return [(x, -y, -z) for x, y, z in pts], tris


def levels(row):
    return [lvl for lvl, _ in row["flags"]]


@unittest.skipIf(np is None, "numpy not available")
class Section(unittest.TestCase):

    def test_box(self):
        P, T = atech_print.arrays(*box(40, 30, 10))
        s = atech_print.section(P, T, 5.0)
        self.assertAlmostEqual(s["area"], 1200.0, places=6)
        self.assertAlmostEqual(s["perimeter"], 140.0, places=6)
        self.assertEqual((s["pieces"], s["holes"]), (1, 0))
        self.assertEqual(atech_print.section(P, T, 11.0)["area"], 0.0)

    def test_a_ring_has_a_hole(self):
        P, T = atech_print.arrays(*lathe([(18, 0), (20, 0), (20, 5), (18, 5)]))
        if atech_print.signed_volume(P, T) < 0:       # section() wants outward facets
            T = T[:, ::-1]
        s = atech_print.section(P, T, 2.5)
        self.assertAlmostEqual(s["area"], PI * (400 - 324) * ROUND, delta=0.05)
        self.assertEqual((s["pieces"], s["holes"]), (1, 1))

    def test_four_feet_are_four_pieces(self):
        feet = [box(5, 5, 10, at=(x, y, 0)) for x in (0, 30) for y in (0, 20)]
        P, T = atech_print.arrays(*join(*feet))
        s = atech_print.section(P, T, 0.1)
        self.assertEqual(s["pieces"], 4)
        self.assertAlmostEqual(s["area"], 100.0, places=6)

    def test_an_inside_out_mesh_is_turned_right(self):
        pts, tris = box(10, 10, 10)
        row = atech_print.report(pts, [t[::-1] for t in tris], "Box")
        self.assertAlmostEqual(row["first_layer"]["area"], 100.0, places=3)


@unittest.skipIf(np is None, "numpy not available")
class Orientation(unittest.TestCase):

    def test_the_largest_flat_side_goes_down(self):
        row = atech_print.report(*box(40, 10, 30), label="Plate")   # standing on 40 x 10
        self.assertAlmostEqual(row["flat_face_mm2"], 1200.0, places=1)
        self.assertAlmostEqual(row["turned_deg"], 90.0, places=1)
        self.assertAlmostEqual(row["height_mm"], 10.0, places=3)
        self.assertAlmostEqual(row["first_layer"]["area"], 1200.0, places=1)
        self.assertEqual(row["first_layer"]["pieces"], 1)
        self.assertFalse(row["supports"])
        self.assertEqual(row["flags"], [])

    def test_the_bottom_is_kept_when_nearly_as_big(self):
        row = atech_print.report(*box(10, 10, 11), label="Block")   # sides 110, bottom 100
        self.assertEqual(row["turned_deg"], 0.0)
        self.assertAlmostEqual(row["flat_face_mm2"], 100.0, places=1)
        row = atech_print.report(*box(10, 10, 14), label="Post")    # sides 140: turn it
        self.assertAlmostEqual(row["turned_deg"], 90.0, places=1)

    def test_a_cup_given_rim_down_is_turned_onto_its_base(self):
        # cad-workflow: "shells were exported rim-down once"
        cup = [(0, 0), (20, 0), (20, 30), (18, 30), (18, 2), (0, 2)]
        row = atech_print.report(*flipped(lathe(cup)), label="Cup")
        self.assertAlmostEqual(row["turned_deg"], 180.0, places=1)
        self.assertAlmostEqual(row["first_layer"]["area"], PI * 400 * ROUND, delta=1.0)
        self.assertEqual(row["first_layer"]["holes"], 0)
        self.assertFalse(row["supports"])
        self.assertEqual(row["flags"], [])

    def test_export_uses_the_same_numbers(self):
        with open(os.path.join(ADDON, "acadagent", "export_tools.py"), encoding="utf-8") as fh:
            src = fh.read()
        for name in ("OVERHANG_DEG", "OVERHANG_TOL_DEG", "BED_TOL", "KEEP_BOTTOM_SHARE",
                     "OVERHANG_FLAG_MM2", "OVERHANG_FLAG_SHARE"):
            m = re.search(r"(?m)^%s = ([0-9.]+)" % name, src)
            self.assertTrue(m, name)
            self.assertEqual(getattr(atech_print, name), float(m.group(1)), name)


@unittest.skipIf(np is None, "numpy not available")
class FirstLayer(unittest.TestCase):

    def test_a_half_millimetre_rim_is_a_knife_edge(self):
        row = atech_print.report(*lathe([(19.5, 0), (20, 0), (20, 5), (19.5, 5)]), label="Rim")
        fl = row["first_layer"]
        self.assertAlmostEqual(fl["line_mm"], 0.5, delta=0.01)
        self.assertEqual(levels(row), ["warning"])
        self.assertIn("0.50 mm wide", row["flags"][0][1])
        self.assertIn("ONE side", row["flags"][0][1])

    def test_a_one_millimetre_rim_holds(self):
        # the egg cup after its fix: "a continuous 0.95 mm ring"
        row = atech_print.report(*lathe([(19.05, 0), (20, 0), (20, 5), (19.05, 5)]), label="Rim")
        self.assertAlmostEqual(row["first_layer"]["line_mm"], 0.95, delta=0.01)
        self.assertEqual(row["flags"], [])

    def test_chamfers_on_both_sides_of_the_bed_rim(self):
        # cad-workflow: a lead-in on both sides "made a knife-edge first
        # layer; the print came loose". Both ends chamfered: no good side.
        both = [(18.8, 0), (19.2, 0), (20, 0.8), (20, 4.2), (19.2, 5), (18.8, 5),
                (18, 4.2), (18, 0.8)]
        row = atech_print.report(*lathe(both), label="Ring")
        self.assertLess(row["first_layer"]["line_mm"], 0.8)
        self.assertEqual(levels(row), ["warning"])
        # one end left plain: that end goes down, and it holds
        one = [(18.8, 0), (19.2, 0), (20, 0.8), (20, 5), (18, 5), (18, 0.8)]
        row = atech_print.report(*lathe(one), label="Ring")
        self.assertAlmostEqual(row["turned_deg"], 180.0, places=1)
        self.assertAlmostEqual(row["first_layer"]["line_mm"], 2.0, delta=0.02)
        self.assertEqual(row["flags"], [])

    def test_no_flat_side(self):
        arc = [(10 * math.sin(PI * i / 48), 10 - 10 * math.cos(PI * i / 48)) for i in range(49)]
        row = atech_print.report(*lathe(arc), label="Ball")
        self.assertEqual(row["flat_face_mm2"], 0.0)
        self.assertEqual(levels(row)[0], "warning")
        self.assertIn("no flat side", row["flags"][0][1])
        self.assertIn("no flat side", atech_print.line(row))

    def test_a_small_foot_under_a_wide_body(self):
        dome = [(20 * math.cos(PI / 2 * i / 24), 25 + 10 * math.sin(PI / 2 * i / 24))
                for i in range(25)]
        mushroom = [(0, 0), (3, 0), (3, 25)] + dome
        foot = PI * 9
        row = atech_print.report(*lathe(mushroom), label="Mushroom",
                                 planes=[(foot, (0.0, 0.0, -1.0))])
        self.assertAlmostEqual(row["first_layer"]["area"], foot * ROUND, delta=0.1)
        self.assertEqual(levels(row), ["note", "note"])
        self.assertIn("stands on 28 mm2", row["flags"][0][1])
        self.assertTrue(row["supports"])
        # the cap's flat underside hangs over air: pi (20^2 - 3^2)
        self.assertAlmostEqual(row["overhang_mm2"], PI * (400 - 9) * ROUND, delta=2.0)


@unittest.skipIf(np is None, "numpy not available")
class Overhang(unittest.TestCase):

    def test_a_flange_over_air_needs_supports(self):
        spool = [(0, 0), (20, 0), (20, 5), (3, 5), (3, 25), (20, 25), (20, 30), (0, 30)]
        row = atech_print.report(*lathe(spool), label="Spool")
        self.assertEqual(row["turned_deg"], 0.0)
        self.assertAlmostEqual(row["overhang_mm2"], PI * (400 - 9) * ROUND, delta=2.0)
        self.assertTrue(row["supports"])
        self.assertEqual(levels(row), ["note"])
        self.assertIn("supports", atech_print.line(row))

    def test_a_45_degree_chamfer_is_not_an_overhang(self):
        # a cone of exactly 45 degrees, wide end up: Export's tolerance
        funnel = [(0, 0), (5, 0), (15, 10), (0, 10)]
        row = atech_print.report(*lathe(funnel), label="Funnel",
                                 planes=[(PI * 25, (0.0, 0.0, -1.0))])
        self.assertEqual(row["overhang_mm2"], 0.0)
        steep = [(0, 0), (5, 0), (20, 10), (0, 10)]          # 56 degrees from vertical
        row = atech_print.report(*lathe(steep), label="Funnel",
                                 planes=[(PI * 25, (0.0, 0.0, -1.0))])
        self.assertGreater(row["overhang_mm2"], 800.0)

    def test_the_bed_face_is_not_an_overhang(self):
        row = atech_print.report(*box(40, 30, 10), label="Plate")
        self.assertEqual(row["overhang_mm2"], 0.0)

    def test_lines(self):
        row = atech_print.report(*box(40, 30, 10), label="Plate")
        self.assertEqual(atech_print.line(row),
                         "PRINT Plate: on its 1200 mm2 flat side; first layer 1200 mm2 in "
                         "1 piece, lines 17.14 mm wide on average; no supports")
        self.assertEqual(atech_print.line({"label": "X", "skipped": "time budget"}),
                         "PRINT X: not judged (time budget)")


# ---------------------------------------------------------------- ./check
MODEL = textwrap.dedent('''
    import FreeCAD as App
    import Part
    doc = App.ActiveDocument
    # a tray, drawn the way it is used (open side up): fine as it stands
    tray = Part.makeBox(60, 40, 12).cut(Part.makeBox(56, 36, 10, App.Vector(2, 2, 2)))
    doc.addObject("Part::Feature", "Tray").Shape = tray
    # a lid drawn in place, its lip hanging down: Export turns it over
    lid = Part.makeBox(60, 40, 2, App.Vector(0, 0, 12.2)).fuse(
        Part.makeBox(55.6, 35.6, 3, App.Vector(2.2, 2.2, 9.2)).cut(
            Part.makeBox(52, 32, 3, App.Vector(4, 4, 9.2))))
    doc.addObject("Part::Feature", "Lid").Shape = lid
    # a thin ring beside them: its only flat sides are 0.7 mm wide
    ring = Part.makeCylinder(15, 6, App.Vector(90, 20, 0)).cut(
        Part.makeCylinder(14.3, 6, App.Vector(90, 20, 0)))
    doc.addObject("Part::Feature", "Ring").Shape = ring
    doc.recompute()
''')


def _freecadcmd():
    from acadagent import sandbox
    return sandbox.find_freecadcmd()


@unittest.skipIf(np is None, "numpy not available")
class InCheck(unittest.TestCase):

    def test_check_prints_a_line_per_part_and_warns_about_the_ring(self):
        fc = _freecadcmd()
        if fc is None:
            if os.environ.get("ATECH_REQUIRE_FREECADCMD") == "1":
                self.fail("no freecadcmd")
            self.skipTest("bundled freecadcmd not found")
        with tempfile.TemporaryDirectory() as ws:
            with open(os.path.join(ws, "model.py"), "w") as fh:
                fh.write(MODEL)
            env = dict(os.environ, ATECH_CHECK_SCRIPT=os.path.join(ws, "model.py"),
                       ATECH_CHECK_PNG="", ATECH_CHECK_TIMEOUT="120")
            p = subprocess.run([fc, os.path.join(KIT, "check.py")], env=env, cwd=ws,
                               capture_output=True, text=True, timeout=300)
            out = p.stdout + p.stderr
        lines = {ln.split(":", 1)[0]: ln for ln in out.splitlines() if ln.startswith("PRINT ")}
        self.assertIn("PRINT Tray", lines, out[-3000:])
        self.assertIn("on its 2400 mm2 flat side;", lines["PRINT Tray"])
        self.assertIn("no supports", lines["PRINT Tray"])
        self.assertIn("turned 180 deg", lines["PRINT Lid"])
        self.assertIn("no supports", lines["PRINT Lid"])
        self.assertIn("lines 0.70 mm wide", lines["PRINT Ring"])
        warn = [ln for ln in out.splitlines() if "WARNING" in ln and "Ring" in ln]
        self.assertTrue(any("will not stick" in ln for ln in warn), out[-3000:])
        # information only: the print check never decides the verdict (the
        # Lid's missing screws do, here - an older gate)
        verdict = "\n".join(ln for ln in out.splitlines()
                            if ln.startswith(("PROBLEM", "CHECK FAIL")))
        for words in ("first layer", "will not stick", "flat side", "supports"):
            self.assertNotIn(words, verdict)
        self.assertNotIn("Ring", verdict)


if __name__ == "__main__":
    unittest.main()
