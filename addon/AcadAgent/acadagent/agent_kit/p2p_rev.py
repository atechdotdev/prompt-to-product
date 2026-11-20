"""p2p_rev - versions of a product, and what changed between them (R1170).

Each time the product pack is made, a snapshot of what defines the
product is kept in <product folder>/revisions.json. When it differs from
the last one it becomes a new version: the major number moves when the
electronics or the brief change (a different product), the minor number
when only the parts or the firmware change.

    snapshot(facts)           the compact facts that define the product
    add(folder, snap)         keep it; returns (history, the new entry or
                              None when nothing changed)
    diff(a, b)                what changed, in plain words
    changelog_md(history)     every version, newest first
    latest(folder)            the last entry or None

facts (the same as the pack's): {"brief": p2p_brief dict | None,
 "modules": [{"module", "ports"}], "parts": [{"label", "count", "size_mm",
 "volume_cm3"}], "whole_mm", "grams", "screws": [...], "code": str | None,
 "accept": (met, total) | None, "qa": "not tested" | ...}
Python 3.9+, stdlib only.
"""
import datetime
import hashlib
import json
import os

REV_FILE = "revisions.json"


def _h(text):
    return hashlib.sha1((text or "").encode("utf-8")).hexdigest()[:10] if text else None


def snapshot(facts):
    f = facts or {}
    b = f.get("brief") or {}
    mods = sorted(("%s@%s" % (m.get("module"), ",".join(str(p) for p in m.get("ports") or []))
                   for m in f.get("modules") or []))
    parts = sorted(({"label": p.get("label"), "count": int(p.get("count") or 1),
                     "size_mm": [round(float(v), 1) for v in (p.get("size_mm") or [])][:3],
                     "volume_cm3": round(float(p.get("volume_cm3") or 0), 1)}
                    for p in f.get("parts") or []), key=lambda p: p["label"] or "")
    return {
        "brief": _h(json.dumps({k: b.get(k) for k in ("modules", "size", "behaviours",
                                                     "without", "power")},
                               sort_keys=True)) if b else None,
        "title": b.get("title"),
        "modules": mods,
        "parts": parts,
        "whole_mm": [round(float(v), 1) for v in f.get("whole_mm") or []][:3] or None,
        "grams": round(float(f.get("grams") or 0)),
        "screws": sorted(f.get("screws") or []),
        "code": _h(f.get("code")),
        "accept": list(f["accept"]) if f.get("accept") else None,
        "qa": f.get("qa"),
    }


def _key(s):
    """What makes two snapshots the same product version (not the QA state
    or the acceptance score: those are results, not the design)."""
    return json.dumps({k: s.get(k) for k in ("brief", "modules", "parts", "whole_mm",
                                             "screws", "code")}, sort_keys=True)


def load(folder):
    try:
        with open(os.path.join(folder, REV_FILE), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, list) else []
    except (OSError, ValueError):
        return []


def latest(folder):
    h = load(folder)
    return h[-1] if h else None


def _bump(prev, snap):
    if prev is None:
        return "1.0"
    major, minor = (int(x) for x in prev["version"].split("."))
    p = prev["snap"]
    if p.get("modules") != snap.get("modules") or p.get("brief") != snap.get("brief"):
        return "%d.0" % (major + 1)
    return "%d.%d" % (major, minor + 1)


def add(folder, snap, when=None, note=""):
    history = load(folder)
    prev = history[-1] if history else None
    if prev is not None and _key(prev["snap"]) == _key(snap):
        # same design: keep the newest results on the same version
        prev["snap"]["accept"] = snap.get("accept")
        prev["snap"]["qa"] = snap.get("qa")
        _write(folder, history)
        return history, None
    entry = {"version": _bump(prev, snap),
             "when": when or datetime.datetime.now().strftime("%d %b %Y %H:%M"),
             "snap": snap, "changes": diff(prev["snap"], snap) if prev else ["First version."],
             "note": note or ""}
    history.append(entry)
    _write(folder, history)
    return history, entry


def _write(folder, history):
    os.makedirs(folder, exist_ok=True)
    p = os.path.join(folder, REV_FILE)
    with open(p + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(history, fh, indent=2, ensure_ascii=False)
    os.replace(p + ".tmp", p)


def _mm(d):
    return " x ".join("%g" % v for v in d) + " mm" if d else "?"


def diff(a, b):
    a, b = a or {}, b or {}
    out = []
    if a.get("brief") != b.get("brief") and a.get("brief") and b.get("brief"):
        out.append("The brief changed.")
    am = {m.split("@")[0]: m.split("@")[1] for m in a.get("modules") or []}
    bm = {m.split("@")[0]: m.split("@")[1] for m in b.get("modules") or []}
    for m in sorted(set(bm) - set(am)):
        out.append("Added the %s (port %s)." % (m.replace("_", " "), bm[m]))
    for m in sorted(set(am) - set(bm)):
        out.append("Removed the %s." % m.replace("_", " "))
    for m in sorted(set(am) & set(bm)):
        if am[m] != bm[m]:
            out.append("Moved the %s from port %s to %s." % (m.replace("_", " "), am[m], bm[m]))
    ap = {p["label"]: p for p in a.get("parts") or []}
    bp = {p["label"]: p for p in b.get("parts") or []}
    for lab in sorted(set(bp) - set(ap)):
        out.append("New part: %s." % lab)
    for lab in sorted(set(ap) - set(bp)):
        out.append("Part gone: %s." % lab)
    for lab in sorted(set(ap) & set(bp)):
        x, y = ap[lab], bp[lab]
        if x["size_mm"] != y["size_mm"]:
            out.append("%s: %s -> %s." % (lab, _mm(x["size_mm"]), _mm(y["size_mm"])))
        elif abs(x["volume_cm3"] - y["volume_cm3"]) >= 0.5:
            out.append("%s: reshaped (%g -> %g cm3)." % (lab, x["volume_cm3"], y["volume_cm3"]))
        if x["count"] != y["count"]:
            out.append("%s: %d -> %d copies." % (lab, x["count"], y["count"]))
    if a.get("whole_mm") != b.get("whole_mm") and a.get("whole_mm") and b.get("whole_mm"):
        out.append("Overall size %s -> %s." % (_mm(a["whole_mm"]), _mm(b["whole_mm"])))
    if a.get("screws") != b.get("screws"):
        out.append("Screws: %s -> %s." % (", ".join(a.get("screws") or []) or "none",
                                         ", ".join(b.get("screws") or []) or "none"))
    if a.get("code") != b.get("code"):
        out.append("The firmware changed." if a.get("code") and b.get("code") else
                   "Firmware added." if b.get("code") else "Firmware removed.")
    if a.get("grams") != b.get("grams") and abs((a.get("grams") or 0) - (b.get("grams") or 0)) \
            >= 2:
        out.append("Filament about %d g -> %d g." % (a.get("grams") or 0, b.get("grams") or 0))
    if a.get("accept") != b.get("accept") and b.get("accept"):
        out.append("Brief criteria met: %s -> %d of %d." % (
            "%d of %d" % tuple(a["accept"]) if a.get("accept") else "-", b["accept"][0],
            b["accept"][1]))
    return out or ["No visible change."]


def changelog_md(history):
    L = ["## Versions", ""]
    for e in reversed(history or []):
        L += ["### %s (%s)" % (e["version"], e["when"]), ""]
        L += ["- " + c for c in e["changes"]]
        if e.get("note"):
            L.append("- Note: %s" % e["note"])
        L.append("")
    return "\n".join(L)
