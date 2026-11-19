"""wiring_view - the Wiring view of the Atech modules page (R962).

The wiring diagram of the design in the sidebar, from agent_kit/
atech_wiring.py: the board with each module's port, plugged in or by cable,
then the same facts as selectable text (power modules, every connection,
the Atech SDK's cautions in full, what is not known yet), and Open large /
Export wiring (PDF, PNG, SVG).

It is port-level only, like the model: no pin numbers, wire colours,
currents or bus names. Every sentence a user sees is atech_wiring's or one
of the few below (the honesty test greps both files).

    wiring_mod()          atech_wiring, or None when it cannot be imported
    WiringView            paints an SVG keeping its aspect ratio
    WiringPanel           the view, its text and its two buttons
    export_wiring(w, p)   the sheet as .pdf (A4 landscape, 1 page), .png
                          (2400 px wide) or .svg
"""
import os
import sys

from PySide6 import QtCore, QtGui, QtSvg, QtWidgets

from . import style

#: The few words this file adds (the rest are atech_wiring's).
OPEN_LARGE = "Open large…"
EXPORT = "Export wiring…"
EXPORT_TITLE = "Export wiring"
FILTERS = "PDF (*.pdf);;Picture (*.png);;SVG (*.svg)"
H_POWER = "POWER MODULES"
H_CONNECTIONS = "CONNECTIONS"
H_CAUTIONS = "ATECH SDK CAUTIONS"
H_UNKNOWN = "NOT KNOWN YET"
SAVED = "Saved: %s"
NOT_SAVED = "Could not save the wiring: %s"
PNG_WIDTH = 2400


def _log(msg):
    try:
        import FreeCAD
        FreeCAD.Console.PrintLog("[Atech] wiring: %s\n" % msg)
    except Exception:                                   # noqa: BLE001
        pass


def wiring_mod():
    """agent_kit/atech_wiring (the kit put on sys.path the way capture.py
    does), or None when it cannot be imported."""
    try:
        kit = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_kit")
        if kit not in sys.path:
            sys.path.append(kit)
        import atech_wiring
        return atech_wiring
    except Exception as exc:                            # noqa: BLE001
        _log("atech_wiring: %r" % (exc,))
        return None


def panel_theme(aw, mode=None):
    """The panel diagram's colours: atech_wiring's light or dark set, on
    the page's own background and text colours."""
    try:
        m = mode or style.mode()
    except Exception:                                   # noqa: BLE001
        m = "light"
    t = dict(aw.DARK if m == "dark" else aw.LIGHT)
    try:
        tok = style.tokens(m)
        t.update({"bg": tok["panel"], "fg": tok["text"], "muted": tok["muted"]})
    except Exception:                                   # noqa: BLE001
        pass
    return t


def _renderer(svg_text):
    return QtSvg.QSvgRenderer(QtCore.QByteArray(svg_text.encode("utf-8")))


def _fit(src_w, src_h, rect):
    """The largest rect of src's aspect centred in rect (QRectF)."""
    if src_w <= 0 or src_h <= 0:
        return QtCore.QRectF(rect)
    k = min(rect.width() / src_w, rect.height() / src_h)
    w, h = src_w * k, src_h * k
    return QtCore.QRectF(rect.x() + (rect.width() - w) / 2,
                         rect.y() + (rect.height() - h) / 2, w, h)


# ------------------------------------------------------------- export
def export_wiring(w, path):
    """Write the wiring sheet of wiring dict w to path, by its suffix:
    .pdf (A4 landscape, one page), .png (2400 px wide, white) or .svg.
    Returns the path; raises ValueError for another suffix."""
    aw = wiring_mod()
    if aw is None:
        raise RuntimeError("the wiring model is not available")
    text = aw.svg(w, "sheet")
    ext = os.path.splitext(path)[1].lower()
    if ext == ".svg":
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path
    r = _renderer(text)
    size = r.defaultSize()
    if ext == ".png":
        h = int(round(PNG_WIDTH * size.height() / float(max(size.width(), 1))))
        img = QtGui.QImage(PNG_WIDTH, h, QtGui.QImage.Format_ARGB32)
        img.fill(QtGui.QColor("#ffffff"))
        p = QtGui.QPainter(img)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setRenderHint(QtGui.QPainter.TextAntialiasing)
        r.render(p, QtCore.QRectF(0, 0, PNG_WIDTH, h))
        p.end()
        if not img.save(path, "PNG"):
            raise OSError("could not write %s" % path)
        return path
    if ext == ".pdf":
        writer = QtGui.QPdfWriter(path)
        writer.setPageSize(QtGui.QPageSize(QtGui.QPageSize.A4))
        writer.setPageOrientation(QtGui.QPageLayout.Landscape)
        writer.setPageMargins(QtCore.QMarginsF(10, 10, 10, 10), QtGui.QPageLayout.Millimeter)
        writer.setResolution(150)
        writer.setTitle(aw.TITLE % (w.get("project") or "Design"))
        writer.setCreator(style.PRODUCT)
        p = QtGui.QPainter(writer)
        page = QtCore.QRectF(0, 0, writer.width(), writer.height())
        r.render(p, _fit(size.width(), size.height(), page))
        p.end()
        return path
    raise ValueError("unknown wiring export type: %r (use .pdf, .png or .svg)" % ext)


# ------------------------------------------------------------- widgets
class WiringView(QtWidgets.QWidget):
    """An SVG painted at the widget's width, its height following the
    SVG's aspect ratio."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WiringView")
        self._r = None
        self._ratio = 1.0
        self.setAccessibleName("Wiring diagram")
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)

    def set_svg(self, text, description=""):
        self._r = _renderer(text) if text else None
        if self._r is not None and self._r.isValid():
            s = self._r.defaultSize()
            self._ratio = s.height() / float(max(s.width(), 1))
        self.setAccessibleDescription(description)
        self._fit_height(self.width())
        self.update()

    def renderer(self):
        return self._r

    def _fit_height(self, width):
        if width > 0:
            self.setFixedHeight(max(1, int(round(width * self._ratio))))

    def resizeEvent(self, ev):                         # noqa: N802
        super().resizeEvent(ev)
        self._fit_height(ev.size().width())

    def sizeHint(self):                                # noqa: N802
        w = 360
        return QtCore.QSize(w, int(round(w * self._ratio)))

    def paintEvent(self, ev):                          # noqa: N802
        if self._r is None or not self._r.isValid():
            return
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setRenderHint(QtGui.QPainter.TextAntialiasing)
        s = self._r.defaultSize()
        self._r.render(p, _fit(s.width(), s.height(), QtCore.QRectF(self.rect())))
        p.end()


class OpenLarge(QtWidgets.QDialog):
    """The wiring sheet in its own resizable window."""

    def __init__(self, w, parent=None):
        super().__init__(parent)
        aw = wiring_mod()
        self.setWindowTitle(aw.TITLE % (w.get("project") or "Design"))
        self.setObjectName("WiringLarge")
        self.resize(1100, 760)
        lay = QtWidgets.QVBoxLayout(self)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.view = WiringView()
        self.view.set_svg(aw.svg(w, "sheet"), "\n".join(aw.lines(w)))
        scroll.setWidget(self.view)
        lay.addWidget(scroll)


def _body(text=""):
    lab = QtWidgets.QLabel(text)
    lab.setObjectName("WiringText")
    lab.setWordWrap(True)
    lab.setTextFormat(QtCore.Qt.PlainText)
    lab.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
    # Ignored across: long lines wrap at the sidebar's width, never widen it
    lab.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Minimum)
    return lab


def _head(text):
    lab = QtWidgets.QLabel(text)
    lab.setObjectName("MSection")
    return lab


class WiringPanel(QtWidgets.QWidget):
    """The Wiring view: the panel diagram, the facts as text, Open large
    and Export wiring. set_wiring(w) shows a wiring dict (atech_wiring.build)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WiringPanel")
        self.aw = wiring_mod()
        self.w = None
        self.folder = None
        self._large = None
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        self.view = WiringView()
        lay.addWidget(self.view)
        self.empty = _body(self.aw.EMPTY if self.aw else "")
        lay.addWidget(self.empty)
        self.sections = {}
        for key, title in (("power", H_POWER), ("connections", H_CONNECTIONS),
                           ("cautions", H_CAUTIONS), ("unknown", H_UNKNOWN)):
            h, b = _head(title), _body()
            lay.addWidget(h)
            lay.addWidget(b)
            self.sections[key] = (h, b)
        row = QtWidgets.QHBoxLayout()
        self.btn_large = QtWidgets.QPushButton(OPEN_LARGE)
        self.btn_large.setObjectName("MGhost")
        self.btn_large.setAccessibleName("Open the wiring diagram large")
        self.btn_large.clicked.connect(self.open_large)
        self.btn_export = QtWidgets.QPushButton(EXPORT)
        self.btn_export.setObjectName("MGhost")
        self.btn_export.setAccessibleName("Export the wiring diagram as PDF, picture or SVG")
        self.btn_export.clicked.connect(self.export_dialog)
        for b in (self.btn_large, self.btn_export):
            b.setCursor(QtCore.Qt.PointingHandCursor)
            row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)
        self.status = _body()
        self.status.hide()
        lay.addWidget(self.status)
        lay.addStretch(1)
        self.set_wiring(None)

    # ---------------------------------------------------------- state
    def set_wiring(self, w, folder=None):
        """Show wiring dict w (None or no connections: the empty state)."""
        self.w = w
        self.folder = folder
        aw = self.aw
        if aw is None:
            return
        if w is None:
            w = aw.build(None, firmware_on=False)
        conns = w["connections"]
        self.view.set_svg(aw.svg(w, "panel", panel_theme(aw)), "\n".join(aw.lines(w)))
        self.empty.setVisible(not conns)
        for key, (h, b) in self.sections.items():
            text = self._section(key, w)
            h.setVisible(bool(conns) and bool(text))
            b.setVisible(bool(conns) and bool(text))
            b.setText(text)
        for btn in (self.btn_large, self.btn_export):
            btn.setEnabled(bool(conns))
        self.status.hide()

    def _section(self, key, w):
        aw = self.aw
        if key == "power":
            return "\n".join([w["power"]["text"] or ""] + list(w["notes"])).strip()
        if key == "connections":
            return "\n".join([aw.connection_text(c) for c in w["connections"]] + list(w["flags"]))
        if key == "cautions":
            return "\n\n".join(c["text"] for c in w["cautions"])
        if key == "unknown":
            return "\n".join(list(w["unknown"]) + [aw.PINOUT_ASK])
        return ""

    def restyle(self):
        if self.w is not None or self.aw is not None:
            self.set_wiring(self.w, self.folder)

    # ---------------------------------------------------------- actions
    def open_large(self):
        if not self.w or not self.w["connections"]:
            return
        self._large = OpenLarge(self.w, self.window())
        self._large.show()

    def default_path(self):
        name = "%s wiring.pdf" % ((self.w or {}).get("project") or "Design")
        name = name.replace(os.sep, "-")
        folder = self.folder if self.folder and os.path.isdir(self.folder) \
            else os.path.expanduser("~")
        return os.path.join(folder, name)

    def export_dialog(self):
        if not self.w or not self.w["connections"]:
            return
        path, flt = QtWidgets.QFileDialog.getSaveFileName(
            self, EXPORT_TITLE, self.default_path(), FILTERS)
        if not path:
            return
        if not os.path.splitext(path)[1]:
            path += ".png" if "png" in (flt or "") else ".svg" if "svg" in (flt or "") \
                else ".pdf"
        self.export_to(path)

    def export_to(self, path):
        try:
            export_wiring(self.w, path)
            self.status.setText(SAVED % path)
        except Exception as exc:                        # noqa: BLE001
            _log("export: %r" % (exc,))
            self.status.setText(NOT_SAVED % exc)
        self.status.show()
        return path
