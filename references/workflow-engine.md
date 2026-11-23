# Agent 动态编排与阶段交接

## 1. 目标

运行中的 Agent 以 [能力清单](../capabilities/registry.json) 为可用能力来源，从用户要求的交付物反推本轮最短路径。能力可继续增加，编排不受固定编号限制。

## 2. 编排输入

先形成执行简表。字段、取值和加载数量上限以 [编排计划格式](../catalog/_schemas/workflow-plan.schema.json) 为准，写入持久记录前用它校验：

```json
{
  "goal": "用户本次要完成的结果",
  "project_id": "已确认的项目 ID；一次性任务可留空",
  "task_id": "已确认的任务 ID；一次性任务可留空",
  "baseline_version": 1,
  "inputs": ["已有材料及成熟度"],
  "deliverables": ["交付物及格式"],
  "constraints": ["时间、技术、范围和权限"],
  "project_maturity": "idea|defined|specified|prototyped|implemented",
  "task_mode": "analysis|planning|prd|interaction|prototype|review|redesign|change|delivery",
  "prototype_mode": "delivery|exploration|null",
  "execution_depth": "rapid|standard|strict",
  "steps": [
    {"id": "analyze-input", "purpose": "核对材料事实", "status": "planned", "inputs": ["会议纪要"], "outputs": ["事实清单"]},
    {"id": "write-prd", "purpose": "形成需求文档", "status": "planned", "inputs": ["事实清单"], "outputs": ["PRD"]}
  ],
  "decision_gates": ["需要用户选择的路径"],
  "resources": {
    "scenarios": ["built-in:general-product"],
    "component_libraries": ["built-in:native-html"],
    "templates": ["built-in:standard-prd"],
    "cases": []
  },
  "current_capability": "analyze-input"
}
```

`resources` 每一项能装几个由 schema 的 `maxItems` 固定；需要改上限时改 schema，不要在别处再抄一份数字（`SKILL.md` 的「扩展资源匹配」是同一份规则给人看的说法）。用户没有提供的字段可以留空。跨轮任务先按 [跨轮协议](cross-round-protocol.md) 确定项目与任务归属，再读取业务内容；只有缺失内容会改变业务规则、范围或交付形态时才追问。

## 3. 选择与交接

1. 在能力清单中匹配 `when` 与目标，核对 `accepts` 是否已有可靠输入。
2. 只有输入缺口会改变本轮产物时才插入上游能力，如 `clarify-requirements`。已有 PRD、页面规格或原型可直接交给下游。
3. 每阶段只加载本阶段登记的 `instruction` 和必要资源。自动匹配到 `bundled-module` 且其额外确认节奏未获授权时，先告知用户该模块的目录和确认节奏并征得同意；用户不接受时重编能满足目标的简明路径。选定模块后读取完整 `procedure.md`，再按需读取该模块的模板、规范和脚本说明；遵守其工作步骤与确认点。所需文件缺失时报告包不完整，不按清单摘要猜测执行。
4. 完成阶段时核对 `produces`、实际文件路径、状态、来源、待决事项。跨轮阶段还核对规则与输入产物版本，并把依赖写入产物索引。缺少交接物时补做或明确记录缺口，不把草稿当成已确认输入。
5. 用户补充新信息后更新目标任务的轮次记录，只重编受影响的后续阶段。完成一次能力后重新判断终点产物是否已经满足；项目共用规则更新时按产物依赖检查其他受影响任务。

## 4. 编排步骤

1. 跨轮任务先确定项目与任务 ID、允许共享的规则及采用版本；再从交付物反推所需能力，可参考 [常见编排](../workflows/recipes.md)，但不机械执行整条路径。
2. 检查输入成熟度和已存在的产物；能直接进入目标阶段时跳过上游。
3. 区分只读分析、文件修改和外部动作；只执行用户授权的范围。
4. 检查重要路径冲突；有实质影响时进入 [决策门禁](decision-gates.md)。
5. 匹配场景、组件、模板和案例，按 [扩展协议](extension-protocol.md) 解析优先级。
6. 为每阶段登记输入、说明文件、预期产物、检查方式和当前状态。

目标、范围或规则仍有多个可能答案时，先查阅材料和项目上下文，再按依赖关系组织澄清问题。事实由材料核实；只有需要用户取舍的决定才交给用户。简单任务不启动完整访谈。

### 常见反推规则

- 只要问题报告：`analyze-input → review-validate`；不自动修改。
- 只要日常 PRD：范围明确时直接 `write-prd`；否则按缺口补 `analyze-input`、`clarify-requirements` 或 `plan-product`。
- 用户明确要完整六步 PRD：选择 `make-prd`，遵守它的逐阶段确认。
- 只要交互稿：已有需求时直接 `design-interaction`。
- 只要评审原型：已有页面规格时直接 `build-prototype`；只有文字需求时按需补 `design-interaction`。
- UI 或状态有一个待操作验证的问题：选择 `prototype_mode=exploration`；方向已定且供评审或开发时选择 `prototype_mode=delivery`。
- 只要验收：直接 `review-validate`；需要修复时按用户授权追加相应能力。
- 增量变更：先 `analyze-input` 判断影响，再选择受影响能力，最后检查与交付。

## 5. 运行计划格式

复杂任务开始前展示：

```markdown
## 本次运行计划

- 模式：[任务模式] × [执行深度]
- 调用：[能力 ID、目的及阶段产物]
- 跳过：[已有合格产物覆盖的能力及理由]
- 决策点：[需要用户选择的路径]
- 采用资源：[场景、组件、模板、案例及版本]
- 跨轮依据：[项目 ID、任务 ID、规则版本、输入产物版本]
- 交付物：[文件或对话结果]
```

用户可以修改计划。简单、低风险任务在内部完成编排，不需要展示完整计划。

## 6. 计划变更

执行中出现新材料或新要求时：

1. 判断是否改变目标、范围、技术形态或交付物。
2. 小范围变化更新当前节点。
3. 跨阶段变化重新生成受影响部分的计划。
4. 需要用户决策时暂停在门禁处。
5. 连续项目把计划变化写入目标任务的轮次记录；项目级规则变更另记来源和版本，并检查依赖产物。

## 7. 结束条件

满足以下条件后结束本次运行：

- 用户要求的交付物已经生成。
- 探索型原型已记录回答的问题、用户选定方向和仍未验证的部分；后续需要正式产物时重新进入相应能力。
- 必要质量门禁已执行或明确记录未验证项。
- 事实、推断、决策和遗留问题可以区分。
- 没有未经授权的后续修改或外部动作。

