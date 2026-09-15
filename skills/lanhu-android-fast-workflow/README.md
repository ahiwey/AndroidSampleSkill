# 蓝湖 Android 快速实现

用于几页 UI 的主要视觉、交互和跳转实现，默认不调用 MCP，以本地原图和 xxhdpi 切图为输入。先做通流程，再按反馈修局部。
规则入口：[SKILL.md](SKILL.md)。

```text
使用 $lanhu-android-fast-workflow 实现这组页面的主要 UI、交互和跳转。
本地设计图/切图目录或蓝湖链接：……
页面范围：……
对照产物目录：……
默认快速模式、不调用 MCP；缺设计的下游页接可返回空页，缺项交付时汇总。
```

项目有更严构建时限而希望覆盖时，补充：“本次最终安装构建允许最多 10 分钟。”
局部修复：“只修截图中的图标大小，不扩大精修范围。”
精修模式：“对指定区域高度还原，并做同场景截图对照。”

## 实现流程

1. 实际看设计图，按共用页面和差异状态归组，定向找现有源码。
2. 用一张短表记页面位置、动作结果和资源缺项，普通跳转自行判断。
3. 先完成代表页的主要布局、图片、图标背景和文字层级，再复用到其他页并接通流程。
4. 合并必要检查；有已授权可用真机优先走主要链路，无真机复用已有适用验收工具。细微样式差异不反复调整，空页和未验证项如实交付。

主要页面有设计就实现；空页仅用于缺少设计且允许暂缺内容的下游入口。跳转需带正确对象/日期等参数，返回与已有刷新机制接通。
本轮优化集中减少重复看图、逐页重复实现、重复构建和无关工具调用；尚未实测完整任务耗时及 Token 节省比例。

## 工具

按需使用：本地文件已整理就跳过素材脚本；已经知道设备条件就复用验收路径。自测与官方校验仅用于修改 Skill 后验证，不在每次页面实现时执行。

```powershell
python scripts/local_assets.py --input "<zip-or-directory>" --designs "<design-dir>" --output "<review-dir>" --density xxhdpi
powershell -NoProfile -File scripts/visual_qa_router.ps1 -ProjectRoot "<project>" -Scope interaction
powershell -NoProfile -File scripts/self_test.ps1
```

本地整理只需 Python 3，支持 PNG、JPEG 和 WebP 的尺寸检查，并记录 PNG/WebP 的透明通道信息。检查限文件头和结构，不等同完整像素解码，也不校正 JPEG 的 EXIF 旋转；SVG 等格式保留并列尺寸待检。
在线适配器需要已有 Node.js、浏览器和 playwright-core，不保证官方 ZIP 自动下载。
完整自测还需 Node.js/JDK；不自动安装依赖。

## 官方格式校验

PyYAML 只用于 Skill 编写阶段的 YAML 校验，不是 Android 或本地取图依赖。
在 Skill 目录执行，安装和验证必须使用同一个 Python：

```powershell
python -m pip install --user -r requirements-validation.txt
python scripts/validate_skill.py
powershell -NoProfile -File scripts/self_test.ps1 -ValidateSkill
```

虚拟环境内安装时省略 `--user`。脚本不自动安装依赖；缺少依赖会明确失败，不会宣称校验通过。
官方校验器位于其他位置时使用 `python scripts/validate_skill.py --validator "<quick_validate.py-path>"`。
