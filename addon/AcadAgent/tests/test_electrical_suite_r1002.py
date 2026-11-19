"""R1002/R1004/R1005: the electrical suite window, Make it and the chat's
hand-over card, offscreen with a duck-typed design (no FreeCAD).

    QT_QPA_PLATFORM=offscreen python -m unittest test_electrical_suite_r1002
"""
import os
import stat
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["ATECH_SDK_CATALOG"] = "snapshot"
os.environ["ATECH_NO_REVEAL"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
if ADDON not in sys.path:
    sys.path.insert(0, ADDON)

try:
    from PySide6 import QtCore, QtWidgets
    APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
except ImportError:                                     # pragma: no cover
    QtWidgets = None


class O(object):
    def __init__(self, name, **kw):
        self.Name = self.Label = name
        for k, v in kw.items():
            setattr(self, k, v)


class Doc(object):
    Name = "Desk_buddy"
    Label = "Desk buddy"
    FileName = ""

    def __init__(self, mods=None):
        self.Objects = [O("board", AtechRole="board")] + [
            O("%s_%d" % (m, i), AtechRole="module", AtechModule=m, AtechPorts=list(p))
            for i, (m, p) in enumerate(mods if mods is not None else [("usbc", [8]), ("button", [1]),
                                                ("light", [3]), ("screen", [9, 10]),
                                                ("temp_humidity", [5])])]


FAKE = """#!/bin/sh
echo "fake atech $*"
[ "$1" = emulate ] && echo "boot report: POWERON; btn ok, led ok"
exit 0
"""


@unittest.skipIf(QtWidgets is None, "PySide6 not installed")
class Suite(unittest.TestCase):
    def setUp(self):
        from acadagent import sdk_tools, electrical_suite
        self.tmp = tempfile.TemporaryDirectory()
        self.old = sdk_tools.PRODUCTS_DIR
        sdk_tools.PRODUCTS_DIR = self.tmp.name
        self.ES = electrical_suite
        self.w = electrical_suite.ElectricalSuite(Doc())

    def tearDown(self):
        from acadagent import sdk_tools
        sdk_tools.PRODUCTS_DIR = self.old
        self.w.close()
        self.w.deleteLater()
        self.tmp.cleanup()

    def test_pages_and_verdict(self):
        self.assertEqual(self.w.nav.count(), len(self.ES.PAGES))
        for key, _w, _i in self.ES.PAGES:
            self.assertTrue(self.w.show_page(key))
            self.assertEqual(self.w.current_page(), key)
        self.assertEqual(self.w.r["verdict"]["level"], "ok")
        self.assertEqual(self.w.pill.text(), "Ready to wire")
        self.assertIn("Desk buddy", self.w.windowTitle())

    def test_power_inputs_saved_in_product_folder(self):
        self.w.show_page("power")
        tbl = self.w.loads_table
        row = [i for i in range(tbl.rowCount())
               if tbl.item(i, 2).data(QtCore.Qt.UserRole) == "light"][0]
        tbl.item(row, 2).setText("42")
        APP.processEvents()
        QtCore.QCoreApplication.processEvents()
        QtCore.QTimer.singleShot(0, lambda: None)
        APP.processEvents()
        inp = self.w.inputs()
        self.assertEqual(inp["loads"], {"light": 42.0})
        self.assertIn("light", {r["key"]: r for r in self.w.r["budget"]["rows"]})
        light = [r for r in self.w.r["budget"]["rows"] if r["key"] == "light"][0]
        self.assertEqual(light["ma"], 42.0)
        self.assertEqual(light["source"], "you")
        self.w._power_changed(supply="usb2")
        APP.processEvents()
        self.assertEqual(self.w.r["budget"]["supply"], "usb2")

    def test_firmware_without_sdk(self):
        self.w.sdk = None
        self.w.refresh()
        self.assertFalse(self.w.cmd_buttons["build"].isEnabled())
        self.assertFalse(self.w.run("build"))

    def test_firmware_run_with_fake_sdk(self):
        exe = os.path.join(self.tmp.name, "atech")
        with open(exe, "w") as fh:
            fh.write(FAKE)
        os.chmod(exe, os.stat(exe).st_mode | stat.S_IEXEC)
        self.w.sdk = exe
        self.w.refresh()
        self.assertTrue(self.w.cmd_buttons["emulate"].isEnabled())
        done = []
        loop = QtCore.QEventLoop()
        self.assertTrue(self.w.run("emulate"))
        self.w.runner.finished.connect(lambda *a: (done.append(a), loop.quit()))
        QtCore.QTimer.singleShot(5000, loop.quit)
        if not done:
            loop.exec()
        self.assertEqual(done[0][1], 0)
        self.assertIn("POWERON; btn ok, led ok", self.w.run_status.text())
        fw = os.path.join(self.w.folder(), "firmware", "project.yaml")
        self.assertTrue(os.path.isfile(fw))
        from acadagent import product
        self.assertIn("emulated", product.read_state(self.w.folder()))

    def test_bringup_ticks(self):
        self.w._tick("Plug USB-C into the computer.", True)
        from acadagent import product
        st = product.read_state(self.w.folder())
        self.assertEqual(st["bringup"]["done"], ["Plug USB-C into the computer."])

    def test_exports(self):
        r = self.w.r
        pdf = os.path.join(self.tmp.name, "r.pdf")
        self.ES.report_pdf(r, pdf)
        self.assertGreater(os.path.getsize(pdf), 2000)
        for ext in (".svg", ".png", ".pdf"):
            p = os.path.join(self.tmp.name, "s" + ext)
            self.ES.export_svg(self.ES.E().schematic_svg(r), p)
            self.assertTrue(os.path.getsize(p) > 100, ext)
        p = self.w.save_to(os.path.join(self.tmp.name, "c.csv"),
                           lambda rr, path: self.w._write(path, self.ES.E().connections_csv(rr)))
        self.assertTrue(os.path.isfile(p))

    def test_empty_design(self):
        w = self.ES.ElectricalSuite(Doc(mods=[]))
        self.assertEqual(w.r["verdict"]["level"], "empty")
        self.assertEqual(w.pill.text(), "No electronics")
        w.close()

    def test_open_suite_reuses_window(self):
        a = self.ES.open_suite(Doc(), "ports", parent=None)
        b = self.ES.open_suite(Doc(), "power", parent=None)
        self.assertIs(a, b)
        self.assertEqual(b.current_page(), "power")
        a.close()


@unittest.skipIf(QtWidgets is None, "PySide6 not installed")
class MakeIt(unittest.TestCase):
    def setUp(self):
        from acadagent import sdk_tools, product_view, export_tools
        self.tmp = tempfile.TemporaryDirectory()
        self.old = (sdk_tools.PRODUCTS_DIR, export_tools.bom, product_view.built)
        sdk_tools.PRODUCTS_DIR = self.tmp.name
        export_tools.bom = lambda doc, *a, **k: {
            "printed": [{"part": "Body", "count": 1, "names": ["Body"], "volume_cm3": 40,
                         "mass_g": 49.6, "colour": "orange"}],
            "hardware": [{"kind": "Board", "name": "Atech board", "ports": "",
                          "length_mm": None, "label": "b"}]}
        product_view.built = lambda doc: True
        self.PV = product_view

    def tearDown(self):
        from acadagent import sdk_tools, export_tools
        sdk_tools.PRODUCTS_DIR, export_tools.bom, self.PV.built = self.old
        self.tmp.cleanup()

    def test_steps_and_pack(self):
        w = self.PV.MakeIt(Doc())
        self.assertEqual(len(w.rows), 7)
        self.assertIn("steps done", w.sub.text())
        files = w.make_pack()
        names = [a for a, _b in files]
        self.assertIn("product.html", names)
        self.assertIn("electrical/electrical-report.pdf", names)
        self.assertIn("electrical/wiring.pdf", names)
        self.assertTrue(os.path.isfile(os.path.join(w.f["folder"], "README.md")))
        self.assertIn("Product pack", w.note.text())
        w.close()

    def test_assembly_dialog(self):
        w = self.PV.MakeIt(Doc())
        d = w.act("assembly")
        self.assertIn("Plug in the modules", d.browser.toPlainText())
        d.close()
        w.close()

    def test_suite_action(self):
        w = self.PV.MakeIt(Doc())
        s = w.act("electrical")
        self.assertEqual(s.current_page(), "overview")
        s.close()
        w.close()


@unittest.skipIf(QtWidgets is None, "PySide6 not installed")
class Commands(unittest.TestCase):
    def test_menu_entries(self):
        from acadagent import shell
        keys = {c[3] for c in shell.EXPORT_COMMANDS}
        self.assertTrue({"makeit", "electrical"} <= keys)

    def test_panel_card_text(self):
        from acadagent import panel
        self.assertIn("%s", panel.AgentPanel.MAKE_IT_BODY)
        self.assertEqual(panel.AgentPanel.MAKE_IT_TITLE, "Ready to make it")


if __name__ == "__main__":
    unittest.main()
