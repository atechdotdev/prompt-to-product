"""print_plates - Print: the design straight to a Bambu Lab printer (R920).

    R920  Print button: the view bar's Print opens a chooser - "Print on
          Bambu Lab" (recommended when Bambu Studio is installed), "Export
          a file..." (export_tools.ExportDialog) and "Get it made by Atech"
          (print_order) (PrintDialog).
    R921  printer profile: the printer, filament and process Bambu Studio
          has selected (BambuStudio.conf "presets" - only those keys are
          read, never the account or access code), resolved through the
          system presets' "inherits" chain for the bed size
          (bambu_profile).
    R922  print plates: every printed part laid on its largest flat side
          (export_tools.export_for_print, scope "parts"), checked against
          the bed (turned 90 deg when that fits), then Bambu Studio's own
          command line arranges them onto as many plates as they need and
          slices every plate (--arrange 1 --slice 0). A part that needs
          supports turns on tree supports (a user process that inherits
          the selected one). The result is a Bambu project 3MF with the
          plates already sliced (make_plates).
    R923  open in Bambu Studio: the sliced project opens in Bambu Studio,
          where Print sends it to the printer over the user's own Bambu
          account or LAN - Bambu Lab has no public API for sending a job,
          so Prompt To Product never talks to the printer itself (open_project).
    R924  print log: each print run is a folder in ~/Documents/Atech
          Prints/<design>/<time>/ with the parts, the sliced project and
          print.json (profile, plates, time, filament, flags), so how the
          print came out can be matched to what was sent (print_log).

make_plates runs headless (freecadcmd); only PrintDialog imports Qt.
"""
import json
import math
import os
import subprocess
import sys
import time

from . import export_tools as et

APP_BUNDLES = ("BambuStudio.app", "Bambu Studio.app")
APP_ROOTS = ("/Applications", os.path.expanduser("~/Applications"))
SUPPORT_DIR = os.path.expanduser("~/Library/Application Support/BambuStudio")
PRINTS_DIR = os.path.expanduser("~/Documents/Atech Prints")
ENV_PRINTS = "ATECH_PRINTS_DIR"

#: what is used when Bambu Studio has no printer selected yet
DEFAULT_MACHINE = "Bambu Lab X1 Carbon 0.4 nozzle"
#: mm kept clear round a part on the bed (Bambu's own arrange keeps ~6)
BED_MARGIN = 6.0
#: g of 1.75 mm filament per metre, per g/cm3 of density
G_PER_M_PER_DENSITY = math.pi * 0.0875 ** 2 * 100.0
SLICE_TIMEOUT_S = 900


def _log(msg):
    et._log("print: %s" % msg)


# ===================================================================
# R921 Bambu Studio and its profile
# ===================================================================
def bambu_studio(roots=APP_ROOTS):
    """The Bambu Studio app bundle, or None."""
    for r in roots:
        for b in APP_BUNDLES:
            p = os.path.join(r, b)
            if os.path.isdir(p):
                return p
    return None


#: R1041 Bambu Connect: Bambu's own bridge from other apps to the printer
#: (wiki.bambulab.com/en/software/bambu-connect). It takes a sliced file
#: through its URL scheme and sends it to the printer it is bound to.
CONNECT_BUNDLES = ("Bambu Connect.app", "BambuConnect.app")
CONNECT_DOWNLOAD = "https://wiki.bambulab.com/en/software/bambu-connect"


def bambu_connect(roots=APP_ROOTS):
    """The Bambu Connect app bundle, or None."""
    for r in roots:
        for b in CONNECT_BUNDLES:
            p = os.path.join(r, b)
            if os.path.isdir(p):
                return p
    return None


def connect_url(path, name, version="1.0.0"):
    """bambu-connect://import-file?path=...&name=...&version=... (every
    value encodeURIComponent-encoded, as the wiki asks)."""
    from urllib.parse import quote
    return "bambu-connect://import-file?path=%s&name=%s&version=%s" % (
        quote(os.path.abspath(path), safe=""), quote(name, safe=""), quote(version, safe=""))


def send_to_connect(project, name=None, runner=None):
    """Hand the sliced project to Bambu Connect. Its file is named
    <name>.gcode.3mf (a copy next to it when it is not). Returns the URL."""
    if not project.endswith(".gcode.3mf"):
        gp = project[:-len(".3mf")] + ".gcode.3mf" if project.endswith(".3mf") \
            else project + ".gcode.3mf"
        import shutil
        shutil.copyfile(project, gp)
        project = gp
    name = name or os.path.basename(project)[:-len(".gcode.3mf")]
    url = connect_url(project, name)
    (runner or (lambda c: subprocess.Popen(c)))(["open", url])
    return url


def bambu_cli(app):
    return os.path.join(app, "Contents", "MacOS", "BambuStudio")


def _system_dir(support_dir):
    return os.path.join(support_dir, "system", "BBL")


def _preset_path(support_dir, kind, name):
    p = os.path.join(_system_dir(support_dir), kind, name + ".json")
    return p if os.path.isfile(p) else None


def resolve_preset(support_dir, kind, name):
    """The preset's settings with its "inherits" chain applied (child
    wins), or {} when it is not a system preset."""
    chain, seen = [], set()
    while name and name not in seen:
        seen.add(name)
        p = _preset_path(support_dir, kind, name)
        if not p:
            break
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        chain.append(d)
        name = d.get("inherits")
    out = {}
    for d in reversed(chain):
        out.update(d)
    return out


def _bed(machine):
    """(width, depth, height) mm of a resolved machine preset."""
    xs, ys = [], []
    for pt in machine.get("printable_area") or []:
        try:
            x, y = str(pt).split("x")
            xs.append(float(x))
            ys.append(float(y))
        except ValueError:
            continue
    h = machine.get("printable_height")
    if not xs:
        return None
    return (max(xs) - min(xs), max(ys) - min(ys), float(h) if h else 250.0)


def _first(v):
    if isinstance(v, list):
        return v[0] if v else None
    return v


def bambu_profile(support_dir=SUPPORT_DIR):
    """{"machine", "process", "filament" (preset names), their system files,
    "model" ("Bambu Lab H2S"), "bed" (w, d, h) mm, "density", "picked"
    (True when Bambu Studio had them selected)} or None when Bambu Studio
    has never been set up. Only BambuStudio.conf's "presets" are read."""
    picked = {}
    try:
        with open(os.path.join(support_dir, "BambuStudio.conf"), encoding="utf-8") as fh:
            picked = json.load(fh).get("presets") or {}
    except (OSError, ValueError) as exc:
        _log("BambuStudio.conf: %r" % (exc,))
    machine_name = picked.get("machine")
    if not machine_name or not _preset_path(support_dir, "machine", machine_name):
        machine_name = DEFAULT_MACHINE
    if not _preset_path(support_dir, "machine", machine_name):
        return None
    machine = resolve_preset(support_dir, "machine", machine_name)
    process_name = picked.get("print")
    if not process_name or not _preset_path(support_dir, "process", process_name):
        process_name = _first(machine.get("default_print_profile"))
    filament_name = _first(picked.get("filaments")) or picked.get("filament")
    if not filament_name or not _preset_path(support_dir, "filament", filament_name):
        filament_name = _first(machine.get("default_filament_profile"))
    if not (process_name and _preset_path(support_dir, "process", process_name)):
        return None
    if not (filament_name and _preset_path(support_dir, "filament", filament_name)):
        return None
    filament = resolve_preset(support_dir, "filament", filament_name)
    try:
        density = float(_first(filament.get("filament_density")) or et.PLA_DENSITY)
    except (TypeError, ValueError):
        density = et.PLA_DENSITY
    return {"machine": machine_name, "process": process_name, "filament": filament_name,
            "machine_file": _preset_path(support_dir, "machine", machine_name),
            "process_file": _preset_path(support_dir, "process", process_name),
            "filament_file": _preset_path(support_dir, "filament", filament_name),
            "model": machine.get("printer_model") or machine_name,
            "bed": _bed(machine) or (256.0, 256.0, 256.0),
            "density": density,
            "picked": machine_name == picked.get("machine")}


def printer_name(profile):
    """'Bambu Lab H2S' -> 'H2S' for buttons."""
    m = (profile or {}).get("model") or "Bambu Lab"
    return m[len("Bambu Lab "):] if m.startswith("Bambu Lab ") else m


# ===================================================================
# R922 plates
# ===================================================================
def fits_bed(size, bed, margin=BED_MARGIN):
    """(fits, turned): a laid-flat part of size (x, y, z) on the bed,
    as it lies or turned 90 deg about Z."""
    w, d, h = bed[0] - 2 * margin, bed[1] - 2 * margin, bed[2]
    x, y, z = size
    if z > h:
        return False, False
    if x <= w and y <= d:
        return True, False
    if y <= w and x <= d:
        return True, True
    return False, False


def supports_process(profile, out_dir):
    """A user process that is the selected one with tree supports on."""
    name = "%s - Atech supports" % profile["process"]
    d = {"type": "process", "name": name, "inherits": profile["process"], "from": "User",
         "compatible_printers": [profile["machine"]], "print_settings_id": name,
         "enable_support": "1", "support_type": "tree(auto)"}
    p = os.path.join(out_dir, "process_supports.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1)
    return p


def slice_command(app, profile, parts, out_dir, project_name, process_file=None):
    return [bambu_cli(app), "--orient", "0", "--arrange", "1",
            "--load-settings", "%s;%s" % (profile["machine_file"],
                                          process_file or profile["process_file"]),
            "--load-filaments", profile["filament_file"],
            "--slice", "0", "--outputdir", out_dir,
            "--export-3mf", project_name] + list(parts)


def read_result(out_dir, density=et.PLA_DENSITY):
    """Bambu Studio's result.json -> {"ok", "error", "plates": [{"id",
    "seconds", "parts", "warning", "metres", "grams"}], "seconds",
    "grams"}. Filament use comes from the project's slice_info (the CLI
    leaves grams at 0, so they are worked out from the metres)."""
    p = os.path.join(out_dir, "result.json")
    try:
        with open(p, encoding="utf-8") as fh:
            r = json.load(fh)
    except (OSError, ValueError):
        return {"ok": False, "error": "Bambu Studio wrote no result.", "plates": [],
                "seconds": 0, "grams": 0}
    plates = []
    for pl in r.get("sliced_plates") or []:
        plates.append({"id": int(pl.get("id", len(plates) + 1)),
                       "seconds": float(pl.get("total_predication") or 0),
                       "parts": [o.get("name") for o in pl.get("objects") or []],
                       "warning": pl.get("warning_message") or "",
                       "metres": 0.0, "grams": 0.0})
    return {"ok": int(r.get("return_code", -1)) == 0 and bool(plates),
            "error": "" if int(r.get("return_code", -1)) == 0 else
            (r.get("error_string") or "slicing failed"),
            "plates": plates, "seconds": sum(p["seconds"] for p in plates), "grams": 0.0}


def _filament_use(project, plates, density):
    """Fill each plate's metres and grams from Metadata/slice_info.config."""
    import re
    import zipfile
    try:
        with zipfile.ZipFile(project) as z:
            info = z.read("Metadata/slice_info.config").decode("utf-8", "replace")
    except (OSError, KeyError, zipfile.BadZipFile):
        return
    by_id = {p["id"]: p for p in plates}
    for block in info.split("<plate>")[1:]:
        m = re.search(r'key="index" value="(\d+)"', block)
        if not m or int(m.group(1)) not in by_id:
            continue
        metres = sum(float(x) for x in re.findall(r'used_m="([\d.]+)"', block))
        pl = by_id[int(m.group(1))]
        pl["metres"] = round(metres, 2)
        pl["grams"] = round(metres * G_PER_M_PER_DENSITY * density, 1)


def prints_dir():
    return os.path.abspath(os.path.expanduser(os.environ.get(ENV_PRINTS) or PRINTS_DIR))


def run_folder(doc, root=None):
    base = et.safe_name(getattr(doc, "Label", "") or "design")
    folder = os.path.join(root or prints_dir(), base, time.strftime("%Y-%m-%d %H.%M.%S"))
    os.makedirs(folder, exist_ok=True)
    return folder


def export_parts(doc, folder, include_atech=False):
    """Step 1 (needs FreeCAD, main thread): every visible printed part
    laid flat, one STL each, and the printability rows.
    -> {"folder", "files", "parts", "rows", "needs_supports", "left_out",
        "skipped", "volumes"}."""
    # one STL per part: Bambu Studio names each object after its file
    res = et.export_for_print(doc, os.path.join(folder, "parts"), fmt="STL", scope="parts",
                              include_atech=include_atech, lay_flat=True)
    objs, _left = et.export_targets(doc, "parts", None, include_atech)
    rows = []
    try:
        rows = et.print_report([o for o in objs if not et._is_mesh(o)], walls=False)
    except Exception as exc:                              # noqa: BLE001
        _log("print report: %r" % (exc,))
    return {"folder": folder, "files": res["files"], "parts": res["parts"], "rows": rows,
            "left_out": res["left_out"], "skipped": res["skipped"],
            "volumes": res["volumes"],
            "needs_supports": [r["label"] for r in rows
                               if any("supports" in f for f in r["flags"])]}


def mesh_sizes(files):
    """{file: (x, y, z) mm} of exported STLs (headless: FreeCAD's Mesh)."""
    import Mesh
    out = {}
    for f in files:
        bb = Mesh.Mesh(f).BoundBox
        out[f] = (bb.XLength, bb.YLength, bb.ZLength)
    return out


def missing_parts(files, plates):
    """Labels of exported part files that are on no sliced plate."""
    placed = {os.path.splitext(os.path.basename(n or ""))[0]
              for p in plates for n in p.get("parts") or []}
    return [lab for lab in (os.path.splitext(os.path.basename(f))[0] for f in files)
            if lab not in placed]


def slice_plates(exported, profile, app, runner=None, project_name=None):
    """Step 2 (no FreeCAD; may run on a worker thread): Bambu Studio
    arranges the parts onto plates and slices them. -> the result dict of
    read_result plus "project" (the sliced .3mf), "command", "log"."""
    folder = exported["folder"]
    out_dir = os.path.join(folder, "sliced")
    os.makedirs(out_dir, exist_ok=True)
    name = project_name or (os.path.basename(os.path.dirname(folder)) + ".3mf")
    proc_file = (supports_process(profile, folder) if exported.get("needs_supports")
                 else None)
    cmd = slice_command(app, profile, exported["files"], out_dir, name, proc_file)
    log_path = os.path.join(folder, "slicer.log")
    if runner is not None:
        runner(cmd, out_dir, log_path)
    else:
        with open(log_path, "w", encoding="utf-8") as log:
            subprocess.run(cmd, cwd=out_dir, stdout=log, stderr=subprocess.STDOUT,
                           timeout=SLICE_TIMEOUT_S, check=False)
    res = read_result(out_dir, profile["density"])
    # R941: Bambu Studio's arrange leaves a part it cannot place off every
    # plate and still reports success (measured: A1 mini dropped the head
    # and torso of a 15-part robot). Every exported part must be on a plate.
    res["missing"] = missing_parts(exported["files"], res["plates"])
    if res["ok"] and res["missing"]:
        res.update(ok=False, error="Bambu Studio could not fit %s on the %s's plates. "
                   "Split the part (Edit part > Split) or scale it down."
                   % (", ".join(res["missing"]), printer_name(profile)))
    project = os.path.join(out_dir, name)
    if res["ok"] and not os.path.isfile(project):
        res.update(ok=False, error="Bambu Studio sliced but saved no project.")
    if res["ok"]:
        _filament_use(project, res["plates"], profile["density"])
        res["grams"] = round(sum(p["grams"] for p in res["plates"]), 1)
    res.update(project=project, command=cmd, log=log_path, supports=bool(proc_file))
    return res


def print_log(exported, profile, sliced, sizes=None):
    """R924: print.json in the run folder."""
    data = {"design_folder": exported["folder"], "made": time.strftime("%Y-%m-%d %H:%M:%S"),
            "printer": profile and profile["machine"], "process": profile and profile["process"],
            "filament": profile and profile["filament"], "bed_mm": profile and profile["bed"],
            "parts": exported["parts"], "left_out": exported["left_out"],
            "needs_supports": exported["needs_supports"],
            "supports_on": bool(sliced and sliced.get("supports")),
            "flags": {r["label"]: r["flags"] for r in exported["rows"] if r["flags"]},
            "sizes_mm": {os.path.basename(k): [round(c, 1) for c in v]
                         for k, v in (sizes or {}).items()},
            "plates": sliced and sliced["plates"], "ok": bool(sliced and sliced["ok"]),
            "error": sliced and sliced.get("error"),
            "project": sliced and sliced.get("project"),
            "how_it_printed": ""}
    p = os.path.join(exported["folder"], "print.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    return p


def make_plates(doc, profile=None, app=None, root=None, include_atech=False, runner=None):
    """R922 headless, all steps: export, bed check, slice, log.
    -> {"ok", "error", "folder", "project", "plates", "seconds", "grams",
        "exported", "too_big", "log"}."""
    app = app or bambu_studio()
    profile = profile or bambu_profile()
    if not app or not profile:
        return {"ok": False, "error": "Bambu Studio is not installed or not set up: "
                "open it once and pick your printer.", "plates": []}
    exported = export_parts(doc, run_folder(doc, root), include_atech)
    sizes = mesh_sizes(exported["files"])
    too_big = [os.path.splitext(os.path.basename(f))[0] for f, s in sizes.items()
               if not fits_bed(s, profile["bed"])[0]]
    if too_big:
        sliced = {"ok": False, "plates": [], "error": "Too big for the %s's %d x %d x %d mm "
                  "bed: %s. Split the part (Edit part > Split) or scale it down."
                  % ((printer_name(profile),) + tuple(int(b) for b in profile["bed"])
                     + (", ".join(too_big),))}
    else:
        sliced = slice_plates(exported, profile, app, runner)
    log = print_log(exported, profile, sliced, sizes)
    out = dict(sliced)
    out.update(folder=exported["folder"], exported=exported, too_big=too_big, log=log,
               profile=profile)
    return out


def open_project(project, app=None, runner=None):
    """R923: the sliced project in Bambu Studio (`open -a`)."""
    cmd = ["open", "-a", app or bambu_studio() or "BambuStudio", project]
    (runner or (lambda c: subprocess.Popen(c)))(cmd)
    return cmd


def summary(res):
    """One or two plain sentences about a make_plates result."""
    if not res.get("ok"):
        return res.get("error") or "Slicing failed."
    n = len(res["plates"])
    h, m = divmod(int(round(res["seconds"] / 60.0)), 60)
    t = ("%d h %02d min" % (h, m)) if h else ("%d min" % m)
    bits = ["%d plate%s, about %s and %.0f g of %s." % (
        n, "" if n == 1 else "s", t, res["grams"],
        (res.get("profile") or {}).get("filament", "filament").split(" @")[0])]
    if res.get("supports"):
        bits.append("Tree supports are on for %s." % ", ".join(
            (res.get("exported") or {}).get("needs_supports") or ["some parts"]))
    warn = [p["warning"] for p in res["plates"] if p["warning"]]
    if warn:
        bits.append("Bambu Studio says: %s" % " ".join(warn))
    return " ".join(bits)


# ===================================================================
# R920 the Print chooser
# ===================================================================
def PrintDialog(parent=None, doc_fn=None, selection_fn=None, app_fn=bambu_studio,
                profile_fn=bambu_profile, opener=None, connect_fn=bambu_connect):
    """Print: Bambu Lab (plates, slice, open in Bambu Studio), Export a
    file..., Get it made by Atech."""
    from PySide6 import QtCore, QtWidgets
    doc_fn = doc_fn or et._active_doc
    selection_fn = selection_fn or et._selected

    d = et._tool_dialog(QtWidgets.QDialog, parent, "Print")
    lay = QtWidgets.QVBoxLayout(d)
    lay.setContentsMargins(20, 18, 20, 18)
    lay.setSpacing(10)
    t = QtWidgets.QLabel("Print", d)
    t.setObjectName("ToolTitle")
    lay.addWidget(t)

    app, profile = app_fn(), None
    try:
        profile = profile_fn() if app else None
    except Exception as exc:                              # noqa: BLE001
        _log("profile: %r" % (exc,))
    d.app, d.profile, d.result = app, profile, None

    def card(title, text, button, primary=False):
        box = QtWidgets.QFrame(d)
        box.setObjectName("ToolCard")
        v = QtWidgets.QVBoxLayout(box)
        v.setContentsMargins(14, 12, 14, 12)
        h = QtWidgets.QLabel(title, box)
        h.setObjectName("ToolTitle" if primary else "")
        h.setStyleSheet("font-weight: 600;")
        v.addWidget(h)
        lab = QtWidgets.QLabel(text, box)
        lab.setObjectName("ToolMuted")
        lab.setWordWrap(True)
        v.addWidget(lab)
        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        b = QtWidgets.QPushButton(button, box)
        b.setAccessibleName(button)
        if primary:
            b.setObjectName("ToolPrimary")
            b.setDefault(True)
        row.addWidget(b)
        v.addLayout(row)
        lay.addWidget(box)
        return b, lab

    if app and profile:
        bed = tuple(int(x) for x in profile["bed"])
        what = ("Lays every part flat, fills as many %s plates (%d x %d mm) as it needs, "
                "slices them with %s and %s, and opens the project in Bambu Studio: "
                "press Print there." % ((printer_name(profile),) + bed[:2]
                                        + (profile["process"].split(" @")[0],
                                           profile["filament"].split(" @")[0])))
        d.btn_bambu, d.bambu_text = card("Print on Bambu Lab %s (recommended)"
                                         % printer_name(profile), what,
                                         "Make plates and open Bambu Studio", True)
    else:
        d.btn_bambu, d.bambu_text = card(
            "Print on Bambu Lab",
            "Install Bambu Studio (bambulab.com/download), open it once and pick your "
            "printer: Prompt To Product then makes the plates and slices them for you.",
            "Get Bambu Studio")
    d.atech = QtWidgets.QCheckBox("Include the Atech board, modules and cables "
                                  "(CC BY-NC models)", d)
    d.atech.setAccessibleName("Include the Atech board, modules and cables")
    lay.addWidget(d.atech)
    d.btn_export, _ = card("Export a file",
                           "STL, 3MF or STEP for any slicer, whole or one file per part.",
                           "Export...")
    d.btn_atech, _ = card("No printer?",
                          "Atech prints it for you: one 3D print voucher per print.",
                          "Get it made by Atech...")
    d.status = QtWidgets.QLabel("", d)
    d.status.setObjectName("ToolMuted")
    d.status.setWordWrap(True)
    lay.addWidget(d.status)
    open_row = QtWidgets.QHBoxLayout()
    open_row.addStretch(1)
    d.btn_folder = QtWidgets.QPushButton("Show files", d)
    d.btn_folder.setVisible(False)
    open_row.addWidget(d.btn_folder)
    # R1041: straight to the printer, through Bambu Connect (when installed)
    d.connect_app = connect_fn()
    d.btn_send = QtWidgets.QPushButton("Send to printer", d)
    d.btn_send.setToolTip("Sends the sliced plates to your printer through Bambu "
                          "Connect, without opening Bambu Studio")
    d.btn_send.setAccessibleName("Send to printer with Bambu Connect")
    d.btn_send.setVisible(False)
    open_row.addWidget(d.btn_send)
    d.btn_open = QtWidgets.QPushButton("Open in Bambu Studio", d)
    d.btn_open.setObjectName("ToolPrimary")
    d.btn_open.setVisible(False)
    open_row.addWidget(d.btn_open)
    lay.addLayout(open_row)

    keep = {}

    def export():
        keep["export"] = et.ExportDialog(d.window(), doc_fn, selection_fn)
        keep["export"].show()
        return keep["export"]

    def made():
        from . import print_order
        keep["order"] = print_order.OrderDialog(d.window(), doc_fn)
        keep["order"].show()
        return keep["order"]

    def say(text):
        d.status.setText(text)
        QtWidgets.QApplication.processEvents()

    def finish(res):
        d.result = res
        d.btn_bambu.setEnabled(True)
        say(summary(res))
        d.btn_folder.setVisible(bool(res.get("folder")))
        if res.get("ok"):
            d.btn_open.setVisible(True)
            d.btn_send.setVisible(bool(d.connect_app))
            open_project(res["project"], app, opener)
            say(summary(res) + " Opened in Bambu Studio: check the plates, then Print%s."
                % (" (or Send to printer: Bambu Connect)" if d.connect_app else ""))

    def bambu():
        if not (app and profile):
            from PySide6 import QtGui
            QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://bambulab.com/en/download/studio"))
            return None
        doc = doc_fn()
        if doc is None:
            say("Open a design first: there is nothing to print.")
            return None
        d.btn_bambu.setEnabled(False)
        d.btn_open.setVisible(False)
        say("Laying the parts flat...")
        try:
            exported = export_parts(doc, run_folder(doc), d.atech.isChecked())
            sizes = mesh_sizes(exported["files"])
        except Exception as exc:                          # noqa: BLE001
            d.btn_bambu.setEnabled(True)
            say("Could not lay the parts out: %s" % exc)
            return None
        too_big = [os.path.splitext(os.path.basename(f))[0] for f, s in sizes.items()
                   if not fits_bed(s, profile["bed"])[0]]
        base = {"folder": exported["folder"], "exported": exported, "too_big": too_big,
                "profile": profile}
        if too_big:
            res = dict(base, ok=False, plates=[], error=(
                "Too big for the %s bed: %s. Split it (Edit part > Split) or scale it down."
                % (printer_name(profile), ", ".join(too_big))))
            print_log(exported, profile, res, sizes)
            finish(res)
            return res
        say("Bambu Studio is filling and slicing the plates (%d part%s)..." % (
            len(exported["files"]), "" if len(exported["files"]) == 1 else "s"))
        import threading
        box = {}

        def work():
            try:
                box["res"] = slice_plates(exported, profile, app)
            except Exception as exc:                      # noqa: BLE001
                box["res"] = {"ok": False, "plates": [], "error": "Slicing failed: %s" % exc}

        th = threading.Thread(target=work, daemon=True)
        th.start()
        timer = QtCore.QTimer(d)

        def poll():
            if th.is_alive():
                return
            timer.stop()
            res = dict(base, **box["res"])
            print_log(exported, profile, res, sizes)
            finish(res)
        timer.timeout.connect(poll)
        timer.start(250)
        d._timer = timer
        return th

    def show_folder():
        if d.result and d.result.get("folder"):
            subprocess.Popen(["open", d.result["folder"]])

    d.btn_bambu.clicked.connect(lambda _=False: et._guard(bambu))
    d.btn_export.clicked.connect(lambda _=False: et._guard(export))
    d.btn_atech.clicked.connect(lambda _=False: et._guard(made))
    d.btn_open.clicked.connect(lambda _=False: d.result and open_project(
        d.result["project"], app, opener))
    d.btn_folder.clicked.connect(lambda _=False: show_folder())

    def send():
        if d.result and d.result.get("ok"):
            send_to_connect(d.result["project"], getattr(doc_fn(), "Label", None), opener)
            say("Sent to Bambu Connect: pick the printer there and start the print.")
    d.btn_send.clicked.connect(lambda _=False: et._guard(send))
    d.send = send
    d.bambu, d.export, d.made = bambu, export, made
    d.resize(560, 460)
    return d
