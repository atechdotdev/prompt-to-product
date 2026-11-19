"""R980: electronic components from the KiCad 3D model library
(projects/kicad3d.py, the shipped kicad3d_index.json and kicad3d_pictures/,
step_colours.py, and the Modules page's "Add electronic component (KiCad)..."
dialog, which is shelf_dialog with kicad3d as its source).

    QT_QPA_PLATFORM=offscreen <bundled python> -m unittest -v test_kicad3d_r980

P2P_NET_TESTS=1 adds a real install from GitLab (one small model); it needs
FreeCAD (run it under freecadcmd, or with ATECH_FREECADCMD for the mesher).
"""
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(ADDON))
for p in (ADDON, os.path.join(REPO, "projects")):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import kicad3d  # noqa: E402
import shelf  # noqa: E402
import step_colours  # noqa: E402
import user_parts  # noqa: E402

try:
    from PySide6 import QtWidgets
    _APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    from acadagent import shelf_dialog as sdlg
except ImportError:                                    # no Qt here
    sdlg = None


class R(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestModule(unittest.TestCase):

    def test_urls_pinned_to_the_revision(self):
        u = kicad3d.file_url("Connector_JST.3dshapes/JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical.step")
        self.assertEqual(u, "https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/"
                         + kicad3d.REVISION + "/Connector_JST.3dshapes/"
                         "JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical.step")
        self.assertTrue(re.match(r"^[0-9a-f]{40}$", kicad3d.REVISION))
        self.assertIn("TerminalBlock_Phoenix_MKDS-1%2C5", kicad3d.file_url(
            "TerminalBlock_Phoenix.3dshapes/TerminalBlock_Phoenix_MKDS-1,5-2-5.08.step"))

    def test_fetch_checks_blob_and_size(self):
        data = b"ISO-10303-21;\nHEADER;\n"
        good = shelf.blob_id(data)
        real = shelf._get
        shelf._get = lambda url, timeout=0: R(data)
        d = tempfile.mkdtemp()
        try:
            p = os.path.join(d, "x.step")
            self.assertEqual(kicad3d.fetch("x.step", good, None, p), p)   # size unknown
            os.remove(p)
            self.assertEqual(kicad3d.fetch("x.step", good, len(data), p), p)
            os.remove(p)
            with self.assertRaises(shelf.ShelfError):
                kicad3d.fetch("x.step", "0" * 40, len(data), p)
            self.assertFalse(os.path.exists(p))
            with self.assertRaises(shelf.ShelfError):
                kicad3d.fetch("x.step", good, len(data) + 1, p)
            self.assertFalse(os.path.exists(p))
        finally:
            shelf._get = real
            shutil.rmtree(d, ignore_errors=True)

    def test_keys_and_names(self):
        for bad in ("../x", "nope", "", None, "jst_xh_4/.."):
            with self.assertRaises(shelf.ShelfError):
                kicad3d.check_key(bad)
        self.assertEqual(kicad3d.part_name("jst_xh_4"), "kc_jst_xh_4")
        for key in kicad3d.index()["parts"]:
            self.assertTrue(user_parts.NAME_RE.match(kicad3d.part_name(key)), key)

    def test_search(self):
        self.assertIn("jst_xh_4", [k for k, _ in kicad3d.search("jst xh 4")])
        self.assertIn("usb_c_16p", [k for k, _ in kicad3d.search("USB-C")])
        self.assertTrue(all(e["group"] == "power" for _k, e in kicad3d.search(group="power")))
        # the file name is searched too
        self.assertIn("relay_srd", [k for k, _ in kicad3d.search("SANYOU")])

    def test_attribution_names_the_library_and_licence(self):
        a = kicad3d.attribution(kicad3d.index()["parts"]["led_5mm"])
        self.assertIn("KiCad library contributors", a)
        self.assertIn("CC BY-SA 4.0", a)
        self.assertIn("LED_D5.0mm.step", a)

    def test_no_email_addresses(self):
        """verify_tree's personal-data row refuses @gmail.com in the bundle
        (17 Nov 2026: a STEP header's author address stopped a build); the
        name stays as the credit."""
        for key, p in kicad3d.index()["parts"].items():
            self.assertFalse([a for a in p.get("authors") or () if "@" in a], key)
        import ast
        src = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))),
                           "projects", "build_kicad3d_index.py")
        with open(src, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "step_author"]
        ns = {"re": re}
        exec(compile(ast.Module(body=fn, type_ignores=[]), src, "exec"), ns)  # noqa: S102
        head = b"FILE_NAME('x.step','2020',('Rene Poeschl','someone@gmail.com'),('KiCad'),'','','');"
        self.assertEqual(ns["step_author"](head), ["Rene Poeschl"])

    def test_picture_never_outside_its_folder(self):
        idx = kicad3d._INDEX
        kicad3d._INDEX = json.loads(json.dumps(kicad3d.index()))
        try:
            kicad3d._INDEX["parts"]["led_5mm"]["picture"] = "../kicad3d.py"
            self.assertIsNone(kicad3d.thumbnail("led_5mm"))
        finally:
            kicad3d._INDEX = idx


class TestShippedIndex(unittest.TestCase):

    def test_every_entry_is_complete(self):
        idx = kicad3d.index()
        self.assertEqual(idx["revision"], kicad3d.REVISION)
        self.assertEqual(idx["licence"], "CC BY-SA 4.0")
        self.assertEqual(idx["count"], len(idx["parts"]))
        self.assertGreaterEqual(len(idx["parts"]), 100)
        groups = dict(kicad3d.GROUPS)
        for key, e in idx["parts"].items():
            self.assertIn(e["group"], groups, key)
            self.assertIn(e["category"], user_parts.CATEGORIES, key)
            self.assertTrue(re.match(r"^[0-9a-f]{40}$", e["git_oid"]), key)
            self.assertTrue(e["path"].split("/")[0].endswith(".3dshapes"), key)
            self.assertTrue(e["path"].lower().endswith(".step"), key)
            self.assertGreater(e["bytes"], 1000, key)
            self.assertEqual(len(e["size_mm"]), 3, key)
            self.assertTrue(all(0.5 <= s <= 200 for s in e["size_mm"]), (key, e["size_mm"]))
            self.assertIn("KiCad library contributors", e["authors"], key)
            self.assertTrue(e["description"], key)
            self.assertIsNotNone(kicad3d.thumbnail(key), key)

    def test_measured_sizes_match_datasheets(self):
        p = kicad3d.index()["parts"]
        # MEASURED from the models; these are the datasheet figures
        self.assertEqual(p["esp32_wroom_32e"]["size_mm"][:2], [18.0, 25.5])
        self.assertEqual(p["pico"]["size_mm"][:2], [21.0, 52.3])
        self.assertAlmostEqual(p["pin_header_1x08"]["size_mm"][1], 8 * 2.54, places=2)
        self.assertAlmostEqual(p["jst_xh_4"]["size_mm"][0], 12.4, places=1)


TINY = """ISO-10303-21;
HEADER;
FILE_NAME('x','2026',('Jane'),('Org'),'','','');
ENDSEC;
DATA;
#1 = MANIFOLD_SOLID_BREP('',#2);
#2 = CLOSED_SHELL('',(#3,#4));
#3 = ADVANCED_FACE('',(#9),#5,.T.);
#4 = ADVANCED_FACE('',(#9),#6,.T.);
#5 = PLANE('',#9);
#6 = CYLINDRICAL_SURFACE('',#9,1.);
#9 = CARTESIAN_POINT('',(0.,0.,0.));
#10 = STYLED_ITEM('color',(#11),#1);
#11 = PRESENTATION_STYLE_ASSIGNMENT((#12));
#12 = SURFACE_STYLE_USAGE(.BOTH.,#13);
#13 = SURFACE_SIDE_STYLE('',(#14));
#14 = SURFACE_STYLE_FILL_AREA(#15);
#15 = FILL_AREA_STYLE('',(#16));
#16 = FILL_AREA_STYLE_COLOUR('',#17);
#17 = COLOUR_RGB('',0.1,0.2,0.3);
#20 = STYLED_ITEM('color',(#21),#4);
#21 = PRESENTATION_STYLE_ASSIGNMENT((#22));
#22 = SURFACE_STYLE_USAGE(.BOTH.,#23);
#23 = SURFACE_SIDE_STYLE('',(#24));
#24 = SURFACE_STYLE_FILL_AREA(#25);
#25 = FILL_AREA_STYLE('',(#26));
#26 = FILL_AREA_STYLE_COLOUR('',#27);
#27 = DRAUGHTING_PRE_DEFINED_COLOUR('black');
ENDSEC;
END-ISO-10303-21;
"""


class TestStepColours(unittest.TestCase):

    def test_styles_and_solids(self):
        ents = step_colours.parse(TINY)
        self.assertEqual(step_colours.styles(ents), {1: (0.1, 0.2, 0.3), 4: (0, 0, 0)})
        self.assertEqual(step_colours.solids(ents), [(1, [3, 4], ("Plane", "Cylinder"))])

    def test_faces_take_their_own_colour_else_their_solids(self):
        class F(object):
            def __init__(self, s):
                self.Surface = type(s, (), {})()

        class S(object):
            Faces = [F("Plane"), F("Cylinder")]

        class Shape(object):
            Solids = [S()]
        fc, matched, total = step_colours.face_colours(Shape(), TINY)
        self.assertEqual((matched, total), (1, 1))
        self.assertEqual([c for _f, c in fc], [(0.1, 0.2, 0.3), (0, 0, 0)])

    def test_unmatched_solid_is_default_grey(self):
        class F(object):
            Surface = type("Toroid", (), {})()

        class S(object):
            Faces = [F()]

        class Shape(object):
            Solids = [S()]
        fc, matched, _t = step_colours.face_colours(Shape(), TINY)
        self.assertEqual(matched, 0)
        self.assertEqual(fc[0][1], step_colours.DEFAULT)


@unittest.skipIf(sdlg is None, "PySide6 is not available")
class TestDialog(unittest.TestCase):

    def test_kicad_source_shows_its_own_words(self):
        real = kicad3d.installed
        kicad3d.installed = lambda: {"led_5mm": "kc_led_5mm"}
        try:
            d = sdlg.ShelfDialog(shelf=kicad3d, freecadcmd="")
            self.assertEqual(d.windowTitle(), kicad3d.TITLE)
            self.assertEqual(d.list.count(), len(kicad3d.index()["parts"]))
            self.assertIn("JST", d.query.placeholderText())
            d.query.setText("LED 5 mm")
            texts = [d.list.item(i).text() for i in range(d.list.count())]
            self.assertTrue(any("installed" in t for t in texts), texts)
            self.assertIn("CC BY-SA 4.0", d.info.text())
            d.group.setCurrentIndex([d.group.itemData(i) for i in range(d.group.count())]
                                    .index("connectors"))
            d.query.setText("")
            self.assertGreater(d.list.count(), 30)
            d.close()
        finally:
            kicad3d.installed = real

    def test_shelf_source_keeps_its_words(self):
        d = sdlg.ShelfDialog(shelf=shelf, freecadcmd="")
        self.assertEqual(d.windowTitle(), "Off-the-shelf parts")
        d.close()


@unittest.skipUnless(os.environ.get("P2P_NET_TESTS") == "1", "P2P_NET_TESTS=1 for network")
class TestNetInstall(unittest.TestCase):

    def test_install_a_jst_header(self):
        try:
            import FreeCAD  # noqa: F401
        except ImportError:
            self.skipTest("needs FreeCAD (run under freecadcmd)")
        d = tempfile.mkdtemp()
        old = os.environ.get(user_parts.PARTS_ENV)
        os.environ[user_parts.PARTS_ENV] = d
        try:
            name, sp = kicad3d.install("jst_xh_2")
            self.assertEqual(name, "kc_jst_xh_2")
            self.assertEqual(sp["licence"], "CC BY-SA 4.0")
            self.assertEqual(sp["kicad3d"]["revision"], kicad3d.REVISION)
            self.assertIn(name, user_parts.specs())
            self.assertEqual(kicad3d.installed(), {"jst_xh_2": name})
        finally:
            if old is None:
                os.environ.pop(user_parts.PARTS_ENV, None)
            else:
                os.environ[user_parts.PARTS_ENV] = old
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
