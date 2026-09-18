# 按选择进行验收

UI 任务先完成实现和最小静态检查，处理已发现问题后，再集中询问一次：“是否继续使用 Paparazzi 离屏截图、真机/模拟器截图验证，还是暂不进行视觉验证（仅静态检查）？”已有本范围明确选择或授权时沿用，不重复询问；普通“实现/修复/继续”不构成视觉测试授权。选择前不运行 Paparazzi、ADB/设备探测、安装、启动、点击、UI tree、截图、日志采集或创建模拟器。Paparazzi 不授权设备操作或新增依赖；先核实已有框架，缺失时说明接入成本并确认，不自动切换路线。分别报告静态、视觉和运行结果；旧截图、新录 baseline 或编译通过均不能替代当前设计对照。资源/编译/普通单测按风险最小执行，不默认全量构建。

## 选择与执行边界

- 仅静态：核对 [视觉契约](visual-contract.md)、实际资源引用、布局分组和图表边界计算；可读取用户已有截图和本地设计图，不称为 App 视觉通过。
- Paparazzi：先只读确认现有模块、插件版本、测试入口、可用 task 与 XML/custom View 支持；获选择后跑一个覆盖目标区域的最窄测试。尚未配置时先确认新增依赖/测试接入，不默认安装，也不默认换成 Roborazzi 或设备。
- Paparazzi 使用实际页面/组件代码与资源，不能重画一份“理想布局”当验证对象。固定 viewport、density、fontScale、locale、主题和数据，保留零值及非零 fixture。新录制 baseline 只是候选图，必须实际查看并对照设计，不能 record 后 verify 成功就称还原正确。
- 真机/模拟器：仅本范围明确授权后探测；复用有效设备状态。不自动创建模拟器。检查 APK 对应最新源码、主题、状态、语言和数据；证据注明构建/源码版本及 fixture，源码变化后的旧截图只算历史证据，主要链路与代表页即可。
- 离屏快照不验证 BLE、导航、账号、生命周期或真实交互。公共资源替换静态查受影响变体，获相应验收选择后抽查目标组件及另一使用位置。未覆盖的明确列出。
- 缺素材、左右结构错、错图标、字体颜色角色错、柱形语义错必须处理；细微字形或阴影偏差可注明后交付。不默认全状态矩阵和连续精修。

## 路由工具

路径相对 Skill 根目录。工具不执行测试、构建或安装；不把路由结果当作验收通过。默认 static；如实传入 -StaticChecksCompleted 表示实现与最小静态检查完成且发现的问题已处理，否则视觉路线返回 complete-static-first。只有 device 加设备授权且静态检查完成才探测 ADB：

```powershell
pwsh -NoProfile -File "<skill-root>/scripts/visual_qa_router.ps1" -ProjectRoot "<project>" -Validation static
pwsh -NoProfile -File "<skill-root>/scripts/visual_qa_router.ps1" -ProjectRoot "<project>" -Validation paparazzi -StaticChecksCompleted -Scope layout
# Only after the user selected device validation:
pwsh -NoProfile -File "<skill-root>/scripts/visual_qa_router.ps1" -ProjectRoot "<project>" -Validation device -StaticChecksCompleted -DeviceAuthorized -Scope interaction
```

检测到 Paparazzi 文本仅是线索，可能位于注释或未启用配置；模块/build-logic 自定义配置需定向核实。unverified 表示缺少适用环境，不自动切换或安装。

## 最小构建与返工

复用覆盖当前修改的 APK；确需最终安装才合并修改后运行一次最窄 assemble。源码已变化不能用旧 APK 宣称通过。
纯资源/编译按项目规则，不因未选视觉测试强行 assemble。先确认任务名和无实际活跃构建；限制并发，不 clean、不停止共享 daemon。
最终安装构建默认最多 600 秒，项目更严限制优先。超时只取消本次进程，不重跑全套。
返回成功摘要或首个关键错误，不输出长日志。

返工先看最新局部证据、实际资源与父布局；已选的验收方式覆盖不了新风险时仅确认增量，不自动开启设备。回归之前接受的 3–6 个锚点，不连续猜 offset。
按需使用 ImageDiff.java 定位差异，自动相似分数不代替语义验收；合成图不是 App 截图。

交付区分代码、资源/编译、离屏截图、设备运行和数据受限；空页只验证打开/返回，不宣称内容/保存/同步完成。
