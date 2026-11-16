"""mesh_picture - a flat-shaded isometric PNG of a mesh, drawn with
QPainter (no OpenGL, so it runs in freecadcmd). Used by the index builders
of the off-the-shelf parts (build_shelf_index.py) and the KiCad components
(build_kicad3d_index.py) for the pictures their dialog shows.
"""
import os


PICTURE_PX = (330, 270)       # 1.5 x the dialog's 220 x 180 box


def render_picture(mesh, path):
    """A flat-shaded isometric picture of a mesh (PNG, transparent), drawn
    with QPainter: back faces culled, far triangles first. For the dialog,
    as the library has its own picture for only 3 of the curated parts."""
    import numpy as np
    pts = np.array([[p.x, p.y, p.z] for p in mesh.Points], dtype=float)
    tri = np.array(mesh.Topology[1], dtype=int)
    return render_triangles(pts, tri, path)


def render_triangles(pts, tri, path, colours=None, cull=True):
    """render_picture of points (n x 3, Y up) and triangles (m x 3).
    colours: m x 3 RGB in 0..1 per triangle (one blue-grey when None).
    cull=False draws both sides, shaded by |normal . light|, for meshes
    whose triangle winding is not consistent (a STEP's faces tessellated
    one by one)."""
    import math
    import numpy as np
    from PySide6 import QtCore, QtGui
    if QtGui.QGuiApplication.instance() is None:
        render_picture.app = QtGui.QGuiApplication(["shelf"])
    pts = np.asarray(pts, dtype=float)
    tri = np.asarray(tri, dtype=int)
    P = pts - (pts.min(0) + pts.max(0)) / 2.0
    yaw, pitch = math.radians(35.0), math.radians(28.0)
    cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
    R = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.eye(3)
    R = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]]) @ R
    V = P @ R.T                                   # x right, y up, z toward the viewer
    T = V[tri]
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    ln = np.linalg.norm(n, axis=1)
    keep = (ln > 1e-12) & ((n[:, 2] > 0) if cull else True)
    T, n, ln = T[keep], n[keep], ln[keep]
    n = n / ln[:, None]
    if not cull:
        n = n * np.where(n[:, 2:3] < 0, -1.0, 1.0)  # face the viewer
    light = np.array([-0.35, 0.55, 0.75])
    light /= np.linalg.norm(light)
    shade = 0.35 + 0.65 * np.clip(n @ light, 0.0, 1.0)
    if colours is None:
        rgb = np.tile(np.array([96, 126, 160], dtype=float), (len(T), 1))
    else:
        rgb = 255.0 * (0.12 + 0.88 * np.asarray(colours, dtype=float)[keep])
    order = np.argsort(T[:, :, 2].mean(1))
    w, h = PICTURE_PX
    s = 0.86 * min(w / max(float(np.ptp(V[:, 0])), 1e-9),
                   h / max(float(np.ptp(V[:, 1])), 1e-9))
    img = QtGui.QImage(w, h, QtGui.QImage.Format_ARGB32)
    img.fill(QtCore.Qt.transparent)
    p = QtGui.QPainter(img)
    p.setRenderHint(QtGui.QPainter.Antialiasing, True)
    for i in order:
        c = (rgb[i] * shade[i]).clip(0, 255).astype(int)
        col = QtGui.QColor(int(c[0]), int(c[1]), int(c[2]))
        p.setPen(QtGui.QPen(col, 0.6))
        p.setBrush(col)
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(w / 2 + x * s, h / 2 - y * s)
                                       for x, y, _z in T[i]]))
    p.end()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not img.save(path, "PNG"):
        raise SystemExit("could not write %s" % path)
    return path
