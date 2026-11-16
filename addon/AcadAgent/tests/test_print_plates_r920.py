"""R920-R924 Print: print plates for a Bambu Lab printer (acadagent/print_plates.py).

    cd addon/AcadAgent/tests
    python3 -m unittest test_print_plates_r920                  # pure parts
    QT_QPA_PLATFORM=offscreen "<bundle>/Contents/Resources/bin/python" \\
        -m unittest test_print_plates_r920                      # + dialog, + slice

The pure parts run on a fake Bambu Studio folder (presets with an
"inherits" chain). The slice test needs the bundled freecadcmd
(ATECH_FREECADCMD) and Bambu Studio in /Applications: two blocks, one too
big to share a bed, must come back as two sliced
plates (no bed holds two 200 mm blocks side by side). Each check has a
sabotage twin.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
sys.path.insert(0, ADDON)

from acadagent import print_plates as pp                      # noqa: E402

BUNDLE = os.path.normpath(os.path.join(
    ADDON, "..", "..", "dist", "build-macos-arm64", "Prompt To Product.app", "Contents",
    "Resources", "bin"))
FC = os.environ.get("ATECH_FREECADCMD") or os.path.join(BUNDLE, "freecadcmd")
FC = FC if os.path.isfile(FC) else None
APP = pp.bambu_studio()


def fake_support(machine="Bambu Lab H2S 0.4 nozzle", conf=True, bed=(340, 320)):
    """A Bambu Studio support folder with one printer's presets."""
    d = tempfile.mkdtemp(prefix="atech-bambu-")
    sysd = os.path.join(d, "system", "BBL")
    for kind in ("machine", "process", "filament"):
        os.makedirs(os.path.join(sysd, kind))

    def put(kind, name, data):
        with open(os.path.join(sysd, kind, name + ".json"), "w") as fh:
            json.dump(dict(data, name=name), fh)
    put("machine", "fdm_common", {"printable_area": ["0x0", "256x0", "256x256", "0x256"],
                                  "printable_height": "250"})
    put("machine", machine, {"inherits": "fdm_common", "printer_model": "Bambu Lab H2S",
                             "printable_area": ["0x0", "%dx0" % bed[0],
                                                "%dx%d" % bed, "0x%d" % bed[1]],
                             "printable_height": "340",
                             "default_print_profile": "0.20mm Standard @BBL H2S",
                             "default_filament_profile": ["Bambu PLA Basic @BBL H2S"]})
    put("process", "0.20mm Standard @BBL H2S", {})
    put("filament", "Bambu PLA Basic @BBL H2S", {"filament_density": ["1.26"]})
    if conf:
        with open(os.path.join(d, "BambuStudio.conf"), "w") as fh:
            json.dump({"presets": {"machine": machine,
                                   "filaments": ["Bambu PLA Basic @BBL H2S"]},
                       "access_code": {"SERIAL": "secret"}}, fh)
    return d


class Profile(unittest.TestCase):
    def setUp(self):
        self.d = fake_support()
        self.addCleanup(shutil.rmtree, self.d, True)

    def test_picked_printer_and_bed(self):
        p = pp.bambu_profile(self.d)
        self.assertEqual(p["machine"], "Bambu Lab H2S 0.4 nozzle")
        self.assertEqual(p["process"], "0.20mm Standard @BBL H2S")
        self.assertEqual(p["filament"], "Bambu PLA Basic @BBL H2S")
        self.assertEqual(p["bed"], (340.0, 320.0, 340.0))      # the child wins
        self.assertAlmostEqual(p["density"], 1.26)
        self.assertTrue(p["picked"])
        self.assertEqual(pp.printer_name(p), "H2S")
        self.assertNotIn("secret", json.dumps(p))

    def test_inherited_bed_when_the_child_has_none(self):
        path = os.path.join(self.d, "system", "BBL", "machine", "Bambu Lab H2S 0.4 nozzle.json")
        with open(path) as fh:
            data = json.load(fh)
        del data["printable_area"]
        with open(path, "w") as fh:
            json.dump(data, fh)
        self.assertEqual(pp.bambu_profile(self.d)["bed"][:2], (256.0, 256.0))

    def test_no_studio_setup(self):
        shutil.rmtree(os.path.join(self.d, "system"))
        self.assertIsNone(pp.bambu_profile(self.d))

    def test_sabotage_unknown_machine_is_not_trusted(self):
        with open(os.path.join(self.d, "BambuStudio.conf"), "w") as fh:
            json.dump({"presets": {"machine": "Some Printer"}}, fh)
        # falls back to DEFAULT_MACHINE, absent here: no profile
        self.assertIsNone(pp.bambu_profile(self.d))


class Plates(unittest.TestCase):
    def test_fits_bed(self):
        bed = (256.0, 256.0, 256.0)
        self.assertEqual(pp.fits_bed((100, 50, 20), bed), (True, False))
        self.assertEqual(pp.fits_bed((250, 30, 20), bed), (False, False))   # margin
        self.assertEqual(pp.fits_bed((300, 100, 10), (340.0, 320.0, 340.0)), (True, False))
        self.assertEqual(pp.fits_bed((200, 320, 10), (340.0, 320.0, 340.0)), (True, True))
        self.assertEqual(pp.fits_bed((50, 50, 300), bed), (False, False))   # too tall

    def test_slice_command(self):
        prof = {"machine_file": "/m.json", "process_file": "/p.json", "filament_file": "/f.json"}
        cmd = pp.slice_command("/Applications/BambuStudio.app", prof, ["a.stl"], "/o", "x.3mf")
        self.assertEqual(cmd[0], "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio")
        self.assertIn("--slice", cmd)
        self.assertEqual(cmd[cmd.index("--arrange") + 1], "1")
        self.assertEqual(cmd[cmd.index("--orient") + 1], "0")    # Prompt To Product laid them flat
        self.assertEqual(cmd[cmd.index("--load-settings") + 1], "/m.json;/p.json")
        self.assertEqual(cmd[-1], "a.stl")

    def test_supports_process_inherits(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        p = pp.supports_process({"process": "0.20mm Standard @BBL H2S",
                                 "machine": "Bambu Lab H2S 0.4 nozzle"}, d)
        with open(p) as fh:
            data = json.load(fh)
        self.assertEqual(data["inherits"], "0.20mm Standard @BBL H2S")
        self.assertEqual(data["compatible_printers"], ["Bambu Lab H2S 0.4 nozzle"])
        self.assertEqual(data["enable_support"], "1")

    def _result(self, d, code=0, plates=2):
        with open(os.path.join(d, "result.json"), "w") as fh:
            json.dump({"return_code": code, "error_string": "Success." if code == 0 else "bad",
                       "sliced_plates": [{"id": i + 1, "total_predication": 600.0,
                                          "objects": [{"name": "P%d.stl" % i}],
                                          "warning_message": ""} for i in range(plates)]}, fh)

    def test_read_result_and_filament(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        self._result(d)
        r = pp.read_result(d)
        self.assertTrue(r["ok"])
        self.assertEqual([p["id"] for p in r["plates"]], [1, 2])
        self.assertEqual(r["seconds"], 1200.0)
        proj = os.path.join(d, "x.3mf")
        with zipfile.ZipFile(proj, "w") as z:
            z.writestr("Metadata/slice_info.config",
                       '<config><plate><metadata key="index" value="1"/>'
                       '<filament id="1" used_m="10.0" used_g="0.00"/></plate>'
                       '<plate><metadata key="index" value="2"/>'
                       '<filament id="1" used_m="5.0"/></plate></config>')
        pp._filament_use(proj, r["plates"], 1.24)
        self.assertAlmostEqual(r["plates"][0]["grams"], 29.8, places=1)  # 10 m of 1.75 PLA
        self.assertAlmostEqual(r["plates"][1]["grams"], 14.9, places=1)
        r.update(grams=44.7, profile={"filament": "Bambu PLA Basic @BBL H2S"})
        self.assertEqual(pp.summary(r), "2 plates, about 20 min and 45 g of Bambu PLA Basic.")

    def test_sabotage_failed_slice_is_not_ok(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        self._result(d, code=3002)
        self.assertFalse(pp.read_result(d)["ok"])
        self._result(d, plates=0)
        self.assertFalse(pp.read_result(d)["ok"])
        os.remove(os.path.join(d, "result.json"))
        self.assertFalse(pp.read_result(d)["ok"])

    def test_sabotage_part_left_off_the_plates_is_not_ok(self):
        # R941: Bambu Studio's arrange drops a part it cannot place and
        # still returns 0; the run must fail and name the part.
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        files = [os.path.join(d, n + ".stl") for n in ("Head", "Arm", "Foot")]
        plates = [{"parts": ["Arm.stl"]}, {"parts": ["Foot.stl"]}]
        self.assertEqual(pp.missing_parts(files, plates), ["Head"])
        plates.append({"parts": ["Head.stl"]})
        self.assertEqual(pp.missing_parts(files, plates), [])

        def runner(cmd, out_dir, log_path):
            with open(os.path.join(out_dir, "result.json"), "w") as fh:
                json.dump({"return_code": 0, "sliced_plates": [
                    {"id": 1, "total_predication": 60,
                     "objects": [{"name": "Arm.stl"}, {"name": "Foot.stl"}]}]}, fh)
            open(os.path.join(out_dir, "x.3mf"), "w").close()
        prof = {"machine": "Bambu Lab A1 mini 0.4 nozzle", "model": "Bambu Lab A1 mini",
                "machine_file": "m", "process_file": "p", "filament_file": "f",
                "density": 1.24}
        r = pp.slice_plates({"folder": d, "files": files}, prof, "/Applications/BambuStudio.app",
                            runner, "x.3mf")
        self.assertFalse(r["ok"])
        self.assertEqual(r["missing"], ["Head"])
        self.assertIn("Head", r["error"])
        self.assertIn("A1 mini", r["error"])

    def test_open_project(self):
        seen = []
        pp.open_project("/x/y.3mf", "/Applications/BambuStudio.app", seen.append)
        self.assertEqual(seen, [["open", "-a", "/Applications/BambuStudio.app", "/x/y.3mf"]])


SLICE_SCRIPT = r'''
import json, os, sys
sys.path.insert(0, %(addon)r)
import FreeCAD as App, Part
from acadagent import print_plates as pp
doc = App.newDocument("Plates")
doc.Label = "Plates"
a = doc.addObject("Part::Feature", "Small"); a.Shape = Part.makeBox(20, 20, 10)
b = doc.addObject("Part::Feature", "Big_1"); b.Shape = Part.makeBox(%(big)s, %(big)s, 4)
c = doc.addObject("Part::Feature", "Big_2"); c.Shape = Part.makeBox(%(big)s, %(big)s, 4)
c.Placement.Base = App.Vector(0, 0, 50)
res = pp.make_plates(doc, root=%(root)r)
print("PLATES=" + json.dumps({"ok": res["ok"], "error": res.get("error"),
      "n": len(res["plates"]), "too_big": res.get("too_big"),
      "parts": sorted(sum((p["parts"] for p in res["plates"]), [])),
      "log": json.load(open(res["log"]))}, default=str))
'''


@unittest.skipIf(FC is None or APP is None or pp.bambu_profile() is None,
                 "needs freecadcmd (ATECH_FREECADCMD) and a set-up Bambu Studio")
class Slice(unittest.TestCase):
    def run_fc(self, big):
        root = tempfile.mkdtemp(prefix="atech-plates-")
        self.addCleanup(shutil.rmtree, root, True)
        script = os.path.join(root, "slice.py")
        with open(script, "w") as fh:
            fh.write(SLICE_SCRIPT % {"addon": ADDON, "big": big, "root": root})
        p = subprocess.run([FC, script], capture_output=True, text=True, timeout=900)
        line = [ln for ln in (p.stdout + p.stderr).splitlines() if ln.startswith("PLATES=")]
        self.assertTrue(line, (p.stdout + p.stderr)[-2000:])
        return json.loads(line[-1][len("PLATES="):])

    def test_two_big_parts_two_plates(self):
        # each fits the selected printer's bed, two do not share one (R941:
        # 200 mm was the H2S's; a P2S's arrange dropped them)
        bed = pp.bambu_profile()["bed"]
        r = self.run_fc(int(min(bed[0], bed[1]) * 0.55))
        self.assertTrue(r["ok"], r["error"])
        self.assertEqual(r["n"], 2)
        self.assertEqual(r["parts"], ["Big_1.stl", "Big_2.stl", "Small.stl"])
        self.assertEqual(r["log"]["parts"], ["Small", "Big_1", "Big_2"])
        self.assertTrue(r["log"]["ok"])

    def test_sabotage_too_big_never_slices(self):
        r = self.run_fc(400)
        self.assertFalse(r["ok"])
        self.assertEqual(sorted(r["too_big"]), ["Big_1", "Big_2"])
        self.assertIn("Too big", r["error"])


try:
    from PySide6 import QtWidgets
    _APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
except Exception:                                         # noqa: BLE001
    _APP = None


@unittest.skipIf(_APP is None, "needs PySide6 (the bundle's python, offscreen)")
class Dialog(unittest.TestCase):
    def test_bambu_card_names_the_printer(self):
        d = fake_support()
        self.addCleanup(shutil.rmtree, d, True)
        dlg = pp.PrintDialog(None, lambda: None, lambda: [],
                             app_fn=lambda: "/Applications/BambuStudio.app",
                             profile_fn=lambda: pp.bambu_profile(d))
        self.assertIn("H2S", dlg.findChild(QtWidgets.QLabel, "ToolTitle").text() + " ".join(
            lab.text() for lab in dlg.findChildren(QtWidgets.QLabel)))
        self.assertEqual(dlg.btn_bambu.text(), "Make plates and open Bambu Studio")
        self.assertIsNone(dlg.bambu())                    # no document
        self.assertIn("Open a design first", dlg.status.text())
        with mock.patch.object(pp.et, "ExportDialog") as ed:
            dlg.export()
        ed.assert_called_once()

    def test_without_studio_offers_the_download(self):
        dlg = pp.PrintDialog(None, lambda: None, lambda: [], app_fn=lambda: None)
        self.assertEqual(dlg.btn_bambu.text(), "Get Bambu Studio")


if __name__ == "__main__":
    unittest.main()
