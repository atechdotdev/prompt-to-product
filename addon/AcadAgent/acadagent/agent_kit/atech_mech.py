"""atech_mech - strength by hand, before anybody trusts the geometry (R1290).

The closed-form checks of Gustav's partsmith (mech_calcs.py, materials.py,
2026-08-30), carried over as they are for the cases a printed product has: a
cantilever (a clip arm, a bracket), a simply supported strip (a lid, a
shelf), a snap hook's strain, a pin in double shear, a pin bearing on a
printed hole, a bolt as a stub axle, and a press fit's interference. "The
kind a mechanical engineer does on a napkin": first-order numbers, not FEA.

    import atech_mech as mech
    r = mech.cantilever("clip arm", F=5, L=12, b=6, h=1.6, material="PLA")
    print(r)        # stress_MPa, deflection_mm, allowable, sf, ok

Every function returns a dict with the load, the governing stress or strain,
the allowable, the safety factor `sf`, the one asked for (`sf_required`)
and `ok`. Units: N, mm, MPa.

THE MATERIAL NUMBERS ARE TYPICAL DATA-SHEET VALUES FOR FDM PARTS AT 0.2 mm
LAYERS. None of them is verified on a printer (partsmith says the same).
They tell a part that is ten times too weak from one that is plausible;
they do not prove a part. A load across the layers (direction="z") gets
the Z knock-down, the usual place a print breaks.

selftest() checks each formula against a textbook case, so a later change
cannot quietly break one. Plain Python, no FreeCAD.
"""
import math

#:   E            tensile modulus, MPa
#:   uts_xy       ultimate tensile strength in the layer plane, MPa
#:   z_knockdown  multiply strengths for loads across layers (Z direction)
#:   yield_frac   design "yield" as a fraction of UTS
#:   snap_strain  most strain a snap or flexure is designed for
#:   tg_c         glass transition, deg C (a part in a car or at a lamp)
ALLOWABLES = {
    "PLA":  {"E": 2400.0, "uts_xy": 55.0, "z_knockdown": 0.60, "yield_frac": 0.80,
             "elong_pct": 3.0, "snap_strain": 0.02, "tg_c": 60,
             "source": "Prusament PLA data sheet (typical), read 2026-08-30; unverified"},
    "PETG": {"E": 1500.0, "uts_xy": 47.0, "z_knockdown": 0.70, "yield_frac": 0.80,
             "elong_pct": 8.0, "snap_strain": 0.04, "tg_c": 80,
             "source": "Prusament PETG data sheet (typical), read 2026-08-30; unverified"},
    "ASA":  {"E": 1700.0, "uts_xy": 40.0, "z_knockdown": 0.70, "yield_frac": 0.80,
             "elong_pct": 6.0, "snap_strain": 0.03, "tg_c": 100,
             "source": "Prusament ASA data sheet (typical); unverified"},
    "TPU":  {"E": 60.0, "uts_xy": 30.0, "z_knockdown": 0.80, "yield_frac": 0.50,
             "elong_pct": 400.0, "snap_strain": 0.20, "tg_c": -20,
             "source": "generic 95A TPU data sheet; unverified"},
}

#: bought parts used as structure
BOUGHT = {
    "steel_bolt_4.8": {"E": 200000.0, "yield": 320.0, "uts": 400.0,
                       "source": "ISO 898-1 class 4.8"},
    "pla_filament_pin_1.75": {"E": 2400.0, "uts": 55.0, "shear": 33.0,
                              "note": "extruded filament, no layers"},
}

SAFETY_FACTORS = {
    "static": 2.0,   # sustained loads (its own weight, a preload)
    "impact": 3.0,   # repeated knocks (a wheel on a kerb, a button pressed hard)
    "drop": 1.5,     # the one fall it must survive: it may yield, not break
}

#: ISO metric coarse thread, minor diameter (mm): where a bolt bends
MINOR_D = {"M2": 1.567, "M2.5": 2.013, "M3": 2.459, "M4": 3.242, "M5": 4.134}


def _mat(name):
    try:
        return ALLOWABLES[str(name).upper()]
    except KeyError:
        raise ValueError("atech_mech: no data for %r (have: %s)"
                         % (name, ", ".join(sorted(ALLOWABLES))))


def allowable_stress(name, direction="xy", mode="tension"):
    """Design allowable in MPa: UTS x yield_frac, x the Z knock-down for a
    load across the layers (direction="z"), x 0.6 in shear."""
    a = _mat(name)
    s = a["uts_xy"] * a["yield_frac"]
    if str(direction).lower() == "z":
        s *= a["z_knockdown"]
    if mode == "shear":
        s *= 0.6
    return s


def _result(name, load, value, unit, allowable, sf_required, **extra):
    sf = (allowable / value) if value > 0 else float("inf")
    out = {"case": name, "load_N": round(load, 3), unit: round(value, 4),
           "allowable": round(allowable, 3), "sf": round(sf, 2),
           "sf_required": sf_required, "ok": sf >= sf_required}
    out.update(extra)
    return out


def cantilever(name, F, L, b, h, material="PLA", direction="xy",
               sf_required=SAFETY_FACTORS["static"]):
    """A beam b wide and h deep (in the bending direction) fixed at one end,
    load F at its tip L away: stress F L / (b h^2 / 6), tip deflection
    F L^3 / (3 E I)."""
    E = _mat(material)["E"]
    I = b * h ** 3 / 12.0
    Z = b * h ** 2 / 6.0
    sigma = F * L / Z
    delta = F * L ** 3 / (3 * E * I)
    return _result(name, F, sigma, "stress_MPa", allowable_stress(material, direction),
                   sf_required, deflection_mm=round(delta, 3), L_mm=L, section_mm=[b, h],
                   direction=direction)


def ss_beam(name, F, L, b, h, material="PLA", direction="xy", uniform=True,
            stress_factor=1.0, sf_required=SAFETY_FACTORS["static"]):
    """A strip b x h resting on both ends over span L: M = F L / 8 for a
    load F spread along it, F L / 4 at its middle. stress_factor carries a
    concentration (a window's corner)."""
    E = _mat(material)["E"]
    I = b * h ** 3 / 12.0
    Z = b * h ** 2 / 6.0
    M = F * L / (8.0 if uniform else 4.0)
    sigma = stress_factor * M / Z
    delta = (5.0 * F * L ** 3 / (384 * E * I)) if uniform else (F * L ** 3 / (48 * E * I))
    return _result(name, F, sigma, "stress_MPa", allowable_stress(material, direction),
                   sf_required, deflection_mm=round(delta, 3), L_mm=L, section_mm=[b, h],
                   stress_factor=stress_factor, direction=direction)


def snap_strain(name, deflection, L, t, material="PLA"):
    """A snap hook or flexure of thickness t and length L bent `deflection`
    at its tip: strain 1.5 x deflection x t / L^2 (the formula
    cad.snap_fit_cantilever uses)."""
    eps = 1.5 * deflection * t / L ** 2
    allow = _mat(material)["snap_strain"]
    return _result(name, 0.0, eps, "strain", allow, 1.0, deflection_mm=deflection, L_mm=L,
                   t_mm=t)


def pin_double_shear(name, F, d, pin="pla_filament_pin_1.75",
                     sf_required=SAFETY_FACTORS["impact"]):
    """A pin of diameter d held on both sides of the part that loads it."""
    tau = F / (2 * math.pi * d ** 2 / 4.0)
    p = BOUGHT[pin]
    allow = p.get("shear", 0.6 * p.get("yield", p.get("uts", 0)))
    return _result(name, F, tau, "stress_MPa", allow, sf_required, d_mm=d, pin=pin)


def bearing(name, F, d, t, material="PLA", direction="xy",
            sf_required=SAFETY_FACTORS["impact"]):
    """A pin of diameter d pressing on a printed hole in a wall t thick:
    F / (d t), allowable about 1.5 x tension."""
    sigma = F / (d * t)
    return _result(name, F, sigma, "stress_MPa", 1.5 * allowable_stress(material, direction),
                   sf_required, d_mm=d, t_mm=t, direction=direction)


def bolt_cantilever(name, F, L, size="M3", grade="steel_bolt_4.8", threaded=True,
                    sf_required=SAFETY_FACTORS["impact"]):
    """A bolt as a stub axle, load F at L from where it is held: it bends
    at its thread's minor diameter (threaded=True)."""
    d = MINOR_D[size] if threaded else float(size[1:])
    Z = math.pi * d ** 3 / 32.0
    sigma = F * L / Z
    return _result(name, F, sigma, "stress_MPa", BOUGHT[grade]["yield"], sf_required,
                   L_mm=L, d_mm=d, threaded=threaded)


def press_fit(name, d_shaft, d_bore, material="PLA"):
    """A shaft pressed into a printed hole, AS PRINTED sizes: a screen, not
    a prediction. The interference strain against the material's yield
    strain: over about 5 % the hub may split; between yield and 5 % the
    fit holds by local yielding and relaxes with time."""
    a = _mat(material)
    delta = d_shaft - d_bore
    eps = delta / d_shaft
    eps_y = a["uts_xy"] * a["yield_frac"] / a["E"]
    verdict = ("clearance - nothing holds it" if delta <= 0 else
               "light elastic fit" if eps < eps_y else
               "holds by local yielding (normal for a printed press fit)" if eps <= 0.05 else
               "the hub may split: interference strain over 5 %")
    return {"case": name, "interference_mm": round(delta, 3), "strain": round(eps, 4),
            "yield_strain": round(eps_y, 4), "allowable": 0.05,
            "sf": round(0.05 / eps, 2) if eps > 0 else float("inf"), "sf_required": 1.0,
            "ok": 0 < eps <= 0.05, "verdict": verdict}


def selftest():
    """Textbook checks; a list of failures (empty = pass)."""
    fails = []
    # 10 N at 100 mm on 10 x 10: Z = 166.67 -> 6 MPa
    r = cantilever("t", 10.0, 100.0, 10.0, 10.0, "PLA")
    if abs(r["stress_MPa"] - 6.0) > 1e-6:
        fails.append("cantilever stress %s" % r["stress_MPa"])
    exp = 10.0 * 100 ** 3 / (3 * 2400.0 * (10 * 10 ** 3 / 12))
    if abs(r["deflection_mm"] - round(exp, 3)) > 1e-3:
        fails.append("cantilever deflection")
    if r["allowable"] != 44.0 or r["sf"] != round(44.0 / 6.0, 2) or not r["ok"]:
        fails.append("cantilever allowable")
    if abs(cantilever("t", 10.0, 100.0, 10.0, 10.0, "PLA", "z")["allowable"] - 26.4) > 1e-9:
        fails.append("z knock-down")
    if abs(pin_double_shear("t", 100.0, 2.0)["stress_MPa"] - 100 / (2 * math.pi)) > 1e-3:
        fails.append("pin shear")
    if abs(bearing("t", 10.0, 2.0, 5.0, "PLA")["stress_MPa"] - 1.0) > 1e-9:
        fails.append("bearing")
    if abs(snap_strain("t", 1.0, 10.0, 1.0, "PLA")["strain"] - 0.015) > 1e-9:
        fails.append("snap strain")
    # 10 N at 10 mm on an M3's minor diameter 2.459
    r = bolt_cantilever("t", 10.0, 10.0, "M3")
    if abs(r["stress_MPa"] - 100.0 / (math.pi * 2.459 ** 3 / 32)) > 1e-3:
        fails.append("bolt cantilever")
    # 3.0 shaft in a 2.9 bore: 3.3 %, yields, ok; 2.8: 6.7 %, may split; 3.2: clearance
    if not press_fit("t", 3.0, 2.9)["ok"] or press_fit("t", 3.0, 2.8)["ok"] \
            or press_fit("t", 3.0, 3.2)["ok"]:
        fails.append("press fit screen")
    # uniform 80 N over 20 mm on 30 x 2: M = 200, Z = 20 -> 10 MPa
    if abs(ss_beam("t", 80.0, 20.0, 30.0, 2.0, "PLA")["stress_MPa"] - 10.0) > 1e-6:
        fails.append("ss beam")
    # the same at the middle: M = 400 -> 20 MPa
    if abs(ss_beam("t", 80.0, 20.0, 30.0, 2.0, "PLA", uniform=False)["stress_MPa"] - 20.0) > 1e-6:
        fails.append("ss beam centre load")
    return fails
