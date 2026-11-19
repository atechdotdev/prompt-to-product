"""R962: the Wiring view of the Atech modules page (acadagent/wiring_view.py)
and its export, offscreen with PySide6 only (no FreeCAD):

    QT_QPA_PLATFORM=offscreen ATECH_SDK_CATALOG=snapshot <python with PySide6> \
        -m unittest -v test_wiring_view_r962

The documents are fakes carrying the Atech properties atech_ports writes.
"""
import os
import re
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("ATECH_SDK_CATALOG", "snapshot")
HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
KIT = os.path.join(ADDON, "acadagent", "agent_kit")
for p in (ADDON, KIT):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from PySide6 import QtCore, QtGui, QtSvg, QtWidgets
    _APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    from acadagent import modules_page as mp
    from acadagent import wiring_view as wv
except ImportError:                                    # no Qt here
    wv = None

import atech_wiring as aw                              # noqa: E402


class _Pl(object):
    def __init__(self, v=0):
        self.v = v

    def isSame(self, other, tol=0):                    # noqa: N802
        return isinstance(other, _Pl) and abs(self.v - other.v) <= tol


class _O(object):
    def __init__(self, name, **kw):
        self.Name = name
        self.Label = kw.pop("Label", name)
        self.Placement = kw.pop("Placement", _Pl())
        for k, v in kw.items():
            setattr(self, k, v)


class _Doc(object):
    Name = "Dock"
    Label = "Arm dock"
    FileName = ""

    def __init__(self, objs):
        self.Objects = objs


def arm_doc(moved=False):
    board = _O("Board", AtechRole="board")
    mods = [
        _O("usbc_p7", AtechRole="module", AtechModule="usbc", AtechPorts=[7]),
        _O("robot_arm_p3", AtechRole="module", AtechModule="robot_arm", AtechPorts=[3]),
        _O("button_p1", AtechRole="module", AtechModule="button", AtechPorts=[1]),
        _O("tof_p9", AtechRole="module", AtechModule="distance_sensor", AtechPorts=[9],
           AtechJoint="cable", Placement=_Pl(1)),
    ]
    cable = _O("tof_cable_p9", AtechCableModule="tof_p9", AtechCablePort=9,
               AtechCableLength=82.4, AtechCableBoardAt=_Pl(0),
               AtechCableModuleAt=_Pl(2 if moved else 1))
    return _Doc([board] + mods + [cable])


def wiring(doc=None, **kw):
    doc = doc or arm_doc()
    kw.setdefault("names", {"usbc": "USB-C", "robot_arm": "Robot arm", "button": "Button",
                            "distance_sensor": "Distance sensor"})
    return aw.build(aw.modules_from_doc(doc), project=doc.Label, made="2026-11-16 03:00", **kw)


@unittest.skipIf(wv is None, "PySide6 not installed")
class TestExport(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="wiring-r962-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_pdf_one_page(self):
        p = wv.export_wiring(wiring(), os.path.join(self.tmp, "Arm dock wiring.pdf"))
        with open(p, "rb") as fh:
            data = fh.read()
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertEqual(len(re.findall(rb"/Type\s*/Page\b", data)), 1)

    def test_png_size_and_colour(self):
        p = wv.export_wiring(wiring(), os.path.join(self.tmp, "w.png"))
        img = QtGui.QImage(p)
        self.assertEqual(img.width(), wv.PNG_WIDTH)
        self.assertGreater(img.height(), 1000)
        small = img.scaled(60, 40)
        colours = {small.pixel(x, y) for x in range(60) for y in range(40)}
        self.assertGreater(len(colours), 1)

    def test_svg_parses(self):
        p = wv.export_wiring(wiring(), os.path.join(self.tmp, "w.svg"))
        with open(p, encoding="utf-8") as fh:
            ET.fromstring(fh.read())

    def test_unknown_suffix(self):
        with self.assertRaises(ValueError):
            wv.export_wiring(wiring(), os.path.join(self.tmp, "w.doc"))

    def test_both_layouts_render(self):
        w = wiring()
        for layout in ("panel", "sheet"):
            r = QtSvg.QSvgRenderer(QtCore.QByteArray(aw.svg(w, layout).encode()))
            self.assertTrue(r.isValid(), layout)


@unittest.skipIf(wv is None, "PySide6 not installed")
class TestPanel(unittest.TestCase):

    def test_empty_state(self):
        panel = wv.WiringPanel()
        panel.set_wiring(aw.build(None, firmware_on=False))
        self.assertTrue(panel.empty.isVisibleTo(panel))
        self.assertEqual(panel.empty.text(), aw.EMPTY)
        self.assertFalse(panel.btn_export.isEnabled())
        for h, b in panel.sections.values():
            self.assertFalse(b.isVisibleTo(panel))

    def test_sections_and_accessible_description(self):
        w = wiring()
        panel = wv.WiringPanel()
        panel.set_wiring(w)
        self.assertFalse(panel.empty.isVisibleTo(panel))
        self.assertEqual(panel.view.accessibleName(), "Wiring diagram")
        self.assertEqual(panel.view.accessibleDescription(), "\n".join(aw.lines(w)))
        conn = panel.sections["connections"][1].text()
        self.assertIn("Port 9: Distance sensor", conn)
        self.assertIn("cable 82 mm", conn)
        self.assertIn("USB-C on port 7", panel.sections["power"][1].text())
        self.assertIn("damages the servos", panel.sections["cautions"][1].text())
        self.assertIn(aw.PINOUT_ASK, panel.sections["unknown"][1].text())
        self.assertTrue(panel.btn_export.isEnabled())

    def test_stale_cable_words(self):
        panel = wv.WiringPanel()
        panel.set_wiring(wiring(arm_doc(moved=True)))
        self.assertIn("make it again", panel.sections["connections"][1].text())

    def test_firmware_off_hides_code_names(self):
        on = wv.WiringPanel()
        on.set_wiring(wiring(firmware_on=True))
        self.assertIn("name in code", on.sections["connections"][1].text())
        off = wv.WiringPanel()
        off.set_wiring(wiring(firmware_on=False))
        self.assertNotIn("name in code", off.sections["connections"][1].text())
        self.assertNotIn("name in code", off.view.accessibleDescription())

    def test_view_keeps_aspect(self):
        panel = wv.WiringPanel()
        panel.set_wiring(wiring())
        for width in (380, 300):
            panel.resize(width, 1200)
            panel.view.resize(width, 10)
            panel.view._fit_height(width)
            s = panel.view.renderer().defaultSize()
            self.assertAlmostEqual(panel.view.height(), width * s.height() / s.width(), delta=1)

    def test_default_path(self):
        panel = wv.WiringPanel()
        panel.set_wiring(wiring(), folder=None)
        self.assertEqual(os.path.basename(panel.default_path()), "Arm dock wiring.pdf")


@unittest.skipIf(wv is None, "PySide6 not installed")
class TestModulesPage(unittest.TestCase):

    def test_cells_match_board_map(self):
        self.assertEqual(aw.PORT_CELLS, mp.CELLS)
        self.assertEqual(aw.CELL_MM, mp.CELL_MM)

    def test_button_and_stack(self):
        page = mp.ModulesPage()
        self.assertEqual(page.btn_wiring.text(), "Wiring")
        self.assertTrue(page.btn_wiring.isCheckable())
        self.assertEqual(page.btn_wiring.accessibleName(),
                         "Wiring diagram: which port each module uses")
        board_map = page.map
        self.assertIs(page.map_stack.currentWidget(), board_map)
        self.assertIsNone(page.wiring_panel)           # built on first use
        page.btn_wiring.setChecked(True)
        self.assertIsNotNone(page.wiring_panel)
        self.assertIs(page.map_stack.currentWidget(), page.wiring_panel)
        page.btn_wiring.setChecked(False)
        self.assertIs(page.map_stack.currentWidget(), board_map)
        self.assertIs(page.map, board_map)
        self.assertTrue(page.show_wiring())
        self.assertIs(page.map_stack.currentWidget(), page.wiring_panel)

    def test_sync_rebuilds_only_on_change(self):
        page = mp.ModulesPage()
        page.btn_wiring.setChecked(True)
        doc = arm_doc()
        page._sync_wiring(doc)
        first = page.wiring_panel.w
        self.assertEqual(len(first["connections"]), 4)
        page._sync_wiring(doc)
        self.assertIs(page.wiring_panel.w, first)        # unchanged: not rebuilt
        doc.Objects = doc.Objects[:2]
        page._sync_wiring(doc)
        self.assertEqual(len(page.wiring_panel.w["connections"]), 1)


@unittest.skipIf(wv is None, "PySide6 not installed")
class TestHonestWords(unittest.TestCase):
    """No pin, wire colour, current or 'tested' claim in this file's words."""

    PATTERNS = [r"(?i)\bpin\s*\d+", r"(?i)pinout(?! on request)", r"(?i)pin map",
                r"\bLine [AB]\d?\b", r"\bVCC\b", r"\b\d+(\.\d+)?\s*m?A\b",
                r"(?i)\b(red|black|brown|orange|yellow|white)\s+wire",
                r"(?i)\b(tested|verified|safe)\b"]

    def test_view_strings(self):
        with open(wv.__file__, encoding="utf-8") as fh:
            src = fh.read()
        strings = re.findall(r'"([^"\n]*)"', src)
        for s in strings:
            for pat in self.PATTERNS:
                self.assertIsNone(re.search(pat, s), (pat, s))


if __name__ == "__main__":
    unittest.main()
