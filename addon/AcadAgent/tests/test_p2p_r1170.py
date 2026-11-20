"""R1170 versions and what changed (agent_kit/p2p_rev.py).

    cd addon/AcadAgent/tests && python3 -m unittest test_p2p_r1170
"""
import copy
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(os.path.dirname(HERE), "acadagent", "agent_kit")
if KIT not in sys.path:
    sys.path.insert(0, KIT)

import p2p_brief as B                                          # noqa: E402
import p2p_rev as R                                            # noqa: E402

FACTS = {"brief": B.brief("a desk buddy with a button"),
         "modules": [{"module": "button", "ports": [1]}, {"module": "usbc", "ports": [8]}],
         "parts": [{"label": "Case", "count": 1, "size_mm": [110, 70, 30], "volume_cm3": 40},
                   {"label": "Lid", "count": 1, "size_mm": [110, 70, 4], "volume_cm3": 15}],
         "whole_mm": [110, 70, 34], "grams": 55, "screws": ["M3 x 8 mm screw"],
         "code": "if (btn.wasPressed()) {}", "accept": (8, 9), "qa": "not tested"}


class TestRevisions(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_first_and_unchanged(self):
        h, e = R.add(self.d, R.snapshot(FACTS))
        self.assertEqual(e["version"], "1.0")
        self.assertEqual(e["changes"], ["First version."])
        f = copy.deepcopy(FACTS)
        f["qa"] = "tested"
        f["accept"] = (9, 9)
        h, e = R.add(self.d, R.snapshot(f))
        self.assertIsNone(e, "results are not a new version")
        self.assertEqual(R.latest(self.d)["snap"]["qa"], "tested")
        self.assertEqual(len(h), 1)

    def test_minor_and_major(self):
        R.add(self.d, R.snapshot(FACTS))
        f = copy.deepcopy(FACTS)
        f["parts"][0]["size_mm"] = [120, 70, 30]
        _h, e = R.add(self.d, R.snapshot(f))
        self.assertEqual(e["version"], "1.1")
        self.assertIn("Case: 110 x 70 x 30 mm -> 120 x 70 x 30 mm.", e["changes"])
        f["modules"].append({"module": "speaker", "ports": [3, 4]})
        _h, e = R.add(self.d, R.snapshot(f))
        self.assertEqual(e["version"], "2.0")
        self.assertIn("Added the speaker (port 3,4).", e["changes"])

    def test_diff_words(self):
        a = R.snapshot(FACTS)
        f = copy.deepcopy(FACTS)
        f["parts"] = f["parts"][:1] + [{"label": "Foot", "count": 4, "size_mm": [10, 10, 5],
                                         "volume_cm3": 0.4}]
        f["modules"][0]["ports"] = [2]
        f["code"] = "if (btn.wasPressed()) { led.show(); }"
        f["screws"] = []
        f["grams"] = 70
        ch = R.diff(a, R.snapshot(f))
        for want in ("New part: Foot.", "Part gone: Lid.", "Moved the button from port 1 to 2.",
                     "The firmware changed.", "Screws: M3 x 8 mm screw -> none.",
                     "Filament about 55 g -> 70 g."):
            self.assertIn(want, ch)
        self.assertEqual(R.diff(a, a), ["No visible change."])

    def test_changelog(self):
        R.add(self.d, R.snapshot(FACTS), when="20 Nov 2026 01:00")
        f = copy.deepcopy(FACTS)
        f["code"] = None
        R.add(self.d, R.snapshot(f), when="20 Nov 2026 02:00", note="no firmware yet")
        md = R.changelog_md(R.load(self.d))
        self.assertLess(md.index("### 1.1"), md.index("### 1.0"), "newest first")
        self.assertIn("Firmware removed.", md)
        self.assertIn("Note: no firmware yet", md)

    def test_broken_file(self):
        with open(os.path.join(self.d, R.REV_FILE), "w") as fh:
            fh.write("{")
        self.assertEqual(R.load(self.d), [])
        _h, e = R.add(self.d, R.snapshot(FACTS))
        self.assertEqual(e["version"], "1.0")


if __name__ == "__main__":
    unittest.main()
