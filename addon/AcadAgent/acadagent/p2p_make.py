"""p2p_make - prompt + design -> the whole product pack, headless (R1180).

Run under freecadcmd (no window, nothing on screen):

    P2P_PROMPT="a desk buddy with a button that plays a tune" \\
    P2P_EXAMPLE=desk_buddy            # an agent_kit/examples/*.py, or
    P2P_FCSTD=/path/to/Design.FCStd   # a saved design
    P2P_OUT=~/Desktop/Desk buddy pack # default: ~/Documents/Atech Products/<name>
    ATECH_ARTIFACTS=<repo>/models QT_QPA_PLATFORM=offscreen \\
        freecadcmd addon/AcadAgent/acadagent/p2p_make.py

It builds the design, gathers the facts the Make it window shows, reads
the prompt into a brief (or uses the brief.json beside the design or in
the pack), and writes the product pack: parts list, electrical report,
firmware (the agent's, or written from the brief's behaviours), print
files (3MF, STEP), assembly, brief, done when, print plan, costs, to buy,
manual, quick-start card, label, test plan, changelog, product.html.

Prints "P2P <key> <value>" lines (pack, files, brief, print, cost, qa,
version) and ends with P2P_DONE=0 (or 1 with the error).
"""
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(ADDON))
KIT = os.path.join(HERE, "agent_kit")


def _paths():
    for p in (ADDON, KIT, os.path.join(REPO, "projects")):
        if p not in sys.path:
            sys.path.insert(0, p)
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ["ATECH_NO_REVEAL"] = "1"


def headless_patch():
    """check.py's _headless_patch, read from its source (as the R1004 test)."""
    import ast
    with open(os.path.join(KIT, "check.py"), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    keep = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name in (
        "_headless_patch",)) or (isinstance(n, ast.Assign) and any(
            getattr(t, "id", "") == "_GUI_TOKENS" for t in n.targets))]
    ns = {}
    exec(compile(ast.Module(body=keep, type_ignores=[]), "check.py", "exec"), ns)  # noqa: S102
    return ns["_headless_patch"]


def build_example(name, label=None):
    import FreeCAD as App
    import atech_geom
    doc = App.newDocument("P2P_make")
    doc.Label = label or name.replace("_", " ").capitalize()
    App.setActiveDocument(doc.Name)
    with open(os.path.join(KIT, "examples", name + ".py"), encoding="utf-8") as fh:
        code = fh.read()
    env = {"FreeCAD": App, "App": App, "doc": doc, "__name__": "__agent__",
           atech_geom.VIEW_FN: atech_geom.view_recorder({})}
    exec(compile(headless_patch()(code), name + ".py", "exec"), env)   # noqa: S102
    doc.recompute()
    return doc


def make(doc, prompt=None, out=None, extra_files=True):
    """The pack for doc. Returns (folder, files, status)."""
    from acadagent import product, product_view, export_tools, sdk_tools, p2p_product
    f = product_view.gather(doc)
    if prompt:
        f["prompt"] = prompt
        f["brief"] = p2p_product.kit("p2p_brief").brief(prompt)
    folder = os.path.expanduser(out) if out else f["folder"]
    f["folder"] = folder
    extra = {}
    if extra_files:
        name = sdk_tools.safe_folder(f["project"])
        extra[os.path.join("prints", "%s.3mf" % name)] = (
            "every printed part, ready for a slicer",
            lambda p: export_tools.export_for_print(doc, p, fmt="3MF"))
        extra[os.path.join("cad", "%s.step" % name)] = (
            "the design as STEP, for any CAD tool",
            lambda p: export_tools.export_for_print(doc, p, fmt="STEP"))
        el = f.get("electrical") or {}
        if el.get("modules"):
            def wiring_pdf(p, w=el["wiring"]):
                from acadagent import wiring_view
                wiring_view.export_wiring(w, p)
            extra[os.path.join("electrical", "wiring.pdf")] = ("the wiring diagram",
                                                               wiring_pdf)
    files = product.write_pack(f, folder, extra=extra)
    return folder, files, f.get("p2p_status") or {}


def main():
    _paths()
    try:
        from PySide6 import QtWidgets
        QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    except Exception:                                     # noqa: BLE001
        pass
    import FreeCAD as App
    from acadagent import projects
    projects._mod()
    prompt = os.environ.get("P2P_PROMPT") or None
    if os.environ.get("P2P_FCSTD"):
        doc = App.openDocument(os.path.expanduser(os.environ["P2P_FCSTD"]))
        doc.recompute()
    elif os.environ.get("P2P_EXAMPLE"):
        doc = build_example(os.environ["P2P_EXAMPLE"], os.environ.get("P2P_NAME"))
    else:
        print("P2P error set P2P_EXAMPLE or P2P_FCSTD")
        return 1
    folder, files, st = make(doc, prompt, os.environ.get("P2P_OUT"))
    print("P2P pack %s" % folder)
    print("P2P files %s" % " | ".join(r for r, _w in files))
    for k in ("brief", "print", "cost", "qa", "version"):
        if st.get(k):
            print("P2P %s %s" % (k, st[k]))
    return 0


if __name__ in ("__main__", "p2p_make") or os.path.basename(sys.argv[0] if sys.argv else "") \
        == "freecadcmd" or os.environ.get("P2P_RUN") == "1":
    try:
        rc = main()
    except Exception:                                     # noqa: BLE001
        traceback.print_exc()
        rc = 1
    print("P2P_DONE=%d" % rc)
