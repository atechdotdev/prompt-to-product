"""R1000: the electrical engineer's model (agent_kit/atech_electrical.py).

Pure: standard library only, so it runs in CI's plain step. The SDK
catalog is pinned to the kit's snapshot.

    python -m unittest test_electrical_r1000
"""
import csv
import io
import json
import os
import re
import sys
import unittest
import xml.etree.ElementTree as ET

os.environ["ATECH_SDK_CATALOG"] = "snapshot"
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(os.path.dirname(HERE), "acadagent", "agent_kit")
sys.path.insert(0, KIT)

import atech_firmware  # noqa: E402
import atech_electrical as E  # noqa: E402

CAT = atech_firmware.catalog(refresh=True)


def mod(module, ports, cable=None):
    m = {"module": module, "ports": list(ports), "label": module}
    if cable is not None:
        m["joint"] = "cable"
        m["cables"] = [dict({"port": p, "length": 80.0, "state": "ok"}, **cable.get(p, {}))
                       for p in ports]
    return m


def design(*mods):
    return {"board": {"label": "board", "name": "board"}, "modules": list(mods)}


def ids(r):
    return [x["id"] for x in r["rules"]]


class Facts(unittest.TestCase):
    def test_every_sdk_quote_is_in_the_catalog(self):
        """Each module's SDK-sourced facts quote the catalog text, so a
        catalog update that changes them fails here."""
        for cad, f in E.FACTS.items():
            sid = atech_firmware.SDK_ID.get(cad, cad)
            if not f.get("quote"):
                continue
            desc = CAT["modules"][sid]["description"]
            self.assertIn(f["quote"], desc, cad)

    def test_line_roles_appear_in_the_sdk_text(self):
        for cad, f in E.FACTS.items():
            sid = atech_firmware.SDK_ID.get(cad, cad)
            if not sid or sid not in CAT["modules"]:
                continue
            desc = " ".join(CAT["modules"][sid]["description"].split())
            for line, role in (f.get("lines") or {}).items():
                if role in ("not used", "drive") or role.startswith("LED data"):
                    continue
                self.assertIn(role, desc, (cad, line))

    def test_i2c_addresses_from_the_sdk(self):
        for cad, f in E.FACTS.items():
            sid = atech_firmware.SDK_ID.get(cad, cad)
            for a in f.get("i2c") or ():
                if f.get("source") == E.SRC_PRESETS:
                    continue
                self.assertIn(a, CAT["modules"][sid]["description"], cad)

    def test_every_sdk_module_has_facts(self):
        cads = {v for v in atech_firmware.SDK_ID.values() if v}
        known = {atech_firmware.SDK_ID.get(c, c) for c in E.FACTS}
        self.assertEqual(cads - known, set())

    def test_names_for_every_fact(self):
        self.assertEqual(set(E.FACTS) - set(E.NAMES), set())


class Rules(unittest.TestCase):
    def test_empty_design(self):
        r = E.analyse(design())
        self.assertEqual(r["rules"], [])
        self.assertEqual(r["verdict"]["level"], "empty")

    def test_no_power_is_an_error(self):
        r = E.analyse(design(mod("button", [1])))
        self.assertIn("power.none", ids(r))
        self.assertEqual(r["verdict"]["level"], "error")

    def test_clean_design_is_ready(self):
        r = E.analyse(design(mod("usbc", [8]), mod("button", [1]),
                             mod("temp_humidity", [2])))
        self.assertEqual([x for x in r["rules"] if x["level"] != "note"], [])
        self.assertEqual(r["verdict"]["level"], "ok")
        self.assertTrue(r["verdict"]["text"].startswith("Ready to wire"))

    def test_usbc_off_port_8_is_an_error(self):
        # the port rules: the USB-C module goes on port 8 only
        r = E.analyse(design(mod("usbc", [7]), mod("button", [1])))
        rule = [x for x in r["rules"] if x["id"] == "port.rule"][0]
        self.assertEqual(rule["level"], "error")
        self.assertEqual(rule["ports"], [7])
        self.assertIn("port 8 only", rule["text"])
        self.assertEqual(rule["fix"], "Move it to port 8.")
        self.assertNotIn("power.usbc_port", ids(r))

    def test_only_usbc_on_port_8(self):
        r = E.analyse(design(mod("usbc", [8]), mod("distance_sensor", [8])))
        rule = [x for x in r["rules"] if x["id"] == "port.rule"][0]
        self.assertEqual(rule["level"], "error")
        self.assertIn("Port 8 is the USB-C port", rule["text"])
        self.assertEqual(rule["fix"], "Move it to a free port other than 8 and 12.")

    def test_only_a_button_on_port_12(self):
        r = E.analyse(design(mod("usbc", [8]), mod("screen", [11, 12])))
        rule = [x for x in r["rules"] if x["id"] == "port.rule"][0]
        self.assertEqual(rule["level"], "error")
        self.assertIn("Port 12 is the reset port", rule["text"])
        self.assertEqual(rule["ports"], [11, 12])

    def test_button_on_port_12_is_the_reset_button(self):
        r = E.analyse(design(mod("usbc", [8]), mod("button", [12])))
        self.assertNotIn("port.rule", ids(r))
        note = [x for x in r["rules"] if x["id"] == "port.reset"][0]
        self.assertEqual(note["level"], "note")
        self.assertEqual(note["ports"], [12])
        # the reset button is no firmware input: nothing for project.yaml,
        # so the SDK (which reserves port 12) has nothing to refuse
        self.assertNotIn("sdk.placement", ids(r))
        self.assertEqual(r["verdict"]["level"], "ok")

    def test_port_map_names_the_ruled_ports(self):
        r = E.analyse(design(mod("usbc", [8]), mod("button", [1])))
        roles = {p["port"]: p["role"] for p in r["ports"]}
        self.assertEqual((roles[8], roles[12], roles[1]), ("USB-C", "Reset", ""))

    def test_robot_arm_needs_a_power_module(self):
        r = E.analyse(design(mod("usbc", [8]), mod("robot_arm", [3])))
        self.assertIn("power.arm_rail", ids(r))
        r = E.analyse(design(mod("usbc", [8]), mod("power_jack", [1]), mod("robot_arm", [3])))
        self.assertNotIn("power.arm_rail", ids(r))

    def test_stepper_needs_its_supply(self):
        r = E.analyse(design(mod("usbc", [8]), mod("stepper_motor", [9, 10])))
        rule = [x for x in r["rules"] if x["id"] == "power.stepper_vmot"][0]
        self.assertIn("12-24 V", rule["text"])
        self.assertEqual(rule["ports"], [9, 10])

    def test_sdk_placement_rules(self):
        # a 2-port module not on a pair; a UART module off ports 3/4
        r = E.analyse(design(mod("usbc", [8]), mod("speaker", [6, 7]), mod("robot_arm", [1])))
        texts = " ".join(x["text"] for x in r["rules"] if x["id"] == "sdk.placement")
        self.assertIn("not a 2-port pair", texts)
        self.assertIn("needs uart", texts)

    def test_fix_names_free_ports(self):
        r = E.analyse(design(mod("usbc", [7]), mod("screen", [11, 12]), mod("light", [9]),
                             mod("button", [3]), mod("button", [4]),
                             mod("temp_humidity", [13])))
        fixes = {x["fix"] for x in r["rules"] if x["id"] == "sdk.placement"}
        self.assertEqual(fixes, {"Move it to ports 1+2, 5+6 or 10+11: free, and the Atech "
                                 "SDK accepts them."})
        texts = [(x["id"], x["text"]) for x in r["rules"]]
        self.assertEqual(len(texts), len(set(texts)))          # no repeats

    def test_free_places_single(self):
        w = E.analyse(design(mod("usbc", [8]), mod("robot_arm", [1])))["wiring"]
        e = {"id": "robot_arm", "instance": "arm", "ports": [1], "cad": "robot_arm"}
        self.assertEqual(E.free_places(w, e), ["3", "4"])      # UART ports only

    def test_no_driver_is_a_note(self):
        r = E.analyse(design(mod("usbc", [8]), mod("camera", [1])))
        # camera maps to None in SDK_ID, so plan() leaves it out: no rule at all
        self.assertNotIn("error", [x["level"] for x in r["rules"]])

    def test_cables(self):
        r = E.analyse(design(mod("usbc", [8]),
                             mod("knob", [1, 2], cable={1: {"state": "moved"},
                                                        2: {"state": "missing"}})))
        self.assertIn("cable.stale", ids(r))
        self.assertIn("cable.missing", ids(r))
        self.assertEqual(r["rules"][0]["level"], "error")

    def test_more_than_four_motors(self):
        ms = [mod("dc_motor", [p]) for p in (1, 2, 3, 4, 5)]
        r = E.analyse(design(mod("usbc", [8]), *ms))
        self.assertIn("sdk.motors_pwm", ids(r))

    def test_same_i2c_address_note(self):
        r = E.analyse(design(mod("usbc", [8]), mod("temp_humidity", [1]),
                             mod("temp_humidity", [2])))
        rule = [x for x in r["rules"] if x["id"] == "i2c.same_address"][0]
        self.assertEqual(rule["level"], "note")
        self.assertIn("0x38", rule["text"])

    def test_errors_first(self):
        r = E.analyse(design(mod("speaker", [6, 7]), mod("light", [1])))
        order = [E.LEVELS.index(x["level"]) for x in r["rules"]]
        self.assertEqual(order, sorted(order))

    def test_every_rule_has_a_fix(self):
        r = E.analyse(design(mod("speaker", [6, 7]), mod("robot_arm", [1]),
                             mod("stepper_motor", [9, 10]), mod("light", [12])))
        for x in r["rules"]:
            self.assertTrue(x["fix"], x["id"])


class Budget(unittest.TestCase):
    def test_planning_figures_and_unknowns(self):
        b = E.budget(E.analyse(design(mod("usbc", [8]), mod("light", [1]),
                                      mod("button", [2])))["wiring"])
        self.assertEqual(b["total_ma"], 350 + 110)
        self.assertEqual(b["unknown"], 1)
        self.assertEqual(b["supply"], E.DEFAULT_SUPPLY)
        src = {r["key"]: r["source"] for r in b["rows"]}
        self.assertEqual(src["light"], E.SRC_CHIP)
        self.assertEqual(src["button"], "")

    def test_user_values_win(self):
        w = E.analyse(design(mod("usbc", [8]), mod("light", [1])))["wiring"]
        b = E.budget(w, loads={"light": 40, "_board": 120})
        self.assertEqual(b["total_ma"], 160)
        self.assertTrue(all(r["source"] == E.SRC_YOU for r in b["rows"]))

    def test_status_over_and_tight(self):
        w = E.analyse(design(mod("usbc", [8]), mod("speaker", [13, 14])))["wiring"]
        self.assertEqual(E.budget(w, supply="usb2")["status"], "over")      # 1050 > 500
        self.assertEqual(E.budget(w, supply="usbc15")["status"], "ok")      # 70 %
        self.assertEqual(E.budget(w, supply="usb3", loads={"speaker": 300})["status"],
                         "ok")                                              # 650 / 900
        self.assertEqual(E.budget(w, supply="usb3", loads={"speaker": 400})["status"],
                         "tight")                                           # 750 / 900
        self.assertEqual(E.budget(w, supply="usb3", loads={"speaker": 600})["status"],
                         "over")                                            # 950 / 900
        self.assertEqual(E.budget(w, supply="usbc15", loads={"speaker": 900})["status"],
                         "tight")

    def test_over_is_an_error_rule(self):
        r = E.analyse(design(mod("usbc", [8]), mod("speaker", [13, 14])), supply="usb2")
        self.assertIn("power.over", ids(r))

    def test_own_supply_not_counted(self):
        w = E.analyse(design(mod("usbc", [8]), mod("stepper_motor", [9, 10])))["wiring"]
        b = E.budget(w)
        row = [r for r in b["rows"] if r["key"] == "stepper_motor"][0]
        self.assertTrue(row["own_supply"])
        self.assertEqual(b["unknown"], 0)

    def test_power_bank(self):
        w = E.analyse(design(mod("usbc", [8])))["wiring"]
        b = E.budget(w, bank_mah=10000)
        self.assertAlmostEqual(b["bank_hours"], round(10000 * 3.7 / 5 * 0.85 / 350, 1))
        self.assertNotIn("bank_hours", E.budget(w, bank_mah="x"))

    def test_two_of_a_kind_get_their_own_keys(self):
        w = E.analyse(design(mod("usbc", [8]), mod("light", [1]), mod("light", [2])))["wiring"]
        b = E.budget(w, loads={"light#2": 10})
        keys = [r["key"] for r in b["rows"]]
        self.assertEqual(keys, ["_board", "light", "light#2"])
        self.assertEqual(b["total_ma"], 350 + 110 + 10)

    def test_budget_line(self):
        w = E.analyse(design(mod("usbc", [8]), mod("button", [1])))["wiring"]
        line = E.budget_line(E.budget(w))
        self.assertEqual(line, "About 350 mA of 1,500 mA (23 %) from a USB-C charger or "
                               "port, 1.5 A; 1 module not known yet.")
        line = E.budget_line(E.budget(w, supply="usb2"))
        self.assertIn("from a computer USB port (USB 2.0)", line)


class Ports(unittest.TestCase):
    def test_port_map(self):
        r = E.analyse(design(mod("usbc", [8]), mod("screen", [9, 10]),
                             mod("temp_humidity", [3])))
        pm = {p["port"]: p for p in r["ports"]}
        self.assertEqual(len(pm), 14)
        self.assertEqual(pm[9]["lines"], {"A": "DC", "B": "CS"})
        self.assertEqual(pm[10]["lines"], {"A": "MOSI", "B": "SCLK"})
        self.assertEqual(pm[3]["lines"], {"A": "SDA", "B": "SCL"})
        self.assertTrue(pm[3]["uart"])
        self.assertEqual(pm[1]["state"], "free")
        self.assertEqual(pm[12]["state"], "reserved")

    def test_stepper_second_port(self):
        r = E.analyse(design(mod("usbc", [8]), mod("stepper_motor", [9, 10])))
        pm = {p["port"]: p for p in r["ports"]}
        self.assertEqual(pm[9]["lines"], {"A": "STEP", "B": "DIR"})
        self.assertEqual(pm[10]["lines"], {"A": "ENABLE"})


class Writers(unittest.TestCase):
    def setUp(self):
        self.r = E.analyse(design(mod("usbc", [8]), mod("light", [3]), mod("screen", [9, 10]),
                                  mod("knob", [1, 2], cable={}), mod("robot_arm", [4])),
                           project="Desk <buddy> & co", made="16 Nov 2026", bank_mah=5000)

    def test_csv(self):
        rows = list(csv.reader(io.StringIO(E.connections_csv(self.r))))
        self.assertEqual(rows[0][0], "port")
        self.assertEqual([r[0] for r in rows[1:]], ["1", "2", "3", "4", "8", "9", "10"])
        self.assertEqual(rows[1][6], "P1_DATA1, P1_DATA2")

    def test_netlist(self):
        n = json.loads(E.netlist_json(self.r))
        names = {x["name"] for x in n["nets"]}
        self.assertIn("P9_DATA1", names)
        self.assertIn("GND", names)
        self.assertIsNone(n["pin_numbers"])
        gnd = [x for x in n["nets"] if x["name"] == "GND"][0]
        self.assertEqual(gnd["nodes"][0]["ref"], "BOARD")
        self.assertTrue(n["assumptions"])

    def test_svgs_parse_and_escape(self):
        for th in ("light", "dark"):
            for s in (E.schematic_svg(self.r, th), E.power_tree_svg(self.r, th)):
                root = ET.fromstring(s)
                self.assertTrue(root.tag.endswith("svg"))
                self.assertIn("Desk &lt;buddy&gt; &amp; co", s)

    def test_svg_empty(self):
        s = E.schematic_svg(E.analyse(design()))
        self.assertIn("No Atech modules", s)
        ET.fromstring(s)

    def test_markdown(self):
        md = E.markdown(self.r)
        for head in ("## Rule checks", "## Modules", "## Power", "## Bring-up",
                     "## Firmware", "## Not known yet"):
            self.assertIn(head, md)
        self.assertIn("name: Desk__buddy____co", md)
        self.assertIn("power bank", md)

    def test_no_invented_pins_or_colours(self):
        text = E.markdown(self.r) + E.connections_csv(self.r) + E.schematic_svg(self.r)
        self.assertIsNone(re.search(r"(?i)\bpin\s*\d+", text))
        self.assertIsNone(re.search(r"(?i)\b(red|black|brown|yellow)\s+wire", text))

    def test_check_line(self):
        line = E.check_line(self.r)
        self.assertTrue(line.startswith("ELECTRICAL "))
        self.assertIn("power: About", line)

    def test_bringup(self):
        secs = [s["title"] for s in self.r["bringup"]]
        self.assertEqual(secs[:2], ["Before power", "Power and flash"])
        self.assertIn("Test each module", secs)
        self.assertIn("Motors last", secs)
        tests = " ".join(self.r["bringup"][2]["steps"])
        self.assertIn("atech send led_fill r=0 g=0 b=255", tests)
        self.assertIn("atech monitor --key arm_positions", tests)

    def test_firmware_yaml(self):
        y = self.r["firmware"]["yaml"]
        self.assertIn("board: 14port", y)
        self.assertIn("{id: st7735_tft, instance: screen, ports: [9, 10]}", y)
        self.assertNotIn("usbc", y)


if __name__ == "__main__":
    unittest.main()
