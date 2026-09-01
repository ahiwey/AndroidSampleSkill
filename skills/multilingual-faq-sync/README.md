# 11 语言 FAQ 同步

`multilingual-faq-sync` 用于将 FAQ 的新增、删除、修改和排序同步到默认 11 个语言版本：

```text
cn, cs, de, en, es, fr, hu, it, ja, pt, sk
```

它把英语源作为结构基准，只处理本次发生变化的 FAQ 或子项。英语既可以是 `en.json`，也可以像 `frequently_questions_pro` 一样内嵌在 Vue/JavaScript 的 `items: [...]` 中。删除操作无需翻译；新增或修改只翻译变化的句子。

## 适用场景

- 删除一个 FAQ 或其中一个有序步骤，并让后续编号前移。
- 新增 FAQ，并一次补齐 11 个语言版本。
- 修改标题或答案，同时保持所有语言结构一致。
- 检查 `q_cn`、`q_en` 等语言页面是否缺文件、缺条目或顺序错位。
- 发现缺失语言时，通过一次简短采访确认是否按英语基准补齐。
- 验证占位符、编码、换行和 JSON 格式。

## 快速使用

```text
使用 $multilingual-faq-sync 删除英文第 8 个 FAQ 的第 2 个子项，并按相同结构位置同步 11 个语言 JSON，调整后续编号并验证。
```

新增内容：

```text
使用 $multilingual-faq-sync 在第 9 条 FAQ 后新增“如何恢复出厂设置”，以英语为基准补齐默认 11 个语言版本，只翻译新增内容。
```

## 缺失语言采访

预审计发现语言文件、路由/节点、FAQ 条目或翻译缺失，而你的要求没有说明是否补齐时，Skill 会集中询问一次，例如：

```text
发现 cs、hu、sk 缺失。是否按修改后的英语版本创建并翻译补齐这 3 种语言？
```

如果你已经明确要求“同步默认 11 种语言”或“缺失的翻译一并补齐”，Skill 会直接补齐，不再重复询问。选择不补时，只会在安全的情况下修改现有语言，并明确报告仍存在的语言差异。

## 脚本

先审计：

```powershell
node scripts/faq_sync.mjs audit --dir <faq-json-dir>
node scripts/faq_sync.mjs audit --dir <faq-json-dir> --base <english.vue> --json
```

只查看英文标题、关键词命中或某一条 FAQ，避免读取整份多语言数据：

```powershell
node scripts/faq_sync.mjs inspect --dir <faq-json-dir> --base <english.vue>
node scripts/faq_sync.mjs inspect --dir <faq-json-dir> --base <english.vue> --contains "operating system"
node scripts/faq_sync.mjs inspect --dir <faq-json-dir> --base <english.vue> --faq 8
```

预览变更：

```powershell
node scripts/faq_sync.mjs apply --dir <faq-json-dir> --base <english.vue> --spec <change-spec.json>
```

确认后写入并复查：

```powershell
node scripts/faq_sync.mjs apply --dir <faq-json-dir> --base <english.vue> --spec <change-spec.json> --write
node scripts/faq_sync.mjs audit --dir <faq-json-dir> --base <english.vue>
```

如果用户选择不补缺失语言，可以通过 `--locales cn,de,en,es,fr,it,ja,pt` 明确本次安全同步范围。脚本只使用 Node.js 标准库，不需要安装 npm 依赖。

审计默认最多输出 12 条错误样例，并提供每种语言的问题数量；已有大量结构差异时不会把上百条重复错误送入模型。需要更多样例时再显式使用 `--max-errors <数量>`。

## 为什么更快

- 只读取一次英文基准并用结构坐标同步，不逐语言做语义搜索。
- `inspect` 只输出目标英文片段，避免将完整 JSON 或 Vue 数据送入模型上下文。
- 删除和排序完全由本地脚本完成。
- 新增、修改只翻译变化的句子，一次生成 10 个目标语言结果。
- 多项操作合并为一次预览、一次写入和一次审计。

## 插件建议

日常少量 FAQ 维护不需要新插件。若长期每天新增大量文案，可选择一个有正式 API、术语表和翻译记忆功能的翻译服务；是否接入应取决于凭据管理、费用、隐私和母语审校流程。不要依赖未经支持的网页翻译接口作为核心工作流。

完整规则和变更规范见 [SKILL.md](./SKILL.md)。
