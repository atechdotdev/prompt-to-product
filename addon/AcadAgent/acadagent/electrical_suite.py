"""The electrical engineer suite (R1002).

One window for the electronics of the open design, from
agent_kit/atech_electrical.py:

    Overview    the verdict, the rule checks with their fixes, the power line
    Schematic   the block schematic (each module's chip, bus, Line A/B roles)
    Wiring      the R962 wiring diagram
    Ports       the 14 ports: what the SDK lets each do, who uses it, its lines
    Power       the 5 V budget: type measured mA, pick the supply, power bank
    Firmware    project.yaml from the design; Check, Build, Run without a
                board, Flash, Board health, Watch events (the Atech SDK CLI)
    Bring-up    the first power-on checklist, ticked off as you go
    Export      the report as PDF, the files (CSV, netlist, SVG)

    open_suite(doc=None, page="overview", parent=None)

Every fact on screen is atech_electrical's, with its source. The user's
power figures and ticks are kept in the product folder (product.json),
never in the design file.
"""
import os
import sys
import time

from PySide6 import QtCore, QtGui, QtWidgets

from . import product, sdk_tools, style

PAGES = (("overview", "Overview", "check"), ("schematic", "Schematic", "cpu"),
         ("wiring", "Wiring", "wire"), ("ports", "Ports", "grid"),
         ("power", "Power", "sparkles"), ("firmware", "Firmware", "terminal"),
         ("bringup", "Bring-up", "check"), ("export", "Export", "upload"))
TITLE = "%s – electrical"
LEVEL_COLOUR = {"error": "fail", "warning": "warn", "note": "muted", "ok": "ok",
                "empty": "muted"}

QSS = """
#ElSuite {{ background: {base}; }}
#ElNav {{ background: {panel}; border: none; border-right: 1px solid {line};
    font-family: {UI}; font-size: 13px; outline: 0; padding: 8px 6px; }}
#ElNav::item {{ color: {text}; padding: 8px 10px; border-radius: 8px; margin: 1px 0; }}
#ElNav::item:selected {{ background: {hover}; color: {text}; font-weight: 600; }}
#ElNav::item:hover {{ background: {hover}; }}
#ElHead {{ background: {panel}; border-bottom: 1px solid {line}; }}
#ElTitle {{ color: {text}; font-family: 'Sen', {UI}; font-size: 18px; font-weight: 700; }}
#ElSub {{ color: {muted}; font-family: {UI}; font-size: 12px; }}
#ElPill {{ border-radius: 11px; padding: 3px 10px; font-family: {UI}; font-size: 12px;
    font-weight: 600; color: #ffffff; }}
#ElPage {{ background: {base}; }}
#ElCard {{ background: {panel}; border: 1px solid {line}; border-radius: 12px; }}
#ElH {{ color: {muted}; font-family: {UI}; font-size: 11px; font-weight: 700;
    letter-spacing: 0.5px; }}
#ElBig {{ color: {text}; font-family: 'Sen', {UI}; font-size: 22px; font-weight: 700; }}
#ElText {{ color: {text}; font-family: {UI}; font-size: 13px; }}
#ElMuted {{ color: {muted}; font-family: {UI}; font-size: 12px; }}
#ElRule {{ background: {panel}; border: 1px solid {line}; border-radius: 10px; }}
#ElRuleText {{ color: {text}; font-family: {UI}; font-size: 13px; }}
#ElRuleFix {{ color: {muted}; font-family: {UI}; font-size: 12px; }}
#ElCount {{ color: {text}; font-family: 'Sen', {UI}; font-size: 26px; font-weight: 700; }}
#ElBtn {{ background: {btn_bg}; color: {btn_text}; border: none; border-radius: 9px;
    padding: 7px 14px; font-family: {UI}; font-size: 13px; font-weight: 600; }}
#ElBtn:hover {{ background: {btn_bg_hover}; }}
#ElBtn:disabled {{ background: {line_strong}; color: {muted}; }}
#ElGhost {{ background: transparent; color: {text}; border: 1px solid {line_strong};
    border-radius: 9px; padding: 6px 12px; font-family: {UI}; font-size: 13px; }}
#ElGhost:hover {{ background: {hover}; }}
#ElGhost:disabled {{ color: {dim}; border-color: {line}; }}
#ElConsole {{ background: {sunken}; color: {text}; border: 1px solid {line};
    border-radius: 10px; font-family: {MONO}; font-size: 12px; padding: 8px; }}
#ElYaml {{ background: {sunken}; color: {text}; border: 1px solid {line};
    border-radius: 10px; font-family: {MONO}; font-size: 12px; padding: 8px; }}
QTableWidget#ElTable {{ background: {panel}; color: {text}; border: 1px solid {line};
    border-radius: 10px; gridline-color: {line}; font-family: {UI}; font-size: 13px;
    selection-background-color: {hover}; selection-color: {text}; }}
QHeaderView::section {{ background: {panel}; color: {muted}; border: none;
    border-bottom: 1px solid {line}; padding: 6px; font-family: {UI}; font-size: 11px;
    font-weight: 700; }}
QComboBox#ElCombo, QSpinBox#ElSpin {{ background: {input_bg}; color: {text};
    border: 1px solid {input_border}; border-radius: 8px; padding: 4px 8px;
    font-family: {UI}; font-size: 13px; min-height: 22px; }}
QCheckBox#ElTick {{ color: {text}; font-family: {UI}; font-size: 13px; spacing: 10px; }}
QScrollArea#ElScroll {{ background: transparent; border: none; }}
QScrollArea#ElScroll > QWidget > QWidget {{ background: transparent; }}
"""


def _log(msg):
    try:
        import FreeCAD
        FreeCAD.Console.PrintLog("[Atech] electrical: %s\n" % msg)
    except Exception:                                   # noqa: BLE001
        pass


def E():
    return product.kit("atech_electrical")


def W():
    return product.kit("atech_wiring")


def _icon(name, colour, size=16):
    try:
        return style.icon(name, colour, size)
    except Exception:                                   # noqa: BLE001
        return QtGui.QIcon()


def _lab(text="", name="ElText", wrap=True, select=False):
    lab = QtWidgets.QLabel(text)
    lab.setObjectName(name)
    lab.setWordWrap(wrap)
    lab.setTextFormat(QtCore.Qt.PlainText)
    if select:
        lab.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
    return lab


def _btn(text, primary=False, slot=None, tip=""):
    b = QtWidgets.QPushButton(text)
    b.setObjectName("ElBtn" if primary else "ElGhost")
    b.setCursor(QtCore.Qt.PointingHandCursor)
    if tip:
        b.setToolTip(tip)
    if slot:
        b.clicked.connect(slot)
    return b


def _card():
    f = QtWidgets.QFrame()
    f.setObjectName("ElCard")
    lay = QtWidgets.QVBoxLayout(f)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(8)
    return f, lay


def _scroll_page():
    sc = QtWidgets.QScrollArea()
    sc.setObjectName("ElScroll")
    sc.setWidgetResizable(True)
    sc.setFrameShape(QtWidgets.QFrame.NoFrame)
    inner = QtWidgets.QWidget()
    inner.setObjectName("ElPage")
    lay = QtWidgets.QVBoxLayout(inner)
    lay.setContentsMargins(22, 18, 22, 22)
    lay.setSpacing(12)
    sc.setWidget(inner)
    return sc, lay


def _clear(lay):
    while lay.count():
        it = lay.takeAt(0)
        w = it.widget()
        if w is not None:
            w.deleteLater()
        elif it.layout() is not None:
            _clear(it.layout())


# ------------------------------------------------------------------ the data
def agent_yaml(doc):
    """The project.yaml the agent wrote in this design's chat, or None."""
    try:
        from . import panel as panel_mod
        p = panel_mod.get_panel()
        st = p._docs.get(p._doc_key(doc)) if p is not None else None
        ws = getattr(st, "ws", None)
        path = os.path.join(ws, sdk_tools.PROJECT) if ws else None
        if path and os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                return fh.read()
    except Exception as exc:                            # noqa: BLE001
        _log("agent yaml: %r" % (exc,))
    return None


def gather(doc, inputs=None):
    """atech_electrical.analyse for doc with the user's power inputs."""
    inputs = inputs or {}
    atech = W().modules_from_doc(doc) if doc is not None else None
    fw_on = True
    try:
        from . import build
        fw_on = bool(build.firmware_on())
    except Exception:                                   # noqa: BLE001
        pass
    reserved = None
    try:
        from . import modules_page
        _ports, _ = modules_page._lib()
        reserved = getattr(_ports, "RESERVED", None)
    except Exception:                                   # noqa: BLE001
        reserved = None
    w = W().build(atech, names=dict(E().NAMES), reserved=reserved, firmware_on=fw_on,
                  project=getattr(doc, "Label", "") or "",
                  made=time.strftime("%d %b %Y %H:%M"))
    return E().analyse(w=w, project=getattr(doc, "Label", "") or "",
                       made=time.strftime("%d %b %Y %H:%M"),
                       loads=inputs.get("loads"), supply=inputs.get("supply"),
                       bank_mah=inputs.get("bank_mah"))


def svg_widget(text):
    from . import wiring_view
    v = wiring_view.WiringView()
    v.set_svg(text)
    return v


def export_svg(text, path, title="Electrical"):
    """An SVG to .svg, .png (2400 px) or .pdf (A4 landscape)."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".svg":
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path
    from . import wiring_view
    r = wiring_view._renderer(text)
    size = r.defaultSize()
    if ext == ".png":
        wd = 2400
        h = int(round(wd * size.height() / float(max(size.width(), 1))))
        img = QtGui.QImage(wd, h, QtGui.QImage.Format_ARGB32)
        img.fill(QtGui.QColor("#ffffff"))
        p = QtGui.QPainter(img)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        r.render(p, QtCore.QRectF(0, 0, wd, h))
        p.end()
        img.save(path, "PNG")
        return path
    if ext == ".pdf":
        writer = QtGui.QPdfWriter(path)
        writer.setPageSize(QtGui.QPageSize(QtGui.QPageSize.A4))
        writer.setPageOrientation(QtGui.QPageLayout.Landscape)
        writer.setResolution(150)
        writer.setTitle(title)
        writer.setCreator(style.PRODUCT)
        p = QtGui.QPainter(writer)
        r.render(p, wiring_view._fit(size.width(), size.height(),
                                     QtCore.QRectF(0, 0, writer.width(), writer.height())))
        p.end()
        return path
    raise ValueError("use .svg, .png or .pdf")


def report_pdf(r, path):
    """The whole report: the markdown text, then the schematic and the power
    tree on their own landscape pages."""
    writer = QtGui.QPdfWriter(path)
    writer.setPageSize(QtGui.QPageSize(QtGui.QPageSize.A4))
    writer.setPageMargins(QtCore.QMarginsF(16, 16, 16, 16), QtGui.QPageLayout.Millimeter)
    writer.setResolution(150)
    writer.setTitle(TITLE % (r["project"] or "Design"))
    writer.setCreator(style.PRODUCT)
    doc = QtGui.QTextDocument()
    doc.setDefaultFont(QtGui.QFont("Helvetica", 10))
    doc.setMarkdown(E().markdown(r))
    doc.setPageSize(QtCore.QSizeF(writer.width(), writer.height()))
    p = QtGui.QPainter(writer)
    from . import wiring_view
    pages = max(1, doc.pageCount())
    for i in range(pages):
        if i:
            writer.newPage()
        p.save()
        p.translate(0, -i * writer.height())
        doc.drawContents(p, QtCore.QRectF(0, i * writer.height(), writer.width(), writer.height()))
        p.restore()
    for svg in (E().schematic_svg(r), E().power_tree_svg(r)):
        writer.setPageOrientation(QtGui.QPageLayout.Landscape)
        writer.newPage()
        rd = wiring_view._renderer(svg)
        s = rd.defaultSize()
        rd.render(p, wiring_view._fit(s.width(), s.height(),
                                      QtCore.QRectF(0, 0, writer.width(), writer.height())))
    p.end()
    return path


# ------------------------------------------------------------------ window
class ElectricalSuite(QtWidgets.QDialog):
    """The suite window. doc: a FreeCAD document (None: the active one)."""

    def __init__(self, doc=None, parent=None, page="overview"):
        super().__init__(parent)
        self.setObjectName("ElSuite")
        self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, True)
        self.resize(1180, 800)
        self._doc = doc
        self.r = None
        self.runner = None
        self.sdk = sdk_tools.find()
        self._building = False
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        # header
        head = QtWidgets.QFrame()
        head.setObjectName("ElHead")
        hl = QtWidgets.QHBoxLayout(head)
        hl.setContentsMargins(20, 14, 20, 14)
        col = QtWidgets.QVBoxLayout()
        col.setSpacing(2)
        self.title = _lab("", "ElTitle", wrap=False)
        self.sub = _lab("", "ElSub", wrap=False)
        col.addWidget(self.title)
        col.addWidget(self.sub)
        hl.addLayout(col, 1)
        self.pill = _lab("", "ElPill", wrap=False)
        hl.addWidget(self.pill, 0, QtCore.Qt.AlignVCenter)
        self.btn_refresh = _btn("Refresh", slot=self.refresh,
                                tip="Read the design again")
        hl.addWidget(self.btn_refresh)
        root.addWidget(head)
        body = QtWidgets.QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        self.nav = QtWidgets.QListWidget()
        self.nav.setObjectName("ElNav")
        self.nav.setFixedWidth(184)
        self.nav.setIconSize(QtCore.QSize(16, 16))
        self.stack = QtWidgets.QStackedWidget()
        self.pages = {}
        for key, words, _ico in PAGES:
            it = QtWidgets.QListWidgetItem(words)
            it.setData(QtCore.Qt.UserRole, key)
            self.nav.addItem(it)
            sc, lay = _scroll_page()
            self.pages[key] = (sc, lay)
            self.stack.addWidget(sc)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        body.addWidget(self.nav)
        body.addWidget(self.stack, 1)
        root.addLayout(body, 1)
        self.restyle()
        self.refresh()
        self.show_page(page)

    # -------------------------------------------------------- plumbing
    def doc(self):
        if self._doc is not None:
            return self._doc
        try:
            import FreeCAD
            return FreeCAD.ActiveDocument
        except Exception:                               # noqa: BLE001
            return None

    def folder(self):
        return sdk_tools.product_dir(getattr(self.doc(), "Label", "") or "Design")

    def inputs(self):
        return product.read_state(self.folder()).get("power_inputs") or {}

    def save_inputs(self, **kw):
        st = product.read_state(self.folder())
        cur = dict(st.get("power_inputs") or {})
        cur.pop("when", None)
        cur.update(kw)
        product.mark(self.folder(), "power_inputs", when=product.now_text(), **cur)

    def show_page(self, key):
        for i, (k, _w, _i) in enumerate(PAGES):
            if k == key:
                self.nav.setCurrentRow(i)
                return True
        return False

    def current_page(self):
        return PAGES[self.nav.currentRow()][0]

    def restyle(self):
        self.setStyleSheet(style.qss(QSS))
        t = style.tokens()
        for i, (_k, _w, ico) in enumerate(PAGES):
            self.nav.item(i).setIcon(_icon(ico, t["muted"], 16))
        if self.r is not None:
            self._fill_pill()

    def _fill_pill(self):
        t = style.tokens()
        v = self.r["verdict"]
        words = {"error": "Fix first", "warning": "Warnings", "ok": "Ready to wire",
                 "empty": "No electronics"}[v["level"]]
        self.pill.setText(words)
        c = t[LEVEL_COLOUR[v["level"]] if v["level"] != "empty" else "dim"]
        self.pill.setStyleSheet(
            "QLabel {{ background: {c}; color: #ffffff; border: 1px solid {c}; "
            "border-radius: 11px; padding: 3px 10px; }}".format(c=c))

    def refresh(self):
        doc = self.doc()
        try:
            self.r = gather(doc, self.inputs())
        except Exception as exc:                        # noqa: BLE001
            _log("gather: %r" % (exc,))
            self.r = E().analyse({"modules": []})
        r = self.r
        name = r["project"] or "Design"
        self.setWindowTitle(TITLE % name)
        self.title.setText(TITLE % name)
        self.sub.setText("From the design on %s · %s · not tested on hardware"
                         % (r["made"], r["firmware"]["sdk"]))
        self._fill_pill()
        keep = self.nav.currentRow()
        self._building = True
        for key, _w, _i in PAGES:
            _sc, lay = self.pages[key]
            _clear(lay)
            getattr(self, "_page_" + key)(lay)
            lay.addStretch(1)
        self._building = False
        if keep >= 0:
            self.nav.setCurrentRow(keep)

    # -------------------------------------------------------- pages
    def _page_overview(self, lay):
        r = self.r
        t = style.tokens()
        card, cl = _card()
        big = _lab(r["verdict"]["text"], "ElBig")
        cl.addWidget(big)
        counts = QtWidgets.QHBoxLayout()
        counts.setSpacing(28)
        for lvl, words in (("error", "errors"), ("warning", "warnings"), ("note", "notes")):
            n = sum(x["level"] == lvl for x in r["rules"])
            c = QtWidgets.QVBoxLayout()
            c.setSpacing(0)
            num = _lab(str(n), "ElCount", wrap=False)
            if n and lvl != "note":
                num.setStyleSheet("color: %s;" % t[LEVEL_COLOUR[lvl]])
            c.addWidget(num)
            c.addWidget(_lab(words, "ElMuted", wrap=False))
            counts.addLayout(c)
        mods = [m for m in r["modules"]]
        c = QtWidgets.QVBoxLayout()
        c.setSpacing(0)
        c.addWidget(_lab(str(len(mods)), "ElCount", wrap=False))
        c.addWidget(_lab("modules", "ElMuted", wrap=False))
        counts.addLayout(c)
        counts.addStretch(1)
        cl.addLayout(counts)
        if r["modules"]:
            cl.addWidget(_lab("Power: " + E().budget_line(r["budget"]), "ElText", select=True))
        lay.addWidget(card)
        if r["rules"]:
            lay.addWidget(_lab("RULE CHECKS", "ElH"))
            for x in r["rules"]:
                lay.addWidget(self._rule_card(x))
        if r["unknown"]:
            card, cl = _card()
            cl.addWidget(_lab("NOT KNOWN YET", "ElH"))
            cl.addWidget(_lab("\n".join("• " + u for u in r["unknown"] + [E().LINE_AB_NOTE]),
                              "ElMuted", select=True))
            cl.addWidget(_lab(W().PINOUT_ASK, "ElMuted", select=True))
            lay.addWidget(card)

    def _rule_card(self, x):
        t = style.tokens()
        f = QtWidgets.QFrame()
        f.setObjectName("ElRule")
        h = QtWidgets.QHBoxLayout(f)
        h.setContentsMargins(0, 0, 12, 0)
        h.setSpacing(12)
        bar = QtWidgets.QFrame()
        bar.setFixedWidth(5)
        bar.setStyleSheet("background: %s; border-top-left-radius: 10px;"
                          "border-bottom-left-radius: 10px;" % t[LEVEL_COLOUR[x["level"]]])
        h.addWidget(bar)
        col = QtWidgets.QVBoxLayout()
        col.setContentsMargins(0, 10, 0, 10)
        col.setSpacing(3)
        head = _lab("%s%s" % (E().LEVEL_WORDS[x["level"]],
                              (" · port %s" % "+".join(map(str, x["ports"])))
                              if x["ports"] else ""), "ElH", wrap=False)
        col.addWidget(head)
        col.addWidget(_lab(x["text"], "ElRuleText", select=True))
        if x["fix"]:
            col.addWidget(_lab("Fix: " + x["fix"], "ElRuleFix", select=True))
        h.addLayout(col, 1)
        return f

    def _svg_page(self, lay, svg_light_dark, base, title):
        dark = style.mode() == "dark"
        text = svg_light_dark("dark" if dark else "light")
        card, cl = _card()
        cl.addWidget(svg_widget(text))
        lay.addWidget(card)
        row = QtWidgets.QHBoxLayout()
        for ext, words in ((".pdf", "Save PDF"), (".png", "Save picture"), (".svg", "Save SVG")):
            row.addWidget(_btn(words, slot=lambda _=False, e=ext: self._save_svg(
                svg_light_dark("light"), base + e, title)))
        row.addStretch(1)
        lay.addLayout(row)

    def _page_schematic(self, lay):
        r = self.r
        self._svg_page(lay, lambda th: E().schematic_svg(r, th),
                       "%s schematic" % (r["project"] or "Design"), "Block schematic")
        lay.addWidget(_lab(E().LINE_AB_NOTE + " " + E().RAILS_NOTE, "ElMuted"))

    def _page_wiring(self, lay):
        from . import wiring_view
        p = wiring_view.WiringPanel()
        p.set_wiring(self.r["wiring"], self.folder())
        card, cl = _card()
        cl.addWidget(p)
        lay.addWidget(card)
        self.wiring_panel = p

    def _page_ports(self, lay):
        r = self.r
        tbl = QtWidgets.QTableWidget(len(r["ports"]), 6)
        tbl.setObjectName("ElTable")
        tbl.setHorizontalHeaderLabels(["PORT", "MODULE", "LINE A", "LINE B",
                                       "SDK LETS IT DO", "CONNECTION"])
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        tbl.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        tbl.setShowGrid(False)
        t = style.tokens()
        for i, p in enumerate(r["ports"]):
            vals = [str(p["port"]), p["name"] or ("reserved in the SDK" if p["state"] == "reserved"
                                                  else "free"),
                    p["lines"].get("A", ""), p["lines"].get("B", ""), p["can"], p["how"]]
            for j, v in enumerate(vals):
                it = QtWidgets.QTableWidgetItem(v)
                if p["state"] != "used":
                    it.setForeground(QtGui.QColor(t["dim"]))
                tbl.setItem(i, j, it)
        hh = tbl.horizontalHeader()
        hh.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        hh.setStretchLastSection(True)
        tbl.setMinimumHeight(36 + 30 * len(r["ports"]))
        lay.addWidget(tbl)
        lay.addWidget(_lab(E().LINE_AB_NOTE, "ElMuted"))
        lay.addWidget(_lab("Ports 1-6 run down the left edge, 9-14 down the right, 7 at "
                           "the top and 8 (USB-C) at the bottom, as on the silkscreen.",
                           "ElMuted"))

    def _page_power(self, lay):
        r = self.r
        b = r["budget"]
        inp = self.inputs()
        card, cl = _card()
        cl.addWidget(_lab(E().budget_line(b), "ElBig"))
        row = QtWidgets.QHBoxLayout()
        row.addWidget(_lab("Supply", "ElText", wrap=False))
        self.supply = QtWidgets.QComboBox()
        self.supply.setObjectName("ElCombo")
        for k, (words, ma) in E().SUPPLIES.items():
            self.supply.addItem("%s – %s mA" % (words, "{:,}".format(ma)), k)
        self.supply.setCurrentIndex(max(0, self.supply.findData(b["supply"])))
        self.supply.currentIndexChanged.connect(
            lambda _i: self._power_changed(supply=self.supply.currentData()))
        row.addWidget(self.supply)
        row.addSpacing(18)
        row.addWidget(_lab("Power bank (mAh)", "ElText", wrap=False))
        self.bank = QtWidgets.QSpinBox()
        self.bank.setObjectName("ElSpin")
        self.bank.setRange(0, 100000)
        self.bank.setSingleStep(1000)
        self.bank.setSpecialValueText("none")
        self.bank.setValue(int(inp.get("bank_mah") or 0))
        self.bank.editingFinished.connect(lambda: self._power_changed(bank_mah=self.bank.value()))
        row.addWidget(self.bank)
        row.addStretch(1)
        cl.addLayout(row)
        if b.get("bank_hours"):
            cl.addWidget(_lab("On a %s mAh power bank: about %s h at full load (at least)."
                              % ("{:,}".format(int(b["bank_mah"])), b["bank_hours"]), "ElText"))
        lay.addWidget(card)
        lay.addWidget(_lab("LOADS – TYPE A MEASURED VALUE TO REPLACE A PLANNING FIGURE", "ElH"))
        tbl = QtWidgets.QTableWidget(len(b["rows"]), 4)
        tbl.setObjectName("ElTable")
        tbl.setHorizontalHeaderLabels(["LOAD", "PORTS", "mA (PEAK, 5 V)", "SOURCE"])
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        for i, row_ in enumerate(b["rows"]):
            vals = [row_["name"], "+".join(map(str, row_["ports"])),
                    "" if row_["ma"] is None else "%g" % row_["ma"],
                    (row_["source"] + ": " if row_["source"] else "") + row_["why"]]
            for j, v in enumerate(vals):
                it = QtWidgets.QTableWidgetItem(v)
                it.setData(QtCore.Qt.UserRole, row_["key"])
                if j != 2 or row_.get("own_supply"):
                    it.setFlags(it.flags() & ~QtCore.Qt.ItemIsEditable)
                tbl.setItem(i, j, it)
        hh = tbl.horizontalHeader()
        hh.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        hh.setStretchLastSection(True)
        tbl.setMinimumHeight(40 + 30 * len(b["rows"]))
        tbl.itemChanged.connect(self._load_edited)
        self.loads_table = tbl
        lay.addWidget(tbl)
        card, cl = _card()
        cl.addWidget(svg_widget(E().power_tree_svg(r, "dark" if style.mode() == "dark"
                                                   else "light")))
        lay.addWidget(card)
        lay.addWidget(_lab("Supplies give what the USB specifications promise. Planning "
                           "figures come from each chip's datasheet; the Atech modules' own "
                           "currents are not published, so measure them and type them in. "
                           "Kept in the product folder, not in the design.", "ElMuted"))

    def _load_edited(self, it):
        if self._building or it.column() != 2:
            return
        key = it.data(QtCore.Qt.UserRole)
        txt = (it.text() or "").strip().replace(",", ".")
        loads = dict(self.inputs().get("loads") or {})
        if not txt:
            loads.pop(key, None)
        else:
            try:
                loads[key] = max(0.0, float(txt))
            except ValueError:
                return
        self._power_changed(loads=loads)

    def _power_changed(self, **kw):
        if self._building:
            return
        self.save_inputs(**kw)
        QtCore.QTimer.singleShot(0, self.refresh)

    # -------------------------------------------------------- firmware
    def firmware_yaml(self):
        """(text, where it came from)."""
        y = agent_yaml(self.doc())
        if y:
            return y, "the agent's project.yaml from this design's chat"
        return self.r["firmware"]["yaml"], "made from the design's modules"

    def _page_firmware(self, lay):
        r = self.r
        entries = [e for e in r["firmware"]["entries"] if e.get("id")]
        card, cl = _card()
        if not entries:
            cl.addWidget(_lab("Nothing to program: no module in this design has an Atech "
                              "SDK driver.", "ElBig"))
            lay.addWidget(card)
            return
        text, where = self.firmware_yaml()
        cl.addWidget(_lab("%d module%s to program · %s"
                          % (len(entries), "" if len(entries) == 1 else "s", where), "ElText"))
        if self.sdk:
            cl.addWidget(_lab("Atech SDK: %s" % self.sdk, "ElMuted", select=True))
        else:
            cl.addWidget(_lab("The Atech SDK is not installed. In a terminal: %s  (or %s). %s"
                              % (sdk_tools.INSTALL_COMMAND, sdk_tools.INSTALL_ALT,
                                 sdk_tools.INSTALL_NOTE), "ElText", select=True))
            r0 = QtWidgets.QHBoxLayout()
            r0.addWidget(_btn("Copy install command", slot=lambda: QtWidgets.QApplication
                              .clipboard().setText(sdk_tools.INSTALL_COMMAND)))
            r0.addWidget(_btn("Choose the atech program\u2026", slot=self.choose_sdk,
                              tip="Already installed somewhere else (a venv)? Pick its "
                                  "bin/atech."))
            r0.addWidget(_btn("Look again", slot=self.look_again))
            r0.addStretch(1)
            cl.addLayout(r0)
        row = QtWidgets.QHBoxLayout()
        self.cmd_buttons = {}
        for key in sdk_tools.ORDER:
            words, _a, board, what = sdk_tools.COMMANDS[key]
            b = _btn(words, primary=key in ("build", "upload"),
                     slot=lambda _=False, k=key: self.run(k),
                     tip=what + (" Needs the board on USB." if board else ""))
            b.setEnabled(bool(self.sdk))
            self.cmd_buttons[key] = b
            row.addWidget(b)
        self.btn_stop = _btn("Stop", slot=self.stop_run)
        self.btn_stop.setEnabled(False)
        row.addWidget(self.btn_stop)
        row.addStretch(1)
        cl.addLayout(row)
        row2 = QtWidgets.QHBoxLayout()
        row2.addWidget(_btn("Write firmware folder", slot=self.write_firmware,
                            tip="Write project.yaml into the product folder"))
        row2.addWidget(_btn("Open folder", slot=lambda: self._reveal(
            sdk_tools.firmware_dir(r["project"] or "Design"))))
        row2.addStretch(1)
        cl.addLayout(row2)
        self.run_status = _lab("", "ElText")
        cl.addWidget(self.run_status)
        lay.addWidget(card)
        lay.addWidget(_lab("PROJECT.YAML", "ElH"))
        ed = QtWidgets.QPlainTextEdit(text)
        ed.setObjectName("ElYaml")
        ed.setReadOnly(True)
        ed.setMinimumHeight(220)
        lay.addWidget(ed)
        placement = [x for x in r["rules"] if x["id"] == "sdk.placement"]
        if placement:
            lay.addWidget(_lab("SDK PLACEMENT", "ElH"))
            for x in placement:
                lay.addWidget(self._rule_card(x))
        lay.addWidget(_lab("OUTPUT", "ElH"))
        self.console = QtWidgets.QPlainTextEdit()
        self.console.setObjectName("ElConsole")
        self.console.setReadOnly(True)
        self.console.setMinimumHeight(220)
        self.console.setPlaceholderText("The Atech SDK's output appears here.")
        lay.addWidget(self.console)

    def choose_sdk(self):
        path, _f = QtWidgets.QFileDialog.getOpenFileName(
            self, "Choose the atech program", os.path.expanduser("~"))
        if path and sdk_tools.choose(path):
            self.look_again()

    def look_again(self):
        self.sdk = sdk_tools.find()
        self.refresh()
        self.show_page("firmware")

    def write_firmware(self):
        text, _where = self.firmware_yaml()
        folder = sdk_tools.firmware_dir(self.r["project"] or "Design")
        path = sdk_tools.write_firmware(folder, text)
        if hasattr(self, "run_status"):
            self.run_status.setText("Wrote %s" % path)
        return folder

    def run(self, key):
        if not self.sdk:
            return False
        folder = self.write_firmware()
        if self.runner is None:
            self.runner = sdk_tools.make_runner(self)
            self.runner.line.connect(lambda s: self.console.appendPlainText(s))
            self.runner.finished.connect(self._run_done)
        if self.runner.running():
            return False
        self.console.clear()
        self.run_status.setText("Running: %s…" % sdk_tools.COMMANDS[key][0])
        for b in self.cmd_buttons.values():
            b.setEnabled(False)
        self.btn_stop.setEnabled(True)
        return self.runner.start(key, folder, exe=self.sdk)

    def stop_run(self):
        if self.runner is not None:
            self.runner.stop()

    def _run_done(self, key, code, summary):
        try:
            self.run_status.setText(summary)
            for b in self.cmd_buttons.values():
                b.setEnabled(True)
            self.btn_stop.setEnabled(False)
        except RuntimeError:                            # page rebuilt meanwhile
            pass
        if code == 0 and key in ("build", "upload", "validate", "emulate"):
            mark = {"build": "firmware_built", "upload": "flashed", "validate": "validated",
                    "emulate": "emulated"}[key]
            product.mark(self.folder(), mark)
            if key == "upload":
                product.mark(self.folder(), "firmware_built")

    # -------------------------------------------------------- bring-up
    def _page_bringup(self, lay):
        r = self.r
        if not r["modules"]:
            lay.addWidget(_lab(W().EMPTY, "ElText"))
            return
        ticks = product.read_state(self.folder()).get("bringup") or {}
        done = set(ticks.get("done") or [])
        for sec in r["bringup"]:
            card, cl = _card()
            cl.addWidget(_lab(sec["title"].upper(), "ElH"))
            for s in sec["steps"]:
                cb = QtWidgets.QCheckBox(s)
                cb.setObjectName("ElTick")
                cb.setChecked(s in done)
                cb.toggled.connect(lambda on, s=s: self._tick(s, on))
                cl.addWidget(cb)
            lay.addWidget(card)

    def _tick(self, step, on):
        if self._building:
            return
        st = product.read_state(self.folder()).get("bringup") or {}
        done = set(st.get("done") or [])
        (done.add if on else done.discard)(step)
        product.mark(self.folder(), "bringup", done=sorted(done))

    # -------------------------------------------------------- export
    def _page_export(self, lay):
        r = self.r
        card, cl = _card()
        cl.addWidget(_lab("Everything on these pages, to print for the bench or send to "
                          "someone.", "ElText"))
        name = r["project"] or "Design"
        for words, base, fn in (
                ("Electrical report (PDF)", "%s electrical.pdf" % name, report_pdf),
                ("Report as text (Markdown)", "%s electrical.md" % name,
                 lambda rr, p: self._write(p, E().markdown(rr))),
                ("Connection list (CSV)", "%s connections.csv" % name,
                 lambda rr, p: self._write(p, E().connections_csv(rr))),
                ("Netlist (JSON, port level)", "%s netlist.json" % name,
                 lambda rr, p: self._write(p, E().netlist_json(rr))),
                ("project.yaml (firmware)", "project.yaml",
                 lambda rr, p: self._write(p, self.firmware_yaml()[0]))):
            row = QtWidgets.QHBoxLayout()
            row.addWidget(_lab(words, "ElText", wrap=False), 1)
            row.addWidget(_btn("Save…", slot=lambda _=False, b=base, f=fn: self._save(b, f)))
            cl.addLayout(row)
        lay.addWidget(card)
        self.export_status = _lab("", "ElMuted", select=True)
        lay.addWidget(self.export_status)
        lay.addWidget(_lab("The netlist names each port's nets (P3_DATA1, +5V…) but no pin "
                           "numbers: Atech has not published the pin order.", "ElMuted"))

    @staticmethod
    def _write(path, text):
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        return path

    def _ask_path(self, base):
        folder = self.folder()
        os.makedirs(folder, exist_ok=True)
        path, _f = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save", os.path.join(folder, base.replace(os.sep, "-")))
        return path

    def _save(self, base, fn):
        path = self._ask_path(base)
        if not path:
            return None
        return self.save_to(path, fn)

    def save_to(self, path, fn):
        try:
            fn(self.r, path)
            msg = "Saved: %s" % path
        except Exception as exc:                        # noqa: BLE001
            _log("save: %r" % (exc,))
            msg = "Could not save: %s" % exc
        if hasattr(self, "export_status"):
            self.export_status.setText(msg)
        return path

    def _save_svg(self, text, base, title):
        path = self._ask_path(base)
        if path:
            export_svg(text, path, title)

    @staticmethod
    def _reveal(folder):
        os.makedirs(folder, exist_ok=True)
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder))


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


def open_suite(doc=None, page="overview", parent=None):
    """Show the suite (one window; raised and refreshed when already open)."""
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
                w.show_page(page)
                w.raise_()
                w.activateWindow()
                return w
        except RuntimeError:
            pass
        _OPEN.remove(w)
    w = ElectricalSuite(doc, parent, page)
    _OPEN.append(w)
    w.show()
    return w
