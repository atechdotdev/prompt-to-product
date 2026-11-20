"""R1190 the papers in the app: the Make it window's "Prompt to product" card
and Test by hand (acadagent/p2p_view.py), and the share pack carrying the
papers (share.P2P_PAPERS).

    cd addon/AcadAgent/tests
    QT_QPA_PLATFORM=offscreen ATECH_SDK_CATALOG=snapshot "<bundle>/Contents/Resources/bin/python" \\
        -m unittest test_p2p_r1190
    ATECH_FREECADCMD=<freecadcmd>     # + the share pack's papers
Offscreen only: nothing is shown on screen.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
for p in (ADDON, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("ATECH_SDK_CATALOG", "snapshot")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6 import QtWidgets
    APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    from acadagent import p2p_view
    HAVE_QT = True
except Exception:                                                 # noqa: BLE001
    HAVE_QT = False

import test_p2p_r1180 as r1180                                    # noqa: E402


@unittest.skipUnless(HAVE_QT, "PySide6 / the add-on's Qt modules are not importable here")
class TestCard(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        from acadagent import product
        self.f = r1180.facts(self.d)
        product.write_pack(self.f, self.d)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_lines(self):
        c = p2p_view.papers_card(self.f)
        self.assertEqual(set(c.lines), {"brief", "print", "cost", "qa", "version"})
        self.assertIn("Not tested by hand yet", c.lines["qa"].text())
        self.assertIn("Version 1.0", c.lines["version"].text())
        self.assertTrue(c.btn_qa.isEnabled())
        self.assertTrue(c.btn_brief.isEnabled())

    def test_open_questions_shown(self):
        c = p2p_view.papers_card(self.f)
        texts = [w.text() for w in c.findChildren(QtWidgets.QLabel)]
        self.assertTrue(any(t.startswith("Still open:") for t in texts), texts)

    def test_qa_dialog_saves_and_updates(self):
        c = p2p_view.papers_card(self.f)
        d = c.open_qa()
        ids = list(d.rows)
        d.set(ids[0], "pass", "clean")
        d.set(ids[1], "fail", "too tight")
        d.save()
        with open(os.path.join(self.d, "qa.json")) as fh:
            rec = json.load(fh)
        self.assertEqual(rec[ids[0]]["result"], "pass")
        self.assertEqual(rec[ids[1]]["note"], "too tight")
        self.assertTrue(c.lines["qa"].text().startswith("Tested: 1 failed"))
        # unset a row: it leaves the record
        d.set(ids[1], "")
        d.save()
        with open(os.path.join(self.d, "qa.json")) as fh:
            self.assertNotIn(ids[1], json.load(fh))
        d.close()

    def test_brief_dialog(self):
        c = p2p_view.papers_card(self.f)
        d = c.open_brief()
        t = d.findChild(QtWidgets.QTextBrowser).toPlainText()
        self.assertIn("Brief: Desk buddy", t)
        self.assertIn("Done when", t)
        d.close()

    def test_no_pack_yet(self):
        d = tempfile.mkdtemp()
        try:
            f = r1180.facts(d)
            f.pop("prompt")
            f["bom"] = {"printed": [], "hardware": []}
            f["parts"] = []
            c = p2p_view.papers_card(f)
            self.assertNotIn("brief", c.lines)
            self.assertFalse(c.btn_brief.isEnabled())
        finally:
            shutil.rmtree(d)

    def test_picture_offscreen(self):
        """A grab of the card for the round's log (offscreen, never shown)."""
        c = p2p_view.papers_card(self.f)
        c.resize(860, 260)
        out = os.environ.get("P2P_SHOTS")
        pm = c.grab()
        self.assertFalse(pm.isNull())
        if out:
            os.makedirs(out, exist_ok=True)
            pm.save(os.path.join(out, "papers_card.png"))


@unittest.skipUnless(HAVE_QT, "Qt not importable")
class TestMakeItHasTheCard(unittest.TestCase):
    def test_source_hook(self):
        with open(os.path.join(ADDON, "acadagent", "product_view.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("p2p_view.papers_card(f, self)", src)


try:
    import test_share_r1040 as share_t
    FC = share_t.FC
except Exception:                                                 # noqa: BLE001
    share_t = FC = None


@unittest.skipIf(FC is None, "freecadcmd not found")
class TestSharePapers(unittest.TestCase):
    def test_share_carries_the_papers(self):
        t = share_t.Pack("test_everything_in_one_folder")
        r, out = t.run_fc()
        files = r["files"]
        for want in ("manual.md", "quick-start.html", "label.svg", "test-plan.md",
                     "print-plan.md", "CHANGELOG.md"):
            self.assertIn(want, files, out[-2000:])


if __name__ == "__main__":
    unittest.main()
