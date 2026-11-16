"""R970: GLB / glTF import, "Import a model to change", and the examples
gallery.

    cd addon/AcadAgent/tests && python3 -m unittest test_import_gallery_r970

The glTF reader, the references it feeds, the import script and the
gallery's catalogue need no FreeCAD and no Qt. The Qt parts (Home's short
example row + "All examples", the gallery window) skip without PySide6;
the import build through ./check skips without freecadcmd.
"""
import base64
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
sys.path.insert(0, ADDON)

from acadagent import examples_gallery as eg  # noqa: E402
from acadagent import gltf, references  # noqa: E402

MODELS = os.path.normpath(os.path.join(ADDON, "..", "..", "models"))
BUTTON_GLB = os.path.join(MODELS, "glb", "button.glb")

try:
    from PySide6 import QtWidgets  # noqa: F401
    HAVE_QT = True
except Exception:                                      # noqa: BLE001
    HAVE_QT = False


# ------------------------------------------------------------------ fixtures
CUBE_POS = [(x, y, z) for x in (0.0, 0.01) for y in (0.0, 0.02) for z in (0.0, 0.03)]
CUBE_TRI = [0, 1, 3, 0, 3, 2, 4, 6, 7, 4, 7, 5, 0, 4, 5, 0, 5, 1,
            2, 3, 7, 2, 7, 6, 0, 2, 6, 0, 6, 4, 1, 5, 7, 1, 7, 3]


def _gltf_doc(bin_len, uri=None, extensions=None, node=None, mode=4):
    buf = {"byteLength": bin_len}
    if uri:
        buf["uri"] = uri
    doc = {
        "asset": {"version": "2.0"},
        "scene": 0, "scenes": [{"nodes": [0]}],
        "nodes": [dict({"name": "Body", "mesh": 0}, **(node or {}))],
        "meshes": [{"name": "cube", "primitives": [
            {"attributes": {"POSITION": 0}, "indices": 1, "material": 0, "mode": mode}]}],
        "materials": [{"pbrMetallicRoughness": {"baseColorFactor": [1.0, 0.0, 0.0, 1.0]}}],
        "buffers": [buf],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 96},
                        {"buffer": 0, "byteOffset": 96, "byteLength": 72}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 8, "type": "VEC3"},
            {"bufferView": 1, "componentType": 5123, "count": 36, "type": "SCALAR"}],
    }
    if extensions:
        doc["extensionsUsed"] = extensions
    return doc


def _bin():
    b = struct.pack("<24f", *[c for p in CUBE_POS for c in p])
    return b + struct.pack("<36H", *CUBE_TRI)


def write_glb(path, **kw):
    binary = _bin()
    js = json.dumps(_gltf_doc(len(binary), **kw)).encode()
    js += b" " * (-len(js) % 4)
    binary += b"\0" * (-len(binary) % 4)
    body = (struct.pack("<II", len(js), 0x4E4F534A) + js
            + struct.pack("<II", len(binary), 0x004E4942) + binary)
    with open(path, "wb") as fh:
        fh.write(struct.pack("<III", 0x46546C67, 2, 12 + len(body)) + body)
    return path


class GltfReader(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="r970-")

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_glb_cube_in_mm_z_up(self):
        parts = gltf.read(write_glb(os.path.join(self.d, "c.glb")))
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0].name, "Body")
        self.assertEqual(len(parts[0].triangles), 12)
        # 10 x 20 x 30 mm in glTF (x, y up, z) -> FreeCAD (x, -z, y)
        sx, sy, sz = gltf.size_mm(parts)
        self.assertAlmostEqual(sx, 10.0, 3)
        self.assertAlmostEqual(sy, 30.0, 3)
        self.assertAlmostEqual(sz, 20.0, 3)
        self.assertEqual(parts[0].color[:3], (1.0, 0.0, 0.0))

    def test_node_transform_applied(self):
        p = write_glb(os.path.join(self.d, "t.glb"),
                      node={"translation": [0.1, 0.0, 0.0], "scale": [2, 2, 2]})
        parts = gltf.read(p)
        xs = [v[0] for t in parts[0].triangles for v in t]
        self.assertAlmostEqual(min(xs), 100.0, 3)
        self.assertAlmostEqual(max(xs), 120.0, 3)

    def test_gltf_json_with_data_uri(self):
        binary = _bin()
        uri = "data:application/octet-stream;base64," + base64.b64encode(binary).decode()
        p = os.path.join(self.d, "c.gltf")
        with open(p, "w") as fh:
            json.dump(_gltf_doc(len(binary), uri=uri), fh)
        self.assertEqual(len(gltf.read(p)[0].triangles), 12)

    def test_gltf_with_bin_beside_it_and_missing(self):
        binary = _bin()
        with open(os.path.join(self.d, "c.bin"), "wb") as fh:
            fh.write(binary)
        p = os.path.join(self.d, "c.gltf")
        with open(p, "w") as fh:
            json.dump(_gltf_doc(len(binary), uri="c.bin"), fh)
        self.assertEqual(len(gltf.read(p)[0].triangles), 12)
        os.remove(os.path.join(self.d, "c.bin"))
        with self.assertRaises(gltf.GltfError) as cm:
            gltf.read(p)
        self.assertIn("c.bin", str(cm.exception))

    def test_compressed_is_refused_with_a_way_out(self):
        p = write_glb(os.path.join(self.d, "d.glb"),
                      extensions=["KHR_draco_mesh_compression"])
        with self.assertRaises(gltf.GltfError) as cm:
            gltf.read(p)
        self.assertIn("Draco", str(cm.exception))
        self.assertIn("without compression", str(cm.exception))

    def test_not_a_gltf(self):
        p = os.path.join(self.d, "x.glb")
        with open(p, "wb") as fh:
            fh.write(b"solid nope")
        with self.assertRaises(gltf.GltfError):
            gltf.read(p)

    def test_sabotage_points_only_holds_no_triangles(self):
        p = write_glb(os.path.join(self.d, "p.glb"), mode=0)
        with self.assertRaises(gltf.GltfError) as cm:
            gltf.read(p)
        self.assertIn("no triangles", str(cm.exception))

    @unittest.skipUnless(os.path.isfile(BUTTON_GLB), "models/glb not here")
    def test_real_module_glb_matches_the_catalogue(self):
        # ATECH_PRODUCTS.md: button 19.50 x 10.04 x 19.50 (row x up x slide)
        sx, sy, sz = gltf.size_mm(gltf.read(BUTTON_GLB))
        self.assertAlmostEqual(sx, 19.5, 1)
        self.assertAlmostEqual(sy, 19.5, 1)
        self.assertAlmostEqual(sz, 10.0, 1)


class ReferencesAndImportScript(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="r970-")
        self.ws = os.path.join(self.d, "ws")
        os.makedirs(self.ws)

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_glb_is_a_named_file(self):
        p = write_glb(os.path.join(self.d, "my lamp.glb"))
        self.assertEqual(references.find_paths('use "%s" please' % p), [p])

    def test_attach_writes_a_stl_per_part_with_colour(self):
        p = write_glb(os.path.join(self.d, "lamp.glb"))
        got = references.attach(self.ws, [p])
        self.assertTrue(got[0].ok, got[0].error)
        info = got[0].info
        self.assertEqual(info["kind"], "gltf")
        self.assertEqual([q["name"] for q in info["parts"]], ["body"])
        self.assertEqual(info["parts"][0]["color"], [1.0, 0.0, 0.0])
        self.assertTrue(os.path.isfile(os.path.join(self.ws, "refs", "lamp", "body.stl")))
        self.assertIn("GLB / glTF", references.prompt_block(got))

    def test_import_script_keeps_every_part_side_by_side(self):
        a = write_glb(os.path.join(self.d, "lamp.glb"))
        b = write_glb(os.path.join(self.d, "shade.glb"))
        got = references.attach(self.ws, [a, b])
        code, labels = references.import_script(got)
        compile(code, "model.py", "exec")
        self.assertEqual(labels, ["Lamp", "Shade"])
        self.assertIn("atech_refs.keep(ref, part)", code)
        self.assertIn("('lamp', 'body', 'Lamp', (1.0, 0.0, 0.0), 0.0)", code)
        # the second file starts 15 mm past the first one's 10 mm
        self.assertIn("('shade', 'body', 'Shade', (1.0, 0.0, 0.0), 25.0)", code)

    def test_generic_part_names_take_the_file_name(self):
        if not os.path.isfile(BUTTON_GLB):
            self.skipTest("models/glb not here")
        got = references.attach(self.ws, [BUTTON_GLB])
        _code, labels = references.import_script(got)
        self.assertEqual(labels[0], "Button 1")
        self.assertEqual(len(labels), len(set(labels)))


class Catalogue(unittest.TestCase):
    def test_every_catalogue_example_exists_and_has_a_picture(self):
        disk = set(eg._on_disk())
        for key, title, line, cat in eg.CATALOG:
            with self.subTest(example=key):
                self.assertIn(key, disk)
                self.assertIn(cat, eg.CATEGORIES)
                self.assertTrue(eg.picture(key), "example_pictures/%s.png" % key)
                self.assertTrue(line.endswith("."))

    def test_every_product_example_is_listed(self):
        keys = {r["key"] for r in eg.entries(shipped={})}
        for key in eg._on_disk():
            req = eg._request(os.path.join(eg.EXAMPLES_DIR, key + ".py"))
            if req:
                self.assertIn(key, keys)

    def test_new_example_without_a_row_still_shows(self):
        d = tempfile.mkdtemp()
        try:
            with open(os.path.join(d, "lava_lamp.py"), "w") as fh:
                fh.write('"""Example: "a lava lamp" - test."""\n')
            rows = eg.entries(shipped={}, folder=d)
            self.assertEqual([(r["key"], r["category"], r["line"]) for r in rows],
                             [("lava_lamp", eg.MORE, "A lava lamp.")])
        finally:
            shutil.rmtree(d)

    def test_shipped_projects_are_preferred(self):
        rows = eg.entries(shipped={"hype_button": "Hype button"})
        row = next(r for r in rows if r["key"] == "hype_button")
        self.assertEqual(row["shipped"], "Hype button")
        import acadagent
        fake = mock.Mock()
        with mock.patch.dict(sys.modules, {"acadagent.shell": fake}), \
                mock.patch.object(acadagent, "shell", fake, create=True):
            eg.start(row)
            eg.start(next(r for r in rows if r["key"] == "toy_car"))
        fake.open_default.assert_called_once_with("Hype button")
        fake.open_example.assert_called_once_with("toy_car")

    def test_search_and_category(self):
        rows = eg.entries(shipped={})
        self.assertEqual([r["key"] for r in rows if eg.matches(r, "duck")], ["debug_duck"])
        new = [r for r in rows if eg.matches(r, category=eg.NEW)]
        self.assertEqual(len(new), 10)
        self.assertEqual([r["key"] for r in rows if eg.matches(r, "bird feeder")],
                         ["bird_cam"])
        self.assertFalse([r for r in rows if eg.matches(r, "zzzz")])


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class GalleryWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_cards_filter_and_choose(self):
        rows = eg.entries(shipped={})
        got = []
        dlg = eg.ExamplesDialog(rows=rows, on_start=got.append)
        self.assertEqual(len(dlg.cards), len(rows))
        self.assertEqual(len(dlg.shown()), len(rows))
        dlg.set_category(eg.NEW)
        self.assertEqual(len(dlg.shown()), 10)
        dlg.set_category(None)
        dlg.search.setText("turntable")
        self.assertEqual([c.row["key"] for c in dlg.shown()], ["photo_turntable"])
        self.assertTrue(dlg.shown()[0]._pixmap, "the picture is loaded")
        dlg.search.setText("zzzz")
        self.assertFalse(dlg.shown())
        self.assertIn("No example matches", dlg.empty.text())
        dlg.search.setText("duck")
        dlg.shown()[0].clicked.emit()
        self.assertEqual(dlg.chosen["key"], "debug_duck")
        dlg._on_start(dlg.chosen)
        self.assertEqual([r["key"] for r in got], ["debug_duck"])
        dlg.close()


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class HomeAndImport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        from acadagent import shell
        cls.shell = shell

    def test_glb_is_imported_and_dropped(self):
        s = self.shell
        self.assertIn(".glb", s.IMPORT_EXT)
        self.assertIn(".gltf", s.IMPORT_EXT)
        d = tempfile.mkdtemp()
        p = write_glb(os.path.join(d, "a.glb"))
        self.assertEqual(s.droppable([p]), [p])

    def test_import_files_uses_the_chat(self):
        s = self.shell
        d = tempfile.mkdtemp()
        p = write_glb(os.path.join(d, "a.glb"))
        hook = mock.Mock(return_value="STATE")
        panel = mock.Mock(start_from_files=hook)
        with mock.patch.object(s, "chat_panel", return_value=panel), \
                mock.patch.object(s, "show_chat"), \
                mock.patch.object(s, "_leave_home"):
            self.assertEqual(s.import_files([p, os.path.join(d, "x.txt")]), "STATE")
        hook.assert_called_once_with([p], None)

    def test_sabotage_without_the_chat_it_opens_plain(self):
        s = self.shell
        d = tempfile.mkdtemp()
        p = write_glb(os.path.join(d, "a.glb"))
        with mock.patch.object(s, "chat_panel", return_value=None), \
                mock.patch.object(s, "_leave_home"), \
                mock.patch.object(s, "open_paths", return_value=["A"]) as op:
            self.assertEqual(s.import_files([p]), ["A"])
        op.assert_called_once_with([p])

    def test_home_drop_imports_to_change(self):
        s = self.shell
        d = tempfile.mkdtemp()
        p = write_glb(os.path.join(d, "a.glb"))
        with mock.patch.object(s, "adds_to_design", return_value=False), \
                mock.patch.object(s, "_import_hook", return_value=object()), \
                mock.patch.object(s, "import_files", return_value="S") as imp, \
                mock.patch.object(s, "open_paths", return_value=[]) as op:
            self.assertEqual(s.drop_paths([p]), ["S"])
        imp.assert_called_once_with([p])
        op.assert_called_once_with([])

    def test_commands_offer_import_and_examples(self):
        keys = {c[3] for c in self.shell.TOOL_COMMANDS}
        self.assertIn("importmodel", keys)
        self.assertIn("examples", keys)

    def test_home_short_row_and_all_examples(self):
        home = self.shell.HomeView()
        try:
            home.resize(1200, 900)
            home._layout_cards(4)
            shown = [c for c in home.example_cards if not c.isHidden()]
            self.assertLessEqual(len(shown), 7)
            self.assertFalse(home.all_examples_card.isHidden())
            self.assertIn("examples", home.all_examples_card.accessibleName().lower())
            self.assertTrue(home.btn_import.toolTip())
            with mock.patch.object(self.shell, "show_examples") as se:
                home.all_examples_card.clicked.emit()
            se.assert_called_once()
        finally:
            home.close()


FC = os.environ.get("ATECH_FREECADCMD")
PROJECTS = os.path.normpath(os.path.join(ADDON, "..", "..", "projects"))
KIT = os.path.join(ADDON, "acadagent", "agent_kit")


@unittest.skipUnless(FC and os.path.isfile(FC), "set ATECH_FREECADCMD")
@unittest.skipUnless(os.path.isfile(BUTTON_GLB), "models/glb not here")
class ImportBuilds(unittest.TestCase):
    def test_imported_glb_and_stl_pass_check(self):
        """The project start_from_files makes: two files kept side by side,
        their own parts touching as their makers drew them - CHECK PASS,
        the touching said as IMPORTED warnings, never as problems."""
        ws = tempfile.mkdtemp(prefix="r970-ws-")
        try:
            got = references.attach(ws, [BUTTON_GLB, os.path.join(MODELS, "stl", "knob.stl")])
            code, labels = references.import_script(got)
            with open(os.path.join(ws, "model.py"), "w") as fh:
                fh.write(code)
            with open(os.path.join(ws, "intent.json"), "w") as fh:
                json.dump({"imported": labels}, fh)
            env = dict(os.environ, ATECH_CHECK_SCRIPT=os.path.join(ws, "model.py"),
                       ATECH_CHECK_PNG="", ATECH_CHECK_PATH=PROJECTS,
                       ATECH_ARTIFACTS=os.environ.get("ATECH_ARTIFACTS", MODELS))
            p = subprocess.run([FC, os.path.join(KIT, "check.py")], env=env, cwd=ws,
                               capture_output=True, text=True, timeout=900)
            out = p.stdout + p.stderr
            verdict = [ln for ln in out.splitlines() if ln.startswith("CHECK ")]
            self.assertEqual(verdict[-1:], ["CHECK PASS"], "\n".join(
                ln for ln in out.splitlines() if ln.startswith("PROBLEM"))[-2000:])
            self.assertIn("WARNING IMPORTED", out)
        finally:
            shutil.rmtree(ws, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
