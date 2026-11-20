"""R1120 print plan per Bambu printer (agent_kit/p2p_print.py) and the PRINT
line in ./check.

    cd addon/AcadAgent/tests && python3 -m unittest test_p2p_r1120
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
KIT = os.path.join(ADDON, "acadagent", "agent_kit")
for p in (ADDON, KIT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import p2p_brief as B                                          # noqa: E402
import p2p_print as PP                                         # noqa: E402

PARTS = [{"label": "Case", "size_mm": [110, 70, 30], "volume_cm3": 40, "colour": "black"},
         {"label": "Lid", "size_mm": [110, 70, 4], "volume_cm3": 15, "colour": "white"},
         {"label": "Leg", "count": 4, "size_mm": [12, 12, 80], "volume_cm3": 5,
          "colour": "black"},
         {"label": "Panel", "size_mm": [230, 180, 3], "volume_cm3": 60, "colour": "black"}]


def printer(p, key):
    return [x for x in p["printers"] if x["key"] == key][0]


class TestPack(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(PP.pack_plates([(100, 100)] * 9, (256, 256, 256)), 3)
        self.assertEqual(PP.pack_plates([(100, 100)] * 4, (180, 180, 180)), 4)
        self.assertEqual(PP.pack_plates([(10, 10)] * 50, (256, 256, 256)), 1)
        self.assertIsNone(PP.pack_plates([(300, 10)], (256, 256, 256)))

    def test_turns_a_long_part(self):
        self.assertEqual(PP.pack_plates([(60, 240)], (256, 256, 256)), 1)


class TestPlan(unittest.TestCase):
    def test_which_printer(self):
        p = PP.plan(PARTS)
        self.assertEqual(p["best"], "a1")
        self.assertFalse(printer(p, "a1mini")["fits"])
        self.assertEqual(printer(p, "a1mini")["too_big"], ["Panel"])
        self.assertEqual(printer(p, "h2s")["plates"], 1)
        self.assertGreater(printer(p, "a1")["hours"], printer(p, "x1c")["hours"])

    def test_grams_and_colours(self):
        p = PP.plan(PARTS)
        want = sum(PP.print_grams(x["volume_cm3"], None, x["size_mm"]) * x.get("count", 1)
                   for x in PARTS) * PP.FILAMENT_MARGIN
        self.assertAlmostEqual(p["grams"], round(want, 1), places=0)
        solid = (40 + 15 + 4 * 5 + 60) * PP.PLA_DENSITY
        self.assertLess(p["grams"], solid, "infill: less than the solid mass")
        self.assertEqual(p["colours"], 2)
        self.assertEqual(p["ams"], "ams")

    def test_print_grams_matches_shop(self):
        sys.path.insert(0, ADDON)
        from acadagent import shop
        self.assertAlmostEqual(PP.print_grams(50, 9000), shop.print_grams(50000, 9000), 6)
        # a thin plate prints nearly solid
        self.assertAlmostEqual(PP.print_grams(10, None, (100, 100, 1)), 10 * 1.24, 1)

    def test_too_big(self):
        p = PP.plan([{"label": "Sword", "size_mm": [600, 40, 10], "volume_cm3": 100}])
        self.assertIsNone(p["best"])
        self.assertIn("split", p["parts"][0]["notes"][0])
        self.assertTrue(PP.check_line(p).startswith("PRINT too big"))

    def test_tall_part_brim(self):
        # a tall part that can't lie down: it stands, so it's laid flat on
        # its biggest face anyway - only a part whose flat height is large
        # against its footprint is tall
        p = PP.plan([{"label": "Tower", "size_mm": [20, 20, 20], "volume_cm3": 8}])
        self.assertFalse(p["parts"][0]["tall"])

    def test_material_from_brief(self):
        self.assertEqual(PP.plan(PARTS, B.brief("an outdoor sign"))["material"]["name"],
                         "PETG or ASA")
        self.assertEqual(PP.plan(PARTS, B.brief("a shower caddy, waterproof"))["material"]
                         ["name"], "PETG")
        self.assertEqual(PP.plan(PARTS)["material"]["name"], "PLA")

    def test_quantity_advice(self):
        p = PP.plan(PARTS, B.brief("make 3 of them, a desk lamp"))
        self.assertTrue(any(a.startswith("3 copies") for a in p["advice"]), p["advice"])

    def test_many_colours(self):
        parts = [{"label": "P%d" % i, "size_mm": [10, 10, 10], "volume_cm3": 1,
                  "colour": c} for i, c in enumerate(["red", "blue", "green", "white",
                                                      "black"])]
        self.assertEqual(PP.plan(parts)["ams"], "more than 4 colours")

    def test_text(self):
        p = PP.plan(PARTS)
        self.assertIn("PRINT fits the Bambu Lab A1 and up: 2 plates", PP.check_line(p))
        md = PP.markdown(p)
        self.assertIn("| Bambu Lab A1 mini | no: Panel |", md)
        self.assertIn("Rough, before slicing", md)
        self.assertIsNone(PP.check_line(PP.plan([])))
        self.assertEqual(PP.hours_text(1.5), "1 h 30 min")
        self.assertEqual(PP.hours_text(0.25), "15 min")

    def test_parts_from_check(self):
        res = {"objects": [{"label": "Case", "size": [10, 20, 30], "volume_mm3": 2000},
                           {"label": "Bad", "error": "x"}]}
        self.assertEqual(PP.parts_from_check(res),
                         [{"label": "Case", "count": 1, "size_mm": [10, 20, 30],
                           "volume_cm3": 2.0, "colour": ""}])


try:
    import test_agent_kit as tak
    FC, PROJECTS = tak.FC, tak.PROJECTS
except Exception:                                                 # noqa: BLE001
    FC = PROJECTS = None


@unittest.skipIf(FC is None, "freecadcmd not found")
class TestCheckPrintLine(unittest.TestCase):
    def test_print_line(self):
        ws = tempfile.mkdtemp(prefix="atech-r1120-")
        try:
            shutil.copy(os.path.join(KIT, "examples", "motion_light.py"),
                        os.path.join(ws, "model.py"))
            artifacts = os.environ.get("ATECH_ARTIFACTS") or os.path.normpath(
                os.path.join(ADDON, "..", "..", "models"))
            env = dict(os.environ, ATECH_CHECK_SCRIPT=os.path.join(ws, "model.py"),
                       ATECH_CHECK_PNG="", ATECH_CHECK_PATH=PROJECTS,
                       ATECH_ARTIFACTS=artifacts)
            p = subprocess.run([FC, os.path.join(KIT, "check.py")], env=env,
                               capture_output=True, text=True, timeout=900, cwd=ws)
            out = p.stdout + p.stderr
        finally:
            shutil.rmtree(ws, ignore_errors=True)
        lines = [ln for ln in out.splitlines() if ln.startswith("PRINT ")]
        self.assertEqual(len(lines), 1, out[-3000:])
        self.assertIn("Bambu Lab", lines[0])
        self.assertIn("before slicing", lines[0])


if __name__ == "__main__":
    unittest.main()
