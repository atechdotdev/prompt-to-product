"""atech_wiring - the wiring of an Atech product, from its build (R960).

A build already knows which module sits on which port of the 14-port board,
and whether it is plugged straight in or on a ribbon cable of what length
(check.py's res["atech"], the app's document). This file turns that into a
wiring diagram a maker can read at the bench: port by port, what is on it,
how it connects, what powers the board, what the Atech SDK warns about, and
what is NOT known yet.

It is PORT-LEVEL ONLY. Every Atech port carries DATA1, DATA2, GND, 3.3 V,
5 V and a rail labelled 12 V, but which pin is which is not published
(docs/ATECH_ASSEMBLY.md: OPEN), no module has current figures, and the SDK's
"interface" field is a driver type (it calls the screen and speaker "gpio").
So nothing here names a pin, a wire colour, a current or a bus.

    modules_from_doc(doc)        the app's walk of a FreeCAD document: the
                                 shape of check._atech_report, plus each
                                 cable's state (ok / moved / missing)
    build(atech, ...)            res["atech"] (or modules_from_doc) -> the
                                 wiring dict (SCHEMA 1)
    connection_words(m)          "plugged in" / "by cable 82 mm" for ./check
    power_line(atech)            the ./check WIRING power line
    notes(atech, cat=None)       the ./check WIRING notes (robot arm, stepper)
    svg(w, layout, theme=None)   the diagram as SVG Tiny ("panel" for the
                                 sidebar, "sheet" for export and print)

Python 3.9+, standard library only (no FreeCAD, no Qt), like atech_firmware.
"""
import re
from xml.sax.saxutils import escape

SCHEMA = 1
BOARD_ID = "14port"
PORTS = tuple(range(1, 15))
LINES = ("DATA1", "DATA2", "GND", "3.3 V", "5 V", "12 V")
PIN_ORDER_KNOWN = False

#: CAD modules that bring power to the board (presets.yaml names).
POWER_MODULES = ("usbc", "power_jack")
POWER_WORDS = {"usbc": "USB-C", "power_jack": "Power jack"}

#: Ports the sources disagree on, with each source's own word for the spot:
#: board.yaml ("Ports 8 (USB-C) and 12 (Reset) are reserved and cannot host
#: modules") and the Atech SDK 14port board layout grid ("USB-C", "Restart").
DISPUTED = {8: ("USB-C", "USB-C"), 12: ("Reset", "Restart")}

#: The board map's port cells (modules_page.CELLS, board frame, mm): centre
#: and the way a module there faces. A copy, so this file needs no Qt; a
#: test keeps the two equal.
CELL_MM = (19.5, 20.0)
PORT_CELLS = {
    1: ((-19.5, -49.99), (-1, 0)), 2: ((-19.5, -30.0), (-1, 0)),
    3: ((-19.5, -10.0), (-1, 0)), 4: ((-19.5, 10.0), (-1, 0)),
    5: ((-19.5, 29.99), (-1, 0)), 6: ((-19.5, 49.99), (-1, 0)),
    7: ((0.0, -49.99), (0, -1)), 8: ((0.0, 49.99), (0, 1)),
    9: ((19.5, -49.99), (1, 0)), 10: ((19.5, -30.0), (1, 0)),
    11: ((19.5, -10.0), (1, 0)), 12: ((19.5, 10.0), (1, 0)),
    13: ((19.5, 29.99), (1, 0)), 14: ((19.5, 49.99), (1, 0)),
}

# ------------------------------------------------------------ the words
#: Every sentence a user can see comes from here or wiring_view.py (the
#: honesty test greps both).
TITLE = "%s – wiring"
SUBTITLE = "Made from the design on %s. Not tested on hardware."
FOOTER_SCOPE = ("Shows which port each module uses, not where it sits in the "
                "product or the path of its cable.")
FOOTER_LINES = ("Every port carries DATA1, DATA2, GND, 3.3 V, 5 V and a rail "
                "labelled 12 V (Atech SDK: fed only by a power module, "
                "unregulated). Which pin is which is not published yet, so "
                "don't wire by pin number from this diagram.")
EMPTY = ("No Atech modules on the board yet. Add one in Atech modules or ask "
         "the agent, and the wiring appears here.")
PINOUT_ASK = ("Atech sends a module's pinout on request: hello@atech.dev or "
              "Discord.")
UNKNOWN_PIN_ORDER = "The pin order inside a port"
UNKNOWN_CURRENT = "How much current each module draws"
UNKNOWN_8_12 = "Whether ports 8 and 12 work as module ports"
UNKNOWN_USBC_OFF_8 = "Whether a USB-C module on a port other than 8 powers the board"
UNKNOWN_12V = "Whether the 12 V rail is fed without a power module"
UNKNOWN_JACK_ALONE = "Whether the power jack module powers the board without a USB-C module"
NO_POWER = "No USB-C or power jack module in this design."
ARM_NOTE = ("robot_arm: the Atech SDK says the arm's servos run on the board's "
            "rail labelled 12 V, which only a power module feeds (the power "
            "jack module, or the USB-C PD power module), not the standard "
            "USB-C module. Ask the user which arm and which supply they have "
            "before they connect it; do not add a power jack module on your "
            "own.")
STEPPER_NOTE = ("stepper_motor: the Atech SDK says it needs its own motor "
                "supply (typically 12-24 V) wired to its driver; the board's "
                "ports do not provide it.")


def _disputed_words(port):
    yaml_w, sdk_w = DISPUTED[port]
    return ("Port %d: board.yaml marks it reserved (%s); the Atech SDK board "
            "layout shows %s here" % (port, yaml_w, sdk_w))


def _norm(text):
    """SDK prose as one line: whitespace collapsed, markdown ** dropped."""
    return re.sub(r"\s+", " ", (text or "").replace("**", "")).strip()


# ------------------------------------------------------------ the walk
def _same(a, b):
    try:
        return bool(a.isSame(b, 1e-6))
    except Exception:                                   # noqa: BLE001
        return a == b


def modules_from_doc(doc):
    """The Atech modules of a FreeCAD document in check._atech_report's
    shape ({"board": {label, name} | None, "modules": [...]}, or None when
    the document has neither), each cabled module's cables with a "state":
    "ok", "moved" (the board or the module moved after the cable was made:
    the same test atech_ports._check_cabled fails) or, for a port with no
    cable, a {"port", "state": "missing"} entry. Duck-typed: any object
    with .Objects whose items carry the Atech properties."""
    board = None
    board_obj = None
    mods = []
    objs = list(getattr(doc, "Objects", []) or [])
    for o in objs:
        role = getattr(o, "AtechRole", None)
        if role == "board" and board is None:
            board_obj = o
            board = {"label": o.Label, "name": o.Name}
        elif role == "module":
            m = {"module": str(getattr(o, "AtechModule", "")),
                 "ports": [int(p) for p in (getattr(o, "AtechPorts", ()) or ())],
                 "label": o.Label, "name": o.Name}
            if getattr(o, "AtechJoint", None) == "cable":
                m["joint"] = "cable"
                cables = []
                for q in objs:
                    if getattr(q, "AtechCableModule", None) != o.Name:
                        continue
                    state = "ok"
                    bat = getattr(q, "AtechCableBoardAt", None)
                    mat = getattr(q, "AtechCableModuleAt", None)
                    if (board_obj is not None and bat is not None
                            and not _same(bat, board_obj.Placement)) or (
                            mat is not None and not _same(mat, o.Placement)):
                        state = "moved"
                    cables.append({"label": q.Label, "port": int(q.AtechCablePort),
                                   "length": float(q.AtechCableLength), "state": state})
                have = {c["port"] for c in cables}
                for p in m["ports"]:
                    if p not in have:
                        cables.append({"port": p, "state": "missing"})
                m["cables"] = cables
            mods.append(m)
    if board is None and not mods:
        return None
    return {"board": board, "modules": mods}


# ------------------------------------------------------------ ./check text
def connection_words(m):
    """How a module of res["atech"] connects, for the ATECH line:
    "plugged in", "by cable 82 mm" or "by cable: port 9 82 mm, port 10 79 mm"."""
    if m.get("joint") != "cable":
        return "plugged in"
    cs = sorted((c for c in m.get("cables") or [] if c.get("length") is not None),
                key=lambda c: c["port"])
    if not cs:
        return "by cable"
    if len(cs) == 1:
        return "by cable %d mm" % round(cs[0]["length"])
    return "by cable: " + ", ".join("port %d %d mm" % (c["port"], round(c["length"]))
                                    for c in cs)


def _power_modules(mods):
    return [m for m in mods if m.get("module") in POWER_MODULES]


def power_line(atech):
    """'WIRING power modules: USB-C on port 7' (or '... none'); None with
    no modules at all."""
    mods = (atech or {}).get("modules") or []
    if not mods:
        return None
    pw = _power_modules(mods)
    if not pw:
        return "WIRING power modules: none (no USB-C or power jack module in this design)"
    return "WIRING power modules: " + "; ".join(
        "%s on port %s" % (POWER_WORDS[m["module"]], ",".join(str(p) for p in m["ports"]))
        for m in pw)


def notes(atech, cat=None):
    """The WIRING notes for ./check (never warnings: the agent cannot settle
    them; the human can)."""
    names = {m.get("module") for m in (atech or {}).get("modules") or []}
    out = []
    if "robot_arm" in names:
        out.append("WIRING " + ARM_NOTE)
    if "stepper_motor" in names:
        out.append("WIRING " + STEPPER_NOTE)
    return out


# ------------------------------------------------------------ the model
def _catalog(cat):
    if cat is not None:
        return cat
    try:
        import atech_firmware
        return atech_firmware.catalog()
    except Exception:                                   # noqa: BLE001
        return None


def _code_names(mods, firmware, cat):
    """{(cad module, first port): instance} from a firmware report (check)
    or atech_firmware.plan() (the app)."""
    entries = None
    if firmware:
        entries = firmware.get("modules")
    if entries is None and cat is not None:
        try:
            import atech_firmware
            entries = atech_firmware.plan(mods, cat)
        except Exception:                               # noqa: BLE001
            entries = None
    out = {}
    for e in entries or []:
        if e.get("id") and e.get("ports"):
            out[(e.get("cad"), min(e["ports"]))] = e.get("instance")
    return out


def build(atech, firmware=None, names=None, reserved=None, cat=None,
          firmware_on=True, project="", made=""):
    """The wiring dict of one build.

    atech:     res["atech"] or modules_from_doc(doc)
    firmware:  res["firmware"] (check) or None (the app: plan() is used)
    names:     {cad module: display name}; the CAD id when missing
    reserved:  atech_ports.RESERVED ({port: reason}); when it is not empty
               it is the rule for ports, over the disputed-ports flag
    firmware_on: False hides the code names (the app's firmware switch)
    project, made: the title's project name and the build time text
    """
    names = names or {}
    reserved = {int(k): v for k, v in (reserved or {}).items()}
    mods = list((atech or {}).get("modules") or [])
    cat = _catalog(cat) if firmware_on else None
    code = _code_names(mods, firmware, cat) if firmware_on else {}
    sdk_id = {}
    try:
        import atech_firmware
        sdk_id = atech_firmware.SDK_ID
    except Exception:                                   # noqa: BLE001
        pass
    conns, flags_all, cautions = [], [], []
    used_8_12 = False
    usbc_off_8 = False
    for m in sorted(mods, key=lambda m: min(m.get("ports") or [99])):
        mod = str(m.get("module") or "")
        ports = sorted(int(p) for p in m.get("ports") or [])
        c = {"ports": ports, "module": mod, "name": names.get(mod) or mod,
             "label": m.get("label") or "", "seeded": bool(m.get("seeded")),
             "how": "cable" if m.get("joint") == "cable" else "plugged in",
             "cables": [], "flags": []}
        if c["how"] == "cable":
            for cb in sorted(m.get("cables") or [], key=lambda q: q["port"]):
                c["cables"].append({"port": cb["port"],
                                    "mm": (round(cb["length"]) if cb.get("length") is not None
                                           else None),
                                    "state": cb.get("state", "ok")})
        if ports:
            inst = code.get((mod, ports[0]))
            if inst:
                c["code_name"] = inst
        for p in ports:
            if reserved:
                if p in reserved:
                    c["flags"].append("Port %d: reserved (%s)" % (p, reserved[p]))
            elif p in DISPUTED and mod != "usbc":
                c["flags"].append(_disputed_words(p))
                used_8_12 = True
        if mod == "usbc" and 8 not in ports:
            usbc_off_8 = True
        flags_all.extend(c["flags"])
        sid = sdk_id.get(mod, mod) if mod in sdk_id else mod
        sm = ((cat or {}).get("modules") or {}).get(sid) if sid else None
        if sm and (sm.get("caution") or "").strip():
            if not any(x["module"] == mod for x in cautions):
                cautions.append({"module": mod, "name": c["name"],
                                 "text": "Atech SDK: " + _norm(sm["caution"])})
        conns.append(c)
    pw = [c for c in conns if c["module"] in POWER_MODULES]
    have = {c["module"] for c in conns}
    if not conns:
        power_text = None
    elif not pw:
        power_text = NO_POWER
    else:
        power_text = "; ".join("%s on port %s" % (POWER_WORDS[c["module"]],
                                                 ", ".join(str(p) for p in c["ports"]))
                               for c in pw)
    unknown = [UNKNOWN_PIN_ORDER, UNKNOWN_CURRENT]
    if used_8_12:
        unknown.append(UNKNOWN_8_12)
    if usbc_off_8:
        unknown.append(UNKNOWN_USBC_OFF_8)
    if conns and "power_jack" not in have:
        unknown.append(UNKNOWN_12V)
    if "power_jack" in have and "usbc" not in have:
        unknown.append(UNKNOWN_JACK_ALONE)
    nts = []
    if "robot_arm" in have:
        nts.append("The robot arm needs a power module for its 12 V rail: "
                   "see the Atech SDK caution.")
    if "stepper_motor" in have:
        nts.append("The stepper motor needs its own motor supply (Atech SDK: "
                   "typically 12-24 V).")
    return {"schema": SCHEMA, "board": BOARD_ID, "project": project or "",
            "made": made or "", "connections": conns,
            "power": {"text": power_text,
                      "modules": [{"module": c["module"], "ports": c["ports"]} for c in pw]},
            "flags": flags_all, "cautions": cautions, "notes": nts,
            "unknown": unknown, "firmware_on": bool(firmware_on)}


def connection_text(c):
    """One plain line per connection (the app's list, the accessible
    description, the sheet's table)."""
    ports = ", ".join(str(p) for p in c["ports"])
    head = "Port%s %s: %s" % ("s" if len(c["ports"]) > 1 else "", ports, c["name"])
    if c["how"] == "plugged in":
        how = "plugged in"
    else:
        bits = []
        for cb in c["cables"]:
            if cb["state"] == "missing":
                bits.append("no cable to port %d" % cb["port"])
            elif cb["state"] == "moved":
                bits.append("cable made for an earlier position – make it again")
            elif cb["mm"] is not None:
                bits.append("cable %d mm (at the last build)" % cb["mm"]
                            if len(c["cables"]) == 1 else
                            "port %d: cable %d mm" % (cb["port"], cb["mm"]))
        how = "; ".join(bits) or "by cable"
        if len(c["cables"]) > 1 and all(cb["state"] == "ok" for cb in c["cables"]):
            how += " (at the last build)"
    s = "%s – %s" % (head, how)
    if c.get("code_name"):
        s += " – name in code: %s" % c["code_name"]
    return s


def lines(w):
    """Every text line of the diagram, in reading order (for the app's
    accessible description and the honesty test)."""
    out = [connection_text(c) for c in w["connections"]]
    out += w["flags"]
    if w["power"]["text"]:
        out.append("Power modules: " + w["power"]["text"])
    out += [c["text"] for c in w["cautions"]]
    out += w["notes"]
    out += ["Not known yet: " + u for u in w["unknown"]]
    return out


# ------------------------------------------------------------ the drawing
LIGHT = {"bg": "#ffffff", "fg": "#1c1c1e", "muted": "#5f6368", "board": "#1f6f43",
         "board_fg": "#ffffff", "cell": "#2e8a57", "cell_used": "#f2b233",
         "box": "#f4f4f6", "box_line": "#8a8a90", "flag": "#b3261e",
         "power": "#e69f00"}
DARK = {"bg": "#1c1c1e", "fg": "#f2f2f4", "muted": "#a0a0a8", "board": "#1f6f43",
        "board_fg": "#ffffff", "cell": "#2e8a57", "cell_used": "#f2b233",
        "box": "#2a2a2e", "box_line": "#77777f", "flag": "#ff8a80",
        "power": "#ffb74d"}


def _short(s, n):
    return s if len(s) <= n else s[:n - 1] + "…"


def _wrap(text, width):
    words, out, cur = (text or "").split(), [], ""
    for wd in words:
        if cur and len(cur) + 1 + len(wd) > width:
            out.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    if cur:
        out.append(cur)
    return out


class _Svg:
    def __init__(self, w, h, theme):
        self.t = theme
        self.parts = ['<svg xmlns="http://www.w3.org/2000/svg" version="1.2" '
                      'baseProfile="tiny" width="%d" height="%d" viewBox="0 0 %d %d">'
                      % (w, h, w, h),
                      '<rect x="0" y="0" width="%d" height="%d" fill="%s"/>' % (w, h, theme["bg"])]

    def rect(self, x, y, w, h, fill, stroke=None, sw=1, rx=0):
        self.parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%g" '
                          'fill="%s"%s/>' % (x, y, w, h, rx, fill,
                                             ' stroke="%s" stroke-width="%g"' % (stroke, sw)
                                             if stroke else ""))

    def line(self, x1, y1, x2, y2, stroke, sw=2, dash=None):
        self.parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
                          'stroke-width="%g"%s/>' % (x1, y1, x2, y2, stroke, sw,
                                                     ' stroke-dasharray="%s"' % dash
                                                     if dash else ""))

    def text(self, x, y, s, size=12, fill=None, anchor="start", weight="normal"):
        self.parts.append('<text x="%.1f" y="%.1f" font-family="Helvetica, Arial, sans-serif" '
                          'font-size="%g" font-weight="%s" text-anchor="%s" fill="%s">%s</text>'
                          % (x, y, size, weight, anchor, fill or self.t["fg"], escape(s)))

    def done(self):
        return "\n".join(self.parts + ["</svg>"]) + "\n"


def _board(sv, cx, cy, s, w, size=12):
    """The board (60 x 120 mm) at scale s px/mm, centred at (cx, cy), with
    every port cell numbered. Board frame y runs down the page (port 1 at
    the top left, as on the Atech modules page)."""
    t = sv.t
    used = {p for c in w["connections"] for p in c["ports"]}
    flagged = {int(re.match(r"Port (\d+)", f).group(1)) for f in w["flags"]
               if re.match(r"Port (\d+)", f)}
    sv.rect(cx - 30 * s, cy - 60 * s, 60 * s, 120 * s, t["board"], rx=4 * s)
    for n in PORTS:
        (x, y), _ = PORT_CELLS[n]
        cw, ch = (CELL_MM[0] - 3) * s, (CELL_MM[1] - 4) * s
        if n in (7, 8):
            cw, ch = ch, cw
        px, py = cx + x * s, cy + y * s
        sv.rect(px - cw / 2, py - ch / 2, cw, ch,
                t["cell_used"] if n in used else t["cell"],
                stroke=t["flag"] if n in flagged else None, sw=3)
        if n in flagged:
            # hatch: explicit lines (no SVG pattern in Tiny)
            for k in range(1, 4):
                f = k / 4.0
                sv.line(px - cw / 2 + f * cw, py - ch / 2, px - cw / 2, py - ch / 2 + f * ch,
                        t["flag"], sw=1)
        sv.text(px, py + size * 0.35, str(n), size=size, anchor="middle", weight="bold",
                fill="#1c1c1e" if n in used else t["board_fg"])


def _anchor(n, cx, cy, s):
    """Where a port's leader starts (the cell's outer edge) and its side."""
    (x, y), (fx, fy) = PORT_CELLS[n]
    if fx:
        return cx + (x + fx * CELL_MM[0] / 2) * s, cy + y * s, "left" if fx < 0 else "right"
    return cx + x * s, cy + (y + fy * CELL_MM[0] / 2) * s, "top" if fy < 0 else "bottom"


def _side(n):
    return {7: "top", 8: "bottom"}.get(n, "left" if n <= 6 else "right")


def _leader(sv, c, cx, cy, s, end, col, sw, dash):
    """A leader from the first port's outer edge straight out of the board,
    then to the label end point (never across another cell)."""
    ax, ay, side = _anchor(c["ports"][0], cx, cy, s)
    if len(c["ports"]) > 1 and side in ("left", "right"):
        ay = sum(_anchor(p, cx, cy, s)[1] for p in c["ports"]) / len(c["ports"])
    ex, ey = end
    if side in ("left", "right"):
        bx = cx + (-1 if side == "left" else 1) * (30 * s + 6)
        sv.line(ax, ay, bx, ay, col, sw=sw, dash=dash)
        sv.line(bx, ay, ex, ey, col, sw=sw, dash=dash)
    else:
        by = cy + (-1 if side == "top" else 1) * (60 * s + 6)
        sv.line(ax, ay, ax, by, col, sw=sw, dash=dash)
        sv.line(ax, by, ex, ey, col, sw=sw, dash=dash)


def _spread(ys, gap, lo, hi):
    """Label centres as near their ports' ys as possible, at least gap
    apart, inside lo..hi (ys sorted)."""
    out = []
    for y in ys:
        y = max(y, lo, (out[-1] + gap) if out else lo)
        out.append(y)
    over = (out[-1] - hi) if out else 0
    if over > 0:
        out = [y - over for y in out]
        for i in range(1, len(out)):
            out[i] = max(out[i], out[i - 1] + gap)
    return out


def _groups(conns):
    g = {"left": [], "right": [], "top": [], "bottom": []}
    for c in conns:
        g[_side(c["ports"][0])].append(c)
    for k in g:
        g[k].sort(key=lambda c: (PORT_CELLS[c["ports"][0]][0][1], c["ports"][0]))
    return g


def _sub_panel(c):
    if c["how"] == "plugged in":
        return "plugged in"
    cs = c["cables"]
    if len(cs) == 1 and cs[0]["state"] == "ok" and cs[0]["mm"]:
        return "cable %d mm" % cs[0]["mm"]
    if cs and all(q["state"] == "ok" and q["mm"] for q in cs):
        return "%d cables" % len(cs)
    return "cable: see the list"


def svg(w, layout="panel", theme=None):
    """The diagram. layout "panel": 360 px wide, for the 300-380 px sidebar
    (theme: LIGHT / DARK or a dict of those keys); "sheet": 1200 x 760,
    always light, for export (PDF / PNG / SVG) and Open large."""
    if layout == "sheet":
        return _sheet(w)
    t = dict(LIGHT)
    t.update(theme or {})
    conns = w["connections"]
    g = _groups(conns)
    W, s, cx = 360, 2.2, 180
    btop = 116                           # board top edge
    cy = btop + 60 * s
    side_ys = {}
    for side in ("left", "right"):
        ys = [cy + PORT_CELLS[c["ports"][0]][0][1] * s for c in g[side]]
        side_ys[side] = _spread(ys, 34, btop - 10, 10 ** 6)
    low = max([y for v in side_ys.values() for y in v] + [cy + 60 * s])
    H = int(max(low + 30, cy + 60 * s + (64 if g["bottom"] else 20)) + 50)
    sv = _Svg(W, H, t)
    sv.text(12, 22, _short(TITLE % (w.get("project") or "Design"), 40), size=14, weight="bold")
    sv.text(12, 40, "Port-level only. Not tested on hardware.", size=12, fill=t["muted"])
    _board(sv, cx, cy, s, w)
    if not conns:
        for i, ln in enumerate(_wrap(EMPTY, 44)):
            sv.text(cx, cy + 60 * s + 24 + 16 * i, ln, size=12, anchor="middle", fill=t["muted"])
        return sv.done()
    for side in ("left", "right"):
        for c, ly in zip(g[side], side_ys[side]):
            col = t["power"] if c["module"] in POWER_MODULES else t["fg"]
            lx = 8 if side == "left" else W - 8
            end = (cx - 30 * s - 16, ly) if side == "left" else (cx + 30 * s + 16, ly)
            _leader(sv, c, cx, cy, s, end, col, 2, "6,4" if c["how"] == "cable" else None)
            anchor = "start" if side == "left" else "end"
            sv.text(lx, ly - 2, _short(c["name"], 13), size=12, anchor=anchor, weight="bold",
                    fill=col)
            sv.text(lx, ly + 13, _sub_panel(c), size=12, anchor=anchor, fill=t["muted"])
    for side in ("top", "bottom"):
        for c in g[side]:
            col = t["power"] if c["module"] in POWER_MODULES else t["fg"]
            ly = btop - 40 if side == "top" else cy + 60 * s + 30
            _leader(sv, c, cx, cy, s, (cx + 44, ly + (8 if side == "top" else -8)), col, 2,
                    "6,4" if c["how"] == "cable" else None)
            sv.text(cx + 50, ly - 4, _short(c["name"], 13), size=12, weight="bold", fill=col)
            sv.text(cx + 50, ly + 11, _sub_panel(c), size=12, fill=t["muted"])
    y = H - 22
    sv.line(12, y - 4, 40, y - 4, t["fg"], sw=2)
    sv.text(46, y, "plugged in", size=12, fill=t["muted"])
    sv.line(150, y - 4, 178, y - 4, t["fg"], sw=2, dash="6,4")
    sv.text(184, y, "by cable", size=12, fill=t["muted"])
    return sv.done()


def _box(sv, t, bx, by, c, col):
    sv.rect(bx, by - 22, 150, 44, t["box"], stroke=t["box_line"], rx=6)
    sv.text(bx + 8, by - 4, _short(c["name"], 18), size=14, weight="bold", fill=col)
    sv.text(bx + 8, by + 14, "port %s, %s" % (",".join(str(p) for p in c["ports"]),
                                             "plugged in" if c["how"] == "plugged in"
                                             else "by cable"), size=12, fill=t["muted"])


def _sheet(w):
    t = dict(LIGHT)
    W, H, s = 1200, 760, 3.2
    sv = _Svg(W, H, t)
    sv.text(40, 48, TITLE % (w.get("project") or "Design"), size=26, weight="bold")
    sv.text(40, 74, SUBTITLE % (w.get("made") or "\u2013"), size=14, fill=t["muted"])
    cx, cy = 330, 400
    _board(sv, cx, cy, s, w, size=16)
    conns = w["connections"]
    g = _groups(conns)
    for side in ("left", "right"):
        ys = [cy + PORT_CELLS[c["ports"][0]][0][1] * s for c in g[side]]
        for c, ly in zip(g[side], _spread(ys, 52, 120, 640)):
            col = t["power"] if c["module"] in POWER_MODULES else t["fg"]
            bx = 40 if side == "left" else cx + 30 * s + 50
            _leader(sv, c, cx, cy, s, (bx + 150 if side == "left" else bx, ly), col, 2.5,
                    "8,5" if c["how"] == "cable" else None)
            _box(sv, t, bx, ly, c, col)
    for side in ("top", "bottom"):
        for c in g[side]:
            col = t["power"] if c["module"] in POWER_MODULES else t["fg"]
            ly = cy - 60 * s - 52 if side == "top" else cy + 60 * s + 52
            _leader(sv, c, cx, cy, s, (cx + 40, ly), col, 2.5,
                    "8,5" if c["how"] == "cable" else None)
            _box(sv, t, cx + 40, ly, c, col)
    if not conns:
        for i, ln in enumerate(_wrap(EMPTY, 60)):
            sv.text(cx, cy + 230 + 18 * i, ln, size=14, anchor="middle", fill=t["muted"])
    # right column: the table, power, cautions, unknowns
    x, y = 720, 110
    sv.text(x, y, "Connections", size=16, weight="bold")
    y += 22
    for c in conns:
        for ln in _wrap(connection_text(c), 68):
            sv.text(x, y, ln, size=12)
            y += 16
        y += 2
    for f in w["flags"]:
        for ln in _wrap(f, 68):
            sv.text(x, y, ln, size=12, fill=t["flag"])
            y += 16
    y += 8
    sv.text(x, y, "Power modules", size=16, weight="bold")
    y += 20
    for ln in _wrap(w["power"]["text"] or "–", 68):
        sv.text(x, y, ln, size=12)
        y += 16
    for nt in w["notes"]:
        for ln in _wrap(nt, 68):
            sv.text(x, y, ln, size=12)
            y += 16
    if w["cautions"]:
        y += 8
        sv.text(x, y, "Atech SDK cautions", size=16, weight="bold")
        y += 20
        for c in w["cautions"]:
            for ln in _wrap(c["text"], 72):
                sv.text(x, y, ln, size=11)
                y += 14
    y += 8
    sv.text(x, y, "Not known yet", size=16, weight="bold")
    y += 20
    for u in w["unknown"] + [PINOUT_ASK]:
        for ln in _wrap(u, 68):
            sv.text(x, y, ln, size=12, fill=t["muted"])
            y += 16
    H = max(H, int(y) + 70)
    sv.parts[0] = ('<svg xmlns="http://www.w3.org/2000/svg" version="1.2" baseProfile="tiny" '
                   'width="%d" height="%d" viewBox="0 0 %d %d">' % (W, H, W, H))
    sv.parts[1] = '<rect x="0" y="0" width="%d" height="%d" fill="%s"/>' % (W, H, t["bg"])
    for i, ln in enumerate(_wrap(FOOTER_SCOPE, 150) + _wrap(FOOTER_LINES, 150)):
        sv.text(40, H - 44 + 16 * i, ln, size=12, fill=t["muted"])
    return sv.done()
