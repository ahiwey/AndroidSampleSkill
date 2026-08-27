# Cross-repository file-set fast path

Use this path when the source is another local Android repository, a working tree, or an explicit list of files instead of a commit selector.

## Freeze scope

Capture the source and target roots and branches, the explicit source file list, target dirty files, mapping hints, protected and merge-only paths, and any user-required approval checkpoint. Query project indexes by the requested symbols; do not scan the whole repository for context.

## Generate one preflight dossier

Run:

```powershell
python -m commit_migration analyze --repo <target> --source-repo <source> `
  --file <relative-file-1> --file <relative-file-2> --json
```

The dossier includes file hashes and sizes, declarations, package mapping, direct and related target files, Android resource gaps, target dirty-file collisions, protected/merge-only constraints, and source-brand token hits.

Convert it to a compact matrix before editing:

| Source | Target | Strategy | Preserve | Dependencies | Confidence |
| --- | --- | --- | --- | --- | --- |

Treat missing resources as review candidates: a resource can be migrated with its layout or intentionally replaced by a target equivalent. Never infer `Record*` and `Recording*` as equivalent solely from spelling.

## Read long files safely

First use the dossier and focused searches to locate declarations, lifecycle methods, callbacks, and resource use. For files over 400 lines, read only needed 160-300 line slices:

```powershell
python -m commit_migration slice --file <source-file> --start-line 1 --line-count 240
```

Every slice includes line bounds, total lines, and SHA-256. Before completing a mechanical transfer, verify the expected first and last declarations and the dossier fingerprint. Use `apply_patch` for repository edits.

## Merge by responsibility

Port host contracts and fixed IDs first, then layouts/bindings, lifecycle/state restoration, target-only behavior, source feature behavior, cleanup/callback ownership, resources, and entry-point indexes. A `merge_only_path` must be compared and patched, never replaced wholesale.

## Validate by defect cost

1. `git diff --check` and forbidden source token searches.
2. Resource/Kotlin compile, normally `:<module>:compile<Flavor>DebugKotlin`.
3. Focused unit tests after compilation is clean.
4. Assemble once when XML/resources/manifest or cross-component wiring changed.
5. Manual/device checks for lifecycle, BLE, Wi-Fi, permissions, and process recreation.

On failure, collect all errors with the same root cause from plain build output, fix them together, and rerun only the failed stage.
