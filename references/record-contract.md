# 跨轮记录数据契约与实现计划

本文件定义 [跨轮协议](cross-round-protocol.md) 的机器可检查格式。适用于需要持久记录的项目；单次简短分析无需创建这些文件。格式版本为 `1.0`，对应 [JSON Schema](../catalog/_schemas/project-records.schema.json)。

## 目标与边界

- 六类文件共用明确字段：项目索引、项目、任务、业务规则、产物索引、轮次记录。
- 写入前校验结构；接续任务时校验现存记录和跨文件关联，发现错误后暂停依赖这些记录的交付。
- 校验工具只读，不补字段、不迁移旧 `context.json`、不修改产物，也不判断业务规则是否正确。
- 校验工具检查已登记引用，不检查产物文件内容、内容哈希或交互质量；这些仍按交付标准单独核对。
- 用户指定记录目录时沿用指定目录；校验工具接受项目集合根目录或单个项目目录。

## 统一约定

- 所有记录均包含 `schema_version: "1.0"`；不支持的版本报错，不能当作当前格式继续写入。
- ID 是稳定、非空的字符串；同一项目内任务 ID 唯一，同一业务规则的 `rule_id@revision` 唯一，同一产物的 `artifact_id@version` 唯一。
- 时间使用带时区的 ISO 8601 字符串；未知时间用 `null`，不能填猜测值。
- 初建项目的 `baseline_version` 为 `1`；每次确认项目级规则变更后递增。任务记录保留开轮时采用的版本，允许低于当前项目版本，但交付前需按跨轮协议复查差异。
- 规则确认状态为 `confirmed` 时，`confirmed_by` 和 `confirmed_at` 必须有值；其他状态可为 `null`。旧规则被替代时保留历史版本，使用 `supersedes` 指向 `rule_id@revision`。
- 项目级规则文件的 `task_id` 为 `null`；任务级规则文件的 `task_id` 为对应任务 ID。观察事实 `observation` 不自动视为目标需求。
- 产物可直接依赖项目级规则和本任务规则；不得直接依赖其他任务的任务级规则。跨任务复用具体成果时登记上游产物版本；需要共享业务口径时先确认并提升为项目级规则。
- 已确认的新规则版本替代旧版后，依赖旧版的非 `superseded` 产物及其下游产物都必须标记 `freshness=needs_review`。校验器发现漏标时报错，不自动修改状态；尚未确认的新版本不触发漏标检查。
- 项目索引仅存定位字段；`path` 指向项目目录。产物 `path` 可指向用户指定的外部文件，但校验工具不因此扫描其他目录。
- 词汇表路径写在 `glossary_path`：项目级在 `project.json`，任务级在 `task.json`。没有词汇表时填 `null`——显式写 `null` 比省略更容易区分“没有”和“忘了写”。

## 文件与关键字段

| 文件 | 顶层必填字段 | 主要内容 |
| --- | --- | --- |
| `projects.json` | `schema_version`, `projects` | `project_id`, `name`, `path` 的索引数组 |
| `project.json` | `schema_version`, `project_id`, `name`, `baseline_version`, `status`, `updated_at` | 项目身份、共用基线和词汇表路径 `glossary_path`（可选） |
| `task.json` | `schema_version`, `project_id`, `task_id`, `goal`, `baseline_version`, `status`, `current_stage`, `confirmed_decisions`, `open_questions`, `latest_run_id` | 本任务目标、断点、待决事项和任务级词汇表路径 `glossary_path`（可选） |
| `business-rules.json` | `schema_version`, `project_id`, `task_id`, `rules` | 带来源、范围、确认状态和版本的规则数组 |
| `artifact-index.json` | `schema_version`, `project_id`, `artifacts` | 产物版本、状态（`status` 表示生命周期，`freshness` 表示依据是否仍有效）、规则和上游产物依赖 |
| `runs/<run-id>.json` | `schema_version`, `project_id`, `task_id`, `run_id`, `goal`, `baseline_version`, `input_artifacts`, `capabilities`, `decisions`, `changed_files`, `checks`, `open_questions`, `current_stage`, `next_step` | 一轮执行与交接断点 |

`decision` 元素（`task.confirmed_decisions` 和 `run.decisions` 共用同一形状）：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `id` | 是 | 稳定编号，如 `decision-001` |
| `topic` | 是 | 这个决定要回答什么问题 |
| `choice` | 是 | 选了哪条路径 |
| `reason` | 是 | 为什么这么选；替换旧决定时写明替代了哪一条 |
| `confirmed_by` | 否 | 确认人；尚未确认填 `null` |
| `confirmed_at` | 否 | 确认时间，带时区；尚未确认填 `null` |
| `affected_deliverables` | 否 | 受影响的交付物标识 |

## 最小可用示例

下面每段都是**能直接通过校验**的最小记录。照抄后改字段值即可，不必先去读 schema。

**`projects.json`**

```json
{
  "schema_version": "1.0",
  "projects": [
    { "project_id": "refund-a", "name": "甲客户退款", "path": "refund-a" }
  ]
}
```

**`refund-a/project.json`**

```json
{
  "schema_version": "1.0",
  "project_id": "refund-a",
  "name": "甲客户退款",
  "baseline_version": 1,
  "status": "active",
  "glossary_path": "domain-glossary.md",
  "updated_at": "2026-10-11T06:58:06+00:00"
}
```

**`refund-a/tasks/order-refund/task.json`**

```json
{
  "schema_version": "1.0",
  "project_id": "refund-a",
  "task_id": "order-refund",
  "goal": "完成退款审核的需求与原型",
  "baseline_version": 1,
  "status": "in_progress",
  "current_stage": "write-prd",
  "glossary_path": null,
  "confirmed_decisions": [
    {
      "id": "decision-001",
      "topic": "prototype-technology",
      "choice": "single-file-html",
      "reason": "本轮用于评审和跨团队分发",
      "confirmed_by": "user",
      "confirmed_at": "2026-10-11T06:58:06+00:00",
      "affected_deliverables": ["prototype"]
    }
  ],
  "open_questions": ["驳回后是否允许重新提交"],
  "latest_run_id": "run-001"
}
```

**`refund-a/business-rules.json`**（项目级；任务级结构相同，把 `task_id` 填成具体任务）

```json
{
  "schema_version": "1.0",
  "project_id": "refund-a",
  "task_id": null,
  "rules": [
    {
      "rule_id": "REFUND-07",
      "revision": 1,
      "kind": "requirement",
      "statement": "驳回后允许重新提交",
      "scope": "退款审核",
      "source": { "type": "user", "detail": "2026-10-11 评审会确认" },
      "status": "confirmed",
      "confirmed_by": "user",
      "confirmed_at": "2026-10-11T06:58:06+00:00",
      "supersedes": null
    }
  ]
}
```

**`refund-a/artifact-index.json`**

```json
{
  "schema_version": "1.0",
  "project_id": "refund-a",
  "artifacts": [
    {
      "artifact_id": "prd-v1",
      "task_id": "order-refund",
      "type": "prd",
      "path": "PRD文档/订单管理1.0-02-PRD.md",
      "version": 1,
      "status": "reviewed",
      "freshness": "current",
      "depends_on_rules": [{ "rule_id": "REFUND-07", "revision": 1 }],
      "depends_on_artifacts": [],
      "checks": ["回读全文", "编号一致"],
      "updated_at": "2026-10-11T06:58:06+00:00"
    }
  ]
}
```

**`refund-a/tasks/order-refund/runs/run-001.json`**

```json
{
  "schema_version": "1.0",
  "project_id": "refund-a",
  "task_id": "order-refund",
  "run_id": "run-001",
  "goal": "生成 PRD",
  "baseline_version": 1,
  "input_artifacts": [],
  "capabilities": ["write-prd"],
  "decisions": [
    {
      "id": "decision-001",
      "topic": "prototype-technology",
      "choice": "single-file-html",
      "reason": "本轮用于评审和跨团队分发"
    }
  ],
  "changed_files": ["PRD文档/订单管理1.0-02-PRD.md"],
  "checks": ["编号一致"],
  "open_questions": [],
  "current_stage": "review",
  "next_step": "进入质量审查"
}
```

字段详细类型、取值和嵌套结构以 JSON Schema 为准。可添加自定义字段，但不能替换或省略必填字段。上面的示例由 `tests/test_record_contract.py` 自动校验，改动示例后必须仍能通过。

## 校验器做什么、不做什么

`scripts/validate_records.py` 只读，不在业务记录目录创建任何文件。

**检查**：用 Schema 校验每个现存文件的字段与取值；核对 project/task 目录名与记录里的 ID 是否一致；核对 `projects.json` 的索引路径；核对 `latest_run_id` 是否有对应轮次文件；核对轮次记录里引用的能力 ID 是否都在 [能力清单](../capabilities/registry.json) 里（编排计划里的 `steps[].id` 同理）；核对规则与产物引用能否解析（`rule_id@revision`、`artifact_id@version`）；核对是否越界引用其他任务的任务级规则；核对规则被新版替代后，依赖旧版的产物是否都标了 `needs_review`。

**不检查**：不判断业务规则是否正确，不检查产物文件内容、内容哈希或交互质量，不补字段，不迁移旧 `context.json`，不修改任何文件。

退出码：`0` 通过，`1` 有错误，`2` 缺少 `jsonschema` 等依赖（此时不做任何写入）。

运行命令：`python -X utf8 "<pm-kit 根目录>/scripts/validate_records.py" <项目集合目录或项目目录>`。需要 Python 包 `jsonschema`；缺少依赖时脚本会明确报错并返回退出码 2，且不会修改记录。
