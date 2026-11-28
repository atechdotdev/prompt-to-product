"""R1300 under freecadcmd: ribbons that run through themselves.

Run by test_cables_r1300.py. A ribbon bent across its width tighter than
its half-width turns inside out (its inner edge runs backwards): the solid
stays "valid", its volume goes negative or wrong, and a boolean with it
finds nothing, so ./check passed cables that ran through walls.
"""
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
KIT = os.path.join(ADDON, "acadagent", "agent_kit")
PROJECTS = os.path.normpath(os.path.join(ADDON, "..", "..", "projects"))
sys.path.insert(0, KIT)
sys.path.insert(0, ADDON)
sys.path.insert(0, PROJECTS)

import numpy as np  # noqa: E402
import FreeCAD as App  # noqa: E402
import Part  # noqa: E402

import atech_geom  # noqa: E402
import atech_ports as ap  # noqa: E402

V = App.Vector
FAIL = []


def check(name, ok, detail=""):
    print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAIL.append(name)


def clean(shape):
    """True if OCCT's full check finds nothing (no self-intersection)."""
    return ap.ribbon_selfint(shape) is None


# the bedside lamp's first port-6 route (28 Nov 2026): it leaves the
# board's edge with its width upright and turns straight down, a bend
# across the width - the old ribbon ran through itself here
LAMP_P6 = dict(
    points=[(2.7605, -1.2672, 29.9881), (-3.2395, -1.2672, 29.9881), (-3.5, -4.0, 23.0),
            (16.0, -28.0, 12.0), (30.0, -42.1078, 5.7501), (30.0, -48.1078, 5.7501)],
    t0=(-1.0, 0.0, 0.0), t1=(0.0, -1.0, 0.0), w0=(0.0, 0.0, 1.0), w1=(-1.0, 0.0, 0.0))


def ribbon(case, **kw):
    a = lambda v: np.array(v, dtype=float)                # noqa: E731
    return ap._ribbon([a(p) for p in case["points"]], a(case["t0"]), a(case["t1"]),
                      a(case["w0"]), a(case["w1"]), smooth=True, **kw)


def t_a_bend_across_the_width_is_a_clean_solid():
    """No ribbon that runs through itself is handed on: the route is
    either built clean, of the ribbon's volume, or refused."""
    try:
        sh, length, _ = ribbon(LAMP_P6, free=(ap.CABLE_LEAD / 2, None))
    except ap.AtechPortError as e:
        check("the bend is refused, with where and what to do",
              e.info.get("kind") == "cable_fold" and "near (" in str(e), str(e))
        return
    expect = length * ap.CABLE_W * ap.CABLE_T
    check("one solid", len(sh.Solids) == 1, "%d" % len(sh.Solids))
    check("it does not run through itself", clean(sh), str(ap.ribbon_selfint(sh)))
    check("its volume is the ribbon's", abs(sh.Volume - expect) < 0.03 * expect,
          "%.1f for %.1f" % (sh.Volume, expect))


def t_a_hairpin_is_refused_or_clean():
    """A U-turn of 2 mm across the width: no ribbon can do it; whatever
    comes back is never a solid that runs through itself."""
    case = dict(points=[(0, 0, 0), (10, 0, 0), (12, 1, 0), (10, 2, 0), (0, 2, 0)],
                t0=(1, 0, 0), t1=(-1, 0, 0), w0=(0, 1, 0), w1=(0, -1, 0))
    try:
        sh, _, _ = ribbon(case)
    except ap.AtechPortError as e:
        check("the hairpin is refused, with where and what to do",
              e.info.get("kind") == "cable_fold" and "near (" in str(e)
              and "waypoint" in str(e), str(e))
        return
    check("the hairpin comes out clean", clean(sh) and sh.Volume > 0,
          "%s %.1f" % (ap.ribbon_selfint(sh), sh.Volume))


def t_a_half_turn_in_a_millimetre_is_refused():
    """dice_tower's sensor ribbon (28 Nov 2026): straight, 1 mm of curve
    between its two 6 mm legs, its width turned over end to end - no bend
    at all, so nothing looked at it, and it ran through itself (8 % of its
    volume short). The loft's volume gives it away."""
    case = dict(points=[(0, 0, 0), (0, -6, 0), (0, -7, 0), (0, -13, 0)],
                t0=(0, -1, 0), t1=(0, -1, 0), w0=(0, 0, 1), w1=(0, 0, -1))
    try:
        sh, length, _ = ribbon(case)
    except ap.AtechPortError as e:
        check("the half turn is refused as a twist", e.info.get("kind") == "cable_fold"
              and "twists 180 degrees" in str(e), str(e))
        return
    expect = length * ap.CABLE_W * ap.CABLE_T
    check("the half turn comes out clean", clean(sh) and abs(sh.Volume - expect) < 0.01 * expect,
          "%s %.1f for %.1f" % (ap.ribbon_selfint(sh), sh.Volume, expect))


def item(name, shape):
    return {"name": name, "label": name, "shape": shape, "role": None}


def t_an_inside_out_part_is_not_passed():
    wall = Part.makeBox(20, 20, 4)
    bad = Part.makeBox(6, 6, 10, V(7, 7, -3)).reversed()
    check("a reversed box reads inside out", atech_geom.inside_out(bad) and
          not atech_geom.inside_out(wall), "%.1f" % bad.Volume)
    hits, _ = atech_geom.overlaps([item("Wall", wall), item("Cable", bad)])
    check("its overlap with a wall is found", len(hits) == 1, repr(hits))
    if hits:
        text = atech_geom.overlap_text(hits[0])
        check("the overlap says what it sampled", "inside" in text, text)
    far = Part.makeBox(6, 6, 10, V(40, 7, -3)).reversed()
    hits, _ = atech_geom.overlaps([item("Wall", wall), item("Cable", far)])
    check("clear of the wall: no hit", hits == [], repr(hits))


for fn in (t_a_bend_across_the_width_is_a_clean_solid, t_a_hairpin_is_refused_or_clean,
           t_a_half_turn_in_a_millimetre_is_refused, t_an_inside_out_part_is_not_passed):
    try:
        fn()
    except Exception:                                   # noqa: BLE001
        traceback.print_exc()
        check(fn.__name__, False, "raised")

print("ATECH_CABLES_R1300=%d" % len(FAIL))
if FAIL:
    print("FAILED: " + ", ".join(FAIL))
