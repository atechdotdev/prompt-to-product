"""R1260: the fit of every shaft in a bore (atech_fitcheck) - runs INSIDE freecadcmd.

    <freecadcmd> fc_cadwf_r1260.py        (tests/test_cadwf_r1260.py does this)

A printed pin in printed holes of three sizes, and a DC motor's shaft (a tip
and a direction, as ./check measures them from the module) in a D-bore, in
round bores and in a hole it does not touch. Prints PASS/FAIL per check and
ends with ATECH_CADWF_R1260=<failures>.

ATECH_CADWF_SABOTAGE=noshrink sets the hole shrink to 0 (the classes must
change, and the suite must notice).
"""
import os
import sys
import traceback

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "acadagent", "agent_kit")))

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402

import atech_cad as cad  # noqa: E402
import atech_fit  # noqa: E402
import atech_fitcheck as fc  # noqa: E402

V = App.Vector
FAIL = []
if os.environ.get("ATECH_CADWF_SABOTAGE") == "noshrink":
    atech_fit.FIT["hole_shrink"] = (0.0, "A", "sabotage")


def check(name, ok, detail=""):
    print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAIL.append(name)


def t_pins_in_holes():
    plate = Part.makeBox(60, 20, 6)
    pins = []
    for i, hole_d in enumerate((3.0, 3.3, 3.6)):
        x = 10 + 20 * i
        plate = plate.cut(Part.makeCylinder(hole_d / 2, 8, V(x, 10, -1)))
        pins.append(Part.makeCylinder(1.5, 12, V(x, 10, -3)))
    parts = [{"label": "Plate", "shape": plate}] + [
        {"label": "Pin_%d" % i, "shape": p} for i, p in enumerate(pins)]
    rows = fc.pin_fits(parts)
    by = {r["hole_d"]: r for r in rows}
    check("three pairs", sorted(by) == [3.0, 3.3, 3.6], repr(sorted(by)))
    want = {3.0: (-0.25, "interference"), 3.3: (0.05, "transition"), 3.6: (0.35, "running")}
    for d, (printed, word) in want.items():
        r = by.get(d) or {}
        check("3 mm pin in a %g hole prints %g clear: %s" % (d, printed, word),
              r.get("printed") == printed and r.get("fit") == word,
              "%s / %s" % (r.get("printed"), r.get("fit")))
        check("%g: the pair and the shared length" % d,
              r.get("hole") == "Plate" and str(r.get("pin", "")).startswith("Pin_")
              and abs((r.get("overlap_mm") or 0) - 6.0) < 0.05, repr(r.get("overlap_mm")))
    check("tightest first", [r["hole_d"] for r in rows] == [3.0, 3.3, 3.6])
    text = "\n".join(fc.lines([], rows))
    check("the line says it", "FIT Pin_0 in Plate: a 3 pin in a 3 hole, 0 clear as drawn, "
          "about -0.25 once printed: interference" in text, text)


def t_what_is_not_a_fit():
    plate = Part.makeBox(60, 20, 6).cut(Part.makeCylinder(4.0, 8, V(10, 10, -1)))
    plate = plate.cut(Part.makeCylinder(1.5, 8, V(40, 10, -1)))
    loose = Part.makeCylinder(1.5, 12, V(10, 10, -3))        # 3 in an 8 hole: 5 clear
    off = Part.makeCylinder(1.5, 12, V(41, 10, -3))          # 1 mm off the hole's axis
    short = Part.makeCylinder(1.5, 4, V(40, 10, 5.5))        # only 0.5 mm in the hole
    rows = fc.pin_fits([{"label": "Plate", "shape": plate}, {"label": "Loose", "shape": loose},
                        {"label": "Off", "shape": off}, {"label": "Short", "shape": short}])
    check("a loose pin, an off-axis pin and a barely entered pin are no fits", rows == [],
          repr(rows))
    # a part's own boss in its own bore is not a pair
    ring = Part.makeCylinder(5, 6).cut(Part.makeCylinder(1.6, 6))
    check("one part alone has no pairs", fc.pin_fits([{"label": "Ring", "shape": ring}]) == [])


def _hub(**kw):
    """A hub on a shaft that points +X with its tip at the origin: the
    bore's mouth is 8.8 back along the shaft, at the gearbox side."""
    hub = Part.makeCylinder(8, 12, V(-10, 0, 0), V(1, 0, 0))
    return kw, hub


MOTOR = [{"label": "DC Motor (1)", "tip": (0.0, 0.0, 0.0), "axis": (1.0, 0.0, 0.0)}]


def t_motor_d_bore():
    _, hub = _hub()
    hub = cad.d_bore(hub, (-10, 0, 0), "+X", flat="+Z")
    rows = fc.motor_fits([{"label": "Wheel_Hub", "shape": hub}], MOTOR)
    r = rows[0] if rows else {}
    check("the printed D-bore is recognised", r.get("kind") == "dbore"
          and r.get("hole_d") == 3.4 and r.get("across") == 2.9 and r.get("level") == "info",
          repr(r))
    check("it says how much of the shaft is in it", r.get("engaged_mm") == 8.8,
          repr(r.get("engaged_mm")))
    check("its line", "D-bore 3.4 / 2.9, the push fit that printed" in r.get("text", ""))


def t_motor_old_d_bore_is_a_note():
    _, hub = _hub()
    hub = cad.d_bore(hub, (-10, 0, 0), "+X", bore=3.1, across=2.6)
    r = (fc.motor_fits([{"label": "Hub", "shape": hub}], MOTOR) or [{}])[0]
    check("3.1 / 2.6 is tighter than what printed: a note", r.get("level") == "note"
          and "tighter" in r.get("text", "") and "drilling" in r.get("text", ""), repr(r))


def t_motor_round_bores():
    for d, level, kind, words in ((3.3, "warning", "round", "does not drive"),
                                  (3.0, "warning", "round", "does not drive"),
                                  (3.5, "info", "round", "turns in a round 3.5 hole")):
        _, hub = _hub()
        hub = hub.cut(Part.makeCylinder(d / 2, 14, V(-11, 0, 0), V(1, 0, 0)))
        r = (fc.motor_fits([{"label": "Hub", "shape": hub}], MOTOR) or [{}])[0]
        check("round %g on the motor shaft: %s" % (d, level),
              r.get("level") == level and r.get("kind") == kind and words in r.get("text", ""),
              repr(r))
    _, hub = _hub()
    hub = hub.cut(Part.makeCylinder(2.5, 14, V(-11, 0, 0), V(1, 0, 0)))
    check("a 5 mm hole the shaft does not touch is no fit",
          fc.motor_fits([{"label": "Hub", "shape": hub}], MOTOR) == [])


def t_a_deep_d_bore_the_shaft_only_half_enters():
    # the wheel's bore is deeper than the part of the shaft that reaches it:
    # the flat's middle is past the shaft's tip, and it is still a D-bore
    hub = Part.makeCylinder(8, 14, V(-4.5, 0, 0), V(1, 0, 0))
    hub = cad.d_bore(hub, (-4.5, 0, 0), "+X", depth=11, flat="+Y")
    r = (fc.motor_fits([{"label": "Rim", "shape": hub}], MOTOR) or [{}])[0]
    # 4.5 mm of shaft in the hub, 4.0 of it past the 0.5 lead-in cone
    check("a deep D-bore with 4.5 mm of shaft in it", r.get("kind") == "dbore"
          and r.get("across") == 2.9 and r.get("engaged_mm") == 4.0, repr(r))


def t_motor_elsewhere():
    _, hub = _hub()
    hub = hub.cut(Part.makeCylinder(1.65, 14, V(-11, 0, 0), V(1, 0, 0)))
    hub.translate(V(0, 6, 0))                                # 6 mm off the shaft
    check("a bore that is not on the shaft is not its fit",
          fc.motor_fits([{"label": "Hub", "shape": hub}], MOTOR) == [])
    far = Part.makeCylinder(8, 12, V(5, 0, 0), V(1, 0, 0)).cut(
        Part.makeCylinder(1.65, 14, V(4, 0, 0), V(1, 0, 0)))  # beyond the tip
    check("a bore beyond the shaft's tip is not its fit",
          fc.motor_fits([{"label": "Far", "shape": far}], MOTOR) == [])


for fn in (t_pins_in_holes, t_what_is_not_a_fit, t_motor_d_bore, t_motor_old_d_bore_is_a_note,
           t_motor_round_bores, t_a_deep_d_bore_the_shaft_only_half_enters,
           t_motor_elsewhere):
    try:
        fn()
    except Exception:                                   # noqa: BLE001
        traceback.print_exc()
        check(fn.__name__, False, "raised")

print("ATECH_CADWF_R1260=%d" % len(FAIL))
if FAIL:
    print("FAILED: " + ", ".join(FAIL))
