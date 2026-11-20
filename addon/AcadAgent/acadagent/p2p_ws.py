"""p2p_ws - the brief in the agent's workspace (R1100).

On each user turn (never on Studio's own fix turns) build.prepare_workspace
calls on_user_turn(ws, request):

    first message      p2p_brief.brief(request)   -> brief.json, BRIEF.md
    later messages     p2p_brief.update(b, request), when it changes something

The agent reads BRIEF.md (the API card says so) and ./check prints a
BRIEF line against it (p2p_accept, R1110). Plain Python, no Qt, no FreeCAD;
every failure is logged and swallowed: the brief helps the turn, it never
stops it.
"""
import os
import sys

BRIEF_MD = "BRIEF.md"
#: A first message shorter than this many words that names nothing is
#: not a product request ("hi", "thanks"): no brief yet.
MIN_WORDS = 3


def kit(name):
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_kit")
    if d not in sys.path:
        sys.path.append(d)
    return __import__(name)


def _log(msg):
    try:
        import FreeCAD
        FreeCAD.Console.PrintLog("Atech brief: %s\n" % msg)
    except Exception:                                     # noqa: BLE001
        sys.stderr.write("Atech brief: %s\n" % msg)


def is_request(text, B=None):
    """True when a first message reads as something to make."""
    B = B or kit("p2p_brief")
    t = (text or "").strip()
    if not t or t.startswith("/"):
        return False
    mods, _w = B.modules(t)
    if mods or B.size(t)["max_mm"]:
        return True
    return len(t.split()) >= MIN_WORDS and not t.rstrip().endswith("?")


def write(ws, b, B=None):
    B = B or kit("p2p_brief")
    B.save(b, ws)
    tmp = os.path.join(ws, BRIEF_MD + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(B.markdown(b))
    os.replace(tmp, os.path.join(ws, BRIEF_MD))


def on_user_turn(ws, request):
    """Write or update the brief for a user turn. Returns the brief, or None."""
    try:
        if not ws or not os.path.isdir(ws) or not (request or "").strip():
            return None
        B = kit("p2p_brief")
        old = B.load(ws)
        if old is None:
            if not is_request(request, B):
                return None
            b = B.brief(request)
            write(ws, b, B)
            return b
        nb = B.update(old, request)
        if nb.get("changes"):
            write(ws, nb, B)
            return nb
        return old
    except Exception as exc:                              # noqa: BLE001
        _log("on_user_turn: %r" % (exc,))
        return None


def read(ws):
    try:
        return kit("p2p_brief").load(ws) if ws else None
    except Exception:                                     # noqa: BLE001
        return None
