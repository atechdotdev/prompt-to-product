"""R1180 the whole pack: acadagent/p2p_product.py (papers in product.write_pack)
and acadagent/p2p_make.py (prompt + design -> pack, headless under freecadcmd).

    cd addon/AcadAgent/tests && ATECH_SDK_CATALOG=snapshot python3 -m unittest test_p2p_r1180
    ATECH_FREECADCMD=<freecadcmd>      # + the real headless run on two examples
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(ADDON))
KIT = os.path.join(ADDON, "acadagent", "agent_kit")
for p in (ADDON, KIT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("ATECH_SDK_CATALOG", "snapshot")

from acadagent import p2p_product, product                    # noqa: E402
import atech_electrical as E                                   # noqa: E402

PROMPT = ("A desk buddy with a button that plays a tune, and a light that glows red when "
          "it is too hot. Pocket-sized.")


def facts(folder):
    atech = {"modules": [{"module": "button", "ports": [1], "label": "Button"},
                         {"module": "light", "ports": [2], "label": "Light"},
                         {"module": "speaker", "ports": [3, 4], "label": "Speaker"},
                         {"module": "temp_humidity", "ports": [14], "label": "TH"},
                         {"module": "usbc", "ports": [8], "label": "USB-C"}]}
    el = E.analyse(atech, project="Desk buddy")
    bom = {"printed": [{"part": "Case", "count": 1, "names": ["Case"], "volume_cm3": 30,
                        "mass_g": 37, "colour": "black"},
                       {"part": "Screw_M3x8", "count": 4, "names": ["Screw_M3x8"],
                        "volume_cm3": 0.1, "mass_g": 0.1, "colour": ""}],
           "hardware": [{"kind": "Board", "name": "Atech board", "ports": "",
                         "length_mm": None, "key": "motherboard_14_port", "label": "Board"}]}
    return {"project": "Desk buddy", "built": True, "check": None, "levels": None,
            "bom": bom, "electrical": el, "sdk": None, "state": {}, "folder": folder,
            "parts": [{"label": "Case", "count": 1, "size_mm": [110, 70, 28],
                       "volume_cm3": 30, "colour": "black"}],
            "whole_mm": [110, 70, 30], "prompt": PROMPT}


class TestPapers(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_write_pack_has_every_paper(self):
        files = [r for r, _w in product.write_pack(facts(self.d), self.d)]
        for want in ("brief.md", "done-when.md", "print-plan.md", "costs.md", "costs.csv",
                     "to-buy.md", "manual.md", "quick-start.html", "label.svg",
                     "test-plan.md", "CHANGELOG.md", "firmware/project.yaml", "README.md",
                     "product.html"):
            self.assertIn(want, files)
            self.assertTrue(os.path.getsize(os.path.join(self.d, want)) > 20, want)
        self.assertEqual(len(files), len(set(files)), "no file listed twice")
        for state in ("brief.json", "revisions.json"):
            self.assertTrue(os.path.isfile(os.path.join(self.d, state)))

    def test_firmware_from_the_brief(self):
        product.write_pack(facts(self.d), self.d)
        with open(os.path.join(self.d, "firmware", "project.yaml")) as fh:
            y = fh.read()
        self.assertIn("Written by Prompt2Product from the brief", y)
        self.assertIn("btn.wasPressed()", y)
        self.assertIn("led.setAll(255, 0, 0)", y)
        with open(os.path.join(self.d, "done-when.md")) as fh:
            dw = fh.read()
        self.assertIn("| Firmware does what the brief says (2 behaviours) | yes |", dw)

    def test_agent_code_wins(self):
        f = facts(self.d)
        f["firmware_yaml"] = ("name: x\nboard: 14port\nmodules: []\ncode:\n  setup: |\n    //\n"
                              "  loop: |\n    if (btn.wasPressed()) { spk.playTone(440, 9); }\n")
        g = p2p_product.enrich(f)
        self.assertEqual(p2p_product.firmware_from_brief(g), (None, []))

    def test_readme_status(self):
        f = facts(self.d)
        product.write_pack(f, self.d)
        with open(os.path.join(self.d, "README.md")) as fh:
            md = fh.read()
        for want in ("**Brief**:", "**Print plan**:", "**Cost**:",
                     "**Tested**: Not tested by hand yet", "**Version**: Version 1.0."):
            self.assertIn(want, md)

    def test_second_pack_same_version_then_new(self):
        product.write_pack(facts(self.d), self.d)
        product.write_pack(facts(self.d), self.d)
        R = p2p_product.kit("p2p_rev")
        self.assertEqual(len(R.load(self.d)), 1)
        f = facts(self.d)
        f["parts"][0]["size_mm"] = [115, 70, 28]
        product.write_pack(f, self.d)
        self.assertEqual(R.latest(self.d)["version"], "1.1")

    def test_check_is_never_assumed(self):
        g = p2p_product.enrich(facts(self.d))
        row = [r for r in g["accept"] if r["id"] == "checked"][0]
        self.assertEqual(row["state"], "unknown")

    def test_no_brief_still_packs(self):
        f = facts(self.d)
        f.pop("prompt")
        files = [r for r, _w in product.write_pack(f, self.d)]
        self.assertNotIn("brief.md", files)
        self.assertIn("manual.md", files)
        self.assertIn("print-plan.md", files)

    def test_prices_beside_the_products(self):
        root = tempfile.mkdtemp()
        try:
            folder = os.path.join(root, "Desk buddy")
            p2p_product.kit("p2p_cost").save_prices(root, {"currency": "SEK",
                                                           "filament_per_kg": 250})
            g = p2p_product.enrich(facts(folder))
            self.assertFalse(g["cost"]["planning"])
            self.assertEqual(g["cost"]["currency"], "SEK")
        finally:
            shutil.rmtree(root)


try:
    import test_agent_kit as tak
    FC = tak.FC
except Exception:                                                 # noqa: BLE001
    FC = None


@unittest.skipIf(FC is None, "freecadcmd not found")
class TestHeadless(unittest.TestCase):
    def run_make(self, example, prompt, out):
        env = dict(os.environ, P2P_RUN="1", P2P_EXAMPLE=example, P2P_OUT=out,
                   P2P_PROMPT=prompt, ATECH_ARTIFACTS=os.path.join(REPO, "models"),
                   ATECH_SDK_CATALOG="snapshot", QT_QPA_PLATFORM="offscreen",
                   P2P_NAME=example.replace("_", " ").capitalize())
        p = subprocess.run([FC, os.path.join(ADDON, "acadagent", "p2p_make.py")], env=env,
                           capture_output=True, text=True, timeout=900)
        out_text = p.stdout + p.stderr
        lines = {ln.split(" ", 2)[1]: ln.split(" ", 2)[2] for ln in out_text.splitlines()
                 if ln.startswith("P2P ") and len(ln.split(" ", 2)) == 3}
        self.assertIn("P2P_DONE=0", out_text, out_text[-3000:])
        return lines

    def test_air_monitor(self):
        d = tempfile.mkdtemp(prefix="p2p-r1180-")
        try:
            lines = self.run_make("air_monitor", "An air quality monitor with a CO2 sensor "
                                  "and a screen. When the CO2 is above 1200 ppm the light "
                                  "turns red. When the button is pressed, the screen shows "
                                  "the co2. 100 x 80 x 60 mm, white.", d)
            files = lines["files"].split(" | ")
            for want in ("prints/Air monitor.3mf", "cad/Air monitor.step",
                         "electrical/wiring.pdf", "firmware/project.yaml", "manual.md",
                         "done-when.md", "test-plan.md"):
                self.assertIn(want, files)
            self.assertIn("not met: Fits in 100 x 80 x 60 mm", lines["brief"],
                          "the honest size miss")
            with open(os.path.join(d, "firmware", "project.yaml")) as fh:
                self.assertIn("co2.readCO2() > 1200", fh.read())
            self.assertTrue(lines["qa"].startswith("Not tested"))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_print_only(self):
        d = tempfile.mkdtemp(prefix="p2p-r1180-")
        try:
            lines = self.run_make("desk_buddy", "a little desk buddy figure", d)
            self.assertIn("Bambu Lab", lines["print"])
            self.assertIn("Prints with no electronics", open(os.path.join(
                d, "done-when.md")).read())
            self.assertNotIn("not met", lines["brief"])
            self.assertFalse(os.path.exists(os.path.join(d, "firmware", "project.yaml")))
            with open(os.path.join(d, "manual.md")) as fh:
                self.assertIn("no electronics", fh.read())
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
