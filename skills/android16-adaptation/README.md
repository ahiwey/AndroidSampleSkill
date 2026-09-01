# Android 16 / API 36 适配

`android16-adaptation` 用于审计、实施、验证并记录 Android 16 / API 36 兼容性和发布就绪状态。

> 需要本地 Android 仓库。未执行的设备、人工或最终产物验证不会被标记为通过。

## 何时使用

- 升级 `compileSdk` 或 `targetSdk` 到 36。
- 检查 Android 16 适配是否完成，或准备 API 36 发布。
- 修复 edge-to-edge、预测性返回、后台任务、BLE、局域网或 Intent 安全问题。
- 审计 APK/AAB 中的 16 KB 原生库兼容性。
- 适配平板、折叠屏、分屏和窗口尺寸变化。
- 评估 Google Fit 迁移到 Health Connect。
- 在代码完成后生成 Android 16 测试清单。

## 快速使用

只审计、不修改：

```text
使用 $android16-adaptation 审计当前应用的 Android 16 / API 36 适配状态，只读分析，不修改代码、不构建；按 MUST_FIX、CONDITIONAL、NOT_APPLICABLE、DONE、BLOCKED、NOT_VERIFIED 输出证据表。
```

实施适配：

```text
使用 $android16-adaptation 将 app 模块适配到 API 36。先审计，再只修改确认适用的问题，并执行与改动范围匹配的最小验证。
```

发布验收：

```text
使用 $android16-adaptation 检查 release 变体的 Android 16 发布就绪状态，包括最终 APK/AAB、16 KB 原生库、设备与人工门禁；未运行项保持 NOT_VERIFIED 或 BLOCKED。
```

## 四种工作模式

| 模式 | 行为 |
| --- | --- |
| 审计 | 读取并报告，不修改；除非明确要求，否则不构建。 |
| 实施 | 先审计，最小修改适用项，再做成比例验证。 |
| 验证 | 检查已有实现，运行能证明结论的最窄检查。 |
| 发布就绪 | 增加最终 APK/AAB、设备、人工、监控和回滚门禁。 |

## 覆盖范围

- 构建基线：SDK、AGP、Gradle、JDK 和必要依赖版本。
- 系统栏与窗口：edge-to-edge、状态栏、导航栏、刘海、IME 和手势区域。
- 返回行为：预测性返回、页面业务语义和生命周期状态。
- 条件能力：后台任务、BLE、局域网、健康权限、Intent、媒体、文本和无障碍。
- 原生代码：最终制品内每个 ABI 的 ZIP、AAB 元数据、ELF 对齐和 16 KB 设备加载。
- 大屏：方向/宽高比限制、响应式布局、折叠状态和窗口重建。
- 独立迁移：只有证据证明项目使用 Google Fit 时，才规划 Health Connect 迁移。

## 工作方式

1. 确认产品类型、模块、变体、工具链、UI 技术栈、原生库和设备条件。
2. 运行只读扫描器，输出带证据的首轮状态表。
3. 先完成 API 36 首发基线，再根据范围处理折叠屏/平板等阶段 B 工作。
4. 只修改已证明适用的问题，保护已有业务行为和用户改动。
5. 按静态检查、编译、测试、制品、模拟器、真机和人工流程分层验证。
6. 使用 `PASS`、`PASS_WITH_RISKS` 或 `BLOCKED` 汇总结论，并列出未验证风险。

运行仓库内扫描器的示例：

```powershell
.\skills\android16-adaptation\scripts\audit-android16.ps1 `
  -ProjectRoot "<Android项目路径>" `
  -AppModule "app"
```

## 测试清单

测试清单不会默认生成。只有实施完成且完成相应自动化或构建验证后，才会询问是否生成正常版（30–40 条）或增强版（超过 100 条）。清单中的人工项初始状态是 `NOT_RUN`，不能代替真实测试证据。

完整规则见 [SKILL.md](./SKILL.md)，审计项见 [audit-checklist.md](./references/audit-checklist.md)，验证与发布门禁见 [verification-and-release.md](./references/verification-and-release.md)，官方基线见 [official-baseline.md](./references/official-baseline.md)。
