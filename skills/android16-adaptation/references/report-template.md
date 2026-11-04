# Android 16 delivery report template

Use evidence, not optimistic wording. Remove placeholder examples, but keep unverified rows visible.

```markdown
# Android 16 / API 36 适配与发布方案

## 1. 结论与适用范围
- 总体状态：PASS / PASS_WITH_RISKS / BLOCKED
- 验收范围：API 36 基础适配 / 完整发布验收 / 用户约定范围
- 产品形态与发布渠道：
- 当前/目标工具链：
- 已完成范围：
- 不在本轮范围：

## 2. 阶段 A：API 36 基础适配（默认交付标准）
| 检查项 | 状态 | 证据 | 决策/剩余工作 |

## 3. 阶段 B：折叠屏/平板自适应
| 页面/能力 | compact | medium | expanded | 临时兼容/负责人/期限 |

## 4. 独立迁移：Google Fit 退役
- 状态：DONE / NOT_APPLICABLE / BLOCKED / NOT_VERIFIED
- 使用证据或不适用证据：
- 映射、去重、历史兼容和灰度策略：

## 5. 验证矩阵
| 命令/设备 | 构建标识 | 结果 | 证据路径 | 缺陷/阻断 |

## 6. 发布门禁与灰度
- 当前提交要求、核查日期及证据：
- 已确认阻断 / 必需提交条件待核实 / 本范围未发现阻断：
- Google Play 审核结果：未查询 / 处理中 / 实际审核结果及证据
- P0/P1 状态：
- 回滚条件与产物：
- 灰度阶段与观察指标：

## 7. 剩余问题与未验证风险
| 剩余项 | 可延期优化/未验证/条件风险/实际阻断 | 证据与原因 | 所需输入/下一步 | 发布影响与升级条件 |
```

The final conversational handoff should also include:

```markdown
## 适配结论
- 总体状态：
- 验收范围：
- 是否满足 target 36：
- 当前提交阻断及待核实条件：
- Google Play 实际审核结果（未查询时明确写未查询）：

## 本轮修改
| 文件 | 修改内容 | 对应风险 |

## 验证结果
| 命令/设备 | 结果 | 证据路径 |

## 不适用项及证据
| 项目 | 证据 |

## 外部阻断
| 项目 | 精确文件/依赖/设备 | 需要谁提供什么 |

## 剩余问题与未验证风险
| 剩余项 | 分类 | 证据与原因 | 建议下一步 | 当前提交影响/升级条件 |
```

Decision rules apply to the stated scope. Use [implementation-baseline.md](implementation-baseline.md) for ordinary adaptation. Always list remaining work after completion; if none was found, say so within the reviewed scope. Do not turn unchanged ARMv7 4 KB measurements into warnings, blockers or recurring reminders; report only actual regressions or an explicitly stricter contract. Known 64-bit risks remain in the scoped evidence.

Baseline completion, current submission eligibility and Play approval are separate conclusions. Deferred adaptive-layout/animation/dependency cleanup and expanded coverage do not automatically block basic delivery. Required submission evidence that is missing is unknown, not a pass. Use “未发现本次适配引入的上架阻断，剩余优化不作为当前提交阻断” only with supporting evidence and explicit scope; never infer a real review result. Follow [official-baseline.md](official-baseline.md) for time-sensitive requirements.

Decision rules:

- `PASS`: all required checks for the stated scope have proof. Full release scope requires its final-artifact/runtime/manual gates too; this status never means Play approved.
- `PASS_WITH_RISKS`: the agreed basic implementation and proportional verification are complete, with deferred work, conditional risk or expanded proof remaining. Describe each item's submission impact separately; this status alone does not establish eligibility.
- `BLOCKED`: a required in-scope item, demonstrated P0/P1, applicable submission blocker or explicitly requested release gate is unresolved. Deferred expanded work is not itself a baseline blocker.
