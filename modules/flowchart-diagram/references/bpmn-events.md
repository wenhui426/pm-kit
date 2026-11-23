# BPMN 事件类型详解

## 事件分类矩阵

| 触发器 | 开始 | 中间捕获 | 中间抛出 | 边界中断 | 边界非中断 | 结束 |
|--------|------|----------|----------|----------|------------|------|
| 无 | ✓ | - | ✓ | - | - | ✓ |
| 消息 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 定时器 | ✓ | ✓ | - | ✓ | ✓ | - |
| 条件 | ✓ | ✓ | - | ✓ | ✓ | - |
| 信号 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 错误 | ✓ | - | - | ✓ | - | ✓ |
| 升级 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 取消 | - | - | - | ✓ | - | ✓ |
| 补偿 | - | ✓ | ✓ | ✓ | - | ✓ |
| 链接 | - | ✓ | ✓ | - | - | - |
| 终止 | - | - | - | - | - | ✓ |
| 多重 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 并行多重 | ✓ | ✓ | - | ✓ | ✓ | - |

## 开始事件 (Start Events)

### 无触发开始事件
```xml
<mxCell id="start-none" value="开始" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="40" height="40" as="geometry" />
</mxCell>
```
- 用途：手动启动流程或未指定触发条件

### 消息开始事件
```xml
<mxCell id="start-message" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="40" height="40" as="geometry" />
</mxCell>
<mxCell id="msg-icon" value="" style="shape=message;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#82b366;strokeWidth=1;" vertex="1" parent="start-message">
  <mxGeometry x="10" y="12" width="20" height="16" as="geometry" />
</mxCell>
```
- 用途：接收消息时启动流程

### 定时器开始事件
```xml
<mxCell id="start-timer" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="40" height="40" as="geometry" />
</mxCell>
<mxCell id="timer-icon" value="" style="shape=mxgraph.bpmn.timer_start;fillColor=none;strokeColor=#82b366;strokeWidth=1;" vertex="1" parent="start-timer">
  <mxGeometry x="8" y="8" width="24" height="24" as="geometry" />
</mxCell>
```
- 用途：按时间计划启动（周期性或特定时间点）

### 条件开始事件
- 用途：当业务条件满足时启动
- 示例：库存低于阈值时启动补货流程

### 信号开始事件
- 用途：接收广播信号时启动
- 区别于消息：信号是广播给所有监听者

### 错误开始事件
- 用途：仅用于事件子流程
- 捕获父流程中的错误

## 中间事件 (Intermediate Events)

### 捕获事件（等待）

**消息捕获**：
```xml
<mxCell id="catch-message" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#fff2cc;strokeColor=#d6b656;double=1;" vertex="1" parent="1">
  <mxGeometry x="300" y="100" width="40" height="40" as="geometry" />
</mxCell>
```
- 流程暂停，等待消息到达

**定时器捕获**：
- 流程暂停，等待指定时间

**条件捕获**：
- 流程暂停，等待条件满足

**信号捕获**：
- 流程暂停，等待信号广播

### 抛出事件（触发）

**消息抛出**：
```xml
<mxCell id="throw-message" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#fff2cc;strokeColor=#d6b656;double=1;" vertex="1" parent="1">
  <mxGeometry x="300" y="100" width="40" height="40" as="geometry" />
</mxCell>
<mxCell id="msg-icon-filled" value="" style="shape=message;whiteSpace=wrap;html=1;fillColor=#d6b656;strokeColor=#d6b656;" vertex="1" parent="throw-message">
  <mxGeometry x="10" y="12" width="20" height="16" as="geometry" />
</mxCell>
```
- 发送消息给特定接收者

**信号抛出**：
- 广播信号给所有监听者

**升级抛出**：
- 触发升级处理流程

**补偿抛出**：
- 触发补偿活动执行

## 边界事件 (Boundary Events)

边界事件附着在活动上，分为：

### 中断边界事件
- 触发时：终止当前活动，执行替代路径
- 样式：实线边框

```xml
<!-- 附着在任务上的定时器边界事件 -->
<mxCell id="boundary-timer" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#fff2cc;strokeColor=#d6b656;double=1;" vertex="1" parent="task-1">
  <mxGeometry x="100" y="60" width="30" height="30" as="geometry" />
</mxCell>
```

### 非中断边界事件
- 触发时：当前活动继续，同时执行替代路径
- 样式：虚线边框

```xml
<mxCell id="boundary-timer-non" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#fff2cc;strokeColor=#d6b656;double=1;dashed=1;" vertex="1" parent="task-1">
  <mxGeometry x="100" y="60" width="30" height="30" as="geometry" />
</mxCell>
```

### 常见边界事件场景

| 边界事件类型 | 使用场景 |
|--------------|----------|
| 定时器 | 任务超时处理 |
| 错误 | 任务执行异常处理 |
| 消息 | 等待外部反馈 |
| 取消 | 事务回滚 |
| 补偿 | 定义补偿逻辑 |
| 升级 | 问题升级处理 |

## 结束事件 (End Events)

### 无触发结束事件
```xml
<mxCell id="end-none" value="结束" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=4;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
  <mxGeometry x="600" y="100" width="40" height="40" as="geometry" />
</mxCell>
```
- 用途：正常结束当前流程路径

### 消息结束事件
- 用途：结束时发送消息

### 错误结束事件
```xml
<mxCell id="end-error" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=4;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
  <mxGeometry x="600" y="100" width="40" height="40" as="geometry" />
</mxCell>
<mxCell id="error-icon" value="" style="shape=mxgraph.bpmn.error;fillColor=#b85450;strokeColor=#b85450;" vertex="1" parent="end-error">
  <mxGeometry x="10" y="10" width="20" height="20" as="geometry" />
</mxCell>
```
- 用途：抛出错误，可被父流程捕获

### 终止结束事件
```xml
<mxCell id="end-terminate" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=4;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
  <mxGeometry x="600" y="100" width="40" height="40" as="geometry" />
</mxCell>
<mxCell id="terminate-icon" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#b85450;strokeColor=#b85450;" vertex="1" parent="end-terminate">
  <mxGeometry x="12" y="12" width="16" height="16" as="geometry" />
</mxCell>
```
- 用途：立即终止流程的所有活动实例

### 取消结束事件
- 用途：取消事务子流程

### 补偿结束事件
- 用途：触发补偿活动

## 事件子流程 (Event Subprocess)

事件子流程由事件触发，在父流程上下文中执行：

```xml
<!-- 事件子流程容器 -->
<mxCell id="event-subprocess" value="异常处理" style="swimlane;rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;startSize=30;dashed=1;dashPattern=1 1;" vertex="1" parent="1">
  <mxGeometry x="100" y="300" width="400" height="150" as="geometry" />
</mxCell>
<!-- 事件子流程开始事件 -->
<mxCell id="error-start" value="" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeWidth=2;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="event-subprocess">
  <mxGeometry x="20" y="55" width="40" height="40" as="geometry" />
</mxCell>
```

### 事件子流程类型

| 类型 | 触发时机 | 父流程行为 |
|------|----------|------------|
| 中断型 | 事件触发 | 终止父流程 |
| 非中断型 | 事件触发 | 父流程继续 |
