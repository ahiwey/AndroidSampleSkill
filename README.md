# AndroidSampleSkill

面向 Android 工程与智能体协作流程的可复用 Codex Skills 集合。本仓库只收录由 [ahiwey](https://github.com/ahiwey) 编写和维护的 Skill，不包含本机 Codex 环境中安装的第三方 Skill。

## Skills 一览

| Skill | 主要功能 | 适用场景 | 详细说明 |
| --- | --- | --- | --- |
| `multilingual-faq-sync` | 将 FAQ 的增删改按英语结构坐标快速同步到默认 11 个语言 JSON，自动处理编号、占位符和一致性验证。 | `q_cn/q_en` 等 FAQ 多语言维护、批量新增、删除、更新与结构修复。 | [打开文档](./skills/multilingual-faq-sync/README.md) |
| `android-string-resource-audit` | 审计、补齐并安全排序 Android 多语言 `strings.xml`，检查占位符、编码、乱码和键顺序。 | 缺失翻译、英文回退、批量同步 `values-*`、资源排序。 | [打开文档](./skills/android-string-resource-audit/README.md) |
| `android-open-source-integration` | 规划并实施可追溯、可访问、可移除且符合许可证要求的 Android 开源代码集成。 | 集成 GitHub Android 项目、页面、资源、依赖或模块。 | [打开文档](./skills/android-open-source-integration/README.md) |
| `android16-adaptation` | 审计、实施和验证 Android 16 / API 36 兼容性及发布就绪状态。 | 升级 SDK 36、edge-to-edge、预测性返回、16 KB、平板/折叠屏适配。 | [打开文档](./skills/android16-adaptation/README.md) |
| `commit-migration` | 将提交、分支或另一仓库中的指定文件等价迁移到当前 Android 分支，并适配包名、资源和 Manifest。 | 跨分支、跨品牌或跨仓库移植改动。 | [打开文档](./skills/commit-migration/README.md) |
| `optimize-agent-workflow` | 从近期任务证据中定位返工、耗时和 Token 浪费，并安全改进规则、Prompt 与工作流。 | 智能体任务复盘、持续优化、规则治理。 | [打开文档](./skills/optimize-agent-workflow/README.md) |
| `reasoning-playbooks` | 展示、选择并执行 12 种常用推理与决策方法。 | 概念解释、事实核查、方案比较、系统调研和最小实验。 | [打开文档](./skills/reasoning-playbooks/README.md) |

独立项目 [AndroidEasyRules](https://github.com/ahiwey/AndroidEasyRules) 仍以其原仓库为准，本仓库只提供链接，不重复收录。

## 安装

克隆仓库：

```powershell
git clone https://github.com/ahiwey/AndroidSampleSkill.git
Set-Location AndroidSampleSkill
```

将一个 Skill 安装到 Codex 默认 Skill 目录：

```powershell
$skillRoot = Join-Path $env:USERPROFILE ".codex\skills"
Copy-Item -Recurse -LiteralPath ".\skills\android-string-resource-audit" -Destination $skillRoot
```

需要安装其他 Skill 时，将 `android-string-resource-audit` 替换为 `skills/` 下对应的目录名。覆盖已安装版本前，请先检查或备份目标目录。

## 使用

在 Codex Prompt 中使用 `$skill-name` 显式调用：

```text
Use $android-string-resource-audit to audit app/src/main/res and safely reorder locale strings.xml files.
```

也可以直接描述任务；当请求符合 `SKILL.md` 中的触发条件时，Codex 可自动选择对应 Skill。每个 Skill 的详细文档提供了可复制的 Prompt、执行流程和注意事项。

## 仓库约定

- Keep each skill self-contained under `skills/<skill-name>/`.
- Keep only reusable instructions, scripts, references, assets, and `agents/openai.yaml` inside a skill.
- Validate every `SKILL.md` before publishing.
- Do not add system, plugin-cache, Google-authored, OpenAI-authored, or third-party skills to this repository.
- Never commit credentials, project secrets, generated build output, or private application source.

## 许可证

本项目采用 [MIT License](LICENSE)。
