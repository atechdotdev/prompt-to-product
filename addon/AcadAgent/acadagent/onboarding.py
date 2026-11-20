"""Getting started: the guided tour of Prompt2Product (R1010).

A new user sees the whole path once, in plain words, before the first
project: say what you want, the electronics (the Atech board and its
modules), the CAD (the case, built in FreeCAD), the firmware (handled by
Atech Studio or `pip install atech`, nothing to write), and make it
(print and assemble). The last step has the prompt box, so the tour ends
by starting a product.

    STEPS                       the tour's steps (pure data; tests read it)
    steps()                     STEPS as dicts
    seen(cfg=None)              True once the tour was finished or skipped
    mark_seen()                 remember that (settings.json)
    should_show_first_run(...)  pure: open the tour by itself at start-up?
    GuideDialog(start, parent)  the tour
    open_guide(start=0, parent=None)
    maybe_show_first_run(parent=None)   start-up hook (shell.install)

Home's "How it works" strip (shell.HomeView) opens the tour at a step.
"""
import os

from PySide6 import QtCore, QtGui, QtWidgets

from . import style

#: Bumped when the tour changes enough that everyone should see it again.
VERSION = 1
SEEN_KEY = "onboarding_seen"
STUDIO_URL = "https://studio.atech.dev"
SDK_INSTALL = "pip install atech"
SDK_URL = "https://github.com/atechdotdev/python-sdk"

#: (key, kicker, title, line, points). Plain words, no project jargon: this
#: is the first thing a new user reads.
STEPS = (
    ("describe", "START HERE", "Say what you want to make",
     "Describe a product in your own words: what it does, roughly how big "
     "it is, where it goes. The agent plans the whole thing from that.",
     ("\"A lamp that wakes me up\" is enough to start.",
      "Every answer is measured off the model, so sizes are real.",
      "Change anything later by just asking.")),
    ("electronics", "PART 1 OF 3", "Here is the electronics",
     "The Atech board with snap-in modules: buttons, lights, screens, "
     "speakers, sensors, motors. No soldering and no breadboard.",
     ("The agent picks the modules and seats each one on a port.",
      "The Electrical suite shows the schematic, the power budget and "
      "the wiring, and checks every port.",
      "Everything you need is in the Atech shop on atech.dev.")),
    ("cad", "PART 2 OF 3", "Here is the CAD",
     "The agent designs the case in FreeCAD as real solids, built around "
     "the board, with an opening over every module that needs one.",
     ("Fits, walls and clearances are checked before you see it.",
      "Orbit it, explode it, edit any part by hand or by asking.",
      "Ready for your Bambu printer, or have Atech print it.")),
    ("firmware", "PART 3 OF 3", "Here is the firmware, handled for you",
     "You do not write firmware. Atech Studio or the Atech SDK (pip "
     "install atech) makes it from your design and puts it on the board.",
     ("The app writes the firmware project from the modules you seated.",
      "Build it, try it without a board, then flash it over USB.",
      "In your browser: Atech Studio. On your computer: pip install "
      "atech.")),
    ("make", "LAST STEP", "Make it",
     "Print the parts, snap in the board and modules, and flash the "
     "firmware. Make it walks you through each step and packs every file "
     "into one folder.",
     ("Print files for your printer, a parts list, assembly steps.",
      "Or order the board, the modules and the prints from Atech.",
      "Now: what will you make?")),
)

#: The three parts of a product, for Home's "How it works" strip:
#: (step key, title, line). Their order is the tour's.
PARTS = (
    ("electronics", "Electronics",
     "The Atech board and snap-in modules. No soldering."),
    ("cad", "CAD",
     "A real case, designed in FreeCAD around the board."),
    ("firmware", "Firmware",
     "Handled for you by Atech Studio or pip install atech."),
)


def steps():
    return [dict(key=k, kicker=kk, title=t, line=line, points=list(p))
            for k, kk, t, line, p in STEPS]


def index_of(key):
    """The tour's step number of `key` (0 when unknown)."""
    for i, s in enumerate(STEPS):
        if s[0] == key:
            return i
    return 0


def _log(msg):
    try:
        import FreeCAD
        FreeCAD.Console.PrintLog("[Atech] onboarding: %s\n" % msg)
    except Exception:                                   # noqa: BLE001
        pass


# ---------------------------------------------------------------- state
def seen(cfg=None):
    if cfg is None:
        from . import settings
        cfg = settings.load()
    try:
        return int(cfg.get(SEEN_KEY) or 0) >= VERSION
    except (TypeError, ValueError):
        return False


def mark_seen():
    try:
        from . import settings
        return settings.update(**{SEEN_KEY: VERSION})
    except Exception as exc:                            # noqa: BLE001
        _log("mark seen: %r" % (exc,))
        return False


def should_show_first_run(cfg=None, env=None):
    """Open the tour by itself? Once (until VERSION changes), and never in
    a headless or test run (ATECH_ONBOARDING=0, or the offscreen Qt
    platform). ATECH_ONBOARDING=1 forces it. Saved projects do not count:
    the first run copies the default projects in (default_projects)."""
    env = os.environ if env is None else env
    force = (env.get("ATECH_ONBOARDING") or "").strip()
    if force == "1":
        return True
    if force == "0" or env.get("QT_QPA_PLATFORM") == "offscreen":
        return False
    return not seen(cfg)


# ---------------------------------------------------------------- the view
QSS = """
#Guide {{ background: {base}; }}
#GdRail {{ background: {panel}; border-right: 1px solid {line}; }}
#GdBrand {{ color: {text}; font-family: 'Sen', {UI}; font-size: 15px; font-weight: 700; }}
#GdRailSub {{ color: {muted}; font-family: {UI}; font-size: 11px; }}
#GdStep {{ background: transparent; color: {muted}; border: none; border-radius: 10px;
    padding: 8px 10px; text-align: left; font-family: {UI}; font-size: 13px; }}
#GdStep:hover {{ background: {hover}; color: {text}; }}
#GdStep:checked {{ background: {bubble}; color: {text}; font-weight: 700; }}
#GdKicker {{ color: {accent}; font-family: {UI}; font-size: 12px; font-weight: 700;
    letter-spacing: 0.5px; }}
#GdTitle {{ color: {text}; font-family: 'Sen', {UI}; font-size: 30px; font-weight: 700; }}
#GdLine {{ color: {text}; font-family: {UI}; font-size: 15px; }}
#GdPoint {{ color: {muted}; font-family: {UI}; font-size: 13px; }}
#GdCard {{ background: {panel}; border: 1px solid {line}; border-radius: 16px; }}
#GdCardTitle {{ color: {text}; font-family: {UI}; font-size: 13px; font-weight: 700; }}
#GdCardSub {{ color: {muted}; font-family: {UI}; font-size: 12px; }}
#GdCode {{ background: {sunken}; color: {text}; border: 1px solid {line};
    border-radius: 8px; padding: 6px 10px; font-family: Menlo, Consolas, monospace;
    font-size: 13px; }}
#GdBox {{ background: {sunken}; border: 1px solid {line_strong}; border-radius: 20px; }}
#GdPrompt {{ background: transparent; color: {text}; border: none; padding: 0 6px;
    min-height: 38px; font-family: {UI}; font-size: 15px; }}
#GdBtn {{ background: {btn_bg}; color: {btn_text}; border: none; border-radius: 16px;
    padding: 0 18px; min-height: 34px; font-family: {UI}; font-size: 13px; font-weight: 600; }}
#GdBtn:hover {{ background: {btn_bg_hover}; }}
#GdBtn:disabled {{ background: {line}; color: {dim}; }}
#GdGhost {{ background: transparent; color: {text}; border: 1px solid {line_strong};
    border-radius: 16px; padding: 0 14px; min-height: 32px; font-family: {UI};
    font-size: 13px; }}
#GdGhost:hover {{ background: {hover}; }}
#GdLink {{ background: transparent; color: {muted}; border: none; padding: 0 6px;
    min-height: 30px; font-family: {UI}; font-size: 13px; }}
#GdLink:hover {{ color: {text}; }}
#GdFoot {{ border-top: 1px solid {line}; }}
#GdDots {{ color: {dim}; font-family: {UI}; font-size: 12px; }}
"""


def _lab(text, name, wrap=True):
    lab = QtWidgets.QLabel(text)
    lab.setObjectName(name)
    lab.setWordWrap(wrap)
    lab.setTextFormat(QtCore.Qt.PlainText)
    return lab


def _btn(text, name="GdGhost", slot=None, acc=None):
    b = QtWidgets.QPushButton(text)
    b.setObjectName(name)
    b.setCursor(QtCore.Qt.PointingHandCursor)
    b.setAccessibleName(acc or text)
    if slot is not None:
        b.clicked.connect(slot)
    return b


def _open_url(url):
    QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))


class GuideDialog(QtWidgets.QDialog):
    """The tour: the steps on the left, one step at a time on the right,
    Back / Next under it. Closing it (Skip, Esc, Done, or starting a
    product) marks it seen."""

    started = QtCore.Signal(str)      # the prompt a product was started from

    def __init__(self, start=0, parent=None, on_start=None):
        super().__init__(parent)
        self.setObjectName("Guide")
        self.setWindowTitle("Getting started – %s" % style.PRODUCT)
        self.setAccessibleName("Getting started guide")
        self.resize(900, 600)
        self._on_start = on_start
        self.steps = steps()
        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        rail = QtWidgets.QFrame()
        rail.setObjectName("GdRail")
        rail.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        rail.setFixedWidth(230)
        rl = QtWidgets.QVBoxLayout(rail)
        rl.setContentsMargins(16, 22, 16, 18)
        rl.setSpacing(4)
        rl.addWidget(_lab(style.PRODUCT, "GdBrand", wrap=False))
        rl.addWidget(_lab("From an idea to a working product", "GdRailSub"))
        rl.addSpacing(18)
        self.rail_btns = []
        group = QtWidgets.QButtonGroup(self)
        group.setExclusive(True)
        names = ("Your idea", "Electronics", "CAD", "Firmware", "Make it")
        for i, name in enumerate(names[:len(self.steps)]):
            b = _btn("%d   %s" % (i + 1, name), "GdStep",
                     lambda _=False, n=i: self.go(n),
                     "Step %d: %s" % (i + 1, name))
            b.setCheckable(True)
            group.addButton(b)
            rl.addWidget(b)
            self.rail_btns.append(b)
        rl.addStretch(1)
        rl.addWidget(_lab("Open this again from Settings → Getting started.",
                          "GdRailSub"))
        root.addWidget(rail)

        right = QtWidgets.QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        self.stack = QtWidgets.QStackedWidget()
        for s in self.steps:
            self.stack.addWidget(self._page(s))
        right.addWidget(self.stack, 1)

        foot = QtWidgets.QFrame()
        foot.setObjectName("GdFoot")
        fl = QtWidgets.QHBoxLayout(foot)
        fl.setContentsMargins(36, 12, 24, 14)
        fl.setSpacing(8)
        self.btn_skip = _btn("Skip the tour", "GdLink", self.finish)
        fl.addWidget(self.btn_skip)
        fl.addStretch(1)
        self.dots = _lab("", "GdDots", wrap=False)
        fl.addWidget(self.dots)
        fl.addSpacing(10)
        self.btn_back = _btn("Back", "GdGhost", self.back)
        fl.addWidget(self.btn_back)
        self.btn_next = _btn("Next", "GdBtn", self.next)
        fl.addWidget(self.btn_next)
        right.addWidget(foot)
        root.addLayout(right, 1)

        self.setStyleSheet(style.qss(QSS))
        self.go(start)

    # -- pages
    def _page(self, s):
        page = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(page)
        v.setContentsMargins(40, 36, 40, 20)
        v.setSpacing(0)
        v.addWidget(_lab(s["kicker"], "GdKicker", wrap=False))
        v.addSpacing(8)
        v.addWidget(_lab(s["title"], "GdTitle"))
        v.addSpacing(12)
        v.addWidget(_lab(s["line"], "GdLine"))
        v.addSpacing(16)
        for p in s["points"]:
            v.addWidget(_lab("•  " + p, "GdPoint"))
            v.addSpacing(5)
        v.addSpacing(18)
        extra = getattr(self, "_extra_" + s["key"], None)
        if extra is not None:
            w = extra()
            if w is not None:
                v.addWidget(w)
        v.addStretch(1)
        return page

    def _card(self, title, sub, buttons=()):
        card = QtWidgets.QFrame()
        card.setObjectName("GdCard")
        card.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        h = QtWidgets.QHBoxLayout(card)
        h.setContentsMargins(16, 14, 16, 14)
        h.setSpacing(12)
        col = QtWidgets.QVBoxLayout()
        col.setSpacing(3)
        col.addWidget(_lab(title, "GdCardTitle"))
        if isinstance(sub, QtWidgets.QWidget):
            col.addWidget(sub)
        else:
            col.addWidget(_lab(sub, "GdCardSub"))
        h.addLayout(col, 1)
        for b in buttons:
            h.addWidget(b, 0, QtCore.Qt.AlignVCenter)
        return card

    def _parts_row(self, current):
        """The three parts of a product, the current one marked."""
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(10)
        for key, title, line in PARTS:
            mark = "→  " if key == current else ""
            row.addWidget(self._card(mark + title, line), 1)
        w = QtWidgets.QWidget()
        w.setLayout(row)
        return w

    def _extra_describe(self):
        return self._parts_row(None)

    def _extra_electronics(self):
        from . import shell
        return self._card(
            "The board and modules",
            "See every module, its ports and what it does.",
            [_btn("Board and modules", "GdGhost",
                  lambda: _open_url(shell.site_url("/modules")))])

    def _extra_cad(self):
        return self._parts_row("cad")

    def _extra_firmware(self):
        box = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(10)
        v.addWidget(self._card(
            "Atech Studio, in your browser",
            "Nothing to install. Open your design, build and flash.",
            [_btn("Open Atech Studio", "GdGhost",
                  lambda: _open_url(STUDIO_URL))]))
        code = _lab(SDK_INSTALL, "GdCode", wrap=False)
        code.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.btn_copy = _btn("Copy", "GdGhost", self._copy_install,
                             "Copy the install command")
        v.addWidget(self._card(
            "The Atech SDK, on your computer", code,
            [self.btn_copy,
             _btn("Docs", "GdLink", lambda: _open_url(SDK_URL),
                  "The Atech SDK on GitHub")]))
        return box

    def _copy_install(self):
        QtWidgets.QApplication.clipboard().setText(SDK_INSTALL)
        self.btn_copy.setText("Copied")
        QtCore.QTimer.singleShot(1500, lambda: _alive_set(self.btn_copy, "Copy"))

    def _extra_make(self):
        from . import shell
        box = QtWidgets.QFrame()
        box.setObjectName("GdBox")
        box.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        bl = QtWidgets.QHBoxLayout(box)
        bl.setContentsMargins(14, 6, 6, 6)
        bl.setSpacing(8)
        self.prompt = QtWidgets.QLineEdit()
        self.prompt.setObjectName("GdPrompt")
        self.prompt.setPlaceholderText(
            getattr(shell, "HOME_IDEAS", ("A lamp that wakes me up",))[0] + "…")
        self.prompt.setAccessibleName("Describe what to make")
        self.prompt.returnPressed.connect(self.make_it)
        bl.addWidget(self.prompt, 1)
        self.btn_go = _btn("Make it", "GdBtn", self.make_it,
                           "Make it: start a new project from this")
        bl.addWidget(self.btn_go)
        self.prompt.textChanged.connect(
            lambda t: self.btn_go.setEnabled(bool(t.strip())))
        self.btn_go.setEnabled(False)
        return box

    # -- moving
    def go(self, n):
        n = max(0, min(int(n), len(self.steps) - 1))
        self.stack.setCurrentIndex(n)
        self.rail_btns[n].setChecked(True)
        last = n == len(self.steps) - 1
        self.btn_back.setEnabled(n > 0)
        self.btn_next.setText("Done" if last else "Next")
        self.btn_skip.setVisible(not last)
        self.dots.setText("%d of %d" % (n + 1, len(self.steps)))
        if last and getattr(self, "prompt", None) is not None:
            self.prompt.setFocus(QtCore.Qt.OtherFocusReason)
        return n

    def current(self):
        return self.stack.currentIndex()

    def next(self):
        if self.current() >= len(self.steps) - 1:
            return self.finish()
        return self.go(self.current() + 1)

    def back(self):
        return self.go(self.current() - 1)

    def finish(self):
        mark_seen()
        self.accept()

    def reject(self):                                  # Esc, the close box
        mark_seen()
        super().reject()

    def make_it(self):
        text = self.prompt.text().strip()
        if not text:
            return None
        self.finish()
        self.started.emit(text)
        if self._on_start is not None:
            return self._on_start(text)
        from . import shell
        return shell.start_from_prompt(text)


def _alive_set(btn, text):
    try:
        btn.setText(text)
    except RuntimeError:
        pass


_OPEN = []


def open_guide(start=0, parent=None):
    """Show the tour at step `start` (a number or a step key). One at a
    time: a second call brings the open one forward at that step."""
    if isinstance(start, str):
        start = index_of(start)
    for d in list(_OPEN):
        try:
            if d.isVisible():
                d.go(start)
                d.raise_()
                d.activateWindow()
                return d
        except RuntimeError:
            pass
        _OPEN.remove(d)
    if parent is None:
        try:
            import FreeCADGui
            parent = FreeCADGui.getMainWindow()
        except Exception:                               # noqa: BLE001
            parent = None
    d = GuideDialog(start, parent)
    d.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
    d.destroyed.connect(lambda *_a, x=d: x in _OPEN and _OPEN.remove(x))
    _OPEN.append(d)
    d.show()
    return d


def maybe_show_first_run(parent=None):
    """At start-up: the tour, once, for someone new. Never raises."""
    try:
        if should_show_first_run():
            return open_guide(0, parent)
    except Exception as exc:                            # noqa: BLE001
        _log("first run: %r" % (exc,))
    return None
