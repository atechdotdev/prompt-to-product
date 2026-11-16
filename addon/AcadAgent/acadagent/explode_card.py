"""explode_card - the Exploded view card over the 3D view (R810).

The exploded view was one click on the view bar that threw every part out
from the middle, cables and all, with the camera left where it was and how
far apart only in Show and hide's popover. People could not tell what they
were looking at. Now, whenever a design is apart (the view-bar button, E,
the Atech menu), this card shows at the top right of the 3D view:

    How:          Out from the middle | In layers (stacked along Z)
    How far:      the slider, live
    Step through: < Part 3 of 12: Lid >  selects the part in 3D and says
                  what it is (a printed part, an Atech module out of port 5)
    Fit to view   the camera takes in the parts where they are now
    Put back      every part back where it belongs (as X, Esc and E)

Modules slide straight out of their ports, and the board, its cables and
the cabled modules stay where they are (export_tools.Exploder, R810).
Display only, as before: nothing here changes the document.
"""
from . import export_tools as et


def _log(msg):
    try:
        import FreeCAD
        FreeCAD.Console.PrintLog("Atech exploded view: %s\n" % msg)
    except Exception:                                     # noqa: BLE001
        pass


def _select(doc, o):
    try:
        import FreeCADGui
        FreeCADGui.Selection.clearSelection()
        if o is not None:
            FreeCADGui.Selection.addSelection(doc.Name, o.Name)
    except Exception as exc:                              # noqa: BLE001
        _log("select: %r" % (exc,))


def _fit():
    try:
        from . import viewport
        viewport.fit_all()
    except Exception as exc:                              # noqa: BLE001
        _log("fit: %r" % (exc,))


EXPLODE_QSS = """
#XSeg {{ background: {sunken}; border: 1px solid {line}; border-radius: 10px; }}
#XSegBtn {{
    background: transparent; color: {muted}; border: none; border-radius: 8px;
    min-height: 26px; max-height: 26px; padding: 0 8px;
    font-family: {UI}; font-size: 12px; font-weight: 500;
}}
#XSegBtn:hover {{ color: {text}; }}
#XSegBtn:checked {{ background: {panel}; color: {text}; border: 1px solid {line}; font-weight: 600; }}
#XLabel {{ color: {muted}; font-family: {UI}; font-size: 12px; }}
#XValue {{ color: {text}; font-family: {MONO}; font-size: 11px; }}
#XStep {{ background: {sunken}; border: 1px solid {line}; border-radius: 12px; }}
#XPart {{ color: {text}; font-family: {UI}; font-size: 13px; font-weight: 600; }}
#XInfo {{ color: {muted}; font-family: {UI}; font-size: 11px; }}
#XArrow {{
    background: {panel}; color: {text}; border: 1px solid {line}; border-radius: 14px;
    min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px;
    font-size: 16px; padding: 0 0 2px 0;
}}
#XArrow:hover {{ background: {hover}; }}
#XArrow:disabled {{ color: {dim}; }}
#XKeys {{ color: {dim}; font-family: {UI}; font-size: 11px; }}
"""


def _cube_clearance():
    """Room the navigation cube takes at the top right of the 3D view, so
    the card sits under it rather than over it (0 when it is elsewhere)."""
    try:
        import FreeCAD
        v = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View")
        nv = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/NaviCube")
        if not v.GetBool("ShowNaviCube", True):
            return 0
        if v.GetInt("CornerNaviCube", 1) != 1:      # 1 = top right
            return 0
        size = nv.GetInt("CubeSize", 0) or v.GetInt("NaviCubeSize", 132)
        return int(size) + 8
    except Exception:                                     # noqa: BLE001
        return 0


def ExplodeCard(parent=None, doc_fn=et._active_doc, select_fn=None, fit_fn=None):
    """The card. `select_fn(doc, obj)` and `fit_fn()` default to the 3D
    selection and viewport.fit_all; tests pass their own."""
    from PySide6 import QtCore, QtWidgets
    from . import measure

    Card = measure._card_class()
    select_fn = select_fn or _select
    fit_fn = fit_fn or _fit

    class _ExplodeCard(Card):
        def __init__(self):
            super().__init__("Exploded view", parent)
            self.setObjectName("MeasureCard")
            self.doc_fn = doc_fn
            self.doc = None
            self.step = -1
            self._sync = False
            self.setToolTip("Only the picture moves: every part goes back "
                            "when you close this, build or save.")

            # How: one segmented switch, the two halves the full width
            seg = QtWidgets.QFrame()
            seg.setObjectName("XSeg")
            seg.setAttribute(QtCore.Qt.WA_StyledBackground, True)
            row = QtWidgets.QHBoxLayout(seg)
            row.setContentsMargins(3, 3, 3, 3)
            row.setSpacing(2)
            self.group = QtWidgets.QButtonGroup(self)
            self.group.setExclusive(True)
            self.chips = {}
            tips = {"out": "Every part moves away from the middle of the design",
                    "layers": "The printed parts stack up along Z, bottom to top"}
            for key, label in et.EXPLODE_MODES:
                b = QtWidgets.QPushButton(label)
                b.setObjectName("XSegBtn")
                b.setCheckable(True)
                b.setCursor(QtCore.Qt.PointingHandCursor)
                b.setToolTip(tips.get(key, label))
                b.setAccessibleName(label)
                b.clicked.connect(lambda _=False, k=key: self.set_mode(k))
                self.group.addButton(b)
                self.chips[key] = b
                row.addWidget(b, 1)
            self.lay.addWidget(seg)

            # Spread: label, slider, value on one line
            frow = QtWidgets.QHBoxLayout()
            frow.setSpacing(10)
            far = QtWidgets.QLabel("Spread")
            far.setObjectName("XLabel")
            self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            self.slider.setObjectName("MSlider")
            self.slider.setRange(5, 100)
            self.slider.setAccessibleName("How far apart")
            self.slider.setToolTip("How far apart the parts go")
            self.slider.valueChanged.connect(self._on_slider)
            self.amount = QtWidgets.QLabel("")
            self.amount.setObjectName("XValue")
            self.amount.setFixedWidth(38)
            self.amount.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            far.setBuddy(self.slider)
            frow.addWidget(far)
            frow.addWidget(self.slider, 1)
            frow.addWidget(self.amount)
            self.lay.addLayout(frow)

            # Step through the parts: an inset box, ‹ name › with what it is
            box = QtWidgets.QFrame()
            box.setObjectName("XStep")
            box.setAttribute(QtCore.Qt.WA_StyledBackground, True)
            srow = QtWidgets.QHBoxLayout(box)
            srow.setContentsMargins(6, 6, 6, 6)
            srow.setSpacing(6)
            self.btn_prev = QtWidgets.QPushButton("‹")
            self.btn_next = QtWidgets.QPushButton("›")
            for b, name, tip in ((self.btn_prev, "Previous part", "Previous part (←)"),
                                 (self.btn_next, "Next part", "Next part (→)")):
                b.setObjectName("XArrow")
                b.setCursor(QtCore.Qt.PointingHandCursor)
                b.setAccessibleName(name)
                b.setToolTip(tip)
            self.btn_prev.clicked.connect(lambda: self.go(-1))
            self.btn_next.clicked.connect(lambda: self.go(1))
            mid = QtWidgets.QVBoxLayout()
            mid.setSpacing(1)
            self.part_name = QtWidgets.QLabel("")
            self.part_name.setObjectName("XPart")
            self.part_name.setWordWrap(True)
            self.part_name.setAlignment(QtCore.Qt.AlignCenter)
            self.part_info = QtWidgets.QLabel("")
            self.part_info.setObjectName("XInfo")
            self.part_info.setWordWrap(True)
            self.part_info.setAlignment(QtCore.Qt.AlignCenter)
            mid.addWidget(self.part_name)
            mid.addWidget(self.part_info)
            srow.addWidget(self.btn_prev)
            srow.addLayout(mid, 1)
            srow.addWidget(self.btn_next)
            self.lay.addWidget(box)

            brow = QtWidgets.QHBoxLayout()
            brow.setSpacing(8)
            self.btn_fit = QtWidgets.QPushButton("Fit to view")
            self.btn_fit.setObjectName("MGhost")
            self.btn_fit.setToolTip("Take in every part where it is now")
            self.btn_back = QtWidgets.QPushButton("Put back")
            self.btn_back.setObjectName("MPrimary")
            self.btn_back.setToolTip("Every part back where it belongs (E, Esc)")
            for b in (self.btn_fit, self.btn_back):
                b.setCursor(QtCore.Qt.PointingHandCursor)
                b.setAccessibleName(b.text())
                brow.addWidget(b, 1)
            self.btn_fit.clicked.connect(lambda: et._guard(fit_fn))
            self.btn_back.clicked.connect(self.close_card)
            self.lay.addLayout(brow)
            keys = QtWidgets.QLabel("← → step  ·  E or Esc put back")
            keys.setObjectName("XKeys")
            keys.setAlignment(QtCore.Qt.AlignCenter)
            self.lay.addWidget(keys)
            self.closed.connect(self._on_closed)
            et.on_explode_changed(self._follow)

        # -- placement: top right, under the navigation cube, so Measure's
        # card (top left) and the cube both stay clear
        def place(self):
            p = self.parentWidget()
            if p is None:
                return
            self.adjustSize()
            top = 16 + _cube_clearance()
            h = min(self.sizeHint().height(), max(120, p.height() - top - 16))
            self.setGeometry(max(16, p.width() - self.width() - 16), top, self.width(), h)
            self.raise_()

        def restyle(self):
            super().restyle()
            from . import style
            self.setStyleSheet(self.styleSheet() + style.qss(EXPLODE_QSS, reset=False))

        def showEvent(self, ev):                      # noqa: N802
            # Whatever shows the card, it shows styled and in its place.
            if not getattr(self, "_styled", False):
                self._styled = True
                et._guard(self.restyle)
            super().showEvent(ev)

        def keyPressEvent(self, ev):                  # noqa: N802
            k = ev.key()
            if k in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Up):
                self.go(-1)
                return
            if k in (QtCore.Qt.Key_Right, QtCore.Qt.Key_Down):
                self.go(1)
                return
            if k == QtCore.Qt.Key_E:
                self.close_card()
                return
            super().keyPressEvent(ev)

        # -- state
        def open_for(self, doc, fit=True):
            """Show the card for doc (apart already, or apart now)."""
            if doc is None:
                return
            self.doc = doc
            if et.explode_amount(doc) <= 0.0:
                self._sync = True                 # no second open from _follow
                try:
                    et.set_explode(doc, et._LAST_EXPLODE["factor"] or et.DEFAULT_EXPLODE)
                finally:
                    self._sync = False
            self.step = -1
            self.refresh()
            if not getattr(self, "is_open", False):
                self.open_card()
            self.setFocus(QtCore.Qt.OtherFocusReason)
            if fit:
                et._guard(fit_fn)

        def refresh(self):
            self._sync = True
            try:
                doc = self.doc
                amount = et.explode_amount(doc)
                self.slider.setValue(max(5, int(round(amount * 100))))
                self.amount.setText("%d%%" % self.slider.value())
                mode = et.explode_mode(doc)
                for k, b in self.chips.items():
                    b.setChecked(k == mode)
                self._show_step()
            finally:
                self._sync = False

        def parts(self):
            return et.explode_parts(self.doc)

        def _show_step(self):
            ps = self.parts()
            many = len(ps) > 0
            self.btn_prev.setEnabled(many)
            self.btn_next.setEnabled(many)
            if not ps:
                self.part_name.setText("Nothing to pull apart")
                self.part_info.setText("This design has one part, or only "
                                       "the board and its cables.")
                return
            if not 0 <= self.step < len(ps):
                self.part_name.setText("%d parts apart" % len(ps))
                self.part_info.setText("Step through them one at a time")
                return
            o = ps[self.step]
            self.part_name.setText("%d of %d: %s" % (self.step + 1, len(ps), o.Label))
            self.part_info.setText(et.describe_part(o))

        def go(self, delta):
            ps = self.parts()
            if not ps:
                return
            if not 0 <= self.step < len(ps):
                self.step = 0 if delta > 0 else len(ps) - 1
            else:
                self.step = (self.step + delta) % len(ps)
            self._show_step()
            et._guard(lambda: select_fn(self.doc, ps[self.step]))

        def set_mode(self, mode):
            if self.doc is None:
                return
            self._sync = True
            try:
                et.set_explode(self.doc, self.slider.value() / 100.0, mode=mode)
            finally:
                self._sync = False
            self.step = -1
            self.refresh()
            et._guard(fit_fn)

        def _on_slider(self, v):
            self.amount.setText("%d%%" % v)
            if self._sync or self.doc is None:
                return
            self._sync = True
            try:
                et.set_explode(self.doc, v / 100.0)
            finally:
                self._sync = False

        def _follow(self, doc, factor):
            """E, the view bar, the menu or Show and hide changed it."""
            try:
                if self._sync:
                    return
                if factor <= 0.0:
                    if getattr(self, "is_open", False) and (self.doc is None or doc is self.doc):
                        self.doc = None
                        self.close_card()
                    return
                if doc is et._active_doc() or doc is self.doc:
                    if not getattr(self, "is_open", False) or doc is not self.doc:
                        self.open_for(doc, fit=True)
                    else:
                        self.refresh()
            except RuntimeError:              # the card is gone
                raise

        def _on_closed(self):
            doc, self.doc = self.doc, None
            if doc is not None and et.explode_amount(doc) > 0.0:
                et.set_explode(doc, 0.0)
                et._guard(lambda: select_fn(doc, None))
                et._guard(fit_fn)

    return _ExplodeCard()
