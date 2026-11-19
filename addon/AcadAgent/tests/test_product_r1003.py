"""R1003: prompt to product steps, assembly and the product pack
(acadagent/product.py). Pure: no FreeCAD, no Qt.

    python -m unittest test_product_r1003
"""
import json
import os
import sys
import tempfile
import unittest

os.environ["ATECH_SDK_CATALOG"] = "snapshot"
HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
if ADDON not in sys.path:
    sys.path.insert(0, ADDON)

from acadagent import product as P  # noqa: E402

E = P.kit()

ATECH = {"modules": [
    {"module": "usbc", "ports": [8]}, {"module": "light", "ports": [3]},
    {"module": "screen", "ports": [9, 10]},
    {"module": "knob", "ports": [1, 2], "joint": "cable",
     "cables": [{"port": 1, "length": 82.4, "state": "ok"},
                {"port": 2, "length": 80.0, "state": "ok"}]}]}
BOM = {"printed": [
    {"part": "Body", "count": 1, "names": ["Body"], "volume_cm3": 40, "mass_g": 49.6,
     "colour": "orange"},
    {"part": "Foot", "count": 2, "names": ["Foot_L", "Foot_R"], "volume_cm3": 2,
     "mass_g": 2.5, "colour": "black"}],
    "hardware": [
    {"kind": "Board", "name": "Atech board", "ports": "", "length_mm": None, "label": "b"},
    {"kind": "Module", "name": "Light", "ports": "3", "length_mm": None, "label": "l"},
    {"kind": "Cable", "name": "Cable to Knob", "ports": "1", "length_mm": 82.4, "label": "c"}]}


def facts(**kw):
    f = {"project": "Desk buddy", "built": True, "check": "pass",
         "levels": {"done": 9, "total": 9}, "bom": BOM,
         "electrical": E.analyse(ATECH, project="Desk buddy"), "sdk": None, "state": {}}
    f.update(kw)
    return f


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def by_key(ss):
    return {s["key"]: s for s in ss}


class Steps(unittest.TestCase):
    def test_seven_in_order(self):
        ss = P.steps(facts())
        self.assertEqual([s["key"] for s in ss], [k for k, _t, _i in P.STEPS])

    def test_not_built(self):
        ss = by_key(P.steps(facts(built=False, bom=None, electrical=None)))
        self.assertEqual(ss["design"]["state"], P.TODO)
        self.assertEqual(ss["design"]["action"], "chat")
        self.assertTrue(all(s["state"] == P.TODO for s in ss.values()))

    def test_levels_in_progress(self):
        ss = by_key(P.steps(facts(levels={"done": 4, "total": 9})))
        self.assertEqual(ss["design"]["state"], P.READY)
        self.assertIn("4 of 9", ss["design"]["line"])

    def test_check_failing(self):
        self.assertEqual(by_key(P.steps(facts(check="fail")))["design"]["state"], P.WARN)

    def test_electronics_states(self):
        ss = by_key(P.steps(facts()))
        self.assertEqual(ss["electronics"]["state"], P.DONE)
        bad = E.analyse({"modules": [{"module": "light", "ports": [3]}]})
        ss = by_key(P.steps(facts(electrical=bad)))
        self.assertEqual(ss["electronics"]["state"], P.BLOCKED)
        self.assertTrue(ss["electronics"]["detail"])

    def test_print_only_product(self):
        ss = by_key(P.steps(facts(electrical=E.analyse({"modules": []}))))
        self.assertIn("print-only", ss["electronics"]["line"])
        self.assertEqual(ss["firmware"]["state"], P.DONE)
        self.assertIsNone(ss["firmware"]["action"])

    def test_firmware_progress(self):
        ss = by_key(P.steps(facts()))
        self.assertIn("Install the Atech SDK", ss["firmware"]["line"])
        ss = by_key(P.steps(facts(sdk="/x/atech")))
        self.assertIn("without a board", ss["firmware"]["line"])
        ss = by_key(P.steps(facts(sdk="/x/atech",
                                  state={"firmware_built": {"when": "16 Nov 2026 23:00"}})))
        self.assertIn("Built on 16 Nov", ss["firmware"]["line"])
        ss = by_key(P.steps(facts(state={"flashed": {"when": "17 Nov 2026 01:00"}})))
        self.assertEqual(ss["firmware"]["state"], P.DONE)

    def test_parts_line(self):
        line = by_key(P.steps(facts()))["parts"]["line"]
        self.assertEqual(line, "3 printed (about 55 g of PLA); the Atech board, 1 module, "
                               "1 cable.")

    def test_next_step(self):
        self.assertEqual(P.next_step(P.steps(facts()))["key"], "firmware")
        done = {k: {"when": "x"} for k in ("flashed", "printed", "pack", "ordered")}
        self.assertIsNone(P.next_step(P.steps(facts(state=done))))
        self.assertEqual(P.progress(P.steps(facts(state=done))), (7, 7))


class Assembly(unittest.TestCase):
    def test_steps(self):
        a = P.assembly(facts())
        titles = [s["title"] for s in a]
        self.assertEqual(titles, ["Print the parts", "Get the electronics ready",
                                  "Fit the board", "Power", "Plug in the modules",
                                  "Connect the cabled modules", "Close it", "Flash and test"])
        plug = a[titles.index("Plug in the modules")]["lines"]
        self.assertIn("Screen onto ports 9 and 10.", plug)
        self.assertIn("Knob: ribbon to port 1, 82 mm.",
                      a[titles.index("Connect the cabled modules")]["lines"])
        self.assertIn("2 x Foot (black, 2.5 g)", a[0]["lines"])

    def test_print_only(self):
        a = P.assembly(facts(electrical=E.analyse({"modules": []}),
                             bom={"printed": BOM["printed"], "hardware": []}))
        self.assertEqual([s["title"] for s in a], ["Print the parts", "Close it"])

    def test_markdown(self):
        md = P.assembly_md(facts())
        self.assertTrue(md.startswith("# Desk buddy – assembly"))
        self.assertIn("## 8. Flash and test", md)


class Pack(unittest.TestCase):
    def test_write_pack(self):
        with tempfile.TemporaryDirectory() as d:
            calls = []

            def writer(p):
                calls.append(p)
                with open(p, "w") as fh:
                    fh.write("solid x\nendsolid x\n")

            def broken(p):
                raise RuntimeError("no FreeCAD")

            files = P.write_pack(facts(), d, extra={
                "prints/body.stl": ("print file", writer),
                "prints/broken.stl": ("never", broken)})
            names = [a for a, _b in files]
            for want in ("parts-list.csv", "assembly.md", "electrical/electrical-report.md",
                         "electrical/schematic.svg", "electrical/netlist.json",
                         "electrical/wiring.svg", "firmware/project.yaml",
                         "prints/body.stl", "product.html", "README.md"):
                self.assertIn(want, names)
                self.assertTrue(os.path.isfile(os.path.join(d, want)), want)
            self.assertNotIn("prints/broken.stl", names)
            html = read(os.path.join(d, "product.html"))
            self.assertIn("<title>Desk buddy</title>", html)
            self.assertIn("<svg", html)
            self.assertIn("From prompt to product", html)
            st = P.read_state(d)
            self.assertIn("pack", st)
            self.assertIn("README.md", st["pack"]["files"])
            readme = read(os.path.join(d, "README.md"))
            self.assertIn("## In this folder", readme)

    def test_pack_keeps_agent_firmware(self):
        with tempfile.TemporaryDirectory() as d:
            P.write_pack(facts(firmware_yaml="name: mine\n"), d)
            self.assertEqual(read(os.path.join(d, "firmware", "project.yaml")),
                             "name: mine\n")

    def test_html_escapes(self):
        f = facts(project="<script>x</script>")
        html = P.product_html(f, f["electrical"], [])
        self.assertNotIn("<script>x", html)

    def test_mark(self):
        with tempfile.TemporaryDirectory() as d:
            P.mark(d, "flashed", when="t1", port="/dev/x")
            st = P.mark(d, "printed", when="t2")
            self.assertEqual(st["flashed"], {"when": "t1", "port": "/dev/x"})
            self.assertEqual(json.loads(read(os.path.join(d, P.STATE_FILE)))["printed"]["when"],
                             "t2")


if __name__ == "__main__":
    unittest.main()
