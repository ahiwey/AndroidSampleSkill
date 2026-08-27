---
name: android16-adaptation
description: Audit, implement, verify, and document Android 16 / API 36 compatibility and release readiness for Android apps, with optional post-implementation tester checklists. Use whenever a user asks to upgrade compileSdk or targetSdk to 36, adapt or check an app for Android 16, fix edge-to-edge or predictive back, assess large screens or 16 KB native libraries, investigate API 36 behavior changes, migrate Google Fit, prepare an Android 16 release, or create an Android 16 compatibility test checklist—even when the request is only “is adaptation complete?”.
---

# Android 16 Adaptation

Require a local Android repository. Prefer PowerShell for the bundled scanner; use Gradle, Android SDK/NDK tools, adb, bundletool, and devices only when available and authorized.

Use an evidence-first workflow. Audit before editing, implement only applicable changes, and never turn an unrun manual/device/final-artifact check into `PASS`.

## 1. Establish scope

1. Read repository and module instructions (`AGENTS.md`, `MEMORY.md`, build guidance) using the project's prescribed tools.
2. Inspect `git status --short` and protect unrelated user changes.
3. Determine the request mode:
   - **audit-only**: read and report; do not mutate or build unless explicitly requested.
   - **implementation**: audit, make minimal compatible changes, and run proportional verification.
   - **verification**: inspect current implementation and execute the narrowest checks that prove it.
   - **release-readiness**: include final APK/AAB, device, manual, monitoring, and rollback gates.
4. Identify product type before applying Play policy: phone/tablet, Wear OS, TV, Automotive, or XR.
5. Record app module, variants, min/compile/target SDK, AGP, Gradle, JDK, UI stack, native code, BLE, LAN, health, media, background work, release channel, and available devices.
6. Ask only for a missing choice that materially changes implementation or acceptance. Discover facts from the repository first.

For policy or tool-version claims, re-check the official sources in [references/official-baseline.md](references/official-baseline.md). Treat dates and minimum versions as time-sensitive.

## 2. Produce the first-pass audit

Run the read-only scanner when PowerShell is available:

```powershell
.\scripts\audit-android16.ps1 -ProjectRoot <PROJECT_ROOT> -AppModule <APP_MODULE>
```

If it is unavailable, perform equivalent targeted searches from [references/audit-checklist.md](references/audit-checklist.md). Do not scan build caches or read the whole repository merely to understand it.

For every surface, use exactly one status:

- `MUST_FIX`: required and not complete.
- `CONDITIONAL`: applicable only if the feature exists; further evidence is needed.
- `NOT_APPLICABLE`: disproved with source, manifest, dependency, or artifact evidence.
- `DONE`: code location plus successful verification exists.
- `BLOCKED`: requires a supplier artifact, account, device, product decision, or authorization.
- `NOT_VERIFIED`: implementation may exist, but required proof has not run.

Start with a table containing item, status, evidence/count, primary files, risk, and decision. Static search hits are leads, not proof of a bug.

## 3. Implement Stage A: API 36 release baseline

Read the detailed acceptance checklist in [references/audit-checklist.md](references/audit-checklist.md), then work in the following order.

### Build baseline

- Set the application module to `compileSdk 36` and `targetSdk 36` only when in scope.
- Use at least AGP 8.9.1 for API 36. AGP 8.9 uses Gradle 8.11.1 and JDK 17; re-verify before editing.
- Preserve minSdk, bytecode target, applicationId, signing, versioning, database schema, external APIs, protocol fields, and command timing unless explicitly authorized.
- Do not bundle Kotlin 2, AGP 9, broad dependency modernization, or library-module SDK unification into this migration.
- Inspect resolved dependency versions before upgrading only the libraries needed for compatibility.

### Edge-to-edge

- Treat edge-to-edge as mandatory for target 36 on Android 16; remove reliance on opt-out flags.
- Use AndroidX APIs appropriate to XML/View, Compose, or hybrid UI.
- Handle status bars, navigation bars, display cutout, IME, and relevant side/system-gesture insets separately.
- Base padding/margin updates on captured initial values so repeated inset dispatch is idempotent.
- Do not unconditionally consume root insets. Audit dialogs, sheets, WebView, camera/crop, map, video, lists, and activities outside the shared base.
- Validate gesture and three-button navigation, light/dark themes, cutouts, and input screens.

### Predictive back

- Replace business reliance on `onBackPressed()`, `KEYCODE_BACK`, and permanent top-level interception with supported AndroidX/platform callbacks.
- Preserve page semantics for editing, WebView history, dialogs, selection modes, transfers, upgrades, payments, recordings, and destructive work.
- Keep callback enablement lifecycle- and state-aware.
- Do not use an application-wide opt-out as completion. A component-level temporary opt-out needs an owner, reason, evidence, and removal date.

### Conditional platform surfaces

- **Background work**: audit WorkManager, JobScheduler, alarms, download jobs, fixed-rate executors, services, quotas, stop reasons, restart, Doze, and standby buckets. Change `REPLACE` to `UPDATE` only when repeated periodic scheduling must preserve its cycle.
- **BLE**: if bonding is used, model `ACTION_KEY_MISSING`, `ACTION_ENCRYPTION_CHANGE`, OEM fallback, system pairing UI, and recovery as a state/event/expected-action matrix before editing. Do not alter device protocols or association models without authorization.
- **Local network**: find sockets, LAN HTTP, mDNS/SSDP/NSD, hotspots, native networking, and WebView LAN traffic. Exercise the Android 16 compat flag and handle denial/revocation/socket errors accurately. Do not predeclare a future-platform permission without official support for the target.
- **Health**: map legacy sensor permissions to granular health permissions where applicable; align rationale activity, privacy policy, and store declarations. Test partial grant, denial, revocation, and reauthorization.
- **Intent security**: audit exported components, deep links, nested intents, URI grants, FileProvider, PendingIntent mutability, missing actions, and explicit-intent/filter matching. Do not disable launch security protection to hide failures.
- **Media/text/accessibility**: cover selected-photo access, app-owned photos, MediaStore version assumptions, camera/crop/share, high-glyph languages, RTL, deprecated announcement APIs, and themed icon rendering when used.
- **Platform internals**: audit cross-process ordered-broadcast priority assumptions, hidden/non-SDK reflection, ART-sensitive frameworks, virtual displays, and native/GPU vendor dependencies when present.

### 16 KB native libraries

- Always audit final APK/AAB if any direct or transitive `.so` exists; source-tree checks are insufficient.
- Check every delivered ABI for APK ZIP alignment, AAB page-alignment metadata, ELF `LOAD` alignment, and runtime loading on a 16 KB device.
- Rebuild owned native code with a supported toolchain or obtain compatible prebuilts from the supplier. Without source, do not claim Gradle flags or binary patching as a formal fix.
- Do not silently remove 32-bit or 64-bit ABIs; changing device coverage is a release decision.
- Compatibility mode is not formal acceptance. An incompatible delivered `.so` is a release blocker even if remediation is tracked separately.

### Temporary large-screen strategy

- On phone/tablet apps, audit ignored orientation, resizability, and aspect-ratio restrictions at `sw600dp` and above.
- If full adaptive layouts are out of scope, a temporary restricted-resizability compatibility property may be used only with explicit scope, merged-manifest proof, owner, and removal deadline.
- Do not present this as Stage B completion; the escape hatch no longer applies when targeting API 37.

## 4. Implement Stage B: foldables and tablets

- Inventory reachable pages from manifests, navigation, routes, and callers; separate unreachable/generated components.
- Prioritize launch/auth/home, critical account/device/payment/transfer flows, details/charts/editing, media/chat/WebView, then low-frequency settings/help.
- Use current window size and adaptive size classes, not physical display metrics or device models.
- First achieve no clipping, distortion, inaccessible controls, or lost scrolling; then add constrained content widths or useful list-detail panes.
- Recompute custom drawing after size changes and account for hinges/safe areas.
- Preserve UI and long-running task state across rotation, fold/unfold, split screen, freeform resize, and recreation. Avoid duplicate submissions and restarted transfers.
- Remove the application-level compatibility property when core paths pass; component-level exceptions need owners and deadlines.

## 5. Keep Google Fit retirement independent

Run this work only when dependencies, OAuth scopes, APIs, stored keys, or server fields prove Google Fit is used.

- Inventory data types, scopes, subscriptions, history, server exchange, time zones, deletion, and source identity.
- Introduce an adapter boundary and define Health Connect mapping and deduplication before changing the source.
- Preserve historical preference/database/server keys unless a separately authorized schema or protocol migration exists.
- Prefer a feature flag and staged rollout; avoid combining the first target-36 release with a health-data-source cutover.
- If unused, record dependency, source, manifest, and OAuth evidence for `NOT_APPLICABLE`.

## 6. Verify proportionally

Use [references/verification-and-release.md](references/verification-and-release.md).

1. Discover real Gradle tasks and variants; do not invent task names.
2. Run focused unit/static checks first. Compile when types, resources, manifests, dependencies, or packaging changed.
3. Run release APK/AAB checks only for release-readiness or when the packaging boundary is affected.
4. Keep results separate:
   - automated/static;
   - build/package;
   - emulator;
   - physical device;
   - manual business flow;
   - external/supplier.
5. `BLOCKED` and `NOT_RUN` never count as `PASS`. Emulator evidence does not replace OEM, real peripheral, hotspot, Health Connect, or 16 KB device evidence.

## 7. Offer the optional post-implementation test checklist

Do not generate a test checklist by default. The checklist is a tester handoff derived from the final implementation, so offering it before the code and proportional verification are complete creates stale or speculative cases.

- In **implementation** mode, wait until all authorized code/configuration changes are applied and proportional automated/build verification has finished. Then ask once:

  > 代码已落实。是否需要生成测试清单：正常版（30–40 条）、增强版（超过 100 条），还是不生成（默认）？

- Do not make this offer in audit-only, planning-only, or verification-only work where this task did not implement code.
- If the user already selected a version in the request, do not ask again. Generate it only after the final implementation state is demonstrated and proportionally verified, whether the code was completed in this task or immediately before it.
- If the user chooses not to generate one or does not answer, leave the repository without a new checklist.
- Generate from the final code, audit decisions, applicable features, verification results, and release gates—not from a generic Android 16 list.
- A generated checklist is not evidence that testing ran. Initialize manual results as `NOT_RUN` and unresolved prerequisites or gates as `BLOCKED`.

When the user chooses a version, read and follow [references/test-checklist-generation.md](references/test-checklist-generation.md). The normal version has 30–40 risk-compressed execution points. The enhanced version has more than 100 fine-grained execution points. Do not generate both unless the user explicitly requests both.

## 8. Update the project document and report

If the project has an Android 16 adaptation document, update it in the same change. Otherwise create one only when the user requests a document or gives a destination. Use these seven sections:

1. 结论与适用范围
2. 阶段 A：API 36 首发上架（必须完成）
3. 阶段 B：折叠屏/平板自适应
4. 独立迁移：Google Fit 退役
5. 验证矩阵
6. 发布门禁与灰度
7. 本轮未验证风险

Use [references/report-template.md](references/report-template.md) for the closing report. Lead with `PASS`, `PASS_WITH_RISKS`, or `BLOCKED`, and support it with exact file locations, commands, outcomes, skipped checks, artifacts, external blockers, and release impact.

Before finishing, inspect only the files changed by this task and `git status --short`. Do not clean, reset, reformat, or commit unrelated user changes.
