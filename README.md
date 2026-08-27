# AndroidSampleSkill

A curated collection of reusable Codex skills for Android engineering workflows. This repository contains skills authored and maintained by [ahiwey](https://github.com/ahiwey); externally sourced skills installed in the local Codex environment are intentionally excluded.

## Included skills

| Skill | Purpose |
| --- | --- |
| `android-string-resource-audit` | Audit missing Android translations, placeholders, encoding, mojibake, and locale ordering; safely reorder `strings.xml`. |
| `android-open-source-integration` | Plan and implement traceable Android open-source integrations with licensing and removal guardrails. |
| `android16-adaptation` | Audit, implement, and verify Android 16 / API 36 compatibility and release readiness. |
| `commit-migration` | Port Android commits, branches, or selected files while adapting packages, resources, manifests, and project structure. |
| `reasoning-playbooks` | Route Chinese requests through 12 reusable reasoning and decision playbooks. |

The separate [AndroidEasyRules](https://github.com/ahiwey/AndroidEasyRules) project remains its canonical repository and is linked here instead of being duplicated.

## Install

Clone the repository:

```powershell
git clone https://github.com/ahiwey/AndroidSampleSkill.git
Set-Location AndroidSampleSkill
```

Install one skill into the default Codex skill directory:

```powershell
$skillRoot = Join-Path $env:USERPROFILE ".codex\skills"
Copy-Item -Recurse -LiteralPath ".\skills\android-string-resource-audit" -Destination $skillRoot
```

Replace `android-string-resource-audit` with another folder name from `skills/` when needed. Review or back up an existing destination before updating an already installed skill.

## Invoke

Reference a skill explicitly in a Codex prompt:

```text
Use $android-string-resource-audit to audit app/src/main/res and safely reorder locale strings.xml files.
```

Codex can also select a skill automatically when the request matches its `SKILL.md` description.

## Repository policy

- Keep each skill self-contained under `skills/<skill-name>/`.
- Keep only reusable instructions, scripts, references, assets, and `agents/openai.yaml` inside a skill.
- Validate every `SKILL.md` before publishing.
- Do not add system, plugin-cache, Google-authored, OpenAI-authored, or third-party skills to this repository.
- Never commit credentials, project secrets, generated build output, or private application source.

## License

Released under the [MIT License](LICENSE).
