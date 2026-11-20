"""examples_gallery - every example product, in one window (R970).

Home shows a short row of examples; "All examples" opens this gallery:
a picture of each product (example_pictures/<key>.png, the review
renderer's 3/4 hero view; a shipped default project's own thumbnail
first), its name and one line, grouped by what it is (CATEGORIES), with
search. A card starts a NEW project from that example: the shipped
default project's fresh copy when this installation has it (instant,
shell.open_default), else the example script built in the chat
(shell.open_example).

CATALOG is the gallery's order and words. An example on disk that is
missing from it is still listed (under "More", its request as its line),
so a new example shows up the moment it lands.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PICTURES = os.path.join(HERE, "example_pictures")
EXAMPLES_DIR = os.path.join(HERE, "agent_kit", "examples")

NEW = "New"
ROBOTS = "Robots & vehicles"
HOME = "Home & living"
DESK = "Desk & creator"
FUN = "Sound & games"
SENSE = "Sensors & smart home"
# R1030: six more kinds, so every example sits with its own sort
KITCHEN = "Kitchen & food"
PETS = "Pets"
OUTDOOR = "Outdoor & garden"
HEALTH = "Health & fitness"
KIDS = "Kids & learning"
MAKER = "Workshop & making"
MORE = "More"
CATEGORIES = (NEW, ROBOTS, HOME, KITCHEN, PETS, OUTDOOR, HEALTH, KIDS, DESK, MAKER,
              FUN, SENSE, MORE)

#: R1030: the newest examples. "New" is a filter over these, not their
#: kind: each still sits in its own category (a NEW tag on its card).
NEW_KEYS = ("tea_steeper", "mail_notifier", "hydration_coaster", 
            "star_projector", "filament_dryer", "vinyl_stand", "drawing_bot", 
            "key_hook", "ball_launcher", "mole_bop",)

#: (example key, title, one line, category). Order = the gallery's order.
CATALOG = (
    # R1030: ten products in ten kinds, the newest
    ("tea_steeper", "Tea timer", "A tower whose arm lifts the tea bag out on time.", KITCHEN),
    ("mail_notifier", "Mailbox flag", "A mailbox box that raises a red flag when post lands.", OUTDOOR),
    ("hydration_coaster", "Water reminder", "A glowing coaster that reminds you to drink.", HEALTH),
    ("star_projector", "Star projector", "A star ball that turns and fills the ceiling with stars.", KIDS),
    ("filament_dryer", "Filament dry box", "A dry box that tracks humidity and filament left.", MAKER),
    ("vinyl_stand", "Now playing stand", "A walnut record ledge that hears the song and shows it.", HOME),
    ("drawing_bot", "Drawing robot", "A turtle robot that draws on paper with a real marker.", ROBOTS),
    ("key_hook", "Who's home key hook", "An oak key board whose name tags glow when you're home.", SENSE),
    ("ball_launcher", "Fetch machine", "An orange drum that fires your dog's ball back out.", PETS),
    ("mole_bop", "Mole bop game", "Bop four glowing moles before they hide.", FUN),
    # R990: ten more products
    ("cloud_lamp", "Cloud lamp", "A glowing cloud on a lightning bolt that flashes to music.", HOME),
    ("on_air_sign", "On air sign", "A studio ON AIR light that glows when you talk.", DESK),
    ("theremin", "Air theremin", "A walnut theremin you play by waving over it.", FUN),
    ("piggy_bank", "Coin counter pig", "A chunky pink pig that counts every coin.", KIDS),
    ("starter_jar", "Sourdough monitor", "A smart jar lid that watches your starter rise.", KITCHEN),
    ("dice_tower", "Dice tower", "A castle keep that counts and announces every roll.", FUN),
    ("cat_wand", "Cat wand toy", "A cat-eared turret that waves a feather wand at your cat.", PETS),
    ("drum_pad", "Drum pad", "Four big rubber pads that play real drum sounds.", FUN),
    ("pill_box", "Pill reminder", "A weekly pill box that glows when it's time.", HEALTH),
    ("fortune_ball", "Fortune ball", "A midnight-blue ball that answers when you shake it.", FUN),
    # R940: the ten viral products (R990: in their own kinds now)
    ("hype_button", "Hype button", "A giant red button that plays airhorns.", FUN),
    ("debug_duck", "Debug duck", "A rubber duck that listens to your bugs and quacks.", FUN),
    ("plant_pal", "Plant pal", "A planter with a face that pouts when it is thirsty.", HOME),
    ("tiny_tv", "Tiny TV", "A tiny walnut TV with rabbit ears that plays GIFs.", DESK),
    ("focus_cube", "Focus cube", "A flip timer: the number on top sets the minutes.", DESK),
    ("retro_camera", "Pixel camera", "A toy camera that takes pixel-art photos.", DESK),
    ("bird_cam", "Bird feeder cam", "A bird feeder that photographs every visitor.", OUTDOOR),
    ("follower_counter", "Follower counter", "A desk trophy with your live follower count.", DESK),
    ("coffee_scale", "Coffee scale", "A pour-over scale with a floating platform and a timer.", KITCHEN),
    ("photo_turntable", "Photo turntable", "A geared 360 turntable for product videos.", DESK),
    # robots and things that move
    ("toy_car", "Toy car", "A chunky 4x4 with driven wheels and lights.", ROBOTS),
    ("desk_robot", "Desk robot", "A little robot whose face is a screen.", ROBOTS),
    ("puppy_bot", "Puppy bot", "A rolling robot dog with screen eyes and a wagging tail.", ROBOTS),
    ("balance_bot", "Balance bot", "A balance bot with a screen face on two big wheels.", ROBOTS),
    ("rover", "Explorer rover", "A 4WD rover with a mast, beacon and solar panel.", ROBOTS),
    ("rc_tank", "RC tank", "A tracked tank with motors, lights and a sensor.", ROBOTS),
    ("sesame_atech", "Sesame walker", "The Sesame walking robot with an Atech board and screen.", ROBOTS),
    ("arm_dock", "Robot arm dock", "A robot arm dock with a control deck and arm plate.", ROBOTS),
    # home
    ("bedside_lamp", "Bedside lamp", "A turned column lamp with a frosted globe.", HOME),
    ("motion_light", "Motion night light", "A wall pebble night light with a frosted moon and PIR eye.", HOME),
    ("smart_planter", "Smart planter", "A desk planter with a readout and an inner pot.", OUTDOOR),
    ("pet_feeder", "Pet feeder", "A hopper feeder with a rotary dispenser and a bowl.", PETS),
    ("photo_frame", "Photo frame", "A wood photo frame on a kickstand, a screen in its mat.", HOME),
    ("alarm_clock", "Alarm clock", "A clock radio leaning back on a wedge foot.", HOME),
    ("desk_fan", "Desk fan", "A guarded fan head on a stem, motor-driven.", HOME),
    # desk and creator
    ("macro_pad", "Macro pad", "A wedge keypad with big keys, a label screen and a dial.", DESK),
    ("desk_organizer", "Desk organizer", "A tray with pen cups, a phone dock and a display.", DESK),
    ("desk_buddy", "Desk buddy", "A little printed character that tests your printer.", MAKER),
    # sound and games
    ("smart_speaker", "Smart speaker", "A round speaker with a light ring and buttons.", FUN),
    ("music_box", "Music box", "A walnut music box with a knob and a lit window.", FUN),
    ("handheld_console", "Handheld console", "A game console with grips and a big screen.", FUN),
    ("mini_arcade", "Mini arcade", "A tabletop cabinet with a spinner, buttons and a marquee.", FUN),
    ("metronome", "Metronome", "A pyramid metronome with a dial, a screen and a tap key.", FUN),
    # sensors
    ("weather_station", "Weather station", "A display slab with a louvred sensor hut.", SENSE),
    ("air_monitor", "Air monitor", "A leaning CO2 monitor with a vented sensor chamber.", SENSE),
    ("video_doorbell", "Video doorbell", "A wall slab with a big ring button and a sensor visor.", SENSE),
    ("parking_sensor", "Parking sensor", "A wall traffic light that tells you when to stop.", SENSE),
)
#: Parts and seeds in examples/ that are not products to start from.
NOT_PRODUCTS = ("atech_case", "knob", "gear", "bracket", "enclosure",
                "snap_box", "hinged_box")
#: How many kind chips sit in one row of the gallery's filter (R1030).
CHIPS_PER_ROW = 7
#: How many example cards Home shows before "All examples".
HOME_COUNT = 9


def _request(path):
    import ast
    import re
    try:
        with open(path, encoding="utf-8") as fh:
            doc = ast.get_docstring(ast.parse(fh.read())) or ""
    except (OSError, SyntaxError, ValueError):
        return None
    m = re.match(r'\s*Example:\s*"([^"]+)"', doc)
    return m.group(1) if m else None


def _on_disk(folder=None):
    folder = folder or EXAMPLES_DIR
    try:
        return sorted(n[:-3] for n in os.listdir(folder)
                      if n.endswith(".py") and n[:-3] not in NOT_PRODUCTS)
    except OSError:
        return []


def picture(key):
    p = os.path.join(PICTURES, key + ".png")
    return p if os.path.isfile(p) else None


def entries(shipped=None, folder=None):
    """The gallery's rows: dicts with key, title, line, category, picture
    (a path or None), shipped (the default project's title when this
    installation ships it, else None). `shipped`: {example key: title}
    (default: default_projects' product entries)."""
    if shipped is None:
        shipped = {}
        try:
            from . import default_projects
            for title, key, _sub in default_projects.entries():
                if key:
                    shipped[key] = title
        except Exception:                              # noqa: BLE001
            pass
    disk = set(_on_disk(folder))
    out, seen = [], set()
    for key, title, line, cat in CATALOG:
        if key not in disk and key not in shipped:
            continue
        seen.add(key)
        out.append({"key": key, "title": shipped.get(key) or title, "line": line,
                    "category": cat, "picture": picture(key),
                    "shipped": shipped.get(key), "new": key in NEW_KEYS})
    for key in sorted(disk - seen):
        req = _request(os.path.join(folder or EXAMPLES_DIR, key + ".py"))
        if not req:
            continue
        out.append({"key": key, "title": key.replace("_", " ").capitalize(),
                    "line": req[:1].upper() + req[1:] + ".", "category": MORE,
                    "picture": picture(key), "shipped": shipped.get(key),
                    "new": False})
    return out


def matches(row, text="", category=None):
    """True when the row is in `category` (None: all) and every word of
    `text` is in its title, line or category. NEW: the newest examples
    (row["new"]), whatever their kind."""
    if category == NEW:
        if not row.get("new"):
            return False
    elif category and row["category"] != category:
        return False
    hay = " ".join((row["title"], row["line"], row["category"], row["key"],
                    NEW if row.get("new") else "")).casefold()
    return all(w in hay for w in (text or "").casefold().split())


def start(row):
    """Start a NEW project from the row's example."""
    from . import shell
    if row.get("shipped"):
        return shell.open_default(row["shipped"])
    return shell.open_example(row["key"])


# ------------------------------------------------------------------ window
def _qt():
    from PySide6 import QtCore, QtGui, QtWidgets
    return QtCore, QtGui, QtWidgets


GALLERY_QSS = """
QDialog#ExamplesGallery {{ background: {base}; }}
QLabel#GalleryTitle {{ color: {text}; font-size: 22px; font-weight: 600; }}
QLabel#GalleryCount {{ color: {muted}; font-size: 13px; }}
QLineEdit#GallerySearch {{ background: {input_bg}; color: {text};
    border: 1px solid {input_border}; border-radius: 8px; padding: 6px 10px; }}
QPushButton#GalleryChip {{ background: transparent; color: {muted};
    border: 1px solid {line}; border-radius: 13px; padding: 4px 12px; }}
QPushButton#GalleryChip:hover {{ color: {text}; border-color: {line_strong}; }}
QPushButton#GalleryChip:checked {{ background: {accent}; color: {base};
    border-color: {accent}; }}
QFrame#GalleryCard {{ background: {card}; border: 1px solid {line};
    border-radius: 12px; }}
QFrame#GalleryCard:hover {{ border-color: {accent}; }}
QFrame#GalleryCard:focus {{ border-color: {accent}; }}
QLabel#GalleryCardTitle {{ color: {text}; font-size: 14px; font-weight: 600; }}
QLabel#GalleryCardLine {{ color: {muted}; font-size: 12px; }}
QLabel#GalleryCardTag {{ color: {accent}; font-size: 11px; }}
QLabel#GalleryEmpty {{ color: {muted}; font-size: 13px; }}
"""


def _card_class():
    QtCore, QtGui, QtWidgets = _qt()

    class GalleryCard(QtWidgets.QFrame):
        clicked = QtCore.Signal()
        W, H, PIC = 204, 264, 176

        def __init__(self, row, parent=None):
            super().__init__(parent)
            self.row = row
            self.setObjectName("GalleryCard")
            self.setCursor(QtCore.Qt.PointingHandCursor)
            self.setFocusPolicy(QtCore.Qt.StrongFocus)
            self.setFixedSize(self.W, self.H)
            self.setAccessibleName("Start from the %s example" % row["title"].lower())
            self.setAccessibleDescription(row["line"])
            lay = QtWidgets.QVBoxLayout(self)
            lay.setContentsMargins(12, 12, 12, 12)
            lay.setSpacing(4)
            self.pic = QtWidgets.QLabel()
            self.pic.setFixedSize(self.PIC + 8, self.PIC - 24)
            self.pic.setAlignment(QtCore.Qt.AlignCenter)
            self._pixmap = None
            lay.addWidget(self.pic, 0, QtCore.Qt.AlignHCenter)
            kind = row["category"].upper()
            tag = QtWidgets.QLabel(("NEW  \u00b7  " + kind) if row.get("new") else kind)
            tag.setObjectName("GalleryCardTag")
            lay.addWidget(tag)
            t = QtWidgets.QLabel(row["title"])
            t.setObjectName("GalleryCardTitle")
            lay.addWidget(t)
            s = QtWidgets.QLabel(row["line"])
            s.setObjectName("GalleryCardLine")
            s.setWordWrap(True)
            lay.addWidget(s)
            lay.addStretch(1)

        def load_picture(self):
            if self._pixmap is not None:
                return
            pm = QtGui.QPixmap()
            data = None
            if self.row.get("shipped"):
                try:
                    from . import default_projects
                    data = default_projects.thumbnail(self.row["shipped"])
                except Exception:                      # noqa: BLE001
                    data = None
            if data:
                pm.loadFromData(data)
            elif self.row.get("picture"):
                pm.load(self.row["picture"])
            if pm.isNull():
                self.pic.setText(self.row["title"][:1])
                self._pixmap = False
                return
            self._pixmap = pm.scaled(self.pic.size(), QtCore.Qt.KeepAspectRatio,
                                     QtCore.Qt.SmoothTransformation)
            self.pic.setPixmap(self._pixmap)

        def mouseReleaseEvent(self, ev):               # noqa: N802
            if ev.button() == QtCore.Qt.LeftButton and self.rect().contains(
                    ev.position().toPoint()):
                self.clicked.emit()
            super().mouseReleaseEvent(ev)

        def keyPressEvent(self, ev):                   # noqa: N802
            if ev.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter,
                            QtCore.Qt.Key_Space):
                self.clicked.emit()
                return
            super().keyPressEvent(ev)

    return GalleryCard


_CARD = None


def ExamplesDialog(parent=None, rows=None, on_start=None):   # noqa: N802
    """The gallery window. `on_start(row)` (default start()) runs after
    the window closes, so the new project opens behind no dialog."""
    global _CARD
    QtCore, QtGui, QtWidgets = _qt()
    from . import style
    if _CARD is None:
        _CARD = _card_class()

    class _Dialog(QtWidgets.QDialog):
        COLS_MIN, GAP = 2, 14

        def __init__(self):
            super().__init__(parent)
            self.setObjectName("ExamplesGallery")
            self.setWindowTitle("Examples")
            self.setAccessibleName("Examples")
            self.resize(1040, 760)
            self.rows = entries() if rows is None else rows
            self.chosen = None
            self.category = None
            v = QtWidgets.QVBoxLayout(self)
            v.setContentsMargins(28, 24, 28, 20)
            v.setSpacing(12)
            head = QtWidgets.QHBoxLayout()
            col = QtWidgets.QVBoxLayout()
            col.setSpacing(2)
            t = QtWidgets.QLabel("Start from an example")
            t.setObjectName("GalleryTitle")
            col.addWidget(t)
            self.count = QtWidgets.QLabel()
            self.count.setObjectName("GalleryCount")
            col.addWidget(self.count)
            head.addLayout(col)
            head.addStretch(1)
            self.search = QtWidgets.QLineEdit()
            self.search.setObjectName("GallerySearch")
            self.search.setPlaceholderText("Search examples")
            self.search.setAccessibleName("Search examples")
            self.search.setClearButtonEnabled(True)
            self.search.setFixedWidth(260)
            self.search.textChanged.connect(self.refilter)
            head.addWidget(self.search)
            v.addLayout(head)
            # R1030: 13 kinds do not fit one row - the chips keep their full
            # width and wrap into rows of CHIPS_PER_ROW
            chips = QtWidgets.QVBoxLayout()
            chips.setSpacing(6)
            row = None
            self.chips = []
            present = [c for c in CATEGORIES if any(matches(r, category=c) for r in self.rows)]
            for cat in [None] + present:
                # "&" would be read as a shortcut marker
                b = QtWidgets.QPushButton("All" if cat is None else cat.replace("&", "&&"))
                b.setObjectName("GalleryChip")
                b.setCheckable(True)
                b.setChecked(cat is None)
                b.setCursor(QtCore.Qt.PointingHandCursor)
                b.category = cat
                b.clicked.connect(lambda _=False, c=cat: self.set_category(c))
                b.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                if row is None or row.count() >= CHIPS_PER_ROW:
                    if row is not None:
                        row.addStretch(1)
                    row = QtWidgets.QHBoxLayout()
                    row.setSpacing(6)
                    chips.addLayout(row)
                row.addWidget(b)
                self.chips.append(b)
            if row is not None:
                row.addStretch(1)
            v.addLayout(chips)
            self.scroll = QtWidgets.QScrollArea()
            self.scroll.setWidgetResizable(True)
            self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
            self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            inner = QtWidgets.QWidget()
            self.grid = QtWidgets.QGridLayout(inner)
            self.grid.setSpacing(self.GAP)
            self.grid.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
            self.scroll.setWidget(inner)
            v.addWidget(self.scroll, 1)
            self.empty = QtWidgets.QLabel()
            self.empty.setObjectName("GalleryEmpty")
            self.empty.hide()
            v.addWidget(self.empty)
            self.cards = []
            for r in self.rows:
                c = _CARD(r)
                c.clicked.connect(lambda _=False, row=r: self.choose(row))
                self.cards.append(c)
            self._cols = None
            self.setStyleSheet(style.qss(GALLERY_QSS))
            self.refilter()

        def columns(self):
            avail = self.scroll.viewport().width() or (self.width() - 56)
            return max(self.COLS_MIN, (avail + self.GAP) // (_CARD.W + self.GAP))

        def shown(self):
            return [c for c in self.cards
                    if matches(c.row, self.search.text(), self.category)]

        def refilter(self, *_):
            for c in self.cards:
                self.grid.removeWidget(c)
                c.hide()
            shown = self.shown()
            cols = self.columns()
            self._cols = cols
            for i, c in enumerate(shown):
                self.grid.addWidget(c, i // cols, i % cols)
                c.show()
                c.load_picture()
            n = len(self.rows)
            self.count.setText("%d example%s, each a complete product with the "
                               "Atech board inside. Pick one to start a new "
                               "project from it." % (n, "" if n == 1 else "s"))
            q = self.search.text().strip()
            self.empty.setText("No example matches “%s”." % q if q else
                               "No example here yet.")
            self.empty.setVisible(not shown)

        def set_category(self, cat):
            self.category = cat
            for b in self.chips:
                b.setChecked(b.category == cat)
            self.refilter()

        def resizeEvent(self, ev):                     # noqa: N802
            super().resizeEvent(ev)
            if self.columns() != self._cols:
                self.refilter()

        def choose(self, row):
            self.chosen = row
            self.accept()

    dlg = _Dialog()
    dlg._on_start = on_start or start
    return dlg


def show_gallery(parent=None):
    """Open the gallery; start the chosen example after it closes. Returns
    the chosen row or None."""
    dlg = ExamplesDialog(parent)
    dlg.exec()
    row = dlg.chosen
    if row is not None:
        dlg._on_start(row)
    return row
