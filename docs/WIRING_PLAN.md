# Wiring diagrams in Prompt2Product: plan v3 (R960-R963)

Branch `wiring-diagrams`, worktree `~/dev/atech/atelier-wiring`. The base,
`e2ab15b`, is a snapshot of David's uncommitted working tree, taken on
14 Nov 2026.

## How this plan was made

1. A planner wrote v1 from a code map of ports, cables, firmware, UI and tests.
2. Three reviewers attacked it: a staff engineer, a product/UX lead and a
   QA/release engineer.
3. The planner rewrote it as v2.
4. The same three attacked v2.
5. v3 (this file) takes every point at least two of them agreed on, and lists
   the rest under Rejected.

## What is wrong today

- **The wiring is known but never shown.** A build already knows which module
  is on which port, and whether it is plugged in or on a cable of what length
  (`check._atech_report`). Nothing draws, prints or exports that. The only
  pictures are the board map's sprites and the `ATECH module … on port(s) …`
  lines in `./check`.
- **Only port-level facts exist.** Each port carries DATA1, DATA2, GND, 3.3 V,
  5 V and a rail labelled 12 V. The pin order and which end is pin 1 are OPEN.
  No module has current data.
- **The 12 V rail may be dead.** The Atech SDK says the 12 V rail "carries
  whatever that module is given: nothing regulates it, and the standard USB-C
  module does not feed it". On a board without a power module it may carry
  nothing.
- **The SDK's interface field is a driver type, not the wire.** It calls the
  screen, speaker and microphone "gpio", while their descriptions say SPI or
  I2S. It must not be shown as the electrical interface.
- **Ports 8 and 12 are in dispute.** CAD has 14 identical housings. board.yaml
  says 8 and 12 are reserved (USB-C / Reset). The SDK reserves [8, 12], and its
  board layout shows "USB-C" and "Restart" there. 14_port.md says port 8 takes
  the USB-C module and "data lines reserved". Seven examples put a firmware
  module on 8 or 12 (bedside_lamp, handheld_console, rc_tank, toy_car,
  desk_robot, smart_speaker, weather_station); retro_camera puts a camera on 12.

## What ships

1. **`agent_kit/atech_wiring.py`.** One pure-Python module: stdlib only, py3.9,
   no FreeCAD, no Qt.
   - `modules_from_doc(doc)` is the same walk as `check._atech_report`, plus
     each cable's state. It is used by the app only; check keeps its own walk
     byte-for-byte.
   - `build(atech, firmware=None, names=None, reserved=None, cat=None)`
     returns a wiring dict (schema 1): connections, power modules, the
     8/12 flags, cautions, notes and "not known yet".
   - `svg(w, layout="panel"|"sheet", theme=None)` draws the diagram as
     SVG Tiny (rect, line, text only), deterministic.
   - `power_line(atech)` and `notes(atech)` produce the `./check` lines.
2. **`./check`.**
   - The ATECH line gets how the module connects, inside the existing
     parenthesis: `(plugged in)`, `(by cable 82 mm)`, `(by cable: port 9 82 mm,
     port 10 79 mm)`, or with the seeded flag `(the user's, plugged in)`.
   - One new line per build, computed in `_say_summary` from `res["atech"]`:
     `WIRING power modules: USB-C on port 7` or `WIRING power modules: none`.
   - NOTEs only, never a warning or a problem:
     - robot_arm present: the SDK's 12 V caution, plus "ask the user which arm
       and supply they have".
     - stepper_motor present: it needs its own motor supply.
   - Nothing new goes into the stdout JSON.
3. **The agent's API card.** One WIRING paragraph:
   - the app draws the diagram;
   - name the port, never pin numbers, wire colours or currents;
   - never add a power jack on your own.
4. **The app.**
   - A checkable **Wiring** button in the Atech modules page header swaps the
     board map for a Wiring panel. The panel shows the diagram, then
     selectable text (power modules, each module with its port, connection and
     name in code, Atech SDK cautions in full, Not known yet), then the buttons
     "Open large…" and "Export wiring…".
   - Export writes PDF (one A4 landscape page), PNG (2400×1520) or SVG.
   - "Wiring diagram…" in the Atech menu opens the view.
   - The panel is built only on first use and refreshed only while it is
     visible, and only when the wiring has changed.
5. **Docs.** CHANGELOG R960-R963, a README FAQ paragraph, USABILITY_AUDIT N25
   partly addressed. These go in a separate commit and a separate patch.

## Words the user may see (and nothing else)

- **Title:** "<project> – wiring". **Subtitle:** "Made from the design on
  <date>. Not tested on hardware."
- **Footers:**
  - "Shows which port each module uses, not where it sits in the product or
    the path of its cable."
  - "Every port carries DATA1, DATA2, GND, 3.3 V, 5 V and a rail labelled
    12 V (Atech SDK: fed only by a power module, unregulated). Which pin is
    which is not published yet, so don't wire by pin number from this
    diagram."
- **Cables:** "cable 82 mm (at the last build)". If the cable is stale: "cable
  made for an earlier position – make it again". If a cable is missing: "no
  cable to port N".
- **Ports 8 and 12:** "Port 8/12: board.yaml marks it reserved (USB-C / Reset);
  the Atech SDK board layout shows USB-C / Restart here". This flag appears for
  any module other than usbc. When `atech_ports.RESERVED` is not empty it wins.
- **Not known yet:**
  - the pin order inside a port;
  - how much current each module draws;
  - whether ports 8 and 12 work as module ports (only when one is used);
  - whether a USB-C module on a port other than 8 powers the board (only then);
  - whether the 12 V rail is fed without a power module;
  - "Atech sends a module's pinout on request: hello@atech.dev or Discord."
- **Name in code:** "name in code: arm". Shown only when firmware is on in the
  app (`build.firmware_on()`).
- **Empty state:** "No Atech modules on the board yet. Add one in Atech
  modules or ask the agent, and the wiring appears here."

## Cut, and why

- **Colour legend by driver type, and the driver in the ATECH line:** the SDK
  field is wrong for three modules.
- **The "kept free" mark for power_jack:** the geometry was wrong, the part is
  a placeholder, and no example uses it.
- **The safety-sentence regex:** only robot_arm has a caution, and it is shown
  in full with whitespace normalised.
- **The `sdk_lines` "Line A/B" text, wiring.json, and markdown/QTextDocument
  page 2:** nothing reads them, they look like a pinout, and QTextDocument
  cannot share a QPdfWriter.
- **A W1 note "add a USB-C module" in check:** atech_case, the fast-mode
  default fork, would nag on every first check. The power line says it
  neutrally.
- **Changes to modules_page.power_warning:** it is a tested UI function, and
  its "port 8" wording is not ours to change tonight.
- **Firmware gating inside check:** no such gate exists there.
- **Boards other than the 14-port:** CAD has only the 14-port board.

## Rejected

- **Moving check's walk into atech_wiring:** if the import fails, every Atech
  build loses its module replay.
- **A second PillTabs:** stacked pill controls, and one more animation that
  ignores reduce-motion (N27).

## Done means (measured, reported in the morning note)

- **A1. The checker is unchanged.** Every example's `res["atech"]` is
  byte-identical to the step-0 baseline, there are no new problems or
  warnings, and the new notes appear only on arm_dock.
- **A2. The two walks agree.** `atech_wiring.modules_from_doc` equals
  `check._atech_report` on every example's doc, in the fc test.
- **A3. Honesty grep.** 0 hits across every user-facing string and generated
  SVG for all examples, for pin numbers, "pinout", "pin map", Line A/B, VCC,
  currents (mA/A), wire colours, and tested/verified/safe (except "Not tested
  on hardware").
- **A4. SVG.**
  - Both layouts parse with xml.etree.
  - Two runs are byte-identical.
  - All 14 port numbers are present.
  - The panel's font is at least 10 px at 300 px width.
  - The 8/12 flag is present for toy_car and absent for usbc on 8.
  - robot_arm's caution contains "damages the servos".
- **A5. Export.**
  - The PDF starts with `%PDF` and has 1 page.
  - The PNG is 2400×1520 and has more than one colour.
  - `QSvgRenderer.isValid()` on both layouts.
- **A6. The panel, offscreen.**
  - Toggling keeps the board map's state.
  - The empty state shows.
  - "Firmware off" hides "name in code".
  - The accessible description lists the connections.
- **A7. Existing tests.** The CI lists plus test_modules_page_r300,
  test_firmware_r630 and test_export_tools pass as before. Every Qt suite runs
  with QT_QPA_PLATFORM=offscreen and the SDK catalog pinned to the snapshot.

## Steps

0. Baseline (background): all 44 examples through check with the snapshot SDK.
1. R960 (lead): atech_wiring model, check lines, API card. Tests:
   test_wiring_r960 (pure), fc_wiring_r960 plus its wrapper.
2. R961 (in parallel once the schema is frozen): svg() panel and sheet, plus
   its tests in test_wiring_r960 (pure).
3. R962 (in parallel, against fixtures): wiring_view.py, the modules_page
   button and stack, the menu entry, export. test_wiring_view_r962 runs
   offscreen.
4. R963: ci.yml, CHANGELOG, README, audit, in a separate commit.
5. The post-change run of all 44 examples: A1-A7, and fix anything they find.
6. Hand-over:
   - two patches against `e2ab15b` (code+tests, and docs+CI, both excluding
     `*.orig`), applied with `git apply --check` then `git apply`;
   - a list of the files that overlap David's uncommitted edits.
   - Never merge the branch itself: it contains the snapshot.

## Decisions for David

1. Do ports 8 and 12 work as module ports? Seven examples put modules there.
   **Decided 25 Nov 2026:** no. Port 8 takes only the USB-C module (and the
   USB-C module only port 8); port 12, the reset port, takes only a button
   (the reset button) and is usually empty. Enforced by atech_ports
   (port_rule); the examples that break it are not yet moved.
2. What is the physical pin order, and where is pin 1?
3. Should arm_dock get a power jack? It would need a free cell, the arm's
   voltage and the deck height.
4. Should atech_case get a USB-C module, or keep showing "power modules: none"?

Open facts: how SDK Line A/B maps to DATA1/DATA2; module currents; whether a
power jack alone powers the logic; whether CAD usbc is the standard module or
the PD one; whether usbc off port 8 powers the board.

## Later (not wiring)

The audit's N22/N23/N24 (usage limit, retries, cost), N6 (Trash), #83 (env
overrides), the rest of the rename, the 157 MB board look at startup, and
Help/About each need a product call.
