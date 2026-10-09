---
name: android-r8-release-audit
description: Audit and, when authorized, enable or repair Android R8 optimization, obfuscation, code/resource shrinking and keep rules; inspect resolved consumer rules and release artifacts, and validate affected runtime paths on an authorized device. Use for R8/ProGuard, minify, missing classes, release-only reflection/serialization failures or release-size optimization, not ordinary UI work or an automatic AGP upgrade.
---

# Android R8 Release Audit

将“开启优化”落实为可追溯的配置、保留规则、实际产物与运行证据。默认使用中文沟通，遵守当前项目规则和既有授权；不从 Skill 推断设备、发布或升级权限。

## 选择任务范围

- 只读分析：查看现有源码与产物，提出带证据的建议；不改配置，不运行 Gradle 或设备操作。
- 已授权实施：检查当前差异后修复确定的问题；用户已确认的方案不重复采访。只在新证据改变范围时澄清。
- 产物验证：配置/keep 改动需要时运行最窄的真实 release/minify 任务；设备测试或资源缩减验收需要最终 APK 时再 assemble。
- 设备验证：沿用本任务已有明确授权；缺授权时先完成可独立推进的分析、修改与产物检查，再询问。缺账号、外设或样本记为未验证，不制造通过结果。
- 当前环境有第三方 r8-analyzer 时可作辅助参考，但不要依赖其安装、照搬其默认删除建议或隐藏异常。该技能自身足以完成流程。

## 执行顺序

1. **确认基线与变体。** 从实际生效的插件声明、版本目录/约定插件、Gradle 配置与已解析依赖确认 AGP、R8 覆盖版本、build type/flavor、签名和产物。只审计进入目标变体的模块，settings 中列出不代表应用依赖。保留用户差异，按项目入口定位，不全仓漫扫。
2. **检查优化配置。** 确认代码优化、混淆、代码缩减和资源缩减各自是否生效，查看 full-mode 覆盖、默认规则与所有包含规则。传统 DSL 检查 minifyEnabled、shrinkResources、proguard-android-optimize.txt；新版 DSL 按实际 AGP 官方文档核实等价配置。不要顺手升级 AGP/库，或把某版本的实验开关推广到全部项目。
3. **按证据审计规则。** 阅读 [规则与反射检查](references/rule-audit.md)。建立短表：规则/来源、动态用途、保留或收窄理由、验证路径。检查目标版本的 AAR/JAR consumer rules、生成规则及最终合并配置。库名、宽泛程度和第三方建议都不能单独证明规则冗余。
4. **修复最小集合。** 改实际配置或 app/library 所属规则，保留构造、泛型、字段名或成员名所需的约束。业务协议、缓存格式、签名、权限和版本迁移不随规则修复改变；需要变动时按已有授权处理。未知闭源 SDK 可先局部保守保留，说明成本与未验证部分。
5. **验证最终产物。** 按 [产物与设备验收](references/verification.md) 检查实际合并规则、mapping、移除记录及 APK 内 DEX/资源。原始规则存在或构建成功，不足以证明动态入口保留。
6. **运行相关场景并交付。** 在授权设备上验证最终包与必要的历史数据兼容。按“源码/构建/产物/安装/场景/日志”分别报告完成状态，提供本次修改、证据、未覆盖风险与恢复或后续路径。

## 硬边界

- 不用全局 -dontshrink、-dontoptimize、-dontobfuscate、-ignorewarnings 或整应用 keep 作为交付修复；不要关闭 minify、删除依赖/资源来伪造构建通过。
- 不机械复制 missing_rules.txt 或升级库；先区分可选引用、真实依赖缺失、反射/JNI 与构建环境问题。
- 不自动上传 APK、mapping、日志，不发布应用，不改变签名；检查构建附带上传任务并遵守本任务授权，必要时仅排除上传任务，不关闭本地优化。
- 使用现有任务和工具；不默认 clean、全量测试、安装反编译器或测试依赖，不终止来源不明的 Gradle 进程。
- 不默认新建报告；先在回复中提供结论。需要落盘且没有已指定目录时询问位置。发布版本的 mapping 应按项目既定产物留存方式关联到准确 APK/版本。
- 不把“没有崩溃日志”表述为“所有功能安全”，不把规则健康评分当成 App 质量或混淆百分比。

## 维护验证

新增或改动本 Skill 后运行技能元数据校验、检查引用，并重放 [代表案例](references/replay-cases.md)。区分主代理案例推演、脚本断言与独立行为测试；不为测试此 Skill 自动构建应用、连接设备或创建子代理。
