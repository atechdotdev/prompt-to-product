"""R1040 Share: one folder with everything (acadagent/share.py), and R1041
Bambu Connect (print_plates.send_to_connect).

    cd addon/AcadAgent/tests
    python3 -m unittest test_share_r1040                         # pure parts
    QT_QPA_PLATFORM=offscreen "<bundle>/Contents/Resources/bin/python" \\
        -m unittest test_share_r1040                             # + the window
    ATECH_FREECADCMD=<freecadcmd> python3 -m unittest test_share_r1040   # + the pack

The pack test builds a small design in freecadcmd (two printed parts, a
modelled screw) and makes the share folder without slicing or a picture:
every file is there, the zip holds them, the BOM says what to buy, the 3D
page carries every part. Each check has a sabotage twin.
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from array import array

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
sys.path.insert(0, ADDON)

from acadagent import print_plates as pp                      # noqa: E402
from acadagent import share                                   # noqa: E402

BUNDLE = os.path.normpath(os.path.join(
    ADDON, "..", "..", "dist", "build-macos-arm64", "Prompt To Product.app", "Contents",
    "Resources", "bin"))
FC = os.environ.get("ATECH_FREECADCMD") or os.path.join(BUNDLE, "freecadcmd")
FC = FC if os.path.isfile(FC) else None

BOM = {"printed": [
    {"part": "Body", "count": 1, "names": ["Body"], "volume_cm3": 80.0, "mass_g": 100.0,
     "colour": "cream"},
    {"part": "Arm", "count": 2, "names": ["Arm_L", "Arm_R"], "volume_cm3": 2.0,
     "mass_g": 2.5, "colour": "coral"},
    {"part": "Lid", "count": 1, "names": ["Lid"], "volume_cm3": 40.0, "mass_g": 50.0,
     "colour": "cream"},
    {"part": "M3_Screw", "count": 4, "names": ["M3_Screw_1"], "volume_cm3": 0.1,
     "mass_g": 0.1, "colour": "graphite"}],
    "hardware": [
    {"kind": "Board", "name": "Atech board", "ports": "", "length_mm": None, "label": "Board"},
    {"kind": "Module", "name": "DC Motor", "ports": "3", "length_mm": None, "label": "M1",
     "key": "dc_motor"},
    {"kind": "Module", "name": "Arduino Nano", "ports": "", "length_mm": None, "label": "U1",
     "key": "arduino_nano"},
    {"kind": "Cable", "name": "Cable to DC Motor", "ports": "3", "length_mm": 120.0,
     "label": "C1"}]}


def specs(key):
    return {"arduino_nano": {"user": True, "display_name": "Arduino Nano",
                             "notes": "any Nano clone"}}.get(key, {})


class Bill(unittest.TestCase):
    def setUp(self):
        self.b = share.bill(BOM, spec_fn=specs)

    def test_print_atech_buy(self):
        self.assertEqual([r["part"] for r in self.b["print"]], ["Body", "Arm", "Lid"])
        self.assertEqual([r["name"] for r in self.b["atech"]],
                         ["Atech board", "DC Motor", "Ribbon cable, 120 mm"])
        self.assertEqual([(r["name"], r["count"]) for r in self.b["buy"]],
                         [("M3 Screw", 4), ("Arduino Nano", 1)])
        self.assertEqual(self.b["buy"][1]["note"], "any Nano clone")

    def test_sabotage_screw_named_otherwise_is_printed(self):
        bom = json.loads(json.dumps(BOM))
        bom["printed"][3]["part"] = "Peg"
        b = share.bill(bom, spec_fn=specs)
        self.assertIn("Peg", [r["part"] for r in b["print"]])
        self.assertNotIn("M3 Screw", [r["name"] for r in b["buy"]])

    def test_words_inside_names_are_not_fasteners(self):
        # "Nutcracker" and "Rodent" hold "nut" and "rod" but are printed parts
        bom = {"printed": [dict(BOM["printed"][0], part=n, names=[n]) for n in
                           ("Nutcracker", "Rodent", "Washer_Ring")], "hardware": []}
        b = share.bill(bom, spec_fn=specs)
        self.assertEqual([r["part"] for r in b["print"]], ["Nutcracker", "Rodent"])
        self.assertEqual([r["name"] for r in b["buy"]], ["Washer Ring"])

    def test_filament_per_colour(self):
        self.assertEqual(self.b["filament"], [{"colour": "cream", "grams": 150.0},
                                              {"colour": "coral", "grams": 5.0}])

    def test_sliced_grams_split_over_colours(self):
        fil = share.filament(self.b, {"ok": True, "grams": 31.0})
        self.assertEqual([(f["colour"], f["grams"], f["sliced"]) for f in fil],
                         [("cream", 30.0, True), ("coral", 1.0, True)])
        # sabotage: a failed slice keeps the solid weights, marked as such
        fil = share.filament(self.b, {"ok": False, "grams": 31.0})
        self.assertEqual([f["grams"] for f in fil], [150.0, 5.0])
        self.assertFalse(fil[0]["sliced"])
        self.assertIn("up to 155 g", share.filament_line(fil))

    def test_bom_csv(self):
        rows = share.bom_csv(self.b).splitlines()
        self.assertEqual(rows[0].split(",")[:3], ["What to do", "Item", "Count"])
        self.assertEqual([r.split(",")[0] for r in rows[1:]],
                         ["Print"] * 3 + ["Atech"] * 3 + ["Buy"] * 2)

    def test_shopping_list(self):
        md = share.shopping_md("Robot", self.b, {"ok": True, "grams": 31.0, "seconds": 3900,
                                                 "plates": [{}, {}]})
        self.assertIn("- Cream PLA: 30 g", md)
        self.assertIn("2 plates, 31 g, 1 h 05 min", md)
        self.assertIn("All of it in one cart: https://", md)
        self.assertIn("- 4 x M3 Screw", md)
        self.assertIn("- 1 x Arduino Nano: any Nano clone", md)
        empty = share.shopping_md("Cube", share.bill({"printed": [BOM["printed"][0]],
                                                      "hardware": []}))
        self.assertIn("Nothing else: everything is printed.", empty)
        self.assertIn("No Atech electronics.", empty)
        self.assertIn("up to 100 g", empty)

    def test_unnamed_colour(self):
        self.assertEqual(share.colour_label("#cccce6"), "PLA, colour #cccce6")
        self.assertEqual(share.colour_label("matte black"), "Matte black PLA")


class Texts(unittest.TestCase):
    FILES = [("Robot 3D.html", "the 3D page"), ("Robot - print-ready H2S.3mf", "print it"),
             ("parts/", "STLs"), ("Robot - share.zip", "all of it")]

    def test_message_for_the_person(self):
        b = share.bill(BOM, spec_fn=specs)
        m = share.message("Robot", "", b, self.FILES,
                          {"ok": True, "plates": [{}], "seconds": 3960, "grams": 49.0},
                          "CC BY", "Not printed yet.")
        self.assertIn("- Robot 3D.html: the 3D page", m)
        self.assertNotIn("parts/", m)
        self.assertIn("press Print (1 plate, about 1 h 06 min, 49 g of PLA)", m)
        self.assertIn("- Buy: 4 x M3 Screw, 1 x Arduino Nano.", m)
        self.assertIn("Status: Not printed yet.", m)
        self.assertIn("Licence: CC BY", m)
        # sabotage: no slice, no print-ready promise
        m2 = share.message("Robot", "", b, self.FILES, None, "CC BY")
        self.assertNotIn("press Print", m2)
        self.assertIn("up to 155 g of PLA", m2)

    def test_post_text(self):
        res = {"text": "A robot.", "bill": share.bill(BOM, spec_fn=specs),
               "plates": {"ok": True, "seconds": 600, "grams": 12.0, "plates": [{}]}}
        t = share.post_text(res)
        self.assertTrue(t.startswith("A robot."))
        self.assertIn("Prints in 4 parts, about 10 min and 12 g.", t)
        self.assertIn("Atech: Atech board, DC Motor", t)

    def test_status(self):
        self.assertIn("Not printed", share.status_line({}))
        self.assertIn("Not printed", share.status_line({"printed": {"when": None}}))
        self.assertEqual(share.status_line({"printed": {"when": "9 Nov"}}), "Printed on 9 Nov.")


class Viewer(unittest.TestCase):
    def test_page_carries_every_part(self):
        pos, idx = share._box_mesh((0, 0, 0, 10, 20, 30))
        self.assertEqual((len(pos), len(idx)), (72, 36))
        html = share.viewer_html("Box </script><b>", [
            {"name": "Box", "colour": "#ff0000", "kind": "print", "pos": pos, "idx": idx}],
            share.bill(BOM, spec_fn=specs), [("a.stl", "a part")], {"summary": "1 part"})
        self.assertEqual(html.count("</script>"), 1, "the title must not end the script")
        self.assertIn("<title>Box &lt;/script&gt;&lt;b&gt;</title>", html)
        data = json.loads(html.split("const D=", 1)[1].split(";\nconst $", 1)[0])
        p = data["parts"][0]
        got = array("f")
        got.frombytes(base64.b64decode(p["p"]))
        self.assertEqual(max(got), 30.0)
        self.assertEqual(len(base64.b64decode(p["i"])), 36 * 4)
        self.assertEqual(data["files"], [{"path": "a.stl", "what": "a part"}])
        for word in ("prefers-color-scheme", "data-theme", "max-width:760px", "webgl"):
            self.assertIn(word, html)
        self.assertNotIn("http://", html.split("<script>")[1].split("const D=")[0],
                         "the page loads nothing from the internet")


class Folder(unittest.TestCase):
    def test_ours_is_replaced_someone_elses_kept(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        ours = os.path.join(root, "Robot")
        os.makedirs(ours)
        open(os.path.join(ours, share.MARKER), "w").close()
        open(os.path.join(ours, "old.stl"), "w").close()
        self.assertEqual(share._fresh(ours), ours)
        self.assertEqual(os.listdir(ours), [])
        theirs = os.path.join(root, "Notes")
        os.makedirs(theirs)
        open(os.path.join(theirs, "mine.txt"), "w").close()
        self.assertEqual(share._fresh(theirs), theirs + " 2")
        self.assertEqual(os.listdir(theirs), ["mine.txt"])


class Connect(unittest.TestCase):
    def test_url_is_encoded(self):
        u = pp.connect_url("/tmp/My buddy.gcode.3mf", "My buddy & co")
        self.assertEqual(u, "bambu-connect://import-file?path=%2Ftmp%2FMy%20buddy.gcode.3mf"
                            "&name=My%20buddy%20%26%20co&version=1.0.0")

    def test_send_names_the_file_gcode_3mf(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        p = os.path.join(d, "Buddy.3mf")
        with open(p, "w") as fh:
            fh.write("x")
        seen = []
        url = pp.send_to_connect(p, "Buddy", seen.append)
        self.assertTrue(os.path.isfile(os.path.join(d, "Buddy.gcode.3mf")))
        # R1270: the system opener ("open" on macOS, "xdg-open" on Linux)
        self.assertEqual(seen, [[pp._opener(), url]])
        self.assertIn("Buddy.gcode.3mf", url)
        self.assertIn("name=Buddy&", url)

    def test_found_only_when_installed(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        self.assertIsNone(pp.bambu_connect((d,)))
        os.makedirs(os.path.join(d, "Bambu Connect.app"))
        self.assertEqual(pp.bambu_connect((d,)), os.path.join(d, "Bambu Connect.app"))


PACK_SCRIPT = r'''
import json, os, sys, zipfile
sys.path.insert(0, %(addon)r)
import FreeCAD as App, Part
from acadagent import share
doc = App.newDocument("Robot")
doc.Label = "Little robot"
a = doc.addObject("Part::Feature", "Body"); a.Shape = Part.makeBox(30, 20, 25)
b = doc.addObject("Part::Feature", "Lid"); b.Shape = Part.makeBox(30, 20, 4)
b.Placement.Base = App.Vector(0, 0, 25)
s = doc.addObject("Part::Feature", "M3_Screw"); s.Shape = Part.makeCylinder(1.5, 10)
s.Placement.Base = App.Vector(5, 5, 20)
col = {"Body": ((0.9, 0.85, 0.7), 0), "Lid": ((0.4, 0.6, 0.9), 0), "M3_Screw": ((0.2, 0.2, 0.2), 0)}
res = share.make_share(doc, text="Test", licence=%(licence)r, root=%(root)r,
                       slice_plates=False, picture=False, colours=col)
z = zipfile.ZipFile(res["zip"]).namelist()
html = open(res["html"], encoding="utf-8").read()
data = json.loads(html.split("const D=", 1)[1].split(";\nconst $", 1)[0])
print("PACK=" + json.dumps({"folder": res["folder"], "files": [f for f, _ in res["files"]],
      "zip": sorted(z), "parts": [(p["n"], p["c"], p["k"]) for p in data["parts"]],
      "bom": open(os.path.join(res["folder"], "BOM.csv")).read(),
      "listing": sorted(os.listdir(res["folder"]))}))
'''


@unittest.skipIf(FC is None, "needs freecadcmd (ATECH_FREECADCMD)")
class Pack(unittest.TestCase):
    def run_fc(self, licence="cc-by"):
        root = tempfile.mkdtemp(prefix="p2p-share-")
        self.addCleanup(shutil.rmtree, root, True)
        script = os.path.join(root, "pack.py")
        with open(script, "w") as fh:
            fh.write(PACK_SCRIPT % {"addon": ADDON, "root": root, "licence": licence})
        p = subprocess.run([FC, script], capture_output=True, text=True, timeout=600)
        out = p.stdout + p.stderr
        line = [ln for ln in out.splitlines() if ln.startswith("PACK=")]
        return (json.loads(line[-1][len("PACK="):]) if line else None), out

    def test_everything_in_one_folder(self):
        r, out = self.run_fc()
        self.assertIsNotNone(r, out[-3000:])
        self.assertTrue(r["folder"].endswith("Little robot"))
        for name in ("Little robot 3D.html", "Little robot.3mf", "BOM.csv", "shopping-list.md",
                     "assembly.md", "description.txt", "LICENCE.txt", "MESSAGE.txt",
                     "README.md", "Little robot - share.zip", "share.json", "parts"):
            self.assertIn(name, r["listing"])
        self.assertEqual(r["files"][0], "Little robot 3D.html")
        self.assertIn("Little robot/parts/Body.stl", r["zip"])
        self.assertIn("Little robot/parts/Little robot.step", r["zip"])
        self.assertIn("Little robot/MESSAGE.txt", r["zip"])
        self.assertNotIn("Little robot/share.json", r["zip"])
        self.assertNotIn("Little robot/Little robot - share.zip", r["zip"])
        self.assertEqual(sorted(r["parts"]), [["Body", "#e6d9b2", "print"],
                                              ["Lid", "#6699e6", "print"],
                                              ["M3_Screw", "#333333", "buy"]])
        self.assertIn("Buy,M3 Screw,1", r["bom"])
        self.assertIn("about 3.0 x 3.0 x 10.0 mm", r["bom"])

    def test_sabotage_no_derivatives_licence_still_shares(self):
        # a licence the user picks for their own design never blocks; only an
        # imported part's licence does (makerworld.publish_plan)
        r, out = self.run_fc("cc-by-nd")
        self.assertIsNotNone(r, out[-3000:])


class Window(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from PySide6 import QtWidgets
        except ImportError:
            raise unittest.SkipTest("needs PySide6 (the bundled python)")
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_make_then_send(self):
        d0 = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d0, True)
        for n in ("x - share.zip", "description.txt"):
            with open(os.path.join(d0, n), "w") as fh:
                fh.write("words")

        class Doc(object):
            Label = "Robot"
            Objects = []
        made, opened, ran = [], [], []

        def maker(doc, progress=None, **kw):
            made.append(kw)
            progress("working")
            return {"folder": d0, "zip": os.path.join(d0, "x - share.zip"),
                    "html": os.path.join(d0, "x.html"), "print_ready": None,
                    "plates": None, "bill": share.bill({"printed": [], "hardware": []}),
                    "plan": {}, "message": "hello", "notes": [], "files": [],
                    "status": "", "title": "Robot", "text": ""}
        d = share.ShareDialog(None, lambda: Doc(), opener=opened.append, runner=ran.append,
                              maker=maker)
        self.assertFalse(d.targets.isVisibleTo(d))
        d.make()
        self.assertEqual(made[0]["title"], "Robot")
        self.assertTrue(d.targets.isVisibleTo(d))
        d.send()
        self.assertEqual(ran[-1], ["open", "-R", os.path.join(d0, "x - share.zip")])
        from PySide6 import QtWidgets
        self.assertEqual(QtWidgets.QApplication.clipboard().text(), "hello")
        d.maker_world()
        self.assertEqual(opened[-1], "https://makerworld.com/en")
        self.assertEqual(QtWidgets.QApplication.clipboard().text(), "words")

    def test_sabotage_maker_fails(self):
        class Doc(object):
            Label = "Robot"
            Objects = []

        def maker(doc, progress=None, **kw):
            raise ValueError("Bracket is under the Standard Digital File License")
        d = share.ShareDialog(None, lambda: Doc(), maker=maker)
        d.make()
        self.assertIn("Standard Digital File License", d.status.text())
        self.assertFalse(d.targets.isVisibleTo(d))


if __name__ == "__main__":
    unittest.main()
