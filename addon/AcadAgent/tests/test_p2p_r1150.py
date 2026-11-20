"""R1150 the papers that come with the product: manual, quick-start card and
label (agent_kit/p2p_manual.py).

    cd addon/AcadAgent/tests && python3 -m unittest test_p2p_r1150
"""
import os
import sys
import unittest
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(os.path.dirname(HERE), "acadagent", "agent_kit")
if KIT not in sys.path:
    sys.path.insert(0, KIT)

import p2p_brief as B                                          # noqa: E402
import p2p_manual as M                                         # noqa: E402

PROMPT = ("A box that plays a tune when the button is pressed; when someone walks by, "
          "the screen shows hello. When it is shaken it beeps. For kids.")
FACTS = {"whole_mm": [70, 110, 28], "grams": 55, "part_count": 3, "power_ma": 460,
         "modules": ["button", "pir", "screen", "speaker", "orientation", "usbc"]}


class TestManual(unittest.TestCase):
    def test_sections(self):
        md = M.manual_md(B.brief(PROMPT), FACTS)
        for h in ("## What it does", "## Getting started", "## Using it",
                  "## Looking after it", "## Safety", "## If something is wrong",
                  "## Specifications"):
            self.assertIn(h, md)

    def test_behaviours_in_plain_words(self):
        lines = [M._behaviour_line(r) for r in B.brief(PROMPT)["behaviours"]]
        self.assertEqual(lines, ["Press the button: it plays a tune.",
                                 "Walk past it: the screen shows hello.",
                                 "Shake it: it beeps."])

    def test_module_specific_help(self):
        md = M.manual_md(B.brief(PROMPT), FACTS)
        self.assertIn("about 30 seconds", md, "the PIR settles")
        self.assertIn("about 460 mA (planning figure)", md)
        self.assertIn("children under 3", md)

    def test_never_claims_certification(self):
        md = M.manual_md(B.brief(PROMPT), FACTS)
        self.assertIn("has not been tested for CE, UKCA or FCC", md)
        self.assertIn("not certified", M.label_svg(B.brief(PROMPT), FACTS))

    def test_a_print(self):
        md = M.manual_md(B.brief("a vase"), {"whole_mm": [90, 90, 150], "grams": 80})
        self.assertIn("no electronics, nothing to charge", md)
        self.assertNotIn("## Getting started", md)
        self.assertNotIn("children under 3", md, "one piece: no small parts")
        self.assertNotIn("USB", md)

    def test_places_change_the_advice(self):
        md = M.manual_md(B.brief("a kitchen timer with a button and a speaker"),
                         {"modules": ["button", "speaker"]})
        self.assertIn("not food-safe", md)
        md = M.manual_md(B.brief("a turntable with a stepper motor"),
                         {"modules": ["stepper_motor", "power_jack"]})
        self.assertIn("power supply into the power jack", md)
        md = M.manual_md(B.brief("an outdoor light"), {"modules": ["light"],
                                                        "material": "PETG or ASA"})
        self.assertIn("printed in PETG or ASA", md)


class TestCardAndLabel(unittest.TestCase):
    def test_card(self):
        h = M.card_html(B.brief(PROMPT), FACTS)
        self.assertTrue(h.startswith("<!doctype html>"))
        self.assertIn("@page{size:A6", h)
        self.assertIn("Press the button: it plays a tune.", h)
        self.assertIn("prefers-color-scheme:dark", h)

    def test_label_is_valid_svg(self):
        svg = M.label_svg(B.brief(PROMPT), FACTS)
        root = ET.fromstring(svg)
        self.assertEqual(root.get("width"), "80mm")
        texts = [t.text for t in root.iter("{http://www.w3.org/2000/svg}text")]
        self.assertEqual(texts[0], "Box")
        self.assertIn("Size 70 x 110 x 28 mm", texts)
        self.assertIn("5 V USB-C, about 460 mA", texts)

    def test_label_escapes(self):
        svg = M.label_svg({"title": "Tom & Jerry <3"}, {})
        ET.fromstring(svg)


if __name__ == "__main__":
    unittest.main()
