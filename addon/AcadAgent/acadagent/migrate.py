"""migrate — carry the addon's own data over from an earlier name once.

WHY THIS EXISTS
    FreeCAD keys the user-data folder on branding.xml's ExeName. The product
    was renamed from "Atech Studio" to "Atech Atelier" (ADR-005, owner
    decision 2026-10-03), from "Atech Atelier" to "Prompt To Product"
    (owner decision 2026-11-10) and to "Prompt2Product" (owner decision
    2026-11-16), so FreeCAD.getUserAppDataDir() moves from
        ~/.local/share/Prompt To Product/v1-1/   (or an older name's folder)
        ~/Library/Application Support/Prompt To Product/v1-1/   (macOS)
    to
        ~/.local/share/Prompt2Product/v1-1/
        ~/Library/Application Support/Prompt2Product/v1-1/
    and everything the addon kept under the old one would look lost. The
    newest earlier name that holds addon data is copied from (OLD_NAMES).

WHAT IS COPIED (and only this)
    AcadAgent/trusted_builds.json   the trust store (build._trust_path):
                                    which agent-built objects ran from a
                                    script the user accepted (R11)
    agent/sessions.json             the chat index (panel.sessions_path):
                                    document Uid -> chat folder + Claude
                                    session, so a reopened document continues
                                    its chat (S07)
    parts/                          the user's parts library (user_parts.py,
                                    R750: imported, shelf and SimReady parts)
    Macro/                          the user's FreeCAD macros
    The chat folders themselves are NOT copied: sessions.json stores absolute
    paths, and the old tree is never deleted, so the copied index keeps
    pointing at folders that still exist (panel._restore_state only checks
    os.path.isdir). An EMPTY folder in the new tree (FreeCAD makes Macro/ on
    its first start) counts as not there.

WHAT DOES NOT NEED IT
    The addon's settings file (settings.CONFIG_PATH, ~/.config/acadagent/
    settings.json: engine, model, budget, privacy acknowledgement) is not
    keyed on ExeName and does not move. Nor is the sign-in (account.SERVICE
    keeps its earlier Keychain name).

WHAT THE LAUNCHER DOES FIRST, AND WHY THIS STILL EXISTS
    The AppImage's AppRun (branding/apprun_migrate_block.sh) copies the
    whole old data and config trees before FreeCAD starts, but only when the
    new folder does not exist yet; it is also the only place FreeCAD's own
    preferences (user.cfg, read before any addon runs) can be carried over.
    The macOS bundle has no launcher script, so there this module is all
    the migration there is (FreeCAD's preferences start from the template).
    It also covers a new folder that already existed (FreeCAD created it on
    a start without that block - a dev launch, an image built before it)
    but holds none of the addon's data.
    ATECH_MIGRATE=0 turns this off too, as it does the AppRun block. After AppRun copied a tree this finds the addon data already in
    place and only records "skipped".

RULES
    - Copy, never move; the old tree is never modified or deleted.
    - Once: a marker file (MARKER, in <new>/AcadAgent/) records the outcome.
      A run that could not copy everything says "partial" and the next start
      retries only what is still missing.
    - If the new folder already holds addon data and there is no marker, the
      user has been working in the new folder: nothing is copied (an old file
      would overwrite newer state) and the marker says "skipped".
    - Never raises: a failed migration costs the user their old chats, never
      the start of the app.
"""
import json
import os
import shutil
import time

#: Earlier product names, newest first (ADR-005; 2026-11-10; 2026-11-16).
OLD_NAMES = ("Prompt To Product", "Atech Atelier", "Atech Studio")
OLD_NAME = OLD_NAMES[0]
MARKER = "migrated_from_previous_name.json"
ITEMS = (os.path.join("AcadAgent", "trusted_builds.json"),
         os.path.join("agent", "sessions.json"),
         "parts",
         "Macro")

DONE, PARTIAL, SKIPPED = "done", "partial", "skipped"


def _log(msg):
    try:
        import FreeCAD
        FreeCAD.Console.PrintLog("[AcadAgent migrate] %s\n" % msg)
    except Exception:                                  # noqa: BLE001
        pass


def new_root():
    """FreeCAD's user data dir for this ExeName, or None outside FreeCAD."""
    try:
        import FreeCAD
        return FreeCAD.getUserAppDataDir()
    except Exception:                                  # noqa: BLE001
        return None


def _old_root(new, old_name):
    """The `old_name` folder matching `new`, or None when `new` IS an
    earlier name's folder (the image still carries an old ExeName).

    FreeCAD 1.1 appends a version folder: .../<ExeName>/v1-1. The same
    version folder is used under the old name; an unversioned `new` maps to
    the unversioned old folder."""
    if not new:
        return None
    new = os.path.normpath(new)
    leaf, parent = os.path.basename(new), os.path.dirname(new)
    if leaf.startswith("v") and leaf[1:2].isdigit():
        if os.path.basename(parent) in OLD_NAMES:
            return None
        return os.path.join(os.path.dirname(parent), old_name, leaf)
    if leaf in OLD_NAMES:
        return None
    return os.path.join(parent, old_name)


def old_root_for(new, old_name=None, items=ITEMS):
    """The earlier name's folder to copy from: `old_name`'s when given,
    else the newest earlier name (OLD_NAMES) whose folder holds any of
    `items`, else the newest one's. None when `new` is itself an earlier
    name's folder."""
    if old_name:
        return _old_root(new, old_name)
    roots = [_old_root(new, n) for n in OLD_NAMES]
    if not roots or roots[0] is None:
        return None
    for r in roots:
        if any(_present(os.path.join(r, i)) for i in (items or ())):
            return r
    return roots[0]


def marker_path(new):
    return os.path.join(new, "AcadAgent", MARKER)


def read_marker(new):
    try:
        with open(marker_path(new), encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def _write_marker(new, record):
    path = marker_path(new)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=1)
        os.replace(tmp, path)
        return True
    except OSError as exc:
        _log("marker not written: %r" % (exc,))
        return False


def _copy(src, dst):
    """Copy one file or folder atomically (tmp + replace), keeping modes:
    the trust store and the chat index are written 0600 and stay that way.
    Links inside a copied folder stay links (never followed). An empty
    folder at `dst` is replaced."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + ".migrating"
    if os.path.isdir(src):
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.copytree(src, tmp, symlinks=True)
        if os.path.isdir(dst) and not os.path.islink(dst) and not os.listdir(dst):
            os.rmdir(dst)
    else:
        shutil.copy2(src, tmp)
    os.replace(tmp, dst)


def _is_file(p):
    """A real file, or a real folder with something in it (never a link)."""
    if os.path.islink(p):
        return False
    if os.path.isdir(p):
        try:
            return bool(os.listdir(p))
        except OSError:
            return False
    return os.path.isfile(p)


def _present(p):
    """Something the user would lose if it were overwritten: a file, a
    link, or a non-empty folder (an empty one FreeCAD made is not)."""
    if os.path.islink(p) or os.path.isfile(p):
        return True
    if os.path.isdir(p):
        try:
            return bool(os.listdir(p))
        except OSError:
            return True
    return False


def migrate(new=None, old=None, items=ITEMS):
    """Run the one-time copy. Returns a record dict; its "status" is one of
    "done", "partial", "skipped", or "nothing" (no old data, or no rename),
    or "already" (a marker from an earlier run said done/skipped)."""
    try:
        return _migrate(new, old, items)
    except Exception as exc:                           # noqa: BLE001
        _log("migration failed: %r" % (exc,))
        return {"status": "error", "error": repr(exc)}


def _migrate(new, old, items):
    if os.environ.get("ATECH_MIGRATE", "1") == "0":
        return {"status": "nothing", "why": "ATECH_MIGRATE=0"}
    new = new or new_root()
    if not new:
        return {"status": "nothing", "why": "no user data dir"}
    old = old or old_root_for(new, items=items)
    if not old or os.path.normpath(old) == os.path.normpath(new):
        return {"status": "nothing", "why": "user data dir not renamed"}
    prev = read_marker(new)
    if prev and prev.get("status") in (DONE, SKIPPED):
        return {"status": "already", "marker": prev}
    have_old = [i for i in items if _is_file(os.path.join(old, i))]
    if not have_old:
        return {"status": "nothing", "why": "no addon data in %s" % old}
    have_new = [i for i in items if _present(os.path.join(new, i))]
    record = {"from": os.path.normpath(old), "to": os.path.normpath(new),
              "t": int(time.time()),
              "copied": [], "kept_new": [], "failed": []}
    if have_new and prev is None:
        # The user already works in the new folder: never overwrite it.
        record.update(status=SKIPPED, kept_new=have_new)
        _write_marker(new, record)
        _log("not migrated: %s already holds %s" % (new, ", ".join(have_new)))
        return record
    if prev:                                 # a partial run: keep its copies
        record["copied"] = list(prev.get("copied") or [])
    for item in have_old:
        dst = os.path.join(new, item)
        if _present(dst):
            if item not in record["copied"]:
                record["kept_new"].append(item)
            continue
        try:
            _copy(os.path.join(old, item), dst)
            record["copied"].append(item)
        except OSError as exc:
            record["failed"].append(item)
            _log("could not copy %s: %r" % (item, exc))
    record["status"] = PARTIAL if record["failed"] else DONE
    _write_marker(new, record)
    _log("migrated from %s: %s" % (old, record))
    return record


# ------------------------------------------------ sessions.json v2 (R365)
#: Since R365 a chat is keyed by the document's AtechProjectId instead of
#: its Uid. projects_store stamps a document's FIRST id from its Uid, so
#: every v1 record (keyed by Uid) is already keyed by the right id: what
#: changes is the record. v2 records carry "v": 2 and, once known, "path"
#: (the realpath of the project file), which is how a Finder copy is told
#: from the original and how prune_sessions knows a project was deleted.
SESSIONS_V = 2


def migrate_sessions(path):
    """Bring sessions.json to v2 in place. Idempotent (records already v2
    are left alone); never raises. A v1 record whose chat folder is gone
    and whose document never had a file (an "Unnamed" that was closed)
    can never be reopened: it is dropped. Returns {"migrated": n,
    "dropped": [ids]}."""
    out = {"migrated": 0, "dropped": []}
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return out
    if not isinstance(data, dict):
        return out
    changed = False
    for key, rec in list(data.items()):
        if not isinstance(rec, dict):
            data.pop(key)
            out["dropped"].append(key)
            changed = True
            continue
        if rec.get("v") == SESSIONS_V:
            continue
        ws = rec.get("ws")
        if not rec.get("path") and not (isinstance(ws, str)
                                        and os.path.isdir(ws)):
            data.pop(key)
            out["dropped"].append(key)
            changed = True
            continue
        rec["v"] = SESSIONS_V
        rec.setdefault("path", "")
        prev = rec.get("prev")
        if isinstance(prev, dict) and prev.get("uid") not in (None, key):
            # The build record names the document build.py should find:
            # the same id as the chat.
            prev["uid"] = key
        out["migrated"] += 1
        changed = True
    if changed:
        try:
            tmp = path + ".tmp"
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=1)
            os.replace(tmp, path)
        except OSError as exc:
            _log("sessions.json not migrated: %r" % (exc,))
    return out
