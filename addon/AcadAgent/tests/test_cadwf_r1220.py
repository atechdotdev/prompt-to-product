"""R1220: the kit calls that apply the printed fit numbers
(docs/CAD_WORKFLOW_MERGE.md).

    cd addon/AcadAgent/tests && python3 -m unittest test_cadwf_r1220

What is pinned:
  - cad.d_bore, cad.shaft_hole and cad.fit are in the kit's API and on the
    agent's helper card; cad.wheel takes flat=, cad.screw_boss takes kind=
    (the prompt has told the agent to pass kind= since R511)
  - fc_cadwf_r1220.py under freecadcmd: the D-bore measures 3.4 / 2.9 and
    12 deep, the wheel's too, the insert boss has the insert's pocket, and
    old calls give what they gave; each sabotage switch must be noticed
  - the prompt names the D-bore for wheels on a dc_motor

The FreeCAD class skips when freecadcmd is missing (ATECH_FREECADCMD points
at one; ATECH_REQUIRE_FREECADCMD=1 makes a missing one fail).
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


def _functions(name):
    with open(os.path.join(KIT, name), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    return {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}


def fc(env=None, timeout=600):
    e = dict(os.environ, **(env or {}))
    p = subprocess.run([FC, os.path.join(HERE, "fc_cadwf_r1220.py")], env=e,
                       capture_output=True, text=True, timeout=timeout,
                       cwd=tempfile.gettempdir())
    return p.stdout + p.stderr


def failures(text):
    for line in reversed(text.splitlines()):
        if line.startswith("ATECH_CADWF_R1220="):
            return int(line.split("=", 1)[1])
    return None


class Api(unittest.TestCase):

    def test_signatures(self):
        cad = _functions("atech_cad.py")
        det = _functions("atech_detail.py")
        self.assertEqual(ast.unparse(cad["d_bore"].args),
                         "shape, at, axis, depth=None, bore=None, across=None, "
                         "flat=None, lead_in=0.5")
        self.assertEqual(ast.unparse(cad["shaft_hole"].args),
                         "shape, at, axis, shaft_d, fit_class='running', "
                         "depth=None, through=False")
        self.assertEqual(ast.unparse(cad["fit"].args), "key")
        # new arguments go LAST: every existing positional call keeps working
        self.assertTrue(ast.unparse(det["wheel"].args).endswith(
            "bore=None, axis='+Y', at=(0, 0, 0), flat=False"))
        self.assertTrue(ast.unparse(det["screw_boss"].args).endswith(
            "ribs=4, rib_len=None, kind='tap', insert_len=None"))

    def test_on_the_helper_card(self):
        build._HELPERS = None
        card = build.helper_card()
        for name in ("d_bore", "shaft_hole", "fit"):
            line = next((ln for ln in card.splitlines()
                         if ln.startswith("  cad.%s(" % name)), None)
            self.assertIsNotNone(line, name)
            self.assertTrue(line.rstrip().endswith((".", ")")), line)
        self.assertIn("flat=False", card)
        self.assertIn("kind='tap'", card)
        self.assertIn("3.4 round, 2.9 across the flat", card)

    def test_the_prompt_no_longer_names_a_missing_argument(self):
        # R511 told the agent cad.screw_boss(kind="tap") or kind="insert"
        # while screw_boss had no `kind`: a TypeError on the first try
        det = _functions("atech_detail.py")
        self.assertIn("kind", [a.arg for a in det["screw_boss"].args.args])
        section = build.atech_fit_section()
        if section:
            self.assertIn('kind="insert"', section)

    def test_the_prompt_sends_motor_wheels_to_the_d_bore(self):
        section = build.atech_fit_section()
        self.assertTrue(section, "no fit section")
        self.assertIn("flat=True", section)
        self.assertIn("cad.d_bore", section)
        self.assertIn("cad.shaft_hole", section)

    def test_reference_no_longer_says_a_round_bore_on_the_motor(self):
        with open(os.path.join(KIT, "reference", "ATECH_PRODUCTS.md"),
                  encoding="utf-8") as fh:
            ref = fh.read()
        self.assertNotIn("bore=3.3", ref)
        self.assertIn("flat=True", ref)


@unittest.skipIf(FC is None, "bundled freecadcmd not found")
class Geometry(unittest.TestCase):

    def test_kit_calls(self):
        out = fc()
        self.assertEqual(failures(out), 0, out[-3000:])
        self.assertGreater(out.count("\nPASS "), 45)

    def test_each_sabotage_is_noticed(self):
        for gate in ("dbore", "round", "insert"):
            out = fc({"ATECH_CADWF_SABOTAGE": gate})
            self.assertTrue(failures(out), "sabotage %r went unnoticed" % gate)


if __name__ == "__main__":
    unittest.main()
