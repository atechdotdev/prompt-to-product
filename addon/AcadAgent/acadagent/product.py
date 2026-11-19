"""From a passed design to a product in hand (R1003).

Pure Python (no FreeCAD, no Qt): the Make it view and the chat's hand-over
card gather the facts of a design into one dict, and this module turns
them into

    steps(facts)        the 7 steps, each with its state, one line and the
                        action that does it
    assembly(facts)     assembly instructions for a person, from the design
    write_pack(...)     the product pack: one folder with everything needed
                        to make it (and product.html to show it)

facts = {
  "project": "Desk buddy",
  "built": True, "check": "pass" | "fail" | None,
  "levels": {"done": 9, "total": 9} | None,
  "bom": export_tools.bom(doc),          # printed + hardware
  "electrical": atech_electrical.analyse(...),
  "sdk": "/path/to/atech" | None,
  "state": read_state(folder),           # what was done before (times)
  "prints_dir": "~/Documents/Atech Prints/Desk buddy" | None,
}
"""
import datetime
import html
import json
import os
import sys

from .sdk_tools import product_dir, firmware_dir, safe_folder, PROJECT  # noqa: F401

STATE_FILE = "product.json"
PLA_PRICE_PER_KG = None          # no price is invented; the shop quotes

STEPS = (
    ("design", "Design", "box"),
    ("electronics", "Electronics", "cpu"),
    ("firmware", "Firmware", "code"),
    ("parts", "Parts list", "list"),
    ("print", "Print", "printer"),
    ("assemble", "Assemble", "wrench"),
    ("order", "Get it made", "package"),
)
DONE, READY, TODO, WARN, BLOCKED = "done", "ready", "todo", "warn", "blocked"


def kit(name="atech_electrical"):
    """An agent-kit module (the kit is put on sys.path, as wiring_view does)."""
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_kit")
    if d not in sys.path:
        sys.path.append(d)
    return __import__(name)


def now_text():
    return datetime.datetime.now().strftime("%d %b %Y %H:%M")


# ------------------------------------------------------------------ state
def read_state(folder):
    try:
        with open(os.path.join(folder, STATE_FILE), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def mark(folder, key, when=None, **extra):
    """Record that a step happened ("firmware_built", "flashed", "pack",
    "printed", "ordered"). Returns the new state."""
    os.makedirs(folder, exist_ok=True)
    st = read_state(folder)
    st[key] = dict({"when": when or now_text()}, **extra)
    tmp = os.path.join(folder, STATE_FILE + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, os.path.join(folder, STATE_FILE))
    return st


# ------------------------------------------------------------------ steps
def _step(key, state, line, action=None, action_words=None, detail=None):
    title = dict((k, t) for k, t, _i in STEPS)[key]
    icon = dict((k, i) for k, _t, i in STEPS)[key]
    return {"key": key, "title": title, "icon": icon, "state": state, "line": line,
            "action": action, "action_words": action_words, "detail": detail or []}


def steps(f):
    """The 7 steps for facts f, in order."""
    st = f.get("state") or {}
    bom = f.get("bom") or {"printed": [], "hardware": []}
    el = f.get("electrical") or {}
    mods = [m for m in el.get("modules") or []]
    out = []
    # 1 design
    lv = f.get("levels")
    if not f.get("built"):
        out.append(_step("design", TODO, "Describe it in the chat; the agent designs it.",
                         "chat", "Open the chat"))
    elif f.get("check") == "fail":
        out.append(_step("design", WARN, "The last build has problems the agent is fixing.",
                         "chat", "Open the chat"))
    elif lv and lv.get("done", 0) < lv.get("total", 0):
        out.append(_step("design", READY, "Design level %d of %d done."
                         % (lv["done"], lv["total"]), "chat", "Continue in the chat"))
    else:
        n = sum(r["count"] for r in bom["printed"])
        out.append(_step("design", DONE, "Designed and checked: %d printed part%s%s."
                         % (n, "" if n == 1 else "s",
                            ", %d Atech module%s" % (len(mods), "" if len(mods) == 1 else "s")
                            if mods else ""), "view", "Show it"))
    # 2 electronics
    v = el.get("verdict") or {"level": "empty"}
    if v["level"] == "empty":
        out.append(_step("electronics", DONE if f.get("built") else TODO,
                         "No electronics: a print-only product." if f.get("built")
                         else "Comes with the design.", "electrical", "Electrical suite"))
    else:
        state = {"ok": DONE, "warning": WARN, "error": BLOCKED}[v["level"]]
        out.append(_step("electronics", state, v["text"], "electrical", "Electrical suite",
                         [r["text"] for r in el.get("rules") or [] if r["level"] != "note"][:3]))
    # 3 firmware
    fw = el.get("firmware") or {}
    entries = [e for e in fw.get("entries") or [] if e.get("id")]
    if v["level"] == "empty" or not entries:
        out.append(_step("firmware", DONE if f.get("built") else TODO,
                         "Nothing to program." if f.get("built") else "Comes with the electronics.",
                         None))
    elif st.get("flashed"):
        out.append(_step("firmware", DONE, "Flashed to the board on %s." % st["flashed"]["when"],
                         "firmware", "Firmware"))
    elif st.get("firmware_built"):
        out.append(_step("firmware", READY, "Built on %s. Plug in the board and flash it."
                         % st["firmware_built"]["when"], "firmware", "Flash it"))
    elif not f.get("sdk"):
        out.append(_step("firmware", READY, "%d module%s to program. Install the Atech SDK "
                         "to build and flash." % (len(entries), "" if len(entries) == 1 else "s"),
                         "firmware", "Firmware"))
    else:
        out.append(_step("firmware", READY, "%d module%s to program: build it, or run it "
                         "without a board." % (len(entries), "" if len(entries) == 1 else "s"),
                         "firmware", "Build firmware"))
    # 4 parts
    n_print = sum(r["count"] for r in bom["printed"])
    grams = sum(r["mass_g"] * r["count"] for r in bom["printed"])
    hw = bom["hardware"]
    if not f.get("built"):
        out.append(_step("parts", TODO, "Comes with the design.", None))
    else:
        bits = ["%d printed (about %d g of PLA)" % (n_print, round(grams))]
        if hw:
            nm = sum(1 for r in hw if r["kind"] == "Module")
            nc = sum(1 for r in hw if r["kind"] == "Cable")
            bits.append("the Atech board" + (", %d module%s" % (nm, "" if nm == 1 else "s")
                                             if nm else "")
                        + (", %d cable%s" % (nc, "" if nc == 1 else "s") if nc else ""))
        out.append(_step("parts", DONE, "; ".join(bits) + ".", "bom", "Parts list"))
    # 5 print
    if not f.get("built") or not n_print:
        out.append(_step("print", TODO if not f.get("built") else DONE,
                         "Comes with the design." if not f.get("built") else "Nothing to print.",
                         None))
    elif st.get("printed"):
        out.append(_step("print", DONE, ("Sent to the slicer on %s." % st["printed"]["when"])
                         if st["printed"].get("when") else
                         "Sliced before: its plates are in Atech Prints.",
                         "print", "Print again"))
    else:
        out.append(_step("print", READY, "%d part%s, laid flat and sliced for your printer."
                         % (n_print, "" if n_print == 1 else "s"), "print", "Print"))
    # 6 assemble
    if not f.get("built"):
        out.append(_step("assemble", TODO, "Comes with the design.", None))
    else:
        a = assembly(f)
        out.append(_step("assemble", DONE if st.get("pack") else READY,
                         "%d steps, written from the design." % len(a), "assembly",
                         "Assembly steps"))
    # 7 order
    if not f.get("built"):
        out.append(_step("order", TODO, "Comes with the design.", None))
    elif st.get("ordered"):
        out.append(_step("order", DONE, "Sent to Atech on %s." % st["ordered"]["when"],
                         "order", "Get it made"))
    else:
        out.append(_step("order", READY, "Atech prints it and sends the board and modules.",
                         "order", "Get it made"))
    return out


def progress(ss):
    """(done, total) over the steps that apply."""
    return sum(s["state"] == DONE for s in ss), len(ss)


def next_step(ss):
    """The first step that wants the user, or None when all are done."""
    for s in ss:
        if s["state"] in (BLOCKED, WARN, READY) and s["action"]:
            return s
    return None


# ------------------------------------------------------------------ assembly
def _plural(n, word):
    return "%d %s%s" % (n, word, "" if n == 1 else "s")


def assembly(f):
    """[{title, lines}] for a person at a desk, from the design."""
    bom = f.get("bom") or {"printed": [], "hardware": []}
    el = f.get("electrical") or {}
    conns = ((el.get("wiring") or {}).get("connections")) or []
    out = []
    if bom["printed"]:
        lines = []
        for r in bom["printed"]:
            bits = [r["colour"]] if r.get("colour") else []
            bits.append("%g g" % r["mass_g"])
            lines.append("%s%s (%s)" % ("%d x " % r["count"] if r["count"] > 1 else "",
                                        r["part"], ", ".join(bits)))
        out.append({"title": "Print the parts", "lines": lines + [
            "Print them the way the Print step lays them out (flat side down), and let "
            "the slicer decide on supports."]})
    hw = bom.get("hardware") or []
    if hw:
        out.append({"title": "Get the electronics ready", "lines": [
            ("%s on port %s" % (r["name"], r["ports"]) if r["kind"] == "Module" else
             "%s, %g mm, port %s" % (r["name"], r["length_mm"] or 0, r["ports"])
             if r["kind"] == "Cable" else r["name"]) for r in hw]})
    if any(r["kind"] == "Board" for r in hw):
        out.append({"title": "Fit the board", "lines": [
            "Slide the Atech board into its pocket, ports facing up. Where the case has "
            "an opening for USB-C, port 8 goes next to it.",
            "Don't force it: the pocket is made to the board's size with a small clearance."]})
    plugged = [c for c in conns if c["how"] == "plugged in" and c["module"] != "usbc"]
    cabled = [c for c in conns if c["how"] == "cable"]
    usbc = [c for c in conns if c["module"] == "usbc"]
    if usbc:
        out.append({"title": "Power", "lines": [
            "Push the USB-C module onto port %s."
            % "+".join(map(str, usbc[0]["ports"]))]})
    if plugged:
        out.append({"title": "Plug in the modules", "lines": [
            "%s onto port%s %s." % (c["name"], "s" if len(c["ports"]) > 1 else "",
                                    " and ".join(map(str, c["ports"]))) for c in plugged]
            + ["Each module goes straight down until its header sits on the port."]})
    if cabled:
        lines = []
        for c in cabled:
            for q in c.get("cables") or []:
                lines.append("%s: ribbon to port %d%s." % (
                    c["name"], q["port"], (", %d mm" % q["mm"]) if q.get("mm") else ""))
        out.append({"title": "Connect the cabled modules", "lines": lines + [
            "Fit each module in its place in the case first, then plug its ribbon into the "
            "board. Fold, don't twist."]})
    shell = [r for r in bom["printed"]]
    if len(shell) > 1:
        out.append({"title": "Close it", "lines": [
            "Fit the remaining parts in the order the exploded view shows (press E on "
            "the 3D view to see it).",
            "Check that nothing pinches a ribbon or a module before you close the case."]})
    if [e for e in ((el.get("firmware") or {}).get("entries") or []) if e.get("id")]:
        out.append({"title": "Flash and test", "lines": [
            "Plug the USB-C module into your computer and press Flash to board (Firmware).",
            "Then follow the bring-up checklist in the electrical report, one module at a "
            "time."]})
    return out


def assembly_md(f):
    L = ["# %s – assembly" % (f.get("project") or "Product"), "",
         "Written from the design. Not tested by hand yet.", ""]
    for i, s in enumerate(assembly(f), 1):
        L += ["## %d. %s" % (i, s["title"]), ""]
        L += ["- " + ln for ln in s["lines"]]
        L.append("")
    return "\n".join(L)


# ------------------------------------------------------------------ pack
def readme(f, files):
    el = f.get("electrical") or {}
    ss = steps(f)
    L = ["# %s" % (f.get("project") or "Product"), "",
         "Made with Prompt2Product, made by Atech.dev, on %s." % now_text(), "",
         "## Status", ""]
    for s in ss:
        L.append("- **%s**: %s" % (s["title"], s["line"]))
    L += ["", "## In this folder", ""]
    for name, what in files:
        L.append("- `%s`: %s" % (name, what))
    if el.get("unknown"):
        L += ["", "## Not known yet", ""] + ["- " + u for u in el["unknown"]]
    return "\n".join(L) + "\n"


def write_pack(f, folder, extra=None, picture=None):
    """Write the product pack into folder. extra: {relative path: (what,
    writer(path))} for the files only the app can make (print files, the
    wiring PDF). picture: a PNG path to show on product.html. Returns
    [(relative path, what)] of the files written."""
    E = kit()
    os.makedirs(folder, exist_ok=True)
    el = f.get("electrical") or E.analyse({"modules": []}, project=f.get("project", ""))
    files = []

    def put(rel, text, what):
        p = os.path.join(folder, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        files.append((rel, what))

    from . import export_tools  # lazy: pure functions only
    if f.get("bom"):
        put("parts-list.csv", export_tools.bom_csv(f["bom"]), "the parts list (printed and Atech)")
    put("assembly.md", assembly_md(f), "assembly steps, written from the design")
    if el.get("modules"):
        put(os.path.join("electrical", "electrical-report.md"), E.markdown(el),
            "rule checks, modules, power, bring-up, firmware")
        put(os.path.join("electrical", "schematic.svg"), E.schematic_svg(el), "block schematic")
        put(os.path.join("electrical", "power.svg"), E.power_tree_svg(el), "power budget")
        put(os.path.join("electrical", "connections.csv"), E.connections_csv(el),
            "one row per used port")
        put(os.path.join("electrical", "netlist.json"), E.netlist_json(el),
            "port-level netlist (no pin numbers)")
        try:
            atech_wiring = kit("atech_wiring")
            put(os.path.join("electrical", "wiring.svg"),
                atech_wiring.svg(el["wiring"], layout="sheet"), "the wiring diagram")
        except Exception:                               # noqa: BLE001
            pass
        if [e for e in el["firmware"]["entries"] if e.get("id")]:
            src = f.get("firmware_yaml") or el["firmware"]["yaml"]
            put(os.path.join("firmware", PROJECT), src,
                "firmware for `atech build` / `atech upload`")
    for rel, (what, writer) in sorted((extra or {}).items()):
        p = os.path.join(folder, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        try:
            writer(p)
            if os.path.exists(p):
                files.append((rel, what))
        except Exception:                               # noqa: BLE001
            pass
    pic_rel = None
    if picture and os.path.isfile(picture):
        import shutil
        pic_rel = "picture.png"
        shutil.copyfile(picture, os.path.join(folder, pic_rel))
        files.append((pic_rel, "a picture of the design"))
    files.append(("product.html", "this product on one page (opens in any browser)"))
    files.append(("README.md", "status and this list"))
    with open(os.path.join(folder, "product.html"), "w", encoding="utf-8") as fh:
        fh.write(product_html(f, el, files, pic_rel))
    with open(os.path.join(folder, "README.md"), "w", encoding="utf-8") as fh:
        fh.write(readme(f, files))
    mark(folder, "pack", files=[r for r, _w in files])
    return files


STATE_WORDS = {DONE: "Done", READY: "Ready", TODO: "To do", WARN: "Check", BLOCKED: "Fix first"}


def product_html(f, el, files, pic_rel=None):
    """One self-contained page: status, picture, parts, electrical, assembly."""
    E = kit()
    esc = html.escape
    ss = steps(f)
    bom = f.get("bom") or {"printed": [], "hardware": []}
    rows = "".join(
        '<li class="s-%s"><b>%s</b><span>%s</span><em>%s</em></li>'
        % (s["state"], esc(s["title"]), esc(s["line"]), STATE_WORDS[s["state"]]) for s in ss)
    parts = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%g g</td></tr>"
                    % (r["count"], esc(r["part"]), esc(r.get("colour") or ""), r["mass_g"])
                    for r in bom["printed"])
    hw = "".join("<tr><td>1</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                 % (esc(r["name"]), ("port " + esc(r["ports"])) if r["ports"] else "",
                    ("%g mm" % r["length_mm"]) if r.get("length_mm") else "")
                 for r in bom["hardware"])
    asm = "".join("<li><b>%s</b><ul>%s</ul></li>" % (
        esc(s["title"]), "".join("<li>%s</li>" % esc(x) for x in s["lines"]))
        for s in assembly(f))
    elec = ""
    if el.get("modules"):
        rules = "".join('<li class="r-%s"><b>%s.</b> %s <i>%s</i></li>'
                        % (r["level"], E.LEVEL_WORDS[r["level"]], esc(r["text"]), esc(r["fix"]))
                        for r in el["rules"])
        elec = ('<section><h2>Electronics</h2><p class="v v-%s">%s</p><ul class="rules">%s</ul>'
                '<div class="svg">%s</div><div class="svg">%s</div>'
                '<p class="small">%s</p></section>'
                % (el["verdict"]["level"], esc(el["verdict"]["text"]), rules,
                   E.schematic_svg(el), E.power_tree_svg(el), esc(E.LINE_AB_NOTE)))
    pic = '<img class="pic" src="%s" alt="">' % esc(pic_rel) if pic_rel else ""
    filelist = "".join("<li><code>%s</code> %s</li>" % (esc(a), esc(b)) for a, b in files)
    done, total = progress(ss)
    return PAGE % {
        "title": esc(f.get("project") or "Product"), "when": esc(now_text()),
        "done": done, "total": total, "steps": rows, "pic": pic,
        "parts": parts or '<tr><td colspan="4">No printed parts.</td></tr>', "hw": hw,
        "elec": elec, "asm": asm, "files": filelist}


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s</title>
<style>
:root{--bg:#f7f7f8;--card:#fff;--fg:#1c1c1e;--mu:#6b6b73;--ln:#e3e3e8;--ac:#1f6f43;
--ok:#2f8f5b;--wa:#c78a00;--er:#d33a3a}
@media (prefers-color-scheme:dark){:root{--bg:#141416;--card:#1f1f22;--fg:#f2f2f4;
--mu:#a0a0a8;--ln:#333338}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
main{max-width:1060px;margin:0 auto;padding:32px 16px 64px}
header{display:flex;gap:24px;align-items:center;flex-wrap:wrap}
h1{font-size:30px;margin:0}h2{font-size:19px;margin:0 0 12px}
.by{color:var(--mu);font-size:13px}.pic{max-width:100%%;width:420px;border-radius:14px;
background:var(--card);border:1px solid var(--ln)}
section{background:var(--card);border:1px solid var(--ln);border-radius:14px;padding:20px;
margin-top:18px}
.steps{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.steps li{display:grid;grid-template-columns:130px 1fr auto;gap:12px;align-items:baseline;
padding:10px 12px;border-radius:10px;border:1px solid var(--ln)}
.steps em{font-style:normal;font-size:12px;font-weight:600;padding:2px 8px;border-radius:9px;
background:var(--ln)}
.s-done em{background:var(--ok);color:#fff}.s-warn em{background:var(--wa);color:#fff}
.s-blocked em{background:var(--er);color:#fff}
table{border-collapse:collapse;width:100%%}td,th{text-align:left;padding:6px 8px;
border-bottom:1px solid var(--ln);font-size:14px}
.svg svg{width:100%%;max-width:100%%;height:auto;border-radius:10px;margin-top:12px}
.rules{padding-left:18px}.rules i{color:var(--mu)}.r-error b{color:var(--er)}
.r-warning b{color:var(--wa)}.v{font-weight:700}.v-ok{color:var(--ok)}.v-warning{color:var(--wa)}
.v-error{color:var(--er)}.small{color:var(--mu);font-size:12px}
code{font-size:13px}
@media (max-width:600px){.steps li{grid-template-columns:1fr}}
</style></head><body><main>
<header>%(pic)s<div><h1>%(title)s</h1>
<div class="by">Made with Prompt2Product, made by Atech.dev &middot; %(when)s &middot;
%(done)d of %(total)d steps done</div></div></header>
<section><h2>From prompt to product</h2><ul class="steps">%(steps)s</ul></section>
<section><h2>Parts</h2><table><tr><th>#</th><th>Part</th><th>Colour</th><th>PLA</th></tr>
%(parts)s %(hw)s</table></section>
%(elec)s
<section><h2>Assembly</h2><ol>%(asm)s</ol></section>
<section><h2>Files</h2><ul>%(files)s</ul></section>
</main></body></html>
"""
