# Measurement Loop

Use this reference when closing an audit or comparing it with a previous cycle. Keep the tracking burden below the expected benefit.

## Select metrics

Choose 3–5 metrics that directly test the implemented changes. Prefer task-level facts already visible in task history, terminal records, diffs, or validation output.

| Signal | Low-cost measurement | Useful when |
| --- | --- | --- |
| First-delivery pass rate | Accepted substantive tasks / delivered substantive tasks | Requirements or validation were missed |
| True rework | Tasks redone for an already-stated requirement / sampled tasks | Scope or success criteria were misunderstood |
| Clarification cost | Median user follow-up turns before implementation | Prompts omit decisions that change the result |
| Time to verified result | Request time to first evidence-backed completion | Searches, builds, or waits dominate elapsed time |
| Duplicate reads | Same unchanged file read more than once per task | Context handling or routing is inefficient |
| Tool failure rate | Failed or irrelevant calls / total calls | Tool choice or command construction is unstable |
| Build wait | Time spent on builds that did not change the conclusion | Validation scope is too broad or premature |
| Visual closure | Visual tasks with same-scene evidence / visual tasks | UI fixes regress or require screenshot rework |
| Token usage | Reliable per-task usage only | The platform exposes comparable usage data |

Do not infer token savings from shorter final messages alone. If usage data is unavailable, label duplicate reads, tool calls, and output volume as proxies rather than tokens.

## Record the next cycle

Produce one compact table:

| Metric | Baseline | Target or decision threshold | Collection method | Review window |
| --- | --- | --- | --- | --- |
| Example: true rework | 3/12 sampled tasks | Revisit the rule if still above 1/10 | Compare initial request, first delivery, and correction | Next 10 substantive tasks or 14 days |

Use `baseline unavailable` when evidence is missing. In that case, the next cycle establishes a baseline instead of claiming improvement.

## Decide what to change next

- Keep a change when the target improves without a material increase in time, failures, or maintenance burden.
- Narrow or remove a change when it adds recurring overhead but does not improve its target after one representative review window.
- Avoid attributing improvement to a rule when the sample is too small, task mix changed materially, or external outages dominated results.
- Promote an experiment to a permanent rule only after repeated evidence; promote a repeated multi-step workflow to a Skill only when rules alone are insufficient.
- End with no more than three next actions, each tied to a measured signal.
