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
| R1230 | **Fit coupon.** A kit function builds the five bore pucks (3.2 to 3.6, size marked) and a sleeve gauge; the Fit test window opens it. Compared with cad-workflow's `testfit.py` output. | FreeCAD test: five solids, each bore as labelled; passes `./check`. |
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
  (found by R1260's check; it has no key, so only friction turns the
  part): `toy_car` (Rim_RL, Rim_RR,
  Rim_FL, Rim_FR), `rc_tank` (Sprocket_L, Sprocket_R), `desk_fan` (Rotor),
  `pet_feeder` (Rotor), `photo_turntable` (Pinion). Each needs
  `cad.motor_shaft` and the D-bore, as `starters/starter_wheels.py` now has.
  The examples that use the `n20_wheel` hub in a socket (rover, balance bot)
  are not affected.
- ~~The two projects the app ships with break the port rules~~ Done on
  28 Nov 2026: see "The two default projects, rebuilt" below.
- The examples' port placements (52 of 64, from the port rules commit).
  The user asked to fix only the two default projects for now.
- **`./check` can miss a ribbon that runs through a wall.** Its overlap
  test is a boolean common, and on a ribbon against a revolved shell that
  common came back empty while points of the ribbon were inside the wall
  (the lamp, while it was being rebuilt: port 6's ribbon went out through
  the column, CHECK PASS). Separately, `ap.cable(..., smooth=True)` once
  made a ribbon with a negative volume (inside out), which a boolean test
  also cannot judge. A point-sampled test of each ribbon against each part
  would catch both.
- Turn the R1250 / R1260 lines into gates. Measured so far: the first-layer
  warning fires on 5 of the 873 parts that were judged in the examples, all
  parts with no flat side (a ball, two grilles, a caster ball, a glow ring).
- A test print of the fit coupon on our printers, in PLA too: every `P`
  value is from Gustav's printers in PETG and PETG-CF, and he has no PLA
  record for the bore. PLA is the kit's default material.
- A print that confirms the assumed sizes: the running hole (3.5 for a
  3 mm shaft; no turning hole has been printed), the 0.3 mm sleeve
  clearance (the redrawn sleeve's print is not on record), the lid lip
  (0.20 / 0.15 agrees with cad-workflow's egg lid, 0.20 snug in PLA, and
  box lid, 0.25, but neither is recorded as a confirmed fit).
- Run Print once against a real Bambu Studio. What is known: the template
  file names and the `include` list are confirmed against Gustav's real H2S
  files (`test_gustavs_real_files_when_given`); the command line is assumed
  not to follow `inherits` for machine, process or filament presets (his
  answer of 27 Nov). What is not: one real slice with our files, where a
  Linux install keeps its template files (the folders in
  `LINUX_PROFILE_DIRS` are likely places, not checked), and whether a
  printer refuses a file without a model id.
- The build plate when the printer's file names no default and the
  filament prints on every plate: nothing is set then (Bambu Studio's own
  default, as before), and the result says so. If BambuStudio.conf records
  the plate the person chose, read it. Not known: what the command line
  does with PLA on a plate the printer rules out, and whether a real
  install can have a printer's preset without its model file.
- Print results when the fall-back to preset files is taken (the whole
  presets could not be written): no plate is named on that path; the
  result says to slice again in Bambu Studio.
- The app does not ask how a print came out. `print.json` has an empty
  `how_it_printed` that nothing reads, the by-hand test paper (`qa.json`)
  does not feed the fit record, and the Fit test window opens from the menu
  only. The window now takes "fitted / too tight / too loose, by about";
  asking after a print is the missing step.
- Check what was exported, not only what was drawn (Gustav's rule "run it
  yourself": load the STL that goes to the printer and measure the bore in
  it), and warn when the filament selected in Bambu Studio is not the
  material the design was drawn for.
- `./check`'s shaft check sees true cylinders only. A bore that is a
  polygon or came through a STEP round trip as a spline gets no FIT line.
- One live agent run of a wheel request, to see the agent pick up
  `cad.motor_shaft`. Not done: an agent run costs the user's tokens and the
  harness is built for hours-long runs.

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
- **R1240 done, in part.** `p2p_fitlog`, `fit_view.FitDialog`, the copy into
  the chat folder, the load in `./check`. End to end under freecadcmd: with
  "puck 35" recorded, `cad.d_bore` cuts 3.50 x 3.00; without, 3.40 x 2.90.
  Not done: the Fit rows of `qa.json` do not feed the record (the step's
  own text says they would), and nothing asks after a print (see Later).
- **R1250 done.** `atech_print`, PRINT lines. Measured on all 64 examples
  (894 parts, built with the port rules switched off for the measurement
  only): first run 24 warnings and 79 parts past the time budget; after
  vectorising the slicing and making trim parts a note, 21 parts past the
  budget and 873 judged, 5 of them with a warning. 418 of the 873 (48 %)
  have overhangs that need supports in Export's orientation: said in the
  line, never a warning. `./check` takes the same 60 s median as before.
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
  and stays under its 3500 characters (3489 after the review; the fit tables are 2446 of
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

## The review (27 Nov 2026), and what it changed

After the steps were committed, and with Gustav's files unpacked, twelve
reviewers went through the branch: six looked for defects (slicing, the
facts taken from Gustav's records, the hardware numbers, the kit calls, the
checks, and what cad-workflow learnt that the app still does not do), six
others tried to refute each finding. 40 findings stood, 22 were refuted.
Three were of high or medium weight in what a person would meet:

1. **A slice of PETG or PETG-CF would have failed.** The process written for
   Bambu Studio's command line did not name the build plate, so it sliced
   for the Cool Plate, which those filaments do not print on (Gustav's note
   of 8 Nov; every process file in cad-workflow's builds sets the plate). Fixed:
   `print_plates.bed_type`.
2. **The fit test did not pass the app's own check.** Its engraved digits
   left 0.05 mm walls. Fixed: the pucks and the plate are marked with dots,
   and a test runs `./check` on them.
3. **One part could stall `./check`.** On a solid sewn from a mesh the print
   check's time grew with the square of the face count. Fixed: one measure
   per direction, a face limit, and the time budget is looked at inside a
   part too.

The other fixes, by where they are:

| Where | What was wrong | Now |
|---|---|---|
| `atech_fit` fit classes | The bands called the drawn 3.1 bore (drilled open) a valid press fit and the proven 3.4 "running"; `shaft_hole(3.0, "press")` drew 3.1. | Four classes anchored on the motor-shaft prints: press 3.3, push 3.4, running 3.5 (assumed), clearance 3.75 (assumed). The bands touch, so every clearance has one word. |
| `atech_fit` tags | `slide` 0.3, the 3.5 running hole and the motor face's bearing were tagged as printed. | Tagged assumed. `P` is left on the D-bore and its depth; the hole shrink is `P/A` (worked out from how the bores fitted, not measured on a hole); the legend names PETG / PETG-CF. |
| `atech_fit` user values | A D-bore that is not a D, a negative clearance and a broken `active` were accepted. | Refused; `load_user` never raises. |
| `cad.d_bore` | The default 12 mm went through a thinner part without a word; on 3 mm it blamed `at` and `axis`. | Keeps 1 mm of floor when the whole 8.8 mm shaft still goes in (a part of 9.8 mm and up), else goes through as before; a line says which. (The first fix always kept the floor: see the second check.) |
| `cad.wheel(flat=)` | On a small wheel the error said "use hub_d <= 7.16" when the keyed hub needs 7.4, and the size it led to was refused for its spoke windows. | Both messages name the smallest wheel that builds (25 mm with windows, 19 mm with bar spokes). |
| `cad.fit_coupon` | Module and shaft sizes were typed. | Read from the measured values. |
| `./check` FIT lines | A D-bore turned away from the shaft's flat was "the push fit that printed". | A note with the angle and the call that fixes it. |
| `./check` PRINT lines | A bottom tilted under a degree was "already down"; Export does not agree. | Export's tolerance. |
| `./check` | A guessed size was a sentence in TRAPS only. | TRAPS R41 tells the agent to mark the constant `# MEASURE: <what>, assumed <value>`; `./check` lists the marks in a MEASURE line. |
| Fit record | "Too tight" on the preload made it tighter. A printer name with a bar split the profile. A design script could plant its own record. Results from PLA were used for a PETG-CF print. A rebuild without a turn used the old copy. | Fixed, each with a test: the record is always written (empty when there is none), a build takes the profile of the filament Bambu Studio has selected, and the panel refreshes the copy before every final build. |
| Fit test window | "Forget" made another printer's results the ones in use. "Too tight / too loose" had no way in. | Forget puts none in their place, and the window says whose results the next design uses (another printer's for the same filament may, when it is the only one); the window has the verdict row. |
| Slicing | Missing template files, the fall-back to preset files and an empty model id were silent. Two AppImages: the older was taken. "Show files" ran `open` on Linux. | Said in the result and in `print.json`; the newer file; the system's opener. |
| TRAPS, CHANGELOG, README | "Each of these cost a print", "does not drive", "0.3 mm per side did", a first layer "0.3 mm wide", and the wheel plate's times were more than Gustav's records say. | Reworded to what is on record, each number with its step. |
| `atech_mech` | Its snap strain (2 % / 4 %) disagreed with the fit table's (1.5 % / 3 %). | One value, the fit table's. |
| Reference texts | Still pointed at round 3.3 bores on motor shafts. | Point at `cad.d_bore`. |

Left open, on purpose (all under Later): asking after a print and reading
`qa.json`; bores that are not true cylinders; a real print and a real Bambu
Studio run; the examples.

What the review confirmed as right: the module meshes in this repository
are newer than the set Gustav sent (his are this repository's import of
4 Oct), so they were not swapped; `cad.motor_shaft` gives the shaft's tip,
axis and flat correctly in 18 placements; the board is 7.00 thick; the
USB-C module's receptacle is at the right end; nothing in the branch
changes a port rule.

### The test suite after the review's fixes

The same run as before (every module, one process each), this time with
`ATECH_FREECADCMD` naming the built app's `freecadcmd`, so that tests which
are skipped in a worktree run:

| | modules | tests | failing tests |
|---|---|---|---|
| before the fixes | 127 | 2556 | 71 |
| after the first review's fixes (the working tree before they were committed) | 127 | 2574 | 72 |
| at the final commit, after the second check | 128 | 2600 | 72 |

The last row has the same 72 failing tests as the row above it: none new, none gone.
In the middle row `test_cadwf_r1295` (written during that run) is not counted. No
failure comes from the fixes:

- Five tests that failed before pass now (`test_port_rules`,
  `test_agent_integration_r500`): they needed the built app's FreeCAD.
- Six tests fail that did not before. All six were skipped before, and they
  fail in the same way on the untouched repository when it is run with the
  same setting:
  - `test_default_projects` (4): the two projects the app ships with break
    the port rules (see Later).
  - `test_design_first_r600` (1): a real prompt is 40 000 characters against
    that test's 32 000. Its sibling test fails for the same reason on both
    sides.
  - `test_build_ws` (1): the headless suite, which contains the two above.

## The second check (27 Nov 2026): the fixes themselves

The three fix commits were then checked by four more reviewers, one per
area, and each of their findings was challenged by another. 32 stood, 4
were refuted. One was serious, and it was in a fix:

- **`cad.d_bore` could leave a floor where the shaft goes.** The first fix
  always kept 1 mm of floor in a thin part. On every hub from 5 to 9 mm
  that floor sat where the 8.8 mm shaft's tip reaches, and the recipe the
  kit documented drilled from the far side, which put the floor at the
  gearbox. A real motor under `./check`: "interference FAIL", while the FIT
  line called the bore "the push fit that printed". Now a floor is kept
  only when the whole shaft still goes in; otherwise the bore goes through,
  as it did before this work, and says so. The recipe (TRAPS R33, the
  `motor_shaft` docstring) drills from the gearbox side, the way the shaft
  points. A test pushes a model of the shaft into hubs from 2 to 16 mm.

The others, by area:

| Where | What was wrong | Now |
|---|---|---|
| Print check | Above 1500 faces a part was read from its mesh, which lost a small flat base: a false "no flat side" on a mesh-made ball with a 36 mm2 base, and another side than Export. | Every planar face is read, in time that grows with the face count (7700 faces in a second); above 20 000 faces or past the time budget the part is "not judged". |
| `cad.d_bore` | `at` 0.05 mm off the face, or a groove in the far side, slipped past the thickness measure. | Measured on five lines across the bore, from up to 0.3 mm before the face. |
| FIT lines | A bore with two flats was "the push fit that printed" or "turned 180 degrees", whichever face came first. A round 3.4 bore was told it "may not go on without drilling". The "turned" note claimed an overlap from 10 degrees; it starts at 11.3. | A note of its own for two flats; drilling is named only for a bore that prints under the shaft; "the two D shapes do not line up". |
| MEASURE line | The agent was never told to write the mark it looks for; a `#` inside a string counted as a comment. | TRAPS R41 shows the mark; comments are read as Python reads them. |
| Print results | With the person's own filament preset selected in Bambu Studio (or none), the printer's default PLA was taken as loaded and their results were dropped. PLA-CF was read as PLA; "PLA Basic" typed in the window never matched. | Only what is selected counts, a preset of their own is followed to the system preset it inherits, and filament kinds are told apart. |
| Print results | A later puck result undid a verdict the person had given. "Too loose" by more than a clearance was refused with the whole Save. A link planted at the record's name in a chat folder was written through. The final build could be skipped for a preview built with the older record. | What the person said is kept; a clearance stops at 0 and says so; the file is never written through a link; the final build runs when the record changed. |
| Fit test window | "Forget" said "the app's own values are used" when another printer's results for the same filament would be. | The window says whose results the next design uses. |
| Slicing | The Share window slices too and passed none of the cautions on. The printer's model file was looked for in one folder only. With no include list and no template, the generic start G-code was used without a word. The caution said "start and filament-change G-code" whatever was missing. | Share shows the cautions; the app's own folders are searched; the generic start block is named; the sentence names what is missing. |
| Fit table | `press` 0.00 "as modelled" prints as an interference, the bore that had to be drilled. `hole_shrink` was tagged printed; it was never measured on a hole. "Snug by hand" for 3.4 is on no record. | `press` is 0.15 a side (the press class), assumed; `hole_shrink` is P/A; the wording is what the record says. |
| TRAPS, CHANGELOG | R38 gave 7 h 08 to the wrong step; R40 said "a sleeve or pocket"; "a round bore spins" was left in two places. | Each number with its step; the sleeve only; reworded. |

Two things this check could not settle are under Later: what Bambu
Studio's command line does with PLA on a plate the printer rules out, and
whether a real install keeps a leaf preset without its model file.

## The two default projects, rebuilt (28 Nov 2026)

"Bedside lamp" and "Weather station" are the two projects the default
projects generator test builds, and the first a new user sees. Both broke
the port rules (port 8 takes the USB-C module only, and the USB-C module
no other port; port 12 takes a button only, the board's reset button), so
neither built. Each is now laid out again within the rules. Built with the
rules switched off, the old layouts fail on the port rules only (and the
SDK's warnings that the firmware cannot drive a module on 8 or 12), so the
comparison below is against those builds.

**Weather station.** The screen was on 11 + 12 and the USB-C on 7.

- The screen cannot take the middle pair of the top row (11, 12) without
  using port 12. The middle pair of the other row (3, 4) does not seat a
  screen either: those two ports are 20.2 mm apart, the screen's two
  connectors 20.0, so one header stops 0.05 mm short and its pins press
  0.1 mm into the board's socket (`seated FAIL`, `interference FAIL`).
  Measured on this board, a screen seats on 1+2, 4+5, 9+10, 10+11 and
  13+14, and not on 2+3, 3+4 or 5+6.
- So the screen moved to 10 + 11, 20 mm left of centre, with the lens
  re-centred over it, the keys on 2 + 3 under its two ends, the alert
  light on 14 (top right), and the USB-C on 8 at the right end, its pocket
  and liner mirrored to the right side. The sensor stays on 13 and the hut
  where it was.
- `./check`: CHECK PASS, 0 electrical errors (2 before). The 0.70 mm wall
  warning of the old layout is gone. Every opening's ray count is the
  same, the sensor's ribbon keeps the same gaps (1.31 mm to the hut), the
  print is the same (3 plates, about 201 g, 14.4 h).

**Bedside lamp.** The globe light was cabled from port 8, the USB-C on 2.

- The board stands upright in a round column, so port 8 is at its top or
  its bottom edge. It is now turned so port 8 is at the bottom: the USB-C
  module is cabled from 8 down into the foot, lying flat, its mouth in a
  pocket in the foot's right side, held by pads under it and ribs over it.
  Port 7 is now at the top, so the globe light still rises straight up the
  neck. The two window lights are on 2 and 10, behind the window as before.
  The seam between base and shell moved down to 4 mm, under the USB-C
  pocket.
- The touch button in the foot had been on 7, the only bottom port whose
  ribbon goes straight down. On the turned board that is port 8, so the
  button is cabled from port 6, a side port, and a side port's ribbon
  leaves the board's edge sideways. With the column at its old 35 mm
  radius there were 3 mm for it to turn in, and it went out through the
  column wall. The column is now 40 mm in radius and the foot 65 (the
  foot stays over 1.6 times the column); the key, the screws and the ring
  foot moved out with it, and the screws turned to 30 / 150 / 300 degrees,
  clear of the button's ribbon.
- `./check`: CHECK PASS, 0 electrical errors (2 before), the same openings
  (every light and the USB-C mouth 100 %). Every ribbon was also tested
  point by point against every part (see Later: `./check`'s own overlap
  test missed the ribbon through the wall): all clear, the least gap
  0.30 mm (as the old button ribbon's). The price is size: 130 x 130 x 277
  mm instead of 120 x 120 x 277, about 322 g and 20.1 h on 3 plates
  instead of 293 g and 18.3 h on 2.
