"""R960 under freecadcmd: the app's wiring walk (atech_wiring.modules_from_doc)
agrees with check.py's _atech_report on real example builds, and the wiring
built from it has every module the board carries.

    ATECH_ARTIFACTS=<repo>/models QT_QPA_PLATFORM=offscreen ATECH_SDK_CATALOG=snapshot \
        freecadcmd fc_wiring_r960.py

Prints one "CHECK <id> PASS|FAIL <detail>" line per assertion and ends with
R960_TESTS=<failures>.
"""
import ast
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(ADDON))
KIT = os.path.join(ADDON, "acadagent", "agent_kit")
for p in (ADDON, KIT, os.path.join(REPO, "projects")):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("ATECH_SDK_CATALOG", "snapshot")

import FreeCAD as App  # noqa: E402

from acadagent import projects  # noqa: E402

projects._mod()
import atech_geom  # noqa: E402
import atech_ports as ap  # noqa: E402
import atech_wiring as aw  # noqa: E402

FAILS = []
EXAMPLES = ("toy_car", "arm_dock", "retro_camera", "handheld_console", "debug_duck")


def check(cid, ok, detail=""):
    print("CHECK %s %s %s" % (cid, "PASS" if ok else "FAIL", detail))
    if not ok:
        FAILS.append(cid)


def check_report():
    """check.py's own _atech_report (and placement_list), read from its
    source: check.py is a script, importing it would run it."""
    src = open(os.path.join(KIT, "check.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    keep = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name in (
        "_atech_report", "placement_list", "_headless_patch")) or (
        isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "_GUI_TOKENS"
                                          for t in n.targets))]
    ns = {}
    exec(compile(ast.Module(body=keep, type_ignores=[]), "check.py", "exec"), ns)  # noqa: S102
    return ns["_atech_report"], ns["_headless_patch"]


def build(name, patch):
    for d in list(App.listDocuments()):
        App.closeDocument(d)
    doc = App.newDocument("Wiring")
    App.setActiveDocument(doc.Name)
    code = open(os.path.join(KIT, "examples", name + ".py"), encoding="utf-8").read()
    env = {"FreeCAD": App, "App": App, "doc": doc, "__name__": "__agent__",
           atech_geom.VIEW_FN: atech_geom.view_recorder({})}
    exec(compile(patch(code), name + ".py", "exec"), env)   # noqa: S102
    doc.recompute()
    return doc


def comparable(at):
    out = []
    for m in (at or {}).get("modules") or []:
        out.append((m["module"], tuple(m["ports"]), m["label"], m["name"], m.get("joint"),
                    tuple(sorted((c["label"], c["port"], round(c["length"], 6))
                                 for c in m.get("cables") or [] if "label" in c))))
    return sorted(out)


def main():
    report, patch = check_report()
    for name in EXAMPLES:
        try:
            doc = build(name, patch)
        except Exception:                               # noqa: BLE001
            check("%s_builds" % name, False, traceback.format_exc()[-400:])
            continue
        mine = aw.modules_from_doc(doc)
        theirs = report(doc, set())
        check("%s_same_walk" % name, comparable(mine) == comparable(theirs),
              "%s vs %s" % (comparable(mine)[:3], comparable(theirs)[:3]))
        states = {c.get("state") for m in mine["modules"] for c in m.get("cables") or []}
        check("%s_cables_ok" % name, states <= {"ok"}, states)
        occ = ap.occupied(doc)
        w = aw.build(mine)
        ports = {p for c in w["connections"] for p in c["ports"]}
        check("%s_every_port" % name, ports == set(occ), "%s vs %s" % (sorted(ports), sorted(occ)))
        if name == "arm_dock":
            check("arm_dock_note", any(n.startswith("WIRING robot_arm") for n in aw.notes(mine)))
        else:
            check("%s_no_note" % name, aw.notes(mine) == [], aw.notes(mine))
        if name == "toy_car":
            check("toy_car_port8_flag", any(f.startswith("Port 8:") for f in w["flags"]), w["flags"])
        if name == "handheld_console":
            check("handheld_8_and_12_flags",
                  {f.split(":")[0] for f in w["flags"]} >= {"Port 8", "Port 12"}, w["flags"])
        # a module moved after its cable was made shows as "moved"
        cabled = [o for o in doc.Objects if getattr(o, "AtechJoint", None) == "cable"]
        if cabled:
            o = cabled[0]
            pl = o.Placement
            o.Placement = App.Placement(pl.Base + App.Vector(5, 0, 0), pl.Rotation)
            moved = [m for m in aw.modules_from_doc(doc)["modules"] if m["name"] == o.Name][0]
            check("%s_moved_cable" % name,
                  {c["state"] for c in moved["cables"]} == {"moved"}, moved["cables"])
            o.Placement = pl
    print("R960_TESTS=%d" % len(FAILS))


try:
    main()
except Exception:                                       # noqa: BLE001
    traceback.print_exc()
    print("R960_TESTS=99")
