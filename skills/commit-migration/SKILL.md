---
name: commit-migration
description: Analyze and port Android changes from commits, branches, or another local repository into the current branch with package, class, path, manifest, XML, resource, and target-working-tree-aware adaptation. Use whenever the user asks to apply or migrate commits, ranges, branch changes, brand-fork behavior, or explicit Activity/Fragment/file sets from another Android repository.
---

# Commit Migration

Use this skill for Android repositories when the user wants to port code changes from a Git selection or an explicit file set in another local repository.

## Default behavior

- Modify only the current working branch by default.
- Never modify the source branch by default.
- Do not automatically `checkout`, `cherry-pick`, or `rebase`.
- Prefer equivalent migration plus Android-aware adaptation over raw patch replay.
- Pause only when mapping confidence is low or current-branch custom behavior would be overwritten.
- Treat every pre-existing target working-tree change as user-owned.
- Honor user-requested interview and plan-approval checkpoints before implementation.

## Supported user phrasing

Treat requests like these as triggers:

- `Apply 45959162 to the current branch`
- `Migrate commit 45959162`
- `Apply 45959162,45959163 to the current branch`
- `Apply 45959162..45959199 to the current branch`
- `Apply the latest 3 commits from branch X to the current branch`
- `Bring this branch's changes into the current Android branch`
- `Move these Activities or Fragments from D:\SourceApp into this app`

## Execution order

1. Parse the selector: Git selection or local repository file set.
2. Read target rules, query its index, and load auto-discovered mapping hints.
3. Snapshot target dirty files and run one structured preflight dossier.
4. Resolve mapping, protected-path, merge-only, dirty-target, and name-collision rows before editing.
5. Read long source files in bounded slices and apply equivalent changes in the target repository.
6. Validate in the order static checks → compile → focused tests → assemble.
7. Run the Android follow-up checklist before claiming completion.

## Preferred tools

### MCP first

If the plugin MCP server is available, prefer:

- `analyze_android_commit_migration`
- `build_android_mapping`
- `collect_android_followups`
- `analyze_local_android_migration` for a local source repository and explicit files

### CLI fallback

If MCP is unavailable, use the CLI:

```powershell
python -m commit_migration analyze --repo <target-repo> --commit <sha>
```

Repeat `--commit` for multiple commits, or use:

```powershell
python -m commit_migration analyze --repo <target-repo> --range A..B
python -m commit_migration analyze --repo <target-repo> --branch origin/feature_x --recent 3
```

For a local cross-repository file set:

```powershell
python -m commit_migration analyze --repo <target-repo> --source-repo <source-repo> `
  --file <source-relative-path> --file <another-source-relative-path> --json
```

For a source file over 400 lines, never print it whole. Read bounded slices:

```powershell
python -m commit_migration slice --file <absolute-source-file> --start-line 1 --line-count 240
```

## What to adapt

Always consider:

- package roots
- file paths
- same-responsibility classes with different names
- imports and fully qualified class names
- `AndroidManifest.xml`
- custom View references in XML
- navigation XML
- `provider` and `authority`
- resource names and values XML entries
- reflection strings
- routing strings
- serialization model names
- Proguard or R8 class references
- target dirty-file collisions
- protected and merge-only paths from repository hints
- source brand/package tokens that must not remain

## References

- [workflow.md](./references/workflow.md)
- [android-mapping.md](./references/android-mapping.md)
- [android-checklist.md](./references/android-checklist.md)
- [cross-repo-fast-path.md](./references/cross-repo-fast-path.md)

## Repo-specific hints

If the target repository provides mapping hints, use them first. The expected format is shown in:

- [mapping_hints.example.json](./assets/mapping_hints.example.json)

Auto-discovery includes `.commit-migration/mapping_hints.json`, `.codex/commit-migration/mapping_hints.json`, and `AGENTS/commit-migration-hints.json`.
