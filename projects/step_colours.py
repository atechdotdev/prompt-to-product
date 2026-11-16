"""step_colours - the colours a STEP file gives its solids and faces, and
a coloured tessellation of it (FreeCAD's console import keeps no colours).

    groups = coloured_mesh(path, deflection=0.05)
    # [{"rgb": (r, g, b), "points": [(x, y, z)...], "triangles": [(i, j, k)...]}]

How: STYLED_ITEMs are read from the STEP text (each one's COLOUR_RGB or
DRAUGHTING_PRE_DEFINED_COLOUR, followed through its style entities) with
the solid or face they colour. Part.read's solids are matched to the
file's MANIFOLD_SOLID_BREPs by the sequence of their faces' surface types
(an instanced solid, e.g. one pin placed 8 times, matches every copy);
a face takes its own colour, else its solid's, else DEFAULT.
"""
import re

DEFAULT = (0.62, 0.64, 0.66)

_ENT = re.compile(r"#(\d+)\s*=\s*(.*?);\s*(?=#\d+\s*=|ENDSEC)", re.S)
_REF = re.compile(r"#(\d+)")
_SURF = {"PLANE": "Plane", "CYLINDRICAL_SURFACE": "Cylinder", "CONICAL_SURFACE": "Cone",
         "SPHERICAL_SURFACE": "Sphere", "TOROIDAL_SURFACE": "Toroid",
         "B_SPLINE_SURFACE": "BSplineSurface", "B_SPLINE_SURFACE_WITH_KNOTS": "BSplineSurface",
         "BEZIER_SURFACE": "BezierSurface", "SURFACE_OF_LINEAR_EXTRUSION": "SurfaceOfExtrusion",
         "SURFACE_OF_REVOLUTION": "SurfaceOfRevolution", "OFFSET_SURFACE": "OffsetSurface"}
_NAMED = {"black": (0, 0, 0), "red": (1, 0, 0), "green": (0, 1, 0), "blue": (0, 0, 1),
          "yellow": (1, 1, 0), "magenta": (1, 0, 1), "cyan": (0, 1, 1), "white": (1, 1, 1)}


def _kind(text):
    """The entity's type: 'PLANE' for PLANE(...); for a complex entity
    ( A() B() ...) the first keyword that names a surface, else the first."""
    t = text.lstrip()
    if t.startswith("("):
        words = re.findall(r"([A-Z_][A-Z0-9_]*)\s*\(", t)
        for w in words:
            if w in _SURF:
                return w
        return words[0] if words else ""
    m = re.match(r"([A-Z_][A-Z0-9_]*)", t)
    return m.group(1) if m else ""


def parse(data):
    """{id: (kind, text)} of a STEP file's DATA section (bytes or str)."""
    if isinstance(data, bytes):
        data = data.decode("latin-1", "replace")
    i = data.find("DATA;")
    body = data[i + 5:] if i >= 0 else data
    return {int(m.group(1)): (_kind(m.group(2)), m.group(2)) for m in _ENT.finditer(body)}


def _colour_of(ents, start, depth=8):
    seen, frontier = set(), [start]
    for _ in range(depth):
        nxt = []
        for i in frontier:
            if i in seen or i not in ents:
                continue
            seen.add(i)
            kind, text = ents[i]
            if kind == "COLOUR_RGB":
                nums = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text.split(",", 1)[1])
                if len(nums) >= 3:
                    return tuple(max(0.0, min(1.0, float(n))) for n in nums[:3])
            if kind == "DRAUGHTING_PRE_DEFINED_COLOUR":
                m = re.search(r"'([a-z]+)'", text)
                if m and m.group(1) in _NAMED:
                    return _NAMED[m.group(1)]
            nxt += [int(r) for r in _REF.findall(text)]
        frontier = nxt
    return None


def styles(ents):
    """{target id: rgb} from every (OVER_RIDING_)STYLED_ITEM."""
    out = {}
    for _i, (kind, text) in ents.items():
        if kind not in ("STYLED_ITEM", "OVER_RIDING_STYLED_ITEM"):
            continue
        refs = [int(r) for r in _REF.findall(text)]
        if len(refs) < 2:
            continue
        target = refs[-1] if kind == "STYLED_ITEM" else refs[-2]
        rgb = None
        for r in refs[:-1]:
            rgb = _colour_of(ents, r)
            if rgb:
                break
        if rgb:
            out[target] = rgb
    return out


def solids(ents):
    """[(solid id, [face ids], (surface types...))] in file order."""
    out = []
    for i in sorted(ents):
        kind, text = ents[i]
        if kind not in ("MANIFOLD_SOLID_BREP", "BREP_WITH_VOIDS", "SHELL_BASED_SURFACE_MODEL"):
            continue
        faces = []
        for s in _REF.findall(text):
            sk, st = ents.get(int(s), ("", ""))
            if sk == "ORIENTED_CLOSED_SHELL":          # a void: its shell is referenced
                refs = _REF.findall(st)
                sk, st = ents.get(int(refs[-1]), ("", "")) if refs else ("", "")
            if sk in ("CLOSED_SHELL", "OPEN_SHELL"):
                faces += [int(f) for f in _REF.findall(st)]
        types = []
        for f in faces:
            fk, ft = ents.get(f, ("", ""))
            refs = _REF.findall(ft)
            surf = ents.get(int(refs[-1]), ("", ""))[0] if refs else ""
            types.append(_SURF.get(surf, surf))
        out.append((i, faces, tuple(types)))
    return out


def _surface_name(face):
    try:
        return type(face.Surface).__name__
    except Exception:                                  # noqa: BLE001
        return ""


def face_colours(shape, data):
    """[(face, rgb)] for every face of Part shape `shape` read from STEP
    text `data`. Also returns how many solids were matched by signature."""
    ents = parse(data)
    col = styles(ents)
    sols = solids(ents)
    by_sig = {}
    for sid, faces, types in sols:
        by_sig.setdefault(types, []).append((sid, faces))
    out, matched = [], 0
    parts = list(shape.Solids) or list(shape.Shells) or [shape]
    used = set()
    for s in parts:
        sig = tuple(_surface_name(f) for f in s.Faces)
        cands = by_sig.get(sig) or []
        pick = next((c for c in cands if c[0] not in used), cands[0] if cands else None)
        if pick is None:
            out += [(f, DEFAULT) for f in s.Faces]
            continue
        matched += 1
        used.add(pick[0])
        base = col.get(pick[0], DEFAULT)
        out += [(f, col.get(fid, base)) for f, fid in zip(s.Faces, pick[1])]
    return out, matched, len(parts)


def coloured_mesh(path, deflection=0.05):
    """The STEP file tessellated, grouped by colour (see the module doc)."""
    import Part
    with open(path, "rb") as fh:
        data = fh.read()
    shape = Part.read(path)
    fc, matched, total = face_colours(shape, data)
    groups = {}
    for face, rgb in fc:
        key = tuple(round(c, 3) for c in rgb)
        g = groups.setdefault(key, {"rgb": key, "points": [], "triangles": []})
        try:
            pts, tris = face.tessellate(deflection)
        except Exception:                              # noqa: BLE001
            continue
        base = len(g["points"])
        g["points"] += [(p.x, p.y, p.z) for p in pts]
        g["triangles"] += [(a + base, b + base, c + base) for a, b, c in tris]
    return ([g for g in groups.values() if g["triangles"]],
            {"solids": total, "matched": matched})
