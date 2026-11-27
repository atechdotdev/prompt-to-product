"""R1295: what the review of the cad-workflow merge found, where no other
test file pins it (docs/CAD_WORKFLOW_MERGE.md, "The review").

    cd addon/AcadAgent/tests && python3 -m unittest test_cadwf_r1295

  - the print check cannot stall ./check: a solid sewn from a mesh has
    thousands of planar faces, and reading them one by one grew with the
    square of their number; one part's time budget is looked at between
    its steps, and the product pack has the same budget
  - which side goes down follows Export's own tolerance
  - a size model.py marks `# MEASURE:` gets a line from ./check

Pure Python (fake shapes), plus one ./check run in the bundled freecadcmd
(skipped without it).
"""
import os
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
KIT = os.path.join(ADDON, "acadagent", "agent_kit")
sys.path.insert(0, KIT)
sys.path.insert(0, ADDON)

try:
    import numpy as np
except ImportError:                                     # pragma: no cover
    np = None

import atech_print  # noqa: E402


class _Vec:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z


class Plane:
    pass


class _Vertex:
    def __init__(self, p):
        self.Point = _Vec(*p)


class _Face:
    """A planar face as brep_planes reads one."""
    ParameterRange = (0.0, 1.0, 0.0, 1.0)

    def __init__(self, normal, point, area, calls=None):
        self.Surface = Plane()
        self._n, self.Area, self.Vertexes = normal, area, [_Vertex(point)]
        self._calls = calls

    def normalAt(self, u, v):
        if self._calls is not None:
            self._calls.append(1)
        return _Vec(*self._n)


class _Shape:
    def __init__(self, faces, mesh=None):
        self.Faces = faces
        self._mesh = mesh

    def tessellate(self, deflection):
        pts, tris = self._mesh
        return [_Vec(*p) for p in pts], tris


def _box_mesh(w=20.0, d=10.0, h=5.0):
    pts = [(0, 0, 0), (w, 0, 0), (w, d, 0), (0, d, 0), (0, 0, h), (w, 0, h), (w, d, h), (0, d, h)]
    tris = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
            (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
    return pts, tris


def _box_faces(w=20.0, d=10.0, h=5.0, split=1):
    """The six sides of a box, each cut into `split` coplanar faces."""
    sides = (((0, 0, -1), (0, 0, 0), w * d), ((0, 0, 1), (0, 0, h), w * d),
             ((0, -1, 0), (0, 0, 0), w * h), ((0, 1, 0), (0, d, 0), w * h),
             ((-1, 0, 0), (0, 0, 0), d * h), ((1, 0, 0), (w, 0, 0), d * h))
    return [_Face(n, p, a / split) for n, p, a in sides for _ in range(split)]


@unittest.skipIf(np is None, "numpy not available")
class NoStall(unittest.TestCase):

    def test_coplanar_faces_add_up(self):
        pts = np.asarray(_box_mesh()[0], dtype=float)
        got = atech_print.brep_planes(_Shape(_box_faces(split=40)), pts)
        self.assertEqual(len(got), 6)
        self.assertAlmostEqual(got[0][0], 200.0, places=6)
        self.assertEqual(sorted(round(a) for a, _n in got), [50, 50, 100, 100, 200, 200])

    def test_many_faces_in_many_directions_do_not_stall(self):
        """The part's reach was worked out again for every face, and every
        face was compared with every group of faces: both grew with the
        square of the face count. 6000 faces in 6000 directions (a ball
        sewn from its mesh) are read in well under a second now."""
        import math
        n = 6000
        dirs, pts = [], []
        for i in range(n):                      # points spread over a sphere of radius 20
            z = 1 - 2 * (i + 0.5) / n
            r = math.sqrt(max(0.0, 1 - z * z))
            a = i * math.pi * (3 - math.sqrt(5))
            dirs.append((r * math.cos(a), r * math.sin(a), z))
        pts = [(20 * x, 20 * y, 20 * z) for x, y, z in dirs]
        faces = [_Face(d, q, 0.2) for d, q in zip(dirs, pts)]
        faces += _box_faces(8.0, 8.0, 1.0)      # ... and six real flat sides inside it
        t0 = time.time()
        got = atech_print.brep_planes(_Shape(faces), np.asarray(pts, dtype=float))
        self.assertLess(time.time() - t0, 3.0)
        # every facet of the ball is a resting side of 0.2 mm2: under the
        # 1 mm2 floor; the box inside the ball rests on nothing
        self.assertEqual(got, [])

    def test_too_many_faces_are_not_judged(self):
        """Above MAX_BREP_FACES the part is not judged, and says so. (The
        first fix read such a part from its mesh instead: a small flat
        base was lost and the line said "no flat side to rest on".)"""
        pts, tris = _box_mesh()
        keep = atech_print.MAX_BREP_FACES
        atech_print.MAX_BREP_FACES = 60
        try:
            shape = _Shape(_box_faces(split=11), (pts, tris))
            self.assertIsNone(atech_print.brep_planes(shape, np.asarray(pts, dtype=float)))
            row = atech_print.shape_report(shape, "Sewn")
        finally:
            atech_print.MAX_BREP_FACES = keep
        self.assertEqual(row, {"label": "Sewn", "skipped": "66 faces", "flags": []})
        self.assertGreaterEqual(keep, 20000)
        # under the limit the same shape is judged from its faces
        row = atech_print.shape_report(_Shape(_box_faces(split=11), (pts, tris)), "Sewn")
        self.assertEqual(round(row["flat_face_mm2"]), 200)
        self.assertFalse(row["supports"])

    def test_the_deadline_is_looked_at_between_faces(self):
        pts, tris = _box_mesh()
        shape = _Shape(_box_faces(split=100), (pts, tris))          # 600 faces
        with self.assertRaises(atech_print._Late):
            atech_print.brep_planes(shape, np.asarray(pts, dtype=float),
                                    deadline=time.time() - 1.0)

    def test_a_face_stored_inside_out_still_counts(self):
        pts = np.asarray(_box_mesh()[0], dtype=float)
        faces = _box_faces()
        faces[0] = _Face((0, 0, 1), (0, 0, 0), 200.0)               # the bottom, normal reversed
        got = atech_print.brep_planes(_Shape(faces), pts)
        self.assertEqual(len(got), 6)
        down = [g for g in got if g[1][2] < -0.99]
        self.assertEqual(len(down), 1)
        self.assertAlmostEqual(down[0][0], 200.0)

    def test_a_part_past_the_deadline_is_skipped_not_waited_for(self):
        pts, tris = _box_mesh()
        calls = []
        shape = _Shape([_Face((0, 0, -1), (0, 0, 0), 200.0, calls)], (pts, tris))
        row = atech_print.shape_report(shape, "Late", deadline=time.time() - 1.0)
        self.assertEqual(row, {"label": "Late", "skipped": "time budget", "flags": []})
        self.assertEqual(calls, [])                 # its faces were not even read
        row = atech_print.shape_report(shape, "In time", deadline=time.time() + 60.0)
        self.assertNotIn("skipped", row)
        self.assertEqual(atech_print.line(
            {"label": "Late", "skipped": "time budget", "flags": []}),
            "PRINT Late: not judged (time budget)")

    def test_reports_hands_each_part_the_deadline(self):
        pts, tris = _box_mesh()
        seen = []
        real = atech_print.shape_report

        def spy(shape, label="", deflection=None, deadline=None):
            seen.append(deadline)
            return real(shape, label, deadline=deadline)
        atech_print.shape_report = spy
        try:
            t0 = time.time()
            rows = atech_print.reports(
                [{"label": "A", "shape": _Shape(_box_faces(), (pts, tris))}], budget_s=6.0)
        finally:
            atech_print.shape_report = real
        self.assertEqual(len(rows), 1)
        self.assertTrue(seen and seen[0] is not None)
        self.assertAlmostEqual(seen[0] - t0, 6.0, delta=1.0)

    def test_the_product_pack_has_the_same_budget(self):
        with open(os.path.join(ADDON, "acadagent", "p2p_product.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("BED_BUDGET_S = 6.0", src)
        rows = src[src.index("def part_rows("):]
        rows = rows[:rows.index("\ndef ", 10)]
        self.assertIn("deadline = time.time() + BED_BUDGET_S", rows)
        self.assertIn("deadline=deadline", rows)
        self.assertIn('"skipped": "time budget"', rows)


@unittest.skipIf(np is None, "numpy not available")
class SideDown(unittest.TestCase):

    def test_a_tilted_bottom_is_not_already_down(self):
        """Export keeps the side that already faces down only when it
        faces straight down (within 1e-6 of -Z). The check allowed 1e-4,
        so for a bottom tilted 0.1 to 0.8 degrees the PRINT line named
        another side than the exported plate had."""
        import math
        a = math.radians(0.4)
        tilted = (90.0, (0.0, math.sin(a), -math.cos(a)))       # the bottom, a little off
        side = (100.0, (1.0, 0.0, 0.0))                         # the largest side
        self.assertEqual(atech_print.choose_down([side, tilted]), side)
        flat = (90.0, (0.0, 0.0, -1.0))
        self.assertEqual(atech_print.choose_down([side, flat]), flat)
        with open(os.path.join(ADDON, "acadagent", "export_tools.py"), encoding="utf-8") as fh:
            self.assertIn("-1 + 1e-6", fh.read())


class BrokenRecord(unittest.TestCase):

    def test_load_user_never_raises(self):
        """load_user promises never to raise; an "active" that is a list
        or an object raised TypeError (unhashable) in ./check."""
        import json
        import atech_fit
        for active in (["X1C | PLA"], {"a": 1}, 3, None, "nobody"):
            with tempfile.TemporaryDirectory() as d:
                p = os.path.join(d, "fit_user.json")
                with open(p, "w") as fh:
                    json.dump({"active": active,
                               "profiles": {"X1C | PLA": {"values": {"slide": 0.4}}}}, fh)
                self.assertEqual(atech_fit.load_user(p), [], active)
        for junk in ("[]", "3", '"x"', "{", '{"profiles": []}', '{"profiles": {"a": 3}, '
                     '"active": "a"}'):
            with tempfile.TemporaryDirectory() as d:
                p = os.path.join(d, "fit_user.json")
                with open(p, "w") as fh:
                    fh.write(junk)
                self.assertEqual(atech_fit.load_user(p), [], junk)
        atech_fit.reset_user()
        self.assertEqual(atech_fit.value("slide"), 0.3)


MODEL = textwrap.dedent('''
    import FreeCAD as App
    import Part
    doc = App.ActiveDocument
    BATTERY_L = 65.0        # MEASURE: the 18650 cell's length, assumed 65
    JACK_D = 6.2            # MEASURE the jack's thread, assumed 6.2
    note = "MEASURE: this is a string, not a comment"
    tag = "#7 MEASURE: a hash inside a string is not a comment either"
    LED_D = 5.0             # measure: the LED's body, assumed 5.0
    SLOT = 3.0              # I will measure this later (no mark: no colon, no capitals)
    tray = Part.makeBox(BATTERY_L + 6, 24, 3)
    doc.addObject("Part::Feature", "Tray").Shape = tray
    doc.recompute()
''')


class MeshMadePart(unittest.TestCase):

    def test_a_ball_sewn_from_its_mesh(self):
        from acadagent import sandbox
        fc = sandbox.find_freecadcmd()
        if fc is None:
            if os.environ.get("ATECH_REQUIRE_FREECADCMD") == "1":
                self.fail("no freecadcmd")
            self.skipTest("bundled freecadcmd not found")
        p = subprocess.run([fc, os.path.join(HERE, "fc_cadwf_r1295.py")],
                           capture_output=True, text=True, timeout=300,
                           cwd=tempfile.gettempdir(),
                           env=dict(os.environ, QT_QPA_PLATFORM="offscreen"))
        out = p.stdout + p.stderr
        self.assertIn("ATECH_CADWF_R1295=0", out, out[-3000:])
        self.assertGreaterEqual(out.count("\nPASS "), 8)


class Measure(unittest.TestCase):

    def test_the_agent_is_told_to_write_the_mark(self):
        """Second review: ./check looked for a comment nobody was told to
        write (TRAPS R41 asked for a sentence in the reply only)."""
        with open(os.path.join(KIT, "examples", "TRAPS.md"), encoding="utf-8") as fh:
            traps = fh.read()
        r41 = traps[traps.index("R41. "):traps.index("R42. ")]
        self.assertIn("# MEASURE: the jack's thread, assumed 6.2", r41)
        self.assertIn("./check lists every", " ".join(r41.split()))



    def test_check_names_the_assumed_sizes(self):
        from acadagent import sandbox
        fc = sandbox.find_freecadcmd()
        if fc is None:
            if os.environ.get("ATECH_REQUIRE_FREECADCMD") == "1":
                self.fail("no freecadcmd")
            self.skipTest("bundled freecadcmd not found")

        def run(model):
            with tempfile.TemporaryDirectory() as ws:
                with open(os.path.join(ws, "model.py"), "w") as fh:
                    fh.write(model)
                env = dict(os.environ, ATECH_CHECK_SCRIPT=os.path.join(ws, "model.py"),
                           ATECH_CHECK_PNG="", ATECH_CHECK_TIMEOUT="120")
                p = subprocess.run([fc, os.path.join(KIT, "check.py")], env=env, cwd=ws,
                                   capture_output=True, text=True, timeout=300)
            return p.stdout + p.stderr
        out = run(MODEL)
        lines = [ln for ln in out.splitlines() if ln.startswith("MEASURE ")]
        self.assertEqual(len(lines), 1, out[-3000:])
        self.assertIn("3 sizes in model.py are assumed, not measured", lines[0])
        self.assertIn("the LED's body, assumed 5.0", lines[0])
        self.assertNotIn("a hash inside a string", lines[0])
        self.assertNotIn("later", lines[0])
        self.assertIn("the 18650 cell's length, assumed 65", lines[0])
        self.assertIn("the jack's thread, assumed 6.2", lines[0])
        self.assertNotIn("this is a string", lines[0])
        # information only
        self.assertFalse([ln for ln in out.splitlines()
                          if ln.startswith("PROBLEM") and "MEASURE" in ln])
        # and a script without a mark gets no line
        clean = "\n".join(ln.split("# MEASURE")[0].split("# measure")[0]
                          for ln in MODEL.splitlines())
        self.assertFalse([ln for ln in run(clean).splitlines() if ln.startswith("MEASURE ")])


if __name__ == "__main__":
    unittest.main()
