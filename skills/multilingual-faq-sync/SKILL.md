---
name: multilingual-faq-sync
description: Synchronize FAQ JSON additions, deletions, edits, numbering, and missing translations across the default 11 locales `cn/cs/de/en/es/fr/hu/it/ja/pt/sk`. Use for localized FAQ files or `q_*` routes, including projects whose English baseline is embedded in Vue/JavaScript instead of `en.json`.
---

# Multilingual FAQ Sync

Synchronize only changed FAQ units. Let the bundled script read and transform full files; keep bulk JSON out of model context.

## Contract

Default locales: `cn,cs,de,en,es,fr,hu,it,ja,pt,sk`. English is the structural baseline. It may be `en.json` or an upstream Vue/JavaScript file containing `items: [...]`; when upstream English exists, update it in the same operation.

Preserve structure, ordering, numbering style, placeholders, brands, encoding, indentation, BOM, and line endings. Do not edit compiled bundles or ZIP files as sources.

## Fast path

1. Locate only the FAQ directory, English source, and relevant route/import registrations. Do not read every locale into context.
2. Audit with compact JSON output. Omit `--base` when English is `en.json`:

   ```powershell
   node scripts/faq_sync.mjs audit --dir <json-dir> [--base <english.vue>] --json
   ```

3. If required locale files, routes/nodes, FAQs, or translations are missing and the user has not decided whether to repair them, ask one concise interview question listing the missing locale codes. If the user already requested all 11 languages or said to fill missing content, proceed without asking. If they decline, use `--locales` with the existing set only when that selected structural audit passes, and report the remaining difference.
4. If the audit reports broad pre-existing structural drift, summarize `faqCounts`, `issuesByLocale`, and only the displayed error samples. Do not load more errors or apply coordinates. Ask one decision question: realign/rebuild from English, or perform a separately reviewed semantic repair. Combine this with the missing-language question when both occur.
5. Locate the English target without loading the source file:

   ```powershell
   node scripts/faq_sync.mjs inspect --dir <json-dir> [--base <english.vue>] --contains <keyword>
   node scripts/faq_sync.mjs inspect --dir <json-dir> [--base <english.vue>] --faq <n>
   ```

6. Put all requested operations into one spec, preview once, then write once. Deletions need no translation. Additions and updates translate only changed fields, producing all required locales in one batch.

   ```powershell
   node scripts/faq_sync.mjs apply --dir <json-dir> --spec <spec.json> [--base <english.vue>] [--locales <csv>]
   node scripts/faq_sync.mjs apply --dir <json-dir> --spec <spec.json> [--base <english.vue>] [--locales <csv>] --write
   node scripts/faq_sync.mjs audit --dir <json-dir> [--base <english.vue>] [--locales <csv>]
   ```

7. Run `git diff --check`, search for deletion residue, and inspect only changed source files. Build only if imports, routes, schema, or runtime rendering changed.

For operation fields and examples, read [references/change-spec.md](references/change-spec.md) only when constructing a spec.

## Decision rules

- Use English FAQ/item indexes as cross-locale coordinates only after the selected locale audit passes.
- Guard every delete/update with `expect_en_contains`; never trust an unverified index.
- Top-level FAQ numbers always become continuous after structural changes.
- `renumber_items: auto` shifts subitem numbers only when the original list is fully numbered; use `all` to force numbering and `none` to preserve text.
- Never silently copy English into another locale. Preserve URLs, placeholders, product names, acronyms, measurements, and protocol names.
- Do not install translation plugins for one-off edits. Use a translation provider only when already authorized or when sustained volume justifies credentials, cost, terminology, and review setup.
- Do not rerun translation or full builds after deterministic validation succeeds unless new evidence requires it.

## Token and time limits

- Prefer `audit --json` (12 error samples by default), `inspect --contains`, and `inspect --faq` over printing full files. Increase `--max-errors` only when a specific repair needs more evidence.
- Never load all locale JSON files into model context after structural alignment passes.
- Combine related operations and all changed-string translations into one pass.
- Deletion/reordering is local-only and should not trigger web access or translation.
- Stop after one preview, one write, one post-audit, and one diff review unless a check fails.

## Delivery

Report changed sources, structural coordinates, newly generated translations, numbering/placeholder results, validation commands, and any missing-language or native-review risk.
