# 船舶报警识别Agent产品需求文档（PRD）

## 1. 产品概述

### 1.1 产品定位
基于LangGraph框架开发的智能船舶报警识别Agent，用于自动分析船舶监控图片，判断报警事件是否真实，减少误报率，提高船舶安全管理效率。

### 1.2 目标用户
- 船舶运营管理人员
- 安全监控系统管理员
- 船舶事件审核人员

### 1.3 核心价值
- **自动化审核**：减少人工审核工作量，提高处理效率
- **精准识别**：通过多条件判断，提高报警识别准确率
- **可扩展性**：支持多种事件类型和地点的识别规则配置

## 2. 功能需求

### 2.1 输入信息
系统接收以下输入参数：
- **video_event_record_id**：事件ID（唯一标识）
- **camera_name**：摄像头位置（如：驾驶台、主甲板等）
- **events_type**：事件类型（如：Calling、Smoking、Driver-CloseEyes、Smoke等）
- **snap_url**：监控图片URL地址

### 2.2 核心功能模块

#### 2.2.1 事件判断模块
- **功能**：根据输入信息，初步判断事件发生地点和事件类型
- **输出**：地点分类、事件类型分类，用于后续路由到对应的任务模块

#### 2.2.2 任务模块（按地点划分）
根据事件判断模块的结果，选择执行对应的任务模块：

**驾驶台执行模块**
- **Calling（打电话）事件**：
  - 检测条件：
    1. `has_human_body`：照片中是否检测到驾驶员的人体特征？
    2. `hand_holding_phone`：驾驶员手部位置检测到手机物体？
    3. `phone_near_ear_or_face`：手机是否靠近耳朵或脸部？
    4. `landline_telephone`：是否是有线电话？
    5. `upper_body_fully_visible`：驾驶员上半身特征可以清晰分辨吗？
  - 输出格式：JSON格式，包含5个布尔字段、判断原因（reason）、图片简述（content）

- **Smoking（吸烟）事件**：
  - 检测条件（待定义）：
    1. `has_human_body`：是否检测到人体特征？
    2. `hand_holding_cigarette`：手部是否持有香烟？
    3. `smoke_visible`：是否可见烟雾？
    4. `face_visible`：人脸是否可见？
    5. `smoking_gesture`：是否有吸烟动作？
  - 输出格式：JSON格式

- **Driver-CloseEyes（闭眼）事件**：
  - 检测条件（待定义）：
    1. `has_human_body`：是否检测到人体特征？
    2. `face_visible`：人脸是否清晰可见？
    3. `eyes_closed`：眼睛是否闭合？
    4. `eyes_closed_duration`：闭眼持续时间（估算）
    5. `driver_position`：驾驶员位置是否正常？
  - 输出格式：JSON格式

**主甲板执行模块**
- **Smoke（烟雾）事件**：
  - 检测条件（待定义）：
    1. `smoke_visible`：是否可见烟雾？
    2. `smoke_density`：烟雾密度（高/中/低）
    3. `location_identifiable`：位置是否可识别？
    4. `fire_source_visible`：是否可见火源？
    5. `environment_clear`：环境是否清晰？
  - 输出格式：JSON格式

#### 2.2.3 结果判断模块
- **功能**：基于任务模块返回的检测条件，综合判断报警是否真实
- **判断逻辑**：
  - 根据各检测条件的布尔值，结合业务规则判断
  - 返回结果：`1`（真实报警）或 `0`（误识别）
  - 提供判断依据说明

#### 2.2.4 事件上传模块
- **功能**：调用工具上传分析结果到系统
- **上传内容**：
  - 原始输入信息
  - 检测结果（JSON格式）
  - 最终判断结果（matched：1或0）
  - 判断原因

## 3. 技术架构

### 3.1 技术栈
- **框架**：LangGraph
- **模型**：火山方舟模型（兼容OpenAI API）
- **状态管理**：MessagesState + 自定义状态扩展
- **记忆管理**：MemorySaver

### 3.2 工作流程
```
Start → 事件判断模块 → 任务模块（路由） → 结果判断模块 → 事件上传 → End
```

### 3.3 状态定义
```python
class ShipAlertState(TypedDict):
    messages: Annotated[list, add_messages]  # 消息历史
    video_event_record_id: str  # 事件ID
    camera_name: str  # 摄像头位置
    events_type: str  # 事件类型
    snap_url: str  # 图片URL
    detection_result: dict  # 检测结果（JSON）
    matched: int  # 最终判断结果（1或0）
    reason: str  # 判断原因
```

## 4. 输出格式规范

### 4.1 检测结果JSON格式（以Calling为例）
```json
{
  "has_human_body": true,
  "hand_holding_phone": true,
  "phone_near_ear_or_face": true,
  "landline_telephone": false,
  "upper_body_fully_visible": true,
  "reason": "检测到驾驶员手持手机靠近耳朵，符合打电话行为特征",
  "content": "图片显示驾驶台场景，可见驾驶员上半身，手持手机靠近右耳"
}
```

### 4.2 最终输出格式
```json
{
  "video_event_record_id": "1993846874922176512",
  "camera_name": "驾驶台",
  "events_type": "Calling",
  "snap_url": "https://...",
  "detection_result": {...},
  "matched": 1,
  "reason": "综合判断：真实报警"
}
```

## 5. 非功能需求

### 5.1 性能要求
- 单次分析响应时间 < 10秒
- 支持并发处理多个事件

### 5.2 可靠性要求
- 错误处理机制完善
- 支持重试机制
- 异常情况记录日志

### 5.3 可扩展性
- 支持新增事件类型
- 支持新增检测地点
- 支持自定义检测规则

## 6. 后续优化方向

1. **多事件类型支持**：扩展更多事件类型的检测规则
2. **规则配置化**：将检测规则配置化，支持动态调整
3. **历史学习**：基于历史数据优化判断逻辑
4. **批量处理**：支持批量处理多个事件
5. **可视化界面**：提供Web界面展示分析结果

