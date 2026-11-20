"""share - Share a design: one folder with everything, ready to send or
upload (R1040).

One button (the view bar's Share, Atech menu > Share...) makes

    ~/Documents/Prompt2Product/Shared/<design>/
        <Design> 3D.html          the design in 3D: turn it, pull it apart,
                                  click a part; the parts list, the shopping
                                  list and the files in tabs. One file, no
                                  internet needed (its own small WebGL viewer).
        <Design> - print-ready <printer>.3mf
                                  the Bambu Studio project, sliced (plates,
                                  time, grams): what MakerWorld asks for as
                                  the print profile; only with Bambu Studio
        <Design>.3mf              every printed part laid flat, any slicer
        parts/                    one STL per part, and <Design>.step
        BOM.csv                   print / Atech / buy, one table
        shopping-list.md          filament per colour, Atech modules with
                                  their shop links, the parts to buy
        assembly.md               how it goes together (product.assembly)
        electrical/, firmware/    when the design has Atech electronics
        cover.png                 the share picture (with a 3D view)
        description.txt           MakerWorld's form, ready to paste
        LICENCE.txt               the licence and the credits it carries
        MESSAGE.txt               the message for the person, ready to paste
        README.md                 what each file is
        <Design> - share.zip      all of the above in one file
        share.json                what was made, when (and marks the folder
                                  as ours: making it again replaces it)

The licence checks are MakerWorld's (makerworld.publish_plan): a part
whose licence forbids sharing stops the pack. Atech's board and module
models are not in the files (they are not the user's to share); the 3D
page shows them as plain labelled boxes.

Then the window sends it where it goes: Post to atech.dev (post.py, the
picture and the text filled in), Upload to MakerWorld (the folder shown,
the description copied, the upload page opened: MakerWorld has no upload
API), Send to someone (the zip shown, MESSAGE.txt copied).

bill, bom_csv, shopping_md, message, viewer_html and make_share are
headless (make_share needs FreeCAD; the others plain Python).
"""
import base64
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from array import array

SHARE_ENV = "P2P_SHARE_DIR"
MARKER = "share.json"
#: Parts the user buys, not prints, when the model has them by name.
BUY_RE = re.compile(r"(?i)(?<![a-z])(screws?|bolts?|nuts?|washers?|inserts?|magnets?|"
                    r"bearings?|springs?|o-?rings?|standoffs?|rods?|dowels?)(?![a-z])")
MAX_TRIANGLES = 400000
FILAMENT_MARGIN = 1.1


def _log(msg):
    try:
        import FreeCAD
        FreeCAD.Console.PrintLog("Atech share: %s\n" % msg)
    except Exception:                                     # noqa: BLE001
        sys.stderr.write("Atech share: %s\n" % msg)


def share_root():
    return os.environ.get(SHARE_ENV) or os.path.join(
        os.path.expanduser("~"), "Documents", "Prompt2Product", "Shared")


def safe_name(text):
    s = re.sub(r"[^\w .()-]+", "_", text or "").strip(" ._")
    return s[:80] or "Design"


def _plural(n, word):
    return "%d %s%s" % (n, word, "" if n == 1 else "s")


def duration(seconds):
    m = int(round((seconds or 0) / 60.0))
    h, m = divmod(m, 60)
    return ("%d h %02d min" % (h, m)) if h else ("%d min" % m)


# ===================================================================
# the bill: print / Atech / buy
# ===================================================================
def _spec(key):
    """atech_modules.spec(key) or {} (a user or shelf part has user: True)."""
    try:
        from . import projects
        d = projects._builder_dir()
        if d and d not in sys.path:
            sys.path.insert(0, d)
        import atech_modules
        return atech_modules.specs().get(key) or {}
    except Exception:                                     # noqa: BLE001
        return {}


def bill(bom, spec_fn=None, objects=None):
    """Split export_tools.bom() into what a person does with each line:
    {"print": [{"part","count","colour","mass_g"}],
     "atech": [{"name","count","ports","url"}],          (board, modules, cables)
     "buy":   [{"name","count","note"}],                 (user / shelf parts, and
                                                          modelled screws, nuts...)
     "filament": [{"colour","grams"}]}.
    spec_fn(key) -> the module's spec; objects {label: obj} for sizes."""
    from . import shop
    spec_fn = spec_fn or _spec
    objects = objects or {}
    out = {"print": [], "atech": [], "buy": [], "filament": []}
    buy = {}

    def add_buy(name, count, note=""):
        if name in buy:
            buy[name]["count"] += count
        else:
            buy[name] = {"name": name, "count": count, "note": note}
            out["buy"].append(buy[name])

    grams = {}
    for r in bom.get("printed") or []:
        if BUY_RE.search(r["part"].replace("_", " ")):
            o = objects.get(r["names"][0]) if r.get("names") else None
            add_buy(r["part"].replace("_", " "), r["count"], _size_note(o))
            continue
        out["print"].append({"part": r["part"], "count": r["count"],
                             "colour": r.get("colour") or "", "mass_g": r["mass_g"]})
        c = r.get("colour") or "any colour"
        grams[c] = grams.get(c, 0.0) + r["mass_g"] * r["count"]
    out["filament"] = [{"colour": c, "grams": round(g, 1)}
                       for c, g in sorted(grams.items(), key=lambda kv: -kv[1])]
    atech = {}
    for r in bom.get("hardware") or []:
        key = r.get("key") or ""
        if r["kind"] == "Module":
            sp = spec_fn(key) if key else {}
            if sp.get("user"):
                add_buy(sp.get("display_name") or r["name"], 1,
                        sp.get("notes") or sp.get("source") or "")
                continue
        if r["kind"] == "Cable":
            name = "Ribbon cable, %g mm" % r["length_mm"] if r.get("length_mm") else r["name"]
        else:
            name = r["name"]
        if name in atech:
            atech[name]["count"] += 1
            if r.get("ports"):
                atech[name]["ports"] += ", " + r["ports"]
            continue
        url = shop.SHOP if r["kind"] == "Cable" else shop.module_url(key)
        if r["kind"] == "Board":
            url = shop.module_url(shop.BOARD)
        atech[name] = {"name": name, "count": 1, "ports": r.get("ports") or "",
                       "url": url, "kind": r["kind"], "key": key}
        out["atech"].append(atech[name])
    return out


def _size_note(o):
    """'about 3.0 x 3.0 x 10.0 mm (measured from the model)' or ''."""
    try:
        bb = o.Shape.BoundBox
        a = sorted((bb.XLength, bb.YLength, bb.ZLength))
        return "about %.1f x %.1f x %.1f mm (measured from the model)" % tuple(a)
    except Exception:                                     # noqa: BLE001
        return ""


def bom_from_doc(doc, colours=None):
    """export_tools.bom(doc), with each module row's library key added."""
    from . import export_tools
    b = export_tools.bom(doc, colours=colours)
    for r in b["hardware"]:
        o = doc.getObject(r.get("label") or "") if hasattr(doc, "getObject") else None
        if o is None:
            for x in getattr(doc, "Objects", []):
                if getattr(x, "Label", None) == r.get("label"):
                    o = x
                    break
        if o is not None:
            r["key"] = getattr(o, "AtechModule", "") or ""
    return b


def bom_csv(b):
    import csv
    import io
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["What to do", "Item", "Count", "Colour", "Filament (g)", "Ports",
                "Where to get it", "Notes"])
    for r in b["print"]:
        w.writerow(["Print", r["part"], r["count"], r["colour"], "%.1f" % r["mass_g"],
                    "", "", ""])
    for r in b["atech"]:
        w.writerow(["Atech", r["name"], r["count"], "", "", r["ports"], r["url"], ""])
    for r in b["buy"]:
        w.writerow(["Buy", r["name"], r["count"], "", "", "", "", r["note"]])
    return buf.getvalue()


def colour_label(c):
    """'Sky PLA', or 'PLA, colour #cccce6' when the colour has no name."""
    c = c or ""
    if not c or c == "any colour":
        return "PLA, any colour"
    return "PLA, colour %s" % c if c.startswith("#") else "%s PLA" % c.capitalize()


def filament(b, plates=None):
    """[{"colour", "grams", "sliced"}]: the slicer's grams split over the
    colours by volume when the plates were sliced; else the parts' solid
    mass (an upper bound: a slicer's infill makes it much less)."""
    rows = b.get("filament") or []
    total = sum(f["grams"] for f in rows)
    if plates and plates.get("ok") and plates.get("grams") and total > 0:
        return [{"colour": f["colour"], "grams": round(plates["grams"] * f["grams"] / total, 1),
                 "sliced": True} for f in rows]
    return [dict(f, sliced=False) for f in rows]


def filament_line(fil):
    if not fil:
        return ""
    g = sum(f["grams"] for f in fil)
    return ("about %.0f g of PLA" % g) if fil[0]["sliced"] else (
        "up to %.0f g of PLA (solid; the slicer's infill makes it less)" % g)


def shopping_md(title, b, plates=None):
    """The shopping list for a person: filament, Atech, the rest."""
    from . import shop
    L = ["# %s: shopping list" % title, ""]
    L += ["## Filament", ""]
    fil = filament(b, plates)
    if fil:
        for f in fil:
            if f["grams"] < 1.0:
                L.append("- %s: under 1 g (a little left on a spool will do)"
                         % colour_label(f["colour"]))
                continue
            L.append("- %s: %s%.0f g (have %.0f g or more, for the purge and the brim)"
                     % (colour_label(f["colour"]), "" if f["sliced"] else "up to ",
                        f["grams"], f["grams"] * FILAMENT_MARGIN))
        if plates and plates.get("ok"):
            L.append("- Bambu Studio's estimate for the print-ready file: %s, %.0f g, %s."
                     % (_plural(len(plates["plates"]), "plate"), plates["grams"],
                        duration(plates["seconds"])))
        else:
            L.append("- These are the solid parts' weights: with the slicer's infill a "
                     "print takes much less.")
    else:
        L.append("- Nothing to print.")
    L += ["", "## Atech", ""]
    if b["atech"]:
        for r in b["atech"]:
            L.append("- %s%s%s: %s" % ("%d x " % r["count"] if r["count"] > 1 else "",
                                       r["name"], (" (port %s)" % r["ports"]) if r["ports"]
                                       else "", r["url"]))
        mods = [r for r in b["atech"] if r["kind"] == "Module"]
        if mods:
            L.append("")
            L.append("All of it in one cart: %s" % shop.cart_url(
                [m["key"] or m["name"] for m in mods for _n in range(m["count"])], board=any(
                    r["kind"] == "Board" for r in b["atech"])))
    else:
        L.append("- No Atech electronics.")
    L += ["", "## Buy", ""]
    if b["buy"]:
        for r in b["buy"]:
            L.append("- %d x %s%s" % (r["count"], r["name"], (": " + r["note"]) if r["note"]
                                      else ""))
    else:
        L.append("- Nothing else: everything is printed.")
    return "\n".join(L) + "\n"


# ===================================================================
# the 3D page
# ===================================================================
def _b64(arr):
    return base64.b64encode(arr.tobytes()).decode("ascii")


def _box_mesh(bb):
    """24 vertices / 12 triangles: a box with sharp edges."""
    x0, y0, z0, x1, y1, z1 = bb
    faces = (((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)),
             ((x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)),
             ((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)),
             ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)),
             ((x0, y1, z1), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1)),
             ((x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)))
    pos, idx = array("f"), array("I")
    for q in faces:
        base = len(pos) // 3
        for p in q:
            pos.extend(p)
        idx.extend((base, base + 1, base + 2, base, base + 2, base + 3))
    return pos, idx


def mesh_parts(doc, max_triangles=MAX_TRIANGLES, colours=None):
    """[{"name", "colour" '#rrggbb', "kind" print|atech|buy, "pos" array f,
    "idx" array I}] for every visible top-level part. Atech's board and
    modules are their bounding boxes (their models are not ours to hand on)."""
    from . import export_tools as et
    objs, _left = et.export_targets(doc, "product", None, include_atech=True)
    diag = 1.0
    for o in objs:
        try:
            diag = max(diag, o.Shape.BoundBox.DiagonalLength)
        except Exception:                                 # noqa: BLE001
            pass
    tol = max(0.02, diag / 1500.0)
    for _try in range(6):
        out, total = [], 0
        for o in objs:
            c, _t = et.object_colour(o, colours)
            hexc = et.hex_colour(c) if c else "#b8bcc4"
            role = getattr(o, "AtechRole", None)
            kind = "atech" if role in ("board", "module") else (
                "buy" if BUY_RE.search((o.Label or "").replace("_", " ")) else "print")
            try:
                if role in ("board", "module"):
                    bb = o.Shape.BoundBox if hasattr(o, "Shape") else o.Mesh.BoundBox
                    pos, idx = _box_mesh((bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax))
                    hexc = "#2f7d5b" if role == "board" else "#3d4450"
                elif et._is_mesh(o):
                    pts, tris = o.Mesh.Topology
                    pos = array("f", [v for p in pts for v in (p.x, p.y, p.z)])
                    idx = array("I", [i for t in tris for i in t])
                else:
                    pts, tris = o.Shape.tessellate(tol)
                    pos = array("f", [v for p in pts for v in (p.x, p.y, p.z)])
                    idx = array("I", [i for t in tris for i in t])
            except Exception as exc:                      # noqa: BLE001
                _log("mesh %s: %r" % (o.Label, exc))
                continue
            if not idx:
                continue
            total += len(idx) // 3
            out.append({"name": o.Label, "colour": hexc, "kind": kind, "pos": pos, "idx": idx})
        if total <= max_triangles:
            return out
        tol *= 2.0
    return out


def viewer_html(title, parts, b=None, files=(), meta=None):
    """One self-contained page: the 3D view and the tabs. parts from
    mesh_parts(); b from bill(); files [(relative path, what)]; meta
    {"summary", "licence", "made_with", "when"}."""
    import html as _h
    meta = dict(meta or {})
    data = {
        "title": title,
        "parts": [{"n": p["name"], "c": p["colour"], "k": p["kind"],
                   "p": _b64(p["pos"]), "i": _b64(p["idx"])} for p in parts],
        "bill": b or {"print": [], "atech": [], "buy": [], "filament": []},
        "files": [{"path": f, "what": w} for f, w in files],
        "meta": meta,
    }
    js = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    return (VIEWER.replace("__TITLE__", _h.escape(title))
            .replace("__SUMMARY__", _h.escape(meta.get("summary") or ""))
            .replace("__DATA__", js))


VIEWER = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#f4f2ee;--panel:#ffffff;--ink:#1d1f23;--dim:#6b6f78;--line:#e2dfd8;
--accent:#e8672c;--chip:#f0ede6;--canvas1:#fbfaf7;--canvas2:#e9e6df}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#15171a;
--panel:#1e2125;--ink:#eceae6;--dim:#9a9ea6;--line:#2f3338;--accent:#f07a44;
--chip:#272a2f;--canvas1:#24272c;--canvas2:#15171a}}
:root[data-theme="dark"]{--bg:#15171a;--panel:#1e2125;--ink:#eceae6;--dim:#9a9ea6;
--line:#2f3338;--accent:#f07a44;--chip:#272a2f;--canvas1:#24272c;--canvas2:#15171a}
*{box-sizing:border-box}html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--ink);font:14px/1.45 -apple-system,BlinkMacSystemFont,
"Segoe UI",Inter,Roboto,sans-serif;display:flex;flex-direction:column}
header{display:flex;align-items:baseline;gap:14px;padding:14px 20px;border-bottom:1px solid var(--line);
background:var(--panel);flex-wrap:wrap}
header h1{font-size:18px;margin:0;font-weight:650}header p{margin:0;color:var(--dim)}
main{flex:1;display:flex;min-height:0}
#stage{position:relative;flex:1;min-width:0;background:radial-gradient(ellipse at 50% 35%,
var(--canvas1),var(--canvas2))}
canvas{width:100%;height:100%;display:block;touch-action:none;cursor:grab}
canvas:active{cursor:grabbing}
.bar{position:absolute;left:12px;right:12px;top:12px;display:flex;gap:6px;flex-wrap:wrap;
align-items:center;pointer-events:none}
.bar>*{pointer-events:auto}
button,.chip{font:inherit;font-size:13px;border:1px solid var(--line);background:var(--panel);
color:var(--ink);border-radius:999px;padding:5px 12px;cursor:pointer}
button:hover{border-color:var(--accent)}button.on{background:var(--accent);color:#fff;
border-color:var(--accent)}
.chip{display:flex;gap:8px;align-items:center;cursor:default}
input[type=range]{accent-color:var(--accent);width:110px}
#pick{position:absolute;left:12px;bottom:12px;background:var(--panel);border:1px solid var(--line);
border-radius:10px;padding:6px 10px;display:none;max-width:70%}
#hint{position:absolute;right:12px;bottom:12px;color:var(--dim);font-size:12px}
aside{width:360px;max-width:100%;background:var(--panel);border-left:1px solid var(--line);
display:flex;flex-direction:column;min-height:0}
nav{display:flex;border-bottom:1px solid var(--line)}
nav button{flex:1;border:0;border-radius:0;background:none;padding:10px 4px;color:var(--dim);
border-bottom:2px solid transparent}
nav button.on{color:var(--ink);background:none;border-bottom-color:var(--accent)}
.tab{display:none;overflow:auto;padding:12px 16px;flex:1}.tab.on{display:block}
h3{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--dim);margin:14px 0 6px}
ul{list-style:none;margin:0;padding:0}
.row{display:flex;align-items:center;gap:10px;padding:6px 4px;border-radius:8px;cursor:pointer}
.row:hover,.row.sel{background:var(--chip)}
.sw{width:14px;height:14px;border-radius:4px;flex:none;border:1px solid rgba(0,0,0,.15)}
.row .n{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.k{font-size:11px;color:var(--dim)}
table{width:100%;border-collapse:collapse}td{padding:5px 4px;border-bottom:1px solid var(--line);
vertical-align:top}td.num{text-align:right;white-space:nowrap;color:var(--dim)}
a{color:var(--accent)}code{font-size:12px}
.files li{padding:6px 0;border-bottom:1px solid var(--line)}
.small{color:var(--dim);font-size:12px}
#nogl{display:none;position:absolute;inset:0;align-items:center;justify-content:center;
color:var(--dim);padding:20px;text-align:center}
@media (max-width:760px){main{flex-direction:column}#stage{flex:none;height:62vh}
aside{width:100%;border-left:0;border-top:1px solid var(--line)}header{padding:12px 16px}#hint{display:none}}
</style></head><body>
<header><h1>__TITLE__</h1><p>__SUMMARY__</p></header>
<main>
<div id="stage"><canvas id="c" aria-label="3D view of the design"></canvas>
<div class="bar">
<button data-v="iso" class="on">3D</button><button data-v="front">Front</button>
<button data-v="right">Side</button><button data-v="top">Top</button>
<span class="chip">Apart <input id="ex" type="range" min="0" max="100" value="0"
aria-label="Pull the parts apart"></span>
<button id="spin">Spin</button>
</div>
<div id="pick"></div><div id="hint">Drag to turn &middot; right-drag or two fingers to move &middot; scroll to zoom</div>
<div id="nogl">This browser can't show 3D (WebGL is off). The parts and files are on the right.</div>
</div>
<aside>
<nav><button data-t="parts" class="on">Parts</button><button data-t="shop">Shopping list</button>
<button data-t="files">Files</button></nav>
<div class="tab on" id="t-parts"><ul id="plist"></ul>
<p class="small">Click a part to find it. Untick to hide it.</p></div>
<div class="tab" id="t-shop"></div>
<div class="tab" id="t-files"></div>
</aside></main>
<script>
const D=__DATA__;
const $=s=>document.querySelector(s);
function dec(s,T){const b=atob(s),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return new T(u.buffer)}
function hex(h){h=h.replace('#','');return[0,2,4].map(i=>parseInt(h.substr(i,2),16)/255)}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
// ---------------------------------------------------------------- side panel
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{
 document.querySelectorAll('nav button,.tab').forEach(x=>x.classList.remove('on'));
 b.classList.add('on');$('#t-'+b.dataset.t).classList.add('on')});
const B=D.bill;let shop='';
if(B.filament.length){shop+='<h3>Filament</h3><table>'+B.filament.map(f=>'<tr><td>'+esc(f.colour)+'</td><td class="num">'+(f.grams<1?'under 1':(f.sliced?'':'up to ')+Math.round(f.grams))+' g</td></tr>').join('')+'</table>'+
 (B.filament[0].sliced?'':'<p class="small">Solid weights: with the slicer\'s infill a print takes much less.</p>')}
if(D.meta.plates)shop+='<p class="small">'+esc(D.meta.plates)+'</p>';
shop+='<h3>Print</h3><table>'+(B.print.map(r=>'<tr><td>'+(r.count>1?r.count+' &times; ':'')+esc(r.part)+'<div class="k">'+esc(r.colour)+'</div></td><td class="num">'+r.mass_g+' g</td></tr>').join('')||'<tr><td>Nothing to print.</td></tr>')+'</table>';
if(B.atech.length)shop+='<h3>Atech</h3><table>'+B.atech.map(r=>'<tr><td>'+(r.count>1?r.count+' &times; ':'')+'<a href="'+esc(r.url)+'" target="_blank" rel="noopener">'+esc(r.name)+'</a>'+(r.ports?'<div class="k">port '+esc(r.ports)+'</div>':'')+'</td></tr>').join('')+'</table>';
shop+='<h3>Buy</h3><table>'+(B.buy.map(r=>'<tr><td>'+r.count+' &times; '+esc(r.name)+(r.note?'<div class="k">'+esc(r.note)+'</div>':'')+'</td></tr>').join('')||'<tr><td>Nothing else: everything is printed.</td></tr>')+'</table>';
$('#t-shop').innerHTML=shop;
$('#t-files').innerHTML='<ul class="files">'+D.files.map(f=>'<li><a href="'+encodeURI(f.path)+'">'+esc(f.path)+'</a><div class="k">'+esc(f.what)+'</div></li>').join('')+'</ul>'+
 (D.meta.licence?'<h3>Licence</h3><p>'+esc(D.meta.licence)+'</p>':'')+
 '<p class="small">'+esc(D.meta.made_with||'')+(D.meta.when?'<br>'+esc(D.meta.when):'')+'</p>';
// ---------------------------------------------------------------- GL
const cv=$('#c');
let gl=cv.getContext('webgl2',{antialias:true})||cv.getContext('webgl',{antialias:true});
if(gl&&!(typeof WebGL2RenderingContext!=='undefined'&&gl instanceof WebGL2RenderingContext)&&!gl.getExtension('OES_element_index_uint'))gl=null;
const KIND={print:'',atech:'Atech',buy:'buy'};
const P=D.parts.map((p,i)=>{const pos=dec(p.p,Float32Array),idx=dec(p.i,Uint32Array);
 const nrm=new Float32Array(pos.length);
 for(let t=0;t<idx.length;t+=3){const a=idx[t]*3,b=idx[t+1]*3,c=idx[t+2]*3;
  const ux=pos[b]-pos[a],uy=pos[b+1]-pos[a+1],uz=pos[b+2]-pos[a+2],vx=pos[c]-pos[a],vy=pos[c+1]-pos[a+1],vz=pos[c+2]-pos[a+2];
  const nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;for(const k of[a,b,c]){nrm[k]+=nx;nrm[k+1]+=ny;nrm[k+2]+=nz}}
 let mn=[1e9,1e9,1e9],mx=[-1e9,-1e9,-1e9];for(let k=0;k<pos.length;k+=3)for(let j=0;j<3;j++){mn[j]=Math.min(mn[j],pos[k+j]);mx[j]=Math.max(mx[j],pos[k+j])}
 return{i,name:p.n,col:hex(p.c),hexc:p.c,kind:p.k,pos,nrm,idx,n:idx.length,mn,mx,ctr:[0,1,2].map(j=>(mn[j]+mx[j])/2),show:true}});
let MN=[1e9,1e9,1e9],MX=[-1e9,-1e9,-1e9];P.forEach(p=>{for(let j=0;j<3;j++){MN[j]=Math.min(MN[j],p.mn[j]);MX[j]=Math.max(MX[j],p.mx[j])}});
if(!P.length){MN=[-10,-10,0];MX=[10,10,20]}
const CTR=[0,1,2].map(j=>(MN[j]+MX[j])/2),RAD=Math.max(1,Math.hypot(MX[0]-MN[0],MX[1]-MN[1],MX[2]-MN[2])/2);
// parts list
const pl=$('#plist');
P.forEach(p=>{const li=document.createElement('li');li.className='row';
 li.innerHTML='<input type="checkbox" checked aria-label="Show '+esc(p.name)+'"><span class="sw" style="background:'+p.hexc+'"></span><span class="n">'+esc(p.name)+'</span><span class="k">'+KIND[p.kind]+'</span>';
 li.querySelector('input').onclick=e=>{e.stopPropagation();p.show=e.target.checked;draw()};
 li.onclick=()=>select(p.i===sel?-1:p.i);p.li=li;pl.appendChild(li)});
let sel=-1;
function select(i){sel=i;P.forEach(p=>p.li.classList.toggle('sel',p.i===i));
 const box=$('#pick');if(i<0){box.style.display='none'}else{const p=P[i];box.style.display='block';
 box.innerHTML='<b>'+esc(p.name)+'</b> <span class="k">'+(KIND[p.kind]||'printed')+' &middot; '+[0,1,2].map(j=>(p.mx[j]-p.mn[j]).toFixed(1)).join(' &times; ')+' mm</span>';
 p.li.scrollIntoView({block:'nearest'})}draw()}
if(!gl){$('#nogl').style.display='flex';cv.style.display='none'}
else{
const VS='attribute vec3 p;attribute vec3 n;uniform mat4 M;uniform vec3 off;varying vec3 vn;varying vec3 vw;void main(){vec3 w=p+off;vw=w;vn=n;gl_Position=M*vec4(w,1.);}';
const FS='precision highp float;varying vec3 vn;varying vec3 vw;uniform vec3 col;uniform vec3 eye;uniform float hi;uniform float dim;'+
'void main(){vec3 N=normalize(vn);vec3 V=normalize(eye-vw);if(dot(N,V)<0.)N=-N;vec3 L1=normalize(vec3(.45,-.65,1.));vec3 L2=normalize(vec3(-.8,.5,.25));'+
'float sky=.5+.5*N.z;vec3 amb=mix(vec3(.24,.23,.22),vec3(.42,.44,.48),sky);float d1=max(dot(N,L1),0.);float d2=max(dot(N,L2),0.);'+
'vec3 H=normalize(L1+V);float sp=pow(max(dot(N,H),0.),40.)*.22;float rim=pow(1.-max(dot(N,V),0.),3.)*.12;'+
'vec3 c=col*(amb+d1*.62+d2*.18)+vec3(sp+rim);c=mix(c,vec3(1.,.5,.15),hi*.45);c=mix(c,vec3(.6),dim*.55);gl_FragColor=vec4(c,1.);}';
const GVS='attribute vec3 p;uniform mat4 M;varying vec2 q;void main(){q=p.xy;gl_Position=M*vec4(p,1.);}';
const GFS='precision highp float;varying vec2 q;uniform vec2 c;uniform vec2 r;void main(){vec2 d=(q-c)/r;float a=1.-smoothstep(.2,1.,length(d));gl_FragColor=vec4(0.,0.,0.,a*.22);}';
const IFS='precision highp float;uniform vec3 col;void main(){gl_FragColor=vec4(col,1.);}';
function sh(t,s){const o=gl.createShader(t);gl.shaderSource(o,s);gl.compileShader(o);return o}
function prog(v,f){const o=gl.createProgram();gl.attachShader(o,sh(gl.VERTEX_SHADER,v));gl.attachShader(o,sh(gl.FRAGMENT_SHADER,f));gl.linkProgram(o);return o}
const PR=prog(VS,FS),PI=prog(VS,IFS),PG=prog(GVS,GFS);
function buf(t,a){const b=gl.createBuffer();gl.bindBuffer(t,b);gl.bufferData(t,a,gl.STATIC_DRAW);return b}
P.forEach(p=>{p.bp=buf(gl.ARRAY_BUFFER,p.pos);p.bn=buf(gl.ARRAY_BUFFER,p.nrm);p.bi=buf(gl.ELEMENT_ARRAY_BUFFER,p.idx)});
const gz=MN[2]-RAD*.002,gr=RAD*1.6;
const gb=buf(gl.ARRAY_BUFFER,new Float32Array([CTR[0]-gr,CTR[1]-gr,gz,CTR[0]+gr,CTR[1]-gr,gz,CTR[0]+gr,CTR[1]+gr,gz,CTR[0]-gr,CTR[1]-gr,gz,CTR[0]+gr,CTR[1]+gr,gz,CTR[0]-gr,CTR[1]+gr,gz]));
// camera
const cam={yaw:-Math.PI/3,pitch:.5,dist:RAD*3.2,t:CTR.slice()};let goal=null;
function eyeOf(c){const cp=Math.cos(c.pitch);return[c.t[0]+c.dist*cp*Math.cos(c.yaw),c.t[1]+c.dist*cp*Math.sin(c.yaw),c.t[2]+c.dist*Math.sin(c.pitch)]}
function sub(a,b){return[a[0]-b[0],a[1]-b[1],a[2]-b[2]]}function cr(a,b){return[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]}
function nz(a){const l=Math.hypot(a[0],a[1],a[2])||1;return[a[0]/l,a[1]/l,a[2]/l]}function dt(a,b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]}
function mvp(){const e=eyeOf(cam),f=nz(sub(cam.t,e)),s=nz(cr(f,[0,0,1])),u=cr(s,f);
 const V=[s[0],u[0],-f[0],0,s[1],u[1],-f[1],0,s[2],u[2],-f[2],0,-dt(s,e),-dt(u,e),dt(f,e),1];
 const asp=cv.width/Math.max(1,cv.height),fy=1/Math.tan(.3),n=Math.max(.1,cam.dist-RAD*4),fr=cam.dist+RAD*4;
 const Pm=[fy/asp,0,0,0,0,fy,0,0,0,0,(fr+n)/(n-fr),-1,0,0,2*fr*n/(n-fr),0];
 const M=new Float32Array(16);for(let i=0;i<4;i++)for(let j=0;j<4;j++){let v=0;for(let k=0;k<4;k++)v+=Pm[k*4+j]*V[i*4+k];M[i*4+j]=v}return{M,e,s,u}}
let ex=0;
function off(p){const k=ex*1.1;return[(p.ctr[0]-CTR[0])*k,(p.ctr[1]-CTR[1])*k,(p.ctr[2]-CTR[2])*k*1.4]}
function bindPart(pg,p){let l=gl.getAttribLocation(pg,'p');gl.bindBuffer(gl.ARRAY_BUFFER,p.bp);gl.enableVertexAttribArray(l);gl.vertexAttribPointer(l,3,gl.FLOAT,false,0,0);
 l=gl.getAttribLocation(pg,'n');if(l>=0){gl.bindBuffer(gl.ARRAY_BUFFER,p.bn);gl.enableVertexAttribArray(l);gl.vertexAttribPointer(l,3,gl.FLOAT,false,0,0)}
 gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,p.bi)}
function u(pg,n){return gl.getUniformLocation(pg,n)}
let fb=null,fbt=null,fbr=null,fbw=0,fbh=0;
function render(pick){const{M,e}=mvp();gl.viewport(0,0,cv.width,cv.height);
 gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);
 if(!pick){gl.useProgram(PG);gl.uniformMatrix4fv(u(PG,'M'),false,M);gl.uniform2f(u(PG,'c'),CTR[0],CTR[1]);
  gl.uniform2f(u(PG,'r'),(MX[0]-MN[0])*(.7+ex*.8)+RAD*.2,(MX[1]-MN[1])*(.7+ex*.8)+RAD*.2);
  gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.depthMask(false);
  const l=gl.getAttribLocation(PG,'p');gl.bindBuffer(gl.ARRAY_BUFFER,gb);gl.enableVertexAttribArray(l);gl.vertexAttribPointer(l,3,gl.FLOAT,false,0,0);
  gl.drawArrays(gl.TRIANGLES,0,6);gl.depthMask(true);gl.disable(gl.BLEND);gl.disableVertexAttribArray(1)}
 const pg=pick?PI:PR;gl.useProgram(pg);gl.uniformMatrix4fv(u(pg,'M'),false,M);
 if(!pick)gl.uniform3fv(u(pg,'eye'),e);
 P.forEach(p=>{if(!p.show)return;bindPart(pg,p);gl.uniform3fv(u(pg,'off'),off(p));
  if(pick){gl.uniform3f(u(pg,'col'),((p.i+1)&255)/255,(((p.i+1)>>8)&255)/255,0)}
  else{gl.uniform3fv(u(pg,'col'),p.col);gl.uniform1f(u(pg,'hi'),p.i===sel?1:0);gl.uniform1f(u(pg,'dim'),sel>=0&&p.i!==sel?1:0)}
  gl.drawElements(gl.TRIANGLES,p.n,gl.UNSIGNED_INT,0)});
 for(let k=0;k<3;k++)gl.disableVertexAttribArray(k)}
let pend=false;function draw(){if(!pend){pend=true;requestAnimationFrame(()=>{pend=false;tick()})}}
function tick(){if(goal){let done=true;for(const k of['yaw','pitch','dist']){const d=goal[k]-cam[k];if(Math.abs(d)>1e-3){cam[k]+=d*.18;done=false}else cam[k]=goal[k]}
 for(let j=0;j<3;j++){const d=goal.t[j]-cam.t[j];if(Math.abs(d)>1e-3*RAD){cam.t[j]+=d*.18;done=false}else cam.t[j]=goal.t[j]}if(done)goal=null}
 if(spin&&!drag){cam.yaw+=.006}render(false);if(goal||spin)draw()}
function size(){const r=cv.getBoundingClientRect(),dp=Math.min(2,window.devicePixelRatio||1);cv.width=Math.max(1,r.width*dp|0);cv.height=Math.max(1,r.height*dp|0);draw()}
window.addEventListener('resize',size);size();
function pickAt(x,y){const w=cv.width,h=cv.height;if(!fb||fbw!==w||fbh!==h){fb=gl.createFramebuffer();fbt=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,fbt);
 gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,w,h,0,gl.RGBA,gl.UNSIGNED_BYTE,null);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);
 fbr=gl.createRenderbuffer();gl.bindRenderbuffer(gl.RENDERBUFFER,fbr);gl.renderbufferStorage(gl.RENDERBUFFER,gl.DEPTH_COMPONENT16,w,h);
 gl.bindFramebuffer(gl.FRAMEBUFFER,fb);gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,fbt,0);
 gl.framebufferRenderbuffer(gl.FRAMEBUFFER,gl.DEPTH_ATTACHMENT,gl.RENDERBUFFER,fbr);fbw=w;fbh=h}
 gl.bindFramebuffer(gl.FRAMEBUFFER,fb);render(true);const px=new Uint8Array(4);gl.readPixels(x,h-y-1,1,1,gl.RGBA,gl.UNSIGNED_BYTE,px);
 gl.bindFramebuffer(gl.FRAMEBUFFER,null);const id=px[0]+(px[1]<<8)-1;select(px[3]>0&&id>=0&&id<P.length?id:-1)}
// input
let drag=null,spin=false;const pts=new Map();
cv.addEventListener('contextmenu',e=>e.preventDefault());
cv.addEventListener('pointerdown',e=>{cv.setPointerCapture(e.pointerId);pts.set(e.pointerId,[e.clientX,e.clientY]);goal=null;
 drag={x:e.clientX,y:e.clientY,b:e.button,pan:e.button===2||e.shiftKey,moved:0}});
cv.addEventListener('pointermove',e=>{if(!drag||!pts.has(e.pointerId))return;const prev=pts.get(e.pointerId);pts.set(e.pointerId,[e.clientX,e.clientY]);
 const dx=e.clientX-prev[0],dy=e.clientY-prev[1];drag.moved+=Math.abs(dx)+Math.abs(dy);
 if(pts.size===2){const[a,b]=[...pts.values()];const d=Math.hypot(a[0]-b[0],a[1]-b[1]);if(drag.pd)cam.dist=Math.min(RAD*20,Math.max(RAD*.3,cam.dist*drag.pd/d));drag.pd=d;pan(dx/2,dy/2)}
 else if(drag.pan)pan(dx,dy);else{cam.yaw-=dx*.008;cam.pitch=Math.max(-1.5,Math.min(1.5,cam.pitch+dy*.008))}draw()});
function pan(dx,dy){const{s,u:uu}=mvp(),k=cam.dist*.0016*(window.devicePixelRatio||1);for(let j=0;j<3;j++)cam.t[j]+=(-s[j]*dx+uu[j]*dy)*k}
function up(e){pts.delete(e.pointerId);if(drag&&pts.size===0){if(drag.moved<4&&e.type==='pointerup'){const r=cv.getBoundingClientRect(),dp=cv.width/r.width;pickAt((e.clientX-r.left)*dp|0,(e.clientY-r.top)*dp|0)}drag=null}}
cv.addEventListener('pointerup',up);cv.addEventListener('pointercancel',up);
cv.addEventListener('wheel',e=>{e.preventDefault();goal=null;cam.dist=Math.min(RAD*20,Math.max(RAD*.3,cam.dist*Math.exp(e.deltaY*.0015)));draw()},{passive:false});
const VIEWS={iso:[-Math.PI/3,.5],front:[-Math.PI/2,.02],right:[0,.02],top:[-Math.PI/2,1.5]};
function fit(){let a=[1e9,1e9,1e9],b=[-1e9,-1e9,-1e9];P.forEach(p=>{if(!p.show)return;const o=off(p);for(let j=0;j<3;j++){a[j]=Math.min(a[j],p.mn[j]+o[j]);b[j]=Math.max(b[j],p.mx[j]+o[j])}});
 if(a[0]>b[0])return{t:CTR.slice(),dist:RAD*3.2};return{t:[0,1,2].map(j=>(a[j]+b[j])/2),dist:Math.max(RAD,Math.hypot(b[0]-a[0],b[1]-a[1],b[2]-a[2])/2)*3.2}}
function mark(v){document.querySelectorAll('[data-v]').forEach(x=>x.classList.toggle('on',x.dataset.v===v))}
document.querySelectorAll('[data-v]').forEach(b=>b.onclick=()=>{mark(b.dataset.v);
 const v=VIEWS[b.dataset.v];let y=v[0];while(y-cam.yaw>Math.PI)y-=2*Math.PI;while(cam.yaw-y>Math.PI)y+=2*Math.PI;
 goal=Object.assign({yaw:y,pitch:v[1]},fit());draw()});
$('#ex').oninput=e=>{ex=e.target.value/100;goal=Object.assign({yaw:cam.yaw,pitch:cam.pitch},fit());draw()};
$('#spin').onclick=e=>{spin=!spin;e.target.classList.toggle('on',spin);draw()};
const H=new URLSearchParams(location.hash.slice(1));
if(H.get('apart')){ex=Math.min(1,Math.max(0,+H.get('apart')/100));$('#ex').value=ex*100;const f=fit();cam.t=f.t;cam.dist=f.dist}
if(H.get('view')&&VIEWS[H.get('view')]){const v=VIEWS[H.get('view')];cam.yaw=v[0];cam.pitch=v[1];mark(H.get('view'))}
draw();
}
{const H=new URLSearchParams(location.hash.slice(1)),t=H.get('tab');
 const b=t&&document.querySelector('nav button[data-t="'+t+'"]');if(b)b.click();
 if(H.get('theme'))document.documentElement.dataset.theme=H.get('theme')}
</script></body></html>
"""


# ===================================================================
# texts
# ===================================================================
def licence_text(plan, title):
    from . import design_import as di
    name = di.LICENCES.get(plan["licence"], ("Not stated",))[0]
    L = ["%s" % title, "", "Licence: %s" % name]
    urls = {"cc0": "https://creativecommons.org/publicdomain/zero/1.0/",
            "cc-by": "https://creativecommons.org/licenses/by/4.0/",
            "cc-by-sa": "https://creativecommons.org/licenses/by-sa/4.0/",
            "cc-by-nc": "https://creativecommons.org/licenses/by-nc/4.0/",
            "cc-by-nc-sa": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
            "cc-by-nd": "https://creativecommons.org/licenses/by-nd/4.0/",
            "cc-by-nc-nd": "https://creativecommons.org/licenses/by-nc-nd/4.0/"}
    if plan["licence"] in urls:
        L.append(urls[plan["licence"]])
    if plan.get("licence_note"):
        L += ["", plan["licence_note"]]
    if plan.get("remix"):
        L += ["", "Remix of:"] + ["- %s" % c for c in plan["remix"]]
    L += ["", "The Atech board and module models are not included; they are "
          "Atech's (atech.dev)."]
    return "\n".join(L) + "\n"


#: R1190 the product pack's papers a share carries (p2p_product)
P2P_PAPERS = (
    ("manual.md", "the user manual, for the person who uses it"),
    ("quick-start.html", "a one-page quick-start card (prints on A6)"),
    ("label.svg", "the product label, 80 x 40 mm"),
    ("test-plan.md", "the test by hand, with the results so far"),
    ("done-when.md", "what was asked for, and whether the design does it"),
    ("brief.md", "the request read into parts"),
    ("print-plan.md", "which Bambu printer, plates, filament, rough time"),
    ("CHANGELOG.md", "versions and what changed"),
)


def status_line(state):
    """What is known about the design having been made."""
    if (state or {}).get("printed", {}).get("when"):
        return "Printed on %s." % state["printed"]["when"]
    return "Designed and checked in Prompt To Product. Not printed and tested yet."


def message(title, text, b, files, plates=None, licence="", status=""):
    """MESSAGE.txt: for the person who gets it, ready to paste."""
    from . import makerworld
    L = [title, ""]
    L.append(text.strip() or "A 3D-printed design I made. Everything you need to "
                             "make one is attached.")
    L += ["", "What's attached:"]
    for f, what in files:
        if "/" in f or f in ("README.md", MARKER, "cover.png", "description.txt"):
            continue
        L.append("- %s: %s" % (f, what))
    n_print = sum(r["count"] for r in b["print"])
    L += ["", "To make it:"]
    if plates and plates.get("ok"):
        L.append("- Print: open the print-ready 3MF in Bambu Studio and press Print "
                 "(%s, about %s, %.0f g of PLA)."
                 % (_plural(len(plates["plates"]), "plate"), duration(plates["seconds"]),
                    plates["grams"]))
    elif n_print:
        L.append("- Print: %s, %s. Open the 3MF in any slicer; the parts are already "
                 "laid flat." % (_plural(n_print, "part"), filament_line(filament(b))))
    if b["atech"]:
        L.append("- Atech: %s (links in the shopping list)."
                 % ", ".join(r["name"] for r in b["atech"]))
    if b["buy"]:
        L.append("- Buy: %s." % ", ".join("%d x %s" % (r["count"], r["name"]) for r in b["buy"]))
    L.append("- Put it together: assembly.md, and the 3D page shows how the parts "
             "come apart (the Apart slider).")
    if status:
        L += ["", "Status: %s" % status]
    if licence:
        L += ["Licence: %s" % licence]
    L += ["", makerworld.MADE_WITH]
    return "\n".join(L) + "\n"


def readme(title, files, status=""):
    L = ["# %s" % title, ""]
    if status:
        L += [status, ""]
    L += ["Open **%s 3D.html** first: it shows everything in this folder." % title, "",
          "## Files", ""]
    for f, what in files:
        L.append("- `%s`: %s" % (f, what))
    return "\n".join(L) + "\n"


# ===================================================================
# the pack
# ===================================================================
def _fresh(folder):
    """The folder, emptied when it is one we made before; a new name when
    something else is there."""
    if os.path.isdir(folder):
        if os.path.isfile(os.path.join(folder, MARKER)):
            shutil.rmtree(folder)
        elif os.listdir(folder):
            n = 2
            while os.path.exists("%s %d" % (folder, n)):
                n += 1
            folder = "%s %d" % (folder, n)
    os.makedirs(folder, exist_ok=True)
    return folder


def _facts(doc, b_raw):
    """product.py facts for assembly and electronics; a minimal set when the
    Make it view's gather is not available."""
    try:
        from . import product_view
        f = product_view.gather(doc)
        f["bom"] = b_raw
        return f
    except Exception as exc:                              # noqa: BLE001
        _log("facts: %r" % (exc,))
        return {"project": getattr(doc, "Label", "") or "Design", "built": True,
                "bom": b_raw, "state": {}}


def _plates(doc, profile, app, tick=None):
    """print_plates.make_plates, with Bambu Studio's slicing (the slow part,
    its own process) on a thread: tick() runs meanwhile, so a window can
    repaint. FreeCAD's export stays on this thread."""
    import threading
    import time
    from . import print_plates as pp
    exported = pp.export_parts(doc, pp.run_folder(doc))
    sizes = pp.mesh_sizes(exported["files"])
    too_big = [os.path.splitext(os.path.basename(f))[0] for f, s in sizes.items()
               if not pp.fits_bed(s, profile["bed"])[0]]
    if too_big:
        sliced = {"ok": False, "plates": [], "error": "Too big for the %s bed: %s. Split "
                  "it (Edit part > Split) or scale it down."
                  % (pp.printer_name(profile), ", ".join(too_big))}
    else:
        box = {}

        def work():
            try:
                box["res"] = pp.slice_plates(exported, profile, app)
            except Exception as exc:                      # noqa: BLE001
                box["res"] = {"ok": False, "plates": [], "error": "Slicing failed: %s" % exc}
        th = threading.Thread(target=work, daemon=True)
        th.start()
        while th.is_alive():
            if tick:
                tick()
            time.sleep(0.05)
        sliced = box["res"]
    pp.print_log(exported, profile, sliced, sizes)
    out = dict(sliced)
    out.update(folder=exported["folder"], exported=exported, too_big=too_big, profile=profile)
    return out


def make_share(doc, title=None, text="", licence=None, root=None, slice_plates=True,
               picture=True, app=None, profile=None, progress=None, colours=None):
    """Make the share folder (colours {label: (rgb, transparency)} for a
    run without the 3D view). Returns {"folder", "files" [(rel, what)],
    "zip", "html", "print_ready", "plates", "bill", "plan", "message",
    "notes"}. Raises ValueError when a licence forbids sharing."""
    from . import export_tools as et
    from . import makerworld, print_plates, product
    say = progress or (lambda _t: None)
    if doc is None:
        raise ValueError("Open a design first: there is nothing to share.")
    title = (title or getattr(doc, "Label", "") or "Design").strip()
    plan = makerworld.publish_plan(doc, licence)
    if plan["problems"]:
        raise ValueError(" ".join(plan["problems"]))
    from . import design_import as di
    lic_name = di.LICENCES.get(plan["licence"], ("",))[0]
    stem = safe_name(title)
    folder = _fresh(os.path.join(root or share_root(), stem))
    files, notes = [], []
    et.restore_exploded(doc)

    def rel(p):
        return os.path.relpath(p, folder)

    # print files
    say("Laying the parts flat...")
    p3 = os.path.join(folder, stem + ".3mf")
    try:
        r = et.export_for_print(doc, p3, fmt="3MF", scope="product", lay_flat=True,
                                colours=colours)
        files.append((stem + ".3mf", "every printed part laid flat, for any slicer"))
        if r.get("left_out"):
            notes.append("The Atech board and modules are not in the files (their models "
                         "are Atech's); the shopping list links them.")
    except ValueError as exc:
        notes.append("No print file: %s" % exc)
    parts_dir = os.path.join(folder, "parts")
    try:
        et.export_for_print(doc, parts_dir, fmt="STL", scope="parts")
        try:
            et.export_for_print(doc, os.path.join(parts_dir, stem + ".step"), fmt="STEP",
                                scope="product")
        except ValueError as exc:
            notes.append("No STEP file: %s" % exc)
        files.append(("parts/", "one STL per part, and the STEP file to edit in any CAD"))
    except ValueError as exc:
        notes.append("No part files: %s" % exc)

    plates, print_ready = None, None
    if slice_plates:
        app = app or print_plates.bambu_studio()
        try:
            profile = profile or (print_plates.bambu_profile() if app else None)
        except Exception as exc:                          # noqa: BLE001
            _log("profile: %r" % (exc,))
            profile = None
        if app and profile:
            say("Bambu Studio is slicing the plates for your %s..."
                % print_plates.printer_name(profile))
            try:
                plates = _plates(doc, profile, app, lambda: say(None))
            except Exception as exc:                      # noqa: BLE001
                plates = {"ok": False, "error": "Slicing failed: %s" % exc, "plates": []}
            if plates.get("ok") and plates.get("project"):
                name = "%s - print-ready %s.3mf" % (stem, print_plates.printer_name(profile))
                print_ready = os.path.join(folder, name)
                shutil.copyfile(plates["project"], print_ready)
                files.insert(0, (name, "open in Bambu Studio and print: %s, about %s, %.0f g "
                                       "(sliced for the %s)" % (
                                           _plural(len(plates["plates"]), "plate"),
                                           duration(plates["seconds"]), plates["grams"],
                                           print_plates.printer_name(profile))))
            else:
                notes.append("No print-ready file: %s" % (plates.get("error") or "slicing failed"))

    # the bill
    say("Writing the parts and shopping lists...")
    b_raw = bom_from_doc(doc, colours)
    objects = {o.Label: o for o in getattr(doc, "Objects", [])}
    b = bill(b_raw, objects=objects)
    with open(os.path.join(folder, "BOM.csv"), "w", encoding="utf-8", newline="") as fh:
        fh.write(bom_csv(b))
    files.append(("BOM.csv", "every part: what to print, what Atech makes, what to buy"))
    with open(os.path.join(folder, "shopping-list.md"), "w", encoding="utf-8") as fh:
        fh.write(shopping_md(title, b, plates))
    files.append(("shopping-list.md", "filament per colour, Atech parts with links, "
                                      "parts to buy"))

    # assembly and electronics (the Make it pack's own writers)
    f = _facts(doc, b_raw)
    with open(os.path.join(folder, "assembly.md"), "w", encoding="utf-8") as fh:
        fh.write(product.assembly_md(dict(f, project=title)))
    files.append(("assembly.md", "how it goes together"))
    tmp = tempfile.mkdtemp(prefix="p2p-share-")
    p2p_status = {}
    try:
        g = dict(f, project=title)
        product.write_pack(g, tmp)
        p2p_status = g.get("p2p_status") or {}
        if (f.get("electrical") or {}).get("modules"):
            for sub in ("electrical", "firmware"):
                if os.path.isdir(os.path.join(tmp, sub)):
                    shutil.copytree(os.path.join(tmp, sub), os.path.join(folder, sub))
                    files.append((sub + "/", "the electrical report, schematic and wiring"
                                  if sub == "electrical" else
                                  "the firmware for `atech build` / `atech upload`"))
        # R1190: the papers for the person who makes and uses it
        for name, what in P2P_PAPERS:
            src = os.path.join(tmp, name)
            if os.path.isfile(src):
                shutil.copyfile(src, os.path.join(folder, name))
                files.append((name, what))
    except Exception as exc:                              # noqa: BLE001
        notes.append("No electrical files: %s" % exc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if picture:
        say("Taking the picture...")
        try:
            from . import capture
            img = capture.share_image(doc, out_dir=folder, clipboard=False)
            cover = os.path.join(folder, "cover" + os.path.splitext(img)[1])
            os.replace(img, cover)
            files.append((rel(cover), "the picture, for posts and MakerWorld's cover"))
        except Exception as exc:                          # noqa: BLE001
            _log("cover: %r" % (exc,))
            notes.append("No picture (it needs the 3D view).")

    with open(os.path.join(folder, "description.txt"), "w", encoding="utf-8") as fh:
        fh.write(makerworld.description(title, text, plan))
    files.append(("description.txt", "MakerWorld's upload form, ready to paste"))
    with open(os.path.join(folder, "LICENCE.txt"), "w", encoding="utf-8") as fh:
        fh.write(licence_text(plan, title))
    files.append(("LICENCE.txt", "the licence (%s) and credits" % lic_name))

    status = status_line(f.get("state"))
    if p2p_status.get("qa") and not p2p_status["qa"].startswith("Not tested"):
        status = p2p_status["qa"]                       # R1190: the test by hand
    zip_name = "%s - share.zip" % stem
    html_name = "%s 3D.html" % stem
    files.insert(0, (html_name, "open it in any browser: the design in 3D, its parts, "
                                "the shopping list and the files"))
    files.append((zip_name, "all of it in one file, to send or upload"))
    msg = message(title, text, b, files, plates, lic_name, status)
    with open(os.path.join(folder, "MESSAGE.txt"), "w", encoding="utf-8") as fh:
        fh.write(msg)
    files.append(("MESSAGE.txt", "the message to send with it, ready to paste"))
    files.append(("README.md", "this list"))

    say("Making the 3D page...")
    plates_line = ""
    if plates and plates.get("ok"):
        plates_line = "Print-ready for the %s: %s, about %s, %.0f g." % (
            print_plates.printer_name(plates["profile"]), _plural(len(plates["plates"]), "plate"),
            duration(plates["seconds"]), plates["grams"])
    n_print = sum(r["count"] for r in b["print"])
    summary = ", ".join(x for x in (
        _plural(n_print, "printed part") if n_print else "",
        _plural(sum(r["count"] for r in b["atech"]), "Atech part") if b["atech"] else "",
        _plural(sum(r["count"] for r in b["buy"]), "part") + " to buy" if b["buy"] else "")
        if x)
    with open(os.path.join(folder, html_name), "w", encoding="utf-8") as fh:
        fh.write(viewer_html(title, mesh_parts(doc, colours=colours), dict(b, filament=[
            dict(x, colour=colour_label(x["colour"])) for x in filament(b, plates)]), files, {
            "summary": summary, "licence": lic_name, "plates": plates_line,
            "made_with": makerworld.MADE_WITH,
            "when": "Shared on %s. %s" % (datetime.date.today().isoformat(), status)}))
    with open(os.path.join(folder, "README.md"), "w", encoding="utf-8") as fh:
        fh.write(readme(stem, files, status))
    with open(os.path.join(folder, MARKER), "w", encoding="utf-8") as fh:
        json.dump({"title": title, "when": datetime.datetime.now().isoformat(timespec="seconds"),
                   "licence": plan["licence"], "files": [f_ for f_, _w in files],
                   "plates": plates_line, "design": getattr(doc, "FileName", "") or ""},
                  fh, indent=1)

    say("Packing the zip...")
    zp = os.path.join(folder, zip_name)
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for base, _dirs, names in os.walk(folder):
            for n in sorted(names):
                p = os.path.join(base, n)
                if p == zp or n == MARKER:
                    continue
                z.write(p, os.path.join(stem, os.path.relpath(p, folder)))
    return {"folder": folder, "files": files, "zip": zp,
            "html": os.path.join(folder, html_name), "print_ready": print_ready,
            "plates": plates, "bill": b, "plan": plan, "message": msg, "notes": notes,
            "status": status, "title": title, "text": text}


def summary(res):
    bits = ["Ready in %s." % res["folder"]]
    if res.get("plates") and res["plates"].get("ok"):
        p = res["plates"]
        bits.append("Print-ready: %s, about %s, %.0f g." % (
            _plural(len(p["plates"]), "plate"), duration(p["seconds"]), p["grams"]))
    bits += res.get("notes") or []
    return " ".join(bits)


def post_text(res):
    """The atech.dev post's description: the text, then what it takes."""
    b = res["bill"]
    L = [res.get("text", "").strip()] if res.get("text", "").strip() else []
    n = sum(r["count"] for r in b["print"])
    if n:
        L.append("Prints in %s%s." % (_plural(n, "part"), (
            ", about %s and %.0f g" % (duration(res["plates"]["seconds"]), res["plates"]["grams"]))
            if res.get("plates") and res["plates"].get("ok") else ""))
    if b["atech"]:
        L.append("Atech: %s." % ", ".join(r["name"] for r in b["atech"]))
    if b["buy"]:
        L.append("Also needs: %s." % ", ".join("%d x %s" % (r["count"], r["name"])
                                               for r in b["buy"]))
    return "\n\n".join(L)


# ===================================================================
# the window
# ===================================================================
def _reveal(path, runner=None):
    cmd = ["open", "-R", path] if os.path.isfile(path) else ["open", path]
    (runner or subprocess.Popen)(cmd)
    return cmd


def _copy(text):
    try:
        from PySide6 import QtWidgets
        QtWidgets.QApplication.clipboard().setText(text)
        return True
    except Exception:                                     # noqa: BLE001
        return False


def ShareDialog(parent=None, doc_fn=None, opener=None, runner=None, maker=None):
    """Share: the title, words and licence; Make the share pack (in the
    background); then where it goes."""
    from PySide6 import QtCore, QtWidgets
    from . import design_import as di
    from . import export_tools as et
    from . import makerworld, print_plates
    doc_fn = doc_fn or et._active_doc
    opener = opener or makerworld._open_url
    maker = maker or make_share
    doc = doc_fn()

    d = et._tool_dialog(QtWidgets.QDialog, parent, "Share")
    d.setModal(False)
    lay = QtWidgets.QVBoxLayout(d)
    lay.setContentsMargins(20, 18, 20, 18)
    lay.setSpacing(10)
    t = QtWidgets.QLabel("Share", d)
    t.setObjectName("ToolTitle")
    lay.addWidget(t)
    sub = QtWidgets.QLabel("One folder with everything: the design in 3D (a page anyone "
                           "can open), the print files, the parts and shopping list, how "
                           "it goes together, the licence and a message to send with it.", d)
    sub.setObjectName("ToolMuted")
    sub.setWordWrap(True)
    lay.addWidget(sub)
    form = QtWidgets.QFormLayout()
    d.title = QtWidgets.QLineEdit(getattr(doc, "Label", "") or "", d)
    d.title.setAccessibleName("Title")
    form.addRow("Title", d.title)
    d.text = QtWidgets.QPlainTextEdit(d)
    d.text.setPlaceholderText("What it is and what it does (optional)")
    d.text.setAccessibleName("Description")
    d.text.setFixedHeight(80)
    form.addRow("Description", d.text)
    d.licence = QtWidgets.QComboBox(d)
    d.licence.setAccessibleName("Licence")
    for k in di.LICENCE_ORDER:
        if k not in ("unknown", "own"):
            d.licence.addItem(di.LICENCES[k][0], k)
    form.addRow("Licence", d.licence)
    lay.addLayout(form)
    app = print_plates.bambu_studio()
    d.slice = QtWidgets.QCheckBox("Add a print-ready file, sliced in Bambu Studio "
                                  "(about a minute)", d)
    d.slice.setChecked(bool(app))
    d.slice.setEnabled(bool(app))
    if not app:
        d.slice.setText("Add a print-ready file (needs Bambu Studio)")
    lay.addWidget(d.slice)
    d.checks = QtWidgets.QLabel("", d)
    d.checks.setWordWrap(True)
    lay.addWidget(d.checks)
    d.status = QtWidgets.QLabel("", d)
    d.status.setObjectName("ToolMuted")
    d.status.setWordWrap(True)
    d.status.setTextInteractionFlags(d.status.textInteractionFlags()
                                     | QtCore.Qt.TextSelectableByMouse)
    lay.addWidget(d.status)
    row = QtWidgets.QHBoxLayout()
    row.addStretch(1)
    d.btn_make = QtWidgets.QPushButton("Make the share pack", d)
    d.btn_make.setObjectName("ToolPrimary")
    d.btn_make.setDefault(True)
    row.addWidget(d.btn_make)
    lay.addLayout(row)

    # where it goes (after the pack is made)
    d.targets = QtWidgets.QFrame(d)
    d.targets.setObjectName("ToolCard")
    tv = QtWidgets.QVBoxLayout(d.targets)
    tv.setContentsMargins(14, 12, 14, 12)
    head = QtWidgets.QLabel("SEND IT", d.targets)
    head.setObjectName("ToolMuted")
    head.setStyleSheet("font-weight: 600;")
    tv.addWidget(head)
    d.buttons = {}
    for key, label, tip in (
            ("page", "Open the 3D page", "The page the person gets: turn the design, "
                                         "pull it apart, the parts and the files"),
            ("send", "Send to someone", "Shows the zip (drag it into a mail or a chat) and "
                                        "copies the message"),
            ("post", "Post to atech.dev", "A post on atech.dev/community with the picture "
                                          "and the text"),
            ("makerworld", "Upload to MakerWorld", "Shows the files, copies the description "
                                                   "and opens MakerWorld's upload page"),
            ("folder", "Show folder", "Everything, in Finder")):
        b = QtWidgets.QPushButton(label, d.targets)
        b.setToolTip(tip)
        b.setAccessibleName(label)
        b.setAutoDefault(False)
        d.buttons[key] = b
    g = QtWidgets.QGridLayout()
    for i, key in enumerate(("page", "send", "post", "makerworld", "folder")):
        g.addWidget(d.buttons[key], i // 2, i % 2)
    tv.addLayout(g)
    d.target_text = QtWidgets.QLabel("", d.targets)
    d.target_text.setObjectName("ToolMuted")
    d.target_text.setWordWrap(True)
    tv.addWidget(d.target_text)
    d.targets.setVisible(False)
    lay.addWidget(d.targets)

    plan0 = makerworld.publish_plan(doc) if doc is not None else {
        "licence": "cc-by", "problems": ["Open a design first."], "licence_note": ""}
    i = d.licence.findData(plan0["licence"])
    d.licence.setCurrentIndex(i if i >= 0 else 0)
    d.result = None
    keep = {}

    def refresh():
        plan = makerworld.publish_plan(doc, d.licence.currentData()) if doc is not None \
            else plan0
        if plan["problems"]:
            d.checks.setText("Can't share yet: " + " ".join(plan["problems"]))
        else:
            d.checks.setText(plan.get("licence_note") or "")
        d.btn_make.setEnabled(not plan["problems"])
        return plan

    def done(res):
        d.btn_make.setEnabled(True)
        if isinstance(res, Exception):
            d.status.setText("Could not make the share pack: %s" % res)
            return
        d.result = res
        d.btn_make.setText("Make it again")
        d.status.setText(summary(res))
        d.targets.setVisible(True)
        d.target_text.setText("")

    def make():
        if doc is None:
            d.status.setText("Open a design first: there is nothing to share.")
            return None
        d.btn_make.setEnabled(False)
        d.targets.setVisible(False)
        kw = dict(title=d.title.text(), text=d.text.toPlainText(),
                  licence=d.licence.currentData(), slice_plates=d.slice.isChecked())
        # exports and the picture need FreeCAD's thread; slicing is the slow
        # part and runs in Bambu Studio's own process, so the window only
        # repaints between steps.
        def say(text):
            if text is not None:
                d.status.setText(text)
            QtWidgets.QApplication.processEvents()
        try:
            res = maker(doc, progress=say, **kw)
        except Exception as exc:                          # noqa: BLE001
            res = exc
        done(res)
        return res

    def page():
        if d.result:
            opener(QtCore.QUrl.fromLocalFile(d.result["html"]).toString())

    def send():
        if d.result:
            _reveal(d.result["zip"], runner)
            _copy(d.result["message"])
            d.target_text.setText("The zip is selected in Finder: drag it into a mail, "
                                  "Messages or a chat. The message is copied: paste it.")

    def post_():
        if not d.result:
            return None
        from . import post
        p = post.PostDialog(d.window())
        p.title.setText(d.result["title"])
        p.text.setPlainText(post_text(d.result))
        cover = [os.path.join(d.result["folder"], f) for f, _w in d.result["files"]
                 if f.startswith("cover.")]
        for c in cover:
            p.add_media(c)
        keep["post"] = p
        p.show()
        return p

    def maker_world():
        if not d.result:
            return
        res = d.result
        _reveal(res.get("print_ready") or res["zip"], runner)
        with open(os.path.join(res["folder"], "description.txt"), encoding="utf-8") as fh:
            _copy(fh.read())
        opener(makerworld.UPLOAD_URL)
        d.target_text.setText(
            "On MakerWorld press Upload, then drag in %s (it carries the print profile), "
            "cover.png and the parts/ files. The description is copied: paste it."
            % (os.path.basename(res["print_ready"]) if res.get("print_ready")
               else "the 3MF"))

    def folder():
        if d.result:
            (runner or subprocess.Popen)(["open", d.result["folder"]])

    d.btn_make.clicked.connect(lambda _=False: et._guard(make))
    d.buttons["page"].clicked.connect(lambda _=False: et._guard(page))
    d.buttons["send"].clicked.connect(lambda _=False: et._guard(send))
    d.buttons["post"].clicked.connect(lambda _=False: et._guard(post_))
    d.buttons["makerworld"].clicked.connect(lambda _=False: et._guard(maker_world))
    d.buttons["folder"].clicked.connect(lambda _=False: et._guard(folder))
    d.licence.currentIndexChanged.connect(lambda _i: refresh())
    d.make, d.refresh = make, refresh
    d.send, d.post_, d.maker_world, d.page = send, post_, maker_world, page
    refresh()
    d.resize(560, 0)
    return d
