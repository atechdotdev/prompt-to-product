"""p2p_brief - a prompt becomes a product brief (R1100).

Prompt2Product starts from a sentence ("a desk buddy with a button that
plays a sound and a light that glows red when it's hot"). Before the agent
designs anything, this module reads that sentence into a brief: what the
product is, which Atech modules it needs and why, how big it may be, how it
is powered, where it lives, what it should DO, and the questions still
open. Every later step checks itself against the brief (p2p_accept.py):
the brief's acceptance criteria are the product's definition of done.

    brief(prompt)              the brief dict (below)
    markdown(b)                the brief for a person
    agent_text(b)              the BRIEF paragraph the agent reads
    save(b, folder) / load(folder)   <folder>/brief.json

Plain words only, no model call: the brief is a reading of what the user
wrote, never a guess dressed up as a fact. A thing the prompt does not say
is a question, not a default. Python 3.9+, stdlib only.

b = {
  "prompt": "...", "title": "Desk buddy", "kind": "gadget",
  "modules": [{"module": "button", "count": 1, "why": "button"}],
  "without": ["screen"],                 # "no screen", "without a screen"
  "size": {"max_mm": [120, 80, 60] | None, "words": "120 x 80 x 60 mm",
           "class": "pocket" | None},
  "power": "usb" | "battery" | "wall" | None,
  "places": ["desk", "outdoor", ...],
  "behaviours": [{"when": "button pressed", "then": "plays a sound",
                  "trigger": "button", "action": "speaker"}],
  "colours": ["red"], "quantity": 1, "print_only": False,
  "questions": ["How is it powered: USB-C, a power bank or a battery?"],
  "acceptance": [{"id": "module:button", "kind": "module", ...}],
}
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BRIEF_FILE = "brief.json"
VERSION = 1

#: CAD module (models/presets.yaml) -> words in a prompt that ask for it.
#: Longest phrases first within a module; whole words only.
MODULE_WORDS = {
    "button": ["push button", "push-button", "buttons", "button", "press it", "clicker",
               "click"],
    "light": ["neopixel", "rgb light", "status light", "night light", "lights", "light",
              "leds", "led", "glows", "glow", "lamp", "lights up", "blink", "blinks",
              "flash colour", "colour changing", "color changing"],
    "screen": ["display", "screens", "screen", "shows the", "show the", "shows text",
               "readout"],
    "speaker": ["speaker", "sound", "sounds", "beep", "beeps", "buzzer", "alarm",
                "melody", "music", "tune", "chime", "plays a", "play a"],
    "microphone": ["microphone", "mic", "listens", "listen", "clap", "noise level",
                   "voice"],
    "temp_humidity": ["temperature", "humidity", "thermometer", "hygrometer", "weather",
                      "how hot", "how warm", "too hot", "too cold"],
    "scd40_air_quality": ["co2", "co₂", "air quality", "carbon dioxide", "stuffy"],
    "distance_sensor": ["distance", "proximity", "how far", "range finder",
                        "rangefinder", "tof"],
    "pir": ["motion sensor", "motion", "movement", "someone walks", "presence",
            "walks by", "walks past", "pir"],
    "orientation": ["tilt", "tilted", "shake", "shaken", "orientation", "imu",
                    "accelerometer", "gyro", "flip", "flipped", "upside down"],
    "knob": ["knob", "dial", "rotary", "turn to", "volume control"],
    "dc_motor": ["dc motor", "wheels", "wheel", "drives", "drive", "spins", "spin",
                 "fan", "motor"],
    "stepper_motor": ["stepper", "precise rotation", "turntable", "linear axis"],
    "soil_sensor": ["soil", "plant needs water", "moisture", "watering"],
    "load_cell": ["weigh", "weighs", "weight", "load cell", "kitchen scale"],
    "camera": ["camera", "photo", "photos", "picture of", "webcam"],
    "big_screen": ["big screen", "large screen", "large display", "big display"],
    "robot_arm": ["robot arm", "robotic arm", "so-101", "so101"],
}
#: Words that would match a module but mean something else here.
FALSE_FRIENDS = {
    "light": ["lightweight", "light weight", "light-weight", "light grey", "light gray",
              "light blue", "light green", "light pink", "light colour", "light color",
              "light wood"],
    "knob": ["door knob", "doorknob"],
    "motor": [],
    "dc_motor": ["spin top", "fidget spinner"],
    "screen": ["phone screen", "screen protector", "screen cleaner", "monitor stand"],
    "speaker": ["speaker stand", "speaker grill", "speaker mount"],
    "camera": ["camera mount", "camera stand", "camera holder", "gopro mount"],
}
#: Prompts that are clearly a print with no electronics.
PRINT_ONLY_WORDS = ["vase", "holder", "hook", "bracket", "planter", "organiser",
                    "organizer", "coaster", "tray", "stand", "clip", "box", "case",
                    "mount", "toy", "figure", "fidget", "keychain", "bookend", "comb",
                    "spool", "cable clip", "desk tidy"]
#: Words that say the product has electronics even without a named module.
SMART_WORDS = ["smart", "electronic", "gadget", "sensor", "robot", "device",
               "tracker", "monitor", "station", "controller", "remote", "timer",
               "clock", "alarm", "game", "notif", "reminder", "detector"]

NUMBERS = {"a": 1, "an": 1, "one": 1, "single": 1, "two": 2, "pair of": 2, "double": 2,
           "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
           "nine": 9, "ten": 10}

SIZE_CLASSES = {
    # class: (words, max envelope mm x, y, z) - the largest a thing of that
    # kind would be; the brief says it is a reading of a word, not a spec.
    "keychain": (["keychain", "keyring", "key ring", "key chain"], (60, 40, 20)),
    "pocket": (["pocket", "pocket-sized", "pocket sized", "fits in a pocket"],
               (120, 75, 30)),
    "palm": (["palm", "palm-sized", "hand-sized", "hand sized", "fits in my hand",
              "fits in your hand", "handheld", "hand-held"], (110, 90, 60)),
    "small": (["tiny", "small", "compact", "little", "mini"], (120, 120, 100)),
}
PLACES = {
    "desk": ["desk", "desktop", "office", "workbench", "bedside", "nightstand"],
    "wall": ["wall", "wall-mounted", "wall mounted", "on the wall", "hang"],
    "outdoor": ["outdoor", "outdoors", "outside", "garden", "balcony", "weather"],
    "wet": ["waterproof", "water-resistant", "water resistant", "shower", "bathroom",
            "splash"],
    "kids": ["kid", "kids", "child", "children", "toddler", "baby", "classroom"],
    "car": ["in the car", "in my car", "car dashboard", "dashboard", "bike",
            "bicycle", "scooter", "handlebar"],
    "kitchen": ["kitchen", "fridge", "cooking"],
    "wearable": ["wearable", "wrist", "badge", "necklace", "pendant"],
}
POWER = {
    "battery": ["battery-powered", "battery powered", "battery", "batteries", "power bank", "powerbank", "rechargeable",
                "cordless", "wireless power", "portable"],
    "usb": ["usb-powered", "usb powered", "usb-c powered", "usb", "usb-c", "usbc", "plugged in", "plug in"],
    "wall": ["mains", "wall plug", "power adapter", "12v", "12 v", "24v", "24 v",
             "power supply", "dc jack", "barrel jack"],
}
COLOURS = ["black", "white", "grey", "gray", "red", "orange", "yellow", "green",
           "blue", "purple", "pink", "brown", "silver", "gold", "transparent", "clear",
           "wood"]
KINDS = [
    ("robot", ["robot", "rover", "car", "vehicle"]),
    ("instrument", ["station", "monitor", "meter", "sensor", "detector", "tracker",
                    "thermometer", "logger"]),
    ("toy", ["toy", "game", "pet", "buddy", "companion", "fidget", "kids"]),
    ("clock", ["clock", "timer", "alarm clock", "pomodoro", "countdown"]),
    ("controller", ["controller", "remote", "macro pad", "macropad", "keypad",
                    "dial", "switch"]),
    ("light", ["lamp", "night light", "light"]),
    ("holder", PRINT_ONLY_WORDS),
]
#: action words -> the module that does it (for behaviours).
ACTIONS = [
    ("speaker", ["beep", "beeps", "play", "plays", "sound", "sounds", "chime", "chimes",
                 "alarm", "sing", "sings", "tune", "buzz", "buzzes"]),
    ("light", ["glow", "glows", "light up", "lights up", "turn red", "turns red",
               "turn green", "turns green", "turn blue", "turns blue", "blink", "blinks",
               "flash", "flashes", "colour", "color", "led", "light"]),
    ("screen", ["show", "shows", "display", "displays", "screen", "print", "prints",
                "write", "writes"]),
    ("dc_motor", ["spin", "spins", "drive", "drives", "move", "moves", "motor",
                  "wheel", "wheels", "stop", "stops", "reverse", "reverses", "turn away",
                  "turns away", "back up", "backs up"]),
    ("stepper_motor", ["rotate", "rotates", "turn by", "step", "steps"]),
]
TRIGGERS = [
    ("button", ["button", "press", "pressed", "click", "clicked", "tap", "tapped"]),
    ("knob", ["knob", "dial", "turn the", "turned"]),
    ("pir", ["motion", "someone walks", "walks by", "walks past", "movement",
             "somebody", "someone comes", "someone enters", "presence"]),
    ("temp_humidity", ["hot", "cold", "warm", "temperature", "humid", "humidity"]),
    ("scd40_air_quality", ["co2", "stuffy", "air quality", "air is bad"]),
    ("distance_sensor", ["close", "near", "closer", "distance", "approach"]),
    ("orientation", ["shake", "shaken", "tilt", "tilted", "flip", "flipped",
                     "upside down", "picked up"]),
    ("microphone", ["clap", "loud", "noise", "sound level", "hears"]),
    ("soil_sensor", ["soil", "dry", "thirsty", "needs water"]),
    ("load_cell", ["weight", "weighs", "heavier", "lighter"]),
    ("timer", ["every", "each hour", "each minute", "after", "minutes", "seconds",
               "o'clock", "timer", "countdown"]),
]


# ------------------------------------------------------------------ words
def _norm(prompt):
    t = (prompt or "").replace("’", "'").replace("×", "x")
    return re.sub(r"\s+", " ", t).strip()


def _has(text, phrase):
    return re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(phrase), text) is not None


def _find(text, phrases):
    """The first phrase (in list order) found in text as whole words, or None."""
    for p in phrases:
        if _has(text, p):
            return p
    return None


def _scrub(low, module):
    """low with the false friends of a module blanked out."""
    for ff in FALSE_FRIENDS.get(module, []):
        low = re.sub(r"(?<![\w-])%s(?![\w-])" % re.escape(ff), " ", low)
    return low


def _count_before(low, word):
    """'two buttons' -> 2, '3 lights' -> 3, else 1."""
    m = re.search(r"(\d+|%s)\s+(?:\w+\s+)?%s" % (
        "|".join(re.escape(k) for k in sorted(NUMBERS, key=len, reverse=True)),
        re.escape(word)), low)
    if not m:
        return 1
    g = m.group(1)
    n = int(g) if g.isdigit() else NUMBERS.get(g, 1)
    return max(1, min(n, 8))


def _negated(low, word):
    return re.search(r"(?:\bno|\bwithout(?: an?| any)?|\bnot? (?:need|want)(?: an?| any)?|"
                     r"\bdon't (?:need|want)(?: an?| any)?)\s+(?:\w+\s+)?%s\b"
                     % re.escape(word), low) is not None


# ------------------------------------------------------------------ parts
def modules(prompt):
    """([{"module", "count", "why"}], [modules the prompt rules out])."""
    low = _norm(prompt).lower()
    out, without = [], []
    for mod, words in MODULE_WORDS.items():
        text = _scrub(low, mod)
        if mod == "screen":
            text = _scrub(text, "big_screen") if _find(text, MODULE_WORDS["big_screen"]) \
                else text
            for p in MODULE_WORDS["big_screen"]:
                text = text.replace(p, " ")
        w = _find(text, words)
        if not w:
            continue
        if _negated(text, w):
            without.append(mod)
            continue
        out.append({"module": mod, "count": _count_before(text, w), "why": w})
    # A stepper prompt is not also a DC motor because it says "motor".
    names = {m["module"] for m in out}
    if "stepper_motor" in names and "dc_motor" in names and \
            _find(low, ["dc motor", "wheel", "wheels", "fan"]) is None:
        out = [m for m in out if m["module"] != "dc_motor"]
    if "robot_arm" in names:
        out = [m for m in out if m["module"] not in ("dc_motor", "stepper_motor")]
    return out, without


def size(prompt):
    """{"max_mm": [x, y, z] | None, "words", "class"}."""
    t = _norm(prompt).lower()
    unit = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4, "inch": 25.4,
            "inches": 25.4, '"': 25.4}
    num = r"(\d+(?:[.,]\d+)?)"
    u = r"\s*(mm|cm|inches|inch|in|m|\")?"
    m = re.search(num + u + r"\s*(?:x|by)\s*" + num + u + r"\s*(?:x|by)\s*" + num + u, t)
    if m:
        g = m.groups()
        last = g[5] or g[3] or g[1] or "mm"
        dims = []
        for v, un in ((g[0], g[1]), (g[2], g[3]), (g[4], g[5])):
            dims.append(round(float(v.replace(",", ".")) * unit[un or last], 1))
        return {"max_mm": dims, "words": m.group(0).strip(), "class": None}
    m = re.search(num + u + r"\s*(?:x|by)\s*" + num + u + r"(?!\s*(?:x|by))", t)
    if m:
        g = m.groups()
        last = g[3] or g[1] or "mm"
        a = round(float(g[0].replace(",", ".")) * unit[g[1] or last], 1)
        b2 = round(float(g[2].replace(",", ".")) * unit[g[3] or last], 1)
        return {"max_mm": [a, b2, None], "words": m.group(0).strip(), "class": None}
    m = re.search(r"(?:under|less than|at most|max(?:imum)?|no (?:bigger|larger) than|"
                  r"within|fits? in)\s+(?:a\s+)?" + num + r"\s*(mm|cm|in|inch|inches|m)\b", t)
    if m:
        v = round(float(m.group(1).replace(",", ".")) * unit[m.group(2)], 1)
        return {"max_mm": [v, v, v], "words": m.group(0).strip(), "class": None}
    m = re.search(num + r"\s*(mm|cm|in|inch|inches)\s+(tall|high|wide|long|deep|across|"
                  r"diameter)", t)
    if m:
        v = round(float(m.group(1).replace(",", ".")) * unit[m.group(2)], 1)
        axis = {"tall": 2, "high": 2, "wide": 0, "across": 0, "diameter": 0,
                "long": 1, "deep": 1}[m.group(3)]
        dims = [None, None, None]
        dims[axis] = v
        if m.group(3) in ("diameter", "across"):
            dims[1] = v
        return {"max_mm": dims, "words": m.group(0).strip(), "class": None}
    for cls, (words, env) in SIZE_CLASSES.items():
        w = _find(t, words)
        if w:
            return {"max_mm": list(env), "words": w, "class": cls}
    return {"max_mm": None, "words": "", "class": None}


def power(prompt, mods):
    low = _norm(prompt).lower()
    for p in ("battery", "wall", "usb"):
        if _find(low, POWER[p]):
            return p
    if any(m["module"] == "stepper_motor" for m in mods):
        return "wall"                       # the SDK: the stepper needs 12-24 V
    return None


def places(prompt):
    low = _norm(prompt).lower()
    return [k for k, words in PLACES.items() if _find(low, words)]


def colours(prompt):
    """Colours the print should be. A colour a light shows ('glows red',
    'turns green') is the firmware's, not the filament's."""
    low = _scrub(_norm(prompt).lower(), "light")
    low = re.sub(r"\b(?:glows?|glowing|turns?|turning|flash(?:es)?|blinks?|shines?|lights? up|"
                 r"goes|go|show(?:s)?|in)\s+(?:a\s+)?(?:bright\s+|soft\s+)?(%s)\b"
                 % "|".join(COLOURS), lambda m: " " if not m.group(0).startswith("in") else
                 m.group(0), low)
    found = []
    for c in COLOURS:
        m = re.search(r"(?<![\w-])%s(?![\w-])" % c, low)
        if m:
            found.append((m.start(), "grey" if c == "gray" else c))
    return list(dict.fromkeys(c for _i, c in sorted(found)))


def quantity(prompt):
    low = _norm(prompt).lower()
    m = re.search(r"(?:make|print|build|need|order|batch of|set of)\s+(\d+|%s)\s+"
                  r"(?:of (?:them|these)|copies|units|pieces|pcs|sets)?"
                  % "|".join(k for k in NUMBERS if k not in ("a", "an", "single")), low)
    if m and (m.group(1).isdigit() or m.group(1) in NUMBERS):
        n = int(m.group(1)) if m.group(1).isdigit() else NUMBERS[m.group(1)]
        # "make 3 buttons" is a module count, not a batch.
        tail = low[m.end():m.end() + 30]
        if any(_has(tail.split(".")[0], w) for ws in MODULE_WORDS.values() for w in ws[:3]):
            return 1
        return max(1, min(n, 10000))
    return 1


def kind(prompt, mods):
    low = _norm(prompt).lower()
    for k, words in KINDS:
        if _find(low, words):
            return k
    return "gadget" if mods else "print"


def title(prompt):
    """A short product name from the prompt: 'a desk buddy that ...' -> 'Desk buddy'."""
    t = _norm(prompt)
    t = re.sub(r"(?i)^(please\s+)?(can you\s+)?(make|design|build|create|i want|i need|"
               r"give me|draw|model)\s+(me\s+)?", "", t)
    t = re.sub(r"(?i)^(a|an|the|some)\s+", "", t)
    t = re.split(r"(?i)\s+(?:that|which|with|for|to|so|where|when|who|in|on|made)\b|[,.;:!?(]",
                 t, 1)[0]
    if re.match(r"(?i)(when|whenever|if|once|pressing)\b", t):
        return "Product"
    words = t.split()[:5]
    s = " ".join(words).strip(" -")
    return (s[:1].upper() + s[1:]) if s else "Product"


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?;])\s+|\s*\n\s*", text) if s.strip()]


def _clauses(sentence):
    """A sentence cut where a new 'thing that does' starts: ', and a light
    that ...', '; it ...'. Each clause holds at most one behaviour."""
    parts = re.split(r"(?i),\s*(?:and\s+)?(?=(?:a|an|the|it|when|whenever|if|once)\b)|"
                     r"\s+and\s+(?=(?:a|an|the)\s+\w+(?:\s+\w+)?\s+(?:that|which)\b)|"
                     r"\s+and\s+(?=(?:when|whenever|if)\b)", sentence)
    parts = [p.strip() for p in parts if p and p.strip()]
    out = []
    cond = re.compile(r"(?i)^(?:and\s+)?(?:when|whenever|if|once)\b")
    for p in parts:
        # "When X, it Y": the condition and its result are one clause.
        if out and cond.match(out[-1]) and "," not in out[-1] and not cond.match(p) \
                and not re.search(r"(?i)\bthen\b", out[-1]):
            out[-1] = out[-1] + ", " + p
        else:
            out.append(p)
    return out


_TAIL = re.compile(r"(?i)\s*(?:,|\band\b)?\s*(?:no|without)\s+\w+.*$")
_ON_WORDS = ["turn on", "turns on", "switch on", "switches on", "come on", "comes on",
             "wake up", "wakes up", "react", "reacts", "respond", "responds"]
_OUTPUTS = ["light", "speaker", "screen", "dc_motor", "stepper_motor"]


def _clean(t):
    return _TAIL.sub("", (t or "").strip(" ,.;:")).strip(" ,.;:")


def _rule(when, then, mods_hint):
    when, then = _clean(when), _clean(then)
    if not when or not then:
        return None
    trig = None
    for mod, words in TRIGGERS:
        if _find(when, words):
            trig = mod
            break
    act = None
    for mod, words in ACTIONS:
        if _find(then, words):
            act = mod
            break
    if act is None and _find(then, _ON_WORDS):
        act = next((m for m in _OUTPUTS if m in mods_hint), None)
    if trig is None and act is None:
        return None
    return {"when": when, "then": then, "trigger": trig, "action": act}


def behaviours(prompt, mods_hint=()):
    """'when X, Y' / 'Y when X' / 'if X then Y' / 'a button that Y' /
    'pressing the button makes it Y' -> [{"when", "then", "trigger",
    "action"}]. mods_hint: the modules the prompt names (for 'turns on')."""
    out = []
    hint = set(mods_hint)
    for s in _sentences(_norm(prompt)):
        for part in _clauses(s):
            low = part.lower().rstrip(".!?;")
            r = None
            m = re.match(r"(?:and\s+)?(?:when|whenever|if|once)\s+(.+?)"
                         r"(?:,\s*|\s+then\s+|\s+(?=it\s))(?:it\s+)?(.+)", low)
            if m:
                r = _rule(m.group(1), m.group(2), hint)
            if r is None and "," not in low:
                # "if it gets too cold the light turns blue"
                m = re.match(r"(?:and\s+)?(?:when|whenever|if|once)\s+(.+?)\s+"
                             r"((?:the|a|an|its)\s+\w+.*)", low)
                if m:
                    r = _rule(m.group(1), m.group(2), hint)
            if r is None:
                m = re.search(r"(?:\b(?:that|which|it)\s+)?(\b\w.+?)\s+"
                              r"(?:when|whenever|if|once)\s+(.+)", low)
                if m:
                    then = re.split(r"\b(?:that|which)\s+", m.group(1))[-1]
                    r = _rule(m.group(2), then, hint)
            if r is None:
                # "every 10 minutes it beeps" / "it beeps every hour"
                m = re.search(r"\b(every\s+(?:\d+\s+)?(?:second|minute|hour)s?),?\s+"
                              r"(?:it\s+)?(.+)", low) or None
                if m:
                    r = _rule(m.group(1), m.group(2), hint)
                else:
                    m = re.search(r"(?:\bit\s+)?(\b\w.+?)\s+(every\s+(?:\d+\s+)?"
                                  r"(?:second|minute|hour)s?)\b", low)
                    if m:
                        r = _rule(m.group(2), re.split(r"\b(?:that|which)\s+",
                                                       m.group(1))[-1], hint)
            if r is None:
                m = re.search(r"\b(press(?:ing)? (?:the |a )?button|shaking it|tilting it|"
                              r"turning the knob|clapping)\s+(?:makes it|will|to|makes)\s+(.+)",
                              low)
                if m:
                    r = _rule(m.group(1), m.group(2), hint)
            if r is None:
                m = re.search(r"\b(button|knob|dial|motion sensor|sensor)s?\s+(?:that|which|to)\s+"
                              r"(.+)", low)
                if m:
                    r = _rule(m.group(1) + " pressed" if m.group(1) == "button"
                              else m.group(1), m.group(2), hint)
            if r is not None:
                # quoted words keep the user's case ('shows "Hi there"')
                for q in re.findall(r"[\"\u201c']([^\"\u201d']+)[\"\u201d']", r["then"]):
                    m = re.search(re.escape(q), part, re.I)
                    if m:
                        r["then"] = r["then"].replace(q, m.group(0))
                out.append(r)
    return out


# ------------------------------------------------------------------ brief
QUESTION_POWER = "How is it powered: USB-C from a charger, a power bank inside, or a wall supply?"
QUESTION_SIZE = "How big may it be? A size in mm (e.g. 120 x 80 x 60) or a word (pocket, palm, desk)."
QUESTION_MODULES = ("Does it need electronics? Name what it should sense or do "
                    "(a button, a light, a sound, a screen, a sensor).")


def brief(prompt):
    """The brief for a prompt (see the module docstring)."""
    text = _norm(prompt)
    low = text.lower()
    mods, without = modules(text)
    rules = behaviours(text, [m["module"] for m in mods])
    names = {m["module"] for m in mods}
    # A behaviour that names a module the list missed adds it (with why).
    for r in rules:
        for mod in (r["trigger"], r["action"]):
            if mod and mod != "timer" and mod not in names and mod not in without \
                    and mod in MODULE_WORDS:
                mods.append({"module": mod, "count": 1, "why": "behaviour: %s" % (
                    r["when"] if mod == r["trigger"] else r["then"])})
                names.add(mod)
    smart = bool(mods) or _find(low, SMART_WORDS) is not None
    print_only = not smart and (_find(low, PRINT_ONLY_WORDS) is not None or not mods)
    if mods and "usbc" not in names:
        # Every Atech product with modules is powered through the board's
        # USB-C module unless a power jack is asked for.
        pw = power(text, mods)
        if pw == "wall" and any(m["module"] == "stepper_motor" for m in mods):
            mods.append({"module": "power_jack", "count": 1,
                         "why": "the stepper needs 12-24 V (Atech SDK)"})
        else:
            mods.append({"module": "usbc", "count": 1, "why": "power and programming"})
    sz = size(text)
    pw = power(text, mods) if not print_only else None
    b = {
        "version": VERSION, "prompt": text, "title": title(text), "kind": kind(text, mods),
        "modules": mods, "without": without, "size": sz, "power": pw,
        "places": places(text), "behaviours": rules, "colours": colours(text),
        "quantity": quantity(text), "print_only": print_only,
    }
    b["questions"] = questions(b, smart)
    b["acceptance"] = acceptance(b)
    return b


def questions(b, smart=True):
    q = []
    if not b["print_only"] and not [m for m in b["modules"] if m["module"] != "usbc"]:
        q.append(QUESTION_MODULES)
    if b["size"]["max_mm"] is None:
        q.append(QUESTION_SIZE)
    if not b["print_only"] and b["power"] is None:
        q.append(QUESTION_POWER)
    if "wet" in b["places"]:
        q.append("A printed case is splash-proof at best. Is splash-proof enough, or does "
                 "it need a sealed (gasketed) case?")
    if "outdoor" in b["places"]:
        q.append("Outdoors, PLA softens in the sun. Print in PETG or ASA?")
    if "kids" in b["places"]:
        q.append("For children: no small parts that come off, and screws instead of "
                 "snap fits on the case. OK?")
    for r in b["behaviours"]:
        if r["trigger"] in (None,) and r["action"]:
            q.append("What should make it %s?" % r["then"])
        if r["action"] is None and r["trigger"]:
            q.append("When %s, what should it do (a sound, a light, the screen)?" % r["when"])
    mods = [m for m in b["modules"] if m["module"] not in ("usbc", "power_jack")]
    if mods and not b["behaviours"]:
        q.append("What should it do? Say it as 'when ..., it ...' (e.g. 'when the button "
                 "is pressed, it plays a tune').")
    return q


def acceptance(b):
    """The definition of done: [{"id", "kind", "text", ...}] that
    p2p_accept.check() can test against a built design."""
    a = []
    for m in b["modules"]:
        a.append({"id": "module:%s" % m["module"], "kind": "module", "module": m["module"],
                  "min": m["count"],
                  "text": "Has %s" % ("%d x %s" % (m["count"], module_label(m["module"], False))
                                      if m["count"] > 1 else module_label(m["module"]))})
    for w in b["without"]:
        a.append({"id": "without:%s" % w, "kind": "without", "module": w,
                  "text": "Has no %s (the prompt says so)" % module_label(w, False)})
    if b["size"]["max_mm"]:
        dims = b["size"]["max_mm"]
        a.append({"id": "size", "kind": "size", "max_mm": dims,
                  "text": "Fits in %s mm" % " x ".join("any" if d is None else "%g" % d
                                                       for d in dims)})
    if b["print_only"]:
        a.append({"id": "print_only", "kind": "print_only",
                  "text": "Prints with no electronics"})
    a.append({"id": "printable", "kind": "printable",
              "text": "Every printed part fits a Bambu printer's bed"})
    a.append({"id": "checked", "kind": "checked", "text": "Passes ./check"})
    if not b["print_only"] and [m for m in b["modules"] if m["module"] != "usbc"]:
        a.append({"id": "electrical", "kind": "electrical",
                  "text": "No electrical rule errors"})
        if b["behaviours"]:
            a.append({"id": "firmware", "kind": "firmware",
                      "text": "Firmware does what the brief says (%d behaviour%s)"
                      % (len(b["behaviours"]), "" if len(b["behaviours"]) == 1 else "s")})
    if b["colours"]:
        a.append({"id": "colours", "kind": "colours", "colours": b["colours"],
                  "text": "Printed in %s" % " and ".join(b["colours"])})
    return a


LABELS = {
    "button": "a button", "light": "a light (3x3 RGB)", "screen": "a screen",
    "speaker": "a speaker", "microphone": "a microphone",
    "temp_humidity": "a temperature and humidity sensor",
    "scd40_air_quality": "a CO2 sensor", "distance_sensor": "a distance sensor",
    "pir": "a motion sensor", "orientation": "a tilt/shake sensor", "knob": "a knob",
    "dc_motor": "a DC motor", "stepper_motor": "a stepper motor",
    "soil_sensor": "a soil sensor", "load_cell": "a load cell", "camera": "a camera",
    "big_screen": "a big screen", "robot_arm": "a robot arm",
    "usbc": "the USB-C module", "power_jack": "a power jack",
}


def module_label(mod, article=True):
    t = LABELS.get(mod, mod.replace("_", " "))
    return t if article else re.sub(r"^(a|an|the)\s+", "", t)


REMOVE_RE = re.compile(r"(?i)\b(?:remove|drop|delete|take out|take away|get rid of|lose|"
                       r"no more|without)\s+(?:the\s+|a\s+|an\s+|its\s+)?(\w+(?:\s\w+)?)")
ADD_RE = re.compile(r"(?i)\b(?:add|put|include|give it|with|also)\b")


def update(b, request):
    """The brief after a follow-up message ("add a speaker", "no screen
    after all", "make it 150 mm wide", "in blue"). Only what the message
    says changes; everything else stays. Returns a new dict with
    "changes": [words] (empty when the message changes nothing in the
    brief, e.g. "make the walls thicker")."""
    import copy
    nb = copy.deepcopy(b)
    text = _norm(request)
    low = text.lower()
    changes = []
    # removals first: "remove the screen" / "no screen after all"
    gone = set()
    for m in REMOVE_RE.finditer(low):
        for mod, words in MODULE_WORDS.items():
            if _find(m.group(1), words) or m.group(1).startswith(mod.replace("_", " ")):
                gone.add(mod)
    _mods, neg = modules(text)
    gone |= set(neg)
    for mod in sorted(gone):
        if any(x["module"] == mod for x in nb["modules"]):
            nb["modules"] = [x for x in nb["modules"] if x["module"] != mod]
            changes.append("removed %s" % module_label(mod, False))
            dropped = [r for r in nb["behaviours"] if mod in (r["trigger"], r["action"])]
            nb["behaviours"] = [r for r in nb["behaviours"] if r not in dropped]
            changes += ["dropped: when %s, %s" % (r["when"], r["then"]) for r in dropped]
        elif mod not in nb["without"]:
            changes.append("no %s" % module_label(mod, False))
        if mod not in nb["without"]:
            nb["without"].append(mod)
    have = {x["module"] for x in nb["modules"]}
    for x in _mods:
        if x["module"] in gone:
            continue
        if x["module"] not in have:
            nb["modules"].append(x)
            changes.append("added %s" % module_label(x["module"], False))
            if x["module"] in nb["without"]:
                nb["without"].remove(x["module"])
        else:
            for y in nb["modules"]:
                if y["module"] == x["module"] and x["count"] > 1 and x["count"] != y["count"]:
                    y["count"] = x["count"]
                    changes.append("%d x %s" % (x["count"], module_label(x["module"], False)))
    if [x for x in nb["modules"] if x["module"] not in ("usbc", "power_jack")]:
        if nb.get("print_only"):
            nb["print_only"] = False
            changes.append("now has electronics")
        if not any(x["module"] in ("usbc", "power_jack") for x in nb["modules"]):
            nb["modules"].append({"module": "usbc", "count": 1, "why": "power and programming"})
    sz = size(text)
    if sz["max_mm"]:
        old = nb["size"].get("max_mm") or [None, None, None]
        new = [n if n is not None else (o if sz["max_mm"].count(None) else None)
               for n, o in zip(sz["max_mm"], old)]
        if sz["max_mm"].count(None) == 2:
            new = [n if n is not None else o for n, o in zip(sz["max_mm"], old)]
        nb["size"] = {"max_mm": new, "words": sz["words"], "class": sz["class"]}
        changes.append("size %s" % sz["words"])
    pw = power(text, [])
    if pw and pw != nb.get("power"):
        nb["power"] = pw
        changes.append("power: %s" % pw)
    cs = colours(text)
    if cs and cs != nb.get("colours"):
        nb["colours"] = cs
        changes.append("colours: %s" % ", ".join(cs))
    for pl in places(text):
        if pl not in nb["places"]:
            nb["places"].append(pl)
            changes.append("lives: %s" % pl)
    rules = behaviours(text, [x["module"] for x in nb["modules"]])
    for r in rules:
        if r not in nb["behaviours"]:
            nb["behaviours"].append(r)
            changes.append("does: when %s, %s" % (r["when"], r["then"]))
    q = quantity(text)
    if q > 1 and q != nb.get("quantity"):
        nb["quantity"] = q
        changes.append("%d copies" % q)
    nb["questions"] = questions(nb)
    nb["acceptance"] = acceptance(nb)
    nb.setdefault("history", []).append({"request": text, "changes": changes})
    nb["changes"] = changes
    return nb


# ------------------------------------------------------------------ text
def markdown(b):
    L = ["# Brief: %s" % b["title"], "", "> %s" % b["prompt"], ""]
    L += ["- **Kind:** %s" % b["kind"],
          "- **Electronics:** %s" % ("none, a print" if b["print_only"] else
                                     ", ".join("%s (%s)" % (module_label(m["module"]), m["why"])
                                               for m in b["modules"]) or "not said"),
          "- **Size:** %s" % (b["size"]["words"] or "not said"),
          "- **Power:** %s" % (b["power"] or ("none" if b["print_only"] else "not said")),
          "- **Where:** %s" % (", ".join(b["places"]) or "not said"),
          "- **Colours:** %s" % (", ".join(b["colours"]) or "not said"),
          "- **How many:** %d" % b["quantity"]]
    if b["without"]:
        L.append("- **Without:** %s" % ", ".join(module_label(w) for w in b["without"]))
    if b["behaviours"]:
        L += ["", "## What it does", ""]
        L += ["- When %s, it %s." % (r["when"], r["then"]) for r in b["behaviours"]]
    L += ["", "## Done when", ""] + ["- [ ] %s" % a["text"] for a in b["acceptance"]]
    if b["questions"]:
        L += ["", "## Still open", ""] + ["- %s" % q for q in b["questions"]]
    return "\n".join(L) + "\n"


def agent_text(b):
    """The BRIEF paragraph for the agent's prompt: what was asked, read
    into parts, and what done means. Short; the agent designs, this only
    keeps it on the brief."""
    mods = [m for m in b["modules"]]
    L = ["BRIEF (read from the user's prompt by p2p_brief; follow it, and ask the open "
         "questions only if the answer changes the design):",
         "- Product: %s (%s)." % (b["title"], b["kind"])]
    if b["print_only"]:
        L.append("- A print: no Atech board or modules.")
    elif mods:
        L.append("- Atech modules: %s." % ", ".join(
            "%s%s" % ("%d x " % m["count"] if m["count"] > 1 else "", m["module"])
            for m in mods))
    if b["without"]:
        L.append("- Leave out: %s." % ", ".join(b["without"]))
    if b["size"]["max_mm"]:
        L.append("- Must fit in %s mm (from \"%s\")." % (
            " x ".join("any" if d is None else "%g" % d for d in b["size"]["max_mm"]),
            b["size"]["words"]))
    if b["power"]:
        L.append("- Power: %s." % b["power"])
    if b["places"]:
        L.append("- Lives: %s." % ", ".join(b["places"]))
    for r in b["behaviours"]:
        L.append("- Behaviour: when %s -> %s (write it in project.yaml's code)." % (
            r["when"], r["then"]))
    if b["colours"]:
        L.append("- Colours: %s." % ", ".join(b["colours"]))
    L.append("- Done when: %s." % "; ".join(a["text"] for a in b["acceptance"]))
    return "\n".join(L)


# ------------------------------------------------------------------ files
def save(b, folder):
    os.makedirs(folder, exist_ok=True)
    p = os.path.join(folder, BRIEF_FILE)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(b, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, p)
    return p


def load(folder):
    try:
        with open(os.path.join(folder, BRIEF_FILE), encoding="utf-8") as fh:
            b = json.load(fh)
        return b if isinstance(b, dict) and b.get("prompt") is not None else None
    except (OSError, ValueError):
        return None


def known_modules():
    """The CAD module names in models/presets.yaml (for the tests)."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
    for p in (os.path.join(root, "models", "presets.yaml"),):
        try:
            with open(p, encoding="utf-8") as fh:
                return set(re.findall(r"(?m)^([a-z_0-9]+):\s*$", fh.read()))
        except OSError:
            pass
    return set()


if __name__ == "__main__":
    import sys
    print(markdown(brief(" ".join(sys.argv[1:]) or sys.stdin.read())))
