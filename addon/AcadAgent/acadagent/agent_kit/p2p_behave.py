"""p2p_behave - the brief's "when ..., it ..." becomes firmware (R1140).

The brief (p2p_brief) reads behaviours from the prompt: {"when", "then",
"trigger", "action"}. This writes them as the code: block of the
product's project.yaml, using only the calls the Atech SDK catalog
documents for each module (its usage text), so `atech build` compiles it:

    code(behaviours, instances)   {"setup", "loop", "notes", "unsupported",
                                   "rules": [{"behaviour", "cond", "kind"}]}
    project(name, entries, behaviours)   project.yaml text with that code
    threshold(text, kind)         "above 30 degrees" -> 30.0 (else the default)

instances: {CAD module: firmware instance} from atech_firmware.plan()
(button -> btn, light -> led, ...). A behaviour whose module has no SDK
driver, or is not in the build, is left out and listed in "unsupported";
a guessed threshold is listed in "notes" so the user can tune it.

Rules of the SDK guide the code keeps: loop never blocks (millis(), no
delay()); PIR and knob call update() first; the light calls show() after
staging; the screen's display() is slow, so it is called only on change;
the speaker never plays on boot. Python 3.9+, stdlib only.
"""
import re

import atech_firmware

#: level triggers: (default threshold, unit, comparison) - planning values,
#: always named in "notes"; the prompt's own number wins.
LEVELS = {
    "hot": (28.0, "C", ">"), "cold": (16.0, "C", "<"),
    "humid": (70.0, "%", ">"), "dry_air": (30.0, "%", "<"),
    "co2": (1000.0, "ppm", ">"), "close": (150.0, "mm", "<"),
    "tilt": (45.0, "deg", ">"), "flip": (150.0, "deg", ">"),
    "loud": (2000.0, "", ">"),
}
COLOURS = {
    "red": (255, 0, 0), "green": (0, 255, 0), "blue": (0, 0, 255),
    "white": (255, 255, 255), "yellow": (255, 180, 0), "orange": (255, 80, 0),
    "purple": (160, 0, 255), "pink": (255, 60, 120), "cyan": (0, 200, 255),
    "warm": (255, 140, 40),
}
STATEFUL = ("light", "screen", "dc_motor")


def _num(text):
    """The first number standing on its own ('co2', 'm3' are names)."""
    m = re.search(r"(?<![\w.])(-?\d+(?:\.\d+)?)", text or "")
    return float(m.group(1)) if m else None


def threshold(text, kind):
    """The prompt's number for a level trigger, in the trigger's unit
    ('within 20 cm' -> 200 mm), or the default. (value, guessed)."""
    t = (text or "").lower()
    n = _num(t)
    default = LEVELS[kind][0]
    if n is None:
        return default, True
    if kind == "close":
        if re.search(r"\d\s*cm\b", t):
            n *= 10
        elif re.search(r"\d\s*m\b", t):
            n *= 1000
    if kind in ("hot", "cold") and re.search(r"\d\s*(?:°\s*)?f\b|fahrenheit", t):
        n = (n - 32) * 5.0 / 9.0
    return round(n, 1), False


def _inst(instances, mod):
    return (instances or {}).get(mod)


# ------------------------------------------------------------------ triggers
def trigger(r, instances, n=1):
    """{"pre": [lines before the checks], "cond": C++ bool, "kind": "edge" |
    "level", "off": C++ bool for the edge that ends it (or None), "note"}
    or None when the trigger can't be written."""
    mod = r.get("trigger")
    w = (r.get("when") or "").lower()
    if mod == "timer":
        m = re.search(r"every\s+(\d+)?\s*(second|minute|hour)s?", w)
        k = int(m.group(1)) if m and m.group(1) else 1
        unit = (m.group(2) if m else "minute")
        ms = k * {"second": 1000, "minute": 60000, "hour": 3600000}[unit]
        return {"pre": [], "cond": "_p2p_due(_p2p_t%d, %dUL)" % (n, ms), "kind": "edge",
                "off": None, "timer": "_p2p_t%d" % n,
                "note": None if m else "a timer of 1 minute (the prompt gave no period)",
                "helper": "timer"}
    i = _inst(instances, mod)
    if not i:
        return None
    if mod == "button":
        if re.search(r"\b(held|hold|long)\b", w):
            return {"pre": [], "cond": "%s.isPressed()" % i, "kind": "level", "off": None,
                    "note": None}
        if re.search(r"\breleased?\b|let go", w):
            return {"pre": [], "cond": "%s.wasReleased()" % i, "kind": "edge", "off": None,
                    "note": None}
        return {"pre": [], "cond": "%s.wasPressed()" % i, "kind": "edge", "off": None,
                "note": None}
    if mod == "knob":
        pre = ["%s.update();" % i]
        if re.search(r"press|click|push", w):
            return {"pre": pre, "cond": "%s.wasPressed()" % i, "kind": "edge", "off": None,
                    "note": None}
        return {"pre": pre, "cond": "(%s.wasRotatedCW() || %s.wasRotatedCCW())" % (i, i),
                "kind": "edge", "off": None, "note": None}
    if mod == "pir":
        return {"pre": ["%s.update();" % i],
                "cond": "(%s.isWarmedUp() && %s.wasTriggered())" % (i, i), "kind": "edge",
                "off": "%s.wasCleared()" % i, "note": None}
    if mod in ("temp_humidity", "scd40_air_quality"):
        if mod == "scd40_air_quality" and not re.search(r"hot|cold|warm|humid", w):
            v, guessed = threshold(w, "co2")
            return {"pre": [], "cond": "(%s.isReady() && %s.readCO2() > %d)" % (i, i, v),
                    "kind": "level", "off": None,
                    "note": "CO2 above %d ppm%s" % (v, " (a planning value: tune it)"
                                                    if guessed else "")}
        if re.search(r"humid|damp|wet", w):
            v, guessed = threshold(w, "humid")
            cond = "%s.readHumidity() > %.1ff" % (i, v)
            what = "humidity above %g %%" % v
        elif re.search(r"cold|cool|freez|chilly", w):
            v, guessed = threshold(w, "cold")
            cond = "%s.readTemperature() < %.1ff" % (i, v)
            what = "below %g C" % v
        else:
            v, guessed = threshold(w, "hot")
            cond = "%s.readTemperature() > %.1ff" % (i, v)
            what = "above %g C" % v
        return {"pre": [], "cond": cond, "kind": "level", "off": None,
                "note": what + (" (a planning value: tune it)" if guessed else "")}
    if mod == "distance_sensor":
        v, guessed = threshold(w, "close")
        return {"pre": [], "cond": "(%s.isReady() && %s.getMinDistance() < %d)" % (i, i, v),
                "kind": "level", "off": None,
                "note": "closer than %d mm%s" % (v, " (a planning value: tune it)"
                                                 if guessed else "")}
    if mod == "orientation":
        if re.search(r"shak", w):
            return {"pre": [], "cond": "%s.wasShaken()" % i, "kind": "edge", "off": None,
                    "note": None}
        kind = "flip" if re.search(r"flip|upside|face.?down", w) else "tilt"
        v, guessed = threshold(w, kind)
        return {"pre": [], "cond": "%s.getTiltAngle() > %.1ff" % (i, v), "kind": "level",
                "off": None, "note": "tilted more than %g degrees%s" % (
                    v, " (a planning value: tune it)" if guessed else "")}
    if mod == "microphone":
        v, guessed = threshold(w, "loud")
        return {"pre": [], "cond": "%s.isSoundDetected(%d)" % (i, v), "kind": "level",
                "off": None, "note": "sound level above %d%s" % (
                    v, " (a planning value: tune it)" if guessed else "")}
    return None


# ------------------------------------------------------------------ actions
def _colour(text):
    t = (text or "").lower()
    for name, rgb in COLOURS.items():
        if re.search(r"\b%s\b" % name, t):
            return name, rgb
    return "white", (200, 200, 200)


def action(r, instances, readings):
    """{"on": [lines], "off": [lines] | None, "kind": "state" | "event"}
    or None. readings: {"temperature": expr, ...} for the screen."""
    mod = r.get("action")
    t = (r.get("then") or "").lower()
    i = _inst(instances, mod)
    if not i:
        return None
    if mod == "speaker":
        if re.search(r"tune|melody|song|chime|music|jingle", t):
            on = ["%s.playNote(NOTE_C5, 120);" % i, "%s.playNote(NOTE_E5, 120);" % i,
                  "%s.playNote(NOTE_G5, 200);" % i]
        elif re.search(r"alarm|siren|alert", t):
            on = ["%s.playNote(NOTE_A5, 150);" % i, "%s.playNote(NOTE_E5, 150);" % i,
                  "%s.playNote(NOTE_A5, 150);" % i, "%s.playNote(NOTE_E5, 150);" % i]
        else:
            on = ["%s.playTone(NOTE_A4, 200);" % i]
        return {"on": on, "off": None, "kind": "event"}
    if mod == "light":
        if re.search(r"\b(off|dark|goes out)\b", t):
            return {"on": ["%s.clear();" % i, "%s.show();" % i], "off": None, "kind": "state"}
        name, (rr, g, b) = _colour(t)
        return {"on": ["%s.setAll(%d, %d, %d);   // %s" % (i, rr, g, b, name),
                       "%s.show();" % i],
                "off": ["%s.clear();" % i, "%s.show();" % i], "kind": "state"}
    if mod == "screen":
        quoted = re.search(r"[\"“']([^\"”']{1,20})[\"”']", r.get("then") or "")
        show = None
        for word, expr in (readings or {}).items():
            if re.search(r"\b%s\b" % word, t):
                show = expr
                break
        if quoted:
            body = ['%s.displayText("%s", 4, 30, 2, ST7735_TFT::COLOR_WHITE);'
                    % (i, quoted.group(1).replace('"', "'"))]
        elif show:
            body = ["char buf[24];", "snprintf(buf, sizeof buf, \"%s\", %s);" % (
                show[1], show[0]),
                "%s.displayText(buf, 4, 30, 2, ST7735_TFT::COLOR_WHITE);" % i]
        else:
            txt = re.sub(r"\s+", " ", r.get("when") or "hello")[:18]
            body = ['%s.displayText("%s", 4, 30, 1, ST7735_TFT::COLOR_WHITE);'
                    % (i, txt.replace('"', "'"))]
        return {"on": ["%s.clear();" % i] + body + ["%s.display();" % i],
                "off": ["%s.clear();" % i, "%s.display();" % i], "kind": "state"}
    if mod == "dc_motor":
        if re.search(r"\b(stop|stops|brake|halt)", t):
            return {"on": ["%s.brake();" % i], "off": ["%s.forward(200);" % i],
                    "kind": "state"}
        if re.search(r"revers|back", t):
            return {"on": ["%s.reverse(200);" % i], "off": ["%s.stop();" % i],
                    "kind": "state"}
        return {"on": ["%s.forward(200);" % i], "off": ["%s.stop();" % i], "kind": "state"}
    return None


def readings_for(instances):
    """What the screen can show: {word: (expr, printf format)}."""
    out = {}
    th = _inst(instances, "temp_humidity")
    co2 = _inst(instances, "scd40_air_quality")
    tof = _inst(instances, "distance_sensor")
    if th:
        out["temperature"] = ("%s.readTemperature()" % th, "%.1f C")
        out["humidity"] = ("%s.readHumidity()" % th, "%.0f %%")
    if co2:
        out["co2"] = ("%s.readCO2()" % co2, "%u ppm")
        out.setdefault("temperature", ("%s.readTemperature()" % co2, "%.1f C"))
    if tof:
        out["distance"] = ("%s.getMinDistance()" % tof, "%d mm")
    return out





def _ind(lines, n):
    return [(" " * n + ln) if ln else "" for ln in lines]


def code(behaviours, instances, cat=None, ids=None):
    """cat: the Atech SDK catalog in use (atech_firmware.catalog()); ids:
    {CAD module: SDK id}. A module the catalog lacks (the SDK dropped the
    PIR sensor after 1.0.0a11) is left out of the code and listed in
    "unsupported", so the project still builds."""
    instances = dict(instances or {})
    if cat and ids:
        for mod in list(instances):
            sid = ids.get(mod)
            if sid and sid not in (cat.get("modules") or {}):
                instances.pop(mod)
    readings = readings_for(instances)
    setup = ["// written from the brief by Prompt2Product (R1140); edit freely"]
    pre, body, notes, unsupported, rules = [], [], [], [], []
    helpers = set()
    for n, r in enumerate(behaviours or [], 1):
        tr = trigger(r, instances, n)
        ac = action(r, instances, readings)
        if tr is None or ac is None:
            missing = r.get("trigger") if tr is None else r.get("action")
            unsupported.append("when %s, %s (%s)" % (
                r.get("when"), r.get("then"),
                "no %s in the build or no SDK driver" % (missing or "module")
                if missing else "nothing to trigger it"))
            continue
        if tr.get("timer"):
            helpers.add(tr["timer"])
        for ln in tr["pre"]:
            if ln not in pre:
                pre.append(ln)
        if tr.get("note"):
            notes.append("When %s: %s." % (r["when"], tr["note"]))
        head = "// when %s, %s" % (r["when"], r["then"])
        if tr["kind"] == "level" and ac["kind"] == "state" and ac.get("off"):
            # follow the level: on while true, back when it ends (edges only,
            # so the slow screen is not redrawn every loop)
            var = "b%d_on" % n
            body += [head, "{", "  static bool %s = false;" % var,
                     "  bool now = %s;" % tr["cond"],
                     "  if (now && !%s) {" % var] + _ind(ac["on"], 4) + [
                     "  } else if (!now && %s) {" % var] + _ind(ac["off"], 4) + [
                     "  }", "  %s = now;" % var, "}"]
            rules.append({"behaviour": r, "cond": tr["cond"], "kind": "follow"})
        elif tr["kind"] == "level":
            var = "b%d_was" % n
            body += [head, "{", "  static bool %s = false;" % var,
                     "  bool now = %s;" % tr["cond"],
                     "  if (now && !%s) {" % var] + _ind(ac["on"], 4) + [
                     "  }", "  %s = now;" % var, "}"]
            rules.append({"behaviour": r, "cond": tr["cond"], "kind": "rising"})
        else:
            body += [head, "if (%s) {" % tr["cond"]] + _ind(ac["on"], 2) + ["}"]
            if tr.get("off") and ac.get("off"):
                body += ["if (%s) {" % tr["off"]] + _ind(ac["off"], 2) + ["}"]
            rules.append({"behaviour": r, "cond": tr["cond"], "kind": "edge"})
    loop = []
    if pre:
        loop += ["// these modules want update() before their checks (Atech SDK)"] + pre + [""]
    loop += body or ["// runs forever - never block, use millis()"]
    if helpers:
        # project.yaml's code: holds setup and loop only, so the timers'
        # state lives in statics at the top of loop
        loop = (["// timers (never block: millis())"]
                + ["static unsigned long %s = millis();" % t for t in sorted(helpers)]
                + ["auto _p2p_due = [](unsigned long &last, unsigned long ms) {",
                   "  unsigned long now = millis();",
                   "  if (now - last >= ms) { last = now; return true; }",
                   "  return false;", "};", ""] + loop)
    return {"setup": "\n".join(setup), "loop": "\n".join(loop), "notes": notes,
            "unsupported": unsupported, "rules": rules}


def ids_from(entries):
    return {e["cad"]: e["id"] for e in entries or [] if e.get("id") and e.get("cad")}


def instances_from(entries):
    """{CAD module: instance} from atech_firmware.plan() entries (the
    first of each kind: btn, not btn2)."""
    out = {}
    for e in entries or []:
        if e.get("id") and e.get("cad") and e["cad"] not in out:
            out[e["cad"]] = e["instance"]
    return out


def project(name, entries, behaviours, board=atech_firmware.BOARD, cat=None):
    """(project.yaml text, the code() dict)."""
    c = code(behaviours, instances_from(entries), cat, ids_from(entries))
    return atech_firmware.project_yaml(name, entries, c["setup"], c["loop"], board), c
