"""Make it: from the design to the product in hand (R1004).

The 7 steps of product.steps() for the open design, each with its state,
one line and the button that does it (the chat, the electrical suite, the
firmware, the parts list, Print, the assembly steps, Get it made), and
"Make the product pack": one folder with the print files, the parts list,
the electrical report, the firmware and the assembly steps, plus
product.html to show it.

    open_make_it(doc=None, parent=None)
"""
import os
import tempfile

from PySide6 import QtCore, QtGui, QtWidgets

from . import product, sdk_tools, style

TITLE = "%s – make it"
STATE_COLOUR = {product.DONE: "ok", product.READY: "accent", product.TODO: "dim",
                product.WARN: "warn", product.BLOCKED: "fail"}
ICONS = {"box": "cube", "cpu": "cpu", "code": "terminal", "list": "layers",
         "printer": "upload", "wrench": "settings", "package": "sparkles"}

QSS = """
#MakeIt {{ background: {base}; }}
#MkHead {{ background: {panel}; border-bottom: 1px solid {line}; }}
#MkTitle {{ color: {text}; font-family: 'Sen', {UI}; font-size: 22px; font-weight: 700; }}
#MkSub {{ color: {muted}; font-family: {UI}; font-size: 12px; }}
#MkBar {{ background: {track}; border: none; border-radius: 4px; max-height: 8px;
    min-height: 8px; }}
#MkBar::chunk {{ background: {ok}; border-radius: 4px; }}
#MkStep {{ background: {panel}; border: 1px solid {line}; border-radius: 12px; }}
#MkStep[current="true"] {{ border: 1px solid {accent}; }}
#MkNum {{ color: #ffffff; font-family: {UI}; font-size: 12px; font-weight: 700;
    border-radius: 14px; min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px; }}
#MkStepTitle {{ color: {text}; font-family: {UI}; font-size: 14px; font-weight: 700; }}
#MkLine {{ color: {text}; font-family: {UI}; font-size: 13px; }}
#MkDetail {{ color: {muted}; font-family: {UI}; font-size: 12px; }}
#MkState {{ color: {muted}; font-family: {UI}; font-size: 11px; font-weight: 700;
    letter-spacing: 0.4px; }}
#MkBtn {{ background: {btn_bg}; color: {btn_text}; border: none; border-radius: 9px;
    padding: 7px 14px; font-family: {UI}; font-size: 13px; font-weight: 600; }}
#MkBtn:hover {{ background: {btn_bg_hover}; }}
#MkGhost {{ background: transparent; color: {text}; border: 1px solid {line_strong};
    border-radius: 9px; padding: 6px 12px; font-family: {UI}; font-size: 13px; }}
#MkGhost:hover {{ background: {hover}; }}
#MkPic {{ background: {sunken}; border: 1px solid {line}; border-radius: 12px; }}
#MkNote {{ color: {muted}; font-family: {UI}; font-size: 12px; }}
QScrollArea#MkScroll {{ background: transparent; border: none; }}
QScrollArea#MkScroll > QWidget > QWidget {{ background: transparent; }}
"""


def _log(msg):
    try:
        import FreeCAD
        FreeCAD.Console.PrintLog("[Atech] make it: %s\n" % msg)
    except Exception:                                   # noqa: BLE001
        pass


def _lab(text, name, wrap=True):
    lab = QtWidgets.QLabel(text)
    lab.setObjectName(name)
    lab.setWordWrap(wrap)
    lab.setTextFormat(QtCore.Qt.PlainText)
    return lab


def _btn(text, primary=False, slot=None):
    b = QtWidgets.QPushButton(text)
    b.setObjectName("MkBtn" if primary else "MkGhost")
    b.setCursor(QtCore.Qt.PointingHandCursor)
    if slot:
        b.clicked.connect(slot)
    return b


# ------------------------------------------------------------------ facts
def levels_of(doc):
    """{"done", "total"} of the design levels in this design's chat, or None."""
    try:
        from . import panel as panel_mod
        p = panel_mod.get_panel()
        st = p._docs.get(p._doc_key(doc)) if p is not None else None
        ws = getattr(st, "ws", None)
        if not ws:
            return None
        state = product.kit("atech_levels").read(ws)
        if state is None:              # no ladder, or its last level is done
            return None
        return {"done": state["level"] - 1, "total": state["count"]}
    except Exception as exc:                            # noqa: BLE001
        _log("levels: %r" % (exc,))
        return None


def built(doc):
    if doc is None:
        return False
    try:
        from . import export_tools
        return bool(export_tools.agent_parts(doc)) or any(
            getattr(o, "AtechRole", None) for o in doc.Objects)
    except Exception:                                   # noqa: BLE001
        return bool(getattr(doc, "Objects", None))


def gather(doc):
    """The facts dict product.steps() reads, for doc."""
    from . import electrical_suite
    name = getattr(doc, "Label", "") or "Design"
    folder = sdk_tools.product_dir(name)
    st = product.read_state(folder)
    try:
        from . import export_tools
        bom = export_tools.bom(doc)
    except Exception as exc:                            # noqa: BLE001
        _log("bom: %r" % (exc,))
        bom = {"printed": [], "hardware": []}
    try:
        el = electrical_suite.gather(doc, st.get("power_inputs") or {})
    except Exception as exc:                            # noqa: BLE001
        _log("electrical: %r" % (exc,))
        el = product.kit().analyse({"modules": []}, project=name)
    prints = os.path.join(os.path.expanduser("~/Documents/Atech Prints"), name)
    if os.path.isdir(prints) and "printed" not in st:
        st = dict(st, printed={"when": None, "where": prints})
    f = {"project": name, "built": built(doc), "check": None,
         "levels": levels_of(doc), "bom": bom, "electrical": el,
         "sdk": sdk_tools.find(), "state": st, "folder": folder,
         "firmware_yaml": electrical_suite.agent_yaml(doc)}
    # R1180: part sizes and the chat's workspace (its brief.json)
    try:
        from . import p2p_product
        f["parts"] = p2p_product.part_rows(doc, bom)
        f["whole_mm"] = p2p_product.whole_mm(doc)
        f["ws"] = workspace_of(doc)
    except Exception as exc:                            # noqa: BLE001
        _log("p2p: %r" % (exc,))
    return f


def workspace_of(doc):
    """The chat workspace of doc (where brief.json is), or None."""
    try:
        from . import panel as panel_mod
        p = panel_mod.get_panel()
        st = p._docs.get(p._doc_key(doc)) if p is not None else None
        return getattr(st, "ws", None)
    except Exception:                                   # noqa: BLE001
        return None


def picture(doc, path):
    """A picture of the design (the 3D view, isometric), or None."""
    try:
        import FreeCADGui
        v = FreeCADGui.ActiveDocument.ActiveView if FreeCADGui.ActiveDocument else None
        if v is None:
            return None
        v.saveImage(path, 1200, 800, "Transparent")
        return path if os.path.isfile(path) else None
    except Exception as exc:                            # noqa: BLE001
        _log("picture: %r" % (exc,))
        return None


# ------------------------------------------------------------------ the view
class StepRow(QtWidgets.QFrame):
    def __init__(self, n, s, on_action, current=False):
        super().__init__()
        self.setObjectName("MkStep")
        self.setProperty("current", "true" if current else "false")
        self.step = s
        t = style.tokens()
        h = QtWidgets.QHBoxLayout(self)
        h.setContentsMargins(14, 12, 14, 12)
        h.setSpacing(14)
        num = QtWidgets.QLabel("✓" if s["state"] == product.DONE else str(n))
        num.setObjectName("MkNum")
        num.setAlignment(QtCore.Qt.AlignCenter)
        num.setStyleSheet("QLabel {{ background: {c}; border-radius: 14px; }}".format(
            c=t[STATE_COLOUR[s["state"]]]))
        h.addWidget(num, 0, QtCore.Qt.AlignTop)
        col = QtWidgets.QVBoxLayout()
        col.setSpacing(3)
        top = QtWidgets.QHBoxLayout()
        top.setSpacing(10)
        top.addWidget(_lab(s["title"], "MkStepTitle", wrap=False))
        state = _lab(product.STATE_WORDS[s["state"]].upper(), "MkState", wrap=False)
        state.setStyleSheet("color: %s;" % t[STATE_COLOUR[s["state"]]])
        top.addWidget(state)
        top.addStretch(1)
        col.addLayout(top)
        col.addWidget(_lab(s["line"], "MkLine"))
        for d in s.get("detail") or ():
            col.addWidget(_lab("• " + d, "MkDetail"))
        h.addLayout(col, 1)
        if s["action"] and s["action_words"]:
            b = _btn(s["action_words"], primary=current,
                     slot=lambda _=False, a=s["action"]: on_action(a))
            b.setAccessibleName("%s: %s" % (s["title"], s["action_words"]))
            h.addWidget(b, 0, QtCore.Qt.AlignVCenter)
            self.button = b


class MakeIt(QtWidgets.QDialog):
    def __init__(self, doc=None, parent=None):
        super().__init__(parent)
        self.setObjectName("MakeIt")
        self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, True)
        self.resize(940, 860)
        self._doc = doc
        self.f = None
        self._dlgs = []
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        head = QtWidgets.QFrame()
        head.setObjectName("MkHead")
        hl = QtWidgets.QHBoxLayout(head)
        hl.setContentsMargins(22, 16, 22, 16)
        hl.setSpacing(18)
        self.pic = QtWidgets.QLabel()
        self.pic.setObjectName("MkPic")
        self.pic.setFixedSize(168, 112)
        self.pic.setAlignment(QtCore.Qt.AlignCenter)
        hl.addWidget(self.pic)
        col = QtWidgets.QVBoxLayout()
        col.setSpacing(4)
        self.title = _lab("", "MkTitle", wrap=False)
        self.sub = _lab("", "MkSub")
        self.bar = QtWidgets.QProgressBar()
        self.bar.setObjectName("MkBar")
        self.bar.setTextVisible(False)
        col.addWidget(self.title)
        col.addWidget(self.sub)
        col.addSpacing(6)
        col.addWidget(self.bar)
        col.addStretch(1)
        hl.addLayout(col, 1)
        bcol = QtWidgets.QVBoxLayout()
        self.btn_pack = _btn("Make the product pack", primary=True, slot=self.make_pack)
        self.btn_pack.setToolTip("One folder with the print files, parts list, electrical "
                                 "report, firmware and assembly steps")
        bcol.addWidget(self.btn_pack)
        self.btn_refresh = _btn("Refresh", slot=self.refresh)
        bcol.addWidget(self.btn_refresh)
        bcol.addStretch(1)
        hl.addLayout(bcol)
        root.addWidget(head)
        sc = QtWidgets.QScrollArea()
        sc.setObjectName("MkScroll")
        sc.setWidgetResizable(True)
        sc.setFrameShape(QtWidgets.QFrame.NoFrame)
        inner = QtWidgets.QWidget()
        self.body = QtWidgets.QVBoxLayout(inner)
        self.body.setContentsMargins(22, 18, 22, 22)
        self.body.setSpacing(10)
        sc.setWidget(inner)
        root.addWidget(sc, 1)
        self.setStyleSheet(style.qss(QSS))
        self.refresh()

    def doc(self):
        if self._doc is not None:
            return self._doc
        try:
            import FreeCAD
            return FreeCAD.ActiveDocument
        except Exception:                               # noqa: BLE001
            return None

    def refresh(self):
        doc = self.doc()
        try:
            self.f = gather(doc)
        except Exception as exc:                        # noqa: BLE001
            _log("gather: %r" % (exc,))
            self.f = {"project": getattr(doc, "Label", "") or "Design", "built": False,
                      "state": {}}
        f = self.f
        ss = product.steps(f)
        done, total = product.progress(ss)
        nxt = product.next_step(ss)
        self.setWindowTitle(TITLE % f["project"])
        self.title.setText(f["project"])
        self.sub.setText("From prompt to product: %d of %d steps done.%s" % (
            done, total, (" Next: %s." % nxt["title"].lower()) if nxt else
            " Everything is done."))
        self.bar.setRange(0, total)
        self.bar.setValue(done)
        self.btn_pack.setEnabled(bool(f.get("built")))
        while self.body.count():
            it = self.body.takeAt(0)
            if it.widget() is not None:
                it.widget().deleteLater()
        self.rows = []
        for i, s in enumerate(ss, 1):
            row = StepRow(i, s, self.act, current=(nxt is not None and s["key"] == nxt["key"]))
            self.rows.append(row)
            self.body.addWidget(row)
        try:                                            # R1190
            from . import p2p_view
            self.papers = p2p_view.papers_card(f, self)
            self.body.addWidget(self.papers)
        except Exception as exc:                        # noqa: BLE001
            _log("papers: %r" % (exc,))
            self.papers = None
        self.note = _lab("", "MkNote")
        self.note.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        last = (f.get("state") or {}).get("pack")
        if last:
            self.note.setText("Last product pack: %s, in %s" % (last["when"], f.get("folder")))
        self.body.addWidget(self.note)
        self.body.addStretch(1)
        self._set_picture()

    def _set_picture(self):
        tmp = os.path.join(tempfile.gettempdir(), "atech_makeit_%d.png" % os.getpid())
        p = picture(self.doc(), tmp)
        if p:
            pm = QtGui.QPixmap(p)
            if not pm.isNull():
                self.pic.setPixmap(pm.scaled(self.pic.size(), QtCore.Qt.KeepAspectRatio,
                                             QtCore.Qt.SmoothTransformation))
                self._pic_path = p
                return
        self._pic_path = None
        self.pic.setText(style.PRODUCT)

    # ------------------------------------------------------------ actions
    def act(self, action):
        """Do one step's action. Returns what was opened (tests)."""
        doc = self.doc()
        try:
            if action in ("electrical", "firmware"):
                from . import electrical_suite
                w = electrical_suite.open_suite(doc, "firmware" if action == "firmware"
                                                else "overview", self.window().parent())
                return w
            if action == "assembly":
                d = AssemblyDialog(self.f, self)
                self._dlgs.append(d)
                d.show()
                return d
            if action in ("bom", "print", "order"):
                from . import shell
                key = {"bom": "bom", "print": "print", "order": "made"}[action]
                out = shell.run_command_action(key)
                if action == "print":
                    product.mark(self.f["folder"], "printed")
                if action == "order":
                    product.mark(self.f["folder"], "ordered", note="Get it made opened")
                QtCore.QTimer.singleShot(400, self.refresh)
                return out
            if action in ("chat", "view"):
                self.close()
                if action == "chat":
                    try:
                        from . import panel as panel_mod
                        p = panel_mod.get_panel()
                        if p is not None and hasattr(p, "prompt"):
                            p.prompt.setFocus()
                    except Exception:                   # noqa: BLE001
                        pass
                return action
        except Exception as exc:                        # noqa: BLE001
            _log("action %s: %r" % (action, exc))
            self.note.setText("Could not open it: %s" % exc)
        return None

    def extras(self):
        """The pack's files only the app can make: print files and the wiring PDF."""
        doc = self.doc()
        out = {}
        try:
            from . import export_tools

            def three_mf(path, doc=doc):
                export_tools.export_for_print(doc, path, fmt="3MF")
            out[os.path.join("prints", "%s.3mf" % sdk_tools.safe_folder(self.f["project"]))] = (
                "every printed part, ready for a slicer", three_mf)

            def step(path, doc=doc):
                export_tools.export_for_print(doc, path, fmt="STEP")
            out[os.path.join("cad", "%s.step" % sdk_tools.safe_folder(self.f["project"]))] = (
                "the design as STEP, for any CAD tool", step)
        except Exception as exc:                        # noqa: BLE001
            _log("extras: %r" % (exc,))
        el = self.f.get("electrical") or {}
        if el.get("modules"):
            def wiring_pdf(path, w=el["wiring"]):
                from . import wiring_view
                wiring_view.export_wiring(w, path)

            def report(path, r=el):
                from . import electrical_suite
                electrical_suite.report_pdf(r, path)
            out[os.path.join("electrical", "wiring.pdf")] = ("the wiring diagram to print",
                                                            wiring_pdf)
            out[os.path.join("electrical", "electrical-report.pdf")] = (
                "the electrical report to print", report)
        return out

    def make_pack(self):
        if not self.f or not self.f.get("built"):
            return None
        folder = self.f["folder"]
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            files = product.write_pack(self.f, folder, extra=self.extras(),
                                       picture=getattr(self, "_pic_path", None))
        except Exception as exc:                        # noqa: BLE001
            _log("pack: %r" % (exc,))
            self.note.setText("Could not make the pack: %s" % exc)
            return None
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        self.refresh()
        self.note.setText("Product pack: %d files in %s" % (len(files), folder))
        if not os.environ.get("ATECH_NO_REVEAL"):
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder))
        return files


class AssemblyDialog(QtWidgets.QDialog):
    def __init__(self, f, parent=None):
        super().__init__(parent)
        self.setWindowTitle("%s – assembly" % f.get("project", "Product"))
        self.resize(640, 720)
        lay = QtWidgets.QVBoxLayout(self)
        br = QtWidgets.QTextBrowser()
        br.setOpenExternalLinks(True)
        br.setMarkdown(product.assembly_md(f))
        lay.addWidget(br)
        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        save = QtWidgets.QPushButton("Save…")
        save.clicked.connect(lambda: self._save(f))
        row.addWidget(save)
        lay.addLayout(row)
        self.browser = br

    def _save(self, f):
        folder = sdk_tools.product_dir(f.get("project", "Product"))
        os.makedirs(folder, exist_ok=True)
        path, _x = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save assembly steps", os.path.join(folder, "assembly.md"))
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(product.assembly_md(f))


_OPEN = []


def _alive(w):
    """w, or None when its C++ object is gone (a closed main window)."""
    if w is None:
        return None
    try:
        import shiboken6
        return w if shiboken6.isValid(w) else None
    except Exception:                                   # noqa: BLE001
        try:
            w.objectName()
            return w
        except RuntimeError:
            return None


def open_make_it(doc=None, parent=None):
    if parent is None:
        try:
            import FreeCADGui
            parent = FreeCADGui.getMainWindow()
        except Exception:                               # noqa: BLE001
            parent = None
    parent = _alive(parent)
    for w in list(_OPEN):
        try:
            if w.isVisible():
                w._doc = doc if doc is not None else w._doc
                w.refresh()
                w.raise_()
                w.activateWindow()
                return w
        except RuntimeError:
            pass
        _OPEN.remove(w)
    w = MakeIt(doc, parent)
    _OPEN.append(w)
    w.show()
    return w
