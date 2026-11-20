"""R1140 the brief's behaviours become firmware (agent_kit/p2p_behave.py).

    cd addon/AcadAgent/tests && ATECH_SDK_CATALOG=snapshot python3 -m unittest test_p2p_r1140
    ATECH_SDK_BIN=~/dev/atech/python-sdk/.venv/bin   # + a real `atech build` (~20 s)
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
for p in (ADDON, KIT):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("ATECH_SDK_CATALOG", "snapshot")

import atech_firmware as F                                     # noqa: E402
import p2p_accept as A                                         # noqa: E402
import p2p_behave as H                                         # noqa: E402
import p2p_brief as B                                          # noqa: E402

PROMPT = ("A desk buddy with a button that plays a tune, and a light that glows red when "
          "it is too hot. When the knob is turned, the screen shows the temperature. "
          "Every 10 minutes it beeps. If it is shaken the motor spins. When it is closer "
          "than 20 cm the light turns blue. It chimes every hour.")
SEATED = [{"module": "button", "ports": [1]}, {"module": "light", "ports": [2]},
          {"module": "speaker", "ports": [3, 4]}, {"module": "temp_humidity", "ports": [14]},
          {"module": "knob", "ports": [5, 6]}, {"module": "screen", "ports": [10, 11]},
          {"module": "orientation", "ports": [7]}, {"module": "dc_motor", "ports": [13]},
          {"module": "distance_sensor", "ports": [9]}, {"module": "usbc", "ports": [8]}]


def sdk_bin():
    for d in (os.environ.get("ATECH_SDK_BIN"),
              os.path.expanduser("~/dev/atech/python-sdk/.venv/bin")):
        if d and os.path.isfile(os.path.join(d, "atech")):
            return d
    return None


class TestThresholds(unittest.TestCase):
    def test_numbers(self):
        self.assertEqual(H.threshold("it is above 30 degrees", "hot"), (30.0, False))
        self.assertEqual(H.threshold("it is too hot", "hot"), (28.0, True))
        self.assertEqual(H.threshold("closer than 20 cm", "close"), (200.0, False))
        self.assertEqual(H.threshold("within 0.5 m", "close"), (500.0, False))
        self.assertEqual(H.threshold("over 86 F", "hot"), (30.0, False))
        # the 2 in "co2" is a name, not the threshold
        self.assertEqual(H.threshold("the co2 is above 1200 ppm", "co2"), (1200.0, False))
        self.assertEqual(H.threshold("the co2 is high", "co2"), (1000.0, True))


class TestCode(unittest.TestCase):
    def setUp(self):
        self.b = B.brief(PROMPT)
        self.entries = F.plan(SEATED)

    def test_every_behaviour_is_written(self):
        self.assertEqual(len(self.b["behaviours"]), 7)
        y, c = H.project("desk_buddy", self.entries, self.b["behaviours"])
        self.assertEqual(len(c["rules"]), 7)
        self.assertEqual(c["unsupported"], [])
        self.assertTrue(any("tune it" in n for n in c["notes"]), "guessed values are named")

    def test_sdk_rules(self):
        y, c = H.project("desk_buddy", self.entries, self.b["behaviours"])
        self.assertNotIn("delay(", c["loop"])
        self.assertIn("knob.update();", c["loop"])
        self.assertLess(c["loop"].index("knob.update();"), c["loop"].index("knob.wasRotated"))
        for ln in c["loop"].splitlines():
            if "led.setAll" in ln:
                break
        self.assertIn("led.show();", c["loop"])
        self.assertNotIn("spk.", c["setup"], "never play on boot")
        # the slow screen is drawn on edges only
        self.assertIn("screen.display();", c["loop"])

    def test_lints_clean_and_compares(self):
        y, _c = H.project("desk_buddy", self.entries, self.b["behaviours"])
        d = tempfile.mkdtemp()
        try:
            p = os.path.join(d, "project.yaml")
            with open(p, "w") as fh:
                fh.write(y)
            proj = F.read_project(p)
            self.assertEqual(F.lint_code(proj), [])
            self.assertEqual(F.issues(self.entries), [])
        finally:
            shutil.rmtree(d)

    def test_two_timers_two_clocks(self):
        _y, c = H.project("x", self.entries, self.b["behaviours"])
        self.assertIn("static unsigned long _p2p_t4", c["loop"])
        self.assertIn("static unsigned long _p2p_t7", c["loop"])

    def test_pir_follows_and_clears(self):
        b = B.brief("a night light that turns on when someone walks by")
        e = F.plan([{"module": "light", "ports": [2]}, {"module": "pir", "ports": [5]}])
        _y, c = H.project("n", e, b["behaviours"])
        self.assertIn("pir.update();", c["loop"])
        self.assertIn("pir.isWarmedUp() && pir.wasTriggered()", c["loop"])
        self.assertIn("pir.wasCleared()", c["loop"])

    def test_a_module_the_sdk_dropped(self):
        b = B.brief("a night light that turns on when someone walks by")
        e = F.plan([{"module": "light", "ports": [2]}, {"module": "pir", "ports": [5]}])
        cat = {"modules": {"neopixel": {}}}                   # no pir (SDK after 1.0.0a11)
        _y, c = H.project("n", e, b["behaviours"], cat=cat)
        self.assertEqual(c["rules"], [])
        self.assertEqual(len(c["unsupported"]), 1)
        self.assertNotIn("pir.", c["loop"])

    def test_missing_module_is_unsupported(self):
        b = B.brief("When the button is pressed it beeps")
        e = F.plan([{"module": "button", "ports": [1]}])
        _y, c = H.project("x", e, b["behaviours"])
        self.assertEqual(c["rules"], [])
        self.assertIn("speaker", c["unsupported"][0])

    def test_screen_shows_a_reading_or_quoted_text(self):
        b = B.brief('When the button is pressed, the screen shows "Hi there".')
        e = F.plan([{"module": "button", "ports": [1]}, {"module": "screen", "ports": [10, 11]}])
        _y, c = H.project("x", e, b["behaviours"])
        self.assertIn('"Hi there"', c["loop"])

    def test_acceptance_firmware_is_met(self):
        y, c = H.project("desk_buddy", self.entries, self.b["behaviours"])
        rows = A.check(self.b, {"code": c["setup"] + "\n" + c["loop"]})
        self.assertEqual([r for r in rows if r["id"] == "firmware"][0]["state"], A.MET)


@unittest.skipIf(sdk_bin() is None, "the Atech SDK CLI is not installed")
class TestRealBuild(unittest.TestCase):
    def test_atech_build(self):
        b = B.brief(PROMPT)
        y, _c = H.project("desk_buddy", F.plan(SEATED), b["behaviours"])
        d = tempfile.mkdtemp(prefix="p2p-r1140-")
        try:
            with open(os.path.join(d, "project.yaml"), "w") as fh:
                fh.write(y)
            env = dict(os.environ, PATH=sdk_bin() + os.pathsep + os.environ.get("PATH", ""))
            v = subprocess.run(["atech", "validate", d], env=env, capture_output=True,
                               text=True, timeout=120)
            self.assertEqual(v.returncode, 0, v.stdout + v.stderr)
            r = subprocess.run(["atech", "build", d], env=env, capture_output=True,
                               text=True, timeout=600)
            self.assertEqual(r.returncode, 0, (r.stdout + r.stderr)[-3000:])
            self.assertIn("SUCCESS", r.stdout + r.stderr)
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
