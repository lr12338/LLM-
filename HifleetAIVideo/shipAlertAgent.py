"""
船舶报警识别Agent
基于LangGraph实现的多模块智能分析系统
"""
from typing import Annotated, TypedDict
from dataclasses import dataclass, field
from langchain.tools import tool
import base64
import json
import re
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from config import huoshan_model_deepseekv3_1, huoshan_base_url, huoshan_api_key, huoshan_model_doubaoseed1_6flash, huoshan_model_doubaoseed1_6vision,langsmith_key
import os
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

### 配置langsmith
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = langsmith_key
os.environ["LANGCHAIN_PROJECT"] = "HifleetAIVideo"


# ==================== 1. 初始化模型 ====================
huoshanModel = ChatOpenAI(
    model=huoshan_model_doubaoseed1_6vision,
    base_url=huoshan_base_url,
    api_key=huoshan_api_key,
    temperature=0.1  # 降低温度以提高稳定性
)

# ==================== 2. 定义状态State ====================
class ShipAlertState(TypedDict):
    """船舶报警识别Agent的状态定义"""
    messages: Annotated[list, add_messages]  # 消息历史
    video_event_record_id: str  # 事件ID
    camera_name: str  # 摄像头位置
    events_type: str  # 事件类型
    snap_url: str  # 图片URL
    detection_result: dict  # 检测结果（JSON）
    matched: int  # 最终判断结果（1或0）
    reason: str  # 判断原因
    route_key: str  # 路由标识（location_event_key）


# ==================== 3. 提示词模板定义 ====================

# 驾驶台-打电话事件提示词
CALLING_PROMPT_TEMPLATE = """你是一名专业的船舶安全监控分析专家。请分析以下图片，该图片来自船舶驾驶台的监控摄像头。

事件类型：打电话（Calling）

请仔细分析图片，并回答以下5个问题，返回JSON格式数据：

1. has_human_body（布尔值）：照片中是否检测到驾驶员的人体特征？
2. hand_holding_phone（布尔值）：驾驶员手部位置检测到手机物体？
3. phone_near_ear_or_face（布尔值）：手机是否靠近耳朵或脸部？
4. landline_telephone（布尔值）：是否是有线电话？
5. upper_body_fully_visible（布尔值）：驾驶员上半身特征可以清晰分辨吗？

另外，请提供：
- reason（字符串）：判断原因说明
- content（字符串）：图片内容简述（不考虑图片中的文字）

请严格按照以下JSON格式返回，只返回JSON，不要包含其他文字：
{{
  "has_human_body": true/false,
  "hand_holding_phone": true/false,
  "phone_near_ear_or_face": true/false,
  "landline_telephone": true/false,
  "upper_body_fully_visible": true/false,
  "reason": "判断原因",
  "content": "图片简述"
}}
"""

# 驾驶台-吸烟事件提示词
SMOKING_PROMPT_TEMPLATE = """你是一名专业的船舶安全监控分析专家。请分析以下图片，该图片来自船舶驾驶台的监控摄像头。

事件类型：吸烟（Smoking）

请仔细分析图片，并回答以下5个问题，返回JSON格式数据：

1. has_human_body（布尔值）：是否检测到人体特征？
2. hand_holding_cigarette（布尔值）：手部人体是否检测到细小棒状物体，形态接近香烟？
3. smoke_visible（布尔值）：人体口部是否有可见烟雾特征？
4. face_visible（布尔值）：人脸是否可见？
5. smoking_gesture（布尔值）：是否有吸烟动作？

另外，请提供：
- reason（字符串）：判断原因说明
- content（字符串）：图片内容简述（不考虑图片中的文字）

请严格按照以下JSON格式返回，只返回JSON，不要包含其他文字：
{{
  "has_human_body": true/false,
  "hand_holding_cigarette": true/false,
  "smoke_visible": true/false,
  "face_visible": true/false,
  "smoking_gesture": true/false,
  "reason": "判断原因",
  "content": "图片简述"
}}
"""

# 驾驶台-闭眼事件提示词
CLOSEEYES_PROMPT_TEMPLATE = """你是一名专业的船舶安全监控分析专家。请分析以下图片，该图片来自船舶驾驶台的监控摄像头。

事件类型：闭眼（Driver-CloseEyes）

请仔细分析图片，并回答以下5个问题，返回JSON格式数据：

1. has_human_body（布尔值）：是否检测到人体特征？
2. face_visible（布尔值）：人脸是否清晰可见？
3. eyes_closed（布尔值）：眼睛是否闭合？
4. eyes_closed_duration（字符串）：闭眼持续时间估算（如：瞬间、持续、长时间）
5. driver_position（布尔值）：驾驶员位置是否正常？

另外，请提供：
- reason（字符串）：判断原因说明
- content（字符串）：图片内容简述（不考虑图片中的文字）

请严格按照以下JSON格式返回，只返回JSON，不要包含其他文字：
{{
  "has_human_body": true/false,
  "face_visible": true/false,
  "eyes_closed": true/false,
  "eyes_closed_duration": "持续时间估算",
  "driver_position": true/false,
  "reason": "判断原因",
  "content": "图片简述"
}}
"""

# 主甲板-烟雾事件提示词
SMOKE_PROMPT_TEMPLATE = """你是一名专业的船舶安全监控分析专家。请分析以下图片，该图片来自船舶主甲板的监控摄像头。

事件类型：烟雾（Smoke）

请仔细分析图片，并回答以下5个问题，返回JSON格式数据：

1. smoke_visible（布尔值）：是否可见烟雾？
2. smoke_density（字符串）：烟雾密度（高/中/低/无）
3. location_identifiable（布尔值）：位置是否可识别？
4. fire_source_visible（布尔值）：是否可见火源？
5. environment_clear（布尔值）：环境是否清晰？

另外，请提供：
- reason（字符串）：判断原因说明
- content（字符串）：图片内容简述（不考虑图片中的文字）

请严格按照以下JSON格式返回，只返回JSON，不要包含其他文字：
{{
  "smoke_visible": true/false,
  "smoke_density": "烟雾密度",
  "location_identifiable": true/false,
  "fire_source_visible": true/false,
  "environment_clear": true/false,
  "reason": "判断原因",
  "content": "图片简述"
}}
"""

# 默认事件提示词
DEFAULT_PROMPT_TEMPLATE = """你是一名专业的船舶安全监控分析专家。请分析以下图片：
该图片来自船舶场景的监控摄像头，参考提供的地点与事件类型，在该地点发生了对应事件并以该图片作为凭证
请按照以下结构进行分析图片，并根据事件类型重点关注相关特征：

1. **场景识别**：确认图片拍摄地点是否符合报告位置（{location}）
2. **主体检测**：检测图片中是否存在相关人员、物体或活动
3. **事件特征**：分析是否具备报告事件类型（{event_type}）的典型特征
4. **环境评估**：评估图片质量、光线、角度等对判断的影响

判断所标注的事件类型是否真实存在,并回答以下1个问题，返回JSON格式数据：

1. judge_result（布尔值）：事件是否真实存在

另外，请提供：
- reason（字符串）：判断原因说明
- content（字符串）：图片内容简述（不考虑图片中的文字）

请严格按照以下JSON格式返回，只返回JSON，不要包含其他文字：
{{
  "jude_result": true/false,
  "reason": "判断原因",
  "content": "图片简述"
}}
"""

# 提示词模板映射
PROMPT_TEMPLATES = {
    "驾驶台_Calling": CALLING_PROMPT_TEMPLATE,
    "驾驶台_Smoking": SMOKING_PROMPT_TEMPLATE,
    "驾驶台_Driver-CloseEyes": CLOSEEYES_PROMPT_TEMPLATE,
    "主甲板_Smoke": SMOKE_PROMPT_TEMPLATE,
    "默认场景": DEFAULT_PROMPT_TEMPLATE,
}


# ==================== 4. 工具函数 ====================

def create_message_with_image_url(image_url: str, text: str = ""):
    """使用图片URL创建消息"""
    content = []
    if text:
        content.append({"type": "text", "text": text})
    content.append({
        "type": "image_url",
        "image_url": {"url": image_url}
    })
    return HumanMessage(content=content)


def extract_json_from_text(text: str) -> dict:
    """从文本中提取JSON数据"""
    # 尝试直接解析
    try:
        return json.loads(text)
    except:
        pass
    
    # 尝试提取JSON块
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match)
        except:
            continue
    
    # 如果都失败，返回空字典
    return {}


# ==================== 5. 节点定义 ====================

def event_judge_node(state: ShipAlertState) -> dict:
    """
    事件判断模块
    根据输入信息，初步判断地点与事件标签，确定路由
    """
    # 获取输入信息
    camera_name = state.get("camera_name", "")
    events_type = state.get("events_type", "")
    
    # 构建路由标识
    route_key = f"{camera_name}_{events_type}"
    
    # 验证路由是否支持
    if route_key not in PROMPT_TEMPLATES:
        route_key = DEFAULT_PROMPT_TEMPLATE
        print(f"警告：未找到对应的提示词模板，使用默认处理。route_key: {route_key}")
    
    return {
        "route_key": route_key,
        "messages": [HumanMessage(content=f"事件判断完成：地点={camera_name}, 事件类型={events_type}, 路由={route_key}")]
    }


def task_node(state: ShipAlertState) -> dict:
    """
    任务模块
    根据事件判断模块的结果，选择执行对应的任务模块
    """
    route_key = state.get("route_key", "unknown")
    snap_url = state.get("snap_url", "")

    # 获取对应的提示词模板
    prompt_template = PROMPT_TEMPLATES.get(route_key, f"请分析这张图片,事件地点-类型:{route_key}。{PROMPT_TEMPLATES.get('默认场景','')}")
    # 创建多模态消息
    message = create_message_with_image_url(
        image_url=snap_url,
        text=prompt_template
    )
    
    # 调用模型
    response = huoshanModel.invoke([message])
    
    # 提取JSON结果
    response_text = response.content if hasattr(response, 'content') else str(response)
    detection_result = extract_json_from_text(response_text)
    
    # 如果提取失败，使用默认值
    if not detection_result:
        detection_result = {
            "error": "无法解析模型返回结果",
            "raw_response": response_text
        }
        print(f"警告：无法解析JSON结果，原始响应：{response_text[:200]}")
    
    return {
        "detection_result": detection_result,
        "messages": [response]
    }


def result_judge_node(state: ShipAlertState) -> dict:
    """
    结果判断模块
    基于任务模块返回的检测条件，综合判断报警是否真实
    """
    detection_result = state.get("detection_result", {})
    events_type = state.get("events_type", "")
    route_key = state.get("route_key", "")
    
    matched = 0
    reason = ""
    
    # 根据事件类型和路由，应用不同的判断规则
    if route_key == "驾驶台_Calling":
        # 打电话事件判断规则
        has_human_body = detection_result.get("has_human_body", False)
        hand_holding_phone = detection_result.get("hand_holding_phone", False)
        phone_near_ear_or_face = detection_result.get("phone_near_ear_or_face", False)
        landline_telephone = detection_result.get("landline_telephone", False)
        
        if not has_human_body:
            matched = 0
            reason = "未检测到人体特征，判定为误识别"
        elif landline_telephone:
            matched = 1
            reason = "检测到有线电话，判定为真实报警"
        elif hand_holding_phone and phone_near_ear_or_face:
            matched = 1
            reason = "检测到手持手机靠近耳朵/脸部，判定为真实报警"
        else:
            matched = 0
            reason = "未满足打电话行为的充分条件，判定为误识别"
    
    elif route_key == "驾驶台_Smoking":
        # 吸烟事件判断规则
        has_human_body = detection_result.get("has_human_body", False)
        hand_holding_cigarette = detection_result.get("hand_holding_cigarette", False)
        smoke_visible = detection_result.get("smoke_visible", False)
        smoking_gesture = detection_result.get("smoking_gesture", False)
        
        if not has_human_body:
            matched = 0
            reason = "未检测到人体特征，判定为误识别"
        elif hand_holding_cigarette and (smoke_visible or smoking_gesture):
            matched = 1
            reason = "检测到手持香烟且有吸烟动作/烟雾，判定为真实报警"
        elif hand_holding_cigarette:
            matched = 1
            reason = "检测到手持香烟，判定为真实报警"
        else:
            matched = 0
            reason = "未满足吸烟行为的充分条件，判定为误识别"
    
    elif route_key == "驾驶台_Driver-CloseEyes":
        # 闭眼事件判断规则
        has_human_body = detection_result.get("has_human_body", False)
        face_visible = detection_result.get("face_visible", False)
        eyes_closed = detection_result.get("eyes_closed", False)
        eyes_closed_duration = detection_result.get("eyes_closed_duration", "")
        
        if not has_human_body or not face_visible:
            matched = 0
            reason = "未检测到人体特征或人脸不可见，判定为误识别"
        elif eyes_closed and ("持续" in eyes_closed_duration or "长时间" in eyes_closed_duration):
            matched = 1
            reason = "检测到持续闭眼，判定为真实报警"
        elif eyes_closed:
            matched = 1
            reason = "检测到闭眼，判定为真实报警"
        else:
            matched = 0
            reason = "未检测到闭眼行为，判定为误识别"
    
    elif route_key == "主甲板_Smoke":
        # 烟雾事件判断规则
        smoke_visible = detection_result.get("smoke_visible", False)
        smoke_density = detection_result.get("smoke_density", "无")
        fire_source_visible = detection_result.get("fire_source_visible", False)
        
        if smoke_visible and smoke_density in ["高", "中"]:
            matched = 1
            reason = f"检测到明显烟雾（密度：{smoke_density}），判定为真实报警"
        elif fire_source_visible:
            matched = 1
            reason = "检测到火源，判定为真实报警"
        elif smoke_visible:
            matched = 1
            reason = "检测到烟雾，判定为真实报警"
        else:
            matched = 0
            reason = "未检测到烟雾或火源，判定为误识别"
    
    else:
        # 未知路由，使用通用判断
        judge_result= detection_result.get("judge_result", False)
        if judge_result:
            matched = 1
            reason = f"场景（{route_key}）未定义，判定为真实报警"   
        else:         
            matched = 0
            reason = f"场景（{route_key}）未定义，默认判定为误识别"
    
    return {
        "matched": matched,
        "reason": reason
    }


# @tool
def upload_event_result(
    video_event_record_id: str,
    camera_name: str,
    events_type: str,
    snap_url: str,
    detection_result: dict,
    matched: int,
    reason: str
) -> str:
    """
    事件上传工具
    上传分析结果到系统（这里可以替换为实际的API调用）
    """
    result_data = {
        "video_event_record_id": video_event_record_id,
        "camera_name": camera_name,
        "events_type": events_type,
        "snap_url": snap_url,
        "detection_result": detection_result,
        "matched": matched,
        "reason": reason
    }
    
    # TODO: 这里可以替换为实际的上传API调用
    # 例如：requests.post("https://api.example.com/upload", json=result_data)
    
    print(f"\n========== 事件上传结果 ==========")
    print(json.dumps(result_data, ensure_ascii=False, indent=2))
    print(f"===================================\n")
    
    return f"事件上传成功：{video_event_record_id}, matched={matched}"


def upload_node(state: ShipAlertState) -> dict:
    """
    事件上传模块
    调用工具上传数据
    """
    # 准备上传数据
    result = upload_event_result(
        video_event_record_id=state.get("video_event_record_id", ""),
        camera_name=state.get("camera_name", ""),
        events_type=state.get("events_type", ""),
        snap_url=state.get("snap_url", ""),
        detection_result=state.get("detection_result", {}),
        matched=state.get("matched", 0),
        reason=state.get("reason", "")
    )
    
    return {
        "messages": [HumanMessage(content=f"上传完成：{result}")]
    }


# ==================== 6. 构建Graph ====================

def create_ship_alert_workflow():
    """创建船舶报警识别工作流"""
    workflow = StateGraph(ShipAlertState)
    
    # 添加节点
    workflow.add_node("event_judge", event_judge_node)
    workflow.add_node("task", task_node)
    workflow.add_node("result_judge", result_judge_node)
    workflow.add_node("upload", upload_node)
    
    # 定义边
    workflow.add_edge(START, "event_judge")
    workflow.add_edge("event_judge", "task")
    workflow.add_edge("task", "result_judge")
    workflow.add_edge("result_judge", "upload")
    workflow.add_edge("upload", END)
    
    # 编译
    app = workflow.compile()
    
    return app


# ==================== 7. 主程序 ====================

if __name__ == "__main__":
    # 创建工作流
    app = create_ship_alert_workflow()
    
    # 设置线程配置
    thread_config = {"configurable": {"thread_id": "ship_alert_session_1"}}
    
    # # 测试示例1：驾驶台-打电话事件
    # print("=" * 50)
    # print("测试示例1：驾驶台-打电话事件")
    # print("=" * 50)
    
    # test_input_1 = {
    #     "messages": [],
    #     "video_event_record_id": "1993846874922176512",
    #     "camera_name": "驾驶台",
    #     "events_type": "Calling",
    #     "snap_url": "https://static.hifleet.com/video_event/413601240/995e30e0-1673-409d-8d6f-bca169cd8b78.jpeg",
    #     "detection_result": {},
    #     "matched": 0,
    #     "reason": "",
    #     "route_key": ""
    # }
    
    # final_state_1 = app.invoke(test_input_1, config=thread_config)
    
    # print(f"\n最终结果：")
    # print(f"matched: {final_state_1.get('matched')}")
    # print(f"reason: {final_state_1.get('reason')}")
    # print(f"detection_result: {json.dumps(final_state_1.get('detection_result', {}), ensure_ascii=False, indent=2)}")
    
    # 测试示例2：驾驶台-吸烟事件
    print("\n" + "=" * 50)
    print("测试示例2：驾驶台-吸烟事件")
    print("=" * 50)
    
    test_input_2 = {
        "messages": [],
        "video_event_record_id": "1993845288053395456",
        "camera_name": "驾驶台",
        "events_type": "Smoking",
        "snap_url": "https://static.hifleet.com/video_event/413587240/803ddca1-bfb7-4b53-b10f-fa674d5c191c.jpeg",
        "detection_result": {},
        "matched": 0,
        "reason": "",
        "route_key": ""
    }
    
    final_state_2 = app.invoke(test_input_2, config=thread_config)
    
    print(f"\n最终结果：")
    print(f"matched: {final_state_2.get('matched')}")
    print(f"reason: {final_state_2.get('reason')}")
    print(f"detection_result: {json.dumps(final_state_2.get('detection_result', {}), ensure_ascii=False, indent=2)}")
    print(final_state_2)
