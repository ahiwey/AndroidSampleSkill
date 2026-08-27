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
- Proguard or R8 rules
- pre-existing target working-tree changes
- protected and merge-only target paths
- forbidden source package, brand, and flavor tokens
- Activity/Fragment recreation and callback cleanup when component ownership changes

## Practical rule

If the source change touched any Android-facing component, search for the component's name and related resource identifiers instead of assuming the code file was the only place that changed.

When compilation is needed, expose generated resource and Kotlin errors before starting a full test task. Once compilation is clean, run focused tests once, and run assemble once only when resources, manifest, or component wiring require it.
