# Android 提交与代码迁移

`commit-migration` 用于把 Git 提交、提交范围、分支改动或另一 Android 仓库中的指定文件等价迁移到当前工作分支。

## 何时使用

- 将一个或多个提交应用到当前 Android 分支。
- 迁移某个提交范围或另一分支最近的若干提交。
- 在品牌分支之间同步同一业务功能。
- 从另一份本地 Android 仓库迁移指定 Activity、Fragment 或文件集合。
- 源与目标的包名、类名、目录、资源或 Manifest 结构不同，不能直接 cherry-pick。

## 快速使用

迁移单个提交：

```text
使用 $commit-migration 将提交 45959162 等价迁移到当前分支。不要 cherry-pick；先分析包名、资源、Manifest 和当前未提交改动，再实施并验证。
```

迁移提交范围：

```text
使用 $commit-migration 将 45959162..45959199 的 Android 改动迁移到当前分支，并适配当前项目结构。
```

跨仓库迁移指定文件：

```text
使用 $commit-migration 从 D:\SourceApp 迁移指定的 Activity 和 Fragment 到当前项目，只处理我列出的文件及其必要依赖。
```

## 支持的输入

| 输入类型 | 示例 |
| --- | --- |
| 单个提交 | `45959162` |
| 多个提交 | `45959162,45959163` |
| 提交范围 | `45959162..45959199` |
| 分支最近提交 | `branch X` 的最近 3 个提交 |
| 整体分支差异 | 将某分支的相关改动带入当前分支 |
| 本地文件集合 | 源仓库路径加明确的文件列表 |

## 工作方式

1. 解析提交、范围、分支或本地文件选择器。
2. 读取目标项目规则与映射提示，并记录当前工作树的用户改动。
3. 生成预检材料，识别受保护路径、仅合并路径、脏文件冲突和命名碰撞。
4. 映射包名、路径、同职责类、资源、Manifest、导航和 R8 等目标差异。
5. 读取源改动并在目标中实现等价行为，不机械重放补丁。
6. 按静态检查、编译、聚焦测试和 assemble 的顺序验证；只运行实际存在且有必要的任务。
7. 执行 Android 迁移后的跟进检查，确认没有遗留源品牌或包名。

## 重点适配内容

- 包根、源码路径、导入和完全限定类名。
- 同职责但名称不同的 Activity、Fragment、ViewModel 或服务。
- Manifest 组件、Provider authority、深链和权限。
- XML 自定义 View、导航图、资源名和 values 条目。
- 反射字符串、路由字符串、序列化模型名与 R8/ProGuard 引用。
- 目标分支已有定制、未提交文件和名称冲突。

## 安全边界与输出

默认只修改当前分支，不修改源分支，也不自动执行 `checkout`、`cherry-pick` 或 `rebase`。映射可信度低，或迁移会覆盖目标分支定制行为时，会暂停并说明冲突。

输出通常包含源改动摘要、映射关系、冲突处理、实际修改文件、验证结果和仍需人工确认的差异。

完整规则见 [SKILL.md](./SKILL.md)，详细流程见 [workflow.md](./references/workflow.md)，Android 映射规则见 [android-mapping.md](./references/android-mapping.md)，跨仓库快速路径见 [cross-repo-fast-path.md](./references/cross-repo-fast-path.md)。
