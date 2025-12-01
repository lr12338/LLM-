from typing import Annotated
from typing_extensions import TypedDict
from dataclasses import dataclass, field
from typing import List
from langchain.tools import tool
import base64
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from config import huoshan_model_deepseekv3_1, huoshan_base_url, huoshan_api_key,huoshan_model_doubaoseed1_6flash ,langsmith_key
import os
from langgraph.graph import StateGraph, START, END,MessagesState
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
#添加记忆
from langgraph.checkpoint.memory import MemorySaver

c


# 1. 初始化火山方舟模型（兼容 OpenAI API）
# --------------------------
huoshanModel = ChatOpenAI(
    model=huoshan_model_doubaoseed1_6flash,
    base_url=huoshan_base_url,
    api_key=huoshan_api_key
)

# 2. 定义 LangGraph 状态State和节点Node
# class State(TypedDict):
#     # messages 是一个列表。
#     # Annotated[list, add_messages] 的意思是：
#     # 当有新消息返回时，不要覆盖原来的，而是“追加”（Append）到列表后面。
#     # 这就是 AI 拥有“记忆”的基础。
#     messages:Annotated[list, add_messages]

# 3.定义Node 节点
def chat_node(state: MessagesState):
    #1.获取 State 的 messages
    messages = state["messages"]
    #2.调用 huoshanModel
    response = huoshanModel.invoke(messages)
    #3.返回response 
    #注：这里返回的字典会自动合并入State中的messages ,基于 add_messages逻辑：当有新消息返回时，不要覆盖原来的，而是“追加”（Append）到列表后面
    return {"messages": [response]}

#4.绘制Graph 图
#4.1 创建一个Graph实例 workflow
workflow = StateGraph(MessagesState) 
#4.2 添加节点node并定义
workflow.add_node("chatbot", chat_node)
#4.3 定义边
# Start是图的入口：启动后直接进入node：“chatbot”
workflow.add_edge(START,"chatbot")
#4.4 定义结束边:End
workflow.add_edge("chatbot", END)

#5.编译与运行
#compile 将 画纸 编译成 程序
app = workflow.compile()

#设置进程id
thread_config = {"configurable":{"thread_id":"user_1_session"}}

# ==================== 图片输入处理示例 ====================

# 方法1: 使用图片URL（最简单）
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

# 方法2: 使用本地图片路径（需要转换为base64）
import base64
from pathlib import Path

def create_message_with_local_image(image_path: str, text: str = ""):
    """使用本地图片路径创建消息"""
    # 读取图片文件
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"图片文件不存在: {image_path}")
    
    # 读取图片并转换为base64
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
    
    # 根据文件扩展名确定MIME类型
    mime_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    ext = image_path.suffix.lower()
    mime_type = mime_type_map.get(ext, 'image/jpeg')
    
    # 创建data URI
    data_uri = f"data:{mime_type};base64,{base64_image}"
    
    # 构建消息内容
    content = []
    if text:
        content.append({"type": "text", "text": text})
    content.append({
        "type": "image_url",
        "image_url": {"url": data_uri}
    })
    return HumanMessage(content=content)

# 方法3: 混合文本和图片（推荐）
def create_multimodal_message(text: str, image_url: str = None, image_path: str = None):
    """创建包含文本和图片的多模态消息"""
    content = [{"type": "text", "text": text}]
    
    if image_url:
        # 使用图片URL
        content.append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })
    elif image_path:
        # 使用本地图片路径
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
        
        mime_type_map = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp'
        }
        ext = image_path.suffix.lower()
        mime_type = mime_type_map.get(ext, 'image/jpeg')
        data_uri = f"data:{mime_type};base64,{base64_image}"
        
        content.append({
            "type": "image_url",
            "image_url": {"url": data_uri}
        })
    
    return HumanMessage(content=content)

# ==================== 使用示例 ====================

# 示例1: 使用图片URL
image_url = "https://static.hifleet.com/video_event/413601240/995e30e0-1673-409d-8d6f-bca169cd8b78.jpeg"
message_with_url = create_message_with_image_url(
    image_url=image_url,
    text="请分析这张图片中的内容"
)

# 示例2: 使用本地图片路径
# 假设图片在项目目录下
# local_image_path = "AIProject/HifleetAIVideo/dataset/img/img01.jpeg"  # 你的图片路径
# message_with_local = create_message_with_local_image(
#     image_path=local_image_path,
#     text="请分析这张图片"
# )

# 示例3: 使用混合方式（推荐）
message_mixed = create_multimodal_message(
    text="请详细分析这张图片，包括其中的文字、物体和场景",
    image_url=image_url  # 或使用 image_path=local_image_path
)

# ==================== 调用示例 ====================

# 方式1: 使用图片URL
final_state_url = app.invoke({
    "messages": [message_with_url]
}, config=thread_config)
print(f"AI回答: {final_state_url['messages'][-1].content}")

# 方式2: 使用本地图片（如果文件存在）
# final_state_local = app.invoke({
#     "messages": [message_with_local]
# }, config=thread_config)
# print(f"AI回答: {final_state_local['messages'][-1].content}")

# 方式3: 直接使用URL字符串（简单但不够灵活）
# 注意：这种方式取决于模型是否支持直接解析URL字符串
# user_input = "分析图片:https://static.hifleet.com/video_event/413601240/995e30e0-1673-409d-8d6f-bca169cd8b78.jpeg"
# final_state_simple = app.invoke({
#     "messages": [HumanMessage(content=user_input)]
# }, config=thread_config)
# print(f"AI回答: {final_state_simple['messages'][-1].content}")
