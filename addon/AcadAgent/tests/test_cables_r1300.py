"""R1300: a ribbon cable can no longer run through a part unseen
(docs/CAD_WORKFLOW_MERGE.md, "Cables that ran through walls").

    cd addon/AcadAgent/tests && python3 -m unittest test_cables_r1300

  - a ribbon bent across its width is built so it does not run through
    itself, or refused with where and what to move
  - a part whose faces cross or face inward (a negative volume) is judged
    on sampled points, not on a boolean that finds nothing, and ./check
    names it INSIDE OUT
  - SABOTAGE: the bedside lamp with a narrower column fails on its port-6
    ribbon through the Shell (the old ribbon passed with most of it inside)

All in the bundled freecadcmd (skipped without it).
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from acadagent import sandbox  # noqa: E402
import test_kit_examples_r500 as r500  # noqa: E402

FC = sandbox.find_freecadcmd()

INSIDE_OUT = '''
import FreeCAD as App
import Part
doc = App.ActiveDocument
doc.addObject("Part::Feature", "Plate").Shape = Part.makeBox(30, 20, 3)
doc.addObject("Part::Feature", "Lid").Shape = Part.makeBox(30, 20, 3, App.Vector(0, 0, 10)).reversed()
doc.recompute()
'''


def _need_fc(case):
    if FC is None:
        if os.environ.get("ATECH_REQUIRE_FREECADCMD") == "1":
            case.fail("no freecadcmd")
        case.skipTest("bundled freecadcmd not found")


class Ribbons(unittest.TestCase):

    def test_ribbons_and_inside_out_parts(self):
        _need_fc(self)
        p = subprocess.run([FC, os.path.join(HERE, "fc_cables_r1300.py")],
                           capture_output=True, text=True, timeout=600,
                           cwd=tempfile.gettempdir(),
                           env=dict(os.environ, QT_QPA_PLATFORM="offscreen"))
        out = p.stdout + p.stderr
        self.assertIn("ATECH_CABLES_R1300=0", out, out[-3000:])
        self.assertGreaterEqual(len([ln for ln in out.splitlines() if ln.startswith("PASS ")]), 7)


class Check(unittest.TestCase):

    def test_check_names_an_inside_out_part(self):
        _need_fc(self)
        with tempfile.TemporaryDirectory() as ws:
            with open(os.path.join(ws, "model.py"), "w") as fh:
                fh.write(INSIDE_OUT)
            env = dict(os.environ, ATECH_CHECK_SCRIPT=os.path.join(ws, "model.py"),
                       ATECH_CHECK_PNG="", ATECH_CHECK_TIMEOUT="120")
            p = subprocess.run([FC, os.path.join(sandbox.KIT_DIR, "check.py")], env=env,
                               cwd=ws, capture_output=True, text=True, timeout=300)
        out = p.stdout + p.stderr
        self.assertTrue([ln for ln in out.splitlines()
                         if "Lid: shape is INSIDE OUT" in ln], out[-3000:])
        self.assertFalse([ln for ln in out.splitlines() if "Plate: shape is INSIDE OUT" in ln])

    def test_lamp_with_a_narrow_column_fails_on_its_ribbon(self):
        # SABOTAGE: R_COL 40 -> 35 leaves port 6 no room to turn; the old
        # ribbon turned inside out there and passed with most of it in the
        # Shell (the shipped lamp itself passes in test_kit_examples_r500)
        _need_fc(self)
        models = os.path.normpath(os.path.join(r500.PROJECTS, "..", "models"))
        if os.path.isdir(models):
            os.environ.setdefault("ATECH_ARTIFACTS", models)
        code = r500.read(os.path.join(r500.EXAMPLES, "bedside_lamp.py"))
        narrow = code.replace("\nR_COL = 40.0 ", "\nR_COL = 35.0 ")
        self.assertNotEqual(narrow, code)
        v = r500.check_ws(narrow)
        if "LibraryMissing" in v:
            self.skipTest("no Atech module library here")
        self.assertTrue(v.startswith("CHECK FAIL") and "button_6_cable_p6 and Shell" in v, v)


if __name__ == "__main__":
    unittest.main()
