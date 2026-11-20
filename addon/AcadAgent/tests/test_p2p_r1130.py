"""R1130 cost and buying (agent_kit/p2p_cost.py): exact sizes, one screw type,
prices that are the user's or the site's - never invented.

    cd addon/AcadAgent/tests && python3 -m unittest test_p2p_r1130
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
KIT = os.path.join(ADDON, "acadagent", "agent_kit")
for p in (ADDON, KIT):
    if p not in sys.path:
        sys.path.insert(0, p)

import p2p_cost as C                                           # noqa: E402

BILL = {"filament": [{"colour": "black", "grams": 80}],
        "atech": [{"name": "Atech board"}, {"name": "Button"}],
        "buy": [{"name": "M3x8 screw", "count": 4, "note": ""},
                {"name": "Screw_M3x8", "count": 2, "note": ""},
                {"name": "M2x6 screw", "count": 2, "note": ""},
                {"name": "Magnet", "count": 4,
                 "note": "about 6.0 x 6.0 x 3.0 mm (measured from the model)"}]}
QUOTE = {"currency": "SEK", "total": {"amount": 899, "text": "899 kr"}}


class TestSpec(unittest.TestCase):
    def test_specs(self):
        cases = {"M3x8 screw": "M3 x 8 mm screw", "Screw_M2_5x6": "M2.5 x 6 mm screw",
                 "Screw M3x10 countersunk": "M3 x 10 mm screw, countersunk",
                 "M3 nut": "M3 nut", "Heat-set insert M3": "M3 insert, heat-set",
                 "Magnet 6x3 mm": "magnet, 6 x 3 mm"}
        for name, spec in cases.items():
            self.assertEqual(C.screw_spec(name)["spec"], spec, name)
        self.assertIsNone(C.screw_spec("Lid"))

    def test_merged_and_exact(self):
        rows = C.buy_list(BILL)
        by = {r["spec"]: r for r in rows}
        self.assertEqual(by["M3 x 8 mm screw"]["count"], 6, "two names, one spec")
        self.assertTrue(by["magnet"]["exact"], "a measured size counts")
        rows = C.buy_list({"buy": [{"name": "Screw", "count": 1}]})
        self.assertFalse(rows[0]["exact"])
        self.assertIn("measure the hole", C.shopping_md({"buy": [{"name": "Screw",
                                                                  "count": 1}]}))

    def test_one_screw_type(self):
        self.assertEqual(C.screw_types(C.buy_list(BILL)), ["M3 x 8 mm screw",
                                                           "M2 x 6 mm screw"])
        adv = C.screw_advice(C.buy_list(BILL))
        self.assertIn("use M3 throughout", adv, "the thread used most")
        one = {"buy": [{"name": "M3x8 screw", "count": 8}]}
        self.assertIsNone(C.screw_advice(C.buy_list(one)))
        same = {"buy": [{"name": "M3x8 screw", "count": 2}, {"name": "M3x12 screw",
                                                             "count": 2}]}
        self.assertIn("One length could do", C.screw_advice(C.buy_list(same)))


class TestCosts(unittest.TestCase):
    def test_with_prices_and_quote(self):
        c = C.costs(BILL, {"currency": "SEK", "filament_per_kg": 250,
                           "buy": {"M3 x 8 mm screw": 1.2, "M2 x 6 mm screw": 1,
                                   "magnet": 2}}, QUOTE, quantity=10)
        self.assertEqual(c["unknown"], [])
        self.assertAlmostEqual(c["known_total"], 20 + 899 + 7.2 + 2 + 8, 2)
        self.assertAlmostEqual(c["batch_total"], c["known_total"] * 10, 2)
        self.assertFalse(c["planning"])

    def test_never_invents(self):
        c = C.costs(BILL)
        self.assertTrue(c["planning"], "the filament's planning figure is flagged")
        self.assertIn("planning figure", c["lines"][0]["source"])
        atech = [ln for ln in c["lines"] if ln["section"] == "Atech"][0]
        self.assertIsNone(atech["total"])
        self.assertEqual(len(c["unknown"]), 1 + 3)
        self.assertIn("Not known yet", C.markdown(c))

    def test_grams_from_the_print_plan(self):
        c = C.costs(BILL, {"currency": "SEK", "filament_per_kg": 200}, grams=50)
        self.assertEqual(c["lines"][0]["total"], 10.0)

    def test_margin_needs_every_price(self):
        p = {"currency": "SEK", "filament_per_kg": 250, "sell_price": 1500}
        c = C.costs(BILL, p, QUOTE)
        self.assertIsNone(c["margin"])
        self.assertTrue(any("margin needs every price" in n for n in c["notes"]))
        p["buy"] = {"M3 x 8 mm screw": 1, "M2 x 6 mm screw": 1, "magnet": 1}
        c = C.costs(BILL, p, QUOTE)
        self.assertEqual(c["margin"]["profit"], round(1500 - c["known_total"], 2))

    def test_mixed_currencies_are_said(self):
        c = C.costs(BILL, {"currency": "SEK"}, QUOTE)       # filament in USD (planning)
        self.assertTrue(any("more than one currency" in n for n in c["notes"]))

    def test_csv(self):
        text = C.csv_text(C.costs(BILL, {"currency": "SEK", "filament_per_kg": 250}, QUOTE))
        self.assertTrue(text.startswith("Section,Item,Count"))
        self.assertIn("Known total", text)

    def test_prices_file(self):
        d = tempfile.mkdtemp()
        try:
            self.assertEqual(C.load_prices(d), {})
            C.save_prices(d, {"currency": "EUR", "filament_per_kg": 22})
            self.assertEqual(C.load_prices(d)["currency"], "EUR")
        finally:
            shutil.rmtree(d)

    def test_with_the_real_share_bill(self):
        from acadagent import share
        bom = {"printed": [{"part": "Case", "count": 1, "names": ["Case"], "mass_g": 40,
                            "colour": "black"},
                           {"part": "Screw_M3x8", "count": 4, "names": ["Screw_M3x8"],
                            "mass_g": 0.3, "colour": ""}],
               "hardware": [{"kind": "Board", "name": "Atech board", "ports": "",
                             "length_mm": None, "key": "motherboard_14_port"},
                            {"kind": "Module", "name": "Button", "ports": "3",
                             "length_mm": None, "key": "button"}]}
        b = share.bill(bom, spec_fn=lambda k: {})
        c = C.costs(b, {"currency": "SEK", "filament_per_kg": 250})
        self.assertEqual([r["spec"] for r in C.buy_list(b)], ["M3 x 8 mm screw"])
        self.assertTrue(any(ln["section"] == "Atech" for ln in c["lines"]))


if __name__ == "__main__":
    unittest.main()
