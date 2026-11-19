"""The electrical engineer's view of one design (R1000).

Pure Python (stdlib, py3.9, no FreeCAD, no Qt), on top of atech_wiring
(which module is on which port, plugged in or by cable) and atech_firmware
(the Atech SDK catalog and its placement rules).

    report = analyse(atech, project="Desk buddy", loads={"light": 120},
                     supply="usbc15")

gives one dict (SCHEMA 1) with:

    ports      the 14 ports: who uses each, what the SDK lets it do
    modules    each module's electrical facts, each with its source
    budget     the 5 V power budget, supply, margin, power-bank runtime
    rules      electrical rule checks (error / warning / note), each with a fix
    verdict    one line for the top of the suite
    bringup    a first-power-on checklist from the SDK's events and actions
    firmware   the project.yaml the design asks for, and its issues

and the writers: connections_csv, netlist_json, schematic_svg,
power_tree_svg, markdown.

Where each fact comes from (shown to the user):
    "Atech SDK"        the SDK catalog's module text (atech_sdk_catalog.json)
    "chip datasheet"   a planning figure from the named chip's datasheet
    "you"              a value the user typed in the Power tab
Nothing here invents pin numbers, wire colours or module currents: the pin
order inside a port, Line A/B vs DATA1/DATA2 and every module's current are
not published (WIRING_PLAN.md). Tests check every SDK-sourced sentence
against the catalog text, so a catalog update that changes it fails loudly.
"""
import csv
import io
import json
import re

try:                                    # in the agent kit and the app
    import atech_wiring as _wiring
    import atech_firmware as _fw
except ImportError:                     # pragma: no cover - package import
    from . import atech_wiring as _wiring          # type: ignore
    from . import atech_firmware as _fw            # type: ignore

SCHEMA = 1
PORTS = _wiring.PORTS
LINES = _wiring.LINES

SRC_SDK = "Atech SDK"
SRC_CHIP = "chip datasheet"
SRC_YOU = "you"
SRC_PRESETS = "Atech module notes"

# ---------------------------------------------------------------- module facts
#: CAD module -> facts. "lines" quote the SDK's own words for Line A/B
#: (A1/B1 = the first port, A2/B2 = the second); "quote" is a phrase that
#: must appear in that module's SDK description (test_electrical_r1000).
FACTS = {
    "temp_humidity": {"chip": "AHT20", "signal": "I2C", "i2c": ["0x38"],
                      "lines": {"A": "SDA", "B": "SCL"},
                      "quote": "SDA on Line A, SCL on Line B"},
    "distance_sensor": {"chip": "VL53L5CX (8x8 time of flight)", "signal": "I2C",
                        "lines": {"A": "SDA", "B": "SCL"},
                        "quote": "SDA on Line A, SCL on Line B"},
    "orientation": {"chip": "ICM-40608 or LSM6DSOX (6-axis IMU)", "signal": "I2C",
                    "i2c": ["0x68", "0x6A"], "lines": {"A": "SDA", "B": "SCL"},
                    "quote": "SDA on\nLine A, SCL on Line B"},
    "scd40_air_quality": {"chip": "Sensirion SCD40 (CO2)", "signal": "I2C",
                          "i2c": ["0x62"], "lines": {"A": "SDA", "B": "SCL"},
                          "quote": "SDA on Line A, SCL on Line B"},
    "button": {"chip": "push button", "signal": "digital input (active low, pull-up)",
               "quote": "Active-low with internal\npull-up"},
    "pir": {"chip": "AM312 (passive infrared)", "signal": "digital output",
            "lines": {"A": "OUT", "B": "not used"}, "quote": "Uses only Line A"},
    "dc_motor": {"chip": "H-bridge driver", "signal": "2 lines, PWM speed and direction",
                 "lines": {"A": "drive", "B": "drive"},
                 "quote": "Two GPIO lines drive a small DC motor"},
    "light": {"chip": "WS2812B / SK6812 LEDs (3x3)", "signal": "LED data (one wire)",
              "lines": {"A": "LED data (RGB)", "B": "LED data (RGBW)"},
              "quote": "Drives both Line A (RGB) and Line B\n(RGBW)"},
    "microphone": {"chip": "ICS-43434 (I2S MEMS mic)", "signal": "I2S in",
                   "lines": {"A1": "LR select", "B1": "WS", "A2": "SCK", "B2": "SD"},
                   "quote": "Line A1 = LR select,\nLine B1 = WS, Line A2 = SCK, Line B2 = SD"},
    "speaker": {"chip": "MAX98357A (3 W class-D I2S amp)", "signal": "I2S out",
                "quote": "3W Class-D I2S audio amplifier (MAX98357A)"},
    "screen": {"chip": "ST7735 160x80 colour TFT", "signal": "SPI",
               "lines": {"A1": "DC", "B1": "CS", "A2": "MOSI", "B2": "SCLK"},
               "quote": "DC on Line A1, CS on Line B1, MOSI on Line A2, SCLK on Line B2"},
    "stepper_motor": {"chip": "TMC2209 stepper driver", "signal": "STEP / DIR / ENABLE",
                      "lines": {"A1": "STEP", "B1": "DIR", "A2": "ENABLE"},
                      "supply": "its own motor supply, typically 12-24 V",
                      "quote": "EXTERNAL motor\nsupply (typically 12-24 V)"},
    "knob": {"chip": "rotary encoder, push switch, 12-LED ring", "signal": "quadrature + switch + LED data",
             "quote": "18-step quadrature rotary encoder"},
    "robot_arm": {"chip": "SO-101 arm (Feetech STS3215 servos)", "signal": "half-duplex UART, 1 Mbps",
                  "lines": {"A": "TX", "B": "RX"},
                  "supply": "the board's high-voltage rail, fed by a power module",
                  "quote": "TX on Line A, RX on Line B"},
    "usbc": {"chip": "USB-C power input", "signal": "power in (5 V)", "power_in": True},
    "power_jack": {"chip": "DC power jack", "signal": "power in (high-voltage rail)",
                   "power_in": True},
    "soil_sensor": {"chip": "CH32V003 co-processor", "signal": "I2C", "i2c": ["0x37"],
                    "source": SRC_PRESETS},
    "load_cell": {"chip": "load-cell amplifier", "signal": "not published"},
    "big_screen": {"chip": "large display", "signal": "not published"},
    "camera": {"chip": "camera", "signal": "not published"},
}

# ---------------------------------------------------------------- power
#: Planning figures (peak mA at 5 V) where the chip's datasheet gives a
#: number big enough to matter. Everything else is "not known" until the
#: user types a measured value.
PLANNING_MA = {
    "_board": (350, "ESP32-S3 Wi-Fi transmit bursts (ESP32-S3 datasheet, about 350 mA)"),
    "light": (110, "9 LEDs x 60 mA at full white, and the SDK clamps brightness to 20 %"),
    "speaker": (700, "MAX98357A at its full 3 W at 5 V (datasheet), about 700 mA"),
    "knob": (150, "12-LED ring at the SDK's brightness clamp, about 150 mA"),
}
#: Loads that run from their own supply: not on the 5 V budget.
OWN_SUPPLY = {"stepper_motor": "the motor runs from its own 12-24 V supply (Atech SDK)",
              "robot_arm": "the servos run from the high-voltage rail (Atech SDK)"}
SUPPLIES = {   # key -> (words, mA at 5 V): the USB specifications' figures
    "usb2": ("Computer USB port (USB 2.0)", 500),
    "usb3": ("Computer USB port (USB 3)", 900),
    "usbc15": ("USB-C charger or port, 1.5 A", 1500),
    "usbc3": ("USB-C charger, 3 A", 3000),
}
DEFAULT_SUPPLY = "usbc15"
MARGIN = 0.8              # stay under 80 % of the supply (usual design margin)
BANK_EFF = 0.85           # power bank: 3.7 V cell -> 5 V out
CELL_V, OUT_V = 3.7, 5.0

LEVELS = ("error", "warning", "note")

# words the user sees
NOT_KNOWN = "not known"
LINE_AB_NOTE = ("Line A and Line B are the Atech SDK's names for a port's two "
                "data lines. Which of DATA1/DATA2 each one is, and the pin "
                "order, are not published yet.")
RAILS_NOTE = ("The rails (GND, 3.3 V, 5 V, 12 V) are drawn as shared by every "
              "port, as on most boards; Atech has not published this.")


#: The modules' display names (models/presets.yaml display_name).
NAMES = {"button": "Button", "light": "Light", "usbc": "USB-C", "screen": "Screen",
         "speaker": "Speaker", "dc_motor": "DC Motor", "orientation": "Orientation Sensor",
         "temp_humidity": "Temp / Humidity", "distance_sensor": "Distance Sensor",
         "knob": "Knob", "microphone": "Microphone", "pir": "PIR Motion Sensor",
         "scd40_air_quality": "CO2 Sensor (SCD40)", "robot_arm": "Robot Arm Integrator",
         "stepper_motor": "Stepper Motor Driver", "soil_sensor": "Soil Sensor",
         "load_cell": "Load Cell Amplifier", "power_jack": "Power Jack",
         "big_screen": "Big Screen", "camera": "Camera"}


def _cat(cat=None):
    return cat or _fw.catalog() or {"modules": {}, "boards": {}}


def _sdk(mod, cat):
    sid = _fw.SDK_ID.get(mod, mod)
    if sid is None:
        return None, None
    return sid, (cat.get("modules") or {}).get(sid)


def _board(cat):
    return (cat.get("boards") or {}).get(_fw.BOARD) or {}


# ---------------------------------------------------------------- ports
def lines_on(module, i):
    """{"A": role, "B": role} on the module's i-th port (0 = its first)."""
    ln = FACTS.get(module, {}).get("lines") or {}
    n = str(i + 1)
    out = {}
    for k in ("A", "B"):
        v = ln.get(k + n) or (ln.get(k) if i == 0 else None)
        if v:
            out[k] = v
    return out


def port_map(w, cat=None):
    """[{port, can, module, name, line_role, state}] for the 14 ports.
    can: what the SDK lets the port do ("i2c, digital, gpio, uart");
    state: "used" | "free" | "reserved" (SDK says reserved, nothing on it)."""
    cat = _cat(cat)
    b = _board(cat)
    reserved = set(b.get("reserved") or ())
    by_port = {}
    for c in w.get("connections") or []:
        for i, p in enumerate(c["ports"]):
            by_port[p] = (c, i)
    out = []
    for p in PORTS:
        can = sorted((b.get("ports") or {}).get(str(p)) or ())
        row = {"port": p, "can": ", ".join(can) if can else "",
               "uart": "uart" in can, "analog": "analog" in can,
               "module": "", "name": "", "lines": {}, "state": "free", "how": ""}
        if p in by_port:
            c, i = by_port[p]
            row.update(module=c["module"], name=c["name"], state="used",
                       how=_wiring.connection_text(c).split(" – ", 1)[1].split(
                           " – name in code")[0],
                       lines=lines_on(c["module"], i))
        elif p in reserved:
            row["state"] = "reserved"
        out.append(row)
    return out


# ---------------------------------------------------------------- modules
def module_facts(w, cat=None):
    """Each connection's electrical facts, each with where it comes from."""
    cat = _cat(cat)
    out = []
    for c in w.get("connections") or []:
        mod = c["module"]
        f = FACTS.get(mod, {})
        sid, sm = _sdk(mod, cat)
        src = f.get("source") or (SRC_SDK if sm else SRC_PRESETS)
        row = {"module": mod, "name": c["name"], "ports": c["ports"],
               "how": c["how"], "chip": f.get("chip") or NOT_KNOWN,
               "signal": f.get("signal") or NOT_KNOWN, "source": src,
               "i2c": list(f.get("i2c") or ()), "lines": dict(f.get("lines") or {}),
               "sdk": sid or "", "driver": (sm or {}).get("class") or "",
               "supply": f.get("supply") or "",
               "caution": _wiring._norm((sm or {}).get("caution") or ""),
               "power_in": bool(f.get("power_in")),
               "code_name": c.get("code_name") or ""}
        out.append(row)
    return out


# ---------------------------------------------------------------- budget
def budget(w, loads=None, supply=None, bank_mah=None):
    """The 5 V budget. loads: {cad module or "_board": mA} typed by the user
    (they win over planning figures). Returns rows, totals and a status:
    "ok" (under the margin), "tight" (over 80 %), "over", or "unknown"
    (nothing known but the board)."""
    loads = {k: v for k, v in (loads or {}).items() if v not in (None, "")}
    supply = supply if supply in SUPPLIES else DEFAULT_SUPPLY
    rows = []

    def row(key, name, ports):
        if key in OWN_SUPPLY:
            return {"key": key, "name": name, "ports": ports, "ma": None,
                    "source": SRC_SDK, "why": OWN_SUPPLY[key], "own_supply": True}
        if key in loads:
            return {"key": key, "name": name, "ports": ports, "ma": float(loads[key]),
                    "source": SRC_YOU, "why": "measured or typed by you"}
        if key in PLANNING_MA:
            ma, why = PLANNING_MA[key]
            return {"key": key, "name": name, "ports": ports, "ma": float(ma),
                    "source": SRC_CHIP, "why": why}
        return {"key": key, "name": name, "ports": ports, "ma": None,
                "source": "", "why": "not published: measure it, or ask Atech"}

    rows.append(row("_board", "Atech board (ESP32-S3)", []))
    seen = {}
    for c in w.get("connections") or []:
        if c["module"] in _wiring.POWER_MODULES:
            continue
        key = c["module"]
        seen[key] = seen.get(key, 0) + 1
        k = key if seen[key] == 1 else "%s#%d" % (key, seen[key])
        r = row(k if k in loads else key, c["name"], c["ports"])
        r["key"] = k
        rows.append(r)
    known = [r for r in rows if r["ma"] is not None]
    unknown = [r for r in rows if r["ma"] is None and not r.get("own_supply")]
    total = round(sum(r["ma"] for r in known), 1)
    words, cap = SUPPLIES[supply]
    share = total / cap if cap else 0.0
    if share > 1.0:
        status = "over"
    elif share > MARGIN:
        status = "tight"
    elif len(known) <= 1 and unknown:
        status = "unknown"
    else:
        status = "ok"
    out = {"rows": rows, "total_ma": total, "unknown": len(unknown),
           "supply": supply, "supply_words": words, "supply_ma": cap,
           "share": round(share, 3), "status": status,
           "margin_ma": round(cap * MARGIN - total, 1)}
    if bank_mah:
        try:
            mah = float(bank_mah)
        except (TypeError, ValueError):
            mah = 0
        if mah > 0 and total > 0:
            out["bank_mah"] = mah
            out["bank_hours"] = round(mah * CELL_V / OUT_V * BANK_EFF / total, 1)
    return out


def budget_line(b):
    """"About 1,310 mA of 1,500 mA (87 %) from a USB-C charger or port, 1.5 A;
    2 modules not known yet." """
    s = ("About %s mA of %s mA (%d %%) from a %s"
         % (_n(b["total_ma"]), _n(b["supply_ma"]), round(b["share"] * 100),
            b["supply_words"][0].lower() + b["supply_words"][1:]
            if not b["supply_words"].startswith("USB") else b["supply_words"]))
    if b["unknown"]:
        s += "; %d module%s not known yet" % (b["unknown"], "" if b["unknown"] == 1 else "s")
    return s + "."


def _n(x):
    return "{:,}".format(int(round(x)))


# ---------------------------------------------------------------- rules
def _rule(rid, level, text, fix="", where=None):
    return {"id": rid, "level": level, "text": text, "fix": fix,
            "ports": sorted(where or ())}


def rules(w, cat=None, b=None, firmware_issues=None):
    """Electrical rule checks: [{id, level, text, fix, ports}], errors first."""
    cat = _cat(cat)
    conns = w.get("connections") or []
    have = {}
    for c in conns:
        have.setdefault(c["module"], []).append(c)
    out = []
    if not conns:
        return out
    # power
    if not any(m in have for m in _wiring.POWER_MODULES):
        out.append(_rule("power.none", "error",
                         "Nothing powers the board: no USB-C or power jack module.",
                         "Add a USB-C module. It usually goes on port 8."))
    for c in have.get("usbc", []):
        if 8 not in c["ports"]:
            out.append(_rule("power.usbc_port", "note",
                             "The USB-C module is on port %s, not port 8. Whether it "
                             "powers the board there is not published."
                             % ", ".join(map(str, c["ports"])),
                             "Put it on port 8, or ask Atech.", c["ports"]))
    if "robot_arm" in have and "power_jack" not in have:
        out.append(_rule("power.arm_rail", "warning",
                         "The robot arm's servos run from the high-voltage rail, and "
                         "only a power module feeds it. The standard USB-C module "
                         "does not (Atech SDK).",
                         "Add the power jack module with a supply that matches the "
                         "arm (5 V or 12 V, never above 12 V).",
                         [p for c in have["robot_arm"] for p in c["ports"]]))
    for c in have.get("stepper_motor", []):
        out.append(_rule("power.stepper_vmot", "warning",
                         "The stepper driver needs its own motor supply, typically "
                         "12-24 V. Without it the calls succeed but the motor does "
                         "not move (Atech SDK).",
                         "Wire a 12-24 V supply to the driver board's motor input.",
                         c["ports"]))
    if b is not None:
        if b["status"] == "over":
            out.append(_rule("power.over", "error",
                             "The known loads (%s mA) are more than the supply gives "
                             "(%s mA)." % (_n(b["total_ma"]), _n(b["supply_ma"])),
                             "Use a bigger supply in the Power tab, or lower the "
                             "loads (LED brightness, speaker volume)."))
        elif b["status"] == "tight":
            out.append(_rule("power.tight", "warning",
                             "The known loads use %d %% of the supply; keep under 80 %%."
                             % round(b["share"] * 100),
                             "Pick a bigger supply, or lower the loads."))
        if b["unknown"]:
            out.append(_rule("power.unknown", "note",
                             "%d module%s ha%s no published current, so the power "
                             "budget is a lower bound." % (
                                 b["unknown"], "" if b["unknown"] == 1 else "s",
                                 "s" if b["unknown"] == 1 else "ve"),
                             "Measure it on the bench and type it in the Power tab."))
    # cables
    for c in conns:
        for q in c.get("cables") or []:
            if q.get("state") == "missing":
                out.append(_rule("cable.missing", "error",
                                 "%s has no cable to port %d." % (c["name"], q["port"]),
                                 "Connect it by cable again on the Atech modules page.",
                                 [q["port"]]))
            elif q.get("state") == "moved":
                out.append(_rule("cable.stale", "warning",
                                 "%s's cable to port %d was made for an earlier "
                                 "position." % (c["name"], q["port"]),
                                 "Make the cable again (Atech modules page).", [q["port"]]))
    # SDK placement rules
    if firmware_issues is None:
        firmware_issues = _fw.issues(_fw.plan(_seated(w), cat), cat=cat)
    by_inst = {}
    for e in _fw.plan(_seated(w), cat):
        by_inst["%s (%s)" % (e.get("instance"), e.get("cad") or e.get("id"))] = e
    for t in firmware_issues:
        level = "note" if "has no firmware module" in t else "warning"
        fix = ("Move the module to a port the Atech SDK accepts, or leave it if you "
               "write its firmware yourself." if level == "warning"
               else "Its firmware is up to you for now.")
        key = next((k for k in by_inst if t.startswith(k)), None)
        e = by_inst.get(key) if key else None
        shown = t
        if e is not None:
            shown = NAMES.get(e.get("cad"), e.get("cad") or key) + t[len(key):]
        shown = shown.replace("the 14port", "the 14-port board")
        if level == "warning" and e is not None:
            free = free_places(w, e, cat)
            if free:
                few = free[:3]
                words = few[0] if len(few) == 1 else "%s or %s" % (", ".join(few[:-1]), few[-1])
                fix = "Move it to %s %s: free, and the Atech SDK accepts %s." % (
                    "ports" if "+" in few[0] or len(few) > 1 else "port", words,
                    "them" if len(few) > 1 or "+" in few[0] else "it")
        out.append(_rule("sdk.placement", level, shown[0].upper() + shown[1:] + ".", fix,
                         [int(x) for x in re.findall(r"port (\d+)", t)][:2]))
    for f in w.get("flags") or []:
        out.append(_rule("port.disputed", "warning", f + ".",
                         "Use another port until Atech confirms 8 and 12 take modules.",
                         [int(x) for x in re.findall(r"Port (\d+)", f)]))
    # firmware limits the SDK states
    motors = have.get("dc_motor", [])
    if len(motors) > 4:
        out.append(_rule("sdk.motors_pwm", "warning",
                         "%d DC motors: the SDK gives hardware PWM to the first 4 only; "
                         "the rest run on/off." % len(motors),
                         "Use 4 DC motors or fewer if they all need speed control."))
    # shared I2C addresses
    addr = {}
    for c in conns:
        for a in FACTS.get(c["module"], {}).get("i2c") or ():
            addr.setdefault(a, []).append(c)
    for a, cs in sorted(addr.items()):
        if len(cs) > 1 and len({c["module"] for c in cs}) == 1:
            out.append(_rule("i2c.same_address", "note",
                             "%d %s modules share I2C address %s. They are on "
                             "different ports; whether each port is its own bus is "
                             "not published." % (len(cs), cs[0]["name"], a),
                             "Test them together early.",
                             [p for c in cs for p in c["ports"]]))
    seen, uniq = set(), []
    for r in out:
        k = (r["id"], r["text"])
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    out = uniq
    order = {k: i for i, k in enumerate(LEVELS)}
    out.sort(key=lambda r: (order[r["level"]], r["ports"][:1] or [99]))
    return out


def free_places(w, entry, cat=None):
    """Where a firmware entry could go instead: ["5+6", "1+2"] or ["10"],
    free ports (not used by another module, not reserved) whose interfaces
    the SDK module needs, in port order."""
    cat = _cat(cat)
    b = _board(cat)
    spec = (cat.get("modules") or {}).get(entry.get("id") or "") or {}
    if not spec or not b:
        return []
    mine = set(entry.get("ports") or ())
    used = {p for c in w.get("connections") or [] for p in c["ports"]} - mine
    reserved = set(b.get("reserved") or ())
    need = spec.get("interface")

    def ok(p):
        iface = set((b.get("ports") or {}).get(str(p)) or ())
        if need == "gpio":
            iface |= {"gpio", "digital"}
        return p not in used and p not in reserved and str(p) in (b.get("ports") or {}) \
            and need in iface

    if spec.get("size") == 2:
        return ["%d+%d" % tuple(q) for q in sorted(tuple(x) for x in b.get("adjacent") or ())
                if ok(q[0]) and ok(q[1])]
    return [str(p) for p in sorted(int(x) for x in (b.get("ports") or {})) if ok(p)]


def _seated(w):
    return [{"module": c["module"], "ports": c["ports"]} for c in w.get("connections") or []]


def verdict(rs, w):
    if not (w.get("connections") or []):
        return {"level": "empty", "text": _wiring.EMPTY}
    e = sum(r["level"] == "error" for r in rs)
    wn = sum(r["level"] == "warning" for r in rs)
    if e:
        return {"level": "error", "text": "%d thing%s to fix before you wire it up."
                % (e, "" if e == 1 else "s")}
    if wn:
        return {"level": "warning", "text": "Ready to wire, with %d warning%s to read."
                % (wn, "" if wn == 1 else "s")}
    return {"level": "ok", "text": "Ready to wire: no errors or warnings."}


# ---------------------------------------------------------------- bring-up
def _inst(key, inst):
    return re.sub(r"\{\{\s*instance\s*\}\}", inst, key)


def bringup(w, cat=None, entries=None):
    """The first power-on, step by step: [{title, steps:[str]}]."""
    cat = _cat(cat)
    entries = entries if entries is not None else _fw.plan(_seated(w), cat)
    by_cad = {}
    for e in entries:
        by_cad.setdefault((e["cad"], e["ports"][0] if e["ports"] else 0), e)
    out = [{"title": "Before power", "steps": [
        "Seat every module on the port the port map shows; check each by its port "
        "number on the board's silkscreen.",
        "Cabled modules: the ribbon's lengths are in the wiring list. Don't twist "
        "or kink a ribbon.",
        "Nothing on ports 8 or 12 except the USB-C module, unless Atech says so.",
    ]}]
    own = [c for c in w.get("connections") or [] if c["module"] in OWN_SUPPLY]
    if own:
        out[0]["steps"].append("Leave the motor or servo supply OFF for the first "
                               "power-on; switch it on after the board checks out.")
    out.append({"title": "Power and flash", "steps": [
        "Plug USB-C into the computer. `atech ports` should list the board.",
        "Flash it: `atech upload` in the firmware folder (or Flash in the Firmware tab).",
        "`atech check` reboots the board and reports each module's health.",
    ]})
    tests = []
    for c in w.get("connections") or []:
        e = by_cad.get((c["module"], c["ports"][0] if c["ports"] else 0))
        if not e or not e.get("id"):
            continue
        sm = (cat.get("modules") or {}).get(e["id"]) or {}
        inst = e["instance"]
        for ev in (sm.get("events") or [])[:2]:
            k = _inst(ev["key"], inst)
            unit = (" (%s)" % ev["unit"]) if ev.get("unit") else ""
            tests.append("%s on port %s: watch `atech monitor --key %s`%s, %s"
                         % (c["name"], _ports(c["ports"]), k, unit,
                            _first_sentence(ev.get("description") or "it should change")))
        for ac in (sm.get("actions") or [])[:1]:
            k = _inst(ac["key"], inst)
            tests.append("%s on port %s: `atech send %s%s` and look: %s"
                         % (c["name"], _ports(c["ports"]), k, _example_value(ac),
                            _first_sentence(ac.get("description") or "")))
    if tests:
        out.append({"title": "Test each module", "steps": tests})
    if own:
        out.append({"title": "Motors last", "steps": [
            "Switch the motor or servo supply on, then try one small move first."]})
    return out


def _ports(ps):
    return "+".join(str(p) for p in ps)


def _first_sentence(t):
    t = " ".join(t.split())
    m = re.match(r"(.+?[.!?])(\s|$)", t)
    s = (m.group(1) if m else t)
    return s[0].lower() + s[1:] if s else s


def _example_value(ac):
    vt = ac.get("value_type")
    if vt == "json":
        if "r" in (ac.get("description") or ""):
            return " r=0 g=0 b=255"
        return ""
    if vt in ("int", "float", "number"):
        return " 100"
    return ""


# ---------------------------------------------------------------- analyse
def analyse(atech=None, w=None, cat=None, project="", made="", names=None,
            loads=None, supply=None, bank_mah=None, firmware=None, reserved=None):
    """Everything above in one dict. Give atech (check's res["atech"] or
    atech_wiring.modules_from_doc) or a ready wiring dict w."""
    cat = _cat(cat)
    if w is None:
        w = _wiring.build(atech or {"modules": []}, firmware=firmware,
                          names=dict(NAMES, **(names or {})),
                          reserved=reserved, cat=cat, project=project, made=made)
    entries = _fw.plan(_seated(w), cat)
    issues = _fw.issues(entries, cat=cat)
    b = budget(w, loads=loads, supply=supply, bank_mah=bank_mah)
    rs = rules(w, cat=cat, b=b, firmware_issues=issues)
    return {"schema": SCHEMA, "project": project or w.get("project") or "",
            "made": made or w.get("made") or "", "board": w.get("board"),
            "wiring": w, "ports": port_map(w, cat), "modules": module_facts(w, cat),
            "budget": b, "rules": rs, "verdict": verdict(rs, w),
            "bringup": bringup(w, cat, entries),
            "firmware": {"entries": entries, "issues": issues,
                         "yaml": _fw.project_yaml(project or "product", entries),
                         "sdk": _fw.sdk_label(cat)},
            "unknown": list(w.get("unknown") or []),
            "notes": [LINE_AB_NOTE]}


# ---------------------------------------------------------------- writers
def connections_csv(r):
    """One row per used port: the module, its Line A/B roles (Atech SDK),
    the data nets, the rails and how it connects."""
    buf = io.StringIO()
    wr = csv.writer(buf, lineterminator="\n")
    wr.writerow(["port", "module", "chip", "signal", "line A (Atech SDK)",
                 "line B (Atech SDK)", "data nets", "rails", "connection"])
    chips = {}
    for m in r["modules"]:
        for p in m["ports"]:
            chips[p] = m
    for p in r["ports"]:
        if p["state"] != "used":
            continue
        m = chips.get(p["port"], {})
        wr.writerow([p["port"], p["name"], m.get("chip", ""), m.get("signal", ""),
                     p["lines"].get("A", ""), p["lines"].get("B", ""),
                     "%s, %s" % (_net(p["port"], "DATA1"), _net(p["port"], "DATA2")),
                     "GND, +3V3, +5V, +12V_RAIL", p["how"]])
    return buf.getvalue()


def _net(port, line):
    if line in ("DATA1", "DATA2"):
        return "P%d_%s" % (port, line)
    return {"GND": "GND", "3.3 V": "+3V3", "5 V": "+5V", "12 V": "+12V_RAIL"}[line]


def netlist_json(r):
    """A port-level netlist: data nets per port, shared rails. No pin numbers."""
    nets = {}
    refs = []
    for i, m in enumerate(r["modules"], 1):
        ref = "M%d" % i
        refs.append({"ref": ref, "module": m["module"], "name": m["name"],
                     "chip": m["chip"], "ports": m["ports"]})
        for p in m["ports"]:
            for ln in LINES:
                n = _net(p, ln)
                nets.setdefault(n, [{"ref": "BOARD", "connector": "PORT%d" % p, "signal": ln}]
                                if ln in ("DATA1", "DATA2") else [])
                nets[n].append({"ref": ref, "connector": "PORT%d" % p, "signal": ln})
    for rail in ("GND", "+3V3", "+5V", "+12V_RAIL"):
        if rail in nets:
            nets[rail].insert(0, {"ref": "BOARD", "connector": "rail", "signal": rail})
    doc = {"schema": SCHEMA, "kind": "atech-port-netlist", "project": r["project"],
           "board": r["board"], "parts": refs,
           "nets": [{"name": k, "nodes": v} for k, v in sorted(nets.items())],
           "assumptions": [RAILS_NOTE, LINE_AB_NOTE],
           "pin_numbers": None}
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


THEMES = {
    "light": {"bg": "#ffffff", "fg": "#1c1c1e", "muted": "#6b6b73", "line": "#d4d4da",
              "board": "#1f6f43", "board_fg": "#ffffff", "box": "#f6f6f8",
              "i2c": "#2f6fdf", "spi": "#a24bd6", "i2s": "#d6582f", "digital": "#2f8f5b",
              "uart": "#c78a00", "power": "#d33a3a", "other": "#6b6b73"},
    "dark": {"bg": "#1c1c1e", "fg": "#f2f2f4", "muted": "#a0a0a8", "line": "#3a3a40",
             "board": "#1f6f43", "board_fg": "#ffffff", "box": "#26262a",
             "i2c": "#6c9cf5", "spi": "#c486ec", "i2s": "#f08a62", "digital": "#5cc58a",
             "uart": "#e7b437", "power": "#f06a6a", "other": "#a0a0a8"},
}


def bus_kind(signal):
    s = (signal or "").lower()
    if "power" in s:
        return "power"
    for k in ("i2c", "spi", "i2s", "uart"):
        if k in s:
            return k
    if s and s != NOT_KNOWN and "not published" not in s:
        return "digital"
    return "other"


BUS_WORDS = {"i2c": "I2C", "spi": "SPI", "i2s": "I2S", "uart": "UART",
             "digital": "digital", "power": "power in", "other": "not published"}


def role_words(m):
    """"A: SDA · B: SCL · 0x38" from a module_facts row."""
    bits = ["%s: %s" % kv for kv in sorted(m["lines"].items(),
                                          key=lambda kv: (kv[0][1:], kv[0][0]))]
    if m["i2c"]:
        bits.append("/".join(m["i2c"]))
    return " · ".join(bits)


def schematic_svg(r, theme="light"):
    """A block schematic: power on top, the board in the middle, each module
    as a block with its chip, bus and Line A/B roles, joined to its port."""
    t = THEMES.get(theme, THEMES["light"])
    mods = r["modules"]
    left = [m for m in mods if m["ports"] and min(m["ports"]) <= 7]
    right = [m for m in mods if m not in left]
    row_h, box_w, box_h = 74, 250, 60
    n = max(len(left), len(right), 4)
    W, top = 1100, 150
    H = top + n * row_h + 90
    bx, bw = 440, 220
    by, bh = top - 10, n * row_h
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'font-family="Helvetica, Arial, sans-serif">' % (W, H, W, H),
           '<rect width="%d" height="%d" fill="%s"/>' % (W, H, t["bg"])]
    title = (r["project"] or "Design") + " – block schematic"
    out.append('<text x="24" y="36" font-size="20" font-weight="700" fill="%s">%s</text>'
               % (t["fg"], _esc(title)))
    out.append('<text x="24" y="58" font-size="12" fill="%s">%s</text>' % (
        t["muted"], _esc("Port level, from the design. Not tested on hardware. "
                         "Line roles quote the Atech SDK.")))
    # power band
    pw = [m for m in mods if m["power_in"]]
    px = 24
    for i, (label, col) in enumerate((("+5V", t["power"]), ("+3V3", t["power"]),
                                      ("GND", t["muted"]), ("+12V rail", t["power"]))):
        x = bx - 120 + i * 120
        out.append('<line x1="%d" y1="96" x2="%d" y2="%d" stroke="%s" stroke-width="1.5" '
                   'stroke-dasharray="4 3"/>' % (x + 40, x + 40, by, col))
        out.append('<text x="%d" y="90" font-size="11" fill="%s" text-anchor="middle">%s</text>'
                   % (x + 40, col, label))
    src = ", ".join("%s (port %s)" % (m["name"], _ports(m["ports"])) for m in pw) or \
        "no power module"
    out.append('<text x="%d" y="122" font-size="12" fill="%s">Power in: %s</text>'
               % (px, t["fg"], _esc(src)))
    # board
    out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="10" fill="%s"/>'
               % (bx, by, bw, bh, t["board"]))
    out.append('<text x="%d" y="%d" font-size="14" font-weight="700" fill="%s" '
               'text-anchor="middle">Atech 14-port board</text>'
               % (bx + bw / 2, by + bh / 2 - 8, t["board_fg"]))
    out.append('<text x="%d" y="%d" font-size="12" fill="%s" text-anchor="middle">ESP32-S3</text>'
               % (bx + bw / 2, by + bh / 2 + 12, t["board_fg"]))

    def block(m, i, side):
        y = top + i * row_h
        x = 24 if side == "L" else W - 24 - box_w
        k = bus_kind(m["signal"])
        col = t[k]
        out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="8" fill="%s" stroke="%s"/>'
                   % (x, y, box_w, box_h, t["box"], col))
        out.append('<rect x="%d" y="%d" width="5" height="%d" rx="2" fill="%s"/>'
                   % (x, y, box_h, col))
        out.append('<text x="%d" y="%d" font-size="13" font-weight="700" fill="%s">%s</text>'
                   % (x + 14, y + 18, t["fg"], _esc(_cut(m["name"], 30))))
        out.append('<text x="%d" y="%d" font-size="11" fill="%s">%s</text>'
                   % (x + 14, y + 34, t["muted"], _esc(_cut(m["chip"], 40))))
        roles = role_words(m)
        out.append('<text x="%d" y="%d" font-size="11" fill="%s">%s</text>'
                   % (x + 14, y + 50, col, _esc(_cut(roles, 44))))
        # wire to the board edge
        yy = y + box_h / 2
        x0 = x + box_w if side == "L" else x
        x1 = bx if side == "L" else bx + bw
        dash = ' stroke-dasharray="6 4"' if m["how"] == "cable" else ""
        out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2.5"%s/>'
                   % (x0, yy, x1, yy, col, dash))
        label = "%s · port %s" % (BUS_WORDS[k], _ports(m["ports"]))
        mx = (x0 + x1) / 2
        out.append('<text x="%d" y="%d" font-size="11" fill="%s" text-anchor="middle">%s</text>'
                   % (mx, yy - 6, t["fg"], _esc(_cut(label, 26))))
        pin_x = x1 + (10 if side == "L" else -10)
        out.append('<text x="%d" y="%d" font-size="11" font-weight="700" fill="%s" '
                   'text-anchor="%s">P%s</text>' % (pin_x, yy + 4, t["board_fg"],
                                                   "start" if side == "L" else "end",
                                                   _ports(m["ports"])))

    for i, m in enumerate(left):
        block(m, i, "L")
    for i, m in enumerate(right):
        block(m, i, "R")
    if not mods:
        out.append('<text x="%d" y="%d" font-size="13" fill="%s" text-anchor="middle">%s</text>'
                   % (W / 2, by + bh + 40, t["muted"], _esc(_wiring.EMPTY)))
    # legend
    ly = H - 40
    lx = 24
    for k, word in (("i2c", "I2C"), ("spi", "SPI"), ("i2s", "I2S audio"), ("uart", "UART"),
                    ("digital", "digital / PWM / LED data"), ("power", "power")):
        out.append('<rect x="%d" y="%d" width="14" height="4" fill="%s"/>' % (lx, ly - 4, t[k]))
        out.append('<text x="%d" y="%d" font-size="11" fill="%s">%s</text>'
                   % (lx + 20, ly, t["muted"], word))
        lx += 34 + 7 * len(word)
    out.append('<text x="%d" y="%d" font-size="11" fill="%s">dashed = by cable</text>'
               % (lx, ly, t["muted"]))
    out.append('<text x="24" y="%d" font-size="10" fill="%s">%s</text>'
               % (H - 16, t["muted"], _esc(LINE_AB_NOTE)))
    out.append("</svg>")
    return "\n".join(out) + "\n"


def _cut(s, n):
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def power_tree_svg(r, theme="light"):
    """Supply -> board rails -> loads, with the budget figures."""
    t = THEMES.get(theme, THEMES["light"])
    b = r["budget"]
    rows = b["rows"]
    W, rh = 900, 34
    H = 150 + rh * len(rows) + 40
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'font-family="Helvetica, Arial, sans-serif">' % (W, H, W, H),
           '<rect width="%d" height="%d" fill="%s"/>' % (W, H, t["bg"])]
    out.append('<text x="24" y="34" font-size="18" font-weight="700" fill="%s">%s</text>'
               % (t["fg"], _esc((r["project"] or "Design") + " – power")))
    out.append('<text x="24" y="56" font-size="12" fill="%s">%s</text>'
               % (t["muted"], _esc(budget_line(b))))
    # supply box
    out.append('<rect x="24" y="80" width="230" height="46" rx="8" fill="%s" stroke="%s"/>'
               % (t["box"], t["power"]))
    out.append('<text x="36" y="100" font-size="12" font-weight="700" fill="%s">%s</text>'
               % (t["fg"], _esc(_cut(b["supply_words"], 32))))
    out.append('<text x="36" y="117" font-size="11" fill="%s">5 V, up to %s mA</text>'
               % (t["muted"], _n(b["supply_ma"])))
    # bar
    bw = 560
    out.append('<rect x="300" y="92" width="%d" height="18" rx="9" fill="%s"/>' % (bw, t["line"]))
    share = min(b["share"], 1.2)
    col = {"over": t["power"], "tight": t["uart"]}.get(b["status"], t["digital"])
    out.append('<rect x="300" y="92" width="%d" height="18" rx="9" fill="%s"/>'
               % (max(4, int(bw * min(share, 1.0))), col))
    out.append('<line x1="%d" y1="86" x2="%d" y2="116" stroke="%s" stroke-dasharray="3 3"/>'
               % (300 + bw * MARGIN, 300 + bw * MARGIN, t["fg"]))
    out.append('<text x="%d" y="132" font-size="10" fill="%s" text-anchor="middle">80 %%</text>'
               % (300 + bw * MARGIN, t["muted"]))
    y = 160
    mx = max([r_["ma"] or 0 for r_ in rows] + [1])
    for row in rows:
        out.append('<line x1="139" y1="126" x2="139" y2="%d" stroke="%s"/>' % (y + 10, t["line"]))
        out.append('<line x1="139" y1="%d" x2="160" y2="%d" stroke="%s"/>'
                   % (y + 10, y + 10, t["line"]))
        out.append('<text x="168" y="%d" font-size="12" fill="%s">%s</text>'
                   % (y + 14, t["fg"], _esc(_cut(row["name"], 30))))
        if row["ma"] is not None:
            w_ = int(300 * row["ma"] / mx)
            out.append('<rect x="420" y="%d" width="%d" height="12" rx="3" fill="%s"/>'
                       % (y + 4, max(2, w_), t["i2c"] if row["source"] == SRC_YOU else t["muted"]))
            out.append('<text x="%d" y="%d" font-size="11" fill="%s">%s mA · %s</text>'
                       % (428 + w_, y + 14, t["fg"], _n(row["ma"]), _esc(row["source"])))
        else:
            out.append('<text x="420" y="%d" font-size="11" fill="%s">%s</text>'
                       % (y + 14, t["muted"], _esc(_cut(row["why"], 60))))
        y += rh
    out.append("</svg>")
    return "\n".join(out) + "\n"


LEVEL_WORDS = {"error": "Error", "warning": "Warning", "note": "Note"}


def markdown(r):
    """The whole report as markdown (the PDF and the product pack use it)."""
    L = ["# %s – electrical" % (r["project"] or "Design"), ""]
    if r["made"]:
        L += ["Made from the design on %s. Not tested on hardware." % r["made"], ""]
    L += ["**%s**" % r["verdict"]["text"], ""]
    if r["rules"]:
        L += ["## Rule checks", ""]
        for x in r["rules"]:
            L.append("- **%s.** %s%s" % (LEVEL_WORDS[x["level"]], x["text"],
                                         (" *Fix:* " + x["fix"]) if x["fix"] else ""))
        L.append("")
    L += ["## Modules", "", "| Port | Module | Chip | Signal | Lines (Atech SDK) | Connection |",
          "|---|---|---|---|---|---|"]
    for m in r["modules"]:
        roles = role_words(m)
        L.append("| %s | %s | %s | %s | %s | %s |" % (
            _ports(m["ports"]), m["name"], m["chip"], m["signal"], roles or "–",
            "cable" if m["how"] == "cable" else "plugged in"))
    L += ["", "## Power", "", budget_line(r["budget"]), "",
          "| Load | mA | Source |", "|---|---|---|"]
    for row in r["budget"]["rows"]:
        L.append("| %s | %s | %s |" % (row["name"], _n(row["ma"]) if row["ma"] is not None
                                        else "–", row["source"] or row["why"]))
    if r["budget"].get("bank_hours"):
        L += ["", "On a %s mAh power bank: about %s h at full load." % (
            _n(r["budget"]["bank_mah"]), r["budget"]["bank_hours"])]
    L += ["", "## Bring-up", ""]
    for sec in r["bringup"]:
        L += ["### " + sec["title"], ""]
        L += ["%d. %s" % (i, s) for i, s in enumerate(sec["steps"], 1)]
        L.append("")
    L += ["## Firmware (%s)" % r["firmware"]["sdk"], "", "```yaml",
          r["firmware"]["yaml"].rstrip(), "```", ""]
    if r["unknown"]:
        L += ["## Not known yet", ""] + ["- " + u for u in r["unknown"]] + \
             ["- " + LINE_AB_NOTE, "", _wiring.PINOUT_ASK, ""]
    return "\n".join(L)


def check_line(r):
    """The one ./check line: `ELECTRICAL 0 errors, 2 warnings, 3 notes (…)`."""
    c = {k: sum(x["level"] == k for x in r["rules"]) for k in LEVELS}
    return ("ELECTRICAL %d error%s, %d warning%s, %d note%s; power: %s"
            % (c["error"], "" if c["error"] == 1 else "s",
               c["warning"], "" if c["warning"] == 1 else "s",
               c["note"], "" if c["note"] == 1 else "s", budget_line(r["budget"])))
