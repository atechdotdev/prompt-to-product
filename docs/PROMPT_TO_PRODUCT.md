# Prompt To Product

The plan to finish the rename from Atech Atelier to **Prompt To Product,
made by Atech.dev**, and to make the app and atech.dev lead to each other.
Started 10 Nov 2026; this plan written 12 Nov 2026.

## Done before this plan

- The rename in the repo: names, ids (`dev.atech.PromptToProduct`), assets,
  env `PTP_*`, theme files, splash ("MADE BY" Atech.dev), credits. The user's
  data, parts and macros are carried over from "Atech Atelier" (migrate.py,
  AppRun), and the installer replaces the old app.
- Kept on purpose: GitHub repo `atechdotdev/atech-atelier`, site routes
  `/atelier` and `/connect/atelier`, auth client `atelier`, Keychain service
  `dev.atech.Atelier`. Renaming these needs GitHub and the site backend.
- R950, the app's links to atech.dev: Home has an "On atech.dev" row, the
  "Made by Atech.dev" line is a link, plus footer, sidebar and account-menu links.
- Site (studio worktree `atelier-checkout`, PR #60): `/atelier` redesigned,
  every visible "Atech Atelier" renamed, `/prompt-to-product` redirects to it.

## The plan

| # | Step | Done when |
|---|------|-----------|
| 1 | **Build caches follow the rename.** `build_macos.sh` and `build_appimage.sh` reuse the FreeCAD download and unpacked app cached under `atech-atelier-build/`. | A build does not download or unpack FreeCAD again. |
| 2 | **Build the renamed Mac app.** `build_macos.sh --app-only --brand-from-repo` gives `dist/build-macos-arm64/Prompt To Product.app`, and the verify_tree gate passes. | The bundle id, name, icon and credits are right, and so are the 34 default projects plus 3 starters. |
| 3 | **Full test suite on the new build.** This includes the FreeCAD tests that were skipped while there was no "Prompt To Product.app". | No failure that the rename caused; any failure that was already there before is listed. |
| 4 | **Migration dry run.** Run the built app headless with a copy of the real profile: projects, trusted builds, sessions and parts arrive under "Prompt To Product". | The copy is complete, and the old folder is left alone. |
| 5 | **Home check, offscreen.** Render Home from the built app without a window, and check the "On atech.dev" row, the made-by link and the footer. | A screenshot looks right in light and dark. |
| 6 | **Site: the Connect page and /more.** The consent page (`/connect/atelier`) shows the new name and looks like the new `/atelier`; /more's AI section matches. | Type check, lint and jest pass, and screenshots at desktop and phone width look right. |
| 7 | **Docs.** README, CHANGELOG (R950 and the site), and this plan's results. | Written. |
| 8 | **Hand-over.** Say what was done, what was not, and what only the user can do. | Reported. |

Not in this plan, because only the user can do it: pushing or merging
(PR #60, the `macos-support` branch), renaming the GitHub repo and the site
routes, installing over the running "Atech Atelier.app", and a test print.

## Results (13 Nov 2026)

1. **Done.** Both build scripts reuse `~/.cache/atech-atelier-build/`. The
   build used the cached DMG and unpacked FreeCAD.app: no download, no 7.5 min unpack.
2. **Done.** `dist/build-macos-arm64/Prompt To Product.app` (ad-hoc signed)
   passes the gate with VERIFY_FAILURES=0. It has `dev.atech.PromptToProduct`,
   all 38 default projects built, the smoke test OK and the seal intact.
   The first build failed the personal-data row: example paths `/Users/a/` in
   a comment in references.py (R930). They are now `/Users/<you>/`, and the new test
   `test_no_personal_paths` catches this before a build does.
3. **Done.** Full suite with the built app's Python: 2118 tests. 164
   failed. The same modules were run on HEAD with the same Python and app, and
   161 of the 164 fail there too: the fake `claude` CLIs cannot start,
   because their `#!` line names a Python path with spaces ("… To Product.app";
   the old "Atech Atelier.app" had a space as well); the library is not found;
   eval files are missing. The rest:
   - `test_account_r860`: the menu gained "Docs on atech.dev". Test updated.
   - `test_check_gates_r280.ArchetypeTable`: a real bug. The R940 product types
     were missing from `atech_geom.ARCHETYPE_GATES`. The table is now generated
     in build.ARCHETYPES' order (31 rows, the 7 image gates kept).
   - R930 named-file chat tests: the same fake-CLI failure as their
     neighbours (R930 is not in HEAD, so no baseline).
   - Already broken, found because the module library was found on a re-run
     (these were skipped in the full run and at HEAD):
     `ExamplesWithRequests.test_every_seed_passes_its_archetype` (the smart
     speaker example has a 0.57 mm wall in strict mode) and
     `test_kit_round12 …test_baseline_smart_speaker_is_inside`. The
     example was not changed. A design fix for the user to decide.
   - `test_shell_round12 …test_focus_chat` fails offscreen, before and after.
4. **Done, with a lesson.** With the built app, the new data dir is
   `…/Prompt To Product/v1-1`, the source is `…/Atech Atelier/v1-1`, and
   trusted_builds.json, sessions.json and parts were copied byte for byte. On
   macOS FreeCAD ignores `$HOME`, so the "dry run" ran on the real profile.
   The new folder it made (copies plus a "done" marker) was removed again, so the
   real first start still migrates everything. The old folder was untouched (663 files).
5. **Done.** Home was rendered offscreen from the built app, light and dark.
   The first version put the atech.dev cards at the bottom, under about 60 projects
   and 35 examples. They are now a pill row under the title: Community
   builds, Board and modules, Docs, Prompt To Product.
6. **Done.** The Connect page shows "Connect Prompt To Product" and its
   connected screen links Community, the board and modules, and Docs. /more's AI
   section has the new name and copy, and links "See what it can make".
   tsc, eslint and jest (113 suites) pass, and the screenshots look right.
7. **Done.** CHANGELOG (atech.dev links, the fixes), README (links to
   /atelier and /community), this plan.
8. See the hand-over message in the chat.

Still open (the user's call): push `macos-support` and update PR #60
(studio); rename the GitHub repo and site routes; install the new app over
"Atech Atelier.app"; fix the smart speaker's thin wall; the /atelier video
still shows the old "Atech AI CAD" wordmark (record a new clip).
