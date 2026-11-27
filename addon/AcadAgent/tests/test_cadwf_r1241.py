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
        # what Bambu Studio is said to have selected (the machine the tests
        # run on may have its own)
        self.loaded = ("", "")
        self._loaded = fit_view.loaded_filament
        fit_view.loaded_filament = lambda: self.loaded

    def tearDown(self):
        fit_view.loaded_filament = self._loaded
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
        self.assertIn("No results yet", d.now.text())
        # H2S | PETG was saved last and stays the one in use
        self.assertEqual(data["active"], "H2S | PETG")

    def test_forgetting_the_one_in_use_does_not_put_another_in_its_place(self):
        """R1295 review: Forget made the alphabetically first other
        profile active, so another printer's numbers were drawn without
        anybody choosing them."""
        d = fit_view.FitDialog(home=self.home)
        d.set(printer="A1", material="PETG", window="2")
        d.save()
        d.set(printer="X1C", material="PLA", puck="35")
        d.save()                                    # in use: X1C | PLA
        d.forget()
        data = self._file()
        self.assertEqual(sorted(data["profiles"]), ["A1 | PETG"])
        self.assertIsNone(data["active"])
        self.assertIn("Forgotten: X1C | PLA.", d.error.text())
        self.assertIn("The next design uses the app's own values.", d.error.text())

    def test_too_tight_by_about(self):
        """R1295 review: the "how did it fit" verdict had no way in."""
        d = fit_view.FitDialog(home=self.home)
        self.assertGreater(d.what.count(), 5)
        self.assertEqual([d.how.itemData(i) for i in range(d.how.count())],
                         ["", "fits", "tight", "loose"])
        d.set(printer="X1C", material="PLA", what="lip_loose", how="tight", by=0.05)
        line = d.save()
        self.assertIsNotNone(line, d.error.text())
        rec = self._file()["profiles"]["X1C | PLA"]["values"]["lip_loose"]
        self.assertEqual(rec["value"], 0.25)
        self.assertIn("too tight by about 0.05", rec["note"])
        # said once: a second Save does not open it again
        self.assertEqual(d.how.currentData(), "")
        self.assertIsNone(d.save())
        self.assertEqual(self._file()["profiles"]["X1C | PLA"]["values"]["lip_loose"]["value"],
                         0.25)

    def test_a_refused_value_stores_nothing(self):
        d = fit_view.FitDialog(home=self.home)
        real = d.L.verdict

        def refuse(*a, **k):
            raise ValueError("no")
        d.L.verdict = refuse
        try:
            d.set(printer="X1C", material="PLA", window="4", what="preload", how="tight", by=0.1)
            self.assertIsNone(d.save())
        finally:
            d.L.verdict = real
        self.assertIn("Not saved", d.error.text())
        self.assertFalse(os.path.exists(os.path.join(self.home, "fit_user.json"))
                         and self._file()["profiles"])
        self.assertEqual(d.data["profiles"], {})

    def test_a_clearance_stops_at_zero_and_the_rest_is_saved(self):
        # second review: "too loose" by more than the value was refused,
        # and the puck chosen in the same Save was lost with it
        d = fit_view.FitDialog(home=self.home)
        d.set(printer="X1C", material="PLA", puck="35", what="stop", how="loose", by=0.25)
        self.assertIsNotNone(d.save(), d.error.text())
        vals = self._file()["profiles"]["X1C | PLA"]["values"]
        self.assertEqual(vals["stop"]["value"], 0.0)
        self.assertIn("kept at 0", vals["stop"]["note"])
        self.assertEqual(vals["dbore_d3"]["value"], [3.5, 3.0])

    def test_each_result_is_said_once(self):
        # second review: the puck stayed selected, so the next Save worked
        # the turning hole out again and undid a verdict given in between
        d = fit_view.FitDialog(home=self.home)
        d.set(printer="X1C", material="PLA", puck="35", window="4")
        d.save()
        self.assertEqual((d.puck.currentData(), d.window.currentData(), d.how.currentData()),
                         ("", "", ""))
        d.set(what="bearing_d3", how="tight", by=0.1)
        d.save()
        d.set(window="3")
        d.save()
        vals = self._file()["profiles"]["X1C | PLA"]["values"]
        self.assertEqual(vals["bearing_d3"]["value"], 3.7)
        self.assertEqual(vals["slide"]["value"], 0.3)

    def test_the_window_says_whose_results_the_next_design_uses(self):
        """Second review: Forget said "the app's own values are used"
        while the next build used another printer's results for the same
        filament."""
        d = fit_view.FitDialog(home=self.home)
        self.assertIn("The next design uses the app's own values.", d.now.text())
        d.set(printer="X1C", material="PLA", window="4")
        d.save()
        self.assertIn("The next design uses X1C | PLA.", d.now.text())
        d.set(printer="Bambu Lab H2S", material="PLA", window="2")
        d.save()
        self.loaded = ("Bambu Lab H2S", "PLA")
        d.forget()
        said = d.error.text()
        self.assertIn("Forgotten: Bambu Lab H2S | PLA.", said)
        self.assertIn("The next design uses X1C | PLA (Bambu Studio has PLA selected).", said)
        self.assertNotIn("app's own values", said)
        self.loaded = ("Bambu Lab H2S", "PETG")
        self.assertIn("none of your results is for PETG", d.next_use())
        # typed in small letters, it is the same profile
        self.loaded = ("", "")
        d.set(printer="x1c", material="pla")
        self.assertIn("clearance per side round hardware", d.now.text())   # the stored row
        d.forget()
        self.assertEqual(self._file()["profiles"], {})
        d.forget()
        self.assertIn("Nothing is stored for", d.error.text())

    def test_the_labels_are_the_coupons_dots(self):
        d = fit_view.FitDialog(home=self.home)
        pucks = [d.puck.itemText(i) for i in range(1, d.puck.count())]
        self.assertEqual(pucks[0], "2 dots (3.2 mm)")
        self.assertEqual(pucks[-1], "6 dots (3.6 mm)")
        wins = [d.window.itemText(i) for i in range(1, d.window.count())]
        self.assertEqual(wins, ["2 dots (0.2 mm each side)", "3 dots (0.3 mm each side)",
                                "4 dots (0.4 mm each side)"])

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
