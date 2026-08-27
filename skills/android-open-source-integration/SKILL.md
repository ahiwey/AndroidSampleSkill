---
name: android-open-source-integration
description: Use this skill when the user asks to integrate, insert, add, or merge GitHub open-source Android project code into an existing Android app. Trigger for requests about adding two or three open-source Android projects, inserting Android code, integrating GitHub Android modules, or adding compliant reachable pages and resources with Application-level gating and removable markers.
---

# Android Open-Source Integration

Use this skill to guide compliant large-scale integration of GitHub Android open-source complete-app sources into an existing Android project.

## Trigger Examples

Use this skill for Chinese or English requests whose meaning is:
- Insert two open-source Android project code sources.
- Insert Android code into the current project.
- Integrate GitHub Android project code.
- Add open-source Android project pages, resources, dependencies, or modules.
- Add compliant reachable Android pages with an Application-level switch.

## Core Position

Keep the work framed as legitimate code integration:
- Add real, reachable pages or features.
- Respect licenses and source attribution.
- Avoid unreachable code, dead branches, impossible conditions, or review-evasion patterns.
- Preserve the existing project structure and main user flows.

The user usually wants Chinese communication. Respond in Chinese unless they ask otherwise.

## Required References

Before doing any repository search or code changes, read:
- `references/integration_rules.md`
- `references/output_templates.md`

These files are the editable rule source for this skill. If the user wants to update the integration rules, edit `references/integration_rules.md` first.

## Workflow

1. Inspect the current Android project.
   - Identify root package name, custom `Application`, Manifest, Gradle files, source folders, resource structure, and common naming style.
   - Do not build, assemble, sync Gradle, or run local compilation unless the user explicitly asks.

2. Search GitHub for 10-15 candidate Android open-source projects.
   - Browse the web because repository stars, licenses, and update dates are current information.
   - Apply the filters in `references/integration_rules.md`.
   - Produce a candidate repository table using `references/output_templates.md`.
   - Stop and wait for the user to confirm selected sources. If 3 sources cannot satisfy the rich integration minimums, require selecting 6 sources.

3. After source confirmation, produce a pre-implementation budget table.
   - Estimate file count, dependency count, original file modifications, Manifest changes, R8/ProGuard changes, entry branch locations, and removal method.
   - Confirm the plan reaches the rich integration minimums: 75+ imported screens, 180+ image/font/raw resources, 10+ legitimate new Gradle dependencies, and 90+ direct custom `Application` switch call sites.
   - If the plan cannot reach those minimums, return to candidate selection instead of implementing a trimmed-down integration.
   - Stop and wait for user confirmation.

4. Integrate only after both confirmations.
   - Keep new code under existing source directories and package layers.
   - Use one independent functional subpackage per source.
   - Add or update the custom `Application` switch method, preferring `isInsertQcEnabled()`, defaulting to `false`.
   - Gate every new branch entry through this switch.
   - Plan and implement at least 90 meaningful call sites that directly use the custom `Application` total switch method for new page or feature entries.
   - Use `Insert qc start` and `Insert qc end` markers around new or modified code, XML, Gradle, Manifest, resource, and R8 sections.

5. Record third-party sources.
   - Create or update `docs/insert_qc_sources.md`.
   - Include source URLs, license, star count, commit/tag, actual imported scope, packages, unified feature aliases, resource naming patterns, dependencies, entry paths, and removal steps.

6. Verify without compiling by default.
   - Use static checks, code reading, diff review, path/resource/package inspection, and source record review.
   - Report what was checked and any unresolved risks.

## Guardrails

- Do not insert dead code or intentionally unreachable code.
- Do not use constant-false checks, impossible string comparisons, or hidden branches as the integration mechanism.
- Do not copy whole repositories.
- Do not introduce unclear, viral, or non-commercial-only licenses.
- Do not add dangerous permissions, exported components, broad keep rules, new Maven repositories, new Gradle plugins, or global Manifest changes without explicit user confirmation.
- Do not modify or remove unrelated existing code.

## Output Style

Use the templates in `references/output_templates.md`.

For final implementation reports, include:
- Selected sources.
- New/modified files.
- `Application` switch location and method name.
- Actual `Application` switch call-site count and call-site list.
- Reachable path for every added page.
- Dependency, Manifest, R8/ProGuard, package, and resource naming changes.
- Removal steps.
- Static verification result.
