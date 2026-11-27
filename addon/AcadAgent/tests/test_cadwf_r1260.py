"""R1260: the fit of every shaft in a bore, in ./check
(docs/CAD_WORKFLOW_MERGE.md).

    cd addon/AcadAgent/tests && python3 -m unittest test_cadwf_r1260

What is pinned:
  - fc_cadwf_r1260.py under freecadcmd: a 3 mm pin in 3.0, 3.3 and 3.6
    holes is interference, transition and running once the hole has
    shrunk; a DC motor's shaft in the printed D-bore, in round bores and
    in a hole it does not touch; the sabotage must be noticed
  - a real ./check of the "Two-wheel base" starter, with the real DC
    Motor modules from the library: its wheels push onto the shafts with
    the D-bore that printed (3.4 / 2.9), and the same starter with the
    round 3.3 bore it had until R1260 gets the WARNING

The FreeCAD classes skip when freecadcmd or the module library is missing.
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
REPO = os.path.normpath(os.path.join(ADDON, "..", ".."))
sys.path.insert(0, ADDON)

from acadagent import sandbox  # noqa: E402

KIT = sandbox.KIT_DIR
PROJECTS = os.path.join(REPO, "projects")
STARTER = os.path.join(KIT, "starters", "starter_wheels.py")
FC = sandbox.find_freecadcmd()
if FC is None and os.environ.get("ATECH_REQUIRE_FREECADCMD") == "1":
    raise RuntimeError("ATECH_REQUIRE_FREECADCMD=1 but no freecadcmd was found "
                       "(set ATECH_FREECADCMD)")
#: the module library: $ATECH_ARTIFACTS, else this checkout's own models/
LIBRARY = os.environ.get("ATECH_ARTIFACTS") or (
    REPO if os.path.isfile(os.path.join(REPO, "models", "presets.yaml")) else None)


def fc(env=None, timeout=600):
    e = dict(os.environ, **(env or {}))
    p = subprocess.run([FC, os.path.join(HERE, "fc_cadwf_r1260.py")], env=e,
                       capture_output=True, text=True, timeout=timeout,
                       cwd=tempfile.gettempdir())
    return p.stdout + p.stderr


def failures(text):
    for line in reversed(text.splitlines()):
        if line.startswith("ATECH_CADWF_R1260="):
            return int(line.split("=", 1)[1])
    return None


def check_starter(code):
    """./check on `code` as model.py with the library; (result, output)."""
    ws = tempfile.mkdtemp(prefix="atech-r1260-")
    try:
        with open(os.path.join(ws, "model.py"), "w", encoding="utf-8") as fh:
            fh.write(code)
        with open(os.path.join(ws, "intent.json"), "w", encoding="utf-8") as fh:
            json.dump({"board": "flat", "fitted_after": [
                "Cover", "Screw_1", "Screw_2", "Screw_3", "Screw_4",
                "Tyre_L", "Rim_L", "Tyre_R", "Rim_R"]}, fh)
        env = dict(os.environ, ATECH_CHECK_SCRIPT=os.path.join(ws, "model.py"),
                   ATECH_CHECK_PNG="", ATECH_CHECK_PATH=PROJECTS, ATECH_ARTIFACTS=LIBRARY,
                   ATECH_CHECK_TIMEOUT="300")
        env.pop("ATECH_FIT_USER", None)
        p = subprocess.run([FC, os.path.join(KIT, "check.py")], env=env, cwd=ws,
                           capture_output=True, text=True, timeout=900)
        out = p.stdout + p.stderr
        res = None
        for line in reversed(out.splitlines()):
            if line.startswith("ATECH_CHECK="):
                res = json.loads(line[len("ATECH_CHECK="):])
                break
        return res, out
    finally:
        shutil.rmtree(ws, ignore_errors=True)


@unittest.skipIf(FC is None, "bundled freecadcmd not found")
class Geometry(unittest.TestCase):

    def test_fits(self):
        out = fc()
        self.assertEqual(failures(out), 0, out[-3000:])
        self.assertGreaterEqual(out.count("\nPASS "), 20)

    def test_sabotage_is_noticed(self):
        out = fc({"ATECH_CADWF_SABOTAGE": "noshrink"})
        self.assertTrue(failures(out), "a hole shrink of 0 went unnoticed")


@unittest.skipIf(FC is None, "bundled freecadcmd not found")
@unittest.skipIf(LIBRARY is None, "the Atech module library was not found")
class TwoWheelBase(unittest.TestCase):
    """The real modules, the real check."""

    @classmethod
    def setUpClass(cls):
        with open(STARTER, encoding="utf-8") as fh:
            cls.code = fh.read()

    def test_the_starter_pushes_onto_the_shafts_with_the_printed_d_bore(self):
        self.assertIn('flat=s["flat"]', self.code)
        res, out = check_starter(self.code)
        self.assertIsNotNone(res, out[-3000:])
        rows = (res.get("fits") or {}).get("motors") or []
        on_shaft = [r for r in rows if r["kind"] == "dbore"]
        self.assertEqual(sorted(r["part"] for r in on_shaft), ["Rim_L", "Rim_R"], rows)
        for r in on_shaft:
            self.assertEqual((r["hole_d"], r["across"], r["level"]), (3.4, 2.9, "info"), r)
            # the wheel centre 1.33 past the shaft tip: 4.5 mm of shaft in the
            # hub, 4.05 of it past the bore's 0.5 lead-in cone
            self.assertAlmostEqual(r["engaged_mm"], 4.05, delta=0.2)
        lines = [ln for ln in out.splitlines()
                 if ln.startswith("FIT Rim_") and "on the shaft" in ln]
        self.assertEqual(len(lines), 2, out[-3000:])
        self.assertIn("D-bore 3.4 / 2.9, the push fit that printed", lines[0])
        self.assertNotIn("ROUND", out)
        # the cover's shaft slots are wider than the shaft: not a fit
        self.assertFalse([r for r in rows if r["level"] != "info"], rows)
        verdict = [ln for ln in out.splitlines() if ln.startswith("CHECK ")]
        self.assertEqual(verdict[-1], "CHECK PASS", out[-3000:])

    def test_the_round_bore_it_had_gets_the_warning(self):
        old = self.code.replace('flat=s["flat"],', "bore=3.3,")
        self.assertNotEqual(old, self.code)
        res, out = check_starter(old)
        self.assertIsNotNone(res, out[-3000:])
        rows = (res.get("fits") or {}).get("motors") or []
        bad = [r for r in rows if r["level"] == "warning"]
        self.assertEqual(sorted(r["part"] for r in bad), ["Rim_L", "Rim_R"], rows)
        warn = [ln for ln in out.splitlines()
                if ln.startswith("WARNING Rim_") and "ROUND" in ln]
        self.assertEqual(len(warn), 2, out[-3000:])
        self.assertIn("ROUND 3.3 bore", warn[0])
        self.assertIn("cad.motor_shaft(motor)", warn[0])
        # a warning, never a failure
        self.assertNotIn("ROUND", "\n".join(ln for ln in out.splitlines()
                                            if ln.startswith(("PROBLEM", "CHECK FAIL"))))


if __name__ == "__main__":
    unittest.main()
