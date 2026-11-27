# Merging cad-workflow into Prompt2Product (R1200-R1295)

Asked 27 Nov 2026: bring what makes Gustav's `cad-workflow` parts fit and
print into Prompt2Product, "where it makes sense", with tests kept small,
several commits along the way, and the Atech rules respected. Plan written
the same day. Work happens in the worktree `.claude/worktrees/cad-workflow-merge`
on the branch `cad-workflow-merge` (from `port-rules-8-12`, 9d7e9e3).

Source read: `/home/julius/Atech/cad-workflow` at d0c7386 (snapshot of 26 Nov
2026). A side-by-side comparison of the two systems was made first; this plan
follows from it.

## What cad-workflow has that Prompt2Product lacks

Its value is knowledge from parts that were printed, not its code:

- Fit numbers that came from prints (the DC Motor D-shaft bore, the sleeve
  over the board socket, how much printed holes shrink).
- A test-fit print, and the habit of writing each print result back as a number.
- Printability rules learned the hard way (first layer, which way up, which
  font survives the slicer).
- Fit classes for parts that touch, and hand formulas for strength.
- The Bambu Studio command line's pitfalls.

Prompt2Product today: most of `atech_fit.py` is tag A (assumed), the D-bore
value (3.10 / 2.60) is the size cad-workflow had to drill open, no kit call
applies it, nothing reads a print result back, and `./check` has no
first-layer or overhang check.

## Decisions

Made by the user:

- From Gustav we ask for files only; a test print comes later. Until then a
  value from cad-workflow carries its source and date and is not claimed as
  confirmed on our printers.
- The existing examples are left alone. What they need is listed under
  "Later" and is not part of this plan.
- "Make your best judgement calls on what will produce the most capable and
  reliable program."

Made here, under that last line:

1. **Port the knowledge to the FreeCAD kit. Do not bundle build123d, trimesh
   or manifold3d.** Pure-Python parts of cad-workflow (fit bands, hand
   formulas, slicer preset fixes) are carried over almost as they are. Part
   models are rewritten against the kit and compared with cad-workflow's own
   output. Mesh checks use FreeCAD's tessellation plus numpy, which the app
   already ships. Reason: two geometry stacks in `./check` can disagree, and
   the agent, the 64 examples, TRAPS.md and Dimensions all assume FreeCAD.
2. **New checks never fail a build in this round.** They print lines and
   WARNINGs. A false alarm costs the agent a fix round and can bend a design.
   They become gates only after their false-alarm rate is measured.
3. **A printed number beats an assumed one, and says where it came from.**
   New tag `P` in `atech_fit.py`: proven on a print, with material, printer
   family, date and source file. A value the user's own prints gave is tag `U`
   and beats both.
4. **Print orientation is computed, not asked for.** The first-layer and
   overhang checks use the same rule Export already uses (largest flat face
   down). A declared orientation can come later.
5. **Nothing changes what a module may do or where it may go.** See the next
   section.

## Atech rules this work must respect

Checked against `/home/julius/Atech/python-sdk` (1.0.0a14, 2daa0e3:
`src/atech/catalog/data/boards/14port.yaml`) and this repo's
`projects/atech_ports.py`:

- **Port 8 is the USB-C jack and port 12 the Reset button.** The SDK lists
  both as `reserved`: no module with firmware goes there. Here:
  `PORT_ONLY = {8: usbc, 12: button}`, `MODULE_ONLY = {usbc: (8,)}`. Nothing
  taken from cad-workflow may place a module against these. (cad-workflow's
  egg lamp has USB-C on port 10, but of the 10-port board; it is not carried
  over as a 14-port layout.)
- **Two-port modules use an adjacent pair**: left 1-2 … 5-6, right 9-10,
  10-11, 13-14. Port 12 breaks 11-13. Port 7 has no neighbour.
- **Power modules (USB-C, power jack) are not in the SDK catalog** and get no
  entry in `project.yaml`.
- **Facts carry their source.** The rule from R1000 holds: show only what is
  published or measured, and say which. A number from cad-workflow is "printed
  by Gustav, date, material", not a standard.
- **Hardware geometry stays measured.** Board and module sizes keep coming
  from `models/` (tag CAD). cad-workflow's hand-copied module dimensions are
  used only to cross-check, never to replace them.
- **No new fit value changes a port rule, a seat tolerance or the SDK
  catalog snapshot.**

## What we need from Gustav

1. His Claude memory files for these projects: `feedback_stl_iteration.md`,
   `feedback_dont_over_engineer.md`, `feedback_run_it_yourself`,
   `feedback_verify_edits`, `feedback_free_body_before_sizing` (best: the
   whole memory folder).
2. `~/projects/atech_cad_from_stick/` (the module STEP files the scripts read).
3. `~/projects/atech_module_renders/`: `NOTES.md` (the socket and seating
   mechanism), `cad_solids/`, `meshes/`.
4. `~/projects/ATECH_PRODUCTS_PLAYBOOK.md`.
5. Print results the repo does not record: the robot arm, 12 V and soil
   cases (handed over 19 Nov), the egg cup after its re-slice, the rabbit
   ears, anything since 26 Nov. For each: printer, material, fit verdict.
6. What the key numbers were proven on: bore 3.4 / flat 2.9 and sleeve 0.3
   per side. Which printers and filaments, and do they hold in PLA?
7. Two caliper measurements: the DC motor shaft (diameter and across the
   flat; cad-workflow says 2.5, this repo 2.6) and the board's thickness
   (7.00 or 6.49, open item U1 in `atech_fit.py`).
8. Optional: one or two sliced plates (`*.gcode.3mf`) and his Bambu Studio
   version, to compare with our slicer output.
9. Optional: `partsmith/partsmith.db` and `partsmith/builds/` (weighed parts).

Not needed: printer access codes, customer wheels, the university rig, the
dragon STL.

## Steps

| # | Step | Done when |
|---|------|-----------|
| R1200 | **This plan, and a look at what the repo can reproduce.** Run cad-workflow's `wheel.py` and `testfit.py` in a throwaway venv; note what only exists on Gustav's Mac. | Plan committed. The reference STLs exist, or the plan says why not. |
| R1210 | **Printed fit numbers in `atech_fit.py`.** Tag `P` with a source per value. D-bore, round shaft hole, hole shrink, sleeve, module recess, lid lip, the fit bands (press … pocket). `render_tables()` shows the tag. User overrides (tag `U`) read from a JSON file. | Unit tests: every `P` value has a source; the override beats the table; the prompt tables carry the new values. |
| R1220 | **Kit calls that apply them.** `cad.d_bore()` and `wheel(flat=…)` for the DC Motor shaft; `screw_boss(kind="tap" | "insert")`, which the prompt already tells the agent to use; a `shaft_hole` helper that adds the shrink. The API card and prompt name them. | FreeCAD tests: the D-bore section measures 3.4 / 2.9, 12 deep; the insert boss has the insert hole; old calls give the same solid as before. |
| R1230 | **Fit coupon.** A kit function builds the five bore pucks (3.2 to 3.6, size engraved) and a sleeve gauge; a starter opens it. Compared with cad-workflow's `testfit.py` output. | FreeCAD test: five solids, each bore as labelled; passes `./check`. |
| R1240 | **Print feedback.** `p2p_fitlog.py`: "it fit / too tight / too loose, by how much" becomes a user override per printer and material; the workspace and the prompt carry it; the Fit rows of `qa.json` feed it. A small dialog asks. | Unit tests for the maths and the file; an offscreen test of the dialog. |
| R1250 | **Printability in `./check`.** Per printed part, in its print orientation: first-layer area, share of the footprint and loop count; area of downward faces steeper than 45 degrees; a knife-edge first layer. `PRINT` lines and WARNINGs only. | Unit tests on meshes of cad-workflow's own failures (a cup rim-down, a lid on its tip, a chamfered rim); a real `./check` run prints the lines. |
| R1260 | **Fit class for shafts in bores.** `./check` finds a cylinder inside a hole of another part and reports the clearance and its class (press, transition, running, slide, clearance). NOTE lines only. | FreeCAD test with a 3.0 pin in 3.0, 3.3 and 3.6 holes. |
| R1270 | **Slicing.** Check our Bambu Studio call against cad-workflow's findings (presets with `inherits`, an empty `printer_model_id`); find Bambu Studio on Linux; write `PRINT.md` into the pack (orientation, supports and why, time, grams). | Unit tests with preset fixtures; the pack test finds the paper. |
| R1280 | **Rules for the agent.** TRAPS.md gets cad-workflow's CAD lessons that apply to FreeCAD. The prompt gets "a guessed dimension is marked MEASURE" and the fit-first lines for shafts. | Prompt tests pass; the prompt is not longer than its budget. |
| R1290 | **Hand formulas.** `atech_mech.py`: cantilever, snap strain, pin shear, press fit, with material allowables and a self-test. Available to the agent's script; no gate. | The self-test passes against textbook cases. |
| R1295 | **Prove it.** The test suite against the baseline taken before the work; a real `freecadcmd` build of a DC Motor wheel; one small agent run of the wheel prompt if the harness runs here; CHANGELOG, README, results below. | No new failures; the wheel's bore is 3.4 / 2.9. |

Order of value: R1210-R1220 first (they change what the agent draws), then
R1250, R1230-R1240, R1270, the rest.

## How it is tested, and kept small

- Baseline first: every test module run once on the untouched checkout with
  the built app's Python (`dist/build/squashfs-root/usr/bin/python`), results
  kept. "No new failures" means against that list. The checkout already has
  known failures (52 of 64 examples since the port rules, the fake-CLI
  family).
- Each step adds a small test file of its own (`test_cadwf_r12xx.py`), pure
  Python where it can be, one `freecadcmd` child where geometry is needed.
- Only the touched modules' tests are re-run after a step; the whole suite
  once at the end.
- No long agent evals. At most one or two fast-mode runs at the end.

## Not in this plan

- build123d, trimesh, manifold3d in the app; mesh booleans for "start from a
  mesh". Worth a later step once a real case needs it.
- FEA (gmsh + scikit-fem), MuJoCo as a gate, 2D drawings.
- partsmith's CLI, database and YAML specs; the critic file protocol.
- Talking to printers over the LAN (`tools/bambu.py`): the H2S ignores a
  remote start, and the app hands over to Bambu Studio on purpose.
- EasyEDA PCB import; the boat's flotation; vehicle maths.

## Later (noted, not done here)

- Move the existing examples to the printed values (`wheel(bore=3.3)` on a DC
  Motor shaft becomes the D-bore) and to the port rules.
- Turn the R1250 lines into gates once measured.
- A test print of the fit coupon on our printers, then move values from `P`
  (Gustav's prints) to confirmed.

## Results

(Filled in as each step lands.)
