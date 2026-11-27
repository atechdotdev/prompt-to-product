"""fit_view - the Fit test window (R1240).

Export and share -> Fit test...:

    1. "Make the fit test" opens a new document with the coupon
       (cad.fit_coupon: five pucks with D-bores 3.2 to 3.6 for the DC
       Motor's shaft, and a plate with three windows a module passes
       through). Print it as any design.
    2. Say which puck was snug on the shaft and which window the module
       slid through, for which printer and filament.
    3. Save. The numbers go to ~/Documents/Atech Products/fit_user.json
       (p2p_fitlog) and every design after uses them: the agent's fit
       tables, cad.fit(), cad.d_bore() and cad.wheel(flat=True).

Plain Qt widgets; the logic is agent_kit/p2p_fitlog.py (no FreeCAD there).
FreeCAD is touched only by make_coupon().
"""
from PySide6 import QtCore, QtWidgets

from . import p2p_product

MATERIALS = ("PLA", "PETG", "PETG-CF", "ABS", "ASA", "TPU")
INTRO = ("Printers and filaments differ by a few tenths of a millimetre. Print the fit "
         "test once, tell the app what fitted, and every design after is drawn for "
         "your printer.")


def _log(msg):
    try:
        import FreeCAD
        FreeCAD.Console.PrintLog("Atech fit: %s\n" % msg)
    except Exception:                                     # noqa: BLE001
        pass


def default_profile():
    """(printer, filament) Bambu Studio has selected, or ("", "") - only
    to pre-fill the two fields."""
    try:
        from . import print_plates
        prof = print_plates.bambu_profile() or {}
    except Exception as exc:                              # noqa: BLE001
        _log("no Bambu profile: %r" % (exc,))
        return "", ""
    return str(prof.get("model") or ""), material_of(prof.get("filament"))


def material_of(preset_name):
    """The filament kind in a preset's name ("Bambu PETG-CF @BBL H2S" ->
    "PETG-CF"), or ""."""
    name = str(preset_name or "").upper()
    for m in sorted(MATERIALS, key=len, reverse=True):
        if m in name:
            return m
    return ""


def make_coupon():
    """A new document holding the fit test's parts, bed side down. Returns
    the document."""
    import FreeCAD
    cad = p2p_product.kit("atech_cad")
    doc = FreeCAD.newDocument("Fit_test")
    for label, shape in cad.fit_coupon("all").items():
        o = doc.addObject("Part::Feature", label)
        o.Shape = shape
    doc.recompute()
    return doc


class FitDialog(QtWidgets.QDialog):
    """Printer, filament, the snug puck and the tightest window; Save
    writes fit_user.json."""
    saved = QtCore.Signal(str)

    def __init__(self, parent=None, home=None):
        super().__init__(parent)
        self.setObjectName("AtechFitTest")
        self.setWindowTitle("Fit test")
        self.resize(560, 460)
        self.home = home
        self.L = p2p_product.kit("p2p_fitlog")
        self.data = self.L.load(home)
        v = QtWidgets.QVBoxLayout(self)
        intro = QtWidgets.QLabel(INTRO)
        intro.setWordWrap(True)
        v.addWidget(intro)
        self.btn_make = QtWidgets.QPushButton("Make the fit test")
        self.btn_make.setObjectName("fitMake")
        self.btn_make.setToolTip("Opens a new project with five pucks and a gauge plate: "
                                 "print it, then come back here")
        self.btn_make.clicked.connect(self._make)
        v.addWidget(self.btn_make, 0, QtCore.Qt.AlignLeft)

        form = QtWidgets.QFormLayout()
        printer, material = "", ""
        if self.data.get("active"):
            prof = self.data["profiles"][self.data["active"]]
            printer, material = prof.get("printer", ""), prof.get("material", "")
        else:
            printer, material = default_profile()
        self.printer = QtWidgets.QLineEdit(printer)
        self.printer.setObjectName("fitPrinter")
        self.printer.setPlaceholderText("e.g. Bambu X1C")
        self.material = QtWidgets.QComboBox()
        self.material.setObjectName("fitMaterial")
        self.material.setEditable(True)
        self.material.addItems(MATERIALS)
        self.material.setCurrentText(material or "PLA")
        self.puck = QtWidgets.QComboBox()
        self.puck.setObjectName("fitPuck")
        self.puck.addItem("Not tried yet", "")
        for p in self.L.PUCKS:
            self.puck.addItem("%s (%.1f mm)" % (p, int(p) / 10.0), p)
        self.window = QtWidgets.QComboBox()
        self.window.setObjectName("fitWindow")
        self.window.addItem("Not tried yet", "")
        for w in self.L.WINDOWS:
            self.window.addItem("%s (%.1f mm each side)" % (w, int(w) / 10.0), w)
        form.addRow("Printer", self.printer)
        form.addRow("Filament", self.material)
        form.addRow("Puck that is snug on the motor shaft", self.puck)
        form.addRow("Tightest window a module slides through", self.window)
        v.addLayout(form)

        self.now = QtWidgets.QLabel()
        self.now.setObjectName("fitNow")
        self.now.setWordWrap(True)
        self.now.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        v.addWidget(self.now, 1)
        self.error = QtWidgets.QLabel()
        self.error.setObjectName("fitError")
        self.error.setWordWrap(True)
        v.addWidget(self.error)

        row = QtWidgets.QHBoxLayout()
        self.btn_forget = QtWidgets.QPushButton("Forget this printer's results")
        self.btn_forget.setObjectName("fitForget")
        self.btn_forget.clicked.connect(self.forget)
        row.addWidget(self.btn_forget)
        row.addStretch(1)
        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save
                                        | QtWidgets.QDialogButtonBox.Close)
        bb.accepted.connect(self.save)
        bb.rejected.connect(self.close)
        row.addWidget(bb)
        v.addLayout(row)
        self.printer.editingFinished.connect(self._show)
        self.material.currentTextChanged.connect(lambda _t: self._show())
        self._show()

    # ------------------------------------------------------------ state
    def _profile(self):
        return self.L.profile_name(self.printer.text(), self.material.currentText())

    def _show(self):
        """What is stored for the printer and filament in the two fields."""
        name = self._profile()
        view = dict(self.data, active=name if name in self.data["profiles"] else None)
        rows = self.L.rows(view)
        if not rows:
            self.now.setText("<b>%s</b><br>No results yet: the app's own values are used."
                             % name)
            return
        lines = ["<b>%s</b>" % name]
        for r in rows:
            lines.append("%s: <b>%s</b> (the app's value: %s)%s" % (
                r["what"], self.L._fmt(r["value"]), self.L._fmt(r["table"]),
                (" - " + r["note"]) if r["note"] else ""))
        self.now.setText("<br>".join(lines))

    def set(self, printer=None, material=None, puck=None, window=None):
        """For tests and keyboard users: fill the fields."""
        if printer is not None:
            self.printer.setText(printer)
        if material is not None:
            self.material.setCurrentText(material)
        if puck is not None:
            self.puck.setCurrentIndex(max(0, self.puck.findData(puck)))
        if window is not None:
            self.window.setCurrentIndex(max(0, self.window.findData(window)))
        self._show()

    # ---------------------------------------------------------- actions
    def save(self):
        """Store what the fields say; returns the summary line, or None
        when there was nothing to store or it was refused."""
        self.error.setText("")
        puck, window = self.puck.currentData(), self.window.currentData()
        if not puck and not window:
            self.error.setText("Choose the puck or the window first: there is nothing to "
                               "save yet.")
            return None
        try:
            self.L.use_profile(self.data, self.printer.text(), self.material.currentText())
            if puck:
                self.L.coupon_result(self.data, puck)
            if window:
                self.L.gauge_result(self.data, window)
            self.L.save(self.data, self.home)
        except (ValueError, OSError) as exc:
            self.error.setText("Not saved: %s" % exc)
            return None
        line = self.L.summary(self.data)
        self._show()
        self.saved.emit(line)
        return line

    def forget(self):
        """Drop the results of the printer and filament in the fields."""
        self.error.setText("")
        name = self._profile()
        if name in self.data["profiles"]:
            del self.data["profiles"][name]
            if self.data.get("active") == name:
                self.data["active"] = next(iter(sorted(self.data["profiles"])), None)
            try:
                self.L.save(self.data, self.home)
            except OSError as exc:
                self.error.setText("Not saved: %s" % exc)
        self._show()

    def _make(self):
        try:
            make_coupon()
            self.error.setText("The fit test is open as a new project. Print it "
                               "(Export and share, Print), then come back here.")
        except Exception as exc:                          # noqa: BLE001
            self.error.setText("The fit test could not be made: %s" % exc)


def open_fit_test(parent=None):
    d = FitDialog(parent)
    d.show()
    return d
