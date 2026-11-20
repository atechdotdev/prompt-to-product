"""p2p_manual - the papers that come with the product (R1150).

A product is not done when it prints: the person who gets it needs to know
what it does and how to look after it. From the brief and the build:

    manual_md(brief, facts)     the user manual (for the person who uses it,
                                not the maker): what it does, getting
                                started, using it, care, safety,
                                troubleshooting, specifications
    card_html(brief, facts)     a one-page quick-start card (A6, prints)
    label_svg(brief, facts)     the product label (name, size, power, made by)

facts = {"whole_mm": [x, y, z], "grams": g, "modules": ["button", ...],
         "part_count": n,
         "power_ma": 460 | None, "material": "PLA", "version": "1.0",
         "maker": "Atech.dev"}

Only what is known goes in. The label says "Prototype: not certified" -
nothing here claims a CE/FCC/UKCA mark. Python 3.9+, stdlib only.
"""
import html
import re

import p2p_brief

#: per module: (how to use it, what the person may notice, a fix)
MODULE_NOTES = {
    "button": ("Press the button.", None, None),
    "knob": ("Turn the knob; press it to click.", None, None),
    "light": ("The light is the 3x3 grid on the front.",
              "The light is not very bright.",
              "That is on purpose: its brightness is capped at 20 % so it is easy on the eyes."),
    "screen": ("The small screen shows what the product is doing.",
               "The screen takes a moment to change.",
               "It redraws about 4 times a second at most; that is normal."),
    "speaker": ("Sounds come from the speaker grille.",
                "No sound.", "Check the volume in the firmware, and that nothing covers the grille."),
    "microphone": ("It listens through the small hole in the case.",
                   "It does not react to sound.", "Keep the microphone hole clear."),
    "temp_humidity": ("It measures the temperature and humidity of the air around it.",
                      "The temperature reads a little high.",
                      "The board warms the case slightly; give it a few minutes, and keep "
                      "it out of the sun."),
    "scd40_air_quality": ("It measures CO2 in the room.",
                          "The CO2 reads 0 right after switching on.",
                          "The sensor needs about 5 seconds for its first reading."),
    "distance_sensor": ("It sees how far things are in front of it.",
                        "It does not notice something close.",
                        "Keep the sensor window clean and uncovered."),
    "pir": ("It notices when someone moves nearby.",
            "It does not react for the first half minute.",
            "The motion sensor settles for about 30 seconds after power-on."),
    "orientation": ("It knows when it is tilted, turned over or shaken.", None, None),
    "dc_motor": ("It has a motor.", "The motor does not turn.",
                 "Check that nothing blocks the wheel or shaft."),
    "stepper_motor": ("It has a stepper motor (needs the 12-24 V supply).",
                      "The motor hums but does not move.",
                      "Use the power supply that came with it: USB alone can't drive it."),
    "soil_sensor": ("Push the soil sensor's probe into the soil.", None, None),
    "load_cell": ("Put things on top to weigh them.", None, None),
    "camera": ("The camera looks out through the lens window.", None, None),
}


def _cap(s):
    s = (s or "").strip()
    return s[:1].upper() + s[1:] if s else s


def _behaviour_line(r):
    """'when the button is pressed' + 'plays a tune' -> 'Press the button:
    it plays a tune.'"""
    w = (r.get("when") or "").strip()
    t = (r.get("then") or "").strip().rstrip(".")
    trig = r.get("trigger")
    lead = {"button": "Press the button", "knob": "Turn the knob",
            "pir": "Walk past it", "orientation": "Shake or tilt it" if "shak" not in w
            else "Shake it", "microphone": "Clap or make a sound"}.get(trig)
    if not lead or (trig == "button" and not re.search(r"press|click|tap", w)):
        lead = "When %s" % w
    subj = t if t.startswith(("the ", "a ", "it ")) else "it " + t
    return "%s: %s." % (lead, subj)


def _size_text(mm):
    if not mm:
        return None
    return " x ".join("%g" % round(v) for v in mm) + " mm"


def manual_md(brief, facts=None):
    f = facts or {}
    b = brief or {}
    title = b.get("title") or "Product"
    mods = [m for m in (f.get("modules") or [x["module"] for x in b.get("modules") or []])
            if m not in ("usbc", "power_jack")]
    electronic = bool(mods)
    L = ["# %s - user manual" % title, ""]
    if b.get("prompt"):
        L += ["_%s_" % _cap(b["prompt"].rstrip(".")) + ".", ""]
    # what it does
    L += ["## What it does", ""]
    if b.get("behaviours"):
        L += ["- " + _behaviour_line(r) for r in b["behaviours"]]
    elif electronic:
        L.append("- It has %s." % ", ".join(p2p_brief.module_label(m) for m in mods))
    else:
        L.append("- It is a printed object: no electronics, nothing to charge.")
    L.append("")
    # getting started
    if electronic:
        L += ["## Getting started", ""]
        if "power_jack" in (f.get("modules") or []) or b.get("power") == "wall":
            L.append("1. Plug the power supply into the power jack.")
        else:
            L.append("1. Plug a USB-C cable into the USB-C port and into a USB charger "
                     "(5 V, at least 1 A) or a power bank.")
        L.append("2. It starts by itself in a few seconds.")
        if "pir" in mods:
            L.append("3. Give the motion sensor about 30 seconds to settle.")
        L.append("")
        L += ["## Using it", ""]
        for m in mods:
            use = MODULE_NOTES.get(m, (None,))[0]
            if use:
                L.append("- " + use)
        L.append("")
    # care
    mat = f.get("material") or "PLA"
    L += ["## Looking after it", ""]
    if "PLA" in mat and "PETG" not in mat:
        L.append("- It is printed in PLA: keep it out of hot cars and direct summer sun "
                 "(PLA softens above about 55 C).")
    else:
        L.append("- It is printed in %s." % mat)
    L.append("- Wipe it with a dry or slightly damp cloth. No solvents.")
    if electronic:
        L.append("- Keep the electronics dry. %s" % (
            "It is not waterproof." if "wet" not in (b.get("places") or [])
            else "The case is splash-proof at best: do not put it under water."))
    L.append("")
    # safety
    places = set(b.get("places") or [])
    L += ["## Safety", ""]
    if "kids" in places:
        L.append("- For children: check now and then that no part has come loose. Small "
                 "parts are a choking hazard for children under 3.")
    elif electronic or int(f.get("part_count") or 1) > 1:
        L.append("- Not a toy for children under 3: it has small parts.")
    if electronic:
        L.append("- Use a good USB charger. Do not leave it plugged in under a blanket or "
                 "in a closed box.")
    if "kitchen" in places:
        L.append("- Printed plastic is not food-safe: do not let it touch food.")
    L.append("- A prototype: it has not been tested for CE, UKCA or FCC.")
    L.append("")
    # troubleshooting
    rows = []
    if electronic:
        rows.append(("Nothing happens.", "Try another USB-C cable and charger: some cables "
                     "only charge. Wait 5 seconds after plugging in."))
    for m in mods:
        n = MODULE_NOTES.get(m)
        if n and n[1]:
            rows.append((n[1], n[2]))
    if rows:
        L += ["## If something is wrong", "", "| What you see | What to do |", "|---|---|"]
        L += ["| %s | %s |" % r for r in rows]
        L.append("")
    # specs
    L += ["## Specifications", ""]
    if _size_text(f.get("whole_mm")):
        L.append("- Size: %s" % _size_text(f["whole_mm"]))
    if f.get("grams"):
        L.append("- Printed parts: about %g g of %s" % (round(f["grams"]), mat))
    if electronic:
        L.append("- Electronics: the Atech board with %s" % ", ".join(
            p2p_brief.module_label(m, False) for m in mods))
        if f.get("power_ma"):
            L.append("- Power: 5 V over USB-C, about %d mA (planning figure)" % f["power_ma"])
    L.append("- Version: %s" % (f.get("version") or "1.0"))
    L += ["", "Made with Prompt2Product by %s." % (f.get("maker") or "Atech.dev"), ""]
    return "\n".join(L)


CARD = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s quick start</title>
<style>
:root{--bg:#fff;--fg:#1c1c1e;--mu:#6b6b73;--ln:#e3e3e8;--ac:#1f6f43}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#141416;--fg:#f2f2f4;--mu:#a0a0a8;--ln:#333338}}
:root[data-theme="dark"]{--bg:#141416;--fg:#f2f2f4;--mu:#a0a0a8;--ln:#333338}
@page{size:A6;margin:8mm}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:13px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
main{max-width:420px;margin:0 auto;padding:16px}
h1{font-size:20px;margin:0 0 2px}.mu{color:var(--mu);font-size:11px}
h2{font-size:13px;margin:14px 0 4px;color:var(--ac);text-transform:uppercase;letter-spacing:.04em}
ol,ul{margin:0;padding-left:18px}li{margin:2px 0}
footer{margin-top:14px;padding-top:8px;border-top:1px solid var(--ln);color:var(--mu);font-size:11px}
</style></head><body><main>
<h1>%(title)s</h1><div class="mu">Quick start</div>
%(start)s
<h2>What it does</h2><ul>%(does)s</ul>
<h2>Look after it</h2><ul>%(care)s</ul>
<footer>Made with Prompt2Product by %(maker)s &middot; v%(version)s &middot; prototype, not certified</footer>
</main></body></html>
"""


def _section(md, heading):
    out, on = [], False
    for ln in md.splitlines():
        if ln.startswith("## "):
            on = ln[3:].strip() == heading
            continue
        if on and ln.strip():
            out.append(ln.strip())
    return out


def card_html(brief, facts=None):
    f = facts or {}
    md = manual_md(brief, f)
    esc = html.escape

    def items(lines):
        return "".join("<li>%s</li>" % esc(ln.lstrip("-0123456789. ").strip())
                       for ln in lines if not ln.startswith("|"))
    start = _section(md, "Getting started")
    return CARD % {
        "title": esc((brief or {}).get("title") or "Product"),
        "start": ("<h2>Start</h2><ol>%s</ol>" % items(start)) if start else "",
        "does": items(_section(md, "What it does")),
        "care": items(_section(md, "Looking after it")[:2]),
        "maker": esc(f.get("maker") or "Atech.dev"), "version": esc(f.get("version") or "1.0")}


def label_svg(brief, facts=None):
    """An 80 x 40 mm label (SVG in mm units): name, size, power, maker."""
    f = facts or {}
    esc = html.escape
    title = esc(((brief or {}).get("title") or "Product")[:28])
    lines = []
    if _size_text(f.get("whole_mm")):
        lines.append("Size " + _size_text(f["whole_mm"]))
    mods = [m for m in f.get("modules") or [] if m not in ("usbc", "power_jack")]
    if mods:
        lines.append("5 V USB-C" + (", about %d mA" % f["power_ma"] if f.get("power_ma") else ""))
    lines.append("v%s - prototype, not certified" % (f.get("version") or "1.0"))
    lines.append("Made with Prompt2Product by %s" % (f.get("maker") or "Atech.dev"))
    text = "".join('<text x="4" y="%.1f" font-size="3.2">%s</text>' % (17 + i * 5.2, esc(t))
                   for i, t in enumerate(lines))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="80mm" height="40mm" '
            'viewBox="0 0 80 40" font-family="Helvetica, Arial, sans-serif">'
            '<rect x="0.5" y="0.5" width="79" height="39" rx="3" fill="#fff" stroke="#1c1c1e" '
            'stroke-width="0.6"/>'
            '<text x="4" y="10" font-size="6" font-weight="700" fill="#1c1c1e">%s</text>'
            '<g fill="#1c1c1e">%s</g></svg>' % (title, text))
