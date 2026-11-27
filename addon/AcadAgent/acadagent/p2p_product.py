"""p2p_product - every paper of a prompt-to-product pack, in one place (R1180).

product.write_pack (R1003) makes the product pack: parts list, electrical
report, firmware, print files, assembly, product.html. This adds what turns
it from "the files of a design" into "a product someone can make, use,
test and sell":

    brief.md          the request read into parts, and "Done when"
    done-when.md      each acceptance criterion met / not met / not known
    print-plan.md     which Bambu printer, plates, filament, rough time
    costs.md/.csv     what it costs to make (the user's prices, the site's
                      quote; nothing invented) and to-buy.md (exact sizes)
    manual.md         the user manual; quick-start.html (A6); label.svg
    test-plan.md      the test by hand, with the results so far (qa.json)
    CHANGELOG.md      versions and what changed (revisions.json)
    firmware/project.yaml   written from the brief's behaviours when the
                      agent wrote no code (marked so in the file)

    enrich(f, ws=None, prompt=None, doc=None)   facts + brief, parts, cost
    papers(f, folder)          write them; [(relative path, what)]
    status(f)                  {"brief", "print", "cost", "qa", "version"}
                               one line each, for README and the share message

Plain Python (FreeCAD only in part_rows, which reads a document). Every
paper is written on its own: one that fails is left out, never the pack.
"""
import os
import re
import sys

FILES = ("brief.json", "qa.json", "prices.json", "revisions.json")


def kit(name):
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_kit")
    if d not in sys.path:
        sys.path.append(d)
    return __import__(name)


def _log(msg):
    try:
        import FreeCAD
        FreeCAD.Console.PrintLog("Atech p2p: %s\n" % msg)
    except Exception:                                     # noqa: BLE001
        sys.stderr.write("Atech p2p: %s\n" % msg)


# ------------------------------------------------------------------ facts
#: seconds the "On the bed" measurement may take over all parts of a pack
BED_BUDGET_S = 6.0


def part_rows(doc, bom):
    """bom["printed"] rows with each part's laid-out size and surface, from
    the document: [{"label", "count", "size_mm", "volume_cm3", "area_mm2",
    "colour", "bed"}]."""
    import time
    out = []
    # R1295: the bed measurement has ./check's time budget for all parts
    # together; a part past it is "not measured (time budget)" in the paper
    deadline = time.time() + BED_BUDGET_S
    for r in (bom or {}).get("printed") or []:
        o = None
        try:
            for name in r.get("names") or []:
                o = doc.getObjectsByLabel(name)[0] if doc.getObjectsByLabel(name) else None
                if o is not None:
                    break
        except Exception:                                 # noqa: BLE001
            o = None
        size, area, bed = None, None, None
        if o is not None and hasattr(o, "Shape"):
            bb = o.Shape.BoundBox
            size = [round(bb.XLength, 1), round(bb.YLength, 1), round(bb.ZLength, 1)]
            area = float(o.Shape.Area)
            try:
                # R1270: how it lies on the bed (./check's own measurement)
                if time.time() > deadline:
                    bed = {"label": r["part"], "skipped": "time budget", "flags": []}
                else:
                    bed = kit("atech_print").shape_report(o.Shape, r["part"],
                                                          deadline=deadline)
            except Exception as exc:                      # noqa: BLE001
                _log("bed: %r" % (exc,))
        out.append({"label": r["part"], "count": r["count"], "size_mm": size or [0, 0, 0],
                    "volume_cm3": r.get("volume_cm3") or 0, "area_mm2": area,
                    "colour": r.get("colour") or "", "bed": bed})
    return out


def whole_mm(doc):
    """The overall size of the printed parts (mm), or None."""
    try:
        from . import export_tools
        objs = [o for o in export_tools.agent_parts(doc) if hasattr(o, "Shape")]
        if not objs:
            objs = [o for o in doc.Objects if hasattr(o, "Shape") and not getattr(
                o, "AtechRole", None) and o.Shape.Solids and not o.InList]
        if not objs:
            return None
        bb = objs[0].Shape.BoundBox
        for o in objs[1:]:
            bb.add(o.Shape.BoundBox)
        return [round(bb.XLength, 1), round(bb.YLength, 1), round(bb.ZLength, 1)]
    except Exception as exc:                              # noqa: BLE001
        _log("whole: %r" % (exc,))
        return None


def _bill(f):
    try:
        from . import share
        return share.bill(f.get("bom") or {"printed": [], "hardware": []})
    except Exception as exc:                              # noqa: BLE001
        _log("bill: %r" % (exc,))
        return {"print": [], "atech": [], "buy": [], "filament": []}


def brief_for(f, ws=None, prompt=None):
    """The brief: the chat workspace's (brief.json), else the product
    folder's, else read from prompt, else None."""
    B = kit("p2p_brief")
    for d in (ws, f.get("folder")):
        if d:
            b = B.load(d)
            if b:
                return b
    if prompt:
        return B.brief(prompt)
    return None


def enrich(f, ws=None, prompt=None, doc=None):
    """f (product facts) plus: brief, parts (with sizes), bill, print plan,
    acceptance rows, cost sheet, QA plan + record, revision snapshot."""
    f = dict(f)
    f["brief"] = f.get("brief") or brief_for(f, ws, prompt or f.get("prompt"))
    if doc is not None and not f.get("parts"):
        try:
            f["parts"] = part_rows(doc, f.get("bom"))
        except Exception as exc:                          # noqa: BLE001
            _log("parts: %r" % (exc,))
    f.setdefault("parts", [{"label": r["part"], "count": r["count"], "size_mm": [0, 0, 0],
                            "volume_cm3": r.get("volume_cm3") or 0,
                            "colour": r.get("colour") or ""}
                           for r in (f.get("bom") or {}).get("printed") or []])
    f["bill"] = _bill(f)
    P = kit("p2p_print")
    f["print_plan"] = P.plan(f["parts"], f["brief"])
    C = kit("p2p_cost")
    folder = f.get("folder")
    prices = f.get("prices") or (C.load_prices(folder) if folder else {})
    if not prices:
        root = os.path.dirname(folder) if folder else None
        prices = C.load_prices(root) if root else {}
    f["cost"] = C.costs(f["bill"], prices, f.get("quote"),
                        (f["brief"] or {}).get("quantity") or 1, f["print_plan"]["grams"])
    el = f.get("electrical") or {}
    mods = [{"module": m.get("module") or m.get("key"), "ports": m.get("ports")}
            for m in (el.get("wiring") or {}).get("connections") or []]
    if not mods:
        mods = [{"module": m.get("key") or m.get("module"), "ports": m.get("ports")}
                for m in el.get("modules") or []]
    f["modules_seated"] = mods
    whole = None
    sized = [p["size_mm"] for p in f["parts"] if any(p["size_mm"])]
    if f.get("whole_mm"):
        whole = f["whole_mm"]
    elif doc is not None:
        whole = whole_mm(doc)
    elif len(sized) == 1:
        whole = sized[0]
    f["whole_mm"] = whole
    f["code"] = _code(f)
    if f["brief"]:
        A = kit("p2p_accept")
        errors = sum(r["level"] == "error" for r in el.get("rules") or []) if el else None
        facts = {"modules": mods, "whole_mm": whole,
                 "parts": [p for p in f["parts"] if any(p["size_mm"])] or None,
                 "check": f.get("check"),           # only a check that ran
                 "electrical_errors": errors, "code": f["code"],
                 "colours": sorted({p["colour"] for p in f["parts"] if p.get("colour")})
                 or None}
        f["accept"] = A.check(f["brief"], facts)
    else:
        f["accept"] = None
    Q = kit("p2p_qa")
    screws = C.screw_types(C.buy_list(f["bill"]))
    f["qa_plan"] = Q.plan(f["brief"] or {}, {
        "parts": f["parts"], "modules": [m["module"] for m in mods if m["module"]],
        "accept": f["accept"], "screws": screws})
    f["qa_record"] = Q.load_record(folder) if folder else {}
    f["qa_status"] = Q.status(f["qa_plan"], f["qa_record"])
    return f


def _code(f):
    """The firmware code the pack will carry: the agent's, or None."""
    y = f.get("firmware_yaml")
    if not y or "code:" not in y:
        return None
    return y.split("code:", 1)[1]


def firmware_from_brief(f):
    """(project.yaml text, notes) written from the brief's behaviours, or
    (None, []) when there is nothing to write or the agent wrote code."""
    b = f.get("brief") or {}
    if not b.get("behaviours"):
        return None, []
    if f.get("code") and re.search(r"[;(]", f["code"]):
        return None, []
    el = f.get("electrical") or {}
    entries = [e for e in (el.get("firmware") or {}).get("entries") or [] if e.get("id")]
    if not entries:
        return None, []
    H = kit("p2p_behave")
    F = kit("atech_firmware")
    text, c = H.project(f.get("project") or "product", entries, b["behaviours"],
                        cat=F.catalog())
    if not c["rules"]:
        return None, c["unsupported"]
    head = ("# Written by Prompt2Product from the brief's behaviours (R1140): the agent "
            "wrote no code.\n# Tune the values the notes name; edit freely.\n")
    for n in c["notes"] + ["not written: " + u for u in c["unsupported"]]:
        head += "# - %s\n" % n
    return head + text, c["notes"] + c["unsupported"]


# ------------------------------------------------------------------ papers
def papers(f, folder):
    """Write the papers into folder. f: enrich()ed facts. Returns
    [(relative path, what)]."""
    files = []

    def put(rel, text, what):
        try:
            p = os.path.join(folder, rel)
            os.makedirs(os.path.dirname(p) or folder, exist_ok=True)
            with open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(text() if callable(text) else text)
            files.append((rel, what))
        except Exception as exc:                          # noqa: BLE001
            _log("%s: %r" % (rel, exc))

    os.makedirs(folder, exist_ok=True)
    b = f.get("brief")
    # firmware first: code written from the brief counts for 'Done when'
    text, _notes = firmware_from_brief(f)
    if text:
        f["code"] = text.split("code:", 1)[1] if "code:" in text else text
        if b and f.get("accept") is not None:
            A = kit("p2p_accept")
            f["accept"] = [A._firmware_row(a, b, f["code"]) if a["kind"] == "firmware"
                           else row for a, row in zip(b["acceptance"], f["accept"])]
    if b:
        B = kit("p2p_brief")
        B.save(b, folder)
        put("brief.md", lambda: B.markdown(b), "the request read into parts, and 'Done when'")
    if f.get("accept"):
        A = kit("p2p_accept")
        put("done-when.md", lambda: "# %s\n\n%s" % (f.get("project") or "Product",
                                                    A.markdown(f["accept"])),
            "each 'Done when' criterion: met, not met or not known")
    P = kit("p2p_print")
    if f.get("print_plan") and f["print_plan"]["parts"]:
        # R1270: and how each part goes on the bed (which side down, the
        # first layer, supports and why), when the document was measured
        put("print-plan.md", lambda: P.markdown(f["print_plan"])
            + P.bed_markdown(f.get("parts") or []),
            "which Bambu printer, plates, filament, rough time; which side of each "
            "part goes down, and where supports are needed")
    C = kit("p2p_cost")
    if f.get("cost"):
        put("costs.md", lambda: C.markdown(f["cost"]), "what it costs to make")
        put("costs.csv", lambda: C.csv_text(f["cost"]), "the cost sheet as a table")
        put("to-buy.md", lambda: C.shopping_md(f["bill"]), "what to buy, with exact sizes")
    M = kit("p2p_manual")
    mfacts = {"whole_mm": f.get("whole_mm"), "grams": (f.get("print_plan") or {}).get("grams"),
              "part_count": sum(p.get("count", 1) for p in f.get("parts") or []),
              "modules": [m["module"] for m in f.get("modules_seated") or [] if m["module"]],
              "power_ma": _power_ma(f), "version": _version(f),
              "material": ((f.get("print_plan") or {}).get("material") or {}).get("name")}
    put("manual.md", lambda: M.manual_md(b or {"title": f.get("project")}, mfacts),
        "the user manual (for the person who uses it)")
    put("quick-start.html", lambda: M.card_html(b or {"title": f.get("project")}, mfacts),
        "a one-page quick-start card (prints on A6)")
    put("label.svg", lambda: M.label_svg(b or {"title": f.get("project")}, mfacts),
        "the product label, 80 x 40 mm")
    Q = kit("p2p_qa")
    if f.get("qa_plan"):
        put("test-plan.md", lambda: Q.markdown(f["qa_plan"], f.get("qa_record")),
            "the test by hand, with the results so far")
    if text:
        put(os.path.join("firmware", "project.yaml"), text,
            "firmware written from the brief's behaviours (`atech build`)")
        f["firmware_written"] = True
    R = kit("p2p_rev")
    try:
        snap = R.snapshot({"brief": b, "modules": f.get("modules_seated"),
                           "parts": f.get("parts"), "whole_mm": f.get("whole_mm"),
                           "grams": (f.get("print_plan") or {}).get("grams"),
                           "screws": (f.get("cost") or {}).get("screw_types"),
                           "code": f.get("code") or (text if text else None),
                           "accept": kit("p2p_accept").score(f["accept"])
                           if f.get("accept") else None,
                           "qa": (f.get("qa_status") or {}).get("state")})
        history, _e = R.add(folder, snap)
        f["version"] = history[-1]["version"]
        put("CHANGELOG.md", lambda: "# %s\n\n%s" % (f.get("project") or "Product",
                                                   R.changelog_md(history)),
            "versions and what changed")
    except Exception as exc:                              # noqa: BLE001
        _log("revisions: %r" % (exc,))
    return files


def _power_ma(f):
    try:
        b = (f.get("electrical") or {}).get("budget") or {}
        v = b.get("total_ma") or b.get("ma") or b.get("total")
        return int(round(float(v))) if v else None
    except Exception:                                     # noqa: BLE001
        return None


def _version(f):
    try:
        R = kit("p2p_rev")
        e = R.latest(f.get("folder")) if f.get("folder") else None
        return e["version"] if e else "1.0"
    except Exception:                                     # noqa: BLE001
        return "1.0"


def status(f):
    """One line per paper, for README.md and the share message."""
    out = {}
    if f.get("accept"):
        A = kit("p2p_accept")
        met, total = A.score(f["accept"])
        bad = [r["text"] for r in f["accept"] if r["state"] == "not met"]
        out["brief"] = "%d of %d 'Done when' criteria met%s." % (
            met, total, "; not met: " + "; ".join(bad[:3]) if bad else "")
    pp = f.get("print_plan") or {}
    if pp.get("parts"):
        line = (kit("p2p_print").check_line(pp) or "")[len("PRINT "):].strip()
        out["print"] = (line[:1].upper() + line[1:] + ".") if line else ""
    c = f.get("cost") or {}
    if c.get("lines"):
        C = kit("p2p_cost")
        out["cost"] = "About %s known so far%s." % (
            C._money(c["known_total"], c["currency"] or ""),
            "; %d price%s not known" % (len(c["unknown"]), "" if len(c["unknown"]) == 1
                                        else "s") if c["unknown"] else "")
    if f.get("qa_status"):
        out["qa"] = f["qa_status"]["line"]
    if f.get("version"):
        out["version"] = "Version %s." % f["version"]
    return out
