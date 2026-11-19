"""The Atech SDK's command line, from the app (R1001).

The SDK (`pip install atech`) turns a project.yaml into firmware and talks
to the board: validate, build, emulate (no board needed), upload, check,
monitor. This module finds the `atech` program, writes the firmware
folder for a design, and builds the argument lists. The Qt runner
(SdkRun) streams a command's output line by line.

The program is found like the chat CLIs (agent_cli.Locator): the path in
settings ("atech_sdk_path"), PATH, then the usual install places (pipx,
uv tools, pip --user, Homebrew). Nothing here installs anything.
"""
import glob
import os
import re
import shutil


PATH_KEY = "atech_sdk_path"
INSTALL_COMMAND = "uv tool install atech"
INSTALL_ALT = "pip install atech"
INSTALL_NOTE = ("Python 3.10 or newer. The first build downloads the ESP32 "
                "compiler once (about 2.4 GB); after that builds work offline "
                "and take seconds.")
DOCS_URL = "https://atech.dev/docs"
PRODUCTS_DIR = os.path.join("~", "Documents", "Atech Products")
PROJECT = "project.yaml"

#: The commands the app runs, in the order a first build takes them:
#: key -> (button words, argv after "atech", needs a board, what it does).
COMMANDS = {
    "validate": ("Check", ["validate", "{dir}"], False,
                 "Checks every module's port against the board."),
    "build": ("Build", ["build", "{dir}"], False,
              "Generates the firmware and compiles it."),
    "emulate": ("Run without a board", ["emulate", "{dir}", "--seconds", "10"], False,
                "Runs the firmware on an emulated board for 10 s and prints its events."),
    "upload": ("Flash to board", ["upload", "{dir}"], True,
               "Builds if needed and flashes the board on USB."),
    "check": ("Board health", ["check"], True,
              "Reboots the board and reports each module's health."),
    "monitor": ("Watch events", ["monitor"], True,
                "Streams the board's events until you stop it."),
    "ports": ("Find board", ["ports"], False,
              "Lists the USB ports that look like an Atech board."),
}
ORDER = ("validate", "build", "emulate", "upload", "check", "monitor")


KNOWN = ("~/.local/bin/atech", "~/.local/share/uv/tools/atech/bin/atech",
         "~/.local/pipx/venvs/atech/bin/atech", "/opt/homebrew/bin/atech",
         "/usr/local/bin/atech", "/usr/bin/atech")
_LOC = []


def _locator():
    """agent_cli.Locator (it imports Qt, so only when first needed), plus
    pip --user's versioned folders."""
    if not _LOC:
        from . import agent_cli

        class _Locator(agent_cli.Locator):
            def known_locations(self):
                out = super().known_locations()
                out += sorted(glob.glob(os.path.expanduser(
                    "~/Library/Python/3.*/bin/atech")), reverse=True)
                return out

        _LOC.append(_Locator(("atech",), PATH_KEY, known=KNOWN))
    return _LOC[0]


def _plain_find(explicit):
    if explicit:
        p = os.path.expanduser(explicit)
        return p if os.path.isfile(p) and os.access(p, os.X_OK) else None
    p = shutil.which("atech")
    if p:
        return p
    for c in [os.path.expanduser(k) for k in KNOWN] + sorted(
            glob.glob(os.path.expanduser("~/Library/Python/3.*/bin/atech")), reverse=True):
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def find(explicit=None):
    """Absolute path to `atech`, or None. Starts no process."""
    try:
        return _locator().find(explicit)
    except ImportError:
        return _plain_find(explicit)


def locate(timeout=8):
    """find(), then the login shell's answer (never on the GUI thread)."""
    p = find()
    if p:
        return p
    try:
        _locator().probe_login_shell(timeout)
    except Exception:                                   # noqa: BLE001
        return None
    return find()


def choose(path):
    """Remember an `atech` the user picked (Agent Settings key). True when
    it is a program and was saved."""
    p = os.path.expanduser(path or "")
    if not (os.path.isfile(p) and os.access(p, os.X_OK)):
        return False
    try:
        from . import settings
        return bool(settings.update(**{PATH_KEY: p}))
    except Exception:                                   # noqa: BLE001
        return False


def safe_folder(name):
    """A folder name from a project name: letters, digits, space, - and _."""
    s = re.sub(r"[^\w \-]", "", name or "", flags=re.UNICODE).strip()
    return re.sub(r"\s+", " ", s)[:60] or "Product"


def product_dir(project, root=None):
    """~/Documents/Atech Products/<project> (not created)."""
    root = os.path.expanduser(root or PRODUCTS_DIR)
    return os.path.join(root, safe_folder(project))


def firmware_dir(project, root=None):
    return os.path.join(product_dir(project, root), "firmware")


def write_firmware(folder, yaml_text, keep_code=True):
    """Write <folder>/project.yaml. With keep_code, an existing file's
    code: block (the user's or the agent's setup/loop) is kept and only
    the modules list is replaced. Returns the path."""
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, PROJECT)
    text = yaml_text
    if keep_code and os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as fh:
                old = fh.read()
            code = _code_block(old)
            if code and code.strip() != _code_block(yaml_text).strip():
                text = _code_block_replace(yaml_text, code)
        except OSError:
            pass
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)
    return path


def _code_block(text):
    i = text.find("\ncode:")
    return text[i + 1:] if i >= 0 else ""


def _code_block_replace(text, code):
    i = text.find("\ncode:")
    head = text[: i + 1] if i >= 0 else text.rstrip("\n") + "\n"
    return head + code


def argv(key, folder, exe=None, port=None):
    """The full argument list for one command. port: a serial port for
    the board commands (None: the SDK finds it)."""
    if key not in COMMANDS:
        raise KeyError(key)
    exe = exe or find() or "atech"
    args = [a.replace("{dir}", folder) for a in COMMANDS[key][1]]
    if port and key in ("upload", "check", "monitor"):
        args += ["--port", port]
    return [exe] + args


def child_env(exe=None):
    """The SDK's environment: the bundle's Python paths removed (the
    SDK is its own Python program), and the folder `atech` is in put first
    on PATH: `atech build` runs PlatformIO's `pio`, which pip, pipx and uv
    install next to it (measured 16 Nov 2026: without it the build stops
    with "PlatformIO not found")."""
    try:
        from . import claude_cli
        env = claude_cli._child_env()
    except Exception:                                   # noqa: BLE001
        env = dict(os.environ)
        for k in ("PYTHONHOME", "PYTHONPATH"):
            env.pop(k, None)
    if exe:
        d = os.path.dirname(os.path.abspath(exe))
        parts = [p for p in (env.get("PATH") or "").split(os.pathsep) if p and p != d]
        env["PATH"] = os.pathsep.join([d] + parts)
    return env


def summarise(key, code, text):
    """One line for the result of a run, from its exit code and output."""
    low = (text or "").lower()
    boot = [ln.split(":", 1)[1].strip() for ln in (text or "").splitlines()
            if ln.lower().startswith("boot report:")]
    if code == 0 and key in ("emulate", "check") and boot:
        return ("Ran on the emulated board: " if key == "emulate" else "Board health: ") \
            + boot[-1]
    if code == 0:
        return {"validate": "The SDK accepts every module's port.",
                "build": "Firmware built.",
                "emulate": "The firmware ran on the emulated board.",
                "upload": "Flashed. The board is running the new firmware.",
                "check": "Board health read.",
                "monitor": "Stopped watching.",
                "ports": "Done."}.get(key, "Done.")
    if "platformio" in low and ("not found" in low or "install" in low):
        return "Building needs PlatformIO, which comes with the SDK: reinstall it (%s)." \
            % INSTALL_COMMAND
    if "no board" in low or "no serial" in low or "could not find" in low and "port" in low:
        return "No board found on USB. Plug it in with a data cable and try again."
    if "permission" in low and "port" in low:
        return "The serial port is busy or not allowed. Close other serial monitors " \
               "(or press Free port) and try again."
    errs = [ln.split(":", 1)[1].strip() for ln in (text or "").splitlines()
            if ln.lower().startswith("error:") and ln.split(":", 1)[1].strip()]
    if errs:
        return "The Atech SDK stopped: %s. The Overview page has the fix." % errs[-1]
    return "It stopped with an error (code %d). The output above says why." % code


# ------------------------------------------------------------------ Qt runner
def _qt():
    try:
        from PySide6 import QtCore
    except ImportError:                                 # pragma: no cover
        from PySide2 import QtCore                      # type: ignore
    return QtCore


def make_runner(parent=None):
    """An SdkRun (QObject) on the GUI thread; see SdkRun.start."""
    QtCore = _qt()

    class SdkRun(QtCore.QObject):
        line = QtCore.Signal(str)
        finished = QtCore.Signal(str, int, str)   # key, exit code, summary

        def __init__(self, parent=None):
            super().__init__(parent)
            self.proc = None
            self.key = None
            self._buf = []

        def running(self):
            return self.proc is not None and \
                self.proc.state() != QtCore.QProcess.NotRunning

        def start(self, key, folder, exe=None, port=None):
            if self.running():
                return False
            args = argv(key, folder, exe=exe, port=port)
            self.key, self._buf = key, []
            p = QtCore.QProcess(self)
            env = QtCore.QProcessEnvironment()
            for k, v in child_env(args[0]).items():
                env.insert(k, v)
            p.setProcessEnvironment(env)
            p.setWorkingDirectory(folder if os.path.isdir(folder) else os.path.expanduser("~"))
            p.setProcessChannelMode(QtCore.QProcess.MergedChannels)
            p.readyReadStandardOutput.connect(self._read)
            p.finished.connect(self._done)
            p.errorOccurred.connect(self._error)
            self.proc = p
            self.line.emit("$ atech " + " ".join(args[1:]))
            p.start(args[0], args[1:])
            return True

        def stop(self):
            if self.running():
                self.proc.terminate()
                if not self.proc.waitForFinished(1500):
                    self.proc.kill()

        def _read(self):
            data = bytes(self.proc.readAllStandardOutput()).decode("utf-8", "replace")
            for ln in data.splitlines():
                self._buf.append(ln)
                self.line.emit(ln)

        def _done(self, code, _status=None):
            text = "\n".join(self._buf)
            self.finished.emit(self.key or "", int(code), summarise(self.key, int(code), text))
            self.proc = None

        def _error(self, err):
            if err == QtCore.QProcess.FailedToStart:
                self.line.emit("Could not start the Atech SDK. Install it: " + INSTALL_COMMAND)
                self.finished.emit(self.key or "", 127,
                                   "The Atech SDK is not installed: " + INSTALL_COMMAND)
                self.proc = None

    return SdkRun(parent)
