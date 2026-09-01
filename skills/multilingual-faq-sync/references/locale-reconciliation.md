# Locale reconciliation

Use this workflow only when the required locale set differs from the current branch or a locale is only partially wired.

## Inventory

Build three compact sets without loading full translation files into context:

- Required: the Skill defaults, or an explicit user-provided replacement set.
- Branch: locale codes found in FAQ JSON filenames, locale components/pages, `q_*` route paths, imports, navigation or locale maps, and build entries.
- Effective: the union of required and branch locales.

Run `audit --json` for JSON-backed discovery. Its `requiredLocales`, `discoveredLocales`, `extraLocales`, and `missingLocales` fields cover locale-like JSON files. Use targeted `rg` searches for route/component/registration-only locales.

## Add a missing required locale

Choose one complete working locale as the structural template and trace it end to end. Create every corresponding source used by the project, commonly:

1. A fully translated `<locale>.json` aligned with the English FAQ/item structure. Do not use English as translation fallback.
2. The locale page or component with the correct JSON import and the same rendering behavior as the compatible sibling template.
3. Router import and `/q_<locale>` route node, preserving the project's naming and lazy/eager import convention.
4. Navigation, locale selector/map, static entry, deployment node, or build configuration when sibling locales are registered there.

Search the new locale code across source after creation. A locale is complete only when its source JSON is structurally aligned and its public route resolves through the normal application wiring.

## Preserve branch-only locales

Do not delete, ignore, or downgrade a branch-only locale. Locale-like JSON files in the FAQ directory are automatically included by the script:

- Delete/reorder: apply the same English coordinate locally; no translation is needed.
- Add/update: include translations for every effective locale. The script rejects a spec missing a branch-only locale value.
- Route-only locale with missing JSON: create/repair the JSON first and include the locale explicitly in `--locales` until the audit passes.

## Verification

After content validation, verify locale source symmetry with targeted filename and registration searches. When any page, route, import, locale map, or build entry changed, run the project's narrow build/package command and, when feasible, open each newly created route. Report route verification separately from JSON structural audit.
