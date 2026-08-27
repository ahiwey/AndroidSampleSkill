# Output Templates

Use these templates when applying the Android open-source integration skill. The model may translate labels to Chinese in the final response, but keep all required fields.

## Candidate Repository Table

```markdown
| # | Project | GitHub URL | Stars | License | Recent update | Google Play evidence | Stack judgment | Importable features | Estimated screens | Repository type | Expected content types | Useful sample/demo screens | Unified feature alias | Reusable image resources | Estimated image resource count | Estimated new Gradle dependencies | Minimum gate pass | Expected source screen coverage | Score | Risk | Recommendation |
|---|---------|------------|-------|---------|---------------|----------------------|----------------|---------------------|-------------------|-----------------|------------------------|----------------------------|----------------------|--------------------------|--------------------------------|-----------------------------------|-------------------|---------------------------------|-------|------|----------------|
| 1 |         |            |       |         |               |                      |                |                     |                   |                 |                        |                            |                      |                          |                                |                                   |                   |                                 |       |      |                |
```

After the table, add:

```markdown
Recommended sources: A, B, C.
Reasons:
1.
2.
3.

Please confirm the selected sources. Use 6 sources when fewer sources cannot satisfy the rich integration minimums. I will not modify code before confirmation.
```

## Pre-Implementation Budget Table

Before the table, include:

```markdown
Pre-implementation inventory:
- Root package:
- Custom Application:
- Existing dependency/version notes:
- Alias collision scan:
- Package/resource/id/style/menu/anim/raw/font collision scan:
- Candidate branch locations for 90+ Application switch calls:
-
```

Page-entry mapping before implementation:

```markdown
| # | Original file | Method/callback | Existing trigger condition | Custom Application switch call | Source | Imported page/feature | Reachable when switch true | Removal notes |
|---|---------------|-----------------|----------------------------|--------------------------------|--------|-----------------------|----------------------------|---------------|
| 1 |               |                 |                            |                                |        |                       |                            |               |
```

Source coverage table before implementation:

```markdown
| Source | Major original screen/flow | Import plan: import/adapt/merge/exclude | Target package/page | Exclusion reason if excluded |
|--------|----------------------------|-----------------------------------------|---------------------|------------------------------|
|        |                            |                                         |                     |                              |
```

```markdown
| Source | Java/Kotlin files | XML files | Image/font/raw resources | string/color/style/menu/anim entries | Remote dependencies | Modified original files | Manifest entries | R8/ProGuard rules | Planned new screens | Planned source screen coverage | Planned Application switch call sites | Entry branch locations | Removal method |
|--------|-------------------|-----------|--------------------------|--------------------------------------|---------------------|-------------------------|------------------|-------------------|---------------------|--------------------------------|----------------------------------------|------------------------|----------------|
|        |                   |           |                          |                                      |                     |                         |                  |                   |                     |                                |                                        |                        |                |
```

Summary:

```markdown
Budget summary:
- Estimated total new files:
- Estimated total new screens:
- Estimated total remote dependencies:
- Estimated total image/font/raw resources:
- Estimated total modified original files:
- Estimated total Application switch call sites:
- Application switch call sites distributed across files/flows:
- Meets 75-screen minimum:
- Meets 180 image/font/raw resource minimum:
- Meets 10 new Gradle dependency minimum:
- Exceeds 1200-file soft target:
- Exceeds 48-dependency suggested target:
- Meets 2000-file hard limit:
- Meets 60-dependency hard limit:
- Meets 90 Application switch call-site minimum:

Please confirm whether to start implementation with this budget. I will not modify code before confirmation.
```

## Source Record Template

Use this structure in `docs/insert_qc_sources.md`.

```markdown
# Insert QC Sources

## YYYY-MM-DD - <Feature Name>

- GitHub project:
- GitHub URL:
- Commit/tag:
- Star count at import time:
- License:
- License file:
- Google Play publication evidence:
- Original stack:
- Imported scope:
- Adapted packages:
- Unified feature alias and resource naming pattern:
- New Gradle dependencies:
- Dependency quality notes:
- Asset-license notes:
- Manifest additions:
- R8/ProGuard additions:
- Entry integration locations:
- Application switch:
- Application switch call-site list:
- Page-entry mapping:
- Source coverage table:
- Adaptations, renames, and rewrites:
- Removal steps:
  1. Delete packages:
  2. Delete resources matching the feature alias and documented numeric suffixes:
  3. Remove Gradle dependency block:
  4. Remove Manifest block:
  5. Remove R8/ProGuard block:
  6. Remove entry branches:
  7. Remove Application switch call sites:
  8. Update this source record:
```

## Final Report Template

```markdown
Integration complete.

Sources:
1.
2.
3.

Key locations:
- Application switch:
- Added page reachable paths:
- Third-party source record:

New/modified files:
-

Dependencies and configuration:
- Gradle:
- Manifest:
- R8/ProGuard:
- Unified feature aliases and resource naming:

Application switch gating:
- Actual switch call-site count:
- Meets 90-call-site minimum:
- Uses the same custom Application total switch method:
- Distributed across files/flows:
- Call-site files/methods:
- Page-entry mapping:

Coverage:
- Actual reachable imported screens:
- Actual imported image/font/raw resources:
- Actual new Gradle dependency count:
- Source coverage summary:
- Over-trim check:

Removal:
- Packages:
- Resources:
- Gradle blocks:
- Manifest blocks:
- R8/ProGuard blocks:
- Entry branches:
- Application switch call sites:
- docs/insert_qc_sources.md records:

Static verification:
- Insert qc markers:
- Package and resource naming:
- Application switch gating:
- No insertqc/sample/demo naming:
- 90+ call-site mapping:
- Asset-license notes:
- Dependency quality notes:
- Screen/resource/dependency minimums:
- Source coverage and trimming:
- Source record:
- No compile/build executed:
```
