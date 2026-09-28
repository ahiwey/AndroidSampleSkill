# Android Follow-up Checklist

Before claiming the migration is complete, quickly inspect whether the migrated change also affects:

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

When compilation is needed, expose generated resource and Kotlin errors before starting a full test task. Once compilation is clean, run focused tests once, and run assemble once only when resources, manifest, or component wiring require it.
