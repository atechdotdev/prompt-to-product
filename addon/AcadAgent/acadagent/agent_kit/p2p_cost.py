"""p2p_cost - what the product costs to make, and what to buy (R1130).

The share pack (share.bill) already splits a design into what is printed,
what comes from Atech and what is bought. This puts money and exact sizes
on it:

    screw_spec(name)           "M3x8 screw" -> {"thread": "M3", "length": 8, ...}
    buy_list(bill)             what to buy, with exact sizes, merged by spec
    screw_types(rows)          the distinct screw specs (one type is the goal)
    costs(bill, prices, quote, quantity)   the cost sheet (below)
    markdown(c) / csv_text(c)  for the product pack

prices (the user's, ~/Documents/Atech Products/prices.json, all optional):
  {"currency": "SEK", "filament_per_kg": 229, "buy": {"M3x8 screw": 1.5},
   "sell_price": 499}

No price is invented. A line with no price says "not known" and how to get
one; the filament falls back to a labelled planning figure (PLANNING_PER_KG)
only when the user set none, and the sheet says so. The Atech total comes
from the site's own quote (shop.quote) when the app could ask it.
Python 3.9+, stdlib only.
"""
import csv
import io
import json
import os
import re

PRICES_FILE = "prices.json"
#: A planning figure when the user set no filament price: a typical 1 kg
#: PLA spool in US dollars. Labelled wherever it is used; set your own.
PLANNING_PER_KG = {"currency": "USD", "amount": 20.0}

SCREW_RE = re.compile(
    r"(?i)\b(M\d+(?:\.\d+)?)\s*(?:[x×*]\s*(\d+(?:\.\d+)?)\s*(?:mm)?)?")
KIND_RE = re.compile(r"(?i)\b(screws?|bolts?|nuts?|washers?|inserts?|standoffs?|"
                     r"magnets?|bearings?|springs?|o-?rings?|rods?|dowels?)\b")
HEAD_RE = re.compile(r"(?i)\b(countersunk|flat head|button head|socket head|pan head|"
                     r"cap head|self[- ]tapping|wood screw|heat[- ]set)\b")


def _singular(w):
    w = w.lower()
    return w[:-1] if w.endswith("s") and not w.endswith("ss") else w


def screw_spec(name, note=""):
    """{"kind", "thread", "length", "head", "spec"} from a part's name and
    note ("M3x8 screw", "Screw_M2_5x6", "Heat-set insert M3"); spec is
    the exact words to buy ("M3 x 8 mm screw, socket head"). None when
    the name names no fastener."""
    text = re.sub(r"_", " ", "%s %s" % (name or "", note or ""))
    text = re.sub(r"(?i)\bM(\d) (\d)x", r"M\1.\2x", text)        # M2 5x6 -> M2.5x6
    k = KIND_RE.search(text)
    if not k:
        return None
    kind = _singular(k.group(1))
    m = SCREW_RE.search(text)
    thread = m.group(1).upper() if m else None
    length = float(m.group(2)) if m and m.group(2) else None
    h = HEAD_RE.search(text)
    head = h.group(1).lower() if h else None
    bits = []
    if thread:
        bits.append(thread + (" x %g mm" % length if length else ""))
    bits.append(kind)
    spec = " ".join(bits) + (", %s" % head if head else "")
    dims = None
    if not thread:
        d = re.search(r"(\d+(?:\.\d+)?)\s*(?:mm)?\s*[x\u00d7]\s*(\d+(?:\.\d+)?)"
                      r"(?:\s*[x\u00d7]\s*(\d+(?:\.\d+)?))?\s*(?:mm)?", name or "")
        if d:
            dims = [float(v) for v in d.groups() if v]
            spec += ", %s mm" % " x ".join("%g" % v for v in dims)
    return {"kind": kind, "thread": thread, "length": length, "head": head, "spec": spec,
            "dims": dims}


def buy_list(bill):
    """[{"spec", "count", "note", "exact": bool, "kind"}] from share.bill's
    "buy" rows, merged by spec. exact: thread and length (or a non-screw
    with its size in the note) are known."""
    out, by = [], {}
    for r in (bill or {}).get("buy") or []:
        sp = screw_spec(r.get("name"), r.get("note"))
        if sp:
            key = sp["spec"]
            exact = bool(sp["thread"] and (sp["length"] or sp["kind"] in ("nut", "washer",
                                                                            "insert"))) \
                or bool(sp["dims"]) or (not sp["thread"] and sp["kind"] not in (
                    "screw", "bolt", "nut", "washer", "insert")
                    and bool(re.search(r"\d", r.get("note") or "")))
            kind = sp["kind"]
        else:
            key = r.get("name") or "part"
            exact = bool(re.search(r"\d", (r.get("note") or "") + key))
            kind = "other"
        if key in by:
            by[key]["count"] += int(r.get("count") or 1)
            continue
        row = {"spec": key, "count": int(r.get("count") or 1), "note": r.get("note") or "",
               "exact": exact, "kind": kind, "name": r.get("name")}
        by[key] = row
        out.append(row)
    return out


def screw_types(rows):
    """The distinct screw/bolt specs (thread + length) in a buy list."""
    seen = []
    for r in rows:
        if r["kind"] in ("screw", "bolt") and r["spec"] not in seen:
            seen.append(r["spec"])
    return seen


def screw_advice(rows):
    types = screw_types(rows)
    if len(types) <= 1:
        return None
    use = {}
    for r in rows:
        if r["kind"] in ("screw", "bolt") and r["spec"][:1] == "M":
            t = r["spec"].split(" ")[0]
            use[t] = use.get(t, 0) + r["count"]
    threads = sorted(use, key=lambda t: (-use[t], t)) or sorted(
        {t.split(" ")[0] for t in types})
    if len(threads) == 1:
        return ("%d screw types (%s). One length could do for all: the longest that "
                "every hole takes." % (len(types), ", ".join(types)))
    return ("%d screw types (%s) in %d threads. One type for the whole product is "
            "easier to buy and build: ask the agent to use %s throughout where it fits."
            % (len(types), ", ".join(types), len(threads), threads[0]))


# ------------------------------------------------------------------ prices
def load_prices(folder):
    try:
        with open(os.path.join(folder, PRICES_FILE), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save_prices(folder, prices):
    os.makedirs(folder, exist_ok=True)
    p = os.path.join(folder, PRICES_FILE)
    with open(p + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(prices, fh, indent=2, ensure_ascii=False)
    os.replace(p + ".tmp", p)
    return p


def _money(amount, currency):
    if amount is None:
        return "not known"
    return "%s %s" % (("%.2f" % amount).rstrip("0").rstrip(".") if amount < 100
                      else "{:,.0f}".format(amount), currency)


def costs(bill, prices=None, quote=None, quantity=1, grams=None):
    """The cost sheet:
    {"currency", "lines": [{"section", "item", "count", "unit", "total",
     "source"}], "known_total", "unknown": [items], "batch_total", "margin": {...} | None, "planning": bool, "notes": [...]}.
    grams: the print plan's filament (p2p_print, skin + infill); else the
    bill's solid grams."""
    prices = prices or {}
    lines, unknown, notes = [], [], []
    cur = prices.get("currency")
    # filament
    fil = (bill or {}).get("filament") or []
    total_g = grams if grams is not None else sum(f["grams"] for f in fil)
    per_kg = prices.get("filament_per_kg")
    planning = False
    if per_kg is None:
        per_kg = PLANNING_PER_KG["amount"]
        fcur = PLANNING_PER_KG["currency"]
        planning = True
        notes.append("Filament at %s/kg is a planning figure (a typical PLA spool): set "
                     "your own price in %s." % (_money(per_kg, fcur), PRICES_FILE))
    else:
        fcur = cur or "?"
    if total_g:
        lines.append({"section": "Print", "item": "Filament, about %g g" % round(total_g),
                      "count": 1, "unit": None, "total": round(total_g / 1000.0 * per_kg, 2),
                      "currency": fcur,
                      "source": "planning figure" if planning else "your price"})
    # Atech
    atech = (bill or {}).get("atech") or []
    if atech:
        if quote and quote.get("total"):
            amt = quote["total"].get("amount")
            qc = quote.get("currency") or cur
            lines.append({"section": "Atech", "item": "Board, modules and cables (%d lines)"
                          % len(atech), "count": 1, "unit": None,
                          "total": float(amt) if amt is not None else None, "currency": qc,
                          "source": "atech.dev quote"})
            if quote.get("unknown"):
                unknown += ["%s (no price on atech.dev)" % u for u in quote["unknown"]]
        else:
            lines.append({"section": "Atech", "item": "Board, modules and cables (%d lines)"
                          % len(atech), "count": 1, "unit": None, "total": None,
                          "currency": cur, "source": "open the cart on atech.dev"})
            unknown.append("the Atech parts (ask atech.dev for a quote: Get it made)")
    # bought
    bp = prices.get("buy") or {}
    for r in buy_list(bill):
        unit = bp.get(r["spec"], bp.get(r.get("name") or "", None))
        lines.append({"section": "Buy", "item": r["spec"], "count": r["count"],
                      "unit": unit, "total": round(unit * r["count"], 2) if unit is not None
                      else None, "currency": cur, "source": "your price" if unit is not None
                      else "not known"})
        if unit is None:
            unknown.append(r["spec"])
    currencies = {ln["currency"] for ln in lines if ln["total"] is not None}
    if len(currencies) > 1:
        notes.append("Prices in more than one currency (%s): the total adds only %s."
                     % (", ".join(sorted(c or "?" for c in currencies)), cur or fcur))
    main = cur or fcur
    known = round(sum(ln["total"] for ln in lines if ln["total"] is not None
                      and ln["currency"] == main), 2)
    # quantity: filament and bought parts scale; Atech scales too (no
    # volume price is assumed - the site quotes it)
    margin = None
    sell = prices.get("sell_price")
    if sell is not None and not unknown:
        margin = {"sell": float(sell), "cost": known, "profit": round(float(sell) - known, 2),
                  "percent": round(100.0 * (float(sell) - known) / float(sell), 1)
                  if float(sell) else None}
    elif sell is not None:
        notes.append("A margin needs every price: %d not known." % len(unknown))
    return {"currency": main, "lines": lines, "known_total": known, "unknown": unknown,
            "quantity": int(quantity or 1),
            "batch_total": round(known * int(quantity or 1), 2), "margin": margin,
            "planning": planning, "notes": notes,
            "screw_types": screw_types(buy_list(bill)),
            "screw_advice": screw_advice(buy_list(bill))}


def markdown(c):
    L = ["## What it costs", ""]
    L += ["| Section | Item | # | Unit | Total | From |", "|---|---|---|---|---|---|"]
    for ln in c["lines"]:
        L.append("| %s | %s | %d | %s | %s | %s |" % (
            ln["section"], ln["item"], ln["count"],
            _money(ln["unit"], ln["currency"] or "") if ln["unit"] is not None else "",
            _money(ln["total"], ln["currency"] or ""), ln["source"]))
    L += ["", "**Known so far:** %s per product%s." % (
        _money(c["known_total"], c["currency"] or ""),
        (" (%d x: %s)" % (c["quantity"], _money(c["batch_total"], c["currency"] or "")))
        if c["quantity"] > 1 else "")]
    if c["unknown"]:
        L += ["", "**Not known yet:** " + "; ".join(c["unknown"]) + "."]
    if c["margin"]:
        m = c["margin"]
        L += ["", "**At %s:** %s profit per product (%s %%)." % (
            _money(m["sell"], c["currency"] or ""), _money(m["profit"], c["currency"] or ""),
            m["percent"])]
    if c["screw_advice"]:
        L += ["", "**Screws:** " + c["screw_advice"]]
    for n in c["notes"]:
        L += ["", "_%s_" % n]
    return "\n".join(L) + "\n"


def shopping_md(bill):
    """What to buy, exact sizes first; a row without a size says so."""
    rows = buy_list(bill)
    if not rows:
        return "## To buy\n\nNothing: everything is printed or comes from Atech.\n"
    L = ["## To buy", ""]
    for r in rows:
        L.append("- [ ] %d x %s%s%s" % (r["count"], r["spec"],
                                        " (%s)" % r["note"] if r["note"] else "",
                                        "" if r["exact"] else " - size not in the model: "
                                        "measure the hole before buying"))
    adv = screw_advice(rows)
    if adv:
        L += ["", adv]
    return "\n".join(L) + "\n"


def csv_text(c):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["Section", "Item", "Count", "Unit price", "Total", "Currency", "From"])
    for ln in c["lines"]:
        w.writerow([ln["section"], ln["item"], ln["count"],
                    "" if ln["unit"] is None else ln["unit"],
                    "" if ln["total"] is None else ln["total"], ln["currency"] or "",
                    ln["source"]])
    w.writerow(["", "Known total", "", "", c["known_total"], c["currency"] or "", ""])
    return buf.getvalue()
