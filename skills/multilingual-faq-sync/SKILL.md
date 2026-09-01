---
name: multilingual-faq-sync
description: Reconcile and synchronize FAQ routes, locale JSON, additions, deletions, edits, numbering, and translations across the required 11 locales plus any extra locales already present in the branch. Use for localized FAQ files or `q_*` routes, including projects whose English baseline is embedded in Vue/JavaScript instead of `en.json`.
---

# Multilingual FAQ Sync

Synchronize only changed FAQ units. Let the bundled script read and transform full files; keep bulk JSON out of model context.

## Contract

Required locales: `cn,cs,de,en,es,fr,hu,it,ja,pt,sk`. English is the structural baseline. It may be `en.json` or an upstream Vue/JavaScript file containing `items: [...]`; when upstream English exists, update it in the same operation.

The effective locale set is the union of required locales and every locale already represented by source JSON, routes/components, or locale registrations in the current branch. Never drop or skip a branch-only locale merely because it is absent from the required list.

Preserve structure, ordering, numbering style, placeholders, brands, encoding, indentation, BOM, and line endings. Do not edit compiled bundles or ZIP files as sources.

## Fast path

1. Locate only the FAQ directory, English source, and relevant route/import registrations. Inventory locale codes from JSON filenames, locale components/pages, `q_*` routes, imports, navigation/locale maps, and build entries; do not read every locale's full content into context.
2. Audit with compact JSON output. Omit `--base` when English is `en.json`:

   ```powershell
   node scripts/faq_sync.mjs audit --dir <json-dir> [--base <english.vue>] --json
   ```

3. Reconcile the inventory before content operations:
   - If a required locale is absent from the branch, add its complete source surface using a working locale as the structural template: fully translated JSON, locale page/component, imports, route node, and any navigation, locale-map, or build registration used by sibling locales.
   - If the branch contains a locale outside the required list, preserve it and include it in every audit and mutation. Deletions use the shared coordinate; additions and updates require that locale's changed-field translation.
   - If a route/component exists without its JSON, or JSON exists without a reachable route/registration, treat the locale as incomplete and repair the missing side. Do not claim language completion from a JSON file alone.

   Read [references/locale-reconciliation.md](references/locale-reconciliation.md) only when required and branch locale inventories differ or any locale is incomplete.
4. If the audit reports broad pre-existing structural drift, summarize `faqCounts`, `issuesByLocale`, and only the displayed error samples. Do not load more errors or apply coordinates. Ask one decision question: realign/rebuild from English, or perform a separately reviewed semantic repair. Combine this with the missing-language question when both occur.
5. Locate the target without loading full locale files. Search English directly, or search one selected locale and return the English text at the same structural coordinate:

   ```powershell
   node scripts/faq_sync.mjs inspect --dir <json-dir> [--base <english.vue>] --contains <keyword>
   node scripts/faq_sync.mjs inspect --dir <json-dir> [--base <english.vue>] --locale cn --contains <localized-keyword>
   node scripts/faq_sync.mjs inspect --dir <json-dir> [--base <english.vue>] --faq <n>
   ```

6. Put all requested operations into one spec, preview once, then write once. Use `--spec -` to read JSON from standard input when avoiding a temporary file. Deletions need no translation. Additions and updates translate only changed fields for the full effective locale set in one batch. The script automatically includes locale-like JSON files already present in `--dir`, even when they are absent from `--locales`.

   ```powershell
   node scripts/faq_sync.mjs apply --dir <json-dir> --spec <spec.json> [--base <english.vue>] [--locales <csv>] --json
   node scripts/faq_sync.mjs apply --dir <json-dir> --spec <spec.json> [--base <english.vue>] [--locales <csv>] --write --json
   Get-Content -Raw <spec.json> | node scripts/faq_sync.mjs apply --dir <json-dir> --spec - [--base <english.vue>] [--locales <csv>] --write --json
   ```

   The write command reloads the written sources and runs the structural audit before reporting success. Its JSON report lists operation coordinates, target files, written files, FAQ counts, and validation results. Run a separate `audit` only after external edits or when an independent recheck is requested.

7. Run `git diff --check`, search for deletion residue, and inspect only changed source files. Build only if imports, routes, schema, or runtime rendering changed.

For operation fields and examples, read [references/change-spec.md](references/change-spec.md) only when constructing a spec.

## Decision rules

- Use English FAQ/item indexes as cross-locale coordinates only after the selected locale audit passes.
- Treat `requiredLocales`, `discoveredLocales`, and `extraLocales` in the audit report as the language reconciliation inputs; reconcile route-only locales separately because the JSON helper cannot infer arbitrary router conventions.
- Use `inspect --locale <code>` when the user supplied localized wording; apply only the returned English coordinate and precondition.
- Guard every delete/update with `expect_en_contains`; never trust an unverified index.
- Top-level FAQ numbers always become continuous after structural changes.
- `renumber_items: auto` shifts subitem numbers only when the original list is fully numbered; use `all` to force numbering and `none` to preserve text.
- Never silently copy English into another locale, including when creating a missing required locale. Preserve URLs, placeholders, product names, acronyms, measurements, and protocol names.
- Do not install translation plugins for one-off edits. Use a translation provider only when already authorized or when sustained volume justifies credentials, cost, terminology, and review setup.
- Do not rerun translation or full builds after deterministic validation succeeds unless new evidence requires it.

## Token and time limits

- Prefer `audit --json` (12 error samples by default), `inspect --contains`, and `inspect --faq` over printing full files. Increase `--max-errors` only when a specific repair needs more evidence.
- Never load all locale JSON files into model context after structural alignment passes.
- Combine related operations and all changed-string translations into one pass.
- Deletion/reordering is local-only and should not trigger web access or translation.
- Stop after one preview, one write with its built-in reload audit, and one diff review unless a check fails.

## Delivery

Report required, discovered, and branch-only locales; created route/JSON/registration sources; structural coordinates; newly generated translations; numbering/placeholder results; validation commands; and any native-review risk.
