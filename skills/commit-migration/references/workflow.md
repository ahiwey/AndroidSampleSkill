# Workflow

## Freeze the requested boundary

Read only the target root/module rules, relevant index entries and migration hints. Record:

- Target root and current branch, source root/ref, and source selection.
- Included behavior, explicit exclusions, target-only behavior to preserve, necessary dependencies, and any disabled source behavior to retain.
- Requested phase (prompt, interview, plan or implementation), existing approval, and allowed verification stages.
- Target staged, unstaged and untracked files in the touched area. Snapshot overlapping diff hunks and file fingerprints; status alone cannot distinguish user changes in a shared file.

For a small known fix, keep this in a short working note rather than creating a dossier or planning files. For a larger migration, summarize the preflight in a compact matrix:

| Source behavior/file | Target | Apply / preserve / exclude | Necessary dependency | Conflict / confidence |
| --- | --- | --- | --- | --- |

Treat source and target dirt as current facts, not permission to stash, reset or overwrite. A dirty target is not automatically a blocker; merge independent hunks and ask only when ownership or behavior actually conflicts. Follow explicit protected-path rules, but do not invent additional approval requirements just because a migration touches a database or protocol.

## Resolve the source selection

- **Single/multiple commits:** Resolve full SHAs and their diffs. Preserve dependency order and filter unrelated hunks, including unrelated changes in a shared file. Do not silently include intervening commits.
- **Range `A..B`:** A is excluded by Git range semantics. List the selected commits before applying; confirm an ambiguous inclusive natural-language range instead of guessing.
- **Branch/recent N commits:** Freeze the resolved tip and selected SHAs. For a requested feature, locate its final implementation and relevant corrections at that tip; do not replay all branch history or choose only its first introduction.
- **Local file set/current source behavior:** Freeze source HEAD plus dirty state and per-file hashes. A clean HEAD does not identify uncommitted source content. Read only the necessary local dependency closure.

Verify abbreviated refs and branch spellings in Git; escaped underscores in prose may be normalized after checking the actual ref. Placeholder SHAs such as `459591xx` and a non-Git range such as `A~B` need clarification. A missing commit is a source-resolution gap, not evidence of an empty migration; inspect local refs first and use an authorized fetch only if necessary.

## Tool fallback

1. Inspect currently exposed tools once. Use migration MCP only when callable; a name in this skill or a configured server is not evidence that it is connected.
2. If MCP is absent, probe the chosen existing Python environment once, for example `python -c "import importlib.util; print(importlib.util.find_spec('commit_migration') is not None)"`. A miss in that interpreter is not a claim about every environment. Use a known project virtualenv if one is already specified.
3. If available, run one scoped CLI analysis. Request compact output; expand only unresolved rows. Do not repeat the dossier unless source/target files changed or new dependencies were found.
4. Otherwise use existing Git and `rg`: `git status --short`, `git rev-parse`, `git show --stat`, `git diff`/`git show` for the selected paths, then `rg` for exact symbols and resource IDs. Apply `-C` to the correct repository and use fixed SHAs for source reads. Read local source files only when that working tree is the selected source.

Use the same preflight facts with either tool route. Do not install a package, configure MCP, or create a checkout just to unblock routine analysis. If an unavailable tool normally provides fingerprints or resource indexing, obtain those facts with existing filesystem/hash/XML tools rather than pretending the dossier ran. Follow project command wrappers such as `rtk`.

## Bound discovery and editing

Start with the requested diff, files or indexed symbols; expand through actual imports, resource references and callers. Batch resource-ID lookups over the relevant resource roots, rather than rescanning every locale for each token. Distinguish declarations (`@+id`) from missing resources and target replacements from genuine gaps.

Read files over 400 lines in focused slices with line bounds and fingerprints, using the CLI or existing file tools. If output is truncated, reduce the next slice; never transfer code from incomplete output. Inspect source and target signatures before adapting helpers, Fragment hosts or near-matching names.

Apply minimal patches. Preserve target encoding/BOM/newlines and compare touched text against the original bytes; do not transcode an entire resource tree to fix a small migration. Restrict source-brand searches to migrated material and distinguish forbidden first-party tokens from intentional third-party names.

## Validate to the needed depth

- Start with `git diff --check`, touched-file parsing/reference checks and preservation of overlapping user hunks. Check resources, mappings and rule wiring where affected.
- Compilation is opt-in through the task/project rules or required by a concrete verification need. Use the narrowest module/variant/task. If a focused test already compiled the affected code, do not compile it again just to follow a sequence.
- For state, parsing or data-migration changes, prefer meaningful boundary/legacy fixtures over tests that only repeat the implementation. Check an existing framework before adding dependencies.
- If compilation is needed before tests, expose resource/Kotlin/Java errors first, fix errors with a common cause together, then rerun the failed stage. Assemble only for an actual packaging/install/wiring check; an XML edit alone does not force an APK build.
- Follow the task's visual/device authorization. A build, a component snapshot and interaction in the real host prove different things. Do not start device discovery, installation or screenshots merely because code was migrated.
- Stop after sufficient successful checks unless a change or new failure warrants another run. Record missing dependencies or temporary validation inputs so success does not imply a reproducible clean build.

## Resume and hand off

On continuation, retain the approved source/target, include/exclude matrix, changed files and evidence for each verification stage. Recheck current diff/fingerprints, then continue missing items; reanalyze only changed or newly implicated paths. A later request about copying images, stashing or improving tools is a separate action and does not replace the migration's outcome record.

When the user reports a repeated failure, inspect the latest screenshot/log, actual installed artifact/resource and current diff before changing parameters. For asynchronous/cache problems, use a small state × event × expected-output matrix and distinguish a whole request from a single retry attempt and the owner of a connection/callback. Compare successful and failed inputs with correlated, redacted evidence before tuning timeouts or retries.

Final delivery follows the approved items and lists checks actually run, skipped stages and concrete remaining gaps. Plan-only, interrupted and unresolved verification sessions are not successful implementations. Do not infer runtime correctness from a completion marker or debug compilation.
