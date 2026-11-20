"""R1010: the getting started tour, and Home's "How it works" strip.

    R1010a  the tour: your idea, electronics, CAD, firmware, make it; the
            firmware step says Atech Studio or `pip install atech` handles it
    R1010b  first run: shown once (settings), never offscreen / ATECH_ONBOARDING=0
    R1010c  the dialog: Next / Back / Done, the last step starts a product
    R1010d  Home's strip: one card per part, each opens the tour at its step
    R1010e  the chat's no-document Welcome offers "How it works"

    QT_QPA_PLATFORM=offscreen <bundled python> -m unittest -v test_onboarding_r1010

Every gate has a sabotage test that must see it fail.
"""
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
sys.path.insert(0, ADDON)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6 import QtWidgets
    _APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    HAVE_QT = True
except Exception:                                      # noqa: BLE001
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class Tour(unittest.TestCase):
    def setUp(self):
        from acadagent import onboarding
        self.ob = onboarding

    # R1010a
    def test_steps_in_order(self):
        self.assertEqual([s["key"] for s in self.ob.steps()],
                         ["describe", "electronics", "cad", "firmware", "make"])
        self.assertEqual([p[0] for p in self.ob.PARTS],
                         ["electronics", "cad", "firmware"])

    def test_firmware_is_handled_by_studio_or_pip(self):
        fw = self.ob.steps()[self.ob.index_of("firmware")]
        text = " ".join([fw["title"], fw["line"]] + fw["points"])
        self.assertIn("pip install atech", text)
        self.assertIn("Atech Studio", text)
        self.assertIn("handled", fw["title"])
        part = dict((k, line) for k, _t, line in self.ob.PARTS)["firmware"]
        self.assertIn("pip install atech", part)

    # R1010b
    def test_first_run_once(self):
        env = {}
        self.assertTrue(self.ob.should_show_first_run({}, env))
        self.assertFalse(self.ob.should_show_first_run(
            {self.ob.SEEN_KEY: self.ob.VERSION}, env))
        # a newer tour is shown again
        self.assertTrue(self.ob.should_show_first_run(
            {self.ob.SEEN_KEY: self.ob.VERSION - 1}, env))

    def test_first_run_never_headless(self):
        self.assertFalse(self.ob.should_show_first_run(
            {}, {"QT_QPA_PLATFORM": "offscreen"}))
        self.assertFalse(self.ob.should_show_first_run({}, {"ATECH_ONBOARDING": "0"}))
        self.assertTrue(self.ob.should_show_first_run(
            {self.ob.SEEN_KEY: 99}, {"ATECH_ONBOARDING": "1"}))

    def test_sabotage_seen_flag_ignored(self):
        with mock.patch.object(self.ob, "seen", return_value=False):
            self.assertTrue(self.ob.should_show_first_run(
                {self.ob.SEEN_KEY: self.ob.VERSION}, {}))

    def test_maybe_show_respects_the_test_run(self):
        with mock.patch.object(self.ob, "open_guide") as og:
            self.assertIsNone(self.ob.maybe_show_first_run())
        og.assert_not_called()

    # R1010c
    def test_dialog_walks_and_starts(self):
        started = []
        with mock.patch.object(self.ob, "mark_seen", return_value=True) as ms:
            d = self.ob.GuideDialog(0, on_start=lambda t: started.append(t) or "DOC")
            try:
                self.assertEqual(d.current(), 0)
                self.assertFalse(d.btn_back.isEnabled())
                for _ in range(4):
                    d.next()
                self.assertEqual(d.current(), 4)
                self.assertEqual(d.btn_next.text(), "Done")
                self.assertFalse(d.btn_go.isEnabled())
                d.prompt.setText("A lamp that wakes me up")
                self.assertTrue(d.btn_go.isEnabled())
                self.assertEqual(d.make_it(), "DOC")
                self.assertEqual(started, ["A lamp that wakes me up"])
                ms.assert_called()
                d.back()
                self.assertEqual(d.current(), 3)
                self.assertEqual(d.go(99), 4)
            finally:
                d.deleteLater()

    def test_open_at_a_step_key(self):
        with mock.patch.object(self.ob, "mark_seen", return_value=True):
            d = self.ob.open_guide("firmware")
            try:
                self.assertEqual(d.current(), 3)
                self.assertIs(self.ob.open_guide("cad"), d)   # one at a time
                self.assertEqual(d.current(), 2)
            finally:
                d.close()

    def test_copy_install_command(self):
        with mock.patch.object(self.ob, "mark_seen", return_value=True):
            d = self.ob.GuideDialog(3)
            try:
                d._copy_install()
                self.assertEqual(QtWidgets.QApplication.clipboard().text(),
                                 "pip install atech")
                self.assertEqual(d.btn_copy.text(), "Copied")
            finally:
                d.deleteLater()


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class HomeStrip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from acadagent import onboarding, shell
        cls.shell, cls.ob = shell, onboarding

    # R1010d
    def test_how_cards_open_the_tour_at_their_step(self):
        home = self.shell.HomeView()
        try:
            self.assertEqual([c.step_key for c in home.how_cards],
                             ["electronics", "cad", "firmware"])
            with mock.patch.object(self.ob, "open_guide") as og:
                home.how_cards[2].clicked.emit()
                home.btn_tour.click()
            self.assertEqual([c.args[0] for c in og.call_args_list], ["firmware", 0])
            home.restyle()                       # icons drawn without error
        finally:
            home.deleteLater()

    def test_settings_menu_has_getting_started(self):
        menu = self.shell.settings_menu()
        self.assertIn("Getting started…", [a.text() for a in menu.actions()])


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class ChatWelcome(unittest.TestCase):
    # R1010e
    def test_nodoc_offers_how_it_works(self):
        from acadagent import panel
        fake = mock.Mock(_crane_available=lambda: False,
                         _on_new_document=1, _on_open_file=2,
                         _on_getting_started=3)
        acts = panel.AgentPanel._nodoc_actions(fake) \
            if hasattr(panel, "AgentPanel") else None
        if acts is None:
            self.skipTest("no AgentPanel class")
        self.assertIn(("How it works", 3), acts)


if __name__ == "__main__":
    unittest.main()
