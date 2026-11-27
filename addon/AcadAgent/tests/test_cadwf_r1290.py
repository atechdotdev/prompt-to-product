"""R1290: strength by hand, agent_kit/atech_mech.py (docs/CAD_WORKFLOW_MERGE.md).

    cd addon/AcadAgent/tests && python3 -m unittest test_cadwf_r1290

Gustav's closed-form checks, carried over: each formula against a textbook
number worked out here, the material data's shape, and the module's own
self-test. Pure Python.
"""
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(os.path.dirname(HERE), "acadagent", "agent_kit")
sys.path.insert(0, KIT)

import atech_mech as mech  # noqa: E402


class Formulas(unittest.TestCase):

    def test_selftest_passes(self):
        self.assertEqual(mech.selftest(), [])

    def test_cantilever(self):
        # a clip arm: 5 N at 12 mm on 6 x 1.6 PLA
        r = mech.cantilever("clip", F=5, L=12, b=6, h=1.6, material="PLA")
        Z = 6 * 1.6 ** 2 / 6
        I = 6 * 1.6 ** 3 / 12
        self.assertAlmostEqual(r["stress_MPa"], 5 * 12 / Z, places=3)
        self.assertAlmostEqual(r["deflection_mm"], 5 * 12 ** 3 / (3 * 2400 * I), places=3)
        self.assertEqual(r["allowable"], 44.0)              # 55 x 0.8
        self.assertEqual(r["ok"], r["sf"] >= 2.0)
        # across the layers it is weaker: 44 x 0.6
        z = mech.cantilever("clip", 5, 12, 6, 1.6, "PLA", direction="z")
        self.assertAlmostEqual(z["allowable"], 26.4)
        self.assertLess(z["sf"], r["sf"])

    def test_a_weak_part_is_not_ok(self):
        r = mech.cantilever("thin", F=20, L=40, b=4, h=1.0, material="PLA")
        self.assertFalse(r["ok"])
        self.assertLess(r["sf"], 1.0)

    def test_strip_on_two_supports(self):
        r = mech.ss_beam("lid", F=80, L=20, b=30, h=2, material="PETG")
        self.assertAlmostEqual(r["stress_MPa"], 10.0)
        self.assertAlmostEqual(r["allowable"], 47 * 0.8)
        mid = mech.ss_beam("lid", F=80, L=20, b=30, h=2, material="PETG", uniform=False)
        self.assertAlmostEqual(mid["stress_MPa"], 20.0)
        hot = mech.ss_beam("lid", 80, 20, 30, 2, "PETG", stress_factor=1.6)
        self.assertAlmostEqual(hot["stress_MPa"], 16.0)

    def test_snap_strain_is_the_kits_formula(self):
        # cad.cantilever_strain: 1.5 t y / L^2
        r = mech.snap_strain("hook", deflection=1.2, L=14, t=1.6, material="PLA")
        self.assertAlmostEqual(r["strain"], round(1.5 * 1.2 * 1.6 / 14 ** 2, 4))
        self.assertTrue(r["ok"])                              # 1.47 % under PLA's 2 %
        self.assertFalse(mech.snap_strain("hook", 2.5, 10, 2.0, "PLA")["ok"])
        self.assertTrue(mech.snap_strain("hook", 2.5, 14, 2.0, "PETG")["ok"])

    def test_pin_and_bearing(self):
        r = mech.pin_double_shear("hinge pin", F=30, d=1.75)
        self.assertAlmostEqual(r["stress_MPa"], round(30 / (2 * math.pi * 1.75 ** 2 / 4), 4))
        self.assertEqual(r["allowable"], 33.0)
        b = mech.bearing("hinge eye", F=30, d=1.75, t=3, material="PLA")
        self.assertAlmostEqual(b["stress_MPa"], round(30 / (1.75 * 3), 4))
        self.assertAlmostEqual(b["allowable"], 66.0)          # 1.5 x 44

    def test_bolt_as_an_axle(self):
        r = mech.bolt_cantilever("axle", F=10, L=10, size="M3")
        self.assertAlmostEqual(r["stress_MPa"], round(100 / (math.pi * 2.459 ** 3 / 32), 4))
        self.assertEqual(r["allowable"], 320.0)
        plain = mech.bolt_cantilever("axle", 10, 10, "M3", threaded=False)
        self.assertLess(plain["stress_MPa"], r["stress_MPa"])

    def test_press_fit_screen(self):
        self.assertIn("clearance", mech.press_fit("a", 3.0, 3.2)["verdict"])
        self.assertIn("local yielding", mech.press_fit("a", 3.0, 2.9)["verdict"])
        self.assertIn("split", mech.press_fit("a", 3.0, 2.8)["verdict"])
        self.assertIn("light", mech.press_fit("a", 3.0, 2.98)["verdict"])

    def test_unknown_material(self):
        with self.assertRaises(ValueError):
            mech.cantilever("x", 1, 1, 1, 1, material="unobtainium")


class Data(unittest.TestCase):

    def test_every_material_has_its_fields_and_says_it_is_unverified(self):
        for name, a in mech.ALLOWABLES.items():
            for key in ("E", "uts_xy", "z_knockdown", "yield_frac", "snap_strain", "tg_c",
                        "source"):
                self.assertIn(key, a, "%s: %s" % (name, key))
            self.assertLess(a["z_knockdown"], 1.0)
        self.assertIn("unverified", mech.ALLOWABLES["PLA"]["source"])
        self.assertIn("None of them is verified", " ".join(mech.__doc__.split()))

    def test_safety_factors(self):
        self.assertEqual(mech.SAFETY_FACTORS, {"static": 2.0, "impact": 3.0, "drop": 1.5})

    def test_no_freecad(self):
        with open(mech.__file__, encoding="utf-8") as fh:
            self.assertNotRegex(fh.read(), r"(?m)^\s*(import|from)\s+(FreeCAD|Part)\b")


if __name__ == "__main__":
    unittest.main()
