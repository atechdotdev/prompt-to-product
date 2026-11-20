"""R860 Home's account button: "Sign in", "Waiting for the browser...", or
the signed-in name with its menu (account.py does the work)."""
import threading

from PySide6 import QtCore, QtGui, QtWidgets

from . import account, shop


class _Relay(QtCore.QObject):
    done = QtCore.Signal(object)
    changed = QtCore.Signal()


class AccountButton(QtWidgets.QPushButton):
    """Signed out: Sign in (opens atech.dev/connect/atelier). Waiting: a
    menu to open the page again, paste the code, or cancel. Signed in: the
    name, with the email, the account page and Sign out."""

    def __init__(self, parent=None, acct=None, opener=None, background=True):
        super().__init__(parent)
        self.setObjectName("HomeBtn")
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.acct = acct or account.get()
        self.opener = opener or shop.open_url
        self.background = background
        self.flow = None
        self.last_message = ""
        self._relay = _Relay(self)
        self._relay.done.connect(self._finished)
        self._relay.changed.connect(self.sync)
        self.clicked.connect(self._click)
        self.sync()
        if self.acct.signed_in():
            # check the session is still good, and pick up a new name
            self._bg(lambda: (self.acct.refresh_profile(), self._emit_changed()))

    def _bg(self, fn):
        if self.background:
            threading.Thread(target=fn, daemon=True).start()
        else:
            fn()

    def _emit_changed(self):
        try:
            self._relay.changed.emit()
        except RuntimeError:                              # the window closed first
            pass

    # -- state -------------------------------------------------------- #
    def sync(self):
        if self.flow is not None:
            self.setText("Waiting for the browser…")
            self.setAccessibleName("Signing in: waiting for the browser")
            self.setToolTip("Connect Prompt2Product on the atech.dev page that opened. "
                            "Click for more.")
        elif self.acct.signed_in():
            u = self.acct.user
            other = account.other_site()        # $ATECH_SITE, e.g. staging
            self.setText(self.acct.label() + (" · %s" % other if other else ""))
            self.setAccessibleName("Signed in as %s" % u.get("email", ""))
            self.setToolTip("Signed in to %s as %s" % (other or "Atech", u.get("email", "")))
        else:
            self.setText("Sign in")
            self.setAccessibleName("Sign in with your Atech account")
            self.setToolTip("Sign in with your atech.dev account, the one your Atech board "
                            "and projects are on. Opens atech.dev in your browser.")

    def _click(self):
        if self.flow is None and not self.acct.signed_in():
            return self.sign_in()
        self.menu().popup(self.mapToGlobal(QtCore.QPoint(0, self.height())))

    def menu(self):
        m = QtWidgets.QMenu(self)
        if self.flow is not None:
            m.addAction("Open the page again", lambda: self.opener(self.flow.url))
            m.addAction("Copy the link", lambda: QtGui.QGuiApplication.clipboard().setText(
                self.flow.url))
            m.addAction("Paste a code…", self.paste_code)
            m.addSeparator()
            m.addAction("Cancel", self.cancel)
        else:
            u = self.acct.user or {}
            who = m.addAction(u.get("email", ""))
            who.setEnabled(False)
            m.addAction("Your account on atech.dev", lambda: self.opener(shop.SITE + "/account"))
            m.addAction("Builds on atech.dev", lambda: self.opener(shop.SITE + "/community"))
            m.addAction("Atech shop", lambda: self.opener(shop.SHOP))
            m.addAction("Docs on atech.dev", lambda: self.opener(shop.SITE + "/docs"))
            m.addAction("About Prompt2Product", lambda: self.opener(shop.SITE + "/atelier"))
            m.addSeparator()
            m.addAction("Sign out", self.sign_out)
        self._menu = m
        return m

    # -- actions ------------------------------------------------------ #
    def sign_in(self):
        self.last_message = ""
        self.flow = account.SignIn(self.acct, opener=self.opener, done=self._emit_done)
        self.sync()
        self.flow.start()
        return self.flow

    def _emit_done(self, result):
        try:
            self._relay.done.emit(result)
        except RuntimeError:
            pass

    def _finished(self, result):
        self.flow = None
        self.last_message = result.get("message", "")
        self.sync()
        if not result.get("ok") and self.last_message and not result.get("cancelled"):
            QtWidgets.QToolTip.showText(self.mapToGlobal(QtCore.QPoint(0, self.height())),
                                        self.last_message, self)

    def paste_code(self, code=None):
        if self.flow is None:
            return None
        if code is None:
            code, ok = QtWidgets.QInputDialog.getText(
                self, "Paste the code", "The code from the atech.dev page:")
            if not ok or not code.strip():
                return None
        flow = self.flow
        self._bg(lambda: flow.submit_code(code))
        return True

    def cancel(self):
        if self.flow is not None:
            self.flow.cancel()

    def sign_out(self):
        self._bg(lambda: (self.acct.sign_out(), self._emit_changed()))


#: R1020: the project sidebar's atech.dev menu, (key, label, path on the site)
HUB_SITE = (("account", "Your account", "/account"),
            ("community", "Builds by the community", "/community"),
            ("shop", "Atech shop: board and modules", None),
            ("docs", "Docs", "/docs"),
            ("app", "What's new in Prompt2Product", "/atelier"))


def _initials(name):
    parts = [p for p in str(name or "").replace("@", " ").split() if p[:1].isalnum()]
    return "".join(p[0] for p in parts[:2]).upper() or "?"


class AtechHub(AccountButton):
    """R1020: everything that goes to atech.dev, in one place on the project
    sidebar: who is signed in (or Sign in), this project's Get it made by
    Atech and Post to atech.dev, then the site's pages. A click always opens
    the menu; signed out, its first row signs in.

    project_actions: [(key, label, fn)] for "This project"; enabled() says
    whether a project is open (no project: they are greyed)."""

    def __init__(self, parent=None, acct=None, opener=None, background=True,
                 project_actions=(), enabled=None):
        self.project_actions = list(project_actions)
        self.enabled = enabled or (lambda: True)
        super().__init__(parent, acct=acct, opener=opener, background=background)
        self.setObjectName("AtechHub")
        self.setAccessibleDescription("atech.dev: your account, Get it made, Post, the shop")

    def sync(self):
        super().sync()
        avatar = self.flow is None and self.acct.signed_in()
        if avatar:
            # a round avatar with the initials, as on a website; the name,
            # the email and the site are in the tooltip and the menu
            u = self.acct.user or {}
            self.setText(_initials(u.get("name") or u.get("email")))
            self.setFixedSize(30, 30)
        else:
            self.setMinimumSize(0, 0)
            self.setMaximumSize(16777215, 16777215)
            if self.flow is not None:
                self.setText("Signing in…")
        if self.property("avatar") != avatar:
            self.setProperty("avatar", avatar)
            self.style().unpolish(self)
            self.style().polish(self)
        self.setToolTip(self.toolTip() + "\nClick for Get it made, Post to atech.dev "
                        "and the Atech shop.")

    def _click(self):
        self.menu().popup(self.mapToGlobal(QtCore.QPoint(0, self.height())))

    def menu(self):
        if self.flow is not None:
            return super().menu()
        m = QtWidgets.QMenu(self)
        m.setAccessibleName("atech.dev")
        signed = self.acct.signed_in()
        if signed:
            u = self.acct.user or {}
            other = account.other_site()
            who = m.addAction("%s · %s%s" % (u.get("name") or self.acct.label(), u.get("email", ""),
                                             " (%s)" % other if other else ""))
            who.setEnabled(False)
        else:
            m.addAction("Sign in with your atech.dev account…", self.sign_in)
        m.addSection("This project")
        on = bool(self.enabled())
        for key, label, fn in self.project_actions:
            a = m.addAction(label, fn)
            a.setObjectName("hub_" + key)
            a.setEnabled(on)
        m.addSection("atech.dev")
        for key, label, path in HUB_SITE:
            if key == "account" and not signed:
                continue
            url = shop.SHOP if path is None else shop.SITE + path
            m.addAction(label, lambda u=url: self.opener(u))
        if signed:
            m.addSeparator()
            m.addAction("Sign out", self.sign_out)
        self._menu = m
        return m
