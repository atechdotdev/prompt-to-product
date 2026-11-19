# Full prompt to product, and the electrical engineer suite (R1000-R1009)

Asked 16 Nov 2026: "Make it work like a full prompt to product. Also add an
electrical engineer suite. Make it amazing." Plan written the same night.

## Where it stands

A prompt already becomes a checked design: the chat, the 9 design levels and
`./check`. After that, the trail goes cold:

- Nothing after level 9 says "here is your product, here is how to make it".
- Firmware stops at a `project.yaml` the agent may write. The app never shows,
  validates, compiles or flashes it, though the Atech SDK CLI (`atech
  validate / build / upload / check / monitor`) can do all of it.
- The parts list, the print and the order are in a right-click submenu.
- There are no assembly steps for a person.
- Electrically there is a port-level wiring diagram (R960-R963, applied
  tonight) and nothing else: no port map, power budget, rule check,
  connection list, block schematic or bring-up plan.

## Rule for the electrical data

Show only what is published, and say where each fact comes from: the Atech SDK
catalog, presets.yaml, a chip's datasheet, or the user. Pin order, module
currents, I2C addresses on the board and the 8/12 question stay "not known
yet" (see WIRING_PLAN). Planning figures from chip datasheets are labelled as
such, and the user can replace them with measured values.

## Steps

| # | Step | Done when |
|---|------|-----------|
| R1000 | **`agent_kit/atech_electrical.py`** (stdlib, no FreeCAD/Qt). Built on `atech_wiring.build` + `atech_firmware`. It gives a port map (14 ports: module, what the SDK lets the port do, free/used/disputed), each module's electrical facts with their source (chip, signal type, port count, SDK driver), the power budget (loads, supply, totals, power-bank runtime), electrical rule checks (error/warning/note, each with a fix), a connection list (CSV) and netlist (JSON, signal names, no pin numbers), a block schematic and power tree (SVG), a bring-up checklist from the SDK's events and actions, and a markdown report. | Unit tests cover every rule, the budget maths and SVG/CSV/JSON output for all examples. |
| R1001 | **`sdk_tools.py`**: finds the `atech` CLI (PATH, ~/.local/bin, pipx, uv tools) and runs validate/build/upload/check/monitor/emulate as a QProcess with streamed output. Says how to install it when it is missing. | Pure tests with a fake CLI. |
| R1002 | **Electrical suite window (`electrical_suite.py`)**. Tabs: Overview (verdict, rule checks, power summary), Schematic, Wiring (the R962 panel), Ports, Power (editable mA per module, supply choice, power bank), Firmware (project.yaml from the design, Check, Build, Flash, Monitor), Bring-up, Export (one PDF report plus CSV, JSON and SVG). It opens from the modules page ("Electrical…"), the Atech menu and the Make it view. | Offscreen tests; screenshots in light and dark. |
| R1003 | **`product.py`**: the prompt-to-product status of a design in 7 steps (Design, Electronics, Firmware, Parts and cost, Print, Assemble, Order), assembly instructions written from the design, and the product pack (one folder holding a README, the parts list, the electrical report, the wiring and schematic, project.yaml, print files and the assembly steps). | Pure tests. |
| R1004 | **Make it view (`product_view.py`)**: a 7-step stepper, each step with its status, one line and a button that does it (opens the suite, Print, BOM, Get it made, the pack). | Offscreen tests and screenshots. |
| R1005 | **The chat hands over.** When a design passes with no levels left, the chat shows a "Make it" card (steps and Open). Any time: the Atech menu has "Make it…". | Test of the card. |
| R1006 | **The agent.** The API card gets an ELECTRICAL paragraph (the suite exists; write project.yaml at level 9; name ports, never pins). `./check` gets one `ELECTRICAL` line (rule-check counts). Notes only, no new gates. | test_agent_kit and check tests pass. |
| R1007 | **Build the app**, run the gate and the tests, and take offscreen screenshots of the suite and Make it on real examples. | Gate passes; no new test failures. |
| R1008 | **Showcase**: an interactive page of the suite on real examples, plus a sample product pack on the Desktop. | Published. |
| R1009 | **Docs**: CHANGELOG, README, this plan's results. | Written. |

Not tonight: real pin-level schematics or KiCad PCB export (pin order is not
published), flashing a real board (no board on the bench), committing (the
user asks for that).

## Shared tree

Another session (atech-atelier-5c) owns shell.py's Home code, explode_card.py
and R990 (ten new examples). The ownership was agreed by message. These steps
touch shell.py only to add one menu entry, outside Home. check.py changes are
NOTE lines only, written atomically.

## Results (17 Nov 2026, night)

- **R1000 done.** `agent_kit/atech_electrical.py`, 39 tests. Every SDK-sourced
  fact (line roles, I2C addresses, the stepper's 12-24 V) is checked against
  the catalog text. A rule's fix names the free ports the SDK would accept
  ("Move it to ports 1+2, 5+6 or 10+11").
- **R1001 done.** `sdk_tools.py`, 9 tests (a fake `atech` through QProcess).
  Measured with the real SDK (1.0.0a11, ~/dev/atech/python-sdk/.venv): `atech
  build` needs the SDK's own bin folder on PATH (it runs `pio`). The runner
  now puts it first. Without that, the build stopped with "PlatformIO not
  found".
- **R1002 done.** The suite window, 8 pages, light and dark, offscreen tests.
  Driven with the real SDK: a design's project.yaml was validated, compiled
  for the ESP32-S3 (15 s) and run on the emulated board ("boot report:
  POWERON; btn ok, led ok, th ok, screen ok, spk ok").
- **R1003/R1004 done.** `product.py` (16 tests) and the Make it window. Under
  freecadcmd on the real weather station and debug duck builds
  (`fc_product_r1004.py`, 31 checks): the parts list, a 1.4 MB 3MF, a 4.7 MB
  STEP, the wiring and electrical PDFs, the firmware and product.html.
- **R1005 done.** The chat's "Ready to make it" card (Make it, Electrical
  suite) after the last design level, or once per chat after a clean build.
- **R1006 done.** The `ELECTRICAL` line in ./check, measured on the weather
  station: "0 errors, 3 warnings, 2 notes; power: About 460 mA of 1,500 mA
  (31 %)…". The API card has an ELECTRICAL paragraph.
- **Found on the way:** the weather station example puts its screen on ports
  11+12. The real SDK refuses that ("port 'port_12' not found"), and the
  suite says so before anything is flashed. Moved to 10+11, the same firmware
  validates and runs on the emulator. Examples were not moved: the user
  decides about ports 8 and 12.
- **Full suite** (bundled python, offscreen): 187 failures against 166 in
  the earlier baseline. The new ones are:
  - mine, fixed: the menu-count tests and a deleted main-window parent;
  - from the other session's concurrent R990/Home work: quality-prompt
    example list, shell Home source tests;
  - environment: the KiCad parts installed in the profile, the
    fake-CLI-with-spaces family, timing under a parallel build (they pass
    alone).
