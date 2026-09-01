# Android 多语言字符串审计

`android-string-resource-audit` 用于对照默认语言审计、修复和安全排序 Android `strings.xml`，重点保护占位符、编码、换行与已有翻译。

## 何时使用

- 检查某个 `values-*` 目录是否缺少翻译键，或是否发生英文回退。
- 排查重复键、嵌套 `<string>`、XML 转义、乱码和编码问题。
- 核对 `%s`、`%1$s`、`%%` 等格式化占位符是否一致。
- 按默认语言顺序整理多个地区的 `strings.xml`，同时保留地区独有键。
- 批量同步语言资源，但不希望覆盖已经存在的本地化内容。

## 快速使用

在 Android 项目中向 Codex 输入：

```text
使用 $android-string-resource-audit 审计 app/src/main/res 下所有 strings.xml，先只报告缺失翻译、占位符和排序问题，不修改文件。
```

需要修复时明确范围：

```text
使用 $android-string-resource-audit 补齐 app/src/main/res 中本次新增的缺失翻译，并在预览后按默认语言顺序整理；保留地区独有键，不覆盖已有译文。
```

## 能做什么

| 能力 | 说明 |
| --- | --- |
| 覆盖率审计 | 统计默认键、不可翻译键、各地区缺失键与地区独有键。 |
| 结构检查 | 发现重复键、嵌套字符串、非字符串子节点和 XML 结构异常。 |
| 文本质量线索 | 标记疑似英文回退与 mojibake；品牌、缩写、单位等只作为候选，不机械翻译。 |
| 占位符校验 | 比较格式参数，避免翻译后出现参数丢失、编号变化或转义损坏。 |
| 安全排序 | 先预览，再按默认语言排序；地区独有键保留在末尾且维持相对顺序。 |
| 文件保真 | 保留 UTF-8 BOM、原换行格式和 Android 转义，避免无关的整文件重写。 |

## 工作方式

1. 只定位目标模块及其 `src/main/res`，不扫描无关模块。
2. 使用随附脚本执行只读审计，区分结构缺失和语义翻译缺失。
3. 在修改前说明目标文件、翻译分组、排序方式和验证命令。
4. 使用 XML 感知或精确编辑补齐内容，不改资源名和占位符。
5. 先预览排序结果，确认安全后才写入。
6. 重新审计并检查差异，确认没有误增、误删、重复或语义覆盖。

直接运行审计脚本时，可在仓库根目录执行：

```powershell
$skillDir = Join-Path (Get-Location) "skills\android-string-resource-audit"
python -X utf8 "$skillDir\scripts\audit_android_strings.py" audit "<Android项目>\app\src\main\res"
```

加入 `--json` 可输出机器可读结果；加入 `--strict` 可在结构、排序、编码、乱码或占位符检查失败时返回非零退出码。排序使用 `sort` 子命令，确认预览后再加入 `--write`。

## 输出与边界

最终结果会说明默认键和地区数量、缺失/重复/排序问题、已处理的翻译组、编码与占位符验证，以及未经过母语或真机 UI 检查的风险。

该 Skill 不会仅因“译文与英文相同”就覆盖已有内容，也不会删除地区独有键。遇到异常 XML、重复键或非字符串资源时，会先要求显式修复结构，再允许排序。

实现规则见 [SKILL.md](./SKILL.md)，脚本入口见 [audit_android_strings.py](./scripts/audit_android_strings.py)。
