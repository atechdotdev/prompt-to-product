"""p2p_fitlog - what a print taught, kept as a number (R1240).

Gustav's cad-workflow gets its parts to fit because every print result goes
back into a parameter: "the 3.3 legs were super tight" became BORE_CLR 0.2.
This is that step for everybody. After a print the app asks how it fitted,
and the answer is stored per printer and filament in

    ~/Documents/Atech Products/fit_user.json     (beside prices.json)

    {"version": 1, "active": "Bambu X1C | PLA",
     "profiles": {"Bambu X1C | PLA": {
         "printer": "Bambu X1C", "material": "PLA",
         "values": {"dbore_d3": {"value": [3.5, 3.0], "date": "2026-11-27",
                                 "note": "fit test: puck 35 was snug"}}}}}

atech_fit.load_user() puts the active profile's values in place of the
table's (tag U), so the agent's prompt, cad.fit(), cad.d_bore() and
cad.wheel(flat=True) all follow on the next build. build.prepare_workspace
copies the file into each chat's folder: a design script cannot read the
home folder.

    coupon_result(data, "35")   the puck that was snug on the motor shaft
    gauge_result(data, "3")     the tightest window a module slid through
    verdict(data, key, "tight", 0.1)   "too tight by about 0.1"

Only the keys atech_fit.USER_KEYS can change, each number by at most
atech_fit.USER_SPAN from the table. Hardware sizes, ports and seat
tolerances are never touched.

Plain Python, no FreeCAD, no Qt.
"""
import datetime
import json
import os

import atech_fit

FILE = "fit_user.json"
HOME = os.path.join("~", "Documents", "Atech Products")
VERSION = 1
#: the fit coupon's pucks and windows (atech_detail.COUPON_BORES / _GAPS)
PUCKS = ("32", "33", "34", "35", "36")
WINDOWS = ("2", "3", "4")
#: what each key is, for the person
WORDS = {
    "dbore_d3": "D-bore that pushes onto the motor shaft (round / across the flat)",
    "bearing_d3": "hole a 3 mm shaft turns in",
    "hole_shrink": "how much a printed hole comes out under its drawn size",
    "slide": "clearance per side round hardware",
    "lip_loose": "lid lip, loose",
    "lip_friction": "lid lip, friction",
    "rotate": "printed pin turning in a hole (radial)",
    "press": "printed pin pressed in a printed hole",
    "stop": "stop wall to a module's face",
    "fence": "fence to the board's edge",
    "hole_z": "extra height of a hole across the bed",
    "preload": "hold-down rib into the spine",
}
VERDICTS = ("fits", "tight", "loose")


def folder(home=None):
    return os.path.expanduser(home or HOME)


def path(home=None):
    """The record's file: $ATECH_FIT_USER when set (tests, a second set of
    printers), else fit_user.json in the products folder."""
    env = os.environ.get("ATECH_FIT_USER")
    if env and home is None:
        return os.path.expanduser(env)
    return os.path.join(folder(home), FILE)


def empty():
    return {"version": VERSION, "active": None, "profiles": {}}


def load(home=None):
    """The fit record, always well formed: a missing or broken file is an
    empty record."""
    try:
        with open(path(home), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return empty()
    if not isinstance(data, dict) or not isinstance(data.get("profiles"), dict):
        return empty()
    out = empty()
    for name, prof in data["profiles"].items():
        if not isinstance(prof, dict):
            continue
        vals = prof.get("values")
        out["profiles"][str(name)] = {
            "printer": str(prof.get("printer") or ""),
            "material": str(prof.get("material") or ""),
            "values": {k: (v if isinstance(v, dict) else {"value": v})
                       for k, v in (vals if isinstance(vals, dict) else {}).items()},
        }
    if data.get("active") in out["profiles"]:
        out["active"] = data["active"]
    return out


def save(data, home=None):
    """Write the record (through a temporary file, so a crash leaves the
    old one). Returns its path."""
    os.makedirs(folder(home), exist_ok=True)
    p = path(home)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, p)
    return p


#: filament kinds a preset's name is read for, and the Fit window offers
MATERIALS = ("PLA", "PETG", "PETG-CF", "ABS", "ASA", "TPU")
#: values that are an interference, not a clearance: "too tight" makes
#: them SMALLER (R1295: 'tight' used to raise the hold-down rib's preload)
INTERFERENCE_KEYS = frozenset(("preload",))


def material_of(preset_name):
    """The filament kind in a preset's name ("Bambu PETG-CF @BBL H2S" ->
    "PETG-CF"), or ""."""
    name = str(preset_name or "").upper()
    for m in sorted(MATERIALS, key=len, reverse=True):
        if m in name:
            return m
    return ""


def _clean(text, default):
    """One line without the profile separator (a printer called
    "X1C | office" would be split into the wrong printer and filament)."""
    return " ".join(str(text or "").replace("|", "/").split()) or default


def profile_name(printer, material):
    return "%s | %s" % (_clean(printer, "My printer"), _clean(material, "PLA"))


def pick(data, printer=None, material=None):
    """The profile a build should use: the one for the filament that is
    loaded. With `material` known (Bambu Studio's selected filament), a
    profile of that filament - this printer's first, then the active one,
    then the only one - and None when there is none: results from PLA do
    not fit a PETG-CF print (Gustav keeps a set of sizes per material).
    Without it, the profile saved last ("active")."""
    profiles = data.get("profiles") or {}
    active = data.get("active") if data.get("active") in profiles else None
    want = _clean(material, "").upper()
    if not want:
        return active
    same = sorted(n for n, p in profiles.items()
                  if _clean(p.get("material"), "").upper() == want)
    if not same:
        return None
    exact = profile_name(printer, material) if printer else None
    for n in same:
        if exact and n.upper() == exact.upper():
            return n
    if active in same:
        return active
    return same[0] if len(same) == 1 else None


def effective(home=None, printer=None, material=None):
    """The record as a build reads it: the same profiles, "active" set to
    pick()'s choice (None: the table's own values)."""
    data = load(home)
    data["active"] = pick(data, printer, material)
    if data["active"] is None and data["profiles"] and _clean(material, ""):
        # said by ./check, so nobody wonders where their numbers went
        data["unused"] = ("none of your print results is for %s (you have: %s) - the "
                          "table's values are used; print the fit test in %s to get yours"
                          % (_clean(material, ""), ", ".join(sorted(data["profiles"])),
                             _clean(material, "")))
    return data


def use_profile(data, printer, material):
    """Make the profile of this printer and filament the active one
    (created when new). Returns its name."""
    name = profile_name(printer, material)
    prof = data["profiles"].setdefault(name, {"values": {}})
    prof.setdefault("values", {})
    prof["printer"], prof["material"] = name.split(" | ", 1)
    data["active"] = name
    return name


def _active(data):
    name = data.get("active")
    if name not in data.get("profiles", {}):
        raise ValueError("choose the printer and the filament first")
    return name, data["profiles"][name]


def _today():
    return datetime.date.today().isoformat()


def _plain(v):
    return list(v) if isinstance(v, tuple) else v


def record(data, key, value, note="", date=None):
    """Store the user's value for `key` in the active profile. Raises
    ValueError when atech_fit refuses it (not a fit value, wrong shape, too
    far from the table). Returns the stored value."""
    _name, prof = _active(data)
    shaped = atech_fit.user_value(key, value)
    prof["values"][key] = {"value": _plain(shaped), "note": str(note or ""),
                           "date": date or _today()}
    return shaped


def forget(data, key=None):
    """Drop one value of the active profile (or all of them): the table's
    value counts again."""
    _name, prof = _active(data)
    if key is None:
        prof["values"] = {}
    else:
        prof["values"].pop(key, None)


def current(data, key):
    """The value in force for `key`: the active profile's, else the
    table's."""
    name = data.get("active")
    rec = (data.get("profiles", {}).get(name) or {}).get("values", {}).get(key)
    if rec is not None:
        try:
            return atech_fit.user_value(key, rec.get("value"))
        except ValueError:
            pass
    return atech_fit.table_value(key)


def coupon_result(data, snug, date=None):
    """The fit coupon's puck that was snug and keyed on the motor shaft
    ("32" .. "36", or 3.2 .. 3.6). Its bore becomes this printer's D-bore;
    holes then shrink that much more or less than the table says, so the
    shrink and the hole a shaft turns in move by the same amount. Returns
    {key: value} of what was stored."""
    try:
        bore = float(snug)
    except (TypeError, ValueError):
        raise ValueError("which puck: one of %s" % ", ".join(PUCKS))
    if bore > 10:
        bore /= 10.0
    label = "%d" % round(bore * 10)
    if label not in PUCKS:
        raise ValueError("which puck: one of %s" % ", ".join(PUCKS))
    t_bore, t_across = atech_fit.table_value("dbore_d3")
    delta = round(bore - t_bore, 3)
    note = "fit test: puck %s was snug on the motor shaft" % label
    out = {"dbore_d3": record(data, "dbore_d3",
                              (round(bore, 2), round(t_across + delta, 2)), note, date)}
    derived = note + " (follows the D-bore)"
    for key in ("hole_shrink", "bearing_d3"):
        if abs(delta) < 1e-9:
            _active(data)[1]["values"].pop(key, None)
            continue
        out[key] = record(data, key, round(atech_fit.table_value(key) + delta, 2),
                          derived, date)
    return out


def gauge_result(data, window, date=None):
    """The tightest window of the module gauge a module still slid through
    ("2", "3" or "4": the clearance per side in tenths). Returns {"slide":
    value}."""
    label = str(window).strip()
    if label not in WINDOWS:
        raise ValueError("which window: one of %s" % ", ".join(WINDOWS))
    gap = int(label) / 10.0
    return {"slide": record(data, "slide", gap,
                            "fit test: a module slid through window %s" % label, date)}


def verdict(data, key, how, by=0.1, note="", date=None):
    """How a printed fit turned out: "fits" keeps the value in force as
    proven on this printer; "tight" opens it by `by` mm, "loose" closes it
    by `by` (for a preload, "tight" means less of it). Returns the stored
    value."""
    if how not in VERDICTS:
        raise ValueError("how it fitted: one of %s" % ", ".join(VERDICTS))
    by = abs(float(by))
    step = {"fits": 0.0, "tight": by, "loose": -by}[how]
    if key in INTERFERENCE_KEYS:
        step = -step
    now = current(data, key)
    new = tuple(round(x + step, 2) for x in now) if isinstance(now, tuple) \
        else round(now + step, 2)
    words = {"fits": "it fitted", "tight": "too tight by about %g" % by,
             "loose": "too loose by about %g" % by}[how]
    return record(data, key, new, (note + "; " if note else "") + words, date)


def rows(data):
    """[{"key", "what", "value", "table", "note", "date"}] of the active
    profile, for a window or a paper."""
    name = data.get("active")
    vals = (data.get("profiles", {}).get(name) or {}).get("values", {})
    out = []
    for key in sorted(vals):
        if key not in atech_fit.USER_KEYS:
            continue
        out.append({"key": key, "what": WORDS.get(key, key),
                    "value": vals[key].get("value"),
                    "table": _plain(atech_fit.table_value(key)),
                    "note": vals[key].get("note", ""), "date": vals[key].get("date", "")})
    return out


def _fmt(v):
    if isinstance(v, (list, tuple)):
        return " / ".join("%g" % x for x in v)
    return "%g" % v


def summary(data):
    """One line: whose numbers the next build uses."""
    got = rows(data)
    if not got:
        return "No print results yet: the table's values are used."
    return "%s: %s" % (data["active"], "; ".join(
        "%s %s (table %s)" % (r["key"], _fmt(r["value"]), _fmt(r["table"])) for r in got))


def to_workspace(workspace, home=None, printer=None, material=None):
    """Write the record into a chat's folder (read-only) as a build should
    read it (effective()). The file is ALWAYS there, empty when the person
    has no results: the sandbox protects only files that exist, and a
    design script could otherwise plant its own "print results" (R1295).
    Returns the file's name when it was written or changed."""
    dst = os.path.join(workspace, FILE)
    raw = (json.dumps(effective(home, printer, material), indent=1, sort_keys=True)
           + "\n").encode("utf-8")
    try:
        with open(dst, "rb") as fh:
            if fh.read() == raw:
                return None
    except OSError:
        pass
    try:
        os.chmod(dst, 0o644)
    except OSError:
        pass
    with open(dst, "wb") as fh:
        fh.write(raw)
    os.chmod(dst, 0o444)
    return FILE
