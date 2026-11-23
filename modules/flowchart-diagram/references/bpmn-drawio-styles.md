# BPMN Draw.io 样式参考

## 事件样式

### 开始事件

```xml
<!-- 基础开始事件 -->
style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#d5e8d4;strokeColor=#82b366;"

<!-- 消息开始事件 - 需要叠加消息图标 -->
<!-- 定时器开始事件 - 需要叠加时钟图标 -->
<!-- 信号开始事件 - 需要叠加三角图标 -->
```

### 中间事件

```xml
<!-- 基础中间事件（双线边框） -->
style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#fff2cc;strokeColor=#d6b656;double=1;"

<!-- 非中断中间事件（虚线双边框） -->
style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#fff2cc;strokeColor=#d6b656;double=1;dashed=1;"
```

### 结束事件

```xml
<!-- 基础结束事件（粗边框） -->
style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=4;fillColor=#f8cecc;strokeColor=#b85450;"

<!-- 终止结束事件 - 需要叠加实心圆 -->
<!-- 错误结束事件 - 需要叠加闪电图标 -->
```

### 边界事件

```xml
<!-- 中断边界事件 -->
style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#fff2cc;strokeColor=#d6b656;double=1;"

<!-- 非中断边界事件 -->
style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#fff2cc;strokeColor=#d6b656;double=1;dashed=1;dashPattern=3 3;"
```

## 活动样式

### 任务

```xml
<!-- 基础任务 -->
style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"

<!-- 用户任务（需添加用户图标） -->
style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"

<!-- 服务任务（需添加齿轮图标） -->
style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"

<!-- 脚本任务 -->
style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"

<!-- 业务规则任务 -->
style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"

<!-- 发送任务 -->
style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"

<!-- 接收任务 -->
style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"

<!-- 手动任务 -->
style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
```

### 子流程

```xml
<!-- 展开的子流程 -->
style="swimlane;rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;startSize=30;"

<!-- 折叠的子流程（带+号） -->
style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;"

<!-- 事件子流程（虚线边框） -->
style="swimlane;rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;startSize=30;dashed=1;dashPattern=3 3;"

<!-- 事务子流程（双线边框） -->
style="swimlane;rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;startSize=30;double=1;"
```

### 任务标记图标

```xml
<!-- 循环标记 -->
style="shape=mxgraph.bpmn.loop;fillColor=#6c8ebf;strokeColor=#6c8ebf;"

<!-- 并行多实例标记 -->
style="shape=parallelMarker;fillColor=#6c8ebf;strokeColor=#6c8ebf;"

<!-- 串行多实例标记 -->
style="shape=parallelMarker;fillColor=#6c8ebf;strokeColor=#6c8ebf;direction=south;"

<!-- 补偿标记 -->
style="shape=mxgraph.bpmn.compensation;fillColor=#6c8ebf;strokeColor=#6c8ebf;"
```

## 网关样式

```xml
<!-- 排他网关 (XOR) -->
style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
<!-- 内部添加 X 标记 -->

<!-- 并行网关 (AND) -->
style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
<!-- 内部添加 + 标记 -->

<!-- 包容网关 (OR) -->
style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
<!-- 内部添加 ○ 标记 -->

<!-- 事件网关 -->
style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
<!-- 内部添加双圆五角星标记 -->

<!-- 复杂网关 -->
style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
<!-- 内部添加 * 标记 -->
```

## 连接样式

### 顺序流

```xml
<!-- 基础顺序流 -->
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#666666;"

<!-- 条件顺序流（起始带菱形） -->
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;startArrow=diamond;startFill=0;startSize=12;strokeColor=#666666;"

<!-- 默认顺序流（起始带斜杠） -->
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#666666;"
<!-- 需要在起始端添加斜杠标记 -->
```

### 消息流

```xml
<!-- 消息流 -->
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=open;endFill=0;startArrow=oval;startFill=0;dashed=1;strokeColor=#666666;"
```

### 关联

```xml
<!-- 无向关联 -->
style="endArrow=none;dashed=1;html=1;rounded=0;strokeColor=#999999;"

<!-- 单向关联 -->
style="endArrow=open;dashed=1;html=1;rounded=0;strokeColor=#999999;endFill=0;"

<!-- 双向关联 -->
style="endArrow=open;startArrow=open;dashed=1;html=1;rounded=0;strokeColor=#999999;endFill=0;startFill=0;"
```

## 泳道样式

### 池

```xml
<!-- 水平池 -->
style="swimlane;horizontal=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontColor=#333333;startSize=30;"

<!-- 垂直池 -->
style="swimlane;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontColor=#333333;startSize=30;"

<!-- 黑盒池（空的参与者） -->
style="swimlane;horizontal=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontColor=#333333;startSize=30;collapsible=0;"
```

### 泳道

```xml
<!-- 水平泳道 -->
style="swimlane;horizontal=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;startSize=30;"

<!-- 嵌套泳道 -->
style="swimlane;horizontal=0;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;startSize=25;"
```

## 数据对象样式

```xml
<!-- 数据对象 -->
style="shape=note;whiteSpace=wrap;html=1;size=14;verticalAlign=top;align=left;spacingTop=-6;fillColor=#fff2cc;strokeColor=#d6b656;"

<!-- 数据输入 -->
style="shape=note;whiteSpace=wrap;html=1;size=14;verticalAlign=top;align=left;spacingTop=-6;fillColor=#fff2cc;strokeColor=#d6b656;"
<!-- 左上角添加空心箭头 -->

<!-- 数据输出 -->
style="shape=note;whiteSpace=wrap;html=1;size=14;verticalAlign=top;align=left;spacingTop=-6;fillColor=#fff2cc;strokeColor=#d6b656;"
<!-- 左上角添加实心箭头 -->

<!-- 数据存储 -->
style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#e1d5e7;strokeColor=#9673a6;"

<!-- 数据集合 -->
style="shape=note;whiteSpace=wrap;html=1;size=14;verticalAlign=top;align=left;spacingTop=-6;fillColor=#fff2cc;strokeColor=#d6b656;"
<!-- 底部添加三竖线标记 -->
```

## 人工制品样式

```xml
<!-- 组 -->
style="rounded=1;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#666666;dashed=1;dashPattern=3 3;"

<!-- 注释 -->
style="shape=note;whiteSpace=wrap;html=1;size=14;verticalAlign=top;align=left;spacingTop=-6;fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=10;"
```

## 颜色调色板

### 标准 BPMN 颜色

| 用途 | 填充色 | 边框色 | 十六进制 |
|------|--------|--------|----------|
| 开始事件 | 浅绿 | 绿色 | `#d5e8d4` / `#82b366` |
| 中间事件 | 浅黄 | 黄色 | `#fff2cc` / `#d6b656` |
| 结束事件 | 浅红 | 红色 | `#f8cecc` / `#b85450` |
| 任务/活动 | 浅蓝 | 蓝色 | `#dae8fc` / `#6c8ebf` |
| 子流程 | 浅紫 | 紫色 | `#e1d5e7` / `#9673a6` |
| 网关 | 浅黄 | 黄色 | `#fff2cc` / `#d6b656` |
| 数据对象 | 浅黄 | 黄色 | `#fff2cc` / `#d6b656` |
| 泳道/池 | 浅灰 | 灰色 | `#f5f5f5` / `#666666` |
| 注释 | 浅橙 | 橙色 | `#ffe6cc` / `#d79b00` |

### 泳道分色方案

不同部门/角色使用不同颜色：

| 角色类型 | 填充色 | 边框色 |
|----------|--------|--------|
| 客户/外部 | `#f5f5f5` | `#666666` |
| 销售部门 | `#dae8fc` | `#6c8ebf` |
| 财务部门 | `#d5e8d4` | `#82b366` |
| 运营部门 | `#fff2cc` | `#d6b656` |
| 技术部门 | `#e1d5e7` | `#9673a6` |
| 管理层 | `#f8cecc` | `#b85450` |

## 尺寸规范

| 元素 | 宽度 | 高度 | 说明 |
|------|------|------|------|
| 事件 | 40 | 40 | 圆形，保持 1:1 比例 |
| 边界事件 | 30 | 30 | 附着在活动边缘 |
| 任务 | 100-150 | 60-80 | 根据文字调整 |
| 网关 | 50 | 50 | 菱形，保持 1:1 比例 |
| 泳道宽度 | - | 150+ | 至少容纳一行元素 |
| 池宽度 | 800+ | - | 根据流程长度调整 |

## 间距规范

| 场景 | 推荐间距 |
|------|----------|
| 元素水平间距 | 40-60px |
| 元素垂直间距 | 40-60px |
| 泳道之间 | 0px（紧邻） |
| 池之间 | 40-60px |
| 边界事件位置 | 活动边缘，50%-80% 位置 |
