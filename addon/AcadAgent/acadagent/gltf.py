"""gltf - read the triangles of a .glb / .gltf file (R970).

GLB is what Sketchfab, Thingiverse previews, Printables' 3D view, phone 3D
scanners and most AI 3D generators hand out. FreeCAD has no reader for it,
so this is a small one in plain Python (no FreeCAD needed: the chat's
references use it too):

    parts = read("chair.glb")      # [Part(name, triangles, colour), ...]

Each part is one node of the default scene that carries a mesh (its node
transforms applied), with its triangles as ((x, y, z), (x, y, z), (x, y, z))
in MILLIMETRES, Z up: glTF is metres and Y up, so (x, y, z) -> 1000 * (x,
-z, y). Colour is the first primitive's baseColorFactor (RGBA 0..1) or None.

Read: triangles, triangle strips and fans, indexed or not, any accessor
component type (normalised integers too: KHR_mesh_quantization), sparse
accessors, buffers inside the GLB, as data: URIs or as files beside a .gltf.
Refused, with a sentence for the user: Draco and meshopt compressed meshes
(they need a decoder this app does not ship), files without triangles.
"""
import base64
import json
import math
import os
import struct

EXT = (".glb", ".gltf")
#: glTF metres -> millimetres
SCALE = 1000.0
#: More parts than this: the rest are merged into the last one.
MAX_PARTS = 60
#: More triangles than this in one file is refused (a 1 GB scan).
MAX_TRIANGLES = 3000000

_COMP = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2),
         5125: ("I", 4), 5126: ("f", 4)}
_NORM = {5120: 127.0, 5121: 255.0, 5122: 32767.0, 5123: 65535.0}
_COUNT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
_COMPRESSED = {"KHR_draco_mesh_compression": "Draco",
               "EXT_meshopt_compression": "meshopt",
               "KHR_meshopt_compression": "meshopt"}


class GltfError(ValueError):
    """The file cannot be read; str() is a sentence for the user."""


class Part(object):
    def __init__(self, name, triangles, color=None):
        self.name = name
        self.triangles = triangles
        self.color = color

    def __repr__(self):
        return "Part(%r, %d triangles)" % (self.name, len(self.triangles))


def is_gltf(path):
    return str(path).lower().endswith(EXT)


# ------------------------------------------------------------------ container
def _load(path):
    """(json dict, [buffer bytes])."""
    with open(path, "rb") as fh:
        data = fh.read()
    base = os.path.dirname(os.path.abspath(path))
    if data[:4] == b"glTF":
        if len(data) < 20:
            raise GltfError("%s is cut short." % os.path.basename(path))
        _magic, version, length = struct.unpack_from("<III", data, 0)
        if version != 2:
            raise GltfError("%s is glTF %d; only glTF 2 is read."
                            % (os.path.basename(path), version))
        pos, doc, binchunk = 12, None, None
        while pos + 8 <= min(length, len(data)):
            clen, ctype = struct.unpack_from("<II", data, pos)
            chunk = data[pos + 8:pos + 8 + clen]
            if ctype == 0x4E4F534A:                     # JSON
                doc = json.loads(chunk.decode("utf-8"))
            elif ctype == 0x004E4942 and binchunk is None:   # BIN
                binchunk = chunk
            pos += 8 + clen + (-clen % 4)               # chunks are 4-aligned
        if doc is None:
            raise GltfError("%s has no glTF JSON." % os.path.basename(path))
    else:
        try:
            doc = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise GltfError("%s is neither a .glb nor a glTF JSON file."
                            % os.path.basename(path))
        binchunk = None
    buffers = []
    for i, b in enumerate(doc.get("buffers", [])):
        uri = b.get("uri")
        if uri is None:
            if binchunk is None:
                raise GltfError("%s names a binary chunk it does not have."
                                % os.path.basename(path))
            buffers.append(binchunk)
        elif uri.startswith("data:"):
            try:
                buffers.append(base64.b64decode(uri.split(",", 1)[1]))
            except (IndexError, ValueError):
                raise GltfError("buffer %d of %s is a broken data URI."
                                % (i, os.path.basename(path)))
        else:
            from urllib.parse import unquote
            p = os.path.normpath(os.path.join(base, unquote(uri)))
            if not p.startswith(base + os.sep) and p != base:
                raise GltfError("%s points outside its folder (%s)."
                                % (os.path.basename(path), uri))
            try:
                with open(p, "rb") as fh:
                    buffers.append(fh.read())
            except OSError:
                raise GltfError("%s needs %s beside it: put the .gltf and its "
                                ".bin in one folder, or use the .glb."
                                % (os.path.basename(path), uri))
    return doc, buffers


def _check_extensions(doc, name):
    used = set(doc.get("extensionsRequired", [])) | set(doc.get("extensionsUsed", []))
    for ext, what in _COMPRESSED.items():
        if ext in used:
            raise GltfError(
                "%s is %s compressed, which Prompt2Product cannot unpack. "
                "Export it again without compression (Blender: glTF export, "
                "uncheck Compression), or as STL / OBJ." % (name, what))


# ------------------------------------------------------------------ accessors
def _accessor(doc, buffers, index):
    """The accessor's elements as a list of tuples (floats)."""
    acc = doc["accessors"][index]
    comp = acc["componentType"]
    fmt, size = _COMP[comp]
    n = _COUNT[acc["type"]]
    count = acc["count"]
    norm = acc.get("normalized") and comp in _NORM
    if "bufferView" in acc:
        bv = doc["bufferViews"][acc["bufferView"]]
        buf = buffers[bv["buffer"]]
        start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
        stride = bv.get("byteStride") or n * size
        if stride == n * size:
            flat = struct.unpack_from("<%d%s" % (count * n, fmt), buf, start)
            out = [flat[i:i + n] for i in range(0, len(flat), n)]
        else:
            one = struct.Struct("<%d%s" % (n, fmt))
            out = [one.unpack_from(buf, start + i * stride) for i in range(count)]
    else:
        out = [(0,) * n for _ in range(count)]
    sp = acc.get("sparse")
    if sp:
        idx = sp["indices"]
        ibv = doc["bufferViews"][idx["bufferView"]]
        ifmt, _isz = _COMP[idx["componentType"]]
        ids = struct.unpack_from("<%d%s" % (sp["count"], ifmt), buffers[ibv["buffer"]],
                                 ibv.get("byteOffset", 0) + idx.get("byteOffset", 0))
        val = sp["values"]
        vbv = doc["bufferViews"][val["bufferView"]]
        vals = struct.unpack_from("<%d%s" % (sp["count"] * n, fmt), buffers[vbv["buffer"]],
                                  vbv.get("byteOffset", 0) + val.get("byteOffset", 0))
        out = list(out)
        for k, i in enumerate(ids):
            out[i] = vals[k * n:(k + 1) * n]
    if norm:
        d = _NORM[comp]
        out = [tuple(max(c / d, -1.0) for c in e) for e in out]
    return out


# ------------------------------------------------------------------ matrices
def _mul(a, b):
    """4x4 column-major (glTF's order) product a * b."""
    return [sum(a[r + 4 * k] * b[k + 4 * c] for k in range(4))
            for c in range(4) for r in range(4)]


def _node_matrix(node):
    if "matrix" in node:
        return [float(v) for v in node["matrix"]]
    tx, ty, tz = node.get("translation", (0, 0, 0))
    x, y, z, w = node.get("rotation", (0, 0, 0, 1))
    sx, sy, sz = node.get("scale", (1, 1, 1))
    r = [1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w), 0,
         2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w), 0,
         2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y), 0,
         0, 0, 0, 1]
    s = [sx, 0, 0, 0, 0, sy, 0, 0, 0, 0, sz, 0, 0, 0, 0, 1]
    m = _mul(r, s)
    m[12], m[13], m[14] = tx, ty, tz
    return m


_IDENTITY = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def _apply(m, p):
    x, y, z = p[0], p[1], p[2]
    gx = m[0] * x + m[4] * y + m[8] * z + m[12]
    gy = m[1] * x + m[5] * y + m[9] * z + m[13]
    gz = m[2] * x + m[6] * y + m[10] * z + m[14]
    # glTF Y up, metres -> FreeCAD Z up, millimetres
    return (gx * SCALE, -gz * SCALE, gy * SCALE)


def _det3(m):
    return (m[0] * (m[5] * m[10] - m[9] * m[6]) - m[4] * (m[1] * m[10] - m[9] * m[2])
            + m[8] * (m[1] * m[6] - m[5] * m[2]))


# ------------------------------------------------------------------ meshes
def _triangles(doc, buffers, prim, m):
    mode = prim.get("mode", 4)
    if mode not in (4, 5, 6):
        return []                                   # points and lines
    attrs = prim.get("attributes", {})
    if "POSITION" not in attrs:
        return []
    pos = [_apply(m, p) for p in _accessor(doc, buffers, attrs["POSITION"])]
    if "indices" in prim:
        idx = [int(e[0]) for e in _accessor(doc, buffers, prim["indices"])]
    else:
        idx = list(range(len(pos)))
    if mode == 4:
        tri = [(idx[i], idx[i + 1], idx[i + 2]) for i in range(0, len(idx) - 2, 3)]
    elif mode == 5:
        tri = [((idx[i], idx[i + 1], idx[i + 2]) if i % 2 == 0 else
                (idx[i + 1], idx[i], idx[i + 2])) for i in range(len(idx) - 2)]
    else:
        tri = [(idx[0], idx[i], idx[i + 1]) for i in range(1, len(idx) - 1)]
    flip = _det3(m) < 0                             # a mirroring transform
    out = []
    for a, b, c in tri:
        if a == b or b == c or a == c:
            continue
        pa, pb, pc = pos[a], pos[b], pos[c]
        out.append((pa, pc, pb) if flip else (pa, pb, pc))
    return out


def _colour(doc, prim):
    mi = prim.get("material")
    if mi is None:
        return None
    try:
        f = doc["materials"][mi].get("pbrMetallicRoughness", {}).get("baseColorFactor")
    except (IndexError, KeyError, TypeError):
        return None
    if not f:
        return None
    # glTF colours are linear: to sRGB for the 3D view
    def srgb(c):
        c = max(0.0, min(1.0, float(c)))
        return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return tuple(round(srgb(c), 4) for c in f[:3]) + (float(f[3]) if len(f) > 3 else 1.0,)


def read(path):
    """[Part] of the file's default scene, in mm, Z up."""
    name = os.path.basename(path)
    doc, buffers = _load(path)
    _check_extensions(doc, name)
    nodes = doc.get("nodes", [])
    meshes = doc.get("meshes", [])
    scenes = doc.get("scenes", [])
    if scenes:
        roots = scenes[doc.get("scene", 0) if doc.get("scene", 0) < len(scenes) else 0].get("nodes", [])
    else:
        kids = {c for n in nodes for c in n.get("children", [])}
        roots = [i for i in range(len(nodes)) if i not in kids]
    parts, taken, total = [], {}, 0
    stack = [(r, _IDENTITY) for r in reversed(roots)]
    seen = set()
    while stack:
        ni, parent = stack.pop()
        if ni in seen or ni >= len(nodes):
            continue
        seen.add(ni)
        node = nodes[ni]
        m = _mul(parent, _node_matrix(node))
        if "mesh" in node and node["mesh"] < len(meshes):
            mesh = meshes[node["mesh"]]
            tris, colour = [], None
            for prim in mesh.get("primitives", []):
                if prim.get("extensions", {}).keys() & _COMPRESSED.keys():
                    _check_extensions({"extensionsUsed": list(prim["extensions"])}, name)
                t = _triangles(doc, buffers, prim, m)
                if t and colour is None:
                    colour = _colour(doc, prim)
                tris += t
            total += len(tris)
            if total > MAX_TRIANGLES:
                raise GltfError("%s has more than %d triangles: simplify it "
                                "first (Blender: Decimate)." % (name, MAX_TRIANGLES))
            if tris:
                base = node.get("name") or mesh.get("name") or "part"
                n = taken.get(base, 0) + 1
                taken[base] = n
                label = base if n == 1 else "%s %d" % (base, n)
                if len(parts) < MAX_PARTS:
                    parts.append(Part(label, tris, colour))
                else:
                    parts[-1].triangles += tris
        for c in reversed(node.get("children", [])):
            stack.append((c, m))
    if not parts:
        raise GltfError("%s holds no triangles (only points, lines or an "
                        "empty scene)." % name)
    return parts


def size_mm(parts):
    """(x, y, z) extent of all parts."""
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    for p in parts:
        for t in p.triangles:
            for v in t:
                for i in range(3):
                    if v[i] < lo[i]:
                        lo[i] = v[i]
                    if v[i] > hi[i]:
                        hi[i] = v[i]
    return tuple(hi[i] - lo[i] for i in range(3))


def to_mesh(parts):
    """One FreeCAD Mesh.Mesh of the parts (inside FreeCAD only)."""
    import Mesh
    return Mesh.Mesh([list(map(list, t)) for p in parts for t in p.triangles])


def part_mesh(part):
    import Mesh
    return Mesh.Mesh([list(map(list, t)) for t in part.triangles])
