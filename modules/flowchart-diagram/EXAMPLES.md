# BPMN 示例

> 来源技能的原始结构示例。业务规则、分支完整性和特殊符号需按当前任务复核，例如订单示例没有给出无库存分支，不可直接当作完整业务方案。自带渲染器只支持基础图形子集，支持范围与适配规则以 [procedure.md](procedure.md) 为准。

## 示例 1：简单审批流程

一个基本的请假审批流程：

```xml
<mxfile host="app.diagrams.net">
  <diagram id="leave-approval" name="请假审批流程">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        
        <!-- 开始事件 -->
        <mxCell id="start-1" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
          <mxGeometry x="80" y="110" width="40" height="40" as="geometry" />
        </mxCell>
        
        <!-- 提交申请 -->
        <mxCell id="task-1" value="提交请假申请" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
          <mxGeometry x="160" y="100" width="120" height="60" as="geometry" />
        </mxCell>
        
        <!-- 主管审批 -->
        <mxCell id="task-2" value="主管审批" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
          <mxGeometry x="320" y="100" width="120" height="60" as="geometry" />
        </mxCell>
        
        <!-- 审批网关 -->
        <mxCell id="gw-1" value="" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
          <mxGeometry x="480" y="105" width="50" height="50" as="geometry" />
        </mxCell>
        <mxCell id="gw-1-marker" value="X" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontStyle=1;fontSize=14;" vertex="1" parent="gw-1">
          <mxGeometry width="50" height="50" as="geometry" />
        </mxCell>
        
        <!-- 记录请假 -->
        <mxCell id="task-3" value="记录请假" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
          <mxGeometry x="570" y="100" width="120" height="60" as="geometry" />
        </mxCell>
        
        <!-- 通知申请人（拒绝） -->
        <mxCell id="task-4" value="通知申请人&#xa;（已拒绝）" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
          <mxGeometry x="570" y="200" width="120" height="60" as="geometry" />
        </mxCell>
        
        <!-- 结束事件-批准 -->
        <mxCell id="end-1" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=4;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
          <mxGeometry x="730" y="110" width="40" height="40" as="geometry" />
        </mxCell>
        
        <!-- 结束事件-拒绝 -->
        <mxCell id="end-2" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=4;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
          <mxGeometry x="730" y="210" width="40" height="40" as="geometry" />
        </mxCell>
        
        <!-- 连接线 -->
        <mxCell id="flow-1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="start-1" target="task-1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="flow-2" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="task-1" target="task-2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="flow-3" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="task-2" target="gw-1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="flow-4" value="批准" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="gw-1" target="task-3">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="flow-5" value="拒绝" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="gw-1" target="task-4">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="flow-6" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="task-3" target="end-1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="flow-7" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="task-4" target="end-2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## 示例 2：订单处理流程（带泳道）

跨部门的订单处理流程：

```xml
<mxfile host="app.diagrams.net">
  <diagram id="order-process" name="订单处理流程">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        
        <!-- 池 -->
        <mxCell id="pool-1" value="订单处理" style="swimlane;horizontal=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontColor=#333333;startSize=30;" vertex="1" parent="1">
          <mxGeometry x="40" y="40" width="900" height="360" as="geometry" />
        </mxCell>
        
        <!-- 泳道：销售 -->
        <mxCell id="lane-sales" value="销售部" style="swimlane;horizontal=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;startSize=30;" vertex="1" parent="pool-1">
          <mxGeometry x="30" y="0" width="870" height="120" as="geometry" />
        </mxCell>
        
        <!-- 泳道：仓库 -->
        <mxCell id="lane-warehouse" value="仓库" style="swimlane;horizontal=0;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;startSize=30;" vertex="1" parent="pool-1">
          <mxGeometry x="30" y="120" width="870" height="120" as="geometry" />
        </mxCell>
        
        <!-- 泳道：财务 -->
        <mxCell id="lane-finance" value="财务部" style="swimlane;horizontal=0;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;startSize=30;" vertex="1" parent="pool-1">
          <mxGeometry x="30" y="240" width="870" height="120" as="geometry" />
        </mxCell>
        
        <!-- 销售泳道元素 -->
        <mxCell id="start-order" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="lane-sales">
          <mxGeometry x="40" y="40" width="40" height="40" as="geometry" />
        </mxCell>
        
        <mxCell id="task-receive" value="接收订单" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="lane-sales">
          <mxGeometry x="120" y="35" width="100" height="50" as="geometry" />
        </mxCell>
        
        <mxCell id="task-confirm" value="确认订单" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="lane-sales">
          <mxGeometry x="700" y="35" width="100" height="50" as="geometry" />
        </mxCell>
        
        <mxCell id="end-order" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=4;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="lane-sales">
          <mxGeometry x="820" y="40" width="40" height="40" as="geometry" />
        </mxCell>
        
        <!-- 仓库泳道元素 -->
        <mxCell id="task-check-stock" value="检查库存" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="lane-warehouse">
          <mxGeometry x="260" y="35" width="100" height="50" as="geometry" />
        </mxCell>
        
        <mxCell id="gw-stock" value="" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="lane-warehouse">
          <mxGeometry x="395" y="35" width="50" height="50" as="geometry" />
        </mxCell>
        
        <mxCell id="task-ship" value="发货" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="lane-warehouse">
          <mxGeometry x="560" y="35" width="100" height="50" as="geometry" />
        </mxCell>
        
        <!-- 财务泳道元素 -->
        <mxCell id="task-invoice" value="开具发票" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="lane-finance">
          <mxGeometry x="480" y="35" width="100" height="50" as="geometry" />
        </mxCell>
        
        <!-- 连接线 -->
        <mxCell id="f1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="pool-1" source="start-order" target="task-receive">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="f2" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="pool-1" source="task-receive" target="task-check-stock">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="f3" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="pool-1" source="task-check-stock" target="gw-stock">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="f4" value="有库存" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="pool-1" source="gw-stock" target="task-invoice">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="f5" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="pool-1" source="task-invoice" target="task-ship">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="f6" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="pool-1" source="task-ship" target="task-confirm">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="f7" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="pool-1" source="task-confirm" target="end-order">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## 示例 3：并行处理流程

使用并行网关的文档审核流程：

```xml
<mxfile host="app.diagrams.net">
  <diagram id="parallel-review" name="并行审核流程">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        
        <!-- 开始 -->
        <mxCell id="start" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
          <mxGeometry x="80" y="200" width="40" height="40" as="geometry" />
        </mxCell>
        
        <!-- 提交文档 -->
        <mxCell id="submit" value="提交文档" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
          <mxGeometry x="160" y="190" width="100" height="60" as="geometry" />
        </mxCell>
        
        <!-- 分支网关 -->
        <mxCell id="split" value="+" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontStyle=1;fontSize=20;" vertex="1" parent="1">
          <mxGeometry x="300" y="195" width="50" height="50" as="geometry" />
        </mxCell>
        
        <!-- 并行审核任务 -->
        <mxCell id="legal-review" value="法务审核" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
          <mxGeometry x="400" y="100" width="100" height="60" as="geometry" />
        </mxCell>
        
        <mxCell id="tech-review" value="技术审核" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
          <mxGeometry x="400" y="190" width="100" height="60" as="geometry" />
        </mxCell>
        
        <mxCell id="finance-review" value="财务审核" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
          <mxGeometry x="400" y="280" width="100" height="60" as="geometry" />
        </mxCell>
        
        <!-- 合并网关 -->
        <mxCell id="join" value="+" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontStyle=1;fontSize=20;" vertex="1" parent="1">
          <mxGeometry x="550" y="195" width="50" height="50" as="geometry" />
        </mxCell>
        
        <!-- 汇总结果 -->
        <mxCell id="summary" value="汇总审核结果" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
          <mxGeometry x="640" y="190" width="100" height="60" as="geometry" />
        </mxCell>
        
        <!-- 结束 -->
        <mxCell id="end" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=4;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
          <mxGeometry x="780" y="200" width="40" height="40" as="geometry" />
        </mxCell>
        
        <!-- 连接线 -->
        <mxCell id="e1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="start" target="submit">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="e2" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="submit" target="split">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="e3" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="split" target="legal-review">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="e4" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="split" target="tech-review">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="e5" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="split" target="finance-review">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="e6" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="legal-review" target="join">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="e7" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="tech-review" target="join">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="e8" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="finance-review" target="join">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="e9" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="join" target="summary">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="e10" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="summary" target="end">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## 示例 4：带边界事件的任务

任务超时处理：

```xml
<mxfile host="app.diagrams.net">
  <diagram id="boundary-event" name="超时处理">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        
        <!-- 开始 -->
        <mxCell id="start" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
          <mxGeometry x="80" y="150" width="40" height="40" as="geometry" />
        </mxCell>
        
        <!-- 等待审批任务 -->
        <mxCell id="wait-approval" value="等待审批" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
          <mxGeometry x="180" y="130" width="120" height="80" as="geometry" />
        </mxCell>
        
        <!-- 定时器边界事件 -->
        <mxCell id="timer-boundary" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#fff2cc;strokeColor=#d6b656;double=1;" vertex="1" parent="1">
          <mxGeometry x="270" y="190" width="30" height="30" as="geometry" />
        </mxCell>
        
        <!-- 定时器图标 -->
        <mxCell id="timer-icon" value="⏱" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize=12;" vertex="1" parent="timer-boundary">
          <mxGeometry width="30" height="30" as="geometry" />
        </mxCell>
        
        <!-- 正常完成 -->
        <mxCell id="complete" value="处理审批结果" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
          <mxGeometry x="360" y="130" width="120" height="80" as="geometry" />
        </mxCell>
        
        <!-- 超时处理 -->
        <mxCell id="timeout" value="发送超时提醒" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
          <mxGeometry x="360" y="260" width="120" height="60" as="geometry" />
        </mxCell>
        
        <!-- 结束-正常 -->
        <mxCell id="end-normal" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=4;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
          <mxGeometry x="540" y="150" width="40" height="40" as="geometry" />
        </mxCell>
        
        <!-- 结束-超时 -->
        <mxCell id="end-timeout" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=4;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
          <mxGeometry x="540" y="270" width="40" height="40" as="geometry" />
        </mxCell>
        
        <!-- 连接线 -->
        <mxCell id="f1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="start" target="wait-approval">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="f2" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="wait-approval" target="complete">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="f3" value="超时" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="timer-boundary" target="timeout">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="f4" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="complete" target="end-normal">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="f5" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="timeout" target="end-timeout">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## 示例 5：跨组织消息流

客户与公司之间的交互：

```xml
<mxfile host="app.diagrams.net">
  <diagram id="message-flow" name="消息流示例">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        
        <!-- 客户池 -->
        <mxCell id="pool-customer" value="客户" style="swimlane;horizontal=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontColor=#333333;startSize=30;" vertex="1" parent="1">
          <mxGeometry x="40" y="40" width="700" height="120" as="geometry" />
        </mxCell>
        
        <mxCell id="c-start" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="pool-customer">
          <mxGeometry x="50" y="40" width="40" height="40" as="geometry" />
        </mxCell>
        
        <mxCell id="c-order" value="下单" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="pool-customer">
          <mxGeometry x="140" y="35" width="80" height="50" as="geometry" />
        </mxCell>
        
        <mxCell id="c-wait" value="等待发货" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="pool-customer">
          <mxGeometry x="350" y="35" width="80" height="50" as="geometry" />
        </mxCell>
        
        <mxCell id="c-receive" value="收货" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="pool-customer">
          <mxGeometry x="520" y="35" width="80" height="50" as="geometry" />
        </mxCell>
        
        <mxCell id="c-end" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=4;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="pool-customer">
          <mxGeometry x="640" y="40" width="40" height="40" as="geometry" />
        </mxCell>
        
        <!-- 公司池 -->
        <mxCell id="pool-company" value="公司" style="swimlane;horizontal=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontColor=#333333;startSize=30;" vertex="1" parent="1">
          <mxGeometry x="40" y="200" width="700" height="120" as="geometry" />
        </mxCell>
        
        <mxCell id="s-start" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="pool-company">
          <mxGeometry x="140" y="40" width="40" height="40" as="geometry" />
        </mxCell>
        
        <mxCell id="s-process" value="处理订单" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="pool-company">
          <mxGeometry x="230" y="35" width="80" height="50" as="geometry" />
        </mxCell>
        
        <mxCell id="s-ship" value="发货" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="pool-company">
          <mxGeometry x="430" y="35" width="80" height="50" as="geometry" />
        </mxCell>
        
        <mxCell id="s-end" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=4;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="pool-company">
          <mxGeometry x="550" y="40" width="40" height="40" as="geometry" />
        </mxCell>
        
        <!-- 池内顺序流 -->
        <mxCell id="cf1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="pool-customer" source="c-start" target="c-order">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="cf2" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="pool-customer" source="c-order" target="c-wait">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="cf3" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="pool-customer" source="c-wait" target="c-receive">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="cf4" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="pool-customer" source="c-receive" target="c-end">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="sf1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="pool-company" source="s-start" target="s-process">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="sf2" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="pool-company" source="s-process" target="s-ship">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="sf3" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" edge="1" parent="pool-company" source="s-ship" target="s-end">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <!-- 跨池消息流 -->
        <mxCell id="msg1" value="订单" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=open;endFill=0;startArrow=oval;startFill=0;dashed=1;strokeColor=#666666;" edge="1" parent="1" source="c-order" target="s-start">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="msg2" value="发货通知" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=open;endFill=0;startArrow=oval;startFill=0;dashed=1;strokeColor=#666666;" edge="1" parent="1" source="s-ship" target="c-wait">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```
