"""p2p_qa - test the product by hand, and say honestly whether it was (R1160).

The checks in ./check are the computer's. A product is tested when a
person has printed it, put it together and tried what the brief says it
does. This writes that test plan and keeps the record:

    plan(brief, facts)        [{"id", "group", "test", "expect"}]
    record / save_record / load_record   <product folder>/qa.json
    result(rec, id, "pass" | "fail" | "skip", note="")
    status(tests, rec)        {"state": "not tested" | "partly tested" |
                               "tested" | "failed", "line": "...", counts}
    markdown(tests, rec)      the checklist with the results so far

facts = {"parts": [{"label", "count"}], "modules": ["button", ...],
         "accept": p2p_accept rows | None, "screws": ["M3 x 8 mm screw"]}

Ids are stable (the same design gives the same ids), so results survive a
rebuild; a test whose id is gone is dropped from the status, not counted.
Python 3.9+, stdlib only.
"""
import datetime
import json
import os
import re

QA_FILE = "qa.json"
PASS, FAIL, SKIP = "pass", "fail", "skip"
GROUPS = ("Print", "Fit", "Power", "Modules", "Behaviour", "Brief", "Safety")

BRINGUP = {
    "button": ("Press the button.", "The firmware sees each press once."),
    "knob": ("Turn the knob both ways and press it.", "It counts both ways and clicks."),
    "light": ("Watch the light at power-on.", "All 9 LEDs can light, in every colour."),
    "screen": ("Look at the screen.", "Text is sharp and the right way up."),
    "speaker": ("Make it play a sound.", "Clear, not distorted, not too loud."),
    "microphone": ("Clap near it.", "The sound level jumps."),
    "temp_humidity": ("Compare with a thermometer.", "Within about 1 C after 10 minutes."),
    "scd40_air_quality": ("Breathe near it after a minute.", "CO2 rises, then falls."),
    "distance_sensor": ("Move a hand in front of it.", "The distance follows the hand."),
    "pir": ("Wait 30 s, then walk past.", "It notices the movement."),
    "orientation": ("Tilt it and shake it.", "It reports the tilt and the shake."),
    "dc_motor": ("Run the motor both ways.", "It turns freely, no grinding."),
    "stepper_motor": ("Run the stepper on the 12-24 V supply.", "It moves, no skipping."),
}


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:40] or "x"


def _t(group, tid, test, expect):
    return {"id": "%s:%s" % (group.lower(), tid), "group": group, "test": test,
            "expect": expect}


def plan(brief, facts=None):
    f = facts or {}
    b = brief or {}
    mods = [m for m in (f.get("modules") or [x["module"] for x in b.get("modules") or []])]
    real = [m for m in mods if m not in ("usbc", "power_jack")]
    out = []
    for p in f.get("parts") or []:
        out.append(_t("Print", _slug(p["label"]), "Print %s%s." % (
            "%d x " % p["count"] if p.get("count", 1) > 1 else "", p["label"]),
            "Clean first layer, no stringing that matters, no warped corners."))
    if len(f.get("parts") or []) > 1:
        out.append(_t("Fit", "assemble", "Put the parts together as the assembly steps say.",
                      "Everything fits without force or sanding; nothing rattles."))
    for s in f.get("screws") or []:
        out.append(_t("Fit", _slug(s), "Drive the %ss in." % s,
                      "They bite and hold, the plastic does not crack, no thread strips."))
    if real:
        out.append(_t("Fit", "board", "Fit the Atech board in its pocket.",
                      "It slides in, sits flat, and the USB-C port lines up with its hole."))
        out.append(_t("Power", "boot", "Plug in USB-C.", "It starts in a few seconds."))
        out.append(_t("Power", "warm", "Leave it running for 30 minutes.",
                      "Nothing gets more than hand-warm; it keeps working."))
        for m in real:
            if m in BRINGUP:
                out.append(_t("Modules", m, *BRINGUP[m]))
    for n, r in enumerate(b.get("behaviours") or [], 1):
        out.append(_t("Behaviour", "%d-%s" % (n, _slug(r.get("when"))),
                      "Make this happen: %s." % r.get("when"),
                      "It %s." % (r.get("then") or "").replace("it ", "", 1)))
    for row in f.get("accept") or []:
        if row.get("state") != "met":
            out.append(_t("Brief", _slug(row["id"]), "Check by hand: %s." % row["text"],
                          "Yes (%s by the computer%s)." % (
                              "not known" if row["state"] == "unknown" else "not met",
                              ": " + row["detail"] if row.get("detail") else "")))
    places = set(b.get("places") or [])
    out.append(_t("Safety", "edges", "Run a finger over every edge and corner.",
                  "No sharp edges or loose strings of plastic."))
    if "kids" in places:
        out.append(_t("Safety", "pull", "Pull hard on every small part.",
                      "Nothing comes off that a child could swallow."))
    if "wet" in places:
        out.append(_t("Safety", "splash", "Splash it with water, power off first.",
                      "No water gets to the electronics."))
    return out


# ------------------------------------------------------------------ record
def load_record(folder):
    try:
        with open(os.path.join(folder, QA_FILE), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save_record(folder, rec):
    os.makedirs(folder, exist_ok=True)
    p = os.path.join(folder, QA_FILE)
    with open(p + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=2, ensure_ascii=False)
    os.replace(p + ".tmp", p)
    return p


def result(rec, tid, outcome, note="", when=None, by=""):
    if outcome not in (PASS, FAIL, SKIP):
        raise ValueError("outcome must be pass, fail or skip")
    rec = dict(rec or {})
    rec[tid] = {"result": outcome, "note": note or "", "by": by or "",
                "when": when or datetime.datetime.now().strftime("%d %b %Y %H:%M")}
    return rec


def status(tests, rec):
    rec = rec or {}
    ids = [t["id"] for t in tests]
    got = {i: rec[i]["result"] for i in ids if i in rec and isinstance(rec[i], dict)}
    n_pass = sum(v == PASS for v in got.values())
    n_fail = sum(v == FAIL for v in got.values())
    n_skip = sum(v == SKIP for v in got.values())
    left = len(ids) - len(got)
    if not got:
        state, line = "not tested", "Not tested by hand yet (%d tests planned)." % len(ids)
    elif n_fail:
        bad = [t["test"] for t in tests if got.get(t["id"]) == FAIL]
        state = "failed"
        line = "Tested: %d failed (%s), %d passed%s." % (
            n_fail, "; ".join(bad[:3]), n_pass, ", %d to go" % left if left else "")
    elif left:
        state = "partly tested"
        line = "Partly tested: %d of %d passed, %d to go%s." % (
            n_pass, len(ids), left, ", %d skipped" % n_skip if n_skip else "")
    else:
        state = "tested"
        line = "Tested by hand: all %d passed%s." % (
            n_pass, " (%d skipped)" % n_skip if n_skip else "")
    return {"state": state, "line": line, "pass": n_pass, "fail": n_fail, "skip": n_skip,
            "left": left, "total": len(ids)}


MARK = {PASS: "[x]", FAIL: "[!]", SKIP: "[-]"}


def markdown(tests, rec=None):
    rec = rec or {}
    st = status(tests, rec)
    L = ["## Test by hand", "", st["line"], ""]
    group = None
    for t in tests:
        if t["group"] != group:
            group = t["group"]
            L += ["", "### %s" % group, ""]
        r = rec.get(t["id"]) or {}
        mark = MARK.get(r.get("result"), "[ ]")
        note = " - %s" % r["note"] if r.get("note") else ""
        L.append("- %s %s Expect: %s%s" % (mark, t["test"], t["expect"], note))
    return "\n".join(L).replace("\n\n\n", "\n\n") + "\n"
