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

Every add/update must contain English plus every locale selected by `--locales`. The default therefore requires all 11 values. Each operation may set `renumber_items` to `auto` (default), `all`, or `none`.

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
