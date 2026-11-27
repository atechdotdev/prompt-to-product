"""R1240: print feedback - agent_kit/p2p_fitlog.py and its way into a build
(docs/CAD_WORKFLOW_MERGE.md).

    cd addon/AcadAgent/tests && python3 -m unittest test_cadwf_r1240

"How did it fit?" becomes a number per printer and filament
(fit_user.json); atech_fit puts it in place of the table's; Studio copies
the file into each chat's folder; ./check loads it before model.py runs, so
cad.fit() and cad.d_bore() build with it; the prompt's tables show it (U).

Pure Python, plus one ./check run in the bundled freecadcmd (skipped
without it).
"""
import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
KIT = os.path.join(ADDON, "acadagent", "agent_kit")
sys.path.insert(0, KIT)
sys.path.insert(0, ADDON)

import atech_fit  # noqa: E402
import p2p_fitlog as fl  # noqa: E402


class _Home(unittest.TestCase):
    """Each test gets its own products folder and a clean fit table."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = self._tmp.name
        self._env = os.environ.pop("ATECH_FIT_USER", None)
        atech_fit.reset_user()

    def tearDown(self):
        atech_fit.reset_user()
        if self._env is not None:
            os.environ["ATECH_FIT_USER"] = self._env
        else:
            os.environ.pop("ATECH_FIT_USER", None)
        self._tmp.cleanup()


class Record(_Home):

    def test_nothing_yet(self):
        data = fl.load(self.home)
        self.assertEqual(data, {"version": 1, "active": None, "profiles": {}})
        self.assertIn("No print results yet", fl.summary(data))
        with self.assertRaises(ValueError):
            fl.coupon_result(data, "34")              # no printer chosen

    def test_the_snug_puck_becomes_the_d_bore(self):
        data = fl.load(self.home)
        self.assertEqual(fl.use_profile(data, "Bambu  X1C", " PLA "), "Bambu X1C | PLA")
        got = fl.coupon_result(data, "35", date="2026-11-27")
        # bore 3.5, the flat stays 0.5 under it; holes shrink 0.1 more here,
        # so the shrink and the hole a shaft turns in move with it
        self.assertEqual(got, {"dbore_d3": (3.5, 3.0), "hole_shrink": 0.35,
                               "bearing_d3": 3.6})
        vals = data["profiles"]["Bambu X1C | PLA"]["values"]
        self.assertEqual(vals["dbore_d3"]["value"], [3.5, 3.0])
        self.assertIn("puck 35", vals["dbore_d3"]["note"])
        self.assertEqual(vals["dbore_d3"]["date"], "2026-11-27")
        self.assertEqual(fl.coupon_result(data, 3.3)["dbore_d3"], (3.3, 2.8))
        self.assertEqual(vals["hole_shrink"]["value"], 0.15)

    def test_the_tables_own_puck_confirms_it(self):
        data = fl.load(self.home)
        fl.use_profile(data, "H2S", "PETG")
        fl.coupon_result(data, "35")
        got = fl.coupon_result(data, "34")
        self.assertEqual(got, {"dbore_d3": (3.4, 2.9)})
        vals = data["profiles"]["H2S | PETG"]["values"]
        self.assertEqual(sorted(vals), ["dbore_d3"])   # the derived two are gone

    def test_a_puck_that_is_not_on_the_coupon(self):
        data = fl.load(self.home)
        fl.use_profile(data, "X1C", "PLA")
        for bad in ("31", "40", "", None, "snug"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                fl.coupon_result(data, bad)

    def test_the_module_gauge(self):
        data = fl.load(self.home)
        fl.use_profile(data, "X1C", "PLA")
        self.assertEqual(fl.gauge_result(data, "4"), {"slide": 0.4})
        self.assertEqual(fl.current(data, "slide"), 0.4)
        with self.assertRaises(ValueError):
            fl.gauge_result(data, "5")

    def test_too_tight_too_loose_fits(self):
        data = fl.load(self.home)
        fl.use_profile(data, "X1C", "PLA")
        self.assertEqual(fl.verdict(data, "lip_loose", "tight", 0.05), 0.25)
        self.assertEqual(fl.verdict(data, "lip_loose", "tight", 0.05), 0.3)
        self.assertEqual(fl.verdict(data, "lip_loose", "loose", 0.1), 0.2)
        self.assertEqual(fl.verdict(data, "dbore_d3", "tight", 0.1), (3.5, 3.0))
        self.assertEqual(fl.verdict(data, "slide", "fits"), 0.3)
        note = data["profiles"]["X1C | PLA"]["values"]["slide"]["note"]
        self.assertEqual(note, "it fitted")
        with self.assertRaises(ValueError):
            fl.verdict(data, "slide", "wobbly")
        # R1295 review: a preload is an interference - "too tight" used to
        # make the hold-down rib press HARDER
        base = atech_fit.table_value("preload")
        self.assertEqual(fl.verdict(data, "preload", "tight", 0.05), round(base - 0.05, 2))
        self.assertEqual(fl.verdict(data, "preload", "loose", 0.1), round(base + 0.05, 2))
        # and nothing goes below zero
        with self.assertRaises(ValueError):
            fl.verdict(data, "preload", "tight", 0.5)

    def test_hardware_ports_and_wild_values_are_refused(self):
        data = fl.load(self.home)
        fl.use_profile(data, "X1C", "PLA")
        for key, val in (("board_thickness", 6.5), ("motor_shaft_flat", 2.6),
                         ("usbc_open", (14, 8)), ("slide", 2.0), ("dbore_d3", 3.5)):
            with self.assertRaises(ValueError, msg=key):
                fl.record(data, key, val)
        self.assertEqual(data["profiles"]["X1C | PLA"]["values"], {})

    def test_profiles_keep_their_own_values(self):
        data = fl.load(self.home)
        fl.use_profile(data, "X1C", "PLA")
        fl.gauge_result(data, "2")
        fl.use_profile(data, "X1C", "PETG")
        self.assertEqual(fl.current(data, "slide"), 0.3)        # the table's
        fl.gauge_result(data, "4")
        fl.use_profile(data, "X1C", "PLA")
        self.assertEqual(fl.current(data, "slide"), 0.2)
        self.assertIn("X1C | PLA: slide 0.2 (table 0.3)", fl.summary(data))

    def test_forget(self):
        data = fl.load(self.home)
        fl.use_profile(data, "X1C", "PLA")
        fl.coupon_result(data, "36")
        fl.forget(data, "dbore_d3")
        self.assertEqual(fl.current(data, "dbore_d3"), (3.4, 2.9))
        fl.forget(data)
        self.assertEqual(fl.rows(data), [])


class File(_Home):

    def test_save_and_load(self):
        data = fl.load(self.home)
        fl.use_profile(data, "X1C", "PLA")
        fl.coupon_result(data, "35", date="2026-11-27")
        p = fl.save(data, self.home)
        self.assertEqual(p, os.path.join(self.home, "fit_user.json"))
        self.assertEqual(fl.load(self.home), data)
        self.assertFalse(os.path.exists(p + ".tmp"))
        rows = fl.rows(fl.load(self.home))
        self.assertEqual([r["key"] for r in rows], ["bearing_d3", "dbore_d3", "hole_shrink"])
        self.assertEqual(rows[1]["table"], [3.4, 2.9])

    def test_a_broken_file_is_an_empty_record(self):
        os.makedirs(self.home, exist_ok=True)
        for junk in ("{nope", "[]", '{"profiles": 3}', '{"profiles": {"a": 1}, "active": "a"}'):
            with open(os.path.join(self.home, "fit_user.json"), "w") as fh:
                fh.write(junk)
            self.assertEqual(fl.load(self.home)["active"], None, junk)

    def test_the_fit_table_takes_the_file(self):
        data = fl.load(self.home)
        fl.use_profile(data, "X1C", "PLA")
        fl.coupon_result(data, "35")
        fl.gauge_result(data, "4")
        p = fl.save(data, self.home)
        self.assertEqual(atech_fit.load_user(p),
                         ["bearing_d3", "dbore_d3", "hole_shrink", "slide"])
        self.assertEqual(atech_fit.value("dbore_d3"), (3.5, 3.0))
        self.assertEqual(atech_fit.FIT["slide"][1], "U")
        self.assertIn("X1C | PLA", atech_fit.FIT["slide"][2])
        # the file gone: the table's values count again
        os.unlink(p)
        self.assertEqual(atech_fit.load_user(p), [])
        self.assertEqual(atech_fit.value("dbore_d3"), (3.4, 2.9))
        self.assertEqual(atech_fit.USER, {})

    def test_env_names_another_file(self):
        other = os.path.join(self.home, "elsewhere.json")
        os.environ["ATECH_FIT_USER"] = other
        self.assertEqual(fl.path(), other)
        self.assertEqual(fl.path(self.home), os.path.join(self.home, "fit_user.json"))

    def test_copy_into_a_chat_folder(self):
        with tempfile.TemporaryDirectory() as ws:
            dst = os.path.join(ws, "fit_user.json")
            # R1295 review: with no results the file is still written
            # (empty, read-only). The sandbox protects only files that
            # exist, so a missing one could be planted by a design script.
            self.assertEqual(fl.to_workspace(ws, self.home), "fit_user.json")
            with open(dst) as fh:
                self.assertEqual(json.load(fh), fl.empty())
            self.assertFalse(os.stat(dst).st_mode & stat.S_IWUSR)   # read-only
            self.assertIsNone(fl.to_workspace(ws, self.home))       # unchanged
            data = fl.load(self.home)
            fl.use_profile(data, "X1C", "PLA")
            fl.gauge_result(data, "4")
            fl.save(data, self.home)
            self.assertEqual(fl.to_workspace(ws, self.home), "fit_user.json")
            self.assertFalse(os.stat(dst).st_mode & stat.S_IWUSR)
            self.assertIsNone(fl.to_workspace(ws, self.home))       # unchanged
            fl.gauge_result(data, "2")
            fl.save(data, self.home)
            self.assertEqual(fl.to_workspace(ws, self.home), "fit_user.json")
            with open(dst) as fh:
                self.assertEqual(json.load(fh), data)
            # a planted copy is put right
            os.chmod(dst, 0o644)
            with open(dst, "w") as fh:
                json.dump({"active": "x", "profiles": {"x": {"values": {"slide": 1.2}}}}, fh)
            self.assertEqual(fl.to_workspace(ws, self.home), "fit_user.json")
            with open(dst) as fh:
                self.assertEqual(json.load(fh), data)
            os.unlink(fl.path(self.home))
            fl.to_workspace(ws, self.home)                          # results gone: empty again
            with open(dst) as fh:
                self.assertEqual(json.load(fh), fl.empty())
            self.assertEqual(atech_fit.load_user(dst), [])
            atech_fit.reset_user()

    def test_the_filament_that_is_loaded_chooses_the_results(self):
        """R1295 review: results from PLA were applied to a PETG-CF print
        (whatever was saved last counted). Gustav keeps a set of sizes per
        material."""
        data = fl.load(self.home)
        fl.use_profile(data, "X1C", "PLA")
        fl.gauge_result(data, "4")
        fl.use_profile(data, "H2S", "PETG-CF")
        fl.gauge_result(data, "2")
        fl.save(data, self.home)                    # saved last: H2S | PETG-CF
        self.assertEqual(fl.pick(data), "H2S | PETG-CF")            # nothing known
        self.assertEqual(fl.pick(data, "X1C", "PLA"), "X1C | PLA")
        self.assertEqual(fl.pick(data, "Another", "pla"), "X1C | PLA")   # the only PLA one
        self.assertEqual(fl.pick(data, "H2S", "PETG-CF"), "H2S | PETG-CF")
        self.assertIsNone(fl.pick(data, "H2S", "PETG"))             # PETG is not PETG-CF
        self.assertIsNone(fl.pick(data, "H2S", "ASA"))
        # two PLA profiles: this printer's, else the one saved last, else none
        fl.use_profile(data, "A1", "PLA")
        fl.gauge_result(data, "3")
        self.assertEqual(fl.pick(data, "X1C", "PLA"), "X1C | PLA")
        self.assertEqual(fl.pick(data, "P1S", "PLA"), "A1 | PLA")   # active
        fl.use_profile(data, "H2S", "PETG-CF")
        self.assertIsNone(fl.pick(data, "P1S", "PLA"))              # cannot tell which
        fl.save(data, self.home)
        eff = fl.effective(self.home, "H2S", "ASA")
        self.assertIsNone(eff["active"])
        self.assertIn("none of your print results is for ASA", eff["unused"])
        self.assertEqual(atech_fit.apply_user(eff), ([], []))
        eff = fl.effective(self.home, "X1C", "PLA")
        self.assertEqual(eff["active"], "X1C | PLA")
        self.assertNotIn("unused", eff)
        self.assertEqual(atech_fit.apply_user(eff)[0], ["slide"])
        self.assertEqual(atech_fit.value("slide"), 0.4)
        atech_fit.reset_user()
        with tempfile.TemporaryDirectory() as ws:
            fl.to_workspace(ws, self.home, "H2S", "ASA")
            self.assertEqual(atech_fit.load_user(os.path.join(ws, "fit_user.json")), [])
            fl.to_workspace(ws, self.home, "H2S", "PETG-CF")
            self.assertEqual(atech_fit.load_user(os.path.join(ws, "fit_user.json")), ["slide"])
            self.assertEqual(atech_fit.value("slide"), 0.2)
        atech_fit.reset_user()

    def test_material_from_a_preset_name(self):
        self.assertEqual(fl.material_of("Bambu PETG-CF @BBL H2S"), "PETG-CF")
        self.assertEqual(fl.material_of("Bambu PLA Basic @BBL X1C"), "PLA")
        self.assertEqual(fl.material_of(None), "")

    def test_a_bar_in_a_name_does_not_split_the_profile(self):
        """R1295 review: a printer called "X1C | office" was read back as
        printer "X1C" and filament "office | PLA"."""
        data = fl.load(self.home)
        name = fl.use_profile(data, "X1C | office", "PLA")
        self.assertEqual(name, "X1C / office | PLA")
        prof = data["profiles"][name]
        self.assertEqual((prof["printer"], prof["material"]), ("X1C / office", "PLA"))
        self.assertEqual(fl.pick(data, "X1C | office", "PLA"), name)


class Studio(_Home):
    """build.py: the file reaches the chat folder and the prompt."""

    #: what Bambu Studio is said to have selected in a test (the machine
    #: the tests run on may have its own)
    loaded = ("", "")

    def setUp(self):
        super().setUp()
        from acadagent import build
        self._loaded = build.loaded_filament
        build.loaded_filament = lambda: self.loaded

    def tearDown(self):
        from acadagent import build
        build.loaded_filament = self._loaded
        super().tearDown()

    def test_the_loaded_filament_chooses_the_results(self):
        """R1295: PLA results are not drawn into a PETG print, and ./check's
        copy says why."""
        from acadagent import build
        self._record()                              # X1C | PLA
        self.loaded = ("Bambu Lab H2S", "PETG")
        self.assertIn("slide 0.3 (A)", build.atech_fit_tables())
        with tempfile.TemporaryDirectory() as ws:
            build.fit_to_workspace(ws)
            with open(os.path.join(ws, "fit_user.json")) as fh:
                got = json.load(fh)
            self.assertIsNone(got["active"])
            self.assertIn("PETG", got["unused"])
        self.loaded = ("Bambu Lab X1 Carbon", "PLA")
        self.assertIn("slide 0.4 (U)", build.atech_fit_tables())

    def test_a_rebuild_without_a_turn_gets_the_new_results(self):
        """R1295 review: Dimensions and "go back to this build" rebuilt
        with the chat folder's old copy. The panel refreshes it before
        every final build."""
        from acadagent import build
        self._record()
        with tempfile.TemporaryDirectory() as ws:
            build.fit_to_workspace(ws)
            data = fl.load()
            fl.gauge_result(data, "2")              # a new result, no agent turn
            fl.save(data)
            self.assertEqual(build.fit_to_workspace(ws), "fit_user.json")
            self.assertEqual(atech_fit.load_user(os.path.join(ws, "fit_user.json")),
                             ["bearing_d3", "dbore_d3", "hole_shrink", "slide"])
            self.assertEqual(atech_fit.value("slide"), 0.2)
        with open(os.path.join(ADDON, "acadagent", "panel.py"), encoding="utf-8") as fh:
            src = fh.read()
        run = src[src.index("    def _run_build("):]
        run = run[:run.index("\n    def ", 10)]
        self.assertIn("build.fit_to_workspace(state.ws)", run)

    def _record(self):
        os.environ["ATECH_FIT_USER"] = os.path.join(self.home, "fit_user.json")
        data = fl.load()
        fl.use_profile(data, "X1C", "PLA")
        fl.coupon_result(data, "35")
        fl.gauge_result(data, "4")
        fl.save(data)

    def test_prepare_workspace_copies_it(self):
        from acadagent import build, sandbox
        self._record()
        with tempfile.TemporaryDirectory() as ws:
            written = build.prepare_workspace(ws)
            self.assertIn("fit_user.json", written)
            with open(os.path.join(ws, "fit_user.json")) as fh:
                self.assertEqual(json.load(fh)["active"], "X1C | PLA")
        self.assertIn("fit_user.json", sandbox.PROTECTED)

    def test_the_prompt_shows_the_users_numbers(self):
        from acadagent import build
        self._record()
        tables = build.atech_fit_tables()
        self.assertIn("slide 0.4 (U)", tables)
        self.assertIn("hole_shrink 0.35 (U)", tables)
        section = build.atech_fit_section()
        self.assertIn("holes print 0.35 mm small", " ".join(section.split()))
        # and without the file, the table's again
        os.unlink(os.environ["ATECH_FIT_USER"])
        self.assertIn("slide 0.3 (A)", build.atech_fit_tables())


MODEL = textwrap.dedent('''
    import FreeCAD as App
    import Part
    import atech_cad as cad
    doc = App.ActiveDocument
    hub = Part.makeCylinder(8, 14)
    hub = cad.d_bore(hub, (0, 0, 14), "-Z", flat="+X", lead_in=0)
    air = Part.makeBox(8, 8, 0.02, App.Vector(-4, -4, 8)).cut(hub)
    print("MEASURED %.2f x %.2f" % (air.BoundBox.YLength, air.BoundBox.XLength))
    print("FITKEY", cad.fit("dbore_d3"), cad.fit("slide"))
    doc.addObject("Part::Feature", "Hub").Shape = hub
    doc.recompute()
''')


class InCheck(_Home):

    def _check(self, ws):
        from acadagent import sandbox
        fc = sandbox.find_freecadcmd()
        if fc is None:
            if os.environ.get("ATECH_REQUIRE_FREECADCMD") == "1":
                self.fail("no freecadcmd")
            self.skipTest("bundled freecadcmd not found")
        with open(os.path.join(ws, "model.py"), "w") as fh:
            fh.write(MODEL)
        env = dict(os.environ, ATECH_CHECK_SCRIPT=os.path.join(ws, "model.py"),
                   ATECH_CHECK_PNG="", ATECH_CHECK_TIMEOUT="120")
        p = subprocess.run([fc, os.path.join(KIT, "check.py")], env=env, cwd=ws,
                           capture_output=True, text=True, timeout=300)
        return p.stdout + p.stderr

    def test_a_build_uses_the_users_d_bore(self):
        data = fl.load(self.home)
        fl.use_profile(data, "X1C", "PLA")
        fl.coupon_result(data, "35")
        fl.save(data, self.home)
        with tempfile.TemporaryDirectory() as ws:
            fl.to_workspace(ws, self.home)
            out = self._check(ws)
        self.assertIn("MEASURED 3.50 x 3.00", out, out[-2500:])
        self.assertIn("FITKEY (3.5, 3.0) 0.3", out)
        line = [ln for ln in out.splitlines() if ln.startswith("FIT your own print results")]
        self.assertTrue(line, out[-2500:])
        self.assertIn("X1C | PLA", line[0])
        self.assertIn("dbore_d3 3.5 x 3", line[0])
        self.assertIn('"fit_user"', out)

    def test_without_a_record_the_table_is_used(self):
        with tempfile.TemporaryDirectory() as ws:
            out = self._check(ws)
        self.assertIn("MEASURED 3.40 x 2.90", out, out[-2500:])
        self.assertNotIn("FIT your own print results", out)


if __name__ == "__main__":
    unittest.main()
