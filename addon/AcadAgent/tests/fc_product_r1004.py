"""R1004 under freecadcmd: Make it on real example builds. The facts come
from the document (parts list, electrical report), and the product pack
holds real print files (3MF), a STEP, the wiring and electrical PDFs and
product.html.

    ATECH_ARTIFACTS=<repo>/models QT_QPA_PLATFORM=offscreen ATECH_SDK_CATALOG=snapshot \
        freecadcmd fc_product_r1004.py

Prints one "CHECK <id> PASS|FAIL <detail>" line per assertion and ends with
R1004_TESTS=<failures>.
"""
import os
import sys
import tempfile
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
os.environ["ATECH_NO_REVEAL"] = "1"

import FreeCAD as App  # noqa: E402
from PySide6 import QtWidgets  # noqa: E402

APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
from acadagent import projects  # noqa: E402
projects._mod()
import atech_geom  # noqa: E402

FAILS = []
EXAMPLES = ("weather_station", "debug_duck")


def check(cid, ok, detail=""):
    print("CHECK %s %s %s" % (cid, "PASS" if ok else "FAIL", str(detail)[:300]))
    if not ok:
        FAILS.append(cid)


def headless_patch():
    """check.py's _headless_patch, read from its source (as fc_wiring_r960)."""
    import ast
    src = open(os.path.join(KIT, "check.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    keep = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name in (
        "_headless_patch",)) or (isinstance(n, ast.Assign) and any(
            getattr(t, "id", "") == "_GUI_TOKENS" for t in n.targets))]
    ns = {}
    exec(compile(ast.Module(body=keep, type_ignores=[]), "check.py", "exec"), ns)  # noqa: S102
    return ns["_headless_patch"]


PATCH = headless_patch()


def build(name):
    for d in list(App.listDocuments()):
        App.closeDocument(d)
    doc = App.newDocument("Make_it")
    doc.Label = name.replace("_", " ").title()
    App.setActiveDocument(doc.Name)
    code = open(os.path.join(KIT, "examples", name + ".py"), encoding="utf-8").read()
    env = {"FreeCAD": App, "App": App, "doc": doc, "__name__": "__agent__",
           atech_geom.VIEW_FN: atech_geom.view_recorder({})}
    exec(compile(PATCH(code), name + ".py", "exec"), env)     # noqa: S102
    doc.recompute()
    return doc


def main():
    from acadagent import sdk_tools, product, product_view, export_tools, wiring_view
    from acadagent import electrical_suite
    sdk_tools.PRODUCTS_DIR = tempfile.mkdtemp()
    for name in EXAMPLES:
        try:
            doc = build(name)
        except Exception:                               # noqa: BLE001
            check("%s_builds" % name, False, traceback.format_exc()[-400:])
            continue
        f = product_view.gather(doc)
        check("%s_built" % name, f["built"])
        n_printed = sum(r["count"] for r in f["bom"]["printed"])
        check("%s_printed_parts" % name, n_printed > 0, n_printed)
        ss = product.steps(f)
        check("%s_seven_steps" % name, len(ss) == 7)
        el = f["electrical"]
        mods = [m["module"] for m in el["modules"]]
        if name == "weather_station":
            check("ws_modules", {"usbc", "screen", "light", "temp_humidity"} <= set(mods), mods)
            check("ws_firmware_entries",
                  len([e for e in el["firmware"]["entries"] if e.get("id")]) == 5,
                  el["firmware"]["entries"])
            check("ws_board_hardware",
                  any(r["kind"] == "Board" for r in f["bom"]["hardware"]))
            check("ws_cable_in_assembly",
                  "Connect the cabled modules" in [s["title"] for s in product.assembly(f)])
        else:
            check("duck_print_only_or_modules", isinstance(mods, list))
        folder = os.path.join(sdk_tools.PRODUCTS_DIR, name)

        def three_mf(path, doc=doc):
            export_tools.export_for_print(doc, path, fmt="3MF")

        def step(path, doc=doc):
            export_tools.export_for_print(doc, path, fmt="STEP")
        extra = {"prints/%s.3mf" % name: ("print file", three_mf),
                 "cad/%s.step" % name: ("STEP", step)}
        if el["modules"]:
            extra["electrical/wiring.pdf"] = (
                "wiring", lambda p, w=el["wiring"]: wiring_view.export_wiring(w, p))
            extra["electrical/electrical-report.pdf"] = (
                "report", lambda p, r=el: electrical_suite.report_pdf(r, p))
        files = [a for a, _b in product.write_pack(f, folder, extra=extra)]
        for want in ("prints/%s.3mf" % name, "cad/%s.step" % name, "product.html",
                     "README.md", "assembly.md", "parts-list.csv"):
            p = os.path.join(folder, want)
            check("%s_pack_%s" % (name, os.path.basename(want)),
                  want in files and os.path.isfile(p) and os.path.getsize(p) > 200,
                  (want, os.path.getsize(p) if os.path.isfile(p) else None))
        if el["modules"]:
            for want in ("electrical/wiring.pdf", "electrical/electrical-report.pdf",
                         "firmware/project.yaml", "electrical/schematic.svg"):
                check("%s_pack_%s" % (name, os.path.basename(want)), want in files, files)
        print("PACK %s %s" % (name, folder))
    print("R1004_TESTS=%d" % len(FAILS))


try:
    main()
except Exception:                                       # noqa: BLE001
    traceback.print_exc()
    print("R1004_TESTS=99")
