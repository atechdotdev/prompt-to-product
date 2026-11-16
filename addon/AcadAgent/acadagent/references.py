"""references - files the user names in the chat, made readable to the agent (R930).

"Use this file and make it look cooler", "use this one but adjust it for
Atech": the user pastes a path (or drops a file on the message box, which
writes its file:// link). The agent can read only its chat folder (one
--add-dir) and model.py builds in a sandbox that cannot see the rest of the
home folder, so a path outside is a dead end for both. Here, before the
turn starts, every CAD file or picture named in the message is brought into
the chat folder under refs/<name>/:

    STEP / IGES / BREP      copied as they are (atech_refs.shape loads them)
    STL / OBJ / PLY / OFF   copied as they are
    3MF (Bambu Studio's     every object written out as its own STL, with
      .gcode.3mf too)       the plate picture; the sliced G-code is left out
    PNG / JPG               copied, for the agent to look at

with ref.json (what each part is, its size) and README.md (how model.py
loads them: agent_kit/atech_refs.py). The message the agent gets names the
copies, never the original paths, and says how a remix is done: keep what
is not changed as it is (intent.json "imported"), change or add only what
the request asks - "for Atech" means fitting the Atech board, screen and
modules into it.

find_paths() and attach() are headless (no FreeCAD, no Qt).
"""
import hashlib
import json
import os
import re
import shutil
import struct
import zipfile

try:                                    # Python 3
    from urllib.parse import unquote
except ImportError:                     # pragma: no cover
    from urllib import unquote

REFS_DIR = "refs"
REF_FILE = "ref.json"
README = "README.md"
SOLID_EXT = (".step", ".stp", ".iges", ".igs", ".brep", ".brp")
MESH_EXT = (".stl", ".obj", ".ply", ".off")
PICTURE_EXT = (".png", ".jpg", ".jpeg")
#: ".gcode.3mf" ends in ".3mf" too.
THREEMF_EXT = (".3mf",)
#: R970: GLB / glTF (Sketchfab, scanners, AI 3D generators): a STL per part
GLTF_EXT = (".glb", ".gltf")
ALL_EXT = SOLID_EXT + MESH_EXT + THREEMF_EXT + GLTF_EXT + PICTURE_EXT
#: Bigger files are not copied (a whole-project archive, a video).
MAX_BYTES = 400 * 1024 * 1024
#: At most this many files from one message.
MAX_FILES = 8

_EXT_RE = "|".join(re.escape(e[1:]) for e in sorted(ALL_EXT, key=len, reverse=True))
#: file:///Users/<you>/b%20c.stl (a drop on the box writes these)
_URL = re.compile(r"file://(?:localhost)?(/[^\s<>\"']+)", re.I)
#: "/Users/<you>/b c.stl", '~/x.step' (a path with spaces, quoted)
_QUOTED = re.compile(r"[\"'`]((?:~|/)[^\"'`\n]+?\.(?:%s))[\"'`]" % _EXT_RE, re.I)
#: /Users/<you>/b\ c.stl or ~/x.step (a Terminal-style path, spaces escaped)
_BARE = re.compile(r"(?<![\w:/])((?:~|/)(?:\\ |[^\s\"'`<>])+?\.(?:%s))(?=$|[\s,;:!?)\]]|\.(?:\s|$))"
                   % _EXT_RE, re.I)
#: /Users/<you>/My Files/b.stl (spaces, unquoted; only when the file exists)
_SPACED = re.compile(r"(?<![\w:/])((?:~|/)[^\n\"'`<>]*?\.(?:%s))(?![A-Za-z0-9])" % _EXT_RE, re.I)


def _log(msg):
    try:
        import FreeCAD
        FreeCAD.Console.PrintLog("[references] %s\n" % msg)
    except Exception:                                  # noqa: BLE001
        pass


# ------------------------------------------------------------------ finding
def find_paths(text):
    """The existing local files the message names, in order, each once:
    file:// links, quoted paths, bare absolute or ~ paths. Only the kinds
    attach() handles (ALL_EXT)."""
    found = []
    spans = []

    def add(raw, span):
        p = os.path.expanduser(raw.strip())
        p = os.path.normpath(p)
        if any(a <= span[0] < b for a, b in spans):
            return
        spans.append(span)
        if p.lower().endswith(ALL_EXT) and os.path.isfile(p) and p not in found:
            found.append(p)

    text = text or ""
    for m in _URL.finditer(text):
        add(unquote(m.group(1)), m.span())
    for m in _QUOTED.finditer(text):
        add(m.group(1), m.span())
    for m in _BARE.finditer(text):
        p = m.group(1).replace("\\ ", " ")
        if os.path.isfile(os.path.expanduser(p)):
            add(p, m.span())
    # A path with spaces pasted as it is: taken only when it is a file.
    for m in _SPACED.finditer(text):
        if os.path.isfile(os.path.expanduser(m.group(1))):
            add(m.group(1), m.span())
    return found[:MAX_FILES]


# ------------------------------------------------------------------ naming
def slug(path):
    """refs/<slug>: the file's name without its extensions, plain."""
    base = os.path.basename(path)
    low = base.lower()
    for ext in (".gcode.3mf",) + ALL_EXT:
        if low.endswith(ext):
            base = base[:-len(ext)]
            break
    s = re.sub(r"[^A-Za-z0-9]+", "_", base).strip("_").lower()
    return (s or "file")[:60]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _part_name(name, taken):
    s = re.sub(r"[^A-Za-z0-9]+", "_", name or "").strip("_").lower() or "part"
    s = s[:50]
    out, n = s, 2
    while out in taken:
        out = "%s_%d" % (s, n)
        n += 1
    taken.add(out)
    return out


# ------------------------------------------------------------------ meshes
def _bounds(tris):
    xs = [p[0] for t in tris for p in t]
    ys = [p[1] for t in tris for p in t]
    zs = [p[2] for t in tris for p in t]
    return [min(xs), min(ys), min(zs)], [max(xs), max(ys), max(zs)]


def write_stl(path, tris, name="prompt_to_product"):
    """Binary STL of [(p1, p2, p3), ...] (normals left to the reader)."""
    with open(path, "wb") as fh:
        head = ("%s" % name).encode("ascii", "replace")[:80]
        fh.write(head.ljust(80, b" "))
        fh.write(struct.pack("<I", len(tris)))
        pack = struct.Struct("<12fH").pack
        for a, b, c in tris:
            fh.write(pack(0.0, 0.0, 0.0, a[0], a[1], a[2], b[0], b[1], b[2],
                          c[0], c[1], c[2], 0))


def read_stl(path):
    """[(p1, p2, p3)] of an STL, binary or ASCII."""
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) >= 84:
        n = struct.unpack("<I", data[80:84])[0]
        if 84 + 50 * n == len(data):
            out = []
            unpack = struct.Struct("<12fH").unpack_from
            for i in range(n):
                v = unpack(data, 84 + 50 * i)
                out.append(((v[3], v[4], v[5]), (v[6], v[7], v[8]),
                            (v[9], v[10], v[11])))
            return out
    pts = [tuple(float(x) for x in m.groups()) for m in re.finditer(
        rb"vertex\s+(\S+)\s+(\S+)\s+(\S+)", data)]
    return [tuple(pts[i:i + 3]) for i in range(0, len(pts) - 2, 3)]


def _round(v):
    return [round(x, 2) for x in v]


def _mesh_entry(name, file, tris):
    lo, hi = _bounds(tris)
    return {"name": name, "file": file, "kind": "mesh",
            "triangles": len(tris), "min": _round(lo), "max": _round(hi),
            "size": _round([hi[i] - lo[i] for i in range(3)])}


def _plate_picture(z):
    names = z.namelist()
    for want in (r"Metadata/plate_\d+\.png$", r"Metadata/top_\d+\.png$",
                 r"Metadata/thumbnail\.png$", r".*\.png$"):
        for n in names:
            if re.match(want, n, re.I) and "small" not in n.lower():
                return n
    return None


def _bambu_names(path):
    """{object id: name} from Bambu Studio's Metadata/model_settings.config
    (its 3D model leaves the objects unnamed)."""
    import xml.etree.ElementTree as ET
    try:
        with zipfile.ZipFile(path) as z:
            root = ET.fromstring(z.read("Metadata/model_settings.config"))
    except (KeyError, OSError, ET.ParseError, zipfile.BadZipFile):
        return {}
    out = {}
    for o in root.iter("object"):
        for md in o.findall("metadata"):
            if md.get("key") == "name" and md.get("value"):
                out[o.get("id")] = md.get("value")
                break
    return out


def _from_3mf(path, dst):
    from . import makerworld
    items = makerworld.read_3mf(path)
    if not items:
        raise ValueError("the 3MF holds no objects")
    names = _bambu_names(path)
    parts, taken = [], set()
    for name, tris in items:
        m = re.match(r"object (\S+)$", name or "")
        if m and m.group(1) in names:
            name = names[m.group(1)]
        name = re.sub(r"\.(stl|step|stp|obj|3mf)$", "", name or "", flags=re.I)
        pn = _part_name(name, taken)
        f = pn + ".stl"
        write_stl(os.path.join(dst, f), tris, pn)
        parts.append(_mesh_entry(pn, f, tris))
    info = {"kind": "3mf", "parts": parts}
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        info["sliced"] = any(n.lower().endswith(".gcode") for n in names)
        pic = _plate_picture(z)
        if pic:
            with open(os.path.join(dst, "picture.png"), "wb") as fh:
                fh.write(z.read(pic))
            info["picture"] = "picture.png"
    return info


def _from_gltf(path, dst):
    """R970: a GLB / glTF as one STL per part of its scene (mm, Z up), each
    with its colour, so model.py keeps or remixes them like a 3MF's."""
    from . import gltf
    try:
        items = gltf.read(path)
    except gltf.GltfError as exc:
        raise ValueError(str(exc))
    parts, taken = [], set()
    for p in items:
        pn = _part_name(p.name, taken)
        f = pn + ".stl"
        write_stl(os.path.join(dst, f), p.triangles, pn)
        e = _mesh_entry(pn, f, p.triangles)
        if p.color:
            e["color"] = [round(c, 3) for c in p.color[:3]]
        parts.append(e)
    return {"kind": "gltf", "parts": parts,
            "units": "metres in the file, read as millimetres x 1000"}


def _from_solid(path, dst):
    f = "model" + os.path.splitext(path)[1].lower()
    shutil.copyfile(path, os.path.join(dst, f))
    entry = {"name": "model", "file": f, "kind": "solid"}
    try:                                    # inside FreeCAD: its size too
        import Part
        s = Part.read(path)
        b = s.BoundBox
        entry.update({"bodies": len(s.Solids),
                      "min": _round([b.XMin, b.YMin, b.ZMin]),
                      "max": _round([b.XMax, b.YMax, b.ZMax]),
                      "size": _round([b.XLength, b.YLength, b.ZLength])})
    except Exception as exc:                           # noqa: BLE001
        _log("size of %s: %r" % (path, exc))
    return {"kind": "solid", "parts": [entry]}


def _from_mesh(path, dst):
    ext = os.path.splitext(path)[1].lower()
    f = "model" + ext
    shutil.copyfile(path, os.path.join(dst, f))
    if ext == ".stl":
        try:
            tris = read_stl(path)
            if tris:
                return {"kind": "mesh", "parts": [_mesh_entry("model", f, tris)]}
        except Exception as exc:                       # noqa: BLE001
            _log("read %s: %r" % (path, exc))
    return {"kind": "mesh", "parts": [{"name": "model", "file": f,
                                       "kind": "mesh"}]}


def _from_picture(path, dst):
    f = "picture" + os.path.splitext(path)[1].lower()
    shutil.copyfile(path, os.path.join(dst, f))
    return {"kind": "picture", "parts": [], "picture": f}


# ------------------------------------------------------------------ attach
class Attached(object):
    def __init__(self, path, folder, info=None, error=""):
        self.path = path            # the original
        self.folder = folder        # refs/<slug>, relative to the workspace
        self.info = info or {}
        self.error = error

    @property
    def ok(self):
        return not self.error


def attach(ws, paths):
    """Bring `paths` into <ws>/refs/<slug>/. The same file (by checksum)
    named again is not copied twice. Returns [Attached]."""
    out = []
    root = os.path.join(ws, REFS_DIR)
    for p in paths:
        name = slug(p)
        rel = "%s/%s" % (REFS_DIR, name)
        try:
            if os.path.getsize(p) > MAX_BYTES:
                raise ValueError("it is bigger than %d MB"
                                 % (MAX_BYTES // (1024 * 1024)))
            digest = sha256(p)
            dst = os.path.join(root, name)
            old = _read_info(dst)
            if old and old.get("sha256") != digest:     # another file, same name
                name = "%s_%s" % (name, digest[:6])
                rel = "%s/%s" % (REFS_DIR, name)
                dst = os.path.join(root, name)
                old = _read_info(dst)
            if old and old.get("sha256") == digest:
                out.append(Attached(p, rel, old))
                continue
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            os.makedirs(dst)
            low = p.lower()
            if low.endswith(THREEMF_EXT):
                info = _from_3mf(p, dst)
            elif low.endswith(GLTF_EXT):
                info = _from_gltf(p, dst)
            elif low.endswith(SOLID_EXT):
                info = _from_solid(p, dst)
            elif low.endswith(MESH_EXT):
                info = _from_mesh(p, dst)
            else:
                info = _from_picture(p, dst)
            info.update({"name": name, "source": os.path.basename(p),
                         "sha256": digest})
            with open(os.path.join(dst, REF_FILE), "w", encoding="utf-8") as fh:
                json.dump(info, fh, indent=1)
            with open(os.path.join(dst, README), "w", encoding="utf-8") as fh:
                fh.write(readme(info))
            out.append(Attached(p, rel, info))
        except Exception as exc:                       # noqa: BLE001
            _log("attach %s: %r" % (p, exc))
            out.append(Attached(p, rel, error=str(exc) or type(exc).__name__))
    return out


def _read_info(folder):
    try:
        with open(os.path.join(folder, REF_FILE), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


# ------------------------------------------------------------------ words
def _mm(v):
    return " x ".join("%g" % round(x, 1) for x in v) + " mm"


def _part_line(p):
    bits = [p["name"], p["file"]]
    if p.get("size"):
        bits.append(_mm(p["size"]))
    if p.get("triangles"):
        bits.append("%d triangles" % p["triangles"])
    if p.get("bodies", 1) > 1:
        bits.append("%d bodies" % p["bodies"])
    return ", ".join(bits)


def what(info):
    """A few words on what the file is."""
    k = info.get("kind")
    n = len(info.get("parts", ()))
    if k == "3mf":
        s = "%d part%s from a %s" % (n, "" if n == 1 else "s",
                                     "sliced Bambu Studio print file"
                                     if info.get("sliced") else "3MF")
        return s + ", laid out flat on the print plate as printed, not assembled"
    if k == "gltf":
        return ("%d part%s from a GLB / glTF scene, assembled as in the file "
                "(glTF metres read as mm; a model made at the wrong scale may "
                "need scaling)" % (n, "" if n == 1 else "s"))
    if k == "solid":
        return "a solid model (STEP/IGES/BREP)"
    if k == "mesh":
        return "a mesh model"
    return "a picture"


def readme(info):
    name = info["name"]
    lines = ["# refs/%s" % name, "",
             "%s: %s." % (info.get("source", name), what(info)), ""]
    if info.get("parts"):
        lines += ["Parts (positions in mm, as in the file):", ""]
        lines += ["- %s" % _part_line(p) for p in info["parts"]]
        lines.append("")
    if info.get("picture"):
        lines += ["%s shows it: look at it before you start." % info["picture"], ""]
    if info.get("parts"):
        lines += [
            "Load it in model.py:", "",
            "```python",
            "import atech_refs",
            "atech_refs.parts(%r)          # the names above" % name,
            "k = atech_refs.keep(%r, %r)   # a part kept unchanged" % (name, info["parts"][0]["name"]),
            "s = atech_refs.solid(%r, %r)  # a part you change: cut, fuse, fillet it"
            % (name, info["parts"][0]["name"]),
            "s = atech_refs.solid(%r, %r, flat=True)  # moved to sit on z=0 at the origin"
            % (name, info["parts"][0]["name"]),
            "doc.addObject('Part::Feature', %r).Shape = k" % info["parts"][0]["name"],
            "```", "",
            "Every part goes in as a Part::Feature (a Mesh::Feature is not "
            "built). Put the Label of each part you keep unchanged in "
            "intent.json \"imported\": the checks fit it but do not judge its "
            "walls, and a flaw its maker left in it (a broken mesh) is not "
            "sent back to you. A part you change is a solid (atech_refs.solid) "
            "and is yours to check like any other; solid() says when a mesh "
            "is too broken to cut.", ""]
    if info.get("kind") == "3mf":
        lines += ["The parts lie where the slicer put them for printing. To "
                  "assemble them, work out from their shapes how they go "
                  "together and place each one.", ""]
    return "\n".join(lines)


def prompt_block(attached):
    """The lines put before the user's message: what was brought in, where
    it is, how a remix goes. "" when nothing was named."""
    if not attached:
        return ""
    lines = ["FILES THE USER NAMED (copied into this chat folder; the original "
             "paths are outside your reach, never read them):"]
    ok = False
    for a in attached:
        src = os.path.basename(a.path)
        if not a.ok:
            lines.append("- %s: could not be brought in (%s). Tell the user." % (src, a.error))
            continue
        ok = True
        info = a.info
        line = "- %s -> %s/: %s" % (src, a.folder, what(info))
        if info.get("parts"):
            line += ". Parts: " + "; ".join(_part_line(p) for p in info["parts"][:20])
            if len(info["parts"]) > 20:
                line += "; ... (%d in all)" % len(info["parts"])
        if info.get("picture"):
            line += ". Picture: %s/%s" % (a.folder, info["picture"])
        lines.append(line)
    if ok:
        lines += [
            "Read each folder's README.md first (it shows how model.py loads "
            "the parts with atech_refs). Work FROM these files: the request "
            "is a remix of them, not a new design that looks like them. Keep "
            "every part you do not need to change exactly as it is (its Label "
            "in intent.json \"imported\"); change or add only what the request "
            "asks. \"For Atech\" / \"adjust it for Atech\" means: fit the Atech "
            "board, screen and modules into it (mounts, openings, cable "
            "paths, a cover that holds them) in place of the electronics it "
            "was made for, keeping its look and mechanics.",
            ""]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ R970
def _unique(label, taken):
    out, n = label, 2
    while out in taken:
        out = "%s %d" % (label, n)
        n += 1
    taken.add(out)
    return out


def import_script(attached):
    """(model.py, Labels) for a project made by importing files (R970,
    panel.start_from_files): every part of every attached file kept as it
    is, in its own colour when the file has one. The Labels go in
    intent.json "imported"."""
    rows, taken = [], set()
    cursor = None                       # files after the first go beside it
    for a in attached:
        info = a.info
        ref = info["name"]
        parts = info.get("parts", ())
        los = [p["min"][0] for p in parts if p.get("min")]
        his = [p["max"][0] for p in parts if p.get("max")]
        dx = 0.0
        if los and his:
            if cursor is not None:
                dx = round(cursor - min(los), 2)
            cursor = max(his) + dx + 15.0
        stem = re.sub(r"[_]+", " ", ref).strip().capitalize() or "Part"
        for i, p in enumerate(parts, 1):
            generic = re.match(r"(part|mesh|object|node|model|body|geometry)(_\d+)?$",
                               p["name"], re.I)
            if len(parts) == 1:
                label = stem
            elif generic:
                label = "%s %d" % (stem, i)
            else:
                label = re.sub(r"[_]+", " ", p["name"]).strip().capitalize()
            label = _unique(label, taken)
            rows.append((ref, p["name"], label,
                         tuple(p["color"]) if p.get("color") else None, dx))
    labels = [r[2] for r in rows]
    names = ", ".join(sorted({os.path.basename(a.path) for a in attached}))
    code = (
        '"""Imported: %s - every part kept exactly as the file has it.\n\n'
        'Prompt2Product made this from the imported file(s) (refs/, see each\n'
        'folder\'s README.md). Change it for what the user asks; parts you do\n'
        'not change stay kept, their Labels in intent.json "imported".\n'
        '"""\n'
        'import FreeCAD\n'
        'import atech_refs\n\n'
        '# (ref folder, part, Label, colour, x shift: files side by side)\n'
        'PARTS = [\n%s]\n\n'
        'for ref, part, label, colour, dx in PARTS:\n'
        '    o = doc.addObject("Part::Feature", "Imported")\n'
        '    o.Label = label\n'
        '    s = atech_refs.keep(ref, part)\n'
        '    if dx:\n'
        '        s.translate(FreeCAD.Vector(dx, 0, 0))\n'
        '    o.Shape = s\n'
        '    if colour:\n'
        '        o.ViewObject.ShapeColor = colour\n'
        % (names.replace('"', "'"),
           "".join("    (%r, %r, %r, %r, %r),\n" % r for r in rows)))
    return code, labels
