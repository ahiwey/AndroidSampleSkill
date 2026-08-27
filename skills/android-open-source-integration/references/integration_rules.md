# Integration Rules

This file is the main editable rule set for the Android open-source integration skill.

## Overall Goal

Integrate multiple GitHub Android open-source complete-app sources into the current Android project in a compliant, maintainable, and removable way.

Requirements:
1. Add real reachable pages or features.
2. Preserve the existing directory structure and main flows.
3. Do not move original files or perform large unrelated refactors.
4. Gate new branch entries through an `Application`-level switch.
5. Default the switch method to `false`; the user will fill in the later logic.
6. Mark all new or modified blocks with `Insert qc start` and `Insert qc end`.

## Source Requirements

Each source must satisfy:
1. Complete Android app repository from GitHub, not just a tiny library or isolated component.
2. No Jetpack Compose.
3. No `kotlin-android-extensions`.
4. No ButterKnife.
5. No databinding.
6. UI access through ViewBinding or `findViewById`.
7. Kotlin is allowed.
8. AndroidX is allowed; old support libraries are not allowed.
9. GitHub stars below 1500.
10. Prefer sources not obviously published on Google Play.
11. License must be explicit and allow reuse.
12. Adapt and rewrite as needed for the current project style; do not mechanically paste large unchanged blocks.
13. Final selected sources should be complete functional app repositories with multiple screens, real navigation, resources, models, adapters, dialogs, and feature flows.
14. Final selected sources should include image resources such as drawable, mipmap, raw image assets, or UI illustration assets that can be legally reused.
15. App category is unrestricted: notes, health, pet, gallery, tools, finance, education, media, task management, weather, travel, reading, and other complete app types are all acceptable if they meet the technical and license rules.
16. Prefer sources with legitimate Gradle dependencies that are necessary for the imported feature. Within the dependency budget, richer dependency usage is preferred over no-dependency toy projects.
17. Small single-purpose custom-view repositories are low priority and should not be selected unless the user explicitly confirms or they include many sample pages, resources, and realistic screens.

## Minimum Source Gate

Final selected sources should meet these minimums unless the user explicitly approves an exception after seeing the candidate table:
1. At least 8-15 adaptable reachable pages or screens per source.
2. At least 40 reusable image resources per source, counted across drawable, mipmap, raw images, UI illustrations, or similar visual assets.
3. At least 8 legitimate required new Gradle dependencies per source.
4. Complete app shape with real navigation or feature flow, not just a one-screen component demo.
5. Clear license coverage for both code and bundled assets.
6. Enough code and resources to preserve a meaningful feature flow, not just one isolated screen.

If a candidate fails one of these minimums, mark the missing item in the candidate table and do not recommend it by default.

## Rich Integration Gate

The integration should favor breadth and depth. If a run cannot meet these minimums, stop before implementation and return to candidate selection.

Per run minimums:
1. At least 75 planned reachable imported pages or screens across all selected sources.
2. At least 180 planned reusable image/font/raw resources across all selected sources.
3. At least 10 legitimate new Gradle dependencies across all selected sources.
4. At least 90 direct call sites to the same custom `Application` total switch method.
5. Start with 3 selected sources only if they satisfy every rich integration minimum.
6. If 3 selected sources cannot satisfy every rich integration minimum, select 6 sources for the run.

Do not satisfy these minimums with artificial dependencies, duplicate pages, placeholder screens, unreachable screens, or empty resources. If the chosen repositories do not naturally support these numbers, choose larger complete-app repositories.

## License Policy

Preferred licenses:
1. MIT
2. Apache-2.0
3. BSD-2-Clause
4. BSD-3-Clause
5. ISC

Exclude by default:
1. No LICENSE file or unclear license.
2. GPL.
3. AGPL.
4. LGPL.
5. SSPL.
6. Non-commercial, personal-use-only, or no-derivatives licenses.
7. Repositories where GitHub license detection conflicts with the license text and cannot be resolved.

If license status is unclear, mark the candidate high risk and do not select it by default.

## Candidate Repository Review

Before editing code:
1. Find 10-15 candidate repositories.
2. Produce a candidate table.
3. Wait for the user to confirm selected sources. Prefer 6 sources when fewer sources cannot satisfy the rich integration minimums.
4. Do not clone, copy, rewrite, or integrate source code before confirmation.

Candidate table fields:
1. Project name.
2. GitHub URL.
3. Star count.
4. License.
5. Recent update date.
6. Whether it appears to be on Google Play.
7. Technical stack judgment.
8. Importable feature.
9. Estimated page count or screen count.
10. Whether it is a complete app, feature module, sample-heavy demo, or small component.
11. Expected content types: Activity, Fragment, Adapter, View, Dialog, utility class, model, resource, dependency.
12. Whether sample/demo pages are useful and can be adapted.
13. Proposed unified feature alias, such as `note`, `pet`, `gallery`, or `reader`.
14. Whether image resources are present and reusable.
15. Estimated reusable image resource count.
16. Estimated required new Gradle dependency count.
17. Whether the source passes the minimum source gate.
18. Expected import coverage: major original screens imported / major original screens available.
19. Candidate score from 0 to 100.
20. Integration risk.
21. Recommended priority.

## Candidate Scoring

Score every candidate from 0 to 100 so selection favors the user's preferred source shape.

Suggested scoring:
1. Complete functional app structure: 15 points.
2. Many reachable screens or pages: 25 points.
3. Reusable image resources: 20 points.
4. Legitimate required Gradle dependencies: 15 points.
5. Technical compatibility with the current project: 10 points.
6. Clear reusable license: 10 points.
7. Low integration risk and clear removability: 5 points.

Selection rules:
1. Prefer the highest-scoring complete app repositories.
2. Final selected sources should normally score 80 or above.
3. Custom-view-only sources should score no higher than 40 unless they include many sample pages, image resources, adapters, dependencies, and realistic screens.
4. If a lower-scoring source is recommended, explain why it is still useful.
5. Prefer candidates whose expected import coverage keeps most major app screens, rather than candidates that require heavy trimming.

## Asset License Review

1. Do not assume the source code license automatically covers image, font, raw, or media assets.
2. Inspect repository license notes, asset folders, README, attribution files, and obvious third-party asset references.
3. If bundled images or fonts have unclear origin or unclear reuse rights, do not import them by default.
4. Prefer assets that are clearly covered by the repository license or explicitly marked reusable.
5. If image resources are unclear but the code source is otherwise good, either exclude those assets, replace them with project-owned assets, or ask the user before importing.
6. Record asset-license notes in `docs/insert_qc_sources.md`.

## Pre-Implementation Budget

After the user confirms selected sources, but before editing files, output a budget table and wait for confirmation.

Budget fields for each source:
1. Estimated Java/Kotlin files.
2. Estimated XML files.
3. Estimated image/font/raw resources.
4. Estimated string/color/style/menu/anim resource entries.
5. Estimated remote dependencies.
6. Estimated modified original files.
7. Estimated Manifest entries.
8. Estimated R8/ProGuard rules.
9. Planned existing-flow branch entry location.
10. Planned removal method.
11. Planned new reachable page or screen count.
12. Planned `Application` switch call-site count.
13. Planned reusable image/font/raw resource count.
14. Planned new Gradle dependency count.
15. Planned source screen coverage.

Summary fields:
1. Total estimated new files.
2. Total estimated remote dependencies.
3. Total estimated modified original files.
4. Total planned new reachable pages or screens.
5. Total planned `Application` switch call sites.
6. Total planned reusable image/font/raw resources.
7. Total planned new Gradle dependencies.

Before the budget table, inspect and summarize:
1. Existing root package and source-layer packages.
2. Existing custom `Application` location.
3. Existing dependency versions that may affect imported sources.
4. Existing resource names that may collide with each unified feature alias.
5. At least 90 candidate existing-flow branch locations where the `Application` switch can reasonably gate new pages or features.
6. Any alias collision plan, such as `note`, `note1`, `pet`, or `pet1`.
7. Existing package names, layout names, drawable names, string names, id names, style names, menu names, anim names, raw names, and font names that may collide with imported aliases or resources.
8. A page-entry mapping table that explains each planned switch call site, the original project location, the imported page or feature it opens, and why the branch is reachable.
9. A source coverage table that lists the selected source's major original screens and whether each screen will be imported, adapted, merged, or excluded.

Budget limits:
1. Integrate 3 sources only when 3 sources satisfy every rich integration minimum; otherwise integrate 6 sources per run.
2. Suggested total new files: 350-1200.
3. Hard maximum total new files: 2000.
4. If estimated new files exceed 1200, explain why and wait for confirmation.
5. If estimated new files exceed 2000, reduce scope or ask for explicit approval.
6. Suggested total remote dependencies: 10-48.
7. Hard maximum total remote dependencies: 60.
8. Each source should add at least 8 necessary remote dependencies.
9. Each source may add 8-12 necessary remote dependencies when those dependencies are genuinely required by the imported complete app.
10. If one source needs fewer than 8 dependencies, explain why and prefer choosing a richer complete-app source unless the user explicitly approves the exception.
11. When multiple candidates are otherwise equal, prefer the one with more pages, more reusable image resources, and more legitimate required dependencies, as long as the hard limits are not exceeded.
12. Do not add artificial or unused dependencies just to increase dependency count.
13. A low-dependency final implementation fails the user's current preference unless the user explicitly approved the lower dependency count in the budget.
14. If planned reachable pages drop below 75 total, planned reusable image/font/raw resources drop below 180 total, planned new Gradle dependencies drop below 10 total, or planned custom `Application` switch call sites drop below 90 total, stop and revise source selection before editing.

## Source Coverage and Trimming

Do not over-trim selected complete apps. The point is to keep many pages, resources, dependencies, and meaningful feature flows.

Allowed trimming:
1. Original standalone app shell files that conflict with the current project.
2. Launcher-only setup.
3. Original `Application` class when it conflicts with the current app.
4. Signing, release, CI, tests, unrelated scripts, or global build-system files.
5. Screens that require unavailable backend services, accounts, private APIs, paid SDKs, or unsafe permissions, when no simple local adaptation exists.

Avoid trimming:
1. Normal list/detail/edit/settings/help/about/profile/statistics/search/filter/preview pages.
2. Adapters, models, dialogs, and utility classes used by imported pages.
3. Image resources used by imported pages.
4. Legitimate Gradle dependencies required by imported pages.
5. Sample/demo pages that provide useful reachable screens or realistic UI states.

Coverage expectations:
1. If a selected source has 20 or fewer major app screens, plan to import or adapt at least 90% of them.
2. If a selected source has more than 20 major app screens, plan to import or adapt at least 80% of major screens from that source.
3. Every excluded major source screen must have a clear reason in the coverage table.
4. If coverage is low because the source is hard to adapt, return to candidate selection instead of delivering a tiny integration.

## Page Entry Mapping

Before editing, create a mapping for every planned `Application` switch call site.

Each mapping row must include:
1. Original project file.
2. Method or callback.
3. Existing user action, state, or flow condition.
4. Exact custom `Application` total switch method call, such as `isInsertQcEnabled()`.
5. Imported source.
6. Imported page or feature opened.
7. Whether the path is reachable when the switch returns `true`.
8. Removal notes.

The mapping must contain at least 90 planned call sites before implementation starts.

## Import Scope

Do not copy entire repositories.

Prefer importing complete functional flows rather than isolated snippets. The goal is to add more real pages, image resources, dependencies, and meaningful feature code while keeping the current project structure stable.

Import planned:
1. Activities.
2. Fragments.
3. Adapters.
4. Custom views.
5. Dialogs.
6. Utility classes.
7. Data models.
8. UI resources.
9. Necessary dependencies.
10. Sample or demo pages when they provide multiple useful screens, realistic UI states, resource coverage, or navigation examples.
11. App feature screens from complete app repositories, adapted into the current app's package, naming, resources, and entry gating.
12. Image resources that are part of the selected app experience and are allowed by the source license.
13. Full local feature flows from complete apps, including list/detail/create/edit/search/filter/settings/statistics/profile/help/about/preview pages when present and adaptable.

Do not import:
1. Whole repository root content without selection.
2. Original standalone app shell files that conflict with the current project, such as launcher-only flow, original application class, original package identity, signing setup, or global build configuration.
3. Unit tests, androidTest, or test fixtures.
4. CI configuration.
5. README images unless they are intentionally reused as app resources and license allows it.
6. Release signing configuration.
7. Unrelated scripts.
8. Unrelated buildSrc or Gradle plugin code.

Do not use "minimal viable import" as the default strategy. Prefer "broad feature import with safe adaptation": preserve many source pages and resources while removing only incompatible shell, build, test, signing, backend, or unsafe pieces.

Custom-view repositories:
1. Avoid sources that only provide one small custom view and very little surrounding code.
2. Do not select custom-view-only sources by default.
3. Allow custom-view sources only when they include many sample pages, configuration screens, preview pages, adapters, image resources, dependencies, or resource-rich demos that can be adapted as real reachable pages.

## Package and Directory Rules

1. Detect the current root package, such as `com.example.app`.
2. Place each source under existing source directories.
3. Use existing package-layer semantics, such as `ui`, `base`, `utils`, `adapter`, `widget`, `model`, `dialog`, `view`, `fragment`, or `activity`.
4. Add a feature subpackage under those existing layers.
5. Do not create a random top-level package such as `insertqc.gallery` if it does not match the project style.
6. If a matching layer does not exist, choose the nearest existing layer rather than creating many new top-level layers.
7. Do not move original files.
8. Assign one unified feature alias per imported repository and use it consistently across packages and resources.
9. Do not use `sample`, `demo`, or the original repository's sample package wording in new package or directory names.
10. Derive the alias from the repository's actual feature domain, not from whether the source code came from a sample folder.
11. Examples: `StoryNote` should use `note`; `PetHealth` should use `pet`; a gallery app should use `gallery`; a book reader app should use `reader`.
12. Do not use `insertqc`, `insert_qc`, `qc`, or similar marker words in package names, directory names, class names, file names, or resource names. `Insert qc` is only a comment marker.
13. Package and directory names should use only the unified feature alias unless a collision exists.
14. If the target package or directory already exists, append a number to the alias: `note`, `note1`, `note2`; `pet`, `pet1`, `pet2`.
15. Example: use `<root>.ui.mine.note`, not `<root>.ui.mine.insertqc.note`.

Examples:
1. For a note feature:
   - `<root>.ui.note`
   - `<root>.base.note`
   - `<root>.base.dialog`
   - `<root>.utils.note`
2. For a gallery feature:
   - `<root>.ui.gallery`
   - `<root>.adapter.gallery`
   - `<root>.model.gallery`
   - `<root>.utils.gallery`
3. For a preview feature:
   - `<root>.widget.preview`
   - `<root>.base.dialog`
   - `<root>.ui.preview`
4. For a pet health feature:
   - `<root>.ui.pet`
   - `<root>.adapter.pet`
   - `<root>.model.pet`
   - `<root>.utils.pet`

## Resource Naming

1. Assign one unified feature alias per source, such as `note`, `gallery`, `preview`, `pet`, or `reader`.
2. Prefix new layout, drawable, mipmap, menu, anim, xml, raw, font, string, color, style, and id names with the feature alias where practical.
3. Do not overwrite existing resources.
4. Avoid generic names like `title`, `content`, `item_layout`, `activity_main`, or `ic_back`.
5. If referencing existing resources is necessary, explain why.
6. Do not use `insertqc`, `insert_qc`, `_qc_`, `sample`, or `demo` in resource names.
7. Examples: `StoryNote` uses `note_`; `PetHealth` uses `pet_`; a reader app uses `reader_`.
8. If a resource name already exists, append a number before the extension or at the end of the resource name: `note_activity.xml`, `note_activity1.xml`, `note_title`, `note_title1`, `pet_icon`, `pet_icon1`.
9. Use the same collision rule for layout ids, drawable names, string names, color names, style names, menu names, anim names, raw names, and font names.

## Name Collision Scan

Before editing files:
1. Scan existing packages and directories under the current app source roots.
2. Scan existing layout, drawable, mipmap, menu, anim, xml, raw, font, string, color, style, and id names.
3. For each selected source, produce an alias and resource collision plan.
4. Use numeric suffixes consistently when collisions exist, such as `note1`, `note_activity1`, or `note_title1`.
5. Do not overwrite, rename, or move existing project resources to make room for imported resources.

## Application Switch

1. Find the existing custom `Application`.
2. If it exists, add a switch method there.
3. If it does not exist, add one in the existing project style and register it in Manifest without disturbing other app configuration.
4. Prefer method name: `isInsertQcEnabled()`.
5. The method must default to `false`.
6. The method body is reserved for the user to fill later.
7. All added branch entries must check this custom `Application` total switch method.
8. When the switch returns `false`, original behavior must remain unchanged.
9. When the switch returns `true`, added pages and features must be reachable and functional.
10. Prefer direct, readable checks against the custom `Application` total switch method at the existing-flow branch point. Do not hide the check behind unrelated helpers, local booleans, constants, wrapper methods, or feature-flag abstractions.
11. The switch check should be placed near the branch that opens the new page or executes the new feature, so the relationship is easy to audit and remove.
12. The 90+ required call sites must call this same custom `Application` total switch method, such as `isInsertQcEnabled()`.

## Application Switch Call-Site Density

1. Each integration run must plan and implement at least 90 meaningful call sites that directly call the custom `Application` total switch method before opening an integrated page or executing an integrated feature.
2. These call sites should be in original project flow files or original project entry/interaction code that is being modified to connect the imported features.
3. Calls inside the imported feature's internal implementation do not count toward the 90-call-site minimum unless they gate a distinct imported subpage or imported subfeature from an existing reachable imported flow.
4. Do not create empty, duplicate, unreachable, or no-op switch checks just to increase the count.
5. Each counted call site must guard one real page entry, feature entry, subfeature entry, menu branch, list branch, empty-state branch, success/failure branch, settings branch, or secondary action.
6. Prefer distributing the 90+ call sites across multiple existing pages, flows, adapters, menu handlers, and click handlers when the current project structure supports it.
7. The pre-implementation budget must include the planned switch call-site count per source and total planned switch call-site count.
8. After implementation, report the actual switch call-site count and list the files/methods where the checks were added.
9. If fewer than 90 meaningful call sites are possible without harming the existing app structure, stop before editing and ask the user whether to choose larger source apps, select 6 sources, or select different entry flows.
10. The switch method itself counts as the control point but does not count toward the 90 call sites.
11. The 90+ call sites should be distributed across at least 12 original project files or at least 6 existing user flows when the current project structure allows it.
12. Do not place all 90 checks in one Activity, Fragment, Adapter, or method unless the user explicitly approves after reviewing the page-entry mapping.
13. Each counted call site must be documented with trigger condition, target page or feature, source repository, and removal notes.

## Entry Integration

Use existing-flow branch entries:
1. Do not add one centralized entry page.
2. Do not add prominent homepage buttons unless the project already has a matching pattern.
3. Inspect existing click handlers, navigation, menus, list item logic, empty states, settings rows, success/failure branches, or secondary actions.
4. Choose low-impact, semantically reasonable branch points.
5. Keep branch code short; it should only check the `Application` switch and route to the new feature.
6. Prefer branch points that can naturally connect to many different imported pages or subfeatures, so the 90+ switch call sites are meaningful and maintainable.
7. Do not route all imported pages through a single hidden dispatcher just to reduce visible integration work; the original project should visibly gate many distinct new page or feature entries through the custom `Application` switch.
8. Each entry branch should map to a specific imported page or subfeature; avoid generic "open random imported page" behavior.

Do not use:
1. Constant-false conditions.
2. Impossible string comparisons.
3. Unreachable branches.
4. Dead code.

## Manifest and Permission Safety

1. New activities default to `android:exported="false"`.
2. Do not add dangerous permissions unless necessary and explicitly confirmed.
3. Do not add background services, receivers, providers, file providers, deep links, schemes, or intent filters unless necessary and explicitly confirmed.
4. Do not modify launcher Activity, application theme, `allowBackup`, `networkSecurityConfig`, `usesCleartextTraffic`, or other global settings unless explicitly confirmed.
5. Put new Manifest entries inside `Insert qc start` and `Insert qc end`.

## R8 and ProGuard

1. Do not add broad keep rules such as `-keep class ** { *; }`.
2. Add keep rules only if required.
3. Scope keep rules to the new packages, specific classes, or specific dependencies.
4. Put new keep rules inside `Insert qc start` and `Insert qc end`.
5. Explain keep rules in `docs/insert_qc_sources.md`.

## Dependency Rules

1. Reuse current project dependencies and AndroidX first.
2. Avoid cold, unmaintained, or unclear-license dependencies.
3. Do not add new Maven repository sources, Gradle plugins, or build-system changes unless explicitly confirmed.
4. Put new dependencies inside `Insert qc start` and `Insert qc end`.
5. Document every dependency in `docs/insert_qc_sources.md`.
6. Prefer dependencies with a release or meaningful commit activity within the last 3 years, or stable widely used Android libraries.
7. Avoid obscure JitPack dependencies, private Maven repositories, abandoned libraries, or dependencies with unclear licenses unless the user explicitly approves.
8. For every new dependency, record purpose, license, maintenance status, Maven coordinate, and whether it can be replaced by an existing project dependency.
9. Do not remove or rewrite away all source dependencies just to make integration easier if those dependencies are legitimate and within budget.
10. If a selected source's planned imported pages no longer require any new Gradle dependency after adaptation, explain why in the budget and ask the user before proceeding.
11. Final implementation should normally add at least 10 legitimate new Gradle dependencies across all selected sources.

## Insert qc Markers

Java/Kotlin:

```kotlin
// Insert qc start
// New or modified content
// Insert qc end
```

XML:

```xml
<!-- Insert qc start -->
<!-- New or modified content -->
<!-- Insert qc end -->
```

Gradle:

```gradle
// Insert qc start
// New dependency or config
// Insert qc end
```

Apply corresponding comment syntax in strings, colors, drawables, menu, navigation, Manifest, and R8/ProGuard files. If local comments are unsafe, group new items in a marked section.

## Source Record

Create or update `docs/insert_qc_sources.md`.

For each source, record:
1. Import date.
2. GitHub project name.
3. GitHub URL.
4. Commit hash or tag/version.
5. Star count.
6. License type.
7. License file path or link.
8. Whether Google Play publication evidence was found.
9. Original project technology stack.
10. Actual imported scope.
11. New or adapted packages.
12. Unified feature alias and resource naming pattern.
13. New Gradle dependencies.
14. Manifest additions.
15. Entry integration location.
16. Application switch method.
17. Application switch call-site list.
18. Page-entry mapping list.
19. Asset-license notes.
20. Dependency quality notes.
21. Source coverage table and excluded-screen reasons.
22. Adaptations, renames, and rewrites.
23. Removal steps.

Do not put long source attribution in code files. If needed, add only:

```kotlin
// See docs/insert_qc_sources.md for source attribution.
```

## Removability

Every source must be removable by:
1. Deleting its feature subpackages.
2. Deleting resources that use its unified feature alias and documented numeric suffixes.
3. Removing its Gradle dependency block.
4. Removing its Manifest block.
5. Removing its R8/ProGuard block.
6. Removing its existing-flow branch entry.
7. Removing its documented `Application` switch call sites.
8. Updating `docs/insert_qc_sources.md`.

The final report must include a removal checklist that confirms whether deleting the documented packages, resources, Gradle blocks, Manifest blocks, R8/ProGuard blocks, entry branches, docs records, and custom `Application` switch call sites would remove the integrated code.

## Static Acceptance Checklist

Before reporting completion, verify by static inspection:
1. No `insertqc`, `insert_qc`, `_qc_`, `sample`, or `demo` appears in package names, directory names, class names, file names, or resource names introduced by the integration.
2. At least 90 meaningful call sites directly call the custom `Application` total switch method.
3. The 90+ call sites are documented and each one maps to a real imported page or feature.
4. The switch method itself defaults to `false`.
5. Every new or modified block is wrapped with `Insert qc start` and `Insert qc end` where the file type supports comments.
6. Every selected source has a record in `docs/insert_qc_sources.md`.
7. Every selected source is a complete app-style repository or has an explicitly approved exception.
8. Image/font/raw assets have license notes or were excluded/replaced.
9. New dependencies have purpose, license, maintenance, and replacement notes.
10. Final integration includes at least 75 reachable imported pages or screens unless the user explicitly approved a lower number.
11. Final integration includes at least 180 reusable image/font/raw resources unless the user explicitly approved a lower number.
12. Final integration includes at least 10 legitimate new Gradle dependencies unless the user explicitly approved a lower number.
13. Source coverage table shows the integration did not over-trim selected complete apps.
14. No build, assemble, Gradle sync, or compile command was run unless the user explicitly requested it.

## Project Style

Follow current project conventions.

Default preferences:
1. Communicate in Chinese.
2. Do not add unit tests unless the user asks.
3. Do not run build, assemble, Gradle sync, or compile unless the user asks.
4. Prefer static checks, code reading, and diff review.
5. Use English comments only.
6. Add comments only for non-obvious rendering, timing, scaling, smoothing, compatibility, or business logic.
7. Layout filenames and layout ids use lowercase underscore style.
