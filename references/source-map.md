# 能力来源与整合说明

本文件记录 pm-kit 各部分的来源，供维护时判断“改这块会不会影响别处”。它不在运行时链路里，Agent 执行任务不需要读它。

## 来源

| 当前部分 | 主要来源 | 当前处理 |
| --- | --- | --- |
| 单一入口与渐进加载 | 用户要求、skill-creator | 只保留 `pm-kit/SKILL.md` 一个入口，其余按能力清单的 `instruction` 按需读取 |
| 产品规划与结构化澄清 | make-prd、frame、brief、journey；`skills-main` 的 `grilling`、`domain-modeling` | 合并为 `product-planning.md`：先从材料核对事实，再按依赖整理用户决策；只有长期项目才维护词汇表 |
| 材料分析 | scope、audit、extract | 合并为 `input-handling.md`，截图、HTML、文档和反馈走同一入口 |
| 竞品分析 | [doubao-competitor-report](https://github.com/153496792-sudo/doubao-competitor-report) | 借鉴证据要求、场景对比和深度报告结构，改为按目标选择分析路径并交付本地文件 |
| PRD | make-prd、prd、stories | 日常 PRD 走 `prd-workflow.md`；完整六步走内嵌模块 `make-prd` |
| 交互设计 | sitemap、stories、edge、flow-web/mobile | 合并为 `interaction-design.md`：IA、流程、页面和状态 |
| 流程图与泳道图 | 用户提供的 `参考/flowchart-diagram` | 内嵌为 `modules/flowchart-diagram`，保留示例、元素/事件/样式参考和两个导出脚本；适配浏览器发现、换行、回退/折点、输出保护与失败报告，BPMN 风格子集不宣称完整标准兼容 |
| 原型 | prd-html、flow-web/mobile；`skills-main` 的 `prototype` | 合并为 `prototype-html.md`：探索型与交付型分开；交付型默认单文件 HTML；明确要求后进 React；完整多页走内嵌模块 `prd-html` |
| 验证 | check、access、test、qa、metric | 合并为 `review-validation.md`，并定为**严重度分级与问题报告格式的唯一出处** |
| 交付 | make-prd、prd-html、chain-protocol、retro | 合并为 `delivery-standards.md` |
| 动态编排 | 原 skill-graph、spec-kit 的分阶段状态记录 | 把流程拆成可登记能力，按输入、目标和阶段产物动态组合；不做固定编号的流水线 |
| 能力注册与内嵌模块 | make-prd、prd-html、html-prd | 三套原能力连同模板、规范和脚本收入 `modules/`；能力清单用 `resource_base` 指明各自的资源基准 |
| 跨轮协作与隔离 | 原项目 `context.json` 与模块交接需求 | 见 `cross-round-protocol.md` 与 `record-contract.md`：项目/任务归属门禁、两级业务规则、产物依赖、每轮读写闭环 |
| 模式与深度 | 本次整合 | `task-modes.md` 的 rapid/standard/strict |
| 决策门禁 | 三套材料中的路径冲突 | `decision-gates.md` |
| 扩展目录 | 本次整合 | `catalog/` 的 built-in/local 四类资源 |

## 整合边界

- **`pm-kit` 是唯一维护位置**。早期散落在 `skills/` 下的同名独立技能目录（`make-prd`、`prd-html` 等）已不再维护；改动只需改本包，不要反向同步，也不要按它们判断当前行为。
- 连接器和外部系统没有进入本次合并范围。
- 与 [使用说明与扩展指南.md](../使用说明与扩展指南.md) 的分工：本文件讲“从哪来”，使用说明讲“怎么用、怎么扩”，不互相复述。
