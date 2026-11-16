"""render_example_pictures - the gallery's picture of each example (R970).

Runs INSIDE freecadcmd. Builds each product example the way ./check does
and saves the review renderer's 3/4 hero view, 360 x 360, to
addon/AcadAgent/acadagent/example_pictures/<key>.png (examples_gallery
shows it; test_import_gallery_r970 wants one per catalogued example):

    REPO=$PWD; cd /tmp && \
    KIT=$REPO/addon/AcadAgent/acadagent/agent_kit PROJECTS=$REPO/projects \
    ATECH_ARTIFACTS=$REPO/models OUT=$REPO/addon/AcadAgent/acadagent/example_pictures \
    ONLY=hype_button,debug_duck <freecadcmd> $REPO/branding/render_example_pictures.py

ONLY (comma-separated keys) limits it; without it every example is drawn
(about 5 minutes).
"""
import os, sys, json, time, shutil, tempfile
KIT = os.environ["KIT"]; PROJECTS = os.environ["PROJECTS"]; OUT = os.environ["OUT"]
for p in (KIT, PROJECTS):
    sys.path.insert(0, p)
import importlib.util
import FreeCAD as App
import atech_geom
_sp = importlib.util.spec_from_file_location("check_pics", os.path.join(KIT, "check.py"))
check = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(check)
import numpy as np, review
from PIL import Image
PX = 360
os.makedirs(OUT, exist_ok=True)
ex = os.path.join(KIT, "examples")
keys = sorted(n[:-3] for n in os.listdir(ex) if n.endswith(".py") and n != "atech_case.py"
              and n[:-3] not in ("knob", "gear", "bracket", "enclosure", "snap_box", "hinged_box"))
only = [k for k in os.environ.get("ONLY", "").split(",") if k]
if only:
    keys = [k for k in keys if k in only]
for key in keys:
    t0 = time.time()
    ws = tempfile.mkdtemp(prefix="pic-")
    try:
        src = open(os.path.join(ex, key + ".py"), encoding="utf-8").read()
        open(os.path.join(ws, "model.py"), "w").write(src)
        os.chdir(ws)
        tree = atech_geom.record_view(src, {})
        doc, err, out, env, seeded, view = check._run(App, tree, os.path.join(ws, "model.py"), 300)
        if err:
            print("PICFAIL", key, err.strip().splitlines()[-1]); continue
        items = check._review_items(doc, seeded, view, set())
        scene = review.scene_from(items)
        shadow = review.ShadowMap(scene, review.KEY)
        diag = float(np.linalg.norm(scene["max"] - scene["min"]))
        ctr = (scene["min"] + scene["max"]) / 2
        _n, v, up, persp = review.HERO
        cam = review.camera(v, up, ctr, diag, persp)
        img, _s = review.render_view(scene, cam, PX, PX, shadow, ss=2, margin=0.06)
        Image.fromarray((np.clip(img, 0, 1) * 255).astype("uint8")).quantize(colors=200).save(
            os.path.join(OUT, key + ".png"), optimize=True)
        print("PIC", key, round(time.time() - t0, 1))
    except Exception as exc:
        print("PICFAIL", key, repr(exc))
    finally:
        os.chdir("/")
        shutil.rmtree(ws, ignore_errors=True)
