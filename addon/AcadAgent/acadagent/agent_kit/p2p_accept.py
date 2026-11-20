"""p2p_accept - is the product what the brief asked for? (R1110)

The brief (p2p_brief) ends in acceptance criteria: the product's
definition of done. This module tests a built design against them:

    check(brief, facts)      [{"id", "text", "state", "detail"}], one per
                             criterion; state "met" | "not met" | "unknown"
    score(rows)              (met, total)
    line(rows)               one BRIEF line for ./check
    lines(rows)              the ./check BRIEF lines (the summary, then one
                             per criterion not met)
    markdown(rows)           a table for the product pack
    facts_from_check(res, ws)   the facts from ./check's result dict

facts = {
  "modules": [{"module": "button", "ports": [3]}],    # seated or cabled
  "whole_mm": [x, y, z] | None,                       # all printed parts
  "parts": [{"label": "Case", "size_mm": [x, y, z]}], # printed parts
  "check": "pass" | "fail" | None,
  "electrical_errors": 0 | None,
  "code": "setup + loop text of project.yaml" | None,
  "colours": ["black", ...] | None,                   # the printed parts'
}

"unknown" is honest: a fact the caller could not give is never guessed.
Information only: ./check prints it, no verdict changes on it.
Python 3.9+, stdlib only.
"""
import os
import re

import p2p_printers

MET, NOT_MET, UNKNOWN = "met", "not met", "unknown"
#: mm a size may run over the brief before it is "not met" (rounding,
#: a chamfer): the brief reads words, not tolerances.
SIZE_SLACK = 1.0

#: brief trigger/action module -> the firmware instance the code must use
#: (atech_firmware.INSTANCE through SDK_ID); None: no SDK driver yet.
INSTANCE = {
    "button": "btn", "light": "led", "screen": "screen", "speaker": "spk",
    "microphone": "mic", "dc_motor": "motor", "orientation": "imu",
    "temp_humidity": "th", "distance_sensor": "tof", "knob": "knob",
    "stepper_motor": "stepper", "pir": "pir", "scd40_air_quality": "co2",
    "robot_arm": "arm", "timer": "millis", "soil_sensor": None, "load_cell": None,
    "camera": None, "big_screen": None,
}


def _row(a, state, detail=""):
    return {"id": a["id"], "text": a["text"], "state": state, "detail": detail}


def _fmt(dims):
    return " x ".join("any" if d is None else "%g" % round(d, 1) for d in dims)


def size_ok(want, have, slack=SIZE_SLACK):
    """want [x, y, z] (None: any) against the built size have [x, y, z].
    All three given: the product may be turned any way (largest against
    largest). One or two given: those axes as modelled (Z is up)."""
    if not have:
        return None
    if all(w is not None for w in want):
        return all(h <= w + slack for w, h in zip(sorted(want), sorted(have)))
    return all(w is None or h <= w + slack for w, h in zip(want, have))


def code_uses(code, inst):
    """True when the firmware code names the instance (btn.wasPressed(),
    led.setAll(...), millis())."""
    if inst == "millis":
        return re.search(r"\bmillis\s*\(", code) is not None
    return re.search(r"\b%s\d*\s*(?:\.|->|_\w+\b)" % re.escape(inst), code) is not None


def check(brief, facts):
    facts = facts or {}
    mods = {}
    for m in facts.get("modules") or []:
        mods[m.get("module")] = mods.get(m.get("module"), 0) + 1
    known_mods = facts.get("modules") is not None
    out = []
    for a in brief.get("acceptance") or []:
        k = a["kind"]
        if k == "module":
            if not known_mods:
                out.append(_row(a, UNKNOWN, "no build yet"))
            else:
                n = mods.get(a["module"], 0)
                out.append(_row(a, MET if n >= a["min"] else NOT_MET,
                                "%d in the build" % n))
        elif k == "without":
            if not known_mods:
                out.append(_row(a, UNKNOWN, "no build yet"))
            else:
                n = mods.get(a["module"], 0)
                out.append(_row(a, NOT_MET if n else MET,
                                "%d in the build" % n if n else ""))
        elif k == "print_only":
            if not known_mods:
                out.append(_row(a, UNKNOWN, "no build yet"))
            else:
                out.append(_row(a, MET if not mods else NOT_MET,
                                ("%d module%s in the build" % (sum(mods.values()),
                                 "" if sum(mods.values()) == 1 else "s")) if mods else ""))
        elif k == "size":
            have = facts.get("whole_mm")
            ok = size_ok(a["max_mm"], have)
            out.append(_row(a, UNKNOWN if ok is None else (MET if ok else NOT_MET),
                            ("is %s mm" % _fmt(have)) if have else "no build yet"))
        elif k == "printable":
            parts = facts.get("parts")
            if parts is None:
                out.append(_row(a, UNKNOWN, "no build yet"))
            else:
                big = [p["label"] for p in parts
                       if not p2p_printers.printers_for(p["size_mm"])]
                small = [p["label"] for p in parts
                         if p2p_printers.printers_for(p["size_mm"]) and not
                         p2p_printers.fits(p["size_mm"], p2p_printers.PRINTERS[0][2])]
                if big:
                    out.append(_row(a, NOT_MET, "too big for every Bambu bed: %s"
                                    % ", ".join(big)))
                else:
                    out.append(_row(a, MET, ("needs a 256 mm bed or bigger: %s"
                                             % ", ".join(small)) if small else
                                    "fits even the A1 mini"))
        elif k == "checked":
            c = facts.get("check")
            out.append(_row(a, UNKNOWN if c is None else (MET if c == "pass" else NOT_MET)))
        elif k == "electrical":
            e = facts.get("electrical_errors")
            out.append(_row(a, UNKNOWN if e is None else (MET if e == 0 else NOT_MET),
                            ("%d error%s" % (e, "" if e == 1 else "s")) if e else ""))
        elif k == "firmware":
            out.append(_firmware_row(a, brief, facts.get("code")))
        elif k == "colours":
            have = facts.get("colours")
            if not have:
                out.append(_row(a, UNKNOWN, "no colours set on the parts"))
            else:
                miss = [c for c in a["colours"] if c not in have]
                out.append(_row(a, NOT_MET if miss else MET,
                                ("missing %s" % ", ".join(miss)) if miss else ""))
        else:
            out.append(_row(a, UNKNOWN, "not a criterion this app can test"))
    return out


def _firmware_row(a, brief, code):
    if not code or not code.strip() or not re.search(r"[;(]", code):
        return _row(a, NOT_MET if code is not None else UNKNOWN,
                    "project.yaml has no code yet" if code is not None else "no project.yaml")
    miss, skip = [], []
    for r in brief.get("behaviours") or []:
        for mod in (r.get("trigger"), r.get("action")):
            if not mod:
                continue
            inst = INSTANCE.get(mod)
            if inst is None:
                skip.append(mod)
            elif not code_uses(code, inst):
                miss.append("%s (%s)" % (inst, "when %s" % r["when"] if mod == r.get("trigger")
                                         else r["then"]))
    if miss:
        return _row(a, NOT_MET, "the code never uses %s" % "; ".join(miss))
    if skip:
        return _row(a, UNKNOWN, "no Atech SDK driver yet for %s" % ", ".join(sorted(set(skip))))
    return _row(a, MET, "the code uses every module the behaviours name")


def score(rows):
    return sum(r["state"] == MET for r in rows), len(rows)


def line(rows):
    met, total = score(rows)
    bad = [r for r in rows if r["state"] == NOT_MET]
    unk = [r for r in rows if r["state"] == UNKNOWN]
    s = "BRIEF %d of %d criteria met" % (met, total)
    if bad:
        s += "; not met: %d" % len(bad)
    if unk:
        s += "; unknown: %d" % len(unk)
    return s + " (BRIEF.md 'Done when'; information, not a gate)"


def lines(rows):
    out = [line(rows)]
    for r in rows:
        if r["state"] == NOT_MET:
            out.append("BRIEF   not met: %s%s" % (r["text"], " - %s" % r["detail"]
                                                  if r["detail"] else ""))
    return out


STATE_MARK = {MET: "yes", NOT_MET: "**no**", UNKNOWN: "not known"}


def markdown(rows, title="Done when"):
    met, total = score(rows)
    L = ["## %s (%d of %d)" % (title, met, total), "", "| Criterion | Met | Why |",
         "|---|---|---|"]
    for r in rows:
        L.append("| %s | %s | %s |" % (r["text"].replace("|", "/"), STATE_MARK[r["state"]],
                                       (r["detail"] or "").replace("|", "/")))
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ ./check
def _code_from_project(ws):
    p = os.path.join(ws, "project.yaml")
    if not os.path.isfile(p):
        return None
    try:
        import atech_firmware
        proj = atech_firmware.read_project(p) or {}
        code = proj.get("code") or {}
        if isinstance(code, dict):
            return "%s\n%s" % (code.get("setup") or "", code.get("loop") or "")
        return str(code)
    except Exception:                                   # noqa: BLE001
        try:
            with open(p, encoding="utf-8") as fh:
                t = fh.read()
            return t.split("code:", 1)[1] if "code:" in t else ""
        except OSError:
            return None


def facts_from_check(res, ws, electrical_errors=None):
    """./check's result dict -> facts. Printed parts are the objects that
    are not Atech hardware (the board, modules and cables are meshes and
    not in res["objects"])."""
    parts = []
    for f in res.get("objects") or []:
        if f.get("error") or not f.get("size"):
            continue
        parts.append({"label": f.get("label"), "size_mm": list(f["size"])[:3]})
    at = res.get("atech") or {}
    mods = [{"module": m.get("module") or m.get("label"), "ports": m.get("ports")}
            for m in at.get("modules") or []]
    return {
        "modules": mods,
        "whole_mm": res.get("whole_size"),
        "parts": parts,
        "check": "fail" if res.get("problems") else "pass",
        "electrical_errors": electrical_errors,
        "code": _code_from_project(ws) if ws else None,
        "colours": None,
    }
