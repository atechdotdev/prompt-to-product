"""R1270: what Bambu Studio's command line needs (docs/CAD_WORKFLOW_MERGE.md).

    cd addon/AcadAgent/tests && python3 -m unittest test_cadwf_r1270

Gustav found these on real prints (cad-workflow builds/kit_cases/
REVISIONS.md, 2026-09-28): the command line loads only the preset file it
is given, so what a preset inherits is lost (bed 45 C, flow 1.0, no
density); the printer's own start G-code lives in template files it never
loads; and its slices have an empty printer model id, which the printer
checks. Here: each preset is written out whole, the model id is put in
after slicing, and Bambu Studio is found on Linux.

No Bambu Studio is needed: the support folder and the slicer are fakes.
"""
import json
import os
import shutil
import stat
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
sys.path.insert(0, ADDON)

from acadagent import print_plates as pp  # noqa: E402

MACHINE = "Bambu Lab H2S 0.4 nozzle"
PROCESS = "0.20mm Standard @BBL H2S"
FILAMENT = "Bambu PETG HF @BBL H2S"
START = "; H2S start\nM620 M ;enable remap\nT1000\n"


def support():
    """A Bambu Studio support folder whose presets inherit, as the real
    ones do: the leaf files hold almost nothing themselves."""
    d = tempfile.mkdtemp(prefix="atech-bambu-r1270-")
    sysd = os.path.join(d, "system", "BBL")
    for kind in ("machine", "process", "filament"):
        os.makedirs(os.path.join(sysd, kind))

    def put(kind, name, data):
        with open(os.path.join(sysd, kind, name + ".json"), "w") as fh:
            json.dump(dict(data, name=name), fh)
    put("machine", "fdm_machine_common", {
        "type": "machine", "machine_start_gcode": "G28 ; generic", "printable_height": "100",
        "extruder_type": ["Direct Drive"], "machine_end_gcode": ""})
    put("machine", "fdm_bbl_3dp_002_common", {
        "type": "machine", "inherits": "fdm_machine_common",
        "physical_extruder_map": ["0"], "nozzle_volume": ["107"]})
    put("machine", MACHINE, {
        "type": "machine", "inherits": "fdm_bbl_3dp_002_common", "from": "system",
        "setting_id": "GM037", "printer_model": "Bambu Lab H2S",
        "printable_area": ["0x0", "340x0", "340x320", "0x320"], "printable_height": "340",
        "default_print_profile": PROCESS, "default_filament_profile": [FILAMENT]})
    # the printer's own G-code, in template files beside the preset
    put("machine", MACHINE + " template machine_start_gcode", {
        "type": "machine", "machine_start_gcode": START})
    put("machine", MACHINE + " template machine_end_gcode", {
        "type": "machine", "machine_end_gcode": "; H2S end\n"})
    put("machine", "Bambu Lab H2S", {"type": "machine_model", "model_id": "O1S",
                                     "nozzle_diameter": "0.4;0.6;0.8"})
    put("process", "fdm_process_common", {"type": "process", "layer_height": "0.2",
                                          "wall_loops": "2", "enable_support": "0"})
    put("process", PROCESS, {"type": "process", "inherits": "fdm_process_common",
                             "from": "system", "setting_id": "GP158"})
    put("filament", "fdm_filament_petg", {
        "type": "filament", "filament_density": ["1.27"], "filament_flow_ratio": ["0.95"],
        "textured_plate_temp": ["70"], "nozzle_temperature": ["255"]})
    put("filament", FILAMENT, {"type": "filament", "inherits": "fdm_filament_petg",
                               "from": "system", "setting_id": "GFSG02_11"})
    with open(os.path.join(d, "BambuStudio.conf"), "w") as fh:
        json.dump({"presets": {"machine": MACHINE, "filaments": [FILAMENT]}}, fh)
    return d


def project(path, model_id=""):
    """A sliced Bambu project as the command line writes it."""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("Metadata/slice_info.config",
                   '<?xml version="1.0"?>\n<config>\n <plate>\n'
                   '  <metadata key="index" value="1"/>\n'
                   '  <metadata key="printer_model_id" value="%s"/>\n'
                   '  <filament id="1" used_m="2.50" used_g="0"/>\n </plate>\n</config>\n'
                   % model_id)
        z.writestr("Metadata/plate_1.gcode", "; gcode\n")
        z.writestr("3D/3dmodel.model", "<model/>")
    return path


class WholePresets(unittest.TestCase):

    def setUp(self):
        self.d = support()
        self.addCleanup(shutil.rmtree, self.d, True)

    def test_the_leaf_alone_has_almost_nothing(self):
        # what the command line used to be given
        with open(os.path.join(self.d, "system", "BBL", "filament", FILAMENT + ".json")) as fh:
            leaf = json.load(fh)
        self.assertNotIn("textured_plate_temp", leaf)
        self.assertNotIn("filament_density", leaf)

    def test_filament_carries_what_it_inherits(self):
        f = pp.flat_preset(self.d, "filament", FILAMENT)
        self.assertEqual(f["textured_plate_temp"], ["70"])
        self.assertEqual(f["filament_flow_ratio"], ["0.95"])
        self.assertEqual(f["filament_density"], ["1.27"])
        self.assertEqual(f["name"], FILAMENT)
        self.assertNotIn("inherits", f)
        self.assertEqual(f["from"], "User")

    def test_machine_carries_its_chain_and_its_own_gcode(self):
        m = pp.flat_preset(self.d, "machine", MACHINE)
        self.assertEqual(m["physical_extruder_map"], ["0"])       # two levels up
        self.assertEqual(m["extruder_type"], ["Direct Drive"])    # three levels up
        self.assertEqual(m["printable_height"], "340")            # the leaf wins
        self.assertEqual(m["machine_end_gcode"], "; H2S end\n")   # empty in the chain
        self.assertNotIn("inherits", m)
        self.assertEqual((m["name"], m["from"]), (MACHINE, "system"))
        self.assertEqual(pp.preset_names(self.d, "machine", MACHINE),
                         [MACHINE, "fdm_bbl_3dp_002_common", "fdm_machine_common"])

    def test_the_printers_own_start_gcode_beats_the_generic_one(self):
        # "my gcode started with the generic fdm_machine_common start gcode
        # (G28, lift nozzle), no M620 M ... the entire choose-filament step
        # is gone at the printer": the root's generic block is replaced
        self.assertEqual(pp.resolve_preset(self.d, "machine", MACHINE)["machine_start_gcode"],
                         "G28 ; generic")
        m = pp.flat_preset(self.d, "machine", MACHINE)
        self.assertEqual(m["machine_start_gcode"], START)
        self.assertIn("M620 M", m["machine_start_gcode"])
        # a start block the preset's OWN file sets is kept
        p = os.path.join(self.d, "system", "BBL", "machine", MACHINE + ".json")
        with open(p) as fh:
            d = json.load(fh)
        d["machine_start_gcode"] = "; my own start\n"
        with open(p, "w") as fh:
            json.dump(d, fh)
        self.assertEqual(pp.flat_preset(self.d, "machine", MACHINE)["machine_start_gcode"],
                         "; my own start\n")

    def test_templates_of_another_printer_are_not_taken(self):
        other = os.path.join(self.d, "system", "BBL", "machine",
                             "Bambu Lab H2D 0.4 nozzle template machine_end_gcode.json")
        with open(other, "w") as fh:
            json.dump({"machine_end_gcode": "; H2D end\n"}, fh)
        self.assertEqual(pp.flat_preset(self.d, "machine", MACHINE)["machine_end_gcode"],
                         "; H2S end\n")

    def test_process_with_supports(self):
        prof = pp.bambu_profile(self.d)
        with tempfile.TemporaryDirectory() as out:
            files = pp.write_flat_presets(prof, out, supports=True)
            self.assertEqual(sorted(files), ["filament_file", "machine_file", "process_file"])
            with open(files["process_file"]) as fh:
                proc = json.load(fh)
        self.assertEqual(proc["layer_height"], "0.2")              # inherited, now present
        self.assertEqual(proc["wall_loops"], "2")
        self.assertEqual((proc["enable_support"], proc["support_type"]), ("1", "tree(auto)"))
        self.assertEqual(proc["name"], PROCESS + " - Atech supports")
        self.assertEqual(proc["compatible_printers"], [MACHINE])
        self.assertEqual(proc["from"], "User")

    def test_not_a_system_preset(self):
        self.assertEqual(pp.flat_preset(self.d, "filament", "My own PLA"), {})
        prof = dict(pp.bambu_profile(self.d), filament="My own PLA")
        with tempfile.TemporaryDirectory() as out:
            self.assertIsNone(pp.write_flat_presets(prof, out))
        self.assertIsNone(pp.write_flat_presets({"machine": MACHINE}, "/nowhere"))


class ModelId(unittest.TestCase):

    def setUp(self):
        self.d = support()
        self.addCleanup(shutil.rmtree, self.d, True)

    def test_profile_knows_the_printers_model_id(self):
        prof = pp.bambu_profile(self.d)
        self.assertEqual(prof["model_id"], "O1S")
        self.assertEqual(prof["support_dir"], self.d)

    def test_an_empty_id_is_filled_in(self):
        with tempfile.TemporaryDirectory() as out:
            p = project(os.path.join(out, "car.3mf"))
            self.assertTrue(pp.fix_model_id(p, "O1S"))
            with zipfile.ZipFile(p) as z:
                info = z.read("Metadata/slice_info.config").decode()
                self.assertIn('key="printer_model_id" value="O1S"', info)
                self.assertIn('used_m="2.50"', info)                 # the rest untouched
                self.assertEqual(sorted(z.namelist()),
                                 ["3D/3dmodel.model", "Metadata/plate_1.gcode",
                                  "Metadata/slice_info.config"])
                self.assertEqual(z.read("Metadata/plate_1.gcode"), b"; gcode\n")
            self.assertFalse(os.path.exists(p + ".tmp"))
            self.assertFalse(pp.fix_model_id(p, "O1S"))               # nothing left to do

    def test_an_id_that_is_there_is_left_alone(self):
        with tempfile.TemporaryDirectory() as out:
            p = project(os.path.join(out, "car.3mf"), "O1D")
            self.assertFalse(pp.fix_model_id(p, "O1S"))
            with zipfile.ZipFile(p) as z:
                self.assertIn('value="O1D"', z.read("Metadata/slice_info.config").decode())

    def test_nothing_to_do(self):
        with tempfile.TemporaryDirectory() as out:
            p = project(os.path.join(out, "car.3mf"))
            self.assertFalse(pp.fix_model_id(p, ""))
            self.assertFalse(pp.fix_model_id(os.path.join(out, "none.3mf"), "O1S"))
            junk = os.path.join(out, "junk.3mf")
            with open(junk, "w") as fh:
                fh.write("not a zip")
            self.assertFalse(pp.fix_model_id(junk, "O1S"))


class Slice(unittest.TestCase):
    """slice_plates with a fake slicer: what is passed, what is fixed."""

    def setUp(self):
        self.d = support()
        self.addCleanup(shutil.rmtree, self.d, True)
        self.run_dir = tempfile.mkdtemp(prefix="atech-run-")
        self.addCleanup(shutil.rmtree, self.run_dir, True)
        self.folder = os.path.join(self.run_dir, "Car", "2026-11-27 10.00")
        os.makedirs(self.folder)
        self.part = os.path.join(self.folder, "Body.stl")
        with open(self.part, "w") as fh:
            fh.write("solid\nendsolid\n")

    def _runner(self, seen):
        def run(cmd, out_dir, log_path):
            seen.append(cmd)
            with open(os.path.join(out_dir, "result.json"), "w") as fh:
                json.dump({"return_code": 0, "sliced_plates": [
                    {"id": 1, "total_predication": 600, "objects": [{"name": "Body.stl"}]}]}, fh)
            project(os.path.join(out_dir, cmd[cmd.index("--export-3mf") + 1]))
        return run

    def _exported(self, supports=()):
        return {"folder": self.folder, "files": [self.part], "needs_supports": list(supports),
                "parts": ["Body"], "left_out": [], "rows": []}

    def test_the_slicer_gets_whole_presets_and_the_file_gets_its_model_id(self):
        prof = pp.bambu_profile(self.d)
        seen = []
        res = pp.slice_plates(self._exported(), prof, "/Applications/BambuStudio.app",
                              runner=self._runner(seen))
        self.assertTrue(res["ok"], res)
        self.assertTrue(res["whole_presets"])
        self.assertTrue(res["model_id_set"])
        cmd = seen[0]
        settings = cmd[cmd.index("--load-settings") + 1].split(";")
        filament = cmd[cmd.index("--load-filaments") + 1]
        self.assertEqual([os.path.basename(s) for s in settings], ["machine.json", "process.json"])
        self.assertEqual(os.path.basename(filament), "filament.json")
        for p in settings + [filament]:
            self.assertEqual(os.path.dirname(p), self.folder)
        with open(filament) as fh:
            self.assertEqual(json.load(fh)["textured_plate_temp"], ["70"])
        with zipfile.ZipFile(res["project"]) as z:
            self.assertIn('value="O1S"', z.read("Metadata/slice_info.config").decode())
        self.assertFalse(res["supports"])
        self.assertEqual(res["plates"][0]["metres"], 2.5)

    def test_supports_go_in_the_whole_process(self):
        prof = pp.bambu_profile(self.d)
        seen = []
        res = pp.slice_plates(self._exported(["Body"]), prof, "/Applications/BambuStudio.app",
                              runner=self._runner(seen))
        self.assertTrue(res["ok"] and res["supports"], res)
        proc = seen[0][seen[0].index("--load-settings") + 1].split(";")[1]
        with open(proc) as fh:
            d = json.load(fh)
        self.assertEqual(d["support_type"], "tree(auto)")
        self.assertEqual(d["layer_height"], "0.2")       # not lost with the parent

    def test_presets_that_cannot_be_read_fall_back_to_the_system_files(self):
        prof = dict(pp.bambu_profile(self.d), support_dir=None)
        seen = []
        res = pp.slice_plates(self._exported(), prof, "/Applications/BambuStudio.app",
                              runner=self._runner(seen))
        self.assertTrue(res["ok"])
        self.assertFalse(res["whole_presets"])
        settings = seen[0][seen[0].index("--load-settings") + 1].split(";")
        self.assertEqual(settings[0], prof["machine_file"])


class Linux(unittest.TestCase):

    def test_support_folders(self):
        self.assertEqual(pp.support_dirs("darwin", "/Users/a"),
                         ["/Users/a/Library/Application Support/BambuStudio"])
        got = pp.support_dirs("linux", "/home/a")
        self.assertEqual(got[0], "/home/a/.config/BambuStudio")
        self.assertIn("com.bambulab.BambuStudio", got[1])

    def test_on_path(self):
        self.assertEqual(pp.linux_studio(which=lambda n: "/usr/bin/" + n
                                         if n == "bambu-studio" else None, dirs=()),
                         "/usr/bin/bambu-studio")
        self.assertIsNone(pp.linux_studio(which=lambda n: None, dirs=()))

    def test_an_appimage_in_applications(self):
        with tempfile.TemporaryDirectory() as d:
            app = os.path.join(d, "Bambu_Studio_linux_fedora-v02.03.00.70.AppImage")
            other = os.path.join(d, "OrcaSlicer.AppImage")
            notes = os.path.join(d, "bambu studio notes.txt")
            for p in (app, other, notes):
                with open(p, "w") as fh:
                    fh.write("x")
            os.chmod(app, os.stat(app).st_mode | stat.S_IXUSR)
            os.chmod(other, os.stat(other).st_mode | stat.S_IXUSR)
            self.assertEqual(pp.linux_studio(which=lambda n: None, dirs=(d,)), app)
            # the executable is the command line, and it opens a project
            self.assertEqual(pp.bambu_cli(app), app)
            seen = []
            pp.open_project("/tmp/car.3mf", app=app, runner=seen.append)
            self.assertEqual(seen, [[app, "/tmp/car.3mf"]])

    def test_a_mac_bundle_is_as_before(self):
        self.assertEqual(pp.bambu_cli("/Applications/BambuStudio.app"),
                         "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio")
        seen = []
        pp.open_project("/tmp/car.3mf", app="/Applications/BambuStudio.app", runner=seen.append)
        self.assertEqual(seen, [["open", "-a", "/Applications/BambuStudio.app", "/tmp/car.3mf"]])


class OnTheBed(unittest.TestCase):
    """The print plan says which side of each part goes down, and why
    supports are needed (p2p_print.bed_markdown)."""

    def setUp(self):
        kit = os.path.join(ADDON, "acadagent", "agent_kit")
        if kit not in sys.path:
            sys.path.insert(0, kit)

    def test_table(self):
        import p2p_print
        parts = [
            {"label": "Tray", "bed": {
                "flat_face_mm2": 2400.0, "turned_deg": 0.0, "supports": False,
                "overhang_mm2": 0.0, "overhang_pct": 0.0, "flags": [],
                "first_layer": {"area": 2400.0, "pieces": 1, "line_mm": 24.0}}},
            {"label": "Lid", "bed": {
                "flat_face_mm2": 2400.0, "turned_deg": 180.0, "supports": True,
                "overhang_mm2": 310.4, "overhang_pct": 6.2,
                "flags": [["note", "310 mm2 (6.2 %) faces down steeper than 45 degrees: "
                           "supports there"]],
                "first_layer": {"area": 2400.0, "pieces": 1, "line_mm": 24.0}}},
            {"label": "Ring", "bed": {
                "flat_face_mm2": 64.4, "turned_deg": 0.0, "supports": False,
                "overhang_mm2": 0.0, "overhang_pct": 0.0,
                "flags": [["warning", "its first layer is a line only 0.70 mm wide"]],
                "first_layer": {"area": 64.4, "pieces": 1, "line_mm": 0.7}}},
            {"label": "Ball", "bed": {"skipped": "time budget"}},
            {"label": "Bought", "bed": None},
        ]
        md = p2p_print.bed_markdown(parts)
        self.assertIn("## On the bed", md)
        self.assertIn("| Tray | as drawn, on its 2400 mm2 flat side | 2400 mm2 in 1 piece "
                      "| no |  |", md)
        self.assertIn("| Lid | turned 180 deg onto its 2400 mm2 flat side |", md)
        self.assertIn("yes: 310 mm2 (6.2 %) hang over air steeper than 45 deg", md)
        self.assertIn("its first layer is a line only 0.70 mm wide", md)
        self.assertIn("| Ball | not measured (time budget) |", md)
        self.assertNotIn("Bought", md)

    def test_nothing_measured_nothing_written(self):
        import p2p_print
        self.assertEqual(p2p_print.bed_markdown([{"label": "A"}, {"label": "B", "bed": None}]), "")
        self.assertEqual(p2p_print.bed_markdown(None), "")


if __name__ == "__main__":
    unittest.main()
