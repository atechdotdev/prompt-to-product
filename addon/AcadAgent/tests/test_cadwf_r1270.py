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
    # as the real file: the plate it ships with, and the one it does not take
    put("machine", "Bambu Lab H2S", {"type": "machine_model", "model_id": "O1S",
                                     "default_bed_type": "Textured PEI Plate",
                                     "not_support_bed_type": "Cool Plate",
                                     "nozzle_diameter": "0.4;0.6;0.8"})
    put("process", "fdm_process_common", {"type": "process", "layer_height": "0.2",
                                          "wall_loops": "2", "enable_support": "0"})
    put("process", PROCESS, {"type": "process", "inherits": "fdm_process_common",
                             "from": "system", "setting_id": "GP158"})
    put("filament", "fdm_filament_petg", {
        "type": "filament", "filament_density": ["1.27"], "filament_flow_ratio": ["0.95"],
        "textured_plate_temp": ["70"], "hot_plate_temp": ["70"], "cool_plate_temp": ["0"],
        "nozzle_temperature": ["255"]})
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
            self.assertEqual(sorted(k for k in files if k.endswith("_file")),
                             ["filament_file", "machine_file", "process_file"])
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


class BedType(unittest.TestCase):
    """R1295 review (high): the process written for the command line had
    no "curr_bed_type". Gustav's note of 2026-11-08: the command line then
    slices for the Cool Plate, and PETG and PETG-CF (bed temperature 0 on
    that plate) fail with "Filaments are not compatible with the plate
    type". All 16 of his process files that printed set "Textured PEI
    Plate"."""

    def setUp(self):
        self.d = support()
        self.addCleanup(shutil.rmtree, self.d, True)

    def _model(self, **change):
        p = os.path.join(self.d, "system", "BBL", "machine", "Bambu Lab H2S.json")
        with open(p) as fh:
            d = json.load(fh)
        for k, v in change.items():
            if v is None:
                d.pop(k, None)
            else:
                d[k] = v
        with open(p, "w") as fh:
            json.dump(d, fh)

    def _plate(self, filament=None):
        m = pp.flat_preset(self.d, "machine", MACHINE)
        f = pp.flat_preset(self.d, "filament", FILAMENT)
        f.update(filament or {})
        return pp.bed_type(self.d, m, f)

    def test_the_process_names_the_printers_plate(self):
        prof = pp.bambu_profile(self.d)
        for supports in (False, True):
            with tempfile.TemporaryDirectory() as out:
                files = pp.write_flat_presets(prof, out, supports=supports)
                with open(files["process_file"]) as fh:
                    proc = json.load(fh)
            self.assertEqual(proc["curr_bed_type"], "Textured PEI Plate", supports)
            self.assertEqual(files["bed_type"], "Textured PEI Plate")
            self.assertNotEqual(proc["curr_bed_type"], "Cool Plate")

    def test_never_a_plate_the_printer_does_not_take(self):
        self._model(default_bed_type="Cool Plate")          # a contradiction in the file
        self.assertEqual(self._plate(), "Textured PEI Plate")
        self._model(default_bed_type=None, not_support_bed_type=["Cool Plate",
                                                                 "Textured PEI Plate"])
        self.assertEqual(self._plate(), "High Temp Plate")
        self._model(not_support_bed_type="Cool Plate;Textured PEI Plate")   # a ";" list
        self.assertEqual(self._plate(), "High Temp Plate")

    def test_never_a_plate_the_filament_has_no_temperature_for(self):
        # the printer says nothing: PETG (cool plate 0) still gets a plate it prints on
        self._model(default_bed_type=None, not_support_bed_type=None)
        self.assertEqual(self._plate(), "Textured PEI Plate")
        self.assertEqual(self._plate({"textured_plate_temp": ["0"]}), "High Temp Plate")
        # the printer's default, but this filament does not print on it
        self._model(default_bed_type="Textured PEI Plate")
        self.assertEqual(self._plate({"textured_plate_temp": ["0"]}), "High Temp Plate")

    def test_nothing_known_changes_nothing(self):
        # no default in the printer's file and a filament that prints on the
        # cool plate: Bambu Studio's own default, as before
        self._model(default_bed_type=None, not_support_bed_type=None)
        self.assertEqual(self._plate({"cool_plate_temp": ["35"]}), "")
        prof = pp.bambu_profile(self.d)
        p = os.path.join(self.d, "system", "BBL", "filament", "fdm_filament_petg.json")
        with open(p) as fh:
            d = json.load(fh)
        d["cool_plate_temp"] = ["35"]
        with open(p, "w") as fh:
            json.dump(d, fh)
        with tempfile.TemporaryDirectory() as out:
            files = pp.write_flat_presets(prof, out)
            with open(files["process_file"]) as fh:
                self.assertNotIn("curr_bed_type", json.load(fh))
        self.assertEqual(files["bed_type"], "")
        # no machine_model file at all
        os.unlink(os.path.join(self.d, "system", "BBL", "machine", "Bambu Lab H2S.json"))
        self.assertEqual(self._plate({"cool_plate_temp": ["35"]}), "")
        self.assertEqual(self._plate({"cool_plate_temp": ["0"]}), "Textured PEI Plate")


class MissingGcode(unittest.TestCase):
    """R1295 review: when the printer's template files were not found the
    slice silently carried the generic start G-code - "the entire
    choose-filament step is gone at the printer" - and was reported as
    made from whole presets."""

    def setUp(self):
        self.d = support()
        self.addCleanup(shutil.rmtree, self.d, True)
        self.mdir = os.path.join(self.d, "system", "BBL", "machine")

    def _include(self, names):
        p = os.path.join(self.mdir, MACHINE + ".json")
        with open(p) as fh:
            d = json.load(fh)
        d["include"] = names
        with open(p, "w") as fh:
            json.dump(d, fh)

    def test_everything_found_is_not_a_caution(self):
        self._include([MACHINE + " template machine_start_gcode",
                       MACHINE + " template machine_end_gcode"])
        missing = []
        pp.machine_templates(self.d, [MACHINE], missing=missing)
        self.assertEqual(missing, [])
        with tempfile.TemporaryDirectory() as out:
            files = pp.write_flat_presets(pp.bambu_profile(self.d), out)
        self.assertEqual(files["missing_templates"], [])

    def test_an_included_template_that_is_nowhere_is_named(self):
        self._include([MACHINE + " template machine_start_gcode",
                       MACHINE + " template change_filament_gcode",
                       MACHINE + " template layer_change_gcode"])
        missing = []
        got = pp.machine_templates(self.d, [MACHINE], dirs=[self.mdir], missing=missing)
        self.assertEqual(got["machine_start_gcode"], START)
        self.assertEqual(missing, [MACHINE + " template change_filament_gcode",
                                   MACHINE + " template layer_change_gcode"])
        with tempfile.TemporaryDirectory() as out:
            files = pp.write_flat_presets(pp.bambu_profile(self.d), out)
        self.assertEqual(len(files["missing_templates"]), 2)
        res = {"ok": True, "whole_presets": True, "bed_type": "Textured PEI Plate",
               "missing_templates": files["missing_templates"], "model_id": "O1S"}
        text = " ".join(pp.slice_cautions(res))
        self.assertIn("start and filament-change G-code was not found", text)
        self.assertIn("change_filament_gcode", text)
        self.assertIn("Slice it again in Bambu Studio", text)

    def test_no_start_gcode_at_all_is_named(self):
        for f in os.listdir(self.mdir):
            if " template " in f or f == "fdm_machine_common.json":
                os.unlink(os.path.join(self.mdir, f))
        p = os.path.join(self.mdir, "fdm_bbl_3dp_002_common.json")
        with open(p) as fh:
            d = json.load(fh)
        d.pop("inherits")
        with open(p, "w") as fh:
            json.dump(d, fh)
        with tempfile.TemporaryDirectory() as out:
            files = pp.write_flat_presets(pp.bambu_profile(self.d), out)
        self.assertEqual(files["missing_templates"], ["machine_start_gcode"])

    def test_what_the_person_is_told(self):
        ok = {"ok": True, "whole_presets": True, "bed_type": "Textured PEI Plate",
              "missing_templates": [], "model_id": "O1S"}
        self.assertEqual(pp.slice_cautions(ok), ["Sliced for the Textured PEI Plate: use "
                                                 "that plate."])
        self.assertEqual(pp.slice_cautions(dict(ok, bed_type="")), [])
        text = " ".join(pp.slice_cautions(dict(ok, whole_presets=False)))
        self.assertIn("could not be read in full", text)
        self.assertIn("Slice it again in Bambu Studio", text)
        # the file still has an empty model id (no id known for this printer)
        text = " ".join(pp.slice_cautions(dict(ok, model_id="")))
        self.assertIn("does not name the printer model", text)
        self.assertNotIn("does not name", " ".join(pp.slice_cautions(dict(ok, model_id=None))))
        self.assertEqual(pp.slice_cautions({"ok": False, "missing_templates": ["x"]}), [])

    def test_linux_profile_folders_are_searched(self):
        root = tempfile.mkdtemp(prefix="atech-flatpak-")
        self.addCleanup(shutil.rmtree, root, True)
        mdir = os.path.join(root, "profiles", "BBL", "machine")
        os.makedirs(mdir)
        dirs = pp.machine_dirs(self.d, roots=(), linux=(os.path.join(root, "profiles"),
                                                        "/no/such/place"))
        self.assertEqual(dirs, [self.mdir, mdir])
        self.assertTrue(any("flatpak" in d for d in pp.LINUX_PROFILE_DIRS))
        self.assertTrue(any(d.startswith("/usr/share/") for d in pp.LINUX_PROFILE_DIRS))


class ModelId(unittest.TestCase):

    def setUp(self):
        self.d = support()
        self.addCleanup(shutil.rmtree, self.d, True)

    def test_what_a_sliced_project_carries(self):
        with tempfile.TemporaryDirectory() as out:
            self.assertEqual(pp.project_model_id(project(os.path.join(out, "a.3mf"))), "")
            self.assertEqual(pp.project_model_id(project(os.path.join(out, "b.3mf"), "O1S")),
                             "O1S")
            self.assertIsNone(pp.project_model_id(os.path.join(out, "none.3mf")))
            with zipfile.ZipFile(os.path.join(out, "c.3mf"), "w") as z:
                z.writestr("Metadata/slice_info.config", "<config/>")
            self.assertIsNone(pp.project_model_id(os.path.join(out, "c.3mf")))

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
        # R1295: the plate goes in the process, and what the slice was given
        # is in the result, the sentence and print.json
        with open(settings[1]) as fh:
            self.assertEqual(json.load(fh)["curr_bed_type"], "Textured PEI Plate")
        self.assertEqual(res["bed_type"], "Textured PEI Plate")
        self.assertEqual(res["missing_templates"], [])
        self.assertEqual(res["model_id"], "O1S")
        self.assertEqual(res["cautions"], ["Sliced for the Textured PEI Plate: use that plate."])
        res.update(seconds=600, grams=7.5, profile=prof)
        self.assertTrue(pp.summary(res).endswith("Sliced for the Textured PEI Plate: use "
                                                 "that plate."), pp.summary(res))
        with open(pp.print_log(self._exported(), prof, res)) as fh:
            log = json.load(fh)
        self.assertEqual((log["whole_presets"], log["model_id_set"], log["bed_type"],
                          log["missing_templates"]),
                         (True, True, "Textured PEI Plate", []))
        self.assertEqual(log["cautions"], res["cautions"])

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
        # R1295: and that is said, not silent
        self.assertIn("could not be read in full", " ".join(res["cautions"]))
        res.update(seconds=600, grams=7.5, profile=prof)
        self.assertIn("Slice it again in Bambu Studio", pp.summary(res))
        with open(pp.print_log(self._exported(), prof, res)) as fh:
            self.assertFalse(json.load(fh)["whole_presets"])

    def test_a_failed_slice_has_no_cautions_and_logs(self):
        prof = pp.bambu_profile(self.d)

        def run(cmd, out_dir, log_path):
            with open(os.path.join(out_dir, "result.json"), "w") as fh:
                json.dump({"return_code": -51, "error_string": "Filaments are not compatible "
                           "with the plate type"}, fh)
        res = pp.slice_plates(self._exported(), prof, "/Applications/BambuStudio.app",
                              runner=run)
        self.assertFalse(res["ok"])
        self.assertEqual(res["cautions"], [])
        with open(pp.print_log(self._exported(), prof, res)) as fh:
            log = json.load(fh)
        self.assertFalse(log["ok"])
        self.assertEqual(log["bed_type"], "Textured PEI Plate")


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

    def test_two_appimages_the_newer_one(self):
        # R1295 review: the alphabetically first was taken - the older version
        with tempfile.TemporaryDirectory() as d:
            old = os.path.join(d, "Bambu_Studio_linux-v02.02.00.85.AppImage")
            new = os.path.join(d, "Bambu_Studio_linux-v02.08.02.61.AppImage")
            for p, when in ((old, 1_700_000_000), (new, 1_780_000_000)):
                with open(p, "w") as fh:
                    fh.write("x")
                os.chmod(p, os.stat(p).st_mode | stat.S_IXUSR)
                os.utime(p, (when, when))
            self.assertEqual(pp.linux_studio(which=lambda n: None, dirs=(d,)), new)
            os.utime(old, (1_790_000_000, 1_790_000_000))
            self.assertEqual(pp.linux_studio(which=lambda n: None, dirs=(d,)), old)

    def test_no_app_on_linux_uses_the_systems_opener(self):
        # R1295 review: `open -a` is a macOS command
        seen = []
        real, plat = pp.bambu_studio, sys.platform
        pp.bambu_studio = lambda *a, **k: None
        try:
            sys.platform = "linux"
            pp.open_project("/tmp/car.3mf", runner=seen.append)
            sys.platform = "darwin"
            pp.open_project("/tmp/car.3mf", runner=seen.append)
        finally:
            pp.bambu_studio, sys.platform = real, plat
        self.assertEqual(seen, [["xdg-open", "/tmp/car.3mf"],
                                ["open", "-a", "BambuStudio", "/tmp/car.3mf"]])
        with open(pp.__file__, encoding="utf-8") as fh:
            self.assertNotIn('Popen(["open"', fh.read())

    def test_a_mac_bundle_is_as_before(self):
        self.assertEqual(pp.bambu_cli("/Applications/BambuStudio.app"),
                         "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio")
        seen = []
        pp.open_project("/tmp/car.3mf", app="/Applications/BambuStudio.app", runner=seen.append)
        self.assertEqual(seen, [["open", "-a", "/Applications/BambuStudio.app", "/tmp/car.3mf"]])


class Include(unittest.TestCase):
    """The real layout (Bambu Studio 02.08.02.61, Gustav's H2S files,
    2026-11-27): a machine preset lists its templates in "include"; each
    template is {name, instantiation, <key>}; they sit in the app's own
    profiles folder."""

    def setUp(self):
        self.d = support()
        self.addCleanup(shutil.rmtree, self.d, True)
        self.mdir = os.path.join(self.d, "system", "BBL", "machine")

    def _put(self, folder, name, data):
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, name + ".json"), "w") as fh:
            json.dump(dict(data, name=name), fh)

    def test_another_nozzle_includes_the_04_templates(self):
        # there is no "... 0.2 nozzle template ..." file: the 0.2 preset
        # names the 0.4 nozzle's
        self._put(self.mdir, "Bambu Lab H2S 0.2 nozzle", {
            "type": "machine", "inherits": "fdm_bbl_3dp_002_common", "from": "system",
            "printer_model": "Bambu Lab H2S", "printable_height": "340",
            "include": [MACHINE + " template machine_start_gcode",
                        MACHINE + " template machine_end_gcode"]})
        m = pp.flat_preset(self.d, "machine", "Bambu Lab H2S 0.2 nozzle")
        self.assertEqual(m["machine_start_gcode"], START)
        self.assertEqual(m["machine_end_gcode"], "; H2S end\n")
        self.assertEqual(m["name"], "Bambu Lab H2S 0.2 nozzle")
        # the list stays in the file, as in Gustav's proven machine files
        self.assertEqual(len(m["include"]), 2)

    def test_only_the_included_templates_are_taken(self):
        p = os.path.join(self.mdir, MACHINE + ".json")
        with open(p) as fh:
            d = json.load(fh)
        d["include"] = [MACHINE + " template machine_start_gcode"]
        with open(p, "w") as fh:
            json.dump(d, fh)
        m = pp.flat_preset(self.d, "machine", MACHINE)
        self.assertEqual(m["machine_start_gcode"], START)
        self.assertEqual(m["machine_end_gcode"], "")          # not included: the chain's

    def test_real_template_shape(self):
        self._put(self.mdir, MACHINE + " template time_lapse_gcode", {
            "instantiation": "false", "time_lapse_gcode": "; lapse\n"})
        got = pp.machine_templates(self.d, [MACHINE])
        self.assertEqual(got["time_lapse_gcode"], "; lapse\n")
        self.assertNotIn("instantiation", got)
        self.assertNotIn("name", got)

    def test_templates_in_the_apps_own_folder(self):
        # the user's copy has the presets but not the templates
        for f in os.listdir(self.mdir):
            if " template " in f:
                os.unlink(os.path.join(self.mdir, f))
        self.assertEqual(pp.machine_templates(self.d, [MACHINE]), {})
        app = tempfile.mkdtemp(prefix="atech-app-")
        self.addCleanup(shutil.rmtree, app, True)
        res = os.path.join(app, "BambuStudio.app", "Contents", "Resources", "profiles", "BBL",
                           "machine")
        self._put(res, MACHINE + " template machine_start_gcode", {"machine_start_gcode": START})
        dirs = pp.machine_dirs(self.d, roots=(app,), linux=())
        self.assertEqual(dirs, [self.mdir, res])
        got = pp.machine_templates(self.d, [MACHINE], dirs=dirs)
        self.assertEqual(got, {"machine_start_gcode": START})

    def test_gustavs_real_files_when_given(self):
        # ATECH_BAMBU_FILES=<folder with "Bambu Lab H2S 0.4 nozzle.json", its
        # start template and "Bambu Lab H2S.json">. Bambu's own files are
        # not kept in this repository.
        src = os.environ.get("ATECH_BAMBU_FILES")
        if not src or not os.path.isfile(os.path.join(src, MACHINE + ".json")):
            self.skipTest("set ATECH_BAMBU_FILES to a folder with the real H2S presets")
        d = tempfile.mkdtemp(prefix="atech-real-")
        self.addCleanup(shutil.rmtree, d, True)
        mdir = os.path.join(d, "system", "BBL", "machine")
        os.makedirs(mdir)
        for f in os.listdir(src):
            if f.endswith(".json"):
                shutil.copy(os.path.join(src, f), mdir)
        with open(os.path.join(src, MACHINE + " template machine_start_gcode.json")) as fh:
            want = json.load(fh)["machine_start_gcode"]
        m = pp.flat_preset(d, "machine", MACHINE)
        self.assertEqual(m["machine_start_gcode"], want)
        self.assertGreater(len(want), 5000)
        self.assertIn("M620", want)
        self.assertEqual((m["from"], m["name"]), ("system", MACHINE))
        self.assertNotIn("inherits", m)
        self.assertEqual(m["printable_height"], "340")
        self.assertEqual(pp.model_id(d, m), "O1S")


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
