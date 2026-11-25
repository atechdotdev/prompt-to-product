"""R960/R961: the wiring model and its drawing (agent_kit/atech_wiring.py).

Pure: standard library only (no FreeCAD, no Qt), so it runs in CI's plain
step. The SDK catalog is pinned to the kit's snapshot so the cautions read
the same everywhere.
"""
import os
import re
import sys
import unittest
import xml.etree.ElementTree as ET

os.environ["ATECH_SDK_CATALOG"] = "snapshot"
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(os.path.dirname(HERE), "acadagent", "agent_kit")
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, KIT)

import atech_firmware  # noqa: E402
import atech_wiring as aw  # noqa: E402

atech_firmware.catalog(refresh=True)

#: What a user-facing wiring string must never say (plan v3, A3).
FORBIDDEN = [r"(?i)\bpin\s*\d+", r"(?i)pinout\b(?! on request)", r"(?i)pin map",
             r"\bLine [AB]\d?\b", r"\bVCC\b", r"\b\d+(\.\d+)?\s*m?A\b",
             r"(?i)\b(red|black|brown|orange|yellow|white)\s+wire",
             r"(?i)\b(tested|verified|safe)\b"]
ALLOWED = ["Not tested on hardware"]


def honest_hits(text):
    for a in ALLOWED:
        text = text.replace(a, "")
    # the SDK caution is quoted, not ours: "Never plug more than 12 V" has no
    # pin, current or colour, so it passes the same patterns
    return [p for p in FORBIDDEN if re.search(p, text)]


def mod(module, ports, label=None, cable=None, seeded=False):
    m = {"module": module, "ports": list(ports), "label": label or "%s_p%s" % (
        module, "_".join(str(p) for p in ports)), "name": label or module}
    if seeded:
        m["seeded"] = True
    if cable is not None:
        m["joint"] = "cable"
        m["cables"] = [{"label": "c%d" % p, "port": p, "length": float(mm)}
                       for p, mm in zip(ports, cable)]
    return m


def atech(*mods):
    return {"board": {"label": "Board", "name": "Board"}, "modules": list(mods)}


ARM = atech(mod("robot_arm", [3]), mod("usbc", [7]), mod("screen", [10, 11]),
            mod("knob", [13, 14]), mod("button", [9]), mod("light", [5]))
TOY = atech(mod("dc_motor", [1]), mod("dc_motor", [9]), mod("usbc", [7]),
            mod("distance_sensor", [8], cable=[82.4]), mod("light", [6], cable=[120]),
            mod("light", [14], cable=[121.6]))


class CheckLines(unittest.TestCase):
    def test_connection_words(self):
        self.assertEqual(aw.connection_words(mod("button", [3])), "plugged in")
        self.assertEqual(aw.connection_words(mod("light", [8], cable=[82.4])), "by cable 82 mm")
        self.assertEqual(aw.connection_words(mod("speaker", [9, 10], cable=[82, 79])),
                         "by cable: port 9 82 mm, port 10 79 mm")

    def test_power_line(self):
        self.assertEqual(aw.power_line(ARM), "WIRING power modules: USB-C on port 7")
        self.assertEqual(aw.power_line(atech(mod("button", [3]))),
                         "WIRING power modules: none (no USB-C or power jack module in this design)")
        self.assertIsNone(aw.power_line(atech()))
        self.assertIsNone(aw.power_line(None))

    def test_notes_only_for_arm_and_stepper(self):
        self.assertEqual(aw.notes(TOY), [])
        n = aw.notes(ARM)
        self.assertEqual(len(n), 1)
        self.assertTrue(n[0].startswith("WIRING robot_arm: "))
        self.assertIn("do not add a power jack module on your own", n[0])
        n = aw.notes(atech(mod("stepper_motor", [1, 2])))
        self.assertIn("12-24 V", n[0])
        # the SDK says NEMA 17, David says the module is NEMA 20: no size quoted
        self.assertNotIn("NEMA", n[0])

    def test_notes_avoid_test_suite_forbidden_warning_words(self):
        # test_kit_examples_r270 forbids these in warnings; notes stay clear too
        for s in aw.notes(ARM) + aw.notes(atech(mod("stepper_motor", [1, 2]))):
            for bad in ("sealed", "OPEN", "pilot", "channel", "limited to", "left out",
                        "cover", "only touches", "falls off"):
                self.assertNotIn(bad, s)


class Model(unittest.TestCase):
    def test_connections_sorted_and_named(self):
        w = aw.build(ARM, names={"robot_arm": "Robot arm"})
        self.assertEqual([c["ports"][0] for c in w["connections"]], [3, 5, 7, 9, 10, 13])
        self.assertEqual(w["connections"][0]["name"], "Robot arm")
        self.assertEqual(w["connections"][1]["name"], "light")        # no name: the id
        self.assertEqual(w["schema"], aw.SCHEMA)

    def test_connection_set_equals_input(self):
        for a in (ARM, TOY):
            w = aw.build(a)
            self.assertEqual(sorted((tuple(c["ports"]), c["module"]) for c in w["connections"]),
                             sorted((tuple(sorted(m["ports"])), m["module"]) for m in a["modules"]))

    def test_code_names_from_the_sdk_plan(self):
        w = aw.build(ARM)
        names = {c["module"]: c.get("code_name") for c in w["connections"]}
        self.assertEqual(names["robot_arm"], "arm")
        self.assertIsNone(names["usbc"])                  # no firmware
        self.assertEqual(names["screen"], "screen")

    def test_firmware_off_hides_code_names_and_cautions(self):
        w = aw.build(ARM, firmware_on=False)
        self.assertFalse(any(c.get("code_name") for c in w["connections"]))
        self.assertNotIn("name in code", "\n".join(aw.lines(w)))
        self.assertEqual(w["cautions"], [])

    def test_robot_arm_caution_in_full(self):
        w = aw.build(ARM)
        self.assertEqual([c["module"] for c in w["cautions"]], ["robot_arm"])
        text = w["cautions"][0]["text"]
        self.assertTrue(text.startswith("Atech SDK: "))
        self.assertIn("damages the servos", text)          # normalised across the newline
        self.assertNotIn("\n", text)

    def test_port_rules(self):
        # TOY: usbc on 7 and a distance sensor on 8 break both port-8 rules
        w = aw.build(TOY)
        self.assertEqual(w["flags"], [
            "The USB-C module goes on port 8 only (port 8 is the USB-C port), "
            "not on port 7.",
            "Port 8 is the USB-C port: only the USB-C module goes there."])
        # the USB-C module on 8: no flag
        w = aw.build(atech(mod("usbc", [8]), mod("button", [3])))
        self.assertEqual(w["flags"], [])
        # anything but a button on 12 is flagged, a module without firmware too
        w = aw.build(atech(mod("camera", [11, 12]), mod("usbc", [8])))
        self.assertTrue(w["flags"][0].startswith("Port 12 is the reset port"))
        # a button on 12 is the reset button: no flag, a note
        w = aw.build(atech(mod("button", [12]), mod("usbc", [8])))
        self.assertEqual(w["flags"], [])
        self.assertIn(aw.RESET_NOTE, w["notes"])
        self.assertTrue([c for c in w["connections"] if c.get("reset")])

    def test_port_rule_matches_the_library_table(self):
        # projects/atech_ports.py enforces the same table (it needs FreeCAD
        # to import, so its source is read here)
        import ast
        with open(os.path.join(REPO_ROOT, "projects", "atech_ports.py"),
                  encoding="utf-8") as fh:
            src = fh.read()
        vals = {}
        for node in ast.parse(src).body:
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and getattr(node.targets[0], "id", None) in
                    ("PORT_ONLY", "MODULE_ONLY", "PORT_ROLE")):
                vals[node.targets[0].id] = ast.literal_eval(node.value)
        self.assertEqual(vals, {"PORT_ONLY": aw.PORT_ONLY,
                                "MODULE_ONLY": aw.MODULE_ONLY,
                                "PORT_ROLE": aw.PORT_ROLE})

    def test_power_and_unknowns(self):
        w = aw.build(atech(mod("button", [3])))
        self.assertEqual(w["power"]["text"], aw.NO_POWER)
        self.assertIn(aw.UNKNOWN_12V, w["unknown"])
        w = aw.build(ARM)
        self.assertEqual(w["power"]["text"], "USB-C on port 7")
        w = aw.build(atech(mod("power_jack", [3]), mod("button", [4])))
        self.assertIn(aw.UNKNOWN_JACK_ALONE, w["unknown"])
        self.assertNotIn(aw.UNKNOWN_12V, w["unknown"])
        for x in (aw.UNKNOWN_PIN_ORDER, aw.UNKNOWN_CURRENT):
            self.assertIn(x, w["unknown"])

    def test_empty(self):
        w = aw.build(None)
        self.assertEqual(w["connections"], [])
        self.assertIsNone(w["power"]["text"])
        self.assertIn(aw.EMPTY.split(".")[0], aw.svg(w, "panel"))

    def test_cable_states_in_text(self):
        a = atech(mod("light", [11], cable=[90]))
        a["modules"][0]["cables"][0]["state"] = "moved"
        t = aw.connection_text(aw.build(a)["connections"][0])
        self.assertIn("cable made for an earlier position – make it again", t)
        a["modules"][0]["cables"] = [{"port": 11, "state": "missing"}]
        self.assertIn("no cable to port 11", aw.connection_text(aw.build(a)["connections"][0]))
        t = aw.connection_text([c for c in aw.build(TOY)["connections"]
                                if c["module"] == "distance_sensor"][0])
        self.assertIn("cable 82 mm (at the last build)", t)


class _P:
    """A Placement stand-in with FreeCAD's isSame."""

    def __init__(self, v):
        self.v = v

    def isSame(self, other, tol):                      # noqa: N802
        return abs(self.v - other.v) <= tol


class _O:
    def __init__(self, name, **kw):
        self.Name = name
        self.Label = kw.pop("Label", name)
        self.Placement = kw.pop("Placement", _P(0))
        for k, v in kw.items():
            setattr(self, k, v)


class _Doc:
    def __init__(self, objs):
        self.Objects = objs


class FromDoc(unittest.TestCase):
    def doc(self, moved=False, drop=False):
        board = _O("Board", AtechRole="board", Placement=_P(0))
        seated = _O("button_p3", AtechRole="module", AtechModule="button", AtechPorts=[3],
                    AtechJoint="prismatic")
        spk = _O("speaker_p9_10", AtechRole="module", AtechModule="speaker",
                 AtechPorts=[9, 10], AtechJoint="cable", Placement=_P(5 if moved else 0))
        cables = [_O("speaker_cable_p%d" % p, AtechCableModule="speaker_p9_10",
                     AtechCablePort=p, AtechCableLength=80.0 + p,
                     AtechCableBoardAt=_P(0), AtechCableModuleAt=_P(0)) for p in (9, 10)]
        if drop:
            cables = cables[:1]
        return _Doc([board, seated, spk] + cables)

    def test_shape_matches_check_report(self):
        a = aw.modules_from_doc(self.doc())
        self.assertEqual(a["board"], {"label": "Board", "name": "Board"})
        self.assertEqual([m["module"] for m in a["modules"]], ["button", "speaker"])
        self.assertNotIn("joint", a["modules"][0])
        spk = a["modules"][1]
        self.assertEqual(spk["joint"], "cable")
        self.assertEqual([(c["port"], c["length"], c["state"]) for c in spk["cables"]],
                         [(9, 89.0, "ok"), (10, 90.0, "ok")])

    def test_moved_and_missing(self):
        spk = aw.modules_from_doc(self.doc(moved=True))["modules"][1]
        self.assertEqual({c["state"] for c in spk["cables"]}, {"moved"})
        spk = aw.modules_from_doc(self.doc(drop=True))["modules"][1]
        self.assertEqual(spk["cables"][-1], {"port": 10, "state": "missing"})

    def test_empty_doc(self):
        self.assertIsNone(aw.modules_from_doc(_Doc([])))


class Drawing(unittest.TestCase):
    CASES = (ARM, TOY, atech(mod("button", [3])), atech(),
             atech(mod("stepper_motor", [1, 2]), mod("power_jack", [4])),
             atech(*[mod("button", [p]) for p in aw.PORTS]))

    def test_both_layouts_parse_and_are_deterministic(self):
        for a in self.CASES:
            w = aw.build(a, project="Test", made="2026-11-16 03:00")
            for layout in ("panel", "sheet"):
                s = aw.svg(w, layout)
                root = ET.fromstring(s)
                self.assertTrue(root.tag.endswith("svg"))
                self.assertEqual(s, aw.svg(w, layout))
                texts = [t.text for t in root.iter() if t.tag.endswith("text")]
                for n in aw.PORTS:
                    self.assertIn(str(n), texts, (layout, n))
                # SVG Tiny subset only
                tags = {t.tag.split("}")[-1] for t in root.iter()}
                self.assertLessEqual(tags, {"svg", "rect", "line", "text"})

    def test_panel_font_readable_at_300px(self):
        s = aw.svg(aw.build(TOY), "panel")
        sizes = [float(x) for x in re.findall(r'font-size="([\d.]+)"', s)]
        width = float(re.search(r'viewBox="0 0 ([\d.]+)', s).group(1))
        self.assertGreaterEqual(min(sizes) * 300 / width, 10)

    def test_hatch_only_for_disputed(self):
        # the hatch lines are drawn in the flag colour
        flag = aw.LIGHT["flag"]
        self.assertIn('stroke="%s" stroke-width="1"' % flag, aw.svg(aw.build(TOY), "panel"))
        self.assertNotIn('stroke="%s" stroke-width="1"' % flag,
                         aw.svg(aw.build(atech(mod("usbc", [8]))), "panel"))

    def test_sheet_carries_the_caution_and_footers(self):
        s = aw.svg(aw.build(ARM, project="Arm dock", made="x"), "sheet")
        flat = " ".join(t.text or "" for t in ET.fromstring(s).iter() if t.tag.endswith("text"))
        self.assertIn("damages the servos", flat)
        self.assertIn("Not tested on hardware", flat)
        self.assertIn("Which pin is which is not published yet", flat)
        self.assertIn("hello@atech.dev", flat)

    def test_honesty(self):
        for a in self.CASES:
            w = aw.build(a, project="Test", made="2026-11-16 03:00")
            texts = list(aw.lines(w)) + [aw.power_line(a) or ""] + aw.notes(a)
            for layout in ("panel", "sheet"):
                root = ET.fromstring(aw.svg(w, layout))
                texts += [t.text or "" for t in root.iter() if t.tag.endswith("text")]
            self.assertEqual(honest_hits("\n".join(texts)), [], a)
        consts = [v for k, v in vars(aw).items() if k.isupper() and isinstance(v, str)]
        self.assertEqual(honest_hits("\n".join(consts)), [])

    def test_cells_match_the_board_map(self):
        # modules_page.CELLS without importing Qt: read the literal
        with open(os.path.join(os.path.dirname(KIT), "modules_page.py"), encoding="utf-8") as fh:
            src = fh.read()
        block = re.search(r"^CELLS = (\{.*?^\})", src, re.S | re.M).group(1)
        import ast
        self.assertEqual(ast.literal_eval(block), aw.PORT_CELLS)
        self.assertIn("CELL_MM = (19.5, 20.0)", src)


if __name__ == "__main__":
    unittest.main()
