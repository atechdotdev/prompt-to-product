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
import re

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
#: how a note ends when the value was worked out from the snug puck
DERIVED_NOTE = " (follows the D-bore)"


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


#: filament kinds the Fit window offers
MATERIALS = ("PLA", "PETG", "PETG-CF", "ABS", "ASA", "TPU")
#: ... and every kind a preset's or a typed name is read for. A filled
#: filament is its own kind: PLA-CF is not PLA (R1295: it was read as PLA,
#: and PC, PA and PET-CF as nothing at all)
KINDS = MATERIALS + ("PLA-CF", "PLA-GF", "PETG-GF", "PET-CF", "PET-GF", "ABS-GF", "ASA-CF",
                     "ASA-GF", "PAHT-CF", "PA6-CF", "PA6-GF", "PA12-CF", "PA-CF", "PA-GF",
                     "PPA-CF", "PPA-GF", "PPS-CF", "PC-CF", "PCTG", "PC", "PA", "PVA",
                     "HIPS", "PPS", "PP", "PET")
#: values that are an interference, not a clearance: "too tight" makes
#: them SMALLER (R1295: 'tight' used to raise the hold-down rib's preload)
INTERFERENCE_KEYS = frozenset(("preload",))


def material_of(preset_name):
    """The filament kind in a preset's name ("Bambu PETG-CF @BBL H2S" ->
    "PETG-CF"), or ""."""
    name = str(preset_name or "").upper()
    for m in sorted(KINDS, key=len, reverse=True):
        # a whole word: "PA" is not in "PAHT-CF", nor "PC" in "PCTG"
        if re.search(r"(?<![A-Z0-9])%s(?![A-Z0-9])" % re.escape(m), name):
            return m
    return ""


def kind(material):
    """A material as it is compared: its filament kind ("PLA Basic" ->
    "PLA"), else the text itself in capitals."""
    return material_of(material) or _clean(material, "").upper()


def _clean(text, default):
    """One line without the profile separator (a printer called
    "X1C | office" would be split into the wrong printer and filament)."""
    return " ".join(str(text or "").replace("|", "/").split()) or default


def profile_name(printer, material):
    """ "<printer> | <filament kind>". A filament typed as Bambu names it
    ("PLA Basic") is stored as its kind, or no build would match it."""
    return "%s | %s" % (_clean(printer, "My printer"),
                        material_of(material) or _clean(material, "PLA"))


def match(data, printer, material):
    """The stored profile for this printer and filament, whatever the
    capitals ("x1c | pla" is "X1C | PLA"), or None."""
    want = profile_name(printer, material).upper()
    for name in data.get("profiles") or {}:
        if name.upper() == want:
            return name
    return None


def pick(data, printer=None, material=None):
    """The profile a build should use: the one for the filament that is
    loaded. With `material` known (Bambu Studio's selected filament), a
    profile of that filament - this printer's first, then the active one,
    then the only one - and None when there is none: results from PLA do
    not fit a PETG-CF print (Gustav keeps a set of sizes per material).
    Without it, the profile saved last ("active")."""
    profiles = data.get("profiles") or {}
    active = data.get("active") if data.get("active") in profiles else None
    want = kind(material)
    if not want:
        return active
    same = sorted(n for n, p in profiles.items() if kind(p.get("material")) == want)
    if not same:
        return None
    exact = match(data, printer, material) if printer else None
    if exact in same:
        return exact
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
        want = kind(material)
        same = sorted(n for n, p in data["profiles"].items()
                      if kind(p.get("material")) == want)
        if same:
            data["unused"] = ("you have print results for %s from more than one printer "
                              "(%s) and none is for this one - the table's values are used; "
                              "save the one to use in Export and share > Fit test"
                              % (want, ", ".join(same)))
        else:
            data["unused"] = ("none of your print results is for %s (you have: %s) - the "
                              "table's values are used; print the fit test in %s to get yours"
                              % (_clean(material, ""), ", ".join(sorted(data["profiles"])),
                                 _clean(material, "")))
    return data


def use_profile(data, printer, material):
    """Make the profile of this printer and filament the active one
    (created when new). Returns its name."""
    name = match(data, printer, material) or profile_name(printer, material)
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


def record(data, key, value, note="", date=None, derived=False):
    """Store the user's value for `key` in the active profile. Raises
    ValueError when atech_fit refuses it (not a fit value, wrong shape, too
    far from the table). `derived`: worked out from another result, not
    said by the person (it gives way to what they say). Returns the stored
    value."""
    _name, prof = _active(data)
    shaped = atech_fit.user_value(key, value)
    prof["values"][key] = {"value": _plain(shaped), "note": str(note or ""),
                           "date": date or _today()}
    if derived:
        prof["values"][key]["derived"] = True
    return shaped


def _is_derived(rec):
    return bool(rec.get("derived")) or str(rec.get("note") or "").endswith(DERIVED_NOTE)


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
    vals = _active(data)[1]["values"]
    for key in ("hole_shrink", "bearing_d3"):
        # R1295: what the person said themselves (a verdict on the turning
        # hole) is theirs; only a value an earlier puck derived follows
        if key in vals and not _is_derived(vals[key]):
            continue
        if abs(delta) < 1e-9:
            vals.pop(key, None)
            continue
        out[key] = record(data, key, round(atech_fit.table_value(key) + delta, 2),
                          note + DERIVED_NOTE, date, derived=True)
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
    by `by` (for a preload, "tight" means less of it). A clearance stops at
    0, and the note says so. Returns the stored value."""
    if how not in VERDICTS:
        raise ValueError("how it fitted: one of %s" % ", ".join(VERDICTS))
    by = abs(float(by))
    step = {"fits": 0.0, "tight": by, "loose": -by}[how]
    if key in INTERFERENCE_KEYS:
        step = -step
    now = current(data, key)
    moved = tuple(round(x + step, 2) for x in now) if isinstance(now, tuple) \
        else round(now + step, 2)
    # R1295: "too loose by 0.25" on a 0.2 clearance was refused outright
    # (below zero), and the whole Save with it
    new = tuple(max(0.0, x) for x in moved) if isinstance(moved, tuple) else max(0.0, moved)
    words = {"fits": "it fitted", "tight": "too tight by about %g" % by,
             "loose": "too loose by about %g" % by}[how]
    if new != moved:
        words += " (kept at 0: it cannot go below)"
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
    return FILE if _write_plain(dst, raw, 0o444) else None


def _write_plain(dst, raw, mode):
    """Put `raw` at `dst` as a plain file of `mode`, never through a link:
    a link or a folder planted at that name is removed first, the new file
    is made beside it (O_EXCL, O_NOFOLLOW) and moved into place. A file
    that already holds `raw` only gets its mode put right. True when the
    file was written (as build._write_if_changed, which the kit cannot
    import)."""
    import shutil
    if os.path.islink(dst):
        os.unlink(dst)
    elif os.path.isdir(dst):
        shutil.rmtree(dst)
    try:
        with open(dst, "rb") as fh:
            if fh.read() == raw:
                if (os.lstat(dst).st_mode & 0o777) != mode:
                    os.chmod(dst, mode)
                return False
    except OSError:
        pass
    tmp = dst + ".tmp"
    if os.path.lexists(tmp):
        if os.path.isdir(tmp) and not os.path.islink(tmp):
            shutil.rmtree(tmp)
        else:
            os.unlink(tmp)
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(raw)
        os.fchmod(fh.fileno(), mode)
    os.replace(tmp, dst)
    return True
