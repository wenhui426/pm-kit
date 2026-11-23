# 常见任务编排参考

这些路径是调度起点。根据用户已有产物和本轮目标增减阶段；每阶段的输入、输出和说明位置以 [能力清单](../capabilities/registry.json) 为准。

| 用户目标 | 推荐路径 | 需要检查的交接条件 |
| --- | --- | --- |
| 只分析截图或旧页面 | `analyze-input → review-validate` | 有可读取材料；仅输出分析或问题报告 |
| 竞品拆解、选样或对标分析 | `analyze-input? → clarify-requirements? → analyze-competitors` | 按材料和决策问题选择分析路径，报告保存为本地文件 |
| 竞品分析后形成方案或 PRD | `analyze-competitors? → plan-product → write-prd?` | 已有合格报告可直接引用；竞品观察和待验证建议按项目决策转成我方需求 |
| 模糊想法形成方案 | `clarify-requirements → plan-product` | 会改变范围的选择已确认或标为未决 |
| 会议纪要形成日常 PRD | `analyze-input → clarify-requirements? → plan-product? → write-prd` | 已有事实和足够清晰的需求范围；`?` 表示按缺口加入 |
| 完整产品定型到正式 PRD | `make-prd` | 用户接受其逐阶段确认、指定目录和版本规则 |
| 从模糊想法到正式 PRD、再到需长期维护的多页面原型 | `make-prd → prd-html → review-validate → deliver-change` | 两个专项模块的确认节奏已告知且用户接受；确认版 PRD 交给 `prd-html`，原型目录与设计规范由后者确认 |
| 现有 HTML 反向整理 PRD | `html-prd` | HTML 与本地依赖可读取；原文件保持不变 |
| 已确认需求形成交互稿 | `design-interaction → review-validate` | 需求和关键业务规则足以定义页面与状态 |
| 已确认流程生成独立流程图或泳道图 | `flowchart-diagram → review-validate? → deliver-change?` | 角色和分支规则已有依据；PNG 检查浏览器依赖；仅文字或 Mermaid 不触发三格式绘图 |
| 材料含糊，需先梳理再绘制业务图 | `analyze-input → clarify-requirements? → flowchart-diagram` | 澄清会改变流转的角色、分支、异常出口；不自动扩展为 PRD 或原型 |
| PRD 与独立业务图组合交付 | `write-prd/make-prd → flowchart-diagram → deliver-change` | 图引用确认的 PRD 版本与规则；流程变化时检查文档、原型和图文件依赖 |
| 交互稿形成评审原型 | `design-interaction? → build-prototype → review-validate` | 页面规格已存在时跳过设计；默认交付单文件 HTML |
| 需页面规格和逐页验收的 PRD 驱动原型 | `prd-html` | 用户接受规范选型、逐页验收及其目录要求；页数不单独触发 |
| 方向未定时试 UI 或状态 | `clarify-requirements? → build-prototype(exploration) → 用户选择` | 明确本轮只回答的设计问题；选择后再重编交付路径 |
| 改版或局部变更 | `analyze-input → 按影响选 write-prd/design-interaction/build-prototype → review-validate` | 先区分只读分析和修改授权，限定受影响范围 |
| 多产物连续项目 | `按目标选择能力 → deliver-change` | 每项产物有状态、路径和未决事项 |

调度时先看终点产物，再检查阶段输入。已有合格产物可直接交给下游。阶段交接未满足时，只补所需能力；如果需要用户决定业务规则或路径，停在该决策点。用户答复后从当前任务记录继续，不重跑已确认阶段。
