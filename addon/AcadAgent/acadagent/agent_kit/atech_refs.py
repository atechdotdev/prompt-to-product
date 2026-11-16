"""atech_refs - load the files the user named in the chat (R930).

Prompt To Product copies them into the chat folder as refs/<name>/ (ref.json says
what is there; README.md shows the calls). model.py builds with the chat
folder as its working folder, so:

    import atech_refs
    atech_refs.names()                 # ["crab_plate1", ...]
    atech_refs.parts("crab_plate1")    # ["body", "leg_1", ...]
    atech_refs.info("crab_plate1")     # ref.json: sizes, triangles, source
    k = atech_refs.keep("crab_plate1", "leg")     # unchanged, for the document
    s = atech_refs.solid("crab_plate1", "body")   # Part solid to cut and fuse
    s = atech_refs.solid("crab_plate1", "body", flat=True)  # on z=0, centred
    m = atech_refs.mesh("crab_plate1", "body")    # Mesh.Mesh, to measure
    s = atech_refs.shape("bracket")    # a STEP/IGES/BREP as it is

Only Part shapes come back from model.py (a Mesh::Feature is not built), so
every part goes in as doc.addObject("Part::Feature", label).Shape = ...

A mesh made a solid is sewn from its triangles (a few seconds for tens of
thousands); pass max_triangles to simplify a heavy one first.
"""
import json
import os

REFS_DIR = "refs"
#: More triangles than this are simplified before a mesh becomes a solid.
MAX_TRIANGLES = 60000


class RefError(ValueError):
    pass


def _root():
    return os.path.join(os.getcwd(), REFS_DIR)


def names():
    root = _root()
    try:
        return sorted(n for n in os.listdir(root)
                      if os.path.isfile(os.path.join(root, n, "ref.json")))
    except OSError:
        return []


def info(name):
    p = os.path.join(_root(), name, "ref.json")
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except OSError:
        raise RefError("No refs/%s here. Files the user named: %s"
                       % (name, ", ".join(names()) or "none"))


def parts(name):
    return [p["name"] for p in info(name).get("parts", ())]


def _entry(name, part):
    ps = info(name).get("parts", ())
    if part is None:
        if len(ps) != 1:
            raise RefError("refs/%s has %d parts; name one of: %s"
                           % (name, len(ps), ", ".join(p["name"] for p in ps)))
        return ps[0]
    for p in ps:
        if p["name"] == part:
            return p
    raise RefError("refs/%s has no part %r; its parts: %s"
                   % (name, part, ", ".join(p["name"] for p in ps)))


def path(name, part=None):
    return os.path.join(_root(), name, _entry(name, part)["file"])


def _flat(shape_or_mesh, is_mesh):
    import FreeCAD
    b = shape_or_mesh.BoundBox
    v = FreeCAD.Vector(-(b.XMin + b.XMax) / 2.0, -(b.YMin + b.YMax) / 2.0, -b.ZMin)
    if is_mesh:
        shape_or_mesh.translate(v.x, v.y, v.z)
    else:
        shape_or_mesh.translate(v)
    return shape_or_mesh


def mesh(name, part=None, flat=False):
    """The part as a Mesh.Mesh, in the file's coordinates (flat=True: centred
    on the origin, sitting on z=0)."""
    import Mesh
    e = _entry(name, part)
    if e.get("kind") == "solid":
        import MeshPart
        m = MeshPart.meshFromShape(Shape=shape(name, part), LinearDeflection=0.05,
                                   AngularDeflection=0.3)
    else:
        m = Mesh.Mesh(path(name, part))
    return _flat(m, True) if flat else m


def shape(name, part=None, flat=False):
    """A STEP/IGES/BREP part as the file has it (a mesh part: solid())."""
    import Part
    e = _entry(name, part)
    if e.get("kind") != "solid":
        return solid(name, part, flat=flat)
    s = Part.read(path(name, part))
    return _flat(s, False) if flat else s


def keep(name, part=None, flat=False):
    """A part you keep unchanged, as a Part shape for the document (a mesh
    in the document is not built: only Part shapes come back). Never refused
    for a broken mesh: put its Label in intent.json "imported" and it is
    shown and fitted, not sent back to you as invalid."""
    e = _entry(name, part)
    if e.get("kind") == "solid":
        return shape(name, part, flat=flat)
    return _sew(name, dict(e, _keep=True), mesh(name, part, flat=flat),
                MAX_TRIANGLES * 4, 0.05)


def solid(name, part=None, flat=False, max_triangles=MAX_TRIANGLES, tolerance=0.05):
    """The part as one Part solid you can cut, fuse and fillet."""
    e = _entry(name, part)
    if e.get("kind") == "solid":
        s = shape(name, part)
        if len(s.Solids) == 1:
            s = s.Solids[0]
        return _flat(s, False) if flat else s
    s = _sew(name, e, mesh(name, part), max_triangles, tolerance)
    if not s.isValid():
        try:
            s.fix(1e-4, 1e-4, 1e-4)
        except Exception:                              # noqa: BLE001
            pass
    if not s.isValid():
        # A self-intersecting mesh (bodies that overlap, exported as one)
        # sews into a solid that cuts and fuses leave unchanged.
        raise RefError("refs/%s %s is a broken mesh (its triangles cross), so "
                       "cuts and fuses on it do nothing. Keep it unchanged "
                       "(atech_refs.keep, Label in intent.json \"imported\") "
                       "or draw the part again from its measurements."
                       % (name, e["name"]))
    return _flat(s, False) if flat else s


def _sew(name, e, m, max_triangles, tolerance):
    import Part
    if m.CountFacets > max_triangles:
        m.decimate(tolerance * 10, 1.0 - float(max_triangles) / m.CountFacets)
    if not m.isSolid():
        try:
            m.fillupHoles(1000)
            m.harmonizeNormals()
        except Exception:                              # noqa: BLE001
            pass
    sh = Part.Shape()
    sh.makeShapeFromMesh(m.Topology, tolerance, True)
    try:
        s = Part.makeSolid(sh)
    except Exception:                                  # noqa: BLE001
        s = sh
    try:
        s = s.removeSplitter()
    except Exception:                                  # noqa: BLE001
        pass
    if not s.Solids:
        if e.get("_keep"):
            return s                    # a shell: shown, fitted, not cut
        raise RefError("refs/%s %s is not a closed mesh, so it makes no solid; "
                       "keep it unchanged (atech_refs.keep) and build around it."
                       % (name, e["name"]))
    s = s.Solids[0] if len(s.Solids) == 1 else Part.makeCompound(s.Solids)
    if s.Volume < 0:
        s.reverse()
    return s
