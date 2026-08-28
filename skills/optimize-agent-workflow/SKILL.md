---
name: optimize-agent-workflow
description: Audit recent Codex, WorkBuddy, or other coding-agent tasks and apply safe, evidence-backed improvements that reduce rework, elapsed time, unnecessary tool usage, and token consumption. Use when the user asks for a recent-task retrospective, continuous workspace optimization, prompt-process improvement, AGENTS.md or MEMORY.md tuning, recurring agent-environment maintenance, or synchronization of reusable rule improvements into AndroidEasyRules.
---

# Optimize Agent Workflow

Audit recent work from evidence, implement a small set of high-value improvements, and leave a measurable follow-up loop.

## 1. Set the audit boundary

- Default to the latest 14 days or 20 substantive tasks, whichever provides the clearer bounded sample.
- Prefer task history, turn summaries, terminal output, diffs, failures, active rules, relevant skills, and plugin configuration.
- Exclude idle chats and the current unfinished audit from the baseline.
- Read only the evidence needed to test a suspected pattern. Do not scan all projects for context.
- State missing evidence before analysis. Never invent task-level token counts or precise savings.

## 2. Build an evidence table

For every sampled task, capture only fields available from the environment:

- task title, project, date, turns, visible duration, files changed, validation performed;
- initial request, later user corrections, tool failures, repeated searches or builds;
- whether the task was analysis-only, Quick, Strict, or an approved plan followed by implementation.

Classify follow-up turns correctly:

- Count a turn as rework only when an earlier delivery missed the same stated requirement, constraint, or validation target.
- Do not count planned “方案确认 → 实施”, new scope, requested interviews, or external runtime evidence as rework.
- Mark conclusions as confirmed, evidence-backed inference, or unverified.

## 3. Diagnose the highest-value patterns

Prioritize recurring causes:

- requirement or success-criterion ambiguity;
- visual changes closed with static checks but no same-scene runtime evidence;
- async, cache, lifecycle, bind/unbind, or duplicate-request fixes missing a state matrix;
- repeated broad searches, duplicate reads, over-planning, or unnecessary builds;
- sequential questions that could have been one batch of 1–3 independent decisions;
- approved plans being re-investigated without changed code or new evidence;
- rules that conflict, duplicate one another, are too vague, or cannot be verified;
- a repeated workflow better expressed as a focused Skill.

For each proposed improvement report evidence, expected benefit, downside, validation, priority `P0/P1/P2`, and type.

## 4. Implement safe improvements

Before editing, give a short plan naming files, reasons, and validation.

- Apply only reversible, low-risk changes supported by repeated evidence.
- Preserve existing user rules and unrelated working-tree changes.
- Prefer tightening an existing rule over adding a parallel rule.
- Keep project facts in project rules or `MEMORY.md`; export only generic behavior to shared rule packs.
- Do not install plugins, connect accounts, delete data, or publish externally without authorization.
- If evidence is weak, define a small reversible experiment and measurement window instead of writing a permanent rule.

## 5. Export reusable rules through AndroidEasyRules

Whenever this Skill changes an agent root rule or project rule, classify every changed rule:

1. Keep project-specific paths, brands, flavors, commands, and business behavior only in that project.
2. Generalize reusable Android or collaboration behavior without source-project details.
3. Locate a writable AndroidEasyRules source repository by repository name or Git remote; otherwise locate an installed AndroidEasyRules rules pack.
4. If AndroidEasyRules is available, apply the generalized change to its canonical global/project template and relevant focused rule or Skill. Update the active local rule too so the current computer benefits immediately.
5. Run the AndroidEasyRules validator and require `health_grade=A+` or higher. Run importer `--dry-run --strict` against a representative Android project.
6. If a source repository with a remote is available and publishing is authorized, commit and push the rule update. Otherwise remind the user to submit it.
7. If AndroidEasyRules is absent, update only the current computer's agent root and in-scope project rules. Do not install AndroidEasyRules implicitly.

Never treat an installed plugin cache as the only durable source without warning that an upgrade can overwrite it.

## 6. Handle new Skills consistently

When the audit finds a repeated workflow that merits a Skill, recommend it rather than creating it automatically.

After the user approves Skill creation:

- create or update it under the writable `AndroidSampleSkill/skills/<skill-name>/` repository;
- use the `skill-creator` workflow and keep the Skill self-contained;
- validate it with `quick_validate.py` and run focused tests for bundled scripts;
- update the AndroidSampleSkill index;
- remind the user to commit and publish; commit or push only when authorized.

If AndroidSampleSkill cannot be found, ask for its repository path instead of silently using a cache or `$CODEX_HOME/skills`.

## 7. Validate and define the next baseline

- Inspect final diffs and UTF-8 validity.
- Use the smallest validation that covers the changed rule or workflow; do not run Android Gradle for rules-only edits.
- Track future measurements such as first-delivery pass rate, true rework turns, clarification turns, same-scene visual validation coverage, repeated file reads, tool failures, build wait time, and time to verified result.
- Report token changes only when the environment exposes reliable per-task usage. Otherwise use tool/output proxies and label estimates.

## 8. Deliver the closeout

Include:

- audit scope and evidence sufficiency;
- the 3–7 most important findings;
- implemented changes and changed files;
- validation commands and results;
- deferred changes and reasons;
- next-cycle metrics;
- improved general, Quick, and relevant specialist prompt templates;
- remaining risks, including unsynchronized or uncommitted rule sources.

End substantial audits by asking whether the result meets the user's needs and whether this Skill or another repeated workflow should be updated. When Skill files or AndroidEasyRules source files changed, explicitly remind the user whether they were committed and published.
