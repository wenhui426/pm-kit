# flowchart-diagram 内嵌模块

从业务说明、PRD 或交互规格生成普通流程图、角色泳道图或矩阵泳道图。默认尝试输出可编辑 `.drawio`、内嵌 SVG 的离线 `.html` 和高清 `.png`；用户可指定其中一种。

通过 pm-kit 唯一入口调用，例如：

```text
使用 pm-kit，把已确认的退款流程画成泳道图。
角色包括用户、客服和财务，覆盖通过、退回补充和拒绝。
生成可编辑 draw.io、离线 HTML 和 PNG，保存到指定项目目录。
```

Agent 执行入口是 [procedure.md](procedure.md)。资源清单：

- [EXAMPLES.md](EXAMPLES.md)：五个原始 XML 示例。
- `references/`：BPMN 元素、事件和 draw.io 样式参考。
- `scripts/render_bpmn_html.py`：标准库 SVG HTML 渲染器。
- `scripts/bpmn_to_png.py`：通过 Chrome/Edge/Chromium 导出 PNG，支持指定浏览器路径。
- [evals/evals.json](evals/evals.json)：路由、角色、分支与缺依赖的评测用例。

来自用户提供的 `参考/flowchart-diagram`。整合后保留单入口组织，适配浏览器路径、换行、连线折点、失败处理和输出覆盖保护。原参考目录继续保留。

此模块提供 BPMN 风格可视化，渲染器支持基础图形子集。高级符号、格式限制、导出命令和验收方式以执行入口为准。PNG 缺浏览器时不会伪报生成成功；导出工作文件默认保留。
