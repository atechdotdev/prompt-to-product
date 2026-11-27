"""atech_fitcheck - the fit of every shaft in a bore (R1260).

"No overlap" is not "it goes together and stays together". Gustav's
partsmith keeps a register of every place two parts touch, each with a fit
class, and fails a pair whose clearance is in the wrong band. This is the
part of that idea ./check can measure on its own, for round fits:

    a DC Motor's shaft in a printed bore
        a wheel or hub needs the keyed D-bore that printed (3.4 / 2.9);
        a round bore does not drive, and one that prints tight has to be
        drilled open (both happened to cad-workflow's first wheels)
    a printed pin in a printed hole
        the clearance as drawn, what is left of it once the hole has
        shrunk in printing, and the class that is (press, transition,
        running, slide, clearance)

./check prints one FIT line per pair. A round bore that grips the motor's
D-shaft is a WARNING; nothing here fails a build (docs/
CAD_WORKFLOW_MERGE.md, decision 2). The bands and the shrink are
atech_fit's ("fit_bands", "hole_shrink"), so a user's own print results
move the verdicts too.

Needs FreeCAD shapes (cylinder faces); the numbers are numpy.
"""
import numpy as np

import atech_fit

#: cylinders outside this range (radius, mm) are not shafts or bores
R_MIN, R_MAX = 0.5, 30.0
#: two axes are one when parallel within this (cosine) and this close (mm)
PARALLEL = 0.9995
AXIS_TOL = 0.15
#: a pin and a hole are a fit when the hole is at most this much wider
#: (diametral, mm) and they share at least this much length (mm)
FIT_MAX = 1.6
OVERLAP_MIN = 1.5
#: cylinder faces looked at per check, pairs reported
MAX_CYLINDERS = 6000
MAX_ROWS = 12
#: a bore this much wider than the motor's shaft does not touch it
FREE_HOLE = 1.5
#: how far a D-bore may differ from the table's and still be "the" fit
DBORE_TOL = 0.06


def _unit(v):
    v = np.asarray(tuple(v), dtype=float)
    n = np.linalg.norm(v)
    return v / n if n else v


def cylinders(shape, label=""):
    """The cylinder faces of a shape: [{"label", "r", "a" axis, "c" point
    on it, "t0", "t1" extent along the axis, "hole": concave}]."""
    out = []
    for f in shape.Faces:
        s = f.Surface
        if type(s).__name__ != "Cylinder":
            continue
        r = float(s.Radius)
        if not (R_MIN <= r <= R_MAX) or f.Area < 1e-3:
            continue
        a = _unit(s.Axis)
        c = np.array(tuple(s.Center), dtype=float)
        vt = np.array([tuple(v.Point) for v in f.Vertexes], dtype=float)
        if not len(vt):
            continue
        t = (vt - c) @ a
        try:
            u0, u1, v0, v1 = f.ParameterRange
            p = f.valueAt((u0 + u1) / 2, (v0 + v1) / 2)
            n = f.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
        except Exception:                               # noqa: BLE001
            continue
        pv = np.array(tuple(p), dtype=float) - c
        radial = pv - (pv @ a) * a
        hole = float(np.array(tuple(n), dtype=float) @ radial) < 0
        out.append({"label": label, "r": r, "a": a, "c": c, "t0": float(t.min()),
                    "t1": float(t.max()), "hole": hole})
    return out


def _coaxial(cyl, point, axis):
    """Is `cyl`'s axis the line through `point` along `axis`?"""
    if abs(float(cyl["a"] @ axis)) < PARALLEL:
        return False
    rel = point - cyl["c"]
    return float(np.linalg.norm(rel - (rel @ cyl["a"]) * cyl["a"])) <= AXIS_TOL


def _flat_across(shape, cyl, lo, hi):
    """The width of a D-bore from its round side to its flat: a planar
    face along the bore's axis, inside the bore's radius, within the axial
    range lo..hi (in the cylinder's own coordinate). None for a round bore."""
    a, c, r = cyl["a"], cyl["c"], cyl["r"]
    best = None
    for f in shape.Faces:
        if type(f.Surface).__name__ != "Plane":
            continue
        try:
            u0, u1, v0, v1 = f.ParameterRange
            n = _unit(f.normalAt((u0 + u1) / 2, (v0 + v1) / 2))
            p = np.array(tuple(f.valueAt((u0 + u1) / 2, (v0 + v1) / 2)), dtype=float)
        except Exception:                               # noqa: BLE001
            continue
        if abs(float(n @ a)) > 0.02:
            continue                                    # not along the bore
        rel = p - c
        t = float(rel @ a)
        # the flat runs the bore's whole depth; the shaft may reach only
        # part of it, so it is the flat's extent that must meet lo..hi
        vt = np.array([tuple(v.Point) for v in f.Vertexes], dtype=float)
        if not len(vt):
            continue
        ft = (vt - c) @ a
        if float(ft.max()) < lo - 0.25 or float(ft.min()) > hi + 0.25:
            continue
        d = abs(float((rel - t * a) @ n))               # the plane's distance from the axis
        radial = rel - t * a
        if d >= r - 0.02 or float(np.linalg.norm(radial)) > r + 0.02:
            continue
        across = r + d
        if best is None or across < best:
            best = across
    return best


def motor_fits(parts, motors):
    """For each DC motor shaft, the printed bore it sits in.

    parts   [{"label", "shape"}] printed parts
    motors  [{"label", "tip" (x, y, z), "axis" unit vector pointing OUT
              along the shaft}]
    Rows: {"motor", "part", "hole_d", "across" (None: round), "engaged_mm",
           "printed" (clearance once printed), "kind", "level", "text"}."""
    shaft_d, shaft_len = atech_fit.value("motor_shaft")
    t_bore, t_across = atech_fit.value("dbore_d3")
    shrink = atech_fit.value("hole_shrink")
    rows = []
    for m in motors:
        tip = np.array(tuple(m["tip"]), dtype=float)
        ax = _unit(m["axis"])
        for p in parts:
            best = None
            for cyl in cylinders(p["shape"], p["label"]):
                if not cyl["hole"] or not _coaxial(cyl, tip, ax):
                    continue
                # the shaft, in the cylinder's own axial coordinate
                s1 = float((tip - cyl["c"]) @ cyl["a"])
                s0 = float((tip - ax * shaft_len - cyl["c"]) @ cyl["a"])
                lo, hi = max(min(s0, s1), cyl["t0"]), min(max(s0, s1), cyl["t1"])
                if hi - lo < 1.0:
                    continue
                if best is None or cyl["r"] < best[0]["r"]:
                    best = (cyl, lo, hi)
            if best is None:
                continue
            cyl, lo, hi = best
            hole_d = round(2 * cyl["r"], 2)
            across = _flat_across(p["shape"], cyl, lo, hi)
            row = {"motor": m["label"], "part": p["label"], "hole_d": hole_d,
                   "across": round(across, 2) if across else None,
                   "engaged_mm": round(hi - lo, 1),
                   "printed": round(hole_d - shrink - shaft_d, 2), "level": "info"}
            if hole_d >= shaft_d + FREE_HOLE:
                continue                                # a hole it does not touch: no fit
            elif across is not None:
                row["kind"] = "dbore"
                off = max(abs(hole_d - t_bore), abs(across - t_across))
                if off <= DBORE_TOL:
                    row["text"] = ("%s on the shaft of %s: D-bore %g / %g, the push fit that "
                                   "printed; %g mm of the shaft in it"
                                   % (p["label"], m["label"], hole_d, row["across"],
                                      row["engaged_mm"]))
                else:
                    tighter = hole_d < t_bore or across < t_across
                    row["level"] = "note"
                    row["text"] = ("%s on the shaft of %s: D-bore %g / %g, %s than the %g / %g "
                                   "that printed and fitted (%s) - cad.d_bore's default is "
                                   "that fit"
                                   % (p["label"], m["label"], hole_d, row["across"],
                                      "tighter" if tighter else "looser", t_bore, t_across,
                                      "it may need drilling open" if tighter
                                      else "it may slip on the flat"))
            else:
                row["kind"] = "round"
                word = atech_fit.fit_word(row["printed"])
                if row["printed"] >= atech_fit.value("fit_bands")["running"][0]:
                    row["text"] = ("%s: the shaft of %s turns in a round %g hole, about %g "
                                   "clear once printed (%s)"
                                   % (p["label"], m["label"], hole_d, row["printed"], word))
                else:
                    row["level"] = "warning"
                    row["text"] = ("%s sits on the shaft of %s with a ROUND %g bore (prints "
                                   "about %g clear: %s). The shaft is a D: a round bore does "
                                   "not drive, and this one may not go on without drilling. "
                                   "Use s = cad.motor_shaft(motor), then cad.wheel(..., flat=s[\"flat\"]) or "
                                   "cad.d_bore(..., flat=s[\"flat\"]) (%g / %g, the "
                                   "fit that printed)"
                                   % (p["label"], m["label"], hole_d, row["printed"], word,
                                      t_bore, t_across))
            rows.append(row)
    return rows


def pin_fits(parts):
    """Every printed pin in a printed hole of another part: [{"pin", "hole",
    "pin_d", "hole_d", "drawn", "printed", "fit", "overlap_mm", "text"}],
    tightest first, at most MAX_ROWS (the rest counted in "more" of the
    last row). ({"skipped": reason} alone when there are too many faces.)"""
    cyl = []
    for p in parts:
        cyl += cylinders(p["shape"], p["label"])
        if len(cyl) > MAX_CYLINDERS:
            return [{"skipped": "%d round faces" % len(cyl)}]
    pins = [c for c in cyl if not c["hole"]]
    holes = [c for c in cyl if c["hole"]]
    if not pins or not holes:
        return []
    shrink = atech_fit.value("hole_shrink")
    HA = np.array([h["a"] for h in holes])
    HC = np.array([h["c"] for h in holes])
    HR = np.array([h["r"] for h in holes])
    HT0 = np.array([h["t0"] for h in holes])
    HT1 = np.array([h["t1"] for h in holes])
    seen = {}
    for pin in pins:
        par = np.abs(HA @ pin["a"]) >= PARALLEL
        gap = 2 * (HR - pin["r"])
        ok = par & (gap >= -0.6) & (gap <= FIT_MAX)
        if not ok.any():
            continue
        rel = pin["c"] - HC
        off = np.linalg.norm(rel - (np.einsum("ij,ij->i", rel, HA))[:, None] * HA, axis=1)
        ok &= off <= AXIS_TOL
        for i in np.nonzero(ok)[0]:
            h = holes[i]
            if h["label"] == pin["label"]:
                continue
            # the pin's ends in the hole's axial coordinate
            sgn = 1.0 if float(HA[i] @ pin["a"]) > 0 else -1.0
            base = float((pin["c"] - HC[i]) @ HA[i])
            e0, e1 = base + sgn * pin["t0"], base + sgn * pin["t1"]
            over = min(max(e0, e1), HT1[i]) - max(min(e0, e1), HT0[i])
            if over < OVERLAP_MIN:
                continue
            key = (pin["label"], h["label"], round(2 * pin["r"], 2), round(2 * h["r"], 2))
            if key not in seen or over > seen[key]:
                seen[key] = float(over)
    rows = []
    for (pl, hl, pd, hd), over in seen.items():
        drawn = round(hd - pd, 2)
        printed = round(drawn - shrink, 2)
        word = atech_fit.fit_word(printed)
        rows.append({"pin": pl, "hole": hl, "pin_d": pd, "hole_d": hd, "drawn": drawn,
                     "printed": printed, "fit": word, "overlap_mm": round(over, 1),
                     "text": "%s in %s: a %g pin in a %g hole, %g clear as drawn, about %g "
                             "once printed: %s" % (pl, hl, pd, hd, drawn, printed, word)})
    rows.sort(key=lambda r: (r["printed"], r["pin"], r["hole"]))
    more = len(rows) - MAX_ROWS
    rows = rows[:MAX_ROWS]
    if more > 0 and rows:
        rows[-1]["more"] = more
    return rows


def lines(motor_rows, pin_rows):
    """The FIT lines ./check prints."""
    out = ["FIT " + r["text"] for r in motor_rows]
    for r in pin_rows:
        if r.get("skipped"):
            out.append("FIT pins in holes: not judged (%s)" % r["skipped"])
            continue
        out.append("FIT " + r["text"] + (" (and %d more pairs)" % r["more"]
                                         if r.get("more") else ""))
    return out
