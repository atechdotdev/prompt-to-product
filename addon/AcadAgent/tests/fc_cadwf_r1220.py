"""R1220: the kit calls that apply the printed fit numbers - runs INSIDE freecadcmd.

    <freecadcmd> fc_cadwf_r1220.py        (tests/test_cadwf_r1220.py does this)

cad.d_bore, cad.shaft_hole, cad.fit, cad.wheel(flat=True) and
cad.screw_boss(kind="insert"). Every expected number is worked out here from
the sizes asked for, never read back from the helper. Prints PASS/FAIL per
check and ends with ATECH_CADWF_R1220=<failures>.

ATECH_CADWF_SABOTAGE=<gate> breaks one thing to prove the suite can fail:
  dbore   d_bore cuts the old 3.10 / 2.60
  round   wheel(flat=True) cuts a round through bore
  insert  screw_boss(kind="insert") drills the thread-forming pilot
"""
import math
import os
import sys
import traceback

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "acadagent", "agent_kit")))

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402

import atech_cad as cad  # noqa: E402
import atech_detail as det  # noqa: E402
import atech_fit  # noqa: E402

V = App.Vector
FAIL = []
SAB = os.environ.get("ATECH_CADWF_SABOTAGE", "")

if SAB == "dbore":
    atech_fit.FIT["dbore_d3"] = ((3.10, 2.60), "A", "sabotage")
elif SAB == "round":
    _real_wheel = det.wheel

    def _round_wheel(*a, **k):
        if k.pop("flat", False):
            k.setdefault("bore", 3.4)
        return _real_wheel(*a, **k)
    det.wheel = cad.wheel = _round_wheel
elif SAB == "insert":
    det.insert_d = det.pilot_d


def check(name, ok, detail=""):
    print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAIL.append(name)


def case(fn):
    try:
        fn()
    except Exception:                                   # noqa: BLE001
        traceback.print_exc()
        check(fn.__name__, False, "raised")


def d_area(bore, across):
    """Area of a D: a circle of diameter `bore` cut by a chord `across`
    from its far side."""
    r = bore / 2.0
    h = bore - across
    seg = r * r * math.acos((r - h) / r) - (r - h) * math.sqrt(2 * r * h - h * h)
    return math.pi * r * r - seg


def section_extent(shape, origin, normal, around, reach):
    """Size (along u, along v) of the hole in `shape`'s section through
    `origin`: a block `reach` wide around `around`, minus the material."""
    n = V(normal)
    probe = Part.makeCylinder(reach, 0.02, V(origin) - n * 0.01, n)
    air = probe.cut(shape)
    return air


# ------------------------------------------------------------------ d_bore
def t_d_bore_default_is_the_printed_fit():
    block = Part.makeBox(20, 20, 20, V(-10, -10, 0))
    res = cad.d_bore(block, (0, 0, 20), "-Z", flat="+X", lead_in=0)
    removed = block.Volume - res.Volume
    want = d_area(3.4, 2.9) * 12.0
    check("d_bore volume", abs(removed - want) < 0.02 * want,
          "%.3f vs %.3f" % (removed, want))
    # measured in a section 6 mm down: round side to round side 3.4, far
    # side to the flat 2.9, and the flat is on +X
    air = Part.makeBox(8, 8, 0.02, V(-4, -4, 14)).cut(res)
    bb = air.BoundBox
    check("d_bore round width (Y)", abs(bb.YLength - 3.4) < 0.01, "%.3f" % bb.YLength)
    check("d_bore across the flat (X)", abs(bb.XLength - 2.9) < 0.01, "%.3f" % bb.XLength)
    check("d_bore flat on +X", abs(bb.XMax - (2.9 - 1.7)) < 0.01 and abs(bb.XMin + 1.7) < 0.01,
          "x %.3f..%.3f" % (bb.XMin, bb.XMax))
    # blind: 12 deep, nothing at 12.5
    check("d_bore is 12 deep", res.isInside(V(0, 0, 20 - 12.5), 1e-6, True)
          and not res.isInside(V(0, 0, 20 - 11.5), 1e-6, True))
    check("d_bore one valid solid", res.isValid() and len(res.Solids) == 1)


def t_d_bore_lead_in_and_axis():
    block = Part.makeBox(20, 20, 20, V(-10, -10, 0))
    res = cad.d_bore(block, (10, 0, 10), "-X", flat="+Z", depth=8)
    # mouth on the +X face, widened by 0.5 all round at the face
    air = Part.makeBox(0.02, 8, 8, V(9.98, -4, 6)).cut(res)
    bb = air.BoundBox
    check("lead-in mouth is 4.4 wide", abs(bb.YLength - 4.4) < 0.05, "%.3f" % bb.YLength)
    air = Part.makeBox(0.02, 8, 8, V(6.0, -4, 6)).cut(res)
    bb = air.BoundBox
    check("along -X: round width 3.4 (Y)", abs(bb.YLength - 3.4) < 0.01, "%.3f" % bb.YLength)
    check("along -X: across the flat 2.9 (Z), flat on +Z",
          abs(bb.ZLength - 2.9) < 0.01 and abs(bb.ZMax - (10 + 2.9 - 1.7)) < 0.01,
          "z %.3f..%.3f" % (bb.ZMin, bb.ZMax))
    check("depth 8", res.isInside(V(10 - 8.5, 0, 10), 1e-6, True)
          and not res.isInside(V(10 - 7.5, 0, 10), 1e-6, True))


def t_d_bore_refuses_nonsense():
    block = Part.makeBox(20, 20, 20, V(-10, -10, 0))
    for kw, why in (({"across": 3.4}, "across = bore"), ({"across": 1.0}, "across < bore/2"),
                    ({"depth": 0}, "no depth"), ({"flat": "-Z"}, "flat along the axis")):
        try:
            cad.d_bore(block, (0, 0, 20), "-Z", **kw)
            check("d_bore refuses " + why, False)
        except cad.CadError:
            check("d_bore refuses " + why, True)
    try:
        cad.d_bore(block, (0, 0, 20), "+Z")              # drilling out of the part
        check("d_bore refuses the wrong direction", False)
    except cad.CadError:
        check("d_bore refuses the wrong direction", True)


def _shaft(tip_z):
    """The DC Motor's shaft as a solid (3.0 round, 2.5 across the flat on
    +X, 8.8 long), pointing +Z with its tip at tip_z."""
    cyl = Part.makeCylinder(1.5, 8.8, V(0, 0, tip_z - 8.8))
    return cyl.common(Part.makeBox(2.5, 4, 9, V(-1.5, -2, tip_z - 8.9)))


def t_d_bore_in_a_thin_part():
    """R1295 review: the default 12 mm bore in a thinner part went through
    without a word, or (3 mm and under) failed with "most of it is in air
    - check `at` and `axis`". The first fix always kept a 1 mm floor; the
    second review found that floor in the shaft's way on every hub from 5
    to 9 mm. A floor is kept only when the whole 8.8 mm shaft goes in."""
    # the hub sits 0.5 off the gearbox, the bore goes in the way the shaft
    # points (+Z): whatever the hub's thickness the shaft must go in
    for t in (2.0, 3.0, 4.5, 5.0, 6.0, 8.0, 9.0, 9.5, 9.8, 10.0, 11.0, 12.5, 13.0, 16.0):
        hub = Part.makeCylinder(8, t, V(0, 0, 0.5))
        res = cad.d_bore(hub, (0, 0, 0.5), "+Z", flat="+X", lead_in=0)
        over = res.common(_shaft(8.8)).Volume
        check("%g mm hub: the shaft goes in (no overlap)" % t, over < 1e-6, "%.4f mm3" % over)
        top = 0.5 + t
        open_top = not res.isInside(V(0, 0, top - 0.5), 1e-6, True)
        if t - 1.0 >= 8.8 - 1e-9:
            check("%g mm hub: blind, a floor stays" % t, not open_top
                  and (t >= 13 or not res.isInside(V(0, 0, top - 1.5), 1e-6, True)))
        else:
            check("%g mm hub: through, as it always was" % t, open_top)
        check("%g mm hub: one valid solid" % t, res.isValid() and len(res.Solids) == 1)
    # the depths: 10 mm -> 9, 12.5 -> 11.5, 13 and more -> the table's 12
    for t, deep in ((10.0, 9.0), (12.5, 11.5), (13.0, 12.0), (16.0, 12.0)):
        hub = Part.makeCylinder(8, t)
        res = cad.d_bore(hub, (0, 0, t), "-Z", flat="+X", lead_in=0)
        want = d_area(3.4, 2.9) * deep
        removed = hub.Volume - res.Volume
        check("%g mm part: %g deep" % (t, deep), abs(removed - want) < 0.02 * want,
              "%.3f vs %.3f" % (removed, want))
    # a depth that is GIVEN is cut as given: blind in a thin part too
    res = cad.d_bore(Part.makeCylinder(8, 8), (0, 0, 8), "-Z", depth=5, flat="+X", lead_in=0)
    check("depth given: 5 deep in an 8 mm part", res.isInside(V(0, 0, 2.5), 1e-6, True)
          and not res.isInside(V(0, 0, 3.5), 1e-6, True))
    res = cad.d_bore(Part.makeCylinder(8, 4), (0, 0, 4), "-Z", depth=4.5, flat="+X", lead_in=0)
    check("depth given: through a 4 mm part", not res.isInside(V(0, 0, 0.2), 1e-6, True)
          and res.isValid())
    # `at` a little off the face is still on it
    for off in (0.05, 0.1, 0.25, -0.1):
        hub = Part.makeCylinder(8, 11)
        res = cad.d_bore(hub, (0, 0, 11 + off), "-Z", flat="+X", lead_in=0)
        check("`at` %+g mm off the face: still blind" % off,
              res.isInside(V(0, 0, 0.5), 1e-6, True), "")
    # a groove in the far side is seen: the bore does not break into it
    hub = Part.makeCylinder(8, 11)
    ring = Part.makeCylinder(1.6, 2.5).cut(Part.makeCylinder(1.0, 2.5))
    hub = hub.cut(ring)                                  # a ring groove 2.5 deep from below
    res = cad.d_bore(hub, (0, 0, 11), "-Z", flat="+X", lead_in=0)
    check("far-side groove: one solid, the shaft still goes in",
          res.isValid() and len(res.Solids) == 1, "%d solids" % len(res.Solids))
    # a hub standing on a wider flange: measured where the bore is
    hub = Part.makeCylinder(5, 10, V(0, 0, 6)).fuse(Part.makeCylinder(12, 2, V(0, 0, 6)))
    res = cad.d_bore(hub, (0, 0, 16), "-Z", flat="+X", lead_in=0)
    check("10 mm hub on a flange: 9 deep", res.isInside(V(0, 0, 6.5), 1e-6, True)
          and not res.isInside(V(0, 0, 7.5), 1e-6, True))


def t_d_bore_follows_the_users_value():
    block = Part.makeBox(20, 20, 20, V(-10, -10, 0))
    atech_fit.set_user("dbore_d3", (3.5, 3.0), note="35 was snug")
    try:
        res = cad.d_bore(block, (0, 0, 20), "-Z", flat="+X", lead_in=0)
        air = Part.makeBox(8, 8, 0.02, V(-4, -4, 14)).cut(res)
        bb = air.BoundBox
        check("the user's 3.5 / 3.0 is cut", abs(bb.YLength - 3.5) < 0.01
              and abs(bb.XLength - 3.0) < 0.01, "%.3f x %.3f" % (bb.YLength, bb.XLength))
        check("cad.fit reads it", cad.fit("dbore_d3") == (3.5, 3.0))
    finally:
        atech_fit.reset_user()
    check("cad.fit after reset", cad.fit("dbore_d3") == (3.40, 2.90))
    try:
        cad.fit("no_such_key")
        check("cad.fit refuses an unknown key", False)
    except cad.CadError:
        check("cad.fit refuses an unknown key", True)


def t_kit_defaults_equal_the_table():
    for key, val in cad._FIT_DEFAULTS.items():
        check("kit default %s" % key, atech_fit.value(key) == val,
              "%r vs %r" % (atech_fit.value(key), val))


# -------------------------------------------------------------- shaft_hole
def t_shaft_hole():
    block = Part.makeBox(20, 20, 6, V(-10, -10, 0))
    res = cad.shaft_hole(block, (0, 0, 6), "-Z", 3.0, through=True)
    removed = block.Volume - res.Volume
    want = math.pi * (3.5 / 2) ** 2 * 6
    check("running hole for a 3 mm shaft is drawn 3.5", abs(removed - want) < 0.01 * want,
          "%.3f vs %.3f" % (removed, want))
    # R1295: the classes are the ones the motor-shaft prints gave. On a
    # 3 mm shaft press is 3.3 (went on hot), push 3.4 (the fit that
    # shipped); the first rule drew 3.1 for "press", the bore that had to
    # be drilled open
    for cls, want_d in (("press", 3.3), ("push", 3.4), ("running", 3.5), ("clearance", 3.75)):
        res = cad.shaft_hole(block, (0, 0, 6), "-Z", 3.0, fit_class=cls, through=True)
        d = math.sqrt((block.Volume - res.Volume) / 6 / math.pi) * 2
        check("%s hole for a 3 mm shaft is drawn %g" % (cls, want_d), abs(d - want_d) < 0.01,
              "%.3f" % d)
    res = cad.shaft_hole(block, (0, 0, 6), "-Z", 5.0, fit_class="press", through=True)
    d = math.sqrt((block.Volume - res.Volume) / 6 / math.pi) * 2
    check("press hole for a 5 mm pin is drawn 5.3", abs(d - 5.3) < 0.01, "%.3f" % d)
    for old in ("transition", "slide", "pocket"):
        try:
            cad.shaft_hole(block, (0, 0, 6), "-Z", 3.0, fit_class=old)
            check("shaft_hole refuses the old class %s" % old, False)
        except cad.CadError:
            check("shaft_hole refuses the old class %s" % old, True)
    try:
        cad.shaft_hole(block, (0, 0, 6), "-Z", 3.0, fit_class="tight")
        check("shaft_hole refuses an unknown fit", False)
    except cad.CadError:
        check("shaft_hole refuses an unknown fit", True)


# ------------------------------------------------------------------- wheel
def _rim_bore(rim, z):
    """The bounding box of the air in a 6 mm disc round the wheel's axis
    (+Z here) at height z."""
    air = Part.makeCylinder(3.0, 0.02, V(0, 0, z)).cut(rim)
    return air


def t_wheel_flat():
    w = cad.wheel(50, 24, tread=None, axis="+Z", flat=True)
    rim = w["rim"]
    rw = 0.84 * 12.0
    check("wheel parts", sorted(w) == ["cap", "rim", "tyre"])
    air = _rim_bore(rim, -rw + 5.0)
    bb = air.BoundBox
    check("wheel D-bore round width 3.4", abs(bb.YLength - 3.4) < 0.01, "%.3f" % bb.YLength)
    check("wheel D-bore across the flat 2.9", abs(bb.XLength - 2.9) < 0.01, "%.3f" % bb.XLength)
    # blind from the back: open at the back face, closed under the cap
    check("open at the back", not rim.isInside(V(0, 0, -rw + 0.5), 1e-6, True))
    check("12 deep", not rim.isInside(V(0, 0, -rw + 11.5), 1e-6, True)
          and rim.isInside(V(0, 0, -rw + 12.5), 1e-6, True))
    hub_r = rim.common(Part.makeCylinder(30, 0.02, V(0, 0, -rw + 2.0)))
    # the hub keeps 2 mm round the bore: material at r = 1.7 + 1.9
    check("2 mm of hub round the bore", rim.isInside(V(0, 1.7 + 1.9, -rw + 2.0), 1e-6, True),
          "section area %.1f" % hub_r.Area)
    check("rim valid", rim.isValid() and len(rim.Solids) == 1)


def t_wheel_unchanged_without_flat():
    a = cad.wheel(40, 16, tread=None, axis="+Z", bore=3.3)
    rim = a["rim"]
    # a round through bore, as before: air on the axis from back to front
    rw = 0.84 * 8.0
    check("round bore still goes through", not rim.isInside(V(0, 0, 0), 1e-6, True)
          and not rim.isInside(V(0, 0, -rw + 0.2), 1e-6, True))
    air = _rim_bore(rim, 0.0)
    bb = air.BoundBox
    check("round bore is round 3.3", abs(bb.XLength - 3.3) < 0.01 and abs(bb.YLength - 3.3) < 0.01,
          "%.3f x %.3f" % (bb.XLength, bb.YLength))
    b = cad.wheel(40, 16, tread=None, axis="+Z")
    check("no bore without bore= or flat=", b["rim"].isInside(V(0, 0, 0), 1e-6, True))


def t_wheel_flat_refusals():
    try:
        cad.wheel(50, 24, tread=None, flat=True, hub_d=5.0)
        check("thin hub refused", False)
    except cad.CadError as exc:
        check("thin hub refused", "hub_d >= 7.4" in str(exc), str(exc))
    try:
        cad.wheel(30, 5, tread=None, flat=True)
        check("thin wheel refused", False)
    except cad.CadError as exc:
        check("thin wheel refused", "deep" in str(exc), str(exc))
    # R1295 review: at d 18 the message was "use hub_d <= 7.16", when the
    # keyed hub needs 7.4: it now names what can change
    try:
        cad.wheel(18, 10, tread=None, flat=True)
        check("small keyed wheel refused", False)
    except cad.CadError as exc:
        msg = str(exc)
        check("small keyed wheel: the way out is a larger wheel or bar spokes",
              "rim_d >= 15.5 (a wheel of d >= 25" in msg and "spoke_style='bar'" in msg
              and "rim_d >= 11.4 (d >= 19)" in msg and "hub_d <=" not in msg, msg)
    # between the two sizes the windows do not fit, and that message says the same
    try:
        cad.wheel(22, 10, tread=None, flat=True)
        check("22 mm keyed wheel with windows refused", False)
    except cad.CadError as exc:
        msg = str(exc)
        check("22 mm keyed wheel: windows need d 25, or bars",
              "no room for spoke windows" in msg and "d >= 25" in msg
              and "spoke_style='bar'" in msg, msg)
    # and both wheels the messages name build
    for d, style in ((25, "window"), (19, "bar")):
        try:
            w = cad.wheel(d, 10, tread=None, flat=True, spoke_style=style)
            check("a %d mm keyed wheel with %s spokes builds" % (d, style),
                  all(s.isValid() for s in w.values()))
        except cad.CadError as exc:
            check("a %d mm keyed wheel with %s spokes builds" % (d, style), False, str(exc))


# -------------------------------------------------------------- screw_boss
def _tub():
    outer = Part.makeBox(40, 40, 20)
    inner = Part.makeBox(36, 36, 18, V(2, 2, 2))
    return outer.cut(inner)


def t_screw_boss_insert():
    tub = _tub()
    top = V(20, 20, 14)
    res = cad.screw_boss(tub, top, "-Z", size="M3", kind="insert")
    # the pocket: 4.0 wide, 4.5 deep, in a boss 4.0 + 3.2 wide
    air = Part.makeCylinder(6.0, 0.02, V(20, 20, 12.0)).cut(res)
    hole = [s for s in air.Solids if s.isInside(V(20, 20, 12.01), 1e-6, True)]
    d = math.sqrt(4 * hole[0].Volume / 0.02 / math.pi) if hole else 0.0
    check("insert pocket is 4.0 wide", abs(d - 4.0) < 0.03, "%.3f" % d)
    # the boss is 12 tall (top at 14, floor top at 2): the pocket runs as
    # deep as a tap pilot would (min(12, 4 d + 1) = 12), at one width
    check("pocket has room for the screw tip", not res.isInside(V(21.8, 20, 14 - 11.5), 1e-6, True)
          and res.isInside(V(21.8, 20, 14 - 12.5), 1e-6, True))
    check("boss wall 1.6 round the pocket", res.isInside(V(20 + 2.0 + 1.5, 20, 12.0), 1e-6, True)
          and not res.isInside(V(20 + 2.0 + 1.75, 20, 12.5), 1e-6, True))
    short = cad.screw_boss(tub, V(20, 20, 6.5), "-Z", size="M3", kind="insert", ribs=0)
    check("a 4.5 mm boss takes the 4 mm insert + 0.5",
          not short.isInside(V(21.8, 20, 6.5 - 4.4), 1e-6, True)
          and short.isInside(V(21.8, 20, 6.5 - 4.6), 1e-6, True))
    try:
        cad.screw_boss(tub, V(20, 20, 6), "-Z", size="M3", kind="insert", ribs=0)
        check("a 4 mm boss is refused for a 4 mm insert", False)
    except cad.CadError:
        check("a 4 mm boss is refused for a 4 mm insert", True)
    check("insert boss valid", res.isValid() and len(res.Solids) == 1)
    rows = __import__("atech_geom").screw_pilots([
        {"label": "Screw_1", "shape": cad.screw("socket", "M3", 8, at=(20, 20, 14), axis="-Z")},
        {"label": "Tub", "shape": res}])
    check("./check reads it as an insert", bool(rows) and rows[0].get("verdict") == "insert",
          repr(rows[0] if rows else None))


def t_screw_boss_tap_is_as_before():
    tub = _tub()
    top = V(20, 20, 14)
    a = cad.screw_boss(tub, top, "-Z", size="M3")
    b = cad.screw_boss(tub, top, "-Z", size="M3", kind="tap")
    check("kind='tap' is the default boss", abs(a.Volume - b.Volume) < 1e-6)
    air = Part.makeCylinder(6.0, 0.02, V(20, 20, 10.0)).cut(a)
    hole = [s for s in air.Solids if s.isInside(V(20, 20, 10.01), 1e-6, True)]
    d = math.sqrt(4 * hole[0].Volume / 0.02 / math.pi) if hole else 0.0
    check("tap pilot is 2.5", abs(d - 2.5) < 0.03, "%.3f" % d)
    for bad in ({"kind": "glue"}, {"kind": "insert", "size": "M5"}):
        try:
            cad.screw_boss(tub, top, "-Z", **bad)
            check("screw_boss refuses %r" % (bad,), False)
        except cad.CadError:
            check("screw_boss refuses %r" % (bad,), True)


for fn in (t_d_bore_default_is_the_printed_fit, t_d_bore_in_a_thin_part, t_d_bore_lead_in_and_axis,
           t_d_bore_refuses_nonsense, t_d_bore_follows_the_users_value,
           t_kit_defaults_equal_the_table, t_shaft_hole, t_wheel_flat,
           t_wheel_unchanged_without_flat, t_wheel_flat_refusals,
           t_screw_boss_insert, t_screw_boss_tap_is_as_before):
    case(fn)

print("ATECH_CADWF_R1220=%d" % len(FAIL))
if FAIL:
    print("FAILED: " + ", ".join(FAIL))
