"""R1210: printed fit numbers in atech_fit (docs/CAD_WORKFLOW_MERGE.md).

The values that came from Gustav's prints (tag P, each with a source), the
fit classes, and the user's own values (tag U) that beat the table.

Pure Python:
    cd addon/AcadAgent/tests && python3 -m unittest test_cadwf_r1210
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(os.path.dirname(HERE), "acadagent", "agent_kit")
sys.path.insert(0, KIT)

import atech_fit  # noqa: E402


class PrintedValues(unittest.TestCase):

    def tearDown(self):
        atech_fit.reset_user()

    def test_dbore_is_the_printed_one(self):
        # cad-workflow builds/wheels/wheel.py: shaft 3.0 / 2.5 + 0.2 a side
        self.assertEqual(atech_fit.value("dbore_d3"), (3.40, 2.90))
        self.assertEqual(atech_fit.value("dbore_depth"), 12.0)
        self.assertEqual(atech_fit.FIT["dbore_d3"][1], "P")
        shaft_d = atech_fit.value("motor_shaft")[0]
        flat = atech_fit.value("motor_shaft_flat")
        bore, across = atech_fit.value("dbore_d3")
        self.assertAlmostEqual(bore - shaft_d, 0.4)
        self.assertAlmostEqual(across - flat, 0.4)

    def test_shaft_flat_is_measured(self):
        self.assertEqual(atech_fit.value("motor_shaft_flat"), 2.5)
        self.assertEqual(atech_fit.FIT["motor_shaft_flat"][1], "CAD")

    def test_every_printed_value_has_a_source(self):
        for key, (_v, tag, _note) in atech_fit.FIT.items():
            if "P" in tag.split("/"):
                self.assertIn(key, atech_fit.SOURCES, key)
                s = atech_fit.SOURCES[key]
                for field in ("by", "date", "material", "printer", "ref",
                              "result"):
                    self.assertTrue(s.get(field), "%s: no %s" % (key, field))
                self.assertIn(s["date"], atech_fit.source(key))
        self.assertEqual(atech_fit.source("wall"), "")

    def test_no_source_without_a_printed_tag(self):
        for key in atech_fit.SOURCES:
            self.assertIn("P", atech_fit.FIT[key][1].split("/"), key)

    def test_hole_for_a_turning_shaft(self):
        # 3.0 shaft + 0.25 running clearance + 0.25 shrink
        self.assertEqual(atech_fit.hole_for(3.0, "running"), 3.5)
        self.assertEqual(atech_fit.value("bearing_d3"),
                         atech_fit.hole_for(3.0, "running"))
        self.assertEqual(atech_fit.value("face_dc_motor")["bearing_d"], 3.5)
        with self.assertRaises(KeyError):
            atech_fit.hole_for(3.0, "tight")

    def test_fit_classes(self):
        self.assertAlmostEqual(atech_fit.printed_clearance(3.3, 3.0), 0.05)
        self.assertEqual(atech_fit.fit_word(-0.1), "press")
        self.assertEqual(atech_fit.fit_word(0.0), "transition")
        self.assertEqual(atech_fit.fit_word(0.25), "running")
        self.assertEqual(atech_fit.fit_classes(0.32),
                         ["running", "slide", "clearance", "pocket"])
        self.assertEqual(atech_fit.fit_word(0.6), "clearance")
        self.assertEqual(atech_fit.fit_word(1.2), "pocket")
        self.assertEqual(atech_fit.fit_word(-0.5), "interference")
        self.assertEqual(atech_fit.fit_word(3.0), "loose")
        self.assertEqual(atech_fit.fit_word(0.1),
                         "between transition and running")
        # the old 3.3 hole for a 3 mm shaft prints as a transition fit:
        # the shaft does not turn in it
        self.assertEqual(
            atech_fit.fit_word(atech_fit.printed_clearance(3.3, 3.0)),
            "transition")

    def test_prompt_tables(self):
        out = atech_fit.render_tables()
        self.assertIn("P printed and fitted", out)
        self.assertIn("hole_shrink 0.25 (P)", out)
        self.assertIn("bearing_d3 3.5 (P/A)", out)
        self.assertIn("slide 0.3 (P/A)", out)
        # applied by a kit call, so not in the table
        self.assertNotIn("dbore_d3 ", out)
        self.assertLess(len(out), 2600, len(out))
        # every value still formats for the rule texts
        vals = atech_fit.prompt_values()
        self.assertEqual(vals["dbore_d3"], "3.4 x 2.9")


class UserValues(unittest.TestCase):

    def tearDown(self):
        atech_fit.reset_user()

    def test_a_user_value_beats_the_table(self):
        got = atech_fit.set_user("dbore_d3", [3.5, 3.0], note="35 was snug",
                                 date="2026-11-27", profile="X1C | PLA")
        self.assertEqual(got, (3.5, 3.0))
        self.assertEqual(atech_fit.value("dbore_d3"), (3.5, 3.0))
        val, tag, note = atech_fit.FIT["dbore_d3"]
        self.assertEqual(tag, "U")
        self.assertIn("35 was snug", note)
        self.assertIn("3.4 x 2.9", note)
        atech_fit.reset_user()
        self.assertEqual(atech_fit.value("dbore_d3"), (3.40, 2.90))
        self.assertEqual(atech_fit.FIT["dbore_d3"][1], "P")
        self.assertEqual(atech_fit.USER, {})

    def test_a_scalar_stays_a_scalar(self):
        atech_fit.set_user("slide", 0.35)
        self.assertEqual(atech_fit.value("slide"), 0.35)
        self.assertIn("slide 0.35 (U)", atech_fit.render_tables())

    def test_hardware_and_ports_cannot_change(self):
        for key in ("board_thickness", "motor_shaft", "motor_shaft_flat",
                    "usbc_open", "module_size", "fit_bands", "wall"):
            with self.assertRaises(ValueError, msg=key):
                atech_fit.set_user(key, 1.0)
        for key in atech_fit.USER_KEYS:
            self.assertIn(key, atech_fit.FIT)
            self.assertNotIn("CAD", atech_fit.FIT[key][1].split("/"), key)

    def test_wrong_shape_and_wild_values_are_refused(self):
        with self.assertRaises(ValueError):
            atech_fit.set_user("dbore_d3", 3.5)
        with self.assertRaises(ValueError):
            atech_fit.set_user("slide", [0.3, 0.3])
        with self.assertRaises(ValueError):
            atech_fit.set_user("slide", "0.3")
        with self.assertRaises(ValueError):
            atech_fit.set_user("slide", 2.0)
        with self.assertRaises(ValueError):
            atech_fit.set_user("slide", float("nan"))
        self.assertEqual(atech_fit.value("slide"), 0.30)

    def test_span_is_measured_from_the_table_not_the_last_value(self):
        atech_fit.set_user("slide", 1.2)
        with self.assertRaises(ValueError):
            atech_fit.set_user("slide", 2.0)
        self.assertEqual(atech_fit.value("slide"), 1.2)

    def test_file_with_profiles(self):
        data = {"version": 1, "active": "X1C | PLA", "profiles": {
            "X1C | PLA": {"printer": "Bambu X1C 0.4", "material": "PLA",
                          "values": {"dbore_d3": {"value": [3.5, 3.0],
                                                  "date": "2026-11-27"},
                                     "board_thickness": {"value": 6.5},
                                     "slide": 0.25}},
            "H2S | PETG": {"values": {"slide": {"value": 0.4}}}}}
        applied, refused = atech_fit.apply_user(data)
        self.assertEqual(applied, ["dbore_d3", "slide"])
        self.assertEqual([k for k, _ in refused], ["board_thickness"])
        self.assertEqual(atech_fit.value("slide"), 0.25)
        self.assertEqual(atech_fit.value("board_thickness"), 7.00)
        # another profile, and the first one's values are gone
        data["active"] = "H2S | PETG"
        applied, refused = atech_fit.apply_user(data)
        self.assertEqual(applied, ["slide"])
        self.assertEqual(atech_fit.value("slide"), 0.4)
        self.assertEqual(atech_fit.value("dbore_d3"), (3.40, 2.90))

    def test_load_user_never_raises(self):
        self.assertEqual(atech_fit.load_user("/no/such/fit_user.json"), [])
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "fit_user.json")
            with open(bad, "w") as fh:
                fh.write("{not json")
            self.assertEqual(atech_fit.load_user(bad), [])
            for junk in ([], "x", {"active": "a"}, {"profiles": []},
                         {"active": "a", "profiles": {"a": {"values": 3}}}):
                with open(bad, "w") as fh:
                    json.dump(junk, fh)
                self.assertEqual(atech_fit.load_user(bad), [], junk)
            with open(bad, "w") as fh:
                json.dump({"active": "a", "profiles": {"a": {"values": {
                    "rotate": {"value": 0.3}}}}}, fh)
            self.assertEqual(atech_fit.load_user(bad), ["rotate"])
            self.assertEqual(atech_fit.value("rotate"), 0.3)

    def test_fit_helpers_follow_the_users_shrink(self):
        atech_fit.set_user("hole_shrink", 0.15)
        self.assertEqual(atech_fit.hole_for(3.0, "running"), 3.4)


if __name__ == "__main__":
    unittest.main()
