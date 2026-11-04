# 规则与反射检查

按本次受影响依赖和动态入口定向排查，避免清单驱动的无边界扫描。官方依据见文末；版本相关结论以项目实际解析产物和匹配版本文档为准。

## 普通开发的模型检查

只从本次新增/修改的类型及实际使用入口追踪，包含新增未跟踪文件；沿其字段、集合泛型和嵌套枚举核对到实际 adapter，不扫描无关模型。简记“类型/用途 → serializer/adapter → 名称与构造契约 → 生效规则 → 验证状态”，无需另建报告。

- 先查调用端使用的 Moshi、Gson、kotlinx.serialization、自定义 adapter 或其他机制及当前依赖版本；类名含 Entity/Bean、存在某个注解、外层已生成 adapter，都不能单独证明链路安全。纯 UI 状态或普通逻辑类不强加 JSON 注解/keep；仅由 Room 等生成代码使用的类型也先确认是否另有 JSON/反射用途。
- Moshi 区分 codegen、Kotlin 反射和 Java 反射。对采用 codegen 的模型确认 `@JsonClass(generateAdapter = true)` 与现有处理器/生成产物匹配；分别检查字段类型和枚举。默认枚举反射路径按当前版本核实 `@JsonClass(generateAdapter = false)` 及其 consumer 是否生效，或提供等价精准保留证据。`@Json(name=...)` 固定 JSON 名称不等于保证反射成员存活；自定义 adapter 以实际注册/选中路径为准。
- Gson 核对 `@SerializedName` 或既有稳定命名策略、实际字段与承载类、实例化方式/构造器、TypeToken 及 Retrofit 返回泛型。字段注解不替代完整规则；`-keepclassmembers` 不能单独证明类不会被删除。kotlinx.serialization 等生成方案确认现有插件、生成 serializer 及发现方式，不混加 Moshi/Gson 注解。
- 核对目标变体加载的 app/library、consumer 和生成规则；已覆盖时复用并记录依据，缺失时仅补本次动态用途需要的注解或规则。不得整包 keep、关闭混淆、添加全局 dontwarn，或顺手升级依赖来兜底。
- 本地 JSON 包括持久化结果和状态枚举：用旧字段名/枚举值的代表样本及新增值检查读写兼容，不只测新写新读，不清缓存掩盖问题。遇到未知枚举按既有兼容策略处理，不凭空更改协议。
- 完成范围内静态检查；有必要且符合项目构建边界时，执行最窄真实 minify/release 任务，核对对应 configuration、mapping 与 DEX 中的类型、字段、构造器、泛型和所需枚举成员。Debug 单测/编译通过不能证明 Release 安全，缺构建/产物/旧缓存运行证据时分别标未验证，不以自动构建替代检查。

机制依据：[Moshi R8/枚举说明](https://github.com/square/moshi#r8--proguard)、[Gson 排错](https://google.github.io/gson/Troubleshooting.html)、[R8 FAQ](https://r8.googlesource.com/r8/+/refs/heads/main/compatibility-faq.md)。实施结论仍以项目实际依赖和合并规则为准。

## 规则来源和冲突

- 配置来源包括默认规则、app proguardFiles、library consumerProguardFiles、AAR 内 proguard.txt / consumer 文件、JAR META-INF/proguard、代码生成器规则和嵌套 JAR。只查看进入目标变体的产物；不要因另一个模块存在就假设规则已合并。
- 同名库的新版本规则不能替代当前依赖版本证据。标注“规则已在目标 consumer 中完整覆盖”后才删除应用重复项；应用模型字段/缓存协议未必由库规则覆盖。
- 检查 SDK consumer 中的全局指令，包括 ignorewarnings、dont*、flattenpackagehierarchy/repackageclasses、printmapping 等；它们可能影响整应用，而非只影响 SDK。逐条判断意图与实际作用，不把所有重打包指令判为错误。
- 若需要隔离有污染的 consumer，先验证当前 AGP 支持的过滤能力、实际依赖标识及过滤粒度，再补回被排除的必要局部 keep，并核对最终 configuration。不要只排除 consumer 而丢弃其反射/JNI 保留规则；不为使用过滤 API 顺手升级插件。
- 保留规则不是越少越好。条件 keep、成员规则和 allowshrinking/allowoptimization/allowobfuscation 各自有不同语义；允许重命名不等于允许删除或改变实例化方式。

## 动态用途检查表

| 机制 | 应核实的证据与约束 |
| --- | --- |
| Gson/反射 JSON | 所用版本是否附带 consumer；未注解字段的线协议名称、SerializedName 字段及承载类、反射创建的构造器/Unsafe 分配行为；不能只保成员却让类被删除或优化成不可实例化 |
| TypeToken/泛型 | 实际 TypeToken 基类及子类的存活、Signature，相关 InnerClasses/EnclosingMethod 关系；仅 keepattributes 不能保证被裁剪元素及两端关系存在 |
| Retrofit 协程 | 目标版本的接口注解、返回类型、Continuation/Response 泛型规则及实际服务方法；不因 Retrofit 已有 consumer 就假设所有版本都覆盖 full mode |
| Moshi | 区分代码生成适配器、Kotlin 反射与 Java 反射模型；确认生成 keep 被合并、按名称发现的适配器构造器保留；针对 Java 缓存模型核验字段名 |
| 本地缓存/数据库 | 旧版本写入的 JSON、枚举名称、序列化字段与新包兼容；只验证新写新读无法覆盖升级后读取旧数据 |
| 命名反射/工厂 | Class.forName、getDeclaredMethod/Field、注解扫描、XML 类名、路由字符串、反射 ViewBinding inflate、动态 ViewHolder 构造器 |
| 属性动画 | ObjectAnimator/PropertyValuesHolder 的字符串属性名映射到 getter/setter；普通自定义对象尤其容易漏保；区分类型化 Property 和平台 View 已有规则，避免整包 keep |
| JNI/闭源 SDK | native 注册/回调与名称查找、SDK 发布规则、实际 ABI/so；不假设仅 native 方法默认 keep 覆盖所有被 native 调用的 Java 类/成员 |
| EventBus/Room/WebView | 订阅注解、生成实现/适配器、JavascriptInterface 方法及现有 consumer；按调用方式定向保护 |
| 动态资源 | getIdentifier、资源名拼接、WebView/assets、皮肤/远端资源；区分系统或外部包资源与本应用资源，必要时在资源 keep 中保护准确入口 |

普通 .class / ::class.java 引用本身不是字符串反射丢失的充分证据。先追到动态消费者再决定规则，不为每个类字面量新增 keep。

## Missing class 与宽泛 keep

1. 将首个错误关联到实际依赖及可达运行路径。
2. 必选运行依赖缺失应修复依赖关系；可选平台或 JVM 扩展只有确认 Android 路径不会使用时才加精确 dontwarn。
3. 使用当前工具链可用的 whyareyoukeeping 等诊断回答“为什么保留”，避免一次输出整应用图。
4. 每次收窄给出动态用途证据和对应验收；闭源未知部分允许局部保守方案。不要把先前项目的 SDK 包名或模型选择器复制成通用模板。

## 官方依据

- [启用 R8 与版本对应 DSL](https://developer.android.com/topic/performance/app-optimization/enable-app-optimization)
- [Keep rules 的作用](https://developer.android.com/topic/performance/app-optimization/keep-rules-overview)
- [R8 full-mode / Gson / Retrofit FAQ](https://r8.googlesource.com/r8/+/refs/heads/main/compatibility-faq.md)
- [AGP 8.9 KeepRules API 示例参考](https://developer.android.com/reference/tools/gradle-api/8.9/com/android/build/api/dsl/KeepRules)；这不是要求使用 8.9，也不是所有版本均支持相同接口。
