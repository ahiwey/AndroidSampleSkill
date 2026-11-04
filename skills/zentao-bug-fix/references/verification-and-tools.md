# 验收证据与本地工具

在开始验证、恢复批次或维护 Skill 时读取。本文工具只处理本地证据和建议，不连接禅道、创建聊天、操作设备、改 Git 索引或授权任何动作。`<skill>`、`<repo>`、`<batch>` 均替换为本次已确认的真实绝对路径。

## 每条先回答“测试是否会触发缺陷”

| 证据 | 能说明什么 | 不能自动说明什么 |
| --- | --- | --- |
| 静态检查/编译 | 规则、分支和类型检查的实际范围 | 点击、时序和服务端行为 |
| 生产组件 Paparazzi＋看图 | 指定数据、语言、主题下的画面 | 被 fixture 绕过的守卫、保存/刷新、上传及宿主导航 |
| 触发真实修复路径的聚焦测试 | 覆盖的缺陷行为与边界；适用时有红绿证据 | 未触及的宿主、设备或网络链路 |
| 获授权的真实交互 | 本次设备/版本/入口/场景的实际结果 | 其他设备、版本或全部场景 |
| 禅道刷新读回 | 两个目标字段实际落库 | 代码功能正确或已发布 |

关键反事实检查：恢复旧逻辑后，本测试是否仍会通过？若测试根本没有经过改动路径，或只是手工填入期望值，则只计组件显示；无需为证明这点回滚共享工作区。可隔离行为优先用真实函数做聚焦回归，不复制一份判断当被测对象。

默认静态＋已有 Paparazzi 是本 Skill 配置的验收方式，执行时声明即可。使用生产布局/View，只跑目标场景，复用覆盖最终源码的编译日志；生成后必须查看截图。框架不存在先记录受阻并说明接入或改验收方案的选项，不自动加依赖。纯逻辑且没有 UI 输出时记录不适用理由和实际非设备行为验证；缺框架或构建失败不属于不适用。

两项默认检查完成且没有已知失败，可以按授权确认 Bug；总报告和最终回复仍必须分开列“缺陷回归通过”和“行为待回归”。后者不强制申请设备权限才能交付，不能擅自升级为真机。用户已要求真实交互时，不以离屏通过替代。

## 只做一次工作区基线

主聊天在任务开始时将基线保存到已约定批次目录（优先已被项目忽略的目录），目录须已存在：

```text
python -B <skill>/scripts/workspace_guard.py capture --repo <repo> --output <batch>/workspace-before.json
python -B <skill>/scripts/workspace_guard.py check --repo <repo> --baseline <batch>/workspace-before.json --allow-new app/path/Fix.kt
```

`--allow-new` 可重复，只放本次允许修改且起点无差异的精确文件路径。工具以 UTF-8 解码 Git 的 NUL 分隔结果，识别中文/空格/重命名，记录 HEAD、分支、索引内容及已有改动文件哈希；不保存文件正文或凭据，不覆盖已存在的基线。`check` 输出 JSON，退出码 0=一致，1=发现变化，2=输入/环境错误。命令级 safe.directory 仅限显式目标仓库，不写全局配置。

已有改动文件被本次合法修改时，检查仍应报告变化：主聊天据差异逐块确认旧改动保留，不把文件加入豁免列表来假装基线未变。目录/子模块内容不递归哈希，相关任务需另做定向复核。不能用哈希代替语义检查。子聊天只引用同一份基线，最终验证后复核一次；中途出现新编辑或外部变化时才重查。

## 写回前使用本地验收检查

将本条已获得的真实证据摘要保存为 `<batch>/bug-<id>/acceptance.json`，例如：

```json
{
  "code": "done",
  "checks": {"static": "passed", "paparazzi": "passed"},
  "behavior": {"status": "not_run", "coverage": "component_only", "evidence": ""},
  "writeback": {"requested": true, "authorized": true, "attempted": false, "observation": "unchanged", "retry_count": 0}
}
```

```text
python -B <skill>/scripts/workflow_guard.py acceptance <batch>/bug-<id>/acceptance.json
```

- `code`：`pending/done/failed/skipped`。缺交接或差异未复核时为 pending；纯复测 done 表示约定复测已完成，不虚构修复。
- `checks`：本条必要检查项及 `passed/failed/pending/not_applicable`。默认要求 static、paparazzi；添加的编译等项目也必须 passed。未覆盖的可选行为放在 behavior 中，不能将已知失败省略。
- Paparazzi 无 UI 不适用：`checks.paparazzi=not_applicable`、填写 `no_ui_reason` 并要求 `checks.non_visual=passed`。用户另选验收方式时提供 `validation_override`，含 `authorized: true`、非空 `reason` 及 `required` 检查名列表；授权必须有本轮人类依据。
- `behavior.status`：`passed/failed/not_run`。只有实际触发缺陷路径才填 `coverage=defect_path` 和非空 `evidence`（日志/报告路径）；仅画面通过仍是 component_only。脚本不会读取日志来替人判断覆盖率，不能通过伪填字段获得通过。
- `writeback.observation`：`unchanged` 表示刚读回的两字段仍是已知原值；`matches` 表示刚读回符合目标；`unknown` 表示尚未核验；`conflict` 表示他人改动影响决策。默认 unknown，不能凭之前的成功提示填 matches。明确写回失败使用 `failed: true`。
- 不写禅道用 `requested: false`；需写但没有人类授权时 `authorized: false`。设备权限不在此 JSON 中授予，仍按主 Skill 单独核实。

输出中 `ready_for_writeback` 只是已有检查结果下的建议；`flow=complete` 还需要写回读回或明确不写回。`behavior=needs_regression` 必须进入主报告，即使 flow 已完成。`do_not_write/needs_authorization/readback_first/needs_attention/writeback_failed` 均不能执行确认。退出码 0 只表示成功计算建议，不代表 Bug 验收通过；必须看返回字段。

## 超时与下一轮排程

使用同一脚本的 `writeback/creation/schedule` 子命令检查相应 JSON，读取建议后才使用真实工具：

- `writeback` 输入与上述 writeback 对象一致：保存超时先标 attempted=true、observation=unknown，先读回；目标已符合不重复提交；确认原值未改才允许一次有依据重试，仍不明或失败就停止。
- `creation` 输入 `{"observation":"unknown"}`：超时建议 lookup_first；工具查到已有任务改为 exists→reuse，确认不存在才 absent→create。查询超时不等于不存在。
- `schedule` 输入 `{"limit":3,"completed":[],"tasks":[{"id":"项目:编号","files":["app/Fix.kt"],"depends_on":[]}]}`，只输入下一轮候选；上一轮写入须已结束。同文件、依赖未完成、范围不明均 deferred；Windows 默认忽略路径大小写，需区分时设置 case_sensitive=true。共享 API/资源契约的冲突仍由主聊天判断，必要时填依赖；此脚本不分析代码。重名 ID 拒绝，不能用新 ID 重建旧任务。

## 维护时的实际验证

```text
python -B -m unittest discover -s <skill>/tests -p test_*.py -v
```

测试调用实际辅助函数与 CLI，并在自动清理的临时 Git 仓库验证基线；没有生产写入。覆盖默认有限验收、组件测试不能冒充行为回归、缺失/失败检查、缺失交接、显式改验收、无权限、写回失败/超时、重复创建、同文件/依赖排程、中文路径、索引保留及基线不可覆盖。

这些测试证明本地判定与基线工具的行为，不证明智能体已正确读取网页或真实服务可用。维护时再用脱敏样例逐条核对“输入证据 → 建议 → 报告”是否一致；实际浏览器和设备效果只引用带日期的真实证据。不要用匹配几句文案或结构评分冒充工作流端到端验证。
