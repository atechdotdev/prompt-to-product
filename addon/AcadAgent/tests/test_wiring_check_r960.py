"""R960: fc_wiring_r960.py under freecadcmd (ATECH_FREECADCMD): the app's
wiring walk equals check.py's _atech_report on five example builds, every
seated port is in the wiring, the robot-arm note shows on arm_dock only, the
port 8 / 12 flags on toy_car and handheld_console, and a cable whose module
moved reads "moved". Skips without freecadcmd or the module library."""
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from test_modules_page_r300 import FC, LIB, MODELS  # noqa: E402


@unittest.skipUnless(FC and LIB, "needs freecadcmd and the Atech module library")
class WiringOnExamples(unittest.TestCase):
    def test_fc_wiring(self):
        env = dict(os.environ, ATECH_ARTIFACTS=MODELS, QT_QPA_PLATFORM="offscreen",
                   ATECH_SDK_CATALOG="snapshot")
        out = subprocess.run([FC, os.path.join(HERE, "fc_wiring_r960.py")], env=env,
                             capture_output=True, text=True, timeout=1800).stdout
        fails = [ln for ln in out.splitlines() if ln.startswith("CHECK ") and " FAIL " in ln]
        self.assertEqual(fails, [], out[-3000:])
        m = re.search(r"R960_TESTS=(\d+)", out)
        self.assertTrue(m and m.group(1) == "0", out[-3000:])
        self.assertGreaterEqual(out.count(" PASS "), 25, out[-3000:])


if __name__ == "__main__":
    unittest.main()
