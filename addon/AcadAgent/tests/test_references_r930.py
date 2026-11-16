"""R930: files named in the chat are brought into the chat folder (refs/).

  TestFind       paths found in a message: file:// links (a drop on the
                 box), quoted paths with spaces, escaped and bare paths;
                 missing files and other kinds ignored
  TestAttach     a Bambu Studio 3MF (also .gcode.3mf) made into one STL per
                 object with its Bambu name and the plate picture; STL and
                 STEP copied; the same file not copied twice; the prompt
                 block names the copies, never the originals
  TestKit        agent_kit/atech_refs.py under freecadcmd, cwd = the chat
                 folder as in the sandbox: names, parts, mesh, solid, flat

    ATECH_FREECADCMD=<freecadcmd> python3 -m unittest -v test_references_r930
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
if ADDON not in sys.path:
    sys.path.insert(0, ADDON)

from acadagent import references as refs                  # noqa: E402

KIT = os.path.join(ADDON, "acadagent", "agent_kit")

CUBE_V = [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0),
          (0, 0, 10), (10, 0, 10), (10, 10, 10), (0, 10, 10)]
CUBE_T = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
          (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 32


def bambu_3mf(path, sliced=True):
    """Bambu Studio's layout: meshes in 3D/Objects, unnamed objects in the
    main model, the names in Metadata/model_settings.config."""
    ns = 'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"'
    pns = 'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06"'
    verts = "".join('<vertex x="%g" y="%g" z="%g"/>' % v for v in CUBE_V)
    tris = "".join('<triangle v1="%d" v2="%d" v3="%d"/>' % t for t in CUBE_T)
    obj = ('<?xml version="1.0"?><model unit="millimeter" %s><resources>'
           '<object id="1" type="model"><mesh><vertices>%s</vertices><triangles>%s'
           '</triangles></mesh></object></resources><build/></model>' % (ns, verts, tris))
    comp = ('<object id="%d" type="model"><components><component '
            'p:path="/3D/Objects/object_1.model" objectid="1" '
            'transform="1 0 0 0 1 0 0 0 1 %d 0 0"/></components></object>')
    main = ('<?xml version="1.0"?><model unit="millimeter" %s %s><resources>%s%s'
            '</resources><build><item objectid="2" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>'
            '<item objectid="4" transform="1 0 0 0 1 0 0 0 1 0 50 0"/></build></model>'
            % (ns, pns, comp % (2, 100), comp % (4, 0)))
    settings = ('<config><object id="2"><metadata key="name" value="Bottom-Cover.stl"/>'
                '</object><object id="4"><metadata key="name" value="Lid (top).stl"/>'
                '</object></config>')
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("3D/3dmodel.model", main)
        z.writestr("3D/Objects/object_1.model", obj)
        z.writestr("Metadata/model_settings.config", settings)
        z.writestr("Metadata/plate_1_small.png", PNG)
        z.writestr("Metadata/plate_1.png", PNG + b"big")
        if sliced:
            z.writestr("Metadata/plate_1.gcode", "G28\n" * 1000)


def cube_tris(dx=0.0):
    return [tuple((CUBE_V[i][0] + dx, CUBE_V[i][1], CUBE_V[i][2]) for i in t)
            for t in CUBE_T]


class _Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="atech-r930-")
        self.ws = os.path.join(self.tmp, "ws")
        os.makedirs(self.ws)
        self.files = os.path.join(self.tmp, "My Files")
        os.makedirs(self.files)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def touch(self, name, data=b"x"):
        p = os.path.join(self.files, name)
        with open(p, "wb") as fh:
            fh.write(data)
        return p


class TestFind(_Tmp):
    def test_file_url_from_a_drop(self):
        p = self.touch("crab plate.gcode.3mf")
        url = "file://" + p.replace(" ", "%20")
        self.assertEqual(refs.find_paths("%s\n\nUse this file and make it look cooler" % url), [p])

    def test_quoted_escaped_and_bare(self):
        a = self.touch("a b.step")
        b = self.touch("c d.stl")
        plain = os.path.join(self.tmp, "plain.STL")
        with open(plain, "wb") as fh:
            fh.write(b"x")
        text = 'use "%s" and %s, then %s.' % (a, b.replace(" ", "\\ "), plain)
        self.assertEqual(refs.find_paths(text), [a, b, plain])

    def test_tilde(self):
        home = os.path.expanduser("~")
        if not self.tmp.startswith(home):
            self.skipTest("temp folder is not under the home folder")
        p = self.touch("t.obj")
        self.assertEqual(refs.find_paths("this: ~" + p[len(home):]), [p])

    def test_ignored(self):
        self.touch("notes.txt")
        text = ("%s/notes.txt %s/missing.stl https://example.com/x.stl "
                "make it 3mm thicker" % (self.files, self.files))
        self.assertEqual(refs.find_paths(text), [])

    def test_once_each(self):
        p = self.touch("x.stl")
        url = "file://" + p.replace(" ", "%20")
        self.assertEqual(refs.find_paths("%s and again %s" % (p, url)), [p])

    def test_unquoted_spaces_when_the_file_is_there(self):
        p = self.touch("crab body.stl")
        self.assertEqual(refs.find_paths("use %s but adjust it for atech" % p), [p])
        self.assertEqual(refs.find_paths("use %s/no such.stl" % self.files), [])

    def test_slug(self):
        self.assertEqual(refs.slug("/a/Atech Crab PLA_plate1.gcode.3mf"), "atech_crab_pla_plate1")
        self.assertEqual(refs.slug("/a/x.STEP"), "x")


class TestAttach(_Tmp):
    def test_bambu_gcode_3mf(self):
        src = os.path.join(self.files, "crab_plate1.gcode.3mf")
        bambu_3mf(src)
        got = refs.attach(self.ws, [src])
        self.assertEqual(len(got), 1)
        a = got[0]
        self.assertTrue(a.ok, a.error)
        self.assertEqual(a.folder, "refs/crab_plate1")
        d = os.path.join(self.ws, "refs", "crab_plate1")
        info = json.load(open(os.path.join(d, "ref.json")))
        self.assertEqual([p["name"] for p in info["parts"]], ["bottom_cover", "lid_top"])
        self.assertTrue(info["sliced"])
        self.assertEqual(info["parts"][0]["size"], [10, 10, 10])
        self.assertEqual(info["parts"][0]["min"], [100, 0, 0])
        self.assertEqual(info["parts"][1]["min"], [0, 50, 0])
        self.assertEqual(info["parts"][0]["triangles"], 12)
        # one STL per object, read back the same; the big plate picture
        tris = refs.read_stl(os.path.join(d, "bottom_cover.stl"))
        self.assertEqual(len(tris), 12)
        with open(os.path.join(d, "picture.png"), "rb") as fh:
            self.assertTrue(fh.read().endswith(b"big"))
        self.assertFalse([f for f in os.listdir(d) if f.endswith(".gcode")])
        readme = open(os.path.join(d, "README.md")).read()
        self.assertIn("atech_refs.solid('crab_plate1', 'bottom_cover')", readme)
        self.assertIn("atech_refs.keep('crab_plate1', 'bottom_cover')", readme)
        self.assertIn("Mesh::Feature is not built", readme)
        self.assertIn("not assembled", readme)

    def test_prompt_block_names_copies_not_originals(self):
        src = os.path.join(self.files, "crab.3mf")
        bambu_3mf(src, sliced=False)
        block = refs.prompt_block(refs.attach(self.ws, [src]))
        self.assertIn("refs/crab/", block)
        self.assertIn("bottom_cover", block)
        self.assertIn("refs/crab/picture.png", block)
        self.assertIn("For Atech", block)
        self.assertNotIn(self.files, block)
        self.assertEqual(refs.prompt_block([]), "")

    def test_same_file_once_other_file_beside(self):
        src = self.touch("part.stl")
        refs.write_stl(src, cube_tris())
        first = refs.attach(self.ws, [src])[0]
        stamp = os.path.getmtime(os.path.join(self.ws, first.folder, "ref.json"))
        again = refs.attach(self.ws, [src])[0]
        self.assertEqual(again.folder, first.folder)
        self.assertEqual(os.path.getmtime(os.path.join(self.ws, again.folder, "ref.json")), stamp)
        other = os.path.join(self.tmp, "part.stl")
        refs.write_stl(other, cube_tris(5))
        b = refs.attach(self.ws, [other])[0]
        self.assertNotEqual(b.folder, first.folder)
        self.assertTrue(os.path.isfile(os.path.join(self.ws, first.folder, "model.stl")))
        self.assertEqual(b.info["parts"][0]["min"], [5, 0, 0])

    def test_step_and_picture_copied(self):
        step = self.touch("bracket.step", b"ISO-10303-21;")
        pic = self.touch("sketch.png", PNG)
        got = refs.attach(self.ws, [step, pic])
        self.assertTrue(all(a.ok for a in got))
        self.assertTrue(os.path.isfile(os.path.join(self.ws, "refs/bracket/model.step")))
        self.assertEqual(got[1].info["picture"], "picture.png")
        self.assertIn("refs/sketch/picture.png", refs.prompt_block(got))

    def test_broken_file_reported(self):
        bad = self.touch("broken.3mf", b"not a zip")
        got = refs.attach(self.ws, [bad])
        self.assertFalse(got[0].ok)
        self.assertIn("could not be brought in", refs.prompt_block(got))


def _fc():
    try:
        from acadagent import sandbox
        return sandbox.find_freecadcmd()
    except Exception:                                      # noqa: BLE001
        return os.environ.get("ATECH_FREECADCMD")


FC = _fc()

KIT_SCRIPT = r'''
import json, sys
sys.path.append(%(kit)r)
import atech_refs as R
out = {}
out["names"] = R.names()
out["parts"] = R.parts("crab")
m = R.mesh("crab", "lid_top")
out["facets"] = m.CountFacets
s = R.solid("crab", "bottom_cover")
out["valid"] = s.isValid()
out["volume"] = round(s.Volume, 3)
out["xmin"] = round(s.BoundBox.XMin, 3)
f = R.solid("crab", "bottom_cover", flat=True)
out["flat"] = [round(f.BoundBox.XMin, 3), round(f.BoundBox.ZMin, 3)]
cut = s.cut(__import__("Part").makeBox(5, 5, 20, __import__("FreeCAD").Vector(100, 0, -5)))
out["cut"] = round(cut.Volume, 3)
k = R.keep("crab", "lid_top", flat=True)
out["keep"] = [k.ShapeType, round(k.Volume, 3), round(k.BoundBox.ZMin, 3)]
try:
    R.solid("crab", "nope")
    out["err"] = ""
except R.RefError as e:
    out["err"] = str(e)
try:
    R.solid("crab")
except R.RefError as e:
    out["many"] = str(e)
print("REFS_RESULT=" + json.dumps(out))
'''


@unittest.skipIf(FC is None, "freecadcmd not found (set ATECH_FREECADCMD)")
class TestKit(_Tmp):
    def test_atech_refs_in_the_chat_folder(self):
        src = os.path.join(self.files, "crab.gcode.3mf")
        bambu_3mf(src)
        refs.attach(self.ws, [src])
        script = os.path.join(self.tmp, "kit_refs.py")
        with open(script, "w") as fh:
            fh.write(KIT_SCRIPT % {"kit": KIT})
        env = {"HOME": self.tmp, "FREECAD_USER_HOME": self.tmp, "PATH": "/usr/bin:/bin"}
        p = subprocess.run([FC, script], env=env, cwd=self.ws,
                           capture_output=True, text=True, timeout=300)
        line = [ln for ln in (p.stdout + p.stderr).splitlines()
                if ln.startswith("REFS_RESULT=")]
        self.assertTrue(line, (p.stdout + p.stderr)[-2000:])
        r = json.loads(line[-1].split("=", 1)[1])
        self.assertEqual(r["names"], ["crab"])
        self.assertEqual(r["parts"], ["bottom_cover", "lid_top"])
        self.assertEqual(r["facets"], 12)
        self.assertTrue(r["valid"])
        self.assertAlmostEqual(r["volume"], 1000.0, places=1)
        self.assertAlmostEqual(r["xmin"], 100.0, places=2)
        self.assertEqual(r["flat"], [-5.0, 0.0])
        self.assertAlmostEqual(r["cut"], 750.0, places=1)
        self.assertEqual(r["keep"], ["Solid", 1000.0, 0.0])
        self.assertIn("its parts: bottom_cover, lid_top", r["err"])
        self.assertIn("has 2 parts", r["many"])


if __name__ == "__main__":
    unittest.main()
