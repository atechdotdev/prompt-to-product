"""R1001: running the Atech SDK CLI from the app (acadagent/sdk_tools.py).

Pure except TestRunner, which runs a fake `atech` (a /bin/sh script)
through QProcess when PySide6 is there.

    python -m unittest test_sdk_tools_r1001
"""
import os
import stat
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
if ADDON not in sys.path:
    sys.path.insert(0, ADDON)

from acadagent import sdk_tools as S  # noqa: E402

YAML = ("name: demo\nboard: 14port\nmodules:\n  - {id: button, instance: btn, port: 1}\n"
        "code:\n  setup: |\n    // runs once\n  loop: |\n    // forever\n")
FAKE = """#!/bin/sh
echo "fake atech $*"
case "$1" in
  validate) echo "OK: 1 module"; exit 0;;
  upload) echo "no serial port found" ; exit 2;;
  *) exit 0;;
esac
"""


def fake_exe(folder):
    p = os.path.join(folder, "atech")
    with open(p, "w") as fh:
        fh.write(FAKE)
    os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)
    return p


class TestPure(unittest.TestCase):
    def test_argv(self):
        self.assertEqual(S.argv("validate", "/x/fw", exe="/bin/atech"),
                         ["/bin/atech", "validate", "/x/fw"])
        self.assertEqual(S.argv("upload", "/x/fw", exe="atech", port="/dev/cu.usb1"),
                         ["atech", "upload", "/x/fw", "--port", "/dev/cu.usb1"])
        self.assertEqual(S.argv("emulate", "/f", exe="a")[:3], ["a", "emulate", "/f"])
        self.assertEqual(S.argv("check", "/f", exe="a"), ["a", "check"])
        with self.assertRaises(KeyError):
            S.argv("rm", "/f")

    def test_order_covers_commands(self):
        self.assertTrue(set(S.ORDER) <= set(S.COMMANDS))
        for k in S.ORDER:
            words, _args, board, what = S.COMMANDS[k]
            self.assertTrue(words and what)
        self.assertFalse(S.COMMANDS["emulate"][2])     # no board needed
        self.assertTrue(S.COMMANDS["upload"][2])

    def test_folders(self):
        self.assertEqual(S.safe_folder("Desk buddy: v2/../x"), "Desk buddy v2x")
        self.assertEqual(S.safe_folder("***"), "Product")
        d = S.firmware_dir("Desk buddy", root="/tmp/p")
        self.assertEqual(d, os.path.join("/tmp/p", "Desk buddy", "firmware"))

    def test_write_keeps_code(self):
        with tempfile.TemporaryDirectory() as d:
            p = S.write_firmware(d, YAML)
            with open(p) as fh:
                self.assertEqual(fh.read(), YAML)
            mine = YAML.replace("// forever", "if (btn.wasPressed()) {}")
            with open(p, "w") as fh:
                fh.write(mine)
            new = YAML.replace("port: 1}", "port: 2}")
            S.write_firmware(d, new)
            with open(p) as fh:
                got = fh.read()
            self.assertIn("port: 2}", got)                  # modules from the design
            self.assertIn("btn.wasPressed()", got)          # the code kept
            S.write_firmware(d, new, keep_code=False)
            with open(p) as fh:
                self.assertNotIn("wasPressed", fh.read())

    def test_find_explicit(self):
        with tempfile.TemporaryDirectory() as d:
            exe = fake_exe(d)
            self.assertEqual(S.find(exe), exe)
            self.assertIsNone(S.find(os.path.join(d, "missing")))

    def test_summaries(self):
        self.assertEqual(S.summarise("build", 0, ""), "Firmware built.")
        self.assertIn("No board found", S.summarise("upload", 2, "no serial port found"))
        self.assertIn("PlatformIO", S.summarise("build", 1, "PlatformIO not found"))
        self.assertIn("code 3", S.summarise("build", 3, "boom"))
        self.assertEqual(S.summarise("emulate", 1, "x\nerror: port 'port_12' not found on board '14port'"),
                         "The Atech SDK stopped: port 'port_12' not found on board '14port'. "
                         "The Overview page has the fix.")
        self.assertEqual(S.summarise("emulate", 0, "boot report: POWERON; btn ok"),
                         "Ran on the emulated board: POWERON; btn ok")

    def test_child_env_drops_bundle_python(self):
        os.environ["PYTHONHOME"] = "/x"
        try:
            self.assertNotIn("PYTHONHOME", S.child_env())
        finally:
            os.environ.pop("PYTHONHOME", None)


try:
    from PySide6 import QtCore, QtWidgets
    APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
except ImportError:                                     # pragma: no cover
    QtCore = None


@unittest.skipIf(QtCore is None, "PySide6 not installed")
class TestRunner(unittest.TestCase):
    def run_one(self, key, folder, exe):
        r = S.make_runner()
        lines, done = [], []
        r.line.connect(lines.append)
        r.finished.connect(lambda k, c, s: done.append((k, c, s)))
        self.assertTrue(r.start(key, folder, exe=exe))
        loop = QtCore.QEventLoop()
        r.finished.connect(lambda *a: loop.quit())
        QtCore.QTimer.singleShot(5000, loop.quit)
        if not done:
            loop.exec()
        return lines, done

    def test_validate_and_upload(self):
        with tempfile.TemporaryDirectory() as d:
            exe = fake_exe(d)
            lines, done = self.run_one("validate", d, exe)
            self.assertEqual(done[0][:2], ("validate", 0))
            self.assertIn("OK: 1 module", lines)
            self.assertEqual(lines[0], "$ atech validate " + d)
            lines, done = self.run_one("upload", d, exe)
            self.assertEqual(done[0][1], 2)
            self.assertIn("No board found", done[0][2])

    def test_missing_program(self):
        with tempfile.TemporaryDirectory() as d:
            lines, done = self.run_one("validate", d, os.path.join(d, "nope"))
            self.assertEqual(done[0][1], 127)
            self.assertIn(S.INSTALL_COMMAND, done[0][2])


if __name__ == "__main__":
    unittest.main()
