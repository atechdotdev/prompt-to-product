"""p2p_print - can it be printed, on which Bambu printer, how long (R1120).

Before Bambu Studio is opened (or where it is not installed: ./check, the
product pack, a share), this plans the print from the parts alone:

    plan(parts, brief=None)     the print plan (below)
    markdown(p)                 for the product pack
    check_line(p)               one PRINT line for ./check

parts = [{"label", "count", "size_mm": [x, y, z], "volume_cm3", "colour",
          "area_mm2" (optional)}]
(count defaults to 1; colour may be ""). Grams: skin + 15 % infill, as
shop.print_grams.

plan = {
  "parts": [{"label", "count", "flat_mm", "smallest": key | None,
             "printers": [keys], "tall": bool, "notes": [...]}],
  "printers": [{"key", "name", "fits": bool, "plates": n | None,
                "hours": float | None, "too_big": [labels]}],
  "best": key | None,          # the smallest printer every part fits
  "grams": float, "by_colour": {"black": g, ...}, "colours": n,
  "ams": "none" | "ams" | "more than 4 colours",
  "material": {"name": "PLA", "why": "..."},
  "advice": ["..."],
}

Time and grams are rough, before slicing, and labelled so: the slicer's
numbers win (the Print step and the share pack slice for real). Python
3.9+, stdlib only.
"""
import math

import p2p_printers as P

PLA_DENSITY = 1.24          # g/cm3 (export_tools.PLA_DENSITY)
#: Grams per hour a printer of this class lays down on a typical part at
#: Bambu's standard 0.20 mm profile - a planning figure, not a measurement.
#: The slicer's time always wins.
GRAMS_PER_HOUR = {"a1mini": 14.0, "a1": 16.0, "p1s": 20.0, "p2s": 22.0, "x1c": 20.0,
                  "h2s": 24.0, "h2d": 24.0}
SPACING = 6.0               # mm between parts on a plate (Bambu's arrange ~6)
FILAMENT_MARGIN = 1.1       # purge, brim, a failed first layer (share.FILAMENT_MARGIN)
#: A part taller than this many times its smallest footprint side may tip
#: over while printing: add a brim.
TALL_RATIO = 3.0
AMS_SLOTS = 4
#: shop.py's filament model (R850): about 1 mm of solid skin over the
#: surface, 15 % infill inside. A part's solid mass would overstate a case
#: several times over.
SKIN_MM = 1.0
INFILL = 0.15


def print_grams(volume_cm3, area_mm2=None, size_mm=None):
    """About how many grams a part prints with (shop.print_grams). No area
    given: the bounding box's surface stands in (rough, says so)."""
    vol = max(0.0, float(volume_cm3 or 0)) * 1000.0
    if area_mm2 is None:
        x, y, z = [float(v or 0) for v in (size_mm or (0, 0, 0))][:3]
        area_mm2 = 2 * (x * y + y * z + x * z)
    skin = min(vol, max(0.0, float(area_mm2)) * SKIN_MM)
    return (skin + INFILL * (vol - skin)) * PLA_DENSITY / 1000.0


def _flat(size):
    return P.lay_flat(size)


def pack_plates(footprints, bed, margin=P.MARGIN, spacing=SPACING):
    """How many plates the footprints [(w, d)] take on bed (w, d, h):
    first-fit-decreasing shelves (each part may turn 90 degrees). Returns
    the plate count, or None when one part does not fit at all. A plan,
    not Bambu's arrange: it is never better than the real one by more
    than a plate."""
    W, D = bed[0] - 2 * margin, bed[1] - 2 * margin
    items = []
    for w, d in footprints:
        if max(w, d) <= W and min(w, d) <= D:
            w, d = (max(w, d), min(w, d))        # long side along X
        elif w <= W and d <= D:
            pass
        elif d <= W and w <= D:
            w, d = d, w
        else:
            return None
        items.append((w, d))
    items.sort(key=lambda t: (-t[1], -t[0]))
    plates = []                                  # each: list of shelves [y_used, x_used, h]
    for w, d in items:
        placed = False
        for shelves in plates:
            for sh in shelves:
                if d <= sh[2] and sh[1] + w <= W + 1e-9:
                    sh[1] += w + spacing
                    placed = True
                    break
            if placed:
                break
            used = sum(sh[2] + spacing for sh in shelves)
            if used + d <= D + 1e-9:
                shelves.append([used, w + spacing, d])
                placed = True
                break
        if not placed:
            plates.append([[0.0, w + spacing, d]])
    return len(plates)


def material(brief):
    places = set((brief or {}).get("places") or [])
    if "outdoor" in places or "car" in places:
        return {"name": "PETG or ASA", "why": "PLA softens in the sun and in a hot car"}
    if "wet" in places:
        return {"name": "PETG", "why": "PETG takes water and soap better than PLA"}
    if "kitchen" in places:
        return {"name": "PETG", "why": "it takes warm water; no printed part is food-safe "
                "without a food-safe coating"}
    return {"name": "PLA", "why": "easy to print and stiff enough indoors"}


def plan(parts, brief=None):
    rows, grams, by_colour = [], 0.0, {}
    footprints = []
    for p in parts or []:
        n = int(p.get("count") or 1)
        size = [float(v or 0) for v in (p.get("size_mm") or [0, 0, 0])][:3]
        flat = _flat(size)
        fits = [x["key"] for x in P.printers_for(size)]
        tall = flat[2] > TALL_RATIO * max(1e-6, min(flat[0], flat[1]))
        notes = []
        if not fits:
            notes.append("too big for every Bambu bed laid flat (%s mm): split it"
                         % " x ".join("%g" % round(v) for v in flat))
        if tall and flat[2] > 30:
            notes.append("tall and thin: print it with a brim so it does not tip over")
        g = print_grams(p.get("volume_cm3"), p.get("area_mm2"), size) * n
        grams += g
        col = (p.get("colour") or "any colour").strip() or "any colour"
        by_colour[col] = by_colour.get(col, 0.0) + g
        rows.append({"label": p.get("label") or "part", "count": n,
                     "flat_mm": [round(v, 1) for v in flat],
                     "smallest": fits[0] if fits else None, "printers": fits,
                     "tall": tall, "notes": notes, "grams": round(g, 1)})
        footprints += [(flat[0], flat[1])] * n
    printers = []
    for key, name, bed in P.PRINTERS:
        too_big = [r["label"] for r in rows if key not in r["printers"]]
        plates = pack_plates(footprints, bed) if not too_big and footprints else None
        hours = round(grams * FILAMENT_MARGIN / GRAMS_PER_HOUR[key], 1) \
            if not too_big and grams else None
        printers.append({"key": key, "name": name, "fits": not too_big, "plates": plates,
                         "hours": hours, "too_big": too_big})
    best = next((p["key"] for p in printers if p["fits"]), None) if rows else None
    named = [c for c in by_colour if c != "any colour"]
    ncol = len(named)
    ams = "none" if ncol <= 1 else ("ams" if ncol <= AMS_SLOTS else "more than 4 colours")
    mat = material(brief)
    advice = []
    if best is None and rows:
        advice.append("At least one part is too big for every Bambu printer: split it "
                      "(Edit part > Split) or scale the design down.")
    if ams == "ams":
        advice.append("%d colours: print with an AMS (A1/A1 mini: AMS lite), or print "
                      "each colour's parts on its own." % ncol)
    elif ams == "more than 4 colours":
        advice.append("%d colours is more than one AMS holds (4): group the parts by "
                      "colour and print in batches." % ncol)
    if any(r["tall"] and r["flat_mm"][2] > 30 for r in rows):
        advice.append("A tall part: turn on a brim in the slicer.")
    if mat["name"] != "PLA":
        advice.append("Print in %s: %s." % (mat["name"], mat["why"]))
    q = int((brief or {}).get("quantity") or 1)
    if q > 1 and best:
        b = [p for p in printers if p["key"] == best][0]
        advice.append("%d copies: about %d plates and %.0f h on the %s (rough)."
                      % (q, (b["plates"] or 1) * q, (b["hours"] or 0) * q, b["name"]))
    return {"parts": rows, "printers": printers, "best": best,
            "grams": round(grams * FILAMENT_MARGIN, 1),
            "by_colour": {k: round(v * FILAMENT_MARGIN, 1) for k, v in by_colour.items()},
            "colours": ncol, "ams": ams, "material": mat, "advice": advice,
            "quantity": q}


def _name(key):
    p = P.by_key(key)
    return p["name"] if p else key


def check_line(p):
    if not p["parts"]:
        return None
    if p["best"] is None:
        big = [r["label"] for r in p["parts"] if not r["printers"]]
        return ("PRINT too big for every Bambu bed: %s (split it or scale it; a note, not "
                "a gate)" % ", ".join(big))
    b = [x for x in p["printers"] if x["key"] == p["best"]][0]
    return ("PRINT fits the %s and up: %d plate%s, about %g g of %s, roughly %g h before "
            "slicing%s" % (b["name"], b["plates"] or 1, "" if (b["plates"] or 1) == 1 else "s",
                           round(p["grams"]), p["material"]["name"], b["hours"] or 0,
                           "; %d colours (AMS)" % p["colours"] if p["ams"] == "ams" else ""))


def markdown(p):
    L = ["## Print plan", "",
         "Rough, before slicing: the slicer's time and grams win.", ""]
    if p["best"]:
        L.append("- **Smallest printer that takes every part:** %s" % _name(p["best"]))
    L.append("- **Filament:** about %g g (%s)" % (round(p["grams"]), ", ".join(
        "%s %g g" % (c, round(g)) for c, g in sorted(p["by_colour"].items()))))
    L.append("- **Material:** %s (%s)" % (p["material"]["name"], p["material"]["why"]))
    L += ["", "| Printer | Fits | Plates | Time (rough) |", "|---|---|---|---|"]
    for x in p["printers"]:
        L.append("| %s | %s | %s | %s |" % (
            x["name"], "yes" if x["fits"] else "no: " + ", ".join(x["too_big"]),
            x["plates"] if x["plates"] else "-", ("%g h" % x["hours"]) if x["hours"] else "-"))
    L += ["", "| Part | # | Laid flat (mm) | Smallest printer | Notes |", "|---|---|---|---|---|"]
    for r in p["parts"]:
        L.append("| %s | %d | %s | %s | %s |" % (
            r["label"], r["count"], " x ".join("%g" % v for v in r["flat_mm"]),
            _name(r["smallest"]) if r["smallest"] else "none", "; ".join(r["notes"])))
    if p["advice"]:
        L += ["", "### Advice", ""] + ["- " + a for a in p["advice"]]
    return "\n".join(L) + "\n"


def parts_from_check(res):
    """./check's result -> parts (size and volume per object)."""
    out = []
    for f in res.get("objects") or []:
        if f.get("error") or not f.get("size"):
            continue
        out.append({"label": f.get("label"), "count": 1, "size_mm": list(f["size"])[:3],
                    "volume_cm3": float(f.get("volume_mm3") or 0) / 1000.0, "colour": ""})
    return out


def hours_text(h):
    if h is None:
        return "-"
    m = int(round(h * 60))
    return "%d h %02d min" % (m // 60, m % 60) if m >= 60 else "%d min" % m


def ceil_div(a, b):
    return int(math.ceil(float(a) / b))
