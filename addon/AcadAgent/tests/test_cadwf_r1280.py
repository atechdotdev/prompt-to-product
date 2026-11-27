"""R1280: what the agent is told (docs/CAD_WORKFLOW_MERGE.md).

    cd addon/AcadAgent/tests && python3 -m unittest test_cadwf_r1280

TRAPS.md carries the lessons of Gustav's printed parts, each naming the kit
call or the ./check line that deals with it; the fit section of the prompt
points at the PRINT and FIT lines; and every kit call a trap names exists.
Pure Python.
"""
import ast
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
sys.path.insert(0, ADDON)

from acadagent import build, sandbox  # noqa: E402

KIT = sandbox.KIT_DIR
TRAPS = os.path.join(KIT, "examples", "TRAPS.md")


def _section():
    with open(TRAPS, encoding="utf-8") as fh:
        text = fh.read()
    m = re.search(r"\n## From parts that were designed and printed \(R1280\).*", text, re.S)
    return m.group(0) if m else ""


def _kit_functions():
    names = set()
    for f in ("atech_cad.py", "atech_form.py", "atech_detail.py"):
        with open(os.path.join(KIT, f), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names |= {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    return names


class Traps(unittest.TestCase):

    def test_the_printed_lessons_are_there(self):
        sec = _section()
        self.assertTrue(sec, "no R1280 section in TRAPS.md")
        for needle in ("3.4 / 2.9", "has no key", "0.25 mm under its drawn size",
                       "ONE side only", "slivers", "largest\n    flat side",
                       "shell with ribs", "0.3 mm per side", "MEASURE:"):
            self.assertIn(needle, sec, needle)
        self.assertEqual(re.findall(r"(?m)^R(\d+)\. ", sec),
                         [str(n) for n in range(33, 43)])

    def test_it_claims_only_what_was_printed(self):
        """R1295 review: the section said more than Gustav's records do."""
        sec = " ".join(_section().split())
        for gone in ("each of these cost a print", "does not drive", "0.3 mm wide",
                     "0.3 mm per side did", "it still does not turn",
                     "Thin strokes left hairline gaps"):
            self.assertNotIn(gone, sec, gone)
        # the material the fits were proven in, and what is only assumed
        self.assertIn("PETG and PETG-CF; no PLA print on record", sec)
        self.assertIn("the running size is assumed", sec)
        self.assertIn("that size is assumed, its print is not on record", sec)
        # the wheel plate's numbers, each with the step that gave it
        self.assertIn("14 h 36 and 334 g", sec)
        self.assertIn("7 h 08 and 171 g", sec)
        self.assertIn("smaller and without tread, 4 h 13 and 135 g", sec)
        self.assertIn("0.6 mm lead-in on both sides of a 1.2 mm rim", sec)

    def test_every_kit_call_a_trap_names_exists(self):
        have = _kit_functions()
        for name in set(re.findall(r"`?cad\.([a-z_]+)\(", _section())):
            self.assertIn(name, have, "TRAPS.md names cad.%s, which the kit does not have" % name)
        for name in ("motor_shaft", "wheel", "d_bore", "shaft_hole", "fit", "fit_coupon", "text"):
            self.assertIn("cad.%s(" % name, _section())

    def test_the_numbers_are_the_fit_tables(self):
        sys.path.insert(0, KIT)
        import atech_fit
        atech_fit.reset_user()
        sec = _section()
        bore, across = atech_fit.value("dbore_d3")
        self.assertIn("%g / %g" % (bore, across), sec)
        self.assertIn("%g mm under" % atech_fit.value("hole_shrink"), sec)
        self.assertIn('"push")`\n    draws %g' % atech_fit.hole_for(3.0, "push"), sec)
        self.assertIn('`"press"` %g' % atech_fit.hole_for(3.0, "press"), sec)
        self.assertIn('`"running"` %g' % atech_fit.hole_for(3.0, "running"), sec)
        self.assertIn("%g mm per side" % atech_fit.value("slide"), sec)

    def test_the_starter_it_points_at_is_there(self):
        self.assertIn("starters/starter_wheels.py", _section())
        with open(os.path.join(KIT, "starters", "starter_wheels.py"), encoding="utf-8") as fh:
            self.assertIn("cad.motor_shaft(", fh.read())


class Prompt(unittest.TestCase):

    def test_fit_section_points_at_the_new_lines(self):
        sec = " ".join(build.atech_fit_section().split())
        self.assertIn("./check's PRINT lines say which side of each part goes down", sec)
        self.assertIn("FIT lines", sec)
        self.assertIn("SHAFTS:", sec)

    def test_every_placeholder_was_filled(self):
        sec = build.atech_fit_section()
        self.assertNotRegex(sec, r"\{[a-z_]+\}")


if __name__ == "__main__":
    unittest.main()
