"""The port rules of the 14-port board: port 8 takes only the USB-C module
and the USB-C module goes only on port 8; port 12, the reset port, takes
only a button.

The pure rule (atech_wiring.port_rule, the table the electrical checks use)
is tested here directly. The library's enforcement runs fc_port_rules.py
under freecadcmd and skips without it (set ATECH_FREECADCMD).
"""
import os
import re
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(os.path.dirname(HERE), "acadagent", "agent_kit")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, KIT)

import atech_wiring as aw  # noqa: E402


def _freecadcmd():
    env = os.environ.get("ATECH_FREECADCMD")
    if env and os.path.isfile(env):
        return env
    p = os.path.join(REPO, "dist", "build", "squashfs-root", "usr", "bin", "freecadcmd")
    if os.path.isfile(p):
        return p
    return shutil.which("freecadcmd")


FC = _freecadcmd()


class PureRule(unittest.TestCase):
    def test_port_8_is_usbc_only(self):
        self.assertIsNone(aw.port_rule("usbc", 8))
        for m in ("light", "button", "distance_sensor"):
            self.assertIn("Port 8 is the USB-C port", aw.port_rule(m, 8))

    def test_usbc_goes_on_8_only(self):
        for n in (1, 7, 12, 14):
            self.assertIn("port 8 only", aw.port_rule("usbc", n))

    def test_port_12_is_a_button_only(self):
        self.assertIsNone(aw.port_rule("button", 12))
        self.assertIn("reset port", aw.port_rule("speaker", [11, 12]))
        self.assertIn("reset port", aw.port_rule("camera", (11, 12)))
        self.assertTrue(aw.is_reset_button("button", [12]))
        self.assertFalse(aw.is_reset_button("button", [3]))

    def test_other_ports_take_any_other_module(self):
        for n in (1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 13, 14):
            self.assertIsNone(aw.port_rule("light", n))
        self.assertIsNone(aw.port_rule("screen", (10, 11)))


@unittest.skipIf(FC is None, "freecadcmd not found (set ATECH_FREECADCMD)")
class InFreeCAD(unittest.TestCase):
    def test_library_enforces_the_rules(self):
        env = dict(os.environ, ATECH_ARTIFACTS=os.path.join(REPO, "models"),
                   QT_QPA_PLATFORM="offscreen")
        out = subprocess.run([FC, os.path.join(HERE, "fc_port_rules.py")], env=env,
                             cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             timeout=600).stdout.decode("utf-8", "replace")
        checks = dict(re.findall(r"^CHECK (\S+) (PASS|FAIL)", out, re.M))
        m = re.search(r"^PORT_RULES_TESTS=(\d+)", out, re.M)
        self.assertGreaterEqual(len(checks), 14, out[-3000:])
        self.assertEqual([k for k, v in checks.items() if v != "PASS"], [], out[-3000:])
        self.assertIsNotNone(m, out[-3000:])
        self.assertEqual(int(m.group(1)), 0)


if __name__ == "__main__":
    unittest.main()
