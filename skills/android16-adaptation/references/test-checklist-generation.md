# Android 16 test checklist generation

Use this reference only after the implementation workflow has completed and the user has selected a checklist version. The checklist is a QA execution artifact, not proof that testing has run.

## Timing and choice contract

1. Do not create any checklist during initial audit, planning, code editing, or build verification by default.
2. After authorized code/configuration changes and proportional verification are complete, offer exactly one choice: normal, enhanced, or no checklist.
3. If the original request already names a version, generate without asking again only after the final implementation state is demonstrated and proportionally verified. This also supports a checklist-only follow-up immediately after implementation.
4. If no version is selected, create nothing. Do not silently pick the normal version.
5. Base the checklist on the final repository state, changed files, applicability decisions, verified artifacts, and remaining blockers.

## Version definitions

| Version | Size | Design | Intended use |
| --- | ---: | --- | --- |
| Normal | 30–40 execution points; aim for 36–38 | Merge related state and environment checks into risk-based end-to-end rows while retaining traceability to the covered surfaces | Routine target-36 release regression |
| Enhanced | More than 100 execution points; minimum 101 | Split pages, states, permission transitions, device environments, failure/recovery paths, and release gates into independently executable rows | Major refactor, first high-risk release, broad OEM/peripheral validation, or regulated evidence |

Do not pad either version with duplicate or `NOT_APPLICABLE` rows merely to hit a count. If the applicable project scope genuinely cannot support more than 100 distinct enhanced checks, explain the evidence and ask whether the user wants the maximum evidence-based set instead.

## Derive coverage from the project

Use these inputs in order:

1. The final audit table and its `MUST_FIX`, `CONDITIONAL`, `DONE`, `NOT_APPLICABLE`, `BLOCKED`, and `NOT_VERIFIED` decisions.
2. The code/configuration actually changed during implementation and the call paths or screens affected.
3. The final merged manifest, resolved dependencies, APK/AAB/native reports, and focused automated/build results when available.
4. Reachable activities, fragments, composables, dialogs, WebViews, input pages, long-running tasks, external entry points, and device integrations.
5. Remaining device, account, supplier, policy, and operational release gates.

Exclude disproved `NOT_APPLICABLE` surfaces and state the evidence for exclusion. Do not copy every Android 16 platform change into every app.

## Coverage expectations

Both versions should cover every applicable high-risk surface:

- install/update, cold start, process death, reboot, account state, and minimum supported API;
- edge-to-edge, status/navigation bars, cutouts, IME, dialogs/popups, themes, and representative old-system regression;
- predictive-back start/cancel/complete, three-button back, overlays, unsaved state, WebView history, and protected long-running work;
- runtime permissions, notifications, foreground services, jobs/timers, background recovery, Doze/standby, and reboot behavior;
- applicable BLE bonding/reconnect/key loss, LAN/hotspot/local-network denial and recovery, media/URI, health, external intents, and security paths;
- final 16 KB APK/AAB/ELF/runtime checks whenever any delivered `.so` exists;
- representative tablet, foldable, split-screen, resize, state-restoration, language/RTL, font-scale, theme, and accessibility checks;
- release artifacts, evidence, P0/P1 defect state, rollback, rollout, and monitoring gates.

For the normal version, combine checks that share the same setup and user journey. Keep a `覆盖范围/原编号` field so a composite row can be audited. A row is `PASS` only when all sub-checks listed in that row pass.

For the enhanced version, split at least along these dimensions when applicable:

- each reachable critical page or component;
- gesture start, cancellation, completion, and three-button behavior;
- permission first grant, denial, "don't ask again", partial grant, revocation, and reauthorization;
- foreground, background, killed process, reboot, offline, weak network, Doze, and standby buckets;
- Pixel/reference device, each agreed major OEM, 4 KB and 16 KB, minimum API, tablet, foldable, and freeform/split-screen;
- BLE bond states and key-loss/encryption events; LAN allow/deny/revoke/socket failure/recovery states;
- each shipped ABI and each native-backed feature;
- happy path, cancellation, timeout, interruption, recovery, and repeated-operation behavior for critical transfers or upgrades.

## Output contract

Use the user's requested format. If the user does not name a format and spreadsheet authoring is available, prefer an `.xlsx` workbook suitable for direct QA execution. Otherwise create a Markdown table and state the tooling limitation.

When producing XLSX, use the available spreadsheet skill/tooling and follow its authoring, formula, inspection, and visual-render validation requirements.

Default filenames:

- `Android16_API36_测试清单_正常版.xlsx`
- `Android16_API36_测试清单_增强版.xlsx`

For an XLSX workbook, use these sheets unless the project has an established template:

1. `使用说明`: scope, build/branch/device record, result rules, sampling limits, and evidence requirements.
2. `测试清单`: the selected 30–40 or 101+ execution rows.
3. `环境与门禁`: required environments, prerequisites, release gates, owners, and evidence.
4. `测试汇总`: formula-driven totals by category and priority plus release conclusion.

Recommended test columns:

| Column | Purpose |
| --- | --- |
| 编号 | Stable unique identifier |
| 分类 | Android 16 risk surface or product feature |
| 优先级 | `P0`, `P1`, or justified `P2` |
| 环境 | Device/API/navigation/peripheral profile |
| 覆盖范围/原编号 | Traceability to merged checks, code surfaces, or enhanced parent group |
| 前置条件 | Required state, account, device, permission, and artifact |
| 操作步骤 | Executable tester actions |
| 预期结果 | Observable acceptance result |
| 结果 | `PASS`, `FAIL`, `BLOCKED`, or `NOT_RUN` |
| 证据/缺陷 | Log, screenshot/recording, artifact, or defect link |
| 执行人/日期/备注 | Execution ownership and notes |

Use filters, frozen headers, wrapped text, priority/status conditional formatting, and result dropdown validation. Keep editable input cells visually distinct. Summary values and release conclusions must be formulas referencing the execution sheets rather than hardcoded totals.

## Acceptance checks

Before delivering the checklist:

- verify stable unique IDs and exact row count for the selected version;
- verify every applicable P0/P1 surface and every implementation change maps to at least one row;
- verify normal-version composite rows retain traceability and do not hide unexecuted sub-checks;
- verify enhanced rows are independently executable rather than cosmetic duplicates;
- initialize manual results to `NOT_RUN` and unresolved prerequisites/gates to `BLOCKED`;
- reconcile category and priority totals with the source rows;
- scan formula ranges for `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, and `#N/A`;
- render and visually inspect every worksheet when producing XLSX;
- report excluded surfaces, sampling limits, unavailable environments, and the fact that reduced coverage cannot guarantee zero defects.
