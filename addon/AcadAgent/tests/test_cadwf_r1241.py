"""R1240: the Fit test window, fit_view.FitDialog (docs/CAD_WORKFLOW_MERGE.md).

    cd addon/AcadAgent/tests && QT_QPA_PLATFORM=offscreen python3 -m unittest test_cadwf_r1241

Offscreen Qt: the window stores the snug puck and the tightest window for
the printer and filament in its fields, shows what is stored, forgets one
printer's results, and is reachable from the Export and share menu.
Skips without PySide6.
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
for p in (ADDON, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6 import QtWidgets
    APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    from acadagent import fit_view
    HAVE_QT = True
except Exception:                                                 # noqa: BLE001
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "PySide6 not available")
class Window(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = self._tmp.name
        self._env = os.environ.pop("ATECH_FIT_USER", None)

    def tearDown(self):
        if self._env is not None:
            os.environ["ATECH_FIT_USER"] = self._env
        self._tmp.cleanup()

    def _file(self):
        with open(os.path.join(self.home, "fit_user.json")) as fh:
            return json.load(fh)

    def test_save_the_puck_and_the_window(self):
        d = fit_view.FitDialog(home=self.home)
        self.assertIn("No results yet", d.now.text())
        got = []
        d.saved.connect(got.append)
        d.set(printer="Bambu X1C", material="PETG", puck="35", window="4")
        line = d.save()
        self.assertEqual(got, [line])
        self.assertIn("Bambu X1C | PETG", line)
        data = self._file()
        self.assertEqual(data["active"], "Bambu X1C | PETG")
        vals = data["profiles"]["Bambu X1C | PETG"]["values"]
        self.assertEqual(vals["dbore_d3"]["value"], [3.5, 3.0])
        self.assertEqual(vals["slide"]["value"], 0.4)
        self.assertIn("3.5 / 3", d.now.text())
        self.assertIn("the app's value: 3.4 / 2.9", d.now.text())
        self.assertEqual(d.error.text(), "")

    def test_nothing_chosen_saves_nothing(self):
        d = fit_view.FitDialog(home=self.home)
        d.set(printer="X1C", material="PLA")
        self.assertIsNone(d.save())
        self.assertIn("nothing to save", d.error.text())
        self.assertFalse(os.path.exists(os.path.join(self.home, "fit_user.json")))

    def test_a_second_window_shows_what_is_stored(self):
        d = fit_view.FitDialog(home=self.home)
        d.set(printer="X1C", material="PLA", puck="33")
        d.save()
        again = fit_view.FitDialog(home=self.home)
        self.assertEqual(again.printer.text(), "X1C")
        self.assertEqual(again.material.currentText(), "PLA")
        self.assertIn("3.3 / 2.8", again.now.text())
        # another filament on the same printer has no results yet
        again.set(material="PETG")
        self.assertIn("No results yet", again.now.text())

    def test_forget_one_printer(self):
        d = fit_view.FitDialog(home=self.home)
        d.set(printer="X1C", material="PLA", puck="35")
        d.save()
        d.set(printer="H2S", material="PETG", window="2")
        d.save()
        d.set(printer="X1C", material="PLA")
        d.forget()
        data = self._file()
        self.assertEqual(sorted(data["profiles"]), ["H2S | PETG"])
        self.assertEqual(data["active"], "H2S | PETG")
        self.assertIn("No results yet", d.now.text())

    def test_material_from_a_bambu_preset_name(self):
        self.assertEqual(fit_view.material_of("Bambu PETG-CF @BBL H2S"), "PETG-CF")
        self.assertEqual(fit_view.material_of("Bambu PLA Basic @BBL X1C"), "PLA")
        self.assertEqual(fit_view.material_of("Generic PETG"), "PETG")
        self.assertEqual(fit_view.material_of(None), "")

    def test_in_the_export_menu(self):
        with open(os.path.join(ADDON, "acadagent", "shell.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn('("Atech_FitTest", "Fit test\\u2026"', src)
        self.assertIn('if key == "fittest":', src)
        self.assertIn("fit_view.FitDialog(parent)", src)


if __name__ == "__main__":
    unittest.main()
