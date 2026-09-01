# Change spec

Indexes and positions are one-based. Operations run in listed order.

## Operations

- `delete_faq`: `faq`, `expect_en_contains`
- `delete_item`: `faq`, `item`, `expect_en_contains`
- `add_faq`: `position`, `translations[locale] = {title, itemTexts[]}`
- `update_faq`: `faq`, `expect_en_contains`, `translations[locale] = {title, itemTexts[]}`
- `add_item`: `faq`, `position`, `translations[locale] = "..."`
- `update_item`: `faq`, `item`, `expect_en_contains`, `translations[locale] = "..."`
- `update_title`: `faq`, `expect_en_contains`, `translations[locale] = "..."`

Every add/update must contain English plus every effective locale: all locales selected by `--locales` and every locale-like JSON file already present in `--dir`. The default therefore requires all 11 values plus any branch-only locales. Each operation may set `renumber_items` to `auto` (default), `all`, or `none`.

Pass a file path to `--spec`, or pass `--spec -` to read the same JSON object from standard input. Add `--json` to receive a structured dry-run/write report; a successful write report includes the files written and the result of reloading and auditing them.

## Deletion example

```json
{
  "operations": [
    {
      "type": "delete_item",
      "faq": 1,
      "item": 1,
      "expect_en_contains": "operating system"
    },
    {
      "type": "delete_faq",
      "faq": 8,
      "expect_en_contains": "charging time"
    }
  ]
}
```

Deletion uses structural coordinates, so translated text is neither loaded nor regenerated.

## Update example

```json
{
  "operations": [
    {
      "type": "update_title",
      "faq": 8,
      "expect_en_contains": "charge",
      "translations": {
        "en": "8. How do I charge the watch?",
        "cn": "8. 如何给手表充电？",
        "cs": "8. Jak hodinky nabiji?",
        "de": "8. Wie lade ich die Uhr auf?",
        "es": "8. ¿Cómo cargo el reloj?",
        "fr": "8. Comment charger la montre ?",
        "hu": "8. Hogyan tölthetem fel az órát?",
        "it": "8. Come si ricarica l'orologio?",
        "ja": "8. 時計を充電するには？",
        "pt": "8. Como carregar o relógio?",
        "sk": "8. Ako nabiť hodinky?"
      }
    }
  ]
}
```
