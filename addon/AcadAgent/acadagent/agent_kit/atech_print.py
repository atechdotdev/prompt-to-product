"""atech_print - how each part will lie on the bed (R1250).

Before a person or a slicer looks: which side goes down, what the first
layer is (its area, how many separate pieces, how wide its lines are), and
how much of the part hangs over air. These are the checks Gustav's
cad-workflow ran on every STL after prints failed for exactly these reasons:

    a shell exported rim-down, a lid standing on its tip
        -> the first layer against the body above it
    a rim chamfered on both sides: a knife-edge first layer that came loose
        -> the mean width of the first layer's lines
    cross bars in a hull printed standing: 103 g of support
        -> the area of downward faces steeper than 45 degrees

./check prints one PRINT line per part and a WARNING for a first layer that
will not hold. Nothing here fails a build (docs/CAD_WORKFLOW_MERGE.md,
decision 2): the numbers are measured, the verdict stays with the person.

The orientation is the one Export uses (export_tools.orient_for_print): the
largest flat side the part can rest on goes down, and the side it already
stands on wins when it is nearly as big.

Pure numpy on triangle arrays: report(points, tris). shape_report(shape)
tessellates a FreeCAD shape first; only that function needs FreeCAD.
"""
import math

try:
    import numpy as np
except ImportError:                                     # pragma: no cover
    np = None

#: the height the first layer is cut at (the middle of a 0.2 mm layer); an
#: odd number so the cut does not run through a row of mesh vertices
FIRST_LAYER_Z = 0.1013
#: one extrusion line of a 0.4 mm nozzle
LINE_MM = 0.4
#: a first layer narrower than this on average (two lines) is a knife edge;
#: a wall drawn at exactly two lines measures a hair under it, hence the
#: tolerance (the alarm clock's snooze key: 0.79)
KNIFE_MM = 2 * LINE_MM
KNIFE_TOL = 0.05
#: below these a part is trim: its first-layer trouble is a note, not a
#: warning (a glint with no flat side, a 2 mm2 letter)
SMALL_MM3 = 2000.0
SMALL_FIRST_MM2 = 10.0
#: Export's own numbers (export_tools), kept equal by test_cadwf_r1250
OVERHANG_DEG = 45.0
OVERHANG_TOL_DEG = 0.5
BED_TOL = 0.05
KEEP_BOTTOM_SHARE = 0.8
OVERHANG_FLAG_MM2 = 10.0
OVERHANG_FLAG_SHARE = 0.01
#: a flat side smaller than this (mm2) is not one a part rests on
FLAT_MIN_MM2 = 1.0
#: ... and, when only the mesh is known, neither is one under this share of
#: the part's surface: the facets of a curved surface are flat too
FLAT_MIN_SHARE = 0.02
#: the first layer under this share of the widest slice above it, on a part
#: at least TALL_MM tall, is a small foot (said in the line, not a warning)
SMALL_FOOT_SHARE = 0.2
TALL_MM = 20.0
#: tessellation of a shape for these checks (mm), and the triangles above
#: which a part is not judged (a note says so)
DEFLECTION_MM = 0.2
MAX_TRIANGLES = 400000
#: directions tried as "down", the ones with the most facet area first
MAX_DIRECTIONS = 60
PLANE_TOL = 0.02


def arrays(points, tris):
    """(P float (n, 3), T int (m, 3)) from lists, tuples or arrays."""
    P = np.asarray([tuple(p) for p in points], dtype=float).reshape(-1, 3)
    T = np.asarray([tuple(t) for t in tris], dtype=np.int64).reshape(-1, 3)
    return P, T


def tri_normals(P, T):
    """(unit normals (m, 3), areas (m,)); a degenerate facet has area 0."""
    a = P[T[:, 0]]
    n = np.cross(P[T[:, 1]] - a, P[T[:, 2]] - a)
    ln = np.linalg.norm(n, axis=1)
    area = ln / 2.0
    safe = np.where(ln > 0, ln, 1.0)
    return n / safe[:, None], area


def signed_volume(P, T):
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


def supporting_planes(P, T, tol=PLANE_TOL):
    """[(area mm2, outward unit normal)] of the flat sides the part can
    rest on, largest first: every facet in the plane, and nothing of the
    part beyond it. From the mesh alone, so a side counts only from
    FLAT_MIN_SHARE of the surface up (shape_report asks the shape's own
    planar faces instead: brep_planes)."""
    N, A = tri_normals(P, T)
    keep = A > 0
    if not keep.any():
        return []
    floor = max(FLAT_MIN_MM2, FLAT_MIN_SHARE * float(A.sum()))
    key = np.round(N[keep], 3)
    uniq, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    summed = np.bincount(inv, weights=A[keep], minlength=len(uniq))
    order = np.argsort(-summed)[:MAX_DIRECTIONS]
    Tk = T[keep]
    Nk = N[keep]
    Ak = A[keep]
    out = []
    for i in order:
        if summed[i] < floor:
            break
        members = inv == i
        n = Nk[members].mean(axis=0)
        ln = float(np.linalg.norm(n))
        if ln <= 0:
            continue
        n = n / ln
        h = P @ n
        d = float(h.max())
        on = members & (h[Tk].min(axis=1) >= d - tol)
        area = float(Ak[on].sum())
        if area >= floor:
            out.append((area, tuple(float(x) for x in n)))
    out.sort(key=lambda g: -g[0])
    return out


def choose_down(planes):
    """The side that goes on the bed, as Export chooses it: the largest,
    unless the one already facing down is at least KEEP_BOTTOM_SHARE of it.
    (area, normal) or None when the part has no flat side."""
    if not planes:
        return None
    best = planes[0]
    down = [p for p in planes if p[1][2] < -1 + 1e-6]     # export_tools.orient_for_print
    if down and down[0][0] >= KEEP_BOTTOM_SHARE * best[0]:
        best = down[0]
    return best


def rotation_to_down(n):
    """The 3 x 3 matrix that turns the unit vector n onto (0, 0, -1)."""
    n = np.asarray(n, dtype=float)
    t = np.array([0.0, 0.0, -1.0])
    c = float(n @ t)
    if c > 1 - 1e-9:
        return np.eye(3)
    if c < -1 + 1e-9:
        return np.diag([1.0, -1.0, -1.0])               # half a turn about X
    v = np.cross(n, t)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx / (1.0 + c)


def lay_flat(P, n=None):
    """P turned so that n points down, resting on z = 0."""
    Q = P if n is None else P @ rotation_to_down(n).T
    Q = Q.copy()
    Q[:, 2] -= Q[:, 2].min()
    return Q


def overhang(P, T, angle=OVERHANG_DEG):
    """(overhang mm2, total mm2) of a part lying on z = 0: facets that face
    down steeper than `angle` from vertical and are not on the bed."""
    N, A = tri_normals(P, T)
    lim = -math.cos(math.radians(angle - OVERHANG_TOL_DEG))
    above = P[T][:, :, 2].max(axis=1) > BED_TOL
    return float(A[(N[:, 2] < lim) & above].sum()), float(A.sum())


def bed_contact(P, T):
    """Area (mm2) of the facets lying flat on z = 0."""
    N, A = tri_normals(P, T)
    on = (N[:, 2] < -0.999) & (P[T][:, :, 2].max(axis=1) <= BED_TOL)
    return float(A[on].sum())


def _segments(P, T, z):
    """The oriented segments (material on the left, seen from +Z) where the
    plane at height z cuts the mesh: (p (k, 2), q (k, 2)), or None."""
    N, _A = tri_normals(P, T)
    tri = P[T]
    s = tri[:, :, 2] - z
    s = np.where(s == 0.0, 1e-9, s)
    neg = s < 0
    cross = neg.any(axis=1) & ~neg.all(axis=1)
    tri, s, N, neg = tri[cross], s[cross], N[cross], neg[cross]
    if not len(tri):
        return None
    # the vertex alone on its side of the plane, and the two across from it
    lone_neg = neg.sum(axis=1) == 1
    alone = np.where(lone_neg[:, None], neg, ~neg)
    i0 = alone.argmax(axis=1)
    rows = np.arange(len(tri))
    i1, i2 = (i0 + 1) % 3, (i0 + 2) % 3
    a, sa = tri[rows, i0], s[rows, i0]
    out = []
    for j in (i1, i2):
        b, sb = tri[rows, j], s[rows, j]
        t = (sa / (sa - sb))[:, None]
        out.append((a + t * (b - a))[:, :2])
    p, q = out
    # material on the left: walk along k x n, k = +Z
    flip = (q[:, 0] - p[:, 0]) * -N[:, 1] + (q[:, 1] - p[:, 1]) * N[:, 0] < 0
    p2 = np.where(flip[:, None], q, p)
    q2 = np.where(flip[:, None], p, q)
    return p2, q2


def section_area(P, T, z):
    """The area (mm2, holes taken out) of a closed mesh's slice at z."""
    seg = _segments(P, T, z)
    if seg is None:
        return 0.0
    p, q = seg
    return max(0.0, float((p[:, 0] * q[:, 1] - q[:, 0] * p[:, 1]).sum() / 2.0))


def section(P, T, z):
    """The slice of a closed mesh at height z: {"area" mm2 (holes taken
    out), "perimeter" mm (outer and inner), "pieces" (separate islands),
    "holes"}."""
    seg = _segments(P, T, z)
    if seg is None:
        return {"area": 0.0, "perimeter": 0.0, "pieces": 0, "holes": 0}
    p, q = seg
    segs = np.stack([p, q], axis=1)
    twice = p[:, 0] * q[:, 1] - q[:, 0] * p[:, 1]
    length = np.hypot(q[:, 0] - p[:, 0], q[:, 1] - p[:, 1])
    # loops: join segments at shared end points
    keys = {}
    parent = list(range(len(segs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    ends = np.round(segs * 2000).astype(np.int64).tolist()
    for k in range(len(segs)):
        for end in (0, 1):
            key = (ends[k][end][0], ends[k][end][1])
            other = keys.get(key)
            if other is None:
                keys[key] = k
            else:
                a, b = find(k), find(other)
                if a != b:
                    parent[a] = b
    loops = {}
    for k in range(len(segs)):
        r = find(k)
        loops[r] = loops.get(r, 0.0) + twice[k] / 2.0
    pieces = sum(1 for a in loops.values() if a > 1e-6)
    holes = sum(1 for a in loops.values() if a < -1e-6)
    return {"area": max(0.0, float(twice.sum() / 2.0)), "perimeter": float(length.sum()),
            "pieces": pieces, "holes": holes}


def report(points, tris, label="", planes=None):
    """One part's row: how it lies on the bed and what its first layer and
    overhangs are. Keys: label, flat_face_mm2, turned_deg, height_mm,
    first_layer {area, perimeter, pieces, holes, line_mm}, widest_mm2,
    overhang_mm2, overhang_pct, supports, flags [(level, sentence)].
    planes: the part's flat sides [(area, normal)] when the caller knows
    them exactly (brep_planes); else they are read from the mesh."""
    P, T = arrays(points, tris)
    if signed_volume(P, T) < 0:
        T = T[:, ::-1]
    chosen = choose_down(supporting_planes(P, T) if planes is None else planes)
    n = chosen[1] if chosen else None
    Q = lay_flat(P, n)
    height = float(Q[:, 2].max())
    first = section(Q, T, min(FIRST_LAYER_Z, height / 2.0))
    first["line_mm"] = round(2.0 * first["area"] / first["perimeter"], 2) \
        if first["perimeter"] > 0 else 0.0
    widest = first["area"]
    for i in range(1, 10):
        widest = max(widest, section_area(Q, T, height * i / 10.0 + 1e-4))
    over, tot = overhang(Q, T)
    turned = 0.0 if n is None else math.degrees(math.acos(max(-1.0, min(1.0, -n[2]))))
    row = {
        "label": label,
        "flat_face_mm2": round(chosen[0], 1) if chosen else 0.0,
        "down": [round(c, 4) for c in n] if n is not None else None,
        "turned_deg": round(turned, 1),
        "height_mm": round(height, 2),
        "volume_mm3": round(abs(signed_volume(P, T)), 1),
        "first_layer": {k: (round(v, 2) if isinstance(v, float) else v)
                        for k, v in first.items()},
        "widest_mm2": round(widest, 1),
        "overhang_mm2": round(over, 1),
        "overhang_pct": round(100.0 * over / tot, 1) if tot else 0.0,
        "supports": bool(over > max(OVERHANG_FLAG_MM2, OVERHANG_FLAG_SHARE * tot)),
    }
    row["flags"] = flags(row)
    return row


def flags(row):
    """[(level, sentence)] for a row. level "warning": the first layer will
    not hold as drawn. level "note": worth knowing before it is sliced."""
    out = []
    fl = row["first_layer"]
    # R1250, measured on the 64 examples: a small trim part (an eye, a
    # glint, a letter) with no flat side or a thin first layer is said in
    # a note; the warning is for a part that costs a print when it fails
    if not row["flat_face_mm2"]:
        out.append(("warning" if row.get("volume_mm3", SMALL_MM3) >= SMALL_MM3 else "note",
                    "no flat side to rest on: it will print on supports or a raft - "
                    "give it a flat base, or split it where it is widest"))
    elif fl["area"] > 0 and fl["line_mm"] < KNIFE_MM - KNIFE_TOL:
        out.append(("warning" if fl["area"] >= SMALL_FIRST_MM2 else "note",
                    "its first layer is a line only %.2f mm wide (%g mm2 in %d piece%s): "
                    "under two 0.4 mm lines it will not stick - widen the face it stands on, "
                    "and chamfer that edge on ONE side only"
                    % (fl["line_mm"], round(fl["area"], 1), fl["pieces"],
                       "" if fl["pieces"] == 1 else "s")))
    if row["flat_face_mm2"] and row["height_mm"] >= TALL_MM \
            and fl["area"] < SMALL_FOOT_SHARE * row["widest_mm2"]:
        out.append(("note",
                    "it stands on %g mm2 under a body %g mm2 wide and %g mm tall: "
                    "a brim, or a wider base" % (round(fl["area"]), round(row["widest_mm2"]),
                                                 round(row["height_mm"]))))
    if row["supports"]:
        out.append(("note",
                    "%g mm2 (%g %%) faces down steeper than 45 degrees: supports there"
                    % (round(row["overhang_mm2"]), row["overhang_pct"])))
    return out


def line(row):
    """The PRINT line ./check prints for one part."""
    if row.get("skipped"):
        return "PRINT %s: not judged (%s)" % (row["label"], row["skipped"])
    fl = row["first_layer"]
    if row["flat_face_mm2"]:
        lies = "on its %g mm2 flat side%s" % (
            round(row["flat_face_mm2"]),
            "" if row["turned_deg"] < 0.5 else " (turned %g deg)" % round(row["turned_deg"]))
    else:
        lies = "no flat side"
    bits = [lies,
            "first layer %g mm2 in %d piece%s, lines %.2f mm wide on average"
            % (round(fl["area"], 1), fl["pieces"], "" if fl["pieces"] == 1 else "s",
               fl["line_mm"]),
            ("supports: %g mm2 over 45 deg (%g %%)" % (round(row["overhang_mm2"]),
                                                       row["overhang_pct"]))
            if row["supports"] else "no supports"]
    return "PRINT %s: %s" % (row["label"], "; ".join(bits))


#: a shape with more faces than this is not judged (a note says so). Under
#: it every planar face is read: R1295 first read a many-faced shape from
#: its mesh instead, which lost small flat sides (a false "no flat side"
#: on a mesh-made part with a 36 mm2 base). What made it slow is gone: the
#: part's reach is worked out for all directions at once, and coplanar
#: faces are grouped by direction, so the time grows with the face count,
#: not its square.
MAX_BREP_FACES = 20000
#: products of directions x points worked out in one piece
_REACH_CHUNK = 4000000


class _Late(Exception):
    """The time budget ran out inside one part."""


def brep_planes(shape, points, tol=PLANE_TOL, deadline=None):
    """[(area mm2, outward unit normal)] of the PLANAR faces of a FreeCAD
    shape that it can rest on (no point of `points`, an (n, 3) array of
    the part's surface, lies beyond the plane), coplanar faces added up,
    largest first. The rule of export_tools.flat_faces. None for a shape
    with more than MAX_BREP_FACES faces; raises _Late when `deadline` (a
    time.time() value) passes on the way."""
    import time
    faces = shape.Faces
    if len(faces) > MAX_BREP_FACES:
        return None
    recs = []
    for i, f in enumerate(faces):
        if deadline is not None and i % 200 == 199 and time.time() > deadline:
            raise _Late()
        try:
            if f.Surface.__class__.__name__ != "Plane":
                continue
            u0, u1, v0, v1 = f.ParameterRange
            nv = f.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
            p0 = f.Vertexes[0].Point if f.Vertexes else f.CenterOfMass
            recs.append((nv.x, nv.y, nv.z, nv.x * p0.x + nv.y * p0.y + nv.z * p0.z, f.Area))
        except Exception:                               # noqa: BLE001
            continue
    if not recs:
        return []
    R = np.asarray(recs, dtype=float)
    N, D, A = R[:, :3], R[:, 3], R[:, 4]
    pts = np.asarray(points, dtype=float)
    # how far the part reaches along each direction, and against it
    uniq, inv = np.unique(np.round(N, 6) + 0.0, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    hi, lo = np.empty(len(uniq)), np.empty(len(uniq))
    step = max(1, _REACH_CHUNK // max(1, len(pts)))
    for s in range(0, len(uniq), step):
        if deadline is not None and time.time() > deadline:
            raise _Late()
        H = uniq[s:s + step] @ pts.T
        hi[s:s + step], lo[s:s + step] = H.max(axis=1), H.min(axis=1)
    buckets = {}               # rounded outward normal -> [[area, normal, d], ...]
    for i in range(len(R)):
        if hi[inv[i]] <= D[i] + tol:
            n, d = N[i], float(D[i])
        elif -lo[inv[i]] <= -D[i] + tol:        # the face is stored inside out
            n, d = -N[i], -float(D[i])
        else:
            continue
        groups = buckets.setdefault(tuple(np.round(n, 5) + 0.0), [])
        for g in groups:
            if float(g[1] @ n) > 1 - 1e-6 and abs(g[2] - d) < tol:
                g[0] += A[i]
                break
        else:
            groups.append([float(A[i]), n, d])
    out = [g for groups in buckets.values() for g in groups]
    out.sort(key=lambda g: -g[0])
    return [(float(a), tuple(float(x) for x in n)) for a, n, _d in out
            if a >= FLAT_MIN_MM2]


def shape_report(shape, label="", deflection=DEFLECTION_MM, deadline=None):
    """report() of a FreeCAD shape (tessellated at `deflection` mm), its
    flat sides taken from its planar faces. A part too fine to judge, or
    one that passes `deadline` (a time.time() value) on the way, comes
    back with "skipped"."""
    import time
    if np is None:
        return {"label": label, "skipped": "numpy is not available", "flags": []}
    pts, tris = shape.tessellate(deflection)
    if not tris:
        return {"label": label, "skipped": "no surface", "flags": []}
    if len(tris) > MAX_TRIANGLES:
        return {"label": label, "skipped": "%d facets" % len(tris), "flags": []}
    late = {"label": label, "skipped": "time budget", "flags": []}
    if deadline is not None and time.time() > deadline:
        return late
    P = [(p.x, p.y, p.z) for p in pts]
    try:
        planes = brep_planes(shape, np.asarray(P, dtype=float), deadline=deadline)
    except _Late:
        return late
    if planes is None:
        return {"label": label, "skipped": "%d faces" % len(shape.Faces), "flags": []}
    if deadline is not None and time.time() > deadline:
        return late
    return report(P, tris, label, planes=planes)


def reports(parts, budget_s=6.0):
    """Rows for [{"label", "shape"}]; parts past the time budget are
    skipped and say so. The budget is looked at between parts and between
    the steps of one part."""
    import time
    t0 = time.time()
    rows = []
    for p in parts:
        if time.time() - t0 > budget_s:
            rows.append({"label": p["label"], "skipped": "time budget", "flags": []})
            continue
        try:
            rows.append(shape_report(p["shape"], p["label"], deadline=t0 + budget_s))
        except Exception as exc:                        # noqa: BLE001
            rows.append({"label": p["label"], "skipped": "could not measure: %s" % exc,
                         "flags": []})
    return rows
