# 任务模式与执行深度

## 1. 任务模式

下表左列是面向用户的模式名，右列是调度用的能力 ID（登记在 `capabilities/registry.json`）。两套名字用途不同，不要混用：模式名用来判断任务性质，能力 ID 用来加载说明文件。

| 模式 | 适用目标 | 常用能力 |
| --- | --- | --- |
| 探索 | 模糊想法、问题定义、机会判断 | `clarify-requirements`、`plan-product` |
| 材料分析 | 文档、截图、HTML、反馈分析 | `analyze-input`、`review-validate` |
| 竞品分析 | 竞品选样、产品拆解、同场景对标 | `analyze-competitors`，按需先用 `analyze-input` |
| 产品规划 | 用户、范围、MVP、指标 | `clarify-requirements`、`plan-product` |
| PRD | 编写、审查、修订需求 | `write-prd` 或 `make-prd` |
| 交互设计 | IA、流程、页面和状态；独立流程图或泳道图 | `design-interaction`；独立图文件用 `flowchart-diagram` |
| 原型交付 | 生成供评审或开发使用的 HTML / React 原型 | `build-prototype` 或 `prd-html`、`review-validate` |
| 原型探索 | 用可运行样例回答一个尚未解决的 UI 或业务状态问题 | `clarify-requirements`、`build-prototype` |
| 评审 | 产品走查、无障碍、测试、QA | `review-validate` |
| 改版 | 现状分析、问题驱动设计 | `analyze-input`、`design-interaction`、`build-prototype` |
| 增量修改 | 修改已有文档、页面或工程 | `analyze-input`、受影响能力、`review-validate` |
| 交付 | 开发交接、验收、复盘 | `review-validate`、`deliver-change` |

一个任务可以组合两个相邻模式，例如“PRD + 原型”“改版 + 交付”。主模式由用户最终交付物决定。

模式名给人看，运行计划里的 `task_mode` 给机器看。写计划时取下面九个值（多个模式可以映射到同一个值）：`analysis`（探索、材料分析、竞品分析）、`planning`（产品规划）、`prd`（PRD）、`interaction`（交互设计）、`prototype`（原型交付、原型探索）、`review`（评审）、`redesign`（改版）、`change`（增量修改）、`delivery`（交付）。取值以 [编排计划格式](../catalog/_schemas/workflow-plan.schema.json) 的枚举为准。

“原型探索”和“原型交付”是 `build-prototype` 的两种用途。前者用于比较或验证设计问题，后者用于形成可评审或开发接手的产物。任务只写“做原型”时按原型交付处理，判据见 [原型生成规范](prototype-html.md)。

## 2. 执行深度

### rapid 快速

适合早期讨论、方向草案、一次性分析和低成本 Demo。

- 减少非关键追问。
- 合理建议可以先写入草稿，但必须标记假设。
- 只验证关键路径。
- 不将草稿标记为正式开发交付。

### standard 标准

默认深度。

- 确认会影响范围和规则的关键信息。
- 执行必要工作流和主要质量检查。
- 覆盖主流程、关键异常、权限和一致性。
- 文件需要打开、回读或运行验证。

### strict 严格

适合正式开发、发布验收，以及涉及权限、资金、健康、合规和重要数据的产品。

- 完整记录来源和决策。
- 执行深度审查和全状态检查。
- 覆盖权限、数据、异常、恢复、发布和回滚。
- 多交付物逐项对齐并回归。
- 未决事项必须有负责人或处理状态。

## 3. 选择规则

- 用户明确指定时遵循用户选择。
- 未指定时使用 standard。
- 用户说“先看方向、快速出稿、今天先出”时推荐 rapid。
- 用户说“开发接手、正式发布、验收、上线”时推荐 strict。
- 风险较高但用户选择 rapid 时，说明省略项和风险后执行。
- 用户表达“还不确定哪种方案合适”“想先试试状态变化”时，判断是否进入原型探索；先明确一个待回答的问题。

## 4. 切换模式

任务中可以切换深度：

```text
rapid 原型验证方向
→ 用户确认
→ standard 补齐 PRD 和状态
→ strict 进入开发验收
```

切换时保留已确认内容，只补充新深度要求的部分。

