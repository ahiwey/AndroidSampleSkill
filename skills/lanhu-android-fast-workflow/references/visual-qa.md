# 按选择进行验收

UI 任务先完成实现和最小静态检查，处理已发现问题后，再集中询问一次：“是否继续使用 Paparazzi 离屏截图、真机/模拟器截图验证，还是暂不进行视觉验证（仅静态检查）？”已有本范围明确选择或授权时沿用，不重复询问；普通“实现/修复/继续”不构成视觉测试授权。选择前不运行 Paparazzi、ADB/设备探测、安装、启动、点击、UI tree、截图、日志采集或创建模拟器。Paparazzi 不授权设备操作或新增依赖；先核实已有框架，缺失时说明接入成本并确认，不自动切换路线。分别报告静态、视觉和运行结果；旧截图、新录 baseline 或编译通过均不能替代当前设计对照。资源/编译/普通单测按风险最小执行，不默认全量构建。

## 选择与执行边界

- 仅静态：核对 [视觉契约](visual-contract.md)、实际资源引用、布局分组和图表边界计算；可读取用户已有截图和本地设计图，不称为 App 视觉通过。
- Paparazzi：先只读确认现有模块、插件版本、测试入口、可用 task 与 XML/custom View 支持；获选择后跑一个覆盖目标区域的最窄测试。尚未配置时先确认新增依赖/测试接入，不默认安装，也不默认换成 Roborazzi 或设备。
- Paparazzi 使用实际页面/组件代码与资源，不能重画一份“理想布局”当验证对象。固定 viewport、density、fontScale、locale、主题和数据，保留零值及非零 fixture。新录制 baseline 只是候选图，必须实际查看并对照设计，不能 record 后 verify 成功就称还原正确。
- 真机/模拟器：仅本范围明确授权后探测；复用有效设备状态。不自动创建模拟器。检查 APK 对应最新源码、主题、状态、语言和数据；证据注明构建/源码版本及 fixture，源码变化后的旧截图只算历史证据，主要链路与代表页即可。
- 离屏快照不验证 BLE、导航、账号、生命周期或真实交互。公共资源替换静态查受影响变体，获相应验收选择后抽查目标组件及另一使用位置。未覆盖的明确列出。
- 缺素材、左右结构错、错图标、字体颜色角色错、柱形语义错必须处理；细微字形或阴影偏差可注明后交付。不默认全状态矩阵和连续精修。

## 证据分层与可重复输入

- 组件渲染、纯状态/存储测试、真实宿主/导航运行分别记结果。手工 inflate 弹窗、叠遮罩或替代 Context 只证明该组件/替身场景；注明与真实 Fragment/Dialog、窗口、键盘及生命周期的差异。避免把存储断言塞入截图测试而迫使纯逻辑验证运行截图框架。
- 除 viewport 等条件，还固定 Clock/now、时区、日期分组、locale 与测试数据时间戳；检查模型默认时间及 LocalDate.now() 等隐式输入。优先沿用现有注入/fixture，不为测试自动加依赖。截图测试通过不能证明真实请求、保存或导航。
- 长文本/窄屏仅选风险最高的代表状态：核对卡片父子宽度、weight/约束、wrap_content、最大宽度、换行及输入栏。修父布局后复看受影响的欢迎/消息/选择态，而非重复打开全部截图。
- 新图先对照设计；重跑后优先查看变化图和受影响锚点。哈希未变只表示文件相同，不表示已审查或对应当前源码；不要用手绘测试宿主掩盖实际页面问题。

## 只读摘要与中断续验

`python scripts/verification_summary.py --report <exact-JUnit.xml> --snapshot <exact-image.png>`：参数可重复；可用 `--previous <已有摘要.json>` 比较哈希。只向 stdout 输出现有证据，不写文件、不运行测试/构建/设备；无 testcase、报告缺失或损坏返回 incomplete/非零。失败细节有界；通过仅表示所选报告通过，源码新鲜度、视觉审查及运行仍须另证。仅选本范围文件，避免混入不同运行的重复报告；需要保存时沿用已确认目录。

- 等待长任务优先用会话完成通知/有界等待，不连续 tail 同一日志；完成后一次汇总报告和变化截图，在原映射追加结果。
- 中断时在原映射简记：源码/产物标识、已授权范围、构建/安装/启动/场景各阶段结果、下一项。构建成功不等于安装完成；恢复时只复核源码与产物是否仍匹配、授权是否仍在本范围，继续缺项，不重跑已有效阶段。其他任务的设备授权不能继承。
- UI tree 获取/解析失败先保存首个错误并区分命令失败、XML 提取和页面状态；原因明确后最多一次针对性重试。仍失败则在已授权范围采用已知截图/导航证据或报告阻塞，不循环变更 dump 命令。截图只能证明可见状态，不能替代未执行的点击/保存链路。

## 路由工具调用

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
