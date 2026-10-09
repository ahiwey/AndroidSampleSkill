# 规则与反射检查

按本次受影响依赖和动态入口定向排查，避免清单驱动的无边界扫描。官方依据见文末；版本相关结论以项目实际解析产物和匹配版本文档为准。

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
