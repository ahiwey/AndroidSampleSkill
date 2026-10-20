# Cross-repository file-set fast path

Use this path when the source is another local Android repository, a working tree, or an explicit list of files instead of a commit selector.

## Freeze scope

Capture the source and target roots and branches, source HEAD and selected-file fingerprints (including source dirty content), the explicit source file list, target dirty hunks, mapping hints, protected and merge-only paths, and any user-required approval checkpoint. Keep explicitly excluded features and target customizations in the matrix. Query project indexes by the requested symbols; do not scan the whole repository for context.

## Generate one preflight dossier

After the one-time capability probe in [workflow.md](./workflow.md#tool-fallback), use the callable MCP or an available CLI. For the CLI, run:

```powershell
python -m commit_migration analyze --repo <target> --source-repo <source> `
  --file <relative-file-1> --file <relative-file-2> --json
```

The dossier includes file hashes and sizes, declarations, package mapping, direct and related target files, Android resource gaps, target dirty-file collisions, protected/merge-only constraints, and source-brand token hits. If neither tool is available, collect these facts with scoped Git/`rg`, precise reads, hashes and resource XML inspection; the absence of a dossier tool does not block a migration or authorize installing it.

Convert it to a compact matrix before editing:

| Source | Target | Strategy | Preserve | Dependencies | Confidence |
| --- | --- | --- | --- | --- | --- |

Treat missing resources as review candidates: a resource can be migrated with its layout or intentionally replaced by a target equivalent. Never infer `Record*` and `Recording*` as equivalent solely from spelling.

## Read long files safely

First use the dossier and focused searches to locate declarations, lifecycle methods, callbacks, and resource use. For files over 400 lines, read only needed 160-300 line slices:

```powershell
python -m commit_migration slice --file <source-file> --start-line 1 --line-count 240
```

The CLI slice includes line bounds, total lines, and SHA-256. With fallback reads, record equivalent bounds and file hashes. Before completing a mechanical transfer, verify the expected first and last declarations and the preflight fingerprint. Use `apply_patch` for repository edits and preserve text encoding/BOM/newlines.

## Merge by responsibility

Port host contracts and fixed IDs first, then layouts/bindings, lifecycle/state restoration, target-only behavior, source feature behavior, cleanup/callback ownership, resources, and entry-point indexes. A `merge_only_path` must be compared and patched, never replaced wholesale.

For Activity/Fragment conversion, explicitly map toolbar owner/actions, stable container IDs and Fragment tags, restored instances, ViewModel scope, view lifecycle, permissions/results, and callback cleanup. Reuse restored Fragments after recreation instead of adding duplicates. Preserve the target's current image tint and theme resources. Support alternative hosts only when requested; do not wire a new host entry merely to demonstrate reuse.

## Validate by defect cost

Start with `git diff --check`, changed XML/reference checks and scoped source-token searches. Then choose only the needed and authorized checks using [workflow.md](./workflow.md#validate-to-the-needed-depth):

- Resource/Kotlin/Java compilation for a concrete compile need.
- Focused tests for changed behavior, reusing compilation performed by that task.
- Assemble for packaging or an authorized installation, not automatically for every layout change.
- Visual/device scenarios for lifecycle, BLE, Wi-Fi, permissions and recreation only within the current task's authorization.

On failure, collect all errors with the same root cause from plain build output, fix them together, and rerun only the failed stage.
