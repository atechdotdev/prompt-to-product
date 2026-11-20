"""p2p_printers - Bambu Lab printers and what fits on them (R1110, R1120).

The build volumes are Bambu Lab's published ones (mm, single nozzle). The
app's Print step reads the real bed from the installed Bambu Studio
profile (print_plates._bed); this table is for the places with no Bambu
Studio: ./check, the brief's acceptance, the product pack.

    PRINTERS                 [(key, name, (w, d, h))], smallest first
    fits(size, bed)          a part of size (x, y, z) laid on its biggest
                             face fits the bed (turned 90 degrees if need be)
    printers_for(size)       the printers it fits, smallest first
    smallest(size)           the smallest printer it fits, or None

Python 3.9+, stdlib only.
"""

#: (key, name, (width, depth, height) mm). Bambu Lab's spec pages.
PRINTERS = [
    ("a1mini", "Bambu Lab A1 mini", (180.0, 180.0, 180.0)),
    ("a1", "Bambu Lab A1", (256.0, 256.0, 256.0)),
    ("p1s", "Bambu Lab P1S", (256.0, 256.0, 256.0)),
    ("p2s", "Bambu Lab P2S", (256.0, 256.0, 256.0)),
    ("x1c", "Bambu Lab X1 Carbon", (256.0, 256.0, 256.0)),
    ("h2s", "Bambu Lab H2S", (340.0, 320.0, 340.0)),
    ("h2d", "Bambu Lab H2D", (325.0, 320.0, 325.0)),
]
#: mm kept clear at the bed edge (print_plates.BED_MARGIN is the same idea)
MARGIN = 5.0


def by_key(key):
    for k, n, bed in PRINTERS:
        if k == key or n == key:
            return {"key": k, "name": n, "bed": bed}
    return None


def lay_flat(size):
    """(x, y, z) of a part laid on its biggest face: the two largest
    dimensions on the bed, the smallest up. The Print step lays parts on
    their flat side; this is the box that needs."""
    s = sorted(float(v or 0) for v in size)
    return (s[2], s[1], s[0])


def fits(size, bed, margin=MARGIN, flat=True):
    """True when a part of size fits bed (w, d, h). flat: lay it on its
    biggest face first (the default); else as modelled, turned 90 degrees
    about Z when that fits."""
    x, y, z = lay_flat(size) if flat else tuple(float(v or 0) for v in size)
    w, d, h = bed[0] - 2 * margin, bed[1] - 2 * margin, bed[2]
    if z > h:
        return False
    return (x <= w and y <= d) or (y <= w and x <= d)


def printers_for(size, flat=True):
    return [{"key": k, "name": n, "bed": bed} for k, n, bed in PRINTERS
            if fits(size, bed, flat=flat)]


def smallest(size, flat=True):
    got = printers_for(size, flat)
    return got[0] if got else None


def largest_bed():
    return max((bed for _k, _n, bed in PRINTERS), key=lambda b: b[0] * b[1] * b[2])
