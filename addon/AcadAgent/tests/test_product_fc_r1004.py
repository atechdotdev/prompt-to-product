"""R1004: fc_product_r1004.py under freecadcmd (ATECH_FREECADCMD): Make it
and the product pack on real example builds (3MF, STEP, PDFs). Skips
without freecadcmd or the module library."""
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
class MakeItOnExamples(unittest.TestCase):
    def test_fc_product(self):
        env = dict(os.environ, ATECH_ARTIFACTS=MODELS, QT_QPA_PLATFORM="offscreen",
                   ATECH_SDK_CATALOG="snapshot", ATECH_NO_REVEAL="1")
        out = subprocess.run([FC, os.path.join(HERE, "fc_product_r1004.py")], env=env,
                             capture_output=True, text=True, timeout=1800).stdout
        fails = [ln for ln in out.splitlines() if ln.startswith("CHECK ") and " FAIL " in ln]
        self.assertEqual(fails, [], out[-3000:])
        m = re.search(r"R1004_TESTS=(\d+)", out)
        self.assertTrue(m and m.group(1) == "0", out[-3000:])
        self.assertGreaterEqual(out.count(" PASS "), 20, out[-3000:])


if __name__ == "__main__":
    unittest.main()
