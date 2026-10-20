# Android Follow-up Checklist

Use only the sections relevant to the migrated behavior. For a known value-only edit, do not turn this checklist into a whole-project audit. Before claiming a component migration is complete, inspect its references in:

- `AndroidManifest.xml`
- custom View fully qualified names in layout XML
- `navigation` XML destinations and arguments
- `provider` declarations
- `authority` strings
- imports and fully qualified class names
- resource names and values-based resources
- reflection strings
- route paths or keys
- serialization model names
- ProGuard/R8 rules and their module/variant build configuration wiring
- pre-existing target working-tree changes
- protected and merge-only target paths
- forbidden source package, brand, and flavor tokens
- Activity/Fragment recreation and callback cleanup when component ownership changes

## Feature closure

Trace the selected behavior through entry point → capability/permission/connection gate → action → persistence or protocol → UI/result feedback → cleanup. Mark each affected link as migrated, preserved, intentionally excluded or not verified. Necessary dependencies belong in the migration boundary; unrelated source behavior does not.

- Reuse target entries and infrastructure instead of copying a second network, BLE, notification or navigation stack.
- Check initialization, device readback, capability defaults, unsupported/offline behavior, and reset/unbind cleanup when the feature uses them. An entry that opens successfully does not prove its save action or global callback works.
- For settings, verify saving, feedback and refresh in the affected consumers. For global events, check the existing application/host delivery path rather than assuming the original Activity is always foreground.
- For requests, caches and transfers, list the relevant state × event × expected output before editing. Separate request completion from per-attempt callbacks; keep one owner for cancellation, connection teardown and temporary files. Include account/device/language isolation only where the selected feature requires it.

## Data and API compatibility

- Compare source/target endpoint, request fields, units, dates, response shape and serializer configuration. Use the actual target model helpers and saved data, not similarly named fields. A compatible UI does not imply compatible payloads.
- Check representative empty, legacy and malformed values at changed parsing boundaries (for example, a JSON array persisted as text must not be split as a plain numeric list). Preserve valid old data; do not clear storage to make validation pass.
- For Room changes, derive the next version from the target, adapt tables/DAO/entities, register a nondestructive migration in its existing chain, and check defaults, nullability, indexes and schema agreement. Source database version numbers must not overwrite the target's history.
- For V1 → V2 or cache changes, define when old rows/preferences are readable history, eligible cache, or explicitly converted data. Keep the approved scope for history pages and hidden entries; hiding UI alone does not remove underlying requests.
- Verify representative upgrade paths and ownership keys where possible. State separately when schema/static inspection was performed but actual upgrade/runtime behavior was not exercised.

## Resources, encoding and presentation

- Preserve the target file's encoding, BOM and newline convention. Use explicit encodings in scripted edits; avoid PowerShell/default-encoding or terminal-output round trips when copying non-ASCII text. Check touched comments and resource values against original/source text, not only XML well-formedness. Review new replacement characters or mojibake relative to the baseline without flagging legitimate language text as corruption.
- Migrate required resource keys into the target's existing locale set, preserving placeholders, escaping and `translatable` semantics. For a few existing value-only keys, use targeted coverage/XML/diff checks rather than sorting or auditing every resource. Do not restore an entire strings file to erase corruption and silently discard required translations or user edits; repair affected content from the captured baseline.
- Reuse target themes, selectors, typography and image tint, including charging/disabled/error states. Check the caller's actual resource/theme usage; copying a custom View is not enough.
- Apply the target RTL rules to XML/style, dynamic layout, custom drawing and necessary callers. Use semantic start/end for navigation/calendar; retain a local LTR timeline when that is the business meaning. Document physical-direction exceptions.
- Keep static layout review, current design comparison, component rendering and actual-host/device verification distinct. Follow existing visual/device authorization and do not add screenshot dependencies automatically.

## Host and lifecycle conversion

For Activity/Fragment transfers, follow [cross-repo-fast-path.md](./cross-repo-fast-path.md#merge-by-responsibility). Verify toolbar actions, host-specific visibility, stable IDs, restored instances, state/result delivery and view-lifecycle cleanup. Preserve target-only improvements such as tinting, transfer queues, retry policies and capability gates by comparing behavior, not just class names.

## Obfuscation rule adaptation

For every code migration, check whether the migrated behavior depends on shrinker rules, even when no rule file appears in the selected diff or explicit file set.

- Inspect the relevant source and target module/variant configuration, including `proguardFiles`, `consumerProguardFiles`, and any referenced rule files or includes. Rule filenames may be customized; do not assume only `proguard-rules.pro` exists.
- Trace reflection, serialization, JNI, annotation-driven discovery, and string-based class/member lookup used by the migrated code. Check existing target and dependency consumer rules before adding missing rules; if no adaptation is needed, record the reason.
- Migrate only the rules required by the selected behavior. Apply the confirmed package/class mapping to rule selectors, annotations, inheritance constraints, and member signature types; preserve required member names and attributes. Keep third-party package references unchanged unless that dependency actually changed, and check for stale source-only names.
- Merge with the target's existing rules and preserve user edits. Avoid copying whole source rule files, adding blanket package-wide `-keep`/`-dontwarn` rules, or disabling shrinking/obfuscation to hide migration problems.
- Confirm that adapted app rules are loaded by the intended minified variant and that library consumer rules are wired for downstream apps. Resolve relative rule-file paths and include chains in the target module; a copied but unreferenced file is not integrated.
- Statically verify mapped references, rule-file paths, and configuration wiring. When build validation is authorized or required by the task, use the narrowest relevant minified variant; debug compilation alone does not validate R8 behavior. Report static, minified-build, and affected runtime-path verification separately, explicitly marking any unperformed checks.

## Practical rule

If the source change touched any Android-facing component, search for the component's name and related resource identifiers instead of assuming the code file was the only place that changed.

Verification depth is selected in [workflow.md](./workflow.md#validate-to-the-needed-depth). Do not automatically compile or assemble because this checklist mentions a resource or component; when validation is requested, avoid rerunning stages already covered by a successful task.
