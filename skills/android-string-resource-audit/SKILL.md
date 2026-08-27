---
name: android-string-resource-audit
description: Audit, repair, and safely reorder Android `strings.xml` locale resources against the default language. Use for missing translations, English fallback text, `translatable="false"` exclusions, inconsistent key order, duplicate or nested string nodes, format-placeholder mismatches, XML escaping, UTF-8/BOM/newline preservation, mojibake checks, or bulk `values-*` synchronization.
---

# Android String Resource Audit

Audit first, separate structural gaps from semantic translation gaps, make the smallest safe edits, then verify the same invariants again.

## Workflow

1. Read the repository and nearest module rules. Identify the target module and its `src/main/res` directory. Do not scan unrelated modules.
2. Run the bundled audit without modifying files:

   ```powershell
   python -X utf8 scripts/audit_android_strings.py audit <module>/src/main/res
   ```

   Add `--json` when machine-readable evidence is useful. Add `--strict` for a nonzero exit when structural, ordering, encoding, mojibake, or placeholder failures exist.
3. Interpret findings deliberately:
   - Treat a missing key as a real fallback gap unless the default key has `translatable="false"`.
   - Treat an exact English match only as a candidate. Preserve units, symbols, acronyms, brands, proper nouns, sports names, language names, loanwords, empty values, and words naturally spelled the same in the target language.
   - Prioritize repeated feature batches, long English sentences, non-Latin locales containing English prose, and keys introduced by the same commit.
   - Do not overwrite an existing localized value merely because another translation seems preferable.
4. Before writing, state the target files, translation groups, sorting behavior, and validation commands.
5. Apply translations with XML-aware or tightly targeted edits. Preserve Android escapes such as `\'`, `\n`, `%%`, `%s`, `%1$s`, and inline markup. Never translate placeholder tokens or resource names.
6. Preview ordering changes:

   ```powershell
   python -X utf8 scripts/audit_android_strings.py sort <module>/src/main/res
   ```

   If the preview is correct, rerun with `--write`. The sorter keeps locale-only keys after default-language keys and preserves their relative order.
7. Rerun `audit` and compare its failures with the pre-change baseline. Use `--strict` when the baseline is clean or when all reported failures are in scope. Then run `git diff --check` and inspect the changed-value set. Confirm no key was accidentally added, removed, duplicated, nested, or semantically overwritten.

## Safety Rules

- Keep `audit` read-only. Use `sort --write` only after reviewing the dry run.
- Refuse automatic sorting when a file contains nested `<string>` elements, duplicate keys, non-string resource children, malformed XML, or a regex/XML block-count mismatch. Repair the structure explicitly first.
- Preserve each file's UTF-8 BOM and newline bytes. Do not normalize unrelated line endings or reserialize whole XML trees.
- Do not delete locale-only keys. Report them and retain them after the default-language order.
- Compare placeholders for changed values even when the repository already has unrelated historical mismatches.
- Avoid Gradle for value-only translation and ordering changes. Run the narrow resource task only for added, deleted, or renamed keys, or when repository rules require it.
- Report translation quality as unreviewed when no native-language review or runtime UI check was performed.

## Output Expectations

Summarize:

- default, excluded, and translatable key counts;
- locale count and missing/duplicate/order failures;
- confirmed translation groups and intentionally preserved same-as-default terms;
- encoding, BOM, newline, XML, escaping, and placeholder results;
- commands run, results, and unverified risks.

## Bundled Script

Use `scripts/audit_android_strings.py` for deterministic audit and ordering. Run `--help` for all options. The script has no third-party dependencies.
