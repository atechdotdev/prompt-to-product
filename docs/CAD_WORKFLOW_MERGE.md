# Merging cad-workflow into Prompt2Product (R1200-R1295)

Asked 27 Nov 2026: bring what makes Gustav's `cad-workflow` parts fit and
print into Prompt2Product, "where it makes sense", with tests kept small,
several commits along the way, and the Atech rules respected. Plan written
the same day. Work happens in the worktree `.claude/worktrees/cad-workflow-merge`
on the branch `cad-workflow-merge` (from `port-rules-8-12`, 9d7e9e3).

Source read: Gustav's `cad-workflow` repository at d0c7386 (snapshot of 26 Nov
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

Checked against the `python-sdk` repository (1.0.0a14, 2daa0e3:
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

- **Five examples put a part on a motor's D-shaft with a round 3.3 mm bore**
  (found by R1260's check; it does not drive): `toy_car` (Rim_RL, Rim_RR,
  Rim_FL, Rim_FR), `rc_tank` (Sprocket_L, Sprocket_R), `desk_fan` (Rotor),
  `pet_feeder` (Rotor), `photo_turntable` (Pinion). Each needs
  `cad.motor_shaft` and the D-bore, as `starters/starter_wheels.py` now has.
  The examples that use the `n20_wheel` hub in a socket (rover, balance bot)
  are not affected.
- The examples' port placements (52 of 64, from the port rules commit).
- Turn the R1250 / R1260 lines into gates. Measured so far: the first-layer
  warning fires on 5 of 873 parts in the examples, all parts with no flat
  side (a ball, two grilles, a caster ball, a glow ring).
- A test print of the fit coupon on our printers, then move values from `P`
  (Gustav's prints) to confirmed. Until then they are his printers' numbers.
- Run Print once against a real Bambu Studio: R1270 follows Gustav's notes
  and was tested with a fake support folder only. The exact names of the
  machine template files, and whether a process preset's `inherits` is
  followed, could not be checked here.
- One live agent run of a wheel request, to see the agent pick up
  `cad.motor_shaft`. Not done: an agent run costs the user's tokens and the
  harness is built for hours-long runs.
- `atech_fit`'s lid lip (0.20 / 0.15) agrees with cad-workflow's egg lid
  (0.20 snug in PLA) and box lid (0.25) but neither is recorded as a
  confirmed fit; left tagged A.

## Results (27 Nov 2026)

All eleven steps are done and committed on `cad-workflow-merge`, one commit
per step (two for R1240 and R1250).

- **R1200 done.** cad-workflow reproduces on Linux with build123d 0.13:
  `testfit.py` gives the same 85.99 x 14.0 x 10.0 mm, 7.167 cm3 as the STL in
  the repo; `wheel.py` gives 16.28 cm3 against 16.26 (another font: Arial
  Black is a macOS font). Only on Gustav's Mac: the module STEPs, his memory
  files, the EasyEDA cache (the list above).
- **R1210 done.** `atech_fit`: tags P and U, `SOURCES`, D-bore 3.4 / 2.9 x 12
  (was 3.10 / 2.60), `hole_shrink` 0.25, the fit bands, `hole_for`,
  `fit_word`, user values. The shaft's flat is 2.50, measured here from
  `models/stl/dc_motor.stl` (2.998 round): cad-workflow's 2.5 was right and
  this repo's 2.60 was derived from the wrong bore.
- **R1220 done.** `cad.d_bore`, `cad.shaft_hole`, `cad.fit`,
  `cad.wheel(flat=)`, `cad.screw_boss(kind=)`. Measured under freecadcmd: the
  bore's section is 3.400 x 2.900, 12 deep; three sabotage switches are each
  noticed.
- **R1230 done.** `cad.fit_coupon`: the row is 86.00 x 14.00 x 10.00 mm and
  7.179 cm3 against Gustav's 7.167.
- **R1240 done.** `p2p_fitlog`, `fit_view.FitDialog`, the copy into the chat
  folder, the load in `./check`. End to end under freecadcmd: with "puck 35"
  recorded, `cad.d_bore` cuts 3.50 x 3.00; without, 3.40 x 2.90.
- **R1250 done.** `atech_print`, PRINT lines. Measured on all 64 examples
  (894 parts, built with the port rules switched off for the measurement
  only): first run 24 warnings and 79 parts past the time budget; after
  vectorising the slicing and making trim parts a note, 5 warnings and 21
  parts past the budget. 418 parts (48 %) have overhangs that need supports
  in Export's orientation: said in the line, never a warning. `./check`
  takes the same 60 s median as before.
- **R1260 done.** `atech_fitcheck`, FIT lines, `cad.motor_shaft`. Found on
  the way: a D-bore whose flat does not face the shaft's flat overlaps the
  shaft in the model, so the wheel and the bore take the shaft's own flat,
  measured from the module. The "Two-wheel base" starter had round 3.3 bores;
  it now passes `./check` with both wheels read as "D-bore 3.4 / 2.9, the
  push fit that printed". On the examples: 9 round bores on motor shafts
  (listed under Later) and 367 pin-in-hole pairs in 56 examples.
- **R1270 done, not run against a real Bambu Studio.** Whole presets for the
  command line, the template G-code, the model id, Linux discovery, "On the
  bed" in the print plan. One more thing found: the supports process
  inherited from the selected one, so with supports on it would have lost
  its parent's settings under the same rule.
- **R1280 done.** TRAPS R33-R42; the prompt's fit section names the calls
  and stays under its 3500 characters (3484; the fit tables are 2420 of
  2600).
- **R1290 done.** `atech_mech`, 12 tests, its own self-test.
- **R1295: see below.**

### The test suite, before and after

Every test module, one process each, with the built app's Python and the
checkout's own module library (`ATECH_ARTIFACTS`), first on the untouched
checkout (9d7e9e3) and then on this branch:

| | modules | tests | failing tests |
|---|---|---|---|
| before | 117 | 2439 | 71 |
| after | 127 | 2556 | 71 |

The ten new modules (`test_cadwf_r1210` ... `r1290`, 113 tests) all pass.
`test_build_ws` runs 4 more tests.

Seven tests fail after that passed before. None is caused by the change;
all come from running in a git worktree:

- `test_port_rules` (1) and `test_agent_integration_r500` (4) look for
  `dist/build/.../freecadcmd` inside the checkout. A worktree has no `dist/`,
  so they picked up the system's FreeCAD 1.1.4 from PATH. With
  `ATECH_FREECADCMD` pointing at the built app's, both modules pass.
- `test_print_order_r850` (2) reads the site's prices from a `studio`
  checkout next to the repository. Next to a worktree there is none.

Seven other tests failed before and pass after (five in
`test_eval_harness`, one each in `test_build_ws` and `test_shell_round10`).
They are not claimed as fixes: the same modules passed in an earlier run of
the untouched checkout, so they vary with the machine's load.

The 71 that fail on both sides are the known ones: the examples that break
the port rules, and the fake-CLI family.

### What was not done

- No live agent run (see Later).
- Nothing was printed, and Bambu Studio was not run.
- The existing examples were not changed, as agreed.
