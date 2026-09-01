# 多语言 FAQ 同步

`multilingual-faq-sync` 用于将 FAQ 的新增、删除、修改和排序同步到默认 11 个必需语言，以及当前分支已有的额外语言：

```text
cn, cs, de, en, es, fr, hu, it, ja, pt, sk
```

它把英语源作为结构基准，只处理本次发生变化的 FAQ 或子项。英语既可以是 `en.json`，也可以像 `frequently_questions_pro` 一样内嵌在 Vue/JavaScript 的 `items: [...]` 中。删除操作无需翻译；新增或修改只翻译变化的句子。若分支已有 `tr` 等默认列表外语言，也会自动纳入 JSON 审计与写入。

## 适用场景

- 删除一个 FAQ 或其中一个有序步骤，并让后续编号前移。
- 新增 FAQ，并一次补齐 11 个语言版本。
- 修改标题或答案，同时保持所有语言结构一致。
- 检查 `q_cn`、`q_en` 等语言页面是否缺文件、缺条目或顺序错位。
- 默认语言缺失时，完整补齐翻译 JSON、语言组件、路由导入/节点及同类注册。
- 当前分支存在默认列表外语言时，继续正确同步其增删改文案。
- 验证占位符、编码、换行和 JSON 格式。

## 快速使用

```text
使用 $multilingual-faq-sync 删除英文第 8 个 FAQ 的第 2 个子项，并按相同结构位置同步 11 个语言 JSON，调整后续编号并验证。
```

新增内容：

```text
使用 $multilingual-faq-sync 在第 9 条 FAQ 后新增“如何恢复出厂设置”，以英语为基准补齐默认 11 个语言版本，只翻译新增内容。
```

## 语言对账

Skill 使用三个集合判断范围：默认必需语言、当前分支发现的语言、两者并集形成的有效语言。`audit --json` 会输出 `requiredLocales`、`discoveredLocales`、`extraLocales` 和 `missingLocales`。

- 必需语言缺失：参照一个完整可用语言，从 JSON、页面/组件、路由 import、`/q_<locale>` 节点一直补到导航、语言映射或构建注册；不能只新增 JSON。
- 分支额外语言：保留并纳入所有操作。删除按相同坐标执行；新增和更新必须提供该语言的变更字段翻译。
- 路由与 JSON 只存在一侧：视为未完成并修复缺失侧。

## 脚本

先审计：

```powershell
node scripts/faq_sync.mjs audit --dir <faq-json-dir>
node scripts/faq_sync.mjs audit --dir <faq-json-dir> --base <english.vue> --json
```

只查看英文标题、关键词命中或某一条 FAQ，避免读取整份多语言数据。用户只提供了某种本地化文案时，可指定语言搜索，并同时拿到同一结构坐标上的英文：

```powershell
node scripts/faq_sync.mjs inspect --dir <faq-json-dir> --base <english.vue>
node scripts/faq_sync.mjs inspect --dir <faq-json-dir> --base <english.vue> --contains "operating system"
node scripts/faq_sync.mjs inspect --dir <faq-json-dir> --base <english.vue> --locale cn --contains "手机系统"
node scripts/faq_sync.mjs inspect --dir <faq-json-dir> --base <english.vue> --faq 8
```

预览变更：

```powershell
node scripts/faq_sync.mjs apply --dir <faq-json-dir> --base <english.vue> --spec <change-spec.json> --json
```

确认后写入并复查：

```powershell
node scripts/faq_sync.mjs apply --dir <faq-json-dir> --base <english.vue> --spec <change-spec.json> --write --json
Get-Content -Raw <change-spec.json> | node scripts/faq_sync.mjs apply --dir <faq-json-dir> --base <english.vue> --spec - --write --json
```

`--spec -` 从标准输入读取变更规范，可省去临时规范文件。写入命令会重新加载实际文件并完成结构审计；JSON 报告包含操作坐标、目标文件、实际写入文件、FAQ 数量和验证结果。只有文件之后又被其他工具修改，或需要独立复核时，才再单独运行 `audit`。

`--locales` 定义本次必需集合，但脚本仍会自动合并 FAQ 目录中已有的语言 JSON，避免分支额外语言被漏改。脚本只使用 Node.js 标准库，不需要安装 npm 依赖。

审计默认最多输出 12 条错误样例，并提供每种语言的问题数量；已有大量结构差异时不会把上百条重复错误送入模型。需要更多样例时再显式使用 `--max-errors <数量>`。

## 为什么更快

- 只读取一次英文基准并用结构坐标同步，不逐语言做语义搜索。
- `inspect` 只输出目标语言命中片段及同坐标英文，避免将完整 JSON 或 Vue 数据送入模型上下文。
- 删除和排序完全由本地脚本完成。
- 新增、修改只翻译变化的句子，一次生成有效语言集合的目标结果。
- 多项操作合并为一次预览、一次写入；写入过程内置重新加载审计。

## 插件建议

日常少量 FAQ 维护不需要新插件。若长期每天新增大量文案，可选择一个有正式 API、术语表和翻译记忆功能的翻译服务；是否接入应取决于凭据管理、费用、隐私和母语审校流程。不要依赖未经支持的网页翻译接口作为核心工作流。

完整规则和变更规范见 [SKILL.md](./SKILL.md)。
