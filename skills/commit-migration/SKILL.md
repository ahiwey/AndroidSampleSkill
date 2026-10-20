---
name: commit-migration
description: Port selected Android commits, branch features, or code from another local repository into the current branch, adapting behavior, dependencies, data and target customizations. Use for applying commits, brand-fork synchronization, Activity/Fragment transfers, or implementing a feature or fix from a reference Android project. Ordinary in-project edits and Git-history-only operations do not need this workflow.
---

# Commit Migration

Port the selected behavior into the target architecture. A request to follow another Android project can be a small equivalent fix or a complete feature migration; choose the smallest sufficient workflow.

## Default behavior

- Modify only the current working branch by default.
- Never modify the source branch by default.
- Do not automatically `checkout`, `cherry-pick`, or `rebase`.
- Prefer equivalent migration plus Android-aware adaptation over raw patch replay.
- Treat every pre-existing target working-tree change as user-owned.
- Respect requested interview, plan-only, no-build and validation boundaries. Reuse approval already given for the same scope; resolve only new uncertainty, conflicts or protected-path requirements.
- Preserve source comments or disabled code when explicitly requested; copying a disabled capability does not authorize enabling it.

## Supported user phrasing

Treat requests like these as triggers:

- `Apply 45959162 to the current branch`
- `Migrate commit 45959162`
- `Apply 45959162,45959163 to the current branch`
- `Apply 45959162..45959199 to the current branch`
- `Apply the latest 3 commits from branch X to the current branch`
- `Bring this branch's changes into the current Android branch`
- `Move these Activities or Fragments from D:\SourceApp into this app`
- `参考另一个 Android 项目的实现，修复当前逻辑`
- `迁移这个功能，保留当前 UI 和主题，先给方案`

## Choose the scope

- **Quick:** Known files and a bounded equivalent fix, resource update or value change. Read the source behavior, target call sites and intersecting dirty changes; patch and run the highest-value static check. Expand only when evidence reveals dependencies or uncertainty.
- **Feature / cross-component:** Multiple responsibilities, database/API changes, host conversion or asynchronous ownership. Freeze the migration boundary and use one scoped preflight dossier or its Git/`rg` equivalent.
- **Plan-only / prompt-only:** Deliver only what was requested. A plan or question in a final response is not an implemented migration.

For selector handling, tool detection, preflight, approval and resumption, read [workflow.md](./references/workflow.md). For an explicit local file set or Activity/Fragment conversion, also read [cross-repo-fast-path.md](./references/cross-repo-fast-path.md).

## Essential sequence

1. Identify target root/current branch and the exact source commit, branch tip or working-tree file fingerprints. Record include/exclude items, target behavior to preserve and validation scope.
2. Read target rules and the relevant index/hints. Check dirty files, protected paths, merge-only paths and name collisions within this scope.
3. Map by responsibility using [android-mapping.md](./references/android-mapping.md). Separate requested changes, necessary dependencies and unrelated source edits. Resolve genuine conflicts before writing.
4. Port equivalent behavior with bounded source reads. Preserve target text encoding, themes, resource conventions and user changes; do not replace shared files wholesale.
5. Follow only the applicable sections of [android-checklist.md](./references/android-checklist.md): feature closure, data compatibility, host/lifecycle ownership, resources/RTL, and [R8 adaptation](./references/android-checklist.md#obfuscation-rule-adaptation).
6. Run static checks first. Select further verification by task need and authorization; compile, tests and assemble are not mandatory successive stages. Do not repeat a stage already covered by a successful task without new evidence.
7. Report implemented items and exclusions against the confirmed boundary, actual checks, remaining gaps and any temporary validation prerequisites. Separate build, installation, visual checks and runtime evidence.

## Available-tool routing

Probe once for this task. Prefer exposed migration MCP tools (`analyze_android_commit_migration`, `build_android_mapping`, `collect_android_followups`, or `analyze_local_android_migration`). If absent, check whether `commit_migration` is importable in an existing Python environment before using its CLI. If neither exists, continue with scoped Git, `rg` and precise file reads as described in [workflow.md](./references/workflow.md#tool-fallback); do not install tools or repeatedly search for unavailable MCPs.

When the CLI is available:

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

For a source file over 400 lines, locate relevant symbols and read bounded slices. With the CLI:

```powershell
python -m commit_migration slice --file <absolute-source-file> --start-line 1 --line-count 240
```

## Repo-specific hints

If the target repository provides mapping hints, use them first. The expected format is shown in:

- [mapping_hints.example.json](./assets/mapping_hints.example.json)

Auto-discovery includes `.commit-migration/mapping_hints.json`, `.codex/commit-migration/mapping_hints.json`, and `AGENTS/commit-migration-hints.json`.
