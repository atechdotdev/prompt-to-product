"""R1100 the brief: a prompt read into parts (agent_kit/p2p_brief.py) and
written into the agent's workspace (acadagent/p2p_ws.py, build.prepare_workspace).

    cd addon/AcadAgent/tests && python3 -m unittest test_p2p_r1100
"""
import json
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

import p2p_brief as B                                          # noqa: E402
from acadagent import p2p_ws                                   # noqa: E402

DESK = ("A desk buddy with a button that plays a sound, and a light that glows red "
        "when it is too hot. Pocket-sized, black.")


def mods(b):
    return {m["module"]: m["count"] for m in b["modules"]}


class TestModules(unittest.TestCase):
    def test_every_module_name_is_a_real_cad_module(self):
        known = B.known_modules()
        self.assertGreater(len(known), 15, "presets.yaml not found")
        for name in list(B.MODULE_WORDS) + ["usbc", "power_jack"]:
            self.assertIn(name, known)

    def test_desk_buddy(self):
        b = B.brief(DESK)
        self.assertEqual(set(mods(b)), {"button", "light", "speaker", "temp_humidity", "usbc"})
        self.assertEqual(b["title"], "Desk buddy")
        self.assertFalse(b["print_only"])

    def test_counts(self):
        self.assertEqual(mods(B.brief("a game with two buttons and a screen"))["button"], 2)
        self.assertEqual(mods(B.brief("3 buttons in a row"))["button"], 3)
        self.assertEqual(mods(B.brief("a robot car with two wheels"))["dc_motor"], 2)

    def test_negation(self):
        b = B.brief("a weather station without a screen, with a light")
        self.assertNotIn("screen", mods(b))
        self.assertIn("screen", b["without"])
        self.assertTrue(any(a["id"] == "without:screen" for a in b["acceptance"]))

    def test_false_friends(self):
        b = B.brief("a lightweight phone stand in light grey")
        self.assertEqual(mods(b), {})
        self.assertTrue(b["print_only"])
        self.assertEqual(B.brief("a camera mount for a tripod")["modules"], [])

    def test_stepper_needs_a_power_jack(self):
        b = B.brief("a turntable driven by a stepper motor")
        self.assertIn("stepper_motor", mods(b))
        self.assertIn("power_jack", mods(b))
        self.assertNotIn("dc_motor", mods(b))
        self.assertEqual(b["power"], "wall")


class TestSize(unittest.TestCase):
    def test_three_d(self):
        self.assertEqual(B.size("120 x 80 x 60 mm")["max_mm"], [120, 80, 60])
        self.assertEqual(B.size("12x8x6cm")["max_mm"], [120, 80, 60])
        self.assertEqual(B.size("4 by 3 by 2 inches")["max_mm"], [101.6, 76.2, 50.8])

    def test_two_d_and_one_axis(self):
        self.assertEqual(B.size("a 100 x 50 mm tag")["max_mm"], [100, 50, None])
        self.assertEqual(B.size("15 cm tall")["max_mm"], [None, None, 150])
        self.assertEqual(B.size("under 10 cm")["max_mm"], [100, 100, 100])

    def test_words(self):
        s = B.size("pocket-sized")
        self.assertEqual(s["class"], "pocket")
        self.assertIsNone(B.size("a lamp")["max_mm"])


class TestOther(unittest.TestCase):
    def test_power_places_colours(self):
        b = B.brief("an outdoor weather station on a power bank, white")
        self.assertEqual(b["power"], "battery")
        self.assertIn("outdoor", b["places"])
        self.assertEqual(b["colours"], ["white"])
        self.assertTrue(any("PETG" in q for q in b["questions"]))

    def test_a_light_colour_is_not_a_print_colour(self):
        self.assertEqual(B.brief(DESK)["colours"], ["black"])
        self.assertEqual(B.colours("a red box that glows green"), ["red"])

    def test_quantity(self):
        self.assertEqual(B.brief("make 10 cable clips")["quantity"], 10)
        self.assertEqual(B.brief("make 3 buttons on a panel")["quantity"], 1)

    def test_questions_only_for_what_is_missing(self):
        b = B.brief("a 100 x 60 x 40 mm USB-powered night light that glows when "
                    "someone walks by")
        self.assertEqual(b["power"], "usb")
        self.assertFalse(any("powered" in q for q in b["questions"]))
        self.assertFalse(any("How big" in q for q in b["questions"]))


class TestBehaviours(unittest.TestCase):
    def cases(self):
        return [
            (DESK, [("button", "speaker"), ("temp_humidity", "light")]),
            ("a robot car with two wheels and a distance sensor that stops when "
             "something is close, no screen", [("distance_sensor", "dc_motor")]),
            ("a night light that turns on when someone walks by", [("pir", "light")]),
            ("When the button is pressed, it shows the temperature on the screen. If it "
             "gets too cold the light turns blue.",
             [("button", "screen"), ("temp_humidity", "light")]),
            ("Pressing the button makes it beep", [("button", "speaker")]),
            ("a plant pot with a soil sensor; it beeps when the plant needs water",
             [("soil_sensor", "speaker")]),
        ]

    def test_cases(self):
        for prompt, want in self.cases():
            got = [(r["trigger"], r["action"]) for r in B.brief(prompt)["behaviours"]]
            self.assertEqual(got, want, prompt)

    def test_no_screen_is_not_an_action(self):
        b = B.brief("a robot car with a distance sensor that stops when something is "
                    "close, no screen")
        self.assertEqual(b["behaviours"][0]["then"], "stops")

    def test_behaviour_adds_its_module(self):
        b = B.brief("a box that beeps when it is shaken")
        self.assertIn("orientation", mods(b))
        self.assertIn("speaker", mods(b))


class TestUpdate(unittest.TestCase):
    def test_follow_ups(self):
        b = B.brief("a desk lamp with a button, 120 x 80 x 60 mm")
        b = B.update(b, "add a speaker that beeps when the button is pressed")
        self.assertIn("speaker", mods(b))
        self.assertEqual(len(b["behaviours"]), 1)
        b = B.update(b, "remove the button")
        self.assertNotIn("button", mods(b))
        self.assertEqual(b["behaviours"], [], "a behaviour on a removed module goes too")
        b = B.update(b, "make it 150 mm wide")
        self.assertEqual(b["size"]["max_mm"], [150, 80, 60])
        n = len(b["history"])
        b2 = B.update(b, "make the walls thicker")
        self.assertEqual(b2["changes"], [])
        self.assertEqual(len(b2["history"]), n + 1)

    def test_print_becomes_electronic(self):
        b = B.update(B.brief("a phone stand"), "add a light that glows when the phone is close")
        self.assertFalse(b["print_only"])
        self.assertIn("usbc", mods(b))


class TestText(unittest.TestCase):
    def test_markdown_and_agent_text(self):
        b = B.brief(DESK)
        md = B.markdown(b)
        for want in ("# Brief: Desk buddy", "## Done when", "- [ ] Has a button",
                     "When it is too hot, it glows red.", "## Still open"):
            self.assertIn(want, md)
        at = B.agent_text(b)
        self.assertTrue(at.startswith("BRIEF"))
        self.assertIn("Done when:", at)
        self.assertIn("120 x 75 x 30", at)

    def test_save_load(self):
        d = tempfile.mkdtemp()
        try:
            b = B.brief(DESK)
            B.save(b, d)
            self.assertEqual(B.load(d), b)
            with open(os.path.join(d, B.BRIEF_FILE), "w") as fh:
                fh.write("{broken")
            self.assertIsNone(B.load(d))
        finally:
            shutil.rmtree(d)


class TestWorkspace(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.ws, ignore_errors=True)

    def test_first_turn_writes_brief(self):
        b = p2p_ws.on_user_turn(self.ws, DESK)
        self.assertIsNotNone(b)
        self.assertTrue(os.path.isfile(os.path.join(self.ws, "brief.json")))
        with open(os.path.join(self.ws, "BRIEF.md")) as fh:
            self.assertIn("Desk buddy", fh.read())

    def test_chit_chat_writes_nothing(self):
        self.assertIsNone(p2p_ws.on_user_turn(self.ws, "hi"))
        self.assertIsNone(p2p_ws.on_user_turn(self.ws, "what can you do?"))
        self.assertFalse(os.path.exists(os.path.join(self.ws, "brief.json")))

    def test_later_turn_updates(self):
        p2p_ws.on_user_turn(self.ws, DESK)
        p2p_ws.on_user_turn(self.ws, "add a screen")
        with open(os.path.join(self.ws, "brief.json")) as fh:
            self.assertIn("screen", [m["module"] for m in json.load(fh)["modules"]])

    def test_broken_never_raises(self):
        self.assertIsNone(p2p_ws.on_user_turn(os.path.join(self.ws, "missing"), DESK))
        self.assertIsNone(p2p_ws.on_user_turn(self.ws, ""))

    def test_prepare_workspace_hook(self):
        try:
            from acadagent import build
        except Exception as exc:                          # noqa: BLE001
            self.skipTest("build.py needs FreeCAD here: %r" % (exc,))
        build.prepare_workspace(self.ws, reset_intent=True, request=DESK)
        self.assertTrue(os.path.isfile(os.path.join(self.ws, "BRIEF.md")))
        # a fix turn never writes the brief
        ws2 = tempfile.mkdtemp()
        try:
            build.prepare_workspace(ws2, reset_intent=False, request=DESK)
            self.assertFalse(os.path.exists(os.path.join(ws2, "BRIEF.md")))
        finally:
            shutil.rmtree(ws2)

    def test_api_card_mentions_brief(self):
        root = os.path.dirname(os.path.dirname(ADDON))
        with open(os.path.join(root, "projects", "atech_ports.py"), encoding="utf-8") as fh:
            self.assertIn("BRIEF: BRIEF.md in the workspace", fh.read())


if __name__ == "__main__":
    unittest.main()
