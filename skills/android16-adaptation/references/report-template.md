# Android 16 delivery report template

Use evidence, not optimistic wording. Remove placeholder examples, but keep unverified rows visible.

```markdown
# Android 16 / API 36 适配与发布方案

## 1. 结论与适用范围
- 总体状态：PASS / PASS_WITH_RISKS / BLOCKED
- 产品形态与发布渠道：
- 当前/目标工具链：
- 已完成范围：
- 不在本轮范围：

## 2. 阶段 A：API 36 首发上架（必须完成）
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
- P0/P1 状态：
- 回滚条件与产物：
- 灰度阶段与观察指标：

## 7. 本轮未验证风险
| 风险 | 原因 | 所需设备/权限/外部输入 | 负责人/期限 | 发布影响 |
```

The final conversational handoff should also include:

```markdown
## 适配结论
- 总体状态：
- 是否满足 target 36：
- 是否具备发布条件：

## 本轮修改
| 文件 | 修改内容 | 对应风险 |

## 验证结果
| 命令/设备 | 结果 | 证据路径 |

## 不适用项及证据
| 项目 | 证据 |

## 外部阻断
| 项目 | 精确文件/依赖/设备 | 需要谁提供什么 |

## 未验证风险
| 风险 | 原因 | 建议下一步 | 发布影响 |
```

Decision rules:

- `PASS`: required automated, final-artifact, emulator/device, and agreed manual checks have proof; no open release blocker.
- `PASS_WITH_RISKS`: code/build work is complete but non-blocking manual, OEM, peripheral, account, or operational proof remains.
- `BLOCKED`: a required artifact, P0/P1, release gate, or external dependency is unresolved.
