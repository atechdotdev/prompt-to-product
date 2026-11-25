"""The port rules under freecadcmd (port 8 the USB-C module only, and the
USB-C module on port 8 only; port 12 a button only): atech_ports refuses
and check() FAILs what the rules forbid, pair_for and the starters keep
off port 12.

    ATECH_ARTIFACTS=<repo>/models freecadcmd fc_port_rules.py

Prints one "CHECK <id> PASS|FAIL" line per assertion and ends with
PORT_RULES_TESTS=<failures>. Run by test_port_rules.py.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(ADDON))
for p in (ADDON, os.path.join(REPO, "projects")):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("ATECH_ARTIFACTS", os.path.join(REPO, "models"))
import FreeCAD as App  # noqa: E402
import atech_ports as ap  # noqa: E402
res = []


def ok(name, cond):
    res.append((name, bool(cond)))
    print("CHECK", name.split(" ")[0], "PASS" if cond else "FAIL", name)


def refused(fn):
    try:
        fn()
        return None
    except ap.PortNotAllowed as e:
        return e
doc = App.newDocument("rules")
ap.board_object(doc)
e = refused(lambda: ap.seat(doc, "usbc", 7));     ok("usbc_on_7_refused", e and e.info["kind"] == "port_rule")
e = refused(lambda: ap.seat(doc, "light", 8));    ok("light_on_8_refused", e and "USB-C port" in str(e))
e = refused(lambda: ap.seat(doc, "speaker", (11, 12))); ok("speaker_on_12_refused", e and "reset port" in str(e))
e = refused(lambda: ap.cable(doc, "light", 12, ap.module_placement("light", (30, -140, 20), face="-Y", cable="+Z")))
ok("cable_light_12_refused", e is not None)
u = ap.seat(doc, "usbc", 8);                       ok("usbc_on_8_ok", u is not None)
b = ap.seat(doc, "button", 12);                    ok("button_on_12_ok", b is not None)
l = ap.seat(doc, "light", 3)
e = refused(lambda: ap.move(doc, l, 12));          ok("move_light_to_12_refused", e is not None)
ok("light_still_on_3", list(l.AtechPorts) == [3])
pair = ap.pair_for(doc, "screen", 11);             ok("pair_for_avoids_12 %s" % (pair,), 12 not in pair)
v = ap.check(doc)
ok("check_passes_rules", all(r.get("port_rule", {}).get("verdict") == ap.PASS for r in v.values()))
# an old document: a module already on a forbidden port
l.AtechPorts = [12]
v = ap.check(doc, only=[l.Name])[l.Name]
ok("check_fails_old_doc", v["port_rule"]["verdict"] == ap.FAIL and "reset port" in v["port_rule"]["why"])
ok("first_why_says_rule", "reset port" in (ap.first_why(v) or ""))
ok("card_has_rules", "PORT RULES" in ap.api_card())
# the user's own document, re-created as a build's context: not refused
d3 = App.newDocument("seeded")
ap.board_object(d3)
with ap._seeding():
    old = ap.seat(d3, "light", 12)
ok("seeding_keeps_old_module", list(old.AtechPorts) == [12])
ok("seeding_still_fails_check",
   ap.check(d3)[old.Name]["port_rule"]["verdict"] == ap.FAIL)
ok("refuses_again_after_seeding", refused(lambda: ap.seat(d3, "speaker", (11, 12))) is not None)
from acadagent import projects  # noqa: E402
d2 = App.newDocument("starter")
rep = projects.seat_starter(d2, ["usbc", "button", "light"], ap=ap)
placed = {p["name"]: p["ports"] for p in rep["placed"]}
ok("starter %s" % placed, placed.get("usbc") == [8] and 12 not in sum(placed.values(), []) and 8 not in placed.get("button", []))
print("PORT_RULES_TESTS=%d" % sum(1 for _, c in res if not c))
