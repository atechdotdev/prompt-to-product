"""R1110 acceptance: the built design against the brief (agent_kit/p2p_accept.py,
p2p_printers.py) and the BRIEF lines in ./check.

    cd addon/AcadAgent/tests && python3 -m unittest test_p2p_r1110
    (the ./check case needs freecadcmd: ATECH_FREECADCMD=...)
"""
import json
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

import p2p_accept as A                                         # noqa: E402
import p2p_brief as B                                          # noqa: E402
import p2p_printers as P                                       # noqa: E402

DESK = ("A desk buddy with a button that plays a sound, and a light that glows red "
        "when it is too hot. Pocket-sized, black.")


def state(rows, rid):
    return [r for r in rows if r["id"] == rid][0]["state"]


def good_facts():
    return {"modules": [{"module": m, "ports": [i]} for i, m in
                        enumerate(["button", "light", "speaker", "temp_humidity", "usbc"], 1)],
            "whole_mm": [70, 110, 28], "parts": [{"label": "Case", "size_mm": [70, 110, 20]}],
            "check": "pass", "electrical_errors": 0,
            "code": "if (btn.wasPressed()) { spk.playNote(440, 200); }\n"
                    "if (th.readTemperature() > 28) { led.setAll(255, 0, 0); }",
            "colours": ["black"]}


class TestPrinters(unittest.TestCase):
    def test_lay_flat_and_fit(self):
        self.assertEqual(P.lay_flat((20, 300, 100)), (300, 100, 20))
        self.assertTrue(P.fits((170, 20, 170), P.by_key("a1mini")["bed"]))
        self.assertFalse(P.fits((175, 20, 175), P.by_key("a1mini")["bed"]))
        self.assertEqual(P.smallest((100, 100, 10))["key"], "a1mini")
        self.assertEqual(P.smallest((240, 200, 10))["key"], "a1")
        self.assertIn(P.smallest((320, 300, 10))["key"], ("h2s", "h2d"))
        self.assertIsNone(P.smallest((400, 50, 50)))

    def test_turned_90_when_modelled(self):
        self.assertTrue(P.fits((60, 240, 30), (256, 256, 256), flat=False))
        self.assertFalse(P.fits((10, 10, 300), (256, 256, 256), flat=False))


class TestCheck(unittest.TestCase):
    def test_all_met(self):
        rows = A.check(B.brief(DESK), good_facts())
        self.assertEqual(A.score(rows), (len(rows), len(rows)), rows)

    def test_each_miss_is_found(self):
        b = B.brief(DESK)
        f = good_facts()
        f["modules"] = [m for m in f["modules"] if m["module"] != "speaker"]
        self.assertEqual(state(A.check(b, f), "module:speaker"), A.NOT_MET)
        f = good_facts()
        f["whole_mm"] = [80, 140, 30]
        self.assertEqual(state(A.check(b, f), "size"), A.NOT_MET)
        f = good_facts()
        f["check"] = "fail"
        self.assertEqual(state(A.check(b, f), "checked"), A.NOT_MET)
        f = good_facts()
        f["electrical_errors"] = 2
        self.assertEqual(state(A.check(b, f), "electrical"), A.NOT_MET)
        f = good_facts()
        f["code"] = "if (btn.wasPressed()) { spk.playNote(440, 200); }"
        rows = A.check(b, f)
        self.assertEqual(state(rows, "firmware"), A.NOT_MET)
        self.assertIn("led", [r for r in rows if r["id"] == "firmware"][0]["detail"])
        f = good_facts()
        f["colours"] = ["white"]
        self.assertEqual(state(A.check(b, f), "colours"), A.NOT_MET)
        f = good_facts()
        f["parts"] = [{"label": "Huge", "size_mm": [400, 400, 20]}]
        self.assertEqual(state(A.check(b, f), "printable"), A.NOT_MET)

    def test_size_turned_any_way(self):
        self.assertTrue(A.size_ok([120, 75, 30], [30, 75, 120]))
        self.assertFalse(A.size_ok([None, None, 150], [10, 10, 160]))
        self.assertTrue(A.size_ok([None, None, 150], [500, 10, 150.5]))

    def test_unknown_is_never_guessed(self):
        rows = A.check(B.brief(DESK), {})
        self.assertTrue(all(r["state"] == A.UNKNOWN for r in rows), rows)

    def test_without_and_print_only(self):
        b = B.brief("a weather station without a screen, with a light")
        f = {"modules": [{"module": "light"}, {"module": "screen"}, {"module": "usbc"}]}
        self.assertEqual(state(A.check(b, f), "without:screen"), A.NOT_MET)
        b = B.brief("a phone stand")
        self.assertEqual(state(A.check(b, {"modules": []}), "print_only"), A.MET)
        self.assertEqual(state(A.check(b, {"modules": [{"module": "button"}]}), "print_only"),
                         A.NOT_MET)

    def test_firmware_without_driver_is_unknown(self):
        b = B.brief("a plant pot with a soil sensor; it beeps when the plant needs water")
        f = {"code": "spk.playNote(440, 100);"}
        self.assertEqual(state(A.check(b, f), "firmware"), A.UNKNOWN)

    def test_lines_and_markdown(self):
        b = B.brief(DESK)
        f = good_facts()
        f["whole_mm"] = [80, 140, 30]
        ls = A.lines(A.check(b, f))
        self.assertTrue(ls[0].startswith("BRIEF 10 of 11 criteria met; not met: 1"), ls)
        self.assertIn("not met: Fits in 120 x 75 x 30 mm - is 80 x 140 x 30 mm", ls[1])
        md = A.markdown(A.check(b, f))
        self.assertIn("| Fits in 120 x 75 x 30 mm | **no** |", md)

    def test_code_uses(self):
        self.assertTrue(A.code_uses("btn.wasPressed()", "btn"))
        self.assertTrue(A.code_uses("if (btn2.isPressed())", "btn"))
        self.assertFalse(A.code_uses("// a button", "btn"))
        self.assertTrue(A.code_uses("if (millis() - t > 1000)", "millis"))

    def test_facts_from_check(self):
        res = {"objects": [{"label": "Case", "size": [70, 110, 20]}, {"label": "X",
                                                                       "error": "bad"}],
               "atech": {"modules": [{"module": "button", "ports": [3]}]},
               "whole_size": [70, 110, 28], "problems": []}
        f = A.facts_from_check(res, None, 0)
        self.assertEqual(f["parts"], [{"label": "Case", "size_mm": [70, 110, 20]}])
        self.assertEqual(f["check"], "pass")
        self.assertEqual(f["modules"][0]["module"], "button")


try:
    import test_agent_kit as tak
    FC = tak.FC
    PROJECTS = tak.PROJECTS
except Exception:                                                 # noqa: BLE001
    FC = PROJECTS = None


@unittest.skipIf(FC is None, "freecadcmd not found")
class TestCheckBriefLines(unittest.TestCase):
    """./check on the motion light example with a brief beside it prints
    the BRIEF lines; with no brief, none."""

    def run_check(self, brief):
        ws = tempfile.mkdtemp(prefix="atech-r1110-")
        try:
            shutil.copy(os.path.join(KIT, "examples", "motion_light.py"),
                        os.path.join(ws, "model.py"))
            if brief:
                B.save(brief, ws)
            artifacts = os.environ.get("ATECH_ARTIFACTS") or os.path.normpath(
                os.path.join(ADDON, "..", "..", "models"))
            env = dict(os.environ, ATECH_CHECK_SCRIPT=os.path.join(ws, "model.py"),
                       ATECH_CHECK_PNG="", ATECH_CHECK_PATH=PROJECTS,
                       ATECH_ARTIFACTS=artifacts)
            p = subprocess.run([FC, os.path.join(KIT, "check.py")], env=env,
                               capture_output=True, text=True, timeout=900, cwd=ws)
            return p.stdout + p.stderr
        finally:
            shutil.rmtree(ws, ignore_errors=True)

    def test_brief_lines(self):
        out = self.run_check(B.brief("a night light that turns on when someone walks by, "
                                     "with a screen"))
        lines = [ln for ln in out.splitlines() if ln.startswith("BRIEF")]
        self.assertTrue(lines, out[-3000:])
        self.assertIn("criteria met", lines[0])
        self.assertTrue(any("not met: Has a screen" in ln for ln in lines), lines)
        out = self.run_check(None)
        self.assertFalse([ln for ln in out.splitlines() if ln.startswith("BRIEF")])


if __name__ == "__main__":
    unittest.main()
