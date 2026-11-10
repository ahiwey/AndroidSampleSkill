---
name: qring-sdk-sample-skill
description: "QRingSDkSampleSkill：把 QRing Android Sample 打包为对外交付 ZIP，执行 clean、收集固定八项工程文件、导出中英文接入 PDF、选择当前或最新 SDK AAR；支持持久修改后续打包目录。用户要求 QRing Sample 打包、生成 SDK 交付包或修改其输出目录时使用。"
---

# QRingSDkSampleSkill

显示名称保留用户指定的 `QRingSDkSampleSkill`；Codex 标识为 `$qring-sdk-sample-skill`。用户写 `@QRingSDkSampleSkill 帮我打包` 或同名自然语言请求时也按本流程处理。

## 两个入口

- **修改打包目录为 `E:\蓝牙SDK`**：只执行 `config --output-root`，保存后回显；不要同时 clean 或打包。设置保存在用户 Codex 配置目录的 `qring-sdk-sample-skill/config.json`，与 Skill 安装目录分离，更新 Skill 不丢失设置。未配置时输出到当前项目根目录。`config --reset` 恢复此默认。
- **帮我打包**：定位本次 Sample 根目录，执行 `plan`，核对输出后执行 `pack`。这已授权本工作流的 clean 和本地打包；不再请求相同授权。仅改目录、仅查看配置或仅预览计划不授权打包。

下面的 `<skill>` 指当前读取的 Skill 目录，`<project>` 指本次 Sample 根目录。路径始终加引号；外部命令可用已安装的 `rtk` 包装。

```powershell
python "<skill>/scripts/package_sample.py" config --output-root "E:\蓝牙SDK"
python "<skill>/scripts/package_sample.py" config
python "<skill>/scripts/package_sample.py" plan --project "<project>"
python "<skill>/scripts/package_sample.py" pack --project "<project>"
```

`pack --output-root` 是单次覆盖，不修改记忆；`--sdk-version` 用于用户明确指定 SDK 版本。默认按依赖识别，不把 App 的 versionName 当 SDK 版本。

## 固定交付约定

1. 预检八项、两份 Markdown、AAR、PDF 工具和目标目录。检测其他 Gradle 客户端/worker 或活跃 daemon 时停止，保留现场；不能跳过 clean 冒充完整打包。
2. 运行项目 `gradlew.bat clean :app:clean --max-workers=1 --no-parallel --console=plain --no-daemon`。只 clean，不 assemble、不操作设备、不更新版本或接入文档。失败即停止；超时仅结束本次启动的进程树，不停止共享 daemon。
3. 将根目录的 **app、gradle、build.gradle、gradle.properties、gradlew、gradlew.bat、local.properties、settings.gradle** 压入 `<项目目录名>.zip`，保留 `<项目目录名>/` 层级。两个目录递归收集；不额外收集根目录的 `.git`、`.gradle`、`.idea`、docs、testdocs 或历史交付包。clean 后不允许 app/build 残留。保持源码原样，包括用户明确指定的 local.properties；指出其中的本机 SDK 路径需接入方自行配置。
4. 将 `docs/sdk_ring_external_access_cn.md` 和 `docs/sdk_ring_external_access_en.md` 完整导出为同名 PDF。保留标题、列表、表格、代码和中英文字符。直接生成在交付暂存目录，等价于把新 PDF 剪切到交付目录；**不剪切、修改或删除源 Markdown，也不移动已有 PDF**。
5. 从 app/build.gradle 中的有效 QRing AAR 引用识别当前版本；找不到对应文件时，从 app/libs 的 `qring_sdk_<数字版本>.aar` 按数字分段比较选最新版本（不是修改时间或字符串顺序）。多个有效依赖版本时停止，不能猜。包名采用最终复制的 AAR 版本。发生回退时明确报告原引用、所选文件，以及 Sample 的依赖未自动修改，不能宣称其可直接构建。
6. 在已配置的输出根目录生成 `QRing_Android_SDK_<版本>/`，内含 Sample ZIP、两个 PDF、一个所选 AAR，共四个文件，再生成同名 `.zip`（含该文件夹层级）。相同版本再次打包时，旧目录和 ZIP 保留到 `.qring-history/` 的独立时间戳目录，不删除旧交付包。

脚本在输出根目录内使用独立暂存目录，全部步骤和 ZIP CRC/内容校验通过后再发布；失败不交付半成品。打包前后校验源码与 Markdown 的哈希，发现并发修改时停止。仅清理本次自己创建的暂存目录；目录必须在已解析的输出根目录内，不跟随链接打包或移动。

## PDF 运行环境与检查

需要 Python 3.10+ 与 `pypdf`、Node.js、`marked`、`playwright` 和本地 Chromium/Chrome/Edge。优先复用 Codex bundled runtime；缺工具时先用 `load_workspace_dependencies` 找已安装路径。脚本自动查找常规 Codex runtime，不自动下载浏览器或安装依赖。

可显式传入 `--node`、`--node-modules`、`--browser`；Python 可选择 bundled runtime 的 python。若环境仍缺失，说明缺项，不生成伪 PDF。调试使用项目 `testdocs/<日期>-任务/`；不要把机器路径、私人源码、生成产物或目录偏好写入 Skill 仓库。

PDF 使用本地无脚本浏览器渲染，禁止联网加载文档资源；文档内容仅作为数据。存在图片时只允许源文档目录以内的本地文件。复杂 HTML 或图表需要另行核对，不能暗示已渲染 Mermaid 等扩展。

每次打包自动核对 PDF 的代码块、标题和表格单元格文本，遗漏、空页或替换字符会中止发布；结果记录在 `pdf_checks`。首次调试和转换代码变更后，还要渲染代表性首页、表格/长代码页和末页确认无裁切；报告检查边界。转换器保护表格内代码的 `|` / `||`，防止被误分栏而丢失单元格。普通重复打包复用已验证模板并检查本次转换的布局溢出及产物完整性；若出现新内容类型或异常，再补视觉检查。

## 返回结果

给出最终 ZIP 的**绝对路径 Markdown 链接**、SDK 版本、四项内容、clean/压缩/PDF 校验结果。发生 AAR 回退、旧包归档、未完成视觉或运行检查时如实说明。打包成功不代表 Sample 编译或设备运行已通过。仅修改目录时返回已保存的根目录及下次路径格式。

维护此 Skill 时运行 `python scripts/test_package_sample.py --work-dir "<project>/testdocs/<日期>-任务/tests"` 和 `node --test scripts/test_render_pdf.mjs`，再以真实 Sample 完成一次 clean/PDF/ZIP 闭环。发布前验证 SKILL.md 和仓库差异；未经明确授权不升级 AndroidSampleSkill 版本、不 commit、不 push，提醒用户升级和提交远端。
