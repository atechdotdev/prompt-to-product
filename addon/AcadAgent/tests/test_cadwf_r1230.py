"""R1230: the fit coupon, cad.fit_coupon (docs/CAD_WORKFLOW_MERGE.md).

    cd addon/AcadAgent/tests && python3 -m unittest test_cadwf_r1230

What is pinned:
  - cad.fit_coupon is in the kit's API and on the agent's helper card
  - fc_cadwf_r1230.py under freecadcmd: five pucks whose D-bores measure
    what their labels say (3.2 to 3.6, the flat 0.5 under the bore), the
    module gauge's three windows, and the row against Gustav's own
    testfit.stl (same size, volume within 2 %); the sabotage must be noticed

The FreeCAD class skips when freecadcmd is missing.
"""
import ast
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
sys.path.insert(0, ADDON)

from acadagent import build, sandbox  # noqa: E402

KIT = sandbox.KIT_DIR
FC = sandbox.find_freecadcmd()
if FC is None and os.environ.get("ATECH_REQUIRE_FREECADCMD") == "1":
    raise RuntimeError("ATECH_REQUIRE_FREECADCMD=1 but no freecadcmd was found "
                       "(set ATECH_FREECADCMD)")


def fc(env=None, timeout=600):
    e = dict(os.environ, **(env or {}))
    p = subprocess.run([FC, os.path.join(HERE, "fc_cadwf_r1230.py")], env=e,
                       capture_output=True, text=True, timeout=timeout,
                       cwd=tempfile.gettempdir())
    return p.stdout + p.stderr


def failures(text):
    for line in reversed(text.splitlines()):
        if line.startswith("ATECH_CADWF_R1230="):
            return int(line.split("=", 1)[1])
    return None


class Api(unittest.TestCase):

    def test_signature_and_card(self):
        with open(os.path.join(KIT, "atech_detail.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}["fit_coupon"]
        self.assertEqual(ast.unparse(fn.args), "kind='shaft', at=(0, 0, 0)")
        build._HELPERS = None
        line = next((ln for ln in build.helper_card().splitlines()
                     if ln.startswith("  cad.fit_coupon(")), None)
        self.assertIsNotNone(line)
        self.assertIn("D-bores 3.2 to 3.6", line)
        self.assertTrue(line.rstrip().endswith("."), line)

    def test_the_coupon_covers_the_table_value(self):
        sys.path.insert(0, KIT)
        import atech_fit
        src = open(os.path.join(KIT, "atech_detail.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        consts = {t.id: ast.literal_eval(n.value) for n in tree.body
                  if isinstance(n, ast.Assign) for t in n.targets
                  if isinstance(t, ast.Name) and t.id.startswith("COUPON_")}
        bores = consts["COUPON_BORES"]
        # the table's value is in the middle, with a step either side to
        # find a tighter or looser printer
        self.assertEqual(bores[len(bores) // 2], atech_fit.value("dbore_d3")[0])
        self.assertIn(atech_fit.value("slide"), consts["COUPON_GAPS"])
        # R1295: the module and the shaft are the measured ones, read from
        # the fit table, not typed a second time
        fn = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}["fit_coupon"]
        body = ast.unparse(fn)
        self.assertIn("cad.fit('module_size')", body)
        self.assertIn("cad.fit('motor_shaft')", body)
        self.assertIn("cad.fit('motor_shaft_flat')", body)
        self.assertNotIn("COUPON_MODULE", consts)
        for typed in ("19.5", "2.5"):
            self.assertNotIn(typed, [ast.unparse(n) for n in ast.walk(fn)
                                     if isinstance(n, ast.Constant)], typed)


COUPON_MODEL = '''
import FreeCAD as App
import atech_cad as cad
doc = App.ActiveDocument
for label, shape in cad.fit_coupon("all").items():
    doc.addObject("Part::Feature", label).Shape = shape
doc.recompute()
'''


@unittest.skipIf(FC is None, "bundled freecadcmd not found")
class Geometry(unittest.TestCase):

    def test_the_coupon_passes_its_own_check(self):
        """R1295 review: the first coupon had engraved digits whose cusps
        left 0.05 mm walls, and ./check FAILED the part the Fit test
        window makes. It is marked with dots now and must pass."""
        with tempfile.TemporaryDirectory() as ws:
            with open(os.path.join(ws, "model.py"), "w") as fh:
                fh.write(COUPON_MODEL)
            env = dict(os.environ, ATECH_CHECK_SCRIPT=os.path.join(ws, "model.py"),
                       ATECH_CHECK_PNG="", ATECH_CHECK_TIMEOUT="200")
            p = subprocess.run([FC, os.path.join(KIT, "check.py")], env=env, cwd=ws,
                               capture_output=True, text=True, timeout=400)
        out = p.stdout + p.stderr
        self.assertIn("CHECK PASS", out, out[-3500:])
        self.assertNotIn("CHECK FAIL", out, out[-3500:])
        self.assertNotIn("thin wall", out.lower(), out[-3500:])
        # and every part gets its PRINT line with nothing to warn about
        prints = [ln for ln in out.splitlines() if ln.startswith("PRINT Fit_")]
        self.assertTrue(all("no supports" in ln for ln in prints), prints)
        self.assertEqual(len(prints), 6, out[-3500:])

    def test_coupon(self):
        out = fc()
        self.assertEqual(failures(out), 0, out[-3000:])
        self.assertGreater(out.count("\nPASS "), 30)

    def test_sabotage_is_noticed(self):
        out = fc({"ATECH_CADWF_SABOTAGE": "same"})
        self.assertTrue(failures(out), "five equal bores went unnoticed")


if __name__ == "__main__":
    unittest.main()
