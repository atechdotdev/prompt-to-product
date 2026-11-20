"""p2p_view - the prompt-to-product papers in the Make it window (R1190).

    papers_card(f, owner)   a card under the 7 steps: the brief's 'Done when'
                            score, the print plan, the cost, the test by hand
                            and the version, each one line; buttons for the
                            brief and the test by hand
    QADialog                tick each test passed / failed / skipped, with a
                            note; saves <product folder>/qa.json

Plain Qt widgets; the facts come from p2p_product.enrich (no FreeCAD here).
"""
import os

from PySide6 import QtCore, QtWidgets

from . import p2p_product, style

ROWS = (("brief", "Brief"), ("print", "Print plan"), ("cost", "Cost"),
        ("qa", "Tested by hand"), ("version", "Version"))
QSS = """
#P2PCard {{ background: {panel}; border: 1px solid {line}; border-radius: 12px; }}
#P2PHead {{ color: {text}; font-family: {UI}; font-size: 14px; font-weight: 700; }}
#P2PKey {{ color: {muted}; font-family: {UI}; font-size: 12px; min-width: 110px; }}
#P2PLine {{ color: {text}; font-family: {UI}; font-size: 12px; }}
#P2PQuestion {{ color: {muted}; font-family: {UI}; font-size: 12px; }}
"""


def _qss():
    try:
        return style.qss(QSS, reset=False)
    except Exception:                                     # noqa: BLE001
        return ""


def enriched(f):
    try:
        g = p2p_product.enrich(f, ws=f.get("ws"), prompt=f.get("prompt"))
        try:
            R = p2p_product.kit("p2p_rev")
            last = R.latest(f.get("folder")) if f.get("folder") else None
            if last:
                g["version"] = last["version"]
        except Exception:                                 # noqa: BLE001
            pass
        return g
    except Exception:                                     # noqa: BLE001
        return None


class PapersCard(QtWidgets.QFrame):
    def __init__(self, f, owner=None):
        super().__init__()
        self.setObjectName("P2PCard")
        self.setStyleSheet(_qss())
        self.owner = owner
        self.g = enriched(f) or {}
        self.status = p2p_product.status(self.g) if self.g else {}
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(6)
        head = QtWidgets.QLabel("Prompt to product")
        head.setObjectName("P2PHead")
        lay.addWidget(head)
        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        grid.setVerticalSpacing(4)
        self.lines = {}
        r = 0
        for key, word in ROWS:
            text = self.status.get(key)
            if not text:
                continue
            k = QtWidgets.QLabel(word)
            k.setObjectName("P2PKey")
            v = QtWidgets.QLabel(text[:1].upper() + text[1:])
            v.setObjectName("P2PLine")
            v.setWordWrap(True)
            v.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            grid.addWidget(k, r, 0, QtCore.Qt.AlignTop)
            grid.addWidget(v, r, 1)
            self.lines[key] = v
            r += 1
        if not self.lines:
            grid.addWidget(QtWidgets.QLabel("Make the product pack to see the brief, the "
                                            "print plan, the cost and the test by hand."),
                           0, 0, 1, 2)
        lay.addLayout(grid)
        b = self.g.get("brief") or {}
        for q in (b.get("questions") or [])[:2]:
            ql = QtWidgets.QLabel("Still open: " + q)
            ql.setObjectName("P2PQuestion")
            ql.setWordWrap(True)
            lay.addWidget(ql)
        row = QtWidgets.QHBoxLayout()
        self.btn_qa = QtWidgets.QPushButton("Test by hand…")
        self.btn_qa.setEnabled(bool(self.g.get("qa_plan")) and bool(self.g.get("folder")))
        self.btn_qa.clicked.connect(self.open_qa)
        row.addWidget(self.btn_qa)
        self.btn_brief = QtWidgets.QPushButton("Brief…")
        self.btn_brief.setEnabled(bool(b))
        self.btn_brief.clicked.connect(self.open_brief)
        row.addWidget(self.btn_brief)
        row.addStretch(1)
        lay.addLayout(row)
        self._dlgs = []

    def open_qa(self):
        d = QADialog(self.g.get("qa_plan") or [], self.g.get("folder"), self)
        d.saved.connect(self._saved)
        self._dlgs.append(d)
        d.show()
        return d

    def _saved(self, line):
        if "qa" in self.lines:
            self.lines["qa"].setText(line)
        if self.owner is not None and hasattr(self.owner, "refresh"):
            QtCore.QTimer.singleShot(0, self.owner.refresh)

    def open_brief(self):
        B = p2p_product.kit("p2p_brief")
        d = QtWidgets.QDialog(self)
        d.setWindowTitle("Brief")
        d.resize(620, 640)
        v = QtWidgets.QVBoxLayout(d)
        t = QtWidgets.QTextBrowser()
        t.setMarkdown(B.markdown(self.g["brief"]) + "\n" + (
            p2p_product.kit("p2p_accept").markdown(self.g["accept"])
            if self.g.get("accept") else ""))
        v.addWidget(t)
        self._dlgs.append(d)
        d.show()
        return d


def papers_card(f, owner=None):
    return PapersCard(f, owner)


class QADialog(QtWidgets.QDialog):
    """One row per test: Pass / Fail / Skip and a note. Save writes qa.json."""
    saved = QtCore.Signal(str)
    CHOICES = (("", "Not yet"), ("pass", "Passed"), ("fail", "Failed"), ("skip", "Skipped"))

    def __init__(self, tests, folder, parent=None):
        super().__init__(parent)
        self.setObjectName("P2PQA")
        self.setWindowTitle("Test by hand")
        self.resize(760, 640)
        self.tests = tests
        self.folder = folder
        self.Q = p2p_product.kit("p2p_qa")
        self.rec = self.Q.load_record(folder) if folder else {}
        v = QtWidgets.QVBoxLayout(self)
        self.head = QtWidgets.QLabel(self.Q.status(tests, self.rec)["line"])
        self.head.setWordWrap(True)
        v.addWidget(self.head)
        sc = QtWidgets.QScrollArea()
        sc.setWidgetResizable(True)
        inner = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(inner)
        grid.setColumnStretch(1, 1)
        self.rows = {}
        group = None
        r = 0
        for t in tests:
            if t["group"] != group:
                group = t["group"]
                g = QtWidgets.QLabel("<b>%s</b>" % group)
                grid.addWidget(g, r, 0, 1, 3)
                r += 1
            lab = QtWidgets.QLabel("%s<br><span style='color:gray'>Expect: %s</span>"
                                   % (t["test"], t["expect"]))
            lab.setWordWrap(True)
            box = QtWidgets.QComboBox()
            for val, word in self.CHOICES:
                box.addItem(word, val)
            old = (self.rec.get(t["id"]) or {})
            i = box.findData(old.get("result", ""))
            box.setCurrentIndex(max(0, i))
            note = QtWidgets.QLineEdit(old.get("note", ""))
            note.setPlaceholderText("note")
            grid.addWidget(lab, r, 1)
            grid.addWidget(box, r, 0, QtCore.Qt.AlignTop)
            grid.addWidget(note, r, 2, QtCore.Qt.AlignTop)
            self.rows[t["id"]] = (box, note)
            r += 1
        sc.setWidget(inner)
        v.addWidget(sc, 1)
        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save
                                        | QtWidgets.QDialogButtonBox.Close)
        bb.accepted.connect(self.save)
        bb.rejected.connect(self.close)
        v.addWidget(bb)

    def set(self, tid, outcome, note=""):
        """For tests and keyboard users: set one row."""
        box, ed = self.rows[tid]
        box.setCurrentIndex(max(0, box.findData(outcome)))
        ed.setText(note)

    def save(self):
        rec = dict(self.rec)
        for tid, (box, ed) in self.rows.items():
            val = box.currentData()
            if val:
                old = rec.get(tid) or {}
                if old.get("result") != val or old.get("note", "") != ed.text():
                    rec = self.Q.result(rec, tid, val, ed.text())
            else:
                rec.pop(tid, None)
        self.rec = rec
        if self.folder:
            self.Q.save_record(self.folder, rec)
        line = self.Q.status(self.tests, rec)["line"]
        self.head.setText(line)
        self.saved.emit(line)
        return rec
